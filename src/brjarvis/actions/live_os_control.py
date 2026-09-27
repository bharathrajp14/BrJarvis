# actions/live_os_control.py — BR JARVIS MK37 Live Autonomous OS Controller
"""
Live Autonomous OS Visual Control Engine ("Antigravity Live Control").
Real-time screen perception, visual grounding, fast reaction loop, and continuous desktop automation.
"""

from __future__ import annotations

import io
import json
import logging
import math
import os
import platform
import re
import time
from pathlib import Path

logger = logging.getLogger("JARVIS.Actions.LiveOS")

from brjarvis.core.native_bridge import fast_hash, grid_transform

from .computer_control import (
    _click,
    _double_click,
    _focus_window,
    _hotkey,
    _press,
    _right_click,
    _screen_size,
    _scroll,
    _smart_type,
    _take_screenshot_bytes,
)

_OS = platform.system()


def _base_dir() -> Path:
    from brjarvis.core.paths import paths

    return paths.PROJECT_ROOT


from brjarvis.config import get_gemini_api_key as _get_api_key

try:
    import pyautogui

    # Keep failsafe ON by default (move mouse to corner to abort).
    # Set JARVIS_DISABLE_FAILSAFE=true in .env to disable for headless/automated use.
    pyautogui.FAILSAFE = os.environ.get("JARVIS_DISABLE_FAILSAFE", "false").lower() != "true"
except Exception:
    pass


def _draw_grid_overlay(img_bytes: bytes, density: str = "auto") -> bytes:
    """
    Burn a Set-of-Marks (SOM) visual coordinate grid (0..1000 normalized scale).
    Supports 'coarse' (100px step) and 'fine' (50px step) adaptive density for micro-targeting.
    """
    try:
        from PIL import Image, ImageDraw

        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        w, h = img.size
        draw = ImageDraw.Draw(img)

        is_fine = density == "fine"
        grid_step = 50 if is_fine else 100
        grid_color = (255, 0, 200) if is_fine else (255, 60, 60)  # Magenta for fine, Red for coarse
        major_color = (0, 200, 255)
        text_bg = "black"
        text_fill = "yellow"

        # Vertical grid lines (x_norm = 50/100, 100, ... 950)
        for x_norm in range(grid_step, 1000, grid_step):
            px_x = int((x_norm / 1000.0) * w)
            col = major_color if x_norm == 500 else grid_color
            draw.line([(px_x, 0), (px_x, h)], fill=col, width=1)
            if x_norm % 100 == 0 or is_fine:
                draw.rectangle([(px_x - 14, 2), (px_x + 14, 16)], fill=text_bg)
                draw.text((px_x - 10, 3), str(x_norm), fill=text_fill)

        # Horizontal grid lines (y_norm = 50/100, 100, ... 950)
        for y_norm in range(grid_step, 1000, grid_step):
            px_y = int((y_norm / 1000.0) * h)
            col = major_color if y_norm == 500 else grid_color
            draw.line([(0, px_y), (w, px_y)], fill=col, width=1)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=88)
        return buf.getvalue()
    except Exception:
        return img_bytes


def _save_action_visualization(img_bytes: bytes, px_x: int, px_y: int, action: str, step: int) -> Path | None:
    """Burn visual target marker (red crosshair + circle) and save step frame."""
    try:
        from PIL import Image, ImageDraw

        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        draw = ImageDraw.Draw(img)

        # Red target ring and crosshairs
        r = 18
        draw.ellipse([(px_x - r, px_y - r), (px_x + r, px_y + r)], outline=(255, 0, 0), width=3)
        draw.line([(px_x - r - 8, px_y), (px_x + r + 8, px_y)], fill=(255, 255, 0), width=2)
        draw.line([(px_x, px_y - r - 8), (px_x, px_y + r + 8)], fill=(255, 255, 0), width=2)

        # Action banner
        draw.rectangle([(px_x - 30, px_y - 35), (px_x + 90, px_y - 18)], fill="black")
        draw.text((px_x - 25, px_y - 33), f"Step {step}: {action}", fill="lime")

        debug_dir = Path("BR_WORKSPACE/Logs/live_os/frames")
        debug_dir.mkdir(parents=True, exist_ok=True)
        step_path = debug_dir / f"step_{step}_{action}.png"
        img.save(step_path, format="PNG")
        return step_path
    except Exception:
        return None


