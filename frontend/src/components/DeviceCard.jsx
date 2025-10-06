import Card from "react-bootstrap/Card";

function DeviceCard({ device }) {
  const [id, name, device_id, baud_rate, com_port, enabled] = device;

  return (
    <Card className="mb-2 shadow-sm">
      <Card.Body className="text-center">
        <Card.Title>{name}</Card.Title>
        <Card.Text>
          ID: {device_id} <br />
          Port: {com_port} | Baud: {baud_rate}
        </Card.Text>
        <Card.Text>
          Status: {enabled ? "✅ Enabled" : "❌ Disabled"}
        </Card.Text>
      </Card.Body>
    </Card>
  );
}
export default DeviceCard;
