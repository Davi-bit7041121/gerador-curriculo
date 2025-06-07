// Funções auxiliares para dispositivos móveis
function downloadPdfMobile(url) {
  try {
    // Tenta diferentes métodos de download para mobile
    const a = document.createElement('a');
    a.href = url;
    a.download = 'curriculo.pdf';
    a.target = '_blank';

    // Para alguns navegadores móveis
    if (window.navigator && window.navigator.msSaveOrOpenBlob) {
      // Internet Explorer/Edge
      fetch(url).then(response => response.blob()).then(blob => {
        window.navigator.msSaveOrOpenBlob(blob, 'curriculo.pdf');
      });
    } else {
      // Método padrão
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }

    showMobileMessage('Download iniciado! Verifique a pasta Downloads do seu dispositivo.');
  } catch (error) {
    console.error('Erro no download:', error);
    showMobileMessage('Erro no download. Tente usar "Visualizar PDF" e depois salvar pelo menu do navegador.');
  }
}

function sharePdf(url) {
  try {
    if (navigator.share) {
      // API de compartilhamento nativa (disponível em alguns navegadores móveis)
      fetch(url).then(response => response.blob()).then(blob => {
        const file = new File([blob], 'curriculo.pdf', { type: 'application/pdf' });
        navigator.share({
          title: 'Meu Currículo',
          text: 'Confira meu currículo gerado com IA',
          files: [file]
        });
      }).catch(() => {
        // Fallback: copia URL
        copyToClipboard(url);
        showMobileMessage('Link copiado! Cole em qualquer aplicativo para compartilhar.');
      });
    } else {
      // Fallback: copia URL
      copyToClipboard(url);
      showMobileMessage('Link copiado! Cole em qualquer aplicativo para compartilhar.');
    }
  } catch (error) {
    console.error('Erro no compartilhamento:', error);
    showMobileMessage('Use "Visualizar PDF" e depois compartilhe pelo menu do navegador.');
  }
}

function copyToClipboard(text) {
  try {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text);
    } else {
      // Fallback para navegadores mais antigos
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
    }
  } catch (error) {
    console.error('Erro ao copiar:', error);
  }
}

function showMobileMessage(message) {
  const messageDiv = document.createElement('div');
  messageDiv.style.cssText = `
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: #28a745;
    color: white;
    padding: 15px 20px;
    border-radius: 8px;
    z-index: 1000;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    max-width: 90%;
    text-align: center;
  `;
  messageDiv.textContent = message;
  document.body.appendChild(messageDiv);

  setTimeout(() => {
    if (document.body.contains(messageDiv)) {
      document.body.removeChild(messageDiv);
    }
  }, 4000);
}


// Verifica se o usuário está autenticado ao carregar a página
document.addEventListener('DOMContentLoaded', function() {
  const token = localStorage.getItem('token');
  const usuario = localStorage.getItem('usuario');

  if (!token) {
    // Se não estiver autenticado, redireciona para login
    window.location.href = '/login.html';
    return;
  }

  // Verifica se o usuário tem plano selecionado
  if (usuario) {
    const userData = JSON.parse(usuario);
    if (!userData.plano) {
      // Se não tem plano, redireciona para a página de login
      window.location.href = '/login.html';
      return;
    }
  }

  // Exibe mensagem de boas-vindas
  if (usuario) {
    const userData = JSON.parse(usuario);
    const welcomeMessage = document.getElementById('welcome-message');
    const planoInfo = document.getElementById('plano-info');

    if (welcomeMessage) {
      welcomeMessage.textContent = `Bem-vindo, ${userData.nomeCompleto || userData.nomeUsuario}!`;
    }

    if (planoInfo) {
      if (userData.plano === 'premium') {
        planoInfo.innerHTML = `
          <div style="background: #d4edda; color: #155724; padding: 10px; border-radius: 8px;">
            <strong>Plano Premium Ativo</strong> - Você tem acesso a todos os recursos com IA!
          </div>
        `;
        // Mostra botões de IA para usuários Premium
        mostrarBotoesIA();
      } else if (userData.plano === 'gratuito') {
        planoInfo.innerHTML = `
          <div style="background: #d1ecf1; color: #0c5460; padding: 10px; border-radius: 8px;">
            <strong>Plano Gratuito</strong> - <button onclick="mostrarUpgradePlano()" style="color: #007BFF; background:none; border:none; cursor:pointer;">Upgrade para Premium</button> e tenha acesso aos recursos de IA!
          </div>
        `;
      } else {
        planoInfo.innerHTML = `
          <div style="background: #fff3cd; color: #856404; padding: 10px; border-radius: 8px;">
            <strong>Selecione um Plano</strong> - <a href="/planos.html" style="color: #007BFF;">Clique aqui para escolher seu plano</a>
          </div>
        `;
      }
    }
  }
});

