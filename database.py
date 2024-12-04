from pymongo import MongoClient

# MongoDB connection
client = MongoClient("mongodb+srv://harrish:123@cluster0.mongodb.net/twitter_db?retryWrites=true&w=majority")
db = client.twitter_db

def save_tweet(tweet):
    """Save tweet to MongoDB."""
    db.tweets.insert_one(tweet)

def fetch_tweets_by_keyword(keyword):
    """Fetch tweets by keyword from MongoDB."""
    return list(db.tweets.find({"keyword": keyword}))
