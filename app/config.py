"""Configurações globais da aplicação Moneytora."""
from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API = os.getenv("GROQ_API")
# Não levantamos exceções automaticamente para permitir que o restante da aplicação seja
# carregado em ambientes onde a chave ainda não foi configurada. Os módulos que dependem
# diretamente da chave devem tratar a ausência de forma explícita.
