
import os
from langchain_google_genai import ChatGoogleGenerativeAI
import logging
import absl.logging
import grpc

absl.logging.set_verbosity(absl.logging.ERROR)
logging.getLogger('grpc').setLevel(logging.ERROR)
# Set the USER_AGENT environment variable
os.environ["USER_AGENT"] = "MyUserAgent/1.0"

gemini_model = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0,
    max_tokens=None,
    timeout=60,  # Set timeout to 60 seconds
    max_retries=2,
    api_key=os.environ["GOOGLE_API_KEY"]
)
from langchain_community.document_loaders import WebBaseLoader

loader = WebBaseLoader("https://github.com/Dobot-Arm/TCP-IP-Python-V4.git")
data = loader.load()
print(data)

messages = [
    ("system", "You are a helpful assistant that translates English to French. Translate the user sentence."),
    ("human", "I love programming."),
]
try:
    ai_msg = gemini_model.invoke(messages)
    print(ai_msg)
except Exception as e:
    print(f"An error occurred: {e}")