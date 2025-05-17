import heapq
import random
from pathlib import Path

def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    vertices = set()
    edges = set()
    arcs = set()
    required_vertices = set()
    required_edges = set()
    required_arcs = set()
    section = None

    num_vehicles = None
    capacity = None
    depot_node = None
    optimal_value = None

    for line in lines:
        line = line.strip()

        if line.startswith("#Vehicles:"):
            try:
                num_vehicles = int(line.split(":")[1].strip())
            except ValueError:
                num_vehicles = None
            continue
        elif line.startswith("Capacity:"):
            try:
                capacity = int(line.split(":")[1].strip())
            except ValueError:
                capacity = None
            continue
        elif line.startswith("Depot Node:"):
            try:
                depot_node = int(line.split(":")[1].strip())
            except ValueError:
                depot_node = None
            continue
        elif line.startswith("Optimal value:"):
            try:
                optimal_value = int(line.split(":")[1].strip())
            except ValueError:
                optimal_value = None
            continue


        if line.startswith("ReN."):
            section = "ReN"
            continue
        elif line.startswith("ReE."):
            section = "ReE"
            continue
        elif line.startswith("EDGE"):
            section = "EDGE"
            continue
        elif line.startswith("ReA."):
            section = "ReA"
            continue
        elif line.startswith("ARC"):
            section = "ARC"
            continue
        elif line.startswith(("Based", "the", "based", "-1")):
            section = "Err"
            continue

        if line and section:
            parts = line.split("\t")
            if section == "ReN":
                try:
                    node = int(parts[0].replace("N", ""))
                    demand = int(parts[1])
                    s_cost = int(parts[2])
                    aux = (node, (demand, s_cost))
                    required_vertices.add(aux) 
                    vertices.add(node)  
                except ValueError:
                    continue  

            elif section in ["ReE", "EDGE"]:
                try:
                    u, v = int(parts[1]), int(parts[2]) 
                    vertices.update([u, v]) #vertices q nao estavam em ReN
                    edge = (min(u, v), max(u, v)) 
                    t_cost = int(parts[3]) 
                    edges.add((edge, (t_cost))) 

                    if section == "ReE":
                        demand = int(parts[4]) 
                        s_cost = int(parts[5]) 
                        required_edges.add((edge, (t_cost, demand, s_cost)))
                except ValueError:
                    continue

            elif section in ["ReA", "ARC"]:
                try:
                    u, v = int(parts[1]), int(parts[2])
                    vertices.update([u, v]) #vertices q nao estavam em ReN
                    arc = (u, v)
                    t_cost = int(parts[3]) 
                    arcs.add((arc, (t_cost)))
                    if section == "ReA":
                        demand = int(parts[4]) 
                        s_cost = int(parts[5]) 
                        required_arcs.add((arc, (t_cost, demand, s_cost)))
                except ValueError:
                    continue

            elif section == "Err":
                continue

    return vertices, edges, arcs, required_vertices, required_edges, required_arcs, num_vehicles, capacity, depot_node, optimal_value



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


def extrair_tarefas(required_edges, required_arcs, required_vertices):
    tarefas = []
    
    # Adicionando tarefas de arestas requeridas (ER)
    for (u, v), (t_cost, demand, s_cost) in required_edges:
        tarefas.append({'tipo': 'edge', 'origem': u, 'destino': v, 'demanda': demand, 'custo_servico': s_cost, 't_cost': t_cost})
        
    # Adicionando tarefas de arcos requeridos (AR)
    for (u, v), (t_cost, demand, s_cost) in required_arcs:
        tarefas.append({'tipo': 'arc', 'origem': u, 'destino': v, 'demanda': demand, 'custo_servico': s_cost, 't_cost': t_cost})
    
    # Adicionando tarefas de vértices requeridos (ReN)
    for node, (demand, s_cost) in required_vertices:
        tarefas.append({'tipo': 'vertice', 'origem': node, 'destino': node, 'demanda': demand, 'custo_servico': s_cost, 't_cost': 0})
    
    return tarefas

