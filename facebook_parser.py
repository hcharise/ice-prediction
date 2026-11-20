from urllib.parse import urlparse, parse_qs
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

POSTS_MAX = 3 # maximum number of posts to be retrieved (what ultimately ends the looping)
SCROLL_MAX = 8 # max scrolls if no new posts/comments are found
KEY_CHAR_LENGTH = 100 # num characters in keys
SCROLL_DIST = 500 # distance to travel down when scrolling

SCROLL_WAIT_MS = 200 # ms to wait after scrolling
LOAD_TIMEOUT_MS = 5000 # ms to wait after clicking/hovering
TEXT_TIMEOUT_MS = 1000 # ms to wait for value extraction

def extract_posts_and_comments(page):
    posts = []
    comments = []
    found_post_keys = set() # stores keys from posts already found to avoid duplication
    scroll_attempts = 0
    post_index = 0
    
    # Identify initial set of message elements ie post elements
    message_elements = page.locator(
        '[data-ad-preview="message"], [data-ad-comet-preview="message"]'
    )

    # Scroll through posts, extracting text and date from each
    while scroll_attempts < SCROLL_MAX and post_index < POSTS_MAX:

        # Search through message_elements currently in DOM, locating next one that has not been processed
        next_post_element = find_next_post(message_elements, found_post_keys)

        # Once next post is identified, extract post text and timestamp
        if next_post_element is not None:

            # Extract post/comment details
            post_index += 1
            result = handle_post_extraction(next_post_element, page, posts, comments, post_index)
            
            # Print processing/success/failed messages around handling post extraction
            if result is True:
                print(f"Post {post_index}: Succeeded")
            elif result is False:
                print(f"Post {post_index}: Failed")
            else:
                print(f"Post {post_index}: Skipped")

            # Reset scrolls to 0 to find new next post
            scroll_attempts = 0

        else:
            # Scroll down on page before repeating loop to see if new message_elements can be found
            page.mouse.wheel(0, SCROLL_DIST)
            page.wait_for_timeout(SCROLL_WAIT_MS)

            scroll_attempts += 1

    return posts, comments


def find_next_post(message_elements, found_post_keys):

    next_post_element = None
    next_key = None

    # Search through messages currently visible
    for j in range(message_elements.count()):
        try:
            # Get key from next message_element candidate
            candidate = message_elements.nth(j)
            candidate_key = candidate.inner_text(timeout=TEXT_TIMEOUT_MS).strip()[:KEY_CHAR_LENGTH]

            # If next message_element candidate is new, exit search to extract post
            if candidate_key not in found_post_keys:
                next_post_element = candidate
                next_key = candidate_key

                # Mark message as processed before changing the DOM when expanding
                found_post_keys.add(next_key)
                break

        except PlaywrightTimeoutError as e:
            print(f"Timed out inspecting comment {j}: {e}")

    return next_post_element


def handle_post_extraction(next_post_element, page, posts, comments, post_index):
    original_url = page.url
    post_succeeded = False

    try:
        # Identify timestamp link
        timestamp_link = locate_post_timestamp_link(next_post_element)

        # TIMESTAMP - extract timestamp from link
        timestamp = None
        try:
            timestamp = extract_post_timestamp(timestamp_link, page)
        except Exception as e:
            print(f"Error extracting TIMESTAMP from post: {e}")

        # Open dialog box of post
        open_post_window(page, timestamp_link)

        # Skip reels or reposts with different urls
        if not page.url.startswith("https://www.facebook.com/COIceconditions/posts/"):
            print(f"Skipping unsupported post: {page.url}")
            return None

        # Wait for dialog to load fully
        page.locator('[role="dialog"][aria-modal="true"]').wait_for(
            state="visible",
            timeout=LOAD_TIMEOUT_MS
        )

        # POST DETAILS - extract post details
        try:
            post_details = extract_post_details(page, timestamp, post_index)
            posts.append(post_details)
            post_succeeded = True
        except Exception as e:
            print(f"Error extracting POST DETAILS from post: {e}")

        # COMMENT DETAILS - extract comment details
        if post_succeeded:
            try:
                post_comments = extract_comments(page, post_details["post_id"])
                comments.extend(post_comments)
            except Exception as e:
                print(f"Error extracting COMMENT DETAILS from post: {e}")

    except Exception as e:
        print(f"Error extracting post: {e}")

    finally:
        # Close dialog if opened
        if page.url != original_url:
            try:
                close_post_window(page, original_url)
            except Exception as e:
                print(f"Error restoring feed: {e}")
                raise
    
    return post_succeeded


def extract_post_details(page, timestamp, post_index):

    # Extract url, id, and text
    url = page.url
    post_id = extract_post_id(url)
    text = extract_post_text(page)

    # Raise exception if post_id or text are blank
    if not post_id or not text:
        raise ValueError("Post is missing its ID or text")

    return {
        "type": "post",
        "post_index": post_index,
        "post_id": post_id,
        "timestamp": timestamp,
        "url": url,
        "text": text,
    }


