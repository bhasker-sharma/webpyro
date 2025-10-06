import { useEffect, useState } from "react";
import axios from "axios";
import DeviceCell from "../components/DeviceCell";
import GraphSection from "../components/GraphSection";

function Dashboard() {
  const [devices, setDevices] = useState([]);

  useEffect(() => {
    axios.get("http://127.0.0.1:8000/api/devices/")
      .then(res => setDevices(res.data))
      .catch(err => console.error("Error fetching devices:", err));
  }, []);

  return (
    <div className="container-fluid mt-4">
      <h2 className="mb-3">🔥 Pyrometer Dashboard</h2>

      {/* 🔹 Top Device Grid */}
      <div className="row">
        {devices.map(d => (
          <div className="col-md-3 col-sm-6 mb-3" key={d[0]}>
            <DeviceCell device={d} />
          </div>
        ))}
      </div>

      <hr />

      {/* 🔹 Bottom Graph Section */}
      <GraphSection devices={devices} />
    </div>
  );
}

export default Dashboard;
