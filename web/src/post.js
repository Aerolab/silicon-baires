// The look: the same chain as 07_look.py's compositor, in one fullscreen pass.
//
//   blur radius from the Z pass  ->  grain (overlay)  ->  vignette (multiply)
//   ->  white balance  ->  exposure  ->  AgX
//
// ORDER MATTERS AND THIS IS THE ORDER BLENDER USES. The compositor runs on
// linear light and the view transform is applied after it, at display time. So
// the scene renders to a half-float target with tone mapping OFF, everything
// below happens in linear, and AgX is the last thing that touches the pixel.
// Grading first and blurring the graded image is a different picture: the
// blur would average tone-mapped values and the highlights would go grey.
//
// WHAT IS FAITHFUL AND WHAT IS NOT. The blur is the same construction as the
// compositor's: |depth - focus| / spread, raised to 1.7, clamped, times
// BLUR_MAX pixels, with spread proportional to the frame width so the effect
// is the same depth of the FRAME at every point of the move. The numbers come
// out of 07_look.py through the export, not out of this file.
//
// AgX is three.js' AgXToneMapping, which is Blender's AgX with the Base look.
// The .blend renders "AgX - Very High Contrast", and that look is a curve
// three does not ship, so it is approximated here by a contrast pivot in log
// space (LOOK_CONTRAST). It is the one place in this file that is a lookalike
// rather than a port, and it is the first knob to turn when the browser and
// the render disagree about contrast.
import * as THREE from "three";

// --- TONE MAPPING ----------------------------------------------------------
// THE ONE PLACE THE WEB DELIBERATELY DOES NOT MATCH THE RENDER.
//
// The .blend ships through AgX, and AgX is what makes the still read as a
// photograph: it rolls the highlights off instead of clipping them, and it
// desaturates as it goes. Ported faithfully, the page measured within
// tolerance on all five of the reference's numbers.
//
// It is not what this is for. The page is a toy city you can spin, not a frame
// in a film, and the AgX version reads dark and muted next to the plain linear
// one — the greens, the jacaranda purple and the title red all lose chroma at
// exactly the sizes a browser shows them at. So the web ships "none": linear
// light, clipped, a stop brighter, with the shadows open.
//
// Set to "agx" to get the render's grade back. The miniature blur, the grain
// and the vignette are the same either way; the exposure offset, the sky fill
// and the white balance are not, and each one says why below.
export const TONEMAP = "none";        // "none" | "agx"

// --- LOOK CALIBRATION ------------------------------------------------------
// Three numbers that are NOT in the .blend, because they exist to cancel out
// the difference between a path tracer and a rasteriser. They were fitted the
// way _common.GRADE was fitted — by measuring, against
// renders/city_07_look.png. Re-run it from the browser console:
//
//     window.look.env(0.95); window.look.exposure(0.10)
//     window.measure().table
//
//                     mean    std     dark    bright  sat     R/B
//   the render        0.470   0.247   24.0%   15.5%   0.388   1.329
//   TONEMAP "agx"     0.471   0.255   23.0%   15.0%   0.400   1.320
//   TONEMAP "none"    0.609   0.252   4.9%    33.0%   0.263   1.134
//
// The shipped row is the last one and it misses the reference on purpose: the
// page is a whole stop brighter with almost no dark pixels in it, where the
// render puts a quarter of the frame below 0.25. That is the look — lit, open
// shadows, clean colour — and the cost is in the bright column, a third of the
// frame above 0.75 with no rolloff holding it. The numbers are written down so
// it stays a decision instead of becoming a drift.
//
// It also matches ?nopost=1 to within the blur and the grain, which is the
// point: that URL is the reference for this mode.
//
// EXPOSURE_OFFSET is stops on top of whatever the .blend's grade says, rather
// than an absolute, so that changing EXPOSURE in _common.py still moves the
// browser. Under AgX it is +1.22 and that is not a fudge: Cycles bounces light
// and three does not, so the same scene arrives 1.2 stops darker before
// anything is graded. Clipped linear needs less of it back.
// Under "none" it cancels the .blend's own exposure exactly, so the page shows
// the light the scene actually has. AgX needs a stop and a bit put back.
export const EXPOSURE_OFFSET = TONEMAP === "agx" ? 1.22 : 0.82;
// The stand-in for "AgX - Very High Contrast", which three does not ship: a
// pivot around middle grey in log space. 1.0 is three's plain AgX, which
// measures 0.19 flatter in std than the reference.
// Only meaningful under AgX: it stands in for a look AgX has and three does
// not. Clipped linear has plenty of contrast of its own.
export const LOOK_CONTRAST = TONEMAP === "agx" ? 1.45 : 1.0;
// How much of the baked sky lights the city. Below 1 because a rasteriser
// applies the whole hemisphere to every surface at once, where Cycles lets the
// buildings shadow each other from it.
export const ENV_INTENSITY = TONEMAP === "agx" ? 0.85 : 1.0;