def locate_post_timestamp_link(message):

    # Identify timestamp link from post
    container = message.locator("xpath=../../../..")
    header = container.locator("xpath=./*").nth(1)
    timestamp_link = header.locator("a").nth(2)

    return timestamp_link


def extract_post_timestamp(timestamp_link, page):
    # Hover over the timestamp link
    timestamp_link.hover(timeout=LOAD_TIMEOUT_MS)

    # Ensure timestamp has loaded
    page.locator('[role="tooltip"]').wait_for(
        state="visible",
        timeout=LOAD_TIMEOUT_MS
    )

    # Extract timestamp text
    tooltips = page.locator('[role="tooltip"]')
    timestamp = tooltips.first.inner_text(timeout=TEXT_TIMEOUT_MS).strip()

    return timestamp


def open_post_window(page, timestamp_link):
    original_url = page.url

    # Click to open post dialog box
    timestamp_link.click()

    # Wait for new page to load
    page.wait_for_url(
        lambda url: str(url) != original_url,
        timeout=LOAD_TIMEOUT_MS
    )

    
def close_post_window(page, original_url):

    # Go back and wait for page to load
    page.go_back(timeout=LOAD_TIMEOUT_MS)
    page.wait_for_url(original_url, timeout=LOAD_TIMEOUT_MS)

    
def extract_post_text(page):

    # Locate post text
    dialog = page.get_by_role("dialog")
    dialog_message = dialog.locator(
        '[data-ad-preview="message"], [data-ad-comet-preview="message"]'
    )

    # Extract text
    text = dialog_message.inner_text(timeout=LOAD_TIMEOUT_MS).strip()

    return text


def extract_post_id(url):

    # Parse URL
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")

    post_id = None

    # Confirm that post is post, ie has post_id
    if len(path_parts) >= 3 and path_parts[-2] == "posts":
        post_id = path_parts[-1]

    return post_id


def extract_comments(page, post_id):
    found_comment_keys = set() # stores keys from posts already processed to avoid duplication
    scroll_attempts = 0

    comments = []

    # Identify article elements, ie comments
    dialog = page.locator('[role="dialog"][aria-modal="true"]')
    comment_elements = dialog.locator('[role="article"]')

    while scroll_attempts < SCROLL_MAX:

        # Try extracting text and timestamp from each comment
        next_comment = find_next_comment(comment_elements, found_comment_keys)

        if next_comment is not None:
            handle_comment_extraction(next_comment, comments, post_id)
            
            # Reset scroll attempts
            scroll_attempts = 0
        else:
            # Hover mouse on dialog box before scrolling
            dialog.hover()

            # Scroll down on page before repeating loop to see if new comment_elements can be found
            page.mouse.wheel(0, SCROLL_DIST)
            page.wait_for_timeout(SCROLL_WAIT_MS)

            scroll_attempts += 1

    return comments


def find_next_comment(comment_elements, found_comment_keys):

    next_comment = None
    next_key = None

    # Search through visible comments
    for i in range(comment_elements.count()):
        try:
       
            # Get next comment element and its key
            candidate_comment = comment_elements.nth(i)
            candidate_key = candidate_comment.inner_text(timeout=TEXT_TIMEOUT_MS).strip()[:KEY_CHAR_LENGTH]

            if not candidate_key:
                continue

            # Check if this comment has already been found, if not, use it
            if candidate_key not in found_comment_keys:
                next_comment = candidate_comment
                next_key = candidate_key

                # Mark comment as found
                found_comment_keys.add(next_key)

                break

        except PlaywrightTimeoutError as e:
            print(f"Timed out inspecting comment {i}: {e}")

    return next_comment


def handle_comment_extraction(next_comment, comments, post_id):
    try:
        # Find section of article that contains actual comments
        comment_text = next_comment.locator('span[dir="auto"][lang="en"]')
        if comment_text.count() == 0:
            return

        # Extract comment text
        text = comment_text.first.inner_text(timeout=TEXT_TIMEOUT_MS).strip()

        if not text:
            return

        # Get details from comment
        comment_details = extract_comment_details(next_comment)

    except Exception as e:
        print(f"Error extracting comment details: {e}")
        return

    comments.append({
        "type": "comment",
        "post_id": post_id,
        "timestamp": comment_details["timestamp"],
        "comment_id": comment_details["comment_id"],
        "text": text, ## string of text from inner_text of the comment
    })


def extract_comment_details(comment):

    # Identify link on comment that contains metadata (ie the timestamp)
    link = comment.locator('a[href*="/COIceconditions/posts/"]').first

    # Get comment ID
    href = link.get_attribute("href", timeout=TEXT_TIMEOUT_MS)
    parsed = urlparse(href)
    params = parse_qs(parsed.query)
    
    return {
        "timestamp": link.get_attribute("aria-label", timeout=TEXT_TIMEOUT_MS),
        "comment_id": params.get("comment_id", [None])[0],
    }