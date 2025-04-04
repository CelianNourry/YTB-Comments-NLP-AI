from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

# Demande à l'utilisateur l'URL de la vidéo YouTube à scraper
VIDEO_URL = input("Entrez l'URL de la vidéo YouTube à scraper : ")

if VIDEO_URL[:32] != "https://www.youtube.com/watch?v=" or VIDEO_URL == "":
    raise ValueError("L'URL doit être une URL de vidéo YouTube valide.")

# Configurer Selenium avec Chrome
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Lancer Chrome
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get(VIDEO_URL)
time.sleep(5)  # Laisser le temps à la page de charger le contenu dynamique

# Faire défiler la page pour charger tous les commentaies
SCROLL_PAUSE_TIME = 2
last_height = driver.execute_script("return document.documentElement.scrollHeight")

for _ in range(10): # On tente plusieurs scrolls pour charger les avis
    driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
    time.sleep(SCROLL_PAUSE_TIME)
    new_height = driver.execute_script("return document.documentElement.scrollHeight")
    if new_height == last_height: # Si aucun nouveau contenu n'est chargé, arrêter
        break
    last_height = new_height

# Attendre le chargement des commentaires
WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ytd-comment-thread-renderer")))

# Extraire les commentaires
comments = []
for comment in driver.find_elements(By.CSS_SELECTOR, "#content-text"):
    comments.append(comment.text)

# Fermer le navigateur
driver.quit()

# Sauvegarder les commentaires dans un fichier texte
filename = "./results/" + re.sub(r'[^a-zA-Z0-9]', '_', VIDEO_URL) + ".txt"
with open(filename, "w", encoding="utf-8") as f:
    for comment in comments:
        f.write(comment + "\n\n")

print(f"Scraping terminé, {len(comments)} commentaires enregistrés dans {filename}")
