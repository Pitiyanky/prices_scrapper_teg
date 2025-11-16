import time
import logging
import os
import csv
from datetime import datetime
from .webdriver_manager import WebDriverManager
from .scrapers import KromiScraper, KaleaMarketScraper, TuzonaMarketScraper

from config import URL_KROMI_VIVERES, URL_KALEA_MARKET_CAT

def execute_scrapers():
    """ Ejecuta los scrapers para Kromi Market y Kalea Market.
    """
    manager = WebDriverManager()
    all_scraped_data = []
    with manager as driver:
        if driver:
            logging.info("--- Iniciando Scraper para Kromi Market (Víveres) ---")
            scraper_kromi = KromiScraper()
            datos_kromi = scraper_kromi.scrape(driver, URL_KROMI_VIVERES)
            if datos_kromi:
                logging.info(f"Datos de Kromi Market obtenidos: {len(datos_kromi)} productos.")
                
                all_scraped_data.extend(datos_kromi)
            else:
                logging.info("No se obtuvieron datos de Kromi Market")
            logging.info("--- Iniciando Scraper para Kalea Market ---")
            try:
                scraper_kalea = KaleaMarketScraper()
                datos_kalea = scraper_kalea.scrape(driver, URL_KALEA_MARKET_CAT)
                if datos_kalea:
                    logging.info(f"Datos de Kalea Market obtenidos: {len(datos_kalea)} productos.")
                    all_scraped_data.extend(datos_kalea)
                else:
                    logging.info("No se obtuvieron datos de Kalea Market")
            except Exception as e:
                logging.error(f"Error al ejecutar el scraper de Kalea Market: {e}")

            logging.info("--- Iniciando Scraper para Tu zona Market ---")
            scraper_tuzonamarket = TuzonaMarketScraper()
            datos_tuzonamarket = scraper_tuzonamarket.scrape()
            if datos_tuzonamarket:
                logging.info(f"Datos de tuzonamarket Market obtenidos: {len(datos_tuzonamarket)} productos.")
                all_scraped_data.extend(datos_tuzonamarket)
            else:
                logging.info("No se obtuvieron datos de Tu zona Market")
        else:
            logging.critical("No se pudo iniciar el WebDriver. Terminando ejecución.")
            
    
    logging.info("Proceso de scraping finalizado.")
    return all_scraped_data