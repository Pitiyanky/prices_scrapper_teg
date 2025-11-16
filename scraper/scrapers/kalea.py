import re
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException

from .base import BaseScraper

logger = logging.getLogger(__name__)

class KaleaMarketScraper(BaseScraper):


    def __init__(self):
        super().__init__("Kalea Market")
    

    def _click_load_more_button(self, driver, timeout=10):
        """
        Busca y hace clic en el botón "Cargar más".
        Devuelve True si se hizo clic, False en caso contrario (ej. botón no encontrado o no clickeable).
        """
        load_more_button_selector_css = "button.btn-primary.red.load" 
        
        try:
            load_more_button = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, load_more_button_selector_css))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
            time.sleep(0.5)

            load_more_button.click()
            logger.info("Botón 'Cargar más' clickeado.")
            return True
        except TimeoutException:
            logger.info("Botón 'Cargar más' no encontrado o no clickeable (Timeout). Asumiendo fin de productos.")
            return False
        except ElementClickInterceptedException:
            logger.warning("No se pudo hacer clic en 'Cargar más', otro elemento lo interceptó. Intentando de nuevo después de scroll.")
            driver.execute_script("window.scrollBy(0, 150);")
            time.sleep(1)
            try:
                load_more_button = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, load_more_button_selector_css))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                time.sleep(0.5)
                load_more_button.click()
                logger.info("Botón 'Cargar más' clickeado en el segundo intento.")
                return True
            except Exception as e:
                logger.error(f"Error al hacer clic en 'Cargar más' en el segundo intento: {e}")
                return False
        except Exception as e:
            logger.error(f"Error inesperado al intentar clickear 'Cargar más': {e}")
            return False

    def _navigate_to_products_page(self, driver, base_url):
        """
        Realiza los pasos de navegación para seleccionar tienda y categoría.
        Devuelve True si la navegación fue exitosa, False en caso contrario.
        """
        driver.get(base_url)
        logger.info(f"Navegando a la página de selección de tienda/inicio: {base_url}")


        try:
            logger.info("Intentando seleccionar la tienda...")
            store_dropdown_button_selector = (By.CSS_SELECTOR, "div.cuppa-dropdown div.c-btn")
            store_dropdown_button = self._wait_for_element(driver, *store_dropdown_button_selector, timeout=15)
            if not store_dropdown_button: 
                logger.error("Dropdown de tienda no encontrado.")
                return False
            

            dropdown_list_selector = (By.CSS_SELECTOR, "div.dropdown-list.animated.fadeIn")
            dropdown_list_element = driver.find_elements(*dropdown_list_selector)
            
            is_dropdown_visible = False
            if dropdown_list_element and dropdown_list_element[0].is_displayed():
                is_dropdown_visible = True
                logger.info("Dropdown de tiendas ya está visible.")

            if not is_dropdown_visible:
                logger.info("Haciendo clic en el botón del dropdown de tienda.")
                self._click_element(driver, *store_dropdown_button_selector)


            store_list_visible_selector = (By.CSS_SELECTOR, "div.dropdown-list.animated.fadeIn:not([hidden]) ul.lazyContainer")
            store_list_container = self._wait_for_element(driver, *store_list_visible_selector, timeout=10)
            if not store_list_container:
                logger.error("Lista de tiendas no se hizo visible después de hacer clic en el dropdown.")
                if not is_dropdown_visible:
                    logger.info("Intentando un segundo clic en el dropdown de tienda.")
                    self._click_element(driver, *store_dropdown_button_selector)
                    store_list_container = self._wait_for_element(driver, *store_list_visible_selector, timeout=10)
                    if not store_list_container:
                         logger.error("Lista de tiendas sigue sin ser visible.")
                         return False
            

            first_store_label_selector = (By.CSS_SELECTOR, "ul.lazyContainer li.pure-checkbox:first-child label")
            if not self._click_element(driver, *first_store_label_selector):
                logger.error("No se pudo hacer clic en la primera tienda.")
                return False
            logger.info("Primera tienda seleccionada de la lista.")
            if not self._click_element(driver, By.CSS_SELECTOR, "button.btn-primary"):
                logger.error("No se pudo hacer clic en el botón 'Seleccionar tienda'.")
                return False
            time.sleep(3)
            logger.info(f"URL actual después de seleccionar tienda: {driver.current_url}")

        except Exception as e:
            logger.error(f"Error durante la selección de tienda: {e}")
            return False

        try:
            logger.info("Intentando abrir el menú de categorías...")
            menu_icon_selector = (By.CSS_SELECTOR, "img.menu[alt='menu']")
            if not self._click_element(driver, *menu_icon_selector, timeout=15):
                logger.error("No se pudo hacer clic en el ícono del menú.")
                return False
            logger.info("Menú de categorías abierto.")
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//div[@class='category']/p[normalize-space()='despensa']"))
            )
        except Exception as e:
            logger.error(f"Error al abrir el menú de categorías: {e}")
            return False
            
        try:
            logger.info("Intentando seleccionar la categoría 'despensa'...")
            despensa_selector_xpath = "//div[@class='category']/p[normalize-space()='despensa']"
            despensa_element = self._wait_for_element(driver, By.XPATH, despensa_selector_xpath)
            if despensa_element:
                 driver.execute_script("arguments[0].scrollIntoView(true);", despensa_element)
                 time.sleep(0.3)
            if not self._click_element(driver, By.XPATH, despensa_selector_xpath):
                logger.error("No se pudo hacer clic en 'despensa'.")
                return False
            logger.info("Categoría 'despensa' seleccionada.")
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//div[@class='category']/p/strong[normalize-space()='Ver todo']"))
            )
        except Exception as e:
            logger.error(f"Error al seleccionar 'despensa': {e}")
            return False

        try:
            logger.info("Intentando seleccionar 'Ver todo'...")
            ver_todo_selector_xpath = "//div[@class='category']/p/strong[normalize-space()='Ver todo']"
            ver_todo_element = self._wait_for_element(driver, By.XPATH, ver_todo_selector_xpath)
            if ver_todo_element:
                 driver.execute_script("arguments[0].scrollIntoView(true);", ver_todo_element)
                 time.sleep(0.3)
            if not self._click_element(driver, By.XPATH, ver_todo_selector_xpath):
                logger.error("No se pudo hacer clic en 'Ver todo'.")
                return False
            logger.info("'Ver todo' seleccionado. Deberíamos estar en la página de productos.")
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "global-product-card"))
            )
            self.scroll_down(driver)
            logger.info(f"Navegación completada. URL actual: {driver.current_url}")
            return True
        except Exception as e:
            logger.error(f"Error al seleccionar 'Ver todo': {e}")
            return False

    def scrape(self, driver, url):
        logger.info(f"Iniciando scraping para {self.site_name} en URL: {url}")
         
        if not self._navigate_to_products_page(driver, url):
            logger.error("Falló la navegación a la página de productos. Abortando scrape para Kalea.")
            return []
        
        logger.info(f"Navegación a la página de productos de 'despensa' completada. URL actual: {driver.current_url}")
        
        category_product_url = driver.current_url 

        initial_product_card_selector = (By.CLASS_NAME, "global-product-card")
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located(initial_product_card_selector)
            )
            logger.info("Productos iniciales cargados en Kalea Market.")
        except TimeoutException:
            logger.warning(f"Timeout: No se encontraron productos iniciales en {url} para {self.site_name}")
            return []

        scraped_data = []
        processed_product_names = set()

        clicks_done = 0
        
        while True:
            products_before_click = len(driver.find_elements(*initial_product_card_selector))
            
            if not self._click_load_more_button(driver):
                logger.info("No se pudo hacer clic en 'Cargar más' o no estaba presente. Finalizando carga de productos.")
                break
            
            clicks_done += 1
            
            try:
                WebDriverWait(driver, 15).until(
                    lambda d: len(d.find_elements(*initial_product_card_selector)) > products_before_click or \
                              not d.find_element(By.CSS_SELECTOR, "button.btn-primary.red.load").is_displayed()
                )
                products_after_click = len(driver.find_elements(*initial_product_card_selector))
                if products_after_click > products_before_click:
                    logger.info(f"Nuevos productos cargados. Total ahora: {products_after_click}")
                elif not driver.find_elements(By.CSS_SELECTOR, "button.btn-primary.red.load"):
                    logger.info("Botón 'Cargar más' ya no está presente. Asumiendo fin de productos.")
                    break
                else:
                    logger.info("Se hizo clic en 'Cargar más', pero no se detectaron nuevos productos. Asumiendo fin.")
                    break

            except TimeoutException:
                logger.info("Timeout esperando nuevos productos después de hacer clic en 'Cargar más'. Asumiendo fin.")
                break
            except NoSuchElementException:
                logger.info("Botón 'Cargar más' ya no está presente después del clic. Asumiendo fin de productos.")
                break
            
            time.sleep(1)

        logger.info("Recolectando todos los productos después de los clics en 'Cargar más'...")
        all_product_elements = driver.find_elements(*initial_product_card_selector)
        
        if not all_product_elements:
            logger.info(f"No se encontraron elementos de producto en {self.site_name} después de la carga.")
            return []

        logger.info(f"Procesando {len(all_product_elements)} productos en total de Kalea Market...")
        
        for i, product_element in enumerate(all_product_elements):
            name = "Nombre no encontrado"
            price_text = "Precio no encontrado"
            numeric_price = None
            currency = "Moneda no encontrada"

            try:
                name_element = product_element.find_element(By.CSS_SELECTOR, "h5.name")
                name = name_element.text.strip()

                if name in processed_product_names:
                    continue
                processed_product_names.add(name)

                price_text_raw = "Precio no encontrado"
                
                
                price_container_usd_candidates = product_element.find_elements(By.XPATH, ".//div[contains(@class, 'price-container') and not(ancestor::div[contains(@class, 'hide')])]")
                
                p_price_element = None
                
                if len(price_container_usd_candidates) > 1:
                    for pc_candidate in price_container_usd_candidates:
                        try:
                            temp_p = pc_candidate.find_element(By.CSS_SELECTOR, "p.price")
                            if "$" in temp_p.text:
                                p_price_element = temp_p
                                break
                        except NoSuchElementException:
                            continue
                    if not p_price_element:
                         p_price_element = price_container_usd_candidates[1].find_element(By.CSS_SELECTOR, "p.price")

                elif len(price_container_usd_candidates) == 1:
                    try:
                        p_price_element = price_container_usd_candidates[0].find_element(By.CSS_SELECTOR, "p.price")
                    except NoSuchElementException:
                        logger.debug(f"KALEA: No se encontró p.price en el candidato a contenedor USD para '{name}'")
                        
                else: 
                    try:
                        p_price_element = product_element.find_element(By.XPATH, ".//p[@class='price' and not(ancestor::div[contains(@class,'hide')]) and contains(.,'$')]")
                    except NoSuchElementException:
                        logger.warning(f"KALEA: No se pudo encontrar el elemento de precio USD para '{name}'.")


                if p_price_element:
                    price_text_raw = driver.execute_script("""
                        var element = arguments[0];
                        var clone = element.cloneNode(true);
                        var discountedElements = clone.getElementsByTagName('del');
                        for (var i = 0; i < discountedElements.length; i++) {
                            discountedElements[i].parentNode.removeChild(discountedElements[i]);
                        }
                        return clone.textContent.trim();
                    """, p_price_element)
                    logger.debug(f"KALEA: Precio crudo extraído para '{name}': '{price_text_raw}'")
                else:
                    price_text_raw = "Precio no encontrado"
                
                price_text = price_text_raw


                if price_text and price_text != "Precio no encontrado":

                    match_currency = re.search(r"([$BsS/]+)", price_text)
                    if match_currency:
                        currency_symbol = match_currency.group(1).strip().replace('.', '')
                        if currency_symbol == "$": currency = "USD"
                        elif "Bs" in currency_symbol.upper(): currency = "VES"
                        elif "S/" in currency_symbol: currency = "PEN"
                        else: currency = currency_symbol.upper()
                    
                    price_str_for_conversion = re.sub(r'[^\d,.]', '', price_text)
                    
                    if currency == "USD":
                        price_str_for_conversion = price_str_for_conversion.replace(',', '')
                    elif currency == "VES":
                        if '.' in price_str_for_conversion and ',' in price_str_for_conversion:
                            if price_str_for_conversion.rfind(',') > price_str_for_conversion.rfind('.'):
                                price_str_for_conversion = price_str_for_conversion.replace('.', '').replace(',', '.')
                            else:
                                price_str_for_conversion = price_str_for_conversion.replace(',', '')
                        elif ',' in price_str_for_conversion:
                             price_str_for_conversion = price_str_for_conversion.replace(',', '.')


                    else: 
                        if ',' in price_str_for_conversion and '.' in price_str_for_conversion:
                            if price_str_for_conversion.rfind(',') > price_str_for_conversion.rfind('.'):
                                price_str_for_conversion = price_str_for_conversion.replace('.', '').replace(',', '.')
                            else:
                                price_str_for_conversion = price_str_for_conversion.replace(',', '')
                        elif ',' in price_str_for_conversion:
                            if re.search(r',\d{1,2}$', price_str_for_conversion) and price_str_for_conversion.count(',') == 1 :
                                 price_str_for_conversion = price_str_for_conversion.replace(',', '.')
                            else: 
                                 price_str_for_conversion = price_str_for_conversion.replace(',', '')
                    
                    try:
                        numeric_price = float(price_str_for_conversion)
                    except ValueError:
                        logger.warning(f"KALEA: No se pudo convertir '{price_str_for_conversion}' (orig procesado: '{price_text}') a número para '{name}'")
                        numeric_price = None
                else:
                    logger.debug(f"KALEA: Precio no encontrado o vacío para '{name}'.")
                    numeric_price = None 


            except NoSuchElementException: 
                logger.debug(f"KALEA: Elemento faltante para producto {i}. Omitido.")
                continue
            except StaleElementReferenceException:
                logger.warning(f"KALEA: StaleElement para producto {i}. Omitido.")
                continue 
            except Exception as e:
                logger.error(f"KALEA: Error procesando producto {i} ({name}): {e}")
                continue

            if name != "Nombre no encontrado" and numeric_price is not None:
                data_item = {
                    "name": name,
                    "price": numeric_price,
                    "currency": currency,
                    "site": self.site_name,
                    "url": category_product_url 
                }
                scraped_data.append(data_item)
            else:
                if name == "Nombre no encontrado" and (price_text and price_text != "Precio no encontrado"):
                    logger.warning(f"  - Producto Kalea omitido (nombre no encontrado). PrecioTexto='{price_text}'")
                elif name != "Nombre no encontrado" and numeric_price is None and (price_text and price_text != "Precio no encontrado"):
                     logger.warning(f"  - Producto Kalea omitido (precio no parseado): Nombre='{name}', PrecioTexto='{price_text}'")

        logger.info(f"Scraping para {self.site_name} completado. Datos obtenidos: {len(scraped_data)} items de {len(processed_product_names)} nombres únicos.")
        return scraped_data