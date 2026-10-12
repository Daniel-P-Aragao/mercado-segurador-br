# Mercado Segurador Brasileiro: concentração, crescimento e rentabilidade técnica

Pipeline de dados de ponta a ponta com os dados abertos da SUSEP (SES): ingestão e limpeza em **Python**, armazenamento e modelagem em **BigQuery (SQL)** e visualização em **Power BI**.

> **Status:** pipeline e camada de negócio concluídos; dashboard em Power BI em desenvolvimento.

---

## 1. Problema de negócio

Uma seguradora que decide **onde competir**, **onde reprecificar** e **onde há risco técnico** precisa responder três perguntas sobre o mercado:

1. **Concentração:** quem domina cada segmento e quão concentrado ele é?
2. **Rentabilidade técnica:** quais segmentos e seguradoras têm sinistralidade e comissionamento saudáveis, e quais estão sob pressão?
3. **Tendência:** como prêmios e sinistralidade evoluíram, e quais segmentos crescem acima do mercado?

## 2. Dados

| Item | Detalhe |
|---|---|
| Fonte | SUSEP, Sistema de Estatísticas (SES), base completa |
| Tabela principal | `Ses_seguros.csv`: prêmios, sinistros e despesas por seguradora, ramo e mês |
| Volume bruto | 1.807.405 linhas (1995 a 2026) |
| Recorte usado | **2014 em diante**: 780.535 linhas, 161 ramos |
| Granularidade | uma linha por seguradora × ramo × mês (validada: zero duplicatas na chave) |

**Por que a partir de 2014:** o perfil da base mostrou uma quebra estrutural. Até 2013, os sinistros vinham nos campos `sinistro_direto` e `sinistro_retido`; a partir de 2014, esses campos ficam zerados e passa a ser preenchido `sinistro_ocorrido`. Misturar os dois períodos mudaria a definição de sinistralidade no meio da série. Antes disso também havia outra codificação de ramos.

## 3. Abordagem

### Arquitetura

```
SUSEP (zip com CSVs)
   │  Python: download → perfil → limpeza e validação → parquet
   ▼
BigQuery: dataset susep (fato + dimensões)
   │  SQL: views de negócio
   ▼
BigQuery: dataset susep_marts (participação, HHI, CR4)
   │
   ▼
Power BI
```

### Modelo de dados (estrela)

- **`fato_seguros`**: data, seguradora, ramo, prêmio direto, prêmio ganho, sinistro ocorrido, despesa de comercialização
- **`dim_seguradoras`**: cadastro, com indicador de seguradora ativa
- **`dim_ramos`**: hierarquia **segmento → grupo → ramo**, definida em um seed versionado (`seeds/segmentos_ramos.csv`)

### Indicadores

| Indicador | Fórmula | Por quê |
|---|---|---|
| Participação de mercado | prêmio direto da seguradora ÷ prêmio direto do segmento | mede vendas no período |
| Sinistralidade | Σ sinistro ocorrido ÷ Σ prêmio ganho | compara sinistro e prêmio no mesmo regime de competência |
| Comissionamento | Σ despesa de comercialização ÷ Σ prêmio ganho | sinistralidade baixa não basta se a comissão é alta |
| HHI | Σ (participação em p.p.)² | concentração, com peso maior para os líderes |
| CR4 | participação somada das 4 maiores | leitura direta da concentração |

### Decisões técnicas

- **Perfil antes da limpeza.** Antes de transformar, verifiquei a cobertura de cada coluna por ano, se os valores eram mensais ou acumulados (são mensais) e a integridade das chaves entre fato e dimensões.
- **Valores negativos mantidos.** 0,8% dos prêmios ganhos e 7,3% dos sinistros ocorridos são negativos: reflexo legítimo de cancelamentos, reversões de provisão e ressarcimentos. Removê-los inflaria a sinistralidade.
- **Razão de somas, não média de razões.** Em células pequenas o índice explode (o segmento de Crédito, em *run off*, chega a −51.288% em 2025). Por isso os índices são sempre agregados antes da divisão, e só são exibidos quando o prêmio ganho anual é de pelo menos R$ 10 milhões.
- **Regras de negócio versionadas.** Os segmentos estão em um CSV no repositório, não escondidos em fórmulas do dashboard. O pipeline falha se a SUSEP criar um grupo de ramos sem segmento definido.
- **Pipeline idempotente e reconciliado.** As cargas substituem as tabelas (rodar duas vezes dá o mesmo resultado), e a contagem de linhas é conferida entre a camada local e o BigQuery após cada carga. Os totais também foram reconciliados entre pandas e SQL.
- **Views versionadas em código.** Os arquivos `.sql` são parametrizados pelo ID do projeto e criados por script, sem cliques no console.

## 4. Resultados

### O mercado mais que dobrou em valores nominais

