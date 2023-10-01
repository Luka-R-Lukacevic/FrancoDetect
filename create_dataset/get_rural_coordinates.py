import os
import math
import geopandas as gpd
from shapely.geometry import Point
import shutil
import osmnx as ox
import ast
import zipfile
from geopy.geocoders import Nominatim

# Initialize Nominatim API
geolocator = Nominatim(user_agent="MyApp")

def utmToLatLng(easting, northing, zone=2, northernHemisphere=True):
    if not northernHemisphere:
        northing = 10000000 - northing

    a = 6378137
    e = 0.081819191
    e1sq = 0.006739497
    k0 = 0.9996

    arc = northing / k0
    mu = arc / (a * (1 - math.pow(e, 2) / 4.0 - 3 * math.pow(e, 4) / 64.0 - 5 * math.pow(e, 6) / 256.0))

    ei = (1 - math.pow((1 - e * e), (1 / 2.0))) / (1 + math.pow((1 - e * e), (1 / 2.0)))

    ca = 3 * ei / 2 - 27 * math.pow(ei, 3) / 32.0

    cb = 21 * math.pow(ei, 2) / 16 - 55 * math.pow(ei, 4) / 32
    cc = 151 * math.pow(ei, 3) / 96
    cd = 1097 * math.pow(ei, 4) / 512
    phi1 = mu + ca * math.sin(2 * mu) + cb * math.sin(4 * mu) + cc * math.sin(6 * mu) + cd * math.sin(8 * mu)

    n0 = a / math.pow((1 - math.pow((e * math.sin(phi1)), 2)), (1 / 2.0))

    r0 = a * (1 - e * e) / math.pow((1 - math.pow((e * math.sin(phi1)), 2)), (3 / 2.0))
    fact1 = n0 * math.tan(phi1) / r0

    _a1 = 500000 - easting
    dd0 = _a1 / (n0 * k0)
    fact2 = dd0 * dd0 / 2

    t0 = math.pow(math.tan(phi1), 2)
    Q0 = e1sq * math.pow(math.cos(phi1), 2)
    fact3 = (5 + 3 * t0 + 10 * Q0 - 4 * Q0 * Q0 - 9 * e1sq) * math.pow(dd0, 4) / 24

    fact4 = (61 + 90 * t0 + 298 * Q0 + 45 * t0 * t0 - 252 * e1sq - 3 * Q0 * Q0) * math.pow(dd0, 6) / 720

    lof1 = _a1 / (n0 * k0)
    lof2 = (1 + 2 * t0 + Q0) * math.pow(dd0, 3) / 6.0
    lof3 = (5 - 2 * Q0 + 28 * t0 - 3 * math.pow(Q0, 2) + 8 * e1sq + 24 * math.pow(t0, 2)) * math.pow(dd0, 5) / 120
    _a2 = (lof1 - lof2 + lof3) / math.cos(phi1)
    _a3 = _a2 * 180 / math.pi

    latitude = 180 * (phi1 - fact1 * (fact2 + fact3 + fact4)) / math.pi

    if not northernHemisphere:
        latitude = -latitude

    longitude = ((zone > 0) and (6 * zone - 183.0) or 3.0) - _a3

    return (latitude,180+longitude)

