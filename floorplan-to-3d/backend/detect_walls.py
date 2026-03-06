"""Utilities for extracting wall-like line segments from a floor plan image."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

import cv2
import numpy as np


@dataclass
class DetectionConfig:
    """Tunable parameters for wall extraction."""

    canny_threshold1: int = 50
    canny_threshold2: int = 150
    hough_threshold: int = 120
    min_line_length: int = 40
    max_line_gap: int = 10


def _prepare_image(image_path: Path) -> np.ndarray:
    """Load an image and return a denoised grayscale copy."""

    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Auto-threshold style inversion helps when plans have white background
    _, binary = cv2.threshold(
        blurred,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
    )
    return binary


def _merge_similar_lines(lines: np.ndarray, distance_threshold: int = 8) -> List[List[int]]:
    """Merge near-duplicate lines emitted by Hough transform."""

    if lines is None:
        return []

    merged: List[List[int]] = []
    for line in lines[:, 0, :]:
        x1, y1, x2, y2 = map(int, line)
        matched = False

        for existing in merged:
            ex1, ey1, ex2, ey2 = existing
            if (
                abs(x1 - ex1) < distance_threshold
                and abs(y1 - ey1) < distance_threshold
                and abs(x2 - ex2) < distance_threshold
                and abs(y2 - ey2) < distance_threshold
            ) or (
                abs(x1 - ex2) < distance_threshold
                and abs(y1 - ey2) < distance_threshold
                and abs(x2 - ex1) < distance_threshold
                and abs(y2 - ey1) < distance_threshold
            ):
                matched = True
                break

        if not matched:
            merged.append([x1, y1, x2, y2])

    return merged


def detect_walls(image_path: str | Path, config: DetectionConfig | None = None) -> List[List[int]]:
    """Detect wall-like straight segments from a floor plan image.

    Args:
        image_path: Path to an uploaded PNG/JPG/PDF converted image.
        config: Optional detection hyperparameters.

    Returns:
        A list of wall line coordinates ``[x1, y1, x2, y2]``.
    """

    cfg = config or DetectionConfig()
    path = Path(image_path)

    binary = _prepare_image(path)
    edges = cv2.Canny(binary, cfg.canny_threshold1, cfg.canny_threshold2)

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=cfg.hough_threshold,
        minLineLength=cfg.min_line_length,
        maxLineGap=cfg.max_line_gap,
    )

    return _merge_similar_lines(lines)


def normalize_walls(walls: Sequence[Sequence[int]], image_width: int, image_height: int) -> List[List[float]]:
    """Normalize wall coordinates into world space units for frontend usage."""

    if image_width <= 0 or image_height <= 0:
        raise ValueError("Image width and height must be > 0")

    scale = 10.0 / max(image_width, image_height)
    normalized: List[List[float]] = []

    for x1, y1, x2, y2 in walls:
        nx1 = x1 * scale
        nz1 = y1 * scale
        nx2 = x2 * scale
        nz2 = y2 * scale
        normalized.append([round(nx1, 4), round(nz1, 4), round(nx2, 4), round(nz2, 4)])

    return normalized