def calcula_custos_entre_tarefas(tarefas, matriz_distancias):
    custos = {}
    for i, t1 in enumerate(tarefas):
        for j, t2 in enumerate(tarefas):
            if i == j:
                continue
            origem_t1 = t1['destino'] if t1['tipo'] != 'vertice' else t1['origem']
            destino_t2 = t2['origem']
            custo = matriz_distancias[origem_t1][destino_t2] + t1['custo_servico'] + t2['custo_servico']
            custos[(i, j)] = custo
    return custos

def construir_rota_completa(tarefas, tarefa_indices, depot_node, matriz_predecessores):
    rota = [depot_node]
    for i, idx in enumerate(tarefa_indices):
        tarefa = tarefas[idx]
        origem = tarefa['origem']
        
        if i == 0:
            # Caminho do depósito até o início da primeira tarefa
            rota += caminho_mais_curto_com_matriz(matriz_predecessores, rota[-1], origem)[1:]
        else:
            # Caminho do final da tarefa anterior até início da atual
            anterior = tarefas[tarefa_indices[i - 1]]
            ultimo = anterior['destino'] if anterior['tipo'] != 'vertice' else anterior['origem']
            rota += caminho_mais_curto_com_matriz(matriz_predecessores, ultimo, origem)[1:]

        # Adiciona o deslocamento da tarefa
        if tarefa['tipo'] == 'vertice':
            pass  # vértice não tem deslocamento
        else:
            rota.append(tarefa['destino'])

    # Caminho de volta ao depósito
    ultimo = tarefas[tarefa_indices[-1]]
    fim = ultimo['destino'] if ultimo['tipo'] != 'vertice' else ultimo['origem']
    rota += caminho_mais_curto_com_matriz(matriz_predecessores, fim, depot_node)[1:]
    return rota


def ordenar_savings(savings, rng=None):
    if rng is not None:
        rng.shuffle(savings)
    else:
        savings = sorted(savings, key=lambda x: x[1], reverse=True)
    return savings


def calcula_savings(tarefas, custos_entre_tarefas, matriz_distancias, deposito, capacidade_max):
    savings = []
    for i, t1 in enumerate(tarefas):
        for j, t2 in enumerate(tarefas):
            if i >= j:
                continue

            if (t1['demanda'] + t2['demanda']) > capacidade_max:
                continue

            custo_i0 = matriz_distancias[deposito][t1['origem']]
            custo_0j = matriz_distancias[t2['destino']][deposito] if t2['tipo'] != 'vertice' else matriz_distancias[t2['origem']][deposito]
            saving = custo_i0 + custo_0j - custos_entre_tarefas[(i, j)]
            savings.append(((t1['id'], t2['id']), saving))

    return savings


def inicializa_rotas(tarefas, num_vehicles, depot_node, capacity, matriz_predecessores):
    rotas = []

    if num_vehicles == -1:
        for tarefa in tarefas:
            if tarefa['demanda'] > capacity:
                continue
            rota_completa = construir_rota_completa(tarefas, [tarefa['id']], depot_node, matriz_predecessores)
            rotas.append({
                'tarefas': [tarefa['id']],
                'demanda': tarefa['demanda'],
                'rota_completa': rota_completa
            })
    else:
        for i in range(num_vehicles):
            rotas.append({'tarefas': [], 'demanda': 0, 'rota_completa': [depot_node]})
        for idx, tarefa in enumerate(tarefas):
            if tarefa['demanda'] > capacity:
                continue
            rota = rotas[idx % num_vehicles]
            if rota['demanda'] + tarefa['demanda'] <= capacity:
                rota['tarefas'].append(tarefa['id'])
                rota['demanda'] += tarefa['demanda']
                rota['rota_completa'] = construir_rota_completa(tarefas, rota['tarefas'], depot_node, matriz_predecessores)

    return rotas


def pode_fundir_rotas(rota_i, rota_j, capacidade_max):
    return (rota_i['demanda'] + rota_j['demanda']) <= capacidade_max


