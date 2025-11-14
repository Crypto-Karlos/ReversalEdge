import { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [signals, setSignals] = useState([]);
  const [filter, setFilter] = useState('all');
  const [darkMode, setDarkMode] = useState(false);
  const [paused, setPaused] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const audioRef = useRef(null);

  useEffect(() => {
    audioRef.current = new Audio('https://assets.mixkit.co/sfx/preview/mixkit-alarm-digital-clock-beep-989.mp3');
   
    const ws = new WebSocket('wss://reversaledge-backend.onrender.com/ws');
   
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (soundEnabled) audioRef.current.play().catch(() => {});
      if (!paused) {
        setSignals(prev => [data, ...prev].slice(0, 100));
      }
    };

    return () => ws.close();
  }, [paused, soundEnabled]);

  const filtered = signals.filter(s =>
    filter === 'all' ||
    (filter === 'high' && s.confidence >= 85) ||
    (filter === 'buy' && s.type === 'buy') ||
    (filter === 'sell' && s.type === 'sell')
  );

  return (
    <div className={`App ${darkMode ? 'dark' : ''}`}>
      <header>
        <h1>ReversalEdge <span className="version">v2</span></h1>
        <p>AI-Powered Crypto Reversal Scanner • Binance Live Data</p>
      </header>

      <div className="controls">
        <select value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="all">All Signals</option>
          <option value="high">High Confidence (≥85%)</option>
          <option value="buy">BUY Only</option>
          <option value="sell">SELL Only</option>
        </select>
        <button onClick={() => setPaused(!paused)} className="icon">
          {paused ? 'Play' : 'Pause'}
        </button>
        <button onClick={() => setSoundEnabled(!soundEnabled)} className="icon">
          {soundEnabled ? 'Sound On' : 'Sound Off'}
        </button>
        <button onClick={() => setDarkMode(!darkMode)} className="icon">
          {darkMode ? 'Light Mode' : 'Dark Mode'}
        </button>
      </div>

      <div className="signals">
        {filtered.length === 0 ? (
          <p className="no-data">No signals match filter...</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Pair</th>
                <th>Signal</th>
                <th>Confidence</th>
                <th>Price</th>
                <th>Vol ×</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s, i) => (
                <tr key={i} className={s.type}>
                  <td>{new Date(s.time).toLocaleTimeString()}</td>
                  <td><strong>{s.pair}</strong></td>
                  <td className="signal">{s.type.toUpperCase()}</td>
                  <td>{s.confidence}%</td>
                  <td>${s.price}</td>
                  <td>{s.volume_spike}x</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <footer>
        <p>
          <strong>{signals.length}</strong> signals •
          <strong> {filtered.length}</strong> shown •
          Powered by <strong>Binance API</strong>
        </p>
      </footer>
    </div>
  );
}

export default App;
