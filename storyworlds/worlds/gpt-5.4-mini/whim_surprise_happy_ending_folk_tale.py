#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/whim_surprise_happy_ending_folk_tale.py
=======================================================================

A small, self-contained storyworld for a folk-tale style surprise driven by a
child's whim. The core premise: a little character follows a harmless whim into
the woods, encounters a surprising helper or object, and ends with a happy,
warm, complete ending image that proves the surprise changed something.

The world is kept tiny and classical:
- a child
- a simple errand or play plan
- a whimsical detour
- a surprise that solves the problem
- a happy ending with a concrete gift or change

The story engine models typed entities with physical meters and emotional memes,
and the prose is driven by the simulated world state rather than by swapping
nouns into a frozen paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/whim_surprise_happy_ending_folk_tale.py
    python storyworlds/worlds/gpt-5.4-mini/whim_surprise_happy_ending_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/whim_surprise_happy_ending_folk_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/whim_surprise_happy_ending_folk_tale.py --trace
    python storyworlds/worlds/gpt-5.4-mini/whim_surprise_happy_ending_folk_tale.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    detail: str
    secret: str
    outdoor: bool = True
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
class Whim:
    id: str
    phrase: str
    motive: str
    surprise_kind: str
    trail: str
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
class Surprise:
    id: str
    label: str
    phrase: str
    help_text: str
    gift_text: str
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
class Ending:
    id: str
    image: str
    change: str
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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_lift_mood(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["wonder"] >= THRESHOLD and ("lift_mood",) not in world.fired:
        world.fired.add(("lift_mood",))
        child.memes["joy"] += 1
        out.append("__mood__")
    return out


def _r_heal_risk(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    surprise = world.get("surprise")
    if child.memes["fear"] >= THRESHOLD and surprise.meters["glow"] >= THRESHOLD:
        sig = ("heal_risk",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
            child.memes["relief"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("lift_mood", "social", _r_lift_mood),
    Rule("heal_risk", "social", _r_heal_risk),
]


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


def reasonableness_gate(place: Place, whim: Whim, surprise: Surprise, ending: Ending) -> bool:
    return bool(place.outdoor and whim.surprise_kind == surprise.id and ending.change)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for wid, whim in WHIMS.items():
            for sid, surprise in SURPRISES.items():
                for eid, ending in ENDINGS.items():
                    if reasonableness_gate(place, whim, surprise, ending):
                        combos.append((pid, wid, sid, eid))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    whim: str
    surprise: str
    ending: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def tell(place: Place, whim: Whim, surprise: Surprise, ending: Ending,
         child_name: str = "Mira", child_gender: str = "girl",
         helper_name: str = "Old Oak", helper_gender: str = "thing") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child", traits=["curious", "restless"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender,
                              role="helper", traits=["kind"]))
    place_ent = world.add(Entity(id="place", type="place", label=place.label))
    surprise_ent = world.add(Entity(id="surprise", type="thing", label=surprise.label))
    ending_ent = world.add(Entity(id="ending", type="thing", label=ending.image))

    world.facts["place"] = place
    world.facts["whim"] = whim
    world.facts["surprise"] = surprise
    world.facts["ending"] = ending

    child.memes["wonder"] = 1.0
    child.memes["hope"] = 1.0

    world.say(
        f"On a soft morning, {child.id} went down the lane by {place.label} "
        f"with nothing but a small {whim.id} in {child.pronoun('possessive')} heart. "
        f"{place.detail}"
    )
    world.say(
        f"{child.id} had a whim to {whim.phrase}, because the world seemed too neat "
        f"and {whim.motive} was a fine thing to chase."
    )

    world.para()
    child.memes["wonder"] += 1
    world.say(
        f"{child.id} followed {whim.trail} and found the place where {place.secret}."
    )
    world.say(
        f"There, by the old path, {surprise.phrase}. The sight was such a surprise "
        f"that {child.id} stood still and blinked twice."
    )

    child.memes["fear"] += 1
    surprise_ent.meters["glow"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But the surprise was a kind one: {surprise.help_text}. "
        f"{surprise.gift_text}"
    )

    world.para()
    world.say(
        f"{helper.id} had seen the turning of the day and smiled from the hedge. "
        f"With a nod, {helper.pronoun()} showed {child.id} the safe way home."
    )
    world.say(
        f"By evening, {ending.image}. {ending.change}."
    )
    child.memes["joy"] += 2
    child.memes["relief"] += 1

    world.facts.update(
        child=child,
        helper=helper,
        place_ent=place_ent,
        surprise_ent=surprise_ent,
        ending_ent=ending_ent,
        outcome="happy",
    )
    return world


PLACES = {
    "wood": Place(
        "wood",
        "the wood",
        "The trees leaned together like old neighbors, and a silver path curled between them.",
        "a hollow under the roots of a mossy tree",
        outdoor=True,
        tags={"wood", "folk_tale"},
    ),
    "hill": Place(
        "hill",
        "the hill",
        "The hill wore grass like a green blanket, and the wind sang softly along its side.",
        "a little nook where the stones made a half-door",
        outdoor=True,
        tags={"hill", "folk_tale"},
    ),
    "brook": Place(
        "brook",
        "the brook",
        "The brook laughed over its pebbles, and reeds bowed to listen.",
        "a bend where the water whispered under a willow",
        outdoor=True,
        tags={"brook", "folk_tale"},
    ),
}

WHIMS = {
    "whim_of_song": Whim(
        "whim",
        "sing to the birds",
        "long for a bright answer from the morning",
        "hidden_song",
        "the turning of a tune between the trees",
        tags={"whim", "song"},
    ),
    "whim_of_bread": Whim(
        "whim",
        "leave a crumb trail for the mice",
        "feel lonely for tiny friends",
        "mouse_friends",
        "the little crumb path beneath the brambles",
        tags={"whim", "bread"},
    ),
    "whim_of_bells": Whim(
        "whim",
        "hang a ribbon of bells on a branch",
        "want the wind to play along",
        "bell_branch",
        "the shy sound of a branch that waited",
        tags={"whim", "bells"},
    ),
}

SURPRISES = {
    "hidden_song": Surprise(
        "hidden_song",
        "a bird with a bright red scarf",
        "a bird with a bright red scarf sang from the thorn bush",
        "It answered the child's song and carried courage in its beak.",
        "It dropped a golden feather at {child}'s feet.",
        tags={"surprise", "bird"},
    ),
    "mouse_friends": Surprise(
        "mouse_friends",
        "a tiny mouse family",
        "a tiny mouse family peeped from a teacup shell",
        "They had been waiting for a kind voice all day.",
        "They shared a crumb ring and showed a hidden door in the grass.",
        tags={"surprise", "mouse"},
    ),
    "bell_branch": Surprise(
        "bell_branch",
        "an old woman in a blue cloak",
        "an old woman in a blue cloak stepped from behind the elder tree",
        "She had heard the bells before anyone else and came to help.",
        "She tied the bells, gave the child a ribbon, and led the way home.",
        tags={"surprise", "helper"},
    ),
}

ENDINGS = {
    "golden_feather": Ending(
        "golden_feather",
        "the child held a golden feather",
        "The feather stayed warm in a pocket and reminded the child of the brave song",
        tags={"ending", "feather"},
    ),
    "crumb_ring": Ending(
        "crumb_ring",
        "the child shared a crumb ring with the mice",
        "The child had new little friends and no longer felt alone",
        tags={"ending", "crumb", "friends"},
    ),
    "ribbon_bells": Ending(
        "ribbon_bells",
        "the child wore a ribbon of bells",
        "The bells chimed whenever the child walked, and the path felt cheerful",
        tags={"ending", "bells"},
    ),
}

GIRL_NAMES = ["Mira", "Elsa", "Nina", "Tessa", "Lena", "Dora", "Ruth", "Ivy"]
BOY_NAMES = ["Pip", "Owen", "Jory", "Milo", "Finn", "Otis", "Theo", "Bram"]


@dataclass
class ThemeHints:
    id: str
    note: str

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


THEME = ThemeHints("folk_tale", "A small folk tale of whim, surprise, and a happy ending.")


def _child_pair_name(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a folk-tale story for a young child that includes the word '{f['whim'].id}' and ends happily.",
        f"Tell a surprise story where {f['child'].id} follows a small whim in {f['place'].label} and meets a kind surprise.",
        f"Create a gentle folk tale with a surprise, a useful gift, and a happy ending image involving {f['ending'].image}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    whim = f["whim"]
    surprise = f["surprise"]
    ending = f["ending"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, who followed a small whim and wandered by {place.label}."),
        ("What did the child do on a whim?",
         f"{child.id} decided to {whim.phrase}. The whim gave the story its little turn toward surprise."),
        ("What was the surprise?",
         f"{surprise.label.capitalize()} appeared, and it was a kind surprise rather than a scary one. "
         f"The surprise helped {child.id} feel less alone."),
        ("How did the story end?",
         f"It ended happily, with {ending.image}. That ending shows the surprise changed the day for the better."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    place = f["place"]
    whim = f["whim"]
    surprise = f["surprise"]
    ending = f["ending"]
    return [
        ("What is a whim?",
         "A whim is a sudden small idea that pops into your head and makes you want to do something right away."),
        ("What does a surprise do in a story?",
         "A surprise changes what is happening in an unexpected way, which can make the story feel magical or new."),
        ("What is a folk tale?",
         "A folk tale is an old-style story passed along by people, often with simple characters, a special turn, and a gentle lesson."),
        ("Why do happy endings matter?",
         "A happy ending lets the reader feel safe and glad at the end, and it shows the trouble was resolved."),
        (f"Why is {place.label} a good story place?",
         f"{place.label.capitalize()} feels old and open, which suits a folk tale with a wandering whim and a surprise."),
        (f"Why does {whim.id} fit the story?",
         f"The word {whim.id} belongs in a tale about a sudden little decision, so it helps the story feel playful."),
        (f"Why is {surprise.label} important?",
         f"{surprise.label.capitalize()} is the kind surprise that gives the child a new gift, which makes the ending warm and complete."),
        (f"What does the ending image show?",
         f"It shows that {ending.change.lower()}, so the last picture of the story proves the child left with something good."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("wood", "whim_of_song", "hidden_song", "golden_feather", "Mira", "girl", "Old Oak", "thing"),
    StoryParams("hill", "whim_of_bread", "mouse_friends", "crumb_ring", "Pip", "boy", "Grandmother", "woman"),
    StoryParams("brook", "whim_of_bells", "bell_branch", "ribbon_bells", "Lena", "girl", "Blue Cloak", "woman"),
]


def explain_rejection() -> str:
    return "(No story: this world only tells folk-tale whim stories with a matching surprise and a happy ending.)"


ASP_RULES = r"""
valid(P, W, S, E) :- place(P), whim(W), surprise(S), ending(E),
                     whim_surprise(W, S), ending_happy(E), outdoor_place(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("outdoor_place", pid))
    for wid, w in WHIMS.items():
        lines.append(asp.fact("whim", wid))
        lines.append(asp.fact("whim_surprise", wid, w.surprise_kind))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    for eid in ENDINGS:
        lines.append(asp.fact("ending", eid))
        lines.append(asp.fact("ending_happy", eid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), _random.Random(7)))
        _ = sample.story
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    if rc == 0:
        print("OK: ASP parity and generate() smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale whim storyworld with a surprise and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--whim", choices=WHIMS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man", "thing"])
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
    if args.whim and args.surprise:
        w = WHIMS[args.whim]
        s = SURPRISES[args.surprise]
        if w.surprise_kind != s.id:
            raise StoryError("The chosen whim and surprise do not belong together in this tale.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.whim is None or c[1] == args.whim)
              and (args.surprise is None or c[2] == args.surprise)
              and (args.ending is None or c[3] == args.ending)]
    if not combos:
        raise StoryError(explain_rejection())
    place, whim, surprise, ending = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    helper_gender = args.helper_gender or rng.choice(["woman", "man", "thing"])
    helper = args.helper or (rng.choice(["Grandmother", "Old Oak", "Blue Cloak", "River Voice"]))
    return StoryParams(place, whim, surprise, ending, name, gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], WHIMS[params.whim], SURPRISES[params.surprise], ENDINGS[params.ending],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
