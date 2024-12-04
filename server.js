require('dotenv').config();
const express = require('express');
const { TwitterApi } = require('twitter-api-v2');
const Sentiment = require('sentiment');
const { ChartJSNodeCanvas } = require('chartjs-node-canvas');
const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');

// Initialize Express server
const app = express();
const port = 5000;

// Initialize Twitter API client
const client = new TwitterApi({
    appKey: process.env.TWITTER_API_KEY,
    appSecret: process.env.TWITTER_API_SECRET_KEY,
    accessToken: process.env.TWITTER_ACCESS_TOKEN,
    accessSecret: process.env.TWITTER_ACCESS_TOKEN_SECRET,
});

// Initialize sentiment analysis and ChartJS canvas
const sentiment = new Sentiment();
const chartJSNodeCanvas = new ChartJSNodeCanvas({ width: 400, height: 400 });

// Initialize SQLite Database
const db = new sqlite3.Database('tweets.db', (err) => {
    if (err) console.error('Error opening database', err.message);
    else console.log('Connected to SQLite database');
});

// Create table for storing tweets
db.run(`
    CREATE TABLE IF NOT EXISTS tweets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        country TEXT,
        sentimentScore INTEGER,
        sentimentLabel TEXT
    )
`);

// Function to fetch tweets with rate limit handling
async function fetchTweets(query) {
    try {
        const { data } = await client.v2.search(query, {
            max_results: 10,
        });
        return data;
    } catch (error) {
        console.error('Error fetching tweets:', error);
        if (error.code === 429) {
            console.log('Rate limit reached. Waiting...');
            await new Promise((resolve) => setTimeout(resolve, 60000));
            return fetchTweets(query);
        }
    }
}

// Analyze sentiment and store tweets
function analyzeAndStoreTweets(tweets, country) {
    const sentimentResults = { happy: 0, depressed: 0 };

    tweets.forEach((tweet) => {
        const analysis = sentiment.analyze(tweet.text);
        const score = analysis.score;
        const label = score > 0 ? 'happy' : score < 0 ? 'depressed' : 'neutral';

        // Update sentiment count
        if (label === 'happy') sentimentResults.happy += 1;
        else if (label === 'depressed') sentimentResults.depressed += 1;

        // Store tweet in database
        db.run(
            `INSERT INTO tweets (text, country, sentimentScore, sentimentLabel) VALUES (?, ?, ?, ?)`,
            [tweet.text, country, score, label],
            (err) => {
                if (err) console.error('Error inserting tweet:', err.message);
            }
        );
    });

    return sentimentResults;
}

// Generate chart image based on sentiment analysis
async function generateSentimentChart(data) {
    const configuration = {
        type: 'pie',
        data: {
            labels: ['Happy', 'Depressed'],
            datasets: [
                {
                    data: [data.happy, data.depressed],
                    backgroundColor: ['#4caf50', '#f44336'],
                },
            ],
        },
    };

    return chartJSNodeCanvas.renderToBuffer(configuration);
}

// API endpoint to fetch, analyze, and store tweets
app.get('/sentiment/:country', async (req, res) => {
    const country = req.params.country;

    try {
        const tweets = await fetchTweets(country);

        if (!tweets) {
            return res.status(404).send('No tweets found.');
        }

        const sentimentResults = analyzeAndStoreTweets(tweets, country);
        const chartImage = await generateSentimentChart(sentimentResults);

        res.set('Content-Type', 'image/png');
        res.send(chartImage);
    } catch (error) {
        res.status(500).send('Error processing sentiment analysis.');
    }
});

// Start the server
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
