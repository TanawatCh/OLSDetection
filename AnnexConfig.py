"""
Distance is in metre
"""

AerodromeC= ['A','B','C','D','E','F']

Aerodrome_code_number = {
    1:[18,18,23,None,None,None],
    2:[23,23,30,None,None,None],
    3:[30,30,30,45,None,None],
    4:[None,None,45,45,45,60]
}
LenOfRWYStrip = {
    1:{'NIA':30,'NPA':60,'PA_I':60,'PA_II':60,'PA_III':60},
    2:{'NIA':30,'NPA':60,'PA_I':60,'PA_II':60,'PA_III':60},
    3:{'NIA':30,'NPA':60,'PA_I':60,'PA_II':60,'PA_III':60},
    4:{'NIA':30,'NPA':60,'PA_I':60,'PA_II':60,'PA_III':60},
}
# Length of runway strips according to runway code number and runway types
WidthOfRWYStrip = {
    1: {'NIA':30,'NPA':75,'PA_I':75,'PA_II':75,'PAIII':75},
    2: {'NIA':40,'NPA':75,'PA_I':75,'PA_II':75,'PAIII':75},
    # 3: {'NIA':75,'NPA':150,'PA_I':150,'PA_II':150,'PAIII':150},
    # 4: {'NIA':75,'NPA':150,'PA_I':150,'PA_II':150,'PAIII':150}
    3: {'NIA':70,'NPA':140,'PA_I':140,'PA_II':140,'PAIII':140},
    4: {'NIA':70,'NPA':140,'PA_I':140,'PA_II':140,'PAIII':140}
}
# Dimension and slope of the surfaces
OLSForNonInstApp = {
    "take_off_climb":{
        1: {'lenOfInnerEdge':60,'DistFromRWYEnd':30,'Divergence':10,'FinalWidth':380,'Len':1600,'slope':5},
        2: {'lenOfInnerEdge':80,'DistFromRWYEnd':60,'Divergence':10,'FinalWidth':580,'Len':2500,'slope':4},
        3: {'lenOfInnerEdge':180,'DistFromRWYEnd':60,'Divergence':12.5,'FinalWidth':1200,'Len':15000,'slope':2},
        4: {'lenOfInnerEdge':180,'DistFromRWYEnd':60,'Divergence':12.5,'FinalWidth':1200,'Len':15000,'slope':2}
    },
    "conical":{
        1:{'slope':5,"height":35},
        2:{'slope':5,"height":55},
        3:{'slope':5,"height":75},
        4:{'slope':5,"height":100}
    },
    "InnerHorizontal":{
        1:{'height':45,"radius":2000},
        2:{'height':45,"radius":2500},
        3:{'height':45,"radius":4000},
        4:{'height':45,"radius":4000},
    },
    "Approach":{
        1:{'lenOfInneredge':60,"DistFromTHR":30,"Divergence":10},
        2:{'lenOfInneredge':60,"DistFromTHR":30,"Divergence":10},
        3:{'lenOfInneredge':60,"DistFromTHR":30,"Divergence":10},
        4:{'lenOfInneredge':60,"DistFromTHR":30,"Divergence":10},
    },
    "FirstSection":{
        1:{'len':1600,'slope':5},
        2:{'len':2500,'slope':4},
        3:{'len':3000,'slope':3.33},
        4:{'len':3000,'slope':2.5}
    },
    "Transitional":{
        1:{"slope":20},
        2:{"slope":20},
        3:{"slope":14.3},
        4:{"slope":14.3}
    }
}
OLSForNonPrecisionApp = {
    "take_off_climb":{
        1: {'lenOfInnerEdge':60,'DistFromRWYEnd':30,'Divergence':10,'FinalWidth':380,'Len':1600,'slope':5},
        2: {'lenOfInnerEdge':80,'DistFromRWYEnd':60,'Divergence':10,'FinalWidth':580,'Len':2500,'slope':4},
        3: {'lenOfInnerEdge':180,'DistFromRWYEnd':60,'Divergence':12.5,'FinalWidth':1200,'Len':15000,'slope':2},
        4: {'lenOfInnerEdge':180,'DistFromRWYEnd':60,'Divergence':12.5,'FinalWidth':1200,'Len':15000,'slope':2}
    },
    "conical":{
        1:{'slope':5,"height":60},
        2:{'slope':5,"height":60},
        3:{'slope':5,"height":75},
        4:{'slope':5,"height":100}
    },
    "InnerHorizontal":{
        1:{'height':45,"radius":3500},
        2:{'height':45,"radius":3500},
        3:{'height':45,"radius":4000},
        4:{'height':45,"radius":4000},
    },
    "Approach":{
        1:{'lenOfInneredge':150,"DistFromTHR":60,"Divergence":15},
        2:{'lenOfInneredge':150,"DistFromTHR":60,"Divergence":15},
        # 3:{'lenOfInneredge':300,"DistFromTHR":60,"Divergence":15},
        # 4:{'lenOfInneredge':300,"DistFromTHR":60,"Divergence":15},
        3:{'lenOfInneredge':280,"DistFromTHR":60,"Divergence":15},
        4:{'lenOfInneredge':280,"DistFromTHR":60,"Divergence":15},
    },
    "FirstSection":{
        1:{'len':2500,'slope':3.33},
        2:{'len':2500,'slope':3.33},
        3:{'len':3000,'slope':2},
        4:{'len':3000,'slope':2}
    },
    "SecondSection":{
        3:{'len':3600,'slope':2.5},
        4:{'len':3600,'slope':2.5}
    },
    "HorizontalSection":{
        3:{'len':8400,'TotalLen':15000,"slope":0},
        4:{'len':8400,'TotalLen':15000,"slope":0}
    },
    "Transitional":{
        1:{"slope":20},
        2:{"slope":20},
        3:{"slope":14.3},
        4:{"slope":14.3}
    }
}

