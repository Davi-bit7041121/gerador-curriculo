"""API do Gerador de Currículos com autenticação e Firestore."""
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from hashlib import sha256

import firebase_admin
import jwt
from firebase_admin import firestore
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pwdlib import PasswordHash

from resume_generator import converter_html_para_pdf
import json
import urllib.error
import urllib.request

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Gerador de Currículo API",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url=None,
)

origens_configuradas = os.getenv("FRONTEND_ORIGINS", "")
origens = [item.strip() for item in origens_configuradas.split(",") if item.strip()]
if not origens:
    origens = ["http://localhost:5500", "http://127.0.0.1:5500", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

password_hasher = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)


class DadosCadastro(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    nome_usuario: str = Field(alias="nomeUsuario", min_length=3, max_length=50)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    nome_completo: str = Field(alias="nomeCompleto", min_length=3, max_length=100)
    telefone: str = Field(
        alias="telefone",
        min_length=7,
        max_length=20,
        pattern=r"^\+?[0-9\s\-\(\)]+$",
    )


class DadosLogin(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    senha: str = Field(min_length=1, max_length=128)


class DadosCurriculo(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    telefone: str = Field(..., min_length=7, max_length=20, pattern=r"^\+?[0-9\s\-\(\)]+$")
    resumo: str = Field(..., min_length=50, max_length=3000)
    experiencias: str = Field(..., min_length=20, max_length=6000)
    formacao: str = Field(..., min_length=20, max_length=3000)
    habilidades: str = Field(..., min_length=10, max_length=2000)


class DadosMelhoria(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    secao: str = Field(min_length=3, max_length=80)
    texto: str = Field(min_length=1, max_length=6000)


@lru_cache(maxsize=1)
def get_database():
    """Obtém o Firestore usando as credenciais seguras do ambiente do Google Cloud."""
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app()
    return firestore.client()


def get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "")
    if len(secret.encode("utf-8")) < 32:
        raise HTTPException(
            status_code=503,
            detail="A autenticação ainda não foi configurada no servidor.",
        )
    return secret


def _chave_unica(tipo: str, valor: str) -> str:
    return sha256(f"{tipo}:{valor}".encode("utf-8")).hexdigest()


def _criar_token(usuario_id: str) -> str:
    agora = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": usuario_id, "iat": agora, "exp": agora + timedelta(hours=12)},
        get_jwt_secret(),
        algorithm="HS256",
    )


def usuario_autenticado(
    credenciais: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """Valida o ID token emitido pelo Firebase Authentication."""
    if credenciais is None or credenciais.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Faça login para continuar.")
    project_id = os.getenv("FIREBASE_PROJECT_ID", "curriculoiagerador-ef3dc")
    try:
        payload = google_id_token.verify_token(
            credenciais.credentials,
            GoogleAuthRequest(),
            audience=project_id,
            certs_url="https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com",
        )
        if payload.get("iss") != f"https://securetoken.google.com/{project_id}":
            raise ValueError("Emissor do token inválido.")
        usuario_id = payload.get("sub")
        if not usuario_id:
            raise ValueError("Token sem identificador de usuário.")
        return usuario_id
    except Exception as exc:
        logger.info("Token Firebase inválido ou expirado: %s", type(exc).__name__)
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada. Entre novamente.") from exc


def _dados_publicos(usuario_id: str, dados: dict) -> dict:
    return {
        "id": usuario_id,
        "nomeUsuario": dados["nome_usuario"],
        "nomeCompleto": dados["nome_completo"],
        "email": dados["email"],
        "telefone": dados["telefone"],
        "plano": dados.get("plano"),
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/cadastrar", status_code=201)
def cadastrar(dados: DadosCadastro):
    """Cria uma conta; senhas são armazenadas somente como hash Argon2."""
    # Valida a configuração antes de gravar a conta no banco.
    get_jwt_secret()
    email = str(dados.email).strip().lower()
    nome_usuario = dados.nome_usuario.strip()
    username_normalizado = nome_usuario.casefold()
    usuario_id = str(uuid.uuid4())

    registro = {
        "nome_usuario": nome_usuario,
        "nome_usuario_normalizado": username_normalizado,
        "nome_completo": dados.nome_completo.strip(),
        "email": email,
        "telefone": dados.telefone.strip(),
        "senha_hash": password_hasher.hash(dados.senha),
        "plano": None,
        "criado_em": firestore.SERVER_TIMESTAMP,
    }

    try:
        db = get_database()
        email_ref = db.collection("chaves_conta").document(_chave_unica("email", email))
        username_ref = db.collection("chaves_conta").document(
            _chave_unica("usuario", username_normalizado)
        )
        user_ref = db.collection("usuarios").document(usuario_id)
        transaction = db.transaction()

        @firestore.transactional
        def salvar_conta(transacao):
            email_existente = email_ref.get(transaction=transacao)
            usuario_existente = username_ref.get(transaction=transacao)
            if email_existente.exists:
                raise HTTPException(status_code=409, detail="Este e-mail já está cadastrado.")
            if usuario_existente.exists:
                raise HTTPException(status_code=409, detail="Este nome de usuário já está em uso.")
            transacao.create(email_ref, {"usuario_id": usuario_id})
            transacao.create(username_ref, {"usuario_id": usuario_id})
            transacao.create(user_ref, registro)

        salvar_conta(transaction)
        logger.info("Nova conta criada: id=%s", usuario_id)
        return {
            "token": _criar_token(usuario_id),
            "usuario": _dados_publicos(usuario_id, registro),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Falha ao criar conta.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível acessar o banco de dados. Tente novamente mais tarde.",
        ) from exc


@app.post("/login")
def login(dados: DadosLogin):
    """Autentica por e-mail e senha, sem revelar se o e-mail existe."""
    email = str(dados.email).strip().lower()
    try:
        db = get_database()
        chave_ref = db.collection("chaves_conta").document(_chave_unica("email", email))
        chave = chave_ref.get()
        if not chave.exists:
            raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")

        usuario_id = chave.to_dict().get("usuario_id")
        usuario_ref = db.collection("usuarios").document(usuario_id)
        snapshot = usuario_ref.get()
        if not snapshot.exists:
            raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")

        registro = snapshot.to_dict()
        if not password_hasher.verify(dados.senha, registro.get("senha_hash", "")):
            raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")

        return {
            "token": _criar_token(usuario_id),
            "usuario": _dados_publicos(usuario_id, registro),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Falha ao autenticar usuário.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível acessar o serviço de autenticação. Tente novamente.",
        ) from exc


def _melhorar_com_gemini(secao: str, texto: str) -> str:
    """Reescreve um trecho de currículo com Gemini, usando somente a chave do servidor."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="A IA ainda não foi configurada. Adicione GEMINI_API_KEY nas variáveis do Vercel.",
        )

    prompt = (
        "Você é um especialista em recrutamento e redação de currículos no Brasil. "
        "Reescreva o trecho abaixo em português brasileiro, com linguagem profissional, "
        "clara, objetiva e natural. Melhore a estrutura e a força dos verbos; elimine "
        "repetições e erros. Preserve rigorosamente todos os fatos informados. "
        "NÃO invente empresas, cargos, datas, cursos, resultados, números, ferramentas, "
        "competências, níveis de domínio ou anos de experiência. Se faltarem dados, "
        "não os complete por conta própria. Não transforme experiência informal em "
        "emprego formal. Retorne somente o texto revisado, sem aspas, explicações ou "
        "títulos adicionais.\n\n"
        f"Seção do currículo: {secao}\n"
        f"Texto original:\n{texto}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.35, "maxOutputTokens": 1200},
    }
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-3.8-flash:generateContent"
        f"?key={api_key}"
    )
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            resultado = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Não registra nem devolve a URL, pois ela contém a chave da API.
        logger.warning("Gemini recusou a solicitação; HTTP %s.", exc.code)
        if exc.code == 429:
            raise HTTPException(
                status_code=429,
                detail="Limite gratuito da IA atingido. Aguarde um pouco e tente novamente.",
            ) from exc
        if exc.code in (401, 403):
            raise HTTPException(
                status_code=503,
                detail="A chave gratuita da IA está inválida ou sem acesso ao modelo.",
            ) from exc
        raise HTTPException(
            status_code=502,
            detail="O serviço de IA está temporariamente indisponível.",
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.warning("Gemini indisponível ou timeout: %s", type(exc).__name__)
        raise HTTPException(
            status_code=504,
            detail="A IA demorou demais para responder. Tente novamente.",
        ) from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning("Resposta inválida recebida do Gemini.")
        raise HTTPException(
            status_code=502,
            detail="A IA retornou uma resposta inválida. Tente novamente.",
        ) from exc

    candidatos = resultado.get("candidates") or []
    partes = (
        candidatos[0].get("content", {}).get("parts", [])
        if candidatos else []
    )
    texto_melhorado = "\n".join(
        parte.get("text", "").strip()
        for parte in partes
        if parte.get("text", "").strip()
    ).strip()
    if not texto_melhorado:
        raise HTTPException(
            status_code=502,
            detail="A IA não conseguiu revisar esse trecho. Tente novamente.",
        )
    return texto_melhorado


@app.post("/melhorar_texto")
def melhorar_texto(
    dados: DadosMelhoria,
    usuario_id: str = Depends(usuario_autenticado),
):
    """Reescreve um trecho com IA generativa para usuários autenticados."""
    try:
        texto_melhorado = _melhorar_com_gemini(dados.secao, dados.texto)
        return {"texto_melhorado": texto_melhorado}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Erro inesperado ao melhorar texto do currículo.")
        raise HTTPException(
            status_code=500,
            detail="Não foi possível melhorar o texto. Tente novamente.",
        ) from exc


def remover_arquivo(path: str) -> None:
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        logger.exception("Não foi possível remover um PDF temporário.")


@app.post("/gerar_curriculo")
def gerar_curriculo(
    dados: DadosCurriculo,
    background_tasks: BackgroundTasks,
    usuario_id: str = Depends(usuario_autenticado),
):
    """Gera PDF somente para usuários autenticados."""
    caminho_pdf = None
    try:
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
