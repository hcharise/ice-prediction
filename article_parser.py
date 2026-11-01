import re
from urllib.parse import urlparse, parse_qs

def extract_posts_and_comments(page):
    SCROLL_MAX = 10 # max scrolls if no new posts are found
    POSTS_MAX = 1 # maximum number of posts to be retrieved (what ultimately ends the looping)
    posts = []
    comments = []
    processed_keys = set() # stores keys from posts already processed to avoid duplication
    scroll_attempts = 0
    
    # Identify initial set of message elements ie post elements
    message_elements = page.locator(
        '[data-ad-preview="message"], [data-ad-comet-preview="message"]'
    )

    # Scroll through posts, extracting text and date from each
    while scroll_attempts < SCROLL_MAX and len(posts) < POSTS_MAX:

        # LOCATE NEXT POST --------------------------------------------------------------------------------
        next_message = None
        next_key = None

        # Search through message_elements currently in DOM, locating next one that has not been processed
        for j in range(message_elements.count()):
            try:
                # Get key from next message_element candidate
                candidate = message_elements.nth(j)
                candidate_key = candidate.inner_text(timeout=1000).strip()[:100]

                # If next message_element candidate is new, exit search to extract post
                if candidate_key not in processed_keys:
                    next_message = candidate
                    next_key = candidate_key
                    break

            except Exception as e:
                print(f"Error inspecting candidate {j}: {e}")

        # EXTRACT POST TEXT & TIMESTAMP -------------------------------------------------------------------
        if next_message is not None:
            try:

                # Mark message as processed before changing the DOM when expanding
                processed_keys.add(next_key)

                # Confirm that Playwright is on the correct post still
                next_message = message_elements.filter(has_text=next_key).first

                ## timestamp, opening
                timestamp = None
                timestamp_link = locate_post_timestamp_link(next_message)
            
                # Extract timestamp from tooltip
                try:
                    timestamp = extract_post_timestamp(timestamp_link, page)
                except Exception as e:
                    print(f"Error extracting TIMESTAMP from post: {e}")
            
                # Flag if dialog box is opened
                dialog_opened = False

                # Open dialog and update flag
                open_post_window(page, timestamp_link)
                dialog_opened = True

                # POST DETAILS
                post_details = extract_post_details(page, timestamp)
                posts.append({
                    "type": "post",
                    "timestamp": post_details["timestamp"],
                    "post_id": post_details["post_id"],
                    "url": post_details["url"],
                    "text": post_details["text"]
                })

                # COMMENT DETAILS
                post_comments = extract_comments(page, post_details["url"])
                comments.extend(post_comments)

            except Exception as e:
                print(f"Error extracting post: {e}")

            finally:
                # Close dialog if opened
                if dialog_opened:
                    try:
                        close_post_window(page)
                    except Exception as e:
                        print(f"Error closing dialog: {e}")
                        raise

            page.wait_for_timeout(1500)

            # Reset scrolls to 0 to find new next post
            scroll_attempts = 0

        else:
            # Scroll down on page before repeating loop to see if new message_elements can be found
            page.mouse.wheel(0, 500)
            page.wait_for_timeout(500)

            scroll_attempts += 1

    return posts, comments

def extract_post_details(page, timestamp):

    text = None
    url = None

    # Extract url and text
    try:
        url = page.url
        text = extract_post_text(page)
        post_id = extract_post_id(url)

    except Exception as e:
        print(f"Error extracting TEXT/URL/ID from post: {e}")

    return {
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
    page.go_back()
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


def extract_comments(page, post_url):
    comments = []

    # Identify article elements ie comments and replies
    articles = page.locator('[role="article"]')
    print(f"Found {articles.count()} possible comments and replies (article elements).")

    # Try extracting text and timestamp from each article
    for i in range(articles.count()):
        article = articles.nth(i)

        try:
            # Find article elements that contain actual comments
            possible_comments = article.locator('span[dir="auto"][lang="en"]')
            if possible_comments.count() == 0:
                continue

            # Extract comment text
            text = possible_comments.first.inner_text(timeout=1000).strip()

            if not text:
                continue

        except Exception as e:
            print(f"Error extracting comment text: {e}")
            continue

        # get metadata from links
        comment_details = extract_comment_details(article)

        try:
            comments.append({
                "type": "comment",
                "post_url": post_url,
                "timestamp": comment_details["timestamp"],
                "comment_id": comment_details["comment_id"],
                "text": text, ## string of text from inner_text of the article
            })
        except Exception as e:
            print(f"Error appending comments: {e}")

    ## NEED to add scrolling here/somewhere to capture all posts
    return comments

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