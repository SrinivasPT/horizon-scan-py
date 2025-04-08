import asyncio

from playwright.async_api import async_playwright

from agents.download.federal_register_url import get_federal_register_urls
from common.file import writeFile


async def download_agent(state):
    # Get the scan config items for the current batch
    all_config_items = state["scan_config"]
    start_idx = state["current_batch"] * state["batch_size"]
    end_idx = min(start_idx + state["batch_size"], len(all_config_items))

    if start_idx >= len(all_config_items):
        return state

    batch_items = all_config_items[start_idx:end_idx]

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome")
        tasks = [fetch_page(browser, item["source"], item["url"]) for item in batch_items]
        # Process Federal Register separately to expand its URLs
        modified_tasks = []
        for item in batch_items:
            if item["source"] == "FEDERAL-REGISTER":
                # Get all URLs for Federal Register
                fr_urls = get_federal_register_urls()
                # Add a task for each URL with a numbered source
                for idx, fr_url in enumerate(fr_urls, 1):
                    modified_tasks.append(fetch_page(browser, f"FEDERAL-REGISTER-{idx}", fr_url))
            else:
                # For regular sources, add task as normal
                modified_tasks.append(fetch_page(browser, item["source"], item["url"]))
        tasks = modified_tasks
        results = await asyncio.gather(*tasks)
        await browser.close()

    # Convert results to a dictionary with source keys
    state["raw_content"] = {source: (url, content, content_type) for source, url, content, content_type in results}
    store_content(state["raw_content"])
    state["current_batch"] += 1
    return state


async def fetch_page(browser, source: str, url: str) -> tuple[str, str, str, str]:
    page = await browser.new_page()
    content_type = "htm"
    try:
        response = await page.goto(url, timeout=30000)
        content_type_header = response.headers.get("content-type", "").lower()

        if any(ct in content_type_header for ct in ["application/rss+xml", "application/xml", "text/xml"]):
            content = await response.text()
            content_type = "xml"
        elif any(ct in content_type_header for ct in ["application/json"]):
            content = await response.text()
            content_type = "json"
        else:
            content = await page.evaluate("() => document.documentElement.outerHTML")
            content_type = "htm"

    except Exception as e:
        content = f"Error: {str(e)}"
    await page.close()
    return source, url, content, content_type


def store_content(content_dict: dict) -> None:
    # Store each URL's content in a separate file using source as key
    for source, (url, content, content_type) in content_dict.items():
        writeFile(source, content, content_type)
