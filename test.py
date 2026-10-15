
from openai import OpenAI

client = OpenAI(
    base_url="https://q5dh1rfszfym23hj.us-east-2.aws.endpoints.huggingface.cloud/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V4-Flash-0731",
    messages=[
        {"role": "user", "content": "Viết hàm tính Fibonacci bằng Python"}
    ]
)

print(response.choices[0].message.content)
