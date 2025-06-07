document.getElementById('cadastroForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  const resultadoDiv = document.getElementById('resultado');
  const loadingIndicator = document.getElementById('loadingIndicator');

  // Limpa mensagens anteriores
  resultadoDiv.innerText = '';
  resultadoDiv.style.color = '';
  // Mostra o indicador de carregamento
  loadingIndicator.style.display = 'block';

  const formData = new FormData(e.target);
  const senha = formData.get('senha');
  const confirmarSenha = formData.get('confirmarSenha');

  // Validação das senhas
  if (senha !== confirmarSenha) {
    resultadoDiv.innerText = 'As senhas não coincidem!';
    resultadoDiv.style.color = 'red';
    loadingIndicator.style.display = 'none';
    return;
  }

  const data = {
    nomeUsuario: formData.get('nomeUsuario'),
    email: formData.get('emailUsuario'),
    senha: formData.get('senha'),
    nomeCompleto: formData.get('nomeCompleto'),
    telefone: formData.get('telefoneUsuario')
  };

  try {
    const response = await fetch('/cadastrar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Erro desconhecido ao cadastrar usuário.');
    }

    const responseData = await response.json();
    resultadoDiv.innerText = 'Cadastro realizado com sucesso! Redirecionando para planos...';
    resultadoDiv.style.color = 'green';

    // Salva token e dados do usuário no localStorage
    localStorage.setItem('token', responseData.token);
    localStorage.setItem('usuario', JSON.stringify(responseData.usuario));

    // Redireciona para a página de planos após 2 segundos
    setTimeout(() => {
      window.location.href = 'planos.html';
    }, 2000);

  } catch (error) {
    console.error('Erro:', error);
    resultadoDiv.innerText = `Erro ao cadastrar: ${error.message}`;
    resultadoDiv.style.color = 'red';
  } finally {
    loadingIndicator.style.display = 'none';
  }
});