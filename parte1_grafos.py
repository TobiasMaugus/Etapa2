import heapq

def dijkstra(start_node, edges, arcs, vertices):
    vertices_ids = {v if isinstance(v, int) else v[0] for v in vertices}
    distancias = {v: float('inf') for v in vertices_ids}
    distancias[start_node] = 0
    predecessores = {v: None for v in vertices_ids}
    heap = [(0, start_node)]

    todos = set()
    for (u, v), t_cost in edges:
        todos.add((u, v, t_cost, False)) #aresta
    for (u, v), t_cost in arcs:
        todos.add((u, v, t_cost, True)) #arco

    while heap:
        dist_atual, current_node = heapq.heappop(heap)
        if dist_atual > distancias[current_node]:
            continue

        for u, v, t_cost, is_arc in todos:
            if u == current_node:
                viz = v
            elif not is_arc and v == current_node:
                viz = u
            else:
                continue

            nova_dist = dist_atual + t_cost
            if nova_dist < distancias[viz]:
                distancias[viz] = nova_dist
                predecessores[viz] = current_node
                heapq.heappush(heap, (nova_dist, viz))

    return distancias, predecessores

def matriz_menores_distancias(vertices, edges, arcs):
     matriz_distancias = {}
 
     for v in vertices:
         distancias, _ = dijkstra(v, edges, arcs, vertices)  #calcula distancias a partir de v
         matriz_distancias[v] = {u: distancias.get(u, float('inf')) for u in vertices}  
 
     return matriz_distancias

def matriz_predecessores(vertices, edges, arcs):
    matriz_predecessores = {}
    for v in vertices:
        _, predecessores = dijkstra(v, edges, arcs, vertices)
        matriz_predecessores[v] = {u: predecessores.get(u, None) for u in vertices}  

    return matriz_predecessores

def caminho_mais_curto_com_matriz(predecessores, start_node, end_node):
    caminho = []
    current_node = end_node
    
    while current_node is not None:
        caminho.insert(0, current_node)
        current_node = predecessores[start_node].get(current_node) 
    
    return caminho