departments = [['Nord',
  5743,
  ['Lille', 'Roubaix', 'Tourcoing', 'Dunkirk', "Villeneuve-d'Ascq"],
  0],
 ['Bouches-du-Rhône', 5087, ['Marseille', 'Aix-en-Provence'], 1],
 ['Rhône', 3249, ['Lyon', 'Villeurbanne', 'Vénissieux'], 1],
 ['Seine-Saint-Denis',
  236,
  ['Saint-Denis',
   'Montreuil',
   'Aubervilliers',
   'Aulnay-sous-Bois',
   'Drancy',
   'Noisy-le-Grand',
   'Pantin',
   'Le Blanc-Mesnil'],
  0],
 ['Hauts-de-Seine',
  176,
  ['Boulogne-Billancourt',
   'Nanterre',
   'Asnières-sur-Seine',
   'Colombes',
   'Courbevoie',
   'Rueil-Malmaison',
   'Issy-les-Moulineaux',
   'Levallois-Perret',
   'Clichy',
   'Antony',
   'Neuilly-sur-Seine'],
  0],
 ['Gironde', 10726, ['Bordeaux', 'Mérignac', 'Pessac'], -1],
 ['Pas-de-Calais', 6671, ['Calais'], 0],
 ['Yvelines', 2284, ['Versailles'], 0],
 ['Loire-Atlantique', 6815, ['Nantes', 'Saint-Nazaire'], -1],
 ['Seine-et-Marne', 5915, ['Meaux', 'Chelles'], 0],
 ['Val-de-Marne',
  245,
  ['Vitry-sur-Seine',
   'Créteil',
   'Champigny-sur-Marne',
   'Saint-Maur-des-Fossés',
   'Ivry-sur-Seine',
   'Maisons-Alfort',
   'Villejuif'],
  0],
 ['Haute-Garonne', 6309, ['Toulouse'], 0],
 ['Essonne', 1804, ['Évry-Courcouronnes'], 0],
 ['Isère', 7431, ['Grenoble'], 1],
 ['Seine-Maritime', 6278, ['Le Havre', 'Rouen'], 0],
 ["Val-d'Oise", 1246, ['Argenteuil', 'Cergy', 'Sarcelles'], 0],
 ['Hérault', 6101, ['Montpellier', 'Béziers'], 0],
 ['Bas-Rhin', 4755, ['Strasbourg'], 2],
 ['Alpes-Maritimes', 4299, ['Nice', 'Cannes', 'Antibes'], 2],
 ['Ille-et-Vilaine', 6775, ['Rennes'], -2],
 ['Var', 5973, ['Toulon', 'La Seyne-sur-Mer', 'Hyères'], 1],
 ['Moselle', 6216, ['Metz'], 1],
 ['Finistère', 6733, ['Brest', 'Quimper'], -2],
 ['Oise', 5860, ['Beauvais'], 0],
 ['Haute-Savoie', 4388, ['Annecy'], 1],
 ['Maine-et-Loire', 7166, ['Angers'], -1],
 ['Haut-Rhin', 3525, ['Mulhouse', 'Colmar'], 2],
 ['Loire', 4781, ['Saint-Étienne'], 0],
 ['Morbihan', 6823, ['Lorient'], -2],
 ['Gard', 5853, ['Nîmes'], 0],
 ['Meurthe-et-Moselle', 5246, ['Nancy'], 1],
 ['Calvados', 5548, ['Caen'], -1],
 ['Vendée', 6720, ['La Roche-sur-Yon'], -1],
 ['Pyrénées-Atlantiques', 7645, ['Pau'], -1],
 ['Loiret', 6776, ['Orléans'], 0],
 ['Puy-de-Dôme', 7970, ['Clermont-Ferrand'], 0],
 ['Ain', 5762, [], 1],
 ['Charente-Maritime', 6864, ['La Rochelle'], -1],
 ['Indre-et-Loire', 6127, ['Tours'], -1],
 ["Côtes-d'Armor", 6878, [], -2],
 ['Eure', 6040, [], 0],
 ['Somme', 6170, ['Amiens'], 0],
 ['Marne', 8162, ['Reims'], 0],
 ['Sarthe', 6206, ['Le Mans'], -1],
 ['Vaucluse', 3567, ['Avignon'], 1],
 ['Saône-et-Loire', 8575, [], 0],
 ['Doubs', 5232, ['Besançon'], 1],
 ["Côte-d'Or", 8763, ['Dijon'], 1],
 ['Aisne', 7369, [], 0],
 ['Drôme', 6530, ['Valence'], 1],
 ['Manche', 5938, ['Cherbourg-en-Cotentin'], -1],
 ['Pyrénées-Orientales', 4116, ['Perpignan'], 0],
 ['Vienne', 6990, ['Poitiers'], -1],
 ['Savoie', 6028, ['Chambéry'], 1],
 ['Eure-et-Loir', 5880, [], 0],
 ['Landes', 9243, [], -1],
 ['Dordogne', 9060, [], -1],
 ['Tarn', 5758, [], 0],
 ['Deux-Sèvres', 5999, ['Niort'], -1],
 ['Aude', 6139, ['Narbonne'], 0],
 ['Haute-Vienne', 5520, ['Limoges'], -1],
 ['Vosges', 5874, [], 1],
 ['Charente', 5956, [], -1],
 ['Allier', 7340, [], 0],
 ['Yonne', 7427, [], 0],
 ['Lot-et-Garonne', 5361, [], -1],
 ['Loir-et-Cher', 6343, [], 0],
 ['Ardèche', 5529, [], 0],
 ['Aube', 6004, ['Troyes'], 0],
 ['Mayenne', 5175, [], -1],
 ['Cher', 7235, ['Bourges'], 0],
 ['Orne', 6103, [], -1],
 ['Aveyron', 8735, [], 0],
 ['Ardennes', 5229, [], 0],
 ['Tarn-et-Garonne', 3717, ['Montauban'], 0],
 ['Jura', 4999, [], 1],
 ['Corrèze', 5857, [], 0],
 ['Haute-Saône', 5360, [], 1],
 ['Hautes-Pyrénées', 4464, [], -1],
 ['Haute-Loire', 4977, [], 0],
 ['Indre', 6790, [], 0],
 ['Nièvre', 6817, [], 0],
 ['Gers', 6257, [], -1],
 ['Meuse', 6216, [], 1],
 ['Haute-Corse', 4666, [], 2],
 ['Lot', 5217, [], 0],
 ['Haute-Marne', 6211, [], 1],
 ['Alpes-de-Haute-Provence', 6925, [], 1],
 ['Corse-du-Sud', 4014, ['Ajaccio'], 2],
 ['Ariège', 4890, [], 0],
 ['Cantal', 5726, [], 0],
 ['Territoire de Belfort', 609, [], 2],
 ['Hautes-Alpes', 134205, [], 1],
 ['Creuse', 5565, [], 0],
 ['Lozère', 5167, [], 0]]


