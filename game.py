import random
from sqlmodel import Session, select
from typing import Callable, Awaitable
from database import engine
from models import Player, Room

# Simple word bank for the MVP
WORDS_DB = [
    "Beach", "Space Station", "Police Station", 
    "Submarine", "Dermatologist Clinic", "Restaurant"
]

async def process_game_command(
    sender_number: str, 
    message_text: str, 
    send_func: Callable[[str, str], Awaitable[None]]
):
    text = message_text.strip().lower()
    
    # We open a synchronous DB session block
    with Session(engine) as session:
        # 1. Ensure Player exists
        player = session.get(Player, sender_number)
        if not player:
            player = Player(whatsapp_number=sender_number)
            session.add(player)
            session.commit()
            session.refresh(player)

        # 2. Command: /create
        if text == "/create":
            room_code = str(random.randint(1000, 9999))
            
            new_room = Room(code=room_code, host_number=sender_number)
            player.current_room = room_code
            
            session.add(new_room)
            session.add(player)
            session.commit()
            
            await send_func(sender_number, f"Room created! Code: *{room_code}*.\nTell your friends to send '/join {room_code}'.\nSend '/start' when everyone is ready.")
            return

        # 3. Command: /join <code>
        if text.startswith("/join"):
            parts = text.split()
            if len(parts) < 2:
                await send_func(sender_number, "Please use: /join <code>")
                return
                
            room_code = parts[1]
            room = session.get(Room, room_code)
            
            if not room:
                await send_func(sender_number, "Room not found. Check the code.")
                return
                
            player.current_room = room_code
            session.add(player)
            session.commit()
            
            # Count players in room
            players_in_room = session.exec(select(Player).where(Player.current_room == room_code)).all()
            
            await send_func(sender_number, f"You joined room *{room_code}*!")
            await send_func(room.host_number, f"New player joined. Total players: {len(players_in_room)}")
            return

        # 4. Command: /start (Starts or re-rolls)
        if text == "/start":
            if not player.current_room:
                await send_func(sender_number, "You are not in a room. Send /create to start one.")
                return
                
            room = session.get(Room, player.current_room)
            if room.host_number != sender_number:
                await send_func(sender_number, "Only the host can start the game.")
                return
                
            players = session.exec(select(Player).where(Player.current_room == room.code)).all()
            
            if len(players) < 3:
                await send_func(sender_number, f"You need at least 3 players to start. Currently have {len(players)}.")
                return

            # Roll the game
            room.secret_word = random.choice(WORDS_DB)
            room.impostor_number = random.choice(players).whatsapp_number
            room.status = "playing"
            session.add(room)
            session.commit()

            # Blast the roles via WhatsApp
            for p in players:
                if p.whatsapp_number == room.impostor_number:
                    await send_func(p.whatsapp_number, "🤫 *YOU ARE THE IMPOSTOR!*\nTry to blend in and guess the location.")
                else:
                    await send_func(p.whatsapp_number, f"📍 The location is: *{room.secret_word}*\nFind out who the impostor is!")
                    
            await send_func(sender_number, "Game started! Send '/start' again anytime to roll a new location and impostor.")
            return

        # 5. Fallback
        if not player.current_room:
            await send_func(sender_number, "Welcome to Impostor! 🕵️‍♂️\nSend */create* to host a game, or */join <code>* to enter one.")
        else:
            await send_func(sender_number, f"You are in room {player.current_room}. Wait for the host to send /start.")