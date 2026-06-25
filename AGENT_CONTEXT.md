# RouteMind — Agent Context

> Last updated: 2026-06-25  
> This file is the single source of truth for any AI agent or contributor onboarding to this repository. Keep it in sync with the codebase.

---

## Project Overview

RouteMind is a **single-page React application** that demos an intelligent AI model routing platform. A user types a query in a unified chat interface; the frontend classifies intent and dispatches the request to the "best" AI model (currently mocked). The routing decision is displayed inline next to the response so users understand _why_ a particular model was chosen.

**Status:** Hackathon prototype. All AI routing is client-side mock logic. No real API calls to any LLM are made.

---

## Repository Layout

```
RouteMind/
├── .github/
│   └── workflows/          # CI pipeline (lint → test → build)
├── src/
│   ├── main.jsx            # React entry point — mounts App inside StrictMode
│   ├── App.jsx             # Router setup (react-router-dom), context providers
│   ├── index.css           # Tailwind base + custom keyframes/animations
│   ├── pages/
│   │   ├── Chat.jsx        # PRIMARY PAGE — all chat/session state lives here
│   │   ├── Home.jsx        # Landing page (your teammate's frontend work)
│   │   ├── Benefits.jsx    # Benefits/features marketing page
│   │   └── Documentation.jsx # Docs page
│   ├── components/
│   │   ├── Sidebar.jsx         # Chat history list, new/delete/rename chat, routing policy selector, telemetry panel
│   │   ├── ChatMessage.jsx     # Renders user + assistant messages; inline RoutingCard; feedback buttons
│   │   ├── ChatInput.jsx       # Auto-resizing textarea, file attachment, keyboard shortcuts
│   │   ├── TypingIndicator.jsx # Animated loading state with step labels and model preview
│   │   ├── RoutingCard.jsx     # Expandable card showing model, confidence, cost, reasoning
│   │   ├── Navbar.jsx          # Top nav for landing/marketing pages; AuthComingSoonModal trigger
│   │   ├── Footer.jsx          # Simple footer used on marketing pages
│   │   ├── Tooltip.jsx         # Lightweight tooltip wrapper (hover-based)
│   │   └── AuthenticationComingSoonModal.jsx  # Modal shown when auth is clicked
│   ├── context/
│   │   ├── ThemeContext.jsx    # Dark/light/system theme — applied to <html> via data-theme attribute
│   │   └── ToastContext.jsx    # Global toast notification system (showToast(message, type))
│   ├── data/
│   │   └── mockData.js        # defaultStats object (seed for localStorage telemetry); mock model list
│   ├── utils/
│   │   ├── mockRouter.js      # getMockRouting(query, file, policy) — intent classification + model selection
│   │   ├── fileHelpers.jsx    # formatFileSize(), getFileIcon() — used in ChatMessage file attachment display
│   │   └── animations.js      # Framer Motion variant presets (currently only used by a few pages)
│   └── test/
│       ├── mockRouter.test.js # Vitest unit tests for getMockRouting()
│       └── setup.js           # Vitest global setup (jsdom)
├── index.html              # Vite entry HTML
├── vite.config.js          # Vite + Vitest config; path alias @ → src/
├── eslint.config.js        # ESLint flat config (react + hooks rules)
├── package.json            # Scripts: dev, build, preview, lint, test, test:run
├── AGENT_CONTEXT.md        # This file
└── README.md               # Public-facing project overview
```

---

## Routing & Page Structure

`App.jsx` wraps everything in `ThemeProvider` and `ToastProvider`, then uses `react-router-dom` for client-side routing:

| Route       | Component           | Notes                                    |
| ----------- | ------------------- | ---------------------------------------- |
| `/`         | `Home.jsx`          | Landing page with Navbar + Footer        |
| `/chat`     | `Chat.jsx`          | Main product interface; no Navbar/Footer |
| `/benefits` | `Benefits.jsx`      | Marketing page                           |
| `/docs`     | `Documentation.jsx` | Docs page                                |

---

## Core State — `Chat.jsx`

All session state is owned by `Chat.jsx` and passed down as props. There is no global state store (no Redux, no Zustand).

### State Variables

