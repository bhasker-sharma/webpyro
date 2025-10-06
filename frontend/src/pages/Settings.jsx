import { useState } from "react";
import axios from "axios";

function Settings() {
  const [name, setName] = useState("");
  const [deviceId, setDeviceId] = useState("");
  const [baudRate, setBaudRate] = useState("9600");
  const [comPort, setComPort] = useState("COM1");

  const handleSubmit = (e) => {
    e.preventDefault();
    axios.post("http://127.0.0.1:8000/api/devices/", null, {
      params: { name, device_id: deviceId, baud_rate: baudRate, com_port: comPort, enabled: true }
    })
    .then(() => alert("✅ Device added! Refresh dashboard to see it."))
    .catch(err => console.error(err));
  };

  return (
    <div className="container mt-4">
      <h2>⚙️ Device Settings</h2>
      <form onSubmit={handleSubmit} className="mt-3">
        <input className="form-control mb-2" placeholder="Device Name" value={name} onChange={e => setName(e.target.value)} />
        <input className="form-control mb-2" placeholder="Device ID" value={deviceId} onChange={e => setDeviceId(e.target.value)} />
        <input className="form-control mb-2" placeholder="Baud Rate" value={baudRate} onChange={e => setBaudRate(e.target.value)} />
        <input className="form-control mb-2" placeholder="COM Port" value={comPort} onChange={e => setComPort(e.target.value)} />
        <button type="submit" className="btn btn-primary">Add Device</button>
      </form>
    </div>
  );
}

export default Settings;
