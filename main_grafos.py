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
clock_otimo = 0
preferencias = le.leitura_referencias()

freq_mhz = psutil.cpu_freq().current  # Frequência atual em MHz
freq_hz = freq_mhz * 1_000_000        # Converte para Hz

for file in folder.iterdir():
    if file.is_file() and file.suffix == '.dat':
        nomedoarquivo = Path(file).stem
        if nomedoarquivo in preferencias:
            clock_otimo = preferencias[nomedoarquivo]
        print(f"\nArquivo processando -> {file.name}")
        # Leitura e preparação
        vertices, edges, arcs, required_vertices, required_edges, required_arcs, num_veicles, capacity, depot_node, optimal_value, IdsReq, IdsReqEA = le.read_file(file)
        matriz_distancias = p1.matriz_menores_distancias(vertices, edges, arcs)
        matriz_pred = p1.matriz_predecessores(vertices, edges, arcs)

        clock_inicio_total = time.perf_counter_ns()
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
        custo_deterministico = p2.custo_total_rotas(rotas_deterministicas, matriz_distancias)

        #  Aleatório
        rotas_aleatorias, melhor_seed, custo_aleatorio = p2.rodar_varias_vezes(
            required_edges=required_edges,
            required_arcs=required_arcs,
            required_vertices=required_vertices,
            depot_node=depot_node,
            num_vehicles=num_veicles,
            capacity=capacity,
            matriz_distancias=matriz_distancias,
            matriz_predecessores=matriz_pred,
            num_execucoes=10
        )

        clock_fim_total = time.perf_counter_ns()
        clock_total = clock_fim_total - clock_inicio_total
        ciclos_estimados = int(clock_total * (freq_hz / 1_000_000_000))

        #  Escolher melhor
        if custo_aleatorio < custo_deterministico:
            melhor_rotas = rotas_aleatorias
            melhor_custo = custo_aleatorio
            tipo = 'ale'
        else:
            melhor_rotas = rotas_deterministicas
            melhor_custo = custo_deterministico
            tipo = 'det'

        melhor_tarefas = p2.extrair_tarefas(required_edges, required_arcs, required_vertices)

        #  Exportar solução
        nome_base = file.stem
        for tipo_antigo in ['det', 'ale']:
            caminho_antigo = saida / f"{nome_base}_{tipo_antigo}.dat"
            if caminho_antigo.exists():
                caminho_antigo.unlink()  # Apaga o arquivo

        # Salva o novo com o sufixo da melhor versão
        nome_saida = saida / f"{nome_base}_{tipo}.dat"

        le.export_dat(
            rotas=melhor_rotas,
            tarefas=melhor_tarefas,
            matriz_distancias=matriz_distancias,
            custo_total=melhor_custo,
            total_clock_referencia=clock_otimo,
            total_clock_local=ciclos_estimados,
            nome_arquivo=nome_saida,
            IdsReq=IdsReq,
            IdsReqEA=IdsReqEA
        )

