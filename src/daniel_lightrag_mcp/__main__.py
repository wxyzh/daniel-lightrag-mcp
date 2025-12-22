#!/usr/bin/env python3
"""
Main entry point for daniel-lightrag-mcp package.
"""

import asyncio
from .cli import cli

if __name__ == "__main__":
    asyncio.run(cli())
