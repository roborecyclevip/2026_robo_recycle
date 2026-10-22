"""V3 captive-nut prototype with fixed motor feet. Assumed interface; not fit/load verified."""
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

def hex_prism(af,height,x,y,z,angle=0):
    radius=af/math.sqrt(3)
    pts=[(x+radius*math.cos(math.radians(angle+60*i)),y+radius*math.sin(math.radians(angle+60*i))) for i in range(6)]
    return cq.Workplane('XY').polyline(pts).close().extrude(height).translate((0,0,z)).val()

def nut_slot(p,x,y,z,axis,edge):
    h=p['nut_pocket_height']; af=p['nut_pocket_af']
    pocket=hex_prism(af,h,x,y,z,90 if axis=='y' else 0)
    if axis=='y':
        channel=block(af,abs(edge-y),z,z+h).translate((x,(edge+y)/2,0))
    else:
        channel=block(abs(edge-x),af,z,z+h).translate(((edge+x)/2,y,0))
    return pocket.fuse(channel).clean()

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
    # Fixed motor feet bypass the lower cap; one-mm notches permit its closure.
    for sx in (-1,1):
        for sy in (-1,1):
            x,y=sx*p['motor_pitch_x']/2,sy*p['motor_pitch_y']/2
            foot=block(p['motor_pad_size'],p['motor_pad_size'],p['motor_mount_z'],4).translate((x,y,0))
            parts['centre_body']=parts['centre_body'].fuse(foot).clean()
            notch=block(p['motor_pad_size']+2,p['motor_pad_size']+2,zlo-1,1).translate((x,y,0))
            parts['lower_Y_cap']=parts['lower_Y_cap'].cut(notch)
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
                start,length=(sep,zhi-sep+1) if upper else (zlo-1,1-zlo)
                recess=p[side+'_head_recess_depth']
                recess_z=zhi-recess if upper else zlo-.01
                parts[cap]=parts[cap].cut(cylinder(p['screw_clearance_diameter']/2,length,(x,y,start)))
                parts[cap]=parts[cap].cut(cylinder(p['head_recess_diameter']/2,recess+.01,(x,y,recess_z)))
                nz=p[side+'_nut_bottom']
                pocket=nut_slot(p,x,y,nz,'y' if upper else 'x',sy*(d/2+1) if upper else sx*(w/2+1))
                bore=cylinder(p['screw_clearance_diameter']/2,9,(x,y,9 if upper else 0))
                for tool in pockets:
                    assert pocket.intersect(tool).Volume()<1e-6, 'Nut slot intersects bearing/rod cavity'
                    assert bore.intersect(tool).Volume()<1e-6, 'Bolt bore intersects bearing/rod cavity'
                parts['centre_body']=parts['centre_body'].cut(pocket).cut(bore)
                fasteners.append({'clamp':side,'xy':[x,y],'nut_bottom':nz,'bolt_length':p['clamp_bolt_length']})
    for sx in (-1,1):
        for sy in (-1,1):
            x,y=sx*p['motor_pitch_x']/2,sy*p['motor_pitch_y']/2
            pocket=nut_slot(p,x,y,p['motor_nut_bottom'],'y',sy*(p['motor_pitch_y']/2+p['motor_pad_size']/2+1))
            bore=cylinder(p['screw_clearance_diameter']/2,19,(x,y,p['motor_mount_z']))
            for tool in pockets:
                assert pocket.intersect(tool).Volume()<1e-6
                assert bore.intersect(tool).Volume()<1e-6
            parts['centre_body']=parts['centre_body'].cut(pocket).cut(bore)
            fasteners.append({'clamp':'motor','xy':[x,y],'nut_bottom':p['motor_nut_bottom'],'bolt_length':p['motor_bolt_length']})
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
    # The core spans z=0..18; the fixed mounting feet extend below it.
    assert math.isclose(P['rod_centre_spacing'],18.0,abs_tol=1e-6)
    assert math.isclose(parts['centre_body'].BoundingBox().zlen,34.0,abs_tol=1e-6)
    report={'status':P['status'],'units':'mm','parts':{},'fasteners':fasteners,'checks':[]}
    for name,part in parts.items():
        assert part.isValid() and len(part.Solids())==1
        cq.exporters.export(part,str(OUT/(name+'_DRAFT.step')))
        # Cap outer flat faces on bed; centre retains assembly orientation.
        printable=part.rotate((0,0,0),(1,0,0),180) if name in ('upper_X_cap','centre_body') else part
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
    # Check idealized purchased hardware against every printed component.
    report['hardware_checks']=[]
    zhi=P['rod_centre_spacing']+(P['upper_bearing_od']+P['bearing_diametral_allowance'])/2+P['outer_wall']
    zlo=-(P['lower_bearing_od']+P['bearing_diametral_allowance'])/2-P['outer_wall']
    for f in fasteners:
        x,y=f['xy']; side=f['clamp']; upper=side=='upper'
        nz=f['nut_bottom']
        # Nuts load against the upper roof for top screws, lower floor for bottom screws.
        actual_nz=nz+P['nut_pocket_height']-P['nut_nominal_height'] if upper else nz
        nut=hex_prism(P['nut_nominal_af'],P['nut_nominal_height'],x,y,actual_nz,0 if side=='lower' else 90).cut(cylinder(1.5,4,(x,y,actual_nz-1)))
        if upper: seat=zhi-P['upper_head_recess_depth']; head=seat+P['washer_thickness']; tip=head-f['bolt_length']
        elif side=='lower': seat=zlo+P['lower_head_recess_depth']; head=seat-P['washer_thickness']; tip=head+f['bolt_length']
        else: seat=P['motor_mount_z']-P['motor_flange_assumed_thickness']; head=seat-P['washer_thickness']; tip=head+f['bolt_length']
        bolt=cylinder(1.5,f['bolt_length'],(x,y,min(head,tip))).fuse(cylinder(3.0,2.5,(x,y,head if upper else head-2.5)))
        washer=cylinder(P['washer_diameter']/2,P['washer_thickness'],(x,y,seat if upper else head)).cut(cylinder(1.75,1,(x,y,seat-.25 if upper else head-.25)))
        for hardware in (nut,bolt,washer):
            for name,part in parts.items():
                assert hardware.intersect(part).Volume()<1e-5, f'{side} hardware collision with {name}'
        protrusion=actual_nz-tip if upper else tip-(actual_nz+P['nut_nominal_height'])
        assert protrusion>=.5, f'{side}: less than one pitch beyond nut'
        # Closed-gap bolt tip must remain within its blind bore.
        if upper: assert tip-P['split_gap']>9
        elif side=='lower': assert tip+P['split_gap']<9
        report['hardware_checks'].append({'group':side,'xy':[x,y],'bolt_length':f['bolt_length'],'thread_beyond_nut_mm':protrusion})
    # Entire lower-cap closure sweep clears fixed feet and body (excluding bearing preload).
    assert parts['lower_Y_cap'].translate((0,0,P['split_gap'])).intersect(parts['centre_body']).Volume()<1e-5
    report['checks']=['Three valid single solids','18 mm core spacing and 34 mm fixed body including feet','STEP round-trip volume agreement','Closed manifold meshes','No housing/bearing/rod overlap','Nut channels clear bearing cavities','12 bolts, nuts and washers clear printed parts; >= one pitch beyond each nut','Clamp bolt tips clear blind ends through closure','Lower cap clears fixed motor feet through 0.6 mm closure']
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
    # Cheap interface gauge: compare all four hole centres to the actual stock top.
    gauge=block(48,52,0,2).cut(block(26,30,-1,3))
    for sx in (-1,1):
        for sy in (-1,1):
            gauge=gauge.cut(cylinder(1.7,4,(sx*P['motor_pitch_x']/2,sy*P['motor_pitch_y']/2,-1)))
    cq.exporters.export(gauge,str(OUT/'motor_pattern_CHECK_FIRST.stl'))
    # Side-load nut test: exact same pocket/channel as the main component.
    coupon=block(16,16,0,9).cut(nut_slot(P,0,0,3,'y',9)).cut(cylinder(1.7,11,(0,0,-1)))
    cq.exporters.export(coupon,str(OUT/'M3_nut_fit_CHECK_FIRST.stl'))
    report['peak_process_ram_mib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
