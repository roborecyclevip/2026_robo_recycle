"""Accurate offscreen CAD render with depth-tested visibility."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import vtk
from build_model import geometry,P,OUT

parts,bearings,rods,fasteners=geometry(P)
palette={'centre_body':(0.20,0.28,0.36),'upper_X_cap':(0.06,0.56,0.63),'lower_Y_cap':(0.93,0.50,0.18)}

def actor(shape,color,shift=(0,0,0)):
    vs,ts=shape.tessellate(.1,.15)
    points=vtk.vtkPoints()
    for v in vs:points.InsertNextPoint(v.x+shift[0],v.y+shift[1],v.z+shift[2])
    cells=vtk.vtkCellArray()
    for tri in ts:
        cells.InsertNextCell(3)
        for i in tri:cells.InsertCellPoint(i)
    mesh=vtk.vtkPolyData();mesh.SetPoints(points);mesh.SetPolys(cells)
    normals=vtk.vtkPolyDataNormals();normals.SetInputData(mesh);normals.ConsistencyOn();normals.AutoOrientNormalsOn();normals.SetFeatureAngle(35)
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
    a=vtk.vtkActor();a.SetMapper(mapper);a.GetProperty().SetColor(*color)
    a.GetProperty().SetAmbient(.28);a.GetProperty().SetDiffuse(.72);a.GetProperty().SetSpecular(.15)
    return a

def scene(exploded):
    r=vtk.vtkRenderer();r.SetBackground(.957,.965,.973)
    for name,part in parts.items():
        z=24 if name=='upper_X_cap' else -24 if name=='lower_Y_cap' else 0
        r.AddActor(actor(part,palette[name],(0,0,z if exploded else 0)))
    for shape in bearings.values():r.AddActor(actor(shape,(.57,.64,.70)))
    for shape in rods.values():r.AddActor(actor(shape,(.73,.79,.84)))
    window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1);window.SetSize(900,800)
    window.AddRenderer(r);window.SetMultiSamples(4)
    cam=r.GetActiveCamera();cam.SetPosition(115,-150,100);cam.SetFocalPoint(0,0,10);cam.SetViewUp(0,0,1)
    cam.ParallelProjectionOn();cam.SetParallelScale(65 if exploded else 52)
    r.ResetCameraClippingRange();window.Render()
    capture=vtk.vtkWindowToImageFilter();capture.SetInput(window);capture.ReadFrontBufferOff();capture.Update()
    path=OUT/('exploded_scene.png' if exploded else 'assembled_scene.png')
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(path));writer.SetInputConnection(capture.GetOutputPort());writer.Write()
    window.Finalize()
    return Image.open(path).convert('RGB')

if __name__=='__main__':
    im=Image.new('RGB',(1800,1200),'#f4f6f8');d=ImageDraw.Draw(im)
    font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    def txt(x,y,s,size=24,color='#23384c',weight=False):d.text((x,y),s,font=ImageFont.truetype(bold if weight else font,size),fill=color)
    im.paste(scene(False),(0,150));im.paste(scene(True),(900,150))
    txt(55,35,'S5 gantry · independent bearing clamps',42,weight=True)
    txt(55,100,'PROTOTYPE 03 / CAPTIVE M3 NUTS + FIXED MOTOR FEET / CHECK FIT BEFORE USE',23,'#a54c16')
    txt(205,170,'Assembled concept',26,weight=True);txt(1090,170,'Exploded components',26,weight=True)
    for x,title,desc,col in [(55,'UPPER CAP','4 × M3×15 bolts\n10 mm rod / 17.44 OD bearing','#168f9e'),(650,'FIXED BODY + FEET','12 side-loaded M3 hex nuts\nMotor bolts do not load caps','#34465a'),(1250,'LOWER CAP','4 × M3×15 bolts\n8 mm rod / 13.14 OD bearing','#d67925')]:
        txt(x,960,title,25,col,True);txt(x,1003,desc,23)
    txt(55,1110,'18 mm bearing spacing. Motor holes: assumed 36 × 40 mm. Print pattern gauge first.',24,'#a54c16')
    txt(55,1155,'48 × 52 mm envelope. Fixed motor face 16 mm below lower rod centre. Fit/load untested.',21,'#526678')
    im.save(OUT/'preview_DRAFT.png')
    print(OUT/'preview_DRAFT.png')
