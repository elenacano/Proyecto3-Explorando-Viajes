import dotenv
import json
import os
import pandas as pd
import numpy as np
import requests
from geopy.geocoders import Nominatim


dotenv.load_dotenv()


def get_coordenadas(ciudades):    
    url = "https://booking-com15.p.rapidapi.com/api/v1/meta/locationToLatLong"
    api_key = os.getenv("api_key")
    dic_coordenadas_ciudades={}

    for ciudad in ciudades:
        coord={}
        querystring = {"query":ciudad}

        headers = {
            "x-rapidapi-key": api_key,
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
    geolocator = Nominatim(user_agent="hoteles")
    location = geolocator.reverse(""+str(latitud)+", "+str(longitud))
    return location.address

def llamada_api_hoteles(ciudades, dic_coordenadas):

	url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotelsByCoordinates"
	api_key = os.getenv("api_key")

	for ciudad in ciudades:
		querystring = {"latitude":dic_coordenadas[ciudad]["latitud"],
					"longitude":dic_coordenadas[ciudad]["longitud"],
					"arrival_date":"2024-12-06",
					"departure_date":"2024-12-08",
					"radius":"10",
					"adults":"1",
					"children_age":"0",
					"room_qty":"1",
					"units":"metric",
					"page_number":"1",
					"temperature_unit":"c",
					"languagecode":"es",
					"currency_code":"EUR"}

		headers = {
			"x-rapidapi-key": api_key,
			"x-rapidapi-host": "booking-com15.p.rapidapi.com"
		}

		response = requests.get(url, headers=headers, params=querystring)
		print(response.status_code)
		res=response.json()
		with open(f"../datos/hoteles_{ciudad}.json", "w") as archivo_json:
			json.dump(res, archivo_json, indent=4)
                  

def limieza_json_hoteles(ciudades):

    for ciudad in ciudades:
        with open(f"../datos/hoteles_{ciudad}.json", "r") as archivo_json:
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



        df = pd.DataFrame(dic_hoteles)
        df["cancelacion_gratuita"] = df["cancelacion_gratuita"].map({0:"NO",1:"SI"})
        df.to_csv(f"../datos/df_hoteles_{ciudad}.csv")

            
def main():
    ciudades = ["rome", "paris"]
    dic_coordenadas = get_coordenadas(ciudades)
    llamada_api_hoteles(ciudades, dic_coordenadas)
    limieza_json_hoteles(ciudades)



if __name__ == "__main__":
    main()