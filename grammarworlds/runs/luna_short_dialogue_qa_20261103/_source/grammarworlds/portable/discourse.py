"""Codeco-style forward/backward references and accessibility scopes.

Independent implementation of the paper's mechanism, not a port of the ACE
rule inventory or its parser. Features bind to physical entity IDs, never prose.
"""
from dataclasses import dataclass, field
from .catalog import rule

SOURCE = "https://arxiv.org/abs/1211.3643"


@dataclass
class Discourse:
    scopes: list[dict[str, dict]] = field(default_factory=lambda: [{}])

    @rule("codeco.forward", SOURCE, "forward reference >", tags=("reference", "introduce", "discourse"))
    def introduce(self, entity_id: str, **features):
        """Register a physical referent in the current accessibility scope."""
        self.scopes[-1][entity_id] = dict(features)

    @rule("codeco.backward", SOURCE, "backward reference <", tags=("reference", "anaphora", "pronoun"))
    def resolve(self, **features):
        """Find accessible antecedents with matching features, nearest scope first."""
        matches, seen = [], set()
        for scope in reversed(self.scopes):
            for entity_id, candidate in reversed(list(scope.items())):
                if entity_id not in seen and all(candidate.get(k) == v for k, v in features.items()):
                    matches.append(entity_id)
                seen.add(entity_id)
        return matches

    @rule("codeco.scope", SOURCE, "scope opener // and scope-closing rules", tags=("reference", "scope", "negation", "hypothetical"))
    def push(self):
        """Open a local scope; pop discards its introductions (no hypothetical leak)."""
        self.scopes.append({})

    def pop(self):
        if len(self.scopes) == 1:
            raise ValueError("cannot close root discourse scope")
        self.scopes.pop()

    @classmethod
    def from_world(cls, world):
        result = cls()
        for event in world.history:
            for entity_id in event.get("referents", []):
                if entity_id in world.entities:
                    entity = world.entities[entity_id]
                    result.introduce(entity_id, pronoun=entity.pronoun, number=entity.number)
        return result