| Variable                | Type                            | Purpose                                                                      |
| ----------------------- | ------------------------------- | ---------------------------------------------------------------------------- |
| `activeChatId`          | `string`                        | ID of the currently visible conversation                                     |
| `chatHistory`           | `Array<{id, title, timestamp}>` | Sidebar list of all sessions                                                 |
| `conversationsMessages` | `Record<chatId, Message[]>`     | All messages keyed by chat ID                                                |
| `isLoading`             | `boolean`                       | True while the simulated routing pipeline runs                               |
| `loadingStep`           | `string`                        | Current step label shown in `TypingIndicator`                                |
| `pendingModel`          | `string \| null`                | Model name revealed partway through loading animation                        |
| `timeoutRefs`           | `useRef(Array)`                 | All active `setTimeout` handles; cleared on unmount and before each new send |

### Message Shape

```js
{
  id: string,           // e.g. "user-101", "assistant-102"
  role: 'user' | 'assistant',
  content: string,
  time: string,         // display string, e.g. "Just now" or "2h ago"
  files?: Array<{       // only on user messages with attachments
    name: string,
    size: number,
    type: string
  }>,
  routing?: {           // only on assistant messages
    model: string,
    cost: string,       // e.g. "$0.0048"
    confidence: string, // e.g. "99%"
    reason: string
  }
}
```

### Key Handlers

- **`handleSendMessage(content, attachedFiles)`** — main dispatch function. Captures `activeChatId` at send time (`chatIdAtSend`) to prevent stale-closure bugs when user switches chats mid-loading. Runs a 4-step `setTimeout` chain (~4.2s total) simulating: intent analysis → model comparison → model selection → response generation. On completion, updates `conversationsMessages`, writes telemetry to `localStorage`, and auto-renames the chat if it's the first message.
- **`handleRegenerateResponse(messageId)`** — slices the message array back to before the target assistant message, then calls `handleSendMessage` with the preceding user message's content and files.
- **`handleNewChat(newChat)`** — adds a new entry to `chatHistory`, sets it active, and initialises its messages array.
- **`handleDeleteChat(id)`** — removes the chat and its messages. If all chats are deleted, creates a new blank one.
- **`handleRenameChat(id, newTitle)`** — updates the title in `chatHistory`.
- **`handleClearConversation()`** — empties messages for the active chat; shows a toast.

---

## `getMockRouting` — `src/utils/mockRouter.js`

**Signature:** `getMockRouting(query: string, file: File | null, policy: string): RoutingResult`

**Policies** (read from `localStorage` key `routingPolicy`, default `'balanced'`):

- `'speed'` — biases toward low-latency models (Gemini Flash, GPT-4o mini)
- `'cost'` — biases toward cheapest models (DeepSeek, Gemini Flash)
- `'quality'` — biases toward frontier models (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro)
- `'balanced'` — default, weighted scoring across latency, cost, and capability

**Classification logic (keyword-based, in priority order):**

1. File attachment present → `Gemini 1.5 Pro` (document) or `GPT-4o` (image)
2. `code / rust / python / javascript / debug / function / algorithm` → `Claude 3.5 Sonnet`
3. `react / next.js / remix / vue / svelte / frontend` → `Claude 3.5 Sonnet`
4. `research / paper / study / analysis / compare` → `Perplexity`
5. `explain / summarize / what is / how does` → `GPT-4o`
6. `write / essay / blog / email / draft` → `GPT-4o`
7. `math / calculate / equation / formula` → `GPT-4o` (with reasoning note)
8. `translate / language / spanish / french` → `GPT-4o mini`
9. `image / draw / generate / create a picture` → `DALL-E 3` (note: no real image generation)
10. Default fallback → `GPT-4o` (balanced)

**Returns:** `{ model, cost, confidence, reason, latency }` — all strings for display.

---

## `Sidebar.jsx` — Detailed Notes

The sidebar is the most complex component (~33KB). Key sub-sections:

- **Chat list** — scrollable list of `chatHistory`, with inline rename (double-click title) and delete (hover → trash icon). Active item is highlighted with `bg-blue-950/30 text-white` (no colored side border — clean active state).
- **Routing policy selector** — `<select>` that reads/writes `localStorage('routingPolicy')`. Emits `storage` event on change so `Chat.jsx` reads the latest value at send time.
- **Telemetry panel** — shows `totalQueries`, `savings`, and a model breakdown pie. Reads from `localStorage('routingStats')` on mount and on a custom `telemetry-updated` window event (fired by `Chat.jsx` after each assistant response). `defaultStats` from `src/data/mockData.js` is used as the seed when no stored data exists.
- **Theme toggle** — wired to `ThemeContext`. Cycles through `'light'`, `'dark'`, `'system'`. Applied to `<html data-theme="...">` by `ThemeContext.jsx`.
- **`Tooltip.jsx`** — the sidebar imports from `src/components/Tooltip.jsx` (extracted to its own file). It is a simple hover wrapper; not accessible for keyboard/screen reader use yet.
- **Mobile behaviour** — controlled by `mobileOpen` prop from `Chat.jsx`. Renders as a fixed overlay with a backdrop on screens below `md` breakpoint.

---

## `ChatMessage.jsx` — Detailed Notes

Handles both `role: 'user'` and `role: 'assistant'` in a single component with an `isUser` branch.

- **Prop contract:** accepts a single `message` object (the dual-prop API from an earlier version has been removed).
- **`CodeBlock`** — internal sub-component. Uses `react-syntax-highlighter` (Prism / `vscDarkPlus` theme). Inline vs. block detection: `!match || !String(children).includes('\n')`.
- **`markdownComponents`** — full set of custom renderers for `react-markdown` + `remark-gfm`: headings, paragraphs, lists, blockquotes, links (with `ExternalLink` icon), tables, and code.
- **`SkeletonMessage`** — rendered when `role === 'assistant'` and content is empty and not streaming. Uses `animate-pulse`.
- **Action toolbar** — appears on hover (`opacity-0 group-hover:opacity-100`). User messages: Copy + Share. Assistant messages: Copy + Regenerate + ThumbsUp + ThumbsDown + Share.
- **`RoutingCard`** is rendered inline below the assistant message content when `message.routing` is present.

---

## `RoutingCard.jsx` — Detailed Notes

An expandable card that displays the routing decision for an assistant message.

- Takes a single `routing` prop: `{ model, cost, confidence, reason }`.
- Collapsed state shows model badge, cost, confidence percentage.
- Expanded state adds the `reason` text and a visual model indicator.
- **Status:** Actively used — rendered inside `ChatMessage.jsx` for every assistant message that has a `routing` object. The component is NOT dead code; an earlier version of this codebase had it imported but hidden in `Chat.jsx` — that has since been corrected.

---

## `ChatInput.jsx` — Detailed Notes

- Auto-resizing `<textarea>` via `useEffect` on `value`. Clamped between 56px and 200px.
- File attachment via hidden `<input type="file">`. Multiple files supported. Accepted types: `.pdf`, `.txt`, `.md`, `.doc`, `.docx`, `.csv`, `.json`, `.png`, `.jpg`, `.jpeg`, `.webp`.
- Attached file previews rendered above the textarea with name, size, and `getFileIcon()`.
- **Keyboard shortcuts:** `Enter` submits; `Shift+Enter` inserts newline.
- **Note:** Helper text at the bottom uses `text-[11px]` which is below the 12px accessibility floor. Should be changed to `text-xs` (12px).

---

## `TypingIndicator.jsx` — Detailed Notes

Shown in the message list while `isLoading === true`.

- Accepts `loadingStep` (current step label string) and `selectedModel` (null until step 3).
- Renders animated step pills cycling through: "Analyzing Intent…" → "Comparing Models…" → "Selecting Best Model…" → "Generating Response…"
- When `selectedModel` becomes non-null (step 3), it renders a model badge preview inside the indicator.

---

## Context Providers

### `ThemeContext.jsx`

- Provides `{ theme, setTheme }` — values: `'light'`, `'dark'`, `'system'`.
- On mount and on every `theme` change, sets `document.documentElement.setAttribute('data-theme', resolved)` where `resolved` is `'light'` or `'dark'` (system preference resolved via `matchMedia`).
- Used by: `Sidebar.jsx` (toggle button), `Navbar.jsx` (toggle button).

### `ToastContext.jsx`