def funde_rotas(rota_i, rota_j, tarefas_dict, depot_node, matriz_predecessores):
    nova_tarefas = rota_i['tarefas'] + rota_j['tarefas']
    nova_rota = {
        'tarefas': nova_tarefas,
        'demanda': rota_i['demanda'] + rota_j['demanda'],
        'rota_completa': construir_rota_completa(tarefas_dict, nova_tarefas, depot_node, matriz_predecessores)
    }
    return nova_rota


def aplica_savings(rotas, savings, capacidade_max, tarefas_dict, depot_node, matriz_predecessores):
    for (id_i, id_j), _ in savings:
        rota_i = next((r for r in rotas if r['tarefas'] and r['tarefas'][-1] == id_i), None)
        rota_j = next((r for r in rotas if r['tarefas'] and r['tarefas'][0] == id_j), None)

        if rota_i and rota_j and rota_i != rota_j:
            if pode_fundir_rotas(rota_i, rota_j, capacidade_max):
                nova_rota = funde_rotas(rota_i, rota_j, tarefas_dict, depot_node, matriz_predecessores)
                rotas.remove(rota_i)
                rotas.remove(rota_j)
                rotas.append(nova_rota)
    return rotas


def orquestrar_clarke_wright(required_edges, required_arcs, required_vertices, depot_node, num_vehicles, capacity, matriz_distancias, matriz_predecessores, seed=None, shuffle=False):
    rng = random.Random(seed) if seed is not None else None

    tarefas = extrair_tarefas(required_edges, required_arcs, required_vertices)
    for i, t in enumerate(tarefas):
        t['id'] = i

    if shuffle and rng:
        rng.shuffle(tarefas)

    tarefas_dict = {t['id']: t for t in tarefas}

    custos_entre_tarefas = calcula_custos_entre_tarefas(tarefas, matriz_distancias)
    rotas = inicializa_rotas(tarefas, num_vehicles, depot_node, capacity, matriz_predecessores)
    savings = calcula_savings(tarefas, custos_entre_tarefas, matriz_distancias, depot_node, capacidade_max=capacity)
    savings_ordenados = ordenar_savings(savings, rng=rng)

    rotas = aplica_savings(rotas, savings_ordenados, capacity, tarefas_dict, depot_node, matriz_predecessores)
    return rotas, tarefas



def mostrar_caminho(rotas, tarefas, matriz_distancias):
    for idx, rota in enumerate(rotas):
        print(f"\nRota {idx + 1}:")
        
        # Mostra a sequência de nós visitados
        print("  Caminho completo:", " -> ".join(str(no) for no in rota['rota_completa']))
        
        # Mostra as tarefas realizadas
        print("  Tarefas:")
        for tarefa_idx in rota['tarefas']:
            tarefa = tarefas[tarefa_idx]
            tipo = tarefa['tipo']
            if tipo == 'vertice':
                print(f"    - {tipo} em {tarefa['origem']}, demanda {tarefa['demanda']}")
            else:
                print(f"    - {tipo} de {tarefa['origem']} para {tarefa['destino']}, demanda {tarefa['demanda']}")
        
        # Mostra a demanda total da rota
        print(f"  Demanda total: {rota['demanda']}")
        print(f"  Custo total: {custo_rota_especifica(rota, matriz_distancias)}")

def custo_total_rotas(rotas, matriz_distancias):
    custo_total = 0
    for rota in rotas:
        rota_completa = rota['rota_completa']
        for i in range(len(rota_completa) - 1):
            origem = rota_completa[i]
            destino = rota_completa[i + 1]
            custo_total += matriz_distancias[origem][destino]
    return custo_total

def custo_rota_especifica(rota, matriz_distancias):
    custo_total = 0
    rota_completa = rota['rota_completa']
    
    for i in range(len(rota_completa) - 1):
        origem = rota_completa[i]
        destino = rota_completa[i + 1]
        custo_total += matriz_distancias[origem][destino]
    
    return custo_total


