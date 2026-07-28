import * as THREE from "./vendor/three.module.min.js";

const canvas = document.querySelector("#seven-space");
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

if (canvas && window.WebGLRenderingContext) {
  try {
    const renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: true,
      powerPreference: "low-power",
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.6));

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 100);
    camera.position.set(0, 0, 8);

    const rig = new THREE.Group();
    scene.add(rig);

    const positions = [];
    const colours = [];
    const cyan = new THREE.Color(0x68ebff);
    const violet = new THREE.Color(0xa88aff);
    for (let index = 0; index < 520; index += 1) {
      positions.push(
        (Math.random() - 0.5) * 16,
        (Math.random() - 0.5) * 10,
        (Math.random() - 0.5) * 5
      );
      const colour = index % 4 === 0 ? violet : cyan;
      colours.push(colour.r, colour.g, colour.b);
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute("color", new THREE.Float32BufferAttribute(colours, 3));
    const particles = new THREE.Points(
      geometry,
      new THREE.PointsMaterial({
        size: 0.022,
        vertexColors: true,
        transparent: true,
        opacity: 0.46,
        depthWrite: false,
      })
    );
    rig.add(particles);

    const rings = new THREE.Group();
    for (let index = 0; index < 4; index += 1) {
      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(1.4 + index * 0.58, 0.008, 5, 140),
        new THREE.MeshBasicMaterial({
          color: index % 2 ? 0xa88aff : 0x68ebff,
          transparent: true,
          opacity: 0.09 + index * 0.018,
        })
      );
      ring.rotation.set(1.14 + index * 0.13, 0.2 * index, 0.15 * index);
      rings.add(ring);
    }
    rings.position.set(-3.2, 0.5, -1);
    rig.add(rings);

    let state = "disconnected";
    let pointerX = 0;
    let pointerY = 0;
    const clock = new THREE.Clock();
    const stateSpeed = {
      disconnected: 0.2,
      connecting: 0.65,
      ready: 0.38,
      thinking: 1.15,
      listening: 0.9,
      speaking: 1.35,
      error: 0.22,
    };

    function resize() {
      const width = Math.max(1, window.innerWidth);
      const height = Math.max(1, window.innerHeight);
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    }

    function render() {
      const elapsed = clock.getElapsedTime();
      const speed = stateSpeed[state] || 0.4;
      rig.rotation.y += (pointerX * 0.045 - rig.rotation.y) * 0.025;
      rig.rotation.x += (-pointerY * 0.025 - rig.rotation.x) * 0.025;
      particles.rotation.y = elapsed * 0.012 * speed;
      particles.position.y = Math.sin(elapsed * 0.23) * 0.1;
      rings.rotation.z = elapsed * 0.025 * speed;
      renderer.render(scene, camera);
      if (!reducedMotion) requestAnimationFrame(render);
    }

    window.addEventListener("resize", resize);
    window.addEventListener("pointermove", (event) => {
      pointerX = event.clientX / Math.max(1, window.innerWidth) - 0.5;
      pointerY = event.clientY / Math.max(1, window.innerHeight) - 0.5;
    }, { passive: true });
    window.addEventListener("seven-state", (event) => {
      state = event.detail?.state || "ready";
      const colour =
        state === "thinking" ? 0xffd078 :
        state === "listening" ? 0xff78b5 :
        state === "speaking" ? 0xa88aff :
        state === "error" ? 0xff716f : 0x68ebff;
      rings.children.forEach((ring, index) => {
        ring.material.color.set(index % 2 ? 0xa88aff : colour);
        ring.material.opacity = state === "thinking" || state === "speaking" ? 0.18 : 0.1;
      });
    });

    resize();
    render();
    if (reducedMotion) renderer.render(scene, camera);
  } catch {
    canvas.hidden = true;
  }
}
