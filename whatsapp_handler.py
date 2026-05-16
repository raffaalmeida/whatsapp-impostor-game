from fastapi import FastAPI
from pywa import WhatsApp
from pywa.types import Message
from typing import Any
from datetime import UTC, datetime, timedelta

from pywa_async import WhatsApp, filters, types

import os

class WhatsAppHandler():
    def __init__(self, fastapi_app: FastAPI):

        self.client = self.define_client(fastapi_app)

        self._register_handlers()


    def define_client(self, fastapi_app) -> WhatsApp:
        """
        Define o cliente WhatsApp.

        Returns:
            WhatsApp: Cliente WhatsApp autenticado.
        """
        whatsapp_phone_id = os.getenv("WHATSAPP_PHONE_ID")
        whatsapp_token = os.getenv("WHATSAPP_TOKEN")
        verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
        whatsapp_bussiness_id = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")
        if not whatsapp_phone_id or not whatsapp_token or not verify_token:
            raise OSError("Variáveis de ambiente não configuradas corretamente.")

        #logger.info(f"whatsapp_phone_id: {whatsapp_phone_id}, whatsapp_bussiness_id: {whatsapp_bussiness_id}")

        return WhatsApp(
            phone_id=whatsapp_phone_id,
            token=whatsapp_token,
            server=fastapi_app,
            verify_token=verify_token,
            webhook_endpoint="/messages",
            business_account_id=whatsapp_bussiness_id
        )
    

    def _register_handlers(self):
        self.client.on_message(self.receive_messages)


    async def receive_messages(self, _: WhatsApp, msg: types.Message) -> None:
        """
        Recebe mensagens de entrada e processa-as.
        """
        if not self._is_message_recent(msg.timestamp):
            #logger.info(f"Mensagem antiga recebida: {msg.from_user} - {msg.caption or msg.text or ''}")
            return

        #logger.info(f"Nova mensagem recebida: {msg.caption or msg.text or ''}")

        payload = await self._format_message(msg)
        user_id = payload["sender"]["id"]
        await self.send_text(to_number=user_id, text="Ola como posso ajudar?")

    
    async def send_text(self, to_number: str, text: str):
        """Sends a text message back to a user."""
        try:
            await self.client.send_message(
                to=to_number,
                text=text
            )
            print(f"Sent to {to_number}: {text}")
        except Exception as e:
            print(f"Error sending message: {e}")
        
    
    async def _format_message(self, data: Any) -> dict:
        """
        Formata um objeto types.Message em um dicionário compatível com o esquema MessagePayload.

        Args:
            data (Any): Objeto da mensagem a ser formatado.

        Returns:
            Dict: Dicionário contendo os dados formatados da mensagem.
        """
        attachments = []
        if data.media:
            media_url = await data.media.get_media_url()
            media_bytes = await self.client.download_media(url=media_url, in_memory=True)
            file_b64 = self._get_media_base64(media_bytes)

            attachments.append(
                {
                    "file_name": data.media.id,
                    "files_url": media_url,
                    "mime_type": data.media.mime_type,
                    "file_base64": file_b64,
                }
            )

        return {
            "text": data.caption or data.text or "",
            "sender": {
                "id": data.from_user.wa_id,
                "name": data.from_user.name,
            },
            "source": {
                "platform": "whatsapp",
                "metadata": {"display_phone_number": data.metadata.display_phone_number, "phone_number_id": data.metadata.phone_number_id, "message_id": data.id},
            },
            "attachments": attachments,
        }
        
    
    def _is_message_recent(self, message_timestamp: datetime) -> bool:
        """
        Verifica se a mensagem foi recebida nos últimos 30 segundos.
        Args:
            message_timestamp: Timestamp da mensagem em UTC
        Returns:
            bool: True se a mensagem for recente, False caso contrário
        """
        current_time = datetime.now(UTC)
        time_diff = current_time - message_timestamp
        return time_diff <= timedelta(seconds=30)
    


