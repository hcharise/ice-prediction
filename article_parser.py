import re
from urllib.parse import urlparse, parse_qs

def extract_posts(page):

    posts = []

    # Identify message elements ie post elements
    message_elements = page.locator(
        '[data-ad-preview="message"], [data-ad-comet-preview="message"]'
    )
    print(f"Found {message_elements.count()} post elements")
    
    for i in range(message_elements.count()):
        message = message_elements.nth(i)

        print(f"\n========== POST {i} ==========")

        # Get message text
        try:
            text = message.inner_text().strip()

            # Identify posts that are cut off, ie have a "See more"
            if "See more" in text:
                print("FOUND A SEE MORE")

            # Find timestamp link
            container = message.locator("xpath=../../../..")
            header = container.locator("xpath=./*").nth(1)
            timestamp_link = header.locator("a").nth(2)

            # Hover over the date to get tooltop
            timestamp_link.hover()
            print("TEXT:", text[:500])

        except Exception as e:
            text = None
            print(f"Error extracting text from post {i}: {e}")

        try:
            # Inspect the suspected timestamp link
            container = message.locator("xpath=../../../..")
            header = container.locator("xpath=./*").nth(1)
            timestamp_link = header.locator("a").nth(2)

            # Hover over the date to get tooltop
            timestamp_link.hover()
            page.wait_for_timeout(1000)

            # Get timestamp from tooltip
            tooltips = page.locator('[role="tooltip"]')
            timestamp = tooltips.first.inner_text(timeout=1000).strip()
            print("TIMESTAMP:", timestamp)
            # could add a layer of validation here - is what we got actually a date/time?
        except Exception as e: # eventually add specific error handling - playwright timeout?
            timestamp = None
            print(f"Error extracting timestamp from post {i}: {e}")

        # Write post info back to posts list
        posts.append({
            "type": "post",
            "timestamp": timestamp,
            "text": text,
        })

    return posts


def extract_comments(page):
    comments = []

    # Identify article elements ie comments and replies
    articles = page.locator('[role="article"]')
    print(f"Found {articles.count()} article elements")
    
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