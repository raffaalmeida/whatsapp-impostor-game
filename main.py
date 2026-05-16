from fastapi import FastAPI, Request, Depends
from contextlib import asynccontextmanager
from database import create_db_and_tables, get_session
from sqlmodel import Session

import os
from pywa import WhatsApp
from dotenv import load_dotenv
import uvicorn
from whatsapp_handler import WhatsAppHandler

load_dotenv()

# Cria o banco de dados e as tabelas quando o app inicia
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Assistente de Gastos MVP")

meu_bot = WhatsAppHandler(fastapi_app=app)

@app.get("/health")
def health_check():
    return {"status": "rodando liso"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)