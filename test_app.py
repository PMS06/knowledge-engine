from app import chunk


def test_chunk():
    assert chunk("") == []
    assert chunk("a b c") == ["a b c"]  # shorter than one window -> one chunk
    words = " ".join(str(n) for n in range(700))
    chunks = chunk(words, size=300, overlap=50)
    assert len(chunks) == 3
    assert chunks[0].split()[-50:] == chunks[1].split()[:50]  # overlap preserved
    assert chunks[-1].split()[-1] == "699"  # no words lost at the tail
