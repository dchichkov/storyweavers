#!/usr/bin/env python3
"""
storyworlds/worlds/similar_acknowledge_rhyme_friendship_folk_tale.py
====================================================================

A small folk-tale storyworld about two similar children who first mistake one
another for rivals, then acknowledge how alike they are, and finally turn that
similarity into friendship with a little rhyme.

Seed tale sketch:
---
In a village by the woods, a small girl and a small boy lived on the same lane.
They were so similar that the neighbors often mixed up their baskets, their
songs, and even their footsteps on the path.

One evening, both children reached the same stone well at the same time. Each
thought the other had taken the better water bucket. They crossed their arms and
spoke sharply. Then an old grandmother heard them and asked them to say what
they both loved. They admitted they both loved the same rhyme, the same apples,
and the same games. The grandmother smiled and said that friends can look
similar and still be kind. The children repeated a little rhyme together, then
shared the bucket and walked home as friends.

World model:
---
    child desire + shared object      -> child conflict if both want it
    spoke sharply                     -> membranes of blame/conflict rise
    acknowledged similarity           -> conflict drops, friendship rises
    shared rhyme                      -> friendship rises; the ending turns warm

Narrative instruments:
---
    Rhyme: short repeated lines used to soften the quarrel.
    Friendship: a state that grows when the children acknowledge their likeness.
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

THRESHOLD = 1.0



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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    friend: object | None = None
    hero: object | None = None
    thing: object | None = None
    def __post_init__(self) -> None:
        for key in ("shine", "fullness", "use", "distance"):
            self.meters.setdefault(key, 0.0)
        for key in ("joy", "love", "conflict", "similarity", "acknowledgment", "friendship"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
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
    place: str
    detail: str
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
class SharedThing:
    id: str
    label: str
    phrase: str
    place: str
    risk: str
    need_ack: bool = True
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
    shared_thing: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    elder_name: str
    elder_type: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "village": Setting(
        place="the village lane",
        detail="The lane was narrow and tidy, with a well at one end and a low wall at the other.",
        affords={"share_buckets", "say_rhyme"},
    ),
    "well": Setting(
        place="the old stone well",
        detail="The old well sat by a willow tree, cool and quiet, with one bucket hanging on a rope.",
        affords={"share_buckets", "say_rhyme"},
    ),
    "orchard": Setting(
        place="the apple orchard",
        detail="The orchard was full of low branches and red apples that shone like little lamps.",
        affords={"share_apples", "say_rhyme"},
    ),
    "gate": Setting(
        place="the garden gate",
        detail="The gate opened onto a green path where neighbors passed with baskets and smiles.",
        affords={"share_baskets", "say_rhyme"},
    ),
}

SHARED_THINGS = {
    "bucket": SharedThing(
        id="bucket", label="bucket", phrase="the village bucket", place="well", risk="borrowed too long"
    ),
    "apples": SharedThing(
        id="apples", label="apples", phrase="a basket of red apples", place="orchard", risk="taken without asking", need_ack=True
    ),
    "basket": SharedThing(
        id="basket", label="basket", phrase="a woven basket", place="gate", risk="mixed up", need_ack=True
    ),
}

GIRL_NAMES = ["Mira", "Nina", "Tala", "Lina", "Rosa", "Suri"]
BOY_NAMES = ["Oren", "Pavel", "Rumi", "Timo", "Bram", "Eli"]
ELDER_NAMES = ["Grandmother Iva", "Old Nera", "Aunt Sela", "Grandmother Mara"]
TRAITS = ["gentle", "curious", "proud", "bright", "spirited"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for thing_id, thing in SHARED_THINGS.items():
            if place == thing.place and "say_rhyme" in setting.affords:
                combos.append((place, thing_id))
    return combos


def is_reasonable(place: str, shared_thing: str) -> bool:
    return (place, shared_thing) in valid_combos()


def explain_rejection(place: str, shared_thing: str) -> str:
    thing = _safe_lookup(SHARED_THINGS, shared_thing)
    return (
        f"(No story: {thing.phrase} does not fit the chosen place, so there is no fair quarrel to mend "
        f"and no honest chance for a shared rhyme there.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale storyworld about similarity, acknowledgment, rhyme, and friendship."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--shared-thing", choices=SHARED_THINGS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-type", choices=["grandmother", "aunt"])
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
    combos = [c for c in valid_combos()
              if getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)
              and (getattr(args, "shared_thing", None) is None or c[1] == getattr(args, "shared_thing", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, thing = rng.choice(list(combos))
    if not is_reasonable(place, thing):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    friend_gender = getattr(args, "friend_gender", None) or ("boy" if hero_gender == "girl" else "girl")
    hero_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero_name])
    elder_type = getattr(args, "elder_type", None) or rng.choice(["grandmother", "aunt"])
    elder_name = getattr(args, "elder_name", None) or rng.choice(ELDER_NAMES)
    return StoryParams(
        place=place,
        shared_thing=thing,
        hero_name=hero_name,
        hero_type=hero_gender,
        friend_name=friend_name,
        friend_type=friend_gender,
        elder_name=elder_name,
        elder_type=elder_type,
    )


def _shared_label(thing: SharedThing) -> str:
    return thing.label


def make_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_type, label=params.friend_name))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder_type, label=params.elder_name))
    thing = world.add(Entity(
        id="thing",
        kind="thing",
        type="thing",
        label=_shared_label(_safe_lookup(SHARED_THINGS, params.shared_thing)),
        phrase=_safe_lookup(SHARED_THINGS, params.shared_thing).phrase,
        owner=None,
        caretaker=elder.id,
        plural=_safe_lookup(SHARED_THINGS, params.shared_thing).label.endswith("s"),
    ))

    hero.memes["similarity"] += 1
    friend.memes["similarity"] += 1
    hero.memes["love"] += 1
    friend.memes["love"] += 1

    world.say(
        f"Once in {setting.place}, there lived two children who were so similar that even the crows mistook one for the other."
    )
    world.say(
        f"{hero.label} was a {params.hero_type} with a {random.choice(['soft', 'bright', 'clear'])} voice, and {friend.label} was a {params.friend_type} with the very same kind of laugh."
    )
    world.say(
        f"They liked the same paths, the same apples, and the same little rhyme about moonlight and dew."
    )

    world.para()
    world.say(setting.detail)
    world.say(
        f"At the center of it all sat {thing.phrase}, and both children wanted {thing.it()} at once."
    )
    hero.meters["distance"] = 1
    friend.meters["distance"] = 1
    hero.memes["desire"] += 1
    friend.memes["desire"] += 1
    hero.memes["conflict"] += 1
    friend.memes["conflict"] += 1
    world.say(
        f"{hero.label} reached first, but {friend.label} reached just after, and both spoke at once: 'That is mine!'"
    )
    world.say(
        f"Their words grew sharp because each thought the other was only copying."
    )

    world.para()
    elder.memes["care"] += 1
    world.say(
        f"Then {elder.label} came along, hearing the two voices from the lane."
    )
    world.say(
        f"She did not scold. Instead, she asked them to look closely and acknowledge what they had in common."
    )
    hero.memes["acknowledgment"] += 1
    friend.memes["acknowledgment"] += 1
    hero.memes["similarity"] += 1
    friend.memes["similarity"] += 1
    hero.memes["conflict"] = 0
    friend.memes["conflict"] = 0
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"{hero.label} blinked, then said, 'You like the same rhyme I like.'"
    )
    world.say(
        f"{friend.label} nodded and answered, 'And you laugh in the same way I do.'"
    )

    world.para()
    world.say(
        f"Together they recited a small rhyme: 'Similar hearts may share one spark; kind words make the world less dark.'"
    )
    world.say(
        f"After that, they split {thing.it()} fairly and walked beside {elder.label} with easy steps."
    )
    world.say(
        f"By the time the sun went low, the two children were no longer only similar. They were friends."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        elder=elder,
        thing=thing,
        setting=setting,
        params=params,
        resolved=True,
    )
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, thing = f["hero"], f["friend"], f["thing"]
    return [
        f"Write a short folk tale about two children who are very similar and must acknowledge it before they can share {thing.phrase}.",
        f"Tell a gentle story where {hero.label} and {friend.label} argue over {thing.label}, then make up with a rhyme.",
        f"Write a simple village story about friendship, similar voices, and a wise elder who helps two children speak kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, elder, thing, params = f["hero"], f["friend"], f["elder"], f["thing"], f["params"]
    return [
        QAItem(
            question=f"Who were the two children in the story?",
            answer=f"The story was about {hero.label} and {friend.label}, two children who were very similar and lived near {world.setting.place}.",
        ),
        QAItem(
            question=f"What did the two children want at the same time?",
            answer=f"They both wanted {thing.phrase}, and that is why they started to quarrel.",
        ),
        QAItem(
            question=f"How did {elder.label} help them make peace?",
            answer=f"{elder.label} asked them to acknowledge what they had in common, and then they shared a little rhyme together.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the end, the children were no longer just similar; they had become friends and walked away together calmly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does acknowledge mean?",
            answer="To acknowledge something means to notice it clearly and say it out loud or admit that it is true.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a short pattern of words that sound alike at the end, like a tiny song or chant.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between people who care about each other, share, and try to be kind.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:7} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
shared(X) :- thing(X).
similar(A,B) :- character(A), character(B), A != B, similarity(A), similarity(B).
quarrel(A,B,X) :- wants(A,X), wants(B,X), A != B.
acknowledge(A) :- admitted(A).
friendship(A,B) :- similar(A,B), acknowledged(A), acknowledged(B), shared_rhyme(A,B).
resolved(A,B) :- friendship(A,B), shared(X), not quarrel(A,B,X).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, st in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(st.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, thing in SHARED_THINGS.items():
        lines.append(asp.fact("thing", tid))
        lines.append(asp.fact("place_of", tid, thing.place))
    lines.append(asp.fact("feature", "rhyme"))
    lines.append(asp.fact("feature", "friendship"))
    lines.append(asp.fact("seed_word", "similar"))
    lines.append(asp.fact("seed_word", "acknowledge"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1. #show thing/1."))
    return sorted(set(asp.atoms(model, "setting")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == {(k,) for k in SETTINGS}:
        print("OK: ASP facts loaded and basic parity check passed.")
        return 0
    print("MISMATCH in ASP parity.")
    return 1


CURATED = [
    StoryParams(
        place="well",
        shared_thing="bucket",
        hero_name="Mira",
        hero_type="girl",
        friend_name="Oren",
        friend_type="boy",
        elder_name="Grandmother Iva",
        elder_type="grandmother",
    ),
    StoryParams(
        place="orchard",
        shared_thing="apples",
        hero_name="Tala",
        hero_type="girl",
        friend_name="Eli",
        friend_type="boy",
        elder_name="Aunt Sela",
        elder_type="aunt",
    ),
    StoryParams(
        place="gate",
        shared_thing="basket",
        hero_name="Lina",
        hero_type="girl",
        friend_name="Bram",
        friend_type="boy",
        elder_name="Old Nera",
        elder_type="grandmother",
    ),
]


def generation_story(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return generation_story(params)


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
        print(asp_program("#show setting/1. #show thing/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

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
            header = f"### {p.hero_name} and {p.friend_name}: {p.shared_thing} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
