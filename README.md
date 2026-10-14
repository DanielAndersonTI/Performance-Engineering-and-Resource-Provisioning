# Atividade 2 — Demanda, Provisionamento e Desempenho

Este repositório reúne o código, os scripts, os dados e a documentação produzidos para a segunda atividade avaliativa da disciplina. O trabalho deve ser desenvolvido em grupos de três e investigará experimentalmente como a demanda e os recursos computacionais provisionados afetam o desempenho e a utilização de recursos de aplicações web.

> **Atenção:** preencham este README e o documento de resultados com as decisões e os valores realmente utilizados. Não registrem resultados estimados ou inventados.

## Objetivos

- Desenvolver três aplicações web, somente com backend, cada uma com um perfil computacional predominante diferente: **CPU-bound**, **Memory-bound** ou **IO-bound**.
- Executar e testar as três aplicações em uma máquina local.
- Configurar uma máquina virtual no VirtualBox, fazer o deploy de uma das aplicações e demonstrar seu funcionamento.
- Experimentar diferentes níveis de demanda e configurações de recursos da VM.
- Medir e analisar, de forma comparativa, o desempenho das aplicações e a utilização dos recursos.
- Relacionar os resultados à demanda e ao provisionamento, identificando possíveis pontos de degradação.

## O que desenvolver

Implementem três aplicações web de backend, usando a linguagem de programação de preferência do grupo. Cada aplicação deve representar um perfil distinto:

| Perfil | Característica a exercitar | Aplicação desenvolvida |
| --- | --- | --- |
| CPU-bound | Predomínio de operações que consomem processador. | SHA-256 repetido sobre um bloco fixo de 1 MiB, com o resumo realimentando o bloco a cada iteração — `apps/cpu/server.py` |
| Memory-bound | Predomínio de operações que consomem memória. | Alocação de `size` MiB e escrita de um byte por página de 4 KiB, forçando a materialização de cada página — `apps/memory/server.py` |
| IO-bound | Predomínio de operações de entrada e saída. | Escrita de `size` KiB em arquivo temporário, `fsync` para forçar a descida ao disco, e releitura — `apps/io/server.py` |

As três aplicações foram implementadas em Python 3 (somente biblioteca padrão no
servidor) e compartilham o mesmo contrato HTTP: `GET /health`, que identifica o
perfil que respondeu, e `GET /work?size=N`, que executa o trabalho. A descrição
completa de cada aplicação, as instruções de execução, o monitoramento e as
decisões do grupo estão no [documento de resultados](RELATORIO.md).

Para cada aplicação, documentem:

- O objetivo, o funcionamento e as principais características.
- Como o perfil computacional é exercitado e por que a aplicação representa esse perfil.
- Como executar e testar localmente, incluindo dependências e comandos necessários.
- Como a aplicação e a infraestrutura foram monitoradas, e quais métricas foram coletadas.

Mantenham o código atualizado neste repositório. Incluam também os scripts de execução, teste, geração de carga e coleta de métricas, bem como os dados brutos e os resultados dos experimentos.

## Etapas de execução

### 1. Desenvolver e testar localmente

1. Implementem as três aplicações e documentem seus requisitos e instruções de execução.
2. Executem cada aplicação em uma máquina local.
3. Testem o funcionamento de cada uma e guardem evidências e comandos utilizados.
4. Atualizem o repositório durante o desenvolvimento.

### 2. Configurar a VM e fazer o deploy

1. Configurem uma máquina virtual no VirtualBox seguindo o roteiro disponibilizado pelo professor.
2. O disco VDI está disponível no link indicado pelo professor. **Nos LCCs, utilizem a versão localizada em `/local/uasc`.**
3. Escolham uma das três aplicações e façam o deploy na VM.
4. Registrem as etapas de configuração, os requisitos, os comandos e eventuais ajustes necessários ao deploy.
5. Testem a aplicação na VM e preparem a demonstração em sala. Também será necessário mostrar as aplicações executando no LCC.

Incluam no relatório a configuração completa da VM usada em cada cenário, como quantidade de CPUs/vCPUs, memória e quaisquer outros recursos relevantes. Registrem ainda o ambiente hospedeiro quando essa informação estiver disponível.

### 3. Realizar os experimentos de carga

