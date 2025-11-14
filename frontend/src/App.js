import { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [signals, setSignals] = useState([]);
  const [ws, setWs] = useState(null);

  useEffect(() => {
    const socket = new WebSocket('wss://reversaledge-backend.onrender.com/ws');
   
    socket.onopen = () => {
      console.log('Connected to ReversalEdge Engine');
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setSignals(prev => [data, ...prev].slice(0, 50)); // Keep last 50
    };

    socket.onclose = () => {
      console.log('Disconnected');
    };

    setWs(socket);

    return () => socket.close();
  }, []);

  return (
    <div className="App">
      <header>
        <h1>ReversalEdge</h1>
        <p>Live Crypto Reversal Scanner</p>
      </header>

      <div className="signals">
        {signals.length === 0 ? (
          <p className="no-data">Waiting for signals...</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Pair</th>
                <th>Signal</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {signals.map((s, i) => (
                <tr key={i} className={s.type}>
                  <td>{new Date(s.time).toLocaleTimeString()}</td>
                  <td><strong>{s.pair}</strong></td>
                  <td className="signal">
                    {s.type === 'buy' ? 'BUY' : 'SELL'}
                  </td>
                  <td>{s.confidence}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <footer>
        <p>Powered by <strong>ReversalEdge Engine</strong> | {signals.length} signals</p>
      </footer>
    </div>
  );
}

export default App;
