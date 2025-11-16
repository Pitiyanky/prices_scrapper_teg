import requests
import time
import logging
from .base import BaseScraper 

logger = logging.getLogger(__name__)

class TuzonaMarketScraper(BaseScraper):
    """
    Scraper para obtener datos de productos de la API de Tuzona Market.
    Itera a través de las páginas de la categoría 'supermercado'.
    """
    
    ALLOWED_CATEGORIES = {
        'Alimentos', 'Lácteos y Huevos', 'Leches y Huevos', 'Mantequillas y Margarinas', 
        'Yogurt', 'Harinas y Cereales','Pasta y Granos', 'Pasta', 'Granos', 'Salsas',
        'Clasicas','Sazonadoras','Pastas','Aceites, Vinagres y Condimentos',
        'Azúcares y Endulzantes','Repostería','Mezclas y Gelatina','Articulos para Reposteria',
        'Chocolates y Dulces', 'Chocolates', 'Caramelos y Chupetas', 'Mermeladas y Siropes', 
        'Chiclets', 'Enlatados y Envasados', 'Tomate y Puré', 'Mariscos y Pescados', 
        'Frutas y Vegetales Enlatados', 'Para untar', 'Galletas y Ponques', 'Galletas Saladas', 
        'Galletas Dulces', 'Ponqués', 'Snacks', 'Papas, Tostones y más', 'Frutos Secos',
        'Café e Infusiones', 'Infusiones y Té', 'Café y Cacao', 'Caldos y Sopas', 
        'Sabores del Mundo' ,'Asia', 'Europa', 'Medio Oriente','Lavado de Ropa'
    }

    def __init__(self):
        """Inicializa el scraper con el nombre del sitio."""
        super().__init__("Tuzona Market")
        self.base_api_url = "https://api.tuzonamarket.com/api/categoria/supermercado/2?pag="
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    
    def _parse_product_data(self, api_item):
        """
        Extrae y formatea los datos de un único item de producto de la API.
        Devuelve un diccionario con los datos o None si el producto no es válido.
        """
        try:
            category_list = api_item.get('categoria', [])
            if not isinstance(category_list, list) or not category_list:
                return None

            first_category = category_list[0]
            if not isinstance(first_category, dict):
                return None
            
            category_name = first_category.get('nombre', 'N/A')

            if category_name not in self.ALLOWED_CATEGORIES:
                logger.debug(f"Producto omitido por categoría no deseada: '{category_name}'")
                return None

            name = api_item.get('nombre', 'Nombre no encontrado')
            

            price = None
            prices_list = api_item.get('precio', [])
            
            basico_price_info = None
            if isinstance(prices_list, list):
                for price_item in prices_list:
                    if not isinstance(price_item, dict):
                        continue
                    
                    user_type_info = price_item.get('usuarioTipo', {})
                    
                    if isinstance(user_type_info, dict) and user_type_info.get('nombre') == 'Basico':
                        basico_price_info = price_item  
                        break  

            if basico_price_info:
                base_price = float(basico_price_info.get('precio', 0.0)) / 100.0
                
                impuesto_info = basico_price_info.get('impuesto', {})
                tax_percentage = 0.0
                if isinstance(impuesto_info, dict):
                    tax_percentage = float(impuesto_info.get('porcentaje', 0.0))

                final_price = base_price
                if tax_percentage > 0:
                    final_price = base_price * (1 + (tax_percentage / 10000.0))

  
                price = final_price
            

            if name != 'Nombre no encontrado' and price is not None:
                product_data = {
                    "name": name,
                    "price": price,
                    "currency": "USD", 
                    "site": self.site_name,
                    "url": f"https://tuzonamarket.com/product/{api_item.get('slug', '')}"
                }

                return product_data
            else:
                logger.warning(f"Producto omitido por datos incompletos o sin precio 'Basico': Nombre='{name}'")
                return None

        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Error parseando un item de producto: {e}. Data: {api_item}")
            return None

  

    def scrape(self, start_page=1, end_page=135, delay_between_requests=1):
        """
        Realiza el scraping de la API de Tuzona Market página por página.
        
        Args:
            start_page (int): La página por la que empezar.
            end_page (int): La última página a scrapear.
            delay_between_requests (int): Segundos de espera entre peticiones.

        Returns:
            list: Una lista de diccionarios, cada uno representando un producto.
        """
        logger.info(f"Iniciando scraping para {self.site_name} desde la página {start_page} hasta la {end_page}.")
        scraped_data = []

        for page_num in range(start_page, end_page + 1):
            url_to_scrape = f"{self.base_api_url}{page_num}"
            logger.info(f"Scrapeando página {page_num}/{end_page} - URL: {url_to_scrape}")

            try:
                response = requests.get(url_to_scrape, headers=self.headers, timeout=15)
                response.raise_for_status() 
                
                api_data = response.json()
                products_list = api_data.get('producto', {}).get('data', [])

                if not products_list:
                    logger.warning(f"No se encontraron productos en la página {page_num}. Podría ser el final.")
                    continue

                logger.info(f"Procesando {len(products_list)} productos de la página {page_num}...")
                for item in products_list:
                    product_dict = self._parse_product_data(item)
                    if product_dict:
                        scraped_data.append(product_dict)
                        logger.debug(f"  - Producto scrapeado: {product_dict['name']}")

            except requests.exceptions.HTTPError as e:
                logger.error(f"Error HTTP en página {page_num}: {e}")
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Error de conexión en página {page_num}: {e}")
            except requests.exceptions.Timeout:
                logger.error(f"Timeout en la petición para la página {page_num}.")
            except ValueError as e: # Error decodificando JSON
                logger.error(f"Error decodificando JSON en página {page_num}: {e}. Respuesta: {response.text[:200]}...")
            finally:
                logger.debug(f"Esperando {delay_between_requests} segundos...")
                time.sleep(delay_between_requests)
        
        logger.info(f"Scraping para {self.site_name} completado. Total de datos obtenidos: {len(scraped_data)} items.")
        return scraped_data

