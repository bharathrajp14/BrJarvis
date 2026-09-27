# BRJARVIS Design System

**Status:** Foundation specification  
**Date:** 2026-08-19  
**Author:** Manus AI

## Design principles

BRJARVIS should feel like a **premium personal AI operating environment**: intelligent, calm, technical, fast, high-information-density, and functional. The system should communicate operational truth rather than simulate intelligence with decorative motion.

The design system applies across the browser, desktop/HUD, floating widget, CLI, voice mode, vision mode, and Career OS. The layouts may differ by surface, but the meanings of color, status, risk, focus, hierarchy, and action should remain consistent.

| Principle | Application |
|---|---|
| Functional before ornamental | Every prominent control maps to a real capability or clearly indicates unavailable, loading, disconnected, denied, or experimental status. |
| Calm intelligence | Use hierarchy, spacing, and concise status summaries instead of constant glow or noisy animation. |
| Progressive disclosure | Show outcomes and current actions by default; reveal tool calls, events, diagnostics, and performance details on demand. |
| Semantic color | Color communicates action, health, warning, error, risk, or selection. It is not used as decoration alone. |
| One product identity | Browser, Qt, floating, and terminal surfaces share token names and interaction semantics. |
| Recoverability | Errors include a reason and an actionable recovery path where one exists. |
| Accessible by default | Keyboard navigation, focus visibility, semantics, contrast, scalable type, and reduced motion are first-class requirements. |

## Semantic tokens

The implementation should expose tokens in a platform-neutral naming scheme. The web surface can map them to CSS custom properties; Qt can map them to palette/style helpers; the CLI can map them to terminal colors and glyph styles.

### Color

The initial palette should be dark-first and restrained. Exact values should be calibrated against the existing palette and contrast tests rather than hardcoded into individual components.

| Token | Meaning | Typical usage |
|---|---|---|
| `surface.canvas` | Application background | Main workspace background |
| `surface.panel` | Primary panel | Sidebar, transcript, task workspace |
| `surface.elevated` | Raised surface | Modal, popover, execution detail |
| `surface.inverse` | Inverted surface | High-contrast badges or light-on-dark contexts |
| `text.primary` | Main readable text | Titles, user content, primary values |
| `text.secondary` | Supporting text | Descriptions, metadata |
| `text.muted` | Low-emphasis text | Captions, timestamps, inactive labels |
| `border.subtle` | Low-emphasis separation | Panel boundaries, dividers |
| `border.default` | Standard separation | Cards, fields, tables |
| `border.strong` | Emphasized separation | Selected or expanded regions |
| `action.primary` | Main interactive intelligence accent | Submit, approve, primary navigation |
| `action.secondary` | Secondary action | Tertiary controls, quiet links |
| `action.focus` | Keyboard focus | Focus rings and current target |
| `status.info` | Informational state | Connected, neutral activity |
| `status.success` | Successful/healthy state | Completed, verified, online |
| `status.warning` | Waiting or caution | Approval pending, degraded |
| `status.error` | Failed state | Task failure, provider error |
| `status.critical` | Dangerous/high-risk state | Destructive or privacy-sensitive action |

Status should also have non-color indicators such as icons, text labels, or patterns. A green indicator alone must not be the only way to communicate health.

### Typography

The application should use a readable proportional UI font for ordinary content and a monospace family only for technical values.

| Level | Use | Guidance |
|---|---|---|
| Display | Product identity or rare hero context | Use sparingly; never displace task information. |
| Page title | Workspace title | Clear, stable, and visually dominant. |
| Section title | Major content group | Supports scanning and grouping. |
| Card title | Task, model, memory, or workflow name | Strong but compact. |
| Body | Conversation, descriptions, explanations | Prioritize readability over density. |
| Secondary | Supporting context and metadata | Reduced emphasis, still legible. |
| Caption | Timestamps, labels, helper text | Never use for essential instructions. |
| Technical | Commands, paths, model IDs, diagnostics, code, logs | Monospace and selectable. |

The entire application must not be monospace. Technical typography should be clearly distinguished while remaining accessible and copyable.

### Spacing and geometry

Use a small base spacing scale and compose layouts from it. Avoid one-off pixel values in feature components. The system should define consistent panel padding, card gaps, row heights, field spacing, and touch/keyboard target sizes.

| Token family | Examples |
|---|---|
| `space.1` through `space.8` | Fine to large spacing steps |
| `radius.sm`, `radius.md`, `radius.lg` | Fields, cards, panels |
| `elevation.1` through `elevation.3` | Subtle to modal layering |
| `z.base`, `z.panel`, `z.popover`, `z.modal`, `z.toast` | Layer ordering |
| `control.height.sm`, `control.height.md`, `control.height.lg` | Compact, standard, prominent controls |

