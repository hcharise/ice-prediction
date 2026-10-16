import re
from urllib.parse import urlparse, parse_qs

def extract_posts(page):
    SCROLL_MAX = 10 # max scrolls if no new posts are found
    POSTS_MAX = 20 # maximum number of posts to be retrieved (what ultimately ends the looping)
    posts = []
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
                candidate_text = candidate.inner_text(timeout=1000).strip()
                candidate_key = candidate_text[:100]

                # If next message_element candidate is new, exit search to extract post
                if candidate_key not in processed_keys:
                    next_message = candidate
                    next_key = candidate_key
                    break

            except Exception as e:
                print(f"Error inspecting candidate {j}: {e}")

        # EXTRACT POST TEXT & TIMESTAMP -------------------------------------------------------------------
        if next_message is not None:

            # Mark message as processed before changing the DOM when expanding
            processed_keys.add(next_key)

            # GET POST TEXT -------------------------------------------------------------------------------
            try:
                # Extract visible text from post
                text = next_message.inner_text(timeout=3000).strip()

                # Check if post has additional text, ie has a "See more" button
                if "See more" in text:
                    try:
                        next_message.get_by_role("button", name="See more").click(timeout=3000)
                        text = next_message.inner_text(timeout=3000).strip()
                        
                    except Exception as e:
                        print(f"Error expanding additional text from post {j}: {e}")

            except Exception as e:
                text = None
                print(f"Error extracting text from post {j}: {e}")

            # GET POST TIMESTAMP --------------------------------------------------------------------------
            try:
                # Locate timestamp link
                container = next_message.locator("xpath=../../../..")
                header = container.locator("xpath=./*").nth(1)
                timestamp_link = header.locator("a").nth(2)

                # Hover over the timestamp link to get tooltop
                timestamp_link.hover(timeout=3000)
                page.wait_for_timeout(1000)

                # Get timestamp from tooltip
                tooltips = page.locator('[role="tooltip"]')
                timestamp = tooltips.first.inner_text(timeout=1000).strip()
                # could add a layer of validation here - is what we got actually a date/time?

            except Exception as e: # eventually add specific error handling - playwright timeout?
                timestamp = None
                print(f"Error extracting timestamp from post {j}: {e}")

            # Write post info back to posts list
            posts.append({
                "type": "post",
                "timestamp": timestamp,
                "text": text,
            })

            # Reset scrolls to 0 to find new next post
            scroll_attempts = 0

        else:
            # Scroll down on page before repeating loop to see if new message_elements can be found
            page.mouse.wheel(0, 500)
            page.wait_for_timeout(500)

            scroll_attempts += 1

    return posts


def extract_comments(page):
    comments = []

    # Identify article elements ie comments and replies
    articles = page.locator('[role="article"]')
    print(f"Found {articles.count()} article elements")

    # Try extracting text and timestamp from each article
    for i in range(articles.count()):
        article = articles.nth(i)

        try:
            text = article.inner_text(timeout=1000).strip()
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