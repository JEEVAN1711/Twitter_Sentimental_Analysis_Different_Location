import React, { useState } from 'react';

const Fetcher = () => {
  const [country, setCountry] = useState('');
  const [tweets, setTweets] = useState([]);

  const fetchTweets = () => {
    fetch(`/analyze?country=${country}`)
      .then(response => response.json())
      .then(data => setTweets(data))
      .catch(error => console.error('Error fetching tweets:', error));
  };

  return (
    <div>
      <input
        type="text"
        value={country}
        onChange={(e) => setCountry(e.target.value)}
        placeholder="Enter country"
      />
      <button onClick={fetchTweets}>Fetch Tweets</button>
      <div>
        {tweets.length > 0 && (
          <ul>
            {tweets.map((tweet, index) => (
              <li key={index}>{tweet.text} - {tweet.sentiment}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default Fetcher;