// Função para fazer logout
function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('usuario');
  window.location.href = '/login.html';
}

// Função para login com Google
function loginComGoogle() {
  // Redireciona para o endpoint de autenticação do Google
  window.location.href = '/auth/google';
}

// Função para mostrar botões de IA para usuários Premium
function mostrarBotoesIA() {
  const botoesIA = document.querySelectorAll('.btn-ia');
  botoesIA.forEach(botao => {
    botao.style.display = 'inline-block';
  });
}

// Função para melhorar texto com IA
async function melhorarTextoIA(campo, secao) {
  const textarea = document.querySelector(`textarea[name="${campo}"]`);
  const texto = textarea.value.trim();

  if (!texto) {
    alert('Por favor, digite algum texto antes de melhorar com IA!');
    return;
  }

  const botao = event.target;
  const resultadoDiv = document.getElementById(`resultado-${campo}`);
  const token = localStorage.getItem('token');

  // Desabilita o botão e mostra loading
  botao.disabled = true;
  botao.innerHTML = '<span class="loading-ia"></span>Melhorando...';

  try {
    const response = await fetch('/melhorar_texto', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        secao: secao,
        texto: texto
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Erro ao melhorar texto com IA.');
    }

    const data = await response.json();

    // Mostra o resultado
    resultadoDiv.innerHTML = `
      <h4>✨ Versão Aprimorada pela IA:</h4>
      <p>${data.texto_melhorado}</p>
      <button type="button" onclick="usarTextoMelhorado('${campo}', \`${data.texto_melhorado.replace(/`/g, '\\`')}\`)" 
              style="background: #28a745; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 10px;">
        ✅ Usar Texto Melhorado
      </button>
    `;
    resultadoDiv.style.display = 'block';

  } catch (error) {
    console.error('Erro:', error);
    alert('Erro ao melhorar texto: ' + error.message);
  } finally {
    // Reabilita o botão
    botao.disabled = false;
    botao.innerHTML = '✨ Melhorar com IA';
  }
}

// Função para usar o texto melhorado
function usarTextoMelhorado(campo, textoMelhorado) {
  const textarea = document.querySelector(`textarea[name="${campo}"]`);
  textarea.value = textoMelhorado;

  // Esconde o resultado
  const resultadoDiv = document.getElementById(`resultado-${campo}`);
  resultadoDiv.style.display = 'none';

  // Mostra confirmação
  alert('Texto melhorado aplicado com sucesso!');
}

