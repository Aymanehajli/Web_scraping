from flask import Flask, render_template_string
import calendar
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

def scrape_doctolib(place="Montpellier"):
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    wait = WebDriverWait(driver, 10)

    driver.get("https://www.doctolib.fr/")
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
    place_input.send_keys(place)
    wait.until(
        EC.text_to_be_present_in_element_value(
            (By.CSS_SELECTOR, "input.searchbar-input.searchbar-place-input"), place
        )
    )
    search_btn = wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR, "button.searchbar-submit-button.dl-button-primary"
    )))
    search_btn.click()

   
    item_elems = wait.until(EC.presence_of_all_elements_located((
        By.CSS_SELECTOR, ".dl-text.dl-text-body.dl-text-bold.dl-text-s.dl-text-primary-110"
    )))
    names = [el.text for el in item_elems]

    
    spec_elems = wait.until(EC.presence_of_all_elements_located((
        By.CSS_SELECTOR, ".dl-doctor-card-speciality-title"
    )))
    specialties = [el.text for el in spec_elems]

    
    avail_elems = wait.until(EC.presence_of_all_elements_located((
        By.CSS_SELECTOR, ".availabilities-day"
    )))
    avail_strings = [el.text for el in avail_elems]

    driver.quit()

    
    avail_days = set()
    avail_details = []
    for s in avail_strings:
        if re.search(r"\d{1,2}:\d{2}", s):
            # extract day number
            for line in s.splitlines():
                parts = line.strip().split()
                if parts and parts[0].isdigit():
                    avail_days.add(int(parts[0]))
                    break
            avail_details.append(s)

    
    doctors = []
    for i, (name, spec) in enumerate(zip(names, specialties), start=1):
        doctors.append({"num": i, "name": name, "spec": spec})

    return doctors, avail_days, avail_details

@app.route('/')
def index():
    year, month = 2025, 6
    doctors, avail_days, avail_details = scrape_doctolib()
    cal = calendar.monthcalendar(year, month)
    week_header = ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"]

    template = '''
    <!doctype html>
    <html lang="fr">
      <head>
        <meta charset="utf-8">
        <title>Disponibilités Doctolib - {{ month_name }} {{ year }}</title>
        <style>
          body { font-family: sans-serif; padding: 20px; }
          table { border-collapse: collapse; width: 100%; max-width: 400px; margin-bottom: 30px; }
          th, td { border: 1px solid #ccc; text-align: center; padding: 8px; }
          .highlight { background-color: #a2d5f2; font-weight: bold; }
          .doctor-list { max-width: 600px; margin: auto; margin-bottom: 30px; }
          .doctor-list th, .doctor-list td { text-align: left; padding: 6px; }
          .avail-list { max-width: 600px; margin: auto; }
          .avail-list pre { white-space: pre-wrap; margin: 0; }
        </style>
      </head>
      <body>
        <h1>Disponibilités avec créneaux horaires pour {{ month_name }} {{ year }}</h1>
        <table>
          <tr>{% for d in week_header %}<th>{{ d }}</th>{% endfor %}</tr>
          {% for week in cal %}
          <tr>
            {% for day in week %}
              {% if day == 0 %}
                <td></td>
              {% elif day in avail_days %}
                <td class="highlight">{{ day }}</td>
              {% else %}
                <td>{{ day }}</td>
              {% endif %}
            {% endfor %}
          </tr>
          {% endfor %}
        </table>

        <h2>Jours et créneaux disponibles</h2>
        <ul class="avail-list">
          {% for s in avail_details %}
            <li><pre>{{ s }}</pre></li>
          {% endfor %}
        </ul>

        <h2>Liste des praticiens</h2>
        <table class="doctor-list">
          <tr><th>N°</th><th>Nom</th><th>Spécialité</th></tr>
          {% for doc in doctors %}
          <tr>
            <td>{{ doc.num }}</td>
            <td>{{ doc.name }}</td>
            <td>{{ doc.spec }}</td>
          </tr>
          {% endfor %}
        </table>
      </body>
    </html>
    '''

    return render_template_string(
        template,
        year=year,
        month_name=calendar.month_name[month],
        cal=cal,
        week_header=week_header,
        avail_days=avail_days,
        avail_details=avail_details,
        doctors=doctors
    )

if __name__ == '__main__':
    app.run(debug=True)
