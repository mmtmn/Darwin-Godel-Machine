import argparse
import os
import subprocess
import threading
from typing import Optional, List, Any

from llm_withtools import (
    OLLAMA_MODEL,
    chat_with_agent
)

from utils.git_utils import (
    reset_to_commit,
    get_current_commit,
    diff_versus_commit,
    apply_patch
)
from utils.logger_utils import setup_logger, safe_log
from utils.eval_utils import (
    get_report_score,
    msg_history_to_report,
    score_tie_breaker
)

class AgenticSystem:
    """
    A coding agent that reads a repository, modifies code, runs tests, and logs attempts.
    If self_improve=True, it attempts to improve itself rather than solve a standard coding problem.
    """

    def __init__(
        self,
        problem_statement: str,
        git_tempdir: str,
        test_description: Optional[str] = None,
        self_improve: bool = False,
        instance_id: Optional[str] = None,
        max_retries: int = 3,
        num_candidates: int = 3,
        chat_history_file: str = "./chat_history.md"
    ):
        self.problem_statement = problem_statement
        self.git_tempdir = git_tempdir
        self.test_description = test_description
        self.self_improve = self_improve
        self.instance_id = instance_id if instance_id else "agent"
        self.max_retries = max_retries
        self.num_candidates = num_candidates

        # If the agent is self-improving, we might choose a different model.
        # But here we keep it simple and use Claude or OpenAI based on a config:
        self.code_model = OLLAMA_MODEL

        # Setup logger
        self.logger = setup_logger(chat_history_file)
        self.base_commit = get_current_commit(self.git_tempdir)

        # State for whether we can still edit code
        self._valid = True

    def forward(self):
        """
        Attempt to solve the assigned problem (or self-improve).
        We do multiple attempts, gather multiple valid patches, 
        then pick the best solution among them.
        """
        regression_tests_summary = self.get_regression_tests()
        valid_patches = []
        valid_reports = []
        valid_scores = []
        best_score = 0
        best_patches_indices = []

        retry_count = 0
        attempts_done = 0

        while (retry_count < self.max_retries) and (len(valid_patches) < self.num_candidates):
            safe_log(f"\n=== Attempt {retry_count + 1} of {self.max_retries} ===")
            safe_log(f"Valid solutions so far: {len(valid_patches)} / {self.num_candidates}")
            safe_log(f"Current best test score: {best_score}")

            if retry_count > 0:
                # revert to base commit
                reset_to_commit(self.git_tempdir, self.base_commit)

            # Build instruction
            base_instruction = (
                f"I have uploaded a code repository in the directory {self.git_tempdir}.\n"
                f"Help solve the following problem:\n\n"
                f"<problem_description>\n{self.problem_statement}\n</problem_description>\n\n"
            )
            if retry_count > 0 and valid_patches:
                base_instruction += (
                    "\nWe have some previous valid patches and test results. "
                    "Try to provide a new or improved solution that addresses shortcomings."
                )

            # Interact with LLM
            chat_with_agent(base_instruction, model=self.code_model, msg_history=[], logging=safe_log)

            # Get the patch
            patch = self.get_current_edits()
            is_valid, reason = self.check_patch_validity(patch)
            if not is_valid:
                safe_log(f"Invalid patch: {reason}")
                retry_count += 1
                if retry_count >= self.max_retries:
                    safe_log("Max retries reached. No valid patch found.")
                continue

            # Evaluate patch
            test_report = self.run_regression_tests(regression_tests_summary)
            test_score = get_report_score(test_report)
            safe_log(f"Test score: {test_score}")
            valid_patches.append(patch)
            valid_reports.append(test_report)
            valid_scores.append(test_score)

            # track best so far
            if test_score > best_score:
                best_score = test_score
                best_patches_indices = [len(valid_patches) - 1]
            elif test_score == best_score:
                best_patches_indices.append(len(valid_patches) - 1)

            attempts_done += 1
            if attempts_done >= self.max_retries:
                break

        if not valid_patches:
            safe_log("Failed to generate any valid patches.")
            return

        # pick best patch
        if len(best_patches_indices) == 1:
            best_index = best_patches_indices[0]
        else:
            # tie-breaker among best
            safe_log(f"Multiple solutions tied for best score {best_score}. Using tie-breaker.")
            best_index = score_tie_breaker(
                self.problem_statement,
                [valid_patches[i] for i in best_patches_indices],
                [valid_reports[i] for i in best_patches_indices],
                logging=safe_log
            )
            best_index = best_patches_indices[best_index]

        safe_log(f"Applying best patch with test score {valid_scores[best_index]}")
        reset_to_commit(self.git_tempdir, self.base_commit)
        apply_patch(self.git_tempdir, valid_patches[best_index])

        # final check
        final_report = self.run_regression_tests(regression_tests_summary)
        final_score = get_report_score(final_report)
        safe_log(f"Final solution test score: {final_score}")

    def get_regression_tests(self) -> str:
        """
        Return a summary or location of the regression tests 
        (for logging / debugging). 
        Could load a text, or call an external script.
        """
        return "Regression tests summary..."

    def run_regression_tests(self, summary: str) -> str:
        """
        Actually run tests in the repo, gather output. 
        This might be domain-specific (Pytest, etc).
        """
        safe_log(f"Running regression tests in {self.git_tempdir} with summary: {summary}")
        # Example: run python -m pytest
        test_cmd = ["python", "-m", "pytest", "-q"]
        try:
            proc = subprocess.run(test_cmd, cwd=self.git_tempdir, capture_output=True, text=True)
            output = f"{proc.stdout}\n{proc.stderr}"
            return output
        except Exception as e:
            return f"Error running tests: {e}"

    def get_current_edits(self) -> str:
        """
        Compare codebase vs the base commit and extract a patch.
        """
        patch = diff_versus_commit(self.git_tempdir, self.base_commit)
        return patch

    def check_patch_validity(self, patch: str):
        """
        Simple check that the patch is not empty, 
        and it actually edits some non-test files.
        """
        if not patch.strip():
            return False, "Empty patch"
        if "+++ b/tests/" in patch and "+++ b/" not in patch.replace("+++ b/tests/", ""):
            # means only tests changed
            return False, "Only test files modified"

        # Edits at least some non-test file
        return True, "OK"

    def is_valid(self) -> bool:
        """
        Return whether agent still can do code edits 
        (in case some self-modification broke it).
        """
        return self._valid

def main():
    parser = argparse.ArgumentParser(description='Process repository with an agentic system.')
    parser.add_argument('--problem_statement', required=True, help='The problem statement')
    parser.add_argument('--git_tempdir', required=True, help='Path to the code repository')
    parser.add_argument('--test_description', default=None, required=False, help='How to test?')
    parser.add_argument('--self_improve', default=False, action='store_true', help='Self-improve?')
    parser.add_argument('--instance_id', default=None, help='Agent instance ID')
    parser.add_argument('--max_retries', type=int, default=3)
    parser.add_argument('--num_candidates', type=int, default=3)
    args = parser.parse_args()

    agent = AgenticSystem(
        problem_statement=args.problem_statement,
        git_tempdir=args.git_tempdir,
        test_description=args.test_description,
        self_improve=args.self_improve,
        instance_id=args.instance_id,
        max_retries=args.max_retries,
        num_candidates=args.num_candidates
    )
    agent.forward()

    # Potentially print final patch
    final_patch = agent.get_current_edits()
    print(final_patch)

if __name__ == "__main__":
    main()
