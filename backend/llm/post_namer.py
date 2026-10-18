import json
import os
import re
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:latest"
CACHE_FILE = "backend/data/cache/post_names_cache.json"

# In-memory cache for fast lookup during process lifetime
_MEMORY_CACHE = {}


def _load_cache():
    global _MEMORY_CACHE
    if _MEMORY_CACHE:
        return _MEMORY_CACHE
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                _MEMORY_CACHE = json.load(f)
        except Exception:
            _MEMORY_CACHE = {}
    return _MEMORY_CACHE


def _save_cache(cache):
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _generate_fallback_name(caption, hashtags, post_type):
    """Fast, deterministic fallback name generation following the same prompt rules."""
    # 1. Try meaningful words from caption
    clean_caption = re.sub(r"https?://\S+|www\.\S+|@\w+|#\w+", " ", caption or "")
    clean_caption = re.sub(r"[^\w\s]", " ", clean_caption)
    words = [w.strip() for w in clean_caption.split() if len(w.strip()) > 1]
    stopwords = {"the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with", "is", "it", "this", "that", "my", "your"}
    meaningful_words = [w for w in words if w.lower() not in stopwords]

    if len(meaningful_words) >= 2:
        return " ".join(meaningful_words[:3]).title()
    elif len(meaningful_words) == 1:
        return f"{meaningful_words[0].title()} Highlight"

    # 2. Try meaningful hashtags
    if isinstance(hashtags, list):
        tag_list = hashtags
    elif isinstance(hashtags, str):
        tag_list = re.findall(r"#\w+", hashtags)
    else:
        tag_list = []

    generic_tags = {"like", "likes", "post", "posts", "share", "trends", "trendingnow", "trend", "viral", "fyp", "explore", "reels", "love"}
    meaningful_tags = []
    for tag in tag_list:
        clean_tag = tag.lstrip("#").lower()
        if clean_tag not in generic_tags and len(clean_tag) > 2:
            # Separate camelCase or concatenated words if possible
            spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", clean_tag).title()
            meaningful_tags.append(spaced)

    if meaningful_tags:
        chosen = meaningful_tags[:2]
        return " ".join(chosen).title()

    # 3. Default based on post type
    clean_type = str(post_type or "Post").replace("_", " ").title()
    if clean_type.lower() in ["sidecar", "feed", "clips"]:
        clean_type = "Post"
    return f"Featured {clean_type}"


def generate_post_name(post):
    caption = post.get("caption") or ""
    hashtags = post.get("hashtags") or []
    post_type = post.get("type") or "Post"
    short_code = post.get("shortCode") or post.get("id") or ""

    # Create cache key
    cache_key = short_code if short_code else f"{caption[:60]}_{str(hashtags)[:40]}"

    cache = _load_cache()
    if cache_key in cache and cache[cache_key]:
        return cache[cache_key]

    if isinstance(hashtags, list):
        hashtag_text = " ".join(hashtags)
    else:
        hashtag_text = str(hashtags)

    prompt = f"""
Generate a short, human-readable English name for this Instagram post.

Post data:

Caption:
{caption}

Hashtags:
{hashtag_text}

Post type:
{post_type}

Rules:

1. Return exactly one short, natural English post name.
2. The name must contain 2 to 4 meaningful English words and Do not add the word "Post" unless it is actually meaningful.
3. Use meaningful words from the caption when available.
4. If the caption contains only emojis or meaningless text, use meaningful hashtags.
5. Hashtags can be converted into normal English words.
6. Prefer specific meaningful hashtags over generic hashtags such as:
   #like, #post, #share, #trendingnow, #trends.
7. For example, #brothers and #trendingsongs can support a name such as:
   "Brothers Trending Song Post"
8. Never include the technical post type such as Sidecar, Image, Video,
   Carousel, Clips, or Feed in the generated name.
9. Do not assume what is shown in the image or video.
10. Do not infer an event, location, person, activity, or story unless explicitly supported.
11. If neither caption nor hashtags contain meaningful information,
    use a generic name based on the post type.
12. Do not include emojis.
13. Do not include hashtags.
14. Do not include quotation marks.
15. Do not explain your answer.
16. Return ONLY the post name.

"""
    data = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    name = None
    try:
        response = requests.post(
            OLLAMA_URL,
            json=data,
            timeout=8  # Fast timeout so Ollama doesn't block responsiveness
        )
        if response.status_code == 200:
            result = response.json()
            raw_name = result.get("response", "").strip()
            name = raw_name.replace('"', "").replace("'", "").strip()
    except Exception:
        # If Ollama is slow, offline or busy, gracefully fallback
        pass

    if not name or len(name) < 2:
        name = _generate_fallback_name(caption, hashtags, post_type)

    if name:
        cache[cache_key] = name
        _save_cache(cache)

    return name