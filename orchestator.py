import pandas as pd
import logging
import os
from datetime import datetime

from scraper import scraper
from data_processor import ProductDataPreprocessor



def setup_logging(log_level=logging.INFO, log_file="orchestrator.log"): # Cambiado nombre del log
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, log_file)
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s')
    
    root_logger = logging.getLogger()
    # Limpiar handlers existentes para evitar duplicación si se llama varias veces
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.setLevel(log_level)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)
    
    file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)
    logging.info("Logging configurado. Logs se guardarán en: %s", log_file_path)


def execute_orchestrator(db_manager=None, run_scrapers_flag=True, 
                         run_preprocessing_flag=True):
    """
    Orquesta el proceso completo de scraping, preprocesamiento y análisis.
    """
    setup_logging(log_level=logging.INFO)
    
    
    if not db_manager.conn:
        logging.critical("Abortando orquestador debido a fallo de conexión a la BD.")
        return 

    all_scraped_data_for_preprocessing = []

    if run_scrapers_flag:
        logging.info("--- Iniciando Fase de Scraping ---")
        all_scraped_data_for_preprocessing = scraper.execute_scrapers()
        
        if all_scraped_data_for_preprocessing:
            logging.info(f"Scraping completado. Total productos crudos obtenidos: {len(all_scraped_data_for_preprocessing)}")
        else:
            logging.info("No se obtuvieron datos de los scrapers.")
    else:
        logging.info("Fase de Scraping omitida por configuración.")


    df_preprocessed_for_db = pd.DataFrame()
    if run_preprocessing_flag and all_scraped_data_for_preprocessing:
        logging.info(f"--- Iniciando Fase de Preprocesamiento para {len(all_scraped_data_for_preprocessing)} productos ---")
        preprocessor = ProductDataPreprocessor(lang='spanish')
        preprocessor.load_data(all_scraped_data_for_preprocessing)
        df_preprocessed_for_db = preprocessor.preprocess_data()
        
        if not df_preprocessed_for_db.empty:
            logging.info("Preprocesamiento completado.")

            products_to_insert_db_list = df_preprocessed_for_db.to_dict('records')
            inserted_count = db_manager.insert_preprocessed_products_batch(products_to_insert_db_list,datetime.now())
            logging.info(f"Se intentó insertar {len(products_to_insert_db_list)} productos preprocesados en BD, insertados exitosamente: {inserted_count}")
        else:
            logging.warning("DataFrame preprocesado está vacío después del preprocesamiento. No se insertará en BD.")
    elif not run_preprocessing_flag:
        logging.info("Fase de Preprocesamiento omitida por configuración.")
    else:
         logging.info("No hay datos crudos para preprocesar.")

    db_manager.close_connection()

    logging.info("Orquestador finalizado.")