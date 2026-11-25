# Pruebas Automatizadas — Urban Routes (Sprint 9)

## Descripción del proyecto

Suite de pruebas automatizadas de extremo a extremo (E2E) para el flujo de solicitud de taxi en **Urban Routes**. Cada caso de prueba se ejecuta de forma independiente en una sesión limpia del navegador, validando desde la configuración de direcciones y selección de tarifa **Comfort** hasta la confirmación del número de teléfono, registro de tarjeta de crédito, envío de mensaje al conductor, solicitud de manta y pañuelos, agregado de helados, apertura del modal de búsqueda y espera de la información del conductor asignado.

## Tecnologías y técnicas utilizadas

* **Lenguaje y entorno:** Python (ejecutado en entorno virtual `.venv` con PyCharm)
* **Automatización web:** Selenium WebDriver (`Options`, `WebDriverWait`, `expected_conditions`, `Keys`, `By`) y captura de logs de rendimiento (`goog:loggingPrefs`) / CDP (`Network.getResponseBody`) para interceptar el código de confirmación telefónica (`retrieve_phone_code`)
* **Framework de pruebas:** `pytest` con `setup_method()` y `teardown_method()` para aislar cada prueba en una instancia limpia del navegador
* **Patrón de diseño:** Page Object Model (POM), separando los datos de prueba en `data.py`, los localizadores y métodos de interacción en `UrbanRoutesPage`, y los 9 escenarios de prueba en `TestUrbanRoutes`
* **Estrategias de localización:** Uso combinado de `By.ID`, `By.CLASS_NAME`, `By.XPATH` y `By.CSS_SELECTOR`

## Cómo ejecutar las pruebas

### 1. Activar el entorno virtual e instalar dependencias

Desde la raíz del proyecto en Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install selenium pytest