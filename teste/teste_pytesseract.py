from PIL import Image
import pytesseract

# No Kali Linux, o Tesseract já estará no caminho padrão, então geralmente não é necessário definir o caminho do executável
# Caso contrário, defina o caminho para o Tesseract como segue:
# pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Carregar uma imagem (substitua pelo caminho da sua imagem)
image = Image.open('images.png')

# Extrair texto da imagem
text = pytesseract.image_to_string(image)

# Exibir o texto extraído
print(text)
