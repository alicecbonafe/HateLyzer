import sys
import os
from datetime import datetime
import json
from hashlib import sha256

import requests
from dotenv import load_dotenv
from openai import OpenAI
from markdown_pdf import MarkdownPdf, Section
import pypandoc
from pytubefix import YouTube
from slugify import slugify
from tiktoken import encoding_for_model
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter
from youtube_transcript_api.proxies import WebshareProxyConfig

load_dotenv()

YT_TOKEN = os.getenv('YT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
HF_TOKEN = os.getenv('HF_TOKEN')
MODEL_NAME = os.getenv('MODEL_NAME')
PROVIDER = os.getenv('PROVIDER')

# Configuração do log
def get_log_file():
    """
    Retorna o nome do arquivo de log baseado na data atual.
    """
    data_str = datetime.now().strftime('%Y-%m-%d')
    return f'log_{data_str}.txt'

def log(msg):
    """
    Escreve uma mensagem no arquivo de log com timestamp.

    Args:
        message (str): Mensagem a ser registrada no log.
    """
    log_file = get_log_file()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f'{timestamp} - {msg}\n')

def download_transcriptions():
    """
    Faz o download das transcrições dos vídeos do canal especificado.
    """
    videos = list_videos()
    for video_id in videos:
        metadata = download_metadata(video_id)
        slug = slugify(metadata['title'])
        destination_name = f"transcriptions/{slug}.md"

        if metadata['publish_date'].year != 2025:
            log(f"[OLD] ({video_id}) {slug}")
            continue
        if os.path.exists(destination_name):
            log(f"[DUPLICATE] ({video_id}) {slug}")
            continue

        log(f"Downloading transcription for {metadata['title']}...")
        transcription = download_transcription(video_id)
        if transcription is None:
            log(f"[UNAVAILABLE] ({video_id}) {slug}")
            continue
        if transcription.startswith('ERROR:'):
            log(f"[ERROR] ({video_id}) {slug} - {transcription}")
            continue

        with open(destination_name, 'w', encoding='utf-8') as destination:
            destination.write(f"# {metadata['title']}\n")
            destination.write("\n")
            destination.write(f"**Publish Date:** {metadata['publish_date']}\n")
            destination.write(f"**Link:** https://www.youtube.com/watch?v={video_id}\n")
            destination.write("\n")
            destination.write("```srt\n")
            destination.write(transcription)
            destination.write("\n```)\n")
            destination.write("\n")

        log(f"Transcription for {metadata['title']} saved to {destination_name}.")

def list_videos(api_key=YT_TOKEN, channel_id=CHANNEL_ID, max_results=None):
    """
    Lista os vídeos do canal do YouTube especificado.

    Args:
        api_key (str): Chave da API do YouTube.
        channel_id (str): ID do canal do YouTube.
        max_results (int, optional): Número máximo de vídeos a listar.

    Returns:
        list: Lista de IDs de vídeos.
    """
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'channelId': channel_id,
        'eventType': 'completed',
        'type': 'video',
        'key': api_key,
        'maxResults': 50
    }

    # Cria uma chave única para o cache baseada nos parâmetros
    cache_dir = 'cache'
    os.makedirs(cache_dir, exist_ok=True)
    cache_key = f"{channel_id}_{max_results}"
    cache_hash = sha256(cache_key.encode('utf-8')).hexdigest()
    cache_file = os.path.join(cache_dir, f"videos_cache_{cache_hash}.json")

    # Tenta carregar do cache
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                videos = json.load(f)
            return videos
        except Exception as e:
            log(f"Erro ao ler cache: {e}. Consultando API...")

    videos = []
    next_page_token = None
    count = 0

    while True:
        if next_page_token:
            params['pageToken'] = next_page_token

        response = requests.get(url, params=params)
        data = response.json()

        for item in data.get('items', []):
            videos.append(item['id']['videoId'])
            count += 1
            if max_results and count >= max_results:
                # Salva no cache antes de retornar
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(videos, f)
                return videos

        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break

    # Salva no cache
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(videos, f)
    return videos

def download_metadata(video_id):
    """
    Faz o download dos metadados de um vídeo do YouTube.

    Args:
        video_id (str): ID do vídeo.

    Returns:
        dict: Metadados do vídeo.
    """
    yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
    return {
        'title': yt.title,
        'publish_date': yt.publish_date,
        'description': yt.description
    }

