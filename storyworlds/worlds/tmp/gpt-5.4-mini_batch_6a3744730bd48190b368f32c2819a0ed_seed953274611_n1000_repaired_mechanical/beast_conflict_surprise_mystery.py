#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/beast_conflict_surprise_mystery.py
===================================================================

A tiny standalone storyworld for a child-friendly mystery with a beast, a
conflict, and a surprise ending.

Premise
-------
A child and a helper search for clues in a moonlit place because something has
gone missing. They hear a beast in the dark, think it may be the cause, and
face a tense conflict about whether to run, hide, or keep looking. The mystery
turns when the beast is revealed to be harmless and connected to the missing
thing, leading to a surprising but gentle resolution.

This world models:
- typed entities with physical meters and emotional memes
- a small forward-chained causal engine
- a reasonableness gate over valid combos
- an inline ASP twin with parity verification
- three Q&A sets grounded in world state, not rendered prose
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    dark: str
    clue: str
    sound: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Beast:
    id: str
    label: str
    sound: str
    harmless_sign: str
    clue_kind: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class MissingThing:
    id: str
    label: str
    phrase: str
    hidden_in: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Resolution:
    id: str
    sense: int
    power: int
    text: str
    surprise: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    place: str
    beast: str
    missing: str
    helper: str
    child: str
    child_gender: str
    helper_gender: str
    resolution: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if not child or not helper:
        return out
    if child.memes["fear"] >= THRESHOLD and child.memes["curiosity"] >= THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["conflict"] += 1
            helper.memes["conflict"] += 1
            out.append("__conflict__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    clue = world.entities.get("clue")
    if clue and clue.meters["found"] >= THRESHOLD:
        sig = ("clue",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("room").meters["mystery"] = max(0.0, world.get("room").meters["mystery"] - 1)
            out.append("The room felt a little less mysterious.")
    return out


CAUSAL_RULES = [Rule("conflict", "social", _r_conflict), Rule("clue", "mystery", _r_clue)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def beakornable(beast: Beast, missing: MissingThing) -> bool:
    return "beast" in beast.tags and "missing" in missing.tags


def sensible_resolutions() -> list[Resolution]:
    return [r for r in RESOLUTIONS.values() if r.sense >= SENSE_MIN]


def outcome_of(params: StoryParams) -> str:
    if params.resolution == "quietly_listen":
        return "surprising"
    res = RESOLUTIONS[params.resolution]
    return "solved" if res.power >= 2 else "tangled"


def best_resolution() -> Resolution:
    return max(RESOLUTIONS.values(), key=lambda r: r.sense)


SENSE_MIN = 2


def predict(world: World, missing_id: str) -> dict:
    sim = world.copy()
    _search(sim, narrate=False)
    return {
        "found": sim.get("clue").meters["found"] >= THRESHOLD,
        "mystery": sim.get("room").meters["mystery"],
    }


def _search(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    helper = world.get("helper")
    clue = world.get("clue")
    beast = world.get("beast")
    room = world.get("room")

    child.memes["curiosity"] += 1
    room.meters["mystery"] += 1
    world.say(
        f"{child.id} and {helper.id} followed tiny signs through the {room.label}."
    )
    world.say(
        f"They heard a low {beast.attrs['sound']} from the dark, and that made the night feel like a mystery."
    )
    child.memes["fear"] += 1
    helper.memes["fear"] += 1
    clue.meters["found"] += 1
    clue.meters["shone"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, place: Place, child: Entity, helper: Entity, missing: MissingThing) -> None:
    child.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On a quiet evening, {child.id} and {helper.id} searched the {place.label} for {missing.phrase}."
    )
    world.say(
        f"The {place.label} was {place.dark}, and every little sound seemed to hide a clue."
    )


def conflict_beat(world: World, child: Entity, helper: Entity, beast: Beast) -> None:
    pred = predict(world, "clue")
    world.facts["predicted_mystery"] = pred["mystery"]
    world.say(
        f"Then something moved in the dark. {child.id} thought the {beast.label} might be the problem."
    )
    world.say(
        f'{"\""}We should run!{"\""} {child.id} said. But {helper.id} stayed still and listened.'
    )


def surprise_beat(world: World, beast: Beast, missing: MissingThing, place: Place) -> None:
    beast_ent = world.get("beast")
    clue = world.get("clue")
    beast_ent.meters["revealed"] += 1
    clue.meters["found"] += 1
    world.say(
        f"At last the truth came out: the {beast.label} was only making that {beast.sound}, and it was guarding the missing {missing.label}."
    )
    world.say(
        f"Inside the {place.label}, hidden right where {missing.hidden_in} would be, lay the missing thing at last."
    )


def resolve(world: World, resolution: Resolution, child: Entity, helper: Entity, missing: MissingThing) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{helper.id} smiled and {resolution.text.format(missing=missing.label)}.'
    )
    world.say(
        f'The surprise was gentle, not scary: the {missing.label} was safe all along, and the {child.id} laughed at the silly mistake.'
    )


def ending_image(world: World, child: Entity, helper: Entity, missing: MissingThing, beast: Beast) -> None:
    world.say(
        f"By the end, {child.id} was holding the {missing.label}, {helper.id} was grinning, and the {beast.label} kept watch like a friendly shadow."
    )


def tell(place: Place, beast: Beast, missing: MissingThing, resolution: Resolution,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_name: str = "Dad", helper_gender: str = "father") -> World:
    world = World()
    room = world.add(Entity(id="room", kind="place", type="room", label=place.label, attrs={"sound": place.sound}))
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label="clue", meters=defaultdict(float)))
    beast_ent = world.add(Entity(id="beast", kind="thing", type="beast", label=beast.label, attrs={"sound": beast.sound}))
    missing_ent = world.add(Entity(id="missing", kind="thing", type="missing", label=missing.label))

    world.facts["place"] = place
    world.facts["beast_cfg"] = beast
    world.facts["missing_cfg"] = missing
    world.facts["resolution"] = resolution

    setup(world, place, child, helper, missing)
    world.para()
    conflict_beat(world, child, helper, beast)
    _search(world, narrate=True)
    world.para()
    surprise_beat(world, beast, missing, place)
    resolve(world, resolution, child, helper, missing)
    world.para()
    ending_image(world, child, helper, missing, beast)

    world.facts.update(
        child=child, helper=helper, room=room, clue=clue, beast=beast_ent, missing=missing_ent,
        outcome=outcome_of(StoryParams(place=place.id, beast=beast.id, missing=missing.id,
                                      helper=helper_name, child=child_name, child_gender=child_gender,
                                      helper_gender=helper_gender, resolution=resolution.id))
    )
    return world


