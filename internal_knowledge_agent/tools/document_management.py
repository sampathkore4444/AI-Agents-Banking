"""
Document Management Tool — MCP tool stub.

In production this would call the bank's document management system
(SharePoint, Documentum, OpenText, etc.) to search, retrieve, and manage
internal documents.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Simulated document store
_DOCUMENTS = {
    "DOC-001": {"id": "DOC-001", "title": "Personal Account Opening SOP", "category": "operations", "version": "3.2", "status": "current", "owner": "Operations Team", "last_updated": "2024-08-15"},
    "DOC-002": {"id": "DOC-002", "title": "AML Policy Manual", "category": "compliance", "version": "5.1", "status": "current", "owner": "Compliance Team", "last_updated": "2024-07-01"},
    "DOC-003": {"id": "DOC-003", "title": "IT Security Procedures", "category": "it", "version": "2.8", "status": "current", "owner": "IT Security", "last_updated": "2024-06-20"},
    "DOC-004": {"id": "DOC-004", "title": "Employee Benefits Guide", "category": "hr", "version": "4.0", "status": "current", "owner": "HR Department", "last_updated": "2024-01-15"},
    "DOC-005": {"id": "DOC-005", "title": "Fair Lending Guidelines", "category": "compliance", "version": "3.5", "status": "current", "owner": "Compliance Team", "last_updated": "2024-09-01"},
}


async def search_documents(
    query: str,
    category: str | None = None,
    max_results: int = 10,
) -> dict:
    """
    Search internal documents by keyword or phrase.

    Returns matching documents with metadata.
    """
    logger.info("Document search: query='%s', category=%s", query, category)

    results = []
    query_lower = query.lower()

    for doc in _DOCUMENTS.values():
        if category and doc["category"] != category:
            continue
        if query_lower in doc["title"].lower() or query_lower in doc["category"].lower():
            results.append(doc)

    return {
        "query": query,
        "results_count": len(results),
        "documents": results[:max_results],
        "searched_at": datetime.utcnow().isoformat(),
    }


async def get_document(document_id: str) -> dict:
    """Retrieve a document by its ID."""
    doc = _DOCUMENTS.get(document_id)
    if not doc:
        return {"error": f"Document {document_id} not found"}

    # Simulate full document content
    doc_content = {
        **doc,
        "content": f"[Full document content for {doc['title']} would be retrieved from the document management system here]",
        "file_url": f"https://docmanagement.internal/documents/{document_id}",
        "download_url": f"https://docmanagement.internal/documents/{document_id}/download",
    }

    return doc_content


async def get_document_by_version(
    document_id: str,
    version: str,
) -> dict:
    """Retrieve a specific version of a document."""
    doc = _DOCUMENTS.get(document_id)
    if not doc:
        return {"error": f"Document {document_id} not found"}

    return {
        **doc,
        "requested_version": version,
        "content": f"[Content for version {version} of {doc['title']}]",
    }


async def list_documents(
    category: str | None = None,
    status: str | None = None,
) -> dict:
    """List all documents with optional filters."""
    results = []
    for doc in _DOCUMENTS.values():
        if category and doc["category"] != category:
            continue
        if status and doc["status"] != status:
            continue
        results.append(doc)

    return {
        "total_count": len(results),
        "documents": results,
    }
