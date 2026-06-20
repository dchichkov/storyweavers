#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/likely_happy_ending_humor_pirate_tale.py
=========================================================================

A standalone story world for a small pirate-tale domain with a likely happy
ending and a little humor.

Premise:
- A child pirate crew wants to find treasure.
- They follow a clue that seems likely to point the right way.
- The clue turns out to be funny but imperfect.
- A small mishap happens, but the crew solves it with teamwork.
- The story ends happily with a shared laugh and a bright treasure reveal.

The world model uses physical meters and emotional memes, with forward-chained
rules that drive the prose and QA from simulated state rather than from the
rendered story text.
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
LIKELY_MIN = 1

GIRL_NAMES = ["Mina", "Lila", "Nora", "Pia", "Tess", "Ruby"]
BOY_NAMES = ["Finn", "Milo", "Ezra", "Toby", "Nico", "Owen"]
TRAITS = ["brave", "curious", "cheerful", "silly", "quick", "kind"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
class Theme:
    id: str
    scene: str
    rig: str
    title: str
    goal: str
    dark_spot: str
    send_off: str

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
class Clue:
    id: str
    label: str
    phrase: str
    location: str
    twist: str
    likely: int
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
class Hazard:
    id: str
    label: str
    phrase: str
    near: str
    noisy: bool = False
    slippery: bool = False
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
class Fix:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["slip"] < THRESHOLD:
            continue
        sig = ("slip", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["bump"] += 1
        out.append("__slip__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("joke_done") and not world.facts.get("laughed"):
        world.facts["laughed"] = True
        for c in world.characters():
            c.memes["joy"] += 1
        out.append("They could not help laughing.")
    return out


CAUSAL_RULES = [Rule("slip", "physical", _r_slip), Rule("laugh", "social", _r_laugh)]


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


def likely_story(clue: Clue) -> bool:
    return clue.likely >= LIKELY_MIN


def sensible_fixs() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


SENSE_MIN = 2


def fire_like_humor(hazard: Hazard) -> bool:
    return hazard.noisy or hazard.slippery


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def solveable(fix: Fix, hazard: Hazard) -> bool:
    severity = 2 if hazard.noisy and hazard.slippery else (1 if hazard.noisy or hazard.slippery else 0)
    return fix.power >= severity


def _do_clue(world: World, clue: Clue, narrate: bool = True) -> None:
    world.get("map").meters["torn"] += 0.0
    world.facts["joke_done"] = False
    if clue.id == "banana":
        world.facts["joke_done"] = True
    propagate(world, narrate=narrate)


def setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} turned the deck into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{theme.title}!" {a.id} shouted. "Let us find {theme.goal}!"'
    )


def clue_time(world: World, b: Entity, clue: Clue, theme: Theme) -> None:
    world.say(
        f"But the way to {theme.goal} looked tricky. {theme.dark_spot} hid the next step."
    )
    world.say(
        f'{b.id} pointed at {clue.phrase}. "{clue.label} is likely to help," {b.pronoun()} said.'
    )


def joke(world: World, a: Entity, clue: Clue) -> None:
    world.facts["joke_done"] = clue.id == "banana"
    world.say(
        f'{a.id} grinned. "{clue.twist}"'
    )


def defy(world: World, a: Entity, b: Entity, clue: Clue) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"That sounds too funny to be true," {a.id} said, and still ran after {clue.label}.'
    )


def fall(world: World, hazard: Hazard) -> None:
    target = world.get("deck")
    target.meters["slippery"] += 1
    target.meters["slip"] += 1
    world.facts["hazard_triggered"] = True
    propagate(world, narrate=False)
    world.say(
        f"{hazard.phrase.capitalize()} made the deck feel like a cheeky banana peel, and {hazard.near} became a slipy mess."
    )


def call_out(world: World, b: Entity, a: Entity, hazard: Hazard) -> None:
    world.say(
        f'"{a.id}! Watch out!" {b.id} cried. "The {hazard.label} is making the deck slippery!"'
    )


def rescue(world: World, parent: Entity, fix: Fix, hazard: Hazard) -> None:
    world.get("deck").meters["slip"] = 0.0
    world.get("deck").meters["slippery"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came in with a grin and {fix.text}."
    )
    world.say(
        f"The deck calmed down, and the silly hazard stopped causing trouble."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, clue: Clue) -> None:
    for c in (a, b):
        c.memes["relief"] += 1
        c.memes["love"] += 1
    world.say("For a moment, everyone just blinked.")
    world.say(
        f"Then {parent.label_word.capitalize()} laughed and said, "
        f'"If something seems likely and also looks like a joke, we check it carefully."'
    )
    world.say(
        f'"We promise," whispered {a.id} and {b.id}.'
    )


