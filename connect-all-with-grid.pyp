# Copyright (C) 2019 Cody Sorgenfrey

import c4d
import c4d.modules.mograph as mo
import c4d.utils as utils
import os

class res(object):
    CONNECT_ALL_WITH_GRID_CONNECT_ALL_WITH_GRID_GROUP = 1000
    CONNECT_ALL_WITH_GRID_CONNECT_ALL_WITH_GRID_OBJECTS = 1001
    CONNECT_ALL_WITH_GRID_CONNECT_ALL_WITH_GRID_GRID_UNIT = 1002
    CONNECT_ALL_WITH_GRID_STEM_TO_GRID_GROUP = 1003
    CONNECT_ALL_WITH_GRID_STEM_TO_GRID_LENGTH_UNITS = 1004
    CONNECT_ALL_WITH_GRID_STEM_TO_GRID_DIRECTION = 1005
    CONNECT_ALL_WITH_GRID_STEM_TO_GRID_DIRECTION_XP = 0
    CONNECT_ALL_WITH_GRID_STEM_TO_GRID_DIRECTION_YP = 1
    CONNECT_ALL_WITH_GRID_STEM_TO_GRID_DIRECTION_ZP = 2
    CONNECT_ALL_WITH_GRID_STEM_TO_GRID_DIRECTION_ = -1
    CONNECT_ALL_WITH_GRID_STEM_TO_GRID_DIRECTION_XN = 3
    CONNECT_ALL_WITH_GRID_STEM_TO_GRID_DIRECTION_YN = 4
    CONNECT_ALL_WITH_GRID_STEM_TO_GRID_DIRECTION_ZN = 5
res = res()

def load_bitmap(path):
    path = os.path.join(os.path.dirname(__file__), path)
    bmp = c4d.bitmaps.BaseBitmap()
    if bmp.InitWith(path)[0] != c4d.IMAGERESULT_OK:
        bmp = None
    return bmp

def snap(v, mult, validate):
    vals = [int(round(v.x / mult)) * mult, int(round(v.y / mult)) * mult, int(round(v.z / mult)) * mult]
    if validate:
        for i in vals:
            if i == 0:
                i = mult

    return c4d.Vector(vals[0], vals[1], vals[2])

