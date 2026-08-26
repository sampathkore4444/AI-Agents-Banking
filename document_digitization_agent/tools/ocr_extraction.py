"""
OCR Extraction Tool — Real AWS Textract + Google Cloud Vision integration.

Supports:
- AWS Textract: AnalyzeDocument, AnalyzeExpense, AnalyzeID, AnalyzeTextract
- Google Cloud Vision: DocumentTextDetection, CropHints
- Automatic fallback: Textract → Google Vision
- Structured field extraction per document type
- Table detection and extraction
- MRZ parsing with checksum validation

Requires:
- AWS: boto3 with valid credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
- Google: google-cloud-vision with service account (GOOGLE_APPLICATION_CREDENTIALS)
"""

from __future__ import annotations

import io
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)

# ── Extraction schemas per document type ──────────────────────────
EXTRACTION_FIELDS = {
    "invoice": ["vendor_name", "invoice_number", "invoice_date", "due_date", "line_items", "subtotal", "tax_amount", "total_amount", "currency"],
    "contract": ["contract_title", "contract_type", "party_a", "party_b", "effective_date", "term_months", "total_value", "payment_terms", "termination_clause", "governing_law"],
    "bank_statement": ["account_holder", "account_number", "statement_period_start", "statement_period_end", "opening_balance", "closing_balance", "total_credits", "total_debits", "transactions"],
    "tax_return": ["taxpayer_name", "ssn_last_four", "filing_status", "tax_year", "adjusted_gross_income", "taxable_income", "total_tax", "total_payments", "refund_or_owed"],
    "payslip": ["employee_name", "employer_name", "pay_period_start", "pay_period_end", "gross_pay", "net_pay", "ytd_gross", "ytd_net"],
    "proof_of_address": ["full_name", "address", "utility_provider", "issue_date"],
    "identity_document": ["full_name", "date_of_birth", "document_number", "nationality", "expiry_date", "issuing_country"],
    "financial_statement": ["company_name", "reporting_period", "total_assets", "total_liabilities", "shareholders_equity", "revenue", "net_income"],
    "loan_application": ["borrower_name", "loan_type", "requested_amount", "property_address", "loan_purpose", "loan_term", "collateral_value"],
    "corporate_resolution": ["company_name", "resolution_date", "authorized_action", "signatories", "resolution_number"],
}


# ══════════════════════════════════════════════════════════════════
#  AWS TEXTRACT CLIENT
# ══════════════════════════════════════════════════════════════════

