from collections import defaultdict
import heapq

class Graph:
    def __init__(self):
        self.adj = defaultdict(list)
        self.edges = {}
        self.demands = {}  # <-- Adiciona isso

    def add_edge(self, u, v, cost, directed=False):
        self.adj[u].append((v, cost))
        self.edges[(u, v)] = (cost, directed)
        if not directed:
            self.adj[v].append((u, cost))
            self.edges[(v, u)] = (cost, directed)

    def get_demand(self, u, v):
        return self.demands.get((u, v)) or self.demands.get((v, u), 0)


    def dijkstra(self, source, blocked_edges=set()):
        dist = defaultdict(lambda: float('inf'))
        dist[source] = 0
        heap = [(0, source)]
        while heap:
            cost_u, u = heapq.heappop(heap)
            if cost_u > dist[u]:
                continue
            for v, cost_uv in self.adj[u]:
                if (u, v) in blocked_edges or (v, u) in blocked_edges:
                    continue
                alt = dist[u] + cost_uv
                if alt < dist[v]:
                    dist[v] = alt
                    heapq.heappush(heap, (alt, v))
        return dist

    def get_cost(self, u, v):
        return self.edges.get((u, v), (float('inf'), True))[0]

    def is_directed(self, u, v):
        return self.edges.get((u, v), (None, True))[1]





class ClarkeWrightSolver:
    def __init__(self, graph, depot, capacity, required_arcs=None, required_edges=None, required_vertices=None, max_routes=None):
        self.graph = graph
        self.depot = depot
        self.capacity = capacity
        self.max_routes = max_routes

        self.required_arcs = required_arcs or []  # Lista de (u, v, props)
        self.required_edges = required_edges or []  # Lista de ((u,v), props)
        self.required_vertices = required_vertices or {}  # Dict: node -> props

        self.routes = []
        self.arc_to_route = {}  # Para garantir exclusividade
        self.vertex_served = {}  # node -> route id que o atende

    def initial_routes(self):
        # Roteamento para arcos/arestas requeridas
        for u, v, props in self.required_arcs:
            demand = props['demand']
            if demand > self.capacity:
                raise ValueError(f"Tarefa ({u},{v}) excede capacidade.")
            route = {
                'path': [self.depot, u, v, self.depot],
                'load': demand,
                'tasks': {(u, v)},
                'service_vertices': set(),
                'service_cost': props['service_cost'],
                'transport_cost': self.graph.get_cost(self.depot, u) +
                                  props['transport_cost'] +
                                  self.graph.get_cost(v, self.depot),
            }
            self.routes.append(route)
            r_id = len(self.routes) - 1
            self.arc_to_route[(u, v)] = r_id
            if not self.graph.is_directed(u, v):
                self.arc_to_route[(v, u)] = r_id

        for (u, v), props in self.required_edges:
            demand = props['demand']
            if demand > self.capacity:
                raise ValueError(f"Tarefa ({u},{v}) excede capacidade.")
            route = {
                'path': [self.depot, u, v, self.depot],
                'load': demand,
                'tasks': {(u, v), (v, u)},
                'service_vertices': set(),
                'service_cost': props['service_cost'],
                'transport_cost': self.graph.get_cost(self.depot, u) +
                                  props['transport_cost'] +
                                  self.graph.get_cost(v, self.depot),
            }
            self.routes.append(route)
            r_id = len(self.routes) - 1
            self.arc_to_route[(u, v)] = r_id
            self.arc_to_route[(v, u)] = r_id

        # Vértices requeridos
        for node, props in self.required_vertices.items():
            demand = props['demand']
            if demand > self.capacity:
                raise ValueError(f"Demanda do vértice {node} excede capacidade.")
            route = {
                'path': [self.depot, node, self.depot],
                'load': demand,
                'tasks': set(),
                'service_vertices': {node},
                'service_cost': props['service_cost'],
                'transport_cost': self.graph.get_cost(self.depot, node) +
                                  self.graph.get_cost(node, self.depot),
            }
            self.routes.append(route)
            r_id = len(self.routes) - 1
            self.vertex_served[node] = r_id

    def compute_savings(self):
        savings = []
        dist_from_depot = self.graph.dijkstra(self.depot)
        blocked_edges = set(self.arc_to_route.keys())  # Inicializa com todas tarefas já atribuídas

        for (u, v, props) in self.required_arcs:
            s = dist_from_depot[u] + self.graph.dijkstra(v)[self.depot] - props['transport_cost']
            savings.append(((u, v), s))

        for ((u, v), props) in self.required_edges:
            s = dist_from_depot[u] + self.graph.dijkstra(v)[self.depot] - props['transport_cost']
            savings.append(((u, v), s))

        savings.sort(key=lambda x: x[1], reverse=True)
        return savings, blocked_edges

    def merge_routes(self, savings, blocked_edges):
        for (i, j), _ in savings:
            if self.max_routes is not None and len([r for r in self.routes if r]) <= self.max_routes:
                break

            r1 = self.arc_to_route.get((i, j))
            if r1 is None:
                continue

            for (u, v), r2 in list(self.arc_to_route.items()):
                if r2 == r1:
                    continue
                route1 = self.routes[r1]
                route2 = self.routes[r2]
                if route1 is None or route2 is None:
                    continue

                # Checa a possibilidade de fusão das rotas
                if i == route2['path'][-2] and route1['path'][1] == j:
                    new_load = route1['load'] + route2['load']
                    if new_load <= self.capacity:
                        blocked_edges.update(route1['tasks'])
                        blocked_edges.update(route2['tasks'])

                        new_path = route2['path'][:-1] + route1['path'][1:]
                        new_tasks = route1['tasks'] | route2['tasks']
                        new_vertices = route1['service_vertices'] | route2['service_vertices']

                        new_transport_cost = route1['transport_cost'] + route2['transport_cost'] \
                            - self.graph.get_cost(self.depot, j) - self.graph.get_cost(i, self.depot) \
                            + self.graph.get_cost(i, j)
                        new_service_cost = route1['service_cost'] + route2['service_cost']

                        self.routes[r2] = {
                            'path': new_path,
                            'load': new_load,
                            'tasks': new_tasks,
                            'service_vertices': new_vertices,
                            'service_cost': new_service_cost,
                            'transport_cost': new_transport_cost,
                        }
                        self.routes[r1] = None

                        for arc in new_tasks:
                            self.arc_to_route[arc] = r2
                            if not self.graph.is_directed(*arc):
                                self.arc_to_route[(arc[1], arc[0])] = r2
                        for v in new_vertices:
                            self.vertex_served[v] = r2
                        break

        self.routes = [r for r in self.routes if r is not None]


    def solve(self):
        self.initial_routes()
        savings, blocked_edges = self.compute_savings()
        self.merge_routes(savings, blocked_edges)
        return self.routes

    def print_route_details(self):
        for idx, route in enumerate(self.routes):
            print(f"Rota {idx + 1}:")
            print(f"  Caminho: {' -> '.join(map(str, route['path']))}")
            print(f"  Demanda total: {route['load']}")

            print("  Tarefas executadas:")
            for (u, v) in route['tasks']:
                t_cost = self.graph.get_cost(u, v)
                d = self.graph.get_demand(u, v)
                print(f"    Aresta: {u} -> {v}, Custo de transporte: {t_cost}, Demanda: {d}")

            print(f"  Custo de serviço: {route['service_cost']}")
            print(f"  Custo de transporte: {route['transport_cost']}")
            print(f"  Custo total: {route['service_cost'] + route['transport_cost']}")
            print()




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


