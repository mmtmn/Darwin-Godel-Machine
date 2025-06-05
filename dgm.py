import argparse
import random
from typing import List, Dict, Any
import os
import shutil
import tempfile
import time
import uuid
from coding_agent import AgenticSystem
from utils.logger_utils import safe_log
from utils.git_utils import init_repo, commit_all, get_current_commit
from utils.eval_utils import evaluate_agent, AgentRecord


# Darwin Gödel Machine
# (A population-based open-ended loop for self-improving coding agents.)

class DarwinGodelMachine:
    def __init__(self,
                 initial_agent: AgenticSystem,
                 benchmark_name: str,
                 max_iterations: int = 80,
                 parallel_samples: int = 2,
                 archive_save_path: str = "./archive"):
        """
        :param initial_agent: The first coding agent. Must have codebase editing & basic functionality.
        :param benchmark_name: Name or path of your coding benchmark for tasks & scoring.
        :param max_iterations: Number of iterations to run the open-ended loop.
        :param parallel_samples: Number of agents to generate in parallel each iteration.
        :param archive_save_path: Path to store the discovered agents (code + metrics).
        """
        self.benchmark_name = benchmark_name
        self.max_iterations = max_iterations
        self.parallel_samples = parallel_samples
        self.archive_save_path = archive_save_path

        # Archive of discovered agents
        self.archive: List[AgentRecord] = []
        # Setup initial agent in the archive
        init_score = evaluate_agent(initial_agent, benchmark_name)
        safe_log(f"Initial agent performance: {init_score:.4f}")
        record = AgentRecord(agent=initial_agent, performance=init_score)
        self.archive.append(record)

        # Create an archive directory
        os.makedirs(self.archive_save_path, exist_ok=True)
        self.save_agent_code(record, name="initial_agent")

    def run(self):
        for iteration in range(self.max_iterations):
            safe_log(f"\n=== Darwin Gödel Machine Iteration {iteration} ===")
            # Parent selection
            parents = self.select_parents()

            # For each parent, spawn a child in parallel
            children_records = []
            for p_idx, parent in enumerate(parents):
                child_record = self.self_modify_agent(parent)
                if child_record is not None:
                    children_records.append(child_record)

            # Extend archive with new children
            for c in children_records:
                self.archive.append(c)

            # (Optional) any concurrency or parallel scheduling goes here.

    def select_parents(self) -> List[AgentRecord]:
        """
        Sample a small set of parents from the archive, 
        favoring those that are high performing & have fewer children.
        We do a weighted random selection.
        """
        # Filter out perfect agents if we have a known max performance.
        # Or keep them if we want to keep exploring.
        # Here we just keep them all for open-ended exploration.
        # Weighted by performance
        total_perf = sum(r.performance for r in self.archive)
        if total_perf <= 1e-9:
            # fallback to uniform
            parents = random.sample(self.archive, min(len(self.archive), self.parallel_samples))
            return parents

        # Weighted sampling
        selected_parents = []
        for _ in range(self.parallel_samples):
            # a quick approach: random pick by performance proportion
            pick_val = random.random() * total_perf
            acc = 0.0
            for rec in self.archive:
                acc += rec.performance
                if acc >= pick_val:
                    selected_parents.append(rec)
                    break
        return selected_parents

    def self_modify_agent(self, parent: AgentRecord) -> AgentRecord:
        """
        Have the parent agent generate a new agent that modifies itself or extends itself,
        and evaluate that new child on the benchmark. 
        """
        safe_log(f"Selected parent with performance {parent.performance:.4f}")
        # Prepare a new codebase directory
        temp_dir = tempfile.mkdtemp(prefix="dgm_child_")
        safe_log(f"Creating child agent code in {temp_dir}")

        # Copy parent's code
        self.copy_codebase(parent.agent.git_tempdir, temp_dir)

        # Now create child agent that modifies code
        child_instance_id = f"child_{str(uuid.uuid4())[:8]}"
        child_agent = AgenticSystem(
            problem_statement=(
                "Self-Improve: Propose next feature to improve the coding agent's own design, "
                "based on prior logs and performance. Focus on a general improvement, not a single fix."
            ),
            git_tempdir=temp_dir,
            test_description="(Self-improvement) Additional checks for the agent itself.",
            self_improve=True,
            instance_id=child_instance_id,
            max_retries=3,
            num_candidates=1  # Typically 1 for self-improvement
        )

        # The agent modifies itself
        # (We rely on child's forward() to do so)
        child_agent.forward()

        # Evaluate the child
        child_score = evaluate_agent(child_agent, self.benchmark_name)

        # Decide if we keep the child
        if not child_agent.is_valid():
            safe_log("Child agent lost codebase editing functionality - discarding.")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None

        safe_log(f"Child agent performance: {child_score:.4f}")
        new_record = AgentRecord(agent=child_agent, performance=child_score)
        # Save the child's code in the archive folder
        short_id = child_instance_id
        self.save_agent_code(new_record, name=f"{short_id}_perf_{child_score:.3f}")
        return new_record

    def copy_codebase(self, src_dir: str, dst_dir: str):
        for item in os.listdir(src_dir):
            if item == ".git":
                continue  # Skip git internals to avoid permission errors
            s = os.path.join(src_dir, item)
            d = os.path.join(dst_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)


    def save_agent_code(self, record: AgentRecord, name: str):
        """
        Save the agent's code and performance in the archive folder.
        """
        save_path = os.path.join(self.archive_save_path, f"{name}")
        os.makedirs(save_path, exist_ok=True)

        agent_dir = record.agent.git_tempdir
        code_dest = os.path.join(save_path, "code")
        os.makedirs(code_dest, exist_ok=True)

        # 👇 Skip .git folder while copying
        for item in os.listdir(agent_dir):
            if item == ".git":
                continue
            s = os.path.join(agent_dir, item)
            d = os.path.join(code_dest, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

        with open(os.path.join(save_path, "performance.txt"), "w") as f:
            f.write(f"Performance: {record.performance:.4f}\n")


def main():
    parser = argparse.ArgumentParser(description="Run the Darwin Gödel Machine.")
    parser.add_argument("--benchmark_name", type=str, default="SWE-bench",
                        help="Name/path of coding benchmark.")
    parser.add_argument("--iterations", type=int, default=80, 
                        help="Number of DGM iterations.")
    parser.add_argument("--archive_path", type=str, default="./archive",
                        help="Where to store discovered agents.")
    parser.add_argument("--parallel_samples", type=int, default=2,
                        help="Number of parents to sample each iteration.")
    args = parser.parse_args()

    # Prepare initial code directory
    init_repo_dir = tempfile.mkdtemp(prefix="dgm_init_agent_")
    init_repo(init_repo_dir)
    with open(os.path.join(init_repo_dir, "agent.py"), "w") as f:
        f.write("# Initial agent code\n")
    # Commit initial
    commit_all(init_repo_dir, "Initial commit - blank agent codebase")

    # Create an initial coding agent
    instance_id = "initial_agent"
    initial_agent = AgenticSystem(
        problem_statement="Initial agent with minimal code editing & tool usage",
        git_tempdir=init_repo_dir,
        test_description="(Initial) Basic tests of code editing functionality",
        self_improve=False,
        instance_id=instance_id,
        max_retries=3,
        num_candidates=1
    )

    # Possibly you want to add actual code to the initial agent's repo,
    # or do an initial forward pass:
    initial_agent.forward()

    # Now create the DGM
    dgm = DarwinGodelMachine(initial_agent=initial_agent,
                             benchmark_name=args.benchmark_name,
                             max_iterations=args.iterations,
                             parallel_samples=args.parallel_samples,
                             archive_save_path=args.archive_path)
    # Launch open-ended run
    dgm.run()

if __name__ == "__main__":
    main()