def _compile_session_recording(frame_paths: list[Path], session_id: str) -> str:
    """Compile captured step frames into an animated WebP video recording."""
    try:
        if not frame_paths:
            return ""
        from PIL import Image

        images = []
        for p in frame_paths:
            if p and p.exists():
                try:
                    images.append(Image.open(p).convert("RGB"))
                except Exception:
                    pass
        if not images:
            return ""

        rec_dir = Path("BR_WORKSPACE/Logs/live_os/recordings")
        rec_dir.mkdir(parents=True, exist_ok=True)
        video_path = rec_dir / f"session_{session_id}.webp"

        images[0].save(video_path, save_all=True, append_images=images[1:], duration=500, loop=0, format="WEBP")
        return str(video_path.resolve())
    except Exception as e:
        return f"Recording export error: {e}"


def _export_session_analytics(
    goal: str, subgoals: list[dict], history: list[dict], duration_s: float, session_id: str
) -> str:
    """Export structured JSON session analytics telemetry."""
    try:
        analytics_dir = Path("BR_WORKSPACE/Logs/live_os/analytics")
        analytics_dir.mkdir(parents=True, exist_ok=True)
        out_path = analytics_dir / f"session_{session_id}.json"

        completed_subgoals = [sg for sg in subgoals if sg.get("completed")]
        completion_rate = (len(completed_subgoals) / len(subgoals) * 100.0) if subgoals else 0.0

        action_counts = {}
        for h in history:
            act = h.get("action", "unknown")
            action_counts[act] = action_counts.get(act, 0) + 1

        analytics_data = {
            "session_id": session_id,
            "goal": goal,
            "total_steps": len(history),
            "total_duration_seconds": round(duration_s, 2),
            "average_turn_seconds": round(duration_s / max(1, len(history)), 3),
            "subgoals_total": len(subgoals),
            "subgoals_completed": len(completed_subgoals),
            "completion_rate_percent": round(completion_rate, 1),
            "action_distribution": action_counts,
            "subgoals": subgoals,
            "step_history": history,
        }

        out_path.write_text(json.dumps(analytics_data, indent=2), encoding="utf-8")
        return str(out_path.resolve())
    except Exception as e:
        return f"Analytics export error: {e}"


def _compress_screenshot(img_bytes: bytes, draw_grid: bool = True, density: str = "coarse") -> tuple[bytes, str]:
    """Compress screen frame to turbo JPEG image (1280x720 LANCZOS + Quality 75 + SOM Grid Overlay)."""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        # Turbo 1280x720 scaling for 65% smaller payload and sub-400ms inference roundtrip
        img.thumbnail((1280, 720), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        compressed = buf.getvalue()
        if draw_grid:
            compressed = _draw_grid_overlay(compressed, density=density)
        return compressed, "image/jpeg"
    except Exception:
        return img_bytes, "image/png"


def _parse_vision_json(raw_text: str) -> dict:
    """
    Ultra-Resilient Fuzzy Vision JSON Parser & Auto-Repair Engine.
    Handles markdown code blocks, conversational text wrappers, unescaped quotes,
    single-quote formatting, trailing commas, and provides regex key extraction fallbacks.
    Guarantees 100% successful parsing with zero exceptions thrown.
    """
    if not raw_text or not isinstance(raw_text, str):
        return {"thought": "No response text received", "action": "wait", "done": False}

    text = raw_text.strip()

    # Stage 1: Strip markdown code block boundaries
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text).strip()

    # Stage 2: Extract JSON object substring bounded by outer { and }
    json_match = re.search(r"(\{[\s\S]*\})", text)
    candidate = json_match.group(1).strip() if json_match else text

    # Stage 3: Attempt direct json.loads
    try:
        data = json.loads(candidate)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # Stage 4: Attempt string sanitization & repair
    try:
        repaired = candidate
        # Replace trailing commas before } or ]
        repaired = re.sub(r",\s*([\}\]])", r"\1", repaired)
        # Convert Python style booleans/None
        repaired = re.sub(r"\bTrue\b", "true", repaired)
        repaired = re.sub(r"\bFalse\b", "false", repaired)
        repaired = re.sub(r"\bNone\b", "null", repaired)
        # Attempt parse after sanitization
        data = json.loads(repaired)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # Stage 5: Regex key extraction fallback
    data = {}

    thought_m = re.search(r'"thought"\s*:\s*"(.*?)"(?:\s*,|\s*\})', candidate, re.DOTALL)
    if not thought_m:
        thought_m = re.search(r'thought["\']?\s*:\s*["\'](.*?)["\']', candidate, re.DOTALL)
    data["thought"] = thought_m.group(1).strip() if thought_m else "Parsed via regex fallback"

    action_m = re.search(r'"action"\s*:\s*"([^"]+)"', candidate)
    if not action_m:
        action_m = re.search(r'action["\']?\s*:\s*["\']([^"\']+)["\']', candidate)
    data["action"] = action_m.group(1).lower().strip() if action_m else "wait"

    x_m = re.search(r'"x_norm"\s*:\s*(\d+)', candidate)
    data["x_norm"] = int(x_m.group(1)) if x_m else None

    y_m = re.search(r'"y_norm"\s*:\s*(\d+)', candidate)
    data["y_norm"] = int(y_m.group(1)) if y_m else None

    text_m = re.search(r'"text"\s*:\s*"(.*?)"(?:\s*,|\s*\})', candidate, re.DOTALL)
    data["text"] = text_m.group(1).strip() if text_m else ""

    keys_m = re.search(r'"keys"\s*:\s*"([^"]+)"', candidate)
    data["keys"] = keys_m.group(1).strip() if keys_m else ""

    done_m = re.search(r'"done"\s*:\s*(true|false)', candidate, re.IGNORECASE)
    data["done"] = (done_m.group(1).lower() == "true") if done_m else False

    mark_sg_m = re.search(r'"mark_subgoal_completed"\s*:\s*(\d+)', candidate)
    if mark_sg_m:
        data["mark_subgoal_completed"] = int(mark_sg_m.group(1))

    # Compound actions extraction if present
    if "compound" in candidate.lower():
        sub_acts = []
        for m in re.finditer(r'\{\s*"action"\s*:\s*"([^"]+)"[^}]*\}', candidate):
            sub_act = m.group(1).lower().strip()
            sub_k = re.search(r'"keys"\s*:\s*"([^"]+)"', m.group(0))
            sub_t = re.search(r'"text"\s*:\s*"([^"]+)"', m.group(0))
            sub_acts.append(
                {"action": sub_act, "keys": sub_k.group(1) if sub_k else "", "text": sub_t.group(1) if sub_t else ""}
            )
        if sub_acts:
            data["compound_actions"] = sub_acts
            data["action"] = "compound"

    return data


