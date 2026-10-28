import os
import re
import uuid
import threading
import mimetypes
import time
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, jsonify, request, send_file, render_template
import yt_dlp

APP_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = APP_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

ALLOWED_HOSTS = {
    "pinterest.com", "www.pinterest.com", "m.pinterest.com",
    "pin.it", "www.pin.it"
}
JOBS = {}
LOCK = threading.Lock()


def cleanup_job_files(job_id):
    """Remove all final and intermediate files created for one download job."""
    if not job_id:
        return
    for path in DOWNLOAD_DIR.glob(f"{job_id}.*"):
        try:
            if path.is_file():
                path.unlink(missing_ok=True)
        except OSError:
            app.logger.warning("Could not remove temporary file: %s", path, exc_info=True)


def cleanup_stale_downloads(max_age_seconds=2 * 60 * 60):
    """Remove abandoned temporary files older than two hours, including .part files."""
    cutoff = time.time() - max_age_seconds
    try:
        for path in DOWNLOAD_DIR.iterdir():
            try:
                if path.is_file() and path.stat().st_mtime < cutoff:
                    path.unlink(missing_ok=True)
            except OSError:
                app.logger.warning("Could not remove stale temporary file: %s", path, exc_info=True)
    except OSError:
        app.logger.warning("Could not scan temporary download directory.", exc_info=True)


# Clean up files left behind by interrupted downloads when the app starts.
cleanup_stale_downloads()


def validate_pin_url(raw_url):
    if not isinstance(raw_url, str) or not raw_url.strip():
        raise ValueError("Paste a Pinterest link first.")
    raw_url = raw_url.strip()
    if not raw_url.startswith(("https://", "http://")):
        raw_url = "https://" + raw_url
    parsed = urlparse(raw_url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or host not in ALLOWED_HOSTS:
        raise ValueError("Please enter a valid Pinterest Pin link (pinterest.com or pin.it).")
    if parsed.username or parsed.password:
        raise ValueError("This URL is not supported.")
    return raw_url


def ydl_options(outtmpl=None, download=False):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 20,
        "retries": 1,
        "extractor_retries": 1,
        "skip_download": not download,
        "restrictfilenames": True,
    }
    if outtmpl:
        opts["outtmpl"] = outtmpl
    return opts


def make_download_filename(title, filepath):
    """Return a useful filename and ensure the extension appears exactly once."""
    suffix = filepath.suffix.lower()
    if not suffix:
        suffix = ".mp4"

    # Keep filenames portable across Windows/macOS/Linux and strip trailing dots/spaces.
    raw_title = str(title or "")
    safe_title = re.sub(r"[^A-Za-z0-9._ -]+", "", raw_title)
    safe_title = re.sub(r"\s+", " ", safe_title).strip(" ._-")

    # Some Pinterest titles contain only emoji/non-ASCII characters; don't emit ".mp4".
    if not safe_title or safe_title.lower() in {"mp4", "video", "media"}:
        safe_title = "pinterest-video"

    # Remove an extension already present in the title to avoid name.mp4.mp4.
    if suffix and safe_title.lower().endswith(suffix):
        safe_title = safe_title[:-len(suffix)].rstrip(" ._-")
    if not safe_title:
        safe_title = "pinterest-video"

    safe_title = safe_title[:90].rstrip(" ._-") or "pinterest-video"
    return f"{safe_title}{suffix}"


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({"ok": True})


@app.post("/api/resolve")
def resolve():
    data = request.get_json(silent=True) or {}
    try:
        url = validate_pin_url(data.get("url", ""))
        with yt_dlp.YoutubeDL(ydl_options()) as ydl:
            info = ydl.extract_info(url, download=False)
        if not info:
            raise ValueError("No media was found for this Pin.")
        formats = info.get("formats") or []
        media_url = info.get("url")
        # We deliberately let yt-dlp handle downloading rather than exposing source URLs.
        return jsonify({
            "ok": True,
            "id": str(info.get("id") or ""),
            "title": info.get("title") or "Pinterest media",
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "media_type": "video" if (
                info.get("duration") or
                any(f.get("vcodec") not in (None, "none") for f in formats)
            ) else "media",
            "formats_available": bool(formats or media_url),
            "message": "Media found. You can now download it."
        })
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        app.logger.exception("Pinterest resolve failed: %s", e)
        return jsonify({
            "ok": False,
            "error": "We couldn't access this Pin. It may be private, deleted, image-only, or Pinterest may have changed its page format. Try another public Pin."
        }), 422


@app.post("/api/download")
def download():
    data = request.get_json(silent=True) or {}
    filepath = None
    try:
        url = validate_pin_url(data.get("url", ""))
        # Also sweep abandoned files during normal traffic; active recent downloads are kept.
        cleanup_stale_downloads()
        job_id = uuid.uuid4().hex
        outtmpl = str(DOWNLOAD_DIR / f"{job_id}.%(ext)s")

        # Do not force a specific format: let yt-dlp select an available one.
        with yt_dlp.YoutubeDL(ydl_options(outtmpl=outtmpl, download=True)) as ydl:
            info = ydl.extract_info(url, download=True)
            prepared_path = Path(ydl.prepare_filename(info))

        filepath = prepared_path
        if not filepath.exists():
            # Post-processing may change the final extension.
            matches = list(DOWNLOAD_DIR.glob(f"{job_id}.*"))
            if matches:
                filepath = matches[0]

        if not filepath.exists() or not filepath.is_file():
            raise RuntimeError("The media download did not produce a file.")

        download_name = make_download_filename(info.get("title"), filepath)
        mimetype = mimetypes.guess_type(download_name)[0] or "application/octet-stream"

        response = send_file(
            filepath,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype
        )

        # Delete after response is sent, avoiding permanent storage of user downloads.
        @response.call_on_close
        def cleanup():
            cleanup_job_files(job_id)

        return response

    except ValueError as e:
        if "job_id" in locals():
            cleanup_job_files(job_id)
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        if "job_id" in locals():
            cleanup_job_files(job_id)
        app.logger.exception("Pinterest download failed: %s", e)
        return jsonify({
            "ok": False,
            "error": "Download failed. This Pin may be private or unsupported, or Pinterest may have changed its format. Try a public video Pin."
        }), 422


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
