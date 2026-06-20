#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rumpus_magic_pirate_tale.py
===========================================================

A standalone story world for a tiny pirate tale with a magical rumpus.

Premise:
- Two child pirates are playing on a small ship during a rumpus.
- One child wants to use a bit of magic for fun.
- The magic causes a lively mess: treasure rattles, lantern glow changes, and the deck becomes chaotic.
- A calm grown-up helps them redirect the magic into a useful, safe trick.
- The ending proves the rumpus changed from wild chaos into a fun, controlled show.

The script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven prose
- separate prompts, story QA, and world QA
- Python reasonableness gate plus inline ASP twin
- --verify smoke-tests generation and checks ASP parity
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
MAGIC_MIN = 2
RUMPUS_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    sparkly: bool = False
    magical: bool = False
    sturdy: bool = False
    helpful: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "pirate_girl"}
        male = {"boy", "father", "dad", "man", "king", "pirate_boy"}
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
class Setting:
    id: str
    place: str
    ship_name: str
    scene: str
    dark_spot: str
    crew_title: str
    crew_plural: str
    safe_finish: str

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
class Magic:
    id: str
    source: str
    effect: str
    shimmer: str
    lesson: str
    dangerous: bool = True
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
class Rumpus:
    id: str
    name: str
    noise: str
    turn: str
    ending: str
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
class Remedy:
    id: str
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


