"""Unit tests for the vision adapters and the meal-photo use case."""

import httpx
import pytest

from app.application.use_cases.nutrition_use_cases import (
    AnalyzeMealPhoto,
    ImageTooLargeError,
    UnsupportedImageTypeError,
)
from app.domain.entities.estimated_food import EstimatedFood
from app.domain.ports.vision import VisionPort, VisionUnavailableError
from app.infrastructure.ai.vision import GeminiVision, StubVision

IMAGE = b"\xff\xd8\xff\xe0 fake jpeg bytes"


def _gemini_json(text: str) -> httpx.Response:
    payload = {"candidates": [{"content": {"parts": [{"text": text}]}}]}
    return httpx.Response(200, json=payload, request=httpx.Request("POST", "https://x/vision"))


async def test_stub_vision_returns_editable_estimates() -> None:
    items = await StubVision().analyze_meal(IMAGE, "image/jpeg")
    assert items
    assert all(item.grams > 0 for item in items)


async def test_gemini_vision_parses_items_and_sends_the_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def fake_post(self: httpx.AsyncClient, url: str, **kwargs: object) -> httpx.Response:
        captured["url"] = url
        captured["json"] = kwargs["json"]
        captured["headers"] = kwargs["headers"]
        return _gemini_json(
            '{"items":[{"name":"huevo frito","grams":55,"kcal":80,'
            '"protein_g":7,"carbs_g":0.6,"fat_g":5.5}]}'
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    items = await GeminiVision("k", "gemini-3.1-flash-lite").analyze_meal(IMAGE, "image/jpeg")

    assert items == [
        EstimatedFood(name="huevo frito", grams=55, kcal=80, protein_g=7, carbs_g=0.6, fat_g=5.5)
    ]
    assert str(captured["url"]).endswith("models/gemini-3.1-flash-lite:generateContent")
    body = captured["json"]
    assert isinstance(body, dict)
    # The image travels inline (base64) and JSON output is forced by schema.
    assert "inline_data" in body["contents"][0]["parts"][1]
    assert body["generationConfig"]["responseMimeType"] == "application/json"


@pytest.mark.parametrize(
    "text",
    ["no soy json", "", '{"items":"not a list"}'],
)
async def test_gemini_vision_tolerates_unusable_replies(
    monkeypatch: pytest.MonkeyPatch, text: str
) -> None:
    # A 200 with an unexpected shape must mean "no foods", never an exception.
    async def fake_post(self: httpx.AsyncClient, url: str, **kwargs: object) -> httpx.Response:
        return _gemini_json(text)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    assert await GeminiVision("k", "m").analyze_meal(IMAGE, "image/jpeg") == []


async def test_gemini_vision_drops_absurd_or_malformed_items(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_post(self: httpx.AsyncClient, url: str, **kwargs: object) -> httpx.Response:
        return _gemini_json(
            '{"items":['
            '{"name":"","grams":10,"kcal":10,"protein_g":1,"carbs_g":1,"fat_g":1},'
            '{"name":"plato gigante","grams":9000,"kcal":10,"protein_g":1,"carbs_g":1,"fat_g":1},'
            '{"name":"sin gramos","kcal":10,"protein_g":1,"carbs_g":1,"fat_g":1},'
            '{"name":"negativo","grams":50,"kcal":10,"protein_g":-3,"carbs_g":1,"fat_g":1},'
            '{"name":"tomate","grams":80,"kcal":15,"protein_g":0.7,"carbs_g":3,"fat_g":0.2}]}'
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    items = await GeminiVision("k", "m").analyze_meal(IMAGE, "image/jpeg")
    assert [item.name for item in items] == ["tomate"]


async def test_gemini_vision_raises_unavailable_on_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_post(self: httpx.AsyncClient, url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(
            429, json={"error": "quota"}, request=httpx.Request("POST", "https://x/vision")
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    with pytest.raises(VisionUnavailableError):
        await GeminiVision("k", "m").analyze_meal(IMAGE, "image/jpeg")


class _DownVision(VisionPort):
    async def analyze_meal(self, image: bytes, mime_type: str) -> list[EstimatedFood]:
        raise VisionUnavailableError("provider down")


class _EmptyVision(VisionPort):
    async def analyze_meal(self, image: bytes, mime_type: str) -> list[EstimatedFood]:
        return []


async def test_analyze_meal_photo_returns_items_with_a_note() -> None:
    result = await AnalyzeMealPhoto(StubVision(), 1024).execute(IMAGE, "image/jpeg")
    assert result.items
    assert result.available is True
    assert "ajusta los gramos" in result.note
    assert "no es consejo" in result.note.lower()  # the nutrition disclaimer travels along


async def test_analyze_meal_photo_flags_an_unavailable_provider() -> None:
    # Graceful degradation: no exception reaches the router (it used to be a 500).
    result = await AnalyzeMealPhoto(_DownVision(), 1024).execute(IMAGE, "image/jpeg")
    assert result.items == ()
    assert result.available is False


async def test_analyze_meal_photo_reports_no_food_differently() -> None:
    result = await AnalyzeMealPhoto(_EmptyVision(), 1024).execute(IMAGE, "image/jpeg")
    assert result.items == ()
    assert result.available is True  # the provider answered, there was just no food


@pytest.mark.parametrize("mime", ["text/plain", "application/pdf", "", "image/gif"])
async def test_analyze_meal_photo_rejects_non_image_uploads(mime: str) -> None:
    with pytest.raises(UnsupportedImageTypeError):
        await AnalyzeMealPhoto(StubVision(), 1024).execute(IMAGE, mime)


async def test_analyze_meal_photo_rejects_an_oversized_image() -> None:
    with pytest.raises(ImageTooLargeError):
        await AnalyzeMealPhoto(StubVision(), max_image_bytes=4).execute(IMAGE, "image/jpeg")


async def test_analyze_meal_photo_accepts_a_charset_suffixed_mime() -> None:
    # Browsers may send `image/jpeg; charset=binary`.
    result = await AnalyzeMealPhoto(StubVision(), 1024).execute(IMAGE, "image/jpeg; charset=binary")
    assert result.items
