#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/doodie_busy_street_crossing_magic_myth.py
=========================================================================

A tiny storyworld for a mythic, magical busy-street-crossing tale featuring
"doodie". A child wants to cross a crowded road to reach a shrine-like market
gate, a magical mishap blocks the way, a sensible helper responds, and the
ending proves the street became safe to cross.

The world is deliberately small and classical:
- typed entities with physical meters and emotional memes
- one causal engine that drives plot-relevant state changes
- a Python reasonableness gate with an inline ASP twin
- grounded prompts, story QA, and world-knowledge QA

The prose aims for a mythic tone without losing child-friendliness.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "priestess"}
        male = {"boy", "father", "dad", "man", "king", "priest"}
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


@dataclass
class Crossing:
    id: str
    label: str
    road: str
    landmark: str
    crowd: str
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
class MagicItem:
    id: str
    label: str
    phrase: str
    spell: str
    forbidden: bool = True
    makes_glamour: bool = True
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
class Hazard:
    id: str
    label: str
    near: str
    flammable: bool = False
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
class Response:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


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


def _r_glamour(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["glamour"] < THRESHOLD:
            continue
        sig = ("glamour", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in world.characters():
            ch.memes["wonder"] += 1
        if "road" in world.entities:
            world.get("road").meters["glow"] += 1
        out.append("__glamour__")
    return out


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("road").meters["blocked"] >= THRESHOLD and ("alarm",) not in world.fired:
        world.fired.add(("alarm",))
        for ch in world.characters():
            ch.memes["fear"] += 1
        out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("glamour", "magic", _r_glamour), Rule("alarm", "social", _r_alarm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness_gate(crossing: Crossing, hazard: Hazard, magic: MagicItem, response: Response) -> bool:
    return crossing.id in {"busy_street"} and hazard.flammable is False and magic.makes_glamour and response.sense >= SENSE_MIN


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def predict(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    _do_magic(sim, sim.get(hazard_id), narrate=False)
    return {
        "blocked": sim.get("road").meters["blocked"] >= THRESHOLD,
        "glow": sim.get("road").meters["glow"],
    }


def _do_magic(world: World, hazard: Entity, narrate: bool = True) -> None:
    hazard.meters["glamour"] += 1
    propagate(world, narrate=narrate)


def open_scene(world: World, hero: Entity, companion: Entity, crossing: Crossing) -> None:
    hero.memes["curiosity"] += 1
    companion.memes["calm"] += 1
    world.say(
        f"At the busy street crossing, {hero.id} and {companion.id} stood beneath "
        f"the old arch of {crossing.landmark}. The {crossing.crowd} moved like a river, "
        f"and the {crossing.sound} of wheels and boots filled the air."
    )
    world.say(
        f"{hero.id} had come with a little heart full of wonder, as though the road "
        f"were a gate to another kingdom."
    )


def need_path(world: World, companion: Entity, crossing: Crossing) -> None:
    world.say(
        f"But the crossing was not empty. It was a crowded thread of stone and steel, "
        f"and no child could simply step into it."
    )
    world.say(
        f'{companion.id} lifted a hand. "We need the light of a safe path," '
        f"{companion.pronoun()} said."
    )


def tempt(world: World, hero: Entity, magic: MagicItem) -> None:
    hero.memes["boldness"] += 1
    world.say(
        f"{hero.id}'s eyes shone. {hero.id} whispered, "
        f'"I know a trick. {magic.phrase} {magic.spell}."'
    )


def warn(world: World, companion: Entity, hero: Entity, hazard: Hazard) -> None:
    pred = predict(world, hazard.id)
    companion.memes["care"] += 1
    world.facts["predicted_blocked"] = pred["blocked"]
    world.say(
        f"{companion.id} frowned. \"No,\" {companion.pronoun()} said softly. "
        f"\"A busy street is no place for a wild charm. It could block the road and "
        f"frighten everyone.\""
    )


def dare(world: World, hero: Entity, magic: MagicItem, hazard: Hazard) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"Doodie," {hero.id} said, as if the strange word could wake the spell. '
        f"Then {hero.id} lifted the charm."
    )


def cast(world: World, hazard: Entity, magic: MagicItem, crossing: Crossing) -> None:
    _do_magic(world, hazard)
    world.say(
        f"A thin shimmer leapt from the {magic.label}. The stones of the crossing "
        f"gleamed, then wavered like water under moonlight. For a breath, the road "
        f"seemed to fold around itself, and the way was no longer clear."
    )
    world.get("road").meters["blocked"] += 1


def call_help(world: World, companion: Entity, hero: Entity, crossing: Crossing) -> None:
    world.say(
        f'{companion.id} raised {companion.pronoun("possessive")} voice. '
        f'"Help! The crossing is not safe!"'
    )
    world.say(
        f"Their cry rang out over the crowd like a temple bell."
    )


def guide(world: World, helper: Entity, response: Response) -> None:
    world.get("road").meters["blocked"] = 0
    body = response.text
    helper.memes["resolve"] += 1
    world.say(
        f"{helper.id} came at once and {body}."
    )
    world.say(
        f"The shimmer faded. The road stopped trembling, and the crowd found its "
        f"slow, human rhythm again."
    )


def ending(world: World, hero: Entity, companion: Entity, crossing: Crossing) -> None:
    hero.memes["joy"] += 1
    companion.memes["relief"] += 1
    world.say(
        f"At last, the two crossed together under the old arch. The street was still "
        f"busy, but now it felt watched over, and every step landed safely."
    )
    world.say(
        f"{hero.id} looked back at the crossing, where the glow had become only a "
        f"pale memory, and smiled as if the road itself had learned a gentler magic."
    )


def failure(world: World, helper: Entity, response: Response, hazard: Hazard) -> None:
    body = response.fail
    helper.memes["resolve"] += 1
    world.say(f"{helper.id} came running and {body}.")
    world.say(
        "The magic swelled too wide. The crossing remained blocked, and the crowd had "
        "to wait until the spell burnt out by itself."
    )


THEMES = {
    "myth": Crossing(
        id="busy_street",
        label="busy street crossing",
        road="the road",
        landmark="the old arch",
        crowd="people and carts",
        sound="clatter",
        tags={"myth", "crossing"},
    )
}

MAGIC_ITEMS = {
    "doodle_charm": MagicItem(
        id="doodle_charm",
        label="doodle-charm",
        phrase="doodie",
        spell="to draw a bridge of light",
        forbidden=True,
        makes_glamour=True,
        tags={"magic", "doodie"},
    ),
    "silver_token": MagicItem(
        id="silver_token",
        label="silver token",
        phrase="a silver token",
        spell="to call a bright lane",
        forbidden=True,
        makes_glamour=True,
        tags={"magic"},
    ),
}

HAZARDS = {
    "road": Hazard(
        id="road",
        label="road",
        near="the crossing",
        flammable=False,
        tags={"road", "crossing"},
    )
}

RESPONSES = {
    "signal_guard": Response(
        id="signal_guard",
        sense=3,
        power=4,
        text="signaled the guards and guided the children behind the painted line until the road was clear",
        fail="signaled the guards, but the spell had already tangled the crossing too tightly",
        qa_text="signaled the guards and guided the children behind the painted line until the road was clear",
        tags={"help", "guard"},
    ),
    "lantern_words": Response(
        id="lantern_words",
        sense=2,
        power=3,
        text="spoke calm lantern-words, traced a safe circle, and opened a clear path through the crowd",
        fail="spoke calm lantern-words, but the crowded road would not open soon enough",
        qa_text="spoke calm lantern-words, traced a safe circle, and opened a clear path through the crowd",
        tags={"help", "magic"},
    ),
    "whistle_call": Response(
        id="whistle_call",
        sense=1,
        power=1,
        text="whistled once and hoped the crowd would part",
        fail="whistled once, but hope was too small against the busy road",
        qa_text="whistled once and hoped the crowd would part",
        tags={"weak"},
    ),
}


@dataclass
class StoryParams:
    theme: str
    magic: str
    response: str
    hero: str
    hero_gender: str
    companion: str
    companion_gender: str
    helper: str
    helper_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for tid, crossing in THEMES.items():
        for mid, magic in MAGIC_ITEMS.items():
            for rid, resp in RESPONSES.items():
                if reasonableness_gate(crossing, HAZARDS["road"], magic, resp):
                    combos.append((tid, mid, rid))
    return combos


GIRL_NAMES = ["Ava", "Mina", "Lina", "Nora", "Ria", "Tia"]
BOY_NAMES = ["Ari", "Ivo", "Leo", "Ned", "Omar", "Pax"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic magic storyworld for a busy street crossing.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--magic", choices=MAGIC_ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("(Refusing a weak response: choose a safer helper action.)")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.magic is None or c[1] == args.magic)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, magic, response = rng.choice(sorted(combos))
    hg = args.hero_gender or rng.choice(["girl", "boy"])
    cg = args.companion_gender or rng.choice(["girl", "boy"])
    hlg = args.helper_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hg)
    companion = args.companion or _pick_name(rng, cg, avoid=hero)
    helper = args.helper or _pick_name(rng, hlg, avoid=hero)
    return StoryParams(
        theme=theme, magic=magic, response=response,
        hero=hero, hero_gender=hg,
        companion=companion, companion_gender=cg,
        helper=helper, helper_gender=hlg,
    )


def tell(params: StoryParams) -> World:
    if params.theme not in THEMES or params.magic not in MAGIC_ITEMS or params.response not in RESPONSES:
        raise StoryError("Invalid parameters.")
    world = World()
    crossing = THEMES[params.theme]
    magic = MAGIC_ITEMS[params.magic]
    response = RESPONSES[params.response]
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="child"))
    companion = world.add(Entity(id=params.companion, kind="character", type=params.companion_gender, role="companion"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    road = world.add(Entity(id="road", type="road", label="the road"))
    hazard = world.add(Entity(id="crossing", type="hazard", label=crossing.label))

    open_scene(world, hero, companion, crossing)
    need_path(world, companion, crossing)
    world.para()
    tempt(world, hero, magic)
    warn(world, companion, hero, hazard)
    dare(world, hero, magic, hazard)
    cast(world, road, magic, crossing)
    call_help(world, companion, hero, crossing)
    world.para()
    if response.power >= 3:
        guide(world, helper, response)
        ending(world, hero, companion, crossing)
        outcome = "safe"
    else:
        failure(world, helper, response, hazard)
        ending(world, hero, companion, crossing)
        outcome = "unsafe"
    world.facts.update(
        crossing=crossing, magic=magic, response=response,
        hero=hero, companion=companion, helper=helper, road=road,
        outcome=outcome, blocked=world.get("road").meters["blocked"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly myth about a busy street crossing where someone says "{f["magic"].phrase}" and a safe helper responds.',
        f"Tell a magical crossing story in a mythic voice where {f['hero'].id} learns not to use {f['magic'].label} alone in the road.",
        f'Write a short mythic story that includes the word "{f["magic"].phrase}" and ends with the crossing safe again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    helper = f["helper"]
    magic = f["magic"]
    response = f["response"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, {companion.id}, and {helper.id} at a busy street crossing. The story follows how a magical choice became a safe crossing again."
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the magic?",
            answer=f"{hero.id} wanted to use {magic.phrase} to open a path through the crossing. That wish sounded grand, but it made the road shimmer and block the way."
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"{helper.id} used a calm response and guided everyone back to safety. The road stopped trembling, so the children could cross without fear."
        ),
    ]
    if f["outcome"] == "safe":
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with the children crossing safely under the old arch. The shimmer faded, and the busy street felt ordinary again."
        ))
    return qa


WORLD_KNOWLEDGE = {
    "crossing": [("What is a street crossing?", "A street crossing is a place where people walk across the road. It is safest to cross when traffic is stopped or a grown-up says it is okay.")],
    "busy": [("What does busy mean?", "Busy means many people or things are moving at the same time. A busy street has lots of cars, carts, or walkers.")],
    "magic": [("What is magic in stories?", "Magic is a special force in stories that can make strange things happen. In a child story, magic often changes the scene or helps teach a lesson.")],
    "guard": [("What does a guard do?", "A guard helps keep a place safe and watches for danger. Guards can guide people and stop trouble before it grows.")],
    "myth": [("What is a myth?", "A myth is an old-style story about heroes, wonders, and lessons. Myths often sound grand and timeless.")],
    "doodie": [("What is doodie in this story?", "In this story, doodie is a strange magic word. It is not a real tool; it is part of the charm the child tries to use.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"crossing", "busy", "magic", "myth", "doodie", "guard"}
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            for q, a in items:
                out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
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
        out.append(f"  {e.id}: {' '.join(bits)}")
    out.append(f"  fired={sorted(world.fired)}")
    return "\n".join(out)


CURATED = [
    StoryParams(
        theme="theme", magic="doodle_charm", response="signal_guard",
        hero="Ava", hero_gender="girl",
        companion="Ned", companion_gender="boy",
        helper="Mina", helper_gender="girl",
    )
]


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(T, M, R) :- theme(T), magic(M), response(R), sensible(R), busy_crossing(T), glamour_magic(M).
blocked :- chosen_magic(M), glamour_magic(M), road(road), glamour(M).
safe :- chosen_response(R), response(R), sense(R,S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
        lines.append(asp.fact("busy_crossing", tid))
    for mid, magic in MAGIC_ITEMS.items():
        lines.append(asp.fact("magic", mid))
        if magic.makes_glamour:
            lines.append(asp.fact("glamour_magic", mid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
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
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        print("MISMATCH in sensible responses")
        rc = 1
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(theme=None, magic=None, response=None, hero=None, hero_gender=None, companion=None, companion_gender=None, helper=None, helper_gender=None), random.Random(777)))
        _ = sample.story
    except Exception as ex:
        print(f"SMOKE TEST FAILED: {ex}")
        rc = 1
    return rc


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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos: {asp_valid_combos()}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(CURATED[0])]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
