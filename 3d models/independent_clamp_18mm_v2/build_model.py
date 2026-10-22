"""Independent bearing clamps: parametric concept, not an OEM drop-in replacement.

Run with the workspace's work/cad-venv/bin/python. All dimensions in mm.
The default exports are deliberately marked DRAFT. Never infer OEM dimensions
from modelling placeholders. Motor bracket and end-stop interface are absent.
"""
from pathlib import Path
from itertools import combinations
import json
import math
import resource
import cadquery as cq

ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT / 'parameters.json').read_text())
OUT = ROOT / 'generated'
OUT.mkdir(exist_ok=True)

def cylinder(radius, length, origin, direction=(0, 0, 1)):
    return cq.Solid.makeCylinder(radius, length, cq.Vector(*origin), cq.Vector(*direction))

def block(x, y, z0, z1):
    return cq.Workplane('XY').box(x, y, z1-z0, centered=(True, True, False)).translate((0,0,z0)).val()

def geometry(p):
    w, d = p['body_width'], p['body_depth']
    sep, gap = p['rod_centre_spacing'], p['split_gap']
    ru = (p['upper_bearing_od'] + p['bearing_diametral_allowance'])/2
    rl = (p['lower_bearing_od'] + p['bearing_diametral_allowance'])/2
    lu = p['upper_bearing_length'] + p['bearing_axial_allowance']
    ll = p['lower_bearing_length'] + p['bearing_axial_allowance']
    zhi, zlo = sep + ru + p['outer_wall'], -rl-p['outer_wall']
    assert sep - ru - rl >= 2, 'Insufficient web between bearing pockets; redesign rather than force a smaller spacing'
    assert w > lu+6 and d > ll+6, 'Bearing end shoulders require more axial length'
    assert gap > p['bearing_diametral_allowance'], 'Insufficient cap travel allowance'
    pockets = [
        cylinder(ru,lu,(-lu/2,0,sep),(1,0,0)),
        cylinder(rl,ll,(0,-ll/2,0),(0,1,0)),
        cylinder((p['upper_rod_diameter']+p['rod_diametral_relief'])/2,w+2,(-w/2-1,0,sep),(1,0,0)),
        cylinder((p['lower_rod_diameter']+p['rod_diametral_relief'])/2,d+2,(0,-d/2-1,0),(0,1,0)),
    ]
    parts = {
        'centre_body': block(w,d,0,sep),
        'upper_X_cap': block(w,d,sep+gap,zhi),
        'lower_Y_cap': block(w,d,zlo,-gap),
    }
    for name in parts:
        for tool in pockets:
            parts[name] = parts[name].cut(tool)
    fasteners = []
    for side in ('upper','lower'):
        upper = side=='upper'
        cap = 'upper_X_cap' if upper else 'lower_Y_cap'
        for sx in (-1,1):
            for sy in (-1,1):
                x,y=sx*p[side+'_screw_x'],sy*p[side+'_screw_y']
                if upper:
                    start, length = sep, zhi-sep+1
                    insert_z, insert_dir = sep, (0,0,-1)
                    recess_z = zhi-p['screw_head_recess_depth']
                else:
                    start, length = zlo-1, 1-zlo
                    insert_z, insert_dir = 0, (0,0,1)
                    recess_z = zlo-0.01
                parts[cap] = parts[cap].cut(cylinder(p['screw_clearance_diameter']/2,length,(x,y,start)))
                parts[cap] = parts[cap].cut(cylinder(p['screw_head_clearance_diameter']/2,p['screw_head_recess_depth']+0.01,(x,y,recess_z)))
                pocket=cylinder(p['insert_pilot_diameter']/2,p['insert_pocket_depth'],(x,y,insert_z),insert_dir)
                # Check blind insert pockets stay out of bearing/rod cavities.
                for tool in pockets:
                    assert pocket.intersect(tool).Volume() < 1e-6, 'Fastener pocket intersects bearing or rod clearance'
                parts['centre_body']=parts['centre_body'].cut(pocket)
                fasteners.append({'clamp':side,'xy':[x,y],'entry_z':insert_z,'direction':insert_dir})
    bearings={
        'upper_bearing_reference': cylinder(p['upper_bearing_od']/2,p['upper_bearing_length'],(-p['upper_bearing_length']/2,0,sep),(1,0,0)).cut(cylinder(p['upper_rod_diameter']/2,p['upper_bearing_length']+2,(-p['upper_bearing_length']/2-1,0,sep),(1,0,0))),
        'lower_bearing_reference': cylinder(p['lower_bearing_od']/2,p['lower_bearing_length'],(0,-p['lower_bearing_length']/2,0),(0,1,0)).cut(cylinder(p['lower_rod_diameter']/2,p['lower_bearing_length']+2,(0,-p['lower_bearing_length']/2-1,0),(0,1,0))),
    }
    rods={
        'upper_X_rod_reference': cylinder(p['upper_rod_diameter']/2,80,(-40,0,sep),(1,0,0)),
        'lower_Y_rod_reference': cylinder(p['lower_rod_diameter']/2,80,(0,-40,0),(0,1,0)),
    }
    return parts,bearings,rods,fasteners

