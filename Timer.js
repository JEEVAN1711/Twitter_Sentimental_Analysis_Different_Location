import React, { useState, useEffect } from 'react';

const Timer = () => {
  const [timestamp, setTimestamp] = useState(null);

  useEffect(() => {
    fetch('/timer')
      .then(response => response.json())
      .then(data => setTimestamp(data.timestamp))
      .catch(error => console.error('Error fetching timestamp:', error));
  }, []);

  return (
    <div>
      <h2>Last Timestamp: {timestamp ? timestamp : 'Loading...'}</h2>
    </div>
  );
};

export default Timer;
