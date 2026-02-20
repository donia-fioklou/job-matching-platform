import requests

def fetch_jobs(query="developer jobs in new york via linkedin", country="us", language="en", date_posted="all"):
    """
    Récupère les offres d'emploi depuis l'API JSearch
    
    Responsabilité: Appeler l'API et retourner les données brutes
    """
    url = "https://jsearch.p.rapidapi.com/search"

    querystring = {
        "query": query,
        "page": "1",
        "num_pages": "1",
        "country": country,
        "language": language,
        "date_posted": date_posted
    }

    headers = {
        "x-rapidapi-key": "d362dda2a5mshee54e969d2ba53cp171898jsn5c7fa025363a",
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    response.raise_for_status()  # Lever une erreur si statut HTTP != 200
    
    return response.json()

