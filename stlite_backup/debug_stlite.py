import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        url = "https://haratoshi93.github.io/poker_helper-/"
        print(f"Navigating to {url} ...")
        
        # コンソールログをフックしてエラーを取得
        page.on("console", lambda msg: print(f"Console [{msg.type}]: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Page Error: {err.message}"))
        
        await page.goto(url)
        # stlite のロードを待つ (spinnerが消えて、メイン画面が出るまで)
        print("Waiting for app to load...")
        try:
            # stliteのローディングスピナーが消え、Streamlitの要素が現れるのを待つ
            await page.wait_for_selector(".stApp", timeout=30000)
            await page.wait_for_timeout(3000) # 少し安定するまで待つ
            
            # ページ内のテキストを少し取得して表示
            content = await page.locator(".stMarkdown").first.inner_text()
            print(f"\n[Success] App Loaded! First markdown text:\n{content}\n")
        except Exception as e:
            print(f"\n[Timeout or Error] Failed to find Streamlit element: {e}\n")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
