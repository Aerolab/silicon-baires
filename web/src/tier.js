// WHAT THE MACHINE ON THE OTHER END CAN AFFORD, in the three numbers that
// decide the bill: how big the buffer is, how many samples it holds, and how
// big the shadow map is.
//
// The page shipped one profile and it was a desktop one. On a phone at
// devicePixelRatio 2, roughly 390x870 CSS, that is:
//
//   colour   RGBA16F, samples: 4     ~44 MB      its resolve target   ~11 MB
//   depth    24-bit,  samples: 4     ~22 MB      its depth texture     ~5 MB
//   shadow   4096^2 PCFSoft          ~67 MB
//
// about 150 MB of framebuffers before one triangle of the city is drawn, on
// top of the glb, the 28.215 instances and the PMREM of the sky. Chromium on
// Android does not degrade under that, it kills the renderer process: what the
// visitor gets is a white page, a sad-tab favicon, and no way to tell whether
// it was the site, the phone or the network. See the guard in index.html for
// the failures that at least get to run some code; this file is about not
// reaching them.
//
// MSAA is where nearly all of it is, and it is also what a phone needs least:
// the parapet edges that crawl on a 110 ppi monitor are below the resolution
// of a 400 ppi screen. Dropping it and the shadow map takes the same page from
// about 150 MB to about 30.
//
// ?tier=low forces the phone profile on a desktop, which is the only way to
// look at what a phone gets without holding one. ?tier=high does the reverse.
// The individual flags (?ss=, ?shadow=) still win over both: see main.js.
const flags = new URLSearchParams(location.search);
const forced = flags.get("tier");

// Four signals, because no single one of them is both available and honest
// everywhere. userAgentData.mobile is the reliable one and it is Chromium
// only; the pointer/size pair covers Safari; deviceMemory is a Chromium hint
// rounded to a power of two, and its ABSENCE has to read as "plenty" rather
// than as "none" or every iPhone AND every desktop Safari lands in low.
const mobileUA = navigator.userAgentData?.mobile ??
  /Android|iPhone|iPad|iPod/.test(navigator.userAgent);
const coarse = matchMedia("(pointer: coarse)").matches;
const small = Math.min(screen.width, screen.height) <= 900;
const ram = navigator.deviceMemory ?? 8;

// The capture is always high: it runs in a headless desktop Chromium and the
// video is the deliverable. A recorder that quietly shot the phone profile
// would be a 2.6 GB file nobody would think to re-check.
const capturing = flags.has("capture");

const low = capturing ? false
  : forced ? forced === "low"
  : mobileUA || (coarse && small) || ram <= 4;

export const TIER = low
  ? {
      name: "low",
      // 1.75 and not 2: the buffer grows with the square of this, so it is
      // 23 % less memory and 23 % less to shade every frame, for a difference
      // that needs a loupe on a phone. Still capped by the device's own ratio,
      // which is what a 1x tablet reports.
      pixelRatio: Math.min(devicePixelRatio, 1.75),
      // No MSAA. The whole point of the file.
      samples: 0,
      // 1024 over a shadow camera fitted to the frame is about 20 cm per
      // texel at the hero width. Soft, but the shadows still sit the buildings
      // on the ground, which is the job they do in this shot.
      shadowMapSize: 1024,
    }
  : {
      name: "high",
      pixelRatio: Math.min(devicePixelRatio, 2),
      samples: 4,
      shadowMapSize: 4096,
    };

// What it thinks it decided and why, for ?stats=1 and for the next person who
// gets a screenshot of a white page from a device they do not own.
export const TIER_WHY = { mobileUA, coarse, small, ram, forced: forced ?? null };
