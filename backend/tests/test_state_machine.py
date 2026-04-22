import pytest
from app.engine.state_machine import TripStateMachine
from app.models.drive_events import TripState


class TestTripStateMachine:
    def test_initial_state(self):
        sm = TripStateMachine()
        assert sm.state == TripState.DRAFT

    def test_valid_transition_draft_to_generating(self):
        sm = TripStateMachine()
        new = sm.transition(TripState.GENERATING)
        assert new == TripState.GENERATING
        assert sm.state == TripState.GENERATING

    def test_full_happy_path(self):
        sm = TripStateMachine()
        sm.transition(TripState.GENERATING)
        sm.transition(TripState.READY)
        sm.transition(TripState.ACTIVE)
        sm.transition(TripState.APPROACHING_STOP)
        sm.transition(TripState.AT_STOP)
        sm.transition(TripState.RESUMED)
        sm.transition(TripState.ACTIVE)
        sm.transition(TripState.COMPLETED)
        assert sm.state == TripState.COMPLETED

    def test_invalid_transition(self):
        sm = TripStateMachine()
        with pytest.raises(ValueError, match="Invalid transition"):
            sm.transition(TripState.ACTIVE)

    def test_can_transition(self):
        sm = TripStateMachine()
        assert sm.can_transition(TripState.GENERATING)
        assert not sm.can_transition(TripState.ACTIVE)
        assert not sm.can_transition(TripState.COMPLETED)

    def test_rerouting_path(self):
        sm = TripStateMachine()
        sm.transition(TripState.GENERATING)
        sm.transition(TripState.READY)
        sm.transition(TripState.ACTIVE)
        sm.transition(TripState.REROUTING)
        sm.transition(TripState.ACTIVE)
        assert sm.state == TripState.ACTIVE

    def test_callback_fires(self):
        sm = TripStateMachine()
        transitions = []
        sm.on_transition(lambda old, new: transitions.append((old, new)))
        sm.transition(TripState.GENERATING)
        assert transitions == [(TripState.DRAFT, TripState.GENERATING)]

    def test_approaching_to_active_pass_through(self):
        sm = TripStateMachine(TripState.APPROACHING_STOP)
        sm.transition(TripState.ACTIVE)
        assert sm.state == TripState.ACTIVE