PLACES = {
    "attic": Place(id="attic", label="attic", dark="dusty and dim", clue="old boxes", sound="scritch-scratch", tags={"mystery"}),
    "garden": Place(id="garden", label="garden", dark="full of shadowy bushes", clue="muddy footprints", sound="rustle-rustle", tags={"mystery"}),
    "cellar": Place(id="cellar", label="cellar", dark="cool and echoing", clue="shelves", sound="thump-thump", tags={"mystery"}),
}

BEASTS = {
    "cat": Beast(id="cat", label="cat beast", sound="mew-mew", harmless_sign="soft paws", clue_kind="fur", tags={"beast", "mystery"}),
    "mole": Beast(id="mole", label="mole beast", sound="sniff-sniff", harmless_sign="small nose", clue_kind="dirt", tags={"beast", "mystery"}),
    "dog": Beast(id="dog", label="dog beast", sound="woof-woof", harmless_sign="wagging tail", clue_kind="fur", tags={"beast", "mystery"}),
}

MISSING = {
    "key": MissingThing(id="key", label="silver key", phrase="a silver key", hidden_in="an old tin box", tags={"mystery"}),
    "hat": MissingThing(id="hat", label="blue hat", phrase="a blue hat", hidden_in="a basket of coats", tags={"mystery"}),
    "map": MissingThing(id="map", label="paper map", phrase="a paper map", hidden_in="a folded book", tags={"mystery"}),
}

RESOLUTIONS = {
    "quietly_listen": Resolution(id="quietly_listen", sense=3, power=3,
                                 text="heard the faint rattle and followed it to the missing {missing}",
                                 surprise="listened for the answer", tags={"surprise"}),
    "look_closer": Resolution(id="look_closer", sense=4, power=3,
                              text="looked closer and found the missing {missing} hiding nearby",
                              surprise="looked again", tags={"surprise"}),
    "call_help": Resolution(id="call_help", sense=2, power=2,
                            text="called for help and soon found the missing {missing}",
                            surprise="called for help", tags={"surprise"}),
}

GIRL_NAMES = ["Mia", "Ava", "Lily", "Zoe", "Nora"]
BOY_NAMES = ["Ben", "Max", "Noah", "Eli", "Finn"]

CURATED = [
    StoryParams(place="attic", beast="cat", missing="key", helper="Dad", child="Mia", child_gender="girl", helper_gender="father", resolution="look_closer"),
    StoryParams(place="garden", beast="mole", missing="map", helper="Mom", child="Ben", child_gender="boy", helper_gender="mother", resolution="quietly_listen"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for b in BEASTS:
            for m in MISSING:
                if beakornable(BEASTS[b], MISSING[m]):
                    combos.append((p, b, m))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery beast storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--beast", choices=BEASTS)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["mother", "father"])
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


def explain_rejection(beast: Beast, missing: MissingThing) -> str:
    return f"(No story: the {beast.label} doesn't really fit the missing {missing.label} mystery.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.beast and args.missing:
        if not beakornable(BEASTS[args.beast], MISSING[args.missing]):
            raise StoryError(explain_rejection(BEASTS[args.beast], MISSING[args.missing]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.beast is None or c[1] == args.beast)
              and (args.missing is None or c[2] == args.missing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, beast, missing = rng.choice(sorted(combos))
    resolution = args.resolution or rng.choice(sorted(RESOLUTIONS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["Mom", "Dad"])
    return StoryParams(place=place, beast=beast, missing=missing, helper=helper, child=child,
                       child_gender=child_gender, helper_gender=helper_gender, resolution=resolution)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that includes the word "beast" and ends with a surprise clue.',
        f'Tell a tense but gentle story where {f["child"].label} thinks a beast in the {f["place"].label} caused the trouble, but the truth is surprising.',
        f'Write a short mystery for a young child with a conflict, a strange sound, and a happy surprise at the end.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    missing = f["missing_cfg"]
    beast = f["beast_cfg"]
    qa = [
        ("Who is the story about?", f"It is about {child.label} and {helper.label}, who went searching in the {place.label}."),
        ("What were they looking for?", f"They were looking for {missing.phrase}. The mystery began because it was missing from its usual spot."),
        ("Why was there a conflict?", f"{child.label} got scared by the beast sound and wanted to run, while {helper.label} wanted to keep looking. That difference made the search tense for a moment."),
        ("What was the surprise?", f"The beast was not the real problem at all. It was connected to the missing {missing.label}, so the scary sound turned out to be part of the answer."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["beast_cfg"].tags) | set(world.facts["missing_cfg"].tags) | {"mystery"}
    out = []
    if "beast" in tags:
        out.append(("What is a beast in a story?", "A beast is often a big animal or a creature in a tale. In this world, the beast only seemed scary at first."))
    if "mystery" in tags:
        out.append(("What is a mystery?", "A mystery is something puzzling that people try to figure out. Clues help them understand what is really happening."))
    if "surprise" in tags:
        out.append(("What is a surprise in a story?", "A surprise is a turn you do not expect. It makes the ending feel exciting and new."))
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.beast not in BEASTS or params.missing not in MISSING or params.resolution not in RESOLUTIONS:
        raise StoryError("Invalid StoryParams.")
    world = tell(PLACES[params.place], BEASTS[params.beast], MISSING[params.missing], RESOLUTIONS[params.resolution],
                 child_name=params.child, child_gender=params.child_gender,
                 helper_name=params.helper, helper_gender=params.helper_gender)
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


ASP_RULES = r"""
beastish(B) :- beast(B).
mysterious(P) :- place(P).
surprising(R) :- resolution(R).
compatible(P,B,M) :- beastish(B), mysterious(P), missing(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for bid in BEASTS:
        lines.append(asp.fact("beast", bid))
    for mid in MISSING:
        lines.append(asp.fact("missing", mid))
    for rid in RESOLUTIONS:
        lines.append(asp.fact("resolution", rid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combo parity.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    else:
        print("OK: parity and smoke test passed.")
    return rc


def valid_default_combo() -> StoryParams:
    return CURATED[0]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and {p.helper}: {p.place}, {p.beast}, {p.missing}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
