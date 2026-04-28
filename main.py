import subprocess
import os

def compress_pdf(input_path, output_path, quality="ebook"):
    """
    quality options:
      - 'screen'  → ~72 DPI  — smallest file
      - 'ebook'   → ~150 DPI — good balance (recommended)
      - 'printer' → ~300 DPI — high quality
      - 'prepress'→ ~300 DPI — near lossless
    """
    if not os.path.exists(input_path):
        print(f"Error: File '{input_path}' not found.")
        return

    result = subprocess.run([
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{quality}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        input_path,
    ], capture_output=True, text=True)

    if result.returncode == 0:
        original_mb = os.path.getsize(input_path) / (1024 * 1024)
        compressed_mb = os.path.getsize(output_path) / (1024 * 1024)
        reduction = ((original_mb - compressed_mb) / original_mb) * 100
        print(f" Done!")
        print(f"   Original:   {original_mb:.1f} MB")
        print(f"   Compressed: {compressed_mb:.1f} MB")
        print(f"   Reduction:  {reduction:.1f}%")
    else:
        print(" Ghostscript error:")
        print(result.stderr)

compress_pdf("Company_Profile.pdf", "compressed.pdf", quality="ebook")
