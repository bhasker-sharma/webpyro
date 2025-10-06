import { useState, useEffect } from "react";
import axios from "axios";

function DeviceCell({ device }) {
  const [id, name, device_id, baud_rate, com_port, enabled] = device;
  const [temp, setTemp] = useState("--");

  // Fetch latest reading
  useEffect(() => {
    axios.get(`http://127.0.0.1:8000/api/readings/${device_id}?limit=1`)
      .then(res => {
        if (res.data.length > 0) {
          setTemp(res.data[0][1].toFixed(1));
        }
      })
      .catch(err => console.error(err));
  }, [device_id]);

  return (
    <div className="border rounded p-3 text-center shadow-sm" style={{ minHeight: "160px" }}>
      {/* Row 1: Device name + status dot */}
      <div className="d-flex justify-content-between align-items-center mb-2">
        <strong>{name}</strong>
        <span
          style={{
            width: "14px",
            height: "14px",
            borderRadius: "50%",
            backgroundColor: enabled ? "green" : "red",
            display: "inline-block"
          }}
        ></span>
      </div>

      {/* Row 2: ID + Port */}
      <div className="mb-2">
        <small>ID: {device_id}</small> <br />
        <small>{com_port} | {baud_rate}</small>
      </div>

      {/* Row 3: Temp Label */}
      <div><strong>Temp</strong></div>

      {/* Row 4: Big Bold Temperature */}
      <h2 className="fw-bold">{temp} °C</h2>
    </div>
  );
}

export default DeviceCell;
