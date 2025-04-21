from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from nltk.tokenize import sent_tokenize, word_tokenize

from sklearn.feature_extraction.text import CountVectorizer

import csv
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords

import time
import re

from dataclasses import dataclass

@dataclass
class Comment:
    text: str
    polarity: int

POSITIF = ["excellent", "merci", "interessant", "banger", "masterclass", "amour", "ambition", "travaille", "soutien", "passionnant", "instructif", "fun", "drole", "rigolo", "bravo", "felicitation", "cool", "bien", "super", "genial", "geniaux", "mature", "top", "parfait", "preferee", "superbe", "extra", "fantastique", "magnifique", "exceptionnel", "formidable", "brillant", "epatant", "sensationnel", "merveilleux", "extraordinaire", "impressionnant", "fascinant", "captivant", "eblouissant", "etonnant", "surprenant", "epoustouflant", "incroyable", "inattendu", ":)", "xd", ":D"]
POSITIVE_VERBS = ["aim", "ador", "approuv", "appreci", "estim", "respecte", "souten", "soutiens", "encourag", "felicit", "remerci", "applaudi", "celebr", "valoris", "honor", "lik", "kiff", "abonn", "partag"]
NEGATIF = ["nul", "bof", "grotesque", "grave", "peur", "grossier", "pourri", "ennuyant" , "ennuyeu", "boring", "flop", "desastre", "insoutenable", "mauvais", "immature", "affreux", "horrible",  "decevant", "catastroph", "lamentable", "ridicule", "insupportable", "abominable", "atroce", "epouvantable", "affreu", "degoutant", "insignifiant", "mediocre", "pitoyable", "terrible", "deplorable", "pathetique", "minable", "indigne", "infame", "ignoble", "revoltant", "scandaleux", "choquant", "abject", "detestable", "haissable", "putaclic", "malheur", "triste", ":(", ":'("]
NEGATIVE_VERBS = ["detest", "desapprouv", "hai"]
CURSE_WORDS = ["sale", "chier", "merde", "bete", "putain", "connard", "connasse", "connerie", "conneries", "con", "connes", "salope", "enfoire", "batard", "foutre", "gueul", "marre", "salete", "complot", "complotiste", "wok", "idiot", "imbecile", "abruti"]
NEGATION = ["pas", "jamais", "ni", "nul", "guere", "nullement", "aucunement", "grave"]
INTENSIFIER = ["plus", "bon", "vrai", "bien", "tres", "trop", "vraiment", "tellement", "si", "hyper", "super", "ultra", "absolument", "totalement", "completement", "parfaitement", "entierement", "absoluement", "terriblement", "extremement", "incroyablement", "infiniment", "extraordinairement", "exceptionnellement"]

# Fonction pour effacer le terminal
def clear_terminal():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

# Fonction qui scrap les commentaires d'une vidéo YouTube, renvoie une liste de commentaires
def scraping(urls):
    TIMEOUT = 4
    MAX_WAIT = 10
    comments = []

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    for url in urls:
        print(f"Scraping de : {url} en cours ...")
        driver.get(url)
        print("Chargement de la page ...")
        time.sleep(5)
        print("Chargement de la page terminé.")

        start_time = time.time()
        last_height = driver.execute_script("return document.documentElement.scrollHeight")

        print("Scroll de la page ...")
        while True:
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.documentElement.scrollHeight")

            if new_height == last_height:
                if time.time() - start_time > TIMEOUT:
                    break
            else:
                start_time = time.time()
                last_height = new_height

            if time.time() - start_time > MAX_WAIT:
                print("Scroll stoppé car il a prit trop de temps.")
                break

        try:
            WebDriverWait(driver, TIMEOUT).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#content-text")))
            i = 0
            for comment in driver.find_elements(By.CSS_SELECTOR, "#content-text"):
                i+= 1
                comments.append(comment.text)
            print(" Commentaires scrapés : ", i)
        except:
            print(f"Impossible d'extraire les commentaires de {url}")
            continue

    driver.quit()
    return comments

import re
from nltk.tokenize import sent_tokenize, word_tokenize

# Nettoie une liste de commentaires. Renvoie une liste des commentaires nettoyés
def clean(comments):
    cleanedComments = []
    for comment in comments:
        comment = re.sub(r"\s+", " ", comment).strip().lower()
        comment = re.sub(r'\d+', '', comment)
        comment = re.sub(r'[àáâäãå]', 'a', comment)
        comment = re.sub(r'[èéêë]', 'e', comment)
        comment = re.sub(r'[ìíîï]', 'i', comment)
        comment = re.sub(r'[òóôöõ]', 'o', comment)
        comment = re.sub(r'[ùúûü]', 'u', comment)
        comment = re.sub(r'ç', 'c', comment)
        comment = re.sub(r'ñ', 'n', comment)

        cleanedComments.append(comment)

    return cleanedComments

