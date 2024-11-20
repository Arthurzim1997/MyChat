import fitz  # PyMuPDF
import json

# Solicitar o nome do arquivo PDF no terminal
pdf_file = input("Digite o nome do arquivo PDF (com extensão): ")

# Solicitar o nome do arquivo JSON de saída
json_file = input("Digite o nome do arquivo JSON de saída (com extensão): ")

try:
    # Abrir o arquivo PDF
    doc = fitz.open(pdf_file)
    data = {}

    # Percorrer todas as páginas do PDF
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)  # Carregar a página
        text = page.get_text("text")   # Extrair o texto em formato simples
        data[f"page_{page_num + 1}"] = text.strip()  # Adicionar ao dicionário

    # Salvar os dados extraídos em um arquivo JSON
    with open(json_file, "w") as json_output:
        json.dump(data, json_output, indent=4)

    print(f"Texto extraído do PDF foi salvo em {json_file}.")
except Exception as e:
    print(f"Erro ao processar o arquivo: {e}")
