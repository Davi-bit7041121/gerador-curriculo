document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('loginForm');
  if (!form) return;

  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const resultado = document.getElementById('resultado');
    const loading = document.getElementById('loadingIndicator');
    const botao = form.querySelector('button[type="submit"]');
    const dados = new FormData(form);

    resultado.textContent = '';
    if (loading) loading.style.display = 'block';
    if (botao) botao.disabled = true;

    try {
      const response = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: dados.get('emailLogin'),
          senha: dados.get('senhaLogin')
        })
      });

      let resposta;
      try { resposta = await response.json(); }
      catch (_) { throw new Error('O servidor retornou uma resposta inválida.'); }

      if (!response.ok) throw new Error(resposta.detail || 'Não foi possível entrar.');
      if (!resposta.token || !resposta.usuario) {
        throw new Error('Resposta de login incompleta. Entre em contato com o suporte.');
      }

      localStorage.setItem('token', resposta.token);
      localStorage.setItem('usuario', JSON.stringify(resposta.usuario));
      resultado.textContent = 'Login realizado. Redirecionando...';
      resultado.dataset.state = 'success';

      // O repositório não contém uma rota /dashboard; encaminha para as páginas existentes.
      window.setTimeout(() => {
        window.location.href = resposta.usuario.plano ? '/index.html' : '/planos.html';
      }, 500);
    } catch (error) {
      console.error('Erro no login:', error);
      resultado.textContent = error.message || 'Erro ao fazer login.';
      resultado.dataset.state = 'error';
    } finally {
      if (loading) loading.style.display = 'none';
      if (botao) botao.disabled = false;
    }
  });
});

function loginComGoogle() {
  window.location.href = '/auth/google';
}
