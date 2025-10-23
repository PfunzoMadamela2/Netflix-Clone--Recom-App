from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import time

app = Flask(__name__)
CORS(app)

TMDB_API_KEY = "db337e69596c06ce7ecc88de2b64b0ff"

GENRES = {
    "action": 28, "adventure": 12, "animation": 16, "comedy": 35, 
    "crime": 80, "documentary": 99, "drama": 18, "family": 10751, 
    "fantasy": 14, "history": 36, "horror": 27, "music": 10402, 
    "mystery": 9648, "romance": 10749, "sci-fi": 878, "thriller": 53, 
    "war": 10752, "western": 37
}

# Add streaming providers mapping
STREAMING_PROVIDERS = {
    "netflix": {"name": "Netflix", "url": "https://www.netflix.com"},
    "disney": {"name": "Disney+", "url": "https://www.disneyplus.com"},
    "hbo": {"name": "Max", "url": "https://www.max.com"},
    "hulu": {"name": "Hulu", "url": "https://www.hulu.com"},
    "prime": {"name": "Amazon Prime", "url": "https://www.primevideo.com"},
    "apple": {"name": "Apple TV+", "url": "https://tv.apple.com"},
    "paramount": {"name": "Paramount+", "url": "https://www.paramountplus.com"},
    "peacock": {"name": "Peacock", "url": "https://www.peacocktv.com"},
}

def parse_search_query(query):
    query_lower = query.lower()
    
    found_genres = []
    for genre in GENRES.keys():
        if genre in query_lower:
            found_genres.append(genre)
    
    year_match = re.search(r'\b(19[0-9]{2}|20[0-9]{2})\b', query)
    year = year_match.group(0) if year_match else None
    
    actor_patterns = [
        r'starring\s+([^,.]+)',
        r'with\s+([^,.]+)',
        r'featuring\s+([^,.]+)',
        r'actor\s*:\s*([^,.]+)',
    ]
    
    actors = []
    for pattern in actor_patterns:
        actor_match = re.search(pattern, query_lower)
        if actor_match:
            actors.append(actor_match.group(1).strip())
    
    company_patterns = [
        r'by\s+([^,.]+)',
        r'production\s*:\s*([^,.]+)',
        r'studio\s*:\s*([^,.]+)',
        r'company\s*:\s*([^,.]+)',
    ]
    
    companies = []
    for pattern in company_patterns:
        company_match = re.search(pattern, query_lower)
        if company_match:
            companies.append(company_match.group(1).strip())
    
    clean_query = query_lower
    for genre in found_genres:
        clean_query = clean_query.replace(genre, "")
    if year:
        clean_query = clean_query.replace(year, "")
    for actor in actors:
        clean_query = clean_query.replace(actor, "")
    for company in companies:
        clean_query = clean_query.replace(company, "")
    
    common_words = ["movies", "movie", "films", "film", "from", "in", "the", "about", "starring", "with", "featuring", "by", "production", "studio", "company"]
    for word in common_words:
        clean_query = re.sub(r'\b' + word + r'\b', '', clean_query)
    
    clean_query = re.sub(r'\s+', ' ', clean_query).strip()
    
    return found_genres, year, clean_query or "movie", actors, companies

def get_streaming_providers(movie_id):
    """Get streaming providers for a movie"""
    try:
        url = "https://api.themoviedb.org/3/movie/{}/watch/providers?api_key={}".format(movie_id, TMDB_API_KEY)
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            providers = data.get("results", {})
            us_providers = providers.get("US", {})
            
            streaming_services = []
            
            # Check flatrate (subscription services)
            flatrate = us_providers.get("flatrate", [])
            for provider in flatrate:
                provider_name = provider.get("provider_name", "").lower()
                for key, service in STREAMING_PROVIDERS.items():
                    if key in provider_name:
                        streaming_services.append({
                            "name": service["name"],
                            "url": service["url"],
                            "type": "stream"
                        })
                        break
            
            # Check rent services
            rent = us_providers.get("rent", [])
            for provider in rent:
                provider_name = provider.get("provider_name", "").lower()
                if "apple" in provider_name:
                    streaming_services.append({
                        "name": "Apple TV",
                        "url": "https://tv.apple.com",
                        "type": "rent"
                    })
                elif "amazon" in provider_name:
                    streaming_services.append({
                        "name": "Amazon Prime",
                        "url": "https://www.primevideo.com",
                        "type": "rent"
                    })
                elif "google" in provider_name:
                    streaming_services.append({
                        "name": "Google Play",
                        "url": "https://play.google.com",
                        "type": "rent"
                    })
                elif "vudu" in provider_name:
                    streaming_services.append({
                        "name": "Vudu",
                        "url": "https://www.vudu.com",
                        "type": "rent"
                    })
            
            # Check buy services
            buy = us_providers.get("buy", [])
            for provider in buy:
                provider_name = provider.get("provider_name", "").lower()
                if "apple" in provider_name and not any(s["name"] == "Apple TV" for s in streaming_services):
                    streaming_services.append({
                        "name": "Apple TV",
                        "url": "https://tv.apple.com",
                        "type": "buy"
                    })
                elif "amazon" in provider_name and not any(s["name"] == "Amazon Prime" for s in streaming_services):
                    streaming_services.append({
                        "name": "Amazon Prime",
                        "url": "https://www.primevideo.com",
                        "type": "buy"
                    })
            
            return streaming_services[:6]  # Limit to 6 providers
            
    except Exception as e:
        print("Error fetching streaming providers: {}".format(e))
    
    return []