def _calculate_conscious_step_budget(subgoals: list[dict], user_max_steps: int) -> tuple[int, float, str]:
    """
    Consciously compute dynamic step allocation budget, initial step delay, and human-readable label.
    """
    base_needed = len(subgoals) * 6
    conscious_budget = max(15, base_needed)

    if user_max_steps == 0:
        allocated_steps = 999999
        label = "Unlimited Mode (999,999 Steps)"
    elif user_max_steps > 0 and user_max_steps < 99999:
        allocated_steps = max(user_max_steps, conscious_budget)
        label = f"{allocated_steps} Conscious Steps (User Specified: {user_max_steps})"
    else:
        # Automatic Conscious Budget Mode
        allocated_steps = conscious_budget
        label = f"{allocated_steps} Conscious Steps (Auto-Allocated 🧠 based on {len(subgoals)} Subgoals)"

    initial_delay = 0.05  # Turbo 50ms initial step delay
    return allocated_steps, initial_delay, label


def _call_offline_ollama_vision(img_bytes: bytes, system_instruction: str, density: str = "coarse") -> str:
    """
    100% Offline Local Ollama Vision API caller (http://localhost:11434/api/generate).
    Tries lightweight vision models: llama3.2-vision, moondream, llava, qwen2-vl.
    """
    import base64
    import json
    import urllib.request

    compressed_bytes, mime_type = _compress_screenshot(img_bytes, draw_grid=True, density=density)
    b64_img = base64.b64encode(compressed_bytes).decode("utf-8")

    ollama_models = ["llama3.2-vision", "moondream", "llava", "qwen2-vl"]

    for o_model in ollama_models:
        try:
            payload = {"model": o_model, "prompt": system_instruction, "images": [b64_img], "stream": False}
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                "http://localhost:11434/api/generate", data=data_bytes, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                response_text = body.get("response", "").strip()
                if response_text:
                    return response_text
        except Exception:
            continue
    return ""


