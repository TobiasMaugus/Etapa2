import parte2_grafos as p2
import csv
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

    IdRequireds = dict()
    IdRequiredsEA = dict()
    current_id = 1  # Contador de IDs

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
                    IdRequireds[aux] = current_id
                    current_id += 1

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
                        aux = (edge, (t_cost, demand, s_cost))
                        IdRequiredsEA[aux] = current_id
                        current_id += 1

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
                        aux=(arc, (t_cost, demand, s_cost))
                        IdRequiredsEA[aux] = current_id
                        current_id += 1
                except ValueError:
                    continue

            elif section == "Err":
                continue

    return vertices, edges, arcs, required_vertices, required_edges, required_arcs, num_vehicles, capacity, depot_node, optimal_value, IdRequireds, IdRequiredsEA

def export_dat(rotas, tarefas, matriz_distancias, custo_total, total_clock_referencia, total_clock_local, nome_arquivo, IdsReq, IdsReqEA):
    linhas_rotas = []

    for idx, rota in enumerate(rotas):
        id_rota = idx + 1
        demanda_total = rota['demanda']
        rota_completa = rota['rota_completa']
        custo = p2.custo_rota_especifica(rota, matriz_distancias)
        num_visitas_deposito = rota['rota_completa'].count(rota_completa[0])
        visitas = len(rota['tarefas']) + num_visitas_deposito
        lista_aux = []

        if len(rota_completa) >= 2:
            inicioRota = rota_completa[0]
            destinoInicioRota = rota_completa[1]
            fimRota = rota_completa[-1]
            origemFimRota = rota_completa[-2]

            # Adiciona tripla "D" do início da rota
            lista_aux.append(f"(D 0,{inicioRota},{destinoInicioRota})")

        # Triplas das tarefas
        for tarefa_idx in rota['tarefas']:
            tarefa = tarefas[tarefa_idx]
            u = tarefa['origem']
            v = tarefa['destino']
            tipo = tarefa['tipo']
            if tipo == 'vertice':
                chave = (tarefa['origem'], (tarefa['demanda'], tarefa['custo_servico']))
                id_tarefa = IdsReq.get(chave, "N/A")

            elif tipo == 'edge':
                u, v = min(tarefa['origem'], tarefa['destino']), max(tarefa['origem'], tarefa['destino'])
                chave = ((u, v), (tarefa['t_cost'], tarefa['demanda'], tarefa['custo_servico']))
                id_tarefa = IdsReqEA.get(chave, "N/A")

            elif tipo == 'arc':
                chave = ((tarefa['origem'], tarefa['destino']), (tarefa['t_cost'], tarefa['demanda'], tarefa['custo_servico']))
                id_tarefa = IdsReqEA.get(chave, "N/A")

            else:
                id_tarefa = "N/A"

            lista_aux.append(f"(S {id_tarefa},{u},{v})")

        if len(rota_completa) >= 2:
            # Adiciona tripla "D" do fim da rota
            lista_aux.append(f"(D 0,{origemFimRota},{fimRota})")
        lista_aux_string = ' '.join(str(item) for item in lista_aux)
        linhas_rotas.append(f"0 1 {id_rota} {demanda_total} {custo:.2f} {visitas} {lista_aux_string}")
    # Cabeçalho
    conteudo = [
        f"{custo_total:.2f}",
        f"{len(rotas)}",
        f"{total_clock_referencia}",
        f"{total_clock_local}",
    ] + linhas_rotas

    with open(nome_arquivo, 'w') as f:
        f.write("\n".join(conteudo))


def leitura_referencias(arq_excel="reference_values.csv"):
    import csv
    resultado = {}
    with open('reference_values.csv', newline='', encoding='utf-8') as f:
        leitor = csv.reader(f)
        next(leitor)
        for linha in leitor:
            if len(linha) >= 5:
                nome = linha[0]
                clocks_melhor_sol = linha[4]
                resultado[nome] = int(clocks_melhor_sol)
    return resultado
