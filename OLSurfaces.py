from AnnexConfig import *
import pyproj
import math
from osgeo import ogr, osr
import numpy as np
class Surfaces:
    def __init__(self,airportName:str
                 ,AirportCode: str="VTXX",
                 rwyWidth: float=45.0,
                 initEPSG: str='4326',
                 tarEPSG: str="32647",
                 approachTypeTHR0: str="NPA",
                 approachTypeTHR1: str="NPA" 
            ):
        
        self.AirportName = airportName
        self.rwyWidth = rwyWidth
        self.AirportCode = AirportCode
        self.initEPSG = pyproj.Proj(f"+init=EPSG:{initEPSG}")
        self.tarEPSG = pyproj.Proj(f"+init=EPSG:{tarEPSG}")
        self.approachTypeTHR0 = approachTypeTHR0
        self.approachTypeTHR1 = approachTypeTHR1

    def createRunwayParameters(self,THR0:dict,THR1:dict):
        self._rwy_info = {
            "THR0":{
                "coord":THR0["coord"],
                "approachType":THR0["AppType"]
            },
            "THR1":{
                "coord":THR1["coord"],
                "approachType":THR1["AppType"]
            }
        }

    def getCodeNumber(self,rwyLength):
        if rwyLength >= 1800:
            return 4
        elif rwyLength > 1000 and rwyLength < 1800:
            return 3
        elif rwyLength > 799  and rwyLength <= 1000:
            return 2
        else:
            return 1

    def coordinateTransform(self,point):
        x,y = pyproj.transform(self.initEPSG,self.tarEPSG,point[0],point[1])
        return x,y

    def coordinateTransformInv(self,point):
        lng,lat = pyproj.transform(self.tarEPSG,self.initEPSG,point[0],point[1])
        return lng,lat

    def deg2rad(self,deg):
        theta_rad = math.pi/2 - math.radians(deg)
        return theta_rad

    def bearing(self,rwThreshold0,rwThreshold1):

        geod = pyproj.Geod(ellps = "WGS84")

        # azimuth from rwThreshold1 to rwThreshold0

        forward, back, dist = geod.inv(rwThreshold1[0],rwThreshold1[1],rwThreshold0[0],rwThreshold0[1])

        return {"forward":forward,"backward":back,"dist":dist}

    def ComputePointPos(self,x0,y0,dist,theta):
        geod = pyproj.Geod(ellps = "WGS84")
        coords = geod.fwd(x0,y0,theta,dist)
        return coords
    
    def meterDistTodegree(self,distM):
        distInMM = (0.000001*(distM*1000))/111.139
        return distInMM +1.941
    
    def GetRWYInfo(self,bearingAndDistInfo, ):
        x1,y1 = self.coordinateTransform(self._rwy_info["THR0"]["coord"])
        self._rwy_info["THR0"]["utm"] = [x1,y1,self._rwy_info["THR0"]["coord"][-1]]
        x2,y2 = self.coordinateTransform(self._rwy_info["THR1"]["coord"])
        self._rwy_info["THR1"]["utm"] = [x2,y2,self._rwy_info["THR1"]["coord"][-1]]
        self._rwy_info["bearing"] = bearingAndDistInfo
        # Length of runway strip
        self._rwy_info["THR0"]["lengthOfRWYStrip"] = LenOfRWYStrip[self._rwy_info["codeNumber"]][self.approachTypeTHR0]
        self._rwy_info["THR1"]["lengthOfRWYStrip"] = LenOfRWYStrip[self._rwy_info["codeNumber"]][self.approachTypeTHR1]
        # Width of runway string
        self._rwy_info["THR0"]["widthOfRWYStrip"] = WidthOfRWYStrip[self._rwy_info["codeNumber"]][self.approachTypeTHR0]
        self._rwy_info["THR1"]["widthOfRWYStrip"] = WidthOfRWYStrip[self._rwy_info["codeNumber"]][self.approachTypeTHR1]
        self._rwy_info["THR0"]["SurfaceParams"] = ApproachType[self.approachTypeTHR0]
        self._rwy_info["THR1"]["SurfaceParams"] = ApproachType[self.approachTypeTHR1]

    def createRunway(self):
        bearingAndDist = self.bearing(self._rwy_info['THR0']["coord"],self._rwy_info['THR1']['coord'])
        #draw strip
        self._rwy_info["codeNumber"] = self.getCodeNumber(bearingAndDist["dist"])
        self.GetRWYInfo(bearingAndDist)

    def findCenterOfRWY(self):
        NorthDiff = self._rwy_info["THR0"]["utm"][1] - self._rwy_info["THR1"]["utm"][1]
        EastDiff = self._rwy_info["THR0"]["utm"][0] - self._rwy_info["THR1"]["utm"][0]

        NorthCen  = self._rwy_info["THR0"]["utm"][1] - (NorthDiff/2)
        EastCen = self._rwy_info["THR0"]["utm"][0] - (EastDiff/2)

        self._rwy_info["centerRWY"] = [EastCen,NorthCen]

    def createLimitSurfaces(self):
        # first rwy
        for surface in self._rwy_info["THR0"]["SurfaceParams"]:
            if surface == "take_off_climb":
                self.takeOffclimb("THR0")
            elif surface == "conical":
                self.conical()
            elif surface == "InnerHorizontal":
                self.innerHorizontal()
            elif surface == "Approach":
                self.Approach("THR1")
            elif surface == "FirstSection":
                self.FirstSection()
            elif surface == "SecondSection":
                self.SecondSection()
            elif surface == "HorizontalSection":
                self.HorizontalSection()
            elif surface == "Transitional":
                self.Transitional()
            elif surface == "InnerTransitional":
                self.InnerTransitional()
            elif surface == "BalkedLanding":
                self.Balkedlanding()
            else :
                "Out of the requirements" 
        # second rwy


    def takeOffClimbCenterPath(self,THR0:tuple,dists:list,surfaceParams):
        """
        In this function, we want to compute the coordinate on each a segment path according to the requirement
        The input is required surface parameter in the AnnexConfig.py
        The initial point will be THR.
        *   In the argument dist is the distances which are not included the length of RWY strip

        """   
        takeOffPathCoords = []
        bearingAng = self._rwy_info["bearing"]['forward']
        for dist in dists:
            lon,lat,_ = self.ComputePointPos(THR0[0],THR0[1],surfaceParams["DistFromRWYEnd"] + dist,bearingAng)
            elev = THR0[-1] + (dist * (surfaceParams["slope"]/100))
            takeOffPathCoords.append([lon,lat,elev])
        return takeOffPathCoords
    
    def takeOffclimb(self,thrName):
        # Get take off climb path coordinates
        surfaceParams = self._rwy_info[thrName]["SurfaceParams"]["take_off_climb"][self._rwy_info["codeNumber"]]
        THR0 = self._rwy_info["THR0"]["coord"]
        distOftakeOffSect = ((surfaceParams["FinalWidth"]/2) - (surfaceParams["lenOfInnerEdge"]/2)) / (surfaceParams["Divergence"]/100)
        dists = [0,distOftakeOffSect,surfaceParams["Len"]]
        THR0TakeOffPath = self.takeOffClimbCenterPath(THR0,dists,surfaceParams)
        
        # Create an array for Distances away from take off path
        distFromTakeOffPath = [
            surfaceParams["lenOfInnerEdge"]/2,
            surfaceParams["FinalWidth"]/2,
            surfaceParams["FinalWidth"]/2,
        ]
        # create take off climb surface
        cnt = [0,1,2]
        cnt_inv = [2,1,0]
        takeOffSurface = []
        # i = 0
        bearingAng = self._rwy_info["bearing"]['forward']
        for i in cnt:
            for j in range(3):
                    lon,lat,_ = self.ComputePointPos(THR0TakeOffPath[i][0],THR0TakeOffPath[i][1],distFromTakeOffPath[i],bearingAng +90)
                    takeOffSurface.append([lon,lat,THR0TakeOffPath[i][-1]])
        for k in cnt_inv:
                    lon,lat,_ = self.ComputePointPos(THR0TakeOffPath[k][0],THR0TakeOffPath[k][1],distFromTakeOffPath[k],bearingAng +270)
                    takeOffSurface.append([lon,lat,THR0TakeOffPath[k][-1]])
        
        return takeOffSurface.append(takeOffSurface[0])
    
    def conical(self):
        pass

    def innerHorizontal(self):
        pass 

    def InnerApproach(self):
        pass 
    
    def ApproachCenterPath(self,thrName):
        THRinit = self._rwy_info[thrName]["coord"]
        ApproachsurfaceParams = self._rwy_info[thrName]["SurfaceParams"]["Approach"][self._rwy_info["codeNumber"]]
        FirstSectionSurfaceParams = self._rwy_info[thrName]["SurfaceParams"]["FirstSection"][self._rwy_info["codeNumber"]]
        SecondSectionSurfaceParams = self._rwy_info[thrName]["SurfaceParams"]["SecondSection"][self._rwy_info["codeNumber"]]
        HorizontalSectionSurfaceParams = self._rwy_info[thrName]["SurfaceParams"]["HorizontalSection"][self._rwy_info["codeNumber"]]
        dists = [0,FirstSectionSurfaceParams["len"], SecondSectionSurfaceParams["len"],HorizontalSectionSurfaceParams["len"]]
        dists = np.array(dists)
        slopes = [0,FirstSectionSurfaceParams["slope"],SecondSectionSurfaceParams["slope"],HorizontalSectionSurfaceParams["slope"]]
        slopes = np.array(slopes)
        slopes = slopes/100
        bearingAng = self._rwy_info["bearing"]["backward"]
        centerPath = []
        surfaceName = ["HorizontalSection","FirstSection","SecondSection","SecondSection"]
        i = 0
        print(dists)
        print(dists * slopes)
        distAcc = 0
        elev = 0
        for i,dist in enumerate(dists):
            lon, lat, _ = self.ComputePointPos(THRinit[0],THRinit[1],distAcc+ApproachsurfaceParams["DistFromTHR"],bearingAng)
            elev += THRinit[-1] +(slopes[i] * dist)
            print(elev)
            centerPath.append([lon,lat,elev])
            distAcc = distAcc + dist
            i += 1
        centerPath[-1][-1] = centerPath[-2][-1]
        print(centerPath)
        return centerPath
    def Approach(self,THRname):
        self.ApproachCenterPath(THRname)
        
    def FirstSection(self):
        pass 
    def SecondSection(self):
        pass 

    def HorizontalSection(self):
        pass

    def Transitional(self):
        pass 

    def InnerTransitional(self):
        pass 

    def Balkedlanding(self):
        pass 


