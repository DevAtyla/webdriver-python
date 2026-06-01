from selenium import webdriver
from selenium.webdriver.common.by import ByType
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebElement, WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as conditions
from utils.functions import timestamp_as_file_name, retry
from collections.abc import Callable
from loguru import logger
from typing import Self
import base64
from pathlib import Path
from enum import Enum
import time


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class ChromeDriver:
    def __init__(
        self,
        diver_executable: str,
        timeout_seconds: int,
        max_retry_attempts: int,
        sleep_seconds: float,
    ):
        self.diver_executable = diver_executable
        self.timeout_seconds = timeout_seconds
        self.sleep_seconds = sleep_seconds
        self.max_retry_attempts: int = max_retry_attempts
        self._driver: WebDriver | None = None
        self._is_driver_started = False

    def is_driver_started(self) -> bool:
        return self._is_driver_started

    def get_driver(self) -> WebDriver:
        if self._driver:
            return self._driver
        raise WebDriverNotInstantiatedException(
            "ChromeDriver ainda não foi instanciado."
        )

    def check_webdriver_started(self) -> None:
        if self.get_driver() is None or not self.is_driver_started():
            raise WebDriverNotStartedException("ChromeDriver ainda não foi iniciado.")

    def start_driver(self, options: tuple[str, ...] = tuple()) -> Self:
        if not self.is_driver_started():
            logger.debug("Iniciando ChromeDriver...")
            opt = webdriver.ChromeOptions()
            for o in options:
                opt.add_argument(o)
            self._driver = webdriver.Chrome(opt)
            self._is_driver_started = True
        return self

    def quit_driver(self):
        if self.is_driver_started():
            logger.debug("Fechando ChromeDriver...")
            self.get_driver().quit()
            self._is_driver_started = False

    def goto(self, url: str):
        self.check_webdriver_started()
        logger.debug(f"Navegando para {url}...")
        self.get_driver().get(url)

    def type(
        self,
        el_type: ByType,
        el_identifier: str,
        text: str,
        wait_for_element: bool = True,
    ) -> WebElement:
        self.check_webdriver_started()
        if wait_for_element:
            self.wait_for(
                el_type=el_type,
                el_identifier=el_identifier,
                until_func=conditions.element_to_be_clickable,
            )
        logger.debug(f"Digitando no elemento {el_identifier}...")
        element = self.get_driver().find_element(el_type, el_identifier)
        element.send_keys(text)
        return element

    def clear(
        self, el_type: ByType, el_identifier: str, wait_for_element: bool = True
    ) -> WebElement:
        self.check_webdriver_started()
        if wait_for_element:
            self.wait_for(
                el_type=el_type,
                el_identifier=el_identifier,
                until_func=conditions.presence_of_element_located,
            )
        logger.debug(f"Limpando o elemento {el_identifier}...")
        element = self.get_driver().find_element(el_type, el_identifier)
        element.clear()
        return element

    def type_and_enter(
        self,
        el_type: ByType,
        el_identifier: str,
        text: str,
        wait_for_element: bool = True,
    ) -> WebElement:
        element = self.type(el_type, el_identifier, text, wait_for_element)
        logger.debug("Apertando botão Enter...")
        element.send_keys(Keys.ENTER)
        return element

    def click(
        self,
        el_type: ByType,
        el_identifier: str,
        wait_for_element: bool = True,
        retry_on_exception: bool = True,
    ) -> WebElement:
        self.check_webdriver_started()
        logger.debug(f"Clicando no elemento {el_identifier}...")
        if wait_for_element:
            element = self.wait_for(
                el_type=el_type,
                el_identifier=el_identifier,
                until_func=conditions.element_to_be_clickable,
                retry_on_exception=retry_on_exception,
            )
        else:
            element = self.get_driver().find_element(el_type, el_identifier)
        if not retry_on_exception:
            element.click()
        else:

            def wait_and_click():
                time.sleep(self.sleep_seconds)
                el = self.wait_for(  # Refresh element reference
                    el_type=el_type,
                    el_identifier=el_identifier,
                    until_func=conditions.element_to_be_clickable,
                    retry_on_exception=False,
                )
                el.click()

            retry(func=wait_and_click, max_attempts=self.max_retry_attempts)
        return element

    def wait_for(
        self,
        el_type: ByType,
        el_identifier: str,
        until_func: Callable,
        retry_on_exception: bool = True,
    ) -> WebElement:
        self.check_webdriver_started()
        logger.debug(f"Aguardando elemento {el_identifier}...")
        if not retry_on_exception:
            return WebDriverWait(self.get_driver(), self.timeout_seconds).until(
                until_func((el_type, el_identifier))
            )
        else:

            def wait_and_retry():
                time.sleep(self.sleep_seconds)
                return WebDriverWait(self.get_driver(), self.timeout_seconds).until(
                    until_func((el_type, el_identifier))
                )

            return retry(func=wait_and_retry, max_attempts=self.max_retry_attempts)

    def scroll_element_into_view(self, element: WebElement) -> None:
        self.check_webdriver_started()
        logger.debug(f"Rolando até o elemento: {element}")
        self.get_driver().execute_script("arguments[0].scrollIntoView();", element)

    def find_element(
        self,
        el_type: ByType,
        el_identifier: str,
    ) -> WebElement:
        logger.debug(f"Procurando pelo elemento {el_identifier}...")
        return self.get_driver().find_element(by=el_type, value=el_identifier)

    def find_and_scroll_into_view(
        self,
        el_type: ByType,
        el_identifier: str,
    ):
        element = self.find_element(el_type, el_identifier)
        self.scroll_element_into_view(element)
        return element

    def implicitly_wait_for(self, seconds: float) -> None:
        logger.debug(
            f"Configurando driver para aguardar implicitamente por {seconds} segundo(s)..."
        )
        self.get_driver().implicitly_wait(seconds)

    def get_page_dimensions(self) -> dict[str, float]:
        """
        Retrieve the dimensions of the current web page.

        Executes a JavaScript snippet in the active WebDriver session to read
        the document body's scroll width and height, which reflect the total
        page size including content outside the visible viewport.

        Returns:
            dict[str, float]: A dictionary with keys ``'width'`` and ``'height'``,
            each holding the corresponding dimension in pixels.
        """
        return self.get_driver().execute_script("""
            return {
                width: document.body.scrollWidth,
                height: document.body.scrollHeight
            };
        """)

    @staticmethod
    def pixels_to_inches(pixels: float):
        """
        Convert a pixel measurement to inches using the standard screen resolution.

        Assumes 96 DPI (dots per inch), which is the default resolution used by
        most web browsers and operating systems for CSS and layout calculations.

        Args:
            pixels (float): The pixel value to convert.

        Returns:
            float: The equivalent measurement in inches.
        """
        return pixels / 96  # 96 DPI standard

    def page_to_pdf(
        self,
        file_path: str,
        print_background: bool = True,
        page_format: str = "A4",
        margin_top: int = 0,
        margin_bottom: int = 0,
        margin_left: int = 0,
        margin_right: int = 0,
        hide_elements: tuple[str, ...] = tuple(),
        paper_width: float = 8.5,
        paper_height: float = 11,
    ):
        """
        Renderiza a página atual do navegador como PDF e salva no caminho especificado.

        Utiliza o Chrome DevTools Protocol (CDP) para gerar o PDF, portanto é
        compatível apenas com o Chrome. Os diretórios intermediários do caminho
        de destino são criados automaticamente, caso não existam.

        Args:
            file_path (str): Caminho completo do arquivo PDF de destino (ex "output/relatorio.pdf").
            print_background (bool): Se True, inclui cores e imagens na renderização. Padrão: True.
            page_format (str): Formato do papel (ex: "A4", "Letter").
                Padrão: "A4".
            margin_top (int): Margem superior em pixels. Padrão: 0.
            margin_bottom (int): Margem inferior em pixels. Padrão: 0.
            margin_left (int): Margem esquerda em pixels. Padrão: 0.
            margin_right (int): Margem direita em pixels. Padrão: 0.
            hide_elements (tuple[str, ...]): Seletores CSS dos elementos que devem
                ser ocultados antes da geração do PDF (ex: (".navbar", "#footer")).
                Padrão: tupla vazia.

        Raises:
            WebDriverNotStartedException: Se o WebDriver não foi iniciado.
            IncompatibleBrowserException: Se o navegador em uso não for o Chrome.
            OSError: Se não for possível criar o diretório ou gravar o arquivo.
        """
        self.check_webdriver_started()

        p = Path(file_path)

        logger.debug(f"Imprimindo PDF da página no caminho: {file_path}")

        if not isinstance(self.get_driver(), webdriver.Chrome):
            raise IncompatibleBrowserException(
                "This function is only supported for Chrome"
            )

        # Create directory, if it does not exist
        p.parent.mkdir(parents=True, exist_ok=True)

        # Inject CSS to hide elements so they don't appear in the PDF
        for selector in hide_elements:
            self.get_driver().execute_script(
                f"document.querySelectorAll('{selector}').forEach((el) => el.style.display = 'none')"
            )

        # Use CDP to render page as PDF
        pdf_data = self.get_driver().execute_cdp_cmd(
            "Page.printToPDF",
            {
                "printBackground": print_background,
                "format": page_format,
                "marginTop": margin_top,
                "marginBottom": margin_bottom,
                "marginLeft": margin_left,
                "marginRight": margin_right,
                "paperWidth": paper_width,
                "paperHeight": paper_height,
            },
        )

        # Decode and save
        with open(p, "wb") as f:
            f.write(base64.b64decode(pdf_data["data"]))

    def save_screenshot_page(self, file_dir: str) -> None:
        self.check_webdriver_started()
        path = Path(f"{file_dir}/{timestamp_as_file_name('png')}")
        path.parent.mkdir(parents=True, exist_ok=True)
        result = self.get_driver().save_screenshot(path)
        if result:
            logger.debug(f"Captura de tela sava no caminho: {path}")
        else:
            logger.error(f"Falha ao salvar captura de tela no caminho: {path}")

    def enable_network_throttling(
        self,
        throttling_profile: NetworkThrottlingProfile,
    ):
        logger.debug(
            f"Habilitando limitação de rede com perfil: {throttling_profile.name}"
        )
        self.get_driver().execute_cdp_cmd("Network.enable", {})
        self.get_driver().execute_cdp_cmd(
            "Network.emulateNetworkConditions", throttling_profile.value
        )


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class NetworkThrottlingProfile(Enum):
    OFFLINE = {
        "offline": True,
        "downloadThroughput": 0,
        "uploadThroughput": 0,
        "latency": 0,
    }
    SLOW_2G = {
        "offline": False,
        "downloadThroughput": 250 * 1024 / 8,
        "uploadThroughput": 50 * 1024 / 8,
        "latency": 2000,
    }
    CELLULAR_2G = {
        "offline": False,
        "downloadThroughput": 450 * 1024 / 8,
        "uploadThroughput": 150 * 1024 / 8,
        "latency": 300,
    }
    CELLULAR_3G = {
        "offline": False,
        "downloadThroughput": 750 * 1024 / 8,
        "uploadThroughput": 250 * 1024 / 8,
        "latency": 100,
    }
    CELLULAR_4G = {
        "offline": False,
        "downloadThroughput": 4 * 1024 * 1024 / 8,
        "uploadThroughput": 3 * 1024 * 1024 / 8,
        "latency": 20,
    }


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class IncompatibleBrowserException(Exception):
    pass


class WebDriverException(Exception):
    pass


class WebDriverNotInstantiatedException(WebDriverException):
    pass


class WebDriverNotStartedException(WebDriverException):
    pass

