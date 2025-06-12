import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException
)

# 1) Setup webdriver and wait
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, 30)

# 2) Go to Doctolib and reject cookies
driver.get("https://www.doctolib.fr/")
try:
    btn = wait.until(EC.element_to_be_clickable((By.ID, "didomi-notice-disagree-button")))
    btn.click()
    wait.until(EC.invisibility_of_element_located((By.ID, "didomi-notice-disagree-button")))
except:
    pass

# 3) Enter “Montpellier” and search
place = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.searchbar-input.searchbar-place-input")))
place.clear()
place.send_keys("Montpellier")
wait.until(EC.text_to_be_present_in_element_value(
    (By.CSS_SELECTOR, "input.searchbar-input.searchbar-place-input"),
    "Montpellier"
))
search_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.searchbar-submit-button.dl-button-primary")))
search_btn.click()

# 4) Grab cards
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test='total-number-of-results']")))
cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".w-full")))

# 5) Prepare CSV
fieldnames = ["Nom", "Spécialité", "Adresse", "Assurance", "Disponibilités", "Type de consultation", "Tarifs"]
rows = []
seen = set()
driver.implicitly_wait(1)

# 6) Loop, limit to 10 entries
for card in cards:
    if len(rows) >= 10:
        break

    # — Nom
    try:
        title = card.find_element(By.CSS_SELECTOR, ".dl-text-bold.dl-text-primary-110").text.strip()
    except:
        continue

    # — Spécialité
    try:
        speciality = card.find_element(By.CSS_SELECTOR, ".dl-doctor-card-speciality-title").text.strip()
    except:
        speciality = ""

    key = (title, speciality)
    if key in seen:
        continue
    seen.add(key)

    # — Adresse
    try:
        addr_div = card.find_element(By.CSS_SELECTOR, "div.mt-8.gap-8.flex")
        parts = addr_div.find_elements(By.CSS_SELECTOR, "p.dl-text-neutral-130")
        address = ", ".join(p.text.strip() for p in parts if p.text.strip())
    except:
        address = ""

    # — Assurance
    try:
        assurance = card.find_element(
            By.CSS_SELECTOR,
            "div.mt-8.gap-8.flex > div.flex.flex-wrap.gap-x-4 > p.dl-text-neutral-130"
        ).text.strip()
    except NoSuchElementException:
        assurance = ""

    # — Disponibilités
    try:
        slots = card.find_elements(By.CSS_SELECTOR, ".availabilities-slot-desktop")
        texts = [s.text.strip() for s in slots if s.text.strip()]
        if not texts:
            fallback = card.find_elements(
                By.CSS_SELECTOR,
                ".dl-text-left.dl-text-primary-110, .dl-text-left.dl-text-neutral-130"
            )
            texts = [f.text.strip() for f in fallback if f.text.strip()]
        availabilities = " | ".join(texts)
    except:
        availabilities = ""

    # — Type de consultation
    try:
        card.find_element(By.XPATH, ".//svg//path[contains(@d, 'M10.25 4.625v6.75c0 .633')]")
        consultation_type = "Visio"
    except NoSuchElementException:
        consultation_type = "Présentiel"

    # — Tarifs
    tarif_output = "Indisponible"
    try:
        link = card.find_element(By.CSS_SELECTOR, "a.dl-p-doctor-result-link")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.dl-p-doctor-result-link")))
        try:
            link.click()
        except ElementClickInterceptedException:
            time.sleep(1)
            driver.execute_script("arguments[0].click();", link)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.dl-profile-text")))
        fee_divs = driver.find_elements(By.CSS_SELECTOR, "div.dl-profile-fee")
        if fee_divs:
            tarifs = [
                f"{fee.find_element(By.CSS_SELECTOR, '.dl-profile-fee-name').text.strip()}: "
                f"{fee.find_element(By.CSS_SELECTOR, '.dl-profile-fee-tag').text.strip()}"
                for fee in fee_divs
            ]
            valid = [t for t in tarifs if "In" in t]
            if valid:
                tarif_output = " | ".join(valid)

        driver.back()
        time.sleep(1)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".w-full")))
    except:
        try:
            driver.back()
            time.sleep(1)
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".w-full")))
        except:
            pass

    rows.append({
        "Nom": title,
        "Spécialité": speciality,
        "Adresse": address,
        "Assurance": assurance,
        "Disponibilités": availabilities,
        "Type de consultation": consultation_type,
        "Tarifs": tarif_output
    })

# 7) Write CSV
with open("doctolib_results.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to doctolib_results.csv")

time.sleep(2)
driver.quit()
