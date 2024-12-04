from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import tweepy
import sqlite3
import time
from datetime import datetime, timedelta
from textblob import TextBlob
import matplotlib.pyplot as plt
import io

app = Flask(__name__)
CORS(app)

# Twitter API credentials
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
    conn.execute('''CREATE TABLE IF NOT EXISTS rate_limits
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     last_request_time TEXT,
                     request_count INTEGER)''')
    conn.commit()
    conn.close()

# Fetch rate limit data
def get_rate_limit_data():
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM rate_limits ORDER BY id DESC LIMIT 1")
    rate_limit = cursor.fetchone()
    conn.close()
    return rate_limit

# Update rate limit data
def update_rate_limit_data(request_count, last_request_time):
    conn = get_db_connection()
    conn.execute("INSERT INTO rate_limits (last_request_time, request_count) VALUES (?, ?)",
                 (last_request_time, request_count))
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

# Route to analyze tweets
@app.route('/analyze', methods=['GET'])
def analyze():
    country = request.args.get("country", default="India", type=str)

    # Get rate limit data
    rate_limit = get_rate_limit_data()
    if rate_limit:
        last_request_time_str = rate_limit[1]
        last_request_time = datetime.strptime(last_request_time_str, "%Y-%m-%d %H:%M:%S")
        request_count = rate_limit[2]
    else:
        last_request_time = datetime.now() - timedelta(days=1)  # If no data, consider 24 hours ago
        request_count = 0

    # Check if the rate limit has been exceeded (500 requests per 24 hours)
    time_remaining = datetime.now() - last_request_time
    if time_remaining < timedelta(days=1) and request_count >= 500:
        time_left = timedelta(days=1) - time_remaining
        return jsonify({
            "error": "Rate limit exceeded. Try again in a few minutes.",
            "time_remaining": str(time_left)
        }), 429

    # Update rate limit data
    new_request_count = request_count + 1
    update_rate_limit_data(new_request_count, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Fetch tweets from database or Twitter API
    conn = get_db_connection()
    cursor = conn.execute('''SELECT text, sentiment FROM tweets WHERE country = ?''', (country,))
    stored_tweets = cursor.fetchall()
    conn.close()

    if not stored_tweets:
        tweets = fetch_tweets_from_twitter(country)
        if not tweets:
            return jsonify({"error": "No tweets found"}), 404
        save_tweets_to_db(tweets, country)
        tweets = [{"text": tweet, "sentiment": analyze_sentiment(tweet)} for tweet in tweets]

    # Perform sentiment analysis
    sentiment_results = {"happy": 0, "depressed": 0, "neutral": 0}
    for tweet in tweets:
        sentiment_results[tweet["sentiment"]] += 1

    # Generate and send the chart
    chart = generate_chart(sentiment_results)
    return send_file(chart, mimetype="image/png")

if __name__ == '__main__':
    init_db()  # Ensure the database is created and initialized
    app.run(debug=True)
