"""Daily batch script for Titan Terminal.

Run this at 8:30 AM local time (or whenever you want) to generate the morning report.
Can be scheduled via cron or run manually.

Usage:
    python -m src.backend.batch

Or with specific symbols:
    python -m src.backend.batch BTC ETH SOL
"""
import sys
import json
from datetime import datetime
from pathlib import Path

from .agents import Orchestrator
from .tools.market_data import get_market_data_fetcher
from .db import init_db
from .config.constants import HYPERLIQUID_PERPS


def run_batch(symbols: list = None) -> dict:
    """Run the morning batch analysis."""

    print(f"\n{'='*60}")
    print(f"TITAN TERMINAL - MORNING BATCH")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # Initialize database
    init_db()

    # Use default symbols if none provided
    if not symbols:
        symbols = HYPERLIQUID_PERPS[:10]  # Top 10 for MVP

    print(f"Analyzing {len(symbols)} symbols: {', '.join(symbols)}\n")

    # Initialize orchestrator and data fetcher
    orchestrator = Orchestrator()
    fetcher = get_market_data_fetcher()

    # Run the batch
    try:
        results = orchestrator.run_morning_batch(
            symbols=symbols,
            market_data_fetcher=fetcher.fetch
        )

        # Print summary
        print(f"\n{'='*60}")
        print("RESULTS SUMMARY")
        print(f"{'='*60}\n")

        for i, signal in enumerate(results[:10], 1):  # Top 10
            if signal.get('error'):
                print(f"{i}. {signal['symbol']}: ERROR - {signal['error']}")
                continue

            action = signal.get('suggested_action', 'Avoid')
            confidence = signal.get('confidence', 0)
            acc_score = signal.get('accumulation_score', 0)
            dist_score = signal.get('distribution_score', 0)
            mentor = signal.get('mentor_verdict', 'N/A')

            score_display = f"Acc:{acc_score}" if acc_score > dist_score else f"Dist:{dist_score}"

            print(f"{i}. {signal['symbol']:8s} | {action:18s} | {score_display:10s} | "
                  f"Conf:{confidence:3d}% | Mentor:{mentor}")

            if signal.get('entry_zone'):
                entry = signal['entry_zone']
                print(f"   Entry: {entry.get('low', 'N/A'):.2f}-{entry.get('high', 'N/A'):.2f} | "
                      f"Stop: {signal.get('stop_loss', 'N/A')} | "
                      f"TP1: {signal.get('tp1', 'N/A')} | "
                      f"R:R: {signal.get('risk_reward', 'N/A')}")

        print(f"\n{'='*60}")
        print(f"Batch complete. {len(results)} signals generated.")
        print(f"All signals saved to SignalJournal for self-learning.")
        print(f"{'='*60}\n")

        # Save JSON output
        output_path = Path(__file__).parent / "output" / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'symbols_analyzed': len(symbols),
                'signals': results
            }, f, indent=2, default=str)

        print(f"JSON output saved to: {output_path}")

        return {
            'success': True,
            'signals': results,
            'output_path': str(output_path)
        }

    except Exception as e:
        print(f"\nERROR: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        fetcher.close()


def main():
    """Entry point for batch script."""
    # Get symbols from command line args if provided
    symbols = sys.argv[1:] if len(sys.argv) > 1 else None

    result = run_batch(symbols)

    if not result['success']:
        sys.exit(1)


if __name__ == "__main__":
    main()
