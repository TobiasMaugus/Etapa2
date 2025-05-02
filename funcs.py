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

def calcula_custos_entre_tarefas(tarefas, matriz_distancias, custos_passados):
    custos = {}
    for i, t1 in enumerate(tarefas):
        for j, t2 in enumerate(tarefas):
            if i == j:
                continue
            origem_t1 = t1['destino'] if t1['tipo'] != 'vertice' else t1['origem']
            destino_t2 = t2['origem']

            # Verificar o custo de serviço apenas para a primeira visita
            if (origem_t1, destino_t2) not in custos_passados:
                custo_servico = t1['custo_servico'] + t2['custo_servico']
            else:
                custo_servico = 0  # Não cobramos s_cost na segunda visita

            custo = matriz_distancias[origem_t1][destino_t2] + custo_servico
            custos[(i, j)] = custo
            custos_passados.add((origem_t1, destino_t2))
    
    return custos

def ordenar_savings(savings):
    """Ordena os savings de maior para menor (ordem decrescente)."""
    return sorted(savings, key=lambda x: x[1], reverse=True)

def calcula_savings(tarefas, custos_entre_tarefas, matriz_distancias, deposito, custos_passados, capacidade_max):
    savings = []
    for i, t1 in enumerate(tarefas):
        for j, t2 in enumerate(tarefas):
            if i >= j:
                continue

            # Verificar a capacidade antes de calcular savings
            if (t1['demanda'] + t2['demanda']) > capacidade_max:
                continue  # Ignora savings onde a fusão das rotas excede a capacidade

            custo_i0 = matriz_distancias[deposito][t1['origem']]
            custo_0j = matriz_distancias[t2['destino']][deposito] if t2['tipo'] != 'vertice' else matriz_distancias[t2['origem']][deposito]
            saving = custo_i0 + custo_0j - custos_entre_tarefas[(i, j)]
            savings.append(((i, j), saving))

    savings_ordenados = ordenar_savings(savings)  # Chama a função de ordenação

    return savings_ordenados

def inicializa_rotas(tarefas, num_vehicles, depot_node, capacity):
    rotas = []

    if num_vehicles == -1:
        # Uma rota por tarefa, mas verificando a capacidade
        for tarefa in tarefas:
            if tarefa['demanda'] > capacity:
                continue  # Ignora tarefas cuja demanda excede a capacidade do veículo
            rota = {
                'tarefas': [tarefas.index(tarefa)],
                'demanda': tarefa['demanda'],
                'rota_completa': [depot_node, tarefa['origem'], tarefa['destino'], depot_node]
            }
            rotas.append(rota)
    else:
        # Inicializa uma rota para cada veículo, inicialmente vazia
        for i in range(num_vehicles):
            rotas.append({
                'tarefas': [],
                'demanda': 0,
                'rota_completa': [depot_node],
            })

        for idx, tarefa in enumerate(tarefas):
            if tarefa['demanda'] > capacity:
                continue  # Ignora tarefas cuja demanda excede a capacidade do veículo

            rota_inicial = rotas[idx % num_vehicles]
            if rota_inicial['demanda'] + tarefa['demanda'] <= capacity:
                rota_inicial['tarefas'].append(idx)
                rota_inicial['demanda'] += tarefa['demanda']
                rota_inicial['rota_completa'].append(tarefa['origem'])
                rota_inicial['rota_completa'].append(tarefa['destino'])

    return rotas

def pode_fundir_rotas(rota_i, rota_j, capacidade_max):
    """Verifica se duas rotas podem ser fundidas sem ultrapassar a capacidade do veículo."""
    return (rota_i['demanda'] + rota_j['demanda']) <= capacidade_max

def funde_rotas(rota_i, rota_j):
    """Funde duas rotas, atualizando a demanda e a sequência de tarefas."""
    nova_rota = {
        'tarefas': rota_i['tarefas'] + rota_j['tarefas'],
        'demanda': rota_i['demanda'] + rota_j['demanda'],
        'rota_completa': rota_i['rota_completa'][:-1] + rota_j['rota_completa'][1:],  # Junta as rotas
    }
    return nova_rota

def aplica_savings(rotas, savings, capacidade_max):
    """Aplica os savings, fundindo as rotas que podem ser combinadas sem exceder a capacidade."""
    for (i, j), _ in savings:
        rota_i = next((r for r in rotas if r['tarefas'][-1] == i), None)
        rota_j = next((r for r in rotas if r['tarefas'][0] == j), None)

        if rota_i and rota_j and rota_i != rota_j:
            if pode_fundir_rotas(rota_i, rota_j, capacidade_max):
                nova_rota = funde_rotas(rota_i, rota_j)
                rotas.remove(rota_i)
                rotas.remove(rota_j)
                rotas.append(nova_rota)
    return rotas

def orquestrar_clarke_wright(required_edges, required_arcs, required_vertices, depot_node, num_vehicles, capacity, matriz_distancias):
    custos_passados = set()  # Guarda os arcos/arestas/vertice já visitados
    # Extraindo as tarefas
    tarefas = extrair_tarefas(required_edges, required_arcs, required_vertices)
    
    # Calculando os custos entre as tarefas
    custos_entre_tarefas = calcula_custos_entre_tarefas(tarefas, matriz_distancias, custos_passados)
    
    # Inicializando rotas vazias com o número de veículos e o depósito
    rotas = inicializa_rotas(tarefas, num_vehicles, depot_node, capacity)
    
    # Calculando savings e ordenando
    savings = calcula_savings(tarefas, custos_entre_tarefas, matriz_distancias, depot_node, custos_passados, capacidade_max=capacity)
    savings_ordenados = ordenar_savings(savings)
    
    # Fase de construção - aplicando as fusões
    rotas = aplica_savings(rotas, savings_ordenados, capacity)
    
    # Resultado final com as rotas
    return rotas



def mostrar_caminho(rotas, tarefas):
    for i, rota in enumerate(rotas):
        caminho = []
        for tarefa_idx in rota['tarefas']:
            tarefa = tarefas[tarefa_idx]
            if tarefa['tipo'] == 'edge':
                caminho.append(f"Aresta: {tarefa['origem']} -> {tarefa['destino']} (Demanda: {tarefa['demanda']})")
            elif tarefa['tipo'] == 'arc':
                caminho.append(f"Arco: {tarefa['origem']} -> {tarefa['destino']} (Demanda: {tarefa['demanda']})")
            elif tarefa['tipo'] == 'vertice':
                caminho.append(f"Vértice: {tarefa['origem']} (Demanda: {tarefa['demanda']})")
        print(f"Viagem {i+1}: {' -> '.join(caminho)}")