OLSForPrecisionAppCate_I = {
    "take_off_climb":{
        1: {'lenOfInnerEdge':60,'DistFromRWYEnd':30,'Divergence':10,'FinalWidth':380,'Len':1600,'slope':5},
        2: {'lenOfInnerEdge':80,'DistFromRWYEnd':60,'Divergence':10,'FinalWidth':580,'Len':2500,'slope':4},
        3: {'lenOfInnerEdge':180,'DistFromRWYEnd':60,'Divergence':12.5,'FinalWidth':1200,'Len':15000,'slope':2},
        4: {'lenOfInnerEdge':180,'DistFromRWYEnd':60,'Divergence':12.5,'FinalWidth':1200,'Len':15000,'slope':2}
    },
    "conical":{
        1:{'slope':5,"height":60},
        2:{'slope':5,"height":60},
        3:{'slope':5,"height":100},
        4:{'slope':5,"height":100}
    },
    "InnerHorizontal":{
        1:{'height':45,"radius":3500},
        2:{'height':45,"radius":3500},
        3:{'height':45,"radius":4000},
        4:{'height':45,"radius":4000},
    },
    "InnerApproach":{
        1:{"width":90,"DistFromTHR":60,"Len":900,"slope":2.5},
        2:{"width":90,"DistFromTHR":60,"Len":900,"slope":2.5},
        3:{"width":120,"DistFromTHR":60,"Len":900,"slope":2},
        4:{"width":120,"DistFromTHR":60,"Len":900,"slope":2}
    },
    "Approach":{
        1:{'lenOfInneredge':150,"DistFromTHR":60,"Divergence":15},
        2:{'lenOfInneredge':150,"DistFromTHR":60,"Divergence":15},
        3:{'lenOfInneredge':300,"DistFromTHR":60,"Divergence":15},
        4:{'lenOfInneredge':300,"DistFromTHR":60,"Divergence":15},
    },
    "FirstSection":{
        1:{'len':3000,'slope':2.5},
        2:{'len':3000,'slope':2.5},
        3:{'len':3000,'slope':2},
        4:{'len':3000,'slope':2}
    },
    "SecondSection":{
        1:{'len':12000,'slope':3},
        2:{'len':12000,'slope':3},
        3:{'len':3600,'slope':2.5},
        4:{'len':3600,'slope':2.5}
    },
    "HorizontalSection":{
        1:{'len':None,'TotalLen':15000},
        2:{'len':None,'TotalLen':15000},
        3:{'len':8400,'TotalLen':15000},
        4:{'len':8400,'TotalLen':15000}
    },
    "Transitional":{
        1:{"slope":14.3},
        2:{"slope":14.3},
        3:{"slope":14.3},
        4:{"slope":14.3}
    },
    "InnerTransitional":{
        1:{"slope":40},
        2:{'slope':40},
        3:{'slope':33.3},
        4:{'slope':33.3}
    },
    "BalkedLanding":{
        1:{"LenOfInnerEdge":90,"DistFromTHR":"Distance to the end of strip","Divergence":10,"slope":4},
        2:{"LenOfInnerEdge":90,"DistFromTHR":"Distance to the end of strip","Divergence":10,"slope":4},
        3:{"LenOfInnerEdge":120,"DistFromTHR":1800,"Divergence":10,"slope":3.33},
        4:{"LenOfInnerEdge":120,"DistFromTHR":1800,"Divergence":10,"slope":3.33},
    }
}

OLSForPrecisionAppCate_IIAndIII = {
    "take_off_climb":{
        3: {'lenOfInnerEdge':180,'DistFromRWYEnd':60,'Divergence':12.5,'FinalWidth':1200,'Len':15000,'slope':2},
        4: {'lenOfInnerEdge':180,'DistFromRWYEnd':60,'Divergence':12.5,'FinalWidth':1200,'Len':15000,'slope':2}
    },
    "conical":{
        3:{'slope':5,"height":100},
        4:{'slope':5,"height":100}
    },
    "InnerHorizontal":{
        3:{'height':45,"radius":4000},
        4:{'height':45,"radius":4000},
    },
    "InnerApproach":{
        3:{"width":120,"DistFromTHR":60,"Len":900,"slope":2},
        4:{"width":120,"DistFromTHR":60,"Len":900,"slope":2}
    },
    "Approach":{
        3:{'lenOfInneredge':300,"DistFromTHR":60,"Divergence":15},
        4:{'lenOfInneredge':300,"DistFromTHR":60,"Divergence":15},
    },
    "FirstSection":{
        3:{'len':3000,'slope':2},
        4:{'len':3000,'slope':2}
    },
    "SecondSection":{
        3:{'len':3600,'slope':2.5},
        4:{'len':3600,'slope':2.5}
    },
    "HorizontalSection":{
        3:{'len':8400,'TotalLen':15000},
        4:{'len':8400,'TotalLen':15000}
    },
    "Transitional":{
        3:{"slope":14.3},
        4:{"slope":14.3}
    },
    "InnerTransitional":{
        3:{'slope':33.3},
        4:{'slope':33.3}
    },
    "BalkedLanding":{
        3:{"LenOfInnerEdge":120,"DistFromTHR":1800,"Divergence":10,"slope":3.33},
        4:{"LenOfInnerEdge":120,"DistFromTHR":1800,"Divergence":10,"slope":3.33},
    }
}
ApproachType = {
    "NIA":OLSForNonInstApp,
    "NPA":OLSForNonPrecisionApp,
    "PA_I":OLSForPrecisionAppCate_I,
    "PA_II&III":OLSForPrecisionAppCate_IIAndIII
}

"""
Instead of using name of the surface, we encode it as integer
    0: take_off_climb
    1: conical
    2: inner horizontal
    3: approach
    4: first section
    5: second section
    6: transitional
    7: inner approach
    8: horizontal section
    9: inner transitional
    10: balked landing
"""
surface_code = {
    0:{
    "name":"Take-off Climb Surface",
    "dict":"take_off_climb"
    },
    1:{
    "name":"Conical Surface",
    "dict":"conical"
    },
    2:{
    "name":"Inner Horizontal Surface",
    "dict":"InnerHorizontal"
    },
    3:{
    "name":"Approach Surface",
    "dict":"Approach"
    },
    4:{
    "name":"First Section",
    "dict":"FirstSection"
    },
    5:{
    "name":"Second Section",
    "dict":"SecondSection"
    },
    6:{
    "name":"Transitional Surface",
    "dict":"Transitional"
    },
    7:{
    "name":"Inner Approach Surface",
    "dict":"InnerApproach"
    },
    8:{
    "name":"Horizontal Section",
    "dict":"HorizontalSection"
    },
    9:{
    "name":"Inner Transitional Surface",
    "dict":"InnerTransitional"
    },
    10:{
    "name":"Balked Landing Surface",
    "dict":"BalkedLanding"
    }    
}