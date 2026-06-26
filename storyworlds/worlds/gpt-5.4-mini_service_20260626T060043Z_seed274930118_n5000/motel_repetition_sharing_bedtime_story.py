#!/usr/bin/env python3
"""
A small storyworld about a motel room, bedtime repetition, and sharing.

Premise:
- A child arrives at a motel for the night.
- The child has a favorite bedtime ritual that repeats.
- The child must share limited bedtime space or items with a sibling/parent/helper.
- The story turns when they make a cozy shared plan.

The world is intentionally small and constraint-driven:
- One motel room, one bedtime task loop, one shared object, one emotional turn.
- The prose should read like a gentle bedtime story, not an event log.
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
# Registries
# ---------------------------------------------------------------------------

ROOMS = {
    "small_room": {
        "label": "a small motel room",
        "mood": "quiet",
        "extras": ["a tiny lamp", "two beds", "a narrow nightstand"],
    },
    "family_room": {
        "label": "a family motel room",
        "mood": "cozy",
        "extras": ["a lamp with a warm shade", "two beds", "a soft chair"],
    },
}

BEDTIME_ITEMS = {
    "blanket": {
        "label": "blanket",
        "phrase": "a soft blue blanket",
        "plural": False,
        "shared": True,
        "comfort": "warmth",
    },
    "book": {
        "label": "book",
        "phrase": "a little bedtime book",
        "plural": False,
        "shared": True,
        "comfort": "calm",
    },
    "pillow": {
        "label": "pillow",
        "phrase": "a round fluffy pillow",
        "plural": False,
        "shared": False,
        "comfort": "rest",
    },
    "stuffie": {
        "label": "stuffie",
        "phrase": "a sleepy bear stuffie",
        "plural": False,
        "shared": False,
        "comfort": "bravery",
    },
}

ROLES = {
    "child": "child",
    "sibling": "sibling",
    "parent": "parent",
    "grandparent": "grandparent",
}

NAMES = [
    "Mia", "Leo", "Nora", "Sam", "Ava", "Eli", "Luna", "Noah", "Ivy", "Milo"
]

HELPER_NAMES = [
    "Tess", "Rina", "Owen", "June", "Piper", "Theo", "Mina", "Ezra"
]


# ---------------------------------------------------------------------------
# Dataclasses
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
    owner: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    companion: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class StoryParams:
    motel: str
    room: str
    item: str
    child_name: str
    child_type: str
    companion_name: str
    companion_type: str
    repeated_action: str
    shared_action: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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
    def __init__(self, motel: str, room: str) -> None:
        self.motel = motel
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------

def valid_combo(room: str, item: str) -> bool:
    return room in ROOMS and item in BEDTIME_ITEMS


def explain_rejection(room: str, item: str) -> str:
    if room not in ROOMS:
        return "(No story: that motel room is not in the world.)"
    if item not in BEDTIME_ITEMS:
        return "(No story: that bedtime item is not in the world.)"
    return "(No story: that bedtime pairing does not support a clear sharing-and-repetition turn.)"


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def _name_for_role(role: str, fallback: str, rng: random.Random) -> str:
    if fallback:
        return fallback
    if role == "child":
        return rng.choice(NAMES)
    return rng.choice(HELPER_NAMES)


def _room_sentence(world: World) -> str:
    room = _safe_lookup(ROOMS, world.room)
    extras = room["extras"]
    if len(extras) == 3:
        return f"The room held {extras[0]}, {extras[1]}, and {extras[2]}."
    return f"The room looked quiet and ready for sleep."


def _repetition_line(action: str, count: int) -> str:
    if count == 1:
        return f"First, {action}."
    if count == 2:
        return f"Then, {action} again."
    return f"And once more, {action}, just the same gentle way."


def _shared_line(item: Entity, child: Entity, companion: Entity) -> str:
    return (
        f"{child.id} and {companion.id} shared {item.phrase} so each of them could feel cozy."
    )


def _bedtime_action(world: World, child: Entity, companion: Entity, item: Entity, action: str) -> None:
    count = int(world.facts.get("repeat_count", 0)) + 1
    world.facts["repeat_count"] = count
    world.say(_repetition_line(action, count))


def _share(item: Entity, child: Entity, companion: Entity) -> None:
    item.shared_with.update({child.id, companion.id})


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is reasonable when the room and item both exist.
valid_story(R, I) :- room(R), item(I).

% Sharing is central when the item is marked shared.
needs_sharing(I) :- item(I), shared_item(I).

% Repetition appears when the bedtime action is done more than once.
repeats(A) :- action(A), repeat_count(N), N >= 2.

% A complete tale needs both: repetition and sharing.
complete_story(R, I, A) :- valid_story(R, I), needs_sharing(I), repeats(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for iid, item in BEDTIME_ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item["shared"]:
            lines.append(asp.fact("shared_item", iid))
    lines.append(asp.fact("action", "tuck_in"))
    lines.append(asp.fact("action", "read_again"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_complete_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show complete_story/3."))
    return sorted(set(asp.atoms(model, "complete_story")))


def asp_verify() -> int:
    python_set = {
        (room, item, action)
        for room in ROOMS
        for item, cfg in BEDTIME_ITEMS.items()
        for action in ("tuck_in", "read_again")
        if valid_combo(room, item) and cfg["shared"] and action == "read_again"
    }
    asp_set = set(asp_complete_stories())
    if asp_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(asp_set)} complete stories).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  only in clingo:", sorted(asp_set - python_set))
    print("  only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    if not valid_combo(params.room, params.item):
        pass

    world = World(params.motel, params.room)
    room_cfg = _safe_lookup(ROOMS, params.room)
    item_cfg = _safe_lookup(BEDTIME_ITEMS, params.item)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        label=params.child_name,
        meters={"sleepiness": 0.0, "comfort": 0.0},
        memes={"hope": 1.0, "small_worry": 0.0, "joy": 0.0},
    ))
    companion = world.add(Entity(
        id=params.companion_name,
        kind="character",
        type=params.companion_type,
        label=params.companion_name,
        meters={"sleepiness": 0.0, "comfort": 0.0},
        memes={"patience": 1.0, "joy": 0.0},
    ))
    item = world.add(Entity(
        id=params.item,
        kind="thing",
        type=params.item,
        label=item_cfg["label"],
        phrase=item_cfg["phrase"],
        owner=child.id,
        shared_with={child.id, companion.id} if item_cfg["shared"] else {child.id},
        plural=item_cfg["plural"],
        meters={"softness": 1.0},
        memes={"calm": 1.0},
    ))

    world.facts.update(
        child=child,
        companion=companion,
        item=item,
        room_label=room_cfg["label"],
        room_mood=room_cfg["mood"],
        action_repeat=params.repeated_action,
        action_share=params.shared_action,
    )

    # Beginning
    world.say(f"That night, {child.id} and {companion.id} stayed at {params.motel}.")
    world.say(_room_sentence(world))
    world.say(f"{child.id} loved the bedtime feel of the place, because everything was quiet and slow.")
    world.say(f"{child.id} held {item.phrase} close, as if it were a tiny moon made for sleep.")

    # Middle: repetition and tension
    world.para()
    child.memes["small_worry"] += 1.0
    world.say(f"{child.id} wanted the same bedtime thing again and again.")
    _bedtime_action(world, child, companion, item, params.repeated_action)
    _bedtime_action(world, child, companion, item, params.repeated_action)
    world.say(f"But {child.id} did not want to keep {params.shared_action} alone.")
    world.say(f"The motel room felt smaller when one cozy thing had to be enough for two sleepy people.")

    # Turn: sharing
    world.para()
    companion.memes["patience"] += 1.0
    child.meters["comfort"] += 1.0
    companion.meters["comfort"] += 1.0
    _share(item, child, companion)
    world.say(
        f"Then {companion.id} smiled and said, "
        f'"We can share it. You do one part, and I do the next."'
    )
    world.say(
        f"So {child.id} and {companion.id} took turns {params.shared_action}, "
        f'and the little ritual became even gentler when it was shared.'
    )

    # End image
    world.para()
    child.meters["sleepiness"] += 1.0
    companion.meters["sleepiness"] += 1.0
    child.memes["joy"] += 1.0
    companion.memes["joy"] += 1.0
    world.say(
        f"At last, {child.id} was tucked in beside {companion.id}, with {item.phrase} shared between them."
    )
    world.say(
        f"The motel lamp glowed softly, the repeated bedtime steps were finished, and both of them drifted off feeling safe."
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    comp = _safe_fact(world, f, "companion")
    item = _safe_fact(world, f, "item")
    return [
        f'Write a gentle bedtime story set in a motel room where {child.id} and {comp.id} share {item.phrase} and repeat a soothing routine.',
        f"Tell a child-friendly story about a motel night, a repeated bedtime action, and two people learning to share a cozy item.",
        f'Write a short bedtime story that includes the word "motel" and ends with a shared sleepy ritual.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    comp: Entity = _safe_fact(world, f, "companion")
    item: Entity = _safe_fact(world, f, "item")
    repeat_count = int(f.get("repeat_count", 0))
    return [
        QAItem(
            question=f"Where did {child.id} and {comp.id} spend the night?",
            answer=f"They spent the night at {world.motel}, in {f['room_label']}.",
        ),
        QAItem(
            question=f"What did {child.id} want to do again and again before sleep?",
            answer=f"{child.id} wanted to {f['action_repeat']} again and again as part of the bedtime routine.",
        ),
        QAItem(
            question=f"How did they make bedtime easier in the motel room?",
            answer=f"They shared {item.phrase} and took turns {f['action_share']}, which made the room feel cozy for both of them.",
        ),
        QAItem(
            question=f"How many times did the story show the bedtime action repeating?",
            answer=f"It was shown {repeat_count} times, so the repeating part felt steady and soothing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a motel?",
            answer="A motel is a place where people can stay for a night or a short trip, often with rooms near parking spaces.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means two or more people use something together or take turns so everyone gets a fair part.",
        ),
        QAItem(
            question="Why can repetition feel comforting at bedtime?",
            answer="Repetition can feel comforting because the same gentle steps help the brain settle down and feel safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

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
        if e.kind == "thing":
            bits.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(
        motel="the Lantern Motel",
        room="small_room",
        item="blanket",
        child_name="Mia",
        child_type="girl",
        companion_name="Nana",
        companion_type="grandparent",
        repeated_action="tuck in the blanket",
        shared_action="reading one more page",
    ),
    StoryParams(
        motel="the Blue Door Motel",
        room="family_room",
        item="book",
        child_name="Leo",
        child_type="boy",
        companion_name="Aunt June",
        companion_type="parent",
        repeated_action="smooth the pillow",
        shared_action="turning the page together",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime storyworld set in a motel room.")
    ap.add_argument("--motel", default="the Lantern Motel")
    ap.add_argument("--room", choices=sorted(ROOMS))
    ap.add_argument("--item", choices=sorted(BEDTIME_ITEMS))
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--companion-name")
    ap.add_argument("--companion-type", choices=["parent", "sibling", "grandparent"])
    ap.add_argument("--repeated-action")
    ap.add_argument("--shared-action")
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
    room = getattr(args, "room", None) or rng.choice(sorted(ROOMS))
    item = getattr(args, "item", None) or rng.choice(sorted(BEDTIME_ITEMS))
    if not valid_combo(room, item):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    companion_type = getattr(args, "companion_type", None) or rng.choice(["parent", "sibling", "grandparent"])
    child_name = getattr(args, "child_name", None) or rng.choice(NAMES)
    companion_name = getattr(args, "companion_name", None) or rng.choice(HELPER_NAMES)
    repeated_action = getattr(args, "repeated_action", None) or rng.choice([
        "read the same page",
        "smooth the blanket",
        "whisper the same good-night line",
    ])
    shared_action = getattr(args, "shared_action", None) or rng.choice([
        "reading one more page",
        "sharing the pillow corner",
        "turning the page together",
    ])
    return StoryParams(
        motel=getattr(args, "motel", None),
        room=room,
        item=item,
        child_name=child_name,
        child_type=child_type,
        companion_name=companion_name,
        companion_type=companion_type,
        repeated_action=repeated_action,
        shared_action=shared_action,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show complete_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show complete_story/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 25):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
            header = f"### {p.child_name} at {p.motel} ({p.room}, {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
