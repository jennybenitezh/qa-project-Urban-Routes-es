import json
import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import data


def retrieve_phone_code(driver) -> str:
    """Intercepta y devuelve el código de confirmación desde los logs de rendimiento."""
    for _ in range(15):
        try:
            logs = driver.get_log("performance")
            for entry in reversed(logs):
                raw_msg = entry.get("message", "")
                if "api/v1/number" not in raw_msg:
                    continue

                outer = json.loads(raw_msg)
                params = outer.get("message", {}).get("params", {})

                body_str = params.get("response", {}).get("body", "")
                request_id = params.get("requestId")

                if not body_str and request_id:
                    try:
                        resp = driver.execute_cdp_cmd(
                            "Network.getResponseBody", {"requestId": request_id}
                        )
                        body_str = resp.get("body", "")
                    except Exception:
                        pass

                if body_str:
                    try:
                        data_body = json.loads(body_str)
                        if isinstance(data_body, dict):
                            for key in ("code", "sms_code", "confirmCode"):
                                if key in data_body:
                                    digits = "".join(c for c in str(data_body[key]) if c.isdigit())
                                    if digits:
                                        return digits
                    except ValueError:
                        pass

                    digits = "".join(c for c in str(body_str) if c.isdigit())
                    if digits:
                        return digits
        except Exception:
            pass
        time.sleep(1)

    raise Exception("No se encontró el código de confirmación del teléfono.")


