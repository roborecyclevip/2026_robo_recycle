# Independent S5 bearing clamp — captive-nut prototype v3

This completes the proposed prototype geometry: independent bearing caps, accessible side-loaded hex nuts and four fixed motor-mount feet. It is NOT a verified OEM replacement or a load-rated drill mount. Use the checks below before manufacturing the main parts or powering the motor. Do not mix v2 and v3 parts: screw recesses and the lower cap have changed.

## What changed

- Twelve ordinary M3 hex nuts replace heat-set inserts. Eight hold the bearing caps; four hold the existing motor bracket to fixed feet.
- The upper and lower cap each have four independent M3×15 screws. The load from each cap ends in the centre body, not the other cap.
- Four feet are integral with the centre body. Four separate M3×20 motor bolts enter from underneath the existing motor bracket into nuts in these feet. Motor bolts do not cross either bearing cap.
- Lower-cap corners are relieved to clear the feet throughout the cap's 0.6 mm closure travel.
- Counterbores accommodate 7 mm OD washers. No bolt threads into printed plastic.

## Assumptions that must be checked

| Feature | Model value / consequence |
|---|---|
| Bearing-centre spacing / middle core | **18 mm**, from the user's tape-measured middle height. The middle core remains 18 mm; its integral feet extend below it. |
| Upper bearing and rod | Bearing OD 17.44 mm × length 29.08 mm; 10 mm rod. |
| Lower bearing and rod | Bearing OD 13.14 mm × length 24.02 mm; 8 mm rod. |
| Seat allowance | +0.10 mm diameter and +0.30 mm bearing length. Rod passages are 11 and 9 mm diameter; these do not grip rods. |
| Solid web between seats | 2.61 mm. |
| Motor four-hole pattern | **36 × 40 mm centre-to-centre**, provisional estimate from photos, NOT verified OEM dimensions. Coordinates (±18, ±20) about the rod crossing. |
| Motor contact plane | **16 mm below the lower rod axis**. This changes tool height relative to the old assembly; recalibrate tool reach/zero and travel limits. |
| Existing bracket | Assumed flat contact at four pads, nominal 4 mm flange thickness, accessible screw heads underneath, and no projection above the contact plane. No accurate model of the existing motor, bracket, wiring or end stops is available. |
| M3×20 motor bolt range | For a flat flange 2–10 mm thick with a 0.5 mm washer. If thicker or underside access is blocked, this attachment needs revision; do not blindly substitute a longer bolt. |
| New footprint | 48 × 52 mm, assembly from z=-16 to z=30.77, excluding motor and screw heads. This is larger/different from stock. Check belts, frame, wiring, end stops and full carriage travel. |

The original M2.5 motor-bracket clearance holes may need enlarging for M3, but only after the mounting pattern, edge distances and access are checked. This package does not authorize modifying threaded metal hardware or forcing a mismatch. If the pattern gauge fails, change the pitch parameters and regenerate; do not bend the bracket or force the screws to line up.

## Print these checks first

1. `generated/M3_nut_fit_CHECK_FIRST.stl`: a small side-loading nut pocket. Try the purchased nut without force; it should slide fully into place and resist rotation when a bolt is turned. Pocket is 5.8 mm across flats × 2.8 mm high, intended for nominal 5.5 × 2.4 mm plain M3 nuts. Verify both nut batches if they differ.
2. `generated/motor_pattern_CHECK_FIRST.stl`: 2 mm thick rectangular frame with the proposed four holes. Compare against the original top that you have at home and then the motor bracket. Check both orientations. This is an alignment gauge, NOT a drilling jig to force an unconfirmed pattern onto stock parts.
3. Bearing coupons `coupon_upper_*` and `coupon_lower_*`: compare +0.00, +0.10 and +0.20 mm diameter allowances with the actual bearing sleeves and intended print process.

Any failed check requires a parameter change/reprint before the large parts. FDM tolerances, the 18 mm tape measurement and material stiffness are not validated by the CAD checks.

## Main print files

Print one of each:

- `generated/centre_body_DRAFT.stl` — fixed 18 mm core plus motor feet; twelve side-loading nut pockets.
- `generated/upper_X_cap_DRAFT.stl` — upper bearing cap, four M3×15 bolts.
- `generated/lower_Y_cap_DRAFT.stl` — lower bearing cap, four M3×15 bolts, relieved corners.

Each STL is grounded at Z=0. Caps have their outer flat faces down. The centre body is inverted (top face down) so the feet grow upward rather than bridging a 48 mm gap. Supports are needed under the centre body's bed-facing bearing recess and may be needed in counterbores; review your slicer. Keep removable support out of the side nut channels where practical; the 2.8 mm slots require careful bridge/support cleanup. Inspect every pocket before inserting hardware.

