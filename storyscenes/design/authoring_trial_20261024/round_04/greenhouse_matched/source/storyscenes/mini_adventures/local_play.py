"""Atomic local actions and detached traces; scenario rules belong to callers."""
from copy import deepcopy

from storyscenes.runtime import Condition, Effect, Scene, StoryError, transition


class LocalPlay:
    """Own a copied state; validate candidates before committing state or events.

    ``validate`` raises on invalid states. It receives detached snapshots so a
    callback cannot change the committed state. ``requires`` maps state keys to
    equality values; changes set declared keys. Rejections raise ``StoryError``
    (or propagate the validator's exception), without recording an event.
    """

    def __init__(self, state, *, actors, validate):
        snapshot = deepcopy(state)
        validate(deepcopy(snapshot))
        self.state = snapshot
        self.events = []
        self._actors = tuple(deepcopy(actors))
        self._validate = validate

    def act(self, name, requires=None, **changes):
        before = deepcopy(self.state)
        requirements = deepcopy({} if requires is None else requires)
        action = Scene(
            id=name, kernel=name, actors=self._actors,
            requires=tuple(Condition(key=k, op="eq", value=v)
                           for k, v in requirements.items()),
            effects=tuple(Effect(key=k, value=deepcopy(v)) for k, v in changes.items()),
            summary=name,
        )
        after = transition(before, action)
        if after is None:
            raise StoryError(f"Illegal or ineffective local action: {name}")
        self._validate(deepcopy(after))
        event = deepcopy({
            "action": name, "requires": requirements,
            "changes": {k: {"before": before[k], "after": v}
                        for k, v in after.items() if v != before[k]},
        })
        self.state = after
        self.events.append(event)
