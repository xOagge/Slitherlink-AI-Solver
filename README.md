# Slitherlink AI Solver

A comprehensive Python-based Artificial Intelligence solver for the classic Slitherlink logic puzzle. This project utilizes state-space search algorithms combined with rigorous constraint propagation to efficiently find solutions to puzzles of varying difficulties.

## How the Code Works

Solving Slitherlink using brute force generates an exponentially large search tree. To overcome this, the solver pairs AI search algorithms (like Depth-First Search and Greedy Search) with a Constraint Satisfaction system to heavily prune the tree[cite: 6, 9]. 

Here is the step-by-step breakdown of the execution pipeline:

1. **Initial Propagation (Static Rules):** Before the search tree is even built, the `InitialPropagator` scans the board for known static patterns[cite: 7]. For example, a `0` cell automatically forbids all surrounding edges, while adjacent `3` cells force specific edges to be drawn[cite: 7]. This solves trivial parts of the puzzle immediately.
2. **State-Space Search:** The core of the solver uses algorithms like DFS or Greedy Search to explore possible moves[cite: 6]. At each step, it looks for "loose ends" (vertices with exactly one connected edge) and attempts to draw the next valid line[cite: 6].
3. **Constraint Propagation (The SAT Oracle):** Every time an edge is drawn, the `ConstraintPropagator` steps in[cite: 9]. It checks the local constraints of the affected cells (ensuring they don't exceed their target number) and vertices (ensuring no vertex has more than 2 edges, avoiding intersections)[cite: 9]. If a move forces another edge to be drawn or forbidden, the propagator applies it in a cascade[cite: 9]. If a rule is broken or a premature loop is closed, the state is marked invalid, and the search algorithm backtracks[cite: 9].
4. **Heuristic Guidance:** For informed algorithms like Greedy Search, a custom heuristic evaluates how close the board is to a solution[cite: 6]. It calculates the number of missing edges and uses Manhattan distance to encourage the AI to connect existing loose ends rather than starting new, fragmented line segments[cite: 6].

## Project Structure

*   `slitherlink.py`: The main execution script containing the `Board` state definition, transition models, goal testing, and search heuristics[cite: 6].
*   `SATOracle.py`: Contains the `ConstraintPropagator` to enforce Slitherlink vertex and cell rules dynamically[cite: 9].
*   `initial_propagator.py`: Implements static pattern recognition for the initial board state[cite: 7].
*   `search.py`: Houses the core AI search algorithms (DFS, BFS, A*, Greedy, RBFS)[cite: 6].
*   `utils.py`: Provides foundational data structures, mathematical operations, and sequence manipulations[cite: 8].

## Usage & Examples

The solver reads puzzle configurations from standard input (`stdin`). You can run the solver using the following commands depending on what you want to achieve:

**1. Standard Solver Execution**
Run the main solver script by piping in a puzzle text file:
```bash
python3 slitherlink.py < tests/test01.
python3 slitherlink_gui.py
python3 example1.py < "../tests/test03.txt"
