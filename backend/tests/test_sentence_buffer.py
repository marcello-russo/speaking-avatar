import pytest
from app.services.sentence_buffer import SentenceBuffer


@pytest.mark.asyncio
async def test_push_single_token():
    sb = SentenceBuffer()
    assert sb.push("Ciao") is None


@pytest.mark.asyncio
async def test_emit_on_primary_boundary():
    sb = SentenceBuffer(soglia_base=100)
    sb.push("Ciao")
    sb.push("come")
    sb.push("stai?")
    result = sb.push("Oggi")
    assert result == "Ciao come stai?"


@pytest.mark.asyncio
async def test_emit_on_forced_threshold():
    sb = SentenceBuffer(soglia_base=15)
    sb.push("Ciao")
    sb.push("come")
    result = sb.push("oggi")
    assert result is not None
    assert "Ciao" in result


@pytest.mark.asyncio
async def test_flush_returns_remainder():
    sb = SentenceBuffer()
    sb.push("Ciao")
    sb.push("mondo")
    assert sb.flush() == "Ciao mondo"
    assert sb.flush() == ""


@pytest.mark.asyncio
async def test_queue_depth_backpressure():
    sb = SentenceBuffer(soglia_base=50)
    sb.set_queue_depth(3)
    words = "Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor".split()
    result = None
    for w in words:
        result = sb.push(w)
    assert result is None
    result = sb.push(".")
    assert result is not None
