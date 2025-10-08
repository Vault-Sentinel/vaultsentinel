"""Script to run a single scan cycle."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.service import VaultSentinelService

async def main():
    """Run a single scan cycle."""
    print("Running VaultSentinel scan...")
    
    service = VaultSentinelService()
    
    try:
        results = await service.run_once()
        print(f"Scan completed successfully!")
        print(f"Results: {results}")
    except Exception as e:
        print(f"Scan failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import asyncio
    exit(asyncio.run(main()))
