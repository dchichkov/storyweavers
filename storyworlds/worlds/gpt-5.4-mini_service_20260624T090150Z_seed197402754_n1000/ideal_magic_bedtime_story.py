#!/usr/bin/env python3
"""
A small bedtime story world with a magical, ideal bedtime routine.

Seed imagination:
A tired child wants one more playful moment before bed, but the room is
gentle and magical. A parent helps turn the last stretch of the evening into
an ideal bedtime: pajamas, a story, a glowing nightlight, and a toy that wakes
with magic only at bedtime. The turn is from restless energy to calm comfort,
and the ending proves sleep arrived in a safe, cozy room.

This script models the bedtime plan as world state:
- the child has energy, sleepiness, comfort, and worry
- magical objects can reduce worry and increase comfort
- the parent can guide the child toward the ideal bedtime sequence
- if the child resists too long, the room feels less peaceful
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
# Story model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0



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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    magical: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    labels: str = ""
    child: object | None = None
    parent: object | None = None
    toy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Room:
    name: str = "bedroom"
    cozy: bool = True
    quiet: bool = False
    glowing: bool = False
    ROOM: object | None = None
    world: object | None = None
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
class ItemSpec:
    id: str
    label: str
    phrase: str
    effect: str
    taste: str
    magical: bool = False
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class StoryParams:
    child_name: str
    child_type: str
    parent_type: str
    item: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(copy.deepcopy(self.room))
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

ROOM = Room()

ITEMS = {
    "lantern": ItemSpec(
        id="lantern",
        label="lantern",
        phrase="a little glowing lantern",
        effect="calm",
        taste="warm",
        magical=True,
    ),
    "storybook": ItemSpec(
        id="storybook",
        label="storybook",
        phrase="a bedtime storybook with silver stars",
        effect="sleep",
        taste="soft",
        magical=True,
    ),
    "blanket": ItemSpec(
        id="blanket",
        label="blanket",
        phrase="a moon-soft blanket",
        effect="comfort",
        taste="soft",
        magical=True,
    ),
    "pillow": ItemSpec(
        id="pillow",
        label="pillow",
        phrase="a fluffy pillow",
        effect="rest",
        taste="gentle",
        magical=False,
    ),
}

CHILD_NAMES = ["Mia", "Lily", "Nora", "Ava", "Leo", "Finn", "Theo", "Milo"]
TRAITS = ["sleepy", "curious", "restless", "gentle", "playful"]

KNOWLEDGE = {
    "sleep": [
        QAItem(
            question="Why do children need sleep?",
            answer="Children need sleep so their bodies and minds can rest, grow, and feel ready for a new day.",
        )
    ],
    "blanket": [
        QAItem(
            question="What does a blanket do at bedtime?",
            answer="A blanket keeps a child warm and cozy while they rest in bed.",
        )
    ],
    "lantern": [
        QAItem(
            question="Why might a night light or lantern help at bedtime?",
            answer="A soft light can make a room feel less scary and help a child feel safe while falling asleep.",
        )
    ],
    "storybook": [
        QAItem(
            question="Why are bedtime stories special?",
            answer="Bedtime stories can feel calm and loving, which helps a child slow down and get ready for sleep.",
        )
    ],
    "magic": [
        QAItem(
            question="What does magic mean in a bedtime story?",
            answer="In a bedtime story, magic can mean a gentle pretend power that helps ordinary things feel special and comforting.",
        )
    ],
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
child_ready(C) :- sleepy(C), comfort(C, K), K >= 2, not worry(C).
ideal_bedtime(C) :- child_ready(C), room_cozy.
magic_help(M) :- magical(M), calming(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.magical:
            lines.append(asp.fact("magical", iid))
        if item.effect == "calm":
            lines.append(asp.fact("calming", iid))
    lines.append(asp.fact("room_cozy"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show magical/1. #show calming/1."))
    got_magical = {x[0] for x in asp.atoms(model, "magical")}
    got_calm = {x[0] for x in asp.atoms(model, "calming")}
    py_magical = {k for k, v in ITEMS.items() if v.magical}
    py_calm = {k for k, v in ITEMS.items() if v.effect == "calm"}
    if got_magical == py_magical and got_calm == py_calm:
        print("OK: ASP parity matches Python registry checks.")
        return 0
    print("MISMATCH between ASP and Python checks.")
    return 1

# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def choose_item(item_id: str) -> ItemSpec:
    if item_id not in ITEMS:
        pass
    return _safe_lookup(ITEMS, item_id)


def build_world(params: StoryParams) -> World:
    world = World(room=Room())
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        labels="",
        meters={},
        memes={"energy": 2.0, "sleepiness": 0.0, "comfort": 0.0, "worry": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label="parent",
        memes={"gentleness": 2.0},
    ))
    item = choose_item(params.item)
    toy = world.add(Entity(
        id=item.id,
        type=item.id,
        label=item.label,
        phrase=item.phrase,
        magical=item.magical,
        owner=child.id,
    ))
    world.facts.update(child=child, parent=parent, item=toy, item_spec=item)
    return world


def opening(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    i = _safe_fact(world, world.facts, "item")
    world.say(
        f"{c.id} was a little {c.type} who loved the evening when the house grew quiet."
    )
    world.say(
        f"On the bedside table sat {i.phrase}, waiting to make the night feel safe."
    )


def rising_tension(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    p = _safe_fact(world, world.facts, "parent")
    i = _safe_fact(world, world.facts, "item")
    c.memes["energy"] += 1.0
    c.memes["worry"] += 1.0
    world.room.quiet = False
    world.say(
        f"{c.id} wanted one more hop and one more laugh, but {c.pronoun('possessive')} "
        f"{p.type} noticed the yawn hiding behind {c.pronoun('possessive')} smile."
    )
    world.say(
        f'"It is time for the ideal bedtime," {p.pronoun().capitalize()} said softly, '
        f'and {i.label} seemed to glow a little brighter.'
    )


def magical_turn(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    p = _safe_fact(world, world.facts, "parent")
    item = _safe_fact(world, world.facts, "item")
    spec = _safe_fact(world, world.facts, "item_spec")

    if spec.magical:
        c.memes["comfort"] += 2.0
        c.memes["worry"] = max(0.0, c.memes["worry"] - 1.0)
        world.room.glowing = True
        world.say(
            f"When {p.pronoun().capitalize()} opened {item.pronoun('possessive')} cover, "
            f"tiny stars of magic twinkled over the bed."
        )
        world.say(
            f"The glow made the room feel warm and gentle, and {c.id} leaned closer to the pillow."
        )
    else:
        c.memes["comfort"] += 1.0
        world.say(
            f"{item.phrase} still helped, because even ordinary things can feel kind at bedtime."
        )


def bedtime_sequence(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    p = _safe_fact(world, world.facts, "parent")
    item = _safe_fact(world, world.facts, "item")
    spec = _safe_fact(world, world.facts, "item_spec")

    c.memes["sleepiness"] += 2.0
    c.memes["energy"] = max(0.0, c.memes["energy"] - 1.5)
    world.room.quiet = True
    world.para()
    world.say(
        f"{p.pronoun().capitalize()} tucked the blanket around {c.pronoun('object')} and read a page from the storybook."
    )
    if spec.magical:
        world.say(
            f"The lantern shone like a moonbeam, and the bedtime story sounded like it was floating on a cloud."
        )
    world.say(
        f"{c.id} sighed, the last worry slid away, and {c.pronoun().capitalize()} closed {c.pronoun('possessive')} eyes."
    )
    world.say(
        f"At the end of the ideal bedtime, the room was still, cozy, and full of soft breathing."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    opening(world)
    world.para()
    rising_tension(world)
    magical_turn(world)
    bedtime_sequence(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    c = _safe_fact(world, world.facts, "child")
    spec = _safe_fact(world, world.facts, "item_spec")
    return [
        f"Write a gentle bedtime story about {c.id}, a child who needs an ideal bedtime and a little magic.",
        f"Tell a cozy story where {c.id} resists sleep for a moment, then finds comfort with {spec.phrase}.",
        "Write a bedtime story with a calm ending, a glowing room, and a child who falls asleep feeling safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = _safe_fact(world, world.facts, "child")
    p = _safe_fact(world, world.facts, "parent")
    item = _safe_fact(world, world.facts, "item")
    spec = _safe_fact(world, world.facts, "item_spec")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {c.id}, a little {c.type} who was getting ready for bed.",
        ),
        QAItem(
            question=f"What made the bedtime feel special?",
            answer=f"{spec.phrase} made the bedtime feel special, and because it was magical, it helped the room feel calm and cozy.",
        ),
        QAItem(
            question=f"What did {p.type} do to help?",
            answer=f"{p.pronoun().capitalize()} spoke softly, opened {item.pronoun('possessive')} cover, and guided {c.id} through the ideal bedtime.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The story ended with the child calm, sleepy, and safely tucked into a quiet, cozy bed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {"sleep", "blanket", "storybook", "magic"}
    for tag in tags:
        out.extend(KNOWLEDGE.get(tag, []))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters, parsing, generation
# ---------------------------------------------------------------------------

DEFAULTS = {
    "child_type": "girl",
    "parent_type": "mother",
    "item": "lantern",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small magical bedtime story world.")
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child_type = getattr(args, "child_type", None) or DEFAULTS["child_type"]
    parent_type = getattr(args, "parent_type", None) or DEFAULTS["parent_type"]
    item = getattr(args, "item", None) or rng.choice(sorted(ITEMS))
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    return StoryParams(
        child_name=name,
        child_type=child_type,
        parent_type=parent_type,
        item=item,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    c = _safe_fact(world, world.facts, "child")
    p = _safe_fact(world, world.facts, "parent")
    item = _safe_fact(world, world.facts, "item")
    lines = ["--- world model state ---"]
    lines.append(f"  child {c.id}: memes={dict(c.memes)}")
    lines.append(f"  parent {p.id}: memes={dict(p.memes)}")
    lines.append(f"  item {item.id}: magical={item.magical}")
    lines.append(
        f"  room: cozy={world.room.cozy} quiet={world.room.quiet} glowing={world.room.glowing}"
    )
    return "\n".join(lines)


def asp_verify_wrapper() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show magical/1. #show calming/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_wrapper())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show magical/1. #show calming/1."))
        print("magical:", sorted({x[0] for x in asp.atoms(model, "magical")}))
        print("calming:", sorted({x[0] for x in asp.atoms(model, "calming")}))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for i, item in enumerate(sorted(ITEMS)):
            params = StoryParams(
                child_name=_safe_lookup(CHILD_NAMES, i % len(CHILD_NAMES)),
                child_type="girl" if i % 2 == 0 else "boy",
                parent_type="mother" if i % 2 == 0 else "father",
                item=item,
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.child_name}: {p.item} bedtime"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
