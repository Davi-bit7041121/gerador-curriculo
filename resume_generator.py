# resume_generator.py
"""Geração segura de currículos em PDF."""
import logging
import os
import tempfile
from html import escape as html_escape

from fastapi import HTTPException
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)


def _texto_para_paragrafo(valor: str) -> str:
    """Escapa conteúdo do usuário antes de entregá-lo ao parser XML do ReportLab."""
    linhas = str(valor or "").splitlines()
    return "<br/>".join(html_escape(linha, quote=True) for linha in linhas)


def gerar_curriculo_html(dados):
    """Mantida por compatibilidade com versões anteriores do projeto."""
    return f"Currículo de {dados.nome}"


def gerar_curriculo_pdf(dados):
    """Gera um PDF completo a partir do objeto de dados."""
    return converter_html_para_pdf("", dados)


def converter_html_para_pdf(html, dados_ou_nome):
    """Gera um PDF A4 usando os dados validados pelo backend."""
    if not hasattr(dados_ou_nome, "nome"):
        raise ValueError("A geração do PDF exige o objeto completo de dados do currículo.")

    dados = dados_ou_nome
    nome = str(dados.nome).strip()
    if not nome:
        raise ValueError("O nome do candidato não pode ficar vazio.")

    # Um arquivo temporário exclusivo evita colisões entre solicitações simultâneas
    # de pessoas com o mesmo nome.
    fd, pdf_path = tempfile.mkstemp(prefix="curriculo_", suffix=".pdf")
    os.close(fd)

    try:
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ResumeTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=26,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#2448cf"),
            spaceAfter=8,
        )
        contact_style = ParagraphStyle(
            "ResumeContact",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#526078"),
        )
        heading_style = ParagraphStyle(
            "ResumeHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            spaceBefore=13,
            spaceAfter=6,
            textColor=colors.HexColor("#2448cf"),
        )
        body_style = ParagraphStyle(
            "ResumeBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#273449"),
            spaceAfter=4,
            wordWrap="LTR",
        )

        story = [Paragraph(_texto_para_paragrafo(nome), title_style)]
        contatos = [
            Paragraph(f"<b>E-mail:</b> {html_escape(str(dados.email), quote=True)}", contact_style),
            Paragraph(f"<b>Telefone:</b> {html_escape(str(dados.telefone), quote=True)}", contact_style),
        ]
        contact_table = Table([[contatos[0], contatos[1]]], colWidths=[85 * mm, 85 * mm])
        contact_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5eaf2")),
        ]))
        story.extend([contact_table, Spacer(1, 8)])

        secoes = [
            ("Resumo Profissional", dados.resumo, False),
            ("Experiências Profissionais", dados.experiencias, True),
            ("Formação Acadêmica", dados.formacao, True),
            ("Habilidades", dados.habilidades, True),
        ]

        for titulo, conteudo, usar_lista in secoes:
            story.append(Paragraph(html_escape(titulo), heading_style))
            linhas = [linha.strip() for linha in str(conteudo or "").splitlines() if linha.strip()]
            if not linhas:
                story.append(Paragraph("Não informado.", body_style))
            elif usar_lista:
                for linha in linhas:
                    story.append(Paragraph(f"&#8226;&nbsp; {_texto_para_paragrafo(linha)}", body_style))
            else:
                story.append(Paragraph(_texto_para_paragrafo(str(conteudo)), body_style))

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=f"Currículo - {nome}",
            author="Gerador de Currículo",
        )
        doc.build(story)
        logger.info("PDF de currículo gerado com sucesso.")
        return pdf_path

    except Exception as exc:
        try:
            os.remove(pdf_path)
        except OSError:
            pass
        logger.exception("Falha ao gerar PDF.")
        raise HTTPException(
            status_code=500,
            detail="Não foi possível gerar o PDF. Revise os dados e tente novamente.",
        ) from exc
