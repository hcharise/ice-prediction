import re
from urllib.parse import urlparse, parse_qs


# come back to this once comments is working!!
# def extract_posts():

def extract_comments(articles):
    comments = []

    for i in range(articles.count()):
        article = articles.nth(i)

        try:
            text = article.inner_text(timeout=3000).strip()
        except Exception:
            continue

        if not text:
            continue

        links = article.locator("a")
        link_info = []

        for j in range(min(links.count(), 25)):
            link = links.nth(j)

            try:
                link_text = link.inner_text(timeout=1000).strip()
            except Exception:
                link_text = ""

            try:
                href = link.get_attribute("href")
            except Exception:
                href = None

            try:
                title = link.get_attribute("title")
            except Exception:
                title = None

            try:
                aria_label = link.get_attribute("aria-label")
            except Exception:
                aria_label = None

            # Keep links that look potentially useful:
            # timestamps, permalinks, comments, etc.
            if (
                re.fullmatch(r"\d+[smhdwy]", link_text)
                or "facebook.com" in (href or "")
                or title
                or aria_label
            ):
                link_info.append({
                    "text": link_text,
                    "href": href,
                    "title": title,
                    "aria_label": aria_label,
                })

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
                    "type": "post",
                    "timestamp": link.get("aria_label"),
                    "post_url": clean_post_url,
                    "comment_id": None,
                    "reply_comment_id": None,
                }
                break

        comments.append({
            "index": i,
            "type": metadata["type"],
            "timestamp": metadata["timestamp"],
            "post_url": metadata["post_url"],
            "comment_id": metadata["comment_id"],
            "reply_comment_id": metadata["reply_comment_id"],
            "text": text,
            "links": link_info
        })

    return comments


# def extract_links():



# def extract_metadata():


