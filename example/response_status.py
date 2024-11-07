import asyncio

try:
    import nodriver as uc
except (ModuleNotFoundError, ImportError):
    import sys, os

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    import nodriver as uc


async def main():
    browser = await uc.start()
    # Get the browser main page/tab
    page = await browser.get()
    try:
        response, request = await page.goto("http://httpbin.org/ip", timeout=30)
        print(response.status)
        print(response.headers)
        content = await page.get_content()
        print(content)
    except Exception as e:
        print(e)
    await asyncio.sleep(2)
    browser.stop()


if __name__ == "__main__":
    uc.loop().run_until_complete(main())

