def clark_wright_savings_with_exclusivity(customers, arcs, required_arcs):
    """
    Algoritmo de Clarke-Wright Savings modificado para garantir a exclusividade de arcos requeridos
    nas rotas.
    
    :param customers: Lista de clientes com as informações de demanda e localização.
    :param arcs: Lista de arcos (aresta de origem-destino) que podem ser usados nas rotas.
    :param required_arcs: Lista de arcos requeridos que não podem ser compartilhados entre rotas.
    :return: Lista de rotas combinadas, com a garantia de exclusividade de arcos requeridos.
    """
    # Inicializa as rotas
    routes = []
    for customer in customers:
        routes.append([customer])  # Cada cliente começa com uma rota individual
    
    # Função para calcular a economia de combinar duas rotas
    def savings(route1, route2):
        # Calcula a economia da junção das duas rotas (como no algoritmo original)
        # Aqui você pode usar a distância entre os pontos de origem e destino das rotas
        return calculate_savings(route1, route2)

    # Função para verificar se algum arco requerido é compartilhado entre duas rotas
    def check_required_arc_exclusivity(route1, route2):
        """
        Verifica se algum arco requerido está presente nas duas rotas.
        Retorna True se algum arco requerido for compartilhado, False caso contrário.
        """
        for arc in required_arcs:
            # Verifica se o arco requerido aparece em ambas as rotas
            if arc in route1 and arc in route2:
                return True
        return False

    # Combina as rotas de maneira iterativa, respeitando a exclusividade dos arcos requeridos
    combined_routes = []
    while len(routes) > 1:
        best_savings = -float('inf')
        best_combination = None

        # Encontra a melhor combinação de rotas com a maior economia
        for i in range(len(routes)):
            for j in range(i + 1, len(routes)):
                if check_required_arc_exclusivity(routes[i], routes[j]):
                    continue  # Não combina se houver exclusividade violada

                # Se a combinação for válida, calcula a economia
                current_savings = savings(routes[i], routes[j])
                if current_savings > best_savings:
                    best_savings = current_savings
                    best_combination = (i, j)

        # Realiza a combinação da melhor opção encontrada
        if best_combination:
            route1, route2 = best_combination
            new_route = routes[route1] + routes[route2]
            routes = [r for idx, r in enumerate(routes) if idx not in best_combination]  # Remove as rotas combinadas
            routes.append(new_route)  # Adiciona a nova rota combinada

    # A última rota remanescente será a solução final
    return routes[0]


def calculate_savings(route1, route2):
    """
    Calcula a economia de combinar duas rotas.
    A economia é a diferença de custo de duas rotas separadas e uma rota combinada.
    
    :param route1: Primeira rota.
    :param route2: Segunda rota.
    :return: A economia da combinação das rotas.
    """
    # Exemplo de cálculo simples de economia
    # Substitua pelo cálculo real, dependendo do seu modelo de custo.
    return random.random()  # Exemplo fictício; substituir pelo cálculo real.


# Exemplo de uso:
customers = [
    {'id': 1, 'location': (1, 2), 'demand': 10},
    {'id': 2, 'location': (2, 3), 'demand': 15},
    # Adicione outros clientes conforme necessário
]

arcs = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    # Adicione outros arcos disponíveis conforme necessário
]

required_arcs = [
    (1, 2),  # Este arco é requerido e deve ser exclusivo para uma rota
    # Adicione outros arcos requeridos conforme necessário
]

# Roda o algoritmo
routes = clark_wright_savings_with_exclusivity(customers, arcs, required_arcs)
print("Rotas resultantes:", routes)
