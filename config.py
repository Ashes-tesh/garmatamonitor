import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    'bot_token': os.getenv('BOT_TOKEN'),
    'server_ip': os.getenv('SERVER_IP'),
    'server_port': int(os.getenv('SERVER_PORT', 27038))
}