#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/clinician_possession_vow_friendship_magic_superhero_story.py
==========================================================================================

A small standalone storyworld: a child superhero friend, a cherished possession,
a vow to protect a clinic helper, and a little burst of magic that turns worry
into a brave rescue.

Seed words:
- clinician
- possession
- vow

Features:
- Friendship
- Magic

Style:
- Superhero Story

The world is built around a tiny simulated domain where:
- a hero and a friend explore a clinic corridor,
- a magic mishap threatens a valued possession,
- a clinician is endangered or needs help,
- friendship and a vow drive the rescue,
- the ending proves something changed in the world state.

This file is self-contained and uses only stdlib plus the shared Storyweavers
result containers. ASP support is inline and imported lazily.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    helper: bool = False
    magical: bool = False
    valuable: bool = False

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"safe": 0.0, "shimmer": 0.0, "tangled": 0.0, "hurt": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "vow": 0.0, "friendship": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "clinician_female"}
        male = {"boy", "father", "dad", "man", "clinician_male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
class Theme:
    id: str
    scene: str
    hero_title: str
    friend_title: str
    lair: str
    mission: str
    ending: str
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
class MagicEvent:
    id: str
    label: str
    source: str
    effect: str
    risk: str
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
class Possession:
    id: str
    label: str
    phrase: str
    owner_kind: str
    valuable: bool = True
    fragile: bool = True
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
class Rescue:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_unravel(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["tangled"] >= THRESHOLD and ("unravel", e.id) not in world.fired:
            world.fired.add(("unravel", e.id))
            e.meters["safe"] += 1
            out.append("__soften__")
    return out


def _r_brave(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.memes["vow"] >= THRESHOLD and e.role == "hero" and ("brave", e.id) not in world.fired:
            world.fired.add(("brave", e.id))
            e.memes["joy"] += 1
            out.append("__brave__")
    return out


CAUSAL_RULES = [_r_unravel, _r_brave]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(magic: MagicEvent, possession: Possession) -> bool:
    return magic.source == "wand" and possession.fragile


def sensible_rescues() -> list[Rescue]:
    return [r for r in RESCUES.values() if r.sense >= 2]


def is_contained(rescue: Rescue, magic: MagicEvent, delay: int) -> bool:
    return rescue.power >= (2 + delay)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for mid, magic in MAGIC_EVENTS.items():
            for pid, pos in POSSESSIONS.items():
                if hazard_at_risk(magic, pos):
                    combos.append((theme, mid, pid))
    return combos


@dataclass
class StoryParams:
    theme: str
    magic: str
    possession: str
    rescue: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    clinician: str
    clinician_type: str
    delay: int = 0
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


THEMES = {
    "city": Theme(
        id="city",
        scene="a bright city clinic with glass doors and a roof garden",
        hero_title="Captain",
        friend_title="Spark",
        lair="the hallway outside the clinic rooms",
        mission="save the clinic and keep everyone calm",
        ending="the roof garden glowed with safe morning light",
    ),
    "harbor": Theme(
        id="harbor",
        scene="a harbor clinic beside the water",
        hero_title="Captain",
        friend_title="Comet",
        lair="the waiting room with the blue chairs",
        mission="help the healer and guard the treasures inside",
        ending="the harbor flags fluttered safely in the breeze",
    ),
    "museum": Theme(
        id="museum",
        scene="a museum clinic tucked behind the hero exhibit",
        hero_title="Guardian",
        friend_title="Nova",
        lair="the quiet gallery corridor",
        mission="protect the calm place and the people who worked there",
        ending="the statue hall sparkled, peaceful again",
    ),
}

MAGIC_EVENTS = {
    "wand_spark": MagicEvent(
        id="wand_spark",
        label="a sparkling wand",
        source="wand",
        effect="tiny stars",
        risk="the spark could tangle a fragile thing",
        tags={"magic", "spark"},
    ),
    "glimmer_bubble": MagicEvent(
        id="glimmer_bubble",
        label="a glimmer bubble",
        source="bubble",
        effect="soft bubbles",
        risk="the bubble was harmless and gentle",
        tags={"magic"},
    ),
    "moon_charm": MagicEvent(
        id="moon_charm",
        label="a moon charm",
        source="charm",
        effect="silver light",
        risk="the light was bright but careful",
        tags={"magic"},
    ),
}

POSSESSIONS = {
    "badge": Possession(
        id="badge",
        label="hero badge",
        phrase="a shiny hero badge",
        owner_kind="hero",
        fragile=True,
        tags={"possession", "badge"},
    ),
    "sketchbook": Possession(
        id="sketchbook",
        label="sketchbook",
        phrase="a sketchbook full of hero plans",
        owner_kind="friend",
        fragile=True,
        tags={"possession", "book"},
    ),
    "stethoscope": Possession(
        id="stethoscope",
        label="stethoscope case",
        phrase="a soft case for the clinician's stethoscope",
        owner_kind="clinician",
        fragile=True,
        tags={"possession", "clinic"},
    ),
}

RESCUES = {
    "shield": Rescue(
        id="shield",
        sense=3,
        power=4,
        text="raised a glowing shield and gently swept the spark away",
        fail="raised a shield, but the magic crackled too fast to stop",
        qa_text="raised a glowing shield and swept the spark away",
        tags={"shield"},
    ),
    "blanket": Rescue(
        id="blanket",
        sense=3,
        power=3,
        text="threw a thick blanket over the shimmer and pressed it flat",
        fail="threw a blanket over it, but the shimmer wriggled free",
        qa_text="threw a thick blanket over the shimmer and pressed it flat",
        tags={"blanket"},
    ),
    "calm_voice": Rescue(
        id="calm_voice",
        sense=2,
        power=2,
        text="spoke in a calm voice and guided everyone back from the sparkle",
        fail="spoke bravely, but the magic was already too big",
        qa_text="spoke in a calm voice and guided everyone back",
        tags={"voice"},
    ),
    "water_bucket": Rescue(
        id="water_bucket",
        sense=1,
        power=1,
        text="splashed water in a hurry, but it was not enough",
        fail="splashed water in a hurry, but the magic kept going",
        qa_text="splashed water in a hurry",
        tags={"water"},
    ),
}


GIRL_NAMES = ["Luna", "Mira", "Nina", "Iris", "Zoe", "Ava"]
BOY_NAMES = ["Max", "Eli", "Noah", "Leo", "Kai", "Finn"]


def explain_rejection(magic: MagicEvent, possession: Possession) -> str:
    if not hazard_at_risk(magic, possession):
        return "(No story: that magic cannot reasonably threaten that possession.)"
    return ""


def explain_rescue(rid: str) -> str:
    r = RESCUES[rid]
    better = ", ".join(sorted(x.id for x in sensible_rescues()))
    return f"(Refusing rescue '{rid}': sense {r.sense} is too low. Try: {better}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld with friendship, magic, and a clinician.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--magic", choices=MAGIC_EVENTS)
    ap.add_argument("--possession", choices=POSSESSIONS)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--clinician")
    ap.add_argument("--clinician-type", choices=["clinician_female", "clinician_male"])
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
    if args.rescue and args.rescue in RESCUES and RESCUES[args.rescue].sense < 2:
        raise StoryError(explain_rescue(args.rescue))
    if args.magic and args.possession:
        if not hazard_at_risk(MAGIC_EVENTS[args.magic], POSSESSIONS[args.possession]):
            raise StoryError(explain_rejection(MAGIC_EVENTS[args.magic], POSSESSIONS[args.possession]))

    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.magic is None or c[1] == args.magic)
              and (args.possession is None or c[2] == args.possession)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, magic, possession = rng.choice(sorted(combos))
    rescue = args.rescue or rng.choice(sorted(r.id for r in sensible_rescues()))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" else "girl")
    clinician_type = args.clinician_type or rng.choice(["clinician_female", "clinician_male"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    clinician = args.clinician or "Dr. Vale"
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(theme=theme, magic=magic, possession=possession, rescue=rescue,
                       hero=hero, hero_type=hero_type, friend=friend, friend_type=friend_type,
                       clinician=clinician, clinician_type=clinician_type, delay=delay)


def tell(params: StoryParams) -> World:
    world = World()
    theme = THEMES[params.theme]
    magic = MAGIC_EVENTS[params.magic]
    possession = POSSESSIONS[params.possession]
    rescue = RESCUES[params.rescue]

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero"))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_type, role="friend"))
    clinician = world.add(Entity(id=params.clinician, kind="character", type=params.clinician_type, role="clinician",
                                 label="the clinician", helper=True))
    item = world.add(Entity(id="possession", kind="thing", type="thing", label=possession.label, valuable=True, magical=False))
    corridor = world.add(Entity(id="corridor", kind="place", type="place", label=theme.lair))
    hero.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    hero.memes["vow"] = 1.0

    world.say(f"{hero.id} and {friend.id} were superhero friends in {theme.scene}.")
    world.say(f'{hero.id} wore a cape and smiled at {friend.id}. "Today we will {theme.mission}," {hero.id} said.')
    world.say(f"They hurried down {theme.lair}, where {clinician.label_word} was helping people stay calm.")

    world.para()
    world.say(f"Then {hero.id} lifted {magic.label}, and {magic.effect} swirled through the air.")
    if magic.source == "wand":
        item.meters["tangled"] += 1
        world.say(f"The sparks rushed toward {possession.phrase}, and it began to look tangled and unsafe.")
    else:
        world.say(f"The magic shimmered above the hallway like a tiny sky.")

    world.para()
    friend.memes["fear"] += 1
    friend.memes["vow"] += 1
    world.say(f'{friend.id} stepped beside {hero.id}. "I vow we will protect {clinician.label_word} and the {possession.label}," {friend.id} said.')
    world.say(f"{clinician.label_word.capitalize()} pointed to the drifting magic and asked them to help keep everyone safe.")

    contained = True
    if magic.source == "wand":
        contained = is_contained(rescue, magic, params.delay)
        if contained:
            item.meters["safe"] += 1
            world.say(f"{hero.id} then {rescue.text}.")
            world.say(f"The spark faded at once, and {clinician.label_word} could keep working without worry.")
        else:
            item.meters["hurt"] += 1
            world.say(f"{hero.id} tried to help, but {rescue.fail}.")
            world.say(f"The magic rushed past them, and {clinician.label_word} had to back away until the hallway cleared.")
    else:
        world.say(f"{friend.id} laughed, and the safe magic drifted harmlessly into the roof light.")
        item.meters["safe"] += 1

    world.para()
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    if contained:
        hero.memes["joy"] += 1
        friend.memes["joy"] += 1
        world.say(f"{clinician.label_word.capitalize()} thanked them both, and {hero.id} and {friend.id} grinned.")
        world.say(f'That night, {hero.id} and {friend.id} kept their vow and walked home like true heroes.')
        world.say(f"In the morning, {theme.ending}.")
    else:
        hero.memes["fear"] += 1
        world.say(f"Afterward, {hero.id} and {friend.id} made the same vow again, louder this time.")
        world.say(f"They promised to use safer magic next time, and {clinician.label_word} nodded with a gentle smile.")
        world.say(f"By the time they left, {theme.ending}.")

    world.facts.update(
        hero=hero, friend=friend, clinician=clinician, possession=possession,
        magic=magic, rescue=rescue, theme=theme, contained=contained,
        item=item, delay=params.delay
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a small child that includes the words "clinician", "{f["possession"].label}", and "vow".',
        f"Tell a friendship-and-magic superhero story where {f['hero'].id} and {f['friend'].id} protect {f['clinician'].label_word} and keep a vow.",
        f"Write a brave story where a magic spark threatens a possession, but friends save the day and the clinician is safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, clinician = f["hero"], f["friend"], f["clinician"]
    possession, magic, rescue, theme = f["possession"], f["magic"], f["rescue"], f["theme"]
    answers = [
        QAItem(
            question="Who are the main heroes?",
            answer=f"The main heroes are {hero.id} and {friend.id}. They are friendship-minded superhero friends who work together to help {clinician.label_word}.",
        ),
        QAItem(
            question="Why did the friend make a vow?",
            answer=f"{friend.id} made a vow because the magic got close to {possession.phrase} and everyone needed help. The vow showed that friendship was part of the rescue, not just the powers.",
        ),
        QAItem(
            question="How did the story turn out?",
            answer=(
                f"It ended safely because {hero.id} used {rescue.qa_text}."
                if f["contained"]
                else f"It was scary for a moment because {hero.id} could not stop the magic in time, but everyone still stayed safe."
            ),
        ),
        QAItem(
            question="What changed by the end?",
            answer=(
                f"The possession was safe again, the clinician could keep working, and {hero.id} and {friend.id} had kept their vow."
            ),
        ),
    ]
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clinician?",
            answer="A clinician is a person who helps care for people in a clinic or hospital. Clinicians work carefully and kindly so people can feel better.",
        ),
        QAItem(
            question="What is a vow?",
            answer="A vow is a serious promise. People make vows when they want to show they will do something important and not give up.",
        ),
        QAItem(
            question="What is magic in a story like this?",
            answer="Magic is something special that can make unusual things happen, like sparks or glowing light. In stories, magic can be exciting, but it still needs careful handling.",
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
        if e.helper:
            bits.append("helper=True")
        if e.valuable:
            bits.append("valuable=True")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    out = []
    for tid in THEMES:
        out.append(asp.fact("theme", tid))
    for mid, m in MAGIC_EVENTS.items():
        out.append(asp.fact("magic", mid))
        out.append(asp.fact("source", mid, m.source))
    for pid, p in POSSESSIONS.items():
        out.append(asp.fact("possession", pid))
        if p.fragile:
            out.append(asp.fact("fragile", pid))
    for rid, r in RESCUES.items():
        out.append(asp.fact("rescue", rid))
        out.append(asp.fact("sense", rid, r.sense))
        out.append(asp.fact("power", rid, r.power))
    return "\n".join(out)


ASP_RULES = r"""
hazard(M,P) :- magic(M), possession(P), source(M, wand), fragile(P).
sensible(R) :- rescue(R), sense(R,S), S >= 2.
valid(T,M,P) :- theme(T), hazard(M,P).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos().")
    if set(asp_sensible()) != {r.id for r in sensible_rescues()}:
        rc = 1
        print("MISMATCH in sensible rescues.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        print("OK: verify smoke test and parity checks passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES or params.magic not in MAGIC_EVENTS or params.possession not in POSSESSIONS:
        raise StoryError("Invalid params.")
    if params.rescue not in RESCUES:
        raise StoryError("Invalid rescue.")
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


CURATED = [
    StoryParams(theme="city", magic="wand_spark", possession="badge", rescue="shield",
                hero="Luna", hero_type="girl", friend="Max", friend_type="boy",
                clinician="Dr. Vale", clinician_type="clinician_female", delay=0),
    StoryParams(theme="harbor", magic="wand_spark", possession="sketchbook", rescue="blanket",
                hero="Eli", hero_type="boy", friend="Mira", friend_type="girl",
                clinician="Dr. Reed", clinician_type="clinician_male", delay=1),
    StoryParams(theme="museum", magic="moon_charm", possession="stethoscope", rescue="calm_voice",
                hero="Ava", hero_type="girl", friend="Noah", friend_type="boy",
                clinician="Dr. Song", clinician_type="clinician_female", delay=0),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    rescue = args.rescue or rng.choice(sorted(r.id for r in sensible_rescues()))
    if args.rescue and RESCUES[args.rescue].sense < 2:
        raise StoryError(explain_rescue(args.rescue))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.magic is None or c[1] == args.magic)
              and (args.possession is None or c[2] == args.possession)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, magic, possession = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" else "girl")
    clinician_type = args.clinician_type or rng.choice(["clinician_female", "clinician_male"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    clinician = args.clinician or "Dr. Vale"
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(theme=theme, magic=magic, possession=possession, rescue=rescue,
                       hero=hero, hero_type=hero_type, friend=friend, friend_type=friend_type,
                       clinician=clinician, clinician_type=clinician_type, delay=delay)


def build_show_asp() -> str:
    return asp_program("", "#show valid/3.\n#show sensible/1.")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(build_show_asp())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print("sensible rescues:", ", ".join(asp_sensible()))
        print()
        for t, m, p in asp_valid_combos():
            print(t, m, p)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
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
            header = f"### {p.hero} & {p.friend}: {p.magic} / {p.possession} ({p.theme})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
