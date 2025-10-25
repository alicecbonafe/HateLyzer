# Hate Speech Detection in YouTube Videos

Este projeto analisa transcrições de vídeos do YouTube para identificar discursos de ódio e falas potencialmente ofensivas.

## Funcionalidades

- Download de transcrições de vídeos de um canal do YouTube.
- Análise de transcrições utilizando modelos de linguagem avançados.
- Geração de relatórios em formato JSON.

## Configuração

1. Clone este repositório:
   ```bash
   git clone <url-do-repositorio>
   ```

2. Crie um arquivo `.env` baseado no `.env.example` e preencha as variáveis necessárias:
   ```bash
   cp .env.example .env
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

Execute o script principal com o nome da função desejada:
```bash
python transcr.py <function_name>
```

### Funções disponíveis

- `download_transcriptions`: Faz o download das transcrições dos vídeos do canal especificado.
- `list_videos`: Lista os vídeos disponíveis no canal.

## Estrutura do Projeto

- `transcr.py`: Script principal com as funções de download e análise.
- `prompts/`: Contém os arquivos de prompt para análise.
- `generated/`: Diretório onde os resultados das análises são salvos.
- `cache/`: Diretório para armazenamento de cache temporário.

## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.