from playwright.sync_api import sync_playwright
import json
import time
from article_parser import extract_comments


PAGE_URL = "https://www.facebook.com/COIceconditions" # facebook URL to retrieve posts from
PROFILE_DIR = "./facebook_playwright_profile" # save facebook credentials
SCROLL_COUNT = 1 # number of times script will scroll down on facebook page


def main():
    with sync_playwright() as p:

        # LOAD PAGE -----------------------------------------------------------------------------------

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

        # LOG IN --------------------------------------------------------------------------------------

        print(
            "\nIf Facebook asks you to log in, log in manually in the browser.\n"
            "Once you can see the Colorado Ice Conditions page, return here."
        )

        # may want to return to using input instead of sleep to verify loading?
        # input("Press ENTER after the page is fully visible... ")
        time.sleep(5)

        # SCROLL & SAVE POSTS/COMMENTS/REPLIES --------------------------------------------------------

        comments = [] # stores main posts
        posts = [] # stores comments & replies

        # Scroll to load more posts
        for i in range(SCROLL_COUNT):
            print(f"Scroll {i + 1}/{SCROLL_COUNT}")
            page.mouse.wheel(0, 1800)
            time.sleep(3)

            # EXTRACT POSTS ---------------------------------------------------------------------------

            message_elements = page.locator(
                '[data-ad-preview="message"], [data-ad-comet-preview="message"]'
            )

            print(f"Found {message_elements.count()} possible post message elements")

            for j in range(message_elements.count()):
                message = message_elements.nth(j)

                try:
                    message_text = message.inner_text(timeout=3000).strip()
                except Exception:
                    continue

                links = message.locator("a")
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

                metadata = {
                    "type": "post",
                    "timestamp": None,
                    "post_url": None,
                    "comment_id": None,
                    "reply_comment_id": None,
                }

                # REPLACING THIS W/ JSON ******************
                print("\nPOSSIBLE POST MESSAGE:")
                print(message_text[:500])
                print("-" * 50)

                for link in link_info:
                    href = link.get("href") or ""

                    if "/COIceconditions/posts/" not in href:
                        continue

                    parsed = urlparse(href)
                    params = parse_qs(parsed.query)

                    print(params)

                    clean_post_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

                    if "reply_comment_id" in params:
                        metadata = {
                            "type": "reply",
                            "timestamp": link.get("aria_label"),
                            "post_url": clean_post_url,
                            "comment_id": params.get("comment_id", [None])[0],
                            "reply_comment_id": params.get("reply_comment_id", [None])[0],
                        }
                        break

                    elif "comment_id" in params:
                        metadata = {
                            "type": "comment",
                            "timestamp": link.get("aria_label"),
                            "post_url": clean_post_url,
                            "comment_id": params.get("comment_id", [None])[0],
                            "reply_comment_id": None,
                        }
                        break

                    else:
                        metadata = {
                            "type": "post",
                            "timestamp": link.get("aria_label"),
                            "post_url": clean_post_url,
                            "comment_id": None,
                            "reply_comment_id": None,
                        }
                        break

                posts.append({
                    "index": i,
                    "type": metadata["type"],
                    "timestamp": metadata["timestamp"],
                    "post_url": metadata["post_url"],
                    "text": message_text,
                    "links": link_info
                })


            # EXTRACT COMMENTS & REPLIES --------------------------------------------------------------

            articles = page.locator('[role="article"]')

            print(f"Found {articles.count()} article elements")

            comments = extract_comments(articles)

        # END OF SCROLL LOOPS -------------------------------------------------------------------------

        # SAVE FOUND TEXT TO JSON ---------------------------------------------------------------------
        with open("facebook_posts.json", "w", encoding="utf-8") as f:
                    json.dump(posts, f, indent=2, ensure_ascii=False)

        with open("facebook_comments&replies.json", "w", encoding="utf-8") as f:
            json.dump(comments, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(posts)} posts for inspection")

        print(f"Saved {len(comments)} comments & replies for inspection")

        # CLOSE BROWSER -------------------------------------------------------------------------------
        # may want to revert to user prompting browser closing in the future
        # input("Press ENTER to close the browser... ")
        context.close()

if __name__ == "__main__":
    main()
