# Independent bearing clamps — concept 01

**Status: editable mechanical concept, not a verified S5 replacement.**

This draft addresses the shared-fastener problem described in ROBO RECYCLERS and shown in the local photos/videos. The centre body carries two perpendicular bearing seats. The upper and lower caps each use four separate screws into blind insert pockets in that body. Neither clamp's screws pass through the other cap. End shoulders capture each bearing axially; enlarged rod passages allow the shafts to slide through their existing bearings.

The motor-support attachment is deliberately not modelled because its mounting face and hole coordinates are unresolved. The three housing components alone cannot mount the drill motor. Independent fastener paths eliminate the shared three-piece bolt stack, but do not prove zero elastic coupling or sufficient rigidity under drill loads.

## Files

- `parameters.json`: editable dimensions and their evidence status.
- `build_model.py`: CadQuery model, exports, fit coupons, and geometric checks.
- `render_vtk.py`: assembled and exploded review image derived from the CAD, using depth-tested rendering.
- `render_preview.py`: optional Matplotlib fallback preview.
- `verify_exports.py`: independent checks of the actual binary STL files.
- `generated/housing_assembly_DRAFT.step`: the three housing components in assembly position.
- `generated/with_reference_rods_DRAFT.step`: housing plus simplified rods/bearings for orientation; do not print reference hardware.
- `generated/*_cap_DRAFT.stl`, `generated/centre_body_DRAFT.stl`: separate grounded housing meshes. Slicer orientation/supports still need review.
- `generated/coupon_*.stl`: short, open bearing-seat saddles at +0.00, +0.10 and +0.20 mm diameter allowance. These compare printed seat fit; they do not validate the complete clamp or bearing preload.
- `generated/validation.json`: results and scope of geometric checks.
- `generated/preview_DRAFT.png`: review image.

## Dimensions and evidence

| Item | Value, mm | Evidence/status |
|---|---:|---|
| Upper rod diameter | 10 | Photo 10; official S5 catalog confirms 10 mm X print-head shaft |
| Lower rod diameter | 8 | Photo 10; official catalog confirms 8 mm Y print-head shaft |
| Upper bearing OD × length | 17.44 × 29.08 | Photo 8 mapped to corrected Teams comment |
| Lower bearing OD × length | 13.14 × 24.02 | Photo 7 mapped to corrected Teams comment |
| Vertical rod centre spacing | **20 placeholder** | **Not measured; not an OEM S5 dimension** |
| Housing plan envelope | **48 × 48 proposed** | New draft envelope; does not reproduce measured OEM outline |
| Total draft height | 43.39 | Result of current placeholder spacing and wall choices |
| Radial-seat diameter allowance | +0.10 | Initial print-fit choice, not verified |
| Axial seat length allowance | +0.30 | Initial print-fit choice, not verified |
| Split gaps | 0.60 each | Available adjustment travel before cap/body faces meet |
| Original rear housing bolts | M2.5 × 75 | Official S5 print-head-cable repair manual |
| New clamp screws | M3 proposed | User authorized separate replacement hardware |
| New screw clearance holes | 3.40 | Draft design choice |
| Insert pilot pockets | Ø4.00 × 6 deep | Placeholder for supplier-specific M3 heat-set inserts |

The smaller bearing's length was initially annotated around 2.3 cm in its photo; the later Teams reply gives 24.02 mm. The photo annotations use incorrect units in places; the later explicit millimetre values are used here. They remain measurements of these particular bearings, not guaranteed catalogue dimensions.

The supplied housing photos also show 39.00, 43.14, 45.36 and 46.50 mm. These have not been silently converted into mounting-hole pitches: the contact points and relevant datum faces need confirmation. Original rod positions must be retained; do not alter the gantry to accommodate the 20 mm placeholder.

## Hardware and assembly intent

Proposed hardware is eight M3 screws and eight matching M3 heat-set inserts. The model uses four upper positions (±9, ±17) and four lower positions (±17, ±7), in mm about the crossed-axis origin. Upper screws enter from above and lower screws from below. Their insert pockets are blind and spatially separate.

Select inserts before finalizing their pilot holes. The cylindrical pockets in the model are not printed M3 threads. They should not be used for direct self-tapping screws without redesign. At the present cap dimensions, screw grip lengths from the bottom of each head recess to the insert entrance are approximately 10.07 mm upper and 7.92 mm lower. Choose final screw lengths from actual insert engagement and bottoming clearance, including the small change when the split gap closes. The original M2.5×75 bolts are not appropriate for these new blind pockets.

