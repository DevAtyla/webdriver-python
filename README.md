# webdriver-python

Biblioteca Python que encapsula o **Selenium WebDriver** para automação de navegador web. Oferece uma API orientada a objetos com esperas explícitas, retentativas configuráveis, captura de tela, exportação de página para PDF via Chrome DevTools Protocol (CDP)[^1] e simulação de condições de rede.

O módulo principal é `main.py`, que define a classe `ChromeDriver` e tipos auxiliares. Funções utilitárias de apoio (`retry`, `timestamp_as_file_name`) ficam em `utils/functions.py`.


[^1]: Disponível apenas no Chrome.


## Pré-requisitos

- **Python 3.10+** (o código usa sintaxe moderna, por exemplo `dict[str, float]` e `Self`)
- **Google Chrome** instalado no sistema (ou outro driver. Consulte a [documentação oficial do Selenium](https://selenium-python.readthedocs.io/installation.html#drivers) para uma lista de drivers disponíveis)

## Como rodar localmente

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd webdriver-python
```

### 2. Criar ambiente virtual (recomendado)

```bash
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

Pacotes instalados:

| Pacote   | Uso                          |
|----------|------------------------------|
| `selenium` | Automação do navegador     |
| `loguru`   | Logs de depuração e erro   |

### 4. Usar como biblioteca

Não há bloco `if __name__ == "__main__"` em `main.py`. Importe `ChromeDriver` em outro script ou no REPL:

```python
from selenium.webdriver.common.by import By
from main import ChromeDriver, NetworkThrottlingProfile

driver = ChromeDriver(
    diver_executable="path/to/driver/binaries.exe",
    timeout_seconds=30,
    max_retry_attempts=3,
    sleep_seconds=0.5,
)

driver.start_driver(options=("--headless",))  # opções opcionais do Chrome
driver.goto("https://example.com")
driver.type(By.ID, "search", "teste")
driver.click(By.CSS_SELECTOR, "button.submit")
driver.save_screenshot_page("output/screenshots")
driver.page_to_pdf("output/relatorio.pdf", hide_elements=(".navbar",))
driver.enable_network_throttling(NetworkThrottlingProfile.CELLULAR_3G)
driver.quit_driver()
```

Execute o seu script a partir da raiz do projeto para que o pacote `utils` seja encontrado:

```bash
python seu_script.py
```

---

## Referência de objetos (`main.py`)

### Classes

#### `ChromeDriver`

Facade sobre `selenium.webdriver.Chrome` com validação de estado, esperas, retentativas e recursos via CDP.

**Construtor**

| Parâmetro            | Tipo    | Descrição |
|----------------------|---------|-----------|
| `diver_executable`   | `str`   | Caminho do executável do driver (armazenado em `self.diver_executable`; a instanciação atual em `start_driver` chama `webdriver.Chrome(opt)` sem passar esse caminho explicitamente). |
| `timeout_seconds`    | `int`   | Tempo máximo (segundos) para `WebDriverWait` em `wait_for` e fluxos que dependem dele. |
| `max_retry_attempts` | `int`   | Número máximo de tentativas usado por `retry()` em `click` e `wait_for` quando `retry_on_exception=True`. |
| `sleep_seconds`      | `float` | Pausa em segundos antes de cada nova tentativa em operações com retry. |

**Atributos internos**

| Atributo              | Tipo                    | Descrição |
|-----------------------|-------------------------|-----------|
| `_driver`             | `WebDriver \| None`     | Instância do Selenium após `start_driver`. |
| `_is_driver_started`  | `bool`                  | Indica se o navegador foi iniciado e ainda não foi encerrado com `quit_driver`. |

**Métodos**

| Método | Retorno | Descrição |
|--------|---------|-----------|
| `is_driver_started()` | `bool` | Retorna se o driver foi iniciado. |
| `get_driver()` | `WebDriver` | Retorna a instância ativa. Levanta `WebDriverNotInstantiatedException` se `_driver` for `None`. |
| `check_webdriver_started()` | `None` | Garante que o driver existe e está marcado como iniciado; senão levanta `WebDriverNotStartedException`. |
| `start_driver(options=())` | `Self` | Cria `ChromeOptions`, aplica cada string em `options` como argumento do Chrome, instancia `webdriver.Chrome` e marca como iniciado. Idempotente se já iniciado. |
| `quit_driver()` | `None` | Chama `quit()` no driver e redefine `_is_driver_started` para `False`. |
| `goto(url)` | `None` | Navega para `url` após validar o estado do driver. |
| `type(el_type, el_identifier, text, wait_for_element=True)` | `WebElement` | Opcionalmente aguarda elemento clicável, localiza, envia `text` com `send_keys`. |
| `clear(el_type, el_identifier, wait_for_element=True)` | `WebElement` | Opcionalmente aguarda presença do elemento, localiza e chama `clear()`. |
| `type_and_enter(el_type, el_identifier, text, wait_for_element=True)` | `WebElement` | Executa `type` e em seguida envia `Keys.ENTER`. |
| `click(el_type, el_identifier, wait_for_element=True, retry_on_exception=True)` | `WebElement` | Clica no elemento. Com espera e retry: dorme, re-aguarda clicável e clica via `retry`. Sem retry: clique direto após `wait_for` ou `find_element`. |
| `wait_for(el_type, el_identifier, until_func, retry_on_exception=True)` | `WebElement` | Espera explícita com `WebDriverWait` e condição Selenium (`until_func((el_type, el_identifier))`). Com retry, envolve a espera em `retry` com `sleep_seconds` entre tentativas. |
| `scroll_element_into_view(element)` | `None` | Executa `scrollIntoView()` via JavaScript no elemento informado. |
| `find_element(el_type, el_identifier)` | `WebElement` | `find_element` direto no driver (sem `check_webdriver_started` no código atual). |
| `find_and_scroll_into_view(el_type, el_identifier)` | `WebElement` | Combina `find_element` e `scroll_element_into_view`. |
| `implicitly_wait_for(seconds)` | `None` | Define `implicitly_wait` no driver. |
| `get_page_dimensions()` | `dict[str, float]` | Via JS, retorna `width` e `height` (`document.body.scrollWidth` / `scrollHeight`). |
| `pixels_to_inches(pixels)` *(estático)* | `float` | Converte pixels para polegadas assumindo **96 DPI**. |
| `page_to_pdf(file_path, print_background=True, page_format="A4", margin_top=0, margin_bottom=0, margin_left=0, margin_right=0, hide_elements=(), paper_width=8.5, paper_height=11)` | `None` | Gera PDF da página atual com CDP `Page.printToPDF` (somente Chrome). Cria diretórios pais, oculta seletores CSS informados, grava PDF em base64. Levanta `IncompatibleBrowserException` se o driver não for `webdriver.Chrome`. |
| `save_screenshot_page(file_dir)` | `None` | Salva PNG em `file_dir/<timestamp>.png` usando `timestamp_as_file_name` de `utils.functions`. Cria diretório se necessário. |
| `enable_network_throttling(throttling_profile)` | `None` | Habilita rede via CDP (`Network.enable` + `Network.emulateNetworkConditions` com o valor do enum). |

**Dependências externas usadas pela classe**

- Selenium: `webdriver`, `ByType`, `Keys`, `WebDriverWait`, `expected_conditions`
- `utils.functions`: `retry`, `timestamp_as_file_name`
- Biblioteca padrão: `base64`, `pathlib.Path`, `time`

---

### Enums

#### `NetworkThrottlingProfile`

Enum com perfis de rede para `ChromeDriver.enable_network_throttling`. Cada membro expõe um `dict` em `.value` aceito pelo CDP `Network.emulateNetworkConditions`.

| Membro        | Descrição resumida |
|---------------|--------------------|
| `OFFLINE`     | Modo offline (`offline: True`, throughput e latência zerados). |
| `SLOW_2G`     | 2G lento: download ~250 Kbps, upload ~50 Kbps, latência 2000 ms. |
| `CELLULAR_2G` | 2G: download ~450 Kbps, upload ~150 Kbps, latência 300 ms. |
| `CELLULAR_3G` | 3G: download ~750 Kbps, upload ~250 Kbps, latência 100 ms. |
| `CELLULAR_4G` | 4G: download ~4 Mbps, upload ~3 Mbps, latência 20 ms. |

Valores de throughput no código são calculados em **bytes por segundo** (`kbps * 1024 / 8`).

---

### Exceções

Hierarquia definida em `main.py`:

```
Exception
├── IncompatibleBrowserException
└── WebDriverException
    ├── WebDriverNotInstantiatedException
    └── WebDriverNotStartedException
```

| Exceção | Base | Quando é levantada |
|---------|------|---------------------|
| `IncompatibleBrowserException` | `Exception` | `page_to_pdf` quando o driver ativo não é instância de `webdriver.Chrome`. |
| `WebDriverException` | `Exception` | Classe base para erros de estado do wrapper (sem lógica extra). |
| `WebDriverNotInstantiatedException` | `WebDriverException` | `get_driver()` chamado sem instância criada (`_driver` é `None`). |
| `WebDriverNotStartedException` | `WebDriverException` | `check_webdriver_started()` quando o driver não está iniciado; também documentada em `page_to_pdf` para driver não iniciado. |

Mensagens padrão (português):

- `WebDriverNotInstantiatedException`: *"ChromeDriver ainda não foi instanciado."*
- `WebDriverNotStartedException`: *"ChromeDriver ainda não foi iniciado."*
- `IncompatibleBrowserException`: *"This function is only supported for Chrome"*

---

## Estrutura do projeto

```
webdriver-python/
├── main.py              # ChromeDriver, enums e exceções
├── utils/
│   └── functions.py     # retry, timestamp_as_file_name
├── requirements.txt
└── README.md
```

## Utilitários relacionados (`utils/functions.py`)

Não são classes, mas são usados por `ChromeDriver`:

| Função | Descrição |
|--------|-----------|
| `timestamp_as_file_name(file_extension)` | Nome de arquivo com hora atual (`HHMMSS.microsegundos.ext`). |
| `retry(func, max_attempts=1, catch=(Exception,))` | Executa callable sem argumentos; em falha dentro de `catch`, registra warning e repete até `max_attempts`. |