def _r_rumpus(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters["rumpus"] < THRESHOLD:
            continue
        sig = ("rumpus", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ent in list(world.entities.values()):
            if ent.kind == "thing" and ent.attrs.get("on_deck"):
                ent.meters["bumped"] += 1
        world.get("deck").meters["chaos"] += 1
        out.append("__rumpus__")
    return out


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters["magic"] < THRESHOLD:
            continue
        sig = ("magic", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("lantern").meters["glow"] += 1
        world.get("treasure").meters["rattled"] += 1
        hero.memes["delight"] += 1
        out.append("__magic__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.get("deck").meters["chaos"] < THRESHOLD:
        return out
    sig = ("worry", "deck")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for hero in world.characters():
        hero.memes["worry"] += 1
    out.append("__worry__")
    return out


CAUSAL_RULES = [
    Rule("rumpus", "physical", _r_rumpus),
    Rule("magic", "physical", _r_magic),
    Rule("worry", "social", _r_worry),
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


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= MAGIC_MIN]


def valid_combo(setting: Setting, rumpus: Rumpus, magic: Magic, remedy: Remedy) -> bool:
    return True if magic.dangerous and remedy.sense >= MAGIC_MIN else False


def remedy_matches(remedy: Remedy, severity: int) -> bool:
    return remedy.power >= severity


def severity(deck: Setting, delay: int) -> int:
    return 1 + delay


def predict_rumpus(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").meters["rumpus"] += 1
    sim.get("hero").meters["magic"] += 1
    propagate(sim, narrate=False)
    return {
        "chaos": sim.get("deck").meters["chaos"],
        "worry": sum(e.memes["worry"] for e in sim.characters()),
    }


def introduce(world: World, hero: Entity, mate: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {mate.id} made a rumpus on the deck "
        f"of the {setting.ship_name}. {setting.scene}"
    )
    world.say(
        f"They were playing pirates, with {setting.crew_title} {hero.id} leading "
        f"the game and {mate.id} keeping watch for hidden treasure."
    )


def need_magic(world: World, mate: Entity, setting: Setting, magic: Magic) -> None:
    world.say(
        f"But the {setting.dark_spot} was dim, and the children wanted a little "
        f"magic to light it up."
    )
    world.say(f'"We need {magic.source}," {mate.id} said, peering into the shadows.')


def tempt(world: World, hero: Entity, magic: Magic) -> None:
    hero.meters["magic"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f'{hero.id} grinned wide. "I know! {magic.source} will make this '
        f'adventure sparkle," {hero.pronoun()} said.'
    )
    world.say(f"The idea sounded thrilling, and the rumpus grew louder.")


def warn(world: World, mate: Entity, hero: Entity, magic: Magic, setting: Setting) -> None:
    pred = predict_rumpus(world)
    mate.memes["care"] += 1
    world.facts["predicted_chaos"] = pred["chaos"]
    world.say(
        f'{mate.id} frowned a little. "{magic.lesson} If we use it near the '
        f'{setting.place}, it could turn our rumpus wild."'
    )


def do_magic(world: World, hero: Entity, magic: Magic, setting: Setting) -> None:
    hero.meters["rumpus"] += 1
    hero.meters["magic"] += 1
    hero.memes["bravery"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{magic.source} flashed in {hero.id}'s hands. For a blink it was lovely, "
        f"a tiny shining trick {magic.shimmer}."
    )
    world.say(
        f"Then the glow bounced off the boards, the treasure box trembled, and the "
        f"whole deck bounced into a proper rumpus."
    )


def alarm(world: World, mate: Entity, hero: Entity, magic: Magic, setting: Setting) -> None:
    world.say(
        f'"{hero.id}! The {setting.ship_name} is getting too wild!" {mate.id} cried. '
        f'"Call for {setting.crew_title}!"'
    )


def calm_fix(world: World, parent: Entity, remedy: Remedy, magic: Magic, setting: Setting) -> None:
    world.get("deck").meters["chaos"] = 0.0
    world.get("lantern").meters["glow"] = 1.0
    body = remedy.text.replace("{magic}", magic.source)
    world.say(
        f"{parent.label_word.capitalize()} came running and {body}."
    )
    world.say(
        f"The lantern steadied, the treasure stopped rattling, and the rumpus "
        f"slipped back into a safe kind of fun."
    )


def lesson(world: World, parent: Entity, hero: Entity, mate: Entity, magic: Magic) -> None:
    for kid in (hero, mate):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    world.say("For a moment, everyone listened to the waves and nobody talked.")
    world.say(
        f"Then {parent.label_word.capitalize()} smiled and said, "
        f'"Magic is for helping, not for making trouble. We can still have fun, '
        f'but we must use it carefully."'
    )
    world.say(
        f'{hero.id} and {mate.id} nodded. "{magic.lesson}," they promised.'
    )


def safe_show(world: World, parent: Entity, hero: Entity, mate: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"The next morning, {parent.label_word.capitalize()} brought out a small "
        f"magic trick for them to practice safely."
    )
    world.say(
        f"The children made the lantern glow soft and gold, and their pirate game "
        f"felt bright again on the {setting.ship_name}."
    )
    world.say(
        f"This time the rumpus was cheerful instead of wild, and the ship sailed "
        f"on under a steady magical light."
    )


def tell(setting: Setting, magic: Magic, rumpus: Rumpus, remedy: Remedy,
         hero_name: str = "Mina", hero_type: str = "girl",
         mate_name: str = "Jory", mate_type: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_type, role="mate"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the captain"))
    deck = world.add(Entity(id="deck", type="thing", label="the deck", attrs={"on_deck": True}))
    world.add(Entity(id="lantern", type="thing", label="lantern", magical=True, sparkly=True, attrs={"on_deck": True}))
    world.add(Entity(id="treasure", type="thing", label="treasure chest", sturdy=True, attrs={"on_deck": True}))

    world.facts["setting"] = setting
    world.facts["magic"] = magic
    world.facts["rumpus"] = rumpus
    world.facts["remedy"] = remedy
    world.facts["delay"] = delay

    hero.meters["rumpus"] = 1
    mate.meters["rumpus"] = 1
    hero.memes["joy"] = 1
    mate.memes["joy"] = 1

    introduce(world, hero, mate, setting)
    need_magic(world, mate, setting, magic)
    world.para()
    tempt(world, hero, magic)
    warn(world, mate, hero, magic, setting)
    world.para()
    do_magic(world, hero, magic, setting)
    alarm(world, mate, hero, magic, setting)
    world.para()
    sev = severity(setting, delay)
    if remedy_matches(remedy, sev):
        calm_fix(world, parent, remedy, magic, setting)
        lesson(world, parent, hero, mate, magic)
        world.para()
        safe_show(world, parent, hero, mate, setting)
        outcome = "contained"
    else:
        world.say(
            f"{parent.label_word.capitalize()} tried to use {remedy.qa_text}, "
            f"but the wild magic was already too strong."
        )
        world.say(
            "So they hurried to the rail, watched the sparkly confusion settle, "
            "and promised to call for help sooner next time."
        )
        outcome = "wild"
    world.facts["outcome"] = outcome
    return world


SETTINGS = {
    "harbor": Setting("harbor", "at the harbor", "Little Gull", "The harbor breeze smelled salty, and gulls circled above the mast.", "the dim hold", "captain", "crew", "sail bright and safe"),
    "cove": Setting("cove", "in the moon cove", "Blue Comet", "The ship rocked gently beside the rocks, and moonlight slid across the rails.", "the cave-like cove below deck", "captain", "crew", "sail bright and safe"),
    "island": Setting("island", "by the island shore", "Starfish Rose", "Palm leaves hissed in the wind, and the little ship creaked like a friendly door.", "the shadowy cabin", "captain", "crew", "sail bright and safe"),
}

MAGICS = {
    "glimmer": Magic("glimmer", "a glimmer spell", "make a soft glow", "like moonlight on water", "Magic should be used with care"),
    "spark": Magic("spark", "a spark charm", "wake up tiny lights", "like fireflies in a jar", "Tiny sparks can become a big problem"),
    "mirror": Magic("mirror", "a mirror spell", "show bright reflections", "like silver coins dancing", "Magic can be beautiful, but it still needs rules"),
}

RUMPUSSES = {
    "deck_rumpus": Rumpus("deck_rumpus", "deck rumpus", "feet thumping and boards creaking", "made the whole deck shake", "turned the rumpus into a tidy show"),
    "treasure_rumpus": Rumpus("treasure_rumpus", "treasure rumpus", "coins jingling and boxes clacking", "made the treasure jump around", "settled the treasure into place"),
}

REMEDIES = {
    "lantern_spell": Remedy("lantern_spell", 2, 2, "used the old lantern trick and guided the {magic} into a soft shine", "tried the old lantern trick, but the {magic} was too wild", "calmed the magic into a soft lantern shine"),
    "song": Remedy("song", 3, 3, "started a slow sea-song and let the {magic} follow the rhythm", "started a sea-song, but the {magic} would not slow down", "used a sea-song to steady the magic"),
    "rope_circle": Remedy("rope_circle", 2, 1, "made a rope circle and told everyone to keep the magic inside it", "made a rope circle, but the {magic} slipped right out", "made a safe rope circle for the magic"),
}

GIRL_NAMES = ["Mina", "Nia", "Lola", "Tess", "Aria", "Ruby"]
BOY_NAMES = ["Jory", "Kai", "Pip", "Ned", "Owen", "Finn"]
TRAITS = ["brave", "curious", "cheerful", "bold", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, m, r, d) for s in SETTINGS for m in MAGICS for r in REMEDIES for d in ("contained", "wild")]


@dataclass
@dataclass
class StoryParams:
    setting: str
    magic: str
    rumpus: str
    remedy: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    parent: str
    trait: str
    delay: int = 0
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s, m, r = f["setting"], f["magic"], f["remedy"]
    return [
        f'Write a pirate tale for a 3-to-5-year-old that includes the word "rumpus" and a little magic on a ship.',
        f"Tell a child-friendly pirate story where {f['hero'].id} wants {m.source} during a rumpus, but a grown-up helps make it safe.",
        f"Write a short magical pirate story with a lively rumpus, a worrying mistake, and a calm fix that ends in a bright ship scene.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, parent = f["hero"], f["mate"], f["parent"]
    setting, magic, remedy = f["setting"], f["magic"], f["remedy"]
    qa: list[QAItem] = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {mate.id}, two young pirates on the {setting.ship_name}. {parent.label_word.capitalize()} helps them when the magic gets too wild."
        ),
        QAItem(
            question="Why did the rumpus start?",
            answer=f"The rumpus started because the children wanted {magic.source} to light up the dark spot below deck. That made the game exciting, but it also made the ship feel too lively."
        ),
    ]
    if f["outcome"] == "contained":
        qa.append(
            QAItem(
                question=f"How did {parent.label_word} help?",
                answer=f"{parent.label_word.capitalize()} used {remedy.qa_text}, which calmed the {magic.source} and steadied the ship. That let the children keep playing without making a bigger mess."
            )
        )
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with a safe pirate show on the {setting.ship_name}. The rumpus became cheerful and controlled, and the lantern glowed softly again."
            )
        )
    else:
        qa.append(
            QAItem(
                question="What went wrong?",
                answer=f"The magic and the rumpus became too strong to settle right away. The grown-up tried to help, but the wild spell needed more care than the remedy could give."
            )
        )
        qa.append(
            QAItem(
                question="How did the children feel at the end?",
                answer=f"They felt sorry and a little shaken, but they learned to call for help sooner. The story leaves them safer and wiser for next time."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    magic: Magic = f["magic"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question="What is a rumpus?",
            answer="A rumpus is a noisy, excited fuss. It can be fun, but it can also get messy if nobody slows it down."
        ),
        QAItem(
            question="What is magic in stories?",
            answer="Magic is a pretend power that can make strange and wonderful things happen. In a story world, it still needs careful rules."
        ),
        QAItem(
            question="Why do pirates need to be careful with glowing tricks?",
            answer="Because a glowing trick can draw attention, make a mess, or trick people into thinking something is safe when it is not. Careful pirates use it only when a grown-up says it is okay."
        ),
        QAItem(
            question="What is a ship deck?",
            answer="The deck is the flat top of a ship where people stand, play, and work. It should stay clear enough for safe feet and safe sailing."
        ),
        QAItem(
            question="Why is the dark spot below deck important in the story?",
            answer="Because the children wanted light there, and that made the magic tempting. The dark spot is what gave the story its problem."
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
rumpus(Deck) :- chaos(Deck).
magic_glow(Lantern) :- magical(Lantern).
wild(D) :- delay(D), D >= 1.
contained :- remedy(R), remedy_power(R, P), severity(S), P >= S.
outcome(contained) :- contained.
outcome(wild) :- not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        if m.dangerous:
            lines.append(asp.fact("dangerous", mid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("remedy_power", rid, r.power))
    lines.append(asp.fact("magic_min", MAGIC_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("delay", params.delay),
        asp.fact("severity", 1 + params.delay),
        asp.fact("remedy", params.remedy),
        asp.fact("remedy_power", params.remedy, REMEDIES[params.remedy].power),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    # Smoke test ordinary generation
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH in valid combos:")
        print(" python-only:", sorted(py - cl))
        print(" clingo-only:", sorted(cl - py))
    else:
        print(f"OK: valid combo parity ({len(py)} combos).")
    cases = list(CURATED)
    for s in range(20):
        cases.append(resolve_params(build_parser().parse_args([]), random.Random(s)))
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad:
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")
        rc = 1
    else:
        print(f"OK: outcome parity over {len(cases)} cases.")
    return rc


def outcome_of(params: StoryParams) -> str:
    return "contained" if REMEDIES[params.remedy].power >= 1 + params.delay else "wild"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny magical pirate rumpus storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--rumpus", choices=RUMPUSSES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    magic = args.magic or rng.choice(list(MAGICS))
    rumpus = args.rumpus or rng.choice(list(RUMPUSSES))
    remedy = args.remedy or rng.choice(list(REMEDIES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_pool = [n for n in (GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)]
    mate_pool = [n for n in (GIRL_NAMES if mate_gender == "girl" else BOY_NAMES)]
    hero = args.hero or rng.choice(hero_pool)
    mate = args.mate or rng.choice([n for n in mate_pool if n != hero] or mate_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, magic, rumpus, remedy, hero, hero_gender, mate, mate_gender, parent, trait, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MAGICS[params.magic], RUMPUSSES[params.rumpus], REMEDIES[params.remedy],
                 params.hero, params.hero_gender, params.mate, params.mate_gender, params.parent, params.trait, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} ASP compatible combos.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("harbor", "glimmer", "deck_rumpus", "lantern_spell", "Mina", "girl", "Jory", "boy", "mother", "curious", 0),
            StoryParams("cove", "spark", "treasure_rumpus", "song", "Kai", "boy", "Lola", "girl", "father", "bold", 1),
            StoryParams("island", "mirror", "deck_rumpus", "rope_circle", "Nia", "girl", "Finn", "boy", "mother", "thoughtful", 0),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
