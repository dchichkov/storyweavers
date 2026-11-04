"""Physical state, carrier-bound concepts, and executable narrative kernels.

Nothing here examines generated English. Preconditions, causal evidence, and
effects operate on entity IDs and persistent facts. The grammar consumes Frames.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
import random


@dataclass
class Entity:
    id: str
    noun: str
    kind: str
    location: str
    number: str = "singular"
    pronoun: str = "it"
    properties: set[str] = field(default_factory=set)
    state: set[str] = field(default_factory=set)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Fact:
    id: str
    text: str
    tags: tuple[str, ...]
    value: float = 1.0


@dataclass(frozen=True)
class Frame:
    kind: str
    actor: str
    patient: str = ""
    instrument: str = ""
    destination: str = ""
    cause_ids: tuple[str, ...] = ()


@dataclass
class World:
    scenario: str
    entities: dict[str, Entity]
    hero: str
    helper: str
    target: str
    tool: str
    setting: str
    facts: dict[str, Fact]
    flags: set[str] = field(default_factory=set)
    history: list[dict] = field(default_factory=list)
    focus: str = ""

    def clone(self) -> World:
        return deepcopy(self)

    def to_dict(self) -> dict:
        def encode(value):
            if isinstance(value, set):
                return sorted(value)
            if isinstance(value, dict):
                return {k: encode(v) for k, v in value.items()}
            if isinstance(value, (list, tuple)):
                return [encode(v) for v in value]
            return value
        return encode(asdict(self))

    @property
    def finished(self) -> bool:
        return "ended" in self.flags

    def snapshot(self) -> dict:
        return {"flags": sorted(self.flags), "entities": {
            k: {"location": e.location, "state": sorted(e.state), "memes": dict(e.memes)}
            for k, e in self.entities.items()}}

    def facts_for_attention(self) -> list[Fact]:
        # The stored facts are original premises. Attention refreshes locations
        # and availability from current carriers rather than reusing stale text.
        facts = [fact for key, fact in self.facts.items()
                 if key in {"problem", "obstacle"} and "solved" not in self.flags]
        helper = self.entities.get(self.helper)
        hero = self.entities[self.hero]
        if helper and helper.location == hero.location:
            facts.append(self.facts["helper_available"])
        tool = self.entities.get(self.tool)
        if tool:
            location = self.entities[tool.location].noun if tool.location in self.entities else tool.location
            text = (f"{location} is holding the {tool.noun}." if tool.location in self.entities
                    else f"The {tool.noun} is in the {location}.")
            facts.append(Fact("tool_available", text, ("tool", "planning")))
        if "solved" in self.flags:
            target = self.entities[self.target]
            facts.append(Fact("outcome", f"The {target.noun} is now {', '.join(sorted(target.state))}.",
                              ("goal", "outcome")))
        facts.extend(Fact(f"{self.hero}.{name}", f"{hero.noun}'s {name.lower()} is {value:.2f}",
                          ("actor", name.lower(), self.hero), value)
                     for name, value in sorted(hero.memes.items()))
        if self.history:
            last = self.history[-1]
            facts.append(Fact(f"event:{last['id']}", f"Previously: {last['frame']['kind']}",
                              ("recent", last["frame"]["kind"]), 1))
        return facts


SCENARIOS = ("rescue", "kite", "key")


def make_world(scenario: str = "rescue", seed: int = 0, *, fear: float | None = None,
               care: float | None = None) -> World:
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario!r}")
    for name, value in (("fear", fear), ("care", care)):
        if value is not None and not 0 <= value <= 1:
            raise ValueError(f"{name} must be between zero and one")
    rng = random.Random(seed)
    name, pronoun = rng.choice((("Lily", "she"), ("Sam", "he"), ("Nora", "she"), ("Ben", "he")))
    helper_name = "Mum" if pronoun == "he" else "Dad"
    setting = {"rescue": "garden", "kite": "meadow", "key": "courtyard"}[scenario]
    entities = {
        "hero": Entity("hero", name, "person", setting, pronoun=pronoun,
                       properties={"animate", "can_hold", "can_climb", "can_repair"},
                       memes={"Care": 0.8 if care is None else care,
                              "Fear": rng.uniform(0.2, 0.7) if fear is None else fear,
                              "Curiosity": 0.65, "Trust": 0.35, "Joy": 0.1}),
        "helper": Entity("helper", helper_name, "person", setting,
                         pronoun="she" if helper_name == "Mum" else "he",
                         properties={"animate", "can_hold", "can_repair"}, memes={"Care": 0.9}),
        "bread": Entity("bread", "bread", "food", "kitchen", properties={"edible"}),
        "water": Entity("water", "water", "drink", "kitchen", properties={"drinkable"}),
        "stone": Entity("stone", "stone", "object", setting, properties={"portable"}),
    }
    if scenario == "rescue":
        animal = rng.choice(("kitten", "puppy", "rabbit"))
        # A puppy/rabbit on a high ledge is plausible without claiming it climbed.
        entities.update({
            "target": Entity("target", animal, "animal", "ledge", properties={"animate", "portable"},
                             state={"stranded", "cold", "frightened"}, memes={"Fear": 0.8}),
            "tool": Entity("tool", "ladder", "tool", "shed", properties={"reach", "portable"}),
            "blanket": Entity("blanket", "blanket", "object", "cottage", properties={"warm", "portable"}),
        })
        obstacle = "The ledge is too high to reach from the ground."
        problem = f"The {animal} is stranded on a cold ledge."
    elif scenario == "kite":
        entities.update({
            "target": Entity("target", "kite", "object", setting, properties={"portable", "flyable"},
                             state={"torn", "grounded"}),
            "tool": Entity("tool", "tape", "tool", "basket", properties={"repair", "portable"}),
        })
        obstacle = "A tear in the kite prevents it from flying."
        problem = "The kite is torn, although there is enough wind to fly it."
    else:
        entities.update({
            "target": Entity("target", "key", "object", "under bench", properties={"portable", "unlocks"},
                             state={"lost", "hidden"}),
            "tool": Entity("tool", "lantern", "tool", "porch", properties={"illuminate", "portable"}),
            "door": Entity("door", "door", "object", "cottage", state={"locked"}),
        })
        obstacle = "It is too dark under the bench to see the key."
        problem = "The cottage door is locked, and the key is missing."
    facts = {
        "problem": Fact("problem", problem, ("problem", "goal", "care")),
        "obstacle": Fact("obstacle", obstacle, ("obstacle", "fear", "planning")),
        "helper_available": Fact("helper_available", f"{helper_name} is nearby and willing to help.",
                                 ("helper", "trust", "planning")),
        "tool_available": Fact("tool_available", f"The {entities['tool'].noun} is in the {entities['tool'].location}.",
                               ("tool", "planning")),
    }
    return World(scenario, entities, "hero", "helper", "target", "tool", setting, facts)


@dataclass(frozen=True)
class Kernel:
    name: str
    requires: frozenset[str]
    excludes: frozenset[str]
    adds: frozenset[str]
    base: float
    query: tuple[str, ...]
    # Hand-authored evidence coefficients; no calibration claim.
    preferences: tuple[tuple[str, float], ...] = ()


def kernel(name, requires=(), excludes=(), adds=(), base=0.0, query=(), preferences=()):
    return Kernel(name, frozenset(requires), frozenset(excludes) | {"ended"},
                  frozenset(adds), base, tuple(query), tuple(preferences))


KERNELS = (
    kernel("notice", excludes=("noticed",), adds=("noticed",), query=("problem",)),
    kernel("want", ("noticed",), ("wanted", "planned", "prepared", "solved"), ("wanted",),
           -1.5, ("goal", "care"), (("Care", 1.0),)),
    kernel("attempt", ("noticed",), ("attempted", "planned", "prepared", "solved"), ("attempted",),
           0.2, ("curiosity", "obstacle", "fear"), (("Curiosity", 1.2), ("Fear", -2.0))),
    kernel("ask", ("noticed",), ("asked", "planned", "prepared", "solved"), ("asked", "planned"),
           -0.1, ("helper", "fear", "trust"), (("Fear", 2.5), ("Trust", 1.2))),
    kernel("think", ("noticed",), ("planned", "prepared", "solved"), ("planned",),
           -0.2, ("planning", "curiosity"), (("Curiosity", 1.3),)),
    kernel("fetch", ("planned",), ("prepared", "solved"), ("prepared",),
           0.4, ("tool", "care"), (("Care", 0.8),)),
    kernel("receive", ("asked",), ("prepared", "solved"), ("prepared",),
           0.1, ("helper", "trust"), (("Trust", 1.4),)),
    kernel("solve", ("prepared",), ("solved",), ("solved",), query=("tool", "goal", "care")),
    kernel("finish", ("solved",), ("resolved",), ("resolved",), query=("goal",)),
    kernel("thank", ("resolved", "asked"), ("thanked",), ("thanked",),
           -0.8, ("helper", "trust"), (("Trust", 1.0),)),
    kernel("ending", ("resolved",), (), ("ended",), 0.4, ("goal", "recent")),
)
BY_NAME = {k.name: k for k in KERNELS}


def grounded_action(world: World, action: str, actor: str, patient: str,
                    instrument: str = "") -> tuple[bool, str]:
    """Reusable type/affordance checks, also exposed to autocomplete tests."""
    entities = world.entities
    if actor not in entities or patient not in entities:
        return False, "unknown carrier"
    subject, obj = entities[actor], entities[patient]
    if "animate" not in subject.properties:
        return False, "actor must be animate"
    if action in {"eat", "drink"}:
        prop = "edible" if action == "eat" else "drinkable"
        return (prop in obj.properties, f"patient must be {prop}")
    if action == "carry":
        return ("can_hold" in subject.properties and "portable" in obj.properties,
                "requires a carrier and a portable object")
    if action in {"rescue", "repair", "find"}:
        ability = {"rescue": "can_climb", "repair": "can_repair", "find": "can_hold"}[action]
        if ability not in subject.properties:
            return False, f"actor must have {ability}"
        prop = {"rescue": "reach", "repair": "repair", "find": "illuminate"}[action]
        if instrument not in entities or prop not in entities[instrument].properties:
            return False, f"instrument must provide {prop}"
        state = {"rescue": "stranded", "repair": "torn", "find": "lost"}[action]
        return state in obj.state, f"patient must be {state}"
    return False, "unsupported action"


def rejection(world: World, k: Kernel) -> str | None:
    if not k.requires <= world.flags:
        return "missing: " + ", ".join(sorted(k.requires - world.flags))
    if k.excludes & world.flags:
        return "already/blocked: " + ", ".join(sorted(k.excludes & world.flags))
    if any(e not in world.entities for e in (world.hero, world.target, world.tool)):
        return "required physical carrier is absent"
    target = world.entities[world.target]
    if k.name in {"notice", "want", "attempt", "ask", "think"}:
        required = {"rescue": "stranded", "kite": "torn", "key": "lost"}[world.scenario]
        if required not in target.state:
            return f"problem is no longer present: {required}"
    if k.name in {"ask", "think", "fetch", "receive"}:
        affordance = {"rescue": "reach", "kite": "repair", "key": "illuminate"}[world.scenario]
        if affordance not in world.entities[world.tool].properties:
            return f"proposed tool cannot {affordance}"
    if k.name in {"ask", "receive", "thank"}:
        if world.helper not in world.entities or world.entities[world.helper].location != world.setting:
            return "helper is absent"
        if world.entities[world.helper].location != world.entities[world.hero].location:
            return "helper is out of speaking range"
    if k.name == "solve":
        action = {"rescue": "rescue", "kite": "repair", "key": "find"}[world.scenario]
        legal, reason = grounded_action(world, action, world.hero, world.target, world.tool)
        if not legal:
            return reason
        if world.entities[world.tool].location != world.hero:
            return "tool is not held by the actor"
    if k.name == "fetch" and "portable" not in world.entities[world.tool].properties:
        return "tool is not portable"
    if k.name == "finish":
        required = {"rescue": "safe", "kite": "repaired", "key": "found"}[world.scenario]
        if required not in target.state:
            return f"resolution requires {required}"
    if k.name == "ending":
        if world.scenario == "rescue" and not {"safe", "warm"} <= target.state:
            return "ending requires an animal that is safe and warm"
        if world.scenario == "kite" and "flying" not in target.state:
            return "ending requires a flying kite"
        if world.scenario == "key" and "open" not in world.entities["door"].state:
            return "ending requires an open door"
    return None


def frames(world: World) -> list[tuple[Kernel, Frame]]:
    result = []
    for k in KERNELS:
        if rejection(world, k) is not None:
            continue
        causes = ["problem"]
        if k.name in {"attempt", "ask", "think", "fetch", "receive", "solve"}:
            causes.append("obstacle")
        if k.name in {"fetch", "receive", "solve"}:
            causes.append("tool_available")
        if k.name in {"ask", "receive", "thank"}:
            causes.append("helper_available")
        actor = world.helper if k.name == "receive" else world.hero
        if k.name == "ending":
            actor = world.target if world.scenario in {"rescue", "kite"} else world.hero
        result.append((k, Frame(k.name, actor, world.target, world.tool,
                               "cottage" if world.scenario in {"rescue", "key"} else world.setting,
                               tuple(causes))))
    return result


def commit(world: World, frame: Frame, sentence: str) -> dict:
    """Validate again at commit; predictions never mutate physical state."""
    if frame.kind not in BY_NAME or frame not in [f for _, f in frames(world)]:
        raise ValueError("frame is not an executable continuation of this world")
    before = world.snapshot()
    k = BY_NAME[frame.kind]
    hero, target, tool = (world.entities[e] for e in (world.hero, world.target, world.tool))
    world.flags.update(k.adds)
    if frame.kind == "attempt":
        hero.memes["Fear"] = min(1, hero.memes["Fear"] + 0.15)
    elif frame.kind == "ask":
        hero.memes["Trust"] = min(1, hero.memes["Trust"] + 0.3)
    elif frame.kind in {"fetch", "receive"}:
        tool.location = world.hero
    elif frame.kind == "solve":
        if world.scenario == "rescue":
            target.state.discard("stranded")
            target.state.add("safe")
            target.location = world.hero
        elif world.scenario == "kite":
            target.state.discard("torn")
            target.state.add("repaired")
        else:
            target.state.difference_update({"lost", "hidden"})
            target.state.add("found")
            target.location = world.hero
        hero.memes["Joy"] += 0.4
    elif frame.kind == "finish":
        if world.scenario == "rescue":
            target.location = "cottage"
            hero.location = "cottage"
            target.state.difference_update({"cold", "frightened"})
            target.state.add("warm")
            target.memes["Fear"] = 0.1
        elif world.scenario == "kite":
            target.state.discard("grounded")
            target.state.add("flying")
            target.location = "sky"
        else:
            world.entities["door"].state.discard("locked")
            world.entities["door"].state.add("open")
        hero.memes["Joy"] += 0.3
    elif frame.kind == "ending":
        if world.scenario == "key":
            hero.location = "cottage"
        elif world.scenario == "rescue":
            target.state.add("resting")
    world.focus = frame.actor
    record = dict(id=len(world.history) + 1, frame=asdict(frame), sentence=sentence,
                  before=before, after=world.snapshot())
    world.history.append(record)
    return record
