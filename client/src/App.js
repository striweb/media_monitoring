import React, { useEffect, useState } from 'react';

function App() {
  const [alerts, setAlerts] = useState([]);

  const fetchAlerts = () => {
    fetch('http://135.181.250.83:5000/alerts')
      .then(response => response.json())
      .then(data => setAlerts(data.alerts))
      .catch(error => console.error('Error fetching data: ', error));
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="App">
      <h1>Alerts</h1>
      {alerts.map((alert, index) => (
        <div key={index}>
          <h2>{alert.title}</h2>
          <p dangerouslySetInnerHTML={{ __html: alert.description }}></p>
          <p>Published on: {new Date(alert.pub_date).toLocaleDateString()}</p>
          <a href={alert.link} target="_blank" rel="noopener noreferrer">Read more</a>
          {alert.media_urls && alert.media_urls.map((url, index) => (
            <img key={index} src={url} alt="media" style={{ width: '100%', height: 'auto' }} />
          ))}
        </div>
      ))}
    </div>
  );
}

export default App;