def fetch_movie_details(movie_id):
    try:
        url = "https://api.themoviedb.org/3/movie/{}?api_key={}&append_to_response=credits,videos,production_companies".format(movie_id, TMDB_API_KEY)
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        
        title = data.get("title", "Unknown Title")
        release_date = data.get("release_date", "")
        year = release_date.split("-")[0] if release_date else "Unknown"
        
        genre_names = [genre["name"] for genre in data.get("genres", [])]
        
        runtime = data.get("runtime", 0)
        runtime_str = "{} min".format(runtime) if runtime else "Unknown"
        
        poster_path = data.get("poster_path")
        poster_url = "https://image.tmdb.org/t/p/w342{}".format(poster_path) if poster_path else None
        
        cast = []
        credits = data.get("credits", {})
        if credits:
            cast = [actor["name"] for actor in credits.get("cast", [])[:8]]
        
        director = "Unknown"
        crew = credits.get("crew", [])
        for person in crew:
            if person.get("job") == "Director":
                director = person.get("name", "Unknown")
                break
        
        production_companies = [company["name"] for company in data.get("production_companies", [])[:3]]
        
        videos = data.get("videos", {}).get("results", [])
        trailer_key = None
        for video in videos:
            if video.get("type") == "Trailer" and video.get("site") == "YouTube":
                trailer_key = video.get("key")
                if "official" in video.get("name", "").lower():
                    break
        
        # Get streaming providers
        streaming_providers = get_streaming_providers(movie_id)
        
        vote_average = data.get("vote_average", 0)
        rating = round(vote_average, 1) if vote_average > 0 else "N/A"
        
        return {
            "tmdbID": movie_id,
            "Title": title,
            "Year": year,
            "Genre": ", ".join(genre_names) if genre_names else "Unknown",
            "Plot": data.get("overview", "No description available"),
            "imdbRating": rating,
            "Poster": poster_url,
            "Runtime": runtime_str,
            "Actors": ", ".join(cast) if cast else "Unknown",
            "Director": director,
            "ReleaseDate": release_date,
            "ProductionCompanies": ", ".join(production_companies) if production_companies else "Unknown",
            "TrailerKey": trailer_key,
            "StreamingProviders": streaming_providers,
            "vote_count": data.get("vote_count", 0)
        }
    except Exception as e:
        print("Error fetching movie details: {}".format(e))
        return None