This package specifies no validated material, wall count, infill, torque or drill load rating. Use the small tests to establish print fit first. A PLA fit sample is not evidence of suitability for motor heat or sustained load. No machine-specific G-code is supplied.

## Assembly order

1. Remove supports and burrs. Check nut coupon, mounting gauge and bearing coupons. Measure washer thickness and bolt/nut dimensions.
2. Slide four upper nuts in through the ±Y faces (higher slots, near z=12.2..15); four lower nuts through the ±X faces (z=3..5.8); four motor nuts through the outer ±Y faces of the feet (z=-10..-7.2). Tweezers or temporary tape can hold unloaded nuts in place. Do not glue them or heat them in.
3. Fit the existing lower bearing/rod into its seat and the relieved lower cap. Use four M3×15 bolts, each with one washer under its head. Heads enter from below.
4. Fit the upper bearing/rod and upper cap using four more M3×15 bolts and washers, entering from above.
5. Tighten the two caps separately, evenly and only enough to remove bearing-sleeve movement. Stop if rod movement becomes rough or tight, plastic cracks, a nut rotates or a bolt bottoms out. Do not force either split gap fully shut as a tightening target.
6. With bearing adjustment complete, attach the existing motor bracket to the four feet using four M3×20 bolts and washers from beneath. All four pad faces must contact squarely without rocking; check the assumed flange thickness/access first. The lower cap remains separated from the bracket by at least 5.38 mm before screw-head protrusion. To adjust lower bolts later, remove the motor bracket independently.
7. Check free manual movement over the full travel with power off, including wiring and end stops. Re-establish tool height because of the new mounting plane. Apply witness marks, test progressively under supervision and inspect for loosening, creep or cracks. Captive nuts stop rotation, not vibration loosening. Do not treat the assembly as approved for unattended powered drilling.

## Fastener dimensions and checks

See `SHOPPING_LIST.md` for linked Bunnings packs. Required: eight M3×15 round-head bolts, four M3×20 round-head bolts, twelve plain M3 hex nuts and twelve 7 mm OD washers. Model uses 0.5 mm washer thickness; clamp geometry accommodates 0.3–0.8 mm while retaining at least one 0.5 mm thread pitch past nominal nuts. No countersunk/nyloc/flange substitutions without redesign.

Calculated with nominal hardware and 0.5 mm washers, thread projection beyond the loaded nuts is 0.83 mm upper, 0.98 mm lower and 7.10 mm motor (inside a clearance bore, assuming a 4 mm flange). Clamp bolts remain clear of blind ends through 0.6 mm cap closure. Actual threads/head profiles and manufacturing tolerances require physical checking. Do not over-tighten printed plastic.

## CAD, regeneration and validation

`generated/housing_assembly_DRAFT.step` is the assembled exchange CAD. `with_reference_rods_DRAFT.step` adds simplified bearings/rods; do not print these reference parts. `parameters.json` and `build_model.py` are the editable parametric source. `render_vtk.py` makes the preview directly from geometry. All dimensions are millimetres.

From the Codex workspace, run with `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 work/cad-venv/bin/python` followed by each script path: build_model.py, verify_exports.py, render_vtk.py. CadQuery/VTK/Pillow are already installed locally. No sudo required.

`generated/validation.json` records checks for three single solids, STEP round-trip volumes, manifold meshes, bearing/rod interference, nut-slot clearance, idealized hardware clearance and full lower-cap closure clearance. The independent STL check covers all eleven files. These are geometric checks, NOT structural analysis or evidence that the assumed motor interface matches the actual assembly.

## Sources and scope

- Dimensions: user photos/Teams corrections for bearings and the latest 18 mm middle measurement. Motor pitch, flange and standoff geometry are explicit design assumptions.
- [Bunnings M3×15 bolt/nut listing](https://www.bunnings.com.au/pinnacle-m3-x-15mm-zinc-plated-round-head-bolts-and-nuts-20-pack_p0168388), [M3×20 listing](https://www.bunnings.com.au/pinnacle-m3-x-20mm-zinc-plated-round-head-bolts-and-nuts-18-pack_p0247264), [washer listing](https://www.bunnings.com.au/pinnacle-m3-black-flat-washer-12-pack_p0257725).
- [Nut manufacturer dimensional reference](https://delightindustrials.com/products/nuts/specs): nominal M3 plain hex nut 5.5 mm across flats, 2.4 mm height. This is NOT a dimension certification for the specific Pinnacle packs.

Previous versions are retained unchanged. V3 is the complete proposed prototype, pending the inexpensive fit checks above and physical load testing.
