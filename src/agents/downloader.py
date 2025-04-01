import asyncio
from playwright.async_api import async_playwright
import os
from src.common.file import getFileName, writeFile, getFile, deleteFile


async def download_agent(state):
    # Get the URL-source pairs for the current batch
    all_sources = state["source_urls"]  # This is a list, not a dictionary
    start_idx = state["current_batch"] * state["batch_size"]
    end_idx = min(start_idx + state["batch_size"], len(all_sources))

    if start_idx >= len(all_sources):
        return state

    batch_sources = all_sources[start_idx:end_idx]

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome")
        tasks = [
            # Assuming each item in the list is a URL string
            # Using the URL itself as the source identifier
            fetch_page(browser, url, url)
            for url in batch_sources
        ]
        results = await asyncio.gather(*tasks)
        await browser.close()

    # Convert results to a dictionary with source keys
    state["raw_content"] = {source: (url, content) for source, url, content in results}
    store_content(state["raw_content"], state["current_batch"])
    state["current_batch"] += 1
    return state


async def fetch_page(browser, source: str, url: str) -> tuple[str, str, str]:
    page = await browser.new_page()
    try:
        await page.goto(url, timeout=30000)
        content = await page.content()
    except Exception as e:
        content = f"Error: {str(e)}"
    await page.close()
    return source, url, content


def store_content(content_dict: dict, batch_number: int) -> None:
    # Create base directory for downloaded content
    base_dir = os.path.join("downloads", f"batch_{batch_number}")

    # Store each URL's content in a separate file using source as key
    for source, (url, content) in content_dict.items():
        # Use the source as the key for the filename
        filename = getFileName(f"{source}_")
        file_path = os.path.join(base_dir, filename)

        # Store the URL along with its content for reference
        data_to_store = f"Source: {source}\nURL: {url}\n\n{content}"
        writeFile(file_path, data_to_store)
