#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tub_bravery_rhyme_folk_tale.py
===============================================================

A small, standalone storyworld for a folk-tale flavored story about a child,
a tub, bravery, and rhyme.

Premise:
- A child needs to wash something shy, muddy, or smoky in an old tub.
- The child is afraid at first, but uses bravery and a little rhyme to make the
  task feel friendly.
- The washing changes the world state: dirt leaves, fear softens, and the tub
  becomes a place of song and care.

This script follows the Storyweavers contract:
- stdlib only
- shared result containers imported eagerly
- StoryParams, build_parser, resolve_params, generate, emit, main
- `--trace`, `--qa`, `--json`, `-n`, `--all`, `--seed`, `--asp`, `--verify`,
  `--show-asp`
- Python reasonableness gate + inline ASP twin
- state-driven story + grounded QA sets

Run it:
    python storyworlds/worlds/gpt-5.4-mini/tub_bravery_rhyme_folk_tale.py
    python storyworlds/worlds/gpt-5.4-mini/tub_bravery_rhyme_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/tub_bravery_rhyme_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/tub_bravery_rhyme_folk_tale.py --verify
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
    wettable: bool = False
    muddy: bool = False
    sootable: bool = False
    shy: bool = False

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
    name: str
    dark: str
    sound: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Trouble:
    id: str
    label: str
    phrase: str
    kind: str  # mud | soot
    risk: str
    arrives: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Remedy:
    id: str
    label: str
    phrase: str
    song: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_stain(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.kind != "thing":
            continue
        if ent.meters["stained"] < THRESHOLD:
            continue
        sig = ("stain", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "home" in world.entities:
            world.get("home").meters["mess"] += 1
        for hero in world.characters():
            hero.memes["worry"] += 1
        out.append("__stain__")
    return out


def _r_cheer(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes["bravery"] < THRESHOLD:
            continue
        sig = ("cheer", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["hope"] += 1
        out.append("__cheer__")
    return out


CAUSAL_RULES = [
    Rule("stain", "physical", _r_stain),
    Rule("cheer", "social", _r_cheer),
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


def wash_risk(trouble: Trouble) -> bool:
    return trouble.kind in {"mud", "soot"}


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= 2]


def is_reasonable(trouble: Trouble, place: Place) -> bool:
    return wash_risk(trouble) and "tub" in place.tags


def can_finish(remedy: Remedy, trouble: Trouble) -> bool:
    return remedy.power >= (2 if trouble.kind == "mud" else 3)


def predict(world: World, trouble_id: str) -> dict:
    sim = world.copy()
    _do_spill(sim, sim.get(trouble_id), narrate=False)
    return {
        "stained": sim.get(trouble_id).meters["stained"] >= THRESHOLD,
        "mess": sim.get("home").meters["mess"],
    }


def _do_spill(world: World, trouble: Entity, narrate: bool = True) -> None:
    trouble.meters["stained"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, helper: Entity, place: Place, trouble: Trouble) -> None:
    world.say(
        f"In a little village where the eaves creaked and the kettle sang, {child.id} "
        f"and {helper.id} came to {place.name}. {place.dark}"
    )
    world.say(
        f"They found {trouble.phrase}. {trouble.arrives}"
    )


def worry(world: World, helper: Entity, child: Entity, trouble: Trouble) -> None:
    pred = predict(world, "trouble")
    child.memes["worry"] += 1
    world.facts["predicted_mess"] = pred["mess"]
    world.say(
        f'{child.id} bit {child.pronoun("possessive")} lip. "If we touch {trouble.label}, '
        f"the whole room will need a scrub," f' {helper.label_word}," {child.pronoun()} said.'
    )


def brave_rhyme(world: World, child: Entity, trouble: Trouble, remedy: Remedy) -> None:
    child.memes["bravery"] += 1
    world.say(
        f'But {child.id} took a breath and stood tall. "{remedy.song}" '
        f"{child.pronoun().capitalize()} sang, and the words felt like a lantern."
    )
    world.say(
        f"With that brave little rhyme, {child.id} lifted {trouble.label} toward the old tub."
    )


def wash(world: World, trouble: Entity, remedy: Remedy) -> None:
    _do_spill(world, trouble)
    world.say(
        f"The {remedy.label} swirled and worked its charm. The water went from gray to clear, "
        f"and the tub held the trouble gently instead of letting it spread."
    )


def soothe(world: World, helper: Entity, child: Entity, trouble: Trouble, remedy: Remedy) -> None:
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    helper.memes["joy"] += 1
    world.say(
        f'{helper.id} smiled like a kind old bard. "Brave hearts can sing clean," '
        f'{helper.pronoun()} said. "And {trouble.label} does not frighten a steady hand."'
    )
    world.say(
        f"{child.id} laughed as {trouble.label} came clean, and the little rhyme danced on."
    )


def ending(world: World, child: Entity, helper: Entity, place: Place, trouble: Trouble) -> None:
    world.say(
        f"By the time the moon rose, the tub was bright, the air smelled fresh, and "
        f"{child.id} had a clean treasure where the trouble had been."
    )
    world.say(
        f"{helper.id} poured the last cup away, and the village child walked home "
        f"brave enough to sing by {child.pronoun('possessive')} own footsteps."
    )


def tell(place: Place, trouble: Trouble, remedy: Remedy,
         child_name: str = "Mara", child_gender: str = "girl",
         helper_name: str = "Grandmother", helper_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child", traits=["small"], shy=True))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender,
                              role="helper", traits=["kind", "steady"]))
    tub = world.add(Entity(id="tub", type="thing", label="the old tub", wettable=True))
    trouble_ent = world.add(Entity(id="trouble", type="thing", label=trouble.label,
                                   wettable=True, muddy=(trouble.kind == "mud"),
                                   sootable=(trouble.kind == "soot")))
    world.add(Entity(id="home", type="home", label="the cottage"))
    child.memes["bravery"] = 1.0
    child.memes["worry"] = 1.0

    setup(world, child, helper, place, trouble)
    world.para()
    worry(world, helper, child, trouble)
    world.para()
    brave_rhyme(world, child, trouble, remedy)
    wash(world, trouble_ent, remedy)
    soothe(world, helper, child, trouble, remedy)
    world.para()
    ending(world, child, helper, place, trouble)

    world.facts.update(
        child=child, helper=helper, tub=tub, trouble=trouble, remedy=remedy,
        place=place, outcome="washed", brave=child.memes["bravery"] >= 2.0
    )
    return world


PLACES = {
    "hearth": Place("hearth", "the hearth room", "A wide old tub stood by the stone wall.", "The fire was low and the room was dim.", {"tub"}),
    "yard": Place("yard", "the yard", "A round tub waited beneath the apple tree.", "The leaves whispered over the path.", {"tub"}),
    "riverbank": Place("riverbank", "the riverbank", "A tub had been set on the grass beside the water.", "The reeds bent and listened.", {"tub"}),
}

TROUBLES = {
    "mud": Trouble("mud", "muddy boots", "a pair of muddy boots", "mud", "mud will drip on the floor", "they had been racing through the lane", {"mud"}),
    "soot": Trouble("soot", "sooty mittens", "a pair of sooty mittens", "soot", "soot will smear the table", "they had been near the chimney", {"soot"}),
}

REMEDIES = {
    "song": Remedy("song", "sweet soap", "a little cake of sweet soap", "Tubs and suds, shine and bloom, make the dark bits leave the room!", 3, 3, {"song"}),
    "water": Remedy("water", "warm water", "a kettle of warm water", "Water bright, water kind, wash the worry from the mind!", 2, 2, {"water"}),
    "rhyme": Remedy("rhyme", "soft cloth", "a soft cloth", "Rhyme and cloth, and gentle care, make the clean folk everywhere!", 2, 2, {"rhyme"}),
}

GIRL_NAMES = ["Mara", "Nell", "Tamsin", "Lina", "Pippa", "Wren"]
BOY_NAMES = ["Robin", "Bram", "Owen", "Jory", "Perrin", "Luca"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, p in PLACES.items():
        for tid, t in TROUBLES.items():
            if not is_reasonable(t, p):
                continue
            for rid, r in REMEDIES.items():
                if sensible_remedies() and can_finish(r, t):
                    out.append((place, tid, rid))
    return out


@dataclass
@dataclass
class StoryParams:
    place: str
    trouble: str
    remedy: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


KNOWLEDGE = {
    "tub": [("What is a tub?", "A tub is a large basin that can hold water for washing things. In old stories, a tub is often used for cleaning or bathing.")],
    "mud": [("What is mud?", "Mud is soft, wet dirt. It sticks to things and can be washed away with water and soap.")],
    "soot": [("What is soot?", "Soot is black powder left behind by smoke. It can smear easily, so cloth and hands need washing after touching it.")],
    "song": [("Why do people sing while doing chores?", "Songs can make chores feel lighter and braver. A steady tune helps someone keep going.")],
    "rhyme": [("What is a rhyme?", "A rhyme is a line of words that sound alike at the end. Folk tales often use rhymes to make a moment feel magical and memorable.")],
    "bravery": [("What is bravery?", "Bravery means doing something hard or scary even while your heart is thumping. Brave people can still feel afraid and act anyway.")],
}
KNOWLEDGE_ORDER = ["tub", "mud", "soot", "song", "rhyme", "bravery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style story for a young child that includes the word "tub" and shows bravery with a rhyme.',
        f"Tell a gentle story where {f['child'].id} is nervous about washing {f['trouble'].label} in a tub, then gets brave and sings a rhyme.",
        f"Write a small folk tale with an old tub, a worried child, and a brave rhyme that helps make the washing feel safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c, h, t, r, p = f["child"], f["helper"], f["trouble"], f["remedy"], f["place"]
    qa = [
        ("Who is the story about?",
         f"It is about {c.id} and {h.id}, who came to {p.name} with a washing problem to solve."),
        ("Why was {0} worried?".format(c.id),
         f"{c.id} worried because {t.label} would make a mess if it got handled without care. {c.id} could already imagine the room needing a big scrub."),
        ("What helped {0} become brave?".format(c.id),
         f"A brave little rhyme helped {c.id} steady {c.pronoun('possessive')} heart. The singing gave {c.id} enough courage to lift the trouble toward the tub."),
        ("What changed by the end?",
         f"The trouble got washed clean, the tub held the water safely, and the mood changed from worried to bright. The ending shows that bravery and rhyme can turn a hard chore into a happy one."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["trouble"].tags) | set(world.facts["remedy"].tags) | {"bravery", "tub"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hearth", "mud", "song", "Mara", "girl", "Grandmother", "woman"),
    StoryParams("yard", "soot", "rhyme", "Robin", "boy", "Grandmother", "woman"),
    StoryParams("riverbank", "mud", "water", "Nell", "girl", "Grandmother", "woman"),
]


def explain_rejection(trouble: Trouble, place: Place) -> str:
    if not is_reasonable(trouble, place):
        return "(No story: this place and trouble do not make a good washing problem for a tub tale.)"
    return "(No story: this combination does not produce a clear, gentle folk-tale turn.)"


def outcome_of(params: StoryParams) -> str:
    return "washed" if can_finish(REMEDIES[params.remedy], TROUBLES[params.trouble]) else "stuck"


def explain_remedy(rid: str) -> str:
    r = REMEDIES[rid]
    good = ", ".join(x.id for x in sensible_remedies())
    return f"(Refusing remedy '{rid}': sense={r.sense} is too low; choose one of {good}.)"


ASP_RULES = r"""
reasonable(P, T) :- place(P), trouble(T), tub_place(P), wash_risk(T).
good_remedy(R) :- remedy(R), sense(R, S), S >= 2.
can_finish(R, T) :- good_remedy(R), power(R, P), trouble_need(T, N), P >= N.
valid(P, T, R) :- reasonable(P, T), can_finish(R, T).

outcome(washed) :- chosen_remedy(R), chosen_trouble(T), power(R, P), trouble_need(T, N), P >= N.
outcome(stuck) :- chosen_remedy(R), chosen_trouble(T), power(R, P), trouble_need(T, N), P < N.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if "tub" in p.tags:
            lines.append(asp.fact("tub_place", pid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("trouble_need", tid, 2 if t.kind == "mud" else 3))
        lines.append(asp.fact("wash_risk", tid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_remedy", params.remedy), asp.fact("chosen_trouble", params.trouble)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP gate")
    smoke = generate(CURATED[0])
    if not smoke.story or "tub" not in smoke.story.lower():
        rc = 1
        print("SMOKE TEST FAILED")
    if all(asp_outcome(p) == outcome_of(p) for p in CURATED):
        print("OK: ASP parity and smoke test passed.")
    else:
        rc = 1
        print("MISMATCH in outcome parity.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale tub storyworld with bravery and rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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


def valid_children(gender: str) -> list[str]:
    return GIRL_NAMES if gender == "girl" else BOY_NAMES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trouble and args.place and not is_reasonable(TROUBLES[args.trouble], PLACES[args.place]):
        raise StoryError(explain_rejection(TROUBLES[args.trouble], PLACES[args.place]))
    if args.remedy and REMEDIES[args.remedy].sense < 2:
        raise StoryError(explain_remedy(args.remedy))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.trouble is None or c[1] == args.trouble)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trouble, remedy = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    child = args.child or rng.choice(valid_children(child_gender))
    helper = args.helper or ("Grandmother" if helper_gender == "woman" else "Grandfather")
    if args.helper is None and helper_gender == "woman":
        helper = rng.choice(["Grandmother", "Auntie"])
    if args.helper is None and helper_gender == "man":
        helper = rng.choice(["Grandfather", "Uncle"])
    return StoryParams(place, trouble, remedy, child, child_gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TROUBLES[params.trouble], REMEDIES[params.remedy],
                 params.child, params.child_gender, params.helper, params.helper_gender)
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.trouble} with {p.remedy} ({p.place}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
