# main.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from resume_generator import gerar_curriculo_html, converter_html_para_pdf
from fastapi.responses import FileResponse
import os
import logging # Importar logging

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Configuração do CORS
# Adapte 'allow_origins' para os domínios do seu frontend em produção
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500", "http://localhost:3000"], # Exemplo: portas comuns de desenvolvimento
    allow_credentials=True,
    allow_methods=["*"], # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"], # Permite todos os cabeçalhos
)

class DadosCurriculo(BaseModel):
    # Validações mais robustas com Pydantic
    nome: str = Field(..., min_length=3, max_length=100, description="Nome completo do candidato.")
    email: EmailStr = Field(..., description="Endereço de e-mail válido.")
    telefone: str = Field(
        ...,
        pattern=r"^\+?[0-9\s\-\(\)]{7,20}$", # Regex simples para telefone (permite +,-,(), espaços e dígitos)
        description="Número de telefone (ex: +55 (11) 98765-4321)."
    )
    resumo: str = Field(..., min_length=50, description="Resumo profissional ou objetivo de carreira.")
    experiencias: str = Field(..., min_length=20, description="Experiências profissionais, separadas por linha ou parágrafo.")
    formacao: str = Field(..., min_length=20, description="Formação acadêmica.")
    habilidades: str = Field(..., min_length=10, description="Lista de habilidades.")

def remover_arquivo(path: str):
    """Função para remover o arquivo após o envio da resposta."""
    try:
        os.remove(path)
        logger.info(f"Arquivo temporário removido: {path}")
    except OSError as e:
        logger.error(f"Erro ao remover arquivo temporário {path}: {e}")

@app.post("/gerar_curriculo")
async def gerar_curriculo(dados: DadosCurriculo, background_tasks: BackgroundTasks):
    """
    Endpoint para gerar um currículo em PDF a partir dos dados fornecidos.
    """
    try:
        html = gerar_curriculo_html(dados)
        caminho_pdf = converter_html_para_pdf(html, dados.nome)

        # Adiciona a tarefa de apagar o PDF depois que a resposta for enviada
        background_tasks.add_task(remover_arquivo, caminho_pdf)

        logger.info(f"Currículo gerado com sucesso e disponível em: {caminho_pdf}")
        return FileResponse(caminho_pdf, filename="curriculo.pdf", media_type='application/pdf')
    except HTTPException as http_exc:
        raise http_exc # Levanta a exceção HTTP já tratada em converter_html_para_pdf
    except Exception as e:
        logger.error(f"Erro inesperado no endpoint /gerar_curriculo: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor ao gerar o currículo.")