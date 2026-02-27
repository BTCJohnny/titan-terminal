"""Trading constants for Titan Terminal.

These are static values that don't change based on environment.
For environment-dependent configuration, use settings.py instead.
"""

# Trading universe - Hyperliquid perpetuals
HYPERLIQUID_PERPS = [
    "BTC", "ETH", "SOL", "AVAX", "ARB", "OP", "MATIC", "LINK",
    "DOGE", "PEPE", "WIF", "BONK", "JUP", "TIA", "SEI", "SUI",
    "INJ", "FET", "RENDER", "TAO"
]

# Risk management (The 3 Laws)
MAX_RISK_PER_TRADE = 0.02  # 2% max risk per trade
MIN_RISK_REWARD = 2.0      # Minimum 2:1 risk-reward ratio
MAX_POSITIONS = 5          # Maximum concurrent positions

# Batch settings (could also come from env if needed later)
MORNING_BATCH_HOUR = 8
MORNING_BATCH_MINUTE = 30
REFRESH_INTERVAL_MINUTES = 15
