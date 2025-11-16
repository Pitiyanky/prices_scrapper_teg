import pandas as pd
import nltk
import logging
from .utils import UDMExtractor, get_product_type

logger = logging.getLogger(__name__)

class ProductDataPreprocessor:
    def __init__(self, lang='spanish'):
        """
        Inicializa el preprocesador de datos de productos.
        Enfocado en limpieza, normalización y extracción de UDM.
        """
        self.lang = lang
        self.df = None

    def _extract_and_normalize_udm(self, product_name_series):
        """
        Extrae cantidad y unidad de una serie de nombres de producto y normaliza unidades.
        Devuelve un DataFrame con 'extracted_quantity' y 'normalized_unit'.
        """
        udm_extractor = UDMExtractor()
        return udm_extractor.extract_and_normalize_udm(product_name_series)
    
    
    def _get_product_type(self, name):
        """
            Obtiene el tipo de producto a partir del nombre.
        """
        return get_product_type(name) if isinstance(name, str) else ''
    

    def load_data(self, data_source):
        """Carga datos desde lista de diccionarios."""
        if isinstance(data_source, list):
            if not data_source:
                logger.warning("Lista de datos de entrada vacía.")
                self.df = pd.DataFrame()
            else:
                self.df = pd.DataFrame(data_source)
                logger.info(f"Datos cargados desde lista de diccionarios. Filas: {len(self.df)}")
        else:
            logger.error("Fuente de datos no soportada.")
            self.df = pd.DataFrame()
        
        return self


    def preprocess_data(self):
        """
        Aplica toda la lógica de preprocesamiento.
        """
        if self.df is None or self.df.empty:
            return pd.DataFrame()

        logger.info("Iniciando preprocesamiento de datos...")

        if 'name' in self.df.columns:
            df_udm_extracted = self._extract_and_normalize_udm(self.df['name'])
            self.df = self.df.reset_index(drop=True)
            df_udm_extracted = df_udm_extracted.reset_index(drop=True)
            self.df = pd.concat([self.df, df_udm_extracted], axis=1)
            self.df['product_type'] = self.df['name'].apply(self._get_product_type)
            logger.info("Extracción y normalización de UDM completada.")
        else:
            
            self.df['extracted_quantity'] = None
            self.df['normalized_unit'] = None
            self.df['product_type'] = None

        logger.info("Preprocesamiento de datos finalizado.")
        return self.df