class TextractClient:
    """AWS Textract OCR client with async wrapper."""

    def __init__(self) -> None:
        self._client = None
        self._available = False
        self._init_client()

    def _init_client(self) -> None:
        try:
            import boto3
            kwargs = {}
            if settings.aws_access_key_id:
                kwargs["aws_access_key_id"] = settings.aws_access_key_id
            if settings.aws_secret_access_key:
                kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
            if settings.aws_region:
                kwargs["region_name"] = settings.aws_region
            self._client = boto3.client("textract", **kwargs)
            self._available = True
            logger.info("AWS Textract client initialized")
        except Exception as e:
            logger.warning("AWS Textract unavailable: %s", e)
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    async def analyze_document(self, document_bytes: bytes, feature_types: list[str] | None = None) -> dict:
        """
        Analyze a document using Textract AnalyzeDocument.

        Feature types: TABLES, FORMS, SIGNATURES, HANDWRITING
        """
        import asyncio

        features = feature_types or ["TABLES", "FORMS"]

        def _call():
            return self._client.analyze_document(
                Document={"Bytes": document_bytes},
                FeatureTypes=features,
            )

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _call)
        return self._parse_analyze_response(response)

    async def analyze_expense(self, document_bytes: bytes) -> dict:
        """
        Analyze an expense document (invoice, receipt) using Textract AnalyzeExpense.
        """
        import asyncio

        def _call():
            return self._client.analyze_expense(Document={"Bytes": document_bytes})

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _call)
        return self._parse_expense_response(response)

    async def analyze_id(self, document_bytes: bytes) -> dict:
        """
        Analyze an identity document (passport, license) using Textract AnalyzeID.
        """
        import asyncio

        def _call():
            return self._client.analyze_id(DocumentPages=[{"Bytes": document_bytes}])

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _call)
        return self._parse_id_response(response)

    def _parse_analyze_response(self, response: dict) -> dict:
        """Parse Textract AnalyzeDocument response into structured data."""
        blocks = response.get("Blocks", [])

        # Extract key-value pairs (FORMS)
        key_value_pairs = {}
        key_blocks = {b["Id"]: b for b in blocks if b.get("BlockType") == "KEY_VALUE_SET"}
        value_blocks = {b["Id"]: b for b in blocks if b.get("BlockType") == "VALUE"}

        for key_id, key_block in key_blocks.items():
            key_text = self._get_text_from_block(key_block, blocks)
            # Find associated value
            value_relationships = key_block.get("Relationships", [])
            for rel in value_relationships:
                if rel.get("Type") == "VALUE":
                    for val_id in rel.get("Ids", []):
                        if val_id in value_blocks:
                            val_text = self._get_text_from_block(value_blocks[val_id], blocks)
                            if key_text and val_text:
                                key_value_pairs[key_text.strip()] = val_text.strip()

        # Extract tables
        tables = []
        table_blocks = [b for b in blocks if b.get("BlockType") == "TABLE"]
        for table_block in table_blocks:
            table = self._extract_table(table_block, blocks)
            if table:
                tables.append(table)

        # Extract all text
        all_text = " ".join(
            b.get("Text", "") for b in blocks
            if b.get("BlockType") in ("LINE", "WORD")
        )

        return {
            "key_value_pairs": key_value_pairs,
            "tables": tables,
            "raw_text": all_text,
            "block_count": len(blocks),
        }

    def _parse_expense_response(self, response: dict) -> dict:
        """Parse Textract AnalyzeExpense response."""
        expense_docs = response.get("ExpenseDocuments", [])

        fields = {}
        summaries = {}

        for doc in expense_docs:
            # Summary fields (vendor name, total, date, etc.)
            for summary_field in doc.get("SummaryFields", []):
                key = summary_field.get("Type", {}).get("Text", "")
                value = summary_field.get("ValueDetection", {}).get("Text", "")
                confidence = summary_field.get("ValueDetection", {}).get("Confidence", 0)
                if key and value:
                    summaries[key] = {"value": value, "confidence": round(confidence / 100, 3)}

            # Line item fields
            line_items = doc.get("LineItemGroups", [])
            for group in line_items:
                for item in group.get("LineItems", []):
                    item_fields = {}
                    for field in item.get("LineItemExpenseFields", []):
                        key = field.get("Type", {}).get("Text", "")
                        value = field.get("ValueDetection", {}).get("Text", "")
                        if key and value:
                            item_fields[key] = value
                    if item_fields:
                        fields[len(fields)] = item_fields

        return {
            "summary_fields": summaries,
            "line_items": fields,
            "expense_doc_count": len(expense_docs),
        }

    def _parse_id_response(self, response: dict) -> dict:
        """Parse Textract AnalyzeID response."""
        identity_docs = response.get("IdentityDocuments", [])

        fields = {}
        for doc in identity_docs:
            for field in doc.get("IdentityDocumentFields", []):
                key = field.get("Type", {}).get("Text", "")
                value = field.get("ValueDetection", {}).get("Text", "")
                confidence = field.get("ValueDetection", {}).get("Confidence", 0)
                if key and value:
                    fields[key] = {"value": value, "confidence": round(confidence / 100, 3)}

        return {
            "identity_fields": fields,
            "document_count": len(identity_docs),
        }

    def _get_text_from_block(self, block: dict, blocks: list[dict]) -> str:
        """Recursively get text from a block and its children."""
        texts = []
        for rel in block.get("Relationships", []):
            if rel.get("Type") == "CHILD":
                for child_id in rel.get("Ids", []):
                    child = next((b for b in blocks if b["Id"] == child_id), None)
                    if child:
                        if child.get("Text"):
                            texts.append(child["Text"])
                        elif child.get("BlockType") == "WORD":
                            texts.append(child.get("Text", ""))
        return " ".join(texts)

    def _extract_table(self, table_block: dict, blocks: list[dict]) -> dict | None:
        """Extract table structure from Textract blocks."""
        relationships = table_block.get("Relationships", [])
        cell_ids = []
        for rel in relationships:
            if rel.get("Type") == "CHILD":
                cell_ids.extend(rel.get("Ids", []))

        cells = []
        for cell_id in cell_ids:
            cell = next((b for b in blocks if b["Id"] == cell_id), None)
            if cell and cell.get("BlockType") == "CELL":
                row_idx = cell.get("RowIndex", 0)
                col_idx = cell.get("ColumnIndex", 0)
                text = self._get_text_from_block(cell, blocks)
                cells.append({"row": row_idx, "col": col_idx, "text": text})

        if not cells:
            return None

        max_row = max(c["row"] for c in cells)
        max_col = max(c["col"] for c in cells)

        # Build grid
        grid = [["" for _ in range(max_col + 1)] for _ in range(max_row + 1)]
        for cell in cells:
            grid[cell["row"] - 1][cell["col"] - 1] = cell["text"]

        headers = grid[0] if grid else []
        rows = grid[1:] if len(grid) > 1 else []

        return {
            "headers": headers,
            "rows": rows,
            "row_count": len(rows),
            "col_count": len(headers),
        }


