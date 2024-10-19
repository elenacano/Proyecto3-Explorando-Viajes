from bs4 import BeautifulSoup
import requests
import numpy as np
from tqdm import tqdm
from time import sleep
import math

import pandas as pd

from selenium import webdriver  
from webdriver_manager.chrome import ChromeDriverManager  
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.support.ui import Select 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

def obtencion_html(lista_urls, ciudades):
    driver = webdriver.Chrome()
   
    if len(ciudades)!=len(lista_urls):
        print("Debe haber el mismo número de ciudades que de enlaces")
        return -1

    j=0
    for url in lista_urls:
        print(url)
        driver.get(url)
        driver.maximize_window()
        sleep(1)

        # Veamos cuantas actividades hay
        num_actividades = driver.find_element("css selector", "#num_tours").text
        num_actividades = int(num_actividades)

        # Como hay que ir cargando el contenido vamos a calcular cuantas veces hay que dar al botón sabiendo que carga 20 actividades cada vez
        num_clicks=math.ceil(num_actividades/20)

        for i in range(num_clicks-1):
            driver.execute_script("window.scrollTo(0, 15000);")
            sleep(1)
            driver.find_element("css selector", "#more_tours > span").click()
            sleep(1)

        # Una vez cargado todo el html de la página lo traemos y lo guardamos
        html_table_page = driver.page_source
        with open(f'../datos/actividades_{ciudades[j]}.html', 'w', encoding='utf-8') as file:
                file.write(html_table_page) 
        j+=1
        sleep(3)

    driver.quit()

    return


def get_puntuacion_opinion_cancelacion(sopa):
    tour_list_desc = sopa.findAll("div", {"class":"tour_list_desc"})

    puntuacion=[]
    opiniones =[]
    cancelacion = []

    for tour in tour_list_desc:
        lista_puntuacion_aux=tour.select("div.tour_list_desc div.rating small") 
        lista_opiniones_aux=tour.select("div.tour_list_desc div.rating span")
        lista_cancelacion_aux=tour.select("div.tour_list_desc div.cancelacion-gratuita")

        # Sacamos la lista de las calificaciones
        if len(lista_puntuacion_aux)==0:
            puntuacion.append(np.nan)
        else:
            puntuacion.append(lista_puntuacion_aux[0].text.replace(" ", ""))

        # Sacamos la lista de las opiniones
        if len(lista_opiniones_aux)==0:
            opiniones.append(np.nan)
        else:
            opiniones.append(lista_opiniones_aux[0].text)

        # Sacamos la lista de si hay cancelacion gratuita
        if len(lista_cancelacion_aux)==0:
            cancelacion.append("No")
        else:
            cancelacion.append("Si")

    return puntuacion, opiniones, cancelacion


def get_duracion_idioma(sopa):
    duracion=[]
    idioma=[]

    tour_featured_aux = sopa.findAll("div", {"class":"price_list"})
    tour_featured = tour_featured_aux[::2]

    for tour in tour_featured:
        lista_duracion_aux=tour.select("div.price_list div.tduration")
        lista_idioma_aux=tour.select("div.price_list div.tlang")

        #Creamos la lista de duracion
        if len(lista_duracion_aux)==0:
            duracion.append(np.nan)
        else:
            duracion.append(lista_duracion_aux[0].text.replace("\n","").strip())

        #Creamos la lista de idiomas
        if len(lista_idioma_aux)==0:
            idioma.append(np.nan)
        else:
            idioma.append(lista_idioma_aux[0].text.replace("\n","").strip())

    return duracion, idioma


def get_precio(sopa):
    precios=[]
    precios_aux = sopa.findAll("div", {"class":"price_container"})
    for precio in precios_aux:
        lista_precio = precio.findAll("span")
        #Es gratis
        if len(lista_precio)==2: 
            precios.append(0)
        #El precio no esta rebajado
        elif len(lista_precio)==3: 
            precios.append(float(lista_precio[0].text))
        #El precio si esta rebajado
        elif len(lista_precio)>3:
            precios.append(float(lista_precio[3].text))
        else:
            precios.append(np.nan)

    return precios


def creacion_df(ciudades):
    for ciudad in ciudades:

        # Traemos los datos del html de cada página y hacemos la sopa
        with open(f'../datos/actividades_{ciudad}.html', 'r', encoding='utf-8') as file:
            html_contenido = file.read()
        sopa = BeautifulSoup(html_contenido, "html.parser")

        # Sacamos las títulos
        lista_titulos = sopa.findAll("h2")
        titulos = [titulo.text for titulo in lista_titulos]

        # Sacamos las categorías
        lista_categorias = sopa.findAll("h3", {"class":"category desktop"})
        categorias = [categoria.text for categoria in lista_categorias]

        # Sacamos la puntuacion, las opiniones y si hay cancelación gratuita
        puntuacion, opiniones, cancelacion = get_puntuacion_opinion_cancelacion(sopa)

        #Sacamos la duración de la actividad y el idioma
        duracion, idioma = get_duracion_idioma(sopa)

        #Sacamos el precio de la actividad
        precios = get_precio(sopa)

        dic_df={"actividad":titulos, 
                "categoria":categorias, 
                "cancelacio_gratuita":cancelacion, 
                "puntuacion":puntuacion, 
                "opiniones":opiniones, 
                "duracion":duracion, 
                "idioma":idioma, 
                "precio":precios}

        df=pd.DataFrame(dic_df)
        df["opiniones"]=df["opiniones"].str.replace(" Opiniones)", "").str.replace("(","")
        
        print(f"Estamos haciendo el df de {ciudad}")
        df.to_csv(f"../datos/df_{ciudad}.csv")
        
    return


def main():
    lista_urls = ["https://www.guias.travel/tour/?s=roma", "https://www.guias.travel/tour/?s=paris"]
    ciudades = ["roma", "paris"]

    res = obtencion_html(lista_urls, ciudades)
    if res == -1:
        return
    
    creacion_df(ciudades)



if __name__ == "__main__":
    main()
