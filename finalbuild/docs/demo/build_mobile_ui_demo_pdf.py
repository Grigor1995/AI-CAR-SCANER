"""Append verified Android Compose screenshots to the existing Desktop mini-demo PDF.

Original Desktop pages are preserved as PDF pages, not rasterized.
Android screenshots come from committed Robolectric native-graphics runs
with fixture data, NOT from a phone/emulator. No iOS capture is invented.
Re-running replaces our Android appendix instead of duplicating it.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import os

from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

ROOT = Path(__file__).resolve().parent
SCREENSHOTS = ROOT / "screenshots"
DOCUMENT = ROOT / "AI-Car-Scanner-UI-Demo-2026-10-26.pdf"
MARKER = "ANDROID / NATIVE COMPOSE / PDF EXTENSION"

GALLERIES = (
    ("Android | Dashboard & languages", "Armenian dark theme and Russian light theme",
     ("android-home-hy.png", "DASHBOARD / HY / DARK"),
     ("android-home-ru-light.png", "DASHBOARD / RU / LIGHT")),
    ("Android | DTC & guided tests", "Fault codes and recorded diagnostic test results",
     ("android-dtc-hy.png", "FAULT CODES"),
     ("android-tests-hy.png", "GUIDED TESTS")),
    ("Android | AI analysis & progress", "Recalculated hypotheses and testing progress",
     ("android-analysis-recalculated.png", "ANALYSIS"),
     ("android-progress-hy.png", "TESTING PROGRESS")),
    ("Android | VCI & reports", "Adapter illustration and privacy-aware reporting",
     ("android-adapter-refined.png", "VCI ADAPTER"),
     ("android-reports-private.png", "REPORTS / HISTORY")),
    ("Android | Diagnostic charts", "Native chart views with localizations",
     ("android-diagram-hy-dark.png", "DIAGRAM / HY / DARK"),
     ("android-diagram-ru-light.png", "DIAGRAM / RU / LIGHT")),
)


def _font():
    for path in (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                 Path("C:/Windows/Fonts/arial.ttf")):
        if path.exists():
            pdfmetrics.registerFont(TTFont("DemoUILatin", str(path)))
            return "DemoUILatin"
    return "Helvetica"


def _draw_screenshot(canvas, filename, x, y, w, h):
    path = SCREENSHOTS / filename
    if not path.is_file():
        raise FileNotFoundError("Missing checked-in Compose screenshot: " + str(path))
    canvas.setFillColor(HexColor("#0A1B2C"))
    canvas.setStrokeColor(HexColor("#1784B4"))
    canvas.roundRect(x, y, w, h, 11, fill=1, stroke=1)
    with Image.open(path) as src:
        if min(src.size) <= 0:
            raise ValueError("Invalid screenshot: " + filename)
        image = ImageReader(src.convert("RGB"))
        size = min((w-18)/src.width, (h-18)/src.height)
        iw, ih = src.width*size, src.height*size
        canvas.drawImage(image, x+(w-iw)/2, y+(h-ih)/2,
                         iw, ih, preserveAspectRatio=True)


def _appendix(width, height):
    output = BytesIO()
    canvas = Canvas(output, pagesize=(width, height), pageCompression=1)
    font = _font()
    margin = width*0.045
    gap = width*0.023
    half = (width - 2*margin - gap)/2
    bottom = height*0.14
    shot_h = height*0.59
    if half < 100 or shot_h < 100:
        raise ValueError("Unexpected original PDF page dimensions")
    for i, (title, subtitle, left, right) in enumerate(GALLERIES, 1):
        canvas.setFillColor(HexColor("#030C18"))
        canvas.rect(0, 0, width, height, fill=1, stroke=0)
        canvas.setFillColor(HexColor("#00AEEF"))
        canvas.rect(0, height-height*.007, width, height*.007, fill=1, stroke=0)
        canvas.setFont(font, max(9, min(14, width*.012)))
        canvas.setFillColor(HexColor("#35C8FF"))
        canvas.drawString(margin, height*.91, "AI CAR SCANNER / MOBILE UI")
        canvas.setFont(font, max(16, min(29, width*.025)))
        canvas.setFillColor(HexColor("#F1F7FC"))
        canvas.drawString(margin, height*.82, title)
        canvas.setFont(font, max(9, min(13, width*.012)))
        canvas.setFillColor(HexColor("#A8BED2"))
        canvas.drawString(margin, height*.76, subtitle)
        for idx, (filename, caption) in enumerate((left, right)):
            x = margin + idx*(half + gap)
            canvas.setFillColor(HexColor("#79E3FF"))
            canvas.setFont(font, max(9, min(12, width*.0105)))
            canvas.drawString(x+3, bottom+shot_h+height*.022, caption)
            _draw_screenshot(canvas, filename, x, bottom, half, shot_h)
        canvas.setFont(font, max(7, min(10, width*.0085)))
        canvas.setFillColor(HexColor("#B0C2D0"))
        canvas.drawString(margin, height*.094,
            "Actual Kotlin / Compose UI capture: API 35 Robolectric native graphics, fixture data.")
        canvas.drawString(margin, height*.061,
            "Not a physical device or emulator. Verified iOS screenshots are not available.")
        canvas.setFillColor(HexColor("#5386A1"))
        canvas.setFont(font, max(5, min(8, width*.0065)))
        canvas.drawString(margin, height*.025, MARKER)
        canvas.drawRightString(width-margin, height*.025, f"ANDROID {i}/5")
        canvas.showPage()
    canvas.save()
    output.seek(0)
    return output


def update_pdf(document=DOCUMENT):
    document = Path(document).resolve()
    if not document.is_file():
        raise FileNotFoundError("Original Desktop UI demo PDF does not exist: " + str(document))
    source = PdfReader(str(document))
    desktop_pages = []
    for page in source.pages:
        if MARKER in (page.extract_text() or ""):
            break
        desktop_pages.append(page)
    if len(desktop_pages) < 1:
        raise RuntimeError("Refusing to replace PDF without original Desktop pages")
    original_size = desktop_pages[0].mediabox
    appendix = PdfReader(_appendix(float(original_size.width), float(original_size.height)))
    writer = PdfWriter()
    for page in desktop_pages:
        writer.add_page(page)
    for page in appendix.pages:
        writer.add_page(page)
    writer.add_metadata({
        "/Title": "AI CAR SCANNER - Desktop and Android UI Demo",
        "/Subject": "Original Desktop demo followed by authentic Android Compose UI captures",
    })
    temp = document.with_name(document.stem + ".building.pdf")
    try:
        with temp.open("wb") as output:
            writer.write(output)
        check = PdfReader(str(temp))
        if len(check.pages) != len(desktop_pages)+len(GALLERIES):
            raise RuntimeError("PDF page count changed unexpectedly")
        if MARKER not in (check.pages[-1].extract_text() or ""):
            raise RuntimeError("Android appendix provenance verification failed")
        os.replace(temp, document)
    finally:
        if temp.exists():
            temp.unlink()
    print(f"Updated PDF: {len(desktop_pages)} Desktop pages + {len(GALLERIES)} Android pages")
    print(document)


if __name__ == "__main__":
    update_pdf()
