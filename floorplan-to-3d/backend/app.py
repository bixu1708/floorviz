"""Flask backend for floor plan upload and 3D layout generation."""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Tuple

import cv2
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

from detect_walls import detect_walls, normalize_walls

try:
    from pdf2image import convert_from_path
except ImportError:  # Optional dependency fallback
    convert_from_path = None

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
CORS(app)


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _convert_pdf_to_png(pdf_path: Path) -> Path:
    if convert_from_path is None:
        raise RuntimeError("PDF upload requires pdf2image package.")

    pages = convert_from_path(str(pdf_path), first_page=1, last_page=1)
    if not pages:
        raise RuntimeError("No pages found in uploaded PDF.")

    output_path = pdf_path.with_suffix(".png")
    pages[0].save(output_path, "PNG")
    return output_path


def _save_upload() -> Tuple[Path, str]:
    if "file" not in request.files:
        raise ValueError("No file field found in request.")

    file = request.files["file"]
    if file.filename == "":
        raise ValueError("No file selected.")

    if not _allowed_file(file.filename):
        raise ValueError("Unsupported file type. Use PNG/JPG/JPEG/PDF.")

    safe_name = secure_filename(file.filename)
    ext = safe_name.rsplit(".", 1)[1].lower()
    file_id = f"{uuid.uuid4().hex}_{Path(safe_name).stem}"
    saved_path = UPLOAD_DIR / f"{file_id}.{ext}"
    file.save(saved_path)

    if ext == "pdf":
        converted_path = _convert_pdf_to_png(saved_path)
        return converted_path, converted_path.name

    return saved_path, saved_path.name


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/upload", methods=["POST"])
def upload():
    try:
        saved_path, filename = _save_upload()
        return jsonify({"message": "File uploaded successfully", "filename": filename, "path": str(saved_path)})
    except Exception as exc:  # noqa: BLE001 - return API-safe error
        return jsonify({"error": str(exc)}), 400


@app.route("/generate3d", methods=["POST"])
def generate_3d():
    payload = request.get_json(silent=True) or {}
    filename = payload.get("filename")
    if not filename:
        return jsonify({"error": "filename is required."}), 400

    image_path = UPLOAD_DIR / filename
    if not image_path.exists():
        return jsonify({"error": "Uploaded file not found."}), 404

    try:
        walls = detect_walls(image_path)
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError("Failed to open uploaded image.")

        height, width = image.shape[:2]
        world_walls = normalize_walls(walls, width, height)

        return jsonify(
            {
                "filename": filename,
                "imageSize": {"width": width, "height": height},
                "walls": walls,
                "wallsWorld": world_walls,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
