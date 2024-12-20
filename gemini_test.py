import os
import google.generativeai as genai
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
print(os.getenv("GOOGLE_API_KEY"))
# Create the model
generation_config = {
  "temperature": 0,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-2.0-flash-thinking-exp-1219",
  generation_config=generation_config,
)

chat_session = model.start_chat(
  history=[
  ]
)

response = chat_session.send_message("why do i get meassage:WARNING: All log messages before absl::InitializeLog() is called are written to STDERR E0000 00:00:1733282340.949044   16480 init.cc:229] grpc_wait_for_shutdown_with_timeout() timed out.")

print(response.text)
