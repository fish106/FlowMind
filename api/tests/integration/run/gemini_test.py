import os

from pytest_httpx import IteratorStream

from core.domain.models import Model
from tests.integration.common import (
    IntegrationTestClient,
)
from tests.utils import fixture_bytes, fixtures_json


async def test_gemini_thinking_streaming(test_client: IntegrationTestClient):
    task = await test_client.create_task()

    test_client.httpx_mock.add_response(
        url=f"https://generativelanguage.googleapis.com/v1alpha/models/gemini-2.0-flash-thinking-exp-01-21:streamGenerateContent?key={os.environ.get('GEMINI_API_KEY')}&alt=sse",
        stream=IteratorStream(fixture_bytes("gemini", "streamed_response_thoughts.txt").splitlines(keepends=True)),
    )
    chunks = [c async for c in test_client.stream_run_task_v1(task, model=Model.GEMINI_2_0_FLASH_THINKING_EXP_0121)]
    assert chunks

    assert chunks[1]["reasoning_steps"] == [
        {
            "step": 'The request asks for a greeting and a JSON response with "greeting" as the key.  This',
        },
    ]
    assert chunks[2]["reasoning_steps"] == [
        {
            "step": 'The request asks for a greeting and a JSON response with "greeting" as the key.  This is straightforward.\n\n1. **Greeting:**  Choose a friendly and common greeting.',
        },
    ]

    assert len(chunks[-1]["reasoning_steps"]) == 1
    assert len(chunks[-1]["reasoning_steps"][0]["step"]) == 608
    assert chunks[-1]["task_output"]["greeting"] == "Hello there!"


async def test_thinking_mode_model(test_client: IntegrationTestClient):
    task = await test_client.create_task()

    test_client.httpx_mock.add_response(
        url=f"https://generativelanguage.googleapis.com/v1alpha/models/gemini-2.0-flash-thinking-exp-01-21:generateContent?key={os.environ.get('GEMINI_API_KEY')}",
        json=fixtures_json("gemini", "completion_thoughts_gemini_2.0_flash_thinking_mode.json"),
    )

    run = await test_client.run_task_v1(
        task,
        model=Model.GEMINI_2_0_FLASH_THINKING_EXP_0121,
    )

    assert (
        run["task_output"]["greeting"]
        == "Explaining how AI works is a bit like explaining how a human brain works – it's incredibly complex and the exact mechanisms are still being researched. While the underlying mechanisms can be complex, the fundamental principles of data-driven learning and pattern recognition remain central.\n"
    )

    assert (
        run["reasoning_steps"][0]["step"]
        == 'My thinking process for generating the explanation of how AI works went something like this:\n\n1. **Deconstruct the Request:** The user asked "Explain how AI works." This is a broad question, so a comprehensive yet accessible explanation is needed. I need to cover the core principles without getting bogged down in overly technical jargon.\n\n2. **Identify Key Concepts:**  I immediately thought of the fundamental building blocks of AI. This led to the identification of:\n'
    )
