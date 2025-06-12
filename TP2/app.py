# app.py
import os
import subprocess
import pandas as pd
from flask import Flask, request, render_template, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = "change_me" 

CSV_PATH = 'doctolib_results.csv'
SCRAPER_SCRIPT = 'test.py'   

def run_scraper():
    """Lance test.py pour (re)générer le CSV."""
    
    if os.path.exists(CSV_PATH):
        os.remove(CSV_PATH)
   
    try:
        subprocess.run(['python3', SCRAPER_SCRIPT], check=True)
    except subprocess.CalledProcessError as e:
        flash(f"Le scraper a échoué (code {e.returncode})", "error")
        return False
    return True

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        
        success = run_scraper()
        if not success:
            return redirect(url_for('index'))

       
        try:
            df = pd.read_csv(CSV_PATH)
        except Exception as e:
            flash(f"Impossible de lire le CSV : {e}", "error")
            return redirect(url_for('index'))

        
        specialty = request.form.get('specialty', '').strip().lower()
        assurance = request.form.get('assurance', '').strip().lower()
        consult   = request.form.get('consultation_type', '').strip().lower()
        addr_inc  = request.form.get('address_include', '').strip().lower()
        addr_exc  = request.form.get('address_exclude', '').strip().lower()
        min_price = request.form.get('min_price')
        max_price = request.form.get('max_price')

       
        if specialty:
            df = df[df['Spécialité'].str.lower().str.contains(specialty, na=False)]
        if assurance:
            df = df[df['Assurance'].str.lower().str.contains(assurance, na=False)]
        if consult:
            df = df[df['Type de consultation'].str.lower() == consult]
        if addr_inc:
            df = df[df['Adresse'].str.lower().str.contains(addr_inc, na=False)]
        if addr_exc:
            df = df[~df['Adresse'].str.lower().str.contains(addr_exc, na=False)]

        import re
        def extract_price(s):
            m = re.search(r'(\d+(?:\.\d+)?)\s*€', str(s))
            return float(m.group(1)) if m else None
        df['_price'] = df['Tarifs'].map(extract_price)

        if min_price:
            try:
                df = df[df['_price'] >= float(min_price)]
            except ValueError:
                flash("Prix minimum invalide", "error")
        if max_price:
            try:
                df = df[df['_price'] <= float(max_price)]
            except ValueError:
                flash("Prix maximum invalide", "error")

        df.drop(columns=['_price'], inplace=True)
        rows = df.to_dict(orient='records')
        count = len(df)
    else:
        rows = []
        count = 0

    return render_template('filter.html',
                           rows=rows,
                           count=count,
                           form=request.form)

if __name__ == '__main__':
    app.run(debug=True)
