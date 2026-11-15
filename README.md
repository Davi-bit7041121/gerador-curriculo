# Gerador de Currículo — API e autenticação

## O que foi adicionado

- Cadastro e login pela API FastAPI.
- Senhas armazenadas com hash Argon2 (a senha original não é salva).
- Contas no Cloud Firestore, com verificação transacional de e-mail e nome de usuário duplicados.
- Token JWT com validade de 12 horas.
- Endpoint de geração de PDF protegido por autenticação.
- Dockerfile para implantação no Google Cloud Run.
- Rewrites do Firebase Hosting para encaminhar as rotas da API ao Cloud Run.

## Implantação necessária (não é automática)

O repositório usa Firebase Hosting para os arquivos do site. O Hosting, sozinho, não executa o FastAPI. É necessário preparar o backend no Google Cloud.

O projeto Firebase indicado no workflow existente é `curriculoiagerador`. Confirme que esse é o projeto correto antes de executar os comandos abaixo. A criação de recursos na nuvem pode exigir ativação de faturamento; peça ajuda ao responsável pela conta e não habilite serviços pagos sem autorização.

### 1. Preparar o Firestore

No console do Firebase, abra o projeto correto, entre em **Firestore Database** e crie o banco no modo nativo. Escolha uma região compatível com a região do Cloud Run.

A conta de serviço usada pelo Cloud Run precisa da função **Cloud Datastore User** (ou permissão equivalente para ler e gravar no Firestore).

### 2. Criar o segredo JWT

No Google Cloud, habilite Secret Manager e crie um segredo chamado `jwt-secret`. Gere um valor aleatório com pelo menos 32 bytes e armazene-o no Secret Manager. Não coloque esse valor no GitHub, no código ou no frontend.

### 3. Implantar a API

Com o Google Cloud CLI instalado e autenticado no projeto correto, habilite Cloud Run, Cloud Build e Artifact Registry. Depois, na pasta do projeto, execute:

```bash
gcloud run deploy curriculo-api \
  --source . \
  --region southamerica-east1 \
  --project curriculoiagerador \
  --allow-unauthenticated \
  --memory 512Mi \
  --set-env-vars ENVIRONMENT=production,FRONTEND_ORIGINS=https://curriculoiagerador.web.app,https://curriculoiagerador.firebaseapp.com \
  --set-secrets JWT_SECRET=jwt-secret:latest
```

O acesso HTTP público é necessário para que o Firebase Hosting encaminhe as chamadas; as rotas de conta e geração de PDF fazem suas próprias verificações. O serviço do Cloud Run deve usar uma conta de serviço com acesso ao Firestore e ao segredo JWT.

### 4. Publicar o Hosting

Depois que o serviço `curriculo-api` estiver implantado na região configurada, publique os arquivos do site com o Firebase CLI:

```bash
firebase deploy --only hosting --project curriculoiagerador
```

O workflow atual do GitHub também publica o Hosting quando há push na branch principal. A primeira implantação do Cloud Run e a configuração do Firestore/Secret Manager precisam ser feitas antes.

## Rotas disponíveis

- `GET /health`
- `POST /cadastrar`
- `POST /login`
- `POST /gerar_curriculo` (exige `Authorization: Bearer <token>`)

## Limitações atuais

A seleção de planos, checkout/pagamento, login Google e melhoria de texto por IA ainda dependem de rotas/serviços próprios e não são implementados por esta alteração. Não considere o Premium ativo nem faça pagamentos com base apenas no frontend.
