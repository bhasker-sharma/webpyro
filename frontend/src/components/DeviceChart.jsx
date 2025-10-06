import { useEffect, useState } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

function DeviceChart({ deviceId }) {
  const [data, setData] = useState([]);

  useEffect(() => {
    axios.get(`http://127.0.0.1:8000/api/readings/${deviceId}`)
      .then(res => {
        setData(res.data.map(r => ({ ts: r[0], value: r[1] })));
      })
      .catch(err => console.error("Error fetching readings:", err));
  }, [deviceId]);

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data}>
        <XAxis dataKey="ts" hide />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="value" stroke="red" />
      </LineChart>
    </ResponsiveContainer>
  );
}
export default DeviceChart;
