import cProfile
import pstats
import io
from sys import stdin

from slitherlink import Board, Slitherlink, SlitherlinkState
from search import depth_first_tree_search

board = Board.parse_instance()
problem = Slitherlink(board)

pr = cProfile.Profile()
pr.enable()

solution_node = depth_first_tree_search(problem)

pr.disable()

stream = io.StringIO()
stats = pstats.Stats(pr, stream=stream)
stats.sort_stats('tottime')
stats.print_stats(30)

print(stream.getvalue())

if solution_node:
    print(solution_node.state.board.print())
else:
    print("No solution found")