# Brave PDF Page Capture

`capture_pdf_pages.py` saves each page of a PDF open in Brave as a separate
PNG screenshot. It attaches to Brave only on your computer, focuses the
already-open PDF viewer, goes to the first page, then presses `PageDown` and
captures each visible page.

The script never downloads the PDF, calls the PDF website, or makes browser
network requests. Brave may still load more of the PDF while it scrolls, just
as it would during normal manual viewing.

## Requirements

- Linux Mint
- Brave Browser
- Python 3.10 or later
- Network access once to install the Python packages

## Install

Open a terminal in this project directory and run:

```bash
sudo apt update
sudo apt install -y python3 python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No separate Playwright browser download is required: the script connects to
your existing Brave instance.

## Run

1. Close every Brave window. Remote debugging must be enabled when Brave starts.
2. Start a dedicated Brave window from the terminal:

   ```bash
   brave-browser --remote-debugging-port=9222 --user-data-dir="$HOME/.config/brave-pdf-capture"
   ```

   If that command is unavailable, try `brave` or `brave-browser-stable` in
   its place.

   The separate profile directory prevents this window from interfering with
   your usual Brave session. You may sign in to websites in this window if the
   PDF needs authentication.

3. In that Brave window, open the PDF and wait until it has loaded. Use the
   PDF viewer's **Fit to page** zoom setting, and close any sidebar. This is
   required so one complete PDF page is visible for every screenshot.
4. In the project terminal, activate the virtual environment if it is not
   already active, then capture the pages:

   ```bash
   source .venv/bin/activate
   python3 capture_pdf_pages.py
   ```

   PNG files are written to `pdf-pages/page-001.png`, `page-002.png`, and so
   on. Do not interact with the Brave window until the command completes.

## Options

Choose another output directory:

```bash
python3 capture_pdf_pages.py --output ~/Pictures/my-pdf
```

The output resolution is the same as the Brave PDF viewer at its current
window size and zoom. Maximize the Brave window before selecting **Fit to
page** for the largest screenshots.

If you have more than one PDF open, select the intended tab with a unique part
of its URL:

```bash
python3 capture_pdf_pages.py --url invoice-2026
```

If you started Brave with another debugging port, provide it explicitly:

```bash
python3 capture_pdf_pages.py --port 9223
```

For a slow-loading PDF, wait longer after each page change:

```bash
python3 capture_pdf_pages.py --wait-ms 1500
```

## Troubleshooting

**`Cannot connect to Brave`**: Close Brave completely and launch it using the
remote-debugging command in step 2. Confirm that the script's `--port` matches
the port in that command.

**`Could not find a matching PDF tab`**: Make sure the PDF is open in the
dedicated debugging-enabled Brave window, not your normal Brave window. For
multiple PDFs, use `--url`.

**Screenshots contain only part of a PDF page**: Stop the script, maximize
Brave, select **Fit to page** in the PDF viewer, return to the first page, and
run it again.

**The script saves only one page**: Click the PDF once and press `PageDown`
yourself to confirm the viewer accepts keyboard navigation. If a site renders
slowly, retry with a higher `--wait-ms` value.
