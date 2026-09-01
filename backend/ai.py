import os
from anthropic import Anthropic
from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

client = Anthropic(
    api_key=api_key
)
