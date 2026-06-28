# ============================================================
# ingest.py
# PRODUCTION-QUALITY WEBSITE CRAWLER + RAG INGESTION PIPELINE
#
# Final improved version:
# - No hardcoded URL
# - Crawls only when called from main.py button click
# - Max pages fixed to 5
# - Crawl depth fixed to 3
# - robots.txt check
# - Retry logic
# - Duplicate content detection
# - Per-website Chroma DB folder
# - Per-website crawl manifest
# - No PDF generation
# ============================================================

import hashlib
import json
import re
import shutil
import time
import urllib.robotparser
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ============================================================
# ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "social_eagle.env"
load_dotenv(dotenv_path=ENV_PATH)


# ============================================================
# FIXED CONFIGURATION
# ============================================================

MAX_PAGES = 5
MAX_DEPTH = 3
REQUEST_DELAY_SECONDS = 0.4

MIN_CONTENT_CHARS = 30
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150

CHROMA_PARENT_FOLDER = BASE_DIR / "chroma_dbs"
COLLECTION_NAME = "website_knowledge_base"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/120 Safari/537.36"
)


# ============================================================
# PROGRESS HELPER
# ============================================================

def emit_progress(progress_callback: Optional[Callable[[str], None]], message: str) -> None:
    """
    Sends progress messages to Streamlit if callback is provided.
    Also prints messages to terminal.
    """
    print(message)

    if progress_callback:
        progress_callback(message)


# ============================================================
# URL VALIDATION
# ============================================================

def ensure_url_has_scheme(url: str) -> str:
    """
    Adds https:// if user enters a URL without http/https.
    """
    url = url.strip()

    if not url:
        raise ValueError("URL cannot be empty.")

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    return url


def normalize_url(url: str) -> str:
    """
    Removes URL fragments and normalizes trailing slash.
    """
    url, _ = urldefrag(url)
    url = url.strip()

    parsed = urlparse(url)

    if parsed.path and not parsed.path.endswith("/"):
        last_part = parsed.path.split("/")[-1]

        if "." not in last_part:
            url = url + "/"

    return url


def validate_start_url(url: str) -> str:
    """
    Validates the user-provided URL.
    """
    url = ensure_url_has_scheme(url)
    parsed = urlparse(url)

    if parsed.scheme not in ["http", "https"]:
        raise ValueError("Only http and https URLs are supported.")

    if not parsed.netloc:
        raise ValueError("Invalid URL. Please enter a valid website URL.")

    if "." not in parsed.netloc:
        raise ValueError("Invalid URL. Please enter a proper domain such as https://example.com")

    return normalize_url(url)


def get_allowed_domain(start_url: str) -> str:
    """
    Returns the domain of the start URL.
    """
    return urlparse(start_url).netloc.lower()


def is_valid_internal_url(url: str, allowed_domain: str) -> bool:
    """
    Allows only internal website HTML pages.
    Skips files, media, scripts, documents, and social links.
    """
    if not url:
        return False

    url = normalize_url(url)
    parsed = urlparse(url)

    if parsed.scheme not in ["http", "https"]:
        return False

    if parsed.netloc.lower() != allowed_domain.lower():
        return False

    lower_url = url.lower()

    skip_patterns = [
        "mailto:",
        "tel:",
        "javascript:",
        ".jpg",
        ".jpeg",
        ".png",
        ".svg",
        ".gif",
        ".webp",
        ".ico",
        ".css",
        ".js",
        ".zip",
        ".mp4",
        ".mp3",
        ".xml",
        ".json",
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        "facebook.com",
        "linkedin.com",
        "twitter.com",
        "x.com",
        "instagram.com",
        "youtube.com",
        "tiktok.com",
    ]

    return not any(pattern in lower_url for pattern in skip_patterns)


def get_site_hash(start_url: str) -> str:
    """
    Creates a stable hash for a website URL.
    """
    clean_url = normalize_url(start_url).lower()
    return hashlib.sha256(clean_url.encode("utf-8")).hexdigest()[:12]


def get_chroma_db_folder(start_url: str) -> str:
    """
    Returns one Chroma DB folder per website URL.
    """
    site_hash = get_site_hash(start_url)
    return str(CHROMA_PARENT_FOLDER / f"site_{site_hash}")


# ============================================================
# ROBOTS.TXT
# ============================================================

def is_allowed_by_robots(url: str, user_agent: str = USER_AGENT) -> bool:
    """
    Checks robots.txt. If robots.txt cannot be read, crawler continues.
    """
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    robot_parser = urllib.robotparser.RobotFileParser()

    try:
        robot_parser.set_url(robots_url)
        robot_parser.read()
        return robot_parser.can_fetch(user_agent, url)

    except Exception:
        return True


