"""Personal Knowledge Engine: upload PDFs, then ask questions about them.

Classic RAG setup with two halves:
  ingestion (/upload): pdf -> text -> chunks -> embeddings -> vector db
  query     (/ask):    question -> embedding -> nearest chunks -> LLM writes the answer
"""

import io

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import OpenAI, OpenAIError
from pydantic import BaseModel
from pypdf import PdfReader

# Pull OPENAI_API_KEY out of .env so it never has to live in the code.
load_dotenv()

app = FastAPI(title="Personal Knowledge Engine")

# Browsers won't let a page on one origin read responses from another unless the
# server allows it. Wide open is fine for a local tool; tighten before deploying.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# The embedding model maps text to a 384-dim vector where similar meaning ends up
# close together ("annual leave" lands near "holiday policy"). Loaded once at
# startup because it's a small neural net and loading per request would be slow.
# Documents and questions have to go through the same model or the vectors
# aren't comparable.
embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Persistent client writes to ./chroma_db, so the index survives restarts.
db = chromadb.PersistentClient(path="chroma_db")

# A collection is roughly a table. Because the embedder is attached here, Chroma
# embeds whatever we add() or query() on its own.
collection = db.get_or_create_collection("documents", embedding_function=embedder)


def chunk(text: str, size: int = 300, overlap: int = 50) -> list[str]:
    """Split text into overlapping windows of `size` words.

    We chunk because one embedding can only represent one idea well, and the
    retrieved pieces also have to fit in the LLM's context later. The overlap is
    there so a sentence sitting on a boundary isn't cut in half and lost to both
    sides.
    """
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + size]))
        if i + size >= len(words):
            break
        i += size - overlap  # slide forward, re-reading the last `overlap` words
    return chunks


@app.get("/")
def home():
    # The little test UI. It talks to /upload and /ask below.
    return FileResponse("index.html")


@app.post("/upload")
def upload(file: UploadFile):
    # We only know how to parse PDFs. (filename can technically be None, hence the guard.)
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "PDF files only")

    # pypdf wants a file-like object, so wrap the raw upload bytes in BytesIO.
    reader = PdfReader(io.BytesIO(file.file.read()))

    # Grab the text layer of every page. Pages that are pure images return None.
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    chunks = chunk(text)

    # Scanned PDFs have no text layer at all. Better to fail loudly than index
    # nothing. OCR would be the proper fix if we ever need those.
    if not chunks:
        raise HTTPException(400, "No extractable text — scanned/image PDF?")

    # Chroma embeds each chunk and stores: a unique id per chunk, the chunk text
    # itself (we hand it to the LLM later), and the source filename for citations.
    collection.add(
        ids=[f"{file.filename}-{n}" for n in range(len(chunks))],
        documents=chunks,
        metadatas=[{"source": file.filename} for _ in chunks],
    )
    return {"file": file.filename, "chunks": len(chunks)}


class Question(BaseModel):
    """Request body for /ask. Pydantic rejects anything malformed with a 422
    before our code even runs."""

    question: str
    n_results: int = 4  # how many chunks to retrieve


@app.post("/ask")
def ask(q: Question):
    if collection.count() == 0:
        raise HTTPException(404, "No documents uploaded yet")

    # Retrieval: embed the question and pull the n_results chunks whose vectors
    # sit closest in meaning.
    results = collection.query(query_texts=[q.question], n_results=q.n_results)

    # query() accepts several questions at once so everything comes back as
    # lists-of-lists; [0] is our single question.
    docs = results["documents"][0]

    # Join the retrieved chunks into one context block, visibly separated so the
    # model can tell where one ends and the next begins.
    context = "\n\n---\n\n".join(docs)

    # Generation: give the model the context and the question. The system message
    # is what keeps it honest; without it the model falls back on whatever it
    # learned in training and happily makes things up.
    try:
        answer = (
            OpenAI()  # picks up OPENAI_API_KEY from the environment
            .chat.completions.create(
                model="gpt-4o-mini",  # reading comprehension doesn't need a big model
                messages=[
                    {
                        "role": "system",
                        "content": "Answer using ONLY the provided context. "
                        "If the answer is not in the context, say you don't know.",
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {q.question}",
                    },
                ],
            )
            .choices[0]
            .message.content
        )
    except OpenAIError as e:
        # Bad key, no credits, outage: not our bug, so report it as a bad
        # upstream (502) rather than a generic 500.
        raise HTTPException(502, f"LLM call failed: {e}")

    # Unique source filenames of the retrieved chunks, so the answer is checkable.
    sources = sorted({m["source"] for m in results["metadatas"][0]})
    return {"answer": answer, "sources": sources}
