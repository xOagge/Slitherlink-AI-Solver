import os
import time
import copy
import random
import multiprocessing
import slitherlink

from slitherlink import Board, Slitherlink, SlitherlinkState
from search import (
    depth_first_tree_search,
    breadth_first_tree_search,
    greedy_search,
    astar_search,
    recursive_best_first_search,
)

# ─────────────────────────────────────────────
#  Algorithms to benchmark (no hill climbing / simulated annealing)
# ─────────────────────────────────────────────
ALGORITHMS = {
    "DFS Tree": depth_first_tree_search,
    # "BFS Tree": breadth_first_tree_search,
    # "Greedy":   greedy_search,
    # "A*":       astar_search,
    # "RBFS":     recursive_best_first_search,
}

RUNS    = 30
TIMEOUT = 60        # seconds per run
TESTS   = range(1, 10)  # test01.txt … test09.txt


# ─────────────────────────────────────────────
#  Attach counter + action shuffler
# ─────────────────────────────────────────────
def attach_counter(problem, seed):
    """
    Monkey-patches result() to count expanded nodes.
    Monkey-patches actions() to shuffle the returned order using
    an isolated RNG seeded per-run, so every run explores a
    different branching order.
    """
    state = {"nodes": 0}
    rng   = random.Random(seed)

    _orig_result  = problem.result
    _orig_actions = problem.actions

    def counted_result(s, a):
        state["nodes"] += 1
        return _orig_result(s, a)

    def shuffled_actions(s):
        acts = list(_orig_actions(s))
        rng.shuffle(acts)
        return tuple(acts)

    problem.result  = counted_result
    problem.actions = shuffled_actions
    return state


# ─────────────────────────────────────────────
#  Worker (runs inside a child process)
# ─────────────────────────────────────────────
def worker(algo_name, board, seed, return_dict):
    random.seed(seed)
    SlitherlinkState.state_id = 0

    problem = Slitherlink(board)
    counter = attach_counter(problem, seed)

    algo = ALGORITHMS[algo_name]

    start = time.perf_counter()
    try:
        result = algo(problem)
        status = "Solved" if result else "Failed"
    except Exception as e:
        status = f"Error({e})"
    elapsed = time.perf_counter() - start

    return_dict["time"]     = elapsed
    return_dict["nodes"]    = counter["nodes"]
    return_dict["status"]   = status
    return_dict["revisits"] = problem.visited_count


# ─────────────────────────────────────────────
#  Single timed run with timeout
# ─────────────────────────────────────────────
def run_once(algo_name, board, seed, timeout=TIMEOUT):
    manager     = multiprocessing.Manager()
    return_dict = manager.dict()

    p = multiprocessing.Process(
        target=worker,
        args=(algo_name, board, seed, return_dict)
    )
    p.start()
    p.join(timeout)

    if p.is_alive():
        p.terminate()
        p.join()
        return timeout, 0, "Timeout", 0

    return (
        return_dict.get("time",     timeout),
        return_dict.get("nodes",    0),
        return_dict.get("status",   "Error"),
        return_dict.get("revisits", 0),
    )


# ─────────────────────────────────────────────
#  Pretty printer
# ─────────────────────────────────────────────
HDR = f"{'Run':>4} | {'Status':<9} | {'Time (s)':>10} | {'Nodes':>8} | {'ms/node':>9} | {'Revisits':>9}"
SEP = "-" * len(HDR)

def print_run(run, status, t, nodes, revisits):
    ms_per_node = (t * 1000 / nodes) if nodes > 0 else float("nan")
    print(f"{run:>4} | {status:<9} | {t:>10.4f} | {nodes:>8} | {ms_per_node:>9.3f} | {revisits:>9}")

def print_summary(times, nodes_list, revisits_list):
    n         = len(times)
    avg_t     = sum(times) / n
    avg_nodes = sum(nodes_list) / n
    avg_rev   = sum(revisits_list) / n
    ms_per    = (avg_t * 1000 / avg_nodes) if avg_nodes > 0 else float("nan")
    print(SEP)
    print(f"{'AVG':>4} | {'':9} | {avg_t:>10.4f} | {avg_nodes:>8.1f} | {ms_per:>9.3f} | {avg_rev:>9.1f}")


# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────
def main():
    BASE_SEED = 42

    for i in TESTS:
        filename = f"test{i:02d}.txt"
        if not os.path.exists(filename):
            print(f"\n[SKIP] {filename} not found")
            continue

        with open(filename, "r") as f:
            slitherlink.stdin = f
            board_template = Board.parse_instance()

        print(f"\n{'═'*60}")
        print(f"  FILE: {filename}")
        print(f"{'═'*60}")

        for algo_name in ALGORITHMS:
            print(f"\n  ── {algo_name} ──")
            print(f"  {HDR}")
            print(f"  {SEP}")

            run_times    = []
            run_nodes    = []
            run_revisits = []

            for run in range(1, RUNS + 1):
                seed  = BASE_SEED + (i * 1000) + (run * 7)
                board = copy.deepcopy(board_template)

                t, nodes, status, revisits = run_once(algo_name, board, seed)

                run_times.append(t)
                run_nodes.append(nodes)
                run_revisits.append(revisits)

                print(f"  ", end="")
                print_run(run, status, t, nodes, revisits)

            print(f"  ", end="")
            print_summary(run_times, run_nodes, run_revisits)


if __name__ == "__main__":
    main()