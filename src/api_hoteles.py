import dotenv # type: ignore
import json
import os
import pandas as pd # type: ignore
import numpy as np
import requests # type: ignore
from geopy.geocoders import Nominatim # type: ignore
from geopy.distance import geodesic # type: ignore

dotenv.load_dotenv()


def get_coordenadas(ciudades):
    """Hacemos varias llamdas a la API para obtener las coordenadas de las ciudades deseadas.

    Args:
        ciudades (list): lista de las ciudades de las cuales queremos saber las coordenadas.

    Returns:
        dict: un diccionario con clave la ciudad y valor otro diccionario con claves la latitud y longitud de dicha ciudad.
    """
    url = "https://booking-com15.p.rapidapi.com/api/v1/meta/locationToLatLong"    
    api_key_hoteles = os.getenv("api_key_hoteles")
    dic_coordenadas_ciudades={}

    for ciudad in ciudades:
        print(f"Calculando las coordenadas de: {ciudad}")
        coord={}
        
        url = "https://booking-com15.p.rapidapi.com/api/v1/meta/locationToLatLong"

        querystring = {"query":{ciudad}}

        headers = {
            "x-rapidapi-key": api_key_hoteles,
            "x-rapidapi-host": "booking-com15.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring)
        print(response.status_code)
        res = response.json()
        latitud = res["data"][0]["geometry"]["location"]["lat"]
        longitud = res["data"][0]["geometry"]["location"]["lng"]
        coord["latitud"]=latitud
        coord["longitud"]=longitud
        dic_coordenadas_ciudades[ciudad]=coord
        
    return dic_coordenadas_ciudades


def get_direccion(latitud, longitud):
    """Calculamos la dirección de un punto a través de sus coordenadas.

    Args:
        latitud (float): latitud del sitio cuya dirección queremos saber.
        longitud (float): longitud del sitio cuya dirección queremos saber.

    Returns:
        str: dirección del sitio.
    """
    geolocator = Nominatim(user_agent="hoteles")
    location = geolocator.reverse(""+str(latitud)+", "+str(longitud))
    return location.address


def  get_pto_ref(ciudad, latitud, longitud, dic_hoteles):

    """Calculamos los km de un punto a otro punto de referencia.

    Args:
        ciudad(str): ciudad donde esta el punto de partida.
        latitud (float): latitud del sitio de partida.
        longitud (float): longitud del sitio de partida.
        dic_hoteles(dict): diccionario al cual queremos añadir la dictancia al punto de referencia.

    Returns:
        dict: el diccionario con una nueva clave y los kilometros al punto de referencia desde el punto pasado como argumento.
    """
    
    geolocator = Nominatim(user_agent="SetMagic")

    if ciudad == "rome":
        location = geolocator.geocode("coliseo")
        coord1 = (latitud, longitud)  # Hotel
        coord2 = (location.latitude, location.longitude)  # Coliseo
        distancia = geodesic(coord1, coord2).kilometers

        if "dist_coliseo" not in dic_hoteles:
            dic_hoteles["dist_coliseo"] = []

        dic_hoteles["dist_coliseo"].append(np.round(distancia,2))
        return dic_hoteles
    
    elif ciudad == "paris":
        location = geolocator.geocode("museo del louvre")
        coord1 = (latitud, longitud)  # Hotel
        coord2 = (location.latitude, location.longitude)  # Museo del Louvre
        distancia = geodesic(coord1, coord2).kilometers

        if "dist_louvre" not in dic_hoteles:
            dic_hoteles["dist_louvre"] = []

        dic_hoteles["dist_louvre"].append(np.round(distancia,2))
        return dic_hoteles
    
    else:
        return dic_hoteles


def llamada_api_hoteles(ciudades, dic_coordenadas):

    """llemada a la API para obtener hoteles cercanos a unas coordenadas y almacenaros en un json.

    Args:
        ciudades (list): lista de las ciudades donde vamos a buscar los hoteles.
        dic_coordenadas (dict): diccionario con las cordenadas de dichas ciudades.
    """

    url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotelsByCoordinates"
    api_key_hoteles = os.getenv("api_key_hoteles")

    for ciudad in ciudades:
        for i in range(1,11):
            querystring = {
                "latitude": dic_coordenadas[ciudad]["latitud"],
                "longitude": dic_coordenadas[ciudad]["longitud"],
                "arrival_date": "2024-12-06",
                "departure_date": "2024-12-08",
                "radius": "10",
                "adults": "1",
                "children_age": "0",
                "room_qty": "1",
                "units": "metric",
                "page_number": {i},
                "temperature_unit": "c",
                "languagecode": "es",
                "currency_code": "EUR"
            }

            headers = {
                "x-rapidapi-key": api_key_hoteles,
                "x-rapidapi-host": "booking-com15.p.rapidapi.com"
            }
            
            print(f"Llamada a la api de hoteles en {ciudad}")
            response = requests.get(url, headers=headers, params=querystring)
            print(response.status_code)
            
            res = response.json()
            with open(f"../datos/hoteles_{ciudad}_{i}.json", "w") as archivo_json:
                json.dump(res, archivo_json, indent=4)
                  

def limieza_json_hoteles(ciudades):

    """A partir de un json obtenemos los datos deseados de cada hotel y los almacenado en un dataframe.

    Args:
        ciudades (list): lista de ciudades para las cuales hemos creado los json.
    """

    for ciudad in ciudades:
        print(f"Creando df de hoteles para {ciudad}")
        df=pd.DataFrame()
        for i in range(1,11):
            with open(f"../datos/hoteles_{ciudad}_{i}.json", "r") as archivo_json:
                res = json.load(archivo_json)

            hoteles=res["data"]["result"]

            dic_hoteles={
                "hotel":[],
                "puntuacion":[],
                "precio_total":[],
                "direccion":[],
                "cancelacion_gratuita":[],
                "hora_checkout":[]
            }

            for hotel in hoteles:
                dic_hoteles["hotel"].append(hotel["hotel_name"])
                dic_hoteles["puntuacion"].append(hotel["review_score"])
                dic_hoteles["precio_total"].append(hotel["composite_price_breakdown"]["all_inclusive_amount"]["value"])
                
                dic_hoteles["cancelacion_gratuita"].append(hotel["is_free_cancellable"])
                dic_hoteles["hora_checkout"].append(hotel["checkout"]["until"])
                latitud = hotel["latitude"]
                longitud = hotel["longitude"]
                dic_hoteles["direccion"].append(get_direccion(latitud, longitud))
                dic_hoteles = get_pto_ref(ciudad, latitud, longitud, dic_hoteles)

            df_hotel = pd.DataFrame(dic_hoteles)
            df = pd.concat([df,df_hotel])

        df["cancelacion_gratuita"] = df["cancelacion_gratuita"].map({0:"NO",1:"SI"})
        df.to_csv(f"../datos/df_hoteles_{ciudad}.csv")

            
def main():
    """Para unas ciudades dadas llamamos a la API para obtener hoteles cercanos, limpiamos los datos y los almacenamos en un DataFrame.
    """
    ciudades = ["rome", "paris"]
    dic_coordenadas = get_coordenadas(ciudades)
    print("Coordenadas calculadas: OK")
    llamada_api_hoteles(ciudades, dic_coordenadas)
    print("Llamada API: OK")
    limieza_json_hoteles(ciudades)
    print("DataFrames creados para los hoteles: OK")



if __name__ == "__main__":
    main()