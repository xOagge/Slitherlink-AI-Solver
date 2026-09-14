#!/usr/bin/python3
# slitherlink.py: Template para implementação do projeto de Inteligência Artificial 2025/2026.
# Devem alterar as classes e funções neste ficheiro de acordo com as instruções do enunciado.
# Além das funções e classes sugeridas, podem acrescentar outras que considerem pertinentes.

# Grupo 00:
# 00000 Nome1
# 00000 Nome2

import random, copy
from sys import stdin
from collections import defaultdict

import build.utils as utils
from build.utils import *

from search import (
    Problem,
    Node,
    astar_search,
    breadth_first_tree_search,
    depth_first_tree_search,
    greedy_search,
    recursive_best_first_search,
)

class SlitherlinkState:
    state_id = 0

    def __init__(self, board):
        self.board:Board = board
        self.id = SlitherlinkState.state_id
        SlitherlinkState.state_id += 1

        #tem as actions permitidas, pois corre-se o propagator antes
        self.allowed_actions = ()

        #store the propagation for the allowed actions, which we do in rank_actions
        self.prop_cache = {}
    
    def __lt__(self, other):
        return self.id < other.id

    # TODO: outros metodos da classe


    def get_board(self):
        return self.board
    
    def __eq__(self, other):
        if not isinstance(other, SlitherlinkState): return False
        is_equal = self.board.all_drawn_edges == other.board.all_drawn_edges
        return is_equal

    def __hash__(self):
        return hash(frozenset(self.board.all_drawn_edges))

