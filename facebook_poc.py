from playwright.sync_api import sync_playwright
import json
import time

PAGE_URL = "https://www.facebook.com/COIceconditions"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page(
            viewport={"width": 1400, "height": 1000}
        )

        print("Opening Facebook page...")
        page.goto(
            PAGE_URL,
            wait_until="domcontentloaded",
            timeout=60_000
        )

        # Give the page time to render.
        time.sleep(5)

        # Scroll a few times to load additional posts.
        for i in range(5):
            print(f"Scroll {i + 1}/5")
            page.mouse.wheel(0, 2500)
            time.sleep(3)

        # Facebook commonly represents feed posts as article-like elements.
        articles = page.locator('[role="article"]')

        print(f"Found {articles.count()} article elements")

        posts = []

        for i in range(articles.count()):
            article = articles.nth(i)

            try:
                text = article.inner_text(timeout=3000).strip()
            except Exception:
                continue

            if not text:
                continue

            posts.append({
                "index": i,
                "text": text
            })

        with open("facebook_posts_poc.json", "w", encoding="utf-8") as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(posts)} items to facebook_posts_poc.json")

        # Keep browser open briefly so you can inspect what loaded.
        time.sleep(10)

        browser.close()


if __name__ == "__main__":
    main()
