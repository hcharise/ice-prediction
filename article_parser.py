import re
from urllib.parse import urlparse, parse_qs

def extract_posts_and_comments(page):
    SCROLL_MAX = 10 # max scrolls if no new posts are found
    POSTS_MAX = 6 # maximum number of posts to be retrieved (what ultimately ends the looping)
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
    while scroll_attempts < SCROLL_MAX and len(posts) < POSTS_MAX:

        # Search through message_elements currently in DOM, locating next one that has not been processed
        next_message, next_key = find_next_post(message_elements, found_post_keys)

        # EXTRACT POST TEXT & TIMESTAMP -------------------------------------------------------------------
        if next_message is not None:

            # Confirm that Playwright is on the correct post still
            # is this still necessary?
            next_message = message_elements.filter(has_text=next_key).first

            # Print processing/success/failed messages around handling post extraction
            post_index += 1
            print(f"Post {post_index}: Processing")
            if handle_post_extraction(next_message, page, posts, comments, post_index):
                print(f"Post {post_index}: Succeeded")
            else:
                print(f"Post {post_index}: FAILED")

            # may not be necessary?
            page.wait_for_timeout(1500)

            # Reset scrolls to 0 to find new next post
            scroll_attempts = 0

        else:
            # Scroll down on page before repeating loop to see if new message_elements can be found
            page.mouse.wheel(0, 500)
            page.wait_for_timeout(500)

            scroll_attempts += 1

    return posts, comments


def find_next_post(message_elements, found_post_keys):

    next_message = None
    next_key = None

    for j in range(message_elements.count()):
        try:
            # Get key from next message_element candidate
            candidate = message_elements.nth(j)
            candidate_key = candidate.inner_text(timeout=1000).strip()[:100]

            # If next message_element candidate is new, exit search to extract post
            if candidate_key not in found_post_keys:
                next_message = candidate
                next_key = candidate_key

                # Mark message as processed before changing the DOM when expanding
                found_post_keys.add(next_key)
                break

        except Exception as e:
            print(f"Error inspecting candidate {j}: {e}")

    return next_message, next_key


def handle_post_extraction(next_message, page, posts, comments, post_index):
    dialog_opened = False
    post_succeeded = False
    
    try:
        ## timestamp, opening
        timestamp = None
        timestamp_link = locate_post_timestamp_link(next_message)

        # Extract timestamp from tooltip
        try:
            timestamp = extract_post_timestamp(timestamp_link, page)
        except Exception as e:
            print(f"Error extracting TIMESTAMP from post: {e}")

        # Open dialog and update flag
        open_post_window(page, timestamp_link)
        dialog_opened = True

        # POST DETAILS
        try:
            post_details = extract_post_details(page, timestamp, post_index)
            posts.append(post_details)
            post_succeeded = True
        except Exception as e:
            print(f"Error extracting POST DETAILS from post: {e}")

        # COMMENT DETAILS
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
        if dialog_opened:
            try:
                close_post_window(page)
            except Exception as e:
                print(f"Error closing dialog: {e}")
                raise # future extractions may fail if this exception is ignored
    
    return post_succeeded


def extract_post_details(page, timestamp, post_index):

    # Initialize
    text = None
    url = None
    post_id = None

    # Extract url and text
    try:
        url = page.url
        text = extract_post_text(page)
        post_id = extract_post_id(url)

    except Exception as e:
        print(f"Error extracting TEXT/URL/ID from post: {e}")

    return {
        "type": "post",
        "post_index": str(post_index),
        "timestamp": timestamp,
        "post_id": post_id,
        "url": url,
        "text": text
    }


def locate_post_timestamp_link(message):

    container = message.locator("xpath=../../../..")
    header = container.locator("xpath=./*").nth(1)
    timestamp_link = header.locator("a").nth(2)

    return timestamp_link


def extract_post_timestamp(timestamp_link, page):
    # Hover over the timestamp link and get timestamp
    timestamp_link.hover(timeout=3000)
    page.wait_for_timeout(1000)
    tooltips = page.locator('[role="tooltip"]')
    timestamp = tooltips.first.inner_text(timeout=1000).strip()
    # could add a layer of validation here - is what we got actually a date/time?

    return timestamp


def open_post_window(page, timestamp_link):
    timestamp_link.click()
    page.wait_for_timeout(1500)

    
def close_post_window(page):
    page.go_back(timeout=5000)
    page.wait_for_timeout(1500)

    
def extract_post_text(page):

    # Extract text
    dialog = page.get_by_role("dialog")
    dialog_message = dialog.locator(
        '[data-ad-preview="message"], [data-ad-comet-preview="message"]'
    )
    text = dialog_message.inner_text(timeout=3000).strip()

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
    SCROLL_MAX = 10 # max scrolls if no new posts are found
    found_comment_keys = set() # stores keys from posts already processed to avoid duplication
    scroll_attempts = 0

    comments = []

    # Identify article elements ie comments and replies
    dialog = page.locator('[role="dialog"][aria-modal="true"]')
    articles = dialog.locator('[role="article"]')

    while scroll_attempts < SCROLL_MAX:

        # Try extracting text and timestamp from each article
        next_comment = find_next_comment(articles, found_comment_keys)

        if next_comment is not None:

            handle_comment_extraction(next_comment, comments, post_id)
            
            # Reset scroll attempts
            scroll_attempts = 0
        else:
            # Hover mouse on dialog box before scrolling
            dialog.hover()

            # Scroll down on page before repeating loop to see if new articles can be found
            page.mouse.wheel(0, 500)
            page.wait_for_timeout(500)

            scroll_attempts += 1

    return comments


def find_next_comment(articles, found_comment_keys):

    next_comment = None
    next_key = None

    # Search through visible comments
    for i in range(articles.count()):
        try:
       
            # Get next article element and its key
            candidate_article = articles.nth(i)
            candidate_key = candidate_article.inner_text(timeout=1000).strip()[:100]

            if not candidate_key:
                continue

            # Check if this article has already been found, if not, use it
            if candidate_key not in found_comment_keys:
                next_comment = candidate_article
                next_key = candidate_key

                # Mark comment as found
                found_comment_keys.add(next_key)

                break
        except Exception as e:
            print(f"Error finding next comment: {e}")

    return next_comment


def handle_comment_extraction(next_comment, comments, post_id):
    try:
        # Find section of article that contain actual comments
        comment_text = next_comment.locator('span[dir="auto"][lang="en"]')
        if comment_text.count() == 0:
            return

        # Extract comment text
        text = comment_text.first.inner_text(timeout=1000).strip()

        if not text:
            return

    except Exception as e:
        print(f"Error extracting comment text: {e}")
        return

    # Get details from comment
    comment_details = extract_comment_details(next_comment)

    try:
        comments.append({
            "type": "comment",
            "post_id": post_id,
            "timestamp": comment_details["timestamp"],
            "comment_id": comment_details["comment_id"],
            "text": text, ## string of text from inner_text of the article
        })
    except Exception as e:
        print(f"Error appending comments: {e}")

# Gets timestamp and comment ID from each comment
def extract_comment_details(article):

    # Identify link on comment that contains metadata (ie the timestamp)
    link = article.locator('a[href*="/COIceconditions/posts/"]').first

    # Get comment ID
    href = link.get_attribute("href")
    parsed = urlparse(href)
    params = parse_qs(parsed.query)

    metadata = {
        "timestamp": link.get_attribute("aria-label"),
        "comment_id": params.get("comment_id", [None])[0],
    }
    
    return metadata