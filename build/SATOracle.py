# como pensado em pensamento com o gemini pro (perguntei e ele verificou se seria uma boa
#forma de organizar o codigo, o ConstraintPropagator vai receber uma board, e para um tal
#estado verificar as obrigatorias e proibidas acoes seguintes)

#PODE E TEM DE SER PESADAMENTE OPTIMIZADO, O PROPAGATE DA RUN A BOARD TODA, DEVE HAVER MANEIRA MAIS RAPIDA
#DE ITERAR APENAS ONDE PRECISO

class ConstraintPropagator:
    def __init__(self, Board):
        self.Board = Board

        #vamos guardar aqui as celulas preenchidas recentemente
        self.completed_3 = set()
        self.completed_2 = set()
        self.completed_1 = set()

        #vamos guardar aqui as celulas forbidden ou mandatory neste loop
        #poderiamos dar backtrack de recently_changed_edges, mas parece ser 
        #mais eficiente para este proposito guardar logo separado 
        self.mandatory_drawn = set()
        self.forbidden_drawn = set()

    def propagate_cells_info(self):
        """get todas as acompleted cells"""
        return (self.completed_3, self.completed_2, self.completed_1)

    def propagate_edges_info(self):
        """get todas as drawn edges"""
        return (self.mandatory_drawn, self.forbidden_drawn)

    def apply_vertex_local_constraints(self, v_coords, v_conn):
        """esta funcao aplica logica as edges locais a um vertex, de forma
        a decidir que edges sao obrigatorias desenhar, proibidas, ou permitidas(
        candidatas a acao)"""
        mandatory = set()
        unallowed = set()
        allowed = set()
        (prohibited, drawn , undrawn) = self.Board.get_edges_around_vertex(v_coords)
        total_edges = len(prohibited) + len(drawn) + len(undrawn) #em cantos pode ser 3 ou 2

        #Hard Constraint
        if v_conn > 2:
            return False
        
        if v_conn == 1:
            #se nao ha para onde desenhar, e false
            if len(undrawn) == 0:
                return False
            #if there is only 1 undrawn/ possible to draw
            elif len(undrawn) == 1:
                edge = list(undrawn)[0]
                # e vai de acordo com regra de celulas
                if self.Board.is_action_possible(edge):
                    mandatory.add(edge) #e obrigatoria
                else:
                    return False #senao a unica possivel e proibida, entao e dead-end
            elif len(undrawn) >= 2: 
                #para todas as edges possiveis segundo regras de vertices
                for edge in undrawn:
                    #se for de acordo com regra de celulas
                    if self.Board.is_action_possible(edge):
                        allowed.add(edge) #permitida
                    else:
                        unallowed.add(edge) #senao e proibida
        elif v_conn == 2:
            #all around edges are prohibited
            unallowed.update(undrawn)
        elif v_conn == 0:
            #conn==0, ou seja, 0 drawn, logo se 1 undrawn, resto e prohibited
            if len(undrawn) == 1:
                edge = list(undrawn)[0]
                unallowed.add(edge)

        return (unallowed, mandatory, allowed)

    def apply_cell_local_constraints(self, r, c, cell_value):
        """
        Aplica a lógica do Slitherlink às células.
        Agora também previne loops 1x1 em células vazias!
        """
        mandatory = set()
        unallowed = set()
        
        edges = self.Board.get_cell_edges(r, c)
        
        drawn = [e for e in edges if e in self.Board.all_drawn_edges]
        prohibited = [e for e in edges if e in self.Board.all_forbidden_edges]
        undrawn = [e for e in edges if e not in drawn and e not in prohibited]
        
        #se tem 3 arestas desenhadas, proibir a proxima
        if len(drawn) == 3: unallowed.update(undrawn)
        #se tem 4 arestas desenhadas, board is dead end
        if len(drawn) == 4: return False 
            
        # celula vazia nao tem regras de restricoes, exceto 1x1 loop
        if cell_value == "." or cell_value == -1:
            return (unallowed, mandatory)
            
        
        # se desenhamos mais do que permitido / permitidas sao menos do que necessario
        #entao board is dead end
        if len(drawn) > cell_value or len(drawn) + len(undrawn) < cell_value:
            return False
            
        #se  numero desenhadas vai de acordo com celula, proibir restantes
        if len(drawn) == cell_value:
            unallowed.update(undrawn)
            if cell_value == 3: self.completed_3.add((r, c))
            elif cell_value == 2: self.completed_2.add((r, c))
            elif cell_value == 1: self.completed_1.add((r, c))
            
        #se todas as perimitidas somarem cell value, temos de desenhar todas
        if len(drawn) + len(undrawn) == cell_value:
            mandatory.update(undrawn)

            #como completa uma celula, adicionamos ao vetor aqui.
            if cell_value == 3: self.completed_3.add((r, c))
            elif cell_value == 2: self.completed_2.add((r, c))
            elif cell_value == 1: self.completed_1.add((r, c))
            
        return (unallowed, mandatory)
    
    #constraints logics
    def propagate(self):
        """propaga as edges proibidas, obrigatorias
        e as opcionais (acoes possiveis). E um loop que apenas termina
        quando nao ha alteracoes, isto pois alterar regras num vertex 2, pode 
        alterar as edges de um vertex 1, processado apriori, entao temos de voltar
        ao 1 para processar de novo"""

        mandatory = set()
        unallowed = set()
        allowed = set()

        changed = True
        #enquanto houver alteracoes, aplicar
        while changed:
            mandatory = set()
            unallowed = set()

            #get relevant vertices
            relevant_edges = self.Board.recently_changed_edges
            if not relevant_edges:
                break
            relevant_vertices = {v for edge in relevant_edges for v in self.Board.get_edge_vertices(edge)}
            relevant_cells = {cell for edge in relevant_edges for cell in self.Board.cells_adjacent_to_edge(edge)}
            #print(relevant_cells)

            #SUPER IMPORTANTE. DA RESET A RECENTLY CHANGED EDGES DE FORMA A USARMOS AS ANTERIORES,
            # MAS PARA O PROXIO LOOP USAMOS APENAS AS NOVAS ALTERACOES, ASSIM O PROCESSO EM CASCATA
            # USA APENAS AS EDGES, VERTICES, AND CELLS, EXTRITAMENTE NECESSARIAS
            self.Board.recently_changed_edges = set()
            

            # LOGIAC DE VERTICES
            for vertice in relevant_vertices:
                #get vertex degree
                v_degree = self.Board.vertices_deg[vertice]
                #apply vertex local constraints
                res1 = self.apply_vertex_local_constraints(vertice, v_degree)
                #apply and save logic
                if res1 is False: return False
                (un, mand, allo) = res1
                unallowed.update(un)
                mandatory.update(mand)
                allowed.update(allo)
            
            # LOGICA DE CELULAS
            for cell in relevant_cells:
                r, c = cell
                cell_val = self.Board.board[r][c]
                if cell_val != "." and cell_val != -1:
                    res_cell = self.apply_cell_local_constraints(r, c, int(cell_val))
                    if res_cell is False: return False # Regra quebrada!
                    
                    unallowed.update(res_cell[0])
                    mandatory.update(res_cell[1])

            #se ha uma edge amba obrigatoria e proibida, board esta estragada, beco sem saida
            if not mandatory.isdisjoint(unallowed):
                return False
            
            #desenhar obrigatorios e proibidos  
            self.Board.recently_changed_edges = set()
            if mandatory:
                self.Board.draw_edges(mandatory)
                self.mandatory_drawn.update(mandatory) #gaurdar todas as alteracoes 
            if unallowed:
                self.Board.forbid_edges(unallowed) # Sem isto, não há efeito cascata!
                self.forbidden_drawn.update(unallowed) #guardar todas as alteracoes

            #manter as allowed edges. em cada iteracao mantemos as allowed edges, num proximo 
            #ciclo, uma allowed edege pode passar a mandatory ou unallowed, nesse caso, removemos
            #de allowed. No fim, temos todas as allowed edges no estadoc ompletamente propagado
            allowed -= mandatory
            allowed -= unallowed

            #se nao foi adicionado obrigatorios ou proibidos, a board fica igual e acabamos o loop
            if len(mandatory) == 0 and len(unallowed) == 0:
                changed = False
        
        #se deu trigger a flag, entao um loop fechou em algum sitio
        if self.Board.potential_loop_closed == True:
            #se loop for prematuro, board is dead end
            if self._has_premature_loop(): return False

        return allowed

    def _has_premature_loop(self) -> bool:
        """
        Verifica se existe algum sub-loop (ciclo fechado) na board.
        Utiliza um pool de arestas (que se vai consumindo) e a função get_edges_around_vertex.
        """

        board = self.Board
        drawn = board.all_drawn_edges

        # nao ha arestas, nao ha loops
        if not drawn: return False

        # arestas nao visitadas. vai diminuindo a medida que percorremos edges
        # objetivo e que cada edge seja percorrida apenas uma vez
        unvisited = set(drawn)

        #OUTTER LOOP: starting edge
        while unvisited:
            # obter edge e remover de unvisited edges
            start_edge = unvisited.pop() 
            
            #curr_edge vai sendo alterado ao longo do loop. dar setup curr = start
            curr_edge = start_edge
            _, curr_v = board.get_edge_vertices(curr_edge) 
            
            loop_size = 1
            #INNER LOOP: percorrer edges adjacentes, comeca em starting edge
            while True:
                # obter drawn edges a volta do curr_v, e transformar em indexes para aceder melhor
                _, drawn_at_v, _ = board.get_edges_around_vertex(curr_v)
                v_edges = list(drawn_at_v)

                # if v_deg nao 2, entao e loose edge, e loop naot em por onde continuar
                if len(v_edges) != 2: break 

                # passou, vertice tem 2 edges. queremos a edge que nao e a atual
                if v_edges[0] != curr_edge: next_edge = v_edges[0]
                else:  next_edge = v_edges[1]

                # se fecharmos um loop (voltamos a inicial), verificamos se e loop global
                #se
                if next_edge == start_edge: return loop_size != len(drawn)

                # se next edge ja tiver sido verificada, 
                if next_edge not in unvisited: break

                # remover esta next edge das nao visitadas.
                unvisited.remove(next_edge)
                
                # Avançar um passo
                curr_edge = next_edge
                loop_size += 1

                # Atualizar o vértice atual para a outra ponta da aresta que acabámos de pisar
                v1, v2 = board.get_edge_vertices(curr_edge)
                curr_v = v1 if v1 != curr_v else v2

        return False