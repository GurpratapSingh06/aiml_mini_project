import os
import time
from app.ingestion.document_processor.pdf_processor import (
    PDFProcessor,
    get_tesseract_status,
    get_document_dependencies_status,
)

def test_real_pdf():
    print("=== DEPENDENCY AUDIT ===")
    deps = get_document_dependencies_status()
    for k, v in deps.items():
        print(f"  {k}: installed={v.get('installed')}, version={v.get('version')}")
    
    tess = get_tesseract_status()
    print(f"\nTesseract Status: available={tess['available']}, path={tess['path']}")
    print(f"Message: {tess['message']}\n")
    
    pdf_path = r"M:\Third Year\MDMPROJECT\data\documents\doc_170cca417c72.pdf"
    if not os.path.exists(pdf_path):
        print(f"ERROR: File {pdf_path} does not exist!")
        return
        
    print(f"=== TESTING REAL MITAOE PDF: {pdf_path} ({os.path.getsize(pdf_path)/1024:.1f} KB) ===")
    processor = PDFProcessor()
    
    t0 = time.perf_counter()
    doc = processor.process(
        file_path=pdf_path,
        source_url="https://mitaoe.ac.in/downloads.php",
    )
    t_proc = (time.perf_counter() - t0) * 1000
    
    print(f"Processing Latency: {t_proc:.2f} ms")
    print(f"Pages Processed: {doc.page_count}")
    print(f"Document Type: {doc.document_type}")
    print(f"Is Scanned: {doc.is_scanned}")
    print(f"Is Mixed: {doc.is_mixed}")
    print(f"Academic Year Extracted: {doc.academic_year}")
    print(f"Full Text Length: {len(doc.full_text)} characters")
    print(f"Tables Found: {len(doc.tables)}")
    if doc.pages:
        p1 = doc.pages[0]
        print(f"Page 1 Text Sample ({len(p1.text)} chars): {p1.text[:200]}...")
        print(f"Page 1 Scanned: {p1.is_scanned}, OCR Confidence: {p1.ocr_confidence}")

if __name__ == "__main__":
    test_real_pdf()
