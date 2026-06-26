#!/usr/bin/env python3
"""
A small storyworld about a pebble, spooky sounds, inner monologue, and a
friendship with a ghost.

The seed inspiration is a child-facing ghost story:
- a little character hears pebble sounds at night,
- fears a ghost,
- discovers the ghost is lonely, not harmful,
- and ends with a friendly shared task that explains the sounds.

This script models the story as a tiny causal world with meters and memes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------

def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    plural: bool = False
    visible: bool = True
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    ghost: object | None = None
    parent: object | None = None
    pebble: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "ghost"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str = "the old garden"
    night: bool = True
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Clue:
    name: str
    source: str
    sound: str
    effect: str
    cause: str
    risky: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Comfort:
    name: str
    label: str
    action: str
    effect: str
    helps: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict = {}
        self.weather: str = "quiet night"

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        para: list[str] = []
        for line in self.lines:
            if line == "":
                if para:
                    out.append(" ".join(para))
                    para = []
            else:
                para.append(line)
        if para:
            out.append(" ".join(para))
        return "\n\n".join(out)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.lines = []
        clone.facts = dict(self.facts)
        clone.weather = self.weather
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the old garden", night=True, affords={"pebbles", "ghost", "friendship"}),
    "path": Setting(place="the moonlit path", night=True, affords={"pebbles", "ghost", "friendship"}),
    "yard": Setting(place="the quiet yard", night=True, affords={"pebbles", "ghost", "friendship"}),
}

CLUES = {
    "pebbles": Clue(
        name="pebbles",
        source="small stones",
        sound="click-click",
        effect="a tiny clatter on the path",
        cause="someone was rolling pebbles under a shoe",
        risky=False,
    ),
    "ghost": Clue(
        name="ghost",
        source="a lonely ghost",
        sound="whooo",
        effect="a chilly whisper in the dark",
        cause="the ghost was trying to say hello",
        risky=True,
    ),
}

COMFORTS = {
    "hello": Comfort(
        name="hello",
        label="a hello",
        action="say hello",
        effect="the dark felt a little less sharp",
        helps={"ghost", "friendship"},
    ),
    "lantern": Comfort(
        name="lantern",
        label="a lantern",
        action="turn on the lantern",
        effect="the path glowed warm and gold",
        helps={"pebbles", "ghost"},
    ),
    "shared_game": Comfort(
        name="shared_game",
        label="a pebble game",
        action="make a pebble path game",
        effect="the spooky sound turned into a game",
        helps={"pebbles", "friendship"},
    ),
}

NAMES = ["Mina", "Noah", "Lina", "Eli", "Sage", "June", "Owen", "Ivy"]
GHOST_NAMES = ["Moss", "Bram", "Pip", "Willow"]
TRAITS = ["curious", "quiet", "brave", "gentle", "sleepy", "careful"]


@dataclass
class StoryParams:
    place: str
    clue: str
    child_name: str
    child_type: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
    params: object | None = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def make_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(
        id=params.child_name, kind="character", type=params.child_type,
        traits=["little", params.trait, "thoughtful"],
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=params.parent_type, label="the parent"
    ))
    ghost = world.add(Entity(
        id="Ghost", kind="character", type="ghost", label="the ghost",
        visible=False, traits=["lonely", "friendly"],
    ))
    pebble = world.add(Entity(
        id="Pebble", kind="thing", type="pebble", label="pebble",
        phrase="a smooth gray pebble", owner=child.id, visible=True,
        meters={"hard": 1.0},
    ))
    child.memes["uneasy"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["friendship"] = 0.0
    ghost.memes["lonely"] = 1.0
    ghost.memes["friendship"] = 0.0
    world.facts.update(child=child, parent=parent, ghost=ghost, pebble=pebble)
    return world


def sound_step(world: World, clue: Clue) -> None:
    if ("sound", clue.name) in world.fired:
        return
    world.fired.add(("sound", clue.name))
    world.say(f"From the dark came {clue.sound}, {clue.effect}.")
    world.facts["sound"] = clue.sound
    world.facts["sound_effect"] = clue.effect
    world.facts["sound_cause_hint"] = clue.cause


def inner_monologue(world: World, child: Entity, clue: Clue) -> None:
    if clue.risky:
        child.memes["uneasy"] += 1
        world.say(
            f"{child.id} swallowed and thought, "
            f'"What if the dark is hiding something mean?"'
        )
    else:
        child.memes["curiosity"] += 1
        world.say(
            f"{child.id} thought, "
            f'"That sound is small. Maybe it is only a pebble."'
        )


def reveal_ghost(world: World, child: Entity, ghost: Entity) -> None:
    if ("reveal", ghost.id) in world.fired:
        return
    world.fired.add(("reveal", ghost.id))
    ghost.visible = True
    world.say(
        f"Then {ghost.id} drifted out from behind the hedge. "
        f"{ghost.id.capitalize()} was not scary at all, only pale and a little lonely."
    )
    child.memes["uneasy"] = max(0.0, child.memes["uneasy"] - 1.0)
    child.memes["curiosity"] += 1


def friendship_offer(world: World, child: Entity, ghost: Entity, comfort: Comfort) -> None:
    if ("comfort", comfort.name) in world.fired:
        return
    world.fired.add(("comfort", comfort.name))
    if comfort.name == "hello":
        world.say(
            f"{child.id} took a breath and said hello. "
            f"The ghost blinked, then smiled as if a window had opened inside {ghost.pronoun('possessive')} chest."
        )
    elif comfort.name == "lantern":
        world.say(
            f"{child.id} turned on the lantern, and {comfort.effect}."
        )
    else:
        world.say(
            f"{child.id} made {comfort.label}, and {comfort.effect}."
        )
    child.memes["friendship"] += 1
    ghost.memes["friendship"] += 1
    ghost.memes["lonely"] = 0.0
    world.facts["comfort"] = comfort


def resolve_pebble(world: World, child: Entity, ghost: Entity, pebble: Entity, clue: Clue) -> None:
    if ("resolve", clue.name) in world.fired:
        return
    world.fired.add(("resolve", clue.name))
    world.say(
        f"Together they found the reason for the little click-click: "
        f"{ghost.id} had been rolling {pebble.label}s along the path to make music."
    )
    world.say(
        f"{child.id} picked up the smooth pebble, and {ghost.id} laughed softly. "
        f"The strange sound was only a game, not a threat."
    )
    child.memes["uneasy"] = 0.0
    child.memes["friendship"] += 1
    ghost.memes["friendship"] += 1
    world.facts["resolved"] = True


def ending_image(world: World, child: Entity, ghost: Entity, pebble: Entity) -> None:
    world.para()
    world.say(
        f"In the end, {child.id} and {ghost.id} sat by the moonlit path, "
        f"listening to the pebble make one last soft tap between them."
    )
    world.say(
        f"The dark felt friendly now, and the tiny stone sounded like a secret shared by new friends."
    )


def tell(setting: Setting, clue: Clue, child_name: str = "Mina",
         child_type: str = "girl", parent_type: str = "mother", trait: str = "curious") -> World:
    params = StoryParams(setting.place.replace("the ", ""), clue.name, child_name, child_type, parent_type, trait)
    world = make_world(params)
    child = world.get(child_name)
    ghost = world.get("Ghost")
    pebble = world.get("Pebble")

    world.say(f"{child.id} was a little {trait} {child_type} who loved quiet evenings in {setting.place}.")
    world.say(f"{child.id} kept a smooth pebble in {child.pronoun('possessive')} pocket because it felt cool and safe.")

    world.para()
    sound_step(world, clue)
    inner_monologue(world, child, clue)

    if clue.risky:
        reveal_ghost(world, child, ghost)
        comfort = COMFORTS["hello"]
        friendship_offer(world, child, ghost, comfort)
    else:
        comfort = COMFORTS["shared_game"]
        friendship_offer(world, child, ghost, comfort)

    resolve_pebble(world, child, ghost, pebble, clue)
    ending_image(world, child, ghost, pebble)

    world.facts.update(setting=setting, clue=clue, child=child, ghost=ghost, pebble=pebble)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    clue = _safe_fact(world, f, "clue")
    return [
        f'Write a gentle ghost story for a small child named {child.id} that includes the sound "{clue.sound}".',
        f'Write a short story where a {child.type} notices pebble sounds at {world.setting.place} and learns the noise is friendly.',
        f'Create a child-facing spooky-but-kind story about a pebble, a ghost, and friendship.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    ghost = _safe_fact(world, f, "ghost")
    pebble = _safe_fact(world, f, "pebble")
    clue = _safe_fact(world, f, "clue")
    qa = [
        QAItem(
            question=f"Why did {child.id} feel uneasy at first?",
            answer=f"{child.id} heard {clue.sound} in the dark and thought something scary might be hiding there.",
        ),
        QAItem(
            question=f"What was making the pebble sound?",
            answer=f"It was actually {ghost.id}, a lonely ghost, rolling the pebble along the path like music.",
        ),
        QAItem(
            question=f"How did {child.id} and {ghost.id} become friends?",
            answer=f"{child.id} said hello, stayed close, and shared the little mystery until it felt safe and friendly.",
        ),
        QAItem(
            question=f"What did the pebble help prove?",
            answer=f"The pebble helped prove the strange noise was not dangerous; it was just a playful tap on the path.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {child.id} felt brave and friendly, and {ghost.id} was no longer lonely.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pebble?",
            answer="A pebble is a small, smooth stone that can roll or tap against the ground.",
        ),
        QAItem(
            question="What does a ghost usually mean in a story?",
            answer="In a story, a ghost is often a spooky-looking character, but it can also be gentle or lonely.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a word that helps you hear a noise in your mind, like tap, click-click, or whooo.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is what a character thinks inside their own head but does not say out loud.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
sound_kind(pebbles).
sound_kind(ghost).

friendly(G) :- ghost(G), kind(G, ghost).
uneasy(C) :- hears(C, S), sound_kind(S), scary_sound(S).
curious(C) :- hears(C, S), sound_kind(S), not scary_sound(S).

resolved(C, G) :- child(C), ghost(G), said_hello(C, G), shared_clue(C, G).
friendship(C, G) :- resolved(C, G), child(C), ghost(G).

scary_sound(ghost).
not scary_sound(pebbles).
#show resolved/2.
#show friendship/2.
#show uneasy/1.
#show curious/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.night:
            lines.append(asp.fact("night", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("sound", cid, c.sound))
        lines.append(asp.fact("effect", cid, c.effect))
        lines.append(asp.fact("cause", cid, c.cause))
    lines.append(asp.fact("child", "mina"))
    lines.append(asp.fact("ghost", "ghost"))
    lines.append(asp.fact("said_hello", "mina", "ghost"))
    lines.append(asp.fact("shared_clue", "mina", "ghost"))
    lines.append(asp.fact("hears", "mina", "ghost"))
    lines.append(asp.fact("kind", "ghost", "ghost"))
    lines.append(asp.fact("kind", "pebble", "pebbles"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set((sym.name, tuple(a.name if hasattr(a, "name") else getattr(a, "string", getattr(a, "number", None)) for a in sym.arguments)) for sym in model)
    expected = {("resolved", ("mina", "ghost")), ("friendship", ("mina", "ghost")), ("scary_sound", ("ghost",))}
    if expected.issubset(atoms):
        print("OK: ASP program is internally consistent.")
        return 0
    print("ASP verification failed.")
    print("Model atoms:", sorted(atoms))
    return 1


def asp_valid_story_set() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "resolved")))


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for clue in CLUES:
            if clue in setting.affords:
                combos.append((place, clue))
    return combos


def explain_rejection(place: str, clue: str) -> str:
    return f"(No story: {clue} is not a supported clue for {place} in this ghost story world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world with pebbles and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None) and getattr(args, "clue", None) and (getattr(args, "place", None), getattr(args, "clue", None)) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    choices = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue = rng.choice(sorted(choices))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    child_type = gender
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, clue=clue, child_name=name, child_type=child_type, parent_type=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CLUES, params.clue), params.child_name, params.child_type, params.parent_type, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.visible is False:
            bits.append("hidden")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="garden", clue="ghost", child_name="Mina", child_type="girl", parent_type="mother", trait="curious"),
    StoryParams(place="path", clue="pebbles", child_name="Owen", child_type="boy", parent_type="father", trait="careful"),
    StoryParams(place="yard", clue="ghost", child_name="Ivy", child_type="girl", parent_type="mother", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        print("ASP resolved atoms:")
        for atom in asp.atoms(model, "resolved"):
            print(" ", atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
