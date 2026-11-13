from src.pdf_reader import split_into_chunks

def test_chunks_keep_page_and_source():
    pages = [{"text": "A " * 1200, "page": 4, "source": "sample.pdf"}]
    chunks = split_into_chunks(pages, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert all(item["page"] == 4 for item in chunks)
    assert all(item["source"] == "sample.pdf" for item in chunks)
    assert all(len(item["text"]) <= 100 for item in chunks)