print("Leia o READ.ME para colocar o arquivo em formato correto!!!")
file_path = input("Digite o caminho/nome do arquivo .dat: ")
(vertices, edges, arcs, required_vertices, required_edges, required_arcs, num_vehicles, capacity, depot_node, optimal_value) = read_file(file_path)

# 2. Inicializa o grafo
graph = Graph()

# Adiciona arestas normais (não requeridas)
for (u, v), t_cost in edges:
    graph.add_edge(u, v, cost=t_cost)

# Adiciona arcos normais (não requeridos)
for (u, v), t_cost in arcs:
    graph.add_edge(u, v, cost=t_cost, directed=True)

# Adiciona arestas requeridas (e converte para formato esperado)
required_edge_tasks = []
# Adiciona arestas requeridas
required_arc_tasks = []
for (u, v), (t_cost, demand, s_cost) in required_edges:
    graph.add_edge(u, v, cost=t_cost)
    graph.demands[(u, v)] = demand  # Atribuindo a demanda corretamente
    graph.demands[(v, u)] = demand  # Para arestas não direcionadas, se necessário

# Adiciona arcos requeridos
for (u, v), (t_cost, demand, s_cost) in required_arcs:
    graph.add_edge(u, v, cost=t_cost, directed=True)
    graph.demands[(u, v)] = demand  # Atribuindo a demanda corretamente para o arco


# Adiciona vértices requeridos (e converte para dicionário esperado)
required_vertex_tasks = {}
for v, (demand, s_cost) in required_vertices:
    required_vertex_tasks[v] = {
        'demand': demand,
        'service_cost': s_cost
    }

# 3. Inicializa e executa o solver
solver = ClarkeWrightSolver(
    graph=graph,
    depot=depot_node,
    required_arcs=required_arc_tasks + required_edge_tasks,  # Unifica arcos + arestas requeridas
    required_vertices=required_vertex_tasks,
    capacity=capacity,
    max_routes=num_vehicles  # Pode ser None, ou limitado
)

solver.solve()
solver.print_route_details()
