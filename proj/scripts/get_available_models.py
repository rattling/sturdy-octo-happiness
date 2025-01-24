from openai import OpenAI
from helper import get_openai_api_key
import os

OPENAPI_KEY = get_openai_api_key()
client = OpenAI(api_key=OPENAPI_KEY)

models = client.models.list()
for model in models:
    print(model.id)
