# Astrara

**O cosmos, decifrado.**

SaaS de mapas astrais com design premium. Gera mandalas astrologicas e interpretacoes com IA.

## Stack

- **Frontend:** Next.js 14 (App Router, TypeScript), Tailwind CSS, Framer Motion
- **Backend:** Python FastAPI, Kerykeion (calculo offline), OpenCage geocoding
- **Database:** PostgreSQL
- **Deploy:** Railway (monorepo)

## Estrutura

```
Code/
├── frontend/          # Next.js app
│   ├── app/           # Pages (App Router)
│   ├── components/    # React components
│   └── lib/           # API client, auth helpers
├── backend/           # FastAPI app
│   ├── routers/       # API endpoints
│   ├── services/      # Business logic
│   └── models/        # Pydantic schemas
└── railway.toml       # Railway config
```

## Setup Local

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env   # Editar com suas credenciais
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp ../.env.example .env.local  # Ajustar NEXT_PUBLIC_API_URL
npm run dev
```

### Variaveis de Ambiente

| Variavel | Descricao |
|----------|-----------|
| `DATABASE_URL` | Connection string PostgreSQL |
| `SECRET_KEY` | Chave secreta para JWT |
| `OPENCAGE_API_KEY` | Chave da API OpenCage (geocoding) |
| `NEXT_PUBLIC_API_URL` | URL do backend (ex: http://localhost:8000) |

## Deploy no Railway

1. Crie um novo projeto no Railway
2. Conecte o repositorio Git
3. O `railway.toml` configura dois servicos automaticamente:
   - `astrara-frontend` (pasta frontend/)
   - `astrara-backend` (pasta backend/)
4. Adicione um servico PostgreSQL no Railway
5. Configure as variaveis de ambiente em cada servico
6. Deploy automatico via push no Git

## Endpoints da API

| Metodo | Rota | Descricao |
|--------|------|-----------|
| POST | `/chart/generate` | Gera mapa astral |
| POST | `/auth/register` | Cria conta |
| POST | `/auth/login` | Login |
| GET | `/user/me` | Dados do usuario |
| GET | `/user/charts` | Mapas salvos |
| POST | `/user/charts/save` | Salvar mapa |

---

**Astrara** - Brain Legal LTDA
