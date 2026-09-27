# BR JARVIS — FINAL VISION & PERCEPTION ARCHITECTURE

## 1. Architectural Invariants
1. **Cheapest-Sufficient Perception Router**: Perception tasks query structured UI representations before escalating to optical models:
   $$\text{Accessibility Tree (Win32)} \rightarrow \text{DOM Tree (CDP)} \rightarrow \text{Windows OCR} \rightarrow \text{VLM Downscaled Image} \rightarrow \text{Full-Res VLM Patch}$$
2. **Dual-Resolution Capture**: Downsample canvas to 1024x1024 for global visual context tokens; crop 100% native resolution bounding boxes around target elements for fine OCR.

---

## 2. Perception Pipeline Hierarchy

```mermaid
graph TD
    ScreenCapture[Screen Capture: vision/screen_analyst.py DXGI GPU] --> PerceptionRouter{Perception Router: vision/engine.py}
    
    PerceptionRouter -->|1. Native Win32 UI| A11y[Win32 UIAutomation Tree: vision/accessibility.py]
    PerceptionRouter -->|2. Web Browser| CDP[Chrome DevTools Protocol: vision/dom_bridge.py]
    PerceptionRouter -->|3. Optical Text| OCR[Windows Media OCR / EasyOCR: vision/ocr_engine.py]
    PerceptionRouter -->|4. Complex Visual Scene| VLM[Multimodal VLM: Gemini 2.5 Flash / Claude 3.7]

    A11y --> CoordinateMapper[Semantic Coordinate Resolver: computer/semantic_operator.py]
    CDP --> CoordinateMapper
    OCR --> CoordinateMapper
    VLM --> CoordinateMapper

    CoordinateMapper --> Operator[OS Automation Execution: computer/operator.py]
```
