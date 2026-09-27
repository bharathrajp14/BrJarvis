# 11 — VISION & MULTIMODAL FORENSIC RECORD

## 1. Overview & Vision Architecture
The `vision/` subsystem provides multi-layered screen perception: high-speed screen capture, accessibility tree parsing, browser DOM introspection via CDP, OCR bounding box detection, and VLM (Visual Language Model) multimodal reasoning.

---

## 2. File-by-File Forensic Analysis

### `vision/engine.py` (81 lines)
- **Role**: Vision Engine Facade (`VisionEngine`).
- **Methods**: `analyze_screen()`, `locate_element(query)`, `describe_region(bbox)`.
- **Pipeline Integration**: Ingests raw screenshot from `vision/screen_analyst.py` and routes to `vision/hybrid_pipeline.py`.
- **Disposition**: **KEEP + IMPROVE**.

### `vision/screen_analyst.py` (91 lines)
- **Role**: Multi-monitor screen capture.
- **Capture Methods**: Direct DXGI desktop duplication (Windows GPU capture < 15ms) with fallback to `mss` / Win32 GDI.
- **Disposition**: **KEEP**.

### `vision/hybrid_pipeline.py` (68 lines)
- **Role**: Dual-resolution image processing pipeline.
- **Strategy**: Crops full-resolution patches around target regions for OCR while downsampling the entire canvas to 1024x1024 for VLM context tokens.
- **Disposition**: **KEEP**.

### `vision/accessibility.py` (105 lines) & `vision/dom_bridge.py` (118 lines)
- **Role**: Structured UI tree extraction.
- **Win32 Accessibility**: Traverses `UIAutomation` element tree to get exact element control types, names, and automation IDs without optical guessing.
- **CDP DOM Bridge**: Connects to Chrome/Edge DevTools protocol to extract DOM elements, CSS selectors, and bounding boxes.
- **Disposition**: **KEEP**.

### `vision/ocr_engine.py` (111 lines)
- **Role**: Local OCR text extraction.
- **Backends**: Windows Media OCR API (built-in Windows 10/11) with fallback to `tesseract` / `easyocr`.
- **Disposition**: **KEEP**.
