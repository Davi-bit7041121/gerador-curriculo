// Utilitários de sessão e mensagens
function obterUsuario() {
  try {
    return JSON.parse(localStorage.getItem('usuario') || 'null');
  } catch (error) {
    console.warn('Dados locais do usuário inválidos:', error);
    localStorage.removeItem('usuario');
    return null;
  }
}

function mensagemResultado(elemento, texto, tipo = 'info') {
  if (!elemento) return;
  elemento.textContent = texto;
  elemento.dataset.state = tipo;
}

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('usuario');
  window.location.href = '/login.html';
}

function loginComGoogle() {
  window.location.href = '/auth/google';
}

function mostrarBotoesIA() {
  document.querySelectorAll('.btn-ia').forEach((botao) => {
    botao.style.display = 'inline-block';
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const token = localStorage.getItem('token');
  const usuario = obterUsuario();

  if (!token) {
    window.location.replace('/login.html');
    return;
  }

  if (!usuario || !usuario.plano) {
    window.location.replace('/planos.html');
    return;
  }

  const welcomeMessage = document.getElementById('welcome-message');
  const planoInfo = document.getElementById('plano-info');

  if (welcomeMessage) {
    welcomeMessage.textContent = `Bem-vindo, ${usuario.nomeCompleto || usuario.nomeUsuario || 'usuário'}!`;
  }

  if (planoInfo) {
    if (usuario.plano === 'premium') {
      planoInfo.innerHTML = '<div class="plan-banner premium"><strong>Plano Premium ativo</strong> — recursos de IA disponíveis.</div>';
      mostrarBotoesIA();
    } else if (usuario.plano === 'gratuito') {
      planoInfo.innerHTML = '<div class="plan-banner free"><strong>Plano Gratuito</strong> — <a href="/planos.html">Conheça o Premium</a>.</div>';
    } else {
      planoInfo.innerHTML = '<div class="plan-banner warning"><strong>Plano não reconhecido.</strong> <a href="/planos.html">Escolha um plano</a>.</div>';
    }
  }

  const form = document.getElementById('resumeForm');
  if (form) form.addEventListener('submit', gerarCurriculo);
});

async function lerErro(response, mensagemPadrao) {
  try {
    const data = await response.json();
    return data.detail || data.message || mensagemPadrao;
  } catch (_) {
    return mensagemPadrao;
  }
}

async function melhorarTextoIA(campo, secao, botao) {
  const textarea = document.querySelector(`textarea[name="${campo}"]`);
  const resultadoDiv = document.getElementById(`resultado-${campo}`);
  if (!textarea || !resultadoDiv || !botao) return;

  const texto = textarea.value.trim();
  if (!texto) {
    mensagemResultado(resultadoDiv, 'Digite um texto antes de solicitar a melhoria.', 'error');
    resultadoDiv.style.display = 'block';
    return;
  }

  const token = localStorage.getItem('token');
  const textoOriginalBotao = botao.textContent;
  botao.disabled = true;
  botao.textContent = 'Melhorando...';

  try {
    const response = await fetch('/melhorar_texto', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ secao, texto })
    });

    if (!response.ok) {
      throw new Error(await lerErro(response, 'Não foi possível melhorar o texto.'));
    }

    const data = await response.json();
    if (typeof data.texto_melhorado !== 'string' || !data.texto_melhorado.trim()) {
      throw new Error('A resposta da melhoria veio vazia ou em formato inválido.');
    }

    resultadoDiv.replaceChildren();
    const titulo = document.createElement('h4');
    titulo.textContent = 'Versão aprimorada';
    const paragrafo = document.createElement('p');
    paragrafo.textContent = data.texto_melhorado;

    const aplicar = document.createElement('button');
    aplicar.type = 'button';
    aplicar.className = 'apply-ai-button';
    aplicar.textContent = 'Usar texto aprimorado';
    aplicar.addEventListener('click', () => {
      textarea.value = data.texto_melhorado;
      textarea.dispatchEvent(new Event('input', { bubbles: true }));
      resultadoDiv.style.display = 'none';
    });

    resultadoDiv.append(titulo, paragrafo, aplicar);
    resultadoDiv.style.display = 'block';
  } catch (error) {
    console.error('Erro na melhoria de texto:', error);
    resultadoDiv.textContent = error.message || 'Erro ao melhorar o texto.';
    resultadoDiv.style.display = 'block';
  } finally {
    botao.disabled = false;
    botao.textContent = textoOriginalBotao;
  }
}

async function gerarCurriculo(evento) {
  evento.preventDefault();
  const form = evento.currentTarget;
  const resultadoDiv = document.getElementById('resultado');
  const loadingIndicator = document.getElementById('loadingIndicator');
  const submitButton = form.querySelector('button[type="submit"]');
  const formData = new FormData(form);
  const data = Object.fromEntries(formData.entries());

  mensagemResultado(resultadoDiv, '');
  loadingIndicator.style.display = 'flex';
  if (submitButton) submitButton.disabled = true;

  let objectUrl = null;
  try {
    const token = localStorage.getItem('token');
    if (!token) throw new Error('Sua sessão expirou. Entre novamente.');

    const response = await fetch('/gerar_curriculo', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error(await lerErro(response, 'Erro ao gerar o currículo.'));
    }

    const blob = await response.blob();
    if (blob.type && !blob.type.includes('pdf')) {
      throw new Error('O servidor não retornou um arquivo PDF válido.');
    }
    if (!blob.size) throw new Error('O PDF retornado está vazio.');

    objectUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = 'curriculo.pdf';
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    link.remove();

    mensagemResultado(resultadoDiv, 'Currículo gerado! O download do PDF foi iniciado.', 'success');
    // Mantém a URL disponível tempo suficiente para o navegador concluir o download.
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60000);
  } catch (error) {
    console.error('Erro ao gerar currículo:', error);
    mensagemResultado(resultadoDiv, error.message || 'Não foi possível gerar o currículo.', 'error');
    if (objectUrl) URL.revokeObjectURL(objectUrl);
  } finally {
    loadingIndicator.style.display = 'none';
    if (submitButton) submitButton.disabled = false;
  }
}

function mostrarUpgradePlano() {
  window.location.href = '/planos.html';
}
