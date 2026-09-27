# 👁️ Computer Vision & Screen Understanding Master Spec (`vision/`)

> **Document Status**: Master System Architecture Specification  
> **Subsystem**: 7-Tier Hybrid Vision Engine, Accessibility Bridge, CDP DOM Bridge & Semantic Graph  
> **Module Path**: `vision/` & `actions/live_os_control.py`  
> **Version**: 38.0.0 (MK38 Architecture)  

---

## 1. Vision Architecture Philosophy

Instead of relying solely on expensive pixel screenshots or standard LLM vision calls, BR JARVIS employs a **7-Tier Hybrid Vision Pipeline** (`vision/hybrid_pipeline.py`). It understands desktop screens via native accessibility APIs, browser DevTools protocol DOM trees, fast local Tesseract OCR, and visual action grounding overlays.

---

## 2. 7-Tier Hybrid Vision Pipeline

```mermaid
graph TD
    ScreenCapture[Screen Frame Capture] --> HashCheck{FNV-1a Frame Hash Check}
    
    HashCheck -->|Is Static (No Change)| Skip[Bypass Vision Processing -> 0ms, 0 Tokens]
    HashCheck -->|Changed| HybridPipeline[7-Tier Hybrid Pipeline: vision/hybrid_pipeline.py]
    
    HybridPipeline --> Tier1[Tier 1: Windows Accessibility API: vision/accessibility.py (<10ms)]
    HybridPipeline --> Tier2[Tier 2: CDP Browser DOM Bridge: vision/dom_bridge.py]
    HybridPipeline --> Tier3[Tier 3: SHA-256 OCR Bounding Box Engine: vision/ocr_engine.py]
    
    Tier1 --> SemanticGraph[SemanticUIGraph Construction]
    Tier2 --> SemanticGraph
    Tier3 --> SemanticGraph
    
    SemanticGraph --> Grounding[Action Execution Grounding]
    Grounding --> VisualTrace[Visual Action Trace Overlay: live_os_control.py]
```

---

## 3. Subsystem Components & Responsibilities

| File | Class | Responsibility |
|---|---|---|
| [accessibility.py](vision/accessibility.py) | `AccessibilityBridge` | Tier 1 Windows UI Automation API bridge extracting native UI control trees via `ctypes` in under 10ms with 0 LLM token cost. |
| [dom_bridge.py](vision/dom_bridge.py) | `CDPBridge` | Tier 2 Chrome/Edge DevTools Protocol debugging bridge extracting web page DOM trees directly from port 9222. |
| [ocr_engine.py](vision/ocr_engine.py) | `OCREngine` | Tier 3 SHA-256 cached PyTesseract bounding box locator extracting text elements from non-accessible desktop applications. |
| [engine.py](vision/engine.py) | `VisionEngine` | Master vision coordinator publishing `screen.understood` & `graph.updated` events onto `EventBus`. |
| [types.py](vision/types.py) | `SemanticUINode`, `SemanticUIGraph` | Data models and hierarchy DAG representing UI roles (`BUTTON`, `TEXTBOX`, `DROPDOWN`, `TAB`, `WINDOW`, etc.). |
| [live_os_control.py](actions/live_os_control.py) | `LiveOSController` | Visual grounding action loop drawing red target crosshairs and action bounding footprints saved to `BR_WORKSPACE/Logs/live_os/`. |