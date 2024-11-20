from langchain_community.document_loaders import WebBaseLoader
from langchain.indexes import VectorstoreIndexCreator
from your_library import PersistentVectorStore
vectorstore = PersistentVectorStore()
index_creator = VectorstoreIndexCreator(vectorstore=vectorstore)
index_creator.from_loaders([WebBaseLoader("https://github.com/Dobot-Arm/TCP-IP-Python-V4.git")])
index_creator.query("什么是任务分解？")
# 创建loader，通过WebBaseLoader加载url内容
"""
loader = WebBaseLoader("https://github.com/Dobot-Arm/TCP-IP-Python-V4.git")
index = VectorstoreIndexCreator().from_loaders([loader])
index.query("什么是任务分解？")
"""