def mesh_check(shape):
    vertices, triangles = shape.tessellate(0.06,0.15)
    # Weld coincident surface-boundary vertices before counting mesh edge use.
    weld={}; ids=[]
    for v in vertices:
        key=tuple(round(c,6) for c in v.toTuple())
        if key not in weld: weld[key]=len(weld)
        ids.append(weld[key])
    edges={}
    for tri in triangles:
        a,b,c=(ids[i] for i in tri)
        assert len({a,b,c})==3, 'Degenerate mesh triangle'
        for u,v in ((a,b),(b,c),(c,a)):
            key=tuple(sorted((u,v))); edges[key]=edges.get(key,0)+1
    bad=sum(n!=2 for n in edges.values())
    assert bad==0, f'Nonmanifold mesh edges: {bad}'
    return {'vertices':len(weld),'triangles':len(triangles),'nonmanifold_edges':bad}

def main():
    parts,bearings,rods,fasteners=geometry(P)
    # Check exact BREP before tessellation expands cached bounding boxes.
    assert math.isclose(parts['centre_body'].BoundingBox().zlen,18.0,abs_tol=1e-6)
    report={'status':P['status'],'units':'mm','parts':{},'fasteners':fasteners,'checks':[]}
    for name,part in parts.items():
        assert part.isValid() and len(part.Solids())==1
        cq.exporters.export(part,str(OUT/(name+'_DRAFT.step')))
        # Cap outer flat faces on bed; centre retains assembly orientation.
        printable=part.rotate((0,0,0),(1,0,0),180) if name=='upper_X_cap' else part
        grounded=printable.translate((0,0,-printable.BoundingBox().zmin))
        cq.exporters.export(grounded,str(OUT/(name+'_DRAFT.stl')),tolerance=0.06,angularTolerance=0.15)
        restored=cq.importers.importStep(str(OUT/(name+'_DRAFT.step'))).val()
        assert restored.isValid() and len(restored.Solids())==1
        assert math.isclose(part.Volume(),restored.Volume(),rel_tol=1e-7)
        bb=part.BoundingBox()
        report['parts'][name]={'volume_mm3':part.Volume(),'bounds_mm':[bb.xlen,bb.ylen,bb.zlen],**mesh_check(part)}
    all_shapes={**parts,**bearings,**rods}
    for (a,sa),(b,sb) in combinations(all_shapes.items(),2):
        overlap=sa.intersect(sb).Volume()
        assert overlap<1e-5, f'{a} overlaps {b}: {overlap}'
    report['checks']=['Three valid single solids','STEP export/import volume agreement','Closed manifold tessellation for all three housing parts','No positive-volume overlap between housing, bearings or rods','Separate blind insert pockets clear of bearing and rod cavities']
    colours={'centre_body':(0.16,0.24,0.32),'upper_X_cap':(0.05,0.55,0.66),'lower_Y_cap':(0.95,0.49,0.13)}
    assembly=cq.Assembly(name='DRAFT_independent_clamps_NOT_OEM_FIT_VERIFIED')
    for name,part in parts.items():assembly.add(part,name=name,color=cq.Color(*colours[name]))
    assembly.export(str(OUT/'housing_assembly_DRAFT.step'))
    for name,part in bearings.items():assembly.add(part,name=name,color=cq.Color(0.65,0.69,0.73))
    for name,part in rods.items():assembly.add(part,name=name,color=cq.Color(0.78,0.81,0.85))
    assembly.export(str(OUT/'with_reference_rods_DRAFT.step'))
    # Small open semicircular saddles isolate bearing-seat print calibration.
    for key in ('upper','lower'):
        od=P[key+'_bearing_od']
        for allowance in (0.0,0.1,0.2):
            r=(od+allowance)/2
            coupon=block(od+8,12,0,r+3).cut(cylinder(r,14,(0,-7,r+3),(0,1,0)))
            assert coupon.isValid() and len(coupon.Solids())==1
            cq.exporters.export(coupon,str(OUT/f'coupon_{key}_plus{allowance:.2f}_DRAFT.stl'))
    report['peak_process_ram_mib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
