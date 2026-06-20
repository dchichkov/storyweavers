#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/warren_viaduct_misunderstanding_happy_ending_foreshadowing_myth.py
====================================================================================================

A standalone storyworld in a small mythic domain: a child messenger, a rabbit
warren, an old viaduct, a misunderstanding, a foreshadowed rescue, and a happy
ending.

The world is built around a tiny village myth. The children fear that the
stone viaduct is cursed when the rabbits vanish into the warren, but the truth
is gentler: the rabbits are carrying shiny trinkets to a hidden nest and the
viaduct is only sheltering them from rain. The story keeps the tone of a myth:
an omen, a mistaken belief, a reveal, and a peaceful ending image.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- generated prose driven by world state
- three Q&A sets from state, not from rendered text
- Python validity gate plus inline ASP twin
- standard CLI with --verify, --asp, --show-asp, --json, --qa, --trace, --all
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SCARED_MIN = 1.0
HELPFUL_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "priestess"}
        male = {"boy", "father", "man", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    myth_word: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Omen:
    id: str
    label: str
    sign: str
    meaning: str
    benign: bool
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Misunderstanding:
    id: str
    label: str
    belief: str
    truth: str
    correction: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    light: bool = False
    wet: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_scatter_rain(world: World) -> list[str]:
    out: list[str] = []
    if world.get("sky").meters["rain"] < THRESHOLD:
        return out
    sig = ("rain",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("viaduct").meters["wet"] += 1
    for k in world.characters():
        if k.role == "worryer":
            k.memes["fear"] += 1
    out.append("__rain__")
    return out


def _r_omen(world: World) -> list[str]:
    out: list[str] = []
    if world.get("bird").meters["sign"] < THRESHOLD:
        return out
    sig = ("omen",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["curiosity"] += 1
    out.append("__omen__")
    return out


CAUSAL_RULES = [Rule("rain", "weather", _r_scatter_rain), Rule("omen", "myth", _r_omen)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(place: Place, omen: Omen, misunderstanding: Misunderstanding) -> bool:
    return place.id in {"warren", "viaduct"} and omen.benign and misunderstanding.id == "vanishing_rabbits"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p.id, o.id, m.id) for p in PLACES.values() for o in OMENS.values() for m in MISUNDERSTANDINGS.values() if valid_combo(p, o, m)]


@dataclass
@dataclass
class StoryParams:
    place: str
    omen: str
    misunderstanding: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
    parent: str
    gift: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


PLACES = {
    "warren": Place("warren", "the rabbit warren", "warren", ["burrows", "soft earth"]),
    "viaduct": Place("viaduct", "the old viaduct", "viaduct", ["stone arches", "river shadow"]),
}

OMENS = {
    "white_stone": Omen("white_stone", "a white stone", "gleamed at dusk", "someone had lit a lamp below", True, {"light"}),
    "heron": Omen("heron", "a heron", "circled above the arches", "the river was waking", True, {"bird"}),
    "bells": Omen("bells", "distant bells", "rang over the hill", "the village feast was near", True, {"sound"}),
}

MISUNDERSTANDINGS = {
    "vanishing_rabbits": Misunderstanding(
        "vanishing_rabbits",
        "the rabbits were taken by the stone bridge",
        "The child thought the rabbits had vanished into danger.",
        "The rabbits were only hiding under the arches and running home through the warren.",
        "The elder pointed out the paw prints and the hidden path under the stones.",
        {"rabbits", "bridge"},
    ),
    "stolen_gift": Misunderstanding(
        "stolen_gift",
        "the shining berry was stolen",
        "The child thought a gift had been stolen.",
        "The rabbits had moved it to a safe burrow for the night.",
        "The elder followed the crumbs and found the little store of gifts.",
        {"gift"},
    ),
}

GIFTS = {
    "lantern": Gift("lantern", "lantern", "a lantern that glowed like a small moon", True, False, {"light"}),
    "cloak": Gift("cloak", "cloak", "a dry cloak", False, True, {"warmth"}),
    "bread": Gift("bread", "bread", "a round loaf of bread", False, False, {"gift"}),
}

GIRL_NAMES = ["Mira", "Iva", "Lena", "Nia", "Sera"]
BOY_NAMES = ["Tarin", "Oren", "Dima", "Bari", "Niko"]
TRAITS = ["watchful", "gentle", "bold", "patient", "curious"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about a warren, a viaduct, and a misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.misunderstanding and args.misunderstanding != "vanishing_rabbits":
        raise StoryError("This world only supports the rabbit-and-viaduct misunderstanding.")
    place = args.place or rng.choice(list(PLACES))
    omen = args.omen or rng.choice(list(OMENS))
    misunderstanding = args.misunderstanding or "vanishing_rabbits"
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_pool = [n for n in (GIRL_NAMES + BOY_NAMES) if n != child]
    elder = args.elder or rng.choice(elder_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    gift = args.gift or rng.choice(list(GIFTS))
    if place not in PLACES or omen not in OMENS or gift not in GIFTS:
        raise StoryError("(No valid combination matches the given options.)")
    if not valid_combo(PLACES[place], OMENS[omen], MISUNDERSTANDINGS[misunderstanding]):
        raise StoryError("(No valid combination matches the given options.)")
    return StoryParams(place, omen, misunderstanding, child, child_gender, elder, elder_gender, parent, gift)


def _setup(world: World, params: StoryParams) -> None:
    child = world.add(Entity(params.child, kind="character", type=params.child_gender, role="seeker", traits=["young", "watchful"]))
    elder = world.add(Entity(params.elder, kind="character", type=params.elder_gender, role="worryer", traits=["older", "patient"]))
    parent = world.add(Entity("Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    world.add(Entity("sky", kind="thing", type="sky", label="the sky"))
    world.add(Entity("bird", kind="thing", type="bird", label="the bird"))
    world.add(Entity("viaduct", kind="place", type="viaduct", label="the viaduct"))
    world.add(Entity("warren", kind="place", type="warren", label="the warren"))
    world.add(Entity("gift", kind="thing", type="gift", label=GIFTS[params.gift].label))
    world.get("bird").meters["sign"] = 1.0
    world.facts.update(child=child, elder=elder, parent=parent, place=PLACES[params.place], omen=OMENS[params.omen], misunderstanding=MISUNDERSTANDINGS[params.misunderstanding], gift=GIFTS[params.gift])


def tell(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    child: Entity = world.facts["child"]
    elder: Entity = world.facts["elder"]
    parent: Entity = world.facts["parent"]
    place: Place = world.facts["place"]
    omen: Omen = world.facts["omen"]
    misunderstanding: Misunderstanding = world.facts["misunderstanding"]
    gift: Gift = world.facts["gift"]

    world.say(f"Long ago, {child.id} and {elder.id} came to {place.label}, where the stones of {place.myth_word} kept the river in their shadow.")
    world.say(f"At dusk, {omen.label} {omen.sign}, and the sign made {child.id} remember the old tale that a hidden thing had gone missing.")
    world.para()
    child.memes["fear"] += 1
    world.say(f'"Look," {child.id} whispered. "The {misunderstanding.id.replace("_", " ")} must be true."')
    world.say(f'But {elder.id} shook {elder.pronoun("possessive")} head. "{misunderstanding.belief} Yet the earth under the arches told another story."')
    world.say(f"{elder.id} knelt, found the paw prints, and followed them toward the {world.get("warren").label}.")
    world.para()
    child.meters["journey"] += 1
    world.get("viaduct").meters["wet"] += 1
    world.get("warren").meters["safe"] += 1
    world.say(f"Then rain began to fall softly on the viaduct, just as if the sky itself wanted to make the lesson gentle.")
    propagate(world, narrate=False)
    world.say(f"The rabbits were not taken at all. They were hiding in the warren, carrying {gift.phrase} to a dry nest beneath the stone arch.")
    world.say(f"{elder.id} laughed softly and showed {child.id} the crumbs, the prints, and the hidden path that the omen had only half-revealed.")
    world.para()
    child.memes["fear"] = 0.0
    child.memes["joy"] += 1
    elder.memes["joy"] += 1
    world.say(f"{parent.label_word.capitalize()} arrived with {GIFTS[params.gift].phrase if False else 'a warm smile'} and was glad the worry had turned into a better story.")
    world.say(f"At last, {child.id} and {elder.id} shared the gift with the rabbits, and the viaduct stood quiet above them like a silver rib of old stone.")
    world.say(f"That night, {child.id} went home knowing the old sign had not been a warning after all, but a foreshadowing of safe paws, kind hands, and a happy ending.")
    world.facts.update(outcome="happy", foreshadowed=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a young child that includes the words "{f["place"].myth_word}" and "viaduct".',
        f"Tell a gentle myth where {f['child'].id} misreads a sign near the viaduct, but the elder explains the truth and the ending is happy.",
        "Write a story with foreshadowing: an omen seems scary at first, then turns out to point toward a kind and safe ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    misunderstanding: Misunderstanding = f["misunderstanding"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and {elder.id}, two travelers who came to the viaduct and listened to an old sign."),
        ("What did the child misunderstand?", f"{child.id} thought that {misunderstanding.label} was happening. In truth, the rabbits were only moving safely through the warren."),
        ("How did the elder help?", f"{elder.id} followed the paw prints, explained the truth, and led the child to the hidden path under the stone arches."),
        ("How did the story end?", "It ended happily: the child learned the truth, the rabbits stayed safe, and everyone left with a calmer heart."),
    ]
    if f.get("foreshadowed"):
        qa.append(("What did the omen do in the story?", "The omen seemed mysterious at first, but it quietly hinted at the safe ending before anyone understood it. That is how the story used foreshadowing."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a warren?", "A warren is a nest of rabbit tunnels and chambers under the ground. Rabbits use it as a home and a hiding place."),
        ("What is a viaduct?", "A viaduct is a long bridge made of arches that carries a road across a valley or river. Old viaducts can stand like stone giants over the water."),
        ("What is foreshadowing?", "Foreshadowing is when a story gives a small clue about what will happen later. The clue may seem mysterious at first, but it makes sense after the ending."),
        ("What is a misunderstanding?", "A misunderstanding happens when someone believes the wrong thing. Later, the truth clears the confusion."),
        ("Why can a myth feel grand?", "A myth often makes ordinary places feel ancient and important, as if the world itself is speaking through signs and tales."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("warren", "heron", "vanishing_rabbits", "Mira", "girl", "Oren", "boy", "mother", "lantern"),
    StoryParams("viaduct", "white_stone", "vanishing_rabbits", "Tarin", "boy", "Lena", "girl", "father", "bread"),
]


def explain_rejection() -> str:
    return "(No story: this world only tells a benign myth about a warren, a viaduct, and a misunderstood sign.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
    for oid, o in OMENS.items():
        lines.append(asp.fact("omen", oid))
        if o.benign:
            lines.append(asp.fact("benign", oid))
    for mid, m in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, O, M) :- place(P), omen(O), benign(O), misunderstanding(M), M = vanishing_rabbits.
happy(valid) :- valid(_, _, _).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, omen=None, misunderstanding=None, gift=None, child=None, child_gender=None, elder=None, elder_gender=None, parent=None), random.Random(7)))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    omen = args.omen or rng.choice(list(OMENS))
    misunderstanding = args.misunderstanding or "vanishing_rabbits"
    if place not in PLACES or omen not in OMENS or misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError(explain_rejection())
    if not valid_combo(PLACES[place], OMENS[omen], MISUNDERSTANDINGS[misunderstanding]):
        raise StoryError(explain_rejection())
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    gift = args.gift or rng.choice(list(GIFTS))
    return StoryParams(place, omen, misunderstanding, child, child_gender, elder, elder_gender, parent, gift)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
