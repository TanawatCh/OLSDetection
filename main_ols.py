from OLSAnalysis import *
from BAGsConfig import *
from AnnexConfig import *
import pandas as pd
import numpy as np
import json
from osgeo import ogr,gdal
import time
OD = ObstacleDetection()

def get_within(surfaceGeom, surfaceAttr,obstGeom,obstAttr,airportInfo):
    # print(obstGeom.Within(surfaceGeom))
    if obstGeom.Within(surfaceGeom) == True:
        if surfaceAttr["surf_code"] == 0:
            allowance = OD.take_off_climb(surfaceGeom,obstGeom,obstAttr,airportInfo)
            return allowance
        elif surfaceAttr["surf_code"] == 1:
            allowance = OD.conical(surfaceGeom,obstGeom,obstAttr,airportInfo)
            return allowance
        elif surfaceAttr["surf_code"] == 2:
            allowance = OD.inner_horizontal(surfaceGeom,obstGeom,obstAttr,airportInfo)
            return allowance
        elif surfaceAttr["surf_code"] == 3:
            allowance = OD.approach(surfaceGeom,obstGeom,obstAttr,airportInfo)
            return allowance
        elif surfaceAttr["surf_code"] == 4:
            allowance = OD.first_section(surfaceGeom,obstGeom,obstAttr,airportInfo)
            return allowance
        elif surfaceAttr["surf_code"] == 5:
            allowance = OD.second_section(surfaceGeom,obstGeom,obstAttr,airportInfo)
            return allowance
        elif surfaceAttr["surf_code"] == 6:
            allowance = OD.transitional(surfaceGeom,obstGeom,obstAttr,airportInfo)
            return allowance
        elif surfaceAttr["surf_code"] == 7:
            allowance = OD.inner_approach(surfaceGeom,obstGeom,obstAttr,airportInfo)
            return allowance
        elif surfaceAttr["surf_code"] == 8:
            allowance = OD.horizontal_section(surfaceGeom,obstGeom,obstAttr,airportInfo)
            return allowance
        elif surfaceAttr["surf_code"] == 9:
            if  "2" in surfaceAttr["surface_name"]:
                allowance = OD.inner_transitional2(surfaceGeom,obstGeom,obstAttr,airportInfo)
                return allowance
            elif "3" in surfaceAttr["surface_name"]:
                allowance = OD.inner_transitional3(surfaceGeom,obstGeom,obstAttr,airportInfo)
                return allowance
            else:
                allowance = OD.inner_transitional(surfaceGeom,obstGeom,obstAttr,airportInfo)
                return allowance
        elif surfaceAttr["surf_code"] == 10:
            allowance = OD.balked_landing(surfaceGeom,obstGeom,obstAttr,airportInfo)
            return allowance
        else:
            print(f"[WARINING] out of our condition {surfaceAttr['surf_code']}")
    else:
        return {"overtake":0.0, "allowance":True}

def detect(surfaces,obstGeom,obstAttr,airportInfo):
    detected_result = {
        "IDNumber":[],
        "lat":[],
        "lon":[],
        "Elevation":[],
        "Type":[],
        "Geometry":[],
        "overtake":[],
        "allowance":[],
        "surface":[]
    }

    for surf in surfaces:
        # surface_geom = ogr.CreateGeometryFromWkt(surf.GetGeometryRef().ExportToWkt())
        surface_geom = ogr.CreateGeometryFromJson(json.dumps(surf["geometry"]))
        for i in range(len(obstGeom)):
            print( surf["properties"]["surface_name"])
            print(obstAttr["IDNumber"][i])
            # print(surf["geometry"]["coordinates"])
            allowance = get_within(surface_geom,surf["properties"],obstGeom[i],obstAttr["Elevation"][i],airportInfo)
            if allowance["allowance"] == False:
                detected_result["IDNumber"].append(obstAttr["IDNumber"][i])
                detected_result["lat"].append(obstAttr["Lat"][i])
                detected_result["lon"].append(obstAttr["Lon"][i]) 
                detected_result["Elevation"].append(obstAttr["Elevation"][i])
                detected_result["Type"].append(obstAttr["Type"][i])
                detected_result["Geometry"].append(obstAttr["geometry"][i])
                detected_result["overtake"].append(allowance["overtake"])
                detected_result["allowance"].append(allowance["allowance"])
                detected_result["surface"].append(surface_code[surf["properties"]["surf_code"]]["name"])

    return detected_result

