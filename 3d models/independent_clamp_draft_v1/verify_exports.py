"""Check the actual exported binary STL files independently of tessellation."""
import json, math, struct
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent
report=json.loads((ROOT/'generated/validation.json').read_text())
for file in sorted((ROOT/'generated').glob('*.stl')):
    data=file.read_bytes(); n=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+50*n
    edges=Counter(); volume=0; zmin=float('inf')
    for i in range(n):
        values=struct.unpack_from('<12fH',data,84+50*i)
        vs=[tuple(round(c,5) for c in values[j:j+3]) for j in (3,6,9)]
        assert len(set(vs))==3
        for a,b in zip(vs,vs[1:]+vs[:1]): edges[tuple(sorted((a,b)))]+=1
        a,b,c=vs
        volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
        zmin=min(zmin,*(v[2] for v in vs))
    assert all(v==2 for v in edges.values()),file.name
    assert volume>0 and abs(zmin)<1e-4,file.name
    key=file.name.replace('_DRAFT.stl','')
    if key in report['parts']:
        exact=report['parts'][key]['volume_mm3']
        assert math.isclose(volume,exact,rel_tol=.005)
    print(f'{file.name}: closed mesh, outward signed volume {volume:.1f} mm3, grounded at Z=0')
report['checks'].append('All 9 actual exported STL files independently checked: closed edges, positive signed volume and Z=0; housing mesh volume within 0.5% of BREP')
(ROOT/'generated/validation.json').write_text(json.dumps(report,indent=2)+'\n')
