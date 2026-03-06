# Floorplan to 3D Prototype

A full-stack prototype that converts a 2D floor plan into an interactive 3D house visualization in the browser.

## Overview

This project implements the following pipeline:

1. User uploads a floor plan (`PNG`, `JPG`, `JPEG`, or `PDF`)
2. Backend preprocesses the image with OpenCV
3. Canny edge detection + Probabilistic Hough transform detect wall lines
4. Lines are converted to structured JSON coordinates
5. Frontend reads wall coordinates and builds 3D wall geometry with Three.js
6. User explores the generated model with orbit controls

## Project Structure

```text
floorplan-to-3d/
│
├── backend/
│   ├── app.py
│   ├── detect_walls.py
│   ├── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── main.js
│   ├── style.css
│
├── uploads/
│
└── README.md
```

## Installation

### 1) Backend setup

```bash
cd floorplan-to-3d/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> Note: PDF support depends on `pdf2image` and a local Poppler installation.

### 2) Start backend server

```bash
python app.py
```

Backend runs on `http://localhost:5000`.

### 3) Start frontend server

In a separate terminal:

```bash
cd floorplan-to-3d/frontend
python -m http.server 8080
```

Frontend runs on `http://localhost:8080`.

## Usage

1. Open `http://localhost:8080`
2. Upload a floor plan image
3. Click **Generate 3D Model**
4. Inspect model with mouse controls:
   - Left drag: rotate
   - Right drag: pan
   - Scroll: zoom

## API Endpoints

### `POST /upload`
Uploads image/PDF into `uploads/`.

Response:

```json
{
  "message": "File uploaded successfully",
  "filename": "<stored-file-name>"
}
```

### `POST /generate3d`
Body:

```json
{
  "filename": "<stored-file-name>"
}
```

Response:

```json
{
  "walls": [[x1, y1, x2, y2]],
  "wallsWorld": [[x1, z1, x2, z2]]
}
```

## Example Floor Plan Input

Use any high-contrast architectural floor plan where walls are clear straight lines. Best results are achieved with black wall lines on a light background.

## Optional Advanced Features (Roadmap)

- Door/window detection with contour analysis or ML segmentation
- Room segmentation via connected components + semantic classification
- Furniture placement from icon detection
- Export 3D model to GLTF/OBJ from frontend scene graph

## Screenshots

Add screenshot(s) of generated 3D output here after running the app locally.

