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
  const terrainMeshRef = useRef<THREE.Mesh | null>(null);
  const hazardGroupRef = useRef<THREE.Group | null>(null);
  const stationsRef = useRef<Array<{ name: string; code: string; isHigh: boolean; pos: THREE.Vector3 }>>([]);

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

  const simDataRef = useRef(simData);
  simDataRef.current = simData;
  const selectedAreaNameRef = useRef(selectedAreaName);
  selectedAreaNameRef.current = selectedAreaName;

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

    // 3. Cinematic Lights matching dark theme
    const ambientLight = new THREE.AmbientLight("#475569", 1.8);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight("#ffffff", 2.2);
    sunLight.position.set(60, 95, 45);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 2048;
    sunLight.shadow.mapSize.height = 2048;
    sunLight.shadow.bias = -0.0004;
    scene.add(sunLight);

    const rimLight = new THREE.DirectionalLight("#38bdf8", 1.4);
    rimLight.position.set(-70, 45, -60);
    scene.add(rimLight);

    const bounceLight = new THREE.DirectionalLight("#a855f7", 0.7);
    bounceLight.position.set(0, -30, 20);
    scene.add(bounceLight);

    // 4. Procedural 3D Terrain Relief Island (72x72)
    const rows = terrainData?.rows || 72;
    const cols = terrainData?.cols || 72;
    const geom = new THREE.PlaneGeometry(80, 80, cols - 1, rows - 1);
    geom.rotateX(-Math.PI / 2);

    const pos = geom.getAttribute("position");
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

      // Dynamic AI risk score color mapping
      const riskVal = simData?.grid_risk?.[i] !== undefined ? simData.grid_risk[i] : 0.12;
      const c = new THREE.Color();
      if (riskVal >= thresholdHigh) {
        const t = Math.min(1, (riskVal - thresholdHigh) / Math.max(0.01, 1 - thresholdHigh));
        c.lerpColors(colorMid, colorHigh, 0.35 + 0.65 * t);
      } else if (riskVal >= thresholdLow) {
        const t = (riskVal - thresholdLow) / Math.max(0.01, thresholdHigh - thresholdLow);
        c.lerpColors(colorLow, colorMid, t);
      } else {
        c.copy(colorLow);
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
    terrainMeshRef.current = terrainMesh;

    // 5. Historical Landslide White Dots (mapped dynamically from baseData.events)
    const dotGeom = new THREE.SphereGeometry(0.55, 8, 8);
    const dotMat = new THREE.MeshBasicMaterial({ color: "#ffffff" });
    const events = baseData?.events || [];

    if (events.length > 0) {
      events.forEach((ev) => {
        const u = Math.max(0, Math.min(1, (ev.lon - bounds.lon_min) / (bounds.lon_max - bounds.lon_min)));
        const v = Math.max(0, Math.min(1, 1 - (ev.lat - bounds.lat_min) / (bounds.lat_max - bounds.lat_min)));
        const x = (u - 0.5) * 80;
        const z = (v - 0.5) * 80;

        const col = Math.max(0, Math.min(cols - 1, Math.round(u * (cols - 1))));
        const row = Math.max(0, Math.min(rows - 1, Math.round(v * (rows - 1))));
        const vIdx = row * cols + col;
        const rawH = elev[vIdx] || 400;
        const normH = Math.max(0, (rawH - elevMin) / elevRange);
        const dx = (u - 0.5) * 2;
        const dy = (v - 0.5) * 2;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const falloff = dist < 0.72 ? 1 : Math.max(0, Math.cos(((dist - 0.72) / 0.28) * (Math.PI / 2)));
        const y = normH * 31 * falloff;

        const dot = new THREE.Mesh(dotGeom, dotMat);
        dot.position.set(x, y + 0.45, z);
        scene.add(dot);
      });
    } else {
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
    }

    // 6. Dynamic Hazard Group for real-time AI danger beacons
    const hazardGroup = new THREE.Group();
    scene.add(hazardGroup);
    hazardGroupRef.current = hazardGroup;

    // 7. Station 3D Anchor Positions for projection
    const stationDefs = [
      { name: "Phước Mỹ", code: "KV07", lat: 15.38, lon: 107.88 },
      { name: "Phước Xuân", code: "KV11", lat: 15.43, lon: 107.92 },
      { name: "Phước Năng", code: "KV10", lat: 15.40, lon: 108.00 },
      { name: "Phước Đức", code: "KV12", lat: 15.34, lon: 108.12 },
      { name: "Phước Chánh", code: "KV08", lat: 15.29, lon: 107.90 },
      { name: "Phước Công", code: "KV09", lat: 15.29, lon: 107.84 },
      { name: "Trà Leng", code: "KV03", lat: 15.10, lon: 107.94 },
      { name: "Trà Mai", code: "KV01", lat: 15.11, lon: 108.01 },
      { name: "Trà Tập", code: "KV06", lat: 15.19, lon: 108.01 },
      { name: "Trà Don", code: "KV02", lat: 15.20, lon: 108.09 },
      { name: "Trà Vân", code: "KV04", lat: 15.18, lon: 108.15 },
      { name: "Trà Linh", code: "KV05", lat: 15.07, lon: 108.12 },
    ];

    const stationPositions = stationDefs.map((st) => {
      const u = Math.max(0, Math.min(1, (st.lon - bounds.lon_min) / (bounds.lon_max - bounds.lon_min)));
      const v = Math.max(0, Math.min(1, 1 - (st.lat - bounds.lat_min) / (bounds.lat_max - bounds.lat_min)));
      const x = (u - 0.5) * 80;
      const z = (v - 0.5) * 80;

      const col = Math.max(0, Math.min(cols - 1, Math.round(u * (cols - 1))));
      const row = Math.max(0, Math.min(rows - 1, Math.round(v * (rows - 1))));
      const vIdx = row * cols + col;
      const rawH = elev[vIdx] || 400;
      const normH = Math.max(0, (rawH - elevMin) / elevRange);
      const dx = (u - 0.5) * 2;
      const dy = (v - 0.5) * 2;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const falloff = dist < 0.72 ? 1 : Math.max(0, Math.cos(((dist - 0.72) / 0.28) * (Math.PI / 2)));
      const y = normH * 31 * falloff;

      return {
        name: st.name,
        code: st.code,
        isHigh: false,
        pos: new THREE.Vector3(x, y + 1.2, z),
      };
    });
    stationsRef.current = stationPositions;

    // Marker rings in 3D
    stationPositions.forEach((st) => {
      const marker = new THREE.Mesh(
        new THREE.SphereGeometry(1.0, 10, 10),
        new THREE.MeshBasicMaterial({ color: "#ffffff", transparent: true, opacity: 0.9 })
      );
      marker.position.copy(st.pos);
      scene.add(marker);
    });

    // 8. Animation & Projection Render Loop
    let animationFrameId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      controls.update();

      // Pulsate active hazard beacons
      if (hazardGroupRef.current && hazardGroupRef.current.children.length > 0) {
        const t = clock.getElapsedTime();
        const pulse = 1 + Math.sin(t * 5) * 0.18;
        hazardGroupRef.current.children.forEach((child) => {
          if (child.name === "beaconHead") {
            child.scale.set(pulse, pulse, pulse);
          } else if (child.name === "hazardRing") {
            const rPulse = 1 + Math.sin(t * 3.5) * 0.22;
            child.scale.set(rPulse, rPulse, rPulse);
          }
        });
      }

      renderer.render(scene, camera);

      // Project 3D stations to 2D screen positions for crisp HTML labels
      const labels = stationPositions.map((st) => {
        const v = st.pos.clone().project(camera);
        const sx = ((v.x + 1) / 2) * width;
        const sy = ((-v.y + 1) / 2) * height;
        const areaData = simDataRef.current?.areas?.find((a) => a.name === st.name);
        const isHigh = areaData ? areaData.level === "Cao" : false;
        return {
          name: st.name,
          x: sx,
          y: sy,
          isSelected: st.name === selectedAreaNameRef.current,
          isHigh,
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
      terrainMeshRef.current = null;
      hazardGroupRef.current = null;
    };
  }, [terrainData, baseData]);

  // Dynamic updates to 3D terrain vertex colors & active hazard beacons when AI results change
  useEffect(() => {
    // 1. Update vertex colors
    if (terrainMeshRef.current && simData?.grid_risk) {
      const mesh = terrainMeshRef.current;
      const geom = mesh.geometry;
      const colorAttr = geom.getAttribute("color") as THREE.BufferAttribute;
      if (colorAttr) {
        const arr = colorAttr.array as Float32Array;
        const count = arr.length / 3;
        const colorLow = new THREE.Color("#2E6B58");
        const colorMid = new THREE.Color("#C6922E");
        const colorHigh = new THREE.Color("#C83228");
        const c = new THREE.Color();

        for (let i = 0; i < count; i++) {
          const riskVal = simData.grid_risk[i] !== undefined ? simData.grid_risk[i] : 0.12;
          if (riskVal >= thresholdHigh) {
            const t = Math.min(1, (riskVal - thresholdHigh) / Math.max(0.01, 1 - thresholdHigh));
            c.lerpColors(colorMid, colorHigh, 0.35 + 0.65 * t);
          } else if (riskVal >= thresholdLow) {
            const t = (riskVal - thresholdLow) / Math.max(0.01, thresholdHigh - thresholdLow);
            c.lerpColors(colorLow, colorMid, t);
          } else {
            c.copy(colorLow);
          }
          arr[i * 3] = c.r;
          arr[i * 3 + 1] = c.g;
          arr[i * 3 + 2] = c.b;
        }
        colorAttr.needsUpdate = true;
      }
    }

    // 2. DYNAMICALLY UPDATE ACTIVE HAZARD BEACONS
    if (hazardGroupRef.current && stationsRef.current.length > 0) {
      const hg = hazardGroupRef.current;
      // Clear previous hazard beacon meshes
      while (hg.children.length > 0) {
        const obj = hg.children[0] as THREE.Mesh;
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) {
          if (Array.isArray(obj.material)) obj.material.forEach((m) => m.dispose());
          else obj.material.dispose();
        }
        hg.remove(obj);
      }

      // Find all areas that have reached High risk
      const highAreas = (simData?.areas || []).filter(
        (a) => a.level === "Cao" || (a.score !== undefined && a.score >= thresholdHigh)
      );

      highAreas.forEach((st) => {
        const match = stationsRef.current.find((p) => p.name === st.name);
        if (match) {
          const px = match.pos.x;
          const py = match.pos.y;
          const pz = match.pos.z;
          const beaconH = 22 + Math.min(14, ((st.score || 0.45) - thresholdHigh) * 40);

          // Red vertical needle line
          const lineGeom = new THREE.CylinderGeometry(0.24, 0.24, beaconH, 8);
          const lineMat = new THREE.MeshBasicMaterial({ color: "#ef4444", transparent: true, opacity: 0.9 });
          const needle = new THREE.Mesh(lineGeom, lineMat);
          needle.position.set(px, py + beaconH / 2, pz);
          hg.add(needle);

          // Glowing danger head sphere on top
          const headGeom = new THREE.SphereGeometry(1.2, 12, 12);
          const headMat = new THREE.MeshBasicMaterial({ color: "#ff2222" });
          const head = new THREE.Mesh(headGeom, headMat);
          head.name = "beaconHead";
          head.position.set(px, py + beaconH, pz);
          hg.add(head);

          // Pulsing ground hazard warning ring
          const ringGeom = new THREE.RingGeometry(1.8, 3.2, 24);
          ringGeom.rotateX(-Math.PI / 2);
          const ringMat = new THREE.MeshBasicMaterial({ color: "#ef4444", side: THREE.DoubleSide, transparent: true, opacity: 0.75 });
          const ring = new THREE.Mesh(ringGeom, ringMat);
          ring.name = "hazardRing";
          ring.position.set(px, py + 0.15, pz);
          hg.add(ring);
        }
      });
    }
  }, [simData, thresholdLow, thresholdHigh]);

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
    <div ref={containerRef} className="relative w-full h-full bg-[#06080c] overflow-hidden select-none">
      {/* Three.js Canvas */}
      <canvas ref={canvasRef} className="w-full h-full block cursor-grab active:cursor-grabbing" />

      {/* 2D Projected Station Labels Layer */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {screenLabels.map((st) => {
          if (st.x < 10 || st.x > (containerRef.current?.clientWidth || 800) - 10) return null;
          if (st.y < 10 || st.y > (containerRef.current?.clientHeight || 600) - 10) return null;

          return (
            <div
              key={st.name}
              style={{
                left: `${st.x}px`,
                top: `${st.y}px`,
                transform: "translate(-50%, -100%) translateY(-10px)",
              }}
              onClick={() => setSelectedArea(st.name)}
              className={`absolute pointer-events-auto text-[11px] font-bold tracking-tight px-2 py-0.5 transition-all cursor-pointer whitespace-nowrap rounded-md shadow-lg ${
                st.isSelected
                  ? "bg-cyan-500 text-slate-950 ring-2 ring-white scale-110 z-30"
                  : st.isHigh
                  ? "bg-[#ef4444] text-white ring-1 ring-white/50 animate-pulse z-20"
                  : "bg-slate-900/80 text-slate-200 border border-white/20 hover:bg-slate-800 hover:text-white z-10"
              }`}
            >
              <span>{st.name}</span>
            </div>
          );
        })}
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
          Sạt lở đã ghi nhận (46 điểm)
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

        <div className="flex items-center bg-slate-900/80 border border-white/10 rounded-lg p-0.5 shadow-xl backdrop-blur-md">
          <button
            onClick={() => setViewMode("3d")}
            className={`px-3 py-1.5 text-xs font-bold rounded-md transition-all ${
              viewMode === "3d"
                ? "bg-brand-yellow text-slate-950 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            3D
          </button>
          <button
            onClick={() => setViewMode("map")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
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
