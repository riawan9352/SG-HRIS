import hashlib
import re
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class SourceCheckResult:
    status: str
    content_hash: str | None
    page_title: str | None
    details: str


def _extract_title(html_text: str) -> str | None:
    match = re.search(r"<title>(.*?)</title>", html_text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip()[:255]


def check_source_website(url: str) -> SourceCheckResult:
    request = Request(
        url=url,
        headers={
            "User-Agent": "Hospital-HRIS-Compliance-Monitor/1.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with urlopen(request, timeout=12) as response:
            raw = response.read(250_000)
            text = raw.decode("utf-8", errors="ignore")
            page_title = _extract_title(text)
            content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            return SourceCheckResult(
                status="ok",
                content_hash=content_hash,
                page_title=page_title,
                details=f"HTTP {response.status}",
            )
    except HTTPError as exc:
        return SourceCheckResult(
            status="http_error",
            content_hash=None,
            page_title=None,
            details=f"HTTPError {exc.code}",
        )
    except URLError as exc:
        return SourceCheckResult(
            status="network_error",
            content_hash=None,
            page_title=None,
            details=f"URLError {exc.reason}",
        )
    except Exception as exc:  # pragma: no cover
        return SourceCheckResult(
            status="failed",
            content_hash=None,
            page_title=None,
            details=str(exc),
        )