// Manipulador do formulário de currículo
document.getElementById('resumeForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  const resultadoDiv = document.getElementById('resultado');
  const loadingIndicator = document.getElementById('loadingIndicator');

  // Limpa mensagens anteriores
  resultadoDiv.innerText = '';
  resultadoDiv.style.color = '';
  // Mostra o indicador de carregamento
  loadingIndicator.style.display = 'block';

  const formData = new FormData(e.target);
  const data = {
    nome: formData.get('nome'),
    email: formData.get('email'),
    telefone: formData.get('telefone'),
    resumo: formData.get('resumo'),
    experiencias: formData.get('experiencias'),
    formacao: formData.get('formacao'),
    habilidades: formData.get('habilidades')
  };

  try {
    const token = localStorage.getItem('token');

    const response = await fetch('/gerar_curriculo', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Erro desconhecido ao gerar currículo.');
    }

    // Se a resposta for um PDF, trata o download/visualização
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);

    // Detecta se é dispositivo móvel
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isAndroidApp = window.navigator.userAgent.includes('wv'); // WebView (APK)

    if (isMobile || isAndroidApp) {
      // Para dispositivos móveis/APK: abre o PDF em nova aba e oferece opções
      const newWindow = window.open(url, '_blank');

      resultadoDiv.innerHTML = `
        <div style="color: green; margin-top: 20px;">
          <h3>✅ Currículo gerado com sucesso!</h3>
          <p>O PDF foi aberto em uma nova aba.</p>
          <div style="margin-top: 15px;">
            <button onclick="window.open('${url}', '_blank')" 
                    style="background: #007BFF; color: white; padding: 10px 20px; border: none; border-radius: 4px; margin: 5px; cursor: pointer;">
              📄 Visualizar PDF
            </button>
            <button onclick="downloadPdfMobile('${url}')" 
                    style="background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 4px; margin: 5px; cursor: pointer;">
              💾 Baixar PDF
            </button>
            <button onclick="sharePdf('${url}')" 
                    style="background: #17a2b8; color: white; padding: 10px 20px; border: none; border-radius: 4px; margin: 5px; cursor: pointer;">
              📤 Compartilhar
            </button>
          </div>
          <p style="font-size: 12px; color: #666; margin-top: 10px;">
            💡 Dica: Use "Visualizar PDF" para ver o arquivo, depois use o menu do navegador para baixar ou compartilhar.
          </p>
        </div>
      `;

      // Fallback: tenta download tradicional após um delay
      setTimeout(() => {
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'curriculo.pdf';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }, 1000);

    } else {
      // Para desktop: download tradicional
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = 'curriculo.pdf';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);

      resultadoDiv.innerText = 'Currículo gerado com sucesso! O download começará automaticamente.';
      resultadoDiv.style.color = 'green';
    }

  } catch (error) {
    console.error('Erro:', error);
    resultadoDiv.innerText = error.message;
    resultadoDiv.style.color = 'red';
  } finally {
    // Esconde o indicador de carregamento
    loadingIndicator.style.display = 'none';
  }
});

function mostrarUpgradePlano() {
  // Cria um overlay
  const overlay = document.createElement('div');
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1001;
  `;

  // Cria o modal
  const modal = document.createElement('div');
  modal.style.cssText = `
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    text-align: center;
  `;

  // Adiciona título
  const title = document.createElement('h2');
  title.textContent = 'Upgrade para Plano Premium?';
  modal.appendChild(title);

  // Adiciona botões
  const upgradeButton = document.createElement('button');
  upgradeButton.textContent = 'Sim, Fazer Upgrade';
  upgradeButton.style.cssText = `
    background: #007BFF;
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin: 10px;
  `;
  upgradeButton.onclick = function() {
    window.location.href = '/planos.html'; // Redireciona para a página de planos
  };
  modal.appendChild(upgradeButton);

  const cancelButton = document.createElement('button');
  cancelButton.textContent = 'Não, Permanecer Gratuito';
  cancelButton.style.cssText = `
    background: #6c757d;
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin: 10px;
  `;
  cancelButton.onclick = function() {
    document.body.removeChild(overlay); // Remove o overlay
  };
  modal.appendChild(cancelButton);

  // Adiciona o modal ao overlay
  overlay.appendChild(modal);

  // Adiciona o overlay ao body
  document.body.appendChild(overlay);
}