import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

try:
    from config import CHROME_DRIVER_EXECUTABLE_PATH, CHROME_BROWSER_PATH
except ImportError:
    print("WARN: config.py no encontrado o paths no definidos. Usando valores por defecto o esperando Selenium Manager.")
    CHROME_DRIVER_EXECUTABLE_PATH = None
    CHROME_BROWSER_PATH = None


class WebDriverManager:
    def __init__(self, driver_executable_path=CHROME_DRIVER_EXECUTABLE_PATH, browser_path=CHROME_BROWSER_PATH):
        self.driver_executable_path = driver_executable_path
        self.browser_path = browser_path
        self.driver = None

    def start_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")

        if self.browser_path and os.path.exists(self.browser_path):
            chrome_options.binary_location = self.browser_path
        elif self.browser_path:
            print(f"WARN: Chrome browser path '{self.browser_path}' no encontrado.")


        service_args = []

        if self.driver_executable_path and os.path.exists(self.driver_executable_path):
            service = Service(executable_path=self.driver_executable_path, service_args=service_args)
            print(f"Usando chromedriver desde: {self.driver_executable_path}")
        else:
            if self.driver_executable_path: # Si se proporcionó pero no existe
                 print(f"WARN: chromedriver.exe path '{self.driver_executable_path}' no encontrado.")
            print("INFO: Intentando usar Selenium Manager para chromedriver.")
            service = Service(service_args=service_args)

        try:
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("WebDriver iniciado correctamente.")
            return self.driver
        except Exception as e:
            print(f"Error al iniciar WebDriver: {e}")
            print("Asegúrate de que ChromeDriver esté en el PATH o que CHROME_DRIVER_EXECUTABLE_PATH sea correcto y compatible con tu versión de Chrome.")
            if self.driver_executable_path:
                print(f"Path de chromedriver intentado: {self.driver_executable_path}")
            if self.browser_path:
                print(f"Path del navegador Chrome: {self.browser_path}")
            return None

    def stop_driver(self):
        if self.driver:
            self.driver.quit()
            print("WebDriver cerrado.")
            self.driver = None

    def __enter__(self):
        return self.start_driver()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_driver()