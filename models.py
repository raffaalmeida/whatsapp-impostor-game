from sqlmodel import Field, SQLModel
from typing import Optional

class Player(SQLModel, table=True):
    whatsapp_number: str = Field(primary_key=True)
    name: Optional[str] = None
    current_room: Optional[str] = None

class Room(SQLModel, table=True):
    code: str = Field(primary_key=True) # e.g., "1234"
    host_number: str
    status: str = "waiting" # "waiting" or "playing"
    secret_word: Optional[str] = None
    impostor_number: Optional[str] = None