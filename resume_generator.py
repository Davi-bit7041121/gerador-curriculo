# resume_generator.py
from jinja2 import Template
import tempfile
import os
import logging
from slugify import slugify
from fastapi import HTTPException
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Configuração básica de logging para este módulo
logger = logging.getLogger(__name__)

def gerar_curriculo_html(dados):
    """
    Esta função agora é mantida para compatibilidade, mas não usamos HTML.
    """
    return f"Currículo de {dados.nome}"

def gerar_curriculo_pdf(dados):
    """
    Gera um arquivo PDF do currículo diretamente dos dados.
    """
    return converter_html_para_pdf("", dados)

def converter_html_para_pdf(html, dados_ou_nome):
    """
    Converte os dados do currículo em um arquivo PDF usando reportlab.
    """
    # Se recebemos um objeto dados, usa ele; senão assume que é uma string nome
    if hasattr(dados_ou_nome, 'nome'):
        dados = dados_ou_nome
        nome = dados.nome
    else:
        nome = dados_ou_nome
        # Para compatibilidade reversa, se só temos nome, não podemos gerar PDF completo
        raise ValueError("Função precisa receber objeto dados completo")
    
    # Usa slugify para criar um nome de arquivo seguro e amigável
    nome_seguro = slugify(nome, separator='_')

    # Define o caminho do PDF no diretório temporário
    pdf_path = os.path.join(tempfile.gettempdir(), f"{nome_seguro}_curriculo.pdf")

    try:
        # Cria o documento PDF
        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)

        # Container para os elementos do PDF
        story = []

        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#007BFF')
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#0056b3')
        )

        normal_style = styles['Normal']
        normal_style.fontSize = 11
        normal_style.spaceAfter = 6

        # Título (nome)
        story.append(Paragraph(nome, title_style))
        story.append(Spacer(1, 12))

        # Informações de contato
        contact_data = [
            ['Email:', dados.email],
            ['Telefone:', dados.telefone]
        ]
        contact_table = Table(contact_data, colWidths=[1.5*inch, 4*inch])
        contact_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(contact_table)
        story.append(Spacer(1, 20))

        # Resumo Profissional
        story.append(Paragraph("Resumo Profissional", heading_style))
        story.append(Paragraph(dados.resumo, normal_style))
        story.append(Spacer(1, 12))

        # Experiências Profissionais
        story.append(Paragraph("Experiências Profissionais", heading_style))
        for experiencia in dados.experiencias.split('\n'):
            if experiencia.strip():
                story.append(Paragraph(f"• {experiencia.strip()}", normal_style))
        story.append(Spacer(1, 12))

        # Formação Acadêmica
        story.append(Paragraph("Formação Acadêmica", heading_style))
        for formacao_item in dados.formacao.split('\n'):
            if formacao_item.strip():
                story.append(Paragraph(f"• {formacao_item.strip()}", normal_style))
        story.append(Spacer(1, 12))

        # Habilidades
        story.append(Paragraph("Habilidades", heading_style))
        for habilidade in dados.habilidades.split('\n'):
            if habilidade.strip():
                story.append(Paragraph(f"• {habilidade.strip()}", normal_style))

        # Constrói o PDF
        doc.build(story)
        logger.info(f"PDF gerado com sucesso usando reportlab em: {pdf_path}")

    except Exception as e:
        logger.error(f"Erro ao gerar PDF para {nome}: {e}")
        raise HTTPException(status_code=500, detail=f"Falha ao gerar o PDF do currículo: {str(e)}")

    return pdf_path