summe=0
for liste in departments:
    summe+=liste[1]
    
anz=10000
for liste in departments:
    ruralpop = liste[1]
    number = math.floor(ruralpop*anz/summe)
    dep = liste[0] + ", France"
    G = ox.graph_from_place(dep, network_type='all')
    Gp = ox.project_graph(G)
    
    home_departments_path = os.path.expanduser("/home/janek/Documents/Departments")
    new_directory_name = liste[0]
    new_directory_path = os.path.join(home_departments_path, new_directory_name)
    os.makedirs(new_directory_path)
    file_path = "/home/janek/Documents/Departments/" + liste[0] + "/" + liste[0] + ".txt"
    
    graphen = []
    boundaries = []
    for town in liste[2]:
        city = town + ", France"
        #city_graph = ox.graph_from_place(city, network_type='all')
        city_boundary = ox.geocode_to_gdf(city)
        #graphen.append(city_graph)
        boundaries.append(city_boundary)
    print(len(boundaries))
    file_content = ""
    while number != 0:
        print(number)
        points = ox.utils_geo.sample_points(ox.get_undirected(Gp), number)
        if liste[3]==-2:                                                               # wichtig für die Umrechnung von utm-Koordinaten in Längen- und Breitengrade
            for point in points:
                x, y = utmToLatLng(point.x, point.y, zone=1, northernHemisphere=True)
                y = y-6
                check = Point(y, x)
                wahr = True
                for i in range(len(boundaries)):
                    is_inside = gpd.sjoin(gpd.GeoDataFrame({'geometry': [check]}), boundaries[i], op='within')
                    if not is_inside.empty:
                        wahr=False
                if wahr: 
                    file_content = file_content + "(" + str(x) + ", " + str(y) + ")" + "\n"                
                    number-=1
        if liste[3]==-1:                                                         
            for point in points:
                x, y = utmToLatLng(point.x, point.y, zone=1, northernHemisphere=True)
                if y>3: y = y-6
                check = Point(y, x)
                wahr = True
                for i in range(len(boundaries)):
                    is_inside = gpd.sjoin(gpd.GeoDataFrame({'geometry': [check]}), boundaries[i], op='within')
                    if not is_inside.empty:
                        wahr=False
                if wahr: 
                    file_content = file_content + "(" + str(x) + ", " + str(y) + ")" + "\n"                
                    number-=1
        if liste[3]==0:
            for point in points:
                x, y = utmToLatLng(point.x, point.y, zone=1, northernHemisphere=True)
                check = Point(y, x)
                wahr = True
                for i in range(len(boundaries)):
                    is_inside = gpd.sjoin(gpd.GeoDataFrame({'geometry': [check]}), boundaries[i], op='within')
                    if not is_inside.empty:
                        wahr=False
                if wahr: 
                    file_content = file_content + "(" + str(x) + ", " + str(y) + ")" + "\n"                
                    number-=1
        if liste[3]==1:                                                         
            for point in points:
                x, y = utmToLatLng(point.x, point.y, zone=1, northernHemisphere=True)
                if y<3: 
                    y = y+6
                check = Point(y, x)
                wahr = True
                for i in range(len(boundaries)):
                    is_inside = gpd.sjoin(gpd.GeoDataFrame({'geometry': [check]}), boundaries[i], op='within')
                    if not is_inside.empty:
                        wahr=False
                if wahr: 
                    file_content = file_content + "(" + str(x) + ", " + str(y) + ")" + "\n"                
                    number-=1
        if liste[3]==2:                                                               
            for point in points:
                x, y = utmToLatLng(point.x, point.y, zone=1, northernHemisphere=True)
                y = y+6
                check = Point(y, x)
                wahr = True
                for i in range(len(boundaries)):
                    is_inside = gpd.sjoin(gpd.GeoDataFrame({'geometry': [check]}), boundaries[i], op='within')
                    if not is_inside.empty:
                        wahr=False
                if wahr: 
                    file_content = file_content + "(" + str(x) + ", " + str(y) + ")" + "\n"                
                    number-=1

    with open(file_path, "w") as file:
        file.write(file_content)