def annotate(comments):
    annotated_comments = []

    # Fonction pour vérifier si l'argument word commence par un des mots de la liste word_list
    def starts_with(word, word_list):
        return any(word.startswith(w) for w in word_list)

    for comment in comments:
        polarity = 0
        sentences = sent_tokenize(comment)

        for sentence in sentences:
            words = word_tokenize(sentence)

            for j in range(len(words)):
                word = words[j]

                if starts_with(word, POSITIF):
                    if j > 0 and starts_with(words[j - 1], NEGATION):
                        polarity -= 1
                    elif j > 1 and starts_with(words[j - 1], INTENSIFIER) and starts_with(words[j - 2], NEGATION):
                        polarity -= 2
                    elif j > 0 and starts_with(words[j - 1], INTENSIFIER):
                        polarity += 3
                    else:
                        polarity += 1

                elif starts_with(word, NEGATIF):
                    if j > 0 and starts_with(words[j - 1], NEGATION):
                        polarity += 1
                    elif j > 1 and starts_with(words[j - 1], INTENSIFIER) and starts_with(words[j - 2], NEGATION):
                        polarity += 2
                    elif j > 0 and starts_with(words[j - 1], INTENSIFIER):
                        polarity -= 3
                    else:
                        polarity -= 1

                elif starts_with(word, POSITIVE_VERBS):
                    if j < len(words) - 1 and starts_with(words[j + 1], NEGATION):
                        polarity -= 1
                    else:
                        polarity += 1

                elif starts_with(word, NEGATIVE_VERBS):
                    if j < len(words) - 1 and starts_with(words[j + 1], NEGATION):
                        polarity += 1
                    else:
                        polarity -= 1

                elif word in CURSE_WORDS:
                    polarity -= 5

        if polarity > 0:
            annotated_comments.append(Comment(text = comment, polarity = 0)) # 0 = positif
        elif polarity < 0:
            annotated_comments.append(Comment(text = comment, polarity = 1)) # 1 = negatif
        else: #neutre
            continue

    print(f"{len(annotated_comments)}/{len(comments)} commentaires retenus.")
    positive_comments_count = sum(1 for comment in annotated_comments if comment.polarity == 0)
    print(f"Commentaires positifs : {positive_comments_count}")
    negative_comments_count = sum(1 for comment in annotated_comments if comment.polarity == 1)
    print(f"Commentaires négatifs : {negative_comments_count}")

    return annotated_comments


def main():
    # Listes de vidéos YouTube à scraper
    urls = [
        "https://www.youtube.com/watch?v=s4UjplzkGtk&ab_channel=PlotTime",
        "https://www.youtube.com/watch?v=AjtEcUPnZlc&ab_channel=PaulHapman",
        "https://www.youtube.com/watch?v=vfBx-M-D5u8&ab_channel=LeRadisIrradi%C3%A9%2FEric.K",
        "https://www.youtube.com/watch?v=nhPgQgHJ7-8&ab_channel=ACIDRAMA",
        "https://www.youtube.com/watch?v=Zk1cDp0gJbY&ab_channel=CatoMinor",
        "https://www.youtube.com/watch?v=Zk1cDp0gJbY&ab_channel=FilmsActu",
        "https://www.youtube.com/watch?v=YCdykV32pGQ&ab_channel=DisneyFR",
        "https://www.youtube.com/watch?v=ca9vexF7Qbs&ab_channel=SonyaLwu",
        "https://www.youtube.com/watch?v=FhlwWxCUG4M&ab_channel=SonyaLwu",
        "https://www.youtube.com/watch?v=Nq_nDdkMXT8&t=537s&ab_channel=L%C3%A9o-TechMaker",
        "https://www.youtube.com/watch?v=_UaWNQotwoU&ab_channel=McSkyz",
        "https://www.youtube.com/watch?v=A2yW_J6kwgM&ab_channel=HugoD%C3%A9crypte-Grandsformats",
        "https://www.youtube.com/watch?v=ZxV1B1WgVUo&t=931s&ab_channel=L%27espritcritique",
        "https://www.youtube.com/watch?v=mTiAxGAqcB8&ab_channel=AstronoGeek",
        "https://www.youtube.com/watch?v=aVGd5znBwYs&ab_channel=ConteF%C3%A9cond",
        "https://www.youtube.com/watch?v=dNNc5LlBYK4&ab_channel=Hardisk",
        "https://www.youtube.com/watch?v=urA4kc35VAs&t=10s&ab_channel=ScienceEtonnante",
        "https://www.youtube.com/watch?v=QMHR62MoA7k&ab_channel=TV5MONDEInfo"

    ]

    comments = scraping(urls)
    comments = clean(comments)
    
    annotated_comments = annotate(comments)

    # Extraction des commentaires pour la vectorisation
    comments = [comment.text for comment in annotated_comments]

    # Utilisation des stopwords français de NLTK
    french_stopwords = stopwords.words('french')

    # Vectorisation avec BoW (CountVectorizer)
    vectorizer = CountVectorizer(stop_words = french_stopwords)
    X_bow = vectorizer.fit_transform(comments)

    polarities = [comment.polarity for comment in annotated_comments]

    # Sauvegarde des données dans un fichier CSV
    filename = "dfYtbComments.csv"

    # Enregistrer les vecteurs BoW et leurs polarisations dans le fichier CSV
    with open(filename, mode = 'w', newline = '', encoding = 'utf-8') as file:
        writer = csv.writer(file)
        
        # CVS sous la forme : polarité, vecteur BoW
        header = vectorizer.get_feature_names_out().tolist()
        header = ['polarity'] + header
        writer.writerow(header)
        
        # Écrire les données dans chaque ligne
        for i in range(len(annotated_comments)):
            row = X_bow[i].toarray().flatten().tolist()
            row = [polarities[i]] + row
            writer.writerow(row)

    print(f"Le fichier CSV a été sauvegardé sous '{filename}'.")

main()