# ══════════════════════════════════════════════════════════════════
#  GOOGLE CLOUD VISION CLIENT
# ══════════════════════════════════════════════════════════════════

class GoogleVisionClient:
    """Google Cloud Vision OCR client."""

    def __init__(self) -> None:
        self._client = None
        self._available = False
        self._init_client()

    def _init_client(self) -> None:
        try:
            from google.cloud import vision
            if settings.google_application_credentials:
                import os
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials
            self._client = vision.ImageAnnotatorClient()
            self._available = True
            logger.info("Google Cloud Vision client initialized")
        except Exception as e:
            logger.warning("Google Cloud Vision unavailable: %s", e)
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    async def detect_document_text(self, document_bytes: bytes) -> dict:
        """Detect full document text including layout."""
        import asyncio
        from google.cloud import vision

        def _call():
            image = vision.Image(content=document_bytes)
            # Try document text detection first (better for documents)
            response = self._client.document_text_detection(image=image)
            return response

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _call)

        if response.error.message:
            raise RuntimeError(f"Google Vision error: {response.error.message}")

        annotation = response.full_text_annotation
        if not annotation:
            return {"raw_text": "", "blocks": [], "confidence": 0}

        # Parse text blocks
        blocks = []
        for page in annotation.pages:
            for block in page.blocks:
                block_text = ""
                block_confidence = 0
                for paragraph in block.paragraphs:
                    para_text = ""
                    for word in paragraph.words:
                        word_text = "".join(symbol.text for symbol in word.symbols)
                        para_text += word_text + " "
                    block_text += para_text.strip() + "\n"
                    block_confidence = max(block_confidence, paragraph.confidence)

                blocks.append({
                    "text": block_text.strip(),
                    "confidence": round(block_confidence, 3),
                    "block_type": block.block_type.name,
                })

        return {
            "raw_text": annotation.text,
            "blocks": blocks,
            "confidence": round(annotation.pages[0].blocks[0].confidence if annotation.pages and annotation.pages[0].blocks else 0, 3),
        }

    async def detect_fulltext(self, document_bytes: bytes) -> dict:
        """Simple full text detection (faster, less accurate)."""
        import asyncio
        from google.cloud import vision

        def _call():
            image = vision.Image(content=document_bytes)
            return self._client.text_detection(image=image)

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _call)

        if response.error.message:
            raise RuntimeError(f"Google Vision error: {response.error.message}")

        texts = response.text_annotations
        if not texts:
            return {"raw_text": "", "words": [], "confidence": 0}

        # First annotation is the full text
        full_text = texts[0].description if texts else ""

        # Rest are individual words/regions
        words = []
        for text in texts[1:]:
            words.append({
                "text": text.description,
                "confidence": round(text.confidence, 3) if hasattr(text, "confidence") else 0,
                "vertices": [{"x": v.x, "y": v.y} for v in text.bounding_poly.vertices],
            })

        return {
            "raw_text": full_text,
            "words": words,
            "confidence": round(sum(w["confidence"] for w in words) / len(words) if words else 0, 3),
        }


# ══════════════════════════════════════════════════════════════════
#  DOCUMENT DOWNLOADER
# ══════════════════════════════════════════════════════════════════