class UrbanRoutesPage:
    # --- Localizadores (By.ID, By.CLASS_NAME, By.XPATH, By.CSS_SELECTOR) ---
    FROM_INPUT = (By.ID, "from")
    TO_INPUT = (By.ID, "to")
    PHONE_INPUT = (By.ID, "phone")
    PHONE_CODE_INPUT = (By.ID, "code")
    COMMENT_INPUT = (By.ID, "comment")

    CALL_TAXI_BUTTON = (By.CLASS_NAME, "button")
    PHONE_NUMBER_FIELD = (By.CLASS_NAME, "np-button")
    ADD_CARD_OPTION = (By.CLASS_NAME, "pp-plus")
    ICE_CREAM_VALUE = (By.CLASS_NAME, "counter-value")
    CAR_SEARCH_MODAL = (By.CLASS_NAME, "order-body")

    COMFORT_TARIFF_CARD = (By.XPATH, "//div[@class='tcard-title' and text()='Comfort']/..")
    PHONE_CONFIRM_BUTTON = (By.XPATH, "//button[contains(text(), 'Confirmar')]")
    CARD_LINK_BUTTON = (By.XPATH, "//button[contains(text(), 'Agregar') or contains(text(), 'Link')]")
    REQUIREMENTS_HEADER = (By.XPATH, "//*[contains(text(), 'Requisitos del pedido')]")

    CALL_TAXI_ROUND_BUTTON = (By.CSS_SELECTOR, "button.button.round")
    TARIFF_PICKER = (By.CSS_SELECTOR, ".tariff-picker.shown")
    PHONE_NEXT_BUTTON = (By.CSS_SELECTOR, ".full")
    PAYMENT_METHOD_FIELD = (By.CSS_SELECTOR, ".pp-button")
    CARD_NUMBER_INPUT = (By.CSS_SELECTOR, ".card-number input")
    CARD_CVV_INPUT = (By.CSS_SELECTOR, ".card-second-row input")
    CLOSE_PAYMENT_MODAL_BUTTON = (By.CSS_SELECTOR, ".payment-picker .close-button")
    BLANKET_SWITCH = (By.CSS_SELECTOR, ".switch input[type='checkbox'], input.switch-input")
    ICE_CREAM_PLUS = (By.CSS_SELECTOR, ".counter-plus")
    SEARCH_TAXI_BUTTON = (By.CSS_SELECTOR, ".smart-button")
    DRIVER_INFO_HEADER = (By.CSS_SELECTOR, ".order-header-title")

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 15)

    def open_home(self):
        self.driver.get(data.urban_routes_url)

    def set_route(self, from_address: str, to_address: str):
        from_el = self.wait.until(EC.visibility_of_element_located(self.FROM_INPUT))
        from_el.clear()
        from_el.send_keys(from_address)

        to_el = self.wait.until(EC.visibility_of_element_located(self.TO_INPUT))
        to_el.clear()
        to_el.send_keys(to_address)

    def click_call_taxi(self):
        self.wait.until(
            lambda d: len(d.find_elements(*self.TARIFF_PICKER)) > 0
            or any(
                btn.is_displayed() and btn.is_enabled()
                for btn in d.find_elements(*self.CALL_TAXI_ROUND_BUTTON)
            )
        )
        if len(self.driver.find_elements(*self.TARIFF_PICKER)) == 0:
            for btn in self.driver.find_elements(*self.CALL_TAXI_ROUND_BUTTON):
                if btn.is_displayed() and btn.is_enabled():
                    btn.click()
                    break

    def select_comfort_tariff(self):
        comfort = self.wait.until(EC.element_to_be_clickable(self.COMFORT_TARIFF_CARD))
        comfort.click()

    def prepare_comfort_screen(self):
        self.open_home()
        self.set_route(data.address_from, data.address_to)
        self.click_call_taxi()
        self.select_comfort_tariff()

    def open_requirements_if_needed(self):
        if len(self.driver.find_elements(*self.BLANKET_SWITCH)) == 0:
            headers = self.driver.find_elements(*self.REQUIREMENTS_HEADER)
            for el in headers:
                if el.is_displayed():
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
                    self.driver.execute_script("arguments[0].click();", el)
                    break

    def fill_phone_number(self, phone_number: str):
        self.wait.until(EC.element_to_be_clickable(self.PHONE_NUMBER_FIELD)).click()
        phone_input = self.wait.until(EC.visibility_of_element_located(self.PHONE_INPUT))
        phone_input.clear()
        phone_input.send_keys(phone_number)

        # Solicitar el código en la app antes de interceptarlo
        self.wait.until(EC.element_to_be_clickable(self.PHONE_NEXT_BUTTON)).click()

        code = retrieve_phone_code(self.driver)
        code_input = self.wait.until(EC.visibility_of_element_located(self.PHONE_CODE_INPUT))
        code_input.send_keys(code)
        self.wait.until(EC.element_to_be_clickable(self.PHONE_CONFIRM_BUTTON)).click()

    def add_credit_card(self, card_number: str, cvv: str):
        self.wait.until(EC.element_to_be_clickable(self.PAYMENT_METHOD_FIELD)).click()
        self.wait.until(EC.element_to_be_clickable(self.ADD_CARD_OPTION)).click()

        card_input = self.wait.until(EC.visibility_of_element_located(self.CARD_NUMBER_INPUT))
        card_input.clear()
        card_input.send_keys(card_number)

        cvv_input = self.wait.until(EC.visibility_of_element_located(self.CARD_CVV_INPUT))
        cvv_input.clear()
        cvv_input.send_keys(cvv)
        cvv_input.send_keys(Keys.TAB)

        link_btn = self.wait.until(EC.element_to_be_clickable(self.CARD_LINK_BUTTON))
        link_btn.click()

        try:
            close_btn = WebDriverWait(self.driver, 4).until(
                EC.element_to_be_clickable(self.CLOSE_PAYMENT_MODAL_BUTTON)
            )
            close_btn.click()
        except TimeoutException:
            pass

    def set_driver_comment(self, comment: str):
        comment_field = self.wait.until(EC.visibility_of_element_located(self.COMMENT_INPUT))
        comment_field.clear()
        comment_field.send_keys(comment)

    def request_blanket_and_tissues(self):
        self.open_requirements_if_needed()
        switch_el = self.wait.until(EC.presence_of_element_located(self.BLANKET_SWITCH))
        if not switch_el.is_selected():
            self.driver.execute_script("arguments[0].click();", switch_el)

    def add_ice_creams(self, count: int):
        self.open_requirements_if_needed()
        plus_buttons = self.wait.until(EC.presence_of_all_elements_located(self.ICE_CREAM_PLUS))
        ice_cream_plus = plus_buttons[0]
        for _ in range(count):
            self.driver.execute_script("arguments[0].click();", ice_cream_plus)

    def start_taxi_search(self):
        search_btn = self.wait.until(EC.element_to_be_clickable(self.SEARCH_TAXI_BUTTON))
        search_btn.click()
        self.wait.until(EC.visibility_of_element_located(self.CAR_SEARCH_MODAL))

    def wait_for_driver_info(self, timeout: int = 60):
        long_wait = WebDriverWait(self.driver, timeout)
        long_wait.until(
            lambda d: d.find_element(*self.DRIVER_INFO_HEADER).text.strip() != ""
            and "Buscando" not in d.find_element(*self.DRIVER_INFO_HEADER).text
        )
        return self.driver.find_element(*self.DRIVER_INFO_HEADER).text


