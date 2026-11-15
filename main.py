"""API principal do gerador de currículos."""
import logging
import os

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from resume_generator import converter_html_para_pdf

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Gerador de Currículo API",
    version="1.1.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url=None,
)

# Em produção, informe os domínios do frontend em FRONTEND_ORIGINS,
# separados por vírgula. Não use "*" junto com credenciais.
origens_configuradas = os.getenv("FRONTEND_ORIGINS", "")
origens = [
    origem.strip()
    for origem in origens_configuradas.split(",")
    if origem.strip()
]
if not origens:
    origens = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


class DadosCurriculo(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    telefone: str = Field(
        ...,
        min_length=7,
        max_length=20,
        pattern=r"^\+?[0-9\s\-\(\)]+$",
    )
    resumo: str = Field(..., min_length=50, max_length=3000)
    experiencias: str = Field(..., min_length=20, max_length=6000)
    formacao: str = Field(..., min_length=20, max_length=3000)
    habilidades: str = Field(..., min_length=10, max_length=2000)


def remover_arquivo(path: str) -> None:
    """Remove o PDF temporário depois que a resposta for enviada."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        logger.exception("Não foi possível remover um PDF temporário.")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/gerar_curriculo")
async def gerar_curriculo(
    dados: DadosCurriculo,
    background_tasks: BackgroundTasks,
):
    """Gera e devolve um currículo em PDF."""
    caminho_pdf = None
    try:
        # Passa o objeto completo: passar apenas dados.nome causava ValueError
        # no gerador, que precisa de todos os campos para montar o documento.
        caminho_pdf = converter_html_para_pdf("", dados)
        background_tasks.add_task(remover_arquivo, caminho_pdf)

        return FileResponse(
            caminho_pdf,
            filename="curriculo.pdf",
            media_type="application/pdf",
            headers={"Cache-Control": "no-store"},
        )
    except HTTPException:
        raise
    except Exception as exc:
        if caminho_pdf:
            remover_arquivo(caminho_pdf)
        logger.exception("Erro inesperado ao gerar currículo.")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao gerar o currículo. Tente novamente.",
        ) from exc
