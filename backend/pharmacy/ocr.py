import os
import io
import tempfile
import logging
from typing import List, Dict, Optional


def _decode_bytes(content: bytes) -> str:
    try:
        return content.decode('utf-8', errors='ignore')
    except Exception:
        try:
            return content.decode('latin-1', errors='ignore')
        except Exception:
            return ''


class OCRService:
    """
    Minimal OCR facade with pluggable providers.

    Supported modes (configured via environment):
    - CSV/TXT passthrough: if file is .csv or .txt, treat content as text.
    - AWS Textract: set USE_AWS_TEXTRACT=1 and provide AWS credentials in env.
    - Gemini: set USE_GEMINI=1 and GEMINI_API_KEY in env (implemented via google-generativeai if installed).
    - OpenRouter (vision-capable): set USE_OPENROUTER=1 and OPENROUTER_API_KEY (stubbed).

    Returns extracted text or None if unsupported/unconfigured.
    """

    @staticmethod
    def extract_text(content: bytes, filename: str) -> Optional[str]:
        # Quick path: CSV/TXT passthrough
        lower = (filename or '').lower()
        if lower.endswith('.csv') or lower.endswith('.txt'):
            return _decode_bytes(content)

        # Try AWS Textract if enabled
        if os.getenv('USE_AWS_TEXTRACT') == '1':
            try:
                import boto3  # type: ignore
                client = boto3.client('textract')
                resp = client.detect_document_text(Document={'Bytes': content})
                lines = []
                for block in resp.get('Blocks', []):
                    if block.get('BlockType') == 'LINE':
                        txt = block.get('Text')
                        if txt:
                            lines.append(txt)
                return '\n'.join(lines) if lines else None
            except Exception:
                # Fall through to other providers
                pass

        # Try Gemini via google-generativeai, if enabled and SDK available
        if os.getenv('USE_GEMINI') == '1' and os.getenv('GEMINI_API_KEY'):
            try:
                import google.generativeai as genai  # type: ignore
                api_key = os.getenv('GEMINI_API_KEY')
                genai.configure(api_key=api_key)

                # Choose a fast, vision-capable model
                model_name = os.getenv('GEMINI_VISION_MODEL', 'gemini-1.5-flash')
                model = genai.GenerativeModel(model_name)

                # Infer mime type from filename
                lower = (filename or '').lower()
                mime = 'application/octet-stream'
                if lower.endswith('.png'):
                    mime = 'image/png'
                elif lower.endswith('.jpg') or lower.endswith('.jpeg'):
                    mime = 'image/jpeg'
                elif lower.endswith('.webp'):
                    mime = 'image/webp'
                elif lower.endswith('.pdf'):
                    mime = 'application/pdf'

                # For PDFs, use upload_file for better extraction stability
                if mime == 'application/pdf':
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                        tmp.write(content)
                        tmp_path = tmp.name
                    try:
                        file = genai.upload_file(tmp_path)
                        resp = model.generate_content([file, "Extract the raw text of this document. Return plain text only, one line per item if possible."])
                    finally:
                        try:
                            os.unlink(tmp_path)
                        except Exception:
                            pass
                else:
                    parts = [
                        {"mime_type": mime, "data": content},
                        "Extract the raw text of this document. Return plain text only, one line per item if possible."
                    ]
                    resp = model.generate_content(parts)

                # Prefer convenience property, fall back to candidates
                txt = getattr(resp, 'text', None)
                if not txt:
                    try:
                        for cand in getattr(resp, 'candidates', []) or []:
                            for part in getattr(getattr(cand, 'content', None), 'parts', []) or []:
                                maybe = getattr(part, 'text', None)
                                if maybe:
                                    txt = maybe
                                    break
                            if txt:
                                break
                    except Exception:
                        txt = None
                # Fallback: try a stronger model if configured default yields no text
                if not txt and model_name.startswith('gemini-1.5-flash'):
                    try:
                        pro_model = genai.GenerativeModel('gemini-1.5-pro')
                        if mime == 'application/pdf':
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                                tmp.write(content)
                                tmp_path = tmp.name
                            try:
                                file = genai.upload_file(tmp_path)
                                resp2 = pro_model.generate_content([file, "Extract the raw text of this document. Return plain text only."])
                            finally:
                                try:
                                    os.unlink(tmp_path)
                                except Exception:
                                    pass
                        else:
                            parts2 = [
                                {"mime_type": mime, "data": content},
                                "Extract the raw text of this document. Return plain text only."
                            ]
                            resp2 = pro_model.generate_content(parts2)
                        txt = getattr(resp2, 'text', None) or txt
                        if not txt:
                            try:
                                for cand in getattr(resp2, 'candidates', []) or []:
                                    for part in getattr(getattr(cand, 'content', None), 'parts', []) or []:
                                        maybe = getattr(part, 'text', None)
                                        if maybe:
                                            txt = maybe
                                            break
                                    if txt:
                                        break
                            except Exception:
                                pass
                    except Exception:
                        pass
                if txt:
                    return txt
            except Exception:
                # Fall through to other providers if Gemini not available or fails
                pass

        # Try OpenRouter (stubbed for vision unless configured client is added)
        if os.getenv('USE_OPENROUTER') == '1' and os.getenv('OPENROUTER_API_KEY'):
            # Vision OCR via OpenRouter would require a model like gpt-4o or similar.
            # Without a client library, we return None.
            return None

        # Unsupported/unconfigured
        return None


def naive_line_parser(text: str) -> List[Dict]:
    """
    Parse invoice-like lines into structured items.

    Expected columns (comma or tab separated):
    name, quantity, buying_price, batch_number, expiry_date(YYYY-MM-DD)

    Returns list of dicts: { name, quantity, buying_price, batch_number, expiry_date }
    Missing or malformed values are coerced to sensible defaults.
    """
    items: List[Dict] = []
    if not text:
        return items

    import re
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Skip header if present
    if lines:
        header = lines[0].lower()
        if ('name' in header and 'quantity' in header) or ('drug' in header and 'qty' in header):
            lines = lines[1:]

    for raw in lines:
        parts = re.split(r"\t|,|;|\|", raw)
        parts = [p.strip() for p in parts if p is not None]
        if not parts:
            continue

        name = parts[0] if len(parts) > 0 else ''
        qty_str = parts[1] if len(parts) > 1 else '0'
        price_str = parts[2] if len(parts) > 2 else None
        batch = parts[3] if len(parts) > 3 else ''
        expiry = parts[4] if len(parts) > 4 else None

        # Coerce quantity
        try:
            qty = int(float(qty_str))
            if qty < 0:
                qty = 0
        except Exception:
            qty = 0

        # Coerce buying price
        bp = None
        if price_str is not None and price_str != '':
            try:
                from decimal import Decimal
                bp = str(Decimal(str(price_str)))
            except Exception:
                bp = None

        # Normalize expiry (YYYY-MM-DD)
        if expiry:
            exp = expiry.strip()
            # Try multiple formats
            for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y'):
                try:
                    import datetime as _dt
                    dt = _dt.datetime.strptime(exp, fmt)
                    expiry = dt.date().isoformat()
                    break
                except Exception:
                    continue

        items.append({
            'name': name,
            'quantity': qty,
            'buying_price': bp,
            'batch_number': batch,
            'expiry_date': expiry,
        })

    return items