# ============================================================
# HTTP SESSION WITH RETRY
# ============================================================

def create_requests_session() -> requests.Session:
    """
    Creates a requests session with retry support.
    """
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.7,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )

    return session


def fetch_html(session: requests.Session, url: str) -> str:
    """
    Downloads HTML content.
    """
    response = session.get(
        url,
        timeout=30,
        allow_redirects=True,
    )

    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()

    if "text/html" not in content_type:
        raise ValueError(f"Skipped non-HTML page. Content-Type: {content_type}")

    return response.text


# ============================================================
# HTML EXTRACTION
# ============================================================

def extract_title(soup: BeautifulSoup, fallback_url: str) -> str:
    """
    Extracts page title.
    """
    h1 = soup.find("h1")

    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)

    if soup.title and soup.title.get_text(strip=True):
        return soup.title.get_text(strip=True)

    return fallback_url


def extract_meta_description(soup: BeautifulSoup) -> str:
    """
    Extracts meta description.
    """
    meta = soup.find("meta", attrs={"name": "description"})

    if meta and meta.get("content"):
        return meta.get("content", "").strip()

    og_description = soup.find("meta", attrs={"property": "og:description"})

    if og_description and og_description.get("content"):
        return og_description.get("content", "").strip()

    return ""


def extract_clean_text(soup: BeautifulSoup) -> str:
    """
    Extracts clean readable text from HTML.
    """
    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    cleaned_lines = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        if len(line) <= 1:
            continue

        cleaned_lines.append(line)

    clean_text = "\n".join(cleaned_lines)
    clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)

    return clean_text.strip()


def build_page_content(title: str, meta_description: str, clean_text: str, url: str) -> str:
    """
    Builds final content for a page.
    """
    parts = []

    if title:
        parts.append(f"Page Title: {title}")

    if meta_description:
        parts.append(f"Page Description: {meta_description}")

    if clean_text:
        parts.append(clean_text)

    parts.append(f"Source URL: {url}")

    return "\n\n".join(parts).strip()


def extract_internal_links(
    soup: BeautifulSoup,
    base_url: str,
    allowed_domain: str,
) -> List[str]:
    """
    Extracts valid internal links.
    """
    links = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(base_url, href)
        full_url = normalize_url(full_url)

        if is_valid_internal_url(full_url, allowed_domain):
            links.add(full_url)

    return sorted(list(links))


def extract_menu_links(
    soup: BeautifulSoup,
    base_url: str,
    allowed_domain: str,
) -> List[str]:
    """
    Extracts menu/header links first.
    Falls back to all internal links.
    """
    menu_links = set()

    nav_candidates = []
    nav_candidates.extend(soup.find_all("nav"))
    nav_candidates.extend(soup.find_all("header"))

    for nav in nav_candidates:
        for a_tag in nav.find_all("a", href=True):
            full_url = urljoin(base_url, a_tag["href"])
            full_url = normalize_url(full_url)

            if is_valid_internal_url(full_url, allowed_domain):
                menu_links.add(full_url)

    if len(menu_links) < 3:
        menu_links.update(
            extract_internal_links(
                soup=soup,
                base_url=base_url,
                allowed_domain=allowed_domain,
            )
        )

    menu_links.add(normalize_url(base_url))

    return sorted(list(menu_links))


# ============================================================
# METADATA
# ============================================================

def classify_section(url: str) -> str:
    """
    Creates section name from first URL path segment.
    """
    parsed = urlparse(url)
    path = parsed.path.strip("/").lower()

    if not path:
        return "Home"

    first_segment = path.split("/")[0]

    return first_segment.replace("-", " ").title()


def classify_subsection(url: str) -> str:
    """
    Creates subsection name from full URL path.
    """
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    if not path:
        return "Home"

    return " / ".join(
        part.replace("-", " ").title()
        for part in path.split("/")
    )


# ============================================================
# CHROMA FOLDER SAFETY
# ============================================================

def reset_chroma_folder(chroma_db_folder: str) -> None:
    """
    Removes old Chroma folder safely before recreating it.
    """
    db_path = Path(chroma_db_folder)

    if not db_path.exists():
        db_path.mkdir(parents=True, exist_ok=True)
        return

    for attempt in range(3):
        try:
            shutil.rmtree(db_path)
            break
        except PermissionError:
            time.sleep(1)

    db_path.mkdir(parents=True, exist_ok=True)


