from playwright.sync_api import sync_playwright
import json
import time

PAGE_URL = "https://www.facebook.com/COIceconditions"
PROFILE_DIR = "./facebook_playwright_profile"


def main():
    with sync_playwright() as p:

        # LOAD PAGE

        context = p.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=False,
            viewport={"width": 1400, "height": 1000},
        )

        page = context.pages[0] if context.pages else context.new_page()

        print("Opening Facebook page...")
        page.goto(
            PAGE_URL,
            wait_until="domcontentloaded",
            timeout=60_000
        )

        # LOG IN

        print(
            "\nIf Facebook asks you to log in, log in manually in the browser.\n"
            "Once you can see the Colorado Ice Conditions page, return here."
        )

        input("Press ENTER after the page is fully visible... ")

        # SCROLL & SAVE POSTS

        # Scroll a few times to load additional posts.
        for i in range(20):
            print(f"Scroll {i + 1}/20")
            page.mouse.wheel(0, 1800)
            time.sleep(3)

        # Facebook commonly represents feed posts as article-like elements.
        articles = page.locator('[role="article"]')

        print(f"Found {articles.count()} article elements")

        posts = []

        # ADD POSTS TO JSON

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


        # CLOSE OUT

        print(f"Saved {len(posts)} likely posts")

        input("Press ENTER to close the browser... ")
        context.close()


if __name__ == "__main__":
    main()
