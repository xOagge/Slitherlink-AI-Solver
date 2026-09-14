# Slitherlink AI Solver

This repository contains a comprehensive, Python-based Artificial Intelligence solver for the classic Slitherlink logic puzzle[cite: 6]. 

## Extensive Project Description

The Slitherlink AI Solver models the puzzle as a complex state-space search problem[cite: 6]. To navigate this space efficiently, the solver relies heavily on AI search tree algorithms, predominantly utilizing Depth-First Search (DFS) and Greedy Search methods, while also supporting A*, Breadth-First Search (BFS), and Recursive Best-First Search (RBFS)[cite: 6]. 

Because a brute-force approach to Slitherlink results in an exponentially large search tree, this project heavily integrates constraint satisfaction techniques[cite: 7, 9]. The AI utilizes a SAT (Boolean Satisfiability) Oracle and Constraint Propagator to continuously evaluate the board[cite: 9]. By applying methods like Forward Checking and Arc Consistency (AC-3), the solver logically deduces mandatory and forbidden edges in real-time[cite: 7]. This dynamic pruning creates a "cascade effect" that drastically reduces the number of nodes the search tree algorithms must explore, allowing the AI to solve complex puzzles efficiently[cite: 9].

## Project Architecture

*   **`slitherlink.py`**: The core file defining the `SlitherlinkState` and `Board` classes, managing the state transitions, action validations, and goal testing[cite: 6]. It also includes the heuristic functions used to guide the greedy and A* searches[cite: 6].
*   **`SATOracle.py`**: Houses the `ConstraintPropagator` class, which dynamically applies local constraints to vertices and cells during the search to prevent illegal moves and premature loops[cite: 9].
*   **`initial_propagator.py`**: Executes static pattern recognition (e.g., adjacent 3s, diagonal 3s, or corner constraints) to solve trivial parts of the board before the main search tree is even initialized[cite: 7].
*   **`utils.py`**: Provides foundational statistical operations, sequence manipulations, and data structures (like Priority Queues) necessary to support the broader AI algorithms[cite: 8].

## Usage Examples

The solver is designed to read puzzle configurations from standard input. Below are three primary ways to execute the code:

**1. Standard Solver Execution:**
You can pipe a text-based puzzle directly into the main script from the command line:
```bash
python3 slitherlink.py < tests/test01.txt