Façam experimentos com a aplicação implantada na VM, combinando diferentes configurações de recursos e diferentes níveis de demanda.

- **Utilizem pelo menos quatro cenários de provisionamento.** O roteiro da atividade pede ao menos quatro cenários; esse requisito é mais rigoroso do que a referência a “pelo menos 2” no template do relatório. Para atender à atividade, usem quatro ou mais.
- Para **cada cenário**, testem mais de um nível de demanda, aumentando a carga de forma controlada.
- **A carga de teste deve ser gerada de fora da máquina virtual.** Descrevam de onde ela foi gerada e a ferramenta ou script utilizado.
- Mantenham comparáveis as condições dos cenários, alterando de forma identificável os recursos provisionados. Registrem diferenças que não puderem ser mantidas constantes.
- Anotem a configuração da VM, os níveis de carga, a duração, o número de repetições, o intervalo de coleta e as condições de cada execução.
- Coletem os dados da aplicação e da infraestrutura durante os testes. Guardem dados brutos para permitir a reprodução e a elaboração dos gráficos.

Não há valores específicos de CPU, memória, demanda ou duração definidos neste README: registrem os valores escolhidos pelo grupo e justifiquem a metodologia no relatório.

## Métricas e análise

Coletem, conforme aplicável:

**Métricas da aplicação**

- Tempo de resposta/latência (informem a unidade e, quando possível, percentis como p50, p95 e p99).
- Vazão, em requisições por segundo.
- Número de requisições concluídas, falhas e timeouts.

**Métricas da infraestrutura da VM**

- Utilização de CPU.
- Consumo ou utilização de memória.
- Outras métricas relevantes ao perfil e à aplicação, se disponíveis.

Apresentem gráficos comparativos que relacionem a demanda, os recursos provisionados, o desempenho e a utilização. Interpretem os dados: indiquem quando o aumento da demanda elevar a latência, reduzir ou estabilizar a vazão, aumentar falhas ou provocar outro sinal de degradação. Discutam se e como a alteração dos recursos provisionados mudou esse comportamento. Não se limitem a exibir gráficos: expliquem as observações e as limitações dos experimentos.

## Documento de resultados

Produzam o documento usando o template disponibilizado pelo professor. O documento deve conter, no mínimo:

1. **Título e grupo:** “Demanda, Provisionamento e Desempenho”, nomes dos integrantes e matrículas.
2. **Aplicações desenvolvidas:** descrição, características, perfil computacional, execução e monitoramento de cada aplicação.
3. **Configuração da VM e deploy:** etapas de configuração, recursos provisionados, aplicação escolhida, requisitos e etapas de deploy.
4. **Teste de stress da aplicação selecionada:** cenários de recursos, níveis de carga, ferramenta e método de geração de carga (fora da VM), duração, repetições e coleta de dados.
5. **Resultados comparativos:** gráficos e métricas de desempenho da aplicação e de utilização dos recursos da VM.
6. **Interpretação e conclusões:** relação entre demanda, provisionamento, desempenho e utilização; degradações observadas; efeitos da alteração de recursos e limitações.

O template menciona pelo menos dois cenários de configuração; para cumprir o enunciado completo da atividade, apresentem **no mínimo quatro**.

## Entregas e demonstrações

- [ ] Três aplicações web de backend com perfis CPU-bound, Memory-bound e IO-bound.
- [ ] Código atualizado no repositório da organização da disciplina.
- [ ] Instruções e evidências de execução e teste local das três aplicações.
- [ ] VM configurada no VirtualBox conforme o roteiro e uma aplicação implantada e testada nela.
- [ ] Demonstração em sala da aplicação em execução na VM e das aplicações no LCC.
- [ ] Experimentos com pelo menos quatro cenários de provisionamento e vários níveis de demanda em cada cenário.
- [ ] Geração de carga externa à VM, coleta de métricas e armazenamento dos dados brutos.
- [ ] Gráficos comparativos e análise dos resultados.
- [ ] Documento de resultados preenchido usando o template disponibilizado.
- [ ] Formulário de entrega respondido **uma vez por cada integrante do grupo**.

## Artefatos do repositório

Organizem o repositório para que outra pessoa consiga entender e, quando possível, reproduzir o trabalho. Incluam todos os artefatos gerados, por exemplo:

