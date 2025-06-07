
// Verifica se o usuário está logado
document.addEventListener('DOMContentLoaded', function() {
  const usuario = localStorage.getItem('usuario');
  
  if (!usuario) {
    // Se não estiver logado, redireciona para login
    window.location.href = '/login.html';
    return;
  }
  
  // Verifica se o usuário já tem um plano
  const userData = JSON.parse(usuario);
  if (userData.plano) {
    // Se já tem plano, redireciona para dashboard
    window.location.href = '/dashboard';
    return;
  }
});

// Impede o usuário de sair da página sem escolher um plano
window.addEventListener('beforeunload', function(e) {
  const usuario = localStorage.getItem('usuario');
  if (usuario) {
    const userData = JSON.parse(usuario);
    if (!userData.plano) {
      e.preventDefault();
      e.returnValue = 'Você precisa escolher um plano antes de continuar!';
      return 'Você precisa escolher um plano antes de continuar!';
    }
  }
});

// Bloqueia navegação por teclas/histórico
window.addEventListener('popstate', function(e) {
  const usuario = localStorage.getItem('usuario');
  if (usuario) {
    const userData = JSON.parse(usuario);
    if (!userData.plano) {
      history.pushState(null, null, location.href);
      alert('Você precisa escolher um plano antes de continuar!');
    }
  }
});

// Carregar Stripe
let stripe;
let elements;

// Inicializar Stripe quando a página carregar
document.addEventListener('DOMContentLoaded', async function() {
  // Carregar Stripe.js
  if (!window.Stripe) {
    const script = document.createElement('script');
    script.src = 'https://js.stripe.com/v3/';
    document.head.appendChild(script);
    
    await new Promise((resolve) => {
      script.onload = resolve;
    });
  }
  
  // Inicializar Stripe com chave pública
  stripe = Stripe('pk_test_51QRwJZFZaGVjhBOKJyEgSfqU7MNKFiPkfZLKjBZOgV4W5xYzXvNGrJmQlK8r9bHgPVnBzLKMnOpQr7sStWvXY00A00H8YzCyF4'); // Substitua pela sua chave pública
});

// Processar pagamento real com Stripe
async function processarPagamento(valor) {
  return new Promise(async (resolve, reject) => {
    try {
      // Criar sessão de checkout no backend
      const response = await fetch('/criar_sessao_pagamento', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          valor: parseFloat(valor.replace(',', '.')),
          plano: 'premium'
        })
      });

      if (!response.ok) {
        throw new Error('Erro ao criar sessão de pagamento');
      }

      const session = await response.json();
      
      // Redirecionar para o Stripe Checkout
      const result = await stripe.redirectToCheckout({
        sessionId: session.sessionId
      });

      if (result.error) {
        reject(result.error.message);
      } else {
        resolve('Redirecionando para pagamento...');
      }
    } catch (error) {
      reject(error.message);
    }
  });
}

async function selecionarPlano(tipoPlano) {
  const resultadoDiv = document.getElementById('resultado');
  const usuario = JSON.parse(localStorage.getItem('usuario'));
  const token = localStorage.getItem('token');
  
  try {
    // Se for plano premium, processar pagamento primeiro
    if (tipoPlano === 'premium') {
      resultadoDiv.innerHTML = `
        <div style="background: #fff3cd; color: #856404; padding: 15px; border-radius: 8px; text-align: center; margin-top: 20px;">
          <h3>Processando Pagamento...</h3>
          <p>Para continuar com o Plano Premium, é necessário efetuar o pagamento.</p>
        </div>
      `;
      
      try {
        await processarPagamento('9,99');
        
        resultadoDiv.innerHTML = `
          <div style="background: #d4edda; color: #155724; padding: 15px; border-radius: 8px; text-align: center; margin-top: 20px;">
            <h3>✅ Pagamento Aprovado!</h3>
            <p>Ativando seu Plano Premium...</p>
          </div>
        `;
      } catch (error) {
        resultadoDiv.innerHTML = `
          <div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; text-align: center; margin-top: 20px;">
            <h3>❌ Pagamento não realizado</h3>
            <p>${error}</p>
            <p>Tente novamente ou escolha o plano gratuito.</p>
          </div>
        `;
        return; // Não prossegue se o pagamento falhou
      }
    }

    const response = await fetch('/selecionar_plano', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        usuarioId: usuario.id,
        plano: tipoPlano
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Erro ao selecionar plano.');
    }

    const responseData = await response.json();
    
    // Atualiza os dados do usuário no localStorage
    usuario.plano = tipoPlano;
    localStorage.setItem('usuario', JSON.stringify(usuario));
    
    if (tipoPlano === 'premium') {
      resultadoDiv.innerHTML = `
        <div style="background: #d4edda; color: #155724; padding: 15px; border-radius: 8px; text-align: center; margin-top: 20px;">
          <h3>🎉 Plano Premium Ativado!</h3>
          <p>Você agora tem acesso a todos os recursos premium, incluindo otimização com IA.</p>
          <p>Redirecionando para o login...</p>
        </div>
      `;
    } else {
      resultadoDiv.innerHTML = `
        <div style="background: #d1ecf1; color: #0c5460; padding: 15px; border-radius: 8px; text-align: center; margin-top: 20px;">
          <h3>✅ Plano Gratuito Selecionado!</h3>
          <p>Você pode gerar currículos em PDF. Upgrade para Premium a qualquer momento!</p>
          <p>Redirecionando para o login...</p>
        </div>
      `;
    }
    
    // Redireciona para o login após 3 segundos
    setTimeout(() => {
      window.location.href = '/login.html';
    }, 3000);

  } catch (error) {
    console.error('Erro:', error);
    resultadoDiv.innerHTML = `
      <div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; text-align: center; margin-top: 20px;">
        <p>Erro ao selecionar plano: ${error.message}</p>
      </div>
    `;
  }
}