class ConnectAllWithGridData(c4d.plugins.ObjectData):
    PLUGIN_ID = 1053147
    PLUGIN_NAME = 'Connect All With Grid'
    PLUGIN_INFO = c4d.OBJECT_GENERATOR | c4d.OBJECT_ISSPLINE
    PLUGIN_DESC = 'Oconnectallwithgrid'
    PLUGIN_ICON = load_bitmap('res/icons/Connect All With Grid.tiff')
    PLUGIN_DISKLEVEL = 0
    LAST_FRAME = -1

    @classmethod
    def Register(cls):
        return c4d.plugins.RegisterObjectPlugin(
            cls.PLUGIN_ID,
            cls.PLUGIN_NAME,
            cls,
            cls.PLUGIN_DESC,
            cls.PLUGIN_INFO,
            cls.PLUGIN_ICON,
            cls.PLUGIN_DISKLEVEL
        )

    def Init(self, node):
        self.InitAttr(node, c4d.InExcludeData, [res.CONNECT_ALL_WITH_GRID_CONNECT_ALL_WITH_GRID_OBJECTS])
        self.InitAttr(node, float, [res.CONNECT_ALL_WITH_GRID_CONNECT_ALL_WITH_GRID_GRID_UNIT])
        self.InitAttr(node, float, [res.CONNECT_ALL_WITH_GRID_STEM_TO_GRID_LENGTH_UNITS])
        self.InitAttr(node, int, [res.CONNECT_ALL_WITH_GRID_STEM_TO_GRID_DIRECTION])

        node[res.CONNECT_ALL_WITH_GRID_CONNECT_ALL_WITH_GRID_GRID_UNIT] = 10.0
        node[res.CONNECT_ALL_WITH_GRID_STEM_TO_GRID_LENGTH_UNITS] = 1.0

        doc = c4d.documents.GetActiveDocument()
        self.LAST_FRAME = doc.GetTime().GetFrame(doc.GetFps())

        return True

    def CheckDirty(self, op, doc) :
        frame = doc.GetTime().GetFrame(doc.GetFps())
        if frame != self.LAST_FRAME:
            self.LAST_FRAME = frame
            op.SetDirty(c4d.DIRTYFLAGS_DATA)

    def GetContour(self, op, doc, lod, bt):
        inEx = op[res.CONNECT_ALL_WITH_GRID_CONNECT_ALL_WITH_GRID_OBJECTS]
        inExCount = inEx.GetObjectCount()
        gridUnit = op[res.CONNECT_ALL_WITH_GRID_CONNECT_ALL_WITH_GRID_GRID_UNIT]
        stemLength = op[res.CONNECT_ALL_WITH_GRID_STEM_TO_GRID_LENGTH_UNITS]
        stemDir = op[res.CONNECT_ALL_WITH_GRID_STEM_TO_GRID_DIRECTION]

        if inExCount is 0: return None

        inMarrs = []
        for x in range(inExCount):
            obj = inEx.ObjectFromIndex(op.GetDocument(), x)

            if obj is not None:
                md = mo.GeGetMoData(obj)
                if md is not None:
                    mdCount = md.GetCount()
                    if mdCount is not 0:
                        moMarr = md.GetArray(c4d.MODATA_MATRIX)
                        moFlags = md.GetArray(c4d.MODATA_FLAGS)
                        for x in range(mdCount):# put marrs into cloner space
                            if moFlags[x] & c4d.MOGENFLAG_CLONE_ON and not moFlags[x] & c4d.MOGENFLAG_DISABLE:
                                moMarr[x] = obj.GetMg() * moMarr[x]
                                inMarrs.append(moMarr[x])
                else:
                    inMarrs.append(obj.GetMg())

        if len(inMarrs) is 0: return None

        outPoints = []
        outPoints.append(inMarrs[0].off) # insert firset point
        for x in range(len(inMarrs) - 1):
            m1 = inMarrs[x]
            m2 = inMarrs[x + 1]

            moveAmount = stemLength * gridUnit
            if stemDir is 1:
                moveVec = c4d.Vector(0, moveAmount, 0)
            elif stemDir is 2:
                moveVec = c4d.Vector(0, 0, moveAmount)
            elif stemDir is 3:
                moveVec = c4d.Vector(-moveAmount, 0, 0)
            elif stemDir is 4:
                moveVec = c4d.Vector(0, -moveAmount, 0)
            elif stemDir is 5:
                moveVec = c4d.Vector(0, 0, -moveAmount)
            else:
                moveVec = c4d.Vector(moveAmount, 0, 0)

            moveMarr = utils.MatrixMove(moveVec)

            # m1 stem
            newPoint = (m1 * moveMarr).off
            stemPoint = snap(newPoint, gridUnit, False)
            outPoints.append(stemPoint)

            # m2 stem
            newPoint = (m2 * moveMarr).off
            stemPoint = snap(newPoint, gridUnit, False)
            outPoints.append(stemPoint)

            # next point
            outPoints.append(m2.off)

        spline = c4d.SplineObject(0, c4d.SPLINETYPE_LINEAR)
        spline.ResizeObject(len(outPoints), 1)
        spline.SetSegment(0, len(outPoints), False)
        spline[c4d.SPLINEOBJECT_INTERPOLATION] = c4d.SPLINEOBJECT_INTERPOLATION_NONE

        for x in range(len(outPoints)):
            spline.SetPoint(x, outPoints[x])

        return spline

if __name__ == '__main__':
    ConnectAllWithGridData.Register()
