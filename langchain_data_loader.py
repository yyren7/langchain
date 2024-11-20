from langchain_community.document_loaders import WebBaseLoader

loader = WebBaseLoader("https://github.com/Dobot-Arm/TCP-IP-Python-V4.git")
data = loader.load()
print(data)