class Board:
    """Representação interna de um tabuleiro de Slitherlink."""

    def adjacent_cell(self, cell:tuple) -> list:
        """Devolve uma lista das células que fazem
        fronteira com a célula enviada no argumento"""

        #lista de celulas adjacentes
        a_cells = []

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_cell = (cell[0] + dr, cell[1] + dc)
            #checkl if calculated cell is inside board
            #cell is treated as having indexes
            if 0 <= new_cell[0] < self.rows and \
               0 <= new_cell[1] < self.cols:
                a_cells.append(new_cell)

        return a_cells

    def get_cell_edges(self, row:int, column:int) -> list:
        """Devolve os arestas da célula enviada no argumento"""

        #cada celula segue esta logica, nao existe celulas com regimes
        #de arestas diferente como no caso de adjacent_cells
        return [('h',row, column), ('h',row+1, column), \
                ('v',row, column), ('v',row, column+1)]

    #exemplo retorna numero, o template diz -> list, alterei para ->int
    def get_active_edges(self, row:int, column:int) -> int:
        """Devolve o número de arestas ativas"""
        drawn = self.all_drawn_edges
        count = 0
        if ('h',row, column) in drawn: count += 1
        if ('h',row+1, column) in drawn: count += 1
        if ('v',row, column) in drawn: count += 1
        if ('v',row, column+1) in drawn: count += 1

        return count

    @staticmethod
    def parse_instance():
        """Lê o test do standard input (stdin) que é passado como argumento
        e retorna uma instância da classe Board.

        Por exemplo:
            $ python3 pipe.py < tests/test-01.txt

            > from sys import stdin
            > line = stdin.readline().split()
        """
        
        #layout = [line.split() for line in stdin]
        layout = [[-1 if cell == '.' else int(cell) for cell in line.split()] for line in stdin]
        return Board(layout)

        #exemplo retorna um numero
    
    def get_inactive_edges(self, row:int, column:int) -> int:
        """Devolve o número de arestas ativas"""
        count = 4
        for edge in self.all_drawn_edges:
            if edge == ('h',row, column) or edge == ('h',row+1, column) \
               or edge == ('v',row, column) or edge == ('v',row, column+1):
               count -= 1
        return count

    # TODO: outros metodos da classe ----------------------------------

    def __init__(self, board:list):
        self.board:list = board
        self.rows:int = len(board) #row size
        self.cols:int = len(board[0]) #column size

        #sendo uma board NxM comprimento, temos 
        # N+1 rows e M columns de linhas horizontais 
        # N rows e M+1 columns de linhas verticais
        #range(X)-> [0,X-1], entao para ter K elementos, range(K)

        #TODAS AS EDGES PARA A BOARD DEFINIDA -----------------
        self.all_edges = {
            ('h', r, c) for r in range(self.rows + 1) for c in range(self.cols)
        } | {
            ('v', r, c) for r in range(self.rows) for c in range(self.cols + 1)
        }

        
        #GLOBAL EDGES
        self.global_forbidden = set() #globally forbidden
        self.global_drawn = set() #globally mandatory
        self.global_domain = set() #globally all edges we can interact with

        #STATE LEVEL RULES
        self.forbidden_edges = set() #state forbidden
        self.drawn_edges = set() #state drawn

        #RECENTLY UPDATED EDGES
        self.recently_changed_edges = set()

        #VERTICES DEGREES
        # {vertice : degree}. Inicialmente  todos vertices com deg 0
        self.vertices_deg = {(r, c): 0 for r in range(self.rows + 1) for c in range(self.cols + 1)}

        #flag para sabermos se um loop foi fechado. default false
        self.potential_loop_closed = False

    @property
    def all_drawn_edges(self):
        """ALL STATE DRAWN EDGES"""
        return self.drawn_edges | self.global_drawn
    
    @property
    def all_forbidden_edges(self):
        """ALL STATE FORBIDDEN EDGES"""
        return self.forbidden_edges | self.global_forbidden


    def draw_edge(self, action):
        """Usado sempre que queremos adicionar uma single edge"""
        self.drawn_edges.add(action) #draw edge
        self.recently_changed_edges.add(action) #recently changed memory
        #update vertices degrees
        v1, v2 = self.get_edge_vertices(action)
        #se antes de update dois vertices dao deg1, entao vamos fechar um loop
        if self.vertices_deg[v1] == 1 and self.vertices_deg[v2] == 1:
            self.potential_loop_closed = True
        self.vertices_deg[v1] += 1
        self.vertices_deg[v2] += 1


    def draw_edges(self, action):
        """Usado sempre que queremos adicionar um conjunto de edges"""
        self.drawn_edges.update(action)#draw edge
        self.recently_changed_edges.update(action)#recently changed memory
        #update vertices degrees
        for edge in action:
            v1, v2 = self.get_edge_vertices(edge)
            #se antes de update dois vertices dao deg1, entao vamos fechar um loop
            if self.vertices_deg[v1] == 1 and self.vertices_deg[v2] == 1:
                self.potential_loop_closed = True
            self.vertices_deg[v1] += 1
            self.vertices_deg[v2] += 1
    
    def forbid_edge(self, action):
        self.forbidden_edges.add(action)
        self.recently_changed_edges.add(action)
    
    def forbid_edges(self, action):
        self.forbidden_edges.update(action)
        self.recently_changed_edges.update(action)


    
    #CALCULAR CONECTIVIDADE DAS EDGES ------------------

    def get_edge_vertices(self, edge):
        t, r, c = edge
        vertices = ()
        if t == 'h': vertices = ((r, c), (r, c + 1))
        else: vertices = ((r, c), (r + 1, c))
        return vertices

    def get_edges_connectivity(self):
        """Importancia: 
            -vertice com conectividade 2: restantes
        edges sao proibidas
            -vertice conectividade 1: loose edge, podemos fazer
        proxima acao aqui
            -vertice conectividade 0: no meio do nada, nao vamos
            construir aqui
        return : {edge: (v1 connect, v2 connect)}
        """
        #{vertice: numero de vezes tocado}
        vertice_count = defaultdict(int)
        #iterate edges
        for edge in self.all_drawn_edges:
            vertices = self.get_edge_vertices(edge)
            vertice_count[vertices[0]] += 1
            vertice_count[vertices[1]] += 1

        #{edge: (v1 connect, v2 connect)}
        connectivity = {}
        for edge in self.all_edges:
            v1, v2 = self.get_edge_vertices(edge)
            # O grau é 0 se o vértice não estiver no dicionário
            connectivity[edge] = ((v1,vertice_count.get(v1, 0)), (v2,vertice_count.get(v2, 0)))
        
        return connectivity
    
    def get_edges_around_vertex(self, vertex):
        """para em ConstraintPropagator sabermos que edges estao desenhadas, proibidas,
        etc, a volta de um vertice, usamos este metodo. da return a todas as relevantes
        , proibidas, e desenhadas, para em constraintPropagator poder receber a situacao
        local na sua totalidade"""
        r, c = vertex
        drawn = self.all_drawn_edges
        forbidden = self.all_forbidden_edges
        all_edges = self.all_edges

        result_drawn = set()
        result_forbidden = set()
        result_undrawn = set()

        for edge in (('h', r, c-1), ('h', r, c), ('v', r-1, c), ('v', r, c)):
            if edge not in all_edges:
                continue
            if edge in drawn:
                result_drawn.add(edge)
            elif edge in forbidden:
                result_forbidden.add(edge)
            else:
                result_undrawn.add(edge)

        return (result_forbidden, result_drawn, result_undrawn)
        
        
    #METODOS PARA INTERAGIRA COES COM CELULAS
        
    def is_action_adjacent_to_edge(self, action):
        """metodo criado para verificar se acao vai criar uma edge
        conectada a uma outra, crucial para afunilar a arvora para solucoes
        plausiveis mais rapido, da return a true ou false, meaning que a
        edge action e conectada ou nao"""

        #orgulhoso de ter feito com desenhinhos, usei o gemini pro para confirmar
        # se logica fazia sentido (mas o clanker nao verificou um erro de que uma
        #last action fecha um ciclo com count 2, otario)

        #util para saber se edge nao cria um branch, nao aceitavel como solucao
        count_1 = 0
        count_2 = 0

        t, r, c = action #type, row, col
        if t == 'h':
            for edge in self.all_drawn_edges:
                t2, r2, c2 = edge
                if t2 == 'h':
                    if r == r2 and c-1 == c2: count_1 += 1
                    if r == r2 and c+1 == c2: count_2 += 1
                if t2 == 'v':
                    if r-1 == r2 and c == c2 or r == r2 and c == c2:
                        count_1 += 1
                    if r-1 == r2 and c+1 == c2 or r == r2 and c+1 == c2:
                        count_2 += 1
        elif t == 'v':
            for edge in self.all_drawn_edges:
                t2, r2, c2 = edge
                if t2 == 'h':
                    if r == r2 and c-1 == c2 or r == r2 and c == c2:
                        count_1 += 1
                    if r+1 == r2 and c == c2 or r+1 == r2 and c-1 == c2:
                        count_2 += 1
                if t2 == 'v':
                    if r-1 == r2 and c == c2:
                        count_1 += 1
                    if r+1 == r2 and c == c2:
                        count_2 += 1
        # nenhum vertice tem branch, e esta conectado em pelo menos um dos lados
        if count_1 <= 1 and count_2 <= 1 and count_1 + count_2 >= 1: 
            return True
        return False

    def cells_adjacent_to_edge(self, action):
        """metodo criado para encontra cells adjacented? afetadas
        pela criacao de uma linha, vai ser usado para avaliar se esta
        nova linha vai levar a uma celula exceder o valor limite proprio"""
        t, r, c = action #type, row, col
        #encontrar celulas adjacentes a linha correspondente a action
        cells_list = []
        if t == 'h':
            if r-1 >= 0: cells_list.append((r-1, c))
            if r < self.rows: cells_list.append((r, c))
        elif t == 'v':
            if c-1 >= 0: cells_list.append((r, c-1))
            if c < self.cols: cells_list.append((r, c))
        return cells_list
    
    def is_action_possible(self, action):
        """verifica se uma action vai de acordo com as restricoes 
        das celulas afetadas"""
        cells_list = self.cells_adjacent_to_edge(action)

        #para as celulas afetadas, vamos ver se ja nao teem linhas limite
        for cell in cells_list:
            cell_r, cell_c = cell[0], cell[1]
            cell_value = self.board[cell_r][cell_c] #valor na celula
            if cell_value == "." or cell_value == -1: continue #celuluas com '.' podem tudo
            n_active_edges = self.get_active_edges(cell_r, cell_c) #n linhas ja ativas
            #se n linhas ativas e igual ao maximo que a celula pode ter, marcar acao
            #como inplausivel
            if n_active_edges >= int(cell_value):
                return False
        #se foi verificado para todas as celulas afetadas por esta acao que nao estao
        #ja no seu limite, podemos entao considerar esta acao plausivel
        return True

    #METODO DE COPY

    def new_state(self):
        """
        Deep copy do Board para evitar partilha de estado entre nós da procura.
        """

        # Nova board com o mesmo layout base
        novo_tabuleiro = Board(self.board)

        # Copiar GLOBALS (normalmente são partilhados logicamente,
        # mas se queres total isolamento na search tree, copia tudo)
        novo_tabuleiro.global_forbidden = self.global_forbidden.copy()
        novo_tabuleiro.global_drawn = self.global_drawn.copy()
        novo_tabuleiro.global_domain = self.global_domain.copy()

        # Copiar STATE (isto é o que muda durante a procura)
        novo_tabuleiro.forbidden_edges = self.forbidden_edges.copy()
        novo_tabuleiro.drawn_edges = self.drawn_edges.copy()

        # reset a recent changed, pois esta nova board esta a receber o seu
        #estado inicial, nada e considerado new changes
        novo_tabuleiro.recently_changed_edges = set()

        #setup a vertices degree
        novo_tabuleiro.vertices_deg = self.vertices_deg.copy()

        return novo_tabuleiro

    def print(self) -> str:
        output_lines = []
        
        for r in range(self.rows):
            row_cells = []
            for c in range(self.cols):

                top    = "1" if ('h', r, c) in self.drawn_edges else "0"
                right  = "1" if ('v', r, c+1) in self.drawn_edges else "0"
                bottom = "1" if ('h', r+1, c) in self.drawn_edges else "0"
                left   = "1" if ('v', r, c) in self.drawn_edges else "0"

                row_cells.append(f"{top}{right}{bottom}{left}")

            output_lines.append("\t".join(row_cells))

        return "\n".join(output_lines)

    #FULL GEMINI - usado durante o desenvolvimento para visualizar como
    #o algoritmo se propaga e refletir sobre que dificuldades tem
    def print_complete(self) -> str:
            """
            Retorna uma representação visual do tabuleiro para debugging.
            + x +   +-------+
            x   |   |       |
            +---+   2       x

            As arestas desenhadas usam '---' e '|'.
            As arestas proibidas usam ' x ' e 'x'.
            """
            output = []
            
            # Fallback seguro caso a variável forbidden_edges ainda não exista no board
            unallowed = getattr(self, 'forbidden_edges', set())
            
            for r in range(self.rows):
                # 1. Linha das arestas HORIZONTAIS e Vértices
                h_line = ""
                for c in range(self.cols):
                    h_line += "+"
                    if ('h', r, c) in self.all_drawn_edges:
                        h_line += "---"
                    elif ('h', r, c) in self.all_forbidden_edges:
                        h_line += " x "  # Representação visual da proibição horizontal
                    else:
                        h_line += "   "
                h_line += "+" # Último vértice da linha
                output.append(h_line)

                # 2. Linha das arestas VERTICAIS e Valores das Células
                v_line = ""
                for c in range(self.cols):
                    if ('v', r, c) in self.all_drawn_edges:
                        v_line += "|"
                    elif ('v', r, c) in self.all_forbidden_edges:
                        v_line += "x"    # Representação visual da proibição vertical
                    else:
                        v_line += " "
                    
                    # Converter para string, mas imprimir espaço se for '-1'
                    val = str(self.board[r][c])
                    v_line += f" {val if val != '-1' else ' '} "
                
                # Última aresta vertical da linha
                if ('v', r, self.cols) in self.all_drawn_edges:
                    v_line += "|"
                elif ('v', r, self.cols) in self.all_forbidden_edges:
                    v_line += "x"
                else:
                    v_line += " "
                output.append(v_line)

            # 3. Linha HORIZONTAL final (fundo do tabuleiro)
            last_h_line = ""
            for c in range(self.cols):
                last_h_line += "+"
                if ('h', self.rows, c) in self.all_drawn_edges:
                    last_h_line += "---"
                elif ('h', self.rows, c) in self.all_forbidden_edges:
                    last_h_line += " x "
                else:
                    last_h_line += "   "
            last_h_line += "+"
            output.append(last_h_line)
            output.append('\n-----------------------------------\n')

            return "\n".join(output)   
    