## Component inventory

Components should be implemented once per platform family and reused across domains. Domain components should compose primitives rather than create bespoke controls.

| Component | Required behavior |
|---|---|
| Button | Primary, secondary, quiet, destructive, loading, disabled, focus, and keyboard activation states |
| Icon button | Accessible label, tooltip/discoverability, focus, pressed state, and disabled state |
| Text input | Label, helper/error text, validation, loading, keyboard behavior, and secure variant where required |
| Command palette | Keyboard-first search, grouped commands, aliases, availability, risk labels, and execution feedback |
| Sidebar/navigation | Grouped routes, active state, collapsed mode, responsive drawer behavior, and shortcut hints |
| Status indicator | Label plus icon/shape; supports healthy, degraded, waiting, disconnected, denied, and unavailable |
| Task card | Goal, status, progress, current step, tool summary, result, artifacts, approval, and recovery |
| Execution timeline | Ordered steps, current activity, completed/failed/waiting states, and expandable detail |
| Tool activity | Human-readable tool name, status, result summary, latency where useful, and diagnostics link |
| Approval dialog | Action, target, risk, reason, affected resources, decision options, and safe defaults |
| Model card | Provider, model, health, latency, capabilities, context, cost estimate if available, and configuration path |
| Memory card | Content, type, source, confidence, importance, privacy, timestamps, and edit/forget actions |
| Workflow card | Trigger, schedule, steps, status, last run, failures, and run/edit/disable actions |
| Activity feed | Grouped events, retention/batching, filters, severity, and details drawer |
| Data table | Keyboard navigation, sorting, filtering, loading, empty, error, and responsive fallback |
| Artifact card | File type, title, provenance, preview/download, verification, and unavailable state |
| Empty state | Explains absence and offers a real next action |
| Loading state | Skeleton or progress appropriate to content; no fake activity |
| Error state | User-facing title, reason, retry/switch/view-diagnostics actions |
| Toast/notification | Concise, dismissible, accessible announcement, and durable activity link for important events |
| Modal/sheet | Focus trap, escape behavior, clear close action, responsive presentation, and unsaved-change handling |

## Interaction patterns

### Task execution

Simple tasks use a compact task card. Complex tasks use an execution timeline or DAG only when parallelism or dependency structure adds value. The default experience should show planning, current step, progress, tools used, results, and recovery controls. Raw event streams remain an advanced detail view.

### Risk and approval

Approval must be derived from the real policy engine and should be proportionate to risk. Low-risk actions should not interrupt unnecessarily. Medium, high, destructive, and privacy-sensitive actions should state what will happen, why it is requested, what resources are affected, and which decision options are available.

### Voice

Voice mode exposes explicit `listening`, `speaking`, `interrupted`, `processing`, `error`, and `disconnected` states. When the user interrupts a response, the UI must visibly show that playback stopped and new input is being processed. Animation is secondary to the state label and transcript.

### Vision and screen intelligence

Vision mode must present the current screen or selected region, detected applications, privacy state, analysis result, and allowed actions. Sensitive screen content must not be silently exposed in activity feeds, logs, notifications, or memory.

### Errors

Errors should be specific and recoverable. A provider failure should identify the provider, explain the failure in plain language, and offer retry, switch-model, or diagnostics actions when supported. Raw exceptions belong only in an explicitly opened diagnostics surface.

### Empty and unavailable states

An empty state means the capability is available but has no records. An unavailable state means the capability cannot currently be used. A disconnected state means transport or provider health is lost. These states require different messages and actions.

## Motion system

Motion communicates state and hierarchy. It should be fast, interruptible, and disabled or simplified for reduced-motion preferences.

| Good use | Prohibited default |
|---|---|
| Task progress and step transitions | Constant floating/pulsing decoration |
| Voice activity visualization | Random movement without state meaning |
| Panel open/close and expand/collapse | Slow transitions that delay interaction |
| Loading and reconnect indication | Simulated reasoning or fake tool activity |
| Status changes | Animation that obscures content or focus |

## Responsive behavior

The browser should support desktop, laptop, tablet, and applicable small-screen layouts. Responsive behavior must reorganize information rather than simply reduce widths.

