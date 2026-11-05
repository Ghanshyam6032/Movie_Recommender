import streamlit as st
from main import MovieRecommender

st.set_page_config(page_title="Movie AI", layout="wide")

engine = MovieRecommender()

# ---------------- SESSION STATE ----------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None

if "search" not in st.session_state:
    st.session_state.search = ""

# ---------------- HOME FUNCTION ----------------
def go_home():
    st.session_state.page = "home"
    st.session_state.selected_movie = None
    st.session_state.search = ""   # ✅ IMPORTANT FIX

# ---------------- UI ----------------
st.title("🎬 Movie Recommender")

st.button("🏠 Home", on_click=go_home)

st.markdown("---")

# ---------------- SEARCH BAR (LIVE) ----------------
search = st.text_input("Search Movies", value=st.session_state.search)

st.session_state.search = search

# =====================================================
# 🏠 HOME PAGE
# =====================================================
if st.session_state.page == "home":

    # ✅ FIX: Always re-evaluate after reset
    if st.session_state.search.strip() != "":
        movies = engine.df[
            engine.df["title"].str.contains(
                st.session_state.search,
                case=False,
                na=False
            )
        ]
    else:
        movies = engine.df.head(10)

    st.subheader("Movies")

    cols = st.columns(5)

    for i, row in enumerate(movies.head(10).itertuples()):

        movie = engine.get_movie_details(row.title)

        with cols[i % 5]:

            if movie and movie["poster"]:
                st.image(movie["poster"], use_container_width=True)
            else:
                st.image("https://via.placeholder.com/300x450")

            st.write(row.title)

            if st.button("Open", key=f"home_{i}"):

                st.session_state.selected_movie = row.title
                st.session_state.page = "details"
                st.rerun()

# =====================================================
# 🎬 DETAILS PAGE
# =====================================================
elif st.session_state.page == "details":

    movie = engine.get_movie_details(st.session_state.selected_movie)

    if movie:

        col1, col2 = st.columns([1, 2])

        with col1:
            if movie["poster"]:
                st.image(movie["poster"])

        with col2:
            st.title(movie["title"])
            st.write("⭐", movie["rating"])
            st.write(movie["overview"])

        st.markdown("---")

        st.subheader("Recommended Movies")

        recs = engine.recommend(st.session_state.selected_movie, 10)

        if recs is not None:

            cols = st.columns(5)

            for i, row in enumerate(recs.itertuples()):

                with cols[i % 5]:

                    rec_movie = engine.get_movie_details(row.title)

                    if rec_movie and rec_movie["poster"]:
                        st.image(rec_movie["poster"])
                    else:
                        st.image("https://via.placeholder.com/300x450")

                    st.write(row.title)

                    if st.button("Open", key=f"rec_{i}"):

                        st.session_state.selected_movie = row.title
                        st.session_state.page = "details"
                        st.rerun()