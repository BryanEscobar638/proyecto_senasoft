from openai import OpenAI

client = OpenAI(
  api_key="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"
)

response = client.responses.create(
  model="gpt-5-nano",
  input="write a haiku about ai",
  store=True,
)

print(response.output_text);
