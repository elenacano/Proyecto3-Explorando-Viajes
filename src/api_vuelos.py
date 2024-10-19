import dotenv # type: ignore
import json
import os
import pandas as pd # type: ignore
import requests # type: ignore

dotenv.load_dotenv()

def llamada_api_vuelos(dic_queries, ciudades):

    """Llamada a la API de sky scrapper para obtener vuelos de ida y vuelta entre dos ciudades
    para el puente de diciembre.

    Args:
        dic_queries (dict): diccionario con originSkyId, originEntityId de Madrid y destinationSkyId,
                            destinationEntityId con los valores de Paris y Roma en una lista.
        ciudades (list): lista de ciudades a las cuales queremos volar desde Madrid.
    """
    
    url = "https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchFlights"
    api_key = os.getenv("api_key")

    for i in range(len(ciudades)):
        print(f"Estamos buscando los vuelos para: {ciudades[i]}")
        
        querystring = {
            "originSkyId": dic_queries["originSkyId"],
            "destinationSkyId": dic_queries["destinationSkyId"][i],
            "originEntityId": dic_queries["originEntityId"],
            "destinationEntityId": dic_queries["destinationEntityId"][i],
            "date": "2024-12-06",
            "returnDate": "2024-12-08",
            "cabinClass": "economy",
            "adults": "1",
            "currency": "EUR",
            "market": "es-ES",
            "countryCode": "ES"
        }

        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "sky-scrapper.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring)
        print(response.status_code)
        res = response.json()
        
        with open(f"../datos/vuelos_{ciudades[i]}.json", "w") as archivo_json:
            json.dump(res, archivo_json, indent=4)

    return



def creacion_dic_vuelos(lista_itinerario):

    """Para cada itinerario sacamos los datos deseados y los almacenamos en un diccionario.

    Args:
        lista_itinerario (list): lista de los 100 mejores itinerarios.

    Returns:
        dict: diccionario con todos los datos extraidos.
    """
    dic_itinerarios={
            "precio": [],
            "origen_ida": [],
            "destino_ida": [],
            "min_duracion_ida": [],
            "escalas_ida": [],
            "hora_salida_ida": [],
            "hora_llegada_ida": [],
            "aerolinea_ida": [],

            "origen_vuelta": [],
            "destino_vuelta": [],
            "min_duracion_vuelta": [],
            "escalas_vuelta": [],
            "hora_salida_vuelta": [],
            "hora_llegada_vuelta": [],
            "aerolinea_vuelta": []
        }
     
    # Cada itinerario tiene un precio y los vuelos de ida y vuelta
    for itinerario in lista_itinerario:

        dic_itinerarios["precio"].append(itinerario["price"]["raw"])

        # vuelos ida
        leg_ida = itinerario["legs"][0]

        dic_itinerarios["origen_ida"].append(leg_ida["origin"]["name"])
        dic_itinerarios["destino_ida"].append(leg_ida["destination"]["name"])
        dic_itinerarios["min_duracion_ida"].append(leg_ida["durationInMinutes"])
        dic_itinerarios["escalas_ida"].append(leg_ida["stopCount"])
        dic_itinerarios["hora_salida_ida"].append(leg_ida["departure"])
        dic_itinerarios["hora_llegada_ida"].append(leg_ida["arrival"])
        dic_itinerarios["aerolinea_ida"].append(leg_ida["carriers"]["marketing"][0]["name"])

        # vuelos vuelta
        leg_vuelta = itinerario["legs"][0]

        dic_itinerarios["origen_vuelta"].append(leg_vuelta["origin"]["name"])
        dic_itinerarios["destino_vuelta"].append(leg_vuelta["destination"]["name"])
        dic_itinerarios["min_duracion_vuelta"].append(leg_vuelta["durationInMinutes"])
        dic_itinerarios["escalas_vuelta"].append(leg_vuelta["stopCount"])
        dic_itinerarios["hora_salida_vuelta"].append(leg_vuelta["departure"])
        dic_itinerarios["hora_llegada_vuelta"].append(leg_vuelta["arrival"])
        dic_itinerarios["aerolinea_vuelta"].append(leg_vuelta["carriers"]["marketing"][0]["name"])

    return dic_itinerarios


def formateo_hora(df):
    """Fomateamos las horas del DataFrame.

    Args:
        df (DataFrame): DataFrame del que deseamos formatear las horas.

    Returns:
        DataFrame: devolvemos el DataFrame con las horas formateadas a nuestro gusto.
    """
    df["hora_salida_ida"]=df["hora_salida_ida"].str.split("T").apply(lambda x: x[1])
    df["hora_salida_ida"]= pd.to_datetime(df['hora_salida_ida'], format='%H:%M:%S').dt.strftime('%H:%M')

    df["hora_llegada_ida"]=df["hora_llegada_ida"].str.split("T").apply(lambda x: x[1])
    df["hora_llegada_ida"]= pd.to_datetime(df['hora_llegada_ida'], format='%H:%M:%S').dt.strftime('%H:%M')

    df["hora_salida_vuelta"]=df["hora_salida_vuelta"].str.split("T").apply(lambda x: x[1])
    df["hora_salida_vuelta"]= pd.to_datetime(df['hora_salida_vuelta'], format='%H:%M:%S').dt.strftime('%H:%M')

    df["hora_llegada_vuelta"]=df["hora_llegada_vuelta"].str.split("T").apply(lambda x: x[1])
    df["hora_llegada_vuelta"]= pd.to_datetime(df['hora_llegada_vuelta'], format='%H:%M:%S').dt.strftime('%H:%M')

    return df


def limpieza_json_vuelos(ciudades):

    """ Tomamos los 100 mejores itinerarios para el vuelo a cada ciudad y extraemos los datos deseados y los guadarmos en un Dataframe.

    Args:
        ciudades (list): lista de ciudades a las que deseamos volar desde Madrid
    """

    for ciudad in ciudades:
        with open(f"../datos/vuelos_{ciudad}.json", "r") as archivo_json:
            res = json.load(archivo_json)

        # Nos quedamos solo con los primeros 100 mejores itinerarios
        lista_itinerario = res["data"]["itineraries"][:100]
        dic_itinerarios = creacion_dic_vuelos(lista_itinerario)
        
        df = pd.DataFrame(dic_itinerarios)
        df_fomateado = formateo_hora(df)
        df_fomateado.to_csv(f"../datos/df_vuelos_{ciudad}.csv")

    return



def main():

    """Hacemos unallamada a la API para obtener itinerarios entre marid y roma o paris y ls almacenamos en un DataFrame.
    """
    
    dic_queries= {
    "originSkyId":"mad",
	"originEntityId":"95565077",
	"destinationSkyId":["ROME", "CDG"],
	"destinationEntityId":["27539793", "95565041"]}
    ciudades=["roma", "paris"]

    llamada_api_vuelos(dic_queries, ciudades)
    limpieza_json_vuelos(ciudades)



if __name__ == "__main__":
    main()