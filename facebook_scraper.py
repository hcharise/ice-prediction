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
            timeout=6000
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

        posts = [] # stores main posts
        comments = [] # stores comments & replies

        # Scroll to load more posts
        # I THINK THIS IS NOT NECESSARY IF SCROLLING WILL HAPPEN AFTER EXPANDING EACH POST? but what about posts that don't expand...?
        for i in range(SCROLL_COUNT):
            print(f"Scroll {i + 1}/{SCROLL_COUNT}")
            page.mouse.wheel(0, 1800)
            time.sleep(3)

            '''
            # Expand any posts with additional text, ie "See more"
            try:
                page.get_by_role("button", name="See more").click()
                print(f"Expanded a see more in scroll {i}")
            except Exception as e:
                print(f"Was not able to expand a see more on the PAGE - {e}")
            '''

            # EXTRACT POSTS & COMMENTS/REPLIES --------------------------------------------------------  
            posts = extract_posts(page)
            comments = extract_comments(page)

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
