"""Aprimoramento conservador de textos de currículo, sem inventar qualificações."""
import re
import unicodedata


def _normalizar_inicio(texto: str) -> str:
    texto = texto.strip()
    return texto[:1].upper() + texto[1:] if texto else ""


def melhorar_texto_ia(secao_curriculo: str, texto_original: str) -> str:
    texto = _normalizar_inicio(texto_original)
    if not texto:
        return texto

    secao = (secao_curriculo or "").strip().casefold()
    if secao == "resumo profissional".casefold():
        return melhorar_resumo_profissional(texto)
    if secao == "experiências profissionais".casefold():
        return melhorar_experiencia_profissional(texto)
    if secao == "formação acadêmica".casefold():
        return melhorar_formacao_academica(texto)
    if secao == "habilidades".casefold():
        return melhorar_habilidades(texto)
    return melhorar_texto_generico(texto)


def melhorar_resumo_profissional(texto: str) -> str:
    texto = _normalizar_inicio(texto)
    texto = re.sub(r"\bgosto de trabalhar\b", "Tenho facilidade para trabalhar", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bsou uma pessoa\b", "Sou um profissional", texto, flags=re.IGNORECASE)
    # Não acrescenta objetivos, anos de experiência ou competências que o usuário não informou.
    return texto


def melhorar_experiencia_profissional(texto: str) -> str:
    texto = _normalizar_inicio(texto)
    substituicoes = {
        r"\btrabalhei como\b": "Atuei como",
        r"\bfazia\b": "Realizava",
        r"\bajudava\b": "Auxiliava",
        r"\batendia clientes\b": "Prestava atendimento ao cliente",
        r"\borganizava produtos\b": "Organizava produtos",
        r"\bcuidava\b": "Era responsável por",
        r"\bfiz\b": "Realizei",
        r"\bconsegui\b": "Alcancei",
    }
    for antigo, novo in substituicoes.items():
        texto = re.sub(antigo, novo, texto, flags=re.IGNORECASE)
    # Não cria métricas nem resultados não fornecidos pelo candidato.
    return texto


def melhorar_formacao_academica(texto: str) -> str:
    texto = _normalizar_inicio(texto)
    texto = re.sub(r"\bestudei na\b", "Estudos realizados na", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bme formei em\b", "Formação em", texto, flags=re.IGNORECASE)
    # Evita dizer "graduado" sem confirmação explícita de conclusão.
    return texto


def _sem_acentos(texto: str) -> str:
    return "".join(
        caractere
        for caractere in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caractere)
    )


def melhorar_habilidades(texto: str) -> str:
    # Aceita vírgulas e quebras de linha; não presume nível de proficiência.
    itens = re.split(r"[,;\n]+", texto)
    normalizadas = []
    vistos = set()
    for item in itens:
        habilidade = item.strip()
        if not habilidade:
            continue
        chave = _sem_acentos(habilidade).casefold()
        if chave in vistos:
            continue
        vistos.add(chave)
        normalizadas.append(habilidade)
    return "\n".join(normalizadas)


def melhorar_texto_generico(texto: str) -> str:
    texto = _normalizar_inicio(texto)
    texto = re.sub(r"\bvc\b", "você", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bvoce\b", "você", texto, flags=re.IGNORECASE)
    return texto
