# Parallax UI

The globe and San Francisco city are connected to the Python backend. Financial values, institutions, shocks, agent jobs, supplier contracts, and Fork Reality outcomes come from API responses. The original fixtures remain development references rather than the active economy.

From the repository root, start the API in one terminal:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_backend --reload
```

The launcher loads supported settings from the ignored root `.env`. Shell variables take precedence. Keep the Nebius key on the backend.

In a second terminal, using Node 22 LTS:

```sh
npm ci
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies API and SSE traffic to http://127.0.0.1:8000. No frontend key is required. When configured, live mode uses the displayed Nemotron model; deterministic demo mode remains explicitly selectable.

Choose United States, San Francisco, and a starting scenario. Credit crunch supports the bank-crisis demo. Supply crunch supports material-shortage recovery through supplier negotiation. The miniature is a visual representation of backend institutions, not a calibrated local forecast.

Validation:

```sh
npm test
npm run build
node scripts/qa-integration.mjs
```

Browser QA requires both servers and installed Google Chrome. Screenshots and its report go to ignored `artifacts/`. The original fixture QA scripts are historical references.

See [UI integration](../../docs/UI_INTEGRATION.md) for supported actions, environment configuration, architecture, and demo steps. External settlement and unsupported rent/tax/interest-rate economics remain future work.

Map data: Natural Earth via datasets/geo-countries; public domain. Three-globe renders the globe, and Canvas renders the fixed city geometry.

City detail and zoom: the Palace of Fine Arts and Golden Gate Park shortcuts focus their districts. Scroll or pinch to zoom around the pointer, use +/−, double-click a district, and drag to pan while zoomed. Clicking a building centers it and opens its inspector. Home or “Back to whole city” restores the overview while retaining tick, branch, playback, and selection. District feed filtering has its own clear action. Figures select the existing representative household group.

The static miniature is cached at three resolutions in tiles when the committed layout loads. District and street zoom reveal extra vector detail; off-screen tiles and movers are culled. The same 400 movers serve every detail level. Activity, queues, closures, and bank stress use the existing snapshot fields; no financial fixture or simulation code changes are needed.

Regenerate only the enriched layout with `node scripts/update-city-layout.mjs`. The fixed layout seed remains 4242 and the layout has a content hash. `node scripts/qa-city-detail.mjs` checks the detail levels, mouse/touch navigation, selection and playback preservation, district feed filtering, and frame rates; its screenshots and report are written to `artifacts/city-detail/`.
`node scripts/qa-landmark-fidelity.mjs` captures the bridge, arched Palace and anchored Ferry Building marina close-ups after the city QA. Hand-built landmark artwork is in `src/city/landmarkArt.ts`; its cable profiles, pier anchoring, irregular shorelines and dry planting are covered by `tests/landmarkArt.test.ts`.
The refined model uses `modelArt.ts` for shared sunlight/materials/cast shadows and matte foliage, `buildingArt.ts` for pitched houses and distinct skyline/Ferry architecture, and `palaceArt.ts` for the detailed rotunda and Alcatraz. Landmark QA now verifies hover names and district clicks for all eight sites and saves island/skyline close-ups. Canvas sizing uses untransformed content dimensions so hit areas remain aligned through the existing city-entry scale animation.

The version-4 city layout follows the demo reference (`docs/demo-reference.png`): coastlines and landmark sites are traced in the reference frame and mapped onto the scene by `ref()` in `cityGeometry.ts`. A circular tabletop holds a natural island with the Marina, a kidney lagoon wrapping the Palace on three sides, the bridge to a raised Marin headland, Coit hill, the east quay and Ferry apron, a south-east harbour and Golden Gate Park with three ponds and a windmill; Alcatraz is a separate island. The city core is a straight two-direction street grid (2.4 grid-unit pitch) inside a ring of shore roads, cut by a diagonal boulevard from the bridge landing to the Ferry plaza; park paths are winding splines. Blocks are subdivided into 2 x 2 lots of pastel houses and apartment cubes with a 5.5-unit minimum clear gap, and 15-20 downtown towers keep at least 38% of each silhouette clear. The layout seed is 4242; its current hash is sf-3e1219b2. Only the city layout fixture is regenerated.

The renderer bakes the whole miniature (ground, roads, shadows, trees, buildings and landmarks, depth-sorted, with the Ferry clock tower last) into tiles at three resolutions. Shadows are drawn on their own layer and laid down once, so they never stack. Each frame draws the same 400 mover identities over the tiles, hiding any whose foot point lies behind a canopy or building outline. Overview labels are the four demo labels, collision-checked against each other, landmarks and controls. Queues use physical path distances and connected sidewalk approaches.

Run `node scripts/qa-island-rework.mjs` for landmark identity, navigation, cache/state preservation, crisis activity, mobile sizing, frame-rate checks and the overview/Palace/park/Ferry/street screenshots in `artifacts/island-rework/`. `CITY_QA_URL` can select another local dev port. `node scripts/audit-island-layout.mjs` audits dry routes, clear building footprints and minimum gaps. The detailed interaction suite remains available as `node scripts/qa-city-detail.mjs`.
