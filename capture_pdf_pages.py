#!/usr/bin/env python3
"""Capture each visible page from a PDF open in Brave."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Browser, Page, sync_playwright


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Screenshot each page from a PDF already open in Brave."
    )
    parser.add_argument(
        "--url",
        help="A unique part of the PDF tab URL. Required only when several PDF tabs are open.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9222,
        help="Brave remote-debugging port (default: 9222).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("pdf-pages"),
        help="Directory for generated PNG files (default: pdf-pages).",
    )
    parser.add_argument(
        "--wait-ms",
        type=int,
        default=700,
        help="Milliseconds to wait after changing pages (default: 700).",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=1000,
        help="Safety limit for screenshots (default: 1000).",
    )
    return parser.parse_args()


def pdf_url_for_page(page: Page) -> str | None:
    """Identify direct PDF tabs and Chromium's extension-based PDF viewer tabs."""
    parsed = urlparse(page.url)
    if parsed.scheme in {"http", "https", "file"} and ".pdf" in parsed.path.lower():
        return page.url

    query_file = parse_qs(parsed.query).get("file", [])
    if query_file:
        return query_file[0]
    return None


def find_pdf_page(browser: Browser, url_hint: str | None) -> Page:
    candidates: list[Page] = []
    for context in browser.contexts:
        for page in context.pages:
            pdf_url = pdf_url_for_page(page)
            if pdf_url and (url_hint is None or url_hint in pdf_url or url_hint in page.url):
                candidates.append(page)

    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        open_tabs = [
            page.url
            for context in browser.contexts
            for page in context.pages
            if page.url != "about:blank"
        ]
        tabs = "\n".join(f"  - {url}" for url in open_tabs) or "  (no open tabs)"
        raise RuntimeError(
            "Could not find a matching PDF tab. Open the PDF in the debugging-enabled "
            f"Brave window and, if needed, pass --url.\nOpen tabs:\n{tabs}"
        )

    matches = "\n".join(f"  - {pdf_url_for_page(page)}" for page in candidates)
    raise RuntimeError(
        "More than one PDF tab matches. Re-run with --url and a unique part of its URL.\n"
        f"Matches:\n{matches}"
    )


def capture_pages(
    page: Page, output_dir: Path, wait_ms: int, max_pages: int
) -> int:
    if wait_ms < 0:
        raise ValueError("--wait-ms cannot be negative.")
    if max_pages < 1:
        raise ValueError("--max-pages must be at least one.")

    output_dir.mkdir(parents=True, exist_ok=True)
    page.bring_to_front()
    page.mouse.click(400, 400)
    page.keyboard.press("Home")
    page.wait_for_timeout(wait_ms)

    previous_digest: str | None = None
    for page_number in range(1, max_pages + 1):
        screenshot = page.screenshot()
        digest = hashlib.sha256(screenshot).hexdigest()
        if digest == previous_digest:
            return page_number - 1

        image_path = output_dir / f"page-{page_number:03d}.png"
        image_path.write_bytes(screenshot)
        print(f"Saved {image_path}")
        previous_digest = digest

        page.keyboard.press("PageDown")
        page.wait_for_timeout(wait_ms)

    raise RuntimeError(
        f"Stopped after --max-pages ({max_pages}) screenshots. Increase the limit if needed."
    )


def main() -> None:
    args = parse_arguments()
    endpoint = f"http://127.0.0.1:{args.port}"

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.connect_over_cdp(endpoint)
        except Exception as error:
            raise RuntimeError(
                f"Cannot connect to Brave at {endpoint}. Start Brave with "
                f"--remote-debugging-port={args.port} first."
            ) from error

        try:
            page = find_pdf_page(browser, args.url)
            count = capture_pages(page, args.output, args.wait_ms, args.max_pages)
        finally:
            browser.close()

    if count == 0:
        raise RuntimeError("No screenshot was captured. Confirm that the PDF viewer is visible.")
    print(f"Captured {count} page(s) to {args.output.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as error:
        raise SystemExit(f"Error: {error}") from error
