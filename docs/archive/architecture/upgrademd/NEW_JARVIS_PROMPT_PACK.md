# BR JARVIS — Tailored Master Upgrade Prompt Pack

Adapted from Zubair Trabzada's Prompt Pack for the enterprise **BR JARVIS** architecture (FastAPI server, RAG Engine, Web Dashboard, Voice Engine & PyQt6 HUD).

---

## PROMPT 1: The 3D Knowledge Galaxy Engine
> Build an interactive 3D Knowledge Galaxy from markdown notes in `./notes/` and `./captures/`.
> - Extend `actions/rag_library.py` to scan all `.md` files in `./notes` and `./captures`, extracting note titles, folder groups, ~700-character excerpts, and wikilink (`[[...]]`) / title reference connections.
> - Assign each node a unique numeric ID equal to its position index in the nodes array.
> - Expose a `/api/galaxy/data` REST endpoint on `server.py` returning `{nodes: [...], links: [...]}`.
> - Create `web/galaxy.html` using `3d-force-graph` from CDN. Style with a cinematic black space background, starfield particles, color-coded glowing nodes by group, and slow idle drift.
> - Clicking a node flies the camera smoothly to it, highlights immediate neighbor nodes, and opens a sleek side panel excerpt viewer.

---

## PROMPT 2: The Brain & RAG Indexing
> Integrate note-based question answering into the `/api/chat` and `/v1/chat/completions` endpoints.
> - Score note excerpts against user questions using keyword overlap and title match weighting.
> - Select top source notes and pass them into the Gemini LLM backend with a system prompt instructing it to answer strictly and concisely based on the notes.
> - Return response format: `{"answer": "...", "nodes": [source_node_indices]}`.
> - Maintain server-side session conversation history for context-aware follow-up questions.

---

## PROMPT 3: The Voice Engine & Web Speech Integration
> Enable bidirectional browser and desktop voice capabilities:
> - Browser TTS using Web Speech API `speechSynthesis` (preferring British English voice).
> - Web microphone input via `webkitSpeechRecognition` with live status indicator ("● listening...", "● thinking...").
> - Seamless audio unlocked on initial user click interaction.

---

## PROMPT 4: The Magic — Fly-To-Source Camera Dive
> When JARVIS responds to a query using indexed notes:
> - Retrieve the returned `nodes` index array.
> - Automatically animate the 3D camera to dive directly to the primary source node, light up the node and its neighbors, and pop open the excerpt drawer.
> - If 4 or more nodes contributed to the answer, light up the entire node cluster in 3D space.

---

## PROMPT 5: The British Butler ("Sir") Persona
> Update system prompts across RAG, chat, and voice engines to enforce the JARVIS British Butler persona:
> - Dry, impeccably polite British butler with a razor wit, addressing the user as "sir".
> - One witty line + factual concise response.
> - Page boot greeting: `"Good evening, sir. [N] notes indexed, all present and accounted for."`

---

## PROMPT 6: Total Recall — Voice & Text Note Capture (`/remember`)
> Add dynamic live note creation:
> - Recognize user input starting with `"remember that..."` or POST requests to `/api/remember`.
> - Save the note content into `./captures/` folder as a formatted `.md` file with a descriptive title.
> - Update the RAG engine index dynamically and insert the new node LIVE into the active 3D galaxy at its most relevant node position with a pulse animation.
> - Fly camera to the new node and confirm out loud with a witty butler response.
