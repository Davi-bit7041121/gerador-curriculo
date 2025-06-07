
import re
from typing import Dict, Any

def melhorar_texto_ia(secao_curriculo: str, texto_original: str) -> str:
    """
    Melhora um texto de uma seção específica do currículo usando regras inteligentes.
    
    Args:
        secao_curriculo (str): O nome da seção (ex: "Resumo Profissional", "Experiência Profissional").
        texto_original (str): O texto fornecido pelo usuário.
    
    Returns:
        str: O texto aprimorado pela IA.
    """
    texto = texto_original.strip()
    
    if secao_curriculo == "Resumo Profissional":
        return melhorar_resumo_profissional(texto)
    elif secao_curriculo == "Experiências Profissionais":
        return melhorar_experiencia_profissional(texto)
    elif secao_curriculo == "Formação Acadêmica":
        return melhorar_formacao_academica(texto)
    elif secao_curriculo == "Habilidades":
        return melhorar_habilidades(texto)
    else:
        return melhorar_texto_generico(texto)

def melhorar_resumo_profissional(texto: str) -> str:
    """Melhora o resumo profissional."""
    # Capitaliza primeira letra e corrige gramática básica
    texto = texto[0].upper() + texto[1:] if texto else ""
    
    # Adiciona conectores profissionais
    if "experiência" in texto.lower() and "anos" in texto.lower():
        texto = re.sub(r'tenho (\d+) anos? de experiência', r'Profissional com \1 anos de experiência consolidada', texto, flags=re.IGNORECASE)
    
    # Melhora descrições genéricas
    texto = re.sub(r'gosto de trabalhar', 'Tenho aptidão para trabalhar', texto, flags=re.IGNORECASE)
    texto = re.sub(r'sou uma pessoa', 'Sou um(a) profissional', texto, flags=re.IGNORECASE)
    
    # Adiciona objetivo profissional se não existir
    if not any(palavra in texto.lower() for palavra in ['objetivo', 'busco', 'procuro']):
        texto += " Busco oportunidades para aplicar minhas competências e contribuir para o crescimento organizacional."
    
    return texto

def melhorar_experiencia_profissional(texto: str) -> str:
    """Melhora a descrição de experiência profissional."""
    texto = texto[0].upper() + texto[1:] if texto else ""
    
    # Substitui verbos informais por verbos de ação
    substituicoes = {
        r'trabalhei como': 'Atuei como',
        r'fazia': 'Realizava',
        r'ajudava': 'Auxiliava',
        r'atendia clientes': 'Prestava atendimento ao cliente',
        r'organizava produtos': 'Gerenciava organização de produtos',
        r'vendia': 'Conduzia vendas de',
        r'cuidava': 'Gerenciava',
        r'fiz': 'Executei',
        r'consegui': 'Alcancei'
    }
    
    for antigo, novo in substituicoes.items():
        texto = re.sub(antigo, novo, texto, flags=re.IGNORECASE)
    
    # Adiciona métricas se possível
    if 'vendas' in texto.lower():
        texto += " Contribuindo para o alcance das metas comerciais estabelecidas."
    
    return texto

def melhorar_formacao_academica(texto: str) -> str:
    """Melhora a descrição de formação acadêmica."""
    texto = texto[0].upper() + texto[1:] if texto else ""
    
    # Padroniza descrições
    texto = re.sub(r'estudei na', 'Graduado(a) pela', texto, flags=re.IGNORECASE)
    texto = re.sub(r'faculdade (\w+)', r'Instituição \1', texto, flags=re.IGNORECASE)
    texto = re.sub(r'me formei em', 'Formação em', texto, flags=re.IGNORECASE)
    
    return texto

def melhorar_habilidades(texto: str) -> str:
    """Melhora e organiza a lista de habilidades."""
    # Separa habilidades por vírgula
    habilidades = [h.strip().title() for h in texto.split(',')]
    
    # Melhora nomes das habilidades
    melhorias = {
        'Excel': 'Microsoft Excel Avançado',
        'Word': 'Microsoft Word',
        'Powerpoint': 'Microsoft PowerPoint',
        'Comunicacao': 'Comunicação Interpessoal',
        'Vendas': 'Técnicas de Vendas',
        'Ingles': 'Inglês Intermediário',
        'Organizacao': 'Organização e Planejamento',
        'Lideranca': 'Liderança de Equipes'
    }
    
    habilidades_melhoradas = []
    for hab in habilidades:
        hab_melhorada = melhorias.get(hab, hab)
        habilidades_melhoradas.append(hab_melhorada)
    
    # Organiza por categorias
    tecnicas = [h for h in habilidades_melhoradas if any(word in h.lower() for word in ['excel', 'word', 'powerpoint', 'sistema', 'python', 'java', 'sql'])]
    comportamentais = [h for h in habilidades_melhoradas if any(word in h.lower() for word in ['comunicação', 'liderança', 'organização', 'vendas', 'negociação'])]
    
    resultado = ""
    if tecnicas:
        resultado += "**Competências Técnicas:** " + ", ".join(tecnicas) + "\n"
    if comportamentais:
        resultado += "**Competências Comportamentais:** " + ", ".join(comportamentais)
    
    return resultado if "**" in resultado else ", ".join(habilidades_melhoradas)

def melhorar_texto_generico(texto: str) -> str:
    """Melhora texto genérico."""
    texto = texto[0].upper() + texto[1:] if texto else ""
    
    # Correções básicas de gramática e formalidade
    texto = re.sub(r'\beu\b', 'Profissional', texto, flags=re.IGNORECASE)
    texto = re.sub(r'\bvc\b|\bvoce\b', 'você', texto, flags=re.IGNORECASE)
    
    return texto
