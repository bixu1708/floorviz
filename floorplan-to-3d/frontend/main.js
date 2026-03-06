import * as THREE from "https://unpkg.com/three@0.165.0/build/three.module.js";
import { OrbitControls } from "https://unpkg.com/three@0.165.0/examples/jsm/controls/OrbitControls.js";

const API_BASE = "http://localhost:5000";
const WALL_HEIGHT = 3;
const WALL_THICKNESS = 0.2;

const viewer = document.getElementById("viewer");
const fileInput = document.getElementById("fileInput");
const generateBtn = document.getElementById("generateBtn");
const statusEl = document.getElementById("status");

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a2030);

const camera = new THREE.PerspectiveCamera(60, viewer.clientWidth / viewer.clientHeight, 0.1, 1000);
camera.position.set(8, 8, 8);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(viewer.clientWidth, viewer.clientHeight);
viewer.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0, 0);
controls.update();

const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(0xffffff, 0.9);
directionalLight.position.set(10, 20, 10);
scene.add(directionalLight);

const floorGeometry = new THREE.PlaneGeometry(40, 40);
const floorMaterial = new THREE.MeshStandardMaterial({ color: 0x2a3146, side: THREE.DoubleSide });
const floor = new THREE.Mesh(floorGeometry, floorMaterial);
floor.rotation.x = -Math.PI / 2;
scene.add(floor);

const grid = new THREE.GridHelper(40, 40, 0x7a86a6, 0x3c445a);
scene.add(grid);

const wallGroup = new THREE.Group();
scene.add(wallGroup);

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#ff9191" : "#9dc1ff";
}

function clearWalls() {
  while (wallGroup.children.length > 0) {
    const wall = wallGroup.children.pop();
    wall.geometry.dispose();
    wall.material.dispose();
  }
}

function createWallMesh(x1, z1, x2, z2) {
  const dx = x2 - x1;
  const dz = z2 - z1;
  const length = Math.max(Math.hypot(dx, dz), WALL_THICKNESS);

  const geometry = new THREE.BoxGeometry(length, WALL_HEIGHT, WALL_THICKNESS);
  const material = new THREE.MeshStandardMaterial({ color: 0xf0f0f0 });
  const mesh = new THREE.Mesh(geometry, material);

  mesh.position.set((x1 + x2) / 2, WALL_HEIGHT / 2, (z1 + z2) / 2);
  mesh.rotation.y = -Math.atan2(dz, dx);

  return mesh;
}

async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });

  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error || "Upload failed");
  }

  return result.filename;
}

async function request3D(filename) {
  const response = await fetch(`${API_BASE}/generate3d`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename }),
  });

  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error || "3D generation failed");
  }

  return result;
}

function renderWalls(wallsWorld) {
  clearWalls();

  wallsWorld.forEach(([x1, z1, x2, z2]) => {
    wallGroup.add(createWallMesh(x1, z1, x2, z2));
  });

  if (wallsWorld.length) {
    controls.target.set(0, 0, 0);
    controls.update();
  }
}

generateBtn.addEventListener("click", async () => {
  const file = fileInput.files?.[0];
  if (!file) {
    setStatus("Please select a floor plan file first.", true);
    return;
  }

  generateBtn.disabled = true;
  try {
    setStatus("Uploading file...");
    const filename = await uploadFile(file);

    setStatus("Detecting walls and generating model...");
    const result = await request3D(filename);

    renderWalls(result.wallsWorld || []);
    setStatus(`Done. Detected ${result.walls?.length || 0} walls.`);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    generateBtn.disabled = false;
  }
});

window.addEventListener("resize", () => {
  camera.aspect = viewer.clientWidth / viewer.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(viewer.clientWidth, viewer.clientHeight);
});

function animate() {
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}
animate();
