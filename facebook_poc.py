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

        import re

        # Scroll a few times to load additional posts.
        for i in range(20):
            print(f"Scroll {i + 1}/20")
            page.mouse.wheel(0, 1800)
            time.sleep(3)

            articles = page.locator('[role="article"]')

            print(f"Found {articles.count()} article elements")

            items = []

            for i in range(articles.count()):
                article = articles.nth(i)

                try:
                    text = article.inner_text(timeout=3000).strip()
                except Exception:
                    continue

                # A comment/reply is often an <article> nested inside the
                # top-level post's <article>.
                is_nested = article.evaluate("""
                    el => {
                        const parent = el.parentElement;
                        return parent ? !!parent.closest('[role="article"]') : false;
                    }
                """)

                links = article.locator("a")
                link_info = []

                for j in range(min(links.count(), 25)):
                    link = links.nth(j)

                    try:
                        link_text = link.inner_text(timeout=1000).strip()
                    except Exception:
                        link_text = ""

                    try:
                        href = link.get_attribute("href")
                    except Exception:
                        href = None

                    try:
                        title = link.get_attribute("title")
                    except Exception:
                        title = None

                    try:
                        aria_label = link.get_attribute("aria-label")
                    except Exception:
                        aria_label = None

                    # Keep links that look potentially useful:
                    # timestamps, permalinks, comments, etc.
                    if (
                        re.fullmatch(r"\d+[smhdwy]", link_text)
                        or "facebook.com" in (href or "")
                        or title
                        or aria_label
                    ):
                        link_info.append({
                            "text": link_text,
                            "href": href,
                            "title": title,
                            "aria_label": aria_label,
                        })

                items.append({
                    "index": i,
                    "is_nested_article": is_nested,
                    "text": text,
                    "links": link_info,
                })

        with open("facebook_debug_articles.json", "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(items)} articles for inspection")

        input("Press ENTER to close the browser... ")
        context.close()


if __name__ == "__main__":
    main()
