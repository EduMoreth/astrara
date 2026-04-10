# SECURITY CHECKLIST — Regras Obrigatórias de Segurança

> **Este documento deve ser lido e respeitado em TODA alteração de código neste projeto.**
> **Este projeto está em PRODUÇÃO com usuários reais e dados sensíveis protegidos pela LGPD (Lei 13.709/2018).**

---

## I. REGRAS DE OURO — NUNCA VIOLAR

1. **NUNCA commitar secrets, tokens, API keys ou senhas** — nem temporariamente. Se acontecer acidentalmente, rotacionar a chave imediatamente e limpar do histórico com `git filter-repo` ou BFG.
2. **NUNCA usar fallbacks inseguros para secrets** — se uma variável de ambiente crítica (JWT_SECRET, STRIPE_SECRET, ADMIN_TOKEN, SECRET_KEY, DATABASE_URL) não estiver definida, o app DEVE falhar na inicialização. Nunca usar valores default como "change-me" ou similar.
3. **NUNCA expor endpoints de debug em produção** — qualquer endpoint de diagnóstico deve ser removido ou protegido com autenticação admin obrigatória.
4. **NUNCA retornar error.message, str(e) ou stack traces ao cliente** — logar internamente e retornar mensagem genérica ao usuário.
5. **NUNCA modificar estrutura do banco de dados sem backup prévio** — toda migration deve ser precedida de snapshot/backup do banco de produção.
6. **NUNCA deletar dados de produção** — soft delete apenas. Dados pessoais só podem ser eliminados por requisição expressa do titular (LGPD Art. 18).

---

## II. AMBIENTE DE PRODUÇÃO — REGRAS DE DEPLOY

### Banco de Dados
- [ ] Backup automático verificado antes de qualquer migration
- [ ] Migrations usam `prisma migrate deploy` ou equivalente seguro (nunca `--accept-data-loss` ou `db push` em produção)
- [ ] Conexão com banco usa SSL obrigatório (`sslmode=require`)
- [ ] Connection pooling configurado (nunca conexão nova por request)
- [ ] Operações que alteram saldo/créditos usam UPDATE atômico (`WHERE balance > 0 RETURNING ...`)

### Variáveis de Ambiente
- [ ] Todas as secrets definidas como variáveis de ambiente na plataforma de deploy (Railway, etc.)
- [ ] Nenhum fallback inseguro no código — app falha se secret ausente
- [ ] `.env`, `.env.production`, `.env.staging`, `*.sql.gz` no `.gitignore`
- [ ] `.claude/` no `.gitignore`

### Docker / Deploy
- [ ] Dockerfiles usam multi-stage build sem copiar `.env`
- [ ] `docker-compose.prod.yml` usa `${VAR:?VAR required}` (sem fallbacks)
- [ ] Nenhum secret em build args

---

## III. CHECKLIST DE SEGURANÇA — Verificar em TODA alteração

### Autenticação & Autorização
- [ ] Todo novo endpoint exige autenticação (exceto rotas explicitamente públicas documentadas)
- [ ] JWT sem fallback secret — `SECRET_KEY` obrigatório
- [ ] Tokens JWT com validade máxima de 24h (ideal) ou 72h (máximo)
- [ ] Rate limiting implementado em: login, register, forgot-password, verify-otp, reset-password
- [ ] OTP invalidado após 5 tentativas falhas
- [ ] Senhas com `min_length=8` no registro

### Proteção contra Ataques
- [ ] Proteção CSRF ativa (SameSite=Strict/Lax + header custom ou token)
- [ ] CORS restrito — sem `localhost` em produção (apenas em `ENV=development`)
- [ ] Inputs validados (Pydantic, Zod, ou equivalente) em todos os endpoints
- [ ] Queries parametrizadas — NUNCA interpolar input do usuário em SQL/Cypher via f-string
- [ ] Allowlists explícitas para campos em queries dinâmicas
- [ ] `dangerouslySetInnerHTML` SEMPRE precedido de `DOMPurify.sanitize()`
- [ ] Upload de arquivos validado (tipo, tamanho, extensão) se aplicável

### Headers de Segurança
- [ ] `Content-Security-Policy` configurado (sem `unsafe-eval` em produção)
- [ ] `X-Frame-Options: DENY` ou `SAMEORIGIN`
- [ ] `Strict-Transport-Security` (HSTS)
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `Referrer-Policy: strict-origin-when-cross-origin`
- [ ] `Permissions-Policy` restritivo (camera=(), microphone=(), geolocation=())

### Stripe / Pagamentos
- [ ] Webhook SEMPRE valida assinatura com `STRIPE_WEBHOOK_SECRET`
- [ ] Se `STRIPE_WEBHOOK_SECRET` não configurado, rejeitar webhook (HTTP 500)
- [ ] Nunca confiar em valores de preço/desconto vindos do cliente

### Logs & Erros
- [ ] Erros detalhados logados server-side apenas
- [ ] Respostas ao cliente: `{ "error": "Internal server error" }` genérico
- [ ] Swagger/Redoc desabilitados em produção (`docs_url=None, redoc_url=None`)
- [ ] Nenhuma informação de infraestrutura exposta em responses

### Dependências
- [ ] `npm audit` e `pip audit` executados — zero vulnerabilidades HIGH/CRITICAL
- [ ] `package-lock.json` / `requirements.txt` com versões fixas
- [ ] Next.js na versão mais recente estável (≥15.x)

---

## IV. LGPD — PROTEÇÃO DE DADOS PESSOAIS

1. **Dados pessoais** (nome, email, CPF, CNPJ, telefone, endereço) são protegidos pela LGPD.
2. **Nunca logar dados pessoais** em plaintext — usar mascaramento (ex: `edu***@gmail.com`).
3. **Nunca expor dados pessoais** em endpoints públicos, mensagens de erro, ou URLs.
4. **Direito de exclusão** — manter endpoint/processo para atender requisições de titulares (Art. 18, IX).
5. **Consentimento** — qualquer novo uso de dados pessoais requer base legal documentada.
6. **Retenção** — dados pessoais devem ter prazo de retenção definido. Não armazenar indefinidamente sem justificativa.
7. **Incidentes** — qualquer vazamento de dados pessoais deve ser documentado e comunicado à ANPD se relevante (Art. 48).

---

## V. ANTES DE CADA COMMIT — CHECKLIST RÁPIDO

```
[ ] Rodei grep -r "TODO\|FIXME\|HACK\|password\|secret\|api_key" no código novo?
[ ] Nenhum secret hardcoded?
[ ] Nenhum endpoint novo sem auth?
[ ] Nenhum error.message exposto ao cliente?
[ ] npm audit / pip audit limpos?
[ ] Migration testada localmente antes de aplicar em produção?
[ ] Backup do banco verificado se migration altera schema?
```

---

## VI. COMANDOS DE VERIFICAÇÃO

```bash
# Verificar secrets no código
grep -rn "sk-\|sk_live\|sk_test\|password.*=.*['\"]" --include="*.py" --include="*.ts" --include="*.js" .

# Verificar secrets no histórico Git
git log -p -S "sk-" --all
git log -p -S "api_key" --all

# Auditar dependências
npm audit
pip audit

# Verificar .env não commitado
git ls-files | grep -i "\.env"
```

---

**Responsável:** Eduardo Moreth Loquez — Brain Legal LTDA
**Última atualização:** 2026-04-10
**Revisão obrigatória:** A cada 90 dias ou após incidente de segurança.
