import DeviceChart from "./DeviceChart";

function GraphSection({ devices }) {
  const colors = [
    "red","blue","green","orange","purple","brown","pink","cyan","magenta","teal"
  ];

  return (
    <div className="row">
      {/* Left 30%: Device Table */}
      <div className="col-md-3 border-end">
        <h5>📋 Device Table</h5>
        <table className="table table-sm table-bordered">
          <thead>
            <tr>
              <th>Device</th>
              <th>Check</th>
              <th>Colour</th>
            </tr>
          </thead>
          <tbody>
            {devices.map((d, i) => (
              <tr key={d[0]}>
                <td>{d[1]}</td>
                <td><input type="checkbox" /></td>
                <td>
                  <span style={{
                    width:"14px",height:"14px",borderRadius:"50%",
                    backgroundColor: colors[i % colors.length],
                    display:"inline-block"
                  }}></span>
                  {" "}{colors[i % colors.length]}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Right 70%: Graphs */}
      <div className="col-md-9">
        <h5>📈 Graph Display</h5>
        {devices.map(d => (
          <div className="mb-4" key={d[0]}>
            <DeviceChart deviceId={d[2]} />
          </div>
        ))}
      </div>
    </div>
  );
}

export default GraphSection;
