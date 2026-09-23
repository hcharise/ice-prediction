from playwright.sync_api import sync_playwright
import json
import time
from article_parser import extract_comments, extract_posts


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

            # EXTRACT COMMENTS & REPLIES --------------------------------------------------------------
            #should move this line to parser eventually...
            message_elements = page.locator(
                '[data-ad-preview="message"], [data-ad-comet-preview="message"]'
            )

            print(f"Found {message_elements.count()} post elements")

            posts = extract_posts(message_elements)

            # EXTRACT COMMENTS & REPLIES --------------------------------------------------------------
            #should move this line to parser eventually...
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
        print("-----------------------------------------------------------------------------------------------")

if __name__ == "__main__":
    main()