// The .blend's white balance warms the frame to match a reference clip that is
// warm. Under "none" the page is not chasing that clip, and the warmth on top
// of unrolled highlights tips the concrete orange, so it is off.
export const WHITE_BALANCE = TONEMAP === "agx";

const VERT = /* glsl */`
  varying vec2 vUv;
  void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }
`;

const FRAG = /* glsl */`
  precision highp float;
  varying vec2 vUv;

  uniform sampler2D tColor;
  uniform sampler2D tDepth;
  uniform vec2  uTexel;         // 1 / resolution
  uniform float uBlurPx;        // BLUR_MAX, scaled to this resolution
  uniform float uFocus;         // metres from the camera to the focus plane
  uniform float uSpread;        // metres of depth that stay sharp
  uniform float uNear, uFar;    // to turn the depth buffer back into metres
  uniform float uGrain, uVignette;
  uniform float uExposure;      // stops
  uniform float uTempScale;     // white balance, as a linear RGB gain
  uniform vec3  uTempGain;
  uniform float uContrast;      // the "Very High Contrast" stand-in
  uniform float uTime;

  ${THREE.ShaderChunk.tonemapping_pars_fragment}

  // The camera is ORTHOGRAPHIC, so the depth buffer is linear in z already and
  // this is a lerp, not the perspective un-projection. Getting this wrong is
  // invisible: a perspective un-projection on an ortho buffer still produces a
  // plausible blur, focused on the wrong plane.
  float depthMetres(vec2 uv) {
    float d = texture2D(tDepth, uv).x;
    return uNear + d * (uFar - uNear);
  }

  // Circle of confusion, 0 at the focus plane and 1 well away from it. The
  // same expression as the compositor's node chain.
  float coc(vec2 uv) {
    float z = depthMetres(uv);
    return min(1.0, pow(abs(z - uFocus) / uSpread, 1.7));
  }

  // 24 taps on a Vogel disc. Each tap is weighted by ITS OWN circle of
  // confusion, so a sharp foreground cannot bleed onto a blurred background:
  // without that weight the buildings grow a halo against the far streets, and
  // it reads as a render bug rather than as a shallow lens.
  #ifndef TAPS
  #define TAPS 24
  #endif
  const float GOLDEN = 2.39996323;

  vec3 blurred(vec2 uv, float r) {
    vec3 sum = texture2D(tColor, uv).rgb;
    float wsum = 1.0;
    for (int i = 0; i < TAPS; i++) {
      float fi = float(i) + 0.5;
      float a = fi * GOLDEN;
      vec2 off = vec2(cos(a), sin(a)) * sqrt(fi / float(TAPS)) * r * uTexel;
      vec2 suv = clamp(uv + off, vec2(0.0), vec2(1.0));
      float w = max(coc(suv), 0.05);
      sum += texture2D(tColor, suv).rgb * w;
      wsum += w;
    }
    return sum / wsum;
  }

  float hash(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
  }

  // Blender's Overlay, per channel, which is not the same as screen or soft
  // light and is what GRAIN was tuned against.
  vec3 overlay(vec3 base, vec3 top, float fac) {
    vec3 o = mix(2.0 * base * top,
                 1.0 - 2.0 * (1.0 - base) * (1.0 - top),
                 step(0.5, base));
    return mix(base, o, fac);
  }

  void main() {
    float c = coc(vUv);
    vec3 col = uBlurPx > 0.01 ? blurred(vUv, c * uBlurPx)
                              : texture2D(tColor, vUv).rgb;

    if (uGrain > 0.0) {
      float n = hash(vUv * 1024.0 + uTime);
      col = overlay(col, vec3(n), uGrain);
    }

    if (uVignette > 0.0) {
      // The compositor's blurred ellipse mask, as an analytic falloff: 1 in
      // the middle, 0 outside 0.86 x 0.94 of the frame, soft at the edge.
      vec2 d = (vUv - 0.5) * 2.0 / vec2(0.86, 0.94);
      float m = 1.0 - smoothstep(0.75, 1.35, length(d));
      col *= mix(1.0, m, uVignette);
    }

    col *= uTempGain * uTempScale;      // white balance
    col *= exp2(uExposure);             // exposure, in stops like Blender's

    // The Very High Contrast stand-in: a pivot around middle grey in log
    // space, applied before the transform so it shapes light and not pixels.
    if (abs(uContrast - 1.0) > 0.001) {
      vec3 l = log2(max(col, vec3(1e-5)) / 0.18);
      col = 0.18 * exp2(l * uContrast);
    }

    #ifdef TONEMAP_AGX
      col = AgXToneMapping(col);
    #else
      col = clamp(col, 0.0, 1.0);
    #endif

    // LINEAR TO sRGB, AND IT HAS TO BE HERE. Everything above works on linear
    // light, which is the only way the blur and the grain mean anything, and a
    // linear value written to the framebuffer is displayed as if it were
    // already encoded — which is a picture about 0.18 darker in the mean with
    // its shadows crushed, and MORE saturated, because the gamma pulls the
    // channels apart. three does this for its own materials and cannot do it
    // for a raw ShaderMaterial, so the pass owns it.
    //
    // The AgX branch was right by accident: three's AgX ends in display space.
    // Encoding it twice would wash it out, so it opts out here.
    #ifndef TONEMAP_AGX
      col = mix(col * 12.92,
                1.055 * pow(col, vec3(0.41666)) - 0.055,
                step(0.0031308, col));
    #endif

    gl_FragColor = vec4(col, 1.0);
  }
`;

