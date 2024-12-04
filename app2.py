from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import tweepy
import sqlite3
from textblob import TextBlob
import matplotlib.pyplot as plt
import io
import time
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Twitter API credentials (replace with your actual credentials)
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAJltvwEAAAAAsm2XgUJ8rv0o5HbUT2Mv1gssDuA%3DYLd4abEN9bBYThkT6K1TgFybzSLq5WxLgf7wd54poO8yp5TWYs"
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# SQLite database connection function
def get_db_connection():
    conn = sqlite3.connect('tweets.db')
    return conn

# Create database table if it doesn't exist
def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS tweets
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     text TEXT,
                     sentiment TEXT,
                     country TEXT)''')
    conn.commit()
    conn.close()

# Fetch tweets from Twitter API
def fetch_tweets_from_twitter(country):
    query = f"{country} mental health -is:retweet lang:en"
    try:
        response = client.search_recent_tweets(query=query, max_results=100)
        return [tweet.text for tweet in response.data] if response.data else []
    except tweepy.TooManyRequests:
        print("Rate limit reached. Waiting for 5 seconds...")
        time.sleep(5)
        return fetch_tweets_from_twitter(country)

# Analyze sentiment of tweets
def analyze_sentiment(tweet):
    analysis = TextBlob(tweet).sentiment.polarity
    if analysis > 0:
        return "happy"
    elif analysis < 0:
        return "depressed"
    else:
        return "neutral"

# Save tweets to database
def save_tweets_to_db(tweets, country):
    conn = get_db_connection()
    for tweet in tweets:
        sentiment = analyze_sentiment(tweet)
        conn.execute('''INSERT INTO tweets (text, sentiment, country)
                        VALUES (?, ?, ?)''', (tweet, sentiment, country))
    conn.commit()
    conn.close()

# Fetch tweets from the database
def fetch_tweets_from_db(country):
    conn = get_db_connection()
    cursor = conn.execute('''SELECT text, sentiment FROM tweets WHERE country = ?''', (country,))
    tweets = cursor.fetchall()
    conn.close()
    return tweets

# Generate sentiment chart
def generate_chart(data):
    labels = list(data.keys())
    values = list(data.values())
    plt.bar(labels, values, color=['blue', 'purple', 'gray'])
    plt.xlabel("Sentiment")
    plt.ylabel("Number of Tweets")
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    return img

# Define cooldown for API requests (3 minutes)
last_request_time = None

@app.route('/analyze', methods=['GET'])
def analyze():
    global last_request_time
    current_time = datetime.now()

    # If last request time exists, check if 3 minutes have passed
    if last_request_time and (current_time - last_request_time) < timedelta(minutes=3):
        wait_time = (timedelta(minutes=3) - (current_time - last_request_time)).seconds
        return jsonify({"error": "Please wait", "wait_time": wait_time})

    country = request.args.get("country", default="India", type=str)

    # Fetch tweets from the database first
    stored_tweets = fetch_tweets_from_db(country)
    if stored_tweets:
        tweets = [{"text": text, "sentiment": sentiment} for text, sentiment in stored_tweets]
    else:
        # Fetch tweets from Twitter API if not stored
        tweets = fetch_tweets_from_twitter(country)
        if not tweets:
            return jsonify({"error": "No tweets found"}), 404
        save_tweets_to_db(tweets, country)

    # Perform sentiment analysis
    sentiment_results = {"happy": 0, "depressed": 0, "neutral": 0}
    for tweet in tweets:
        sentiment = tweet["sentiment"] if "sentiment" in tweet else analyze_sentiment(tweet["text"])
        sentiment_results[sentiment] += 1

    # Generate and send the chart
    chart = generate_chart(sentiment_results)

    # Update last request time
    last_request_time = current_time

    return send_file(chart, mimetype="image/png")


if __name__ == '__main__':
    init_db()  # Ensure the database is created and initialized
    app.run(debug=True)
