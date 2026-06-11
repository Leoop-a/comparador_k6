import os
import glob
import argparse
import pandas as pd
import matplotlib.pyplot as plt

def processar_csv_simplificado(caminho_arquivo):
    print(f"[-] Extraindo a essência de: {caminho_arquivo}")

    iterador_blocos = pd.read_csv(caminho_arquivo,
                                  chunksize=100000,
                                  usecols=['metric_name', 'timestamp', 'metric_value'])

    blocos_reqs = []
    blocos_vus = []
    blocos_falhas = []

    for bloco in iterador_blocos:
        reqs = bloco[bloco['metric_name'] == 'http_reqs']
        vus = bloco[bloco['metric_name'] == 'vus']
        falhas = bloco[bloco['metric_name'] == 'http_req_failed']

        if not reqs.empty: blocos_reqs.append(reqs)
        if not vus.empty: blocos_vus.append(vus)
        if not falhas.empty: blocos_falhas.append(falhas)

    df_reqs_raw = pd.concat(blocos_reqs) if blocos_reqs else pd.DataFrame(columns=['metric_value'])
    df_falhas_raw = pd.concat(blocos_falhas) if blocos_falhas else pd.DataFrame(columns=['metric_value'])

    total_reqs = df_reqs_raw['metric_value'].sum() if not df_reqs_raw.empty else 0
    total_falhas = df_falhas_raw['metric_value'].sum() if not df_falhas_raw.empty else 0
    
    taxa_erro = (total_falhas / total_reqs * 100) if total_reqs > 0 else 0

    df_reqs = df_reqs_raw.copy()
    if not df_reqs.empty:
        df_reqs['timestamp'] = pd.to_datetime(df_reqs['timestamp'], unit='s').dt.floor('s')
        df_reqs = df_reqs.groupby('timestamp')['metric_value'].sum().reset_index().rename(columns={'metric_value': 'rps'})
    else:
        df_reqs = pd.DataFrame(columns=['timestamp', 'rps'])

    df_vus = pd.concat(blocos_vus) if blocos_vus else pd.DataFrame(columns=['timestamp', 'metric_value'])
    if not df_vus.empty:
        df_vus['timestamp'] = pd.to_datetime(df_vus['timestamp'], unit='s').dt.floor('s')
        df_vus = df_vus.groupby('timestamp')['metric_value'].mean().reset_index().rename(columns={'metric_value': 'vus'})
    else:
        df_vus = pd.DataFrame(columns=['timestamp', 'vus'])

    df_resumido = pd.merge(df_reqs, df_vus, on='timestamp', how='outer').fillna(0)
    df_resumido = df_resumido.sort_values('timestamp')

    df_resumido['segundos_decorridos'] = (df_resumido['timestamp'] - df_resumido['timestamp'].min()).dt.total_seconds()
    
    tempo_total = df_resumido['segundos_decorridos'].max() if not df_resumido.empty else 0
    request_rate = total_reqs / tempo_total if tempo_total > 0 else 0

    estatisticas = {
        'taxa_erro': taxa_erro,
        'request_rate': request_rate
    }

    return df_resumido, estatisticas


def gerar_grafico_duracao(arquivo_1, arquivo_2, legenda_1, legenda_2):
    def processar_duracoes(caminho_arquivo):
        blocos_duracao = []

        for bloco in pd.read_csv(caminho_arquivo,
                                 chunksize=100000,
                                 usecols=['metric_name', 'timestamp', 'metric_value']):
            duracoes = bloco[bloco['metric_name'] == 'http_req_duration']
            if not duracoes.empty:
                blocos_duracao.append(duracoes[['timestamp', 'metric_value']])

        if not blocos_duracao:
            return pd.DataFrame(columns=['segundos_decorridos', 'media', 'p95'])

        dados = pd.concat(blocos_duracao)
        dados['timestamp'] = pd.to_datetime(dados['timestamp'], unit='s').dt.floor('s')
        dados = dados.groupby('timestamp')['metric_value'].agg(
            media='mean',
            p95=lambda valores: valores.quantile(0.95)
        ).reset_index()
        dados['segundos_decorridos'] = (
            dados['timestamp'] - dados['timestamp'].min()
        ).dt.total_seconds()
        return dados

    print("[-] Processando duração das requisições...")
    duracao_1 = processar_duracoes(arquivo_1)
    duracao_2 = processar_duracoes(arquivo_2)

    fig_duracao, ax_duracao = plt.subplots(figsize=(14, 7))
    fig_duracao.patch.set_facecolor('#111116')
    ax_duracao.set_facecolor('#111116')

    if not duracao_1.empty:
        ax_duracao.plot(duracao_1['segundos_decorridos'], duracao_1['media'],
                        color=COR_VUS_1, linewidth=1.5, label=f'Média - {legenda_1}')
        ax_duracao.plot(duracao_1['segundos_decorridos'], duracao_1['p95'],
                        color=COR_RPS_1, linewidth=2, label=f'P95 - {legenda_1}')

    if not duracao_2.empty:
        ax_duracao.plot(duracao_2['segundos_decorridos'], duracao_2['media'],
                        color=COR_VUS_2, linewidth=1.5, label=f'Média - {legenda_2}')
        ax_duracao.plot(duracao_2['segundos_decorridos'], duracao_2['p95'],
                        color=COR_RPS_2, linewidth=2, label=f'P95 - {legenda_2}')

    ax_duracao.set_title('Comparativo de Duração das Requisições HTTP',
                         fontsize=14, color='white', pad=15)
    ax_duracao.set_xlabel('Tempo de Execução (s)', fontsize=11, color='#cccccc')
    ax_duracao.set_ylabel('Duração (ms)', fontsize=11, color='#cccccc')
    ax_duracao.tick_params(axis='both', labelcolor='#cccccc')
    ax_duracao.grid(True, linestyle='-', alpha=0.1)
    ax_duracao.set_ylim(bottom=0)
    ax_duracao.legend(loc='upper right', framealpha=0.7,
                      facecolor='#111116', edgecolor='#333344', labelcolor='white')

    caminho_saida = 'graficos_gerados/comparativo_duracao_k6.png'
    plt.savefig(caminho_saida, dpi=300, facecolor=fig_duracao.get_facecolor(),
                bbox_inches='tight')
    print(f"[+] Comparativo de duração salvo em: {caminho_saida}")


