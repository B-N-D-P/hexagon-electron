import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface Vector3DProps {
  data: any;
}

const Vector3D: React.FC<Vector3DProps> = ({ data }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const arrowRef = useRef<THREE.ArrowHelper | null>(null);
  const cubeRef = useRef<THREE.Mesh | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Scene setup
    if (!sceneRef.current) {
      sceneRef.current = new THREE.Scene();
      sceneRef.current.background = new THREE.Color(0x0a0e27);

      cameraRef.current = new THREE.PerspectiveCamera(
        75,
        containerRef.current.clientWidth / containerRef.current.clientHeight,
        0.1,
        1000
      );
      cameraRef.current.position.z = 2;

      rendererRef.current = new THREE.WebGLRenderer({ antialias: true });
      rendererRef.current.setSize(
        containerRef.current.clientWidth,
        containerRef.current.clientHeight
      );
      containerRef.current.appendChild(rendererRef.current.domElement);

      // Add lighting
      const light = new THREE.DirectionalLight(0xffffff, 0.8);
      light.position.set(5, 5, 5);
      sceneRef.current.add(light);

      const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
      sceneRef.current.add(ambientLight);

      // Create cube
      const geometry = new THREE.BoxGeometry(0.8, 0.8, 0.8);
      const material = new THREE.MeshPhongMaterial({
        color: 0x00d9ff,
        wireframe: true,
      });
      cubeRef.current = new THREE.Mesh(geometry, material);
      sceneRef.current.add(cubeRef.current);

      // Animation loop
      const animate = () => {
        requestAnimationFrame(animate);

        if (cubeRef.current) {
          cubeRef.current.rotation.x += 0.005;
          cubeRef.current.rotation.y += 0.008;
        }

        if (rendererRef.current && cameraRef.current) {
          rendererRef.current.render(sceneRef.current!, cameraRef.current);
        }
      };
      animate();
    }

    // Update arrow based on data
    if (
      data &&
      data.sensor_1 &&
      data.sensor_1.axes &&
      sceneRef.current
    ) {
      const axes = data.sensor_1.axes;
      const x = (axes.x?.[axes.x.length - 1] || 0) / 10;
      const y = (axes.y?.[axes.y.length - 1] || 0) / 10;
      const z = (axes.z?.[axes.z.length - 1] || 0) / 10;

      // Remove old arrow
      if (arrowRef.current) {
        sceneRef.current.remove(arrowRef.current);
      }

      // Create new arrow
      const direction = new THREE.Vector3(x, y, z).normalize();
      const length = Math.sqrt(x * x + y * y + z * z);
      const color = Math.min(length * 100, 1) * 0xffffff;

      arrowRef.current = new THREE.ArrowHelper(
        direction,
        new THREE.Vector3(0, 0, 0),
        Math.max(length, 0.1),
        color,
        0.2,
        0.15
      );
      sceneRef.current.add(arrowRef.current);
    }

    return () => {
      // Dispose of Three.js resources
      if (rendererRef.current) {
        rendererRef.current.dispose();
      }
      
      if (sceneRef.current) {
        sceneRef.current.clear();
      }
      
      if (cubeRef.current) {
        if (cubeRef.current.geometry) cubeRef.current.geometry.dispose();
        if (cubeRef.current.material) cubeRef.current.material.dispose();
      }
      
      if (arrowRef.current) {
        if (arrowRef.current.geometry) arrowRef.current.geometry.dispose();
        if (arrowRef.current.material) arrowRef.current.material.dispose();
      }
      
      // Remove DOM element
      if (containerRef.current && rendererRef.current?.domElement) {
        try {
          containerRef.current.removeChild(rendererRef.current.domElement);
        } catch (e) {
          // Already removed
        }
      }
    };
  }, [data]);

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: '300px',
        borderRadius: '8px',
        overflow: 'hidden',
      }}
    />
  );
};

export default Vector3D;
