
from pathlib import Path
from io import BytesIO
from uuid import uuid4
import shutil

from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS


PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge_base"
VECTOR_STORE_PATH = PROJECT_ROOT / "assets" / "faiss_index"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )


def load_knowledge_documents():
    documents = []
    KNOWLEDGE_BASE.mkdir(parents=True, exist_ok=True)

    for file_path in KNOWLEDGE_BASE.rglob("*"):
        if not file_path.is_file():
            continue

        extension = file_path.suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            continue

        if extension == ".pdf":
            reader = PdfReader(str(file_path))

            for page_number, page in enumerate(reader.pages, start=1):
                content = (page.extract_text() or "").strip()

                if content:
                    documents.append(
                        Document(
                            page_content=content,
                            metadata={
                                "source": file_path.name,
                                "page": page_number
                            }
                        )
                    )

        else:
            content = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            ).strip()

            if content:
                documents.append(
                    Document(
                        page_content=content,
                        metadata={"source": file_path.name}
                    )
                )

    if not documents:
        raise ValueError(
            "Knowledge base is empty. Add TXT, MD or PDF documents."
        )

    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    return splitter.split_documents(documents)


def build_vector_store():
    documents = load_knowledge_documents()
    chunks = split_documents(documents)

    embeddings = get_embeddings()

    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings
    )

    VECTOR_STORE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if VECTOR_STORE_PATH.exists():
        shutil.rmtree(VECTOR_STORE_PATH)

    vector_store.save_local(str(VECTOR_STORE_PATH))

    return vector_store


def rebuild_vector_store():
    """Rebuild FAISS after adding or changing knowledge documents."""
    return build_vector_store()


def load_vector_store():
    index_file = VECTOR_STORE_PATH / "index.faiss"

    if not index_file.exists():
        return build_vector_store()

    embeddings = get_embeddings()

    return FAISS.load_local(
        str(VECTOR_STORE_PATH),
        embeddings,
        allow_dangerous_deserialization=True
    )


def add_uploaded_document(uploaded_file):
    """Save an uploaded PDF, TXT or MD file to the knowledge base."""

    if uploaded_file is None:
        raise ValueError("Please select a document.")

    original_name = Path(uploaded_file.name).name
    extension = Path(original_name).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Only PDF, TXT and MD files are supported.")

    file_bytes = uploaded_file.getvalue()

    if not file_bytes:
        raise ValueError("The uploaded document is empty.")

    upload_folder = KNOWLEDGE_BASE / "uploads"
    upload_folder.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid4().hex[:8]}_{original_name}"
    destination = upload_folder / safe_name

    destination.write_bytes(file_bytes)

    return {
        "filename": original_name,
        "saved_as": safe_name,
        "path": str(destination)
    }


def retrieve_documents(question, k=4):
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    vector_store = load_vector_store()

    return vector_store.similarity_search(
        question,
        k=k
    )


def retrieve_context(question, k=4):
    documents = retrieve_documents(question, k)

    context = "\n\n".join(
        document.page_content
        for document in documents
    )

    sources = list(
        dict.fromkeys(
            document.metadata.get("source", "Unknown")
            for document in documents
        )
    )

    return {
        "context": context,
        "sources": sources
    }
