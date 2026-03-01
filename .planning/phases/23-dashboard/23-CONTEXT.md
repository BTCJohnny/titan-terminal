# Phase 23: Dashboard - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning
**Source:** User context (inline)

<domain>
## Phase Boundary

Next.js 14 dashboard that renders the morning report and supports conversational signal Q&A. Single-page app connecting to the FastAPI backend built in Phase 22.

</domain>

<decisions>
## Implementation Decisions

### Stack & Setup
- Next.js 14 App Router, TypeScript, Tailwind CSS
- Dark mode only
- Single-page dashboard — no routing needed
- API base URL: http://localhost:8000 (FastAPI backend from Phase 22)
- All calls go to live backend — no mock data

### Layout (Three-Column)
- Left sidebar: symbol list + confidence scores
- Main content area: signal card for selected symbol
- Right sidebar: chat panel

### Signal Card Display
- Symbol name
- Direction: BULLISH / BEARISH / NO SIGNAL with colour (green / red / grey)
- Confidence as a percentage bar
- suggested_action
- Entry zone: low / ideal / high
- Stop loss, TP1, TP2
- Risk:reward ratio
- Full reasoning text (scrollable, not truncated)
- Wyckoff phase
- Three Laws check (pass/fail badges)

### On-Chain Intelligence Section
- Below the main signal card
- 5 individual Nansen signal cards, one per signal type:
  1. Smart Money Flows
  2. Exchange Flows
  3. On-Chain Holdings
  4. Buy/Sell Pressure
  5. Top PnL Wallets
- Each card shows: signal name, direction badge (bullish/bearish/neutral), raw summary text
- Highlight anomalous signals with distinct border or accent colour
- Pull from NansenSignal object in morning-report response — do not fabricate or mock

### Left Sidebar
- List of symbols from last morning-report run, sorted by confidence descending
- Clicking a symbol loads its signal card
- Show confidence score and suggested_action per row
- "Run Morning Report" button at top calls GET /api/morning-report and refreshes the list

### Chat Panel (Right Sidebar)
- Text input, send button, message history
- Calls POST /api/chat with {"question": "..."}
- Shows assistant response inline
- No auth needed
- "Open in Claude.ai" button — copies current signal context to clipboard and opens claude.ai in a new tab

### Claude's Discretion
- Component file structure and naming
- State management approach (React state vs context)
- Loading/error states UI
- Responsive breakpoints (if any)
- Tailwind theme configuration for dark mode

</decisions>

<specifics>
## Specific Ideas

- Three-column layout: left sidebar (symbols), center (signal card + on-chain), right (chat)
- Colour coding: green for BULLISH, red for BEARISH, grey for NO SIGNAL
- Anomalous Nansen signals get distinct border/accent colour
- Confidence displayed as percentage bar
- Three Laws displayed as pass/fail badges
- "Open in Claude.ai" copies signal context to clipboard

</specifics>

<deferred>
## Deferred Ideas

- Authentication / multi-user support
- Caching layer
- Complex animations
- Mobile responsive design (unless trivial)

</deferred>

---

*Phase: 23-dashboard*
*Context gathered: 2026-03-01 via user inline context*