def get_candidate_obst(obst_geom_np:np.array,geom_typ:str):

    if geom_typ == "Polygon":
        if len(obst_geom_np.shape) == 4:
            # multi parts
            return obst_geom_np[0][0][0]
        else:
            return obst_geom_np[0][0]
        pass
    else:
        return obst_geom_np[0]

def export_csv(fname,csv_data):
    df = pd.DataFrame(csv_data)
    df.to_csv(fname)
    print("Export Done.")

def obst_prenatrated(detected_result):
    obst_above_surface = np.array(detected_result["IDNumber"]).any(np.array(detected_result["penetrated"]) == False)

def test(airportICAO:str="VTBO"):
    st = time.time()
    airportInfo = OD.intiAirportParams(airportICAO)
    print("[INFO] Data Loading..")
    obstMerged = OD.load_data_from_folder(surfaceDir["Obstacle"]+airportICAO+"/",airportICAO,".shp")
    surfaces = OD.load_data_from_folder(surfaceDir["OLS"],airportICAO,".geojson")
    
    obstAttr = {
        "IDNumber":[],
        "Lat":[],
        "Lon":[],
        "Elevation":[],
        "verAcc":[],
        "Type":[],
        "geometry":[],
        "geom":[]       
    }
    PointGeom = []
    for obst in obstMerged:
        if obst["geometry"]["type"] == "Polygon":
            point = ogr.Geometry(ogr.wkbPoint)
            verticesElev = get_candidate_obst(np.array(obst["geometry"]["coordinates"]),obst["geometry"]["type"])
            point.AddPoint(verticesElev[0],verticesElev[1])
            PointGeom.append(point)

            obstAttr["IDNumber"].append(obst["properties"]["IDNumber"])
            obstAttr["Lat"].append(verticesElev[1])
            obstAttr["Lon"].append(verticesElev[0])
            obstAttr["Elevation"].append(obst["properties"]["Elev"])
            obstAttr["Type"].append(obst["properties"]["Type"])
            obstAttr["verAcc"].append(obst["properties"]["vacc"])
            obstAttr["geometry"].append("Polygon")
            obstAttr["geom"].append(point.AddPoint(verticesElev[0],verticesElev[1],obst["properties"]["Elev"]))
        elif obst["geometry"]["type"] == "LineString":

            point = ogr.Geometry(ogr.wkbPoint)
            verticesElev = get_candidate_obst(np.array(obst["geometry"]["coordinates"]),obst["geometry"]["type"])
            point.AddPoint(verticesElev[0],verticesElev[1])
            PointGeom.append(point)

            obstAttr["IDNumber"].append(obst["properties"]["IDNumber"])
            obstAttr["Lat"].append(verticesElev[1])
            obstAttr["Lon"].append(verticesElev[0])
            obstAttr["Elevation"].append(obst["properties"]["Elev"])
            obstAttr["Type"].append(obst["properties"]["Type"])
            obstAttr["verAcc"].append(obst["properties"]["vacc"])
            obstAttr["geometry"].append("Line")
            obstAttr["geom"].append(point.AddPoint(verticesElev[0],verticesElev[1],obst["properties"]["Elev"]))      
        else:
            point = ogr.Geometry(ogr.wkbPoint)
            # print(obst)
            point.AddPoint(obst["geometry"]["coordinates"][0],obst["geometry"]["coordinates"][1])
            PointGeom.append(point)

            obstAttr["IDNumber"].append(obst["properties"]["IDNumber"])
            obstAttr["Lat"].append(obst["geometry"]["coordinates"][1])
            obstAttr["Lon"].append(obst["geometry"]["coordinates"][0])
            obstAttr["Elevation"].append(obst["properties"]["Elev"])
            obstAttr["Type"].append(obst["properties"]["Type"])
            obstAttr["verAcc"].append(obst["properties"]["vacc"])
            obstAttr["geometry"].append("Point")
            obstAttr["geom"].append(point.AddPoint(obst["geometry"]["coordinates"][0],obst["geometry"]["coordinates"][1],obst["properties"]["Elev"]))
    
    # export_csv("VTBO_Obstacle_candidate_from_code.csv",obstAttr)
    print("[INFO] Detecting...")
    detected_result = detect(surfaces,PointGeom,obstAttr,airportInfo)
    return detected_result
    # obst_prenatrated(detected_result)
    # export_csv("VTPO_OLS_analysis_test.csv",detected_result)
    # ed = time.time()
    # print(f"execution time: {ed - st} seconds" )

test(airportICAO="VTPO")
