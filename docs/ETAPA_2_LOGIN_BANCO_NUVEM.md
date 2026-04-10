# Etapa 2 — Login, banco e nuvem

## Objetivo desta etapa
Preparar a subida do sistema para um beta privado com:
- login por usuário
- banco centralizado
- API para cálculos
- caminho de deploy em nuvem

## O que já está incluído neste pacote
- `infra/supabase_schema.sql`: schema inicial do banco no Supabase
- `infra/render.yaml`: blueprint inicial para deploy da API no Render
- `infra/env.example`: variáveis de ambiente
- `backend_api/main.py`: API inicial com `/health` e `/calculate`

## Ordem recomendada
1. Criar o projeto no Supabase
2. Executar o schema SQL
3. Configurar Auth por email/senha
4. Criar o serviço no Render usando `render.yaml`
5. Testar localmente a API
6. Depois conectar o app Streamlit à API e ao banco

## Comando local para testar a API
```powershell
cd C:quicultura_aiqua_project_agent_gui_dashboard_v1
.env\Scripts\python.exe -m pip install -r backend_apiequirements_backend.txt
.env\Scripts\python.exe -m uvicorn backend_api.main:app --reload
```

## Teste rápido
- `GET /health`
- `POST /calculate`

Exemplo de body para `/calculate`:
```json
{
  "payload": {
    "project_name": "Projeto teste",
    "author_name": "Luiz",
    "report_profile": "Produtor"
  }
}
```

## Próxima ligação prática
Depois desta etapa, a próxima peça é substituir o `local_store.py` por uma camada `supabase_store.py`, mantendo o app atual com a mesma experiência visual.
