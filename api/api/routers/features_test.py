from httpx import AsyncClient

from core.domain.models.models import Model


class TestPreviewModels:
    async def test_preview_models(self, test_api_client: AsyncClient):
        response = await test_api_client.get("/features/models")
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) > 0

        model_ids = {item["id"] for item in items}
        assert len(model_ids) == 6  # this might change if one of the included models is also a default model
        assert Model.GPT_4O_AUDIO_PREVIEW_2024_12_17 not in model_ids
        assert Model.DEEPSEEK_R1_2501_BASIC in model_ids
        assert Model.MISTRAL_LARGE_2_LATEST in model_ids
        assert Model.LLAMA_3_3_70B in model_ids
