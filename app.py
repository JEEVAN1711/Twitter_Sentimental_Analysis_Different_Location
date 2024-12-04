from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from tweepy import Client
from textblob import TextBlob
import matplotlib.pyplot as plt
import io
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Set up Twitter API credentials
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAJltvwEAAAAAsm2XgUJ8rv0o5HbUT2Mv1gssDuA%3DYLd4abEN9bBYThkT6K1TgFybzSLq5WxLgf7wd54poO8yp5TWYs"
twitter_client = Client(bearer_token=BEARER_TOKEN)

# Function to fetch tweets based on country
def fetch_tweets(country):
    query = f"{country} mental health -is:retweet lang:en"
    tweets = twitter_client.search_recent_tweets(query=query, max_results=20)
    return [tweet.text for tweet in tweets.data] if tweets.data else []

# Function to perform sentiment analysis
def analyze_sentiments(tweets):
    results = {"happy": 0, "depressed": 0, "neutral": 0}

    for tweet in tweets:
        analysis = TextBlob(tweet).sentiment.polarity
        if analysis > 0:
            results["happy"] += 1
        elif analysis < 0:
            results["depressed"] += 1
        else:
            results["neutral"] += 1

    return results

# Function to generate a chart
def generate_chart(data):
    labels = list(data.keys())
    values = list(data.values())

    plt.figure(figsize=(6, 4))
    plt.bar(labels, values, color=['blue', 'purple', 'gray'])
    plt.title("Sentiment Analysis")
    plt.xlabel("Sentiment")
    plt.ylabel("Number of Tweets")
    plt.tight_layout()

    # Save chart to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    return img

# Route to fetch tweets and perform sentiment analysis
@app.route('/analyze', methods=['GET'])
def analyze():
    country = request.args.get("country", default="India", type=str)
    tweets = fetch_tweets(country)

    if not tweets:
        return jsonify({"error": "No tweets found"}), 404

    sentiment_results = analyze_sentiments(tweets)
    chart = generate_chart(sentiment_results)

    return send_file(chart, mimetype="image/png")

# Start the Flask server
if __name__ == '__main__':
    app.run(debug=True)