def imprimir_resultados(rotas_finais, tarefas, matriz_distancias, optimal_value=None, custo_melhorado=False):
    # Cálculos antes da melhoria
    custo_solucao = custo_total_rotas(rotas_finais, matriz_distancias)
    
    # Imprime o número de tarefas
    print(f"\n\n⎧ Tarefas que deviam ser feitas: {len(required_arcs)+len(required_edges)+len(required_vertices)}")
    print(f"⎩ Tarefas feitas: {len(tarefas)}")
    print(f"⎧ Capacidade Máxima: {capacity}")
    
    # Maior demanda entre as rotas
    maior_demanda_rota = max(rota['demanda'] for rota in rotas_finais)
    print(f"⎩ Maior demanda total entre as rotas: {maior_demanda_rota}")

    # Exibe o custo total antes da melhoria
    if optimal_value:
        print(f"⎧ Custo total da solução: {custo_solucao}")
        print(f"⎪ Valor ótimo conhecido: {optimal_value}")
        gap = ((custo_solucao - optimal_value) / optimal_value) * 100
        print(f"⎩ Gap percentual em relação ao ótimo: {gap:.2f}%")
    else:
        print(f"- Custo total da solução: {custo_solucao}")

    # Exibe o custo melhorado após a melhoria, se solicitado
    if custo_melhorado:
        custo_melhorado = custo_total_rotas(rotas_finais, matriz_distancias)
        print(f"- Custo melhorado da solução: {custo_melhorado}")
    
    print("\n- Rotas finais encontradas:\n")
    mostrar_caminho(rotas_finais, tarefas, matriz_distancias)


def rodar_varias_vezes(required_edges, required_arcs, required_vertices,
                       depot_node, num_vehicles, capacity,
                       matriz_distancias, matriz_predecessores,
                       num_execucoes=10000, master_seed=None):
    rng = random.Random(master_seed)

    melhor_custo = float('inf')
    melhor_seed = None
    melhor_rotas = None
    melhor_tarefas = None

    for _ in range(num_execucoes):
        seed = rng.randint(0, 1_000_000)
        rotas, tarefas = orquestrar_clarke_wright(
            required_edges, required_arcs, required_vertices,
            depot_node, num_vehicles, capacity,
            matriz_distancias, matriz_predecessores,
            seed=seed, shuffle=True
        )
        custo = custo_total_rotas(rotas, matriz_distancias)

        if custo < melhor_custo:
            melhor_custo = custo
            melhor_seed = seed
            melhor_rotas = rotas
            melhor_tarefas = tarefas

    return melhor_rotas, melhor_seed, melhor_custo


    
file = "Testes/BHW8.dat"
vertices, edges, arcs, required_vertices, required_edges, required_arcs, num_veicles, capacity, depot_node, optimal_value = read_file(file)

matriz_distancias = matriz_menores_distancias(vertices, edges, arcs)
matriz_pred = matriz_predecessores(vertices, edges, arcs)

# --- Rodar versão aleatória múltiplas vezes ---
melhor_rotas, melhor_seed, melhor_custo = rodar_varias_vezes(
    required_edges=required_edges,
    required_arcs=required_arcs,
    required_vertices=required_vertices,
    depot_node=depot_node,
    num_vehicles=num_veicles,
    capacity=capacity,
    matriz_distancias=matriz_distancias,
    matriz_predecessores=matriz_pred,
    num_execucoes=100,             # Ajuste esse número conforme desejar
                                # Escolha uma master seed para reprodutibilidade
)

print(f"\nMelhor resultado para o arquivo: {file}")
print(f"Seed que gerou a melhor solução: {melhor_seed}")
print(f"Custo da melhor solução: {melhor_custo}")

# Extrai tarefas para o imprimir_resultados
tarefas = extrair_tarefas(required_edges, required_arcs, required_vertices)

# Imprime a melhor solução
imprimir_resultados(melhor_rotas, tarefas, matriz_distancias, optimal_value)
