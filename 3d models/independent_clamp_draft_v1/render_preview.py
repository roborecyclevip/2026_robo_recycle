"""Render CAD-derived review views, without a desktop CAD application."""
import os
os.environ['MPLBACKEND']='Agg'
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from build_model import geometry,P,OUT

parts,bearings,rods,fasteners=geometry(P)
palette={'centre_body':'#34465a','upper_X_cap':'#168f9e','lower_Y_cap':'#ed8b36'}

def draw_shape(ax,shape,color,shift=(0,0,0),alpha=1):
    verts,tris=shape.tessellate(0.16,0.22)
    v=np.array([p.toTuple() for p in verts])+np.array(shift)
    polys=v[np.array(tris)]
    normals=np.cross(polys[:,1]-polys[:,0],polys[:,2]-polys[:,0])
    lengths=np.linalg.norm(normals,axis=1); lengths[lengths==0]=1
    normals/=lengths[:,None]
    light=np.array([-.3,-.5,1]);light/=np.linalg.norm(light)
    shade=.48+.52*np.abs(normals@light)
    fc=np.clip(shade[:,None]*np.array(colors.to_rgb(color)),0,1)
    col=Poly3DCollection(polys,facecolors=fc,edgecolors='none',alpha=alpha,zsort='average',antialiased=False)
    ax.add_collection3d(col)

fig=plt.figure(figsize=(14,9),facecolor='#f4f6f8')
fig.text(.045,.95,'S5 gantry · independent bearing clamps',fontsize=22,weight='bold',color='#182c40')
fig.text(.045,.914,'PARAMETRIC CONCEPT 01  /  FIT NOT VERIFIED  /  MOTOR ADAPTER NOT INCLUDED',fontsize=10,color='#a54c16')
for i,exploded in enumerate((False,True)):
    ax=fig.add_axes([.02+i*.49,.23,.48,.63],projection='3d',facecolor='#f4f6f8')
    for name,part in parts.items():
        shift=(0,0,24 if name=='upper_X_cap' else -24 if name=='lower_Y_cap' else 0) if exploded else (0,0,0)
        draw_shape(ax,part,palette[name],shift)
    for name,part in bearings.items():draw_shape(ax,part,'#b8c3cb')
    for name,part in rods.items():draw_shape(ax,part,'#cad4dc')
    if exploded:
        for f in fasteners:
            x,y=f['xy'];z=f['entry_z'];end=z+33 if f['clamp']=='upper' else z-33
            ax.plot([x,x],[y,y],[z,end],color=palette['upper_X_cap' if f['clamp']=='upper' else 'lower_Y_cap'],lw=.8,ls='--')
    ax.view_init(elev=23,azim=-55)
    ax.set_xlim(-43,43);ax.set_ylim(-43,43)
    ax.set_zlim(-42 if exploded else -20,67 if exploded else 45)
    ax.set_box_aspect((86,86,109 if exploded else 65))
    ax.set_axis_off()
    ax.set_title('Assembled concept' if not exploded else 'Exploded · independent screw paths',fontsize=13,color='#182c40',pad=2)
fig.text(.045,.205,'UPPER CAP',color=palette['upper_X_cap'],weight='bold',fontsize=12)
fig.text(.045,.155,'10 mm rod\n17.44 OD × 29.08 bearing',fontsize=11,color='#263c4f',linespacing=1.5)
fig.text(.36,.205,'CENTRE BODY',color=palette['centre_body'],weight='bold',fontsize=12)
fig.text(.36,.155,'Separate blind insert pockets\nNo bolt spans both caps',fontsize=11,color='#263c4f',linespacing=1.5)
fig.text(.69,.205,'LOWER CAP',color=palette['lower_Y_cap'],weight='bold',fontsize=12)
fig.text(.69,.155,'8 mm rod\n13.14 OD × 24.02 bearing',fontsize=11,color='#263c4f',linespacing=1.5)
fig.text(.045,.07,'20 mm rod-centre separation shown is a placeholder, NOT an S5 specification.',fontsize=11,color='#a54c16')
fig.text(.045,.038,'Proposed 48 × 48 mm envelope and new M3 hardware require clearance and fit checks. Units: mm.',fontsize=10,color='#566674')
fig.savefig(OUT/'preview_DRAFT.png',dpi=140,facecolor=fig.get_facecolor())
plt.close(fig)
print(OUT/'preview_DRAFT.png')
