# PDF Compressor — Python

A Python-based PDF compression tool that uses **Ghostscript** to significantly reduce PDF file sizes while maintaining readable quality. Born out of a real-world challenge with a 958 MB company profile PDF.

---

##  The Challenge — Why I Switched from pypdf to Ghostscript

### Starting with pypdf (`major.py`)

The initial approach used `pypdf`, a pure-Python library, to compress PDF content streams:

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("Company_Profile.pdf")
writer = PdfWriter()

for page in reader.pages:
    writer.add_page(page)

for page in writer.pages:
    page.compress_content_streams()

with open("compressed_pypdf.pdf", "wb") as f:
    writer.write(f)
```

Running this against a **958 MB PDF** threw the following error:

```
pypdf.errors.LimitReachedError: Declared stream length of 78672860
exceeds maximum allowed length.
```

pypdf has an internal safety cap on the size of individual stream objects it can process. A 958 MB file full of high-resolution images contains stream objects that blow well past this limit — making pypdf unable to even read the pages, let alone compress them.

### The Fix — Ghostscript (`main.py`)

Ghostscript processes PDFs as a continuous stream at a lower level, with no object-size restrictions. It also natively recompresses images, fonts, and content streams in a single pass — exactly what a large, image-heavy PDF needs.

Result: the 958 MB file compressed down to a fraction of its original size using the `ebook` quality setting.

---

##  When to Use pypdf vs Ghostscript

| Scenario | Use |
|---|---|
| Merging, splitting, or rotating PDFs |  pypdf |
| Extracting text or metadata |  pypdf |
| Adding watermarks or passwords |  pypdf |
| Compressing small PDFs (< 50 MB) |  pypdf |
| Compressing large PDFs (> 50 MB) |  Ghostscript |
| Image-heavy PDFs (presentations, profiles) |  Ghostscript |
| Batch processing with quality control |  Ghostscript |
| Reducing DPI of embedded images |  Ghostscript |

**In short:** pypdf is great for structural manipulation of reasonably sized PDFs. The moment file size or embedded image streams become the bottleneck, Ghostscript is the right tool.

---

##  Project Structure

```
compress-pdf/
├── main.py       # Ghostscript-based compression (recommended)
├── major.py      # pypdf-based compression (for smaller files)
└── README.md
```

---

## ⚙️ Prerequisites

### For `main.py` — Ghostscript

**Python packages:** none (uses Python's built-in `subprocess` and `os` modules)

**System dependency:** Ghostscript must be installed on your machine (see Installation below).

---

### For `major.py` — pypdf

**Python packages:**
```bash
pip install pypdf
```

**System dependency:** none — pypdf is pure Python.

---

##  Installation

### Ghostscript

#### Windows

1. Go to [https://www.ghostscript.com/releases/gsdnld.html](https://www.ghostscript.com/releases/gsdnld.html)
2. Download the installer for your architecture (64-bit recommended)
3. Run the `.exe` installer and follow the prompts
4. Add Ghostscript to your system PATH:
   - Search **"Environment Variables"** in the Start menu
   - Under **System Variables**, find `Path` → click **Edit**
   - Add the path to the Ghostscript `bin` folder, e.g.:
     ```
     C:\Program Files\gs\gs10.xx.x\bin
     ```
5. Verify installation:
   ```bash
   gswin64c --version
   ```
   > **Note:** On Windows, replace `gs` in the script with `gswin64c`

####  Linux (Ubuntu / Debian)

```bash
sudo apt-get update
sudo apt-get install ghostscript

# Verify
gs --version
```

#### macOS

```bash
# Using Homebrew
brew install ghostscript

# Verify
gs --version
```

> Don't have Homebrew? Install it from [https://brew.sh](https://brew.sh)

---

### pypdf

All platforms:

```bash
pip install pypdf

# Or with uv
uv add pypdf
```

---

## Usage

### Ghostscript compression (`main.py`)

```python
compress_pdf("Company_Profile.pdf", "compressed.pdf", quality="ebook")
```

Run it:
```bash
python main.py
# or
uv run main.py
```

### Quality settings

| Setting | Image DPI | Best For |
|---|---|---|
| `screen` | 72 DPI | Smallest file, screen-only viewing |
| `ebook` | 150 DPI | Good balance — recommended default |
| `printer` | 300 DPI | High quality, suitable for printing |
| `prepress` | 300 DPI | Near-lossless, professional print |

### Expected output

```
Done!
   Original:   958.0 MB
   Compressed: 121.3 MB
   Reduction:  87.3%
```

---

## Quick Reference

| | pypdf (`major.py`) | Ghostscript (`main.py`) |
|---|---|---|
| Install | `pip install pypdf` | System package |
| File size limit | ~50 MB safe | No limit |
| Image recompression | ❌ | ✅ |
| Lossless structure | ✅ | ✅ |
| Speed on large files | Slow / fails | Fast |
| Python-only | ✅ | ❌ (system dep) |

---

##  License

MIT — free to use and modify.
