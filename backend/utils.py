import json
from typing import TypedDict

class Post(TypedDict):
    id: int
    title: str
    content: str
    author: str
    date: str


POSTS_FILE_PATH: str = "posts.json"


def get_next_id(posts: list[Post]) -> int:
    """Get next id for a post to add to post list."""
    return max((post["id"] for post in posts), default=0) + 1


def get_post_by_id(posts: list[Post], id: int) -> Post | None:
    """Get post with the specified post id."""
    return next((post for post in posts if post["id"] == id), None)

def load_posts(filepath: str = POSTS_FILE_PATH):
    try:
        with open(filepath, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_posts(posts: list[Post], filepath: str = POSTS_FILE_PATH) -> None:
    with open(filepath, "w") as file:
        json.dump(posts, file, indent=4)
