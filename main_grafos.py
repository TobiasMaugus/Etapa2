from pathlib import Path
import parte1_grafos as p1
import parte2_grafos as p2
import leitura_escrita as le
import time
import psutil

folder = Path('./Testes')          # pasta com os arquivos .dat de entrada
saida = Path('./Resultados')       # pasta para arquivos de saída
saida.mkdir(exist_ok=True)

dados_metricas = []
freq_mhz = psutil.cpu_freq().current  # Frequência atual em MHz
freq_hz = freq_mhz * 1_000_000        # Converte para Hz

for file in folder.iterdir():
    if file.is_file() and file.suffix == '.dat':
        clock_inicio_total = time.perf_counter_ns()
        nomedoarquivo = Path(file).stem
        print(f"\nArquivo processando -> {file.name}")
        # Leitura e preparação
        vertices, edges, arcs, required_vertices, required_edges, required_arcs, num_veicles, capacity, depot_node, optimal_value, IdsReq, IdsReqEA = le.read_file(file)
        matriz_distancias = p1.matriz_menores_distancias(vertices, edges, arcs)
        matriz_pred = p1.matriz_predecessores(vertices, edges, arcs)

        # Determinístico
        rotas_deterministicas, tarefas = p2.orquestrar_clarke_wright(
            required_edges=required_edges,
            required_arcs=required_arcs,
            required_vertices=required_vertices,
            depot_node=depot_node,
            num_vehicles=num_veicles,
            capacity=capacity,
            matriz_distancias=matriz_distancias,
            matriz_predecessores=matriz_pred,
            seed=None,
            shuffle=False
        )
        clock_fim_det = time.perf_counter_ns()
        custo_deterministico = p2.custo_total_rotas(rotas_deterministicas, tarefas, matriz_distancias)

        total_tarefas = len(required_vertices) + len(required_edges) + len(required_arcs)
        if total_tarefas <= 33:
            num_exec = 30
        elif total_tarefas <= 70:
            num_exec = 20
        else:
            num_exec = 10

        #  Aleatório
        rotas_aleatorias, melhor_seed, custo_aleatorio, clock_melhor_aleatorio = p2.rodar_varias_vezes(
            required_edges=required_edges,
            required_arcs=required_arcs,
            required_vertices=required_vertices,
            depot_node=depot_node,
            num_vehicles=num_veicles,
            capacity=capacity,
            matriz_distancias=matriz_distancias,
            matriz_predecessores=matriz_pred,
            clockInit=clock_inicio_total,
            num_execucoes=num_exec
        )

       

        #  Escolher melhor
        if custo_aleatorio < custo_deterministico:
            melhor_rotas = rotas_aleatorias
            melhor_custo = custo_aleatorio
            tipo = 'ale'
            clock_melhor_solucao = clock_melhor_aleatorio
        else:
            melhor_rotas = rotas_deterministicas
            melhor_custo = custo_deterministico
            tipo = 'det'
            clock_melhor_solucao = clock_fim_det - clock_inicio_total

        melhor_tarefas = p2.extrair_tarefas(required_edges, required_arcs, required_vertices)

        #  Exportar solução
        nome_base = file.stem
        for tipo_antigo in ['det', 'ale']:
            caminho_antigo = saida / f"{nome_base}_{tipo_antigo}.dat"
            if caminho_antigo.exists():
                caminho_antigo.unlink()  # Apaga o arquivo

        # Salva o novo com o sufixo da melhor versão
        nome_saida = saida / f"{nome_base}_{tipo}.dat"

        clock_fim_total = time.perf_counter_ns()
        clock_total = clock_fim_total - clock_inicio_total
        ciclos_estimados_total = int(clock_total * (freq_hz / 1_000_000_000))
        ciclos_estimados_melhor_sol = int(clock_melhor_solucao * (freq_hz / 1_000_000_000))

        le.export_dat(
            rotas=melhor_rotas,
            tarefas=melhor_tarefas,
            matriz_distancias=matriz_distancias,
            custo_total=melhor_custo,
            total_clock_referencia=ciclos_estimados_total,
            total_clock_local=ciclos_estimados_melhor_sol,
            nome_arquivo=nome_saida,
            IdsReq=IdsReq,
            IdsReqEA=IdsReqEA
        )