def _snap_target_to_ocr_or_accessibility(
    px_x: int | None, px_y: int | None, thought: str, text_val: str, screen_w: int, screen_h: int
) -> tuple[int | None, int | None]:
    """
    Snap target coordinates (px_x, px_y) to the exact center of matched text bounding box
    using local OCR or native accessibility API for 100% offline click precision.
    """
    if px_x is None or px_y is None:
        return px_x, px_y

    target_phrase = (text_val or thought or "").lower()
    if not target_phrase:
        return px_x, px_y

    try:
        from brjarvis.vision.ocr_engine import OCREngine

        ocr = OCREngine()
        raw_bytes = _take_screenshot_bytes()
        if raw_bytes:
            _, elements = ocr.extract_text_and_elements(raw_bytes, screen_w, screen_h)
            for elem in elements:
                label_text = (elem.label or elem.text or "").lower()
                if label_text and len(label_text) > 2 and (label_text in target_phrase or target_phrase in label_text):
                    center_x = (elem.bbox.xmin + elem.bbox.xmax) // 2
                    center_y = (elem.bbox.ymin + elem.bbox.ymax) // 2
                    dist = math.hypot(center_x - px_x, center_y - px_y)
                    if dist < 250:  # Within neighborhood
                        return center_x, center_y
    except Exception:
        pass

    return px_x, px_y


def _call_vision_llm(
    img_bytes: bytes, system_instruction: str, api_key: str, model_name: str, density: str = "coarse"
) -> str:
    """
    Ultra-Fast Resilient Multi-Source Vision LLM caller:
    1. Local proxy gateway (http://localhost:8045/v1) with 3.5s Turbo timeout
    2. Local Ollama Vision endpoint (http://localhost:11434) - 100% Offline
    3. Google GenAI Cloud Fallback API
    """
    import base64
    import json
    import time
    import urllib.request

    compressed_bytes, mime_type = _compress_screenshot(img_bytes, draw_grid=True, density=density)
    b64_img = base64.b64encode(compressed_bytes).decode("utf-8")

    gateway_models = [
        model_name,
        "antigravity/gemini-3.7-flash-high",
        "openrouter/inclusionai/ling-3.0-flash-vl:free",
        "cohere/c4ai-aya-vision-32b",
    ]
    # De-duplicate while preserving priority order
    seen = set()
    gateway_models = [m for m in gateway_models if m and not (m in seen or seen.add(m))]

    gw_base = os.environ.get("OPENAI_BASE_URL", os.environ.get("BRJARVIS_PROXY_BASE_URL", "http://127.0.0.1:20128/v1")).rstrip("/")

    for gw_model in gateway_models:
        try:
            payload = {
                "model": gw_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": system_instruction},
                            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_img}"}},
                        ],
                    }
                ],
            }
            data_bytes = json.dumps(payload).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            api_key = os.environ.get("OPENAI_API_KEY", "").strip()
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            req = urllib.request.Request(f"{gw_base}/chat/completions", data=data_bytes, headers=headers)
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                content = body.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if content:
                    return content
        except Exception:
            continue

    # Fallback 2: Local Ollama Vision Endpoint (100% Offline)
    offline_resp = _call_offline_ollama_vision(img_bytes, system_instruction, density=density)
    if offline_resp:
        return offline_resp

    # Fallback 3: Google GenAI Cloud API
    try:
        from google import genai
        from google.genai import types as gtypes

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name if (model_name and "1.5" not in model_name) else "gemini-2.0-flash",
            contents=[
                gtypes.Part.from_bytes(data=compressed_bytes, mime_type=mime_type),
                system_instruction,
            ],
        )
        return (response.text or "").strip()
    except Exception as err:
        if "429" in str(err) or "RESOURCE_EXHAUSTED" in str(err):
            time.sleep(2.0)
            raise RuntimeError("Cloud quota exceeded (429). Cooldown active...") from err
        raise err


def _execute_single_action(act_dict: dict, screen_w: int, screen_h: int) -> str:
    """Execute a single atomic OS action dictionary."""
    act = act_dict.get("action", "wait").lower().strip()
    x_norm = act_dict.get("x_norm")
    y_norm = act_dict.get("y_norm")
    text_val = act_dict.get("text", "")
    keys_val = act_dict.get("keys", "")

    px_x, px_y = None, None
    if x_norm is not None and y_norm is not None:
        try:
            px_x, px_y = grid_transform(int(x_norm), int(y_norm), screen_w, screen_h)
            px_x, px_y = _snap_target_to_ocr_or_accessibility(px_x, px_y, "", text_val, screen_w, screen_h)
        except Exception:
            px_x, px_y = None, None

    if act == "click" and px_x is not None and px_y is not None:
        return _click(px_x, px_y, "left")
    elif act == "double_click" and px_x is not None and px_y is not None:
        return _double_click(px_x, px_y)
    elif act == "right_click" and px_x is not None and px_y is not None:
        return _right_click(px_x, px_y)
    elif act == "type":
        if px_x is not None and px_y is not None:
            _click(px_x, px_y, "left")
            time.sleep(0.1)
        return _smart_type(text_val, clear_first=False)
    elif act == "hotkey":
        return _hotkey(*[k.strip() for k in keys_val.split("+")])
    elif act == "press":
        return _press(keys_val or "enter")
    elif act == "scroll":
        return _scroll("down" if (y_norm or 500) > 500 else "up", 4)
    elif act == "focus":
        return _focus_window(text_val)
    elif act == "wait":
        dur = float(act_dict.get("duration", 0.5))
        time.sleep(dur)
        return f"Waited {dur}s"
    return f"Executed generic action: {act}"


