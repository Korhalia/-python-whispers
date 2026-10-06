import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, render_template, request, url_for
from flask_limiter import Limiter
from flask_limiter.errors import RateLimitExceeded
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFError, CSRFProtect


APP_ENV = os.environ.get("APP_ENV", "development").strip().lower()
IS_PRODUCTION = APP_ENV == "production"

secret_key = os.environ.get("SECRET_KEY")

if IS_PRODUCTION and not secret_key:
    raise RuntimeError("SECRET_KEY must be set when APP_ENV=production.")

app = Flask(__name__)

app.config.update(
    SECRET_KEY=secret_key or secrets.token_hex(32),
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,  # 2 MB maximum request size
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=IS_PRODUCTION,  # Requires HTTPS in production
    SESSION_COOKIE_SAMESITE="Lax",
)

# CSRF protection requires a token in POST forms.
csrf = CSRFProtect(app)

# Use shared storage such as Redis in production so limits work across workers.
rate_limit_storage = os.environ.get("RATELIMIT_STORAGE_URI")
if IS_PRODUCTION and not rate_limit_storage:
    raise RuntimeError(
        "Set RATELIMIT_STORAGE_URI to shared storage, such as Redis, in production."
    )

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    storage_uri=rate_limit_storage or "memory://",
    default_limits=[],
)


@app.context_processor
def inject_template_variables():
    """Make the current year available to templates."""
    return {"current_year": datetime.now(timezone.utc).year}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>About</title>
    </head>
    <body>
        <h1>About this app</h1>
        <p>This app currently plays a sample track for a music description.
        It does not generate new music yet.</p>
        <a href="/">Return home</a>
    </body>
    </html>
    """


@app.route("/generate", methods=["POST"])
@limiter.limit("10 per minute")
def generate():
    """Validate a music prompt and return the configured sample audio."""
    prompt = request.form.get("prompt", "").strip()

    if not prompt:
        return render_template(
            "index.html",
            error="Please describe the music you want.",
            prompt=prompt,
        ), 400

    if len(prompt) > 1000:
        return render_template(
            "index.html",
            error="Your description must be 1,000 characters or fewer.",
            prompt=prompt,
        ), 400

    # This is a sample track, not newly generated music.
    audio_filename = "music/halloween_dance.wav"
    audio_path = Path(app.static_folder) / audio_filename

    try:
        audio_exists = audio_path.is_file()
    except OSError:
        app.logger.exception("Could not check the sample audio file.")
        audio_exists = False

    if not audio_exists:
        app.logger.error("Sample audio file not found: %s", audio_path)
        return render_template(
            "index.html",
            error="The sample audio file could not be found.",
            prompt=prompt,
        ), 500

    return render_template(
        "index.html",
        generated_audio_url=url_for("static", filename=audio_filename),
        generated_title=f"Sample track for: {prompt}",
        prompt=prompt,
    )


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    return render_template(
        "index.html",
        error="Your form session expired or could not be verified. Please try again.",
        prompt=request.form.get("prompt", "").strip(),
    ), 400


@app.errorhandler(RateLimitExceeded)
def handle_rate_limit(error):
    return render_template(
        "index.html",
        error="Too many requests. Please wait a minute and try again.",
        prompt=request.form.get("prompt", "").strip(),
    ), 429


@app.errorhandler(413)
def request_too_large(error):
    return render_template(
        "index.html",
        error="The request is too large.",
    ), 413


@app.errorhandler(404)
def page_not_found(error):
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>Page not found</title></head>
    <body>
        <h1>404 - Page not found</h1>
        <p><a href="/">Return to the home page</a></p>
    </body>
    </html>
    """, 404


@app.errorhandler(500)
def internal_server_error(error):
    original_exception = getattr(error, "original_exception", None)

    if original_exception:
        app.logger.error(
            "Unhandled server exception",
            exc_info=(
                type(original_exception),
                original_exception,
                original_exception.__traceback__,
            ),
        )
    else:
        app.logger.error("Internal server error: %s", error)

    return """
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>Server error</title></head>
    <body>
        <h1>500 - Server error</h1>
        <p>Something went wrong. Please try again later.</p>
        <p><a href="/">Return to the home page</a></p>
    </body>
    </html>
    """, 500


if __name__ == "__main__":
    if IS_PRODUCTION:
        raise RuntimeError(
            "Do not use Flask's development server in production. "
            "Start this app with a production WSGI server."
        )

    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
