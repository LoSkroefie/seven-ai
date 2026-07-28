import * as THREE from "three";

const STATE_COLOURS = {
  disconnected: 0x70818b,
  connecting: 0x78b8ff,
  connected: 0x62f6be,
  ready: 0x74edff,
  thinking: 0xffd76a,
  listening: 0xff75b9,
  speaking: 0xa487ff,
  error: 0xff6b68,
};

export function createSevenAvatar(canvas) {
  if (!canvas || !window.WebGLRenderingContext) {
    return { setState() {}, start() {}, stop() {}, destroy() {} };
  }

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: "low-power" });
  } catch {
    return { setState() {}, start() {}, stop() {}, destroy() {} };
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.7));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
  camera.position.set(0, 0.2, 7.2);

  const rig = new THREE.Group();
  rig.position.set(-2.6, 0, 0);
  scene.add(rig);

  const material = new THREE.MeshPhysicalMaterial({
    color: 0x122837,
    emissive: 0x74edff,
    emissiveIntensity: 0.35,
    roughness: 0.35,
    metalness: 0.55,
    transparent: true,
    opacity: 0.92,
  });
  const wire = new THREE.MeshBasicMaterial({ color: 0x74edff, wireframe: true, transparent: true, opacity: 0.22 });
  const head = new THREE.Mesh(new THREE.IcosahedronGeometry(0.78, 3), material);
  head.position.y = 1.3;
  rig.add(head);
  const headWire = new THREE.Mesh(head.geometry, wire);
  head.add(headWire);

  const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 1.18, 2.1, 7, 2, true), material);
  torso.position.y = -0.35;
  torso.scale.z = 0.52;
  rig.add(torso);
  const torsoWire = new THREE.Mesh(torso.geometry, wire);
  torso.add(torsoWire);

  const halo = new THREE.Mesh(
    new THREE.TorusGeometry(1.2, 0.018, 8, 120),
    new THREE.MeshBasicMaterial({ color: 0x74edff, transparent: true, opacity: 0.72 })
  );
  halo.position.y = 1.3;
  halo.rotation.x = Math.PI / 2.45;
  rig.add(halo);

  const eyeMaterial = new THREE.MeshBasicMaterial({ color: 0xeaffff });
  [-0.24, 0.24].forEach((x) => {
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.052, 12, 8), eyeMaterial);
    eye.position.set(x, 1.39, 0.72);
    rig.add(eye);
  });

  const points = [];
  for (let index = 0; index < 220; index += 1) {
    const angle = Math.random() * Math.PI * 2;
    const radius = 1.5 + Math.random() * 2.4;
    points.push(Math.cos(angle) * radius, (Math.random() - 0.5) * 5.4, Math.sin(angle) * radius * 0.35);
  }
  const particleGeometry = new THREE.BufferGeometry();
  particleGeometry.setAttribute("position", new THREE.Float32BufferAttribute(points, 3));
  const particles = new THREE.Points(
    particleGeometry,
    new THREE.PointsMaterial({ color: 0x74edff, size: 0.024, transparent: true, opacity: 0.46 })
  );
  rig.add(particles);

  scene.add(new THREE.AmbientLight(0x9ddcff, 0.7));
  const light = new THREE.PointLight(0xa487ff, 5, 12);
  light.position.set(-3, 3, 4);
  scene.add(light);

  let state = "disconnected";
  let running = false;
  let frame = 0;
  const clock = new THREE.Clock();

  function resize() {
    const width = Math.max(1, canvas.clientWidth);
    const height = Math.max(1, canvas.clientHeight);
    if (canvas.width !== Math.round(width * renderer.getPixelRatio()) || canvas.height !== Math.round(height * renderer.getPixelRatio())) {
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      rig.position.x = width < 900 ? 0 : -2.65;
      rig.position.y = width < 900 ? 0.15 : -0.05;
    }
  }

  function render() {
    if (!running) return;
    const elapsed = clock.getElapsedTime();
    const activity = state === "thinking" || state === "listening" || state === "speaking" ? 1.8 : 1;
    head.rotation.y = Math.sin(elapsed * 0.42) * 0.16;
    head.position.y = 1.3 + Math.sin(elapsed * activity) * 0.035;
    halo.rotation.z = elapsed * 0.16 * activity;
    particles.rotation.y = elapsed * 0.028 * activity;
    torso.scale.x = 1 + Math.sin(elapsed * 1.35) * 0.012;
    renderer.render(scene, camera);
    frame = requestAnimationFrame(render);
  }

  function setState(nextState) {
    state = STATE_COLOURS[nextState] ? nextState : "disconnected";
    const colour = new THREE.Color(STATE_COLOURS[state]);
    material.emissive.copy(colour);
    wire.color.copy(colour);
    halo.material.color.copy(colour);
    particles.material.color.copy(colour);
    light.color.copy(colour);
    material.emissiveIntensity = state === "thinking" || state === "speaking" ? 0.75 : 0.35;
  }

  function start() {
    if (running) return;
    running = true;
    clock.start();
    resize();
    render();
  }

  function stop() {
    running = false;
    cancelAnimationFrame(frame);
  }

  const observer = "ResizeObserver" in window ? new ResizeObserver(resize) : null;
  observer?.observe(canvas);
  if (!observer) window.addEventListener("resize", resize);
  setState("disconnected");

  return {
    setState,
    start,
    stop,
    destroy() {
      stop();
      observer?.disconnect();
      if (!observer) window.removeEventListener("resize", resize);
      particleGeometry.dispose();
      head.geometry.dispose();
      torso.geometry.dispose();
      halo.geometry.dispose();
      material.dispose();
      wire.dispose();
      eyeMaterial.dispose();
      halo.material.dispose();
      particles.material.dispose();
      renderer.dispose();
    },
  };
}
