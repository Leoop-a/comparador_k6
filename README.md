# 📊 Comparador K6 (Dashboard Generator)

Um motor de processamento em Python projetado para devorar arquivos CSV massivos gerados por testes de carga do [k6](https://k6.io/) e renderizar dashboards comparativos limpos e minimalistas. Porque os olhos biológicos não foram feitos para processar milhões de linhas de dados brutos de latência.

## ⚙️ Funcionalidades

- **Chunking de Dados:** Processa arquivos de 2GB+ em blocos, evitando o derretimento da memória RAM da sua máquina.
- **Sincronização Temporal:** Alinha perfeitamente testes diferentes no segundo `T=0` para uma comparação justa de SLA.
- **Painel Executivo:** Foca no que importa. Cruzamento de VUs (Usuários Virtuais) vs RPS (Requisições por Segundo), mantendo as taxas de erro isoladas em um painel numérico flutuante. Zero poluição visual.

## 🏗️ Estrutura de Contenção

```text
comparador_k6/
├── dados/                 # ⚠️ Coloque exatamente 2 arquivos CSV do K6 aqui
├── graficos_gerados/      # Os relatórios visuais (.png) aparecerão aqui
├── .gitignore             # Evita que você quebre os servidores do GitHub
├── requirements.txt       # Bibliotecas de suporte (pandas, matplotlib)
├── gerador_graficos.py    # O núcleo de processamento
└── README.md              # Este arquivo que você está lendo
```

## 🛠️ Protocolo de Preparação e Execução

**1. Crie o isolamento do ambiente (Obrigatório):**
```bash
python -m venv venv
```

**2. Ative os sistemas (Se estiver usando Windows):**
```bash
.\venv\Scripts\activate
```

*(Ou, se estiver usando Linux/Mac):*
```bash
source venv/bin/activate
```

**3. Injete as ferramentas de processamento:**
```bash
pip install -r requirements.txt
```

**4. Inicie a varredura (exige os 2 arquivos .csv na pasta 'dados/'):**
```bash
python gerador_graficos.py
```

---
