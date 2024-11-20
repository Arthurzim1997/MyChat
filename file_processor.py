import json
import os
import shutil
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pytesseract
from PIL import Image
import whisper
import moviepy.editor as mp
import docx
import fitz  # PyMuPDF
from colorama import Fore, Style, init
import secrets  # Importado para gerar o sufixo aleatório
import subprocess

# Inicializar colorama e logging
init(autoreset=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Caminho para a pasta do script (mesma pasta onde o script está localizado)
base_dir = Path(__file__).parent

# Diretórios relativos à pasta do script
input_dir = base_dir / "input_dir"
output_dir = base_dir / "output_dir"
processed_dir = base_dir / "processed_dir"
text_dir = input_dir / 'text'  # Diretório para salvar imagens temporárias usadas pelo PyMuPDF

# Subpastas que devem existir dentro de 'input_dir'
subfolders = ['audio', 'code', 'images', 'text', 'video']

# Garantir que as pastas principais e as subpastas existam
for directory in [input_dir, output_dir, processed_dir]:
    if not directory.exists():
        logging.info(f"{Fore.GREEN}Diretório {directory} não encontrado. Criando...")
        directory.mkdir(parents=True, exist_ok=True)

# Garantir que as subpastas dentro de 'input_dir', 'output_dir' e 'processed_dir' existam
for subfolder in subfolders:
    for base_path in [input_dir, output_dir, processed_dir]:
        subfolder_path = base_path / subfolder
        if not subfolder_path.exists():
            logging.info(f"{Fore.GREEN}Subpasta {subfolder_path} não encontrada. Criando...")
            subfolder_path.mkdir(parents=True, exist_ok=True)

# Função para garantir que a estrutura de pastas seja criada
def create_dir_structure(file_path, base_dir):
    new_dir = base_dir / file_path.relative_to(input_dir).parent
    new_dir.mkdir(parents=True, exist_ok=True)
    return new_dir / file_path.name

# Função para gerar um sufixo aleatório
def generate_random_suffix():
    return secrets.token_urlsafe(8)  # Gera um sufixo aleatório de 8 caracteres

# Função para processar arquivos de imagem (OCR com Tesseract)
def process_image(file_path):
    try:
        logging.info(f"{Fore.CYAN}Processando {file_path} com OCR (Tesseract)...")
        image = Image.open(file_path)
        custom_config = r'--oem 3 --psm 3 --dpi 300'
        text = pytesseract.image_to_string(image, lang='por', config=custom_config)

        if text:
            json_data = {
                "file_name": file_path.name,
                "file_type": "image",
                "content": text
            }

            # Gerar nome de arquivo JSON com sufixo aleatório
            random_suffix = generate_random_suffix()
            json_file_name = f"{file_path.stem}-{random_suffix}.json"
            json_output_path = output_dir / file_path.relative_to(input_dir).parent / json_file_name
            json_output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(json_output_path, 'w', encoding='utf-8') as json_file:
                json.dump(json_data, json_file, ensure_ascii=False, indent=4)

            logging.info(f"{Fore.GREEN}Texto extraído e salvo em {json_output_path}")
            return json_output_path
        else:
            logging.warning(f"{Fore.YELLOW}Nenhum texto extraído da imagem {file_path}.")
            return None
    except Exception as e:
        logging.error(f"{Fore.RED}Erro ao processar {file_path}: {e}")
        return None

# Função para processar arquivos de áudio e video (usando Whisper)
model = whisper.load_model("small")
def process_audio_video(file_path):
    try:
        logging.info(f"{Fore.CYAN}Processando áudio {file_path} com Whisper...")
        result = model.transcribe(str(file_path))

        if result["text"]:
            # Verificando se é áudio ou vídeo
            media_type = "audio" if file_path.suffix.lower() in [
                '.mp3', '.wav', '.flac', '.au', '.dts', '.m4a', '.mp2', '.ogg',
                '.opus', '.spx', '.wma', '.aiff', '.ac3', '.aac', '.aif', '.caf', 
                '.eac3', '.pcm'
            ] else "video"  # Caso contrário, consideramos como vídeo

            json_data = {
                "file_name": file_path.name,
                "file_type": media_type,  # 'audio' ou 'video'
                "content": result["text"]
            }

            # Gerar nome de arquivo JSON com sufixo aleatório
            random_suffix = generate_random_suffix()
            json_file_name = f"{file_path.stem}-{random_suffix}.json"
            json_output_path = output_dir / file_path.relative_to(input_dir).parent / json_file_name
            json_output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(json_output_path, 'w', encoding='utf-8') as json_file:
                json.dump(json_data, json_file, ensure_ascii=False, indent=4)

            logging.info(f"{Fore.GREEN}Texto extraído e salvo em {json_output_path}")
            return json_output_path
        else:
            logging.warning(f"{Fore.YELLOW}Nenhuma transcrição encontrada para áudio/video {file_path}.")
            return None
    except Exception as e:
        logging.error(f"{Fore.RED}Erro ao processar áudio/video {file_path}: {e}")
        return None

    ##### (Subfunção do PyMuPDF para processar imagem com OCR usando Tesseract)
def process_image_pdf(img_path):
    try:
        logging.info(f"{Fore.CYAN}Processando {img_path} com OCR (Tesseract)...")
        image = Image.open(img_path)  # Usar img_path aqui
        custom_config = r'--oem 3 --psm 3 --dpi 300'
        text = pytesseract.image_to_string(image, lang='por', config=custom_config)
        return text
    except Exception as e:
        logging.error(f"{Fore.RED}Erro ao processar imagem {img_path}: {e}")
        return None

# Função para processar arquivos PDF usando PyMuPDF (fitz) e OCR se necessário
def process_pdf(file_path):
    try:
        logging.info(f"{Fore.CYAN}Processando PDF {file_path} com PyMuPDF(fitz)...")
        
        doc = fitz.open(file_path)
        text = ""  # Inicializar como string vazia para armazenar o texto extraído
        images_processed = False  # Flag para verificar se as imagens foram processadas
        
        # Definir text_dir para armazenar as imagens temporárias
        text_dir = input_dir / 'text'  # Supondo que input_dir já está definido
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text("text")  # Extrair texto da página
            
            if page_text:
                text += page_text  # Adiciona o texto extraído da página
            else:
                # Se não houver texto, usar OCR para tentar extrair texto das imagens
                logging.info(f"{Fore.CYAN}Nenhum texto extraído da página {page_num + 1}, tentando OCR...")
                
                # Obter a imagem da página e salvar temporariamente em 'text' (input_dir/text)
                pix = page.get_pixmap()  # Criar a imagem da página
                img_path = text_dir / f"page_{page_num + 1}.png"
                img_path.parent.mkdir(parents=True, exist_ok=True)  # Garantir que o diretório exista
                pix.save(img_path)
                
                # Usar OCR (Tesseract) para extrair texto da imagem
                text_from_image = process_image_pdf(img_path)  # Processando a imagem com OCR
                
                if text_from_image:  # Verificar se o OCR retornou texto
                    text += text_from_image  # Adiciona o texto extraído via OCR à variável 'text'
                
                # Excluir a imagem após o processamento
                if img_path.exists():
                    os.remove(img_path)
                    logging.info(f"{Fore.YELLOW}Imagem temporária {img_path} excluída após processamento.")
                
                images_processed = True  # Marcar que uma imagem foi processada

        # Verificar se algum texto foi extraído (do PDF ou das imagens)
        if text:
            json_data = {
                "file_name": file_path.name,
                "file_type": "pdf",
                "content": text
            }

           # Gerar nome de arquivo JSON com sufixo aleatório
            random_suffix = generate_random_suffix()
            json_file_name = f"{file_path.stem}-{random_suffix}.json"
            json_output_path = processed_dir / file_path.relative_to(input_dir).parent / json_file_name
            json_output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(json_output_path, 'w', encoding='utf-8') as json_file:
                json.dump(json_data, json_file, ensure_ascii=False, indent=4)

            logging.info(f"{Fore.GREEN}Texto extraído e salvo em {json_output_path}")
        else:
            logging.warning(f"{Fore.YELLOW}Nenhum texto extraído do PDF {file_path}.")
            return None
    except fitz.FitzError as e:
        logging.error(f"{Fore.RED}Erro ao abrir o PDF {file_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"{Fore.RED}Erro inesperado ao processar PDF {file_path}: {e}")
        return None

    #### Subfunção para converter arquivo .doc para .docx usando LibreOffice
def convert_doc_to_docx(doc_path):
    try:
        if doc_path.suffix.lower() == '.doc':
            logging.info(f"{Fore.GREEN}Convertendo arquivo {doc_path} de .doc para .docx usando LibreOffice")
            
            # Log para garantir que a função está sendo chamada
            logging.info(f"{Fore.GREEN}Iniciando conversão de {doc_path}")
            
            # Comando para usar o LibreOffice em modo headless
            cmd = [
                "soffice", "--headless", "--convert-to", "docx", 
                "--outdir", str(doc_path.parent.resolve()), str(doc_path.resolve())
            ]
            
            # Imprime o comando que será executado no log
            logging.info(f"Comando de conversão: {' '.join(cmd)}")
            
            # Rodando o comando e capturando a saída para depuração
            result = subprocess.run(cmd, capture_output=True, text=True)

            # Logando a saída e erro
            if result.stdout:
                logging.info(f"{Fore.GREEN}Saída do LibreOffice: {result.stdout}")
            if result.stderr:
                logging.error(f"{Fore.RED}Erro no LibreOffice: {result.stderr}")
            
            if result.returncode != 0:
                logging.error(f"{Fore.RED}Erro na conversão: {result.returncode}")
                return None

            # Verificando se o arquivo convertido realmente existe
            docx_path = doc_path.with_suffix('.docx')
            if docx_path.exists():
                logging.info(f"{Fore.GREEN}Arquivo convertido para {docx_path}")
                return docx_path
            else:
                logging.error(f"{Fore.RED}Arquivo convertido não foi encontrado: {docx_path}")
                return None
        else:
            logging.info(f"{Fore.YELLOW}Arquivo {doc_path} não é .doc, mantendo como está.")
            return doc_path  # Se não for .doc, apenas retorna o arquivo original
    except Exception as e:
        logging.error(f"{Fore.RED}Erro ao converter o arquivo {doc_path} para DOCX: {e}")
        return None

# Função para processar arquivos DOCX
def process_docx(file_path):
    try:
        # Verificar e converter arquivos .doc para .docx
        file_path = convert_doc_to_docx(file_path) if file_path.suffix.lower() == '.doc' else file_path
        if not file_path:
            return None  # Se a conversão falhou, não prosseguir

        logging.info(f"Processando arquivo DOCX: {file_path}")

        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])

        if text:
            json_data = {
                "file_name": file_path.name,
                "file_type": "docx",
                "content": text
            }

            # Gerar nome de arquivo JSON com sufixo aleatório
            random_suffix = generate_random_suffix()
            json_file_name = f"{file_path.stem}-{random_suffix}.json"
            json_output_path = output_dir / file_path.relative_to(input_dir).parent / json_file_name
            json_output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(json_output_path, 'w', encoding='utf-8') as json_file:
                json.dump(json_data, json_file, ensure_ascii=False, indent=4)

            logging.info(f"{Fore.GREEN}Texto extraído e salvo em {json_output_path}")
            return json_output_path
        else:
            logging.warning(f"{Fore.YELLOW}Nenhum texto extraído do DOCX {file_path}.")
            return None
    except (FileNotFoundError, IsADirectoryError) as e:
        logging.error(f"Erro de arquivo ao processar {file_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"{Fore.RED}Erro inesperado ao processar o DOCX {file_path}: {e}")
        return None

# Função para processar arquivos de código
def process_code(file_path):
    try:
        logging.info(f"{Fore.CYAN}Processando código {file_path}...")
        with open(file_path, 'r', encoding='utf-utf-8') as f:
            code = f.read()

        if code:
            json_data = {
                "file_name": file_path.name,
                "file_type": "code",
                "content": code
            }

            # Gerar nome de arquivo JSON com sufixo aleatório
            random_suffix = generate_random_suffix()
            json_file_name = f"{file_path.stem}-{random_suffix}.json"
            json_output_path = output_dir / file_path.relative_to(input_dir).parent / json_file_name
            json_output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(json_output_path, 'w', encoding='utf-8') as json_file:
                json.dump(json_data, json_file, ensure_ascii=False, indent=4)

            logging.info(f"{Fore.GREEN}Código extraído e salvo em {json_output_path}")
            return json_output_path
        else:
            logging.warning(f"{Fore.YELLOW}Nenhum código extraído de {file_path}.")
            return None
    except Exception as e:
        logging.error(f"{Fore.RED}Erro ao processar código {file_path}: {e}")
        return None

# Função para processar um único arquivo
def process_file(file):
    try:
        output_path = create_dir_structure(file, output_dir)
        processed_path = create_dir_structure(file, processed_dir)

        text_file = None
        if file.suffix.lower() in [
            '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', 
            '.pbm', '.pgm', '.ppm'
        ]:
            text_file = process_image(file)

        elif file.suffix.lower() in [
            '.mp3', '.wav', '.flac', '.au', '.dts', '.m4a', '.mp2', '.ogg',
            '.opus', '.spx', '.wma', '.aiff', '.ac3', '.aac', '.aif', '.caf', 
            '.eac3', '.pcm', '.mp4', '.flv', '.avi', '.mov', '.mkv'
            ]:
            text_file = process_audio_video(file)

        elif file.suffix.lower() == '.pdf':
            text_file = process_pdf(file)

        elif file.suffix.lower() == '.docx':
            text_file = process_docx(file)

        elif file.suffix.lower() in ['.py', '.java', '.cpp', '.js', '.html']:
            text_file = process_code(file)

        # Mover o arquivo original para a pasta de saída
        shutil.move(file, output_path)
        logging.info(f"{Fore.BLUE}Arquivo original movido para {output_path}")

        # Se o arquivo de texto foi gerado, mover para processed_dir
        if text_file:
            processed_json_path = processed_dir / text_file.relative_to(output_dir)
            processed_json_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(text_file, processed_json_path)
            logging.info(f"{Fore.GREEN}Arquivo JSON movido para {processed_json_path}")

    except Exception as e:
        logging.error(f"{Fore.RED}Erro ao processar o arquivo {file}: {e}")

# Função principal para processar todos os tipos de arquivos
def process_files():
    with ThreadPoolExecutor(max_workers=1) as executor:
        for subfolder in subfolders:
            subfolder_path = input_dir / subfolder
            if subfolder_path.exists():
                # Usando rglob para encontrar todos os arquivos em subpastas recursivamente
                for file in subfolder_path.rglob('*'):
                    if file.is_file():
                        executor.submit(process_file, file)

if __name__ == "__main__":
    process_files()
