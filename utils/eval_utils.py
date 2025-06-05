from typing import List, Tuple
import re

class AgentRecord:
    def __init__(self, agent, performance: float):
        self.agent = agent
        self.performance = performance

def evaluate_agent(agent, benchmark_name: str) -> float:
    """
    Evaluate a coding agent on a chosen benchmark.
    This is placeholder logic: 
    in practice, you'd run a set of tasks, measure pass rates, etc.
    """
    # e.g., run a subset of tasks
    # for demonstration, we just parse "Test Score" from agent logs or do a dummy random approach
    # We'll return a random float or parse from agent logs if we had them
    import random
    # In a real system, you'd parse test logs, do pass@k, etc.
    # Here, just do random for demonstration
    score = random.uniform(0.0, 1.0)
    return score

def get_report_score(report: str) -> float:
    """
    Read the test output and compute a 'score'.
    This is a placeholder for the logic that extracts pass/fail from the logs.
    We'll do a simple approach: count 'FAILED', 'ERROR', or 'ok' lines, etc.
    """
    if not report or "Error running tests:" in report:
        return 0.0

    # naive parse
    num_ok = len(re.findall(r"(?i)\bok\b", report))
    num_fail = len(re.findall(r"(?i)\bfail(ed)?\b", report))
    if num_ok + num_fail == 0:
        # fallback
        return 0.0
    # Weighted
    score = float(num_ok) / (num_ok + num_fail)
    return score

def msg_history_to_report(msg_history):
    """
    Convert msg history to some textual summary or just join them.
    """
    return "\n".join([f"{m['role']}: {m['content']}" for m in msg_history])

def score_tie_breaker(problem_statement: str,
                      patches: List[str],
                      reports: List[str],
                      logging=print) -> int:
    """
    Choose among equally-scoring solutions, e.g. by their patch length or by analyzing logs.
    For demonstration, pick the shortest patch or some simple heuristic.
    """
    best_index = 0
    best_len = len(patches[0])
    for i in range(1, len(patches)):
        l = len(patches[i])
        if l < best_len:
            best_len = l
            best_index = i
    logging(f"Tie-breaker picking patch with length {best_len}. (index={best_index})")
    return best_index