- Código-fonte e instruções para executar cada aplicação.
- Scripts de teste, geração de carga e coleta de métricas.
- Configurações ou comandos relevantes da VM e do deploy, sem incluir credenciais ou outros segredos.
- Dados brutos dos experimentos, resultados processados e gráficos.
- Documento de resultados preenchido e evidências das demonstrações, quando aplicável.

## Materiais da disciplina

- **Roteiro de configuração da VM e deploy:** material disponibilizado pelo professor.
- **Disco VDI:** link disponibilizado pelo professor; nos LCCs, usar a versão em `/local/uasc`.
- **Template do documento de resultados:** material disponibilizado pelo professor.
- **Formulário de entrega:** link disponibilizado pelo professor; cada integrante deve responder individualmente.

---

## Decisões e valores utilizados neste trabalho

**Grupo:** Daniel Anderson de Souza Silva · Ranya Duran Greco

| Decisão | Valor adotado |
| --- | --- |
| Linguagem | Python 3 — o servidor usa apenas a biblioteca padrão |
| Aplicação implantada na VM | **Memory-bound** |
| Cenários de provisionamento | C1 1 vCPU / 1 GB · C2 2 vCPU / 1 GB · C3 1 vCPU / 2 GB · C4 2 vCPU / 2 GB |
| Níveis de demanda | 1, 2 e 4 clientes concorrentes, em cada cenário |
| Tamanho da carga | 256 MiB por requisição |
| Aquecimento / medição | 5 s não registrados / 40 s medidos, por nível |
| Repetições | 1 |
| Geração de carga | **Fora da VM**, do hospedeiro, via `scripts/load_test.py` |
| Coleta na VM | `scripts/monitor.py`, intervalo de ~0,5 s |
| VM | Ubuntu Server 22.04 LTS, rede NAT, portas 2222→22 e 8080→8000 |

### Onde está cada artefato

| Caminho | Conteúdo |
| --- | --- |
| `atividade2-demanda-desempenho/atividade2/atividade2_demanda/apps/` | as três aplicações |
| `…/scripts/` | geração de carga, monitor, orquestrador, gráficos, captura de evidência |
| `…/tests/` | 9 testes funcionais |
| `…/results/` | dados brutos (`measurements.csv`, `run_log.csv`, `resources.csv`), `summary.csv` e `graphs/` |
| `atividade2-demanda-desempenho/evidencias/` | configuração da VM em cada cenário e capturas de tela |
| `figuras/` | cópias das figuras usadas no relatório (gráficos e capturas da VM) |
| `RELATORIO.md` | documento de resultados |
| `DEVELOPMENT_HANDOFF.md` | registro interno do processo de desenvolvimento (em inglês) |

### Como executar

Todos os comandos partem do diretório da aplicação:

```bash
cd atividade2-demanda-desempenho/atividade2/atividade2_demanda
pip install -r requirements.txt     # matplotlib e psutil; o servidor usa só a stdlib

python apps/cpu/server.py    --port 8000    # cada aplicação é um processo independente
python apps/memory/server.py --port 8000
python apps/io/server.py     --port 8000
python apps/server.py --profile memory --port 8000   # ponto de entrada compartilhado

python -m unittest discover -s tests -v     # 9 testes funcionais, todos aprovados
```

Requisitos: Python 3.10 ou superior. No interior da VM, o script de
monitoramento requer `python3-psutil`, instalado via `apt`.

### Principais resultados

O detalhamento completo, os gráficos e as limitações estão no
[documento de resultados](RELATORIO.md) — resultados na §3.3, interpretação,
conclusões e limitações na §3.4.

- Provisionar 2 GB em vez de 1 GB **eliminou o swap**: pico de 507 MB e 545 MB
  nos cenários de 1 GB, contra 0 MB nos dois cenários de 2 GB.
- **Dobrar os vCPUs não trouxe ganho.** A aplicação é serializada pela GIL do
  CPython e não ocupa mais de um núcleo, então o segundo vCPU fica ocioso.
- **O gargalo se desloca.** Em 1 GB o limitante é a memória; em 2 GB, com o swap
  eliminado, passa a ser a CPU.
- Não houve nenhuma falha, erro ou timeout nos 12 níveis medidos.