The lower screw heads need access from beneath. The future motor adapter must preserve that access or be removable separately. It should attach to a fixed datum on the centre body, with its own fasteners, rather than reintroducing a shared clamping stack. Current geometry provides the bearing-holder concept only; it is not a motor bracket.

Clamping retains the bearing's outer sleeve, not the rod. UltiMaker explicitly warns that overtightening the stock head can overload the linear bearings. Its stock torque specification must not be treated as a validated torque for a different printed clamp and inserts.

## Before a usable prototype

1. Verify S5 vertical rod-centre spacing from a trustworthy drawing/model or physical measurement. Searches located official service documents and UM3 CAD, but not an exact dimensioned S5 housing model. UM3 geometry was not substituted for S5 geometry.
2. Establish the motor-adapter mounting plane, hole coordinates, screw size, and wire/end-stop clearances. Keep the drill alignment and original rod locations.
3. Check the proposed 48 mm footprint and 43.39 mm height against the carriage's full travel; these are not OEM dimensions.
4. Print the small seat coupons in the intended material/process and check the actual bearing outer sleeves. Then choose insert and screw clearances for that process.
5. Review print orientation, support removal from bearing seats, and strength around insert pockets. No material, infill, torque, stiffness or fatigue performance has been validated.
6. Test the assembled head for smooth movement and lost motion under realistic loads before powered screw removal.

With no caliper immediately available, a flatbed scan or square-on photos of each detached housing face next to a ruler can help recover the hole layout. That is a useful next reference, not a substitute for final bearing-fit verification. No immediate action is needed while you rest.

## Run locally

From the Codex workspace, using the installed environment:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 work/cad-venv/bin/python '/home/shayyan/Documents/unsw/vip/2026_robo_recycle/3d models/independent_clamp_draft_v1/build_model.py'
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 work/cad-venv/bin/python '/home/shayyan/Documents/unsw/vip/2026_robo_recycle/3d models/independent_clamp_draft_v1/verify_exports.py'
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 work/cad-venv/bin/python '/home/shayyan/Documents/unsw/vip/2026_robo_recycle/3d models/independent_clamp_draft_v1/render_vtk.py'
```

Dependencies: CadQuery 2.8.0, its bundled VTK dependency and Pillow; Matplotlib and NumPy for the optional fallback preview. No sudo or running desktop CAD application is required. Outputs use millimetres. Editing `parameters.json` and rebuilding preserves the parametric design; STEP carries exchange geometry rather than the Python parameter history.

On this laptop, CAD generation and geometry validation peaked at approximately 488 MiB process RAM. All three housing solids passed STEP export/import volume checks. All nine actual STL files passed closed-edge, positive-volume and Z=0 grounding checks; housing mesh volumes agree with the precise solids within 0.5%. These are geometry checks, not physical fit or load tests.

The current model rejects spacing that leaves less than 2 mm of solid web between bearing pockets. If the true S5 spacing fails that constraint, redesign the carrier instead of changing the gantry spacing.

## Sources

- Local `Media (1)` through `Media (10)`, `Media.jpeg`, sampled frames from `issue.mp4` and `MicrosoftTeams-video.mp4`, and ROBO RECYCLERS comments dated 21 October 2026. Video audio was not transcribed.
- [UltiMaker S5 service parts catalog](https://um-support-files.ultimaker.com/spare-parts/Catalogs/UltiMaker%20S5%20-%20Service%20part%20catalog.pdf): rod sizes and print-head bearing pair. Confirms component types, not the missing centre spacing.
- [S5 print-head cable repair manual](https://um-support-files.ultimaker.com/manuals/repair-calibration/S-series/S-line%20-%20Print%20head%20cable.pdf): original rear M2.5×75 bolts and 2 mm hex driver.
- [S5 lift-switch repair manual](https://um-support-files.ultimaker.com/manuals/repair-calibration/S-series/Repair%20guide%20S5%20-%20Lift%20switch%20spring%20%28renders%29.pdf): bearing housing arrangement and overtightening warning.
- [Official UM3 hardware source](https://github.com/Ultimaker/Ultimaker3): found during research, **not used as S5 dimensional evidence**; no third-party CAD geometry was copied into this model.
- [CadQuery export documentation](https://cadquery.readthedocs.io/en/latest/importexport.html).
