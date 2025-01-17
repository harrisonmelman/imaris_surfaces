import ImarisLib
import numpy as np
import math as m
import random
import nrrd

label = list(range(1, 181, 30)) + list(range(1001, 1181, 30))


def GetServer():
    vImarisLib = ImarisLib.ImarisLib()
    vServer = vImarisLib.GetServer()
    return vServer;


vServer = GetServer()
vImarisLib = ImarisLib.ImarisLib()
v = vImarisLib.GetApplication(102)
img = v.GetImage(0)  # load NeuN
# img2 = v.GetImage(1)#load labelmap data
# print(type(img2))
vExtentMin = [img.GetExtendMinX(), img.GetExtendMinY(), img.GetExtendMinZ()]
# vExtentMin2 =[img2.GetExtendMinX(),img2.GetExtendMinY(),img2.GetExtendMinZ()]
print('vExtentMin:', vExtentMin)
aChannel = 0
label = list(range(1, 181, 100)) + list(range(1001, 1181, 100))
# generate a surface for each label

for single_label in label:
    labels = [single_label - 0.5, single_label + 0.5]
    vSur = v.GetImageProcessing().DetectSurfacesWithUpperThreshold(img, [], aChannel, 0, 0, True, False, labels[0],
                                                                   True, False, labels[1], None)
    v.GetSurpassScene().AddChild(vSur, 1)
    vSur.SetName('Surface ' + str(single_label))
    # vSur.SetColorRGBA(0xFF0000FF)