class Slitherlink(Problem):
    def __init__(self, board: Board, gui=None):
        """O construtor especifica o estado inicial."""

        #local import para nao criar circularidade de imports
        from build.initial_propagator import InitialPropagator
        from build.SATOracle import ConstraintPropagator

        self.gui = gui
        
        #CALCULAR GLOBAL FORBIDDEN E MANDATORY EDGES
        Board = board.new_state()
        
        temp_state = SlitherlinkState(Board)
        init_propagator = InitialPropagator(temp_state)

        forbidden = init_propagator.forbidden_edges()
        mandatory = init_propagator.mandatory_edges()

        #INJETAR GLOBAIS EM BOARD
        Board.global_forbidden = Board.all_edges.intersection(set(forbidden))
        Board.global_drawn = Board.all_edges.intersection(set(mandatory))
        Board.global_domain = Board.all_edges - Board.global_forbidden
        Board.recently_changed_edges = Board.global_drawn | Board.global_forbidden
        Board.draw_edges(Board.global_drawn)


        # print("--- Board after Initial Constraints (Before Cascade Propagation) ---")
        # print(Board.print_complete())

        # Correr o Motor de Dedução (Efeito Cascata)
        propagator = ConstraintPropagator(Board)
        allowed_actions = propagator.propagate()

        # Criar o estado inicial verdadeiro PARA A PROCURA
        initial_state = SlitherlinkState(Board)
        
        if allowed_actions is False:
            initial_state.is_valid = False
            initial_state.allowed_actions = []
        else:
            initial_state.is_valid = True
            initial_state.allowed_actions = allowed_actions
            
        self.initial = initial_state

        #Memoria de estados anteriores
        self._visited_buffer = {}
        self._VISITED_BUFFER_LIMIT = 10000

        #para propositos de programacao e estudo
        self.visited_count = 0

        #mostra InitialPropagator + ConstraintPropagator
        # print("--- Board after InitialPropagator + ConstraintPropagator ---")
        # print(self.initial.board.print_complete())

    def _is_visited(self, board_hash: frozenset) -> bool:
        """usado para verificar se uma board ja foi visitada, ou seja
        esta na memoria mais recente."""
        if board_hash in self._visited_buffer:
            return True
        self._visited_buffer[board_hash] = None
        if len(self._visited_buffer) > self._VISITED_BUFFER_LIMIT:
            oldest = next(iter(self._visited_buffer))
            del self._visited_buffer[oldest]
        return False

    def rank_actions(self, state: SlitherlinkState, actions: list) -> list:
        """efetua o rank das actions aceitaveis para uma board, usando a heuristica
        definida que valoriza preencher celulas, desenhar e proibir edges, diminuir
        o numero de loose edges, criacao de loops."""
        from build.SATOracle import ConstraintPropagator

        board = state.board

        #forma sugerida por ai para compactar
        loose_ends_before = sum(1 for d in board.vertices_deg.values() if d == 1)

        valid_scored_actions = []
        prop_cache = {}  # <-- cache: action -> already-propagated board_copy

        for action in actions:
            board_copy = board.new_state()
            board_copy.draw_edge(action)

            PP = ConstraintPropagator(board_copy)
            is_valid = PP.propagate()

            if is_valid is False:
                continue

            board_hash = frozenset(board_copy.all_drawn_edges)
            if self._is_visited(board_hash):
                #print("board is equal to a prevoius studied one")
                self.visited_count += 1
                continue

            # Store the propagated copy — result() will reuse it directly
            prop_cache[action] = (board_copy, is_valid)

            (cells3, cells2, cells1) = PP.propagate_cells_info()
            (drawn_m, drawn_f) = PP.propagate_edges_info()

            score = 0
            score += len(cells3) * 100
            score += len(cells1) * 80
            score += len(cells2) * 50
            score += len(drawn_m) * 20
            score += len(drawn_f) * 5

            loose_ends_after = sum(1 for d in board_copy.vertices_deg.values() if d == 1)

            loose_end_delta = loose_ends_after - loose_ends_before
            score -= loose_end_delta * 200

            if loose_ends_after == 2:
                score += 40
            elif loose_ends_after == 0 and len(board_copy.all_drawn_edges) > 0:
                score += 1000

            valid_scored_actions.append((action, score))

        valid_scored_actions.sort(key=lambda x: x[1], reverse=True)

        # Side-effect: attach cache to state so result() can consume it
        state.prop_cache = prop_cache

        return [action for action, _ in valid_scored_actions]

    def calc_board_action_edges(self, board: Board):
        """
        Uses MRV (Minimum Remaining Values) to find candidate edges.
        Instead of returning all loose ends, it only returns the edges 
        for the single most constrained vertex.
        """

        deg1_v = [v for v, deg in board.vertices_deg.items() if deg == 1]
        
        best_edges = set()
        min_options = 999
        
        for v in deg1_v:
            # Pega nas arestas não desenhadas à volta deste vértice
            _, _, undrawn = board.get_edges_around_vertex(v)
            
            # Se encontrou um beco sem saída imediato, retorna vazio para forçar backtrack
            if len(undrawn) == 0:
                return set()
                
            # MRV: Guarda apenas as arestas do vértice com menos opções.
            if len(undrawn) < min_options:
                min_options = len(undrawn)
                best_edges = set(undrawn)
                
                # devido a propagate, nao vamos ter loose edges com 1 opcao, pois tal e mandatory
                # e deve ser tratado em propagate, entao o menor que reste e 2, mas mantemos o 1 por seguranca
                if min_options == 2 or min_options == 1:
                    break
                    
        return best_edges

    def actions(self, state: SlitherlinkState):
        """define as acoes possiveis para um estado, idealmente da return
        a actions do MRV rankeadas pela heuristica de valorizacao de 
        propagacao. se nao houver loose edges, exemplo, board com caso
        inicial vazio, comecamos por desenhar numa celula com o maior numero
        que encontrarmor"""
        if not state.is_valid: return ()

        valid_actions = list(self.calc_board_action_edges(state.board))
        if valid_actions:
            return tuple(self.rank_actions(state, valid_actions))
            
        # Fallback: no loose ends yet, pick a starting edge
        available = state.board.all_edges - state.board.all_drawn_edges - state.board.all_forbidden_edges
        
        # Try cells in order of descending hint (3, 2, 1)
        for target_hint in (3, 2, 1):
            for r in range(state.board.rows):
                for c in range(state.board.cols):
                    if state.board.board[r][c] == target_hint:
                        cell_edges = [e for e in state.board.get_cell_edges(r, c) if e in available]
                        if cell_edges:
                            return tuple(self.rank_actions(state, cell_edges))

        return ()

    def result(self, state, action):
        """adiciona uma action que foi selecionada em actions, e faz a
        constrains propagation"""

        from build.SATOracle import ConstraintPropagator

        is_single = isinstance(action, tuple) and isinstance(action[0], str)

        # 1 --- CRIAR NOVA BOARD, APLICAR ACTION, E PROPAGAR CONSTRAINTS
        if is_single:
            # Single action: try to use the propagation cache from rank_actions
            cache = getattr(state, 'prop_cache', {})
            if action in cache:
                board_copy, is_valid = cache[action]
            else:
                board_copy = state.board.new_state()
                board_copy.draw_edge(action)
                propagator = ConstraintPropagator(board_copy)
                is_valid = propagator.propagate()
        else:
            # List of actions: no cache, just draw all and propagate once
            board_copy = state.board.new_state()
            for act in action:
                board_copy.draw_edge(act)
            propagator = ConstraintPropagator(board_copy)
            is_valid = propagator.propagate()

        new_state = SlitherlinkState(board_copy)

        #print(new_state.board.print_complete())

        # 2 --- VERIFICAR SE NOVA BOARD E VALIDA

        # 2.1 --- SE PROPAGATE RESUMIU INVALIDO, NOVA BOARD E INVALIDA
        if is_valid is False:
            new_state.is_valid = False
            return new_state
        
        # 3 --- SE TEM CELULAS UNREACHABLE E NAO CORRESPONDIDAS, BOARD E INVALIDA
        # if self.is_region_unreachable(new_state):
        #     new_state.is_valid = False
        #     return new_state

        # 4 --- SE PASSOU POR FILTROS, ENTAO A NOVA BOARD E VALIDA 
        new_state.is_valid = True
        new_state.allowed_actions = is_valid
            
        return new_state
    
    def is_region_unreachable(self, state) -> bool:
        """
        Verifica se há alguma célula insatisfeita que o loop em progresso
        nunca conseguirá alcançar. Se sim, o estado é um beco sem saída.
 
        A ideia é simples: o loop só pode crescer a partir das suas pontas soltas
        (vértices com grau 1). Se uma célula que ainda precisa de arestas não
        tem nenhum vértice candidato acessível a partir dessas pontas, é impossível
        satisfazê-la e podemos fazer prune imediatamente.
        """
        board = state.board
        drawn = board.all_drawn_edges
        all_edges = board.all_edges
        unallowed = board.all_forbidden_edges
 
        # As pontas soltas do loop atual são os únicos pontos de crescimento possíveis.
        # Reutilizamos o vertices_deg que já está atualizado pelo draw_edge/draw_edges.
        loose_ends = [v for v, deg in board.vertices_deg.items() if deg == 1]
 
        # Recolher todas as células que ainda precisam de mais arestas,
        # junto com os vértices candidatos (das arestas ainda disponíveis).
        unsatisfied = []
        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                if hint == -1 or hint == ".":
                    continue
 
                hint = int(hint)
                if board.get_active_edges(r, c) >= hint:
                    continue  # célula já satisfeita
 
                # Quais vértices desta célula ainda têm arestas livres?
                cand_verts = set()
                for edge in board.get_cell_edges(r, c):
                    if edge in drawn or edge in unallowed:
                        continue
                    t, er, ec = edge
                    cand_verts.add((er, ec))
                    cand_verts.add((er, ec + 1) if t == 'h' else (er + 1, ec))
 
                # Se não há nenhuma aresta livre para esta célula, é impossível satisfazê-la.
                if not cand_verts:
                    return True
 
                unsatisfied.append(cand_verts)
 
        # Se não há células insatisfeitas, está tudo bem.
        if not unsatisfied:
            return False
 
        # Se há células insatisfeitas mas não há pontas soltas, o loop está fechado
        # e já não pode crescer — essas células nunca serão satisfeitas.
        if not loose_ends:
            return True
 
        # BFS a partir das pontas soltas, expandindo pelos vértices alcançáveis
        # através de arestas não proibidas. Verificamos em cada passo se já
        # cobrimos todas as células insatisfeitas.
        reachable = set(loose_ends)
        queue = list(loose_ends)
        remaining = len(unsatisfied)
        covered = [False] * len(unsatisfied)
 
        # Verificar logo à partida se alguma ponta solta já toca numa célula insatisfeita.
        for i, cand in enumerate(unsatisfied):
            if not cand.isdisjoint(reachable):
                covered[i] = True
                remaining -= 1
        if remaining == 0:
            return False
 
        idx = 0
        while idx < len(queue):
            vr, vc = queue[idx]
            idx += 1
 
            # Expandir para os vértices vizinhos via arestas disponíveis.
            for edge in (('h', vr, vc), ('h', vr, vc - 1), ('v', vr, vc), ('v', vr - 1, vc)):
                if edge not in all_edges or edge in unallowed:
                    continue
 
                t, er, ec = edge
                # O outro vértice desta aresta (o que não é o atual).
                other = (er, ec + 1) if t == 'h' else (er + 1, ec)
                nb = other if other != (vr, vc) else (er, ec)
 
                if nb in reachable:
                    continue
 
                reachable.add(nb)
                queue.append(nb)
 
                for i, cand in enumerate(unsatisfied):
                    if not covered[i] and nb in cand:
                        covered[i] = True
                        remaining -= 1
                        if remaining == 0:
                            return False
 
        # Ficaram células que o BFS não conseguiu alcançar.
        return True
 
    def goal_test(self, state: SlitherlinkState):
        """
        Verifica se o estado atual é a solução final do puzzle.
        Para ser solução, tem de satisfazer três condições:
          1. Todas as células numeradas têm exatamente o número certo de arestas ativas.
          2. Todos os vértices tocados têm exatamente grau 2 (loop sem pontas soltas).
          3. O loop é único — não existem sub-loops desconectados.
        """
        board = state.board
 
        # Otimização rápida: se nenhum loop foi fechado, nem vale a pena verificar.
        if not board.potential_loop_closed:
            return False
 
        if not board.all_drawn_edges:
            return False
 
        # Teste 1: Todas as células numeradas satisfeitas.
        for r in range(board.rows):
            for c in range(board.cols):
                cell_value = board.board[r][c]
                if cell_value == "." or cell_value == -1:
                    continue
                if board.get_active_edges(r, c) != int(cell_value):
                    return False
 
        # Construir lista de adjacência a partir das arestas desenhadas.
        # Usamos isto tanto para verificar graus como para o BFS de conectividade.
        adj = {}
        for edge in board.all_drawn_edges:
            v1, v2 = board.get_edge_vertices(edge)
            adj.setdefault(v1, []).append(v2)
            adj.setdefault(v2, []).append(v1)
 
        # Teste 2: Todos os vértices no loop têm grau exatamente 2.
        for v, neighbors in adj.items():
            if len(neighbors) != 2:
                return False  # ponta solta (grau 1) ou cruzamento (grau > 2)
 
        # Teste 3: O loop é um único ciclo fechado, sem fragmentos separados.
        # Fazemos BFS a partir de um vértice qualquer e vemos se chegamos a todos.
        start = next(iter(adj))
        visited = set()
        queue = [start]
        while queue:
            curr = queue.pop()
            if curr in visited:
                continue
            visited.add(curr)
            for neighbor in adj[curr]:
                if neighbor not in visited:
                    queue.append(neighbor)
 
        if len(visited) != len(adj):
            return False  # existem ciclos separados
 
        # Passou em tudo — é a solução!
        state.board.forbid_edges(state.board.global_forbidden)
        state.board.draw_edges(state.board.global_drawn)
        return True

    def h(self, node) -> float:
        """
        Função heurística para algoritmos informados (RBFS, Greedy, A*).
        Estima o custo restante para chegar à solução. Valores menores = melhor.
        """
        board = node.state.board
        drawn_edges = board.all_drawn_edges
        
        cell_active = {}
        degree = {}
        
        # 1. Contagem otimizada num único ciclo O(E)
        for t, r, c in drawn_edges:
            v1 = (r, c)
            v2 = (r, c + 1) if t == 'h' else (r + 1, c)
            degree[v1] = degree.get(v1, 0) + 1
            degree[v2] = degree.get(v2, 0) + 1
            
            if t == 'h':
                if r < board.rows: 
                    cell_active[(r, c)] = cell_active.get((r, c), 0) + 1
                if r - 1 >= 0: 
                    cell_active[(r-1, c)] = cell_active.get((r-1, c), 0) + 1
            else:
                if c < board.cols: 
                    cell_active[(r, c)] = cell_active.get((r, c), 0) + 1
                if c - 1 >= 0: 
                    cell_active[(r, c-1)] = cell_active.get((r, c-1), 0) + 1

        missing_edges_estimate = 0
        
        # 2. Avaliação de Dicas (Custo de Células)
        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                # No teu código, células vazias podem ser "." ou -1.
                if hint == -1 or hint == ".": 
                    continue
                
                hint_val = int(hint)
                active = cell_active.get((r, c), 0)
                missing = hint_val - active
                
                # O ConstraintPropagator já deve impedir isto, mas serve de barreira de segurança
                if missing < 0:
                    return float('inf') 
                
                missing_edges_estimate += missing
                
        loose_ends = []
        
        # 3. Avaliação de Vértices
        for v, deg in degree.items():
            if deg > 2:
                return float('inf') # Barreira de segurança contra cruzamentos
            elif deg == 1:
                loose_ends.append(v)
                
        # 4. Fecho Prematuro (Safety net)
        if len(loose_ends) == 0 and len(drawn_edges) > 0 and missing_edges_estimate > 0:
            return float('inf')
            
        # 5. Cálculo Heurístico Base
        heuristic_value = float(missing_edges_estimate)
        
        # 6. Avaliação Topológica Avançada (O segredo do Greedy/RBFS)
        if len(loose_ends) == 2:
            # UM segmento único no tabuleiro. É o comportamento ideal!
            # Calculamos a distância Manhattan entre as pontas.
            # O algoritmo vai preferir jogadas que aproximem as pontas soltas para fechar o loop.
            v1, v2 = loose_ends[0], loose_ends[1]
            manhattan = abs(v1[0] - v2[0]) + abs(v1[1] - v2[1])
            heuristic_value += (manhattan * 0.1) 
            
        elif len(loose_ends) > 2:
            # Múltiplos segmentos soltos.
            # PENALIZAÇÃO EXTREMA: força o algoritmo a ligar as pontas soltas que 
            # já existem em vez de desenhar linhas isoladas noutros lados do tabuleiro.
            heuristic_value += len(loose_ends) * 100 
            
        return heuristic_value



if __name__ == "__main__":
    board = Board.parse_instance()
    problem = Slitherlink(board)
    solution_node = depth_first_tree_search(problem)
    solved_board = solution_node.state.board
    print(solved_board.print())
