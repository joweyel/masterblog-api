from flask import Flask, jsonify, request, Response, Blueprint
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from typing import TypedDict, Literal


class Post(TypedDict):
    id: int
    title: str
    content: str


app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# For creating Swagger UI
SWAGGER_URL: str = "/api/docs"  # (1) swagger endpoint e.g. HTTP://localhost:5002/api/docs
API_URL: str = "/static/masterblog.json"  # (2) ensure you create this dir and file

swagger_ui_blueprint: Blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'Masterblog API'  # (3) You can change this if you like
    }
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

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
    """List all posts, or create a new one.

    GET: returns all posts, optionally sorted via the `sort`
    (`title`/`content`) and `direction` (`asc`/`desc`) query parameters.
    POST: creates a new post from a JSON body with `title` and `content`.

    Returns
    -------
    tuple[Response, int] | Response
        On GET: the (optionally sorted) list of posts, or a 400 error
        if `sort`/`direction` are invalid.
        On POST: the created post with status 201, or a 400 error if
        `title`/`content` are missing.
    """
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
    """Delete the post with the given id.

    Parameters
    ----------
    id : int
        The id of the post to delete.

    Returns
    -------
    tuple[Response, int]
        A confirmation message with status 200, or a 404 error if no
        post with the given id exists.
    """
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
    """Update the title and/or content of the post with the given id.

    Fields omitted from the JSON body keep their current value.

    Parameters
    ----------
    id : int
        The id of the post to update.

    Returns
    -------
    tuple[Response, int]
        The updated post with status 200, or a 404 error if no post
        with the given id exists.
    """
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
    """Search posts by title and/or content.

    A post matches if the `title` query param is contained in its
    title, or the `content` query param is contained in its content
    (case-insensitive). Missing query params are not required to match.

    Returns
    -------
    Response
        The list of matching posts, or an empty list if none match.
    """
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