- Provides `showToast(message: string, type: 'success' | 'error' | 'info')`.
- Renders a stack of toast notifications in a fixed portal at the bottom-right.
- Used by: `Chat.jsx`, `ChatMessage.jsx`, `ChatInput.jsx`, `Sidebar.jsx`.

---

## Data Layer

### `src/data/mockData.js`

Exports:

- `defaultStats` — `{ totalQueries: 0, savings: 0, models: {} }` — used as the seed when `localStorage('routingStats')` is empty.
- `modelList` — array of model descriptor objects used in various UI dropdowns.

### `localStorage` keys used at runtime

| Key             | Written by                     | Read by                 | Purpose                   |
| --------------- | ------------------------------ | ----------------------- | ------------------------- |
| `routingPolicy` | Sidebar policy selector        | `Chat.jsx` at send time | Active routing preference |
| `routingStats`  | `Chat.jsx` after each response | Sidebar telemetry panel | Cumulative session stats  |

---

## Test Suite — `src/test/`

| File                 | What it covers                                                                                                                                                              |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mockRouter.test.js` | `getMockRouting()` — verifies correct model selection for code queries, research queries, file attachments, policy overrides (speed/cost/quality), and the default fallback |
| `setup.js`           | `@testing-library/jest-dom` import for extended matchers                                                                                                                    |

Run tests: `pnpm test:run` (single pass) or `pnpm test` (watch mode).  
CI runs `pnpm test:run` in the `test` job after `lint`.

---

## CI Pipeline — `.github/workflows/`

Three jobs, sequential:

1. **lint** — `pnpm lint` (ESLint flat config)
2. **test** — `pnpm test:run` (Vitest)
3. **build** — `pnpm build` (Vite production build)

---

## Known Issues & Pending Work

| Area                | Issue                                                                                                                           | Priority |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `ChatInput.jsx`     | `text-[11px]` on helper text — below 12px a11y floor                                                                            | Low      |
| `ChatMessage.jsx`   | `RoutingCard` import still present even though the component renders correctly — no action needed, just noting it's intentional | —        |
| `Sidebar.jsx`       | `Tooltip.jsx` is not keyboard/screen-reader accessible                                                                          | Low      |
| `Chat.jsx`          | `handleNewChat` in header button is an inline lambda; should call the same `handleNewChat` function used by Sidebar             | Low      |
| All pages           | No real API integration — all routing is mock                                                                                   | Future   |
| Auth flow           | `AuthenticationComingSoonModal` is a placeholder; no auth system exists                                                         | Future   |
| `Documentation.jsx` | Content is static/hardcoded, not generated from code                                                                            | Future   |

---

## Dependency Notes

Key runtime dependencies (from `package.json`):

| Package                         | Purpose                                                         |
| ------------------------------- | --------------------------------------------------------------- |
| `react` + `react-dom`           | UI framework                                                    |
| `react-router-dom`              | Client-side routing                                             |
| `react-markdown` + `remark-gfm` | Markdown rendering in assistant messages                        |
| `react-syntax-highlighter`      | Code block syntax highlighting (Prism / vscDarkPlus)            |
| `lucide-react`                  | Icon set used throughout                                        |
| `framer-motion`                 | Animation — used in landing/benefits pages and some transitions |
| `tailwindcss` (v4)              | Styling — utility classes + custom design tokens in `index.css` |

Key dev dependencies:
| Package | Purpose |
|---|---|
| `vite` | Build tool + dev server |
| `vitest` | Unit test runner |
| `@testing-library/jest-dom` | Extended DOM matchers for tests |
| `eslint` + `eslint-plugin-react-hooks` | Linting |

---

## Design Tokens (index.css)

Custom Tailwind tokens defined in `src/index.css` under `@theme`:

| Token               | Usage                             |
| ------------------- | --------------------------------- |
| `bg-app-bg`         | Page background (dark: `#0E0E0E`) |
| `bg-card-bg`        | Card/input surfaces               |
| `bg-sidebar-bg`     | Sidebar background                |
| `border-border-app` | All borders                       |
| `text-primary`      | Primary text                      |
| `text-secondary`    | Muted/secondary text              |

Custom animation classes: `animate-slide-up-fade`, `animate-slide-in-right`, `stagger-1` through `stagger-4` — all defined as `@keyframes` in `index.css`.
