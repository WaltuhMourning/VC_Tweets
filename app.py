import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import json
import random
from io import BytesIO

# ---------------------------------
# Load Data
# ---------------------------------
@st.cache_data
def load_data():
    tweets_per_day = pd.read_csv("tweets_per_day.csv")
    tweets_per_day_by_user = pd.read_csv("tweets_per_day_by_user.csv")
    
    with open("overall_wordcloud.txt", "r", encoding="utf-8") as f:
        overall_wordcloud_text = f.read()
    with open("user_wordcloud_text.json", "r", encoding="utf-8") as f:
        user_wordcloud_text = json.load(f)
    with open("markov_chains.json", "r", encoding="utf-8") as f:
        markov_chains = json.load(f)
        
    return tweets_per_day, tweets_per_day_by_user, overall_wordcloud_text, user_wordcloud_text, markov_chains

tweets_per_day, tweets_per_day_by_user, overall_wordcloud_text, user_wordcloud_text, markov_chains = load_data()

# ---------------------------------
# Helper Functions
# ---------------------------------
def filter_by_date(data, start_date, end_date):
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    return data[(data["Date"] >= pd.to_datetime(start_date)) & (data["Date"] <= pd.to_datetime(end_date))]

def generate_markov_tweet(chain, length=20, seed=None):
    """Generate a Markov chain-based tweet of a given length. 
       If 'seed' is provided (and exists in the chain), start from that seed word.
       Otherwise, start from a random word."""
    if not chain:
        return "Not enough data to generate a tweet."
    
    # Use seed if provided and valid
    if seed and seed in chain:
        word = seed
    else:
        word = random.choice(list(chain.keys()))
    
    tweet_words = [word]
    for _ in range(length - 1):
        next_words = chain.get(word, [])
        if not next_words:
            break
        word = random.choice(next_words)
        tweet_words.append(word)
    return " ".join(tweet_words)


# ---------------------------------
# Page Title and Description
# ---------------------------------
st.title("4E News from the Hill: Twitter Analysis Dashboard")

st.markdown(
    """
    **Data Range**: December 31, 2023 - December 23, 2024  
    *Welcome to our Twitter Analysis Tool powered by 4E News from the Hill!  
    Explore tweets, word clouds, and a Markov chain tweet simulator.*
    """
)

# ---------------------------------
# Sidebar: Selection Controls
# ---------------------------------
st.sidebar.header("Filters & Settings")

default_start_date = "2023-12-31"
default_end_date = "2024-12-23"

# User selection
usernames = tweets_per_day_by_user["Author"].unique()
selected_user = st.sidebar.selectbox("Select a Username", ["Overall"] + list(usernames))

# Date range selection
start_date = st.sidebar.date_input("Start Date", pd.to_datetime(default_start_date))
end_date = st.sidebar.date_input("End Date", pd.to_datetime(default_end_date))

min_date = pd.to_datetime(tweets_per_day["Date"]).min().date()
max_date = pd.to_datetime(tweets_per_day["Date"]).max().date()
date_range = st.sidebar.slider(
    "Adjust Date Range (Slider)",
    min_value=min_date,
    max_value=max_date,
    value=(pd.to_datetime(default_start_date).date(), pd.to_datetime(default_end_date).date())
)
start_date, end_date = date_range

# Rolling average checkbox
show_rolling_avg = st.sidebar.checkbox("Show 7-Day Rolling Average")

st.sidebar.markdown("---")
st.sidebar.write("Developed for Streamlit Cloud")

