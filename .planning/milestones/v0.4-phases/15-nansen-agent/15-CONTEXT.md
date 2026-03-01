# Phase 15: Nansen Agent - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning
**Source:** User-provided context

<domain>
## Phase Boundary

Production-ready on-chain agent that fetches 5 Nansen signals via MCP, aggregates into bullish/bearish/neutral with confidence, and logs every analysis to Obsidian vault.

</domain>

<decisions>
## Implementation Decisions

### MCP Integration
- The Nansen MCP server is installed and available as a tool in this environment
- Use Nansen MCP tools directly — do not simulate data or fall back to Claude knowledge
- Before writing any code, use the Nansen MCP tools to discover what's actually available
- Look for tools covering: token flows by holder segment (exchange, whale, smart money), smart money balances, top PnL wallets, and Hyperliquid funding rates

### Signal Mapping
Map the 5 required signals to whatever MCP tool names actually exist:
- Exchange flows → token flow tool filtered to Exchange segment
- Smart money → smart money balance/flow tool
- Whale activity → token flow tool filtered to Whale segment
- Top PnL wallets → top PnL or smart money performance tool
- Fresh wallets → new wallet activity if available, else holder segment data

### Error Handling
- If a required signal has no direct MCP tool: mark it neutral with confidence 0 and log a warning
- Never error out — graceful degradation is required

### Vault Logging
- Append to /Users/johnny_main/Developer/obsidian-vault/obsidian-vault/agents/nansen/signal-combinations.md after every analysis run
- Create the file with header row if it doesn't exist
- Use Python file I/O — not an MCP tool

### File Location
- The agent file lives at src/backend/agents/nansen_agent.py — full replacement of the stub
- NansenSignal model is already built in src/backend/models/ from Phase 14

### Claude's Discretion
- MCP tool invocation patterns and error handling
- Signal aggregation algorithm implementation details
- Logging format and structure within the markdown file

</decisions>

<specifics>
## Specific Ideas

- Exchange flows → token flow tool filtered to Exchange segment
- Smart money → smart money balance/flow tool
- Whale activity → token flow tool filtered to Whale segment
- Top PnL wallets → top PnL or smart money performance tool
- Fresh wallets → new wallet activity if available, else holder segment data
- Aggregation: 4-5 bullish = ACCUMULATION, 0-1 = DISTRIBUTION, else neutral
- Confidence scale: 0-100

</specifics>

<deferred>
## Deferred Ideas

None — context covers phase scope

</deferred>

---

*Phase: 15-nansen-agent*
*Context gathered: 2026-02-28 via user input*
