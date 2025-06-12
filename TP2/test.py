from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
import time
import re

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.get("https://www.doctolib.fr/")
wait = WebDriverWait(driver, 30)

try:
    reject_btn = wait.until(
        EC.element_to_be_clickable((By.ID, "didomi-notice-disagree-button"))
    )
    reject_btn.click()
    wait.until(EC.invisibility_of_element_located((By.ID, "didomi-notice-disagree-button")))
except:
    pass

place_input = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "input.searchbar-input.searchbar-place-input"))
)
place_input.clear()
place_input.send_keys("Montpellier")

wait.until(
    EC.text_to_be_present_in_element_value(
        (By.CSS_SELECTOR, "input.searchbar-input.searchbar-place-input"),
        "Montpellier"
    )
)

search_btn = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.searchbar-submit-button.dl-button-primary"))
)
search_btn.click()

total_results = wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test='total-number-of-results']"))
)
print("Found results count:", total_results.text)

cards = wait.until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".dl-card-content"))
)
print(f"Nombre de cartes trouvées : {len(cards)}")
driver.implicitly_wait(1)
seen = set()


for idx, card in enumerate(cards, start=1):
    try:

        title = card.find_element(
            By.CSS_SELECTOR,
            ".dl-text.dl-text-body.dl-text-bold.dl-text-s.dl-text-primary-110"
        ).text.strip()
    except:
        title = "❌ Nom non trouvé"

    try:
        speciality = card.find_element(
            By.CSS_SELECTOR,
            ".dl-text.dl-text-body.dl-text-regular.dl-text-s.dl-text-neutral-130.dl-doctor-card-speciality-title"
        ).text.strip()
    except:
        speciality = "❌ Spécialité non trouvée"

    if title == "❌ Nom non trouvé" and speciality == "❌ Spécialité non trouvée":
        continue

    try:
       

        avail_elements = card.find_elements(
            By.CSS_SELECTOR,
            ".Tappable-inactive.availabilities-slot.availabilities-slot-desktop"
        )
        avail_texts = [a.text.strip() for a in avail_elements if a.text.strip()]

        if avail_texts:
            availabilities = " | ".join(avail_texts)
        else:
            nextinfo_elements = card.find_elements(
                By.CSS_SELECTOR,
                ".dl-text.dl-text-body.dl-text-regular.dl-text-s.dl-text-left.dl-text-primary-110"
            )
            nextinfo_texts = [e.text.strip() for e in nextinfo_elements if e.text.strip()]

            if nextinfo_texts:
                availabilities = " | ".join(nextinfo_texts)
            
            else:
                next130 = card.find_elements(
                    By.CSS_SELECTOR,
                    ".dl-text.dl-text-body.dl-text-regular.dl-text-s.dl-text-left.dl-text-neutral-130"
                )
                texts130 = [e.text.strip() for e in next130 if e.text.strip()]

                if texts130:
                    availabilities = " | ".join(texts130)
            
                else:
                     availabilities = "❌ Aucune disponibilité"

    except Exception as e:
        availabilities = f"❌ Erreur lors de l'extraction des disponibilités ({e})"

    unique_key = (title, speciality)
    if unique_key not in seen:
        seen.add(unique_key)
        print(f"{len(seen)}. {title} — {speciality}")
        print(f"    ➤ Disponibilités : {availabilities}\n")

time.sleep(200)
driver.quit()
