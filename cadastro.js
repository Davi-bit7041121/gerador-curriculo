document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('cadastroForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const resultadoDiv = document.getElementById('resultado');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const submitButton = form.querySelector('button[type="submit"]');

    resultadoDiv.textContent = '';
    resultadoDiv.dataset.state = '';
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    if (submitButton) submitButton.disabled = true;

    const formData = new FormData(form);
    const senha = String(formData.get('senha') || '');
    const confirmarSenha = String(formData.get('confirmarSenha') || '');

    if (senha !== confirmarSenha) {
      resultadoDiv.textContent = 'As senhas não coincidem.';
      resultadoDiv.dataset.state = 'error';
      if (loadingIndicator) loadingIndicator.style.display = 'none';
      if (submitButton) submitButton.disabled = false;
      return;
    }

    const data = {
      nomeUsuario: formData.get('nomeUsuario'),
      email: formData.get('emailUsuario'),
      senha,
      nomeCompleto: formData.get('nomeCompleto'),
      telefone: formData.get('telefoneUsuario')
    };

    try {
      const response = await fetch('/cadastrar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify(data)
      });

      const contentType = response.headers.get('content-type') || '';
      const responseText = await response.text();
      let responseData = null;

      if (contentType.includes('application/json')) {
        try {
          responseData = JSON.parse(responseText);
        } catch (_) {
          throw new Error('O servidor informou JSON, mas devolveu uma resposta inválida.');
        }
      } else {
        // Firebase Hosting costuma devolver HTML quando não existe uma rota/rewrite
        // para a API. Evita o confuso "Unexpected token T" do JSON.parse.
        if (response.status === 404 || /text\/html/i.test(contentType) || /^\s*<!doctype html/i.test(responseText)) {
          throw new Error('O serviço de cadastro não está conectado ao servidor. A rota /cadastrar não foi encontrada. O backend precisa ser implantado e conectado ao site.');
        }
        throw new Error(`O servidor respondeu em formato inesperado (HTTP ${response.status}). Verifique a implantação do backend.`);
      }

      if (!response.ok) {
        throw new Error(responseData?.detail || responseData?.message || `Falha no cadastro (HTTP ${response.status}).`);
      }

      if (!responseData?.token || !responseData?.usuario) {
        throw new Error('O servidor recebeu o cadastro, mas não retornou token e usuário. A API precisa ser configurada corretamente.');
      }

      localStorage.setItem('token', responseData.token);
      localStorage.setItem('usuario', JSON.stringify(responseData.usuario));
      resultadoDiv.textContent = 'Cadastro realizado com sucesso! Redirecionando para os planos...';
      resultadoDiv.dataset.state = 'success';

      window.setTimeout(() => {
        window.location.href = '/planos.html';
      }, 1200);
    } catch (error) {
      console.error('Erro no cadastro:', error);
      resultadoDiv.textContent = `Erro ao cadastrar: ${error.message || 'Não foi possível concluir o cadastro.'}`;
      resultadoDiv.dataset.state = 'error';
    } finally {
      if (loadingIndicator) loadingIndicator.style.display = 'none';
      if (submitButton) submitButton.disabled = false;
    }
  });
});