// Kelvin to a linear RGB gain, normalised so the green channel is untouched.
// Blender's white balance names the temperature it is correcting FOR, so a
// number above 6500 warms the image: the gain is the RECIPROCAL of that
// illuminant. Getting the direction backwards makes 7800 K look cold, which is
// the exact complaint the grade exists to fix.
function whiteBalanceGain(kelvin) {
  const t = kelvin / 100;
  let r, g, b;
  if (t <= 66) {
    r = 255;
    g = 99.4708025861 * Math.log(t) - 161.1195681661;
    b = t <= 19 ? 0 : 138.5177312231 * Math.log(t - 10) - 305.0447927307;
  } else {
    r = 329.698727446 * Math.pow(t - 60, -0.1332047592);
    g = 288.1221695283 * Math.pow(t - 60, -0.0755148492);
    b = 255;
  }
  const clamp01 = (v) => Math.min(1, Math.max(0, v / 255));
  // sRGB -> linear, then invert: correcting FOR this illuminant.
  const lin = [clamp01(r), clamp01(g), clamp01(b)].map((v) =>
    v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4));
  const inv = lin.map((v) => 1 / Math.max(v, 1e-4));
  return inv.map((v) => v / inv[1]);          // green stays put
}

export function makePost(renderer, cfg) {
  const { post, grade, shot } = cfg;
  const heroElevation = shot.elevation;
  const heroAspect = 1 / shot.aspect;
  const cityTop = cfg.bounds?.top ?? 75;

  // HOW MUCH DEPTH THIS FRAME COVERS, in metres, which is what the sharp band
  // is a fraction of. Two terms, and each one owns an end of the range:
  //
  //   the ground   a frame of height h tilted `e` above it spans h/tan(e), so
  //                this dominates when the camera is low and goes to zero
  //                looking straight down;
  //   the city     from overhead, what varies in depth is not the ground at
  //                all, it is the buildings standing on it — top * sin(e).
  //
  // Without the second term a top-down view computes a 28 m band over a city
  // 74 m tall and everything but one storey goes soft.
  const frameDepth = (w, elevationDeg, aspect) => {
    const e = THREE.MathUtils.degToRad(
      THREE.MathUtils.clamp(elevationDeg, 4, 90));
    return (w / aspect) / Math.tan(e) + cityTop * Math.sin(e);
  };
  // Anchored so the hero frame comes out at exactly FOCUS_SPREAD.
  const SPREAD_K =
    post.FOCUS_SPREAD / frameDepth(shot.hero_width, heroElevation, heroAspect);
  const size = new THREE.Vector2();
  renderer.getDrawingBufferSize(size);

  const target = new THREE.WebGLRenderTarget(size.x, size.y, {
    type: THREE.HalfFloatType,          // linear light, not display pixels
    colorSpace: THREE.LinearSRGBColorSpace,
    samples: 4,                         // MSAA: the city is all hard edges
  });
  target.depthTexture = new THREE.DepthTexture(size.x, size.y);
  target.depthTexture.type = THREE.UnsignedIntType;

  const gain = WHITE_BALANCE ? whiteBalanceGain(grade.white_balance) : [1, 1, 1];
  // ShaderMaterial rather than RawShaderMaterial: the tone mapping chunk above
  // needs the defines and precision three prepends.
  const material = new THREE.ShaderMaterial({
    vertexShader: VERT,
    fragmentShader: FRAG,
    depthTest: false,
    depthWrite: false,
    uniforms: {
      tColor: { value: target.texture },
      tDepth: { value: target.depthTexture },
      uTexel: { value: new THREE.Vector2(1 / size.x, 1 / size.y) },
      uBlurPx: { value: 0 },
      uFocus: { value: post.FOCUS_D },
      uSpread: { value: post.FOCUS_SPREAD },
      uNear: { value: 0.1 },
      uFar: { value: 1000 },
      uGrain: { value: post.GRAIN },
      uVignette: { value: post.VIGNETTE },
      uExposure: { value: grade.exposure + EXPOSURE_OFFSET },
      uTempGain: { value: new THREE.Vector3(...gain) },
      uTempScale: { value: 1.0 },
      uContrast: { value: LOOK_CONTRAST },
      uTime: { value: 0 },
    },
    defines: {
      TAPS: cfg.taps ?? 24,
      ...(TONEMAP === "agx" ? { TONEMAP_AGX: "" } : {}),
    },
  });
  const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material);
  const quadScene = new THREE.Scene().add(quad);
  const quadCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

  return {
    target,
    uniforms: material.uniforms,

    setSize(w, h) {
      target.setSize(w, h);
      material.uniforms.uTexel.value.set(1 / w, 1 / h);
      // BLUR_MAX is in pixels at 1600 wide, exactly as the compositor has it.
      material.uniforms.uBlurPx.value = post.BLUR_MAX * (w / 1600);
    },

    // The frame width drives the sharp band, through the same ratio the
    // compositor's driver uses: at HERO_WIDTH it evaluates to FOCUS_SPREAD.
    //
    // AND SO DOES THE ELEVATION, which the compositor never had to think about
    // because the .blend only ever shoots from 30.6 degrees. Free orbit runs
    // from 24 to 82, and the depth a frame spans changes by a factor of four
    // over that range — a band tuned for the hero angle fogs everything but
    // one row of buildings at the bottom of it. See frameDepth: the band is a
    // fixed fraction of the depth the frame actually covers, and at the hero
    // angle and width that fraction evaluates to FOCUS_SPREAD exactly, which
    // is why the number never moved.
    setFraming(width, heroWidth, near, far,
               elevationDeg = heroElevation, aspect = heroAspect) {
      material.uniforms.uSpread.value = SPREAD_K * frameDepth(width, elevationDeg, aspect);
      material.uniforms.uNear.value = near;
      material.uniforms.uFar.value = far;
    },

    render(scene, camera, time) {
      material.uniforms.uTime.value = time;
      renderer.setRenderTarget(target);
      renderer.clear();
      renderer.render(scene, camera);
      renderer.setRenderTarget(null);
      renderer.render(quadScene, quadCamera);
    },
  };
}
