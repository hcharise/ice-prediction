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
                timestamp_link = locate_timestamp_link(next_message)
            
                # Extract timestamp from tooltip
                try:
                    timestamp = extract_timestamp(timestamp_link, page)
                except Exception as e:
                    print(f"Error extracting TIMESTAMP from post: {e}")
            
                # Flag if dialog box is opened
                dialog_opened = False

                # Open dialog and update flag
                open_dialog(page, timestamp_link)
                dialog_opened = True

                # POST DETAILS
                post_details = extract_post_details(page, next_message, timestamp)
                posts.append({
                    "type": "post",
                    "timestamp": post_details["timestamp"],
                    "url": post_details["url"],
                    "text": post_details["text"]
                })

                # COMMENT DETAILS
                post_comments = extract_comments(page) #, post_details["url"]
                comments.extend(post_comments)

            except Exception as e:
                print(f"Error extracting post: {e}")

            finally:
                # Close dialog if opened
                if dialog_opened:
                    try:
                        close_dialog(page)
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


def extract_post_details(page, message, timestamp):

    text = None
    url = None

    # Extract url and text
    try:
        url = page.url
        text = extract_post_text(page)
    except Exception as e:
        print(f"Error extracting TEXT/URL from post: {e}")

    return {
        "timestamp": timestamp,
        "url": url,
        "text": text
    }


def locate_timestamp_link(message):

    container = message.locator("xpath=../../../..")
    header = container.locator("xpath=./*").nth(1)
    timestamp_link = header.locator("a").nth(2)

    return timestamp_link


def extract_timestamp(timestamp_link, page):
    # Hover over the timestamp link and get timestamp
    timestamp_link.hover(timeout=3000)
    page.wait_for_timeout(1000)
    tooltips = page.locator('[role="tooltip"]')
    timestamp = tooltips.first.inner_text(timeout=1000).strip()
    # could add a layer of validation here - is what we got actually a date/time?

    return timestamp


def open_dialog(page, timestamp_link):
    timestamp_link.click()
    page.wait_for_timeout(1500)

    
def close_dialog(page):
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

def extract_comments(page):
    comments = []

    # Identify article elements ie comments and replies
    articles = page.locator('[role="article"]')
    print(f"Found {articles.count()} possible comments and replies (article elements).")

    # Try extracting text and timestamp from each article
    for i in range(articles.count()):
        article = articles.nth(i)

        try:
            text = article.inner_text(timeout=1000).strip()
            print(f"Text: {text[:10]}")
        except Exception:
            continue

        if not text:
            continue

        link_info = extract_links(article)
        metadata = extract_metadata(link_info)

        comments.append({
            "type": metadata["type"],
            "timestamp": metadata["timestamp"],
            "post_url": metadata["post_url"],
            "comment_id": metadata["comment_id"],
            "reply_comment_id": metadata["reply_comment_id"],
            "text": text,
            "links": link_info
        })

    ## NEED to add scrolling here to capture all posts
    return comments

def extract_links(article):

    links = article.locator("a")
    link_info = []

    for i in range(min(links.count(), 25)):
        link = links.nth(i)

        try:
            link_text = link.inner_text(timeout=1000).strip()
        except Exception:
            link_text = ""

        try:
            href = link.get_attribute("href")
        except Exception:
            href = None

        try:
            aria_label = link.get_attribute("aria-label")
        except Exception:
            aria_label = None


        if (
            re.fullmatch(r"\d+[smhdwy]", link_text)
            or "facebook.com" in (href or "")
            or aria_label
        ):
            link_info.append({
                "text": link_text,
                "href": href,
                "aria_label": aria_label,
            })
    
    return link_info

def extract_metadata(link_info):

    metadata = {
            "type": "unknown",
            "timestamp": None,
            "post_url": None,
            "comment_id": None,
            "reply_comment_id": None,
        }

    for link in link_info:
        href = link.get("href") or ""

        if "/COIceconditions/posts/" not in href:
            continue

        parsed = urlparse(href)
        params = parse_qs(parsed.query)

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
                "type": "unknown",
                "timestamp": link.get("aria_label"),
                "post_url": clean_post_url,
                "comment_id": None,
                "reply_comment_id": None,
            }
            break

    return metadata