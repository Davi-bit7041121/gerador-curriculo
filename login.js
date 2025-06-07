
document.getElementById('loginForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  const resultadoDiv = document.getElementById('resultado');
  const loadingIndicator = document.getElementById('loadingIndicator');

  // Limpa mensagens anteriores
  resultadoDiv.innerText = '';
  resultadoDiv.style.color = '';

  // Mostra o indicador de carregamento
  if (loadingIndicator) {
    loadingIndicator.style.display = 'block';
  }

  const formData = new FormData(e.target);
  const data = {
    email: formData.get('emailLogin'),
    senha: formData.get('senhaLogin')
  };

  try {
    const response = await fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Erro desconhecido ao fazer login.');
    }

    const responseData = await response.json();

    // Salva token e dados do usuário no localStorage
    localStorage.setItem('token', responseData.token);
    localStorage.setItem('usuario', JSON.stringify(responseData.usuario));

    resultadoDiv.innerText = 'Login realizado com sucesso! Redirecionando...';
    resultadoDiv.style.color = 'green';

    // Redireciona para o dashboard após login
    setTimeout(() => {
      window.location.href = '/dashboard';
    }, 1000);

  } catch (error) {
    console.error('Erro no login:', error);
    resultadoDiv.innerText = `Erro: ${error.message}`;
    resultadoDiv.style.color = 'red';
  } finally {
    if (loadingIndicator) {
      loadingIndicator.style.display = 'none';
    }
  }
});

// Função para login com Google
function loginComGoogle() {
  // Redireciona para o endpoint de autenticação do Google
  window.location.href = '/auth/google';
}
