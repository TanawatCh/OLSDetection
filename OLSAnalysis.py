from osgeo import ogr,gdal
import numpy as np 
import glob
import json
import pyproj
from BAGsConfig import *
from OLSurfaces import *
import AnnexConfig

class ObstacleDetection:
    def intiAirportParams(self,ICAO_Airport:str):
        if ICAO_Airport not in BAGsAirports:
            return "Airport is not in the Database"
        else:
            return BAGsAirports[ICAO_Airport]

    def load_terrain(self,url:str):
        terrain_files = glob.glob(url + "*")
        ds = None
        for file in terrain_files:
            if "tif" in file or "tiff" in file:
                print(file)
                ds = gdal.Open(file)
                break
        return {
            "geoTransform":ds.GetGeoTransform(),
            "array":ds.ReadAsArray()
        }

    def load_data_from_file(self,url:str):
        ds = ogr.Open(url)
        return ds

    def get_features(self,ds,obstaclesMerged):
        layers = ds.GetLayer()
        dsFeatures = []
        for feat in layers:
            geoJson = feat.ExportToJson()
            obstaclesMerged.append(json.loads(geoJson))

        # return dsFeatures

    def load_data_from_folder(self,_dir:str,airportICAOCode:str,ext:str):
        try:
            len(airportICAOCode) == 4
        except:
            print("[WARING] Please check the airport ICAO code")
        files = glob.glob(_dir + "*"+ext)
        obstaclesMerged = []
        for file in files:
            if airportICAOCode in file:
                ds = self.load_data_from_file(file)
                self.get_features(ds,obstaclesMerged)
            else:
                continue
        return obstaclesMerged

    def get_terrain_index(self,terrainArr,GeoTrans):
        h,w = terrainArr.shape
        NorthIdx = np.linspace(GeoTrans[3],GeoTrans[3] + (h*GeoTrans[5]),num=h)
        EastIdx = np.linspace(GeoTrans[0],GeoTrans[0] + (w*GeoTrans[1]),num=w)
        return {"NorthIdx":NorthIdx, "EastIdx":EastIdx}

    def get_max_elev_index(self,geom, terrainArray,terrainIdx):
        geom_np = np.array(geom[0])
        verticesElev = []
        for i in range(len(geom[0])):
            NorthDiff = terrainIdx["NorthIdx"] - np.array(geom_np[i,1])
            EastDiff = terrainIdx["EastIdx"] - np.array(geom_np[i,0])

            NorthIdx = np.abs(NorthDiff).argmin(axis=-1)
            EastIdx = np.abs(EastDiff).argmin(axis=-1)
    
            verticesElev.append(terrainArray[EastIdx][NorthIdx])

        return {"maxElev":np.max(np.array(verticesElev)),"latlon":geom_np[np.array(verticesElev).argmax()]}

    def check_height_allowance(self,nearest_vertice:np.array,perpen_dist:float,slope_of_surface:float,obst_elev_from_attr:float,vert_acc:float=1.0):
        """
            Note: a slope value of the surface used in this function is scaled within [0, 1.0]
            The return value is Boolen. If it is False meaning "not allowing", otherwise allow.
        """
        print(perpen_dist * slope_of_surface)
        # print(nearest_vertice)
        height_allowance = (perpen_dist * slope_of_surface) + nearest_vertice[-1]
        obst_elev = obst_elev_from_attr + vert_acc
        return {
            "overtake":round(obst_elev - height_allowance,3),
            "allowance": True if height_allowance - obst_elev > 0 else False
        }

    def get_nearest_vertice(self,surface_geom:np.array,point:np.array):
        point_np = point
        surface_geom_np = surface_geom

        x_diff = np.power(surface_geom_np[0,:,0] - point_np[0],2)
        y_diff = np.power(surface_geom_np[0,:,1] - point_np[1],2)

        eucl_dist = x_diff + y_diff
        eucl_dist = np.sqrt(eucl_dist)

        return {"coordinate":np.array(surface_geom_np[0][eucl_dist.argmin()]),"index":eucl_dist.argmin()}

    def get_dist(self,pt1,pt2):
        # [lon1,lat1,lon2,lat2]
        geod = pyproj.Geod(ellps = "WGS84")
        
        lon_1,lat_1,_ = pt1
        lon_2,lat_2,_ = pt2
        forward, back, dist = geod.inv(lon_1,lat_1,lon_2,lat_2)
        # print ("forward: %f, back: %f, dist: %f"%(forward,back,dist))
        return {"dist":dist,"forward":forward,"backward":back}

    def get_slope_from_surface(self,surface_geom:np.array,perpen_line:np.array,nearest_vertice:np.array):
        """
        Getting slope value from elevation of the surface
            check shape of the surface_geom to make sure it is (1,n,3)
            n : number of vertices
            And, a nearest vertice is actually the vertice where is the closest distance to the obstacle.
            The shape of this is (3,) 
            perpencular line'shape will be (2,3)
        """
        elev_for_slope_cal = []
        
        if (perpen_line[:,2:].all() == nearest_vertice["coordinate"][2:])[0] == False:
            for i in range(surface_geom.shape[1]):
                # print(surface_geom[0,nearest_vertice["index"]+i,2:],nearest_vertice["coordinate"][2:])
                if (surface_geom[0,nearest_vertice["index"]+i:,2:] != nearest_vertice["coordinate"][2:])[0] == True:
                    elev_for_slope_cal = surface_geom[0,nearest_vertice["index"]+i,:]
                    break

        print(nearest_vertice["coordinate"],np.array(elev_for_slope_cal))
        dist = self.get_dist(nearest_vertice["coordinate"],np.array(elev_for_slope_cal))
    
        elevs = nearest_vertice["coordinate"][2:]-elev_for_slope_cal[2:]
        slopeSurface= elevs / dist["dist"]

        return slopeSurface[0]

    def WGStoUTM(self,point,airportInfo):
        epsgOri = pyproj.Proj(airportInfo["globalEPSG"])
        epsgTar = pyproj.Proj(airportInfo["localEPSG"])
        x,y = pyproj.transform(epsgOri,epsgTar,point[0],point[1])
        # print ("location in utm: %f, %f"%(x,y))
        return x,y

    def get_perpencular_dist(self,pt1,pt2,pt3, airportInfo):
        pt1_xy = self.WGStoUTM(pt1,airportInfo) #nearest perpen
        pt2_xy = self.WGStoUTM(pt2,airportInfo) #nearest vertice 
        pt3_xy = self.WGStoUTM(pt3,airportInfo) #obst
        
        d = np.cross(np.array(pt1_xy) - np.array(pt2_xy),np.array(pt3_xy) - np.array(pt1_xy))/np.linalg.norm(np.array(pt2_xy) - np.array(pt1_xy))
        
        return np.abs(d)
    
    def get_step(self,surface_coords):
        diffs = []
        for i in range(surface_coords.shape[0]-1):
            diffs.append(surface_coords[i] - surface_coords[i+1])
        min_arg = np.argmin(np.array(diffs))
        if diffs[min_arg+1][0] == 0.:
            print(surface_coords[min_arg:min_arg + 2])
        

        # return np.array(diffs)
    
    def get_perpencular_line_trans(self,surface:np.array,nearest_vertice:np.array):
        # all transitional surface
        # extract perpencular coordinates
        max_elev_index = np.argmax(surface[0,:,2:])
        extracted_position = surface[0,max_elev_index:max_elev_index +2,:]

        return extracted_position

    def get_perpencular_line(self,surface:np.array,nearest_vertice:np.array):
        #  get the vertices which are represented with the same elevation with neares_vertice.
        surface_temp = surface[0,:-1,:]
        # print(surface_temp[:,2:])
        surface_temp_diff = surface_temp[:,2:] - nearest_vertice[-1]
        
        # print(surface_temp_diff)
        
        sameElev = surface[0,:,-1] == nearest_vertice[-1]
        surfaceSameElev = surface[0,sameElev==True,:]

        # make sure the vertice is not the same coordinate
        surfaceSameElevNotPos = np.round_(surfaceSameElev[:,:2],decimals=8) != np.round_(nearest_vertice[:2],decimals=8)
        surfaceVerticeSameElevNotPos = np.round_(surfaceSameElev[:,:2][surfaceSameElevNotPos == True],decimals=8)
        # print(surface[0,:,:], nearest_vertice[:])
        surfaceVerticePerpenZ = []

        if surfaceVerticeSameElevNotPos.shape[0] == 4:
            surfaceVerticePerpen = list(surfaceVerticeSameElevNotPos)
            surfaceVerticePerpenZ.append([surfaceVerticePerpen[0],surfaceVerticePerpen[1],nearest_vertice[-1]])
        else:
            surfaceVerticePerpen = list(surfaceVerticeSameElevNotPos)
            surfaceVerticePerpenZ.append([surfaceVerticePerpen[0],surfaceVerticePerpen[1],nearest_vertice[-1]])
        # print(surfaceVerticePerpenZ[0])
        return np.array(surfaceVerticePerpenZ[0])


    def inner_horizontal(self,surface_geom,obst,obstAttrElev,airportInfo):
        """
            surface_geom: ogr.Geometry()
            obst: ogr.Geometry()
        """
        surface_geom_np = np.array(json.loads(surface_geom.ExportToJson())["coordinates"]) # should be (1,n,3)
        obst_geom_np = np.array(json.loads(obst.ExportToJson())["coordinates"]) # (3,)

        surface_elev = 0.0
        if surface_geom_np.shape[-1] == 4:
            surface_elev = surface_geom_np[0][0][0][-1]
        else:
            surface_elev = surface_geom_np[0][0][-1]
        
        nearest_vertice = self.get_nearest_vertice(surface_geom_np,obst_geom_np)
        allowance = self.check_height_allowance(nearest_vertice["coordinate"],0.0,0.0,obstAttrElev)
        return allowance
    
    def take_off_climb(self,surface_geom,obst,obstAttrElev,airportInfo):
        """
            surface_geom: ogr.Geometry()
            obst: ogr.Geometry()
        """
        surface_geom_np = np.array(json.loads(surface_geom.ExportToJson())["coordinates"]) # should be (1,n,3)
        obst_geom_np = np.array(json.loads(obst.ExportToJson())["coordinates"]) # (3,)

        # find the vertice that is close to the obstacle within the surface
        nearest_pt = self.get_nearest_vertice(surface_geom_np,obst_geom_np)
        perpenline = self.get_perpencular_line(surface_geom_np,nearest_pt["coordinate"])
        # print(nearest_pt)
        # print(perpenline)
        # print(np.array([nearest_pt["coordinate"],perpenline]))
        perpencular_dist = self.get_perpencular_dist(perpenline,nearest_pt["coordinate"],obst_geom_np,airportInfo)
        OLSSur = Surfaces(airportName=airportInfo["name"],AirportCode=airportInfo["ICAO"])
        codeNumber = OLSSur.getCodeNumber(airportInfo["rwyLength"])
        # print(perpencular_dist)
        approachTypeDim = ApproachType[self.findTHRName(airportInfo["THR"],"NPA")["approachType"]]
        slopeSurface = approachTypeDim["take_off_climb"][codeNumber]["slope"]/100.
        # slopeSurface = 1.46/100.
        check_perpen_elev = self.check_highest_elev_in_surface(surface_geom_np,perpenline)
        # print(check_perpen_elev)
        allowance = self.check_height_allowance(nearest_pt["coordinate"],check_perpen_elev * perpencular_dist,slopeSurface,obstAttrElev)
        return allowance
    
    def conical(self,surface_geom,obst,obstAttrElev,airportInfo):
        """
            surface_geom: ogr.Geometry()
            obst: ogr.Geometry()
        """
        surface_geom_np = np.array(json.loads(surface_geom.ExportToJson())["coordinates"]) # should be (1,n,3)
        obst_geom_np = np.array(json.loads(obst.ExportToJson())["coordinates"]) # (3,)

        # find the vertice that is close to the obstacle within the surface
        nearest_pt = self.get_nearest_vertice(surface_geom_np,obst_geom_np)
        perpenline = self.get_perpencular_line(surface_geom_np,nearest_pt["coordinate"])
        # print(nearest_pt)
        # print(perpenline)
        # print(np.array([nearest_pt["coordinate"],perpenline]))
        perpencular_dist = self.get_perpencular_dist(perpenline,nearest_pt["coordinate"],obst_geom_np,airportInfo)
        OLSSur = Surfaces(airportName=airportInfo["name"],AirportCode=airportInfo["ICAO"])
        codeNumber = OLSSur.getCodeNumber(airportInfo["rwyLength"])
        # print(perpencular_dist)
        approachTypeDim = ApproachType[self.findTHRName(airportInfo["THR"],"NPA")["approachType"]]
        slopeSurface = approachTypeDim["conical"][codeNumber]["slope"]/100.
        # slopeSurface = 1.46/100.
        check_perpen_elev = self.check_highest_elev_in_surface(surface_geom_np,perpenline)
        # print(check_perpen_elev)
        allowance = self.check_height_allowance(nearest_pt["coordinate"],check_perpen_elev * perpencular_dist,slopeSurface,obstAttrElev)
        return allowance

    def inner_approach(self,surface_geom,obst,obstAttrElev,airportInfo):
        """
            surface_geom: ogr.Geometry()
            obst: ogr.Geometry()
        """
        surface_geom_np = np.array(json.loads(surface_geom.ExportToJson())["coordinates"]) # should be (1,n,3)
        obst_geom_np = np.array(json.loads(obst.ExportToJson())["coordinates"]) # (3,)

        # find the vertice that is close to the obstacle within the surface
        nearest_pt = self.get_nearest_vertice(surface_geom_np,obst_geom_np)
        perpenline = self.get_perpencular_line(surface_geom_np,nearest_pt["coordinate"])
        # print(nearest_pt)
        # print(perpenline)
        # print(np.array([nearest_pt["coordinate"],perpenline]))
        perpencular_dist = self.get_perpencular_dist(perpenline,nearest_pt["coordinate"],obst_geom_np,airportInfo)
        OLSSur = Surfaces(airportName=airportInfo["name"],AirportCode=airportInfo["ICAO"])
        codeNumber = OLSSur.getCodeNumber(airportInfo["rwyLength"])
        # print(perpencular_dist)
        approachTypeDim = ApproachType[self.findTHRName(airportInfo["THR"],"PA_I")["approachType"]]
        slopeSurface = approachTypeDim["InnerApproach"][codeNumber]["slope"]/100.
        # slopeSurface = 1.46/100.
        check_perpen_elev = self.check_highest_elev_in_surface(surface_geom_np,perpenline)
        # print(check_perpen_elev)
        allowance = self.check_height_allowance(nearest_pt["coordinate"],check_perpen_elev * perpencular_dist,slopeSurface,obstAttrElev)

        return allowance


    def approach(self,surface_geom,obst,obstAttrElev,airportInfo):
        """
            surface_geom: ogr.Geometry()
            obst: ogr.Geometry()
        """
        surface_geom_np = np.array(json.loads(surface_geom.ExportToJson())["coordinates"]) # should be (1,n,3)
        obst_geom_np = np.array(json.loads(obst.ExportToJson())["coordinates"]) # (3,)

        # find the vertice that is close to the obstacle within the surface
        nearest_pt = self.get_nearest_vertice(surface_geom_np,obst_geom_np)
        perpenline = self.get_perpencular_line(surface_geom_np,nearest_pt["coordinate"])
        # print(nearest_pt)
        # print(perpenline)
        # print(np.array([nearest_pt["coordinate"],perpenline]))
        perpencular_dist = self.get_perpencular_dist(perpenline,nearest_pt["coordinate"],obst_geom_np,airportInfo)
        OLSSur = Surfaces(airportName=airportInfo["name"],AirportCode=airportInfo["ICAO"])
        codeNumber = OLSSur.getCodeNumber(airportInfo["rwyLength"])
        # print(perpencular_dist)
        approachTypeDim = ApproachType[self.findTHRName(airportInfo["THR"],"NPA")["approachType"]]
        slopeSurface = approachTypeDim["FirstSection"][codeNumber]["slope"]/100.
        # slopeSurface = 1.46/100.
        check_perpen_elev = self.check_highest_elev_in_surface(surface_geom_np,perpenline)
        # print(check_perpen_elev)
        allowance = self.check_height_allowance(nearest_pt["coordinate"],check_perpen_elev * perpencular_dist,slopeSurface,obstAttrElev)
        return allowance

    def check_highest_elev_in_surface(self,surface,perpenline):
        print(surface[0,:,2:].max())
        if perpenline[-1] == surface[0,:,2:].max():
            return -1
        else:
            return 1
    def first_section(self,surface_geom,obst,obstAttrElev,airportInfo):
        """
            surface_geom: ogr.Geometry()
            obst: ogr.Geometry()
        """
        surface_geom_np = np.array(json.loads(surface_geom.ExportToJson())["coordinates"]) # should be (1,n,3)
        obst_geom_np = np.array(json.loads(obst.ExportToJson())["coordinates"]) # (3,)

        # find the vertice that is close to the obstacle within the surface
        nearest_pt = self.get_nearest_vertice(surface_geom_np,obst_geom_np)
        perpenline = self.get_perpencular_line(surface_geom_np,nearest_pt["coordinate"])
        # print(nearest_pt)
        # print(perpenline)
        # print(np.array([nearest_pt["coordinate"],perpenline]))
        perpencular_dist = self.get_perpencular_dist(perpenline,nearest_pt["coordinate"],obst_geom_np,airportInfo)
        OLSSur = Surfaces(airportName=airportInfo["name"],AirportCode=airportInfo["ICAO"])
        codeNumber = OLSSur.getCodeNumber(airportInfo["rwyLength"])
        # print(perpencular_dist)
        approachTypeDim = ApproachType[self.findTHRName(airportInfo["THR"],"NPA")["approachType"]]
        slopeSurface = approachTypeDim["FirstSection"][codeNumber]["slope"]/100.
        # slopeSurface = 1.46/100.
        check_perpen_elev = self.check_highest_elev_in_surface(surface_geom_np,perpenline)
        # print(check_perpen_elev)
        allowance = self.check_height_allowance(nearest_pt["coordinate"],check_perpen_elev * perpencular_dist,slopeSurface,obstAttrElev)
        return allowance

    def second_section(self,surface_geom,obst,obstAttrElev,airportInfo):
        """
            surface_geom: ogr.Geometry()
            obst: ogr.Geometry()
        """
        surface_geom_np = np.array(json.loads(surface_geom.ExportToJson())["coordinates"]) # should be (1,n,3)
        obst_geom_np = np.array(json.loads(obst.ExportToJson())["coordinates"]) # (3,)

        # find the vertice that is close to the obstacle within the surface
        nearest_pt = self.get_nearest_vertice(surface_geom_np,obst_geom_np)
        perpenline = self.get_perpencular_line(surface_geom_np,nearest_pt["coordinate"])
        # print(nearest_pt)
        # print(perpenline)
        # print(np.array([nearest_pt["coordinate"],perpenline]))
        perpencular_dist = self.get_perpencular_dist(perpenline,nearest_pt["coordinate"],obst_geom_np,airportInfo)
        OLSSur = Surfaces(airportName=airportInfo["name"],AirportCode=airportInfo["ICAO"])
        codeNumber = OLSSur.getCodeNumber(airportInfo["rwyLength"])
        # print(perpencular_dist)
        approachTypeDim = ApproachType[self.findTHRName(airportInfo["THR"],"NPA")["approachType"]]
        slopeSurface = approachTypeDim["SecondSection"][codeNumber]["slope"]/100.
        # slopeSurface = 1.46/100.
        check_perpen_elev = self.check_highest_elev_in_surface(surface_geom_np,perpenline)
        # print(check_perpen_elev)
        allowance = self.check_height_allowance(nearest_pt["coordinate"],check_perpen_elev * perpencular_dist,slopeSurface,obstAttrElev)
        return allowance

    def horizontal_section(self,surface_geom,obst,obstAttrElev,airportInfo):
        """
            surface_geom: ogr.Geometry()
            obst: ogr.Geometry()
        """
        surface_geom_np = np.array(json.loads(surface_geom.ExportToJson())["coordinates"]) # should be (1,n,3)
        obst_geom_np = np.array(json.loads(obst.ExportToJson())["coordinates"]) # (3,)

        # find the vertice that is close to the obstacle within the surface
        nearest_pt = self.get_nearest_vertice(surface_geom_np,obst_geom_np)
        perpenline = self.get_perpencular_line(surface_geom_np,nearest_pt["coordinate"])
        # print(nearest_pt)
        # print(perpenline)
        # print(np.array([nearest_pt["coordinate"],perpenline]))
        perpencular_dist = self.get_perpencular_dist(perpenline,nearest_pt["coordinate"],obst_geom_np,airportInfo)
        OLSSur = Surfaces(airportName=airportInfo["name"],AirportCode=airportInfo["ICAO"])
        codeNumber = OLSSur.getCodeNumber(airportInfo["rwyLength"])
        # print(perpencular_dist)
        approachTypeDim = ApproachType[self.findTHRName(airportInfo["THR"],"NPA")["approachType"]]
        slopeSurface = approachTypeDim["HorizontalSection"][codeNumber]["slope"]/100.
        # slopeSurface = 1.46/100.
        check_perpen_elev = self.check_highest_elev_in_surface(surface_geom_np,perpenline)
        # print(check_perpen_elev)
        allowance = self.check_height_allowance(nearest_pt["coordinate"],check_perpen_elev * perpencular_dist,slopeSurface,obstAttrElev)
        return allowance

    def findTHRName(self,airportTHRs,condition):
        for i in airportTHRs:
            if airportTHRs[i]["approachType"] == condition:
                return airportTHRs[i]
                break

    def transitional(self,surface_geom,obst,obstAttrElev,airportInfo):
        """
            surface_geom: ogr.Geometry()
            obst: ogr.Geometry()
        """
        surface_geom_np = np.array(json.loads(surface_geom.ExportToJson())["coordinates"]) # should be (1,n,3)
        obst_geom_np = np.array(json.loads(obst.ExportToJson())["coordinates"]) # (3,)

        # find the vertice that is close to the obstacle within the surface
        nearest_pt = self.get_nearest_vertice(surface_geom_np,obst_geom_np)
        perpenline = self.get_perpencular_line_trans(surface_geom_np,nearest_pt["coordinate"])

        perpencular_dist = self.get_perpencular_dist(perpenline[0],perpenline[1],obst_geom_np,airportInfo)
        OLSSur = Surfaces(airportName=airportInfo["name"],AirportCode=airportInfo["ICAO"])
        codeNumber = OLSSur.getCodeNumber(airportInfo["rwyLength"])

        approachTypeDim = ApproachType[self.findTHRName(airportInfo["THR"],"NPA")["approachType"]]
        slopeSurface = approachTypeDim["Transitional"][codeNumber]["slope"]/100.
        check_perpen_elev = self.check_highest_elev_in_surface(surface_geom_np,perpenline[0])
        allowance = self.check_height_allowance(perpenline[0],check_perpen_elev*perpencular_dist,slopeSurface,obstAttrElev)
        return allowance

    def inner_transitional(self,surface_geom,obst,obstAttrElev,airportInfo):
        """
            surface_geom: ogr.Geometry()
            obst: ogr.Geometry()
        """
        surface_geom_np = np.array(json.loads(surface_geom.ExportToJson())["coordinates"]) # should be (1,n,3)
        obst_geom_np = np.array(json.loads(obst.ExportToJson())["coordinates"]) # (3,)

        # find the vertice that is close to the obstacle within the surface
        nearest_pt = self.get_nearest_vertice(surface_geom_np,obst_geom_np)
        perpenline = self.get_perpencular_line_trans(surface_geom_np,nearest_pt["coordinate"])

        perpencular_dist = self.get_perpencular_dist(perpenline[0],perpenline[1],obst_geom_np,airportInfo)
        OLSSur = Surfaces(airportName=airportInfo["name"],AirportCode=airportInfo["ICAO"])
        codeNumber = OLSSur.getCodeNumber(airportInfo["rwyLength"])

        approachTypeDim = ApproachType[self.findTHRName(airportInfo["THR"],"PA_I")["approachType"]]
        slopeSurface = approachTypeDim["InnerTransitional"][codeNumber]["slope"]/100.
        check_perpen_elev = self.check_highest_elev_in_surface(surface_geom_np,perpenline[0])
        allowance = self.check_height_allowance(perpenline[0],check_perpen_elev*perpencular_dist,slopeSurface,obstAttrElev)
        return allowance

    def inner_transitional2(self,surface_geom,obst,obstAttrElev,airportInfo):
        """
            surface_geom: ogr.Geometry()
            obst: ogr.Geometry()
        """
        surface_geom_np = np.array(json.loads(surface_geom.ExportToJson())["coordinates"]) # should be (1,n,3)
        obst_geom_np = np.array(json.loads(obst.ExportToJson())["coordinates"]) # (3,)
        print(surface_geom_np[:,:2,:])
        # find the vertice that is close to the obstacle within the surface
        perpenline = surface_geom_np[:,:2,:]
        nearest_pt = self.get_nearest_vertice(perpenline,obst_geom_np)
        # perpenline = self.get_perpencular_line_trans(surface_geom_np,nearest_pt["coordinate"])
        
        
        perpencular_dist = self.get_perpencular_dist(perpenline[0][0],perpenline[0][1],obst_geom_np,airportInfo)
        OLSSur = Surfaces(airportName=airportInfo["name"],AirportCode=airportInfo["ICAO"])
        codeNumber = OLSSur.getCodeNumber(airportInfo["rwyLength"])

        approachTypeDim = ApproachType[self.findTHRName(airportInfo["THR"],"PA_I")["approachType"]]
        slopeSurface = approachTypeDim["InnerTransitional"][codeNumber]["slope"]/100.
        check_perpen_elev = self.check_highest_elev_in_surface(surface_geom_np,perpenline[0][0])
        print(perpencular_dist)
        allowance = self.check_height_allowance(nearest_pt["coordinate"],perpencular_dist,slopeSurface,obstAttrElev)
        return allowance

    def inner_transitional3(self,surface_geom,obst,obstAttrElev,airportInfo):
        """
            surface_geom: ogr.Geometry()
            obst: ogr.Geometry()
        """
        surface_geom_np = np.array(json.loads(surface_geom.ExportToJson())["coordinates"]) # should be (1,n,3)
        obst_geom_np = np.array(json.loads(obst.ExportToJson())["coordinates"]) # (3,)
        print(surface_geom_np[:,:,:])
        # find the vertice that is close to the obstacle within the surface
        perpenline = surface_geom_np[:,-2:,:]
        nearest_pt = self.get_nearest_vertice(perpenline,obst_geom_np)
        # perpenline = self.get_perpencular_line_trans(surface_geom_np,nearest_pt["coordinate"])
        
        
        perpencular_dist = self.get_perpencular_dist(perpenline[0][0],perpenline[0][1],obst_geom_np,airportInfo)
        OLSSur = Surfaces(airportName=airportInfo["name"],AirportCode=airportInfo["ICAO"])
        codeNumber = OLSSur.getCodeNumber(airportInfo["rwyLength"])

        approachTypeDim = ApproachType[self.findTHRName(airportInfo["THR"],"PA_I")["approachType"]]
        slopeSurface = approachTypeDim["InnerTransitional"][codeNumber]["slope"]/100.
        check_perpen_elev = self.check_highest_elev_in_surface(surface_geom_np,perpenline[0][0])
        allowance = self.check_height_allowance(nearest_pt["coordinate"],perpencular_dist,slopeSurface,obstAttrElev)
        return allowance
    
    def balked_landing(self,surface_geom,obst,obstAttrElev,airportInfo):
        """
            surface_geom: ogr.Geometry()
            obst: ogr.Geometry()
        """
        surface_geom_np = np.array(json.loads(surface_geom.ExportToJson())["coordinates"]) # should be (1,n,3)
        obst_geom_np = np.array(json.loads(obst.ExportToJson())["coordinates"]) # (3,)

        # find the vertice that is close to the obstacle within the surface
        nearest_pt = self.get_nearest_vertice(surface_geom_np,obst_geom_np)
        perpenline = self.get_perpencular_line_trans(surface_geom_np,nearest_pt["coordinate"])

        perpencular_dist = self.get_perpencular_dist(perpenline[0],perpenline[1],obst_geom_np,airportInfo)
        OLSSur = Surfaces(airportName=airportInfo["name"],AirportCode=airportInfo["ICAO"])
        codeNumber = OLSSur.getCodeNumber(airportInfo["rwyLength"])

        approachTypeDim = ApproachType[self.findTHRName(airportInfo["THR"],"PA_I")["approachType"]]
        slopeSurface = approachTypeDim["BalkedLanding"][codeNumber]["slope"]/100.
        check_perpen_elev = self.check_highest_elev_in_surface(surface_geom_np,perpenline[0])
        allowance = self.check_height_allowance(perpenline[0],check_perpen_elev*perpencular_dist,slopeSurface,obstAttrElev)
        return allowance
