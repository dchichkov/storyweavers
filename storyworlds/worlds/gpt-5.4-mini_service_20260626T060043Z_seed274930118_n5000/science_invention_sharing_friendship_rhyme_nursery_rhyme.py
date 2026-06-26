#!/usr/bin/env python3
"""
A standalone storyworld about a little science invention, sharing, friendship,
and rhyme in a nursery-rhyme style.

The world premise:
- A child invents a tiny science toy.
- The toy only works well when it is shared.
- A small friendship tension appears when someone wants to keep it.
- The ending resolves through sharing and a rhyming refrain.
"""

from __future__ import annotations

import argparse
import copy
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

TITLE = "science invention sharing friendship rhyme"

# ---------------------------------------------------------------------------
# World model
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    child: object | None = None
    friend: object | None = None
    toy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str = "the sunny shed"
    light: str = "sunny"
    theme: str = "science"
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
class Invention:
    id: str
    label: str
    phrase: str
    uses: str
    makes: str
    rhyme_tag: str
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
    place: str
    invention: str
    child_name: str
    child_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "shed": Setting(place="the sunny shed", light="sunny"),
    "kitchen": Setting(place="the warm kitchen table", light="bright"),
    "porch": Setting(place="the little front porch", light="golden"),
}

INVENTIONS = {
    "bellwheel": Invention(
        id="bellwheel",
        label="bell wheel",
        phrase="a tiny bell wheel with bright blue spokes",
        uses="spin and sing",
        makes="a merry chime",
        rhyme_tag="bell",
    ),
    "soapboat": Invention(
        id="soapboat",
        label="soap boat",
        phrase="a small soap boat with a shiny sail",
        uses="float and glide",
        makes="a bubbly trail",
        rhyme_tag="boat",
    ),
    "kitefan": Invention(
        id="kitefan",
        label="kite fan",
        phrase="a paper kite fan tied with a string",
        uses="whirl and hum",
        makes="a breezy tune",
        rhyme_tag="kite",
    ),
}

CHILD_NAMES = ["Mina", "Ned", "Lila", "Toby", "Mabel", "Ben"]
TRAITS = ["curious", "cheery", "gentle", "bright", "tiny"]

RHYMES = {
    "bell": ("bell", "swell", "well"),
    "boat": ("boat", "float", "note"),
    "kite": ("kite", "bright", "light"),
}

# ---------------------------------------------------------------------------
# Simulation rules
# ---------------------------------------------------------------------------


def rhyme_line(word: str) -> str:
    a, b, c = _safe_lookup(RHYMES, word)
    return f"{a}, {b}, and {c} make a nursery-rhyme melody."


def introduce(world: World, child: Entity, friend: Entity, invention: Invention) -> None:
    world.say(
        f"{child.id} was a little {child.memes.get('trait', 'curious')} {child.type} "
        f"who loved {world.setting.theme} and making things."
    )
    world.say(
        f"At {world.setting.place}, {child.id} built {invention.phrase}, "
        f"and {invention.uses} was the game it loved to do."
    )
    world.say(
        f"{friend.id} came by with a smile, and the two children were friends from the start."
    )


def use_invention(world: World, child: Entity, invention: Invention) -> None:
    child.meters["pride"] = child.meters.get("pride", 0) + 1
    invention.meters["active"] = invention.meters.get("active", 0) + 1
    world.say(
        f"{child.id} turned the little machine, and it made {invention.makes} "
        f"that sounded soft and sweet."
    )


def share_want(world: World, child: Entity, friend: Entity, invention: Invention) -> None:
    child.memes["attachment"] = child.memes.get("attachment", 0) + 1
    world.say(
        f"{friend.id} clapped and asked, 'May I try?' but {child.id} held the toy a bit too tight."
    )
    world.say(
        f"For a tiny tick, the room went still, like a cloud before rain."
    )


def conflict(world: World, child: Entity, friend: Entity, invention: Invention) -> None:
    child.memes["stingy"] = child.memes.get("stingy", 0) + 1
    friend.memes["sad"] = friend.memes.get("sad", 0) + 1
    world.say(
        f"{child.id} wanted to keep the invention all to {child.pronoun('object')}self, "
        f"and {friend.id} felt the hurt."
    )
    world.say(
        f"Without sharing, the tune sounded small, not bright, not merry."
    )