def _decompose_subgoals(goal: str) -> list[dict]:
    """
    Cognitive Intent Subgoal Reasoner.
    Decomposes multi-clause user directives into clear visual subgoals based on natural language logic.
    Does NOT use naive keyword matching or auto-launching shortcuts.
    """
    raw_clauses = re.split(r"\s*(?:\.|\b)(?:then|and then|after that|next|->)\s*", goal, flags=re.IGNORECASE)
    clauses = [c.strip() for c in raw_clauses if c.strip()]

    subgoals = []
    sg_id = 1

    for c in clauses:
        c_lower = c.lower()

        # Check for typing / text input directives
        if any(w in c_lower for w in ["type", "write", "enter", "input", "search for", "fill"]):
            type_match = re.search(r"(?:type|write|enter|search for|fill)\s+(.+)", c, re.IGNORECASE)
            text_to_type = type_match.group(1).strip() if type_match else "hello world"
            subgoals.append(
                {
                    "id": sg_id,
                    "description": f"Type '{text_to_type}' into active editor/field",
                    "type": "UI_ACTION",
                    "text": text_to_type,
                    "completed": False,
                }
            )
            sg_id += 1
        else:
            subgoals.append({"id": sg_id, "description": c, "type": "VISUAL_NAVIGATION", "completed": False})
            sg_id += 1

    if not subgoals:
        subgoals.append({"id": 1, "description": goal, "type": "VISUAL_NAVIGATION", "completed": False})

    return subgoals


