import React, { useState, useEffect } from 'react';

function App() {
  const [msg, setMsg] = useState("Connecting...");
  const [input, setInput] = useState("");

  useEffect(() => {
    const ws = new WebSocket((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws');
    ws.onopen = () => setMsg("Connected! Type and send a test.");
    ws.onmessage = (e) => setMsg("Server: " + e.data);
    ws.onerror = () => setMsg("Failed");
    return () => ws.close();
  }, []);

  const send = () => {
    const ws = new WebSocket((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws');
    ws.onopen = () => ws.send(input);
  };

  return (
    <div style={{padding:40, fontFamily:'Arial'}}>
      <h1>ReversalEdge</h1>
      <p><strong>Status:</strong> {msg}</p>
      <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Type test" style={{width:300, padding:10}} />
      <button onClick={send} style={{padding:10, marginLeft:10}}>Send</button>
    </div>
  );
}

export default App;
