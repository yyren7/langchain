from IPython.display import Image

Image(agent.graph.get_graph().draw_png())

messages = [HumanMessage(content="What is the weather in sf?")]
result = agent.graph.invoke({"messages": messages})
print(result)
from IPython.display import Markdown
display(Markdown(result["messages"][-1].content))