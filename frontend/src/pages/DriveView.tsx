import { useParams } from "react-router-dom";

export default function DriveView() {
  const { id } = useParams<{ id: string }>();

  return (
    <div style={{ padding: 40 }}>
      <h1>Drive Mode</h1>
      <p>Trip: {id}</p>
      <p>
        Drive view with GPS-triggered events, map, and real-time updates coming
        in Phase 3.
      </p>
    </div>
  );
}
