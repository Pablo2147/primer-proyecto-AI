from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

RUTA_VECTORSTORE = "vectorstore/"
SEPARADOR = "=" * 60


def titulo(texto: str) -> None:
    print(SEPARADOR)
    print(texto)
    print(SEPARADOR)


corpus = [
    "El cliente reintenta hasta 3 veces ante un TimeoutError, con espera creciente.",
    "Los errores de autenticacion nunca se reintentan: fallan de inmediato con un "
    "ValueError.",
    "El costo de cada llamada se calcula a partir de totalTokenCount y la tarifa "
    "vigente por cada 1000 tokens.",
    "El agente de la Unidad 2.4 decide por si mismo que herramienta usar, segun la "
    "descripcion de cada una.",
    "Las pruebas unitarias del cliente usan mocks, de forma que la suite completa "
    "corre en menos de un segundo.",
]

# PASO 1: chunking + embeddings + indexacion
titulo("PASO 1: chunking + embeddings + indexacion")

splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)
chunks = splitter.create_documents(corpus)

print(f"Corpus original: {len(corpus)} documentos")
print(f"Despues de chunking: {len(chunks)} chunks")
print()
for i, chunk in enumerate(chunks, start=1):
    print(f"  chunk {i}: {chunk.page_content}")
print()

print("Calculando embeddings e indexando en Chroma (esto llama a la API)...")
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# ids fijos: si el script se corre otra vez, se actualizan los mismos chunks
# en lugar de duplicarlos en el indice.
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    ids=[f"chunk-{i}" for i in range(1, len(chunks) + 1)],
    persist_directory=RUTA_VECTORSTORE,
)
print(f"Indexados {len(chunks)} chunks en {RUTA_VECTORSTORE}")
print()

# PASO 2: confirmar que quedo en disco
titulo("PASO 2: confirmando que quedo en disco, no solo en memoria")

elementos = sorted(Path(RUTA_VECTORSTORE).iterdir(), key=lambda p: p.name)
print(f"Contenido real de la carpeta {RUTA_VECTORSTORE} ({len(elementos)} elementos):")
for elemento in elementos:
    if elemento.is_dir():
        print(f"  {elemento.name}/")
    else:
        print(f"  {elemento.name}  ({elemento.stat().st_size} bytes)")
print()

# PASO 3: reconectar al indice persistido
titulo("PASO 3: reconectando al indice ya persistido (sin recalcular embeddings)")

vectorstore_recargado = Chroma(
    persist_directory=RUTA_VECTORSTORE,
    embedding_function=embeddings,
)
print(f"Chunks recuperados al reconectar: {vectorstore_recargado._collection.count()}")
