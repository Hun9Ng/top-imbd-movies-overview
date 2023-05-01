import pandas as pd
import plotly.express as px
import streamlit as st
import numpy as np
from streamlit_option_menu import option_menu

#Dataset: https://www.kaggle.com/datasets/karkavelrajaj/imdb-top-250-movies
#Icon1: https://www.webfx.com/tools/emoji-cheat-sheet/
#Icon2: https://icons.getbootstrap.com/

st.set_page_config(page_title='Movie Dashboard',
                   page_icon=':film_frames:',
                   layout='wide')

df=pd.read_csv("movies.csv", dtype={"year":str})

# ----- DATA PROCESSING -----

#CONVERTING DURATION
duration_mins=[]
for i in df["duration"].values:
    if 'h' in i and 'm' in i:
        duration_mins.append((int(i.split(' ')[0].replace('h',''))*60) + \
                        int(i.split(' ')[1].replace('m','')))
    if 'h' in i and 'm' not in i:
        duration_mins.append((int(i.replace('h',''))*60))
    if 'h' not in i and 'm' in i:
        duration_mins.append(int(i.replace('m','')))
df.loc[:,'duration_mins'] = duration_mins
min_duration = int(np.floor(df["duration_mins"].min()/10)*10)
max_duration = int(np.ceil(df["duration_mins"].max()/10)*10)

#CONVERTING IMBD_VOTES
imbd_votes = []
for i in df["imbd_votes"].values:
    imbd_votes.append(int(i.replace(',','')))
df.loc[:,"imbd_votes"] = imbd_votes

#FINDING UNIQUE GENRE
unique_genre = []
for i in df["genre"].values:
    unique_genre += i.split(',')
unique_genre =  sorted(list(set(unique_genre)))
unique_genre_new = ["All"] + sorted(list(set(unique_genre)))

#Adding "All" to each genre
df.loc[:,"genre_new"] = df["genre"].astype(str) + ",All"

# ----- MAIN MENU -----
# with st.sidebar: #if you want to locate the menu to side bar
selected = option_menu(menu_title=None, #requỉed
                           options=["Overview", "Data Table"], #requỉed
                           icons=["book","house"],
                           menu_icon="cast",
                           default_index=0,
                           orientation="horizontal")
if selected == "Overview":
    st.title(f":bar_chart: {selected}")
    st.markdown("##")
if selected == "Data Table":
    st.title(f":clipboard: {selected}")
    st.markdown("##")

# ----- SIDEBAR FILTER -----

st.sidebar.header("Please Filter Here:")

genre = st.sidebar.selectbox("GENRE",
                             options=unique_genre_new)

df_year = df.sort_values("year",ascending=False)
unique_year=list(df_year["year"].unique())
unique_year_new = ["All the years"] + unique_year
year = st.sidebar.multiselect("YEAR",
                              options=unique_year_new,
                              default="All the years")
if "All the years" in year:
    year=unique_year

duration = st.sidebar.slider("DURATION (minutes)",
                             min_value=min_duration,
                             max_value=max_duration,
                             step = 10,
                             value=max_duration)

for i in unique_genre_new:
    if i in genre:
        df_selection = df[(df["genre_new"].str.contains(i))&(df["year"].isin(year))&(df["duration_mins"]<=duration)][['rank', 'movie_id','title','year','link','imbd_votes',
       'imbd_rating', 'certificate', 'duration', 'genre', 'cast_id',
       'cast_name', 'director_id', 'director_name', 'writer_id', 'writer_name',
       'storyline', 'user_id', 'user_name', 'review_id', 'review_title',
       'review_content']]


# ----- MAINPAGE -----

#DATA TABLE
if selected == "Data Table":
    df_selection

#OVERVIEW
#RATING & MOVIE NUMBERS
#Add rating_votes column
df_selection.loc[:,"rating_votes"] = df_selection["imbd_rating"] * df_selection["imbd_votes"]
avg_imbd_rating = round(df_selection["rating_votes"].sum()/df_selection["imbd_votes"].sum(),1)
avg_imbd_rating_star = ":star:" * int(round(avg_imbd_rating,0))
movie_number = df_selection["title"].count()

if selected == "Overview":
    left_column,right_column = st.columns(2)
    with left_column:
        st.subheader("Avg IMDb Rating")
        st.subheader(f"{avg_imbd_rating} {avg_imbd_rating_star}")
    with right_column:
        st.subheader("Number of movies")
        st.subheader(f"{movie_number}")

st.markdown("---")

#MOVIES BY YEAR
#Only considering years with movie >= 4
movies_by_year = pd.DataFrame(df_selection.groupby("year").agg({"rating_votes":"sum","imbd_votes":"sum","title":"count"})).query("title>=4")
movies_by_year.loc[:,"avg_rating"] = round(movies_by_year["rating_votes"]/movies_by_year["imbd_votes"],1)
movies_by_year_filtered=movies_by_year[["avg_rating","title"]].sort_values(["avg_rating","title"],ascending=[False, False])
movies_by_year_filtered = movies_by_year_filtered.rename(columns={"title":"Number of movies","avg_rating":"Avg IMDb rating"})
#Best title of each year
considered_year = list(pd.DataFrame(df_selection.groupby("year")["title"].count()).query("title>=4").index)
#the dataset should be sort by rating first (ascending = False)
best_each_year = df_selection[df_selection["year"].isin(considered_year)].groupby("year").head(1).reset_index(drop=True)[["year","title"]]
best_each_year = best_each_year.rename(columns={"title":"Best title of the year"})
#Join 2 tables
movies_by_year_joined = movies_by_year_filtered.merge(best_each_year, on="year")

#MOVIES BY GENRE
#Find list of unique genre
genre_stats = []
for i in unique_genre:
    numb = 0
    for j in df_selection['genre'].values:
        if i in j:
            numb += 1
    genre_stats.append([i,numb])

genre_stats = pd.DataFrame(genre_stats, columns=["genre","amount"])
genre_stats_sorted = genre_stats.sort_values("amount", ascending=False).reset_index(drop=True)

fig_movies_by_genre = px.bar(
    genre_stats_sorted,
    x="genre",
    y="amount",
    labels={"amount":"Number of movies","genre":"Movie genre"},
    orientation="v",
    title="<b>Movies by genre</b>",
    color_discrete_sequence=["#0083B8"] * len(genre_stats_sorted),
    template="plotly_white"
)
fig_movies_by_genre.update_layout(title_font_size=29
                                  # ,font_family="Courier New",
                                  # font_color="blue",
                                  # title_font_family="Times New Roman",
                                  # title_font_color="red",
                                  # legend_title_font_color="green"
                                  )

if selected == "Overview":
    left_column, right_column = st.columns(2)
    with left_column:
        st.subheader("Movies by year", help="Only show years having more than 3 movies")
        movies_by_year_joined
    right_column.plotly_chart(fig_movies_by_genre, use_container_width=True)

# ----- HIDE STREAMLIT STYLE -----

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)