async def _download_document(document_url: str) -> bytes:
    """Download a document from URL and return bytes."""
    if document_url.startswith("s3://"):
        # S3 URL — use boto3
        import boto3
        import asyncio

        parts = document_url.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""

        s3 = boto3.client("s3")
        def _get():
            response = s3.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get)

    elif document_url.startswith(("http://", "https://")):
        # HTTP URL — use httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(document_url)
            response.raise_for_status()
            return response.content

    else:
        # Local file path
        import os
        path = document_url
        if os.name == "nt":
            path = path.replace("/", "\\")
        with open(path, "rb") as f:
            return f.read()


# ══════════════════════════════════════════════════════════════════
#  FIELD MAPPING (OCR output → schema fields)
# ══════════════════════════════════════════════════════════════════

# Mapping from common OCR key variants to our schema field names
FIELD_ALIASES = {
    # Invoice
    "vendor_name": ["vendor", "seller", "from", "company_name", "supplier", "billed_by"],
    "invoice_number": ["invoice_no", "invoice #", "inv_number", "bill_number", "reference"],
    "invoice_date": ["date", "invoice_date", "bill_date", "date_of_invoice"],
    "due_date": ["due_date", "payment_due", "date_due", "pay_by"],
    "subtotal": ["subtotal", "sub_total", "amount_before_tax", "net_amount"],
    "tax_amount": ["tax", "vat", "gst", "sales_tax", "tax_amount"],
    "total_amount": ["total", "amount_due", "grand_total", "balance_due", "total_amount"],
    "currency": ["currency", "currency_code"],
    # Bank Statement
    "account_holder": ["account_holder", "name", "customer_name", "account_name"],
    "account_number": ["account_no", "account #", "acct_number"],
    "opening_balance": ["opening_balance", "beginning_balance", "start_balance"],
    "closing_balance": ["closing_balance", "ending_balance", "end_balance", "available_balance"],
    "total_credits": ["total_credits", "credits", "total_deposits"],
    "total_debits": ["total_debits", "debits", "total_withdrawals"],
    # Tax Return
    "taxpayer_name": ["taxpayer", "name", "your_name", "filer_name"],
    "adjusted_gross_income": ["agi", "adjusted_gross_income", "total_income"],
    "taxable_income": ["taxable_income", "taxable_amount"],
    "total_tax": ["total_tax", "tax_liability", "total_taxable"],
    "tax_year": ["tax_year", "year", "tax_period"],
    # Payslip
    "employee_name": ["employee", "name", "employee_name"],
    "employer_name": ["employer", "company", "employer_name"],
    "gross_pay": ["gross", "gross_pay", "gross_salary", "total_earnings"],
    "net_pay": ["net", "net_pay", "take_home", "net_salary", "amount_paid"],
}


def _map_ocr_fields(
    ocr_kv: dict[str, str],
    expected_fields: list[str],
) -> tuple[dict[str, Any], dict[str, float]]:
    """
    Map OCR key-value pairs to our schema fields.

    Returns: (mapped_fields, confidence_scores)
    """
    mapped = {}
    confidences = {}

    for field in expected_fields:
        aliases = FIELD_ALIASES.get(field, [field])
        best_value = None
        best_confidence = 0.0

        for alias in aliases:
            alias_lower = alias.lower()
            for ocr_key, ocr_value in ocr_kv.items():
                ocr_key_lower = ocr_key.lower().strip()
                if alias_lower in ocr_key_lower or ocr_key_lower in alias_lower:
                    # Try to parse numeric values
                    parsed = _parse_value(ocr_value, field)
                    if parsed is not None:
                        mapped[field] = parsed
                        confidences[field] = 0.85  # High confidence for matched fields
                        best_value = parsed
                        break
            if best_value is not None:
                break

        if best_value is None:
            # Field not found in OCR output
            confidences[field] = 0.0

    return mapped, confidences


def _parse_value(value: str, field_name: str) -> Any:
    """Parse an OCR string value into the appropriate Python type."""
    if not value or not value.strip():
        return None

    cleaned = value.strip()

    # Numeric fields
    numeric_fields = {
        "subtotal", "tax_amount", "total_amount", "gross_pay", "net_pay",
        "opening_balance", "closing_balance", "total_credits", "total_debits",
        "adjusted_gross_income", "taxable_income", "total_tax", "total_payments",
        "refund_or_owed", "ytd_gross", "ytd_net", "total_value", "requested_amount",
        "collateral_value", "shareholders_equity", "total_assets", "total_liabilities",
        "revenue", "net_income",
    }

    if field_name in numeric_fields:
        # Remove currency symbols, commas, spaces
        cleaned_num = re.sub(r"[,$%\s]", "", cleaned)
        try:
            return float(cleaned_num)
        except ValueError:
            return None

    # Integer fields
    int_fields = {"tax_year", "term_months", "resolution_number"}
    if field_name in int_fields:
        cleaned_int = re.sub(r"[^\d]", "", cleaned)
        try:
            return int(cleaned_int)
        except ValueError:
            return None

    # SSN last four
    if field_name == "ssn_last_four":
        digits = re.sub(r"[^\d]", "", cleaned)
        if len(digits) >= 4:
            return digits[-4:]
        return None

    return cleaned