def download_transcription(video_id):
    """
    Faz o download da transcrição de um vídeo do YouTube.

    Args:
        video_id (str): ID do vídeo.

    Returns:
        str: Transcrição no formato SRT.
    """
    try:
        ytt_api = YouTubeTranscriptApi()
        # https://github.com/jdepoix/youtube-transcript-api?tab=readme-ov-file#working-around-ip-bans-requestblocked-or-ipblocked-exception
        # ytt_api = YouTubeTranscriptApi(
        #     proxy_config=WebshareProxyConfig(
        #         proxy_username="fdiptbsl",
        #         proxy_password="c7oy8xoyv3ms",
        #         filter_ip_locations=["de", "us"],
        #     )
        # )
        transcription = ytt_api.fetch(video_id, languages=['pt', 'en'])
        formatter = SRTFormatter()
        srt_formatted = formatter.format_transcript(transcription)

        # with open(f'{slugify(yt.title)}.srt', 'w', encoding='utf-8') as srt_file:
        #     srt_file.write(srt_formatted)
        return srt_formatted
    except Exception as e:
        log(f"Ocorreu um erro: {e}")
        with open("cache/nao_concluidos.txt", "a", encoding="utf-8") as log_file:
            log_file.write(f"{video_id}\n")
        return f'ERRO: {e}'

def renomear_transcricoes_com_data():
    pasta = 'transcriptions'
    for nome_arquivo in os.listdir(pasta):
        caminho = os.path.join(pasta, nome_arquivo)
        if not os.path.isfile(caminho) or not nome_arquivo.endswith('.md'):
            continue
        with open(caminho, 'r', encoding='utf-8') as f:
            linhas = f.readlines()
        # Procura a linha da data
        data_str = None
        for linha in linhas:
            if linha.strip().startswith('**Data de publicação:**'):
                # Espera formato: **Data de publicação:** 2025-03-31 19:00:00
                data_part = linha.split('**Data de publicação:**')[-1].strip()
                # Extrai apenas a data (YYYY-MM-DD)
                if data_part:
                    data_sql = data_part.split()[0]
                    data_str = data_sql
                break
        if not data_str:
            log(f"[SEM DATA] {nome_arquivo}")
            continue
        # Monta novo nome
        nome_base = nome_arquivo[:-3]  # remove .md
        data_str = data_str.replace('-', '')
        novo_nome = f"{data_str}-{nome_base}.md"
        novo_caminho = os.path.join(pasta, novo_nome)
        if caminho != novo_caminho:
            if os.path.exists(novo_caminho):
                log(f"[REPETIDO] {novo_nome} já existe. Pulando {nome_arquivo}.")
                continue
            os.rename(caminho, novo_caminho)
            log(f"Renomeado: {nome_arquivo} -> {novo_nome}")

# Função para concatenar todos os arquivos .md da pasta transcriptions
def concatenar_transcricoes(
        arquivo_saida="transcricoes_concatenadas.md",
        reverso=True):
    pasta = 'transcriptions'

    arquivos = [f for f in os.listdir(pasta) if f.endswith('.md') and os.path.isfile(os.path.join(pasta, f))]
    arquivos.sort(reverse=reverso)

    with open(arquivo_saida, 'w', encoding='utf-8') as fout:
        for idx, nome_arquivo in enumerate(arquivos):
            caminho = os.path.join(pasta, nome_arquivo)

            with open(caminho, 'r', encoding='utf-8') as fin:
                conteudo = fin.read()
                fout.write(conteudo)
                if not conteudo.endswith('\n'):
                    fout.write('\n')

            if idx < len(arquivos) - 1:
                fout.write('\n---\n\n')

