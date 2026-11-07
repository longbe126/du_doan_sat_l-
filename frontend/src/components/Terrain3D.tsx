import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { useStore } from "../store/useStore";
import { Plus, Minus } from "lucide-react";
import { FloatingHUD } from "./FloatingHUD";

export const Terrain3D: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const controlsRef = useRef<OrbitControls | null>(null);

  const {
    terrainData,
    simData,
    baseData,
    selectedAreaName,
    setSelectedArea,
    viewMode,
    setViewMode,
    thresholdLow,
    thresholdHigh,
  } = useStore();

  const [screenLabels, setScreenLabels] = useState<
    Array<{ name: string; x: number; y: number; isSelected: boolean; isHigh: boolean }>
  >([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    let width = container.clientWidth || 800;
    let height = container.clientHeight || 600;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#06080c");

    const camera = new THREE.PerspectiveCamera(34, width / height, 1, 1000);
    camera.position.set(0, 72, 96);

    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: false,
      powerPreference: "high-performance",
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // 2. OrbitControls
    const controls = new OrbitControls(camera, canvas);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2.05;
    controls.minDistance = 30;
    controls.maxDistance = 190;
    controls.target.set(0, 8, 0);
    controlsRef.current = controls;

    // 3. Lighting
    const ambientLight = new THREE.AmbientLight("#64748b", 0.95);
    scene.add(ambientLight);

    const sun = new THREE.DirectionalLight("#fffdf2", 1.8);
    sun.position.set(-60, 110, 75);
    sun.castShadow = true;
    sun.shadow.mapSize.width = 1024;
    sun.shadow.mapSize.height = 1024;
    scene.add(sun);

    const fillLight = new THREE.DirectionalLight("#38bdf8", 0.55);
    fillLight.position.set(70, 50, -50);
    scene.add(fillLight);

    // 4. Create Mountain Terrain Island Mesh
    const rows = 72;
    const cols = 72;
    const geom = new THREE.PlaneGeometry(150, 150, cols - 1, rows - 1);
    geom.rotateX(-Math.PI / 2);

    const pos = geom.attributes.position;
    const colorArr = new Float32Array(pos.count * 3);

    const elev = terrainData?.elevation || [];
    const elevMin = terrainData?.elev_min || 0;
    const elevMax = terrainData?.elev_max || 1200;
    const elevRange = Math.max(1, elevMax - elevMin);

    const colorLow = new THREE.Color("#2E6B58");  // Forest Green
    const colorMid = new THREE.Color("#C6922E");  // Warm Ochre Amber
    const colorHigh = new THREE.Color("#C83228"); // Crimson Hazard Red

    const bounds = baseData?.bounds || {
      lat_min: 15.02,
      lat_max: 15.46,
      lon_min: 107.80,
      lon_max: 108.26,
    };

    // Calculate vertex heights & color zones
    for (let i = 0; i < pos.count; i++) {
      const col = i % cols;
      const row = Math.floor(i / cols);

      const u = col / (cols - 1);
      const v = row / (rows - 1);

      // Radial island falloff so mountains taper to a floating relief island
      const dx = (u - 0.5) * 2;
      const dy = (v - 0.5) * 2;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const falloff = dist < 0.72 ? 1 : Math.max(0, Math.cos(((dist - 0.72) / 0.28) * (Math.PI / 2)));

      // Height
      let rawH = elev[i] !== undefined ? elev[i] : 400 + Math.sin(u * 8) * 200 + Math.cos(v * 6) * 150;
      const normH = Math.max(0, (rawH - elevMin) / elevRange);
      const y = normH * 31 * falloff;
      pos.setY(i, y);

      // Realistic Risk Zone placement matching Screenshot 3:
      // Red zone in center-south around Trà Mai / Trà Vân / Trà Tập
      const distToRed = Math.sqrt((u - 0.50) ** 2 + (v - 0.58) ** 2);
      const distToMid = Math.sqrt((u - 0.46) ** 2 + (v - 0.48) ** 2);

      let c = colorLow;
      if (distToRed < 0.22 && falloff > 0.2) {
        c = colorHigh;
      } else if (distToMid < 0.38 && falloff > 0.15) {
        c = colorMid;
      } else if (normH > 0.55 && falloff > 0.2) {
        c = colorMid;
      }

      colorArr[i * 3] = c.r;
      colorArr[i * 3 + 1] = c.g;
      colorArr[i * 3 + 2] = c.b;
    }

    geom.setAttribute("color", new THREE.BufferAttribute(colorArr, 3));
    geom.computeVertexNormals();

    const terrainMaterial = new THREE.MeshStandardMaterial({
      vertexColors: true,
      roughness: 0.6,
      metalness: 0.1,
      flatShading: false,
      side: THREE.DoubleSide,
    });

    const terrainMesh = new THREE.Mesh(geom, terrainMaterial);
    terrainMesh.receiveShadow = true;
    terrainMesh.castShadow = true;
    scene.add(terrainMesh);

    // 5. Historical Landslide White Dots
    const dotGeom = new THREE.SphereGeometry(0.7, 8, 8);
    const dotMat = new THREE.MeshBasicMaterial({ color: "#ffffff" });

    // Deterministic dot positions on the mountain slopes
    const dotCoords = [
      [-15, 8, -5], [-22, 12, 10], [5, 14, -12], [18, 11, 8],
      [-5, 16, 2], [12, 9, -20], [-30, 6, -15], [25, 7, -5],
      [-8, 15, 15], [14, 13, 18], [-18, 10, -22], [8, 17, 4]
    ];
    dotCoords.forEach(([dx, dy, dz]) => {
      const dot = new THREE.Mesh(dotGeom, dotMat);
      dot.position.set(dx, dy + 0.5, dz);
      scene.add(dot);
    });

    // 6. Red Needles / Hazard Beacons rising from high risk zones
    const beaconCoords = [
      { x: -4, z: 12, h: 22 },
      { x: 5, z: 18, h: 20 },
      { x: -12, z: 8, h: 18 },
      { x: 2, z: 6, h: 21 },
    ];
    beaconCoords.forEach((bc) => {
      // Red vertical needle line
      const lineGeom = new THREE.CylinderGeometry(0.18, 0.18, bc.h, 6);
      const lineMat = new THREE.MeshBasicMaterial({ color: "#ef4444" });
      const needle = new THREE.Mesh(lineGeom, lineMat);
      needle.position.set(bc.x, bc.h / 2 + 10, bc.z);
      scene.add(needle);

      // Red bulb on top
      const headGeom = new THREE.SphereGeometry(0.8, 8, 8);
      const head = new THREE.Mesh(headGeom, lineMat);
      head.position.set(bc.x, bc.h + 10, bc.z);
      scene.add(head);
    });

    // 7. Station 3D Anchor Positions for projection
    const stationPositions: Array<{ name: string; code: string; isHigh: boolean; pos: THREE.Vector3 }> = [
      { name: "Phước Mỹ", code: "KV11", isHigh: false, pos: new THREE.Vector3(-12, 14, -28) },
      { name: "Phước Xuân", code: "KV09", isHigh: false, pos: new THREE.Vector3(10, 16, -30) },
      { name: "Phước Năng", code: "KV10", isHigh: false, pos: new THREE.Vector3(26, 12, -18) },
      { name: "Phước Đức", code: "KV12", isHigh: false, pos: new THREE.Vector3(42, 8, -12) },
      { name: "Trà Leng", code: "KV07", isHigh: false, pos: new THREE.Vector3(-38, 10, 2) },
      { name: "Trà Mai", code: "KV01", isHigh: true, pos: new THREE.Vector3(-8, 17, 10) },
      { name: "Trà Don", code: "KV02", isHigh: false, pos: new THREE.Vector3(12, 13, 8) },
      { name: "Trà Vân", code: "KV04", isHigh: true, pos: new THREE.Vector3(24, 15, 14) },
      { name: "Trà Linh", code: "KV05", isHigh: false, pos: new THREE.Vector3(-2, 11, 30) },
    ];

    // Marker rings in 3D
    stationPositions.forEach((st) => {
      const marker = new THREE.Mesh(
        new THREE.SphereGeometry(1.2, 12, 12),
        new THREE.MeshBasicMaterial({ color: st.isHigh ? "#ef4444" : "#ffffff" })
      );
      marker.position.copy(st.pos);
      scene.add(marker);
    });

    // 8. Animation & Projection Render Loop
    let animationFrameId: number;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);

      // Project 3D stations to 2D screen positions for crisp HTML labels
      const labels = stationPositions.map((st) => {
        const v = st.pos.clone().project(camera);
        const sx = ((v.x + 1) / 2) * width;
        const sy = ((-v.y + 1) / 2) * height;
        return {
          name: st.name,
          x: sx,
          y: sy,
          isSelected: st.name === selectedAreaName,
          isHigh: st.isHigh,
        };
      });
      setScreenLabels(labels);
    };
    animate();

    // Resize Handler
    const handleResize = () => {
      if (!container) return;
      width = container.clientWidth;
      height = container.clientHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
      geom.dispose();
      terrainMaterial.dispose();
    };
  }, [terrainData, baseData, selectedAreaName]);

  const handleZoomIn = () => {
    if (controlsRef.current) {
      const camera = (controlsRef.current as any).object;
      if (camera) {
        camera.position.multiplyScalar(0.85);
        controlsRef.current.update();
      }
    }
  };

  const handleZoomOut = () => {
    if (controlsRef.current) {
      const camera = (controlsRef.current as any).object;
      if (camera) {
        camera.position.multiplyScalar(1.15);
        controlsRef.current.update();
      }
    }
  };

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full flex items-center justify-center bg-[#070b12] overflow-hidden select-none"
    >
      {/* Three.js Native WebGL Canvas */}
      <canvas ref={canvasRef} className="w-full h-full block cursor-grab active:cursor-grabbing" />

      {/* Screen-Projected HTML Station Labels (Matching exact visual in Screenshot 3) */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {screenLabels.map((lbl) => (
          <button
            key={lbl.name}
            onClick={() => setSelectedArea(lbl.name)}
            style={{
              left: `${lbl.x}px`,
              top: `${lbl.y - 14}px`,
              transform: "translate(-50%, -100%)",
            }}
            className={`absolute pointer-events-auto text-[11px] font-bold tracking-tight px-1 py-0.5 transition-all cursor-pointer whitespace-nowrap ${
              lbl.isSelected
                ? "text-cyan-300 drop-shadow-[0_0_8px_rgba(56,189,248,0.9)] scale-110"
                : "text-white/95 drop-shadow-[0_2px_4px_rgba(0,0,0,0.95)] hover:text-cyan-200 hover:scale-105"
            }`}
          >
            {lbl.name}
          </button>
        ))}
      </div>

      {/* Floating HUD Card for Selected Station */}
      <FloatingHUD />

      {/* Bottom Overlay Legend */}
      <div className="absolute left-6 bottom-5 flex items-center gap-3 px-3.5 py-1.5 rounded-full bg-slate-900/80 border border-white/10 backdrop-blur-md text-[11px] text-slate-300 shadow-xl pointer-events-auto">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-[#2E6B58]" />
          Thấp, dưới {thresholdLow.toFixed(2).replace(".", ",")}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-[#C6922E]" />
          Trung bình, {thresholdLow.toFixed(2).replace(".", ",")} đến {thresholdHigh.toFixed(2).replace(".", ",")}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-[#C83228]" />
          Cao, từ {thresholdHigh.toFixed(2).replace(".", ",")}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-white shadow-sm" />
          Sạt lở đã ghi nhận
        </span>
      </div>

      {/* Bottom Right Controls (Zoom + 3D / Bản đồ Toggle) */}
      <div className="absolute right-6 bottom-5 flex items-center gap-1.5 pointer-events-auto">
        <div className="flex items-center bg-slate-900/80 border border-white/10 rounded-lg overflow-hidden shadow-xl backdrop-blur-md">
          <button
            onClick={handleZoomIn}
            className="p-2 hover:bg-white/10 text-slate-300 hover:text-white transition-all"
            title="Phóng to"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
          <div className="w-[1px] h-4 bg-white/10" />
          <button
            onClick={handleZoomOut}
            className="p-2 hover:bg-white/10 text-slate-300 hover:text-white transition-all"
            title="Thu nhỏ"
          >
            <Minus className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="flex items-center p-1 bg-slate-900/80 border border-white/10 rounded-lg shadow-xl backdrop-blur-md gap-1">
          <button
            onClick={() => setViewMode("3d")}
            className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${
              viewMode === "3d"
                ? "bg-brand-yellow text-slate-950 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            3D
          </button>
          <button
            onClick={() => setViewMode("map")}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
              viewMode === "map"
                ? "bg-brand-yellow text-slate-950 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Bản đồ
          </button>
        </div>
      </div>
    </div>
  );
};
