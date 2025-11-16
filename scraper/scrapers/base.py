from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

class BaseScraper:
    def __init__(self, site_name):
        self.site_name = site_name
        print(f"Scraper para '{self.site_name}' inicializado.")

    def scrape(self, driver, url):
        raise NotImplementedError("Este método debe ser implementado por las clases hijas.")

    def _wait_for_element(self, driver, by, value, timeout=10):
        try:
            return WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            print(f"Timeout: Elemento no encontrado con {by}='{value}' en la URL: {driver.current_url} para {self.site_name}")
            return None
    
    def _click_element(self, driver, by, value, timeout=10):
        """Espera y hace clic en un elemento."""
        element = self._wait_for_element(driver, by, value, timeout)
        if element and element.is_displayed() and element.is_enabled():
            try:
                element.click()
                print(f"Elemento {by}='{value}' clickeado en {self.site_name}.")
                return True
            except Exception as e:
                print(f"Error al hacer clic en {by}='{value}': {e} en {self.site_name}")
                return False
        else:
            if not element:
                print(f"No se pudo hacer clic: Elemento {by}='{value}' no encontrado o no listo en {self.site_name}.")
            elif not element.is_displayed():
                print(f"No se pudo hacer clic: Elemento {by}='{value}' no visible en {self.site_name}.")
            elif not element.is_enabled():
                print(f"No se pudo hacer clic: Elemento {by}='{value}' no habilitado en {self.site_name}.")
            return False
        
    def scroll_down(self,driver):
        """A method for scrolling the page."""

        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:

                break

            last_height = new_height

    def scroll_slowly(self, driver):
        totalScrolledHeight = driver.execute_script("return window.pageYOffset + window.innerHeight")
        height = driver.execute_script("return document.body.scrollHeight")
        while totalScrolledHeight < height - 20:

            driver.execute_script('window.scrollBy(0,20)')
            totalScrolledHeight = driver.execute_script("return window.pageYOffset + window.innerHeight")
            height = driver.execute_script("return document.body.scrollHeight")

            