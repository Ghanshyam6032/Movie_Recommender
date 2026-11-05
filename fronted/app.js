const API_BASE = "http://127.0.0.1:8000";

// App starting initialization anchor
document.addEventListener("DOMContentLoaded", () => {
    loadLandingDashboard();
});

// 1. Initial State: Load 10 Featured Cards on Launch / Reset State
async function loadLandingDashboard() {
    const mainSection = document.getElementById("activeDetailSection");
    const gridSection = document.getElementById("recommendationGridSection");
    const gridTitle = document.getElementById("gridTitle");
    const searchBar = document.getElementById("searchBar");

    // Clear search bar input text on home reset
    if (searchBar) searchBar.value = "";

    mainSection.innerHTML = ""; 
    gridSection.innerHTML = "<div class='shimmer-loader'></div><div class='shimmer-loader'></div>";
    gridTitle.textContent = "Featured Curations";

    try {
        const response = await fetch(`${API_BASE}/initial-movies`);
        const data = await response.json();
        
        gridSection.innerHTML = "";
        renderGridItems(data.movies);
    } catch (err) {
        gridSection.innerHTML = `<p class="error-msg">Failed to process engine logs: ${err.message}</p>`;
    }
}

// 2. Active State Transition: Trigger Loop Execution 
async function selectMoviePipeline(movieTitle) {
    const mainSection = document.getElementById("activeDetailSection");
    const gridSection = document.getElementById("recommendationGridSection");
    const gridTitle = document.getElementById("gridTitle");

    window.scrollTo({ top: 0, behavior: 'smooth' });
    mainSection.innerHTML = "<div class='shimmer-loader' style='height: 300px;'></div>";
    gridSection.innerHTML = "";
    gridTitle.textContent = "Generating Tailored Relational Nodes...";

    try {
        const response = await fetch(`${API_BASE}/recommend`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title: movieTitle })
        });

        if (!response.ok) throw new Error("Target cluster mapping error.");
        const data = await response.json();

        // Render Hero Detail Showcase Layer
        renderHeroCard(data.searched_movie);

        // Update Grid Context Header & Items
        gridTitle.textContent = `Because you interacted with "${data.searched_movie.title}":`;
        renderGridItems(data.recommendations);

    } catch (err) {
        mainSection.innerHTML = `<p class="error-msg">Pipeline Exception: ${err.message}</p>`;
        gridTitle.textContent = "Standby Logs Error";
    }
}

// UI Render Helpers
function renderHeroCard(movie) {
    const mainSection = document.getElementById("activeDetailSection");
    const year = movie.release_date ? movie.release_date.split('-')[0] : 'N/A';
    const rating = movie.rating ? movie.rating.toFixed(1) : '0.0';
    const posterUrl = movie.poster || 'https://via.placeholder.com/300x450?text=No+Poster+Found';

    mainSection.innerHTML = `
        <div class="hero-showcase-card">
            <img src="${posterUrl}" alt="${movie.title}" class="hero-poster" />
            <div class="hero-content">
                <span class="badge-accent">Active Node Profile</span>
                <h2 class="hero-title">${movie.title} <span class="hero-year">(${year})</span></h2>
                <div class="meta-row">
                    <span class="meta-item">⭐ ${rating} / 10</span>
                    <span class="meta-item">📅 Released: ${movie.release_date}</span>
                </div>
                <p class="hero-overview">${movie.overview}</p>
            </div>
        </div>
    `;
}

function renderGridItems(movieArray) {
    const gridSection = document.getElementById("recommendationGridSection");
    gridSection.innerHTML = "";

    movieArray.forEach(movie => {
        const year = movie.release_date ? movie.release_date.split('-')[0] : 'N/A';
        const rating = movie.rating ? movie.rating.toFixed(1) : '0.0';
        const posterUrl = movie.poster || 'https://via.placeholder.com/150x225?text=No+Image';
        
        const sanitizedTitle = movie.title.replace(/'/g, "\\'");

        const card = document.createElement("div");
        card.className = "grid-movie-card";
        card.setAttribute("onclick", `selectMoviePipeline('${sanitizedTitle}')`);
        card.innerHTML = `
            <div class="poster-container">
                <img src="${posterUrl}" alt="${movie.title}" class="grid-poster" loading="lazy" />
                <div class="grid-card-overlay">
                    <span class="overlay-action">Explore Node ➔</span>
                </div>
                <div class="grid-rating-tag">⭐ ${rating}</div>
            </div>
            <div class="grid-info">
                <h4 class="grid-movie-title">${movie.title}</h4>
                <p class="grid-movie-year">${year}</p>
            </div>
        `;
        gridSection.appendChild(card);
    });
}

function executeSearchInput() {
    const input = document.getElementById("searchBar");
    const title = input.value.trim();
    if (!title) return;
    selectMoviePipeline(title);
}