def get_trailer_key(movie_id):
    try:
        url = "https://api.themoviedb.org/3/movie/{}/videos?api_key={}".format(movie_id, TMDB_API_KEY)
        response = requests.get(url, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            videos = data.get("results", [])
            
            trailers = [v for v in videos if v.get("type") == "Trailer" and v.get("site") == "YouTube"]
            teasers = [v for v in videos if v.get("type") == "Teaser" and v.get("site") == "YouTube"]
            
            for video in trailers:
                if "official" in video.get("name", "").lower():
                    return video['key']
            
            if trailers:
                return trailers[0]['key']
            
            if teasers:
                return teasers[0]['key']
            
    except Exception as e:
        print("Error fetching trailer: {}".format(e))
    
    return None

def search_movies_by_actor(actor_name, page=1):
    try:
        url = "https://api.themoviedb.org/3/search/person?api_key={}&query={}&page={}".format(TMDB_API_KEY, requests.utils.requote_uri(actor_name), page)
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            persons = data.get("results", [])
            if persons:
                person_id = persons[0].get("id")
                url = "https://api.themoviedb.org/3/person/{}/movie_credits?api_key={}".format(person_id, TMDB_API_KEY)
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    credits_data = response.json()
                    movies = []
                    for item in credits_data.get("cast", [])[:30]:
                        title = item.get("title", "Unknown Title")
                        if not title or title == "Unknown Title":
                            continue
                            
                        release_date = item.get("release_date", "")
                        year = release_date.split("-")[0] if release_date else "Unknown"
                        
                        current_year = int(time.strftime("%Y"))
                        if year.isdigit() and int(year) > current_year:
                            continue
                        
                        poster_path = item.get("poster_path")
                        poster_url = "https://image.tmdb.org/t/p/w342{}".format(poster_path) if poster_path else None
                        
                        genre_ids = item.get("genre_ids", [])
                        genre_names = []
                        for genre_id in genre_ids:
                            for name, id_val in GENRES.items():
                                if id_val == genre_id:
                                    genre_names.append(name)
                                    break
                        
                        movie_data = {
                            "tmdbID": item.get("id"),
                            "Title": title,
                            "Year": year,
                            "Genre": ", ".join([g.capitalize() for g in genre_names]) if genre_names else "Unknown",
                            "Plot": (item.get("overview", "No description available")[:120] + "...") if item.get("overview") else "No description available",
                            "imdbRating": round(item.get("vote_average", 0), 1) if item.get("vote_average", 0) > 0 else "N/A",
                            "Poster": poster_url,
                            "genres_list": genre_names,
                            "popularity": item.get("popularity", 0),
                            "vote_count": item.get("vote_count", 0),
                            "search_type": "actor",
                            "actor_name": actor_name
                        }
                        movies.append(movie_data)
                    return movies
    except Exception as e:
        print("Actor search error: {}".format(e))
    return []

def search_movies_by_company(company_name, page=1):
    try:
        url = "https://api.themoviedb.org/3/search/company?api_key={}&query={}&page={}".format(TMDB_API_KEY, requests.utils.requote_uri(company_name), page)
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            companies = data.get("results", [])
            if companies:
                company_id = companies[0].get("id")
                url = "https://api.themoviedb.org/3/discover/movie?api_key={}&with_companies={}&sort_by=popularity.desc&page={}".format(TMDB_API_KEY, company_id, page)
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    movies = []
                    for item in data.get("results", [])[:30]:
                        title = item.get("title", "Unknown Title")
                        if not title or title == "Unknown Title":
                            continue
                            
                        release_date = item.get("release_date", "")
                        year = release_date.split("-")[0] if release_date else "Unknown"
                        
                        current_year = int(time.strftime("%Y"))
                        if year.isdigit() and int(year) > current_year:
                            continue
                        
                        genre_ids = item.get("genre_ids", [])
                        genre_names = []
                        for genre_id in genre_ids:
                            for name, id_val in GENRES.items():
                                if id_val == genre_id:
                                    genre_names.append(name)
                                    break
                        
                        poster_path = item.get("poster_path")
                        poster_url = "https://image.tmdb.org/t/p/w342{}".format(poster_path) if poster_path else None
                        
                        movie_data = {
                            "tmdbID": item.get("id"),
                            "Title": title,
                            "Year": year,
                            "Genre": ", ".join([g.capitalize() for g in genre_names]) if genre_names else "Unknown",
                            "Plot": (item.get("overview", "No description available")[:120] + "...") if item.get("overview") else "No description available",
                            "imdbRating": round(item.get("vote_average", 0), 1) if item.get("vote_average", 0) > 0 else "N/A",
                            "Poster": poster_url,
                            "genres_list": genre_names,
                            "popularity": item.get("popularity", 0),
                            "vote_count": item.get("vote_count", 0),
                            "search_type": "company",
                            "company_name": company_name
                        }
                        movies.append(movie_data)
                    return movies
    except Exception as e:
        print("Company search error: {}".format(e))
    return []

def search_movies(query, year=None, page=1):
    try:
        encoded_query = requests.utils.requote_uri(query)
        url = "https://api.themoviedb.org/3/search/movie?api_key={}&query={}&page={}".format(TMDB_API_KEY, encoded_query, page)
        response = requests.get(url, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            movies = []
            for item in data.get("results", []):
                title = item.get("title", "Unknown Title")
                release_date = item.get("release_date", "")
                item_year = release_date.split("-")[0] if release_date else "Unknown"
                
                current_year = int(time.strftime("%Y"))
                if item_year.isdigit() and int(item_year) > current_year:
                    continue
                
                if year and item_year != year:
                    continue
                
                genre_ids = item.get("genre_ids", [])
                genre_names = []
                for genre_id in genre_ids:
                    for name, id_val in GENRES.items():
                        if id_val == genre_id:
                            genre_names.append(name)
                            break
                
                poster_path = item.get("poster_path")
                poster_url = "https://image.tmdb.org/t/p/w342{}".format(poster_path) if poster_path else None
                
                plot = item.get("overview", "No description available")
                if plot and len(plot) > 120:
                    plot = plot[:120] + "..."
                
                movie_data = {
                    "tmdbID": item.get("id"),
                    "Title": title,
                    "Year": item_year,
                    "Genre": ", ".join([g.capitalize() for g in genre_names]) if genre_names else "Unknown",
                    "Plot": plot,
                    "imdbRating": round(item.get("vote_average", 0), 1) if item.get("vote_average", 0) > 0 else "N/A",
                    "Poster": poster_url,
                    "genres_list": genre_names,
                    "popularity": item.get("popularity", 0),
                    "vote_count": item.get("vote_count", 0),
                    "search_type": "general"
                }
                movies.append(movie_data)
            return movies, data.get("total_pages", 1)
    except Exception as e:
        print("Search error: {}".format(e))
    return [], 1

def discover_by_genre(genre, year=None, max_results=12):
    try:
        genre_id = GENRES.get(genre)
        if not genre_id:
            return []
            
        url = "https://api.themoviedb.org/3/discover/movie?api_key={}&with_genres={}&sort_by=popularity.desc".format(TMDB_API_KEY, genre_id)
        
        if year:
            url += "&primary_release_year={}".format(year)
        else:
            current_year = time.strftime("%Y")
            url += "&primary_release_year={}".format(current_year)
        
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            movies = []
            for item in data.get("results", [])[:max_results]:
                title = item.get("title", "Unknown Title")
                release_date = item.get("release_date", "")
                item_year = release_date.split("-")[0] if release_date else "Unknown"
                
                genre_ids = item.get("genre_ids", [])
                genre_names = []
                for genre_id in genre_ids:
                    for name, id_val in GENRES.items():
                        if id_val == genre_id:
                            genre_names.append(name)
                            break
                
                poster_path = item.get("poster_path")
                poster_url = "https://image.tmdb.org/t/p/w342{}".format(poster_path) if poster_path else None
                
                plot = item.get("overview", "No description available")
                if plot and len(plot) > 120:
                    plot = plot[:120] + "..."
                
                movie_data = {
                    "tmdbID": item.get("id"),
                    "Title": title,
                    "Year": item_year,
                    "Genre": ", ".join([g.capitalize() for g in genre_names]) if genre_names else "Unknown",
                    "Plot": plot,
                    "imdbRating": round(item.get("vote_average", 0), 1) if item.get("vote_average", 0) > 0 else "N/A",
                    "Poster": poster_url,
                    "genres_list": genre_names,
                }
                movies.append(movie_data)
            return movies
    except Exception as e:
        print("Discover error: {}".format(e))
    return []

def calculate_relevance_score(movie, query_terms, found_genres, target_year, actors, companies):
    score = 0
    
    title_lower = movie.get('Title', '').lower()
    genre_lower = movie.get('Genre', '').lower()
    plot_lower = movie.get('Plot', '').lower()
    
    for term in query_terms:
        if term in title_lower:
            score += 15
        elif term in genre_lower:
            score += 8
        elif term in plot_lower:
            score += 3
    
    if target_year and movie.get('Year') == target_year:
        score += 20
    
    movie_genres = movie.get("genres_list", [])
    for genre in found_genres:
        if genre in movie_genres:
            score += 10
    
    for actor in actors:
        if actor.lower() in plot_lower or actor.lower() in title_lower:
            score += 12
    
    for company in companies:
        if company.lower() in plot_lower:
            score += 10
    
    rating = movie.get('imdbRating', 0)
    if rating != "N/A":
        score += float(rating) * 2
    
    popularity = movie.get('popularity', 0)
    score += min(popularity * 0.05, 10)
    
    vote_count = movie.get('vote_count', 0)
    if vote_count > 100:
        score += min(vote_count * 0.002, 5)
    
    return score

@app.route("/api/search", methods=["POST"])
def search():
    start_time = time.time()
    data = request.json
    query = data.get("query", "").strip()
    top_k = data.get("top_k", 80)
    
    if not query:
        return jsonify({"error": "Empty query"}), 400
    
    found_genres, year, search_query, actors, companies = parse_search_query(query)
    query_terms = [term for term in search_query.split() if len(term) > 2]
    
    print("Search: '{}' -> Genres: {}, Year: {}, Actors: {}, Companies: {}".format(query, found_genres, year, actors, companies))
    
    all_movies = []
    
    if actors:
        for actor in actors[:2]:
            actor_movies = search_movies_by_actor(actor)
            all_movies.extend(actor_movies)
            time.sleep(0.2)
    
    if companies:
        for company in companies[:2]:
            company_movies = search_movies_by_company(company)
            all_movies.extend(company_movies)
            time.sleep(0.2)
    
    if len(all_movies) < top_k:
        page = 1
        max_pages = 5
        while page <= max_pages and len(all_movies) < top_k:
            movies, total_pages = search_movies(query, year, page)
            all_movies.extend(movies)
            print(f"Page {page}: Found {len(movies)} movies, total: {len(all_movies)}")
            page += 1
            time.sleep(0.3)
    
    if found_genres and len(all_movies) < top_k:
        for genre in found_genres[:3]:
            genre_movies = discover_by_genre(genre, year, 30)
            existing_ids = {m["tmdbID"] for m in all_movies}
            new_movies = [m for m in genre_movies if m["tmdbID"] not in existing_ids]
            all_movies.extend(new_movies[:top_k - len(all_movies)])
            print(f"Genre {genre}: Added {len(new_movies)} new movies")
            time.sleep(0.2)
    
    unique_movies = {}
    for movie in all_movies:
        if movie["tmdbID"] not in unique_movies:
            unique_movies[movie["tmdbID"]] = movie
    all_movies = list(unique_movies.values())
    
    print(f"After deduplication: {len(all_movies)} movies")
    
    scored_movies = []
    for movie in all_movies:
        score = calculate_relevance_score(movie, query_terms, found_genres, year, actors, companies)
        scored_movies.append((movie, score))
    
    scored_movies.sort(key=lambda x: x[1], reverse=True)
    
    max_score = max([s for _, s in scored_movies]) if scored_movies else 1
    final_movies = []
    for movie, score in scored_movies:
        normalized_score = score / max_score if max_score > 0 else 0.5
        movie["score"] = round(normalized_score, 4)
        final_movies.append(movie)
    
    elapsed = time.time() - start_time
    print("Search completed: {} movies in {:.2f}s".format(len(final_movies), elapsed))
    
    return jsonify({
        "query": query,
        "results": final_movies[:top_k],
        "searchTime": round(elapsed, 2),
        "searchType": "actor" if actors else "company" if companies else "general"
    })

@app.route("/api/recommend/<genre>", methods=["GET"])
def get_recommendations(genre):
    try:
        movies = discover_by_genre(genre, None, 20)
        return jsonify({
            "genre": genre,
            "results": movies
        })
    except Exception as e:
        print("Recommendation error: {}".format(e))
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/trending", methods=["GET"])
def get_trending():
    try:
        current_year = time.strftime("%Y")
        popular_genres = ["action", "comedy", "drama", "romance", "thriller", "sci-fi"]
        genre_data = {}
        
        for genre in popular_genres:
            movies = discover_by_genre(genre, current_year, 12)
            if movies:
                genre_data[genre] = movies
        
        return jsonify({"results": genre_data})
    except Exception as e:
        print("Trending error: {}".format(e))
        return jsonify({"results": {}})

@app.route("/api/movie/<int:movie_id>", methods=["GET"])
def get_movie(movie_id):
    try:
        movie_details = fetch_movie_details(movie_id)
        if movie_details:
            return jsonify(movie_details)
        else:
            return jsonify({"error": "Movie not found"}), 404
    except Exception as e:
        print("Movie details error: {}".format(e))
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/movie/<int:movie_id>/trailer", methods=["GET"])
def get_trailer_route(movie_id):
    try:
        trailer_key = get_trailer_key(movie_id)
        if trailer_key:
            return jsonify({"trailerKey": trailer_key})
        else:
            return jsonify({"error": "Trailer not found"}), 404
    except Exception as e:
        print("Trailer error: {}".format(e))
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/movie/<int:movie_id>/streaming", methods=["GET"])
def get_streaming_providers_route(movie_id):
    try:
        providers = get_streaming_providers(movie_id)
        return jsonify({"streamingProviders": providers})
    except Exception as e:
        print("Streaming providers error: {}".format(e))
        return jsonify({"error": "Internal server error"}), 500

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "OK", "message": "CineMatch API is running"})

if __name__ == "__main__":
    app.run(debug=True, port=5000, host='0.0.0.0')