class TestUrbanRoutes:
    def setup_method(self):
        options = Options()
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(5)

    def teardown_method(self):
        if self.driver:
            self.driver.quit()

    def test_1_set_route(self):
        page = UrbanRoutesPage(self.driver)
        page.open_home()
        page.set_route(data.address_from, data.address_to)
        assert self.driver.find_element(*page.FROM_INPUT).get_attribute("value") == data.address_from
        assert self.driver.find_element(*page.TO_INPUT).get_attribute("value") == data.address_to

    def test_2_select_comfort_tariff(self):
        page = UrbanRoutesPage(self.driver)
        page.open_home()
        page.set_route(data.address_from, data.address_to)
        page.click_call_taxi()
        page.select_comfort_tariff()
        parent = self.driver.find_element(*page.COMFORT_TARIFF_CARD)
        assert "active" in parent.get_attribute("class")

    def test_3_fill_phone_number(self):
        page = UrbanRoutesPage(self.driver)
        page.prepare_comfort_screen()
        page.fill_phone_number(data.phone_number)
        assert data.phone_number in self.driver.find_element(*page.PHONE_NUMBER_FIELD).text

    def test_4_add_credit_card(self):
        page = UrbanRoutesPage(self.driver)
        page.prepare_comfort_screen()
        page.add_credit_card(data.card_number, data.card_code)
        assert "Tarjeta" in self.driver.find_element(*page.PAYMENT_METHOD_FIELD).text

    def test_5_set_driver_comment(self):
        page = UrbanRoutesPage(self.driver)
        page.prepare_comfort_screen()
        page.set_driver_comment(data.message_for_driver)
        assert self.driver.find_element(*page.COMMENT_INPUT).get_attribute("value") == data.message_for_driver

    def test_6_request_blanket_and_tissues(self):
        page = UrbanRoutesPage(self.driver)
        page.prepare_comfort_screen()
        page.request_blanket_and_tissues()
        assert self.driver.find_element(*page.BLANKET_SWITCH).is_selected()

    def test_7_add_ice_creams(self):
        page = UrbanRoutesPage(self.driver)
        page.prepare_comfort_screen()
        page.add_ice_creams(2)
        counter_text = self.driver.find_element(*page.ICE_CREAM_VALUE).text
        assert counter_text == "2"

    def test_8_search_taxi_modal(self):
        page = UrbanRoutesPage(self.driver)
        page.prepare_comfort_screen()
        page.fill_phone_number(data.phone_number)
        page.start_taxi_search()
        assert self.driver.find_element(*page.CAR_SEARCH_MODAL).is_displayed()

    def test_9_wait_for_driver_info(self):
        page = UrbanRoutesPage(self.driver)
        page.prepare_comfort_screen()
        page.fill_phone_number(data.phone_number)
        page.start_taxi_search()
        header_text = page.wait_for_driver_info(timeout=60)
        assert len(header_text) > 0