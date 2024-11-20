import requests
from github import Github
import logging

# Configuração da API do GitHub
GITHUB_TOKEN = "your_github_token"  # Substitua pelo seu token do GitHub
g = Github(GITHUB_TOKEN)

# Inicializando o logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_repositories(query):
    try:
        logging.info(f"Buscando repositórios com a query: {query}")
        repositories = g.search_repositories(query=query)
        return repositories
    except Exception as e:
        logging.error(f"Erro ao buscar repositórios: {e}")
        return []

def fetch_code_from_repo(repo_name):
    try:
        logging.info(f"Buscando código do repositório: {repo_name}")
        repo = g.get_repo(repo_name)
        files = repo.get_contents("")
        code = {}
        for file in files:
            if file.name.endswith(".py"):
                code[file.name] = file.decoded_content.decode()
        return code
    except Exception as e:
        logging.error(f"Erro ao buscar código do repositório {repo_name}: {e}")
        return {}

if __name__ == "__main__":
    query = "machine learning"
    repos = fetch_repositories(query)
    for repo in repos:
        logging.info(f"Fetching code from: {repo.name}")
        code = fetch_code_from_repo(repo.name)
        for filename, content in code.items():
            logging.info(f"File: {filename}")
            logging.info(content[:500])  # Imprimir os primeiros 500 caracteres do código
