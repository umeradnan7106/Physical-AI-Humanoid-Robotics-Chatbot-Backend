"""
Ingest book content into Qdrant vector database (FREE VERSION)
Uses Sentence Transformers for embeddings instead of OpenAI
"""
import os
import re
import hashlib
from pathlib import Path
from typing import List, Dict
import markdown
from bs4 import BeautifulSoup
from rag_free import create_collection, upsert_document
from dotenv import load_dotenv

load_dotenv()

DOCS_DIR = Path(__file__).parent.parent / "docs"
CHUNK_SIZE = 500  # words per chunk
CHUNK_OVERLAP = 50  # word overlap between chunks

def clean_markdown(text: str) -> str:
    """Convert markdown to plain text"""
    # Convert markdown to HTML
    html = markdown.markdown(text)
    # Extract text from HTML
    soup = BeautifulSoup(html, 'html.parser')
    # Remove code blocks (we'll keep them but clean)
    text = soup.get_text()
    # Clean extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if len(chunk.split()) > 50:  # Minimum chunk size
            chunks.append(chunk)

    return chunks

def extract_metadata_from_path(file_path: Path) -> Dict:
    """Extract metadata from file path"""
    parts = file_path.parts

    # Determine module
    module = ""
    if "module-01-ros2" in parts:
        module = "Module 1: ROS 2 Fundamentals"
    elif "module-02-simulation" in parts:
        module = "Module 2: Simulation"
    elif "module-03-isaac" in parts:
        module = "Module 3: Isaac Sim"
    elif "module-04-vla" in parts:
        module = "Module 4: VLA Integration"
    elif "introduction" in parts:
        module = "Introduction"
    elif "getting-started" in parts:
        module = "Getting Started"
    elif "capstone" in parts:
        module = "Capstone Project"

    # Extract title from filename
    title = file_path.stem.replace('-', ' ').title()

    # Generate URL
    relative_path = file_path.relative_to(DOCS_DIR)
    url = f"/docs/{str(relative_path).replace(os.sep, '/').replace('.md', '')}"

    return {
        "module": module,
        "title": title,
        "url": url,
        "chapter": f"{module} - {title}" if module else title
    }

def process_markdown_file(file_path: Path) -> List[Dict]:
    """Process a single markdown file"""
    print(f"Processing: {file_path.name}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Clean markdown
    clean_text = clean_markdown(content)

    # Extract metadata
    metadata = extract_metadata_from_path(file_path)

    # Split into chunks
    chunks = split_into_chunks(clean_text)

    # Create documents with metadata
    documents = []
    for idx, chunk in enumerate(chunks):
        # Generate unique ID
        chunk_id = hashlib.md5(
            f"{file_path.name}_{idx}_{chunk[:50]}".encode()
        ).hexdigest()

        documents.append({
            "id": chunk_id,
            "text": chunk,
            "metadata": {
                **metadata,
                "chunk_index": idx,
                "total_chunks": len(chunks)
            }
        })

    return documents

def ingest_all_documents():
    """Ingest all markdown files from docs directory"""
    print("Starting book content ingestion (FREE VERSION)...")
    print("Using Sentence Transformers for embeddings (384 dimensions)")

    # Create collection
    create_collection()

    # Find all markdown files
    md_files = list(DOCS_DIR.rglob("*.md"))

    # Exclude certain files
    exclude_patterns = ['create_placeholders', 'tutorial-', 'blog']
    md_files = [
        f for f in md_files
        if not any(pattern in str(f) for pattern in exclude_patterns)
    ]

    print(f"Found {len(md_files)} markdown files")

    total_chunks = 0

    # Process each file
    for file_path in md_files:
        try:
            documents = process_markdown_file(file_path)

            # Upload to Qdrant
            for doc in documents:
                upsert_document(
                    chunk_id=doc["id"],
                    text=doc["text"],
                    metadata=doc["metadata"]
                )

            total_chunks += len(documents)
            print(f"  Uploaded {len(documents)} chunks")

        except Exception as e:
            print(f"  Error processing {file_path.name}: {e}")

    print(f"\nIngestion complete!")
    print(f"Total chunks uploaded: {total_chunks}")
    print(f"Total files processed: {len(md_files)}")

if __name__ == "__main__":
    ingest_all_documents()
