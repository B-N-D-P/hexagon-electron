import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

export default function StructureViewer3D({ dwgData, sensors, onSensorPlace, selectedSensorId }) {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const sensorMeshesRef = useRef({});
  const draggingSensorRef = useRef(null);
  const [draggingSensor, setDraggingSensor] = useState(null);

  useEffect(() => {
    if (!containerRef.current || !dwgData) return;

    // Initialize Three.js scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1e293b);
    sceneRef.current = scene;

    // Camera setup
    const bounds = dwgData.bounds;
    const camera = new THREE.PerspectiveCamera(
      75,
      containerRef.current.clientWidth / containerRef.current.clientHeight,
      0.1,
      10000
    );
    cameraRef.current = camera;

    // Position camera to view entire structure
    const maxDim = Math.max(
      bounds.size[0],
      bounds.size[1],
      bounds.size[2]
    );
    const fov = camera.fov * (Math.PI / 180);
    let distance = maxDim / 2 / Math.tan(fov / 2);
    distance *= 1.5; // Add zoom out factor

    camera.position.set(
      bounds.center[0] + distance / 2,
      bounds.center[1] + distance / 2,
      bounds.center[2] + distance
    );
    camera.lookAt(...bounds.center);

    // Renderer setup
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    renderer.shadowMap.enabled = true;
    rendererRef.current = renderer;
    containerRef.current.appendChild(renderer.domElement);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(distance, distance, distance);
    directionalLight.castShadow = true;
    scene.add(directionalLight);

    // Draw beams and columns
    drawStructure(scene, dwgData);

    // Add grid
    const gridHelper = new THREE.GridHelper(maxDim * 2, 20, 0x444444, 0x222222);
    gridHelper.position.set(...bounds.center);
    scene.add(gridHelper);

    // Add axes helper
    const axesHelper = new THREE.AxesHelper(maxDim / 2);
    axesHelper.position.set(...bounds.center);
    scene.add(axesHelper);

    // Create sensor meshes
    updateSensorMeshes(scene, sensors, selectedSensorId);

    // Mouse interaction
    let raycaster = new THREE.Raycaster();
    let mouse = new THREE.Vector2();

    function onMouseMove(event) {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      if (draggingSensorRef.current) {
        raycaster.setFromCamera(mouse, camera);
        // Project to a plane at sensor's current Z
        const planeNormal = new THREE.Vector3(0, 0, 1);
        const plane = new THREE.Plane(planeNormal, -draggingSensorRef.current.z);
        const intersection = new THREE.Vector3();
        raycaster.ray.intersectPlane(plane, intersection);
        
        // Update sensor position
        onSensorPlace(draggingSensorRef.current.id, {
          x: intersection.x - dwgData.origin[0],
          y: intersection.y - dwgData.origin[1],
          z: draggingSensorRef.current.z
        });
      }
    }

    function onMouseDown(event) {
      raycaster.setFromCamera(mouse, camera);
      const meshes = Object.values(sensorMeshesRef.current).map(m => m.mesh);
      const intersects = raycaster.intersectObjects(meshes);

      if (intersects.length > 0) {
        const sensorMesh = intersects[0].object;
        const sensorId = sensorMesh.userData.sensorId;
        const sensor = sensors.find(s => s.id === sensorId);
        draggingSensorRef.current = sensor;
        setDraggingSensor(sensor);
      }
    }

    function onMouseUp() {
      draggingSensorRef.current = null;
      setDraggingSensor(null);
    }

    renderer.domElement.addEventListener('mousemove', onMouseMove);
    renderer.domElement.addEventListener('mousedown', onMouseDown);
    renderer.domElement.addEventListener('mouseup', onMouseUp);

    // Animation loop
    function animate() {
      requestAnimationFrame(animate);
      renderer.render(scene, camera);
    }
    animate();

    // Handle window resize
    function onWindowResize() {
      if (!containerRef.current) return;
      const width = containerRef.current.clientWidth;
      const height = containerRef.current.clientHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    }

    window.addEventListener('resize', onWindowResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', onWindowResize);
      renderer.domElement.removeEventListener('mousemove', onMouseMove);
      renderer.domElement.removeEventListener('mousedown', onMouseDown);
      renderer.domElement.removeEventListener('mouseup', onMouseUp);
      if (containerRef.current && renderer.domElement.parentNode === containerRef.current) {
        containerRef.current.removeChild(renderer.domElement);
      }
    };
  }, [dwgData]);

  // Update sensor meshes when sensors change
  useEffect(() => {
    if (sceneRef.current) {
      updateSensorMeshes(sceneRef.current, sensors, selectedSensorId);
    }
  }, [sensors, selectedSensorId]);

  function drawStructure(scene, dwgData) {
    // Validate dwgData
    if (!dwgData || !dwgData.beams || !dwgData.columns) {
      console.error('Invalid dwgData:', dwgData);
      return;
    }
    
    // Draw beams (cyan/teal)
    dwgData.beams.forEach(beam => {
      if (beam.type === 'line') {
        const geometry = new THREE.BufferGeometry();
        const points = [
          new THREE.Vector3(...beam.start),
          new THREE.Vector3(...beam.end)
        ];
        geometry.setFromPoints(points);
        const material = new THREE.LineBasicMaterial({ color: 0x4ECDC4, linewidth: 3 });
        const line = new THREE.Line(geometry, material);
        scene.add(line);

        // Draw cylinder for beam
        const start = new THREE.Vector3(...beam.start);
        const end = new THREE.Vector3(...beam.end);
        const mid = start.clone().add(end).multiplyScalar(0.5);
        const length = start.distanceTo(end);
        const direction = end.clone().sub(start).normalize();
        
        const geometry2 = new THREE.CylinderGeometry(0.2, 0.2, length, 8);
        const material2 = new THREE.MeshPhongMaterial({ color: 0x4ECDC4, opacity: 0.3, transparent: true });
        const mesh = new THREE.Mesh(geometry2, material2);
        mesh.position.copy(mid);
        
        const axis = new THREE.Vector3(0, 1, 0);
        const quaternion = new THREE.Quaternion();
        quaternion.setFromUnitVectors(axis, direction);
        mesh.quaternion.copy(quaternion);
        
        scene.add(mesh);
      }
    });

    // Draw columns (red)
    dwgData.columns.forEach(column => {
      if (column.type === 'line') {
        const geometry = new THREE.BufferGeometry();
        const points = [
          new THREE.Vector3(...column.start),
          new THREE.Vector3(...column.end)
        ];
        geometry.setFromPoints(points);
        const material = new THREE.LineBasicMaterial({ color: 0xFF6B6B, linewidth: 3 });
        const line = new THREE.Line(geometry, material);
        scene.add(line);

        // Draw cylinder for column
        const start = new THREE.Vector3(...column.start);
        const end = new THREE.Vector3(...column.end);
        const mid = start.clone().add(end).multiplyScalar(0.5);
        const length = start.distanceTo(end);
        const direction = end.clone().sub(start).normalize();
        
        const geometry2 = new THREE.CylinderGeometry(0.3, 0.3, length, 8);
        const material2 = new THREE.MeshPhongMaterial({ color: 0xFF6B6B, opacity: 0.3, transparent: true });
        const mesh = new THREE.Mesh(geometry2, material2);
        mesh.position.copy(mid);
        
        const axis = new THREE.Vector3(0, 1, 0);
        const quaternion = new THREE.Quaternion();
        quaternion.setFromUnitVectors(axis, direction);
        mesh.quaternion.copy(quaternion);
        
        scene.add(mesh);
      }
    });

    // Draw origin point
    const originGeometry = new THREE.SphereGeometry(0.5, 16, 16);
    const originMaterial = new THREE.MeshBasicMaterial({ color: 0xFFFF00 });
    const origin = new THREE.Mesh(originGeometry, originMaterial);
    origin.position.set(...dwgData.origin);
    scene.add(origin);
  }

  function updateSensorMeshes(scene, sensors, selectedId) {
    // Remove old sensor meshes
    Object.values(sensorMeshesRef.current).forEach(({ mesh }) => {
      scene.remove(mesh);
    });
    sensorMeshesRef.current = {};

    // Add new sensor meshes
    sensors.forEach(sensor => {
      const geometry = new THREE.SphereGeometry(0.5, 16, 16);
      const color = selectedId === sensor.id ? 0x00FF00 : 0x3b82f6;
      const material = new THREE.MeshPhongMaterial({ color });
      const mesh = new THREE.Mesh(geometry, material);
      
      mesh.position.set(
        sensor.x + dwgData.origin[0],
        sensor.y + dwgData.origin[1],
        sensor.z + dwgData.origin[2]
      );
      mesh.userData.sensorId = sensor.id;
      
      scene.add(mesh);
      sensorMeshesRef.current[sensor.id] = { mesh, sensor };
    });
  }

  return <div ref={containerRef} className="w-full h-full" />;
}
