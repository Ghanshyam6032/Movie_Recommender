import os
import modal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 1. Modal Image & Dependencies Configuration
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "fastapi[standard]",
    "uvicorn",
    "pandas",
    "numpy",
    "scikit-learn",
    "requests",
    "python-dotenv",
    "pydantic"
)

# Modal looks for 'app' variable by default
app = modal.App("movie-recommender-backend", image=image)

# 2. FastAPI App Setup
web_app = FastAPI(title="Advanced Dynamic Matrix Movie Engine")

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MovieRequest(BaseModel):
    title: str

class MovieRecommender:
    def __init__(self):
        import pandas as pd
        from sklearn.feature_extraction.text import TfidfVectorizer
        from dotenv import load_dotenv

        load_dotenv()
        self.api_key = os.getenv("TMDB_API_KEY")
        self.base_url = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
        self.image_base = os.getenv("TMDB_IMAGE_BASE_URL", "https://image.tmdb.org/t/p/w500")

        # Fetching Dataset Matrix safely from your HuggingFace repository
        url = "https://huggingface.co/datasets/Ghanshyam51/movie-recommender-dataset/resolve/main/movies_metadata.csv"
        self.df = pd.read_csv(url, low_memory=False)
        self.df = self.df[["title", "overview", "tagline", "release_date"]].dropna(subset=["title"])

        self.df["title"] = self.df["title"].astype(str).str.strip()
        self.df["overview"] = self.df["overview"].fillna("")
        self.df["tagline"] = self.df["tagline"].fillna("")
        self.df["text"] = self.df["overview"] + " " + self.df["tagline"]
        self.df["release_date"] = self.df["release_date"].fillna("N/A")

        self.df = self.df.drop_duplicates(subset=["title"]).reset_index(drop=True)

        # TF-IDF Setup
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(self.df["text"])

        self.indices = pd.Series(
            self.df.index,
            index=self.df["title"].str.lower()
        ).drop_duplicates()

    def get_filtered_curations(self, filter_type: str):
        """Generates dynamic filtered collections containing 10 unique items"""
        if filter_type == "trending":
            sampled_df = self.df.sample(n=min(12, len(self.df)))
            return sampled_df["title"].tolist()[:10]
            
        elif filter_type == "highly_rated":
            highly_rated_fallbacks = [
                "The Dark Knight", "Inception", "Interstellar", "The Godfather", 
                "Pulp Fiction", "The Matrix", "Schindler's List", "Fight Club",
                "Forrest Gump", "Spirited Away"
            ]
            return [t for t in highly_rated_fallbacks if t.lower() in self.indices.index][:10]
            
        elif filter_type == "epics":
            self.df["desc_len"] = self.df["overview"].apply(lambda x: len(str(x).split()))
            sorted_epics = self.df.sort_values(by="desc_len", ascending=False).head(15)
            return sorted_epics.sample(n=10)["title"].tolist()
            
        elif filter_type == "classics":
            def extract_year(date_str):
                try: 
                    return int(str(date_str).split("-")[0])
                except: 
                    return 2000
            self.df["year"] = self.df["release_date"].apply(extract_year)
            classics_df = self.df[(self.df["year"] > 1970) & (self.df["year"] < 1999)]
            return classics_df.sample(n=min(10, len(classics_df)))["title"].tolist()

        return self.df.head(10)["title"].tolist()

    def recommend(self, title, n=10):
        from sklearn.metrics.pairwise import cosine_similarity

        search_title = title.strip().lower()
        if search_title not in self.indices:
            return None

        idx = self.indices[search_title]
        sim = cosine_similarity(self.matrix[idx], self.matrix).flatten()
        movie_ids = sim.argsort()[::-1][1:n+1]
        return self.df.iloc[movie_ids]

    def movie_details(self, title):
        import requests
        try:
            response = requests.get(
                f"{self.base_url}/search/movie",
                params={"api_key": self.api_key, "query": title},
                timeout=8
            )
            data = response.json()
            if not data.get("results"):
                return self._fallback_template(title)

            movie = data["results"][0]
            return {
                "title": movie.get("title"),
                "overview": movie.get("overview") or "No detailed overview logged inside data clusters.",
                "rating": movie.get("vote_average") or 0.0,
                "poster": self.image_base + movie["poster_path"] if movie.get("poster_path") else None,
                "release_date": movie.get("release_date") or "N/A"
            }
        except Exception:
            return self._fallback_template(title)

    def _fallback_template(self, title):
        return {
            "title": title,
            "overview": "Dynamic metadata tracking engine online.",
            "rating": 0.0,
            "poster": None,
            "release_date": "N/A"
        }

recommender = None

def get_recommender():
    global recommender
    if recommender is None:
        recommender = MovieRecommender()
    return recommender

@web_app.get("/")
def home():
    return {"status": "success", "message": "Loop Engine v3 Matrix Live on Modal"}

@web_app.get("/curations/{filter_type}")
def get_curations(filter_type: str):
    rec = get_recommender()
    titles = rec.get_filtered_curations(filter_type)
    output = [rec.movie_details(title) for title in titles]
    return {"movies": output}

@web_app.post("/recommend")
def recommend(movie: MovieRequest):
    rec = get_recommender()
    searched_movie_info = rec.movie_details(movie.title)
    recommendations = rec.recommend(movie.title, n=10)

    if recommendations is None:
        raise HTTPException(status_code=404, detail="Requested sequence target trace missing.")

    output = [rec.movie_details(t) for t in recommendations["title"]]
    return {
        "searched_movie": searched_movie_info,
        "recommendations": output
    }

# 3. Modal ASGI Endpoint Deployment
@app.function(
    secrets=[modal.Secret.from_dotenv()],
    min_containers=1
)
@modal.asgi_app()
def fastapi_app():
    get_recommender()
    return web_app