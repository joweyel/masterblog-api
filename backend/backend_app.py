from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from typing import TypedDict, Literal


class Post(TypedDict):
    id: int
    title: str
    content: str


app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

POSTS: list[Post] = [
    {"id": 1, "title": "First post", "content": "This is the first post.", },
    {"id": 2, "title": "Second post", "content": "This is the second post.", },
]


def get_next_id(posts: list[Post]) -> int:
    """Get next id for a post to add to post list."""
    return max((post["id"] for post in posts), default=0) + 1


def get_post_by_id(posts: list[Post], id: int) -> Post | None:
    """Get post with the specified post id."""
    return next((post for post in posts if post["id"] == id), None)


@app.route("/api/posts", methods=["GET", "POST"])
def get_posts() -> tuple[Response, int] | Response:
    if request.method == "POST":
        request_data: dict = request.get_json()
        title: str | None = request_data.get("title")
        content: str | None = request_data.get("content")

        if title and content:
            new_id: int = get_next_id(posts=POSTS)
            new_post: Post = {
                "id": new_id,
                "title": title,
                "content": content,
            }
            POSTS.append(new_post)
            return jsonify(new_post), 201
        else:
            missing: list[str] = []
            if not title:
                missing.append("title")
            if not content:
                missing.append("content")
            return jsonify({
                "error": f"Missing required fields",
                "missing": missing,
            }), 400
    ################################
    # Adding Sorting Functionality #
    ################################
    # Get the parameters
    sort: str | None = request.args.get("sort")
    direction: str | None = request.args.get("direction")

    # Check parameters for validity
    if sort and sort not in ("title", "content"):
        return jsonify({"error": f"Invalid sort field: {sort}"}), 400
    if direction and direction not in ("asc", "desc"):
        return jsonify({"error": f"Invalid direction: {direction}"}), 400

    sorted_posts: list[Post] = POSTS
    if sort:
        sorted_posts = sorted(
            sorted_posts,
            key=lambda post: post[sort].lower(),
            reverse=(direction == "desc")  # reverse=False -> asc | reverse=True -> desc
        )

    return jsonify(sorted_posts)


@app.route("/api/posts/<int:id>", methods=["DELETE"])
def delete_post(id: int) -> tuple[Response, int]:
    post: Post | None = get_post_by_id(POSTS, id)
    if post is None:
        return jsonify({
            "error": f"Post with id '{id}' not found"
        }), 404

    POSTS.remove(post)
    return jsonify({
        "message": f"Post with id '{id}' has been deleted successfully."
    }), 200


@app.route("/api/posts/<int:id>", methods=["PUT"])
def update_post(id: int) -> tuple[Response, int]:
    post: Post | None = get_post_by_id(POSTS, id)
    if post is None:
        return jsonify({
            "error": f"Post with id '{id}' not found"
        }), 404
    data = request.get_json(silent=True) or {}
    post["title"] = data.get("title", post["title"])
    post["content"] = data.get("content", post["content"])

    return jsonify(post), 200


@app.route("/api/posts/search", methods=["GET"])
def search_post() -> Response:
    """Search posts based on title and content."""
    title_query: str | None = request.args.get("title")
    content_query: str | None = request.args.get("content")

    results: list[Post] = [
        post for post in POSTS
        if (title_query and title_query.lower() in post["title"].lower())
           or (content_query and content_query.lower() in post["content"].lower())
    ]
    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
