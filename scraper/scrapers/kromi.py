import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import logging
from .base import BaseScraper
logger = logging.getLogger(__name__)

class KromiScraper(BaseScraper):
    def __init__(self):
        super().__init__("Kromi Market Online")

    def _get_product_elements_count(self, driver):
        """Devuelve el número actual de elementos de producto."""
        return len(driver.find_elements(By.CLASS_NAME, "itemProductoPasilloContainer"))

    def _scroll_and_wait_for_load_stabilization(self, driver, 
                                                initial_load_pause=1, 
                                                stabilization_check_interval=0.75, 
                                                stabilization_patience=3, 
                                                loading_img_timeout=10):
        """
        Hace scroll, espera a que el número de productos se estabilice o que el indicador de carga desaparezca.
        - initial_load_pause: Pausa inicial después del scroll para permitir que comience la carga.
        - stabilization_check_interval: Con qué frecuencia verificar si el número de productos ha cambiado.
        - stabilization_patience: Cuántos chequeos consecutivos con el mismo número de productos antes de considerar estabilizado.
        - loading_img_timeout: Timeout para esperar que la imagen de carga (si se usa) desaparezca.
        """
        logger.info(f"Iniciando scroll y esperando estabilización de productos en {self.site_name}...")
        scrolls_done = 0
        consecutive_no_new_global_products = 0
        max_consecutive_no_new_global_products = 2

        loading_img_selector_css = "#loadingMore img[src*='loading_cart.svg']"
        
        last_total_product_count = self._get_product_elements_count(driver)
        logger.debug(f"Productos iniciales antes del ciclo de scroll: {last_total_product_count}")

        while True:
            current_products_before_scroll = self._get_product_elements_count(driver)
            logger.debug(f"Scroll attempt #{scrolls_done + 1}. Productos antes de este scroll: {current_products_before_scroll}")
            
            self.scroll_slowly(driver)
            time.sleep(initial_load_pause) 

            patience_counter = 0
            last_check_product_count = self._get_product_elements_count(driver)

            max_stabilization_checks = int(loading_img_timeout / stabilization_check_interval) + stabilization_patience
            checks_done = 0

            while checks_done < max_stabilization_checks:
                try:
                    loading_image_visible = driver.find_element(By.CSS_SELECTOR, loading_img_selector_css).is_displayed()
                    if loading_image_visible:
                        logger.debug("Indicador de carga (imagen) visible, esperando...")
                        patience_counter = 0 
                        time.sleep(stabilization_check_interval)
                        last_check_product_count = self._get_product_elements_count(driver)
                        checks_done +=1
                        continue
                except (NoSuchElementException, TimeoutException):
                    logger.debug("Indicador de carga (imagen) no visible o no encontrado.")
                    pass
                except StaleElementReferenceException:
                    logger.warning("StaleElementReferenceException al verificar el indicador de carga. Reintentando conteo.")
                    time.sleep(0.5)
                    last_check_product_count = self._get_product_elements_count(driver)
                    patience_counter = 0
                    checks_done +=1
                    continue


                current_check_product_count = self._get_product_elements_count(driver)
                logger.debug(f"  Estabilización check: {patience_counter+1}/{stabilization_patience}. Productos: {current_check_product_count} (antes: {last_check_product_count})")

                if current_check_product_count == last_check_product_count:
                    patience_counter += 1
                else:
                    patience_counter = 0
                    last_check_product_count = current_check_product_count
                
                if patience_counter >= stabilization_patience:
                    logger.info(f"Número de productos estabilizado en {current_check_product_count} después de {patience_counter} chequeos iguales.")
                    break

                time.sleep(stabilization_check_interval)
                checks_done += 1
            
            if checks_done >= max_stabilization_checks and patience_counter < stabilization_patience:
                logger.warning("Se alcanzó el máximo de chequeos de estabilización sin que el conteo se estabilizara completamente o el loader desapareciera.")
            
            scrolls_done += 1
            current_total_product_count = self._get_product_elements_count(driver)
            logger.info(f"Scroll #{scrolls_done} completado. Total productos ahora: {current_total_product_count}")

            if current_total_product_count == last_total_product_count:
                consecutive_no_new_global_products += 1
                logger.info(f"No se cargaron nuevos productos globales en este scroll. Strike {consecutive_no_new_global_products}/{max_consecutive_no_new_global_products}.")
                if consecutive_no_new_global_products >= max_consecutive_no_new_global_products:
                    logger.info("No se cargaron más productos globales después de varios intentos. Asumiendo fin de página.")
                    break
            else:
                consecutive_no_new_global_products = 0
                last_total_product_count = current_total_product_count

    def scrape(self, driver, url):
        logger.info(f"Iniciando scraping para {self.site_name} en URL: {url}")
        driver.get(url)
        scraped_data = []

        self._scroll_and_wait_for_load_stabilization(driver, 
                                                     initial_load_pause=1,
                                                     stabilization_check_interval=0.75,
                                                     stabilization_patience=4,
                                                     loading_img_timeout=15,)  
        
        product_container_selector = (By.CLASS_NAME, "itemProductoPasilloContainer")
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located(product_container_selector)
            )
            logger.info(f"Contenedores de productos encontrados en {self.site_name}.")
        except TimeoutException:
            print(f"Timeout: No se encontraron contenedores de productos en {url} para {self.site_name}")
            return []

        product_elements = driver.find_elements(*product_container_selector)
        if not product_elements:
            logger.warning(f"Timeout: No se encontraron contenedores de productos en {url} para {self.site_name}")
            return []

        logger.info(f"Procesando {len(product_elements)} productos...")

        for product_element in product_elements:
            name = "Nombre no encontrado"
            price_text = "Precio no encontrado"
            numeric_price = None
            currency = "Moneda no encontrada"
            product_url = "#"

            try:
                name_element_anchor = product_element.find_element(By.CSS_SELECTOR, ".product-name-carousel a")
                name = name_element_anchor.text.strip()
                product_url = name_element_anchor.get_attribute('href')

                price_element = product_element.find_element(By.CLASS_NAME, "tag_precio_producto")
                price_text = price_element.text.strip()

                if price_text and price_text != "Precio no encontrado":
                    match_currency = re.match(r"([^\d\s.,]+)", price_text)
                    if match_currency:
                        currency_symbol = match_currency.group(1)
                        if currency_symbol == "$":
                            currency = "USD"
                        else:
                            currency = currency_symbol

                    match_price = re.search(r"([\d,.]+)", price_text)
                    if match_price:
                        price_str_cleaned = match_price.group(1).replace(',', '')
                        try:
                            numeric_price = float(price_str_cleaned)
                        except ValueError:
                            logger.warning(f"No se pudo convertir '{price_str_cleaned}' a número para el producto '{name}'")
                            numeric_price = None
                    else:
                        numeric_price = None


            except NoSuchElementException as e:
                logger.warning(f"Elemento faltante para un producto en {self.site_name}: {e}. Nombre parcial: {name}")
            except Exception as e:
                logger.error(f"Error procesando un producto en {self.site_name}: {e}. Nombre parcial: {name}")

            if name != "Nombre no encontrado" and numeric_price is not None:
                data_item = {
                    "name": name,
                    "price": numeric_price,
                    "currency": currency,
                    "site": self.site_name,
                    "url": product_url
                }
                scraped_data.append(data_item)
                logger.debug(f"  - Producto scrapeado: {name}: {currency} {numeric_price}")
            else:
                logger.info(f"  - Producto omitido (datos incompletos): Nombre='{name}', PrecioTexto='{price_text}'")


        logger.info(f"Scraping para {self.site_name} completado. Datos obtenidos: {len(scraped_data)} items.")
        return scraped_data