| Ano | Prêmio direto (R$ bi) | Sinistralidade |
|---|---|---|
| 2014 | 91,5 | 50,3% |
| 2019 | 112,3 | 45,3% |
| 2021 | 131,8 | 51,0% |
| 2022 | 160,1 | 50,1% |
| 2025 | 204,7 | 40,8% |

### Quatro segmentos concentram cerca de 82% do mercado (2025)

| Segmento | Participação | Sinistralidade |
|---|---|---|
| Automóvel | 30,1% | 60,1% |
| Pessoas | 28,8% | ~29% |
| Patrimonial | 17,4% | 30,5% |
| Rural | 6,3% | 31,3% |

### Concentração por segmento (2025)

| Segmento | Seguradoras | HHI | CR4 |
|---|---|---|---|
| Rural | 38 | 3.862 | 76,2% |
| Habitacional | 23 | 1.653 | 73,0% |
| Grandes Riscos | 20 | 1.448 | 66,8% |
| Automóvel | 44 | 1.355 | 64,8% |
| Transportes | 27 | 780 | 45,8% |
| Responsabilidades | 48 | 692 | 41,3% |
| Riscos Financeiros e Crédito | 51 | 583 | 40,5% |
| Pessoas | 88 | 542 | 36,3% |
| Patrimonial | 67 | 505 | 35,2% |
| **Mercado total** | **132** | **404** | **31,0%** |

<!-- Inserir aqui os prints do dashboard quando estiver pronto -->

## 5. Conclusões para o negócio

- **Automóvel é o maior segmento e o de margem técnica mais apertada.** De cada R$ 100 de prêmio ganho, cerca de R$ 60 viram sinistro. O resultado depende de escala e de eficiência em despesas, o que explica a competição por preço. A concentração é moderada: as quatro maiores somam 65%, mas nenhuma domina sozinha.
- **Rural é o segmento mais concentrado do mercado** (HHI de 3.862), muito acima do patamar usual de mercado altamente concentrado (2.500). Para um entrante, isso indica barreiras relevantes, provavelmente ligadas a canais de distribuição. Identificar os líderes é o próximo passo da análise.
- **Pessoas tem sinistralidade baixa, mas isso não significa margem alta.** Produtos como prestamista costumam ter comissionamento elevado; o indicador de comissionamento será analisado lado a lado no dashboard.
- **A sinistralidade do mercado subiu em 2021–2022 e caiu depois.** Hipóteses a validar por segmento no dashboard: sinistros de vida ligados à pandemia em 2021 e perdas do seguro rural com estiagem em 2022.
- **O mercado como um todo é pouco concentrado** (HHI 404), mas essa visão agregada esconde segmentos muito concentrados. A análise precisa ser feita por segmento.

## 6. Limitações e próximos passos

- **Concentração por empresa, não por grupo econômico.** Grupos com várias seguradoras sob o mesmo controle fazem o HHI real ser maior do que o apresentado. Próximo passo: usar `Ses_grupos_economicos.csv`.
- **Valores nominais.** Deflacionar pelo IPCA para medir o crescimento real.
- **2026 é parcial.** Comparações devem usar o mesmo período de 2025.
- **Migrar a camada SQL para dbt**, com testes automatizados de unicidade e integridade.
- **Concluir o dashboard em Power BI.**

## 7. Como rodar

**Pré-requisitos:** Python 3.10+, Git e um projeto no Google Cloud com BigQuery (o Sandbox gratuito é suficiente).

```bash
git clone https://github.com/Daniel-P-Aragao/mercado-segurador-br.git
cd mercado-segurador-br

python -m venv .venv
# Windows:  .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz, a partir do `.env.example`:

```
GCP_PROJECT=id-do-seu-projeto
```

Execute o pipeline:

```bash
python -m src.download        # baixa e extrai a base do SES
python -m src.perfil          # (opcional) perfil exploratório da base
python -m src.transform       # limpa, valida e gera os parquets
python -m src.load_bigquery   # carrega no BigQuery e confere a contagem
python -m src.build_marts     # cria as views de negócio
```

Na primeira carga, o navegador abre para autorizar o acesso ao BigQuery.

### Estrutura

```
mercado-segurador-br/
├── config.py               # caminhos e parâmetros centralizados
├── requirements.txt
├── .env.example
├── seeds/
│   └── segmentos_ramos.csv # regra de negócio: grupo de ramo → segmento
├── sql/
│   └── marts/              # views de participação e concentração
├── src/
│   ├── download.py
│   ├── inspecionar.py
│   ├── perfil.py
│   ├── transform.py
│   ├── load_bigquery.py
│   └── build_marts.py
└── dashboard/              # arquivo do Power BI e prints
```

---

**Autor:** Daniel Aragão, Ciências Atuariais e Estatística (UFRJ) · [LinkedIn](https://www.linkedin.com/in/daniel-aragão-22369717a)