def call_inference(
        instrucoes_file = "prompts/instructions.md",
        system_file = "prompts/system.md",
        transcriptions_dir = "transcriptions",
        generated_dir = "generated",
        item_inicial = 0,
        max_itens = None,
        reverse_transcriptions=True,
        model_name = MODEL_NAME,
        provider = PROVIDER,
        hf_token = HF_TOKEN,
    ):
    
    def contar_tokens(texto, modelo="gpt-3.5-turbo"):
        try:
            enc = encoding_for_model(modelo)
            return len(enc.encode(texto))
        except Exception:
            return len(texto.split())

    instructions = None
    system_prompt = None

    with open(instrucoes_file, 'r', encoding='utf-8') as fin:
        instructions = fin.read()
        if not instructions.endswith('\n'):
            instructions += '\n'

    with open(system_file, 'r', encoding='utf-8') as fin:
        system_prompt = fin.read()
        if not system_prompt.endswith('\n'):
            system_prompt += '\n'

    transcriptions_files = [f for f in os.listdir(transcriptions_dir) if f.endswith('.md') and os.path.isfile(os.path.join(transcriptions_dir, f))]
    transcriptions_files.sort(reverse=reverse_transcriptions)

    total = len(transcriptions_files)
    if max_itens is not None:
        limite = min(item_inicial + max_itens, total)
    else:
        limite = total

    for idx in range(item_inicial, limite):
        trascription_file = transcriptions_files[idx]
        transcription_path = os.path.join(transcriptions_dir, trascription_file)
        output_path = os.path.join(generated_dir, trascription_file)
        if os.path.exists(output_path):
            log(f"[PULADO] {trascription_file} já existe em {output_path}.")
            continue
        with open(transcription_path, 'r', encoding='utf-8') as fin:
            transcription = fin.read()
            if not transcription.endswith('\n'):
                transcription += '\n'

        messages = []
        messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": instructions})
        messages.append({"role": "user", "content": transcription})

        # Conta tokens de entrada
        entrada_texto = system_prompt + instructions + transcription
        entrada_tokens = contar_tokens(entrada_texto, modelo=model_name)
        log(f"[INFERENCIA] {trascription_file} - Entrada: {entrada_tokens} tokens")

        client = OpenAI(
            base_url='https://router.huggingface.co/v1',
            api_key=hf_token
        )

        response = client.chat.completions.create(
            model=f"{model_name}:{provider}",
            messages=messages,
            max_tokens=8196,
            temperature=0.7,
            top_p=0.9,
        )

        response_text = response.choices[0].message.content
        saida_tokens = contar_tokens(response_text, modelo=model_name)
        log(f"[INFERENCIA] {trascription_file} - Saída: {saida_tokens} tokens")

        with open(output_path, 'w', encoding='utf-8') as fout:
            fout.write(f"# Análise de {trascription_file}\n")
            fout.write("\n")
            fout.write(f"- Modelo: {model_name}\n")
            fout.write(f"- Provedor: {provider}\n")
            fout.write(f"- Tokens de entrada: {entrada_tokens}\n")
            fout.write(f"- Tokens de saída: {saida_tokens}\n")
            fout.write("\n")
            fout.write(response_text)

    return True

def format_document(
        output_file = "document_formatted",
        generated_dir = "generated",
        title = None,
        description = None,
        model_name = MODEL_NAME
):
    pdf = MarkdownPdf(toc_level=2, optimize=True)

    section = ""
    if title:
        section += f"# {title}\n\n"
    if description:
        section += f"{description}\n\n"
    section += f"*Documento gerado com o modelo {model_name}.*\n\n"
    pdf.add_section(Section(section))

    source_files = [f for f in os.listdir(generated_dir) if f.endswith('.md') and os.path.isfile(os.path.join(generated_dir, f))]
    for idx, source_file in enumerate(source_files):
        source_path = os.path.join(generated_dir, source_file)
        with open(source_path, 'r', encoding='utf-8') as fin:
            source_contents = fin.read()
            # Lê o conteúdo do bloco json e transforma em dict
            start_index = source_contents.find('```json')
            end_index = source_contents.find('```', start_index + 1)
            if start_index < 0 or end_index < 0:
                log(f"[SEM JSON] {source_file} não contém bloco json.")
                continue
            json_block = source_contents[start_index + len('```json'):end_index].strip()
            file_data = json.loads(json_block)

            link = file_data.get('link')
            selected_speeches = file_data.get('selected_speeches', [])

            section_text = f"## {file_data.get('title', source_file)}\n\n"
            section_text += f"Link do vídeo original: [{link}]({link})\n\n"
            section_text += f"{file_data.get('analysis', '')}\n\n"

            if selected_speeches:
                section_text += "### Trechos selecionados:\n\n"
                for speech in selected_speeches:
                    timestamp = speech.get('timestamp')
                    start = timestamp[0:8]
                    h, m, s = map(int, start.split(':'))
                    start_seconds = h * 3600 + m * 60 + s
                    link_with_timestamp = f"{link}&t={start_seconds}s"

                    section_text += f"### Trecho - Início em {start}\n\n"
                    section_text += f"Link para o trecho do vídeo: [{link_with_timestamp}]({link_with_timestamp})\n\n"
                    section_text += f"{speech.get('analysis', '')}\n\n"
                section_text += "\n"
            else:
                section_text += "**Nenhum trecho selecionado.**\n\n"

            pdf.add_section(Section(section_text))

    output_file_pdf = f"{output_file}.pdf"
    pdf.save(output_file_pdf)

def main():
    """
    Função principal para executar tarefas com base nos argumentos da linha de comando.
    """
    if len(sys.argv) < 2:
        print("Uso: python transcr.py <nome_da_função>")
        sys.exit(1)

    function_name = sys.argv[1]

    if function_name == "download_transcriptions":
        download_transcriptions()
    elif function_name == "list_videos":
        print(list_videos())
    else:
        print(f"Função {function_name} não reconhecida.")

if __name__ == "__main__":
    main()
