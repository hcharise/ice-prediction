from playwright.sync_api import sync_playwright
import json
import time
from article_parser import extract_comments, extract_posts

PAGE_URL = "https://www.facebook.com/COIceconditions" # facebook URL to retrieve posts from
PROFILE_DIR = "./facebook_playwright_profile" # save facebook credentials
SCROLL_COUNT = 1 # number of times script will scroll down on facebook page

def load_page(p):

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

    # Log into Facebook
    print(
        "\nIf Facebook asks you to log in, log in manually in the browser.\n"
        "Once you can see the Colorado Ice Conditions page, return here."
    )
    # may want to return to using input instead of sleep to verify loading?
    # input("Press ENTER after the page is fully visible... ")
    time.sleep(5)

    return page, context

def main():
    with sync_playwright() as p:

        page, context = load_page(p)

        # EXTRACT POSTS & COMMENTS/REPLIES ----------------------------------------------------------------
        posts = [] # stores main posts
        posts = extract_posts(page)

        comments = [] # stores comments & replies
        comments = extract_comments(page)

        # Save found posts/comments/replies to JSON
        with open("facebook_posts.json", "w", encoding="utf-8") as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)

        with open("facebook_comments&replies.json", "w", encoding="utf-8") as f:
            json.dump(comments, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(posts)} posts for inspection")

        print(f"Saved {len(comments)} comments & replies for inspection")

        # CLOSE BROWSER -----------------------------------------------------------------------------------
        # may want to revert to user prompting browser closing in the future
        # input("Press ENTER to close the browser... ")
        context.close()
        print("-----------------------------------------------------------------------------------------------")

if __name__ == "__main__":
    main()