# ---------------------------------
# Main Content
# ---------------------------------
if selected_user == "Overall":
    # ---------------------------------
    # Overall Tweets per Day
    # ---------------------------------
    st.subheader("Overall Tweets per Day")
    filtered_data = filter_by_date(tweets_per_day, start_date, end_date)

    fig, ax = plt.subplots()
    ax.plot(
        filtered_data["Date"],
        filtered_data["Tweet Count"],
        marker="o",
        markersize=3,
        label="Daily Tweet Count"
    )

    # Optionally show rolling average
    if show_rolling_avg:
        filtered_data["RollingAvg"] = filtered_data["Tweet Count"].rolling(window=7).mean()
        ax.plot(
            filtered_data["Date"],
            filtered_data["RollingAvg"],
            color="red",
            linewidth=2,
            label="7-Day Rolling Avg"
        )

    ax.set_xlabel("Date")
    ax.set_ylabel("Tweet Count")
    ax.set_title("Overall Tweets Per Day")
    ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=10))
    plt.xticks(rotation=45)
    plt.legend()
    st.pyplot(fig)

    # ---------------------------------
    # Overall Word Cloud
    # ---------------------------------
    st.subheader("Overall Word Cloud")
    wc = WordCloud(width=800, height=400, background_color="white").generate(overall_wordcloud_text)
    st.image(wc.to_array(), use_container_width=True)

    st.download_button(
        label="Download Word Cloud",
        data=BytesIO(wc.to_image().tobytes()),
        file_name="overall_wordcloud.png",
        mime="image/png"
    )

    # ---------------------------------
    # Total Tweets (Selected Range)
    # ---------------------------------
    total_tweets = int(filtered_data["Tweet Count"].sum())

    st.metric(label="Total Tweets (Selected Range)", value=f"{total_tweets:,}")

else:
    # ---------------------------------
    # User-Specific Tweets Per Day
    # ---------------------------------
    st.subheader(f"Tweets Per Day for {selected_user}")
    user_data = tweets_per_day_by_user[tweets_per_day_by_user["Author"] == selected_user]
    filtered_data = filter_by_date(user_data, start_date, end_date)

    fig, ax = plt.subplots()
    ax.plot(
        filtered_data["Date"],
        filtered_data["Tweet Count"],
        marker="o",
        markersize=3,
        color="green",
        label="Daily Tweet Count"
    )

    # Optionally show rolling average
    if show_rolling_avg:
        filtered_data["RollingAvg"] = filtered_data["Tweet Count"].rolling(window=7).mean()
        ax.plot(
            filtered_data["Date"],
            filtered_data["RollingAvg"],
            color="red",
            linewidth=2,
            label="7-Day Rolling Avg"
        )

    ax.set_xlabel("Date")
    ax.set_ylabel("Tweet Count")
    ax.set_title(f"Tweets Per Day for {selected_user}")
    ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=10))
    plt.xticks(rotation=45)
    plt.legend()
    st.pyplot(fig)

    # ---------------------------------
    # User-Specific Word Cloud
    # ---------------------------------
    st.subheader(f"Word Cloud for {selected_user}")
    user_text = user_wordcloud_text.get(selected_user, "")

    if user_text:
        wc = WordCloud(width=800, height=400, background_color="white").generate(user_text)
        st.image(wc.to_array(), use_container_width=True)

        st.download_button(
            label=f"Download Word Cloud for {selected_user}",
            data=BytesIO(wc.to_image().tobytes()),
            file_name=f"{selected_user}_wordcloud.png",
            mime="image/png"
        )
    else:
        st.write("No data available for this user.")

    # ---------------------------------
    # Markov Chain Generated Tweet
    # ---------------------------------
    st.subheader(f"Generated Tweet in the Style of {selected_user}")

    chain = markov_chains.get(selected_user, {})

    with st.expander("Tweet Generation Settings"):
        tweet_length = st.slider("Select Tweet Length (in words)", min_value=5, max_value=50, value=20, step=5)
        seed_text = st.text_input("Optional Seed Text (Experimental)", "")

    if st.button("Generate Tweet"):
        generated_tweet = generate_markov_tweet(chain, length=tweet_length, seed=seed_text)
        st.markdown(f"> **{generated_tweet}**")  # Block quote style

    # ---------------------------------
    # Polished Metrics: Total Tweets & Most Active Day
    # ---------------------------------
    if not filtered_data.empty:
        total_tweets = int(filtered_data["Tweet Count"].sum())
        most_active_day = filtered_data.loc[filtered_data["Tweet Count"].idxmax()]

        # Create two columns for metrics
        col1, col2 = st.columns(2)
        col1.metric(
            label="Total Tweets (Selected Range)",
            value=f"{total_tweets:,}"
        )
        col2.metric(
            label="Most Active Day",
            value=most_active_day["Date"].strftime("%Y-%m-%d"),
            delta=f"{int(most_active_day['Tweet Count'])} tweets"
        )
    else:
        st.write("No data in the selected range.")