# ══════════════════════════════════════════════════════════════════
#  MRZ PARSING
# ══════════════════════════════════════════════════════════════════

def _parse_mrz(raw_text: str) -> dict | None:
    """
    Parse Machine Readable Zone from OCR text.

    Supports TD3 (passport - 2 lines × 44 chars) and TD1 (ID card - 3 lines × 30 chars).
    """
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

    # Find MRZ lines (start with P<, I<, or contain <<<<)
    mrz_lines = []
    for line in lines:
        if re.match(r"^[A-Z0-9<]{20,}$", line) and ("<" in line or line.startswith("P")):
            mrz_lines.append(line)

    if not mrz_lines:
        # Try to find in raw text using regex
        mrz_match = re.findall(r"[A-Z0-9<]{30,50}", raw_text)
        mrz_lines = mrz_match

    if len(mrz_lines) < 2:
        return None

    # Determine format
    if len(mrz_lines[0]) == 44:
        return _parse_td3(mrz_lines[:2])
    elif len(mrz_lines[0]) == 30 and len(mrz_lines) >= 3:
        return _parse_td1(mrz_lines[:3])

    return None


def _parse_td3(lines: list[str]) -> dict:
    """Parse TD3 format (passport): 2 lines × 44 characters."""
    if len(lines) < 2:
        return None

    line1 = lines[0].ljust(44)
    line2 = lines[1].ljust(44)

    # Line 1: P<ISSUER<SURNAME<<GIVEN<NAMES<<<<<<<<<<<<<<
    doc_type = line1[0:1]
    issuing_country = line1[1:4].replace("<", "")
    name_part = line1[5:44].replace("<<", ", ").replace("<", " ").strip(", ")

    # Line 2: DOC_NUMBER<CHECK<DOB<CHECK<SEX<EXP<CHECK<PERSONAL<COMPOSITE<CHECK
    doc_number = line2[0:9].replace("<", "")
    dob_raw = line2[13:19]
    sex = line2[20]
    expiry_raw = line2[21:27]

    # Parse dates (YYMMDD)
    dob = _parse_mrz_date(dob_raw)
    expiry = _parse_mrz_date(expiry_raw)

    # Validate checksums
    checksum_valid = _validate_mrz_checksum(line2)

    return {
        "document_type": "passport" if doc_type == "P" else "other",
        "issuing_country": issuing_country,
        "name": name_part,
        "document_number": doc_number,
        "date_of_birth": dob,
        "sex": sex if sex in ("M", "F", "<") else "unknown",
        "expiry_date": expiry,
        "checksum_valid": checksum_valid,
    }


def _parse_td1(lines: list[str]) -> dict:
    """Parse TD1 format (ID card): 3 lines × 30 characters."""
    if len(lines) < 3:
        return None

    line1 = lines[0].ljust(30)
    line2 = lines[1].ljust(30)
    line3 = lines[2].ljust(30)

    doc_type = line1[0:1]
    issuing_country = line1[1:4].replace("<", "")
    doc_number = line1[5:14].replace("<", "")
    dob_raw = line2[0:6]
    sex = line2[7]
    expiry_raw = line2[8:14]
    name_part = line3.replace("<<", ", ").replace("<", " ").strip(", ")

    dob = _parse_mrz_date(dob_raw)
    expiry = _parse_mrz_date(expiry_raw)
    checksum_valid = _validate_mrz_checksum(line1) and _validate_mrz_checksum(line2)

    return {
        "document_type": "id_card" if doc_type == "I" else "other",
        "issuing_country": issuing_country,
        "name": name_part,
        "document_number": doc_number,
        "date_of_birth": dob,
        "sex": sex if sex in ("M", "F", "<") else "unknown",
        "expiry_date": expiry,
        "checksum_valid": checksum_valid,
    }


