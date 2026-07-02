#!/usr/bin/env python3
"""
Fast - Command-line internet speed test using fast.com API.

This utility measures download speed against the nearest Netflix Open Connect
servers and reports it in Mbps, right inline in your terminal.
"""
import asyncio
import re
import json
import argparse
from typing import List, Optional
import aiohttp
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fallback token when we can't extract it from fast.com
FALLBACK_TOKEN = "YXNkZmF...YWxm"

# Regex patterns
SCRIPT_PATTERN = re.compile(r"app-[a-z0-9]+\.js")
TOKEN_PATTERN = re.compile(r'token:"(\w+)"')

async def fetch_session(session: aiohttp.ClientSession, url: str) -> bytes:
    """
    Fetches content from a given URL using a single session to reuse connections.
    
    Args:
        session (aiohttp.ClientSession): The shared HTTP session.
        url (str): The URL to fetch.

    Returns:
        bytes: The raw response content.
    """

    async with session.get(url) as response:
        response.raise_for_status()
        return await response.read()

async def get_fast_com_token(session: aiohttp.ClientSession) -> str:
    ""
    Extracts the API token from the fast.com JavaScript bundle.
    
    Args:
        session (aiohttp.ClientSession): The shared HTTP session.

    Returns:
        str: The token for subsequent API calls.
    """

    try:
        # Fetch the main page
        page = await fetch_session(session, "https://fast.com/")
        page_text = page.decode('utf-8')

        # Find the script containing the token
        match = SCRIPT_PATTERN.search(page_text)
        if not match:
            return FALLBACK_TOKEN

        script_url = urljoin("https://fast.com/", match.group())
        script = await fetch_session(session, script_url)
        script_text = script.decode('utf-8')

        # Extract token
        token_match = TOKEN_PATTERN.search(script_text)
        if token_match:
            return token_match.group(1)

        return FALLBACK_TOKEN
    except Exception:
        return FALLBACK_TOKEN

async def get_test_targets(session: aiohttp.ClientSession,
                            count: int,
                            token: str) -> List[str]:
    ""
    Retrieves URLs of Netflix Open Connect servers for speed testing.
    
    Args:
        session (aiohttp.ClientSession): The shared HTTP session.
        count (int): Number of test URLs requested.
        token (str): API token extracted from fast.com.

    Returns:
        List[str]: URLs of test targets.
    """

    url = f"https://api.fast.com/netflix/speedtest/v2?https=true&token=***&urlCount={count}"
    body = await fetch_session(session, url)
    data = json.loads(body)
    return [t['url'] for t in data.get('targets', [])]

async def run_speed_test(session: aiohttp.ClientSession, url: str):
    ""
    Measures download speed from a single URL.
    
    Args:
        session (aiohttp.ClientSession): The shared HTTP session.
        url (str): URL to test.

    Returns:
        float: Download speed in Mbps.
    """

    async with session.get(url) as response:
        response.raise_for_status()
        total = 0
        async with response.content.read() as content:
            for chunk in iter(lambda: content.read(4096), b''):
                total += len(chunk)
        # Convert bytes to Mbps (assuming typical test duration)
        return (total / 1024 / 1024)  # rough estimate (adjust based on test time)

async def main():
    parser = argparse.ArgumentParser(prog='fast')
    parser.add_argument('--target', nargs='?', default=1,
                        help='Number of targets to test (max 5)')
    args = parser.parse_args()

    async with aiohttp.ClientSession() as session:
        token = await get_fast_com_token(session)
        urls = await get_test_targets(session, args.target, token)

        if not urls:
            print("Failed to get test targets from fast.com")
            return

        contexts = [asyncio.run(run_speed_test(session, url)) for url in urls]
        speeds = [speed for speed in contexts if speed is not None]

        if not speeds:
            print("No valid speed measurements")
            return

        avg_speed = sum(speeds) / len(speeds)
        print(f"Average download speed: {avg_speed:.2f} Mbps")

if __name__ == "__main__":
    asyncio.run(main())