pasta_dados = 'dados'
arquivos_csv = glob.glob(os.path.join(pasta_dados, '*.csv'))

parser = argparse.ArgumentParser(description='Gera gráficos comparativos de testes k6.')
parser.add_argument(
    '--grafico',
    choices=['vus', 'duracao', 'ambos'],
    default='ambos',
    help='Escolha o gráfico a gerar (padrão: ambos).'
)
args = parser.parse_args()

if len(arquivos_csv) < 2:
    print(f"[CRÍTICO] Para comparar, preciso de 2 arquivos. Encontrados: {len(arquivos_csv)}.")
    exit()

arquivos_csv.sort()
arquivo_1, arquivo_2 = arquivos_csv[0], arquivos_csv[1]

legenda_1 = os.path.basename(arquivo_1).replace('.csv', '')
legenda_2 = os.path.basename(arquivo_2).replace('.csv', '')

plt.style.use('dark_background')

COR_VUS_1 = '#5c3a6b'  
COR_RPS_1 = '#b388ff'  

COR_VUS_2 = '#1a594b'  
COR_RPS_2 = '#00e676'  

os.makedirs('graficos_gerados', exist_ok=True)

if args.grafico in ('vus', 'ambos'):
    dados_1, stats_1 = processar_csv_simplificado(arquivo_1)
    dados_2, stats_2 = processar_csv_simplificado(arquivo_2)

    fig, ax_vus = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor('#111116')
    ax_vus.set_facecolor('#111116')

    if not dados_1.empty:
        ax_vus.fill_between(dados_1['segundos_decorridos'], dados_1['vus'], color=COR_VUS_1, alpha=0.5, label=f'VUs - {legenda_1}')
    if not dados_2.empty:
        ax_vus.fill_between(dados_2['segundos_decorridos'], dados_2['vus'], color=COR_VUS_2, alpha=0.4, label=f'VUs - {legenda_2}')

    ax_vus.set_ylabel('Usuários Virtuais (VUs)', color='#cccccc', fontsize=11)
    ax_vus.tick_params(axis='y', labelcolor='#cccccc')
    ax_vus.set_xlabel('Tempo de Execução (s)', fontsize=11, color='#cccccc')
    ax_vus.grid(True, linestyle='-', alpha=0.1)

    max_vus = max(dados_1['vus'].max() if not dados_1.empty else 0, dados_2['vus'].max() if not dados_2.empty else 0)
    ax_vus.set_ylim(0, max_vus * 1.1 if max_vus > 0 else 1)

    ax_rps = ax_vus.twinx()

    if not dados_1.empty:
        ax_rps.plot(dados_1['segundos_decorridos'], dados_1['rps'], color=COR_RPS_1, linewidth=2, label=f'Req/s - {legenda_1}')
    if not dados_2.empty:
        ax_rps.plot(dados_2['segundos_decorridos'], dados_2['rps'], color=COR_RPS_2, linewidth=2, label=f'Req/s - {legenda_2}')

    ax_rps.set_ylabel('Requisições por Segundo (Req/s)', color='white', fontsize=11)
    ax_rps.tick_params(axis='y', labelcolor='white')

    max_rps = max(dados_1['rps'].max() if not dados_1.empty else 0, dados_2['rps'].max() if not dados_2.empty else 0)
    ax_rps.set_ylim(0, max_rps * 1.15 if max_rps > 0 else 1)

    texto_stats = (
        f"--- TESTE: {legenda_1} ---\n"
        f"Request Rate: {stats_1['request_rate']:.2f} req/s\n"
        f"Taxa de Erro: {stats_1['taxa_erro']:.2f}%\n"
        f"\n"
        f"--- TESTE: {legenda_2} ---\n"
        f"Request Rate: {stats_2['request_rate']:.2f} req/s\n"
        f"Taxa de Erro: {stats_2['taxa_erro']:.2f}%"
    )

    caixa_props = dict(boxstyle='round,pad=1', facecolor='#1a1a24', alpha=0.9, edgecolor='#333344')

    ax_vus.text(0.02, 0.96, texto_stats, transform=ax_vus.transAxes, fontsize=10, color='#eeeeee',
                verticalalignment='top', bbox=caixa_props, zorder=5, fontfamily='monospace')

    ax_vus.set_title('Comparativo de Vazão e Carga', fontsize=14, color='white', pad=15)

    h1, l1 = ax_vus.get_legend_handles_labels()
    h2, l2 = ax_rps.get_legend_handles_labels()
    ax_vus.legend(h1 + h2, l1 + l2, loc='upper right', framealpha=0.7, facecolor='#111116', edgecolor='#333344', labelcolor='white')

    caminho_saida = 'graficos_gerados/comparativo_final_k6.png'
    plt.savefig(caminho_saida, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
    print(f"\n[+] Comparativo de VUs salvo em: {caminho_saida}")

if args.grafico in ('duracao', 'ambos'):
    gerar_grafico_duracao(arquivo_1, arquivo_2, legenda_1, legenda_2)

plt.show()