def turn_to_sharing(world: World, child: Entity, friend: Entity, invention: Invention) -> None:
    child.memes["stingy"] = 0
    child.memes["kind"] = child.memes.get("kind", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    invention.meters["shared"] = invention.meters.get("shared", 0) + 1
    world.say(
        f"Then {child.id} thought of friendship, gave the toy a careful turn, and said, "
        f"'You may play too.'"
    )
    world.say(
        f"The moment {friend.id} touched it, the little machine began to sing more clearly."
    )


def finish(world: World, child: Entity, friend: Entity, invention: Invention) -> None:
    child.memes["friendship"] = child.memes.get("friendship", 0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0) + 1
    world.say(
        f"{child.id} and {friend.id} took turns, one by one, and laughed together in time."
    )
    world.say(
        f"{rhyme_line(invention.rhyme_tag)}"
    )
    world.say(
        f"At the end, the invention was shared, the friends were glad, and the little song felt complete."
    )


def tell(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        pass
    if params.invention not in INVENTIONS:
        pass
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        traits=["little"],
        memes={"trait": "curious"},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_type,
        traits=["little"],
        memes={"trait": "kind"},
    ))
    invention = _safe_lookup(INVENTIONS, params.invention)
    toy = world.add(Entity(
        id=invention.id,
        kind="thing",
        type="toy",
        label=invention.label,
        phrase=invention.phrase,
        owner=child.id,
    ))

    world.facts.update(child=child, friend=friend, invention=toy, invention_def=invention)
    introduce(world, child, friend, invention)
    world.para()
    use_invention(world, child, invention)
    share_want(world, child, friend, invention)
    conflict(world, child, friend, invention)
    world.para()
    turn_to_sharing(world, child, friend, invention)
    finish(world, child, friend, invention)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")  # type: ignore[assignment]
    friend: Entity = _safe_fact(world, f, "friend")  # type: ignore[assignment]
    inv: Entity = _safe_fact(world, f, "invention")  # type: ignore[assignment]
    inv_def: Invention = _safe_fact(world, f, "invention_def")  # type: ignore[assignment]
    return [
        f'Write a nursery-rhyme-style story about {child.id}, a small science invention, and friendship.',
        f"Tell a gentle story where {child.id} and {friend.id} learn to share {inv.label}.",
        f"Write a short rhyming story that includes {inv_def.rhyme_tag}, sharing, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")  # type: ignore[assignment]
    friend: Entity = _safe_fact(world, f, "friend")  # type: ignore[assignment]
    inv: Entity = _safe_fact(world, f, "invention")  # type: ignore[assignment]
    inv_def: Invention = _safe_fact(world, f, "invention_def")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {child.id} make at {world.setting.place}?",
            answer=f"{child.id} made {inv.phrase}, a little science invention for play.",
        ),
        QAItem(
            question=f"Why did {friend.id} feel sad for a little while?",
            answer=f"{friend.id} felt sad because {child.id} did not want to share {inv.label} at first.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"{child.id} chose to share, the friends took turns, and the invention made a brighter sound.",
        ),
        QAItem(
            question=f"What kind of ending did the story have?",
            answer=f"It ended with friendship, sharing, and a rhyming line about {inv_def.rhyme_tag}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is science?",
            answer="Science is a way of learning about the world by looking, wondering, testing, and finding out how things work.",
        ),
        QAItem(
            question="What is an invention?",
            answer="An invention is something new that people make to solve a problem or help with a job or a game.",
        ),
        QAItem(
            question="Why is sharing nice?",
            answer="Sharing is nice because it lets more than one person enjoy the same thing, and it can help friends feel close.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like bell and swell.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% An invention is shareable in this storyworld.
shareable(I) :- invention(I).

% Friendship grows when the toy is shared.
friendship_gain(C) :- shares(C, I), invention(I).

% The ending is good if the child shares the invention and the friend smiles.
happy_end :- shares(C, I), friend(F), invention(I), smiles(F).

#show shareable/1.
#show friendship_gain/1.
#show happy_end/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("setting_place", pid, place.place))
    for iid, inv in INVENTIONS.items():
        lines.append(asp.fact("invention", iid))
        lines.append(asp.fact("rhyme_tag", iid, inv.rhyme_tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show shareable/1.\n#show friendship_gain/1.\n#show happy_end/0."))
    shown = {str(a) for a in model}
    expected = {"shareable(bellwheel)", "shareable(soapboat)", "shareable(kitefan)"}
    if shown.issuperset(expected):
        print("OK: ASP rules load and produce shareable inventions.")
        return 0
    print("MISMATCH in ASP verification.")
    print("shown:", sorted(shown))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme science invention story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--invention", choices=INVENTIONS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--child-type", choices=["girl", "boy"], dest="child_type")
    ap.add_argument("--friend-type", choices=["girl", "boy"], dest="friend_type")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    invention = getattr(args, "invention", None) or rng.choice(list(INVENTIONS))
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    friend_type = getattr(args, "friend_type", None) or ("boy" if child_type == "girl" else "girl")
    child_name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    friend_name = getattr(args, "friend", None) or rng.choice([n for n in CHILD_NAMES if n != child_name])
    if child_name == friend_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        invention=invention,
        child_name=child_name,
        child_type=child_type,
        friend_name=friend_name,
        friend_type=friend_type,
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
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
    StoryParams(place="shed", invention="bellwheel", child_name="Mina", child_type="girl", friend_name="Ned", friend_type="boy"),
    StoryParams(place="kitchen", invention="soapboat", child_name="Lila", child_type="girl", friend_name="Ben", friend_type="boy"),
    StoryParams(place="porch", invention="kitefan", child_name="Toby", child_type="boy", friend_name="Mabel", friend_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show shareable/1.\n#show friendship_gain/1.\n#show happy_end/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show shareable/1.\n#show friendship_gain/1.\n#show happy_end/0."))
        for atom in model:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
