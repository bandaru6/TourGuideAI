import { BrowserRouter, Routes, Route } from "react-router-dom";
import TripPlanner from "./pages/TripPlanner";
import TripReview from "./pages/TripReview";
import DriveView from "./pages/DriveView";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<TripPlanner />} />
        <Route path="/trip/:id" element={<TripReview />} />
        <Route path="/drive/:id" element={<DriveView />} />
      </Routes>
    </BrowserRouter>
  );
}