| Width class | Layout strategy |
|---|---|
| Desktop | Three-region command workspace where useful: navigation, main intelligence surface, contextual detail. |
| Laptop | Reduce persistent secondary panels; preserve assistant/task context. |
| Tablet | Use drawers/sheets for navigation and details; prioritize one focused work surface. |
| Small screen | Use stacked conversation/task flows, bottom sheets, and compact command access. |
| Desktop Qt | Native resizable panels and keyboard shortcuts; share visual semantics, not browser layout. |
| CLI | Terminal width-aware rendering with compact fallback and scroll-safe output. |

## Accessibility requirements

Every component must support keyboard operation and visible focus. Interactive controls require accessible names, semantic roles, and state announcements. Color contrast must be validated for text, borders, status, focus, and disabled states. Motion must honor reduced-motion preferences. Shortcut-based actions must also be discoverable through menus or command help.

The command palette is a primary accessibility feature, not merely a power-user shortcut. Task, approval, voice, and error state changes should be announced in a way compatible with the surface’s accessibility model.

## Performance requirements

The UI must remain responsive during streaming responses, high-frequency events, voice activity, vision processing, and complex task updates. Instrumentation must precede optimization.

Required techniques where measurement justifies them include event batching, bounded activity retention, list virtualization, lazy loading of advanced views, memoization of stable projections, incremental transcript rendering, and cancellation of stale requests. No surface should render an unbounded raw event log.

## Validation checklist

A design-system component is ready for domain use only when it has:

| Check | Evidence |
|---|---|
| Semantic states | Loading, empty, unavailable, disconnected, error, disabled, focus, and success/risk states are defined. |
| Accessibility | Keyboard, focus, labels, semantics, contrast, and reduced motion are tested. |
| Runtime neutrality | The component does not fetch data or know backend implementation details. |
| Responsive behavior | Relevant desktop, laptop, tablet, small-screen, Qt, or CLI behavior is documented. |
| Error recovery | The component can present an actionable failure without raw exceptions. |
| Test coverage | Unit/component or equivalent surface tests exist. |
| Documentation | Usage, anatomy, variants, and anti-patterns are recorded. |

## References

[1]: ./FRONTEND_AUDIT.md "Repository-grounded frontend and runtime audit"
[2]: ./TARGET_FRONTEND_ARCHITECTURE.md "Target architecture and shared contracts"
[3]: ../src/brjarvis/ui/colors.py "Existing desktop palette helpers"
[4]: ../src/brjarvis/web/static/style.css "Existing browser visual styles"
[5]: ../src/brjarvis/core/terminal/theme.py "Existing terminal theme"


## Native and headless surface mapping

The native desktop surface should share semantic meaning with the web system without forcing a browser layout onto Qt. The existing Qt palette helpers in `src/brjarvis/ui/colors.py` and widget modules in `src/brjarvis/ui/widgets.py` are the starting point for a native token adapter.

| Shared semantic meaning | Web mapping | Qt mapping | Headless mapping |
|---|---|---|---|
| Primary action | CSS action token and button variant | Qt stylesheet/palette accent | Command text and prompt emphasis |
| Healthy/online | Status color plus label/icon | Status label, badge, and color | Log/status line with explicit text |
| Warning/waiting | Warning badge and approval state | Overlay/status panel | Prompt state such as approval required |
| Error | Error panel/toast with recovery | Error log and visible state | Structured log error and return state |
| Technical value | Technical font and selectable code block | Monospace Qt label/text view | Rich/terminal monospace rendering |
| Focus | CSS focus ring | Qt focus frame/style | Prompt cursor and highlighted selection |
| Reduced motion | Media preference | Native accessibility/system preference | No animation; state text only |

The headless implementation must not be treated as a hidden or broken version of the GUI. It is a deliberate surface with explicit capability limitations. Camera preview, graphical content, and visual screen analysis should report `unavailable` or `requires graphical display` rather than rendering empty placeholders or silently ignoring the request.

## Launcher and lifecycle interaction states

The desktop launcher owns more than visual startup. Because it can start or reuse the backend and launch the voice worker, the design system must provide compact but clear states for backend ownership and worker lifecycle:

- **Starting:** the backend or voice worker is being initialized; controls that depend on it show loading rather than fake readiness.
- **Online:** the runtime is connected and the surface can accept commands.
- **External runtime:** a compatible backend is already running outside the desktop process.
- **Degraded:** one subsystem such as voice, camera, or model routing is unavailable while other capabilities remain usable.
- **Reconnecting:** transport or backend recovery is in progress; current task state is preserved where supported.
- **Stopping:** shutdown is coordinated; new commands are disabled and active work is clearly described.

These states should use the same semantic status tokens as the browser command center and floating widget.
