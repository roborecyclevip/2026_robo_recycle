# Independent bearing clamp — 18 mm prototype v2

Printable bearing-clamp prototype, not a complete bolt-on motor mount. Physical fit/load testing has not been performed. Original v1 is unchanged.

## Geometry

The user's 18 mm middle-component height is interpreted as separation of the bearing-centre split planes. The centre body itself is exactly 18 mm tall. This is tape-measured geometry, not a precision-verified OEM dimension.

- Upper rod: 10 mm. Bearing: 17.44 mm OD × 29.08 mm long.
- Lower rod: 8 mm. Bearing: 13.14 mm OD × 24.02 mm long.
- Bearing-seat diameters: 17.54 and 13.24 mm, including +0.10 mm diametral allowance.
- Seat lengths: 29.38 and 24.32 mm, including +0.30 mm axial allowance.
- Rod exit clearances: 11 and 9 mm. These are clearance passages; clamps retain bearing sleeves, not moving rods.
- Solid web between bearing pockets: 2.61 mm.
- Envelope: 48 × 48 mm, assembly height 41.39 mm before clamping. Check full-travel clearance; this is not the OEM envelope.
- Each cap has 0.60 mm closure clearance outside the 18 mm centre body.

## Print files

Print one each from `generated/`: `centre_body_DRAFT.stl`, `upper_X_cap_DRAFT.stl`, `lower_Y_cap_DRAFT.stl`.

DRAFT denotes an untested physical prototype. All STLs are grounded. Both caps have their outer flat faces down. The centre body's lower bearing recess faces downward: review supports in the slicer and remove them without damaging the seat. Screw recesses also require slicer inspection. No material/machine-specific G-code is supplied.

The small bearing-seat coupons compare +0.00, +0.10 and +0.20 mm diameter allowances. Print these first if possible. A coupon fit is not a full clamp/load test.

`housing_assembly_DRAFT.step` contains exchange geometry. `with_reference_rods_DRAFT.step` includes reference hardware; do not print it as one part. The Python builder and JSON parameters preserve the editable design.

## Fasteners

Four upper and four lower M3 screws enter separate blind pockets in the centre body. No bolt spans both caps. Clearance holes are 3.4 mm; head recesses 6.2 mm diameter × 3 mm deep.

Insert pilots are 4.0 mm diameter × 6 mm deep. These are not finished threads. Select compatible M3 heat-set inserts and check the supplier's pilot specification and printed fit before installing. Do not force incompatible inserts into the body.

Initial upper under-head-to-pocket distance is 9.77 mm, lower 7.62 mm. Candidate M3×14 upper and M3×12 lower project 4.23 and 4.38 mm into the pockets. Verify actual insert engagement, head seating and bottoming clearance throughout cap closure before use. Do not use the original 75 mm bolts in these pockets.

Fit bearings and tighten each cap evenly in small increments. Stop if movement becomes rough or tight. No tightening torque or drill-load capacity is validated. Check full travel by hand before powered operation.

## Motor interface — not included

The existing motor bracket matches the stock four-hole pattern, but exact pitch and mounting-face clearance remain unresolved. This prototype cannot yet secure the motor: it has no motor-mount holes or adapter. Do not drill arbitrary holes or run motor bolts through both caps. The completed attachment must connect to the fixed centre carrier and preserve lower-clamp screw access.

## Verification

Run build_model.py, verify_exports.py and render_vtk.py with the installed CadQuery environment. Checks cover exact 18 mm centre-body height, valid solids, STEP round-trip volume, closed STL meshes and interference with reference bearings/rods. They do not establish physical fit, strength, insert retention or travel clearance.

Sources: user-supplied corrected bearing dimensions and latest 18 mm measurement. Original screw reference: https://um-support-files.ultimaker.com/manuals/repair-calibration/S-series/S-line%20-%20Print%20head%20cable.pdf .