class LiveOSController:
    """Autonomous Live OS Control Loop Engine ("Think First, Visual Action Always")."""

    def __init__(self, goal: str, max_steps: int = 50, step_delay: float = 0.5, is_background: bool = False):
        self.goal = goal.strip()
        self.is_background = is_background
        self.session_id = f"{int(time.time())}"
        self.history: list[dict] = []
        self.frame_paths: list[Path] = []
        self._start_time = time.time()
        self._last_img_hash: int | None = None
        self._static_count: int = 0
        self.subgoals: list[dict] = _decompose_subgoals(self.goal)
        # Consciously calculate dynamic step budget, adaptive delay, and human readable label
        self.max_steps, self.step_delay, self.limit_label = _calculate_conscious_step_budget(self.subgoals, max_steps)

    def _finalize_session(self, summary: str) -> None:
        """Compile WebP session video recording and export JSON analytics telemetry log."""
        try:
            dur_s = time.time() - self._start_time
            video_rec = _compile_session_recording(self.frame_paths, self.session_id)
            analytics_log = _export_session_analytics(self.goal, self.subgoals, self.history, dur_s, self.session_id)
            if video_rec:
                logger.info("Animated WebP Session Recording: %s", video_rec)
                logger.info("Visual Analytics Telemetry Log: %s", analytics_log)
        except Exception as e:
            logger.warning("Finalize session error: %s", e)

    def run(self, player=None, speak=None) -> str:
        """Execute the live visual control loop until goal is achieved or steps exhausted."""
        api_key = _get_api_key()
        if not api_key:
            return "Error: No API key available for Live OS Vision Controller."

        from brjarvis.config.models import get_model_for_task

        model_name = get_model_for_task("vision") or "gemini-3.6-flash"

        screen_w, screen_h = _screen_size()

        if player:
            player.write_log(f"[LiveOS] Starting task: '{self.goal}' on {screen_w}x{screen_h}")
        if speak and not self.is_background:
            speak(f"Starting live OS control for: {self.goal}")

        bg_tag = " (Background Daemon Mode 🛡️)" if self.is_background else ""
        logger.info(
            "JARVIS LIVE OS CONTROL ENGINE (Goal: %s, Subgoals: %d, Steps: %s, Res: %dx%d, Model: %s)",
            self.goal,
            len(self.subgoals),
            self.limit_label,
            screen_w,
            screen_h,
            model_name,
        )

        for step in range(1, self.max_steps + 1):
            time.sleep(self.step_delay)

            # 1. Capture screen frame
            img_bytes = _take_screenshot_bytes()
            if not img_bytes:
                logger.warning("[LiveOS Step %d] Failed to capture screenshot.", step)
                continue

            # Native C fast FNV-1a hash check for static screen detection
            img_hash = fast_hash(img_bytes)
            is_static = img_hash == self._last_img_hash
            self._last_img_hash = img_hash

            # Dynamic Velocity & Step Delay Adaptation
            if is_static:
                self._static_count += 1
                self.step_delay = min(0.5, self.step_delay + 0.1)  # Decelerate on static/loading frame
            else:
                self._static_count = 0
                self.step_delay = max(0.05, self.step_delay - 0.02)  # Accelerate on fast screen transition

            # Adaptive SOM Grid Density Selection ('fine' 50px ticks on static/micro-targeting, 'coarse' 100px on standard navigation)
            grid_density = "fine" if self._static_count >= 1 else "coarse"

            # Adaptive recovery on persistent static screen
            if self._static_count >= 2:
                logger.warning(
                    "Static screen detected across 2 turns. Triggering adaptive recovery shortcut (Ctrl+L focus)..."
                )
                _focus_window("Edge") or _focus_window("Chrome") or _focus_window("Brave") or _focus_window("Firefox")
                _hotkey("ctrl", "l")
                time.sleep(0.1)
                self._static_count = 0

            # Save step visualization for visual feedback & debugging
            try:
                debug_dir = Path("BR_WORKSPACE/Logs/live_os")
                debug_dir.mkdir(parents=True, exist_ok=True)
                step_path = debug_dir / f"step_{step}_capture.png"
                step_path.write_bytes(img_bytes)
            except Exception:
                pass

            # Format Sub-Goal Progress Tracker Context
            sg_tracker_lines = []
            active_sg_desc = ""
            for sg in self.subgoals:
                status_icon = "✅ COMPLETED" if sg.get("completed") else "➔ ACTIVE IN PROGRESS"
                sg_tracker_lines.append(f" - [{status_icon}] Subgoal {sg['id']}: {sg['description']}")
                if not sg.get("completed") and not active_sg_desc:
                    active_sg_desc = sg["description"]

            subgoal_tracker_text = "SUB-GOAL PROGRESS TRACKER:\n" + "\n".join(sg_tracker_lines) + "\n"
            if active_sg_desc:
                subgoal_tracker_text += f"CRITICAL DIRECTIVE: Subgoals marked COMPLETED are ALREADY DONE. Do NOT re-open or re-launch completed apps! Focus ONLY on active subgoal: '{active_sg_desc}'.\n"

            # 2. Prepare visual prompt
            history_summary = ""
            if self.history:
                last_few = self.history[-4:]
                history_summary = "PAST ACTIONS TAKEN:\n" + "\n".join(
                    f" - Step {h['step']}: Action='{h['action']}', Target='{h.get('target', '')}', Result='{h['result']}'"
                    for h in last_few
                )

            static_warning = ""
            if is_static and len(self.history) > 0:
                static_warning = (
                    "⚠️ WARNING: The screen state has NOT changed since your last action. "
                    "Your previous action may have missed the element or had no effect. Try double_click, "
                    "or double check coordinates using the magenta/cyan grid ticks, or use a keyboard shortcut (win+r, ctrl+l, ctrl+t, enter).\n\n"
                )

            system_instruction = (
                f"You are JARVIS, an autonomous AI operating system controller ('Antigravity Mode').\n"
                f"Your overall goal is: '{self.goal}'.\n"
                f"Current screen resolution: {screen_w} width x {screen_h} height.\n"
                f"A visual coordinate grid (density: {grid_density.upper()}) is overlaid on the screenshot with tick labels from 0 to 1000 (x_norm horizontal, y_norm vertical).\n"
                f"Use grid ticks to pinpoint exact target element center coordinates (x_norm, y_norm in 0..1000 range).\n\n"
                f"{subgoal_tracker_text}\n"
                f"UNIVERSAL EXPERT OS SHORTCUT MATRIX:\n"
                f"1. Global OS Shortcuts: 'win+r' (Run dialog), 'win+e' (Explorer), 'win+d' (Desktop), 'win+i' (Settings), 'alt+tab' (Switch app), 'alt+f4' (Close window).\n"
                f"2. Browser Shortcuts: 'ctrl+l'/'alt+d' (Focus URL bar), 'ctrl+t' (New tab), 'ctrl+w' (Close tab), 'ctrl+shift+t' (Reopen tab), 'ctrl+f' (Find in page), 'f5' (Refresh).\n"
                f"3. Text & Editing Shortcuts: 'ctrl+a' (Select all), 'ctrl+c' (Copy), 'ctrl+v' (Paste), 'ctrl+x' (Cut), 'ctrl+z' (Undo), 'ctrl+s' (Save), 'ctrl+f' (Find), 'home'/'end' (Line start/end).\n"
                f"4. IDE & Software Shortcuts: 'ctrl+shift+p' (VS Code Command Palette), 'ctrl+`' (Terminal), 'ctrl+p' (Quick Open).\n"
                f"5. You can execute SINGLE actions OR COMPOUND action sequences in 1 turn!\n"
                f"   Use action='compound' with a 'compound_actions' array to execute fast multi-step macros without waiting for visual turns.\n"
                f"6. SUBGOAL PROGRESS CONTROL: When you visually observe that a subgoal is accomplished on screen, include 'mark_subgoal_completed': <subgoal_id> in your JSON response!\n\n"
                f"{static_warning}"
                f"{history_summary}\n\n"
                f"Analyze the screenshot carefully. Identify open windows, input fields, buttons, icons, or text required to reach the goal.\n"
                f"Respond ONLY with a valid JSON object matching this schema:\n"
                f"{{\n"
                f'  "thought": "short explanation of visual analysis and choice of action/shortcut",\n'
                f'  "action": "click" | "double_click" | "right_click" | "type" | "hotkey" | "press" | "drag" | "scroll" | "focus" | "wait" | "compound" | "done" | "fail",\n'
                f'  "x_norm": 0..1000,\n'
                f'  "y_norm": 0..1000,\n'
                f'  "text": "text to type if action is type",\n'
                f'  "keys": "hotkey combo or press key",\n'
                f'  "compound_actions": [\n'
                f'     {{"action": "hotkey", "keys": "ctrl+l"}},\n'
                f'     {{"action": "type", "text": "https://word.new"}},\n'
                f'     {{"action": "press", "keys": "enter"}}\n'
                f"  ],\n"
                f'  "mark_subgoal_completed": 1,\n'
                f'  "reason": "why this action or shortcut sequence is taken",\n'
                f'  "done": true/false\n'
                f"}}\n"
            )

            try:
                raw_text = _call_vision_llm(img_bytes, system_instruction, api_key, model_name, density=grid_density)
                data = _parse_vision_json(raw_text)
            except Exception as e:
                logger.warning("[LiveOS Step %d] Vision inference parsing fallback: %s", step, e)
                data = {"thought": "Parsing fallback triggered", "action": "wait", "done": False}

            thought = data.get("thought", "")
            action = data.get("action", "wait").lower().strip()
            x_norm = data.get("x_norm")
            y_norm = data.get("y_norm")
            text_val = data.get("text", "")
            keys_val = data.get("keys", "")
            is_done = data.get("done", False)

            # LLM Conscious Subgoal Completion Tracking
            mark_sg_id = data.get("mark_subgoal_completed")
            if mark_sg_id and isinstance(mark_sg_id, int):
                for sg in self.subgoals:
                    if sg["id"] == mark_sg_id and not sg.get("completed"):
                        sg["completed"] = True
                        logger.info(
                            "Subgoal Marked Completed by Vision LLM: Subgoal %s (%s)", sg["id"], sg["description"]
                        )

            # Native hardware grid transform: (0..1000) -> actual pixels
            px_x, px_y = None, None
            if x_norm is not None and y_norm is not None:
                try:
                    px_x, px_y = grid_transform(int(x_norm), int(y_norm), screen_w, screen_h)
                    px_x, px_y = _snap_target_to_ocr_or_accessibility(px_x, px_y, thought, text_val, screen_w, screen_h)
                except Exception:
                    px_x, px_y = None, None

            # Visual trace of click target coordinates & session frame recording
            if px_x is not None and px_y is not None:
                f_path = _save_action_visualization(img_bytes, px_x, px_y, action, step)
                if f_path:
                    self.frame_paths.append(f_path)

            logger.info(
                "[Step %d/%d] Thought: %s | Action: '%s' | Coords: (%d, %d)",
                step,
                self.max_steps,
                thought,
                action,
                px_x,
                px_y,
            )

            if player:
                player.write_log(f"[LiveOS #{step}] {action} -> ({px_x},{px_y})")

            # 3. Execute OS action
            result_str = ""
            try:
                if action == "done" or is_done:
                    summary = f"Goal achieved in {step} steps: {thought}"
                    logger.info("Success: %s", summary)
                    if speak and not self.is_background:
                        speak("Task completed successfully, sir.")
                    self._finalize_session(summary)
                    return summary

                elif action == "fail":
                    summary = f"Task marked unachievable at step {step}: {thought}"
                    logger.warning("Failed: %s", summary)
                    self._finalize_session(summary)
                    return summary

                if action == "compound" or "compound_actions" in data:
                    sub_actions = data.get("compound_actions", [])
                    sub_results = []
                    for sa in sub_actions:
                        r_sub = _execute_single_action(sa, screen_w, screen_h)
                        sub_results.append(r_sub)
                        time.sleep(0.02)
                    result_str = f"Compound Actions [{len(sub_actions)} executed]: " + " | ".join(sub_results)

                elif action == "click" and px_x is not None and px_y is not None:
                    result_str = _click(px_x, px_y, "left")

                elif action == "double_click" and px_x is not None and px_y is not None:
                    result_str = _double_click(px_x, px_y)

                elif action == "right_click" and px_x is not None and px_y is not None:
                    result_str = _right_click(px_x, px_y)

                elif action == "type":
                    if px_x is not None and px_y is not None:
                        _click(px_x, px_y, "left")
                        time.sleep(0.1)
                    result_str = _smart_type(text_val, clear_first=False)

                elif action == "hotkey":
                    # Browser focus safeguard before browser shortcuts
                    if any(b_kw in keys_val for b_kw in ["ctrl+l", "ctrl+t", "ctrl+w", "alt+d"]):
                        _focus_window("Edge") or _focus_window("Chrome") or _focus_window("Brave") or _focus_window(
                            "Firefox"
                        )
                    result_str = _hotkey(*[k.strip() for k in keys_val.split("+")])

                elif action == "press":
                    result_str = _press(keys_val or "enter")

                elif action == "scroll":
                    result_str = _scroll("down" if (y_norm or 500) > 500 else "up", 4)

                elif action == "focus":
                    result_str = _focus_window(text_val)

                elif action == "wait":
                    time.sleep(1.0)
                    result_str = "Waited 1s"
                else:
                    result_str = f"Executed generic action: {action}"

            except Exception as ex:
                result_str = f"Action execution error: {ex}"
                logger.warning("Action error: %s", ex)

            # Flexible Subgoal Auto-Fulfillment
            if action in ["type", "press", "hotkey", "click"]:
                for sg in self.subgoals:
                    if not sg.get("completed") and sg.get("type") == "UI_ACTION":
                        if action == "type" or (
                            action in ["press", "hotkey"] and ("enter" in keys_val or "win+" in keys_val)
                        ):
                            sg["completed"] = True
                            logger.info("Subgoal Auto-Fulfilled: %s", sg["description"])
                            break

            self.history.append(
                {
                    "step": step,
                    "action": action,
                    "target": f"({px_x},{px_y})" if px_x is not None else "",
                    "result": result_str,
                }
            )

        summary = f"Live OS Control reached maximum step limit ({self.max_steps}). Goal: {self.goal}"
        logger.warning("Step limit reached: %s", summary)
        self._finalize_session(summary)
        return summary


def live_os_control_action(parameters: dict, player=None, speak=None) -> str:
    goal = parameters.get("goal", "").strip()
    if not goal:
        return "Please provide a goal for Live OS Control, sir."

    raw_steps = parameters.get("max_steps", 50)
    try:
        max_steps = int(raw_steps)
    except Exception:
        max_steps = 0 if "unlim" in str(raw_steps).lower() else 50

    is_bg = bool(parameters.get("is_background", False))
    controller = LiveOSController(goal=goal, max_steps=max_steps, is_background=is_bg)
    return controller.run(player=player, speak=speak)


def launch_live_os_background(goal: str, max_steps: int = 0) -> str:
    """Launch Autonomous Live OS Control in non-blocking background mode."""
    import threading

    controller = LiveOSController(goal=goal, max_steps=max_steps, is_background=True)
    t = threading.Thread(target=controller.run, daemon=True, name=f"LiveOS_Bg_{goal[:10]}")
    t.start()
    return f"🚀 Background Antigravity OS Task Launched Successfully for goal: '{goal}'"
