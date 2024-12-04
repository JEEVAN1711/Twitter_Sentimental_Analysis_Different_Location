import React, { useState, useEffect } from 'react';
import './App.css'; // Create a separate CSS file for styling

function App() {
  const [sentimentData, setSentimentData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [timeRemaining, setTimeRemaining] = useState(0); // Time remaining for next request

  useEffect(() => {
    // Check the remaining time every second
    const timer = setInterval(() => {
      if (timeRemaining > 0) {
        setTimeRemaining(prevTime => prevTime - 1);
      }
    }, 1000);

    return () => clearInterval(timer); // Clean up the interval on unmount
  }, [timeRemaining]);

  const fetchSentiment = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("http://127.0.0.1:5000/analyze?country=India");
      if (!response.ok) {
        const errorData = await response.json();
        if (errorData.time_remaining) {
          setTimeRemaining(parseInt(errorData.time_remaining)); // Set the remaining time if error
        }
        throw new Error(errorData.error || "Error fetching data");
      }
      const chartImage = await response.blob();
      const imageUrl = URL.createObjectURL(chartImage);
      setSentimentData(imageUrl);
      setTimeRemaining(180); // Reset time to 3 minutes after successful request
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header>
        <img
          src="https://upload.wikimedia.org/wikipedia/commons/6/60/X_Logo_%28blue%29.svg" 
          alt="X Logo"
          className="logo"
        />
        <h1>Country Sentiment Analysis</h1>
      </header>

      <div className="content">
        <button onClick={fetchSentiment} disabled={loading || timeRemaining > 0}>
          {loading ? 'Analyzing...' : 'Analyze Sentiment'}
        </button>
        {error && <p style={{ color: 'red' }}>{error}</p>}

        {timeRemaining > 0 && (
          <p>Next request available in: {Math.floor(timeRemaining / 60)}m {timeRemaining % 60}s</p>
        )}

        {sentimentData && (
          <div>
            <img src={sentimentData} alt="Sentiment Chart" />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
