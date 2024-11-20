import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QProgressBar
from PyQt5.QtCore import Qt
from whisper_transcriber import transcribe_audio
from image_generator import generate_image
from github_integration import fetch_code_from_github
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ChatInterface(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Chat Interface")
        self.setGeometry(100, 100, 500, 400)

        self.layout = QVBoxLayout()

        # Display de chat
        self.chat_display = QTextEdit(self)
        self.chat_display.setReadOnly(True)
        self.layout.addWidget(self.chat_display)

        # Caixa de entrada
        self.user_input = QLineEdit(self)
        self.user_input.setPlaceholderText("Digite sua mensagem ou envie um arquivo...")
        self.layout.addWidget(self.user_input)

        # Barra de progresso
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.layout.addWidget(self.progress_bar)

        # Botão de envio
        self.submit_button = QPushButton("Enviar", self)
        self.submit_button.clicked.connect(self.send_message)
        self.layout.addWidget(self.submit_button)

        # Botão para abrir o seletor de arquivos
        self.file_button = QPushButton("Enviar Arquivo", self)
        self.file_button.clicked.connect(self.open_file_dialog)
        self.layout.addWidget(self.file_button)

        self.setLayout(self.layout)

    def send_message(self):
        user_message = self.user_input.text()
        self.chat_display.append(f"User: {user_message}")
        self.user_input.clear()

        if user_message.lower().startswith("audio:"):
            file_path = user_message.split(":", 1)[1].strip()
            ai_response = self.process_audio(file_path)
        elif user_message.lower().startswith("imagem:"):
            prompt = user_message.split(":", 1)[1].strip()
            ai_response = self.process_image_generation(prompt)
        elif user_message.lower().startswith("github:"):
            repo_info = user_message.split(":", 1)[1].strip()
            ai_response = self.process_github_code(repo_info)
        else:
            ai_response = self.process_text_message(user_message)

        self.chat_display.append(f"AI: {ai_response}")

    def process_text_message(self, message):
        return f"Você disse: {message}"

    def process_audio(self, audio_file):
        try:
            transcription = transcribe_audio(audio_file)
            return f"Áudio transcrito: {transcription}"
        except Exception as e:
            return f"Erro ao transcrever áudio: {str(e)}"

    def process_image_generation(self, prompt):
        try:
            image_path = generate_image(prompt)
            return f"Imagem gerada em {image_path}"
        except Exception as e:
            return f"Erro ao gerar imagem: {str(e)}"

    def process_github_code(self, repo_info):
        try:
            code = fetch_code_from_github(repo_info)
            return f"Código obtido do GitHub: {code[:200]}..."
        except Exception as e:
            return f"Erro ao buscar código no GitHub: {str(e)}"

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo")
        if file_path:
            self.chat_display.append(f"Arquivo selecionado: {file_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatInterface()
    window.show()
    sys.exit(app.exec_())
