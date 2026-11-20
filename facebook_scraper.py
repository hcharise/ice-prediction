from playwright.sync_api import sync_playwright
import json
from facebook_parser import extract_posts_and_comments

PAGE_URL = "https://www.facebook.com/COIceconditions" # facebook URL to retrieve posts from
PROFILE_DIR = "./facebook_playwright_profile" # save facebook credentials

def load_page(p):

    # Set playwright context
    context = p.chromium.launch_persistent_context(
        PROFILE_DIR,
        headless=False,
        viewport={"width": 1400, "height": 1000},
    )
    page = context.pages[0] if context.pages else context.new_page()

    # Open page
    print("Opening Facebook page...")
    page.goto(
        "https://www.facebook.com/COIceconditions",
        wait_until="domcontentloaded"
    )

    # Check whether Facebook is requesting login
    login_form = page.locator('#login_popup_cta_form')
    while login_form.is_visible():
        print(
            "\nFacebook requires login credentials.\n"
            "Log into the browswer manually, including completing any required CAPTCHAs.\n"
        )
        input("Once the Colorado Ice Conditions page is fully visible, return here and press ENTER.")

    # Wait for the feed to be ready
    page.locator(
        '[data-ad-preview="message"], [data-ad-comet-preview="message"]'
    ).first.wait_for(
        state="visible",
        timeout=5000
    )

    print("Facebook feed loaded. Starting extraction...")

    return page

def main():
    with sync_playwright() as p:

        page = load_page(p)

        try:
            # EXTRACT POSTS & COMMENTS ----------------------------------------------------------------
            posts = [] # stores main posts
            comments = [] # stores comments & replies
            posts, comments = extract_posts_and_comments(page)

            # SAVE POSTS & COMMENTS TO JSON -----------------------------------------------------------
            with open("facebook_posts.json", "w", encoding="utf-8") as f:
                json.dump(posts, f, indent=2, ensure_ascii=False)

            with open("facebook_comments.json", "w", encoding="utf-8") as f:
                json.dump(comments, f, indent=2, ensure_ascii=False)

            print(f"Saved {len(posts)} posts.")

            print(f"Saved {len(comments)} comments.")

        finally:
            # CLOSE BROWSER ----------------------------------------------------------------------------
            page.context.close()
            print("-----------------------------------------------------------------------------------")

if __name__ == "__main__":
    main()