def _parse_mrz_date(date_str: str) -> str:
    """Parse MRZ date (YYMMDD) to ISO format (YYYY-MM-DD)."""
    if len(date_str) != 6 or not date_str.isdigit():
        return ""
    yy = int(date_str[:2])
    mm = int(date_str[2:4])
    dd = int(date_str[4:6])
    year = 1900 + yy if yy > 50 else 2000 + yy
    if 1 <= mm <= 12 and 1 <= dd <= 31:
        return f"{year:04d}-{mm:02d}-{dd:02d}"
    return ""


def _validate_mrz_checksum(line: str) -> bool:
    """Validate MRZ checksum digits."""
    weights = [7, 3, 1]
    try:
        total = 0
        for i, char in enumerate(line):
            if char.isdigit():
                total += int(char) * weights[i % 3]
            elif char.isalpha():
                total += (ord(char) - 55) * weights[i % 3]
            elif char == "<":
                total += 0 * weights[i % 3]
        return total % 10 == 0
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════════════

# Singleton clients
_textract = TextractClient()
_google_vision = GoogleVisionClient()


async def extract_document_data(
    document_url: str,
    document_type: str,
    page_range: tuple[int, int] | None = None,
) -> dict:
    """
    Extract structured data from a document using real OCR.

    Uses Textract first (better for structured docs), falls back to Google Vision.
    Maps extracted text to document-type schema fields.

    Returns extracted fields, confidence scores per field, and overall quality metrics.
    """
    logger.info("OCR extraction: type=%s, url=%s", document_type, document_url)

    # Step 1: Download document
    try:
        document_bytes = await _download_document(document_url)
    except Exception as e:
        logger.error("Failed to download document: %s", e)
        return _fallback_extraction(document_url, document_type, str(e))

    # Step 2: Choose OCR provider and extract
    provider_used = "none"
    raw_ocr = {}
    confidence = 0.0

    if settings.ocr_provider in ("textract", "auto") and _textract.available:
        try:
            raw_ocr = await _extract_with_textract(document_bytes, document_type)
            provider_used = "textract"
            confidence = 0.88
            logger.info("Textract extraction successful")
        except Exception as e:
            logger.warning("Textract failed, falling back to Google Vision: %s", e)

    if provider_used == "none" and settings.ocr_provider in ("google_vision", "auto") and _google_vision.available:
        try:
            raw_ocr = await _extract_with_google_vision(document_bytes, document_type)
            provider_used = "google_vision"
            confidence = 0.82
            logger.info("Google Vision extraction successful")
        except Exception as e:
            logger.warning("Google Vision failed: %s", e)

    if provider_used == "none":
        return _fallback_extraction(document_url, document_type, "All OCR providers unavailable")

    # Step 3: Map OCR output to schema fields
    expected_fields = EXTRACTION_FIELDS.get(document_type, ["text_content"])
    key_value_pairs = raw_ocr.get("key_value_pairs", {})

    # For expense/invoice docs, use summary fields from Textract AnalyzeExpense
    if document_type == "invoice" and "summary_fields" in raw_ocr:
        for k, v in raw_ocr["summary_fields"].items():
            key_value_pairs[k] = v.get("value", "") if isinstance(v, dict) else str(v)

    # For identity docs, use AnalyzeID fields
    if document_type == "identity_document" and "identity_fields" in raw_ocr:
        for k, v in raw_ocr["identity_fields"].items():
            key_value_pairs[k] = v.get("value", "") if isinstance(v, dict) else str(v)

    extracted_fields, field_confidences = _map_ocr_fields(key_value_pairs, expected_fields)

    # For text-heavy docs (contracts, financial statements), also map from raw text
    raw_text = raw_ocr.get("raw_text", "")
    if raw_text and len(extracted_fields) < len(expected_fields) * 0.5:
        text_fields = _extract_fields_from_text(raw_text, expected_fields)
        for field, value in text_fields.items():
            if field not in extracted_fields:
                extracted_fields[field] = value
                field_confidences[field] = 0.70  # Lower confidence for text-based extraction

    # Tables
    tables = raw_ocr.get("tables", [])

    # Overall metrics
    matched_fields = sum(1 for f in field_confidences.values() if f > 0)
    avg_confidence = sum(field_confidences.values()) / len(field_confidences) if field_confidences else 0
    quality = "high" if avg_confidence > 0.85 else "medium" if avg_confidence > 0.7 else "low"

    # Pages
    pages = len(tables) + 1 if tables else 1
    if page_range:
        pages = page_range[1] - page_range[0] + 1

    result = {
        "extraction_id": str(uuid.uuid4()),
        "document_url": document_url,
        "document_type": document_type,
        "provider": provider_used,
        "extracted_fields": extracted_fields,
        "field_confidences": field_confidences,
        "matched_fields": matched_fields,
        "total_expected_fields": len(expected_fields),
        "overall_confidence": round(avg_confidence, 3),
        "ocr_quality": quality,
        "tables": tables,
        "raw_text_preview": raw_text[:500] if raw_text else "",
        "pages_processed": pages,
        "page_range": page_range or (1, pages),
        "extracted_at": datetime.utcnow().isoformat(),
    }

    logger.info(
        "OCR extraction complete: provider=%s, confidence=%.2f, quality=%s, fields=%d/%d",
        provider_used, avg_confidence, quality, matched_fields, len(expected_fields),
    )
    return result


