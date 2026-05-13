import pytest
import asyncio
from app.services.sentence_buffer import SentenceBuffer


@pytest.mark.asyncio
async def test_push_single_token():
    sb = SentenceBuffer()
    assert sb.push(" Ciao") is None


@pytest.mark.asyncio
async def test_emit_on_primary_boundary():
    sb = SentenceBuffer(soglia_base=100)
    sb.push(" Ciao")
    sb.push(" come")
    sb.push(" stai?")
    result = sb.push(" Oggi")
    assert result == " Ciao come stai?"


@pytest.mark.asyncio
async def test_emit_on_forced_threshold():
    sb = SentenceBuffer(soglia_base=15)
    sb.push(" Ciao")
    sb.push(" come")
    result = sb.push(" oggi")
    assert result is not None


@pytest.mark.asyncio
async def test_flush_returns_remainder():
    sb = SentenceBuffer()
    sb.push(" Ciao")
    sb.push(" mondo")
    assert sb.flush() == " Ciao mondo"
    assert sb.flush() == ""


@pytest.mark.asyncio
async def test_queue_depth_backpressure():
    sb = SentenceBuffer(soglia_base=50)
    sb.set_queue_depth(3)
    tokens = [f" {w}" for w in "Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor".split()]
    result = None
    for t in tokens:
        result = sb.push(t)
    assert result is None
    result = sb.push(".")
    assert result is not None


@pytest.mark.asyncio
async def test_apostrophe_merge():
    sb = SentenceBuffer()
    sb.push(" dell")
    result = sb.push("'informatica")
    assert sb.flush() == " dell'informatica"


@pytest.mark.asyncio
async def test_no_word_split_on_forced_emit():
    sb = SentenceBuffer(soglia_base=10)
    sb.push(" Ciao")
    sb.push(" come")
    result = sb.push(" stai")
    assert result is not None
    remaining = sb.flush()
    assert "stai" not in result or "stai" in remaining


@pytest.mark.asyncio
async def test_multi_sentence_order():
    """Two complete sentences emitted in correct order."""
    sb = SentenceBuffer(soglia_base=100)
    tokens = " Ciao come stai ? Oggi studiamo le frane".split()
    results = []
    for t in tokens:
        r = sb.push(t)
        if r:
            results.append(r)
    r = sb.flush()
    if r:
        results.append(r)
    assert len(results) == 2
    assert "Ciao" in results[0]
    assert "frane" in results[1]


@pytest.mark.asyncio
async def test_sentence_timeout_emits_in_order():
    """Timeout should emit first complete chunk, rest stays."""
    sb = SentenceBuffer(soglia_base=200, timeout_ms=50)
    tokens = " Le frane sono molto pericolose Esempio".split()
    results = []
    for t in tokens:
        r = sb.push(t)
        if r:
            results.append(r)
        await asyncio.sleep(0.03)
    r = sb.flush()
    if r:
        results.append(r)
    assert len(results) >= 2
    all_text = "".join(results)
    assert "frane" in all_text
    assert "Esempio" in all_text
