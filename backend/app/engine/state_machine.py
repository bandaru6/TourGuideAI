from app.models.drive_events import TripState

VALID_TRANSITIONS: dict[TripState, set[TripState]] = {
    TripState.DRAFT: {TripState.GENERATING},
    TripState.GENERATING: {TripState.READY},
    TripState.READY: {TripState.ACTIVE},
    TripState.ACTIVE: {TripState.APPROACHING_STOP, TripState.REROUTING, TripState.COMPLETED},
    TripState.APPROACHING_STOP: {TripState.AT_STOP, TripState.ACTIVE},
    TripState.AT_STOP: {TripState.RESUMED},
    TripState.RESUMED: {TripState.ACTIVE},
    TripState.REROUTING: {TripState.ACTIVE},
}


class TripStateMachine:
    def __init__(self, initial_state: TripState = TripState.DRAFT):
        self._state = initial_state
        self._callbacks: list = []

    @property
    def state(self) -> TripState:
        return self._state

    def can_transition(self, target: TripState) -> bool:
        allowed = VALID_TRANSITIONS.get(self._state, set())
        return target in allowed

    def transition(self, target: TripState) -> TripState:
        if not self.can_transition(target):
            raise ValueError(
                f"Invalid transition: {self._state.value} → {target.value}. "
                f"Allowed: {[s.value for s in VALID_TRANSITIONS.get(self._state, set())]}"
            )
        old_state = self._state
        self._state = target
        for cb in self._callbacks:
            cb(old_state, self._state)
        return self._state

    def on_transition(self, callback) -> None:
        self._callbacks.append(callback)