# ============================================================
# CRAWLING
# ============================================================

def crawl_site(
    start_url: str,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[List[Document], List[Dict]]:
    """
    Crawls a website using:
    - MAX_PAGES = 5
    - MAX_DEPTH = 3
    """
    start_url = validate_start_url(start_url)
    allowed_domain = get_allowed_domain(start_url)

    emit_progress(progress_callback, "🚀 Starting website crawl...")
    emit_progress(progress_callback, f"Start URL: {start_url}")
    emit_progress(progress_callback, f"Maximum pages: {MAX_PAGES}")
    emit_progress(progress_callback, f"Crawl depth: {MAX_DEPTH}")

    if not is_allowed_by_robots(start_url):
        raise ValueError("This website does not allow crawling based on robots.txt.")

    session = create_requests_session()

    visited = set()
    queued = set()
    queue: List[Tuple[str, int]] = []

    documents: List[Document] = []
    manifest: List[Dict] = []
    skipped_pages: List[Dict] = []
    content_hashes = set()

    try:
        main_html = fetch_html(session, start_url)
        main_soup = BeautifulSoup(main_html, "html.parser")
    except Exception as error:
        raise ValueError(f"Could not open the start URL. Reason: {error}")

    menu_links = extract_menu_links(
        soup=main_soup,
        base_url=start_url,
        allowed_domain=allowed_domain,
    )

    queue.append((start_url, 0))
    queued.add(start_url)

    for link in menu_links:
        if link not in queued:
            queue.append((link, 1))
            queued.add(link)

    while queue and len(documents) < MAX_PAGES:
        current_url, depth = queue.pop(0)
        current_url = normalize_url(current_url)

        if current_url in visited:
            continue

        if depth > MAX_DEPTH:
            skipped_pages.append(
                {
                    "url": current_url,
                    "reason": f"Depth {depth} exceeded max depth {MAX_DEPTH}",
                }
            )
            continue

        if not is_valid_internal_url(current_url, allowed_domain):
            skipped_pages.append(
                {
                    "url": current_url,
                    "reason": "Invalid or external URL",
                }
            )
            continue

        if not is_allowed_by_robots(current_url):
            skipped_pages.append(
                {
                    "url": current_url,
                    "reason": "Blocked by robots.txt",
                }
            )
            visited.add(current_url)
            continue

        try:
            emit_progress(progress_callback, f"🔎 Crawling page {len(documents) + 1}: {current_url}")

            html = fetch_html(session, current_url)
            soup = BeautifulSoup(html, "html.parser")

            title = extract_title(soup, current_url)
            meta_description = extract_meta_description(soup)
            clean_text = extract_clean_text(soup)

            final_content = build_page_content(
                title=title,
                meta_description=meta_description,
                clean_text=clean_text,
                url=current_url,
            )

            if len(final_content) < MIN_CONTENT_CHARS:
                skipped_pages.append(
                    {
                        "url": current_url,
                        "reason": "Page content too short",
                        "characters": len(final_content),
                        "preview": final_content[:300],
                    }
                )
                visited.add(current_url)
                continue

            content_hash = hashlib.sha256(final_content.encode("utf-8")).hexdigest()

            if content_hash in content_hashes:
                skipped_pages.append(
                    {
                        "url": current_url,
                        "reason": "Duplicate page content",
                    }
                )
                visited.add(current_url)
                continue

            content_hashes.add(content_hash)

            section = classify_section(current_url)
            subsection = classify_subsection(current_url)

            document = Document(
                page_content=final_content,
                metadata={
                    "source": current_url,
                    "title": title,
                    "section": section,
                    "subsection": subsection,
                    "depth": depth,
                },
            )

            documents.append(document)

            manifest.append(
                {
                    "url": current_url,
                    "title": title,
                    "section": section,
                    "subsection": subsection,
                    "depth": depth,
                    "characters": len(final_content),
                }
            )

            visited.add(current_url)

            emit_progress(progress_callback, f"✅ Loaded: {title}")

            child_links = extract_internal_links(
                soup=soup,
                base_url=current_url,
                allowed_domain=allowed_domain,
            )

            for child_link in child_links:
                child_link = normalize_url(child_link)

                if child_link not in visited and child_link not in queued and depth + 1 <= MAX_DEPTH:
                    queue.append((child_link, depth + 1))
                    queued.add(child_link)

            time.sleep(REQUEST_DELAY_SECONDS)

        except Exception as error:
            skipped_pages.append(
                {
                    "url": current_url,
                    "reason": str(error),
                }
            )

            visited.add(current_url)

    if not documents:
        debug_message = "No documents were crawled successfully.\n\nReasons found:\n"

        for item in skipped_pages[:5]:
            debug_message += f"- URL: {item.get('url')}\n"
            debug_message += f"  Reason: {item.get('reason')}\n"

            if "characters" in item:
                debug_message += f"  Characters extracted: {item.get('characters')}\n"

            if "preview" in item:
                debug_message += f"  Preview: {item.get('preview')}\n"

        debug_message += (
            "\nPossible causes: JavaScript-rendered website, robots.txt restrictions, "
            "bot protection, redirects, or limited readable HTML content."
        )

        raise ValueError(debug_message)

    emit_progress(progress_callback, f"✅ Crawling completed. Pages loaded: {len(documents)}")

    return documents, manifest


# ============================================================
# MANIFEST
# ============================================================

def save_manifest(manifest: List[Dict], chroma_db_folder: str) -> str:
    """
    Saves manifest inside the website-specific Chroma folder.
    """
    manifest_path = Path(chroma_db_folder) / "crawl_manifest.json"

    with open(manifest_path, "w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=4, ensure_ascii=False)

    return str(manifest_path)


# ============================================================
# CHUNKING
# ============================================================

def split_documents(
    documents: List[Document],
    progress_callback: Optional[Callable[[str], None]] = None,
) -> List[Document]:
    """
    Splits documents into chunks.
    """
    emit_progress(progress_callback, "✂️ Splitting documents into chunks...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    chunks = splitter.split_documents(documents)

    if not chunks:
        raise ValueError("No chunks were created.")

    emit_progress(progress_callback, f"✅ Chunks created: {len(chunks)}")

    return chunks


# ============================================================
# EMBEDDINGS
# ============================================================

def create_embedding_model(
    progress_callback: Optional[Callable[[str], None]] = None,
) -> HuggingFaceEmbeddings:
    """
    Loads HuggingFace embedding model.
    """
    emit_progress(progress_callback, "🤖 Loading embedding model...")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME
    )

    emit_progress(progress_callback, "✅ Embedding model loaded.")

    return embeddings


# ============================================================
# VECTOR DB
# ============================================================

def create_vector_database(
    chunks: List[Document],
    embeddings: HuggingFaceEmbeddings,
    chroma_db_folder: str,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Chroma:
    """
    Creates persistent Chroma vector database.
    """
    emit_progress(progress_callback, "📦 Creating Chroma vector database...")

    reset_chroma_folder(chroma_db_folder)

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=chroma_db_folder,
        collection_name=COLLECTION_NAME,
    )

    emit_progress(progress_callback, "✅ Chroma vector database created.")

    return vector_store


# ============================================================
# PUBLIC FUNCTION CALLED BY STREAMLIT
# ============================================================

def run_ingestion(
    start_url: str,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Dict:
    """
    Main function called from Streamlit only after button click.
    """
    normalized_url = validate_start_url(start_url)
    chroma_db_folder = get_chroma_db_folder(normalized_url)

    documents, manifest = crawl_site(
        start_url=normalized_url,
        progress_callback=progress_callback,
    )

    chunks = split_documents(
        documents=documents,
        progress_callback=progress_callback,
    )

    embeddings = create_embedding_model(
        progress_callback=progress_callback,
    )

    create_vector_database(
        chunks=chunks,
        embeddings=embeddings,
        chroma_db_folder=chroma_db_folder,
        progress_callback=progress_callback,
    )

    manifest_path = save_manifest(
        manifest=manifest,
        chroma_db_folder=chroma_db_folder,
    )

    emit_progress(progress_callback, "🎉 Ingestion completed successfully.")

    return {
        "start_url": normalized_url,
        "documents": documents,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "chroma_db_folder": chroma_db_folder,
        "collection_name": COLLECTION_NAME,
        "page_count": len(documents),
        "chunk_count": len(chunks),
    }


# ============================================================
# OPTIONAL TERMINAL TEST
# ============================================================

if __name__ == "__main__":
    test_url = input("Enter website URL to crawl: ").strip()

    result = run_ingestion(
        start_url=test_url,
        progress_callback=print,
    )

    print("\n🎉 Ingestion completed.")
    print(f"URL: {result['start_url']}")
    print(f"Pages crawled: {result['page_count']}")
    print(f"Chunks created: {result['chunk_count']}")
    print(f"Chroma DB: {result['chroma_db_folder']}")
    print(f"Manifest: {result['manifest_path']}")