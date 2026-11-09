# Developer Tools Research Agent

Agente de pesquisa para comparar ferramentas voltadas a desenvolvedores. A partir de uma pergunta, ele busca páginas na web, identifica produtos relevantes, analisa informações de cada ferramenta e gera uma recomendação breve. O fluxo pode ser usado em um terminal interativo ou carregado pelo servidor de desenvolvimento do LangGraph.

## Como funciona

```text
Pergunta do usuário
    ↓
extract_tools → busca artigos e extrai nomes de ferramentas
    ↓
research → encontra páginas das ferramentas e analisa seu conteúdo
    ↓
analyze → gera uma recomendação com base nos resultados
```

O resultado inclui nome, site, descrição, modelo de preço, indicação de código aberto, tecnologias, linguagens, disponibilidade de API e integrações, quando essas informações são encontradas. A pesquisa considera até quatro ferramentas extraídas dos artigos. Se a extração não retornar nomes, o fluxo tenta usar títulos de uma busca direta.

## Stack

| Tecnologia | Uso |
| --- | --- |
| Python 3.14+ | Linguagem do projeto |
| LangGraph | Orquestração das etapas de pesquisa |
| LangChain e `langchain-openai` | Chamadas ao modelo `gpt-5-nano` e saída estruturada |
| Firecrawl | Busca e extração de conteúdo de páginas web |
| Pydantic | Modelos de estado e de resultados |
| `python-dotenv` | Leitura das variáveis do arquivo `.env` |
| `uv` | Instalação reproduzível das dependências pelo `uv.lock` |

## Pré-requisitos

- Python 3.14 ou superior.
- [`uv`](https://docs.astral.sh/uv/) instalado.
- Chaves de API da OpenAI e do Firecrawl. As chamadas a esses serviços podem gerar custos conforme seus planos.

## Configuração

Na raiz do projeto, instale as dependências:

```bash
uv sync
```

Copie o arquivo de exemplo e preencha as chaves necessárias no `.env`:

```bash
cp .env.example .env
```

O arquivo `.env` está no `.gitignore`. Para habilitar rastreamento no LangSmith, configure opcionalmente `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` e, se necessário, `LANGSMITH_ENDPOINT`.

## Executar no terminal

```bash
uv run python main.py
```

Digite uma consulta, por exemplo `alternativas ao Supabase para aplicações Python`. O programa exibirá as ferramentas encontradas e uma recomendação. Digite `quit` ou `exit` para encerrar.

## Executar com LangGraph

O arquivo `langgraph.json` registra o grafo `developer_tools_research` definido em `src/graph.py`. Para iniciar o servidor local de desenvolvimento:

```bash
uv run langgraph dev
```

Ao invocar o grafo, forneça o estado inicial com a chave `query`, por exemplo:

```json
{"query": "alternativas ao Supabase para aplicações Python"}
```

O estado final contém `extracted_tools`, `companies` e `analysis`, além da consulta original. O servidor carrega as variáveis do `.env` por meio da configuração em `langgraph.json`.

## Estrutura do projeto

| Caminho | Responsabilidade |
| --- | --- |
| `main.py` | Interface interativa de linha de comando |
| `src/graph.py` | Ponto de entrada do grafo para o LangGraph |
| `src/workflow.py` | Etapas de busca, pesquisa e recomendação |
| `src/firecrawl.py` | Integração com busca e scraping do Firecrawl |
| `src/models.py` | Modelos Pydantic do estado e das ferramentas |
| `src/prompts.py` | Instruções enviadas ao modelo |
| `langgraph.json` | Configuração do servidor LangGraph |

## Limitações atuais

- Os dados dependem do conteúdo retornado pela busca e pelas páginas consultadas; preço, licença e outros atributos devem ser confirmados nas fontes oficiais antes de tomar uma decisão.
- Falhas de busca ou de análise podem produzir campos vazios ou resultados incompletos. O projeto ainda não inclui testes automatizados.
