from flask import Flask, jsonify, request, Response, Blueprint
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from typing import TypedDict, Literal
from datetime import datetime


class Post(TypedDict):
    id: int
    title: str
    content: str
    author: str
    date: str


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
    {
        "id": 1,
        "title": "First post",
        "content": "This is the first post.",
        "author": "Your Name",
        "date": "2023-06-07",
    },
    {
        "id": 2,
        "title": "Second post",
        "content": "This is the second post.",
        "author": "Your Name",
        "date": "2023-06-08"
    },
]


def get_next_id(posts: list[Post]) -> int:
    """Get next id for a post to add to post list."""
    return max((post["id"] for post in posts), default=0) + 1


def get_post_by_id(posts: list[Post], id: int) -> Post | None:
    """Get post with the specified post id."""
    return next((post for post in posts if post["id"] == id), None)


@app.route("/api/posts", methods=["GET", "POST"])
def get_posts() -> tuple[Response, int] | Response:
    """List all posts (GET), or create a new one (POST).

    GET: returns all posts, optionally sorted via the `sort`
    (`title`/`content`/`author`/`date`) and `direction` (`asc`/`desc`)
    query parameters.
    POST: creates a new post from a JSON body with `title`, `content`,
    `author`, and `date`.

    Returns
    -------
    tuple[Response, int] | Response
        On GET: the (optionally sorted) list of posts, or a 400 error
        if `sort`/`direction` are invalid.
        On POST: the created post with status 201, or a 400 error if
        `title`/`content`/`author`/`date` are missing.
    """
    if request.method == "POST":
        request_data: dict = request.get_json()
        title: str | None = request_data.get("title")
        content: str | None = request_data.get("content")
        author: str | None = request_data.get("author")
        date: str | None = request_data.get("date")

        fields: dict[str, str | None] = {"title": title, "content": content, "author": author, "date": date}
        missing: list[str] = [name for name, value in fields.items() if not value]

        # If any attribute is missing -> json with error message
        if missing:
            return jsonify({
                "error": "Missing required fields",
                "missing": missing,
            }), 400
        new_post: Post = {"id": get_next_id(posts=POSTS), **fields}
        POSTS.append(new_post)
        return jsonify(new_post), 201

    ################################
    # Adding Sorting Functionality #
    ################################
    # Get the parameters
    sort: str | None = request.args.get("sort")
    direction: str | None = request.args.get("direction")

    # Check parameters for validity (dynamically gets all searchable parameters from `Post` class)
    sortable_fields: tuple[str, ...] = tuple(field for field in Post.__annotations__ if field != "id")
    if sort and sort not in sortable_fields:
        return jsonify({"error": f"Invalid sort field: {sort}"}), 400
    if direction and direction not in ("asc", "desc"):
        return jsonify({"error": f"Invalid direction: {direction}"}), 400

    sorted_posts: list[Post] = POSTS
    if sort:
        if sort == "date":
            key = lambda post: datetime.strptime(post["date"], "%Y-%m-%d")
        else:
            key = lambda post: post[sort].lower()
        sorted_posts = sorted(
            sorted_posts,
            key=key,
            reverse=(direction == "desc"),
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
    """Update the title, content, author, and/or date of the post with the given id.

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
    post["author"] = data.get("author", post["author"])
    post["date"] = data.get("date", post["date"])

    return jsonify(post), 200


@app.route("/api/posts/search", methods=["GET"])
def search_post() -> Response:
    """Search posts by any field defined on `Post` (except `id`).

    A post matches if any provided query param is contained
    (case-insensitive) in the corresponding post field.

    Returns
    -------
    Response
        The list of matching posts, or an empty list if none match.
    """

    # Obtaining the `queries` to search for dynamically based on the attributes of the `Post` class
    searchable_fields: tuple[str, ...] = tuple(field for field in Post.__annotations__ if field != "id")
    queries: dict[str, str | None] = {field: request.args.get(field) for field in searchable_fields}

    # Check if there is a match for any of the specified fields (generalized version)
    results: list[Post] = [
        post for post in POSTS
        if any(value_query and value_query.lower() in post[field].lower() for field, value_query in queries.items())
    ]
    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
