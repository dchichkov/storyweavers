#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bask_rude_magic_lesson_learned_pirate_tale.py
===============================================================================

A small, self-contained storyworld for a pirate-style lesson tale: a child pirate
tries rude magic for a thrill, the magic backfires in a small way, and a gentle
grown-up lesson turns the moment into a brighter, kinder ending.

The seed words are woven into the world model and prose:
- bask
- rude

Features:
- Magic
- Lesson Learned

Style:
- Pirate Tale
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
MAGIC_THRESHOLD = 1.0


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
    sparkly: bool = False
    polite: bool = True

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "pirate", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class CrewKind:
    id: str
    scene: str
    ship: str
    goal: str
    dark_place: str
    sendoff: str
    title_lead: str
    title_helper: str
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


@dataclass
class Trick:
    id: str
    label: str
    effect: str
    hazard: str
    requires_magic: bool = True
    rude: bool = False
    loud: bool = False
    power: int = 0
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
class Reply:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    lesson: str
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
class Setting:
    id: str
    place: str
    clues: str
    light_need: str
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


def _r_magic_backfire(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("kid")
    trick = world.facts.get("trick")
    if trick is None:
        return out
    if kid.meters["spell"] < MAGIC_THRESHOLD:
        return out
    sig = ("backfire", trick.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["surprise"] += 1
    kid.meters["sparkles"] += 1
    out.append("__magic__")
    return out


CAUSAL_RULES = [Rule("magic_backfire", _r_magic_backfire)]


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


def sensible_replies() -> list[Reply]:
    return [r for r in REPLIES.values() if r.sense >= 2]


def valid_combo(crew: CrewKind, setting: Setting, trick: Trick) -> bool:
    return crew.id == "pirates" and trick.requires_magic and trick.rude and setting.id in {"deck", "harbor", "cove"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for crew_id, crew in CREWS.items():
        for setting_id, setting in SETTINGS.items():
            for trick_id, trick in TRICKS.items():
                if valid_combo(crew, setting, trick):
                    combos.append((crew_id, setting_id, trick_id))
    return combos


def predict(world: World, trick: Trick) -> dict:
    sim = world.copy()
    simulate_magic(sim, trick, narrate=False)
    return {
        "sparkles": sim.get("kid").meters["sparkles"],
        "hurt_feelings": sim.get("kid").memes["hurt"],
    }


def simulate_magic(world: World, trick: Trick, narrate: bool = True) -> None:
    kid = world.get("kid")
    sea = world.get("sea")
    kid.meters["spell"] += 1
    kid.meters["sparkles"] += 1
    sea.meters["glow"] += 1
    if trick.rude:
        kid.memes["rudeness"] += 1
        kid.memes["hurt"] += 1
    propagate(world, narrate=narrate)


def setup_scene(world: World, crew: CrewKind, setting: Setting, hero: Entity, mate: Entity) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On the {setting.place}, {hero.id} and {mate.id} turned the day into "
        f"a pirate game. The {crew.ship} rocked gently, and {setting.clues}."
    )
    world.say(
        f"{hero.id} wanted to bask in the spray and light a little magic. "
        f"{mate.id} kept watch near the rail."
    )


def tempt(hero: Entity, trick: Trick) -> None:
    hero.memes["bravado"] += 1


def warning(world: World, mate: Entity, hero: Entity, trick: Trick, setting: Setting) -> bool:
    pred = predict(world, trick)
    if pred["sparkles"] < 1:
        return False
    world.facts["predicted_sparkles"] = pred["sparkles"]
    world.say(
        f'{mate.id} frowned. "That idea is rude, {hero.id}. Magic near the '
        f'{setting.light_need} can spill trouble onto the deck."'
    )
    return True


def rude_choice(world: World, hero: Entity, trick: Trick, setting: Setting) -> None:
    world.say(
        f'{hero.id} grinned and said a rude little spell. The words went up like '
        f'sea-salt in the wind, and the {setting.light_need} trembled.'
    )
    simulate_magic(world, trick)


def apology(world: World, hero: Entity, mate: Entity, captain: Entity) -> None:
    hero.memes["guilt"] += 1
    hero.memes["lesson"] += 1
    mate.memes["relief"] += 1
    world.say(
        f"{captain.label_word.capitalize()} came over at once. {captain.pronoun().capitalize()} "
        f"was not harsh; {captain.pronoun()} only knelt and said, "
        f'"Magic is for helping, not for being rude. A kind word can be stronger than a spell."'
    )
    world.say(
        f"{hero.id} lowered {hero.pronoun('possessive')} head and apologized to {mate.id}."
    )
    world.say(
        f'"I was rude," {hero.id} said. "I will do better."'
    )


def better_magic(world: World, hero: Entity, mate: Entity, trick: Trick, setting: Setting) -> None:
    hero.memes["joy"] += 1
    hero.memes["lesson"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"The next moment, {hero.id} tried again, but this time the magic was gentle. "
        f"It made a tiny lantern-glow under {setting.place}, bright enough for both of them to see."
    )
    world.say(
        f"{hero.id} and {mate.id} laughed, and the {setting.place} shone with safe sparkles "
        f"while they basked in the warm light."
    )
    world.say(
        f"From then on, {hero.id} used magic to share, not to shove."
    )


def tell(crew: CrewKind, setting: Setting, trick: Trick, reply: Reply,
         kid_name: str = "Milo", mate_name: str = "Nia", captain_name: str = "Captain Moss") -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type="boy", role="hero"))
    mate = world.add(Entity(id=mate_name, kind="character", type="girl", role="helper"))
    captain = world.add(Entity(id=captain_name, kind="character", type="pirate", role="captain", label="the captain"))
    sea = world.add(Entity(id="sea", kind="thing", type="thing", label="the sea"))
    world.add(Entity(id="deck", kind="thing", type="thing", label="the deck"))
    world.facts["trick"] = trick
    world.facts["setting"] = setting
    world.facts["crew"] = crew

    setup_scene(world, crew, setting, kid, mate)
    world.para()
    tempt(kid, trick)
    warning(world, mate, kid, trick, setting)
    rude_choice(world, kid, trick, setting)
    world.para()
    apology(world, kid, mate, captain)
    world.para()
    better_magic(world, kid, mate, trick, setting)
    world.facts.update(
        kid=kid, mate=mate, captain=captain, sea=sea, reply=reply,
        outcome="learned"
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    trick = f["trick"]
    return [
        f'Write a pirate tale for a small child that includes the words "{trick.label}" and "bask".',
        f"Tell a story where a little pirate tries a rude magic trick on the {setting.place} and learns a kinder way.",
        f"Write a gentle lesson story with magic, a captain, and a bright ending on the {setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = f["kid"]
    mate = f["mate"]
    captain = f["captain"]
    setting = f["setting"]
    trick = f["trick"]
    return [
        QAItem(
            question="What did the child want to do at first?",
            answer=f"{kid.id} wanted to bask in the sea air and use {trick.label} magic to feel powerful. It looked exciting at first, but the spell was rude and made the moment turn sour."
        ),
        QAItem(
            question="Why did the other child worry?",
            answer=f"{mate.id} worried because rude magic can spread trouble, and the {setting.light_need} near the water could be disturbed. The warning was about safety and about being kind, because the spell was not meant to help."
        ),
        QAItem(
            question="How did the story teach its lesson?",
            answer=f"The captain stopped the trouble with calm words and reminded the crew that magic should help, not hurt feelings. After that, {kid.id} apologized and used gentle magic instead, so the ending showed the lesson clearly."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bask?",
            answer="To bask means to enjoy warm light or a pleasant feeling for a while. In a pirate story, it can mean soaking up the sun or the glow of a lantern."
        ),
        QAItem(
            question="What should a pirate do after being rude?",
            answer="A pirate should apologize, listen, and try again with kinder words. Good crews stay stronger when they speak gently to one another."
        ),
        QAItem(
            question="What does magic do in this world?",
            answer="Magic can make small lights, sparkles, and helpful changes. It works best when it is used kindly, because rude magic causes trouble and leaves a lesson behind."
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CREWS = {
    "pirates": CrewKind(
        id="pirates",
        scene="a bright little pirate adventure",
        ship="ship",
        goal="find the treasure glow",
        dark_place="the lower deck",
        sendoff="sailed on",
        title_lead="Captain",
        title_helper="Mate",
    )
}

SETTINGS = {
    "deck": Setting(
        id="deck",
        place="deck",
        clues="the ropes creaked and gulls called overhead",
        light_need="lantern",
        tags={"sea", "pirate"},
    ),
    "harbor": Setting(
        id="harbor",
        place="harbor",
        clues="the boats bobbed and the water flashed silver",
        light_need="lantern",
        tags={"sea", "pirate"},
    ),
    "cove": Setting(
        id="cove",
        place="cove",
        clues="the cave mouth yawned dark beside the waves",
        light_need="lantern",
        tags={"sea", "pirate"},
    ),
}

TRICKS = {
    "spark": Trick(
        id="spark",
        label="spark spell",
        effect="a burst of tiny light",
        hazard="it can startle friends and singe cloth",
        requires_magic=True,
        rude=True,
        loud=False,
        power=1,
        tags={"magic", "rude"},
    ),
    "snicker": Trick(
        id="snicker",
        label="snicker spell",
        effect="a twitchy trickle of glitter",
        hazard="it makes a mean little mess of feelings",
        requires_magic=True,
        rude=True,
        loud=True,
        power=1,
        tags={"magic", "rude"},
    ),
}

REPLIES = {
    "kind_words": Reply(
        id="kind_words",
        sense=3,
        power=3,
        text="softly gathered the spell into a warm lantern-glow and tucked the sparks away",
        fail="tried to hush the spell, but the magic was already too prickly to calm",
        lesson="used kind words to calm the magic",
        tags={"magic", "lesson"},
    )
}

GIRL_NAMES = ["Nia", "Mara", "Tess", "Luna", "Ari"]
BOY_NAMES = ["Milo", "Finn", "Jace", "Oren", "Pip"]


@dataclass
class StoryParams:
    crew: str
    setting: str
    trick: str
    reply: str
    kid_name: str
    mate_name: str
    captain_name: str
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


CURATED = [
    StoryParams(
        crew="pirates",
        setting="deck",
        trick="spark",
        reply="kind_words",
        kid_name="Milo",
        mate_name="Nia",
        captain_name="Captain Moss",
    ),
    StoryParams(
        crew="pirates",
        setting="cove",
        trick="snicker",
        reply="kind_words",
        kid_name="Pip",
        mate_name="Luna",
        captain_name="Captain Salt",
    ),
]


def valid_params(params: StoryParams) -> bool:
    try:
        return valid_combo(CREWS[params.crew], SETTINGS[params.setting], TRICKS[params.trick])
    except KeyError:
        return False


def explain_rejection(setting: Setting, trick: Trick) -> str:
    return (
        f"(No story: this pirate scene needs a rude magic trick that can actually "
        f"turn the moment. Try one of: {', '.join(sorted(TRICKS))} in a pirate setting.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate tale storyworld with rude magic and a lesson learned."
    )
    ap.add_argument("--crew", choices=CREWS)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--reply", choices=REPLIES)
    ap.add_argument("--name")
    ap.add_argument("--mate")
    ap.add_argument("--captain")
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
    crew = args.crew or "pirates"
    setting = args.setting or rng.choice(list(SETTINGS))
    trick = args.trick or rng.choice(list(TRICKS))
    reply = args.reply or rng.choice(list(REPLIES))
    if not valid_combo(CREWS[crew], SETTINGS[setting], TRICKS[trick]):
        raise StoryError(explain_rejection(SETTINGS[setting], TRICKS[trick]))
    kid_name = args.name or rng.choice(BOY_NAMES)
    mate_name = args.mate or rng.choice(GIRL_NAMES)
    captain_name = args.captain or rng.choice(["Captain Moss", "Captain Salt", "Captain Pearl"])
    return StoryParams(
        crew=crew,
        setting=setting,
        trick=trick,
        reply=reply,
        kid_name=kid_name,
        mate_name=mate_name,
        captain_name=captain_name,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_params(params):
        raise StoryError("(Invalid parameters for this pirate tale.)")
    world = tell(
        CREWS[params.crew],
        SETTINGS[params.setting],
        TRICKS[params.trick],
        REPLIES[params.reply],
        kid_name=params.kid_name,
        mate_name=params.mate_name,
        captain_name=params.captain_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_qa(world)],
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
valid_combo(Crew,Setting,Trick) :- crew(Crew), setting(Setting), trick(Trick), pirate(Crew), magic_trick(Trick), rude_trick(Trick), pirate_setting(Setting).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid in CREWS:
        lines.append(asp.fact("crew", cid))
        lines.append(asp.fact("pirate", cid))
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("pirate_setting", sid))
    for tid, t in TRICKS.items():
        lines.append(asp.fact("trick", tid))
        if t.requires_magic:
            lines.append(asp.fact("magic_trick", tid))
        if t.rude:
            lines.append(asp.fact("rude_trick", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    else:
        print("OK: verification smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
