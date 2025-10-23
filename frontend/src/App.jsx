import React, { useState, useEffect } from "react";
import './styles.css';

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [view, setView] = useState("home");
  const [trendingData, setTrendingData] = useState(null);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState("basic");
  const [showTrailerModal, setShowTrailerModal] = useState(false);
  const [trailerUrl, setTrailerUrl] = useState("");

  const RESULTS_PER_PAGE = 12;
  const currentYear = new Date().getFullYear();

  useEffect(() => {
    loadTrendingMovies();
  }, []);

  const loadTrendingMovies = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/trending");
      if (response.ok) {
        const data = await response.json();
        setTrendingData(data.results);
      } else {
        throw new Error("Failed to load trending movies");
      }
    } catch (err) {
      console.error("Failed to load trending movies:", err);
      setError("Failed to load trending movies");
    }
  };

  const loadRecommendations = async (genre) => {
    try {
      setLoading(true);
      setError("");
      const response = await fetch(`http://localhost:5000/api/recommend/${genre}`);
      if (response.ok) {
        const data = await response.json();
        setResults({
          query: `${genre} recommendations`,
          results: data.results,
          searchTime: 0
        });
        setView("search");
        setCurrentPage(1);
        setQuery(""); // Clear search input when going to recommendations
      } else {
        throw new Error("Failed to load recommendations");
      }
    } catch (err) {
      console.error("Failed to load recommendations:", err);
      setError("Failed to load recommendations");
    } finally {
      setLoading(false);
    }
  };

  const performSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      setError("Please enter a search query");
      return;
    }
    
    setLoading(true);
    setError("");
    setResults(null);
    setCurrentPage(1);
    setView("search");
    
    try {
      const response = await fetch("http://localhost:5000/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k: 80 }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Search failed");
      }
      
      const data = await response.json();
      setResults(data);
    } catch (err) {
      console.error("Search error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const goBackToTrending = () => {
    setView("home");
    setQuery(""); // Clear search input
    setResults(null);
    setCurrentPage(1);
    window.scrollTo(0, 0);
  };

  const fetchMovieDetails = async (movieId) => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:5000/api/movie/${movieId}`);
      if (!response.ok) {
        throw new Error("Failed to load movie details");
      }
      
      const data = await response.json();
      setSelectedMovie(data);
      setModalType("basic");
      setShowModal(true);
    } catch (err) {
      console.error("Movie details error:", err);
      setError("Failed to load movie details");
    } finally {
      setLoading(false);
    }
  };

  const playTrailer = async (movieId) => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:5000/api/movie/${movieId}/trailer`);
      
      if (response.ok) {
        const data = await response.json();
        if (data.trailerKey) {
          setTrailerUrl(`https://www.youtube.com/embed/${data.trailerKey}`);
          setShowTrailerModal(true);
        } else {
          setError("No trailer available for this movie");
        }
      } else {
        throw new Error("Failed to fetch trailer");
      }
    } catch (err) {
      console.error("Trailer error:", err);
      setError("Failed to load trailer");
    } finally {
      setLoading(false);
    }
  };

  const openStreamingService = (url) => {
    window.open(url, '_blank');
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedMovie(null);
    setModalType("basic");
  };

  const closeTrailerModal = () => {
    setShowTrailerModal(false);
    setTrailerUrl("");
  };

  const showExtendedInfo = () => {
    setModalType("extended");
  };

  const getRatingColor = (rating) => {
    if (rating === "N/A") return "#666";
    const num = parseFloat(rating);
    if (num >= 8) return "#10b981";
    if (num >= 7) return "#84cc16";
    if (num >= 6) return "#eab308";
    return "#ef4444";
  };

  const handleImageError = (e) => {
    e.target.style.display = 'none';
    const placeholder = e.target.nextSibling;
    if (placeholder) {
      placeholder.style.display = 'flex';
    }
  };

  const truncateText = (text, maxLength) => {
    if (!text) return "";
    return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
  };

  const formatDate = (dateString) => {
    if (!dateString || dateString === "Unknown") return "Unknown";
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  const getStreamingTypeColor = (type) => {
    switch(type) {
      case 'stream': return '#10b981';
      case 'rent': return '#f59e0b';
      case 'buy': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStreamingTypeText = (type) => {
    switch(type) {
      case 'stream': return 'Stream';
      case 'rent': return 'Rent';
      case 'buy': return 'Buy';
      default: return 'Available';
    }
  };

  const totalPages = results ? Math.ceil(results.results.length / RESULTS_PER_PAGE) : 0;
  const startIndex = (currentPage - 1) * RESULTS_PER_PAGE;
  const currentResults = results ? results.results.slice(startIndex, startIndex + RESULTS_PER_PAGE) : [];

  const goToPage = (page) => {
    setCurrentPage(page);
    window.scrollTo(0, 0);
  };

  const generatePageNumbers = () => {
    const pages = [];
    const maxVisible = 5;
    
    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      let start = Math.max(1, currentPage - 2);
      let end = Math.min(totalPages, currentPage + 2);
      
      if (currentPage <= 3) {
        end = maxVisible;
      } else if (currentPage >= totalPages - 2) {
        start = totalPages - maxVisible + 1;
      }
      
      for (let i = start; i <= end; i++) pages.push(i);
    }
    return pages;
  };

  const genreDisplayNames = {
    "action": "Action 🎬",
    "comedy": "Comedy 😄", 
    "drama": "Drama 🎭",
    "romance": "Romance 💕",
    "thriller": "Thriller 🔪",
    "sci-fi": "Sci-Fi 🚀"
  };

  const BasicMovieModal = () => (
    <div className="modal-overlay" onClick={closeModal}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={closeModal}>×</button>
        
        <div className="movie-details">
          <div className="details-poster">
            {selectedMovie.Poster ? (
              <img 
                src={selectedMovie.Poster} 
                alt={selectedMovie.Title}
                className="details-poster-img"
                onError={handleImageError}
              />
            ) : (
              <div className="poster-placeholder">🎬</div>
            )}
          </div>
          
          <div className="details-info">
            <h2>{selectedMovie.Title} ({selectedMovie.Year})</h2>
            
            <div className="details-meta">
              <div className="rating-badge" style={{backgroundColor: getRatingColor(selectedMovie.imdbRating)}}>
                ⭐ {selectedMovie.imdbRating}
              </div>
              <span className="runtime">{selectedMovie.Runtime}</span>
              <span className="genre">{selectedMovie.Genre}</span>
            </div>
            
            <p className="details-plot">{selectedMovie.Plot}</p>
            
            {selectedMovie.Actors && selectedMovie.Actors !== "Unknown" && (
              <div className="details-cast">
                <strong>Cast:</strong> {truncateText(selectedMovie.Actors, 100)}
              </div>
            )}
            
            {selectedMovie.Director && selectedMovie.Director !== "Unknown" && (
              <div className="details-director">
                <strong>Director:</strong> {selectedMovie.Director}
              </div>
            )}

            {selectedMovie.ProductionCompanies && selectedMovie.ProductionCompanies !== "Unknown" && (
              <div className="details-companies">
                <strong>Production:</strong> {selectedMovie.ProductionCompanies}
              </div>
            )}

            {/* Streaming Providers Section */}
            {selectedMovie.StreamingProviders && selectedMovie.StreamingProviders.length > 0 && (
              <div className="streaming-section">
                <h4>🎯 Where to Watch</h4>
                <div className="streaming-providers">
                  {selectedMovie.StreamingProviders.map((provider, index) => (
                    <button
                      key={index}
                      className="streaming-btn"
                      onClick={() => openStreamingService(provider.url)}
                      style={{ borderLeftColor: getStreamingTypeColor(provider.type) }}
                    >
                      <span className="provider-name">{provider.name}</span>
                      <span 
                        className="provider-type"
                        style={{ backgroundColor: getStreamingTypeColor(provider.type) }}
                      >
                        {getStreamingTypeText(provider.type)}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            <div className="details-actions">
              {selectedMovie.TrailerKey && (
                <button 
                  className="trailer-btn"
                  onClick={() => playTrailer(selectedMovie.tmdbID)}
                >
                  🎬 Watch Trailer
                </button>
              )}
              <button
                className="info-btn"
                onClick={showExtendedInfo}
              >
                📖 More Info
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const ExtendedInfoModal = () => (
    <div className="modal-overlay" onClick={closeModal}>
      <div className="modal-content extended-info" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={closeModal}>×</button>
        
        <div className="extended-movie-details">
          <div className="extended-poster">
            {selectedMovie.Poster ? (
              <img 
                src={selectedMovie.Poster} 
                alt={selectedMovie.Title}
                className="extended-poster-img"
                onError={handleImageError}
              />
            ) : (
              <div className="poster-placeholder-large">🎬</div>
            )}
          </div>
          
          <div className="extended-info-content">
            <h1>{selectedMovie.Title} ({selectedMovie.Year})</h1>
            
            <div className="extended-meta-grid">
              <div className="meta-item">
                <strong>Rating</strong>
                <div className="rating-badge-large" style={{backgroundColor: getRatingColor(selectedMovie.imdbRating)}}>
                  ⭐ {selectedMovie.imdbRating}
                </div>
              </div>
              
              <div className="meta-item">
                <strong>Runtime</strong>
                <span>{selectedMovie.Runtime}</span>
              </div>
              
              <div className="meta-item">
                <strong>Release Date</strong>
                <span>{formatDate(selectedMovie.ReleaseDate)}</span>
              </div>

              {selectedMovie.Director && selectedMovie.Director !== "Unknown" && (
                <div className="meta-item">
                  <strong>Director</strong>
                  <span>{selectedMovie.Director}</span>
                </div>
              )}
              
              <div className="meta-item full-width">
                <strong>Genres</strong>
                <span>{selectedMovie.Genre}</span>
              </div>

              {selectedMovie.ProductionCompanies && selectedMovie.ProductionCompanies !== "Unknown" && (
                <div className="meta-item full-width">
                  <strong>Production Companies</strong>
                  <span>{selectedMovie.ProductionCompanies}</span>
                </div>
              )}
            </div>
            
            <div className="plot-section">
              <h3>Overview</h3>
              <p className="extended-plot">{selectedMovie.Plot}</p>
            </div>
            
            {selectedMovie.Actors && selectedMovie.Actors !== "Unknown" && (
              <div className="cast-section">
                <h3>Cast</h3>
                <p className="extended-cast">{selectedMovie.Actors}</p>
              </div>
            )}

            {/* Streaming Providers in Extended View */}
            {selectedMovie.StreamingProviders && selectedMovie.StreamingProviders.length > 0 && (
              <div className="streaming-section extended">
                <h3>🎯 Where to Watch Legally</h3>
                <div className="streaming-providers extended">
                  {selectedMovie.StreamingProviders.map((provider, index) => (
                    <button
                      key={index}
                      className="streaming-btn extended"
                      onClick={() => openStreamingService(provider.url)}
                      style={{ borderLeftColor: getStreamingTypeColor(provider.type) }}
                    >
                      <span className="provider-name">{provider.name}</span>
                      <span 
                        className="provider-type"
                        style={{ backgroundColor: getStreamingTypeColor(provider.type) }}
                      >
                        {getStreamingTypeText(provider.type)}
                      </span>
                    </button>
                  ))}
                </div>
                <p className="streaming-note">Click to open the streaming service in a new tab</p>
              </div>
            )}
            
            <div className="extended-actions">
              {selectedMovie.TrailerKey && (
                <button 
                  className="trailer-btn-large"
                  onClick={() => playTrailer(selectedMovie.tmdbID)}
                >
                  🎬 Watch Trailer
                </button>
              )}
              <button
                className="back-btn"
                onClick={() => setModalType("basic")}
              >
                ← Back to Details
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const TrailerModal = () => (
    <div className="modal-overlay" onClick={closeTrailerModal}>
      <div className="modal-content trailer-modal" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={closeTrailerModal}>×</button>
        <div className="trailer-container">
          {trailerUrl ? (
            <iframe
              src={trailerUrl}
              title="Movie Trailer"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            ></iframe>
          ) : (
            <div className="no-trailer">Trailer not available</div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="container">
      {showModal && selectedMovie && (
        modalType === "basic" ? <BasicMovieModal /> : <ExtendedInfoModal />
      )}
      
      {showTrailerModal && <TrailerModal />}

      <header className="header">
        <h1 className="logo" onClick={goBackToTrending}>
          🎬 CineMatch
        </h1>
        <p className="tagline">Discover Your Next Favorite Movie</p>
      </header>

      <main className="main">
        <form onSubmit={performSearch} className="search-form">
          <div className="search-input-group">
            <input
              type="text"
              className="search-input"
              placeholder='Try: "sci-fi thriller", "with Tom Hanks", "by Warner Bros", "action 2023"'
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
            />
            <button type="submit" className="search-btn" disabled={loading}>
              {loading ? "Searching..." : "🔍 Search"}
            </button>
          </div>
        </form>

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Searching for movies...</p>
          </div>
        )}

        {error && (
          <div className="error">
            <span>{error}</span>
            <button onClick={() => setError("")} className="error-close">×</button>
          </div>
        )}

        {view === "home" && (
          <section className="home-section">
            <h2 className="section-title">🔥 Trending in {currentYear}</h2>
            <p className="section-subtitle">Popular movies by genre</p>
            
            {!trendingData ? (
              <div className="loading">Loading trending movies...</div>
            ) : Object.keys(trendingData).length === 0 ? (
              <div className="error">No trending movies available</div>
            ) : (
              <div className="genre-sections">
                {Object.entries(trendingData).map(([genre, movies]) => (
                  <div key={genre} className="genre-section">
                    <div className="genre-header">
                      <h3 className="genre-title">{genreDisplayNames[genre] || genre}</h3>
                      <button 
                        className="recommend-btn"
                        onClick={() => loadRecommendations(genre)}
                      >
                        More {genre} →
                      </button>
                    </div>
                    {movies.length === 0 ? (
                      <div className="no-movies">No movies found</div>
                    ) : (
                      <div className="horizontal-scroll">
                        <div className="genre-grid-horizontal">
                          {movies.map((movie) => (
                            <div 
                              key={movie.tmdbID} 
                              className="movie-card trending"
                              onClick={() => fetchMovieDetails(movie.tmdbID)}
                            >
                              <div className="poster-container">
                                {movie.Poster ? (
                                  <>
                                    <img 
                                      src={movie.Poster} 
                                      alt={movie.Title}
                                      className="movie-poster"
                                      onError={handleImageError}
                                    />
                                    <div className="poster-placeholder" style={{display: 'none'}}>🎬</div>
                                  </>
                                ) : (
                                  <div className="poster-placeholder">🎬</div>
                                )}
                                <div className="movie-overlay invisible-overlay"></div>
                              </div>
                              
                              <div className="movie-info">
                                <div className="movie-header">
                                  <h4 className="movie-title">{truncateText(movie.Title, 20)}</h4>
                                  <div 
                                    className="movie-rating"
                                    style={{ backgroundColor: getRatingColor(movie.imdbRating) }}
                                  >
                                    {movie.imdbRating}
                                  </div>
                                </div>
                                <div className="movie-year">{movie.Year}</div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {view === "search" && results && (
          <section className="results-section">
            <div className="results-header">
              <button 
                className="back-btn"
                onClick={goBackToTrending}
              >
                ← Back to Trending
              </button>
              <h2 className="results-title">
                {results.results.length} results for "{results.query}"
                {results.searchType === "actor" && " (Actor Search)"}
                {results.searchType === "company" && " (Company Search)"}
              </h2>
              {results.searchTime && (
                <p className="search-time">Found in {results.searchTime}s</p>
              )}
            </div>

            {results.results.length === 0 ? (
              <div className="no-results">
                <p>No movies found for your search.</p>
                <p>Try different keywords or check the trending movies.</p>
              </div>
            ) : (
              <>
                <div className="results-grid">
                  {currentResults.map((movie) => (
                    <div 
                      key={movie.tmdbID} 
                      className="movie-card search-result"
                      onClick={() => fetchMovieDetails(movie.tmdbID)}
                    >
                      <div className="poster-container">
                        {movie.Poster ? (
                          <>
                            <img 
                              src={movie.Poster} 
                              alt={movie.Title}
                              className="movie-poster"
                              onError={handleImageError}
                            />
                            <div className="poster-placeholder" style={{display: 'none'}}>🎬</div>
                          </>
                        ) : (
                          <div className="poster-placeholder">🎬</div>
                        )}
                        <div className="movie-overlay invisible-overlay"></div>
                      </div>
                      
                      <div className="movie-info">
                        <div className="movie-header">
                          <h3 className="movie-title">{truncateText(movie.Title, 25)}</h3>
                          <div 
                            className="movie-rating"
                            style={{ backgroundColor: getRatingColor(movie.imdbRating) }}
                          >
                            {movie.imdbRating}
                          </div>
                        </div>
                        
                        <div className="movie-meta">
                          <span className="movie-year">{movie.Year}</span>
                          <span className="movie-genre">{movie.Genre?.split(',')[0]}</span>
                        </div>
                        
                        <p className="movie-plot">{truncateText(movie.Plot, 100)}</p>
                        
                        <div className="movie-score">
                          Match: <strong>{(movie.score * 100).toFixed(0)}%</strong>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {totalPages > 1 && (
                  <div className="pagination">
                    <button 
                      className="pagination-btn"
                      disabled={currentPage === 1}
                      onClick={() => goToPage(currentPage - 1)}
                    >
                      ← Previous
                    </button>
                    
                    <div className="page-numbers">
                      {generatePageNumbers().map((pageNum) => (
                        <button
                          key={pageNum}
                          className={`page-btn ${currentPage === pageNum ? 'active' : ''}`}
                          onClick={() => goToPage(pageNum)}
                        >
                          {pageNum}
                        </button>
                      ))}
                    </div>
                    
                    <button 
                      className="pagination-btn"
                      disabled={currentPage === totalPages}
                      onClick={() => goToPage(currentPage + 1)}
                    >
                      Next →
                    </button>
                  </div>
                )}
              </>
            )}
          </section>
        )}
      </main>

      <footer className="footer">
        <small>🎬 CineMatch • Find Your Perfect Movie • {new Date().getFullYear()}</small>
      </footer>
    </div>
  );
}

export default App;