def ending(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme) -> None:
    for c in (a, b):
        c.memes["joy"] += 1
    world.say(
        f"The next morning, {parent.label_word.capitalize()} brought a real lantern and a clean map."
    )
    world.say(
        f"{a.id} held the lantern, {b.id} held the map, and together they {theme.send_off}."
    )
    world.say(
        "This time the treasure was exactly where it should have been: safe, shiny, and worth the laugh."
    )


def tell(theme: Theme, clue: Clue, hazard: Hazard, fix: Fix,
         instigator: str = "Mina", instigator_gender: str = "girl",
         mate: str = "Finn", mate_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    a = world.add(Entity(id=instigator, kind="character", type=instigator_gender, role="instigator"))
    b = world.add(Entity(id=mate, kind="character", type=mate_gender, role="cautioner"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the captain-parent"))
    world.add(Entity(id="deck", type="place", label="the deck"))
    world.add(Entity(id="map", type="thing", label="the map"))
    setup(world, a, b, theme)
    world.para()
    clue_time(world, b, clue, theme)
    joke(world, a, clue)
    defy(world, a, b, clue)
    world.para()
    if fire_like_humor(hazard):
        fall(world, hazard)
        call_out(world, b, a, hazard)
        if solveable(fix, hazard):
            world.para()
            rescue(world, parent, fix, hazard)
            lesson(world, parent, a, b, clue)
            world.para()
            ending(world, parent, a, b, theme)
            outcome = "happy"
        else:
            world.say("The trouble got too big, but this world will not use that ending.")
            outcome = "happy"
    else:
        world.say("The clue led cleanly to the next step, which was a little too easy for a pirate tale.")
        ending(world, parent, a, b, theme)
        outcome = "happy"
    world.facts.update(instigator=a, cautioner=b, parent=parent, theme=theme, clue=clue, hazard=hazard, fix=fix, outcome=outcome)
    return world


THEMES = {
    "cove": Theme("cove", "a lively little cove", "The sails flapped like laundry, a rope swing bounced by the mast, and a crab marched across a spoon.", "Captain", "the hidden chest", "the next clue", "sailed off toward the chest"),
    "island": Theme("island", "a tiny island beach", "The sand was the color of toast, a bucket held shells, and a gull watched from a post like a very stern judge.", "Captain", "the treasure palm", "the palm tree shade", "walked off toward the palm"),
}

CLUES = {
    "banana": Clue("banana", "banana peel", "a peeled banana lying on the map", "by the chart table", "It looks likely to help, but it is mostly a snack in disguise.", 2, tags={"banana", "humor"}),
    "shell": Clue("shell", "shell clue", "a shiny shell with an arrow scratched on it", "near the bucket", "It points the way and also shines like it knows a secret.", 3, tags={"shell"}),
    "parrot": Clue("parrot", "parrot clue", "a parrot pretending to be a signpost", "on the rail", "The bird is trying very hard to be official.", 2, tags={"parrot", "humor"}),
}

HAZARDS = {
    "rope": Hazard("rope", "rope pile", "the rope pile", "the mast", noisy=True, tags={"rope"}),
    "peel": Hazard("peel", "banana peel", "the banana peel", "the deck", slippery=True, tags={"banana", "slippery"}),
    "crab": Hazard("crab", "crabby bucket", "the crabby bucket", "the deck", noisy=True, slippery=True, tags={"crab", "humor"}),
}

FIXES = {
    "mop": Fix("mop", "mop", 3, 2, "wiped the deck dry with a mop and a proud little flourish", "tried to mop it, but the mess kept skating away", "wiped the deck dry with a mop"),
    "cloth": Fix("cloth", "dry cloth", 2, 1, "pressed a dry cloth over the slippery spot until it stopped being silly", "pressed a cloth on it, but the spot was too slippery to calm down", "pressed a dry cloth over the slippery spot"),
    "sand": Fix("sand", "sand bucket", 2, 2, "sprinkled sand over the slick patch and swept it away", "threw sand on it, but the deck was too wild to settle", "sprinkled sand over the slick patch"),
}


@dataclass
class StoryParams:
    theme: str
    clue: str
    hazard: str
    fix: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
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

CURATED = [
    ("cove", "banana", "peel"),
    ("cove", "shell", "rope"),
    ("island", "parrot", "crab"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in THEMES:
        for c in CLUES:
            for h in HAZARDS:
                if likely_story(CLUES[c]) and fire_like_humor(HAZARDS[h]):
                    combos.append((t, c, h))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale storyworld with humor and a likely happy ending.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--fix", choices=FIXES)
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
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.clue is None or c[1] == args.clue)
              and (args.hazard is None or c[2] == args.hazard)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, clue, hazard = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    inst_name = rng.choice(GIRL_NAMES + BOY_NAMES)
    mate_name = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != inst_name])
    ig = "girl" if inst_name in GIRL_NAMES else "boy"
    mg = "girl" if mate_name in GIRL_NAMES else "boy"
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(theme, clue, hazard, fix, inst_name, ig, mate_name, mg, parent, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a 3-to-5-year-old that includes the word "likely" and ends happily.',
        f"Tell a humorous pirate story where {f['instigator'].id} follows a clue that seems likely to help, but the crew finds a funny problem and fixes it together.",
        f'Write a small pirate adventure with a joke, a little mess, and a cheerful ending using the word "likely".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, parent = f["instigator"], f["cautioner"], f["parent"]
    clue, hazard, fix, theme = f["clue"], f["hazard"], f["fix"], f["theme"]
    items = [
        QAItem("Who is the story about?", f"It is about {a.id}, {b.id}, and {parent.label_word} on a pirate-style adventure. They are searching around {theme.scene}."),
        QAItem("What did the crew think was likely to help?", f"They thought {clue.label} was likely to help. It pointed toward the next step, although it also turned out to be funny."),
        QAItem(f"What problem happened with the {hazard.label}?", f"The {hazard.label} made the deck slippery or noisy, so the children had to stop and pay attention. That is why the story needed a quick fix."),
        QAItem("How was the problem solved?", f"They used {fix.label} and calmed the deck back down. The fix worked, so the adventure could keep going safely."),
        QAItem("How did the story end?", f"It ended happily: everyone laughed, the treasure was found, and the deck was safe again. The crew got to finish the adventure together."),
    ]
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["clue"].tags) | set(f["hazard"].tags) | set(f["fix"].tags)
    out: list[QAItem] = []
    if "banana" in tags:
        out.append(QAItem("Why can a banana peel be funny in a story?", "A banana peel can be funny because it often makes characters slip in a silly way. In a pirate tale, that kind of slip can turn into a joke instead of a disaster."))
    if "slippery" in tags:
        out.append(QAItem("What does slippery mean?", "Slippery means something is hard to stand on or hold because feet or hands can slide. People move carefully when the floor is slippery."))
    if "rope" in tags:
        out.append(QAItem("What is rope used for on a ship?", "Rope helps tie things, lift things, and hold sails steady on a ship. Pirates often use rope for many jobs on deck."))
    if "parrot" in tags:
        out.append(QAItem("Why do pirates and parrots go together in stories?", "Parrots are often used in pirate stories because they are colorful, loud, and a little silly. They make the pirate world feel playful."))
    if "shell" in tags:
        out.append(QAItem("What is a shell?", "A shell is a hard outside covering from a sea creature. People often find shells on beaches."))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
likely_story(C) :- clue(C), likely(C, N), likely_min(M), N >= M.
hazardous(H) :- hazard(H), noisy(H).
hazardous(H) :- hazard(H), slippery(H).
compatible(F, H) :- fix(F), hazard(H), power(F, P), severity(H, S), P >= S.
valid(T, C, H) :- theme(T), clue(C), hazard(H), likely_story(C), hazardous(H), compatible(_, H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("likely", cid, c.likely))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.noisy:
            lines.append(asp.fact("noisy", hid))
        if h.slippery:
            lines.append(asp.fact("slippery", hid))
        sev = 2 if h.noisy and h.slippery else (1 if h.noisy or h.slippery else 0)
        lines.append(asp.fact("severity", hid, sev))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("likely_min", LIKELY_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a != b:
        print("MISMATCH in valid combos")
        return 1
    print(f"OK: valid combos match ({len(a)}).")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], CLUES[params.clue], HAZARDS[params.hazard], FIXES[params.fix],
                 params.instigator, params.instigator_gender, params.cautioner, params.cautioner_gender, params.parent)
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
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for t, c, h in combos:
            print(f"  {t:8} {c:8} {h:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(t, c, h, "mop", "Mina", "girl", "Finn", "boy", "mother", "silly")) for t, c, h in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
