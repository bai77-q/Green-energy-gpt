from openai import AsyncOpenAI

GPT_MODEL = "gpt-4o-mini"
GPT4_MODEL = "gpt-4-turbo"
GPT4o_MODEL = "gpt-4o"
GPT4o_MINI_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"
ERNIE = "ERNIE-4.0-Turbo-8K"


async def get_gpt_txt_result(prompt: str, client: AsyncOpenAI, model=GPT_MODEL):
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content


async def get_gpt_stream_result(
    prompt: str,
    client: AsyncOpenAI,
    model=GPT_MODEL,
    temperature=0.9,
    update_cache_func=None,
):
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        stream=True,
        temperature=temperature,
    )
    complete_output = ""
    async for chunk in response:
        content = chunk.choices[0].delta.content
        if content is not None:
            complete_output += content
            yield content

    if update_cache_func:
        update_cache_func(complete_output)


async def get_ernie_stream_result(prompt: str, ernie_chat, model="ERNIE"):
    print(prompt)
    print(model)
    async for r in await ernie_chat.ado(
        model=model, messages=[{"role": "user", "content": prompt}], stream=True
    ):
        yield r["result"]


async def get_gpt_json_result(prompt: str, client: AsyncOpenAI, model=GPT4o_MODEL):
    print(prompt)
    response = await client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    try:
        return response.choices[0].message.content
    except Exception as e:
        print(e)
        return None


async def get_gpt_embedding(query, client: AsyncOpenAI) -> list[float]:
    response = await client.embeddings.create(input=[query], model=EMBEDDING_MODEL)
    return response.data[0].embedding
