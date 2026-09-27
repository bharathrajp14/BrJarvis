# 👁️ BR JARVIS — Vision Engine & Screen Intelligence (`vision/`)

> **Document Status**: Production Architecture Specification  
> **Subsystem**: Screen Capture, PyTesseract OCR, DOM Bridge, Accessibility API & Visual Grounding  
> **Module Path**: `vision/` & `actions/live_os_control.py`  
> **Version**: 38.0.0 (MK38 Architecture)  

---

## 1. Executive Summary

The **Vision Engine** (`vision/`) provides real-time visual perception for BR JARVIS. It enables the AI Operating System to observe multi-monitor desktop environments, extract text bounding boxes via PyTesseract OCR, query operating system accessibility trees via native Win32 `ctypes` (`<10ms`), interact with Web DOM nodes (`dom_bridge.py`), and run a hybrid visual locator pipeline (`hybrid_pipeline.py`).

---

## 2. Architecture & Vision Pipeline

```mermaid
graph TD
    Trigger[Capture Request / GUI Step] --> ScreenAnalyst[ScreenAnalyst: vision/screen_analyst.py]
    
    ScreenAnalyst -->|Multi-Monitor Capture| FrameBuffer[Frame Hash Check: FNV-1a Hash]
    FrameBuffer -->|Frame Unchanged| FastReturn[Return Cached Screen Analysis]
    
    FrameBuffer -->|Frame Changed| HybridPipeline[HybridPipeline: vision/hybrid_pipeline.py]
    
    HybridPipeline --> Accessibility[AccessibilityBridge: vision/accessibility.py (<10ms)]
    HybridPipeline --> DOMBridge[CDPBridge: vision/dom_bridge.py]
    HybridPipeline --> OCREngine[OCREngine: vision/ocr_engine.py]
    
    Accessibility --> SemanticGraph[SemanticUIGraph: vision/types.py]
    DOMBridge --> SemanticGraph
    OCREngine --> SemanticGraph
    
    SemanticGraph --> Grounding[Action Execution Grounding]
    Grounding --> VisualTrace[Visual Action Trace Overlay: live_os_control.py]
```

---

## 3. Subsystem Components & Responsibilities

| File | Class / Subsystem | Primary Function |
|---|---|---|
| [engine.py](vision/engine.py) | `VisionEngine` | Master visual coordinator registered in `CoreRuntime.container`, publishing `screen.understood` and `graph.updated` events. |
| [screen_analyst.py](vision/screen_analyst.py) | `ScreenAnalyst` | High-speed multi-monitor screenshot capture with FNV-1a frame hashing to skip redundant OCR operations on static screens. |
| [ocr_engine.py](vision/ocr_engine.py) | `OCREngine` | PyTesseract wrapper extracting text, confidence scores, and pixel bounding boxes `(x, y, w, h)` with SHA-256 image caching. |
| [accessibility.py](vision/accessibility.py) | `AccessibilityBridge` | Queries Windows UI Automation via native `ctypes` in under 10ms with 0 LLM token cost. |
| [dom_bridge.py](vision/dom_bridge.py) | `CDPBridge` | Connects to Chrome/Edge DevTools Protocol debugging port (`localhost:9222`) for web page DOM trees. |
| [hybrid_pipeline.py](vision/hybrid_pipeline.py) | `HybridVisionPipeline` | Fuses OCR results, accessibility elements, and visual DOM coordinates into a unified `SemanticUIGraph`. |
| [types.py](vision/types.py) | `SemanticUINode`, `SemanticUIGraph` | Pydantic v2 schemas for visual elements, coordinate bounds, UI roles, and hierarchical DAGs. |
| [live_os_control.py](actions/live_os_control.py) | `LiveOSController` | LLM screenshot action execution loop; draws red target crosshairs and action bounding footprints saved to `BR_WORKSPACE/Logs/live_os/`. |