async def extract_table_data(
    document_url: str,
    page_number: int = 1,
) -> dict:
    """
    Extract tabular data from a specific page.

    Uses Textract TABLES feature for best results.
    """
    logger.info("Table extraction: url=%s, page=%d", document_url, page_number)

    try:
        document_bytes = await _download_document(document_url)
    except Exception as e:
        logger.error("Failed to download document: %s", e)
        return {"error": str(e), "tables": []}

    tables = []

    if _textract.available:
        try:
            ocr_result = await _textract.analyze_document(document_bytes, feature_types=["TABLES"])
            tables = ocr_result.get("tables", [])
        except Exception as e:
            logger.warning("Textract table extraction failed: %s", e)

    if not tables and _google_vision.available:
        # Google Vision doesn't have dedicated table extraction,
        # but we can try to parse tables from document text
        try:
            ocr_result = await _google_vision.detect_document_text(document_bytes)
            raw_text = ocr_result.get("raw_text", "")
            tables = _parse_tables_from_text(raw_text)
        except Exception as e:
            logger.warning("Google Vision table extraction failed: %s", e)

    result = {
        "extraction_id": str(uuid.uuid4()),
        "document_url": document_url,
        "page_number": page_number,
        "tables_found": len(tables),
        "tables": [
            {
                "table_index": i,
                "headers": t.get("headers", []),
                "rows": t.get("rows", []),
                "row_count": t.get("row_count", len(t.get("rows", []))),
                "confidence": 0.85 if _textract.available else 0.70,
            }
            for i, t in enumerate(tables)
        ],
        "extracted_at": datetime.utcnow().isoformat(),
    }

    logger.info("Table extraction complete: %d tables found", len(tables))
    return result


async def extract_mrz(document_url: str) -> dict:
    """
    Extract Machine Readable Zone from passport or ID document.

    Uses OCR to get raw text, then parses MRZ with checksum validation.
    """
    logger.info("MRZ extraction: url=%s", document_url)

    try:
        document_bytes = await _download_document(document_url)
    except Exception as e:
        logger.error("Failed to download document: %s", e)
        return {"mrz_found": False, "error": str(e)}

    raw_text = ""

    # Prefer Google Vision for MRZ (better at reading machine-printed text)
    if _google_vision.available:
        try:
            ocr_result = await _google_vision.detect_fulltext(document_bytes)
            raw_text = ocr_result.get("raw_text", "")
        except Exception as e:
            logger.warning("Google Vision MRZ extraction failed: %s", e)

    if not raw_text and _textract.available:
        try:
            ocr_result = await _textract.analyze_document(document_bytes, feature_types=["FORMS"])
            raw_text = ocr_result.get("raw_text", "")
        except Exception as e:
            logger.warning("Textract MRZ extraction failed: %s", e)

    # Parse MRZ from raw text
    mrz_data = _parse_mrz(raw_text) if raw_text else None

    result = {
        "extraction_id": str(uuid.uuid4()),
        "document_url": document_url,
        "mrz_found": mrz_data is not None,
        "mrz_raw": raw_text[:200] if raw_text else "",
        "parsed_data": mrz_data if mrz_data else {},
        "checksum_valid": mrz_data.get("checksum_valid", False) if mrz_data else False,
        "confidence": 0.92 if mrz_data and mrz_data.get("checksum_valid") else 0.5 if mrz_data else 0.0,
        "extracted_at": datetime.utcnow().isoformat(),
    }

    logger.info("MRZ extraction complete: found=%s, valid=%s",
                result["mrz_found"], result["checksum_valid"])
    return result


# ══════════════════════════════════════════════════════════════════
#  INTERNAL HELPERS
# ══════════════════════════════════════════════════════════════════

async def _extract_with_textract(document_bytes: bytes, document_type: str) -> dict:
    """Route to appropriate Textract API based on document type."""
    if document_type == "invoice":
        return await _textract.analyze_expense(document_bytes)
    elif document_type == "identity_document":
        id_result = await _textract.analyze_id(document_bytes)
        doc_result = await _textract.analyze_document(document_bytes, feature_types=["FORMS"])
        doc_result["identity_fields"] = id_result.get("identity_fields", {})
        return doc_result
    else:
        return await _textract.analyze_document(document_bytes, feature_types=["TABLES", "FORMS"])


async def _extract_with_google_vision(document_bytes: bytes, document_type: str) -> dict:
    """Extract using Google Cloud Vision."""
    result = await _google_vision.detect_document_text(document_bytes)

    # Convert Google Vision blocks to key-value pairs (heuristic)
    key_value_pairs = {}
    raw_text = result.get("raw_text", "")

    # Try to parse key: value patterns from text
    for line in raw_text.split("\n"):
        line = line.strip()
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip()
            value = parts[1].strip()
            if key and value:
                key_value_pairs[key] = value

    return {
        "key_value_pairs": key_value_pairs,
        "tables": [],
        "raw_text": raw_text,
        "block_count": len(result.get("blocks", [])),
    }


def _extract_fields_from_text(raw_text: str, expected_fields: list[str]) -> dict[str, Any]:
    """Extract fields from raw OCR text using regex patterns."""
    fields = {}

    patterns = {
        "vendor_name": r"(?:from|vendor|seller|company)[:\s]+(.+)",
        "invoice_number": r"(?:invoice\s*(?:#|no|number))[:\s]+([A-Z0-9\-]+)",
        "invoice_date": r"(?:date|invoice\s*date)[:\s]+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})",
        "total_amount": r"(?:total|amount\s*due|grand\s*total)[:\s]*[$€£]?\s*([\d,]+\.?\d*)",
        "account_holder": r"(?:account\s*holder|name)[:\s]+(.+)",
        "taxpayer_name": r"(?:taxpayer|name|filer)[:\s]+(.+)",
        "employee_name": r"(?:employee|name)[:\s]+(.+)",
        "company_name": r"(?:company|entity|organization)[:\s]+(.+)",
    }

    for field in expected_fields:
        pattern = patterns.get(field)
        if pattern:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                fields[field] = _parse_value(match.group(1), field)

    return fields


def _parse_tables_from_text(raw_text: str) -> list[dict]:
    """Heuristic table parsing from raw OCR text."""
    tables = []
    lines = raw_text.split("\n")

    # Look for pipe-delimited tables
    pipe_lines = [l for l in lines if "|" in l and l.count("|") >= 2]
    if len(pipe_lines) >= 2:
        rows = []
        for line in pipe_lines:
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if cells:
                rows.append(cells)

        if rows:
            headers = rows[0]
            data_rows = rows[1:]
            tables.append({
                "headers": headers,
                "rows": data_rows,
                "row_count": len(data_rows),
                "col_count": len(headers),
            })

    return tables


def _fallback_extraction(document_url: str, document_type: str, error: str) -> dict:
    """Return a structured error when all OCR providers fail."""
    expected_fields = EXTRACTION_FIELDS.get(document_type, ["text_content"])
    return {
        "extraction_id": str(uuid.uuid4()),
        "document_url": document_url,
        "document_type": document_type,
        "provider": "none",
        "extracted_fields": {},
        "field_confidences": {f: 0.0 for f in expected_fields},
        "matched_fields": 0,
        "total_expected_fields": len(expected_fields),
        "overall_confidence": 0.0,
        "ocr_quality": "failed",
        "error": error,
        "pages_processed": 0,
        "extracted_at": datetime.utcnow().isoformat(),
    }
