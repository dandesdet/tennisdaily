"""Generate static share pages from index.html. Requires Pillow for JPEG previews."""

import json
import re
from dataclasses import dataclass, field
from html import escape
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://tennisdaily.uz/"


@dataclass
class Post:
    id: str
    titles: list = field(default_factory=list)
    descriptions: list = field(default_factory=list)
    images: list = field(default_factory=list)


class PostParser(HTMLParser):
    void = set("area base br col embed hr img input link meta param source track wbr".split())

    def __init__(self):
        super().__init__()
        self.posts = {}
        self.stack = []
        self.post = None
        self.depth = 0
        self.capture = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        post_id = attrs.get("id", "")
        if tag in {"article", "div"} and re.fullmatch(r"post-[a-z0-9-]+", post_id):
            if post_id in self.posts:
                raise ValueError(f"Duplicate post ID: {post_id}")
            self.post = self.posts[post_id] = Post(post_id)
            self.depth = len(self.stack)
        language = next((lang for lang in ("ru", "uz", "en") if f"data-{lang}" in attrs), None)
        if self.post:
            if (tag == "h3" or tag == "p" and "ct" not in attrs.get("class", "").split()) and self.capture is None:
                self.capture = (len(self.stack), tag, [])
            if tag == "img" and attrs.get("src"):
                self.post.images.append(attrs["src"])
        if tag not in self.void:
            self.stack.append((tag, language))

    def handle_endtag(self, tag):
        depth = next((i for i in range(len(self.stack) - 1, -1, -1)
                      if self.stack[i][0] == tag), None)
        if depth is None:
            return
        del self.stack[depth:]
        if self.capture and depth <= self.capture[0]:
            _, element, parts = self.capture
            languages = {language for language, text in parts if language and text.strip()}
            preferred = next((language for language in ("ru", "uz", "en") if language in languages), None)
            text = " ".join("".join(text for language, text in parts
                                    if language is None or language == preferred).split())
            if text:
                collection = self.post.titles if element == "h3" else self.post.descriptions
                collection.append((preferred == "ru", text))
            self.capture = None
        if self.post and depth <= self.depth:
            self.post = None

    def handle_data(self, data):
        if self.capture:
            depth, _, parts = self.capture
            language = next((language for _, language in reversed(self.stack[depth:]) if language), None)
            parts.append((language, data))


def preferred_text(values):
    return next((text for russian, text in values if russian), values[0][1] if values else "")


def preview_image(post, folder):
    candidates = [src for src in post.images if not src.startswith("img/groups/")]
    src = next(iter(candidates or post.images), "img/og.jpg")
    if urlsplit(src).scheme == "https":
        return src, None
    path = ROOT / src.lstrip("/")
    with Image.open(path) as original:
        photo = ImageOps.exif_transpose(original).convert("RGB")
        photo.thumbnail((1200, 1200))
        buffer = BytesIO()
        photo.save(buffer, format="JPEG", quality=86, optimize=True)
        data = buffer.getvalue()
    image_path = folder / "preview.jpg"
    if not image_path.exists() or image_path.read_bytes() != data:
        image_path.write_bytes(data)
    return urljoin(SITE, f"post/{post.id}/preview.jpg"), photo.size


def write_preview(post):
    folder = ROOT / "post" / post.id
    folder.mkdir(parents=True, exist_ok=True)
    title = preferred_text(post.titles)
    if not title:
        raise ValueError(f"Missing heading for {post.id}")
    description = preferred_text(post.descriptions)
    image, size = preview_image(post, folder)
    canonical = urljoin(SITE, f"post/{post.id}/")
    target = f"../../?post={post.id}#{post.id}"
    metadata = {
        "og:type": "article", "og:site_name": "Tennis Daily", "og:title": title,
        "og:description": description, "og:url": canonical, "og:image": image,
        "og:image:type": "image/jpeg",
    }
    if size:
        metadata.update({"og:image:width": str(size[0]), "og:image:height": str(size[1])})
    tags = "\n".join(f'<meta property="{key}" content="{escape(value)}">'
                     for key, value in metadata.items() if value)
    page = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} · Tennis Daily</title>
{tags}
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{canonical}">
</head>
<body>
<h1>{escape(title)}</h1>
<p>{escape(description)}</p>
<p><a id="post-link" href="{target}">Открыть на Tennis Daily</a></p>
<script>location.replace(document.getElementById('post-link').href);</script>
</body>
</html>
"""
    (folder / "index.html").write_text(page, encoding="utf-8")


def main():
    parser = PostParser()
    parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))
    for post in parser.posts.values():
        write_preview(post)
    # Keep previously published links available even when posts leave the index.
    ids = sorted(p.parent.name for p in (ROOT / "post").glob("post-*/index.html"))
    (ROOT / "post" / "index.js").write_text(
        f"window.tennisDailyPostPreviews = new Set({json.dumps(ids, indent=2)});\n",
        encoding="utf-8",
    )
    print(f"Generated {len(parser.posts)} post previews")


if __name__ == "__main__":
    main()
