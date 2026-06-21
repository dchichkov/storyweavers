#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nonsensical_bike_lane_bravery_myth.py
======================================================================

A small standalone storyworld about a child in a bike lane, a strange mythic
challenge, and bravery that turns a nonsense idea into a sensible rescue.

Seed words:
- nonsensical
- bike lane
- Bravery
- Myth

The world is built around a child who hears a grand, myth-like dare to do
something absurd in a bike lane. The story model lets bravery mean two different
things: reckless boasting, and the quieter courage to stop, warn, and help.
The ending proves which kind won.

This script follows the shared Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven prose
- generation prompts, story QA, and world QA from world state
- Python and ASP parity checks
- CLI support for --all, --seed, -n, --trace, --qa, --json, --asp, --verify, --show-asp
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
BRAVERY_START = 5.0
CAUTION_START = 4.0
DANGER_START = 0.0


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
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
class Setting:
    id: str
    place: str
    detail: str
    danger_phrase: str
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
class Myth:
    id: str
    title: str
    voice: str
    dare: str
    warning: str
    turn: str
    ending: str
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
class Hazard:
    id: str
    label: str
    phrase: str
    risk: int
    makes_danger: bool = True
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
    label: str
    phrase: str
    power: int
    sense: int
    success: str
    fail: str
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
class StoryParams:
    myth: str
    setting: str
    hazard: str
    rescue: str
    hero: str
    hero_type: str
    witness: str
    witness_type: str
    elder: str
    elder_type: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["risk"] < THRESHOLD:
            continue
        sig = ("danger", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for c in world.characters():
            c.memes["fear"] += 1
        if "lane" in world.entities:
            world.get("lane").meters["danger"] += 1
        out.append("__danger__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["safe"] < THRESHOLD:
            continue
        sig = ("calm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["bravery"] += 1
        e.memes["calm"] += 1
        out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule("danger", "social", _r_danger),
    Rule("calm", "social", _r_calm),
]


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


def sensible_rescues() -> list[Rescue]:
    return [r for r in RESCUES.values() if r.sense >= 2]


def valid_combo(myth: Myth, setting: Setting, hazard: Hazard, rescue: Rescue) -> bool:
    return setting.id == "bike_lane" and hazard.makes_danger and rescue.sense >= 2


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for mid in MYTHS:
        for sid in SETTINGS:
            for hid, hz in HAZARDS.items():
                for rid, rs in RESCUES.items():
                    if valid_combo(MYTHS[mid], SETTINGS[sid], hz, rs):
                        combos.append((mid, sid, hid, rid))
    return combos


def reasonableness_error(hazard: Hazard, rescue: Rescue) -> str:
    return (
        f"(No story: {hazard.label} is too ordinary for a mythic bike-lane challenge, "
        f"or {rescue.label} is too weak to count as brave help. "
        f"Pick a real lane hazard and a sensible rescue.)"
    )


def predict(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    _trigger_hazard(sim, sim.get(hazard_id), narrate=False)
    return {
        "danger": sim.get("lane").meters["danger"],
        "risk": sum(c.meters["risk"] for c in sim.characters()),
    }


def _trigger_hazard(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["risk"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, myth: Myth, hero: Entity, witness: Entity, setting: Setting) -> None:
    hero.memes["bravery"] += BRAVERY_START
    witness.memes["caution"] += CAUTION_START
    world.say(
        f"In the old {setting.place}, {myth.voice} told of {hero.id}, who entered the "
        f"{setting.place} as if it were a silver road. {setting.detail}"
    )
    world.say(
        f'"{myth.title}!" cried {hero.id}. "{myth.dare}"'
    )
    world.say(
        f"{witness.id} frowned. {myth.warning}"
    )


def tempt(world: World, hero: Entity, myth: Myth) -> None:
    hero.memes["boast"] += 1
    world.say(
        f"{hero.id}'s eyes shone with a reckless light. "
        f'"{myth.turn}" {hero.id} said, and the claim sounded bold and {myth.id}.'
    )


def warn(world: World, witness: Entity, hero: Entity, hazard: Hazard) -> None:
    prediction = predict(world, "hazard")
    witness.memes["caution"] += 1
    world.facts["prediction"] = prediction
    world.say(
        f'{witness.id} shook {witness.pronoun("possessive")} head. '
        f'"That is nonsensical," {witness.id} said. "{hazard.phrase} can lead to a real tumble."'
    )


def defy(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.meters["risk"] += 1
    world.say(f"{hero.id} did not listen. {hero.id} reached for the {hazard.label} anyway.")


def sound_alarm(world: World, witness: Entity, hero: Entity, elder: Entity, setting: Setting) -> None:
    world.say(
        f'"{hero.id}!" shouted {witness.id}. "{setting.danger_phrase}!"'
    )
    world.say(f'"{elder.id}!"')


def rescue_success(world: World, elder: Entity, rescue: Rescue, hazard: Hazard) -> None:
    elder.meters["safe"] += 1
    body = rescue.success.replace("{hazard}", hazard.label)
    world.say(
        f"{elder.id} came at once and {body}."
    )
    world.say(
        f"The lane quieted, and the strange trouble lost its teeth."
    )


def rescue_fail(world: World, elder: Entity, rescue: Rescue, hazard: Hazard) -> None:
    elder.meters["safe"] += 0.2
    body = rescue.fail.replace("{hazard}", hazard.label)
    world.say(
        f"{elder.id} tried to help, but {body}."
    )
    world.say(
        f"The lane stayed wild, and the odd danger kept growing."
    )


def lesson(world: World, elder: Entity, hero: Entity, witness: Entity, myth: Myth) -> None:
    for c in (hero, witness):
        c.memes["relief"] += 1
        c.memes["lesson"] += 1
    world.say(
        f"Then {elder.id} knelt by them both and said, "
        f'"Bravery is not shouting the loudest. Bravery is seeing what is wrong and stopping it."'
    )
    world.say(
        f"{hero.id} and {witness.id} nodded, and the words settled like dust after rain."
    )


def ending(world: World, hero: Entity, witness: Entity, elder: Entity, myth: Myth) -> None:
    hero.memes["bravery"] += 1
    witness.memes["bravery"] += 1
    world.say(
        f"After that, {hero.id} walked the bike lane more carefully, with {witness.id} and {elder.id} beside {hero.pronoun('object')}."
    )
    world.say(
        f"{myth.ending}, and this time the road looked ordinary instead of impossible."
    )


def tell(myth: Myth, setting: Setting, hazard: Hazard, rescue: Rescue,
         hero: str = "Aria", hero_type: str = "girl",
         witness: str = "Milo", witness_type: str = "boy",
         elder: str = "Grandmother", elder_type: str = "woman") -> World:
    world = World()
    h = world.add(Entity(id=hero, kind="character", type=hero_type, role="hero"))
    w = world.add(Entity(id=witness, kind="character", type=witness_type, role="witness"))
    e = world.add(Entity(id=elder, kind="character", type=elder_type, role="elder"))
    lane = world.add(Entity(id="lane", kind="thing", type="place", label=setting.place))
    hz = world.add(Entity(id="hazard", kind="thing", type="hazard", label=hazard.label))
    world.facts.update(hero=h, witness=w, elder=e, lane=lane, hazard=hz, myth=myth, setting=setting, rescue=rescue)

    opening(world, myth, h, w, setting)
    world.para()
    tempt(world, h, myth)
    warn(world, w, h, hazard)
    defy(world, h, hazard)
    sound_alarm(world, w, h, e, setting)
    if rescue.sense >= 3:
        world.para()
        rescue_success(world, e, rescue, hazard)
        lesson(world, e, h, w, myth)
        world.para()
        ending(world, h, w, e, myth)
        outcome = "saved"
    else:
        world.para()
        rescue_fail(world, e, rescue, hazard)
        ending(world, h, w, e, myth)
        outcome = "failed"
    world.facts["outcome"] = outcome
    return world


MYTHS = {
    "sun_chariot": Myth(
        id="sun_chariot",
        title="The Sun-Chariot Tale",
        voice="the old singers said",
        dare="Ride where no wheel should go and laugh at the wind!",
        warning="But a true road is not made for dares.",
        turn="I can be brighter than the morning star!",
        ending="At sunset, the lane glowed gold and calm",
        tags={"myth", "bravery"},
    ),
    "river_fox": Myth(
        id="river_fox",
        title="The River-Fox Story",
        voice="the storytellers whispered",
        dare="Follow the fox-road and do not fear the bend!",
        warning="Some bends hide trouble, even when they sparkle.",
        turn="I will be swift as a fox and never slip!",
        ending="By dusk, the lane remembered every brave footstep",
        tags={"myth", "bravery"},
    ),
    "thunder_wheel": Myth(
        id="thunder_wheel",
        title="The Thunder-Wheel Saga",
        voice="the drums of the market claimed",
        dare="Chase the thunder through the painted lane!",
        warning="Thunder is loud, but the ground can still be foolish.",
        turn="Let the whole road hear how fearless I am!",
        ending="When night came, the bike lane was quiet as a chapel",
        tags={"myth", "bravery"},
    ),
}

SETTINGS = {
    "bike_lane": Setting(
        id="bike_lane",
        place="bike lane",
        detail="The white line ran straight as a spear, and the curb waited beside it like a patient stone wall.",
        danger_phrase="The bike lane is for bikes, not for leaps and dares.",
        tags={"bike_lane"},
    )
}

HAZARDS = {
    "fallen_branch": Hazard(
        id="fallen_branch",
        label="fallen branch",
        phrase="a fallen branch across the lane",
        risk=3,
        makes_danger=True,
        tags={"branch", "tumble"},
    ),
    "loose_cone": Hazard(
        id="loose_cone",
        label="loose traffic cone",
        phrase="a loose cone wobbling in the lane",
        risk=2,
        makes_danger=True,
        tags={"cone", "tumble"},
    ),
    "spilled_gravel": Hazard(
        id="spilled_gravel",
        label="spilled gravel",
        phrase="spilled gravel shining like tiny teeth",
        risk=3,
        makes_danger=True,
        tags={"gravel", "tumble"},
    ),
    "curb_gap": Hazard(
        id="curb_gap",
        label="broken curb stone",
        phrase="a broken stone in the curb",
        risk=1,
        makes_danger=True,
        tags={"curb", "tumble"},
    ),
}

RESCUES = {
    "slow_down": Rescue(
        id="slow_down",
        label="slow down and walk the bikes",
        phrase="to slow the bikes and walk them around the danger",
        power=3,
        sense=3,
        success="slowed the bikes and walked them around the hazard",
        fail="could not slow the hazard in time",
        tags={"bravery", "safe"},
    ),
    "lift_around": Rescue(
        id="lift_around",
        label="lift the bikes around the hazard",
        phrase="to lift the bikes around the danger",
        power=4,
        sense=3,
        success="lifted the bikes around the hazard and set them back down safely",
        fail="could not lift the danger aside",
        tags={"bravery", "safe"},
    ),
    "signal_stop": Rescue(
        id="signal_stop",
        label="signal the riders to stop",
        phrase="to signal the riders to stop",
        power=2,
        sense=3,
        success="signaled the riders to stop and cleared the lane",
        fail="could not call the riders in time",
        tags={"bravery", "safe"},
    ),
    "shout_warning": Rescue(
        id="shout_warning",
        label="shout a warning",
        phrase="to shout a warning and hope for the best",
        power=1,
        sense=1,
        success="",
        fail="shouted, but the warning was too small and too late",
        tags={"nonsensical"},
    ),
}

CHARACTERS = {
    "Aria": {"girl", "boy"},
    "Milo": {"boy"},
    "Nia": {"girl"},
    "Tavi": {"girl", "boy"},
    "Joren": {"boy"},
    "Sera": {"girl"},
}

TRAITS = ["bold", "careful", "quick", "thoughtful", "steady"]


def explain_combo(hazard: Hazard, rescue: Rescue) -> str:
    return reasonableness_error(hazard, rescue)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: mythic bravery in a bike lane.")
    ap.add_argument("--myth", choices=MYTHS)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--hero")
    ap.add_argument("--witness")
    ap.add_argument("--elder")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--witness-type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["woman", "man"])
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
    if args.hazard and args.rescue:
        if not valid_combo(MYTHS[args.myth or next(iter(MYTHS))], SETTINGS[args.setting or "bike_lane"], HAZARDS[args.hazard], RESCUES[args.rescue]):
            raise StoryError(explain_combo(HAZARDS[args.hazard], RESUES[args.rescue]))  # type: ignore[name-defined]
    combos = [c for c in valid_combos()
              if (args.myth is None or c[0] == args.myth)
              and (args.setting is None or c[1] == args.setting)
              and (args.hazard is None or c[2] == args.hazard)
              and (args.rescue is None or c[3] == args.rescue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    myth, setting, hazard, rescue = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    witness_type = args.witness_type or rng.choice(["girl", "boy"])
    elder_type = args.elder_type or rng.choice(["woman", "man"])
    hero = args.hero or rng.choice([n for n in ["Aria", "Tavi", "Nia", "Sera"] if hero_type in CHARACTERS[n]])
    witness = args.witness or rng.choice([n for n in ["Milo", "Joren", "Tavi"] if witness_type in CHARACTERS[n]])
    elder = args.elder or rng.choice(["Grandmother", "Grandfather"])
    return StoryParams(myth=myth, setting=setting, hazard=hazard, rescue=rescue,
                       hero=hero, hero_type=hero_type, witness=witness, witness_type=witness_type,
                       elder=elder, elder_type=elder_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    myth, setting, hazard, rescue = f["myth"], f["setting"], f["hazard"], f["rescue"]
    hero, witness = f["hero"], f["witness"]
    return [
        f'Write a mythic story about {setting.place} that includes the word "nonsensical" and shows bravery in a sensible way.',
        f"Tell a child-safe myth where {hero.id} hears a nonsensical dare in the bike lane, {witness.id} warns about danger, and an elder helps.",
        f"Write a short myth-style story in the bike lane where a brave child faces {hazard.label} and chooses {rescue.label} instead of boasting.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    myth, setting, hazard, rescue = f["myth"], f["setting"], f["hazard"], f["rescue"]
    hero, witness, elder = f["hero"], f["witness"], f["elder"]
    qa = [
        ("What kind of story is this?",
         f"It is a myth-like story about bravery in the bike lane. The old voice and the grand dare make it feel like a legend, but the actions stay concrete and safe."),
        ("What made the challenge nonsensical?",
         f"The dare pushed {hero.id} toward a risky choice in the bike lane, which is not a place for foolish stunts. That is why {witness.id} called it nonsensical and warned against it."),
        ("Who warned the hero?",
         f"{witness.id} warned {hero.id} first, and then {elder.id} came to help. The warning mattered because the hazard could have caused a tumble."),
    ]
    if f.get("outcome") == "saved":
        qa.append((
            "How was the danger handled?",
            f"{elder.id} used {rescue.label} and {rescue.success}. That turned the scene from reckless boasting into true bravery."
        ))
        qa.append((
            "How did bravery change in the story?",
            f"At first, bravery looked loud and showy. By the end, bravery meant stopping, warning, and choosing the safer path."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"The help was not enough, so the lane stayed dangerous. Even so, the story still shows that speaking up was the bravest choice available."
        ))
    return qa


KNOWLEDGE = {
    "bike_lane": [("What is a bike lane?",
                   "A bike lane is a marked part of the road where bikes are meant to ride. It helps keep riders and cars separated.")],
    "bravery": [("What is bravery?",
                 "Bravery means doing the right thing even when you feel afraid. It can mean helping, warning, or asking for help.")],
    "myth": [("What is a myth?",
               "A myth is an old story people tell about big deeds, strange places, or powerful ideas. Myths often sound grand and ancient.")],
    "branch": [("Why can a fallen branch be dangerous in a bike lane?",
                "A branch can make a bike wobble or stop suddenly. That can cause a rider to fall.")],
    "gravel": [("Why is spilled gravel dangerous for bikes?",
                "Gravel can make wheels slip, especially when a bike turns fast. A rider can lose balance.")],
    "cone": [("Why should a traffic cone stay where it belongs?",
               "A cone warns people about danger. If it falls over, the warning is lost and someone can trip.")],
    "safe": [("What is a safer choice when a road looks dangerous?",
               "A safer choice is to slow down, stop, and ask a grown-up for help. That keeps everyone out of trouble.")],
}
KNOWLEDGE_ORDER = ["myth", "bravery", "bike_lane", "branch", "gravel", "cone", "safe"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["myth"].tags) | set(world.facts["setting"].tags) | set(world.facts["hazard"].tags) | set(world.facts["rescue"].tags)
    out = []
    for k in KNOWLEDGE_ORDER:
        if k in tags and k in KNOWLEDGE:
            out.extend(KNOWLEDGE[k])
    return out


def tell(params: StoryParams) -> World:
    myth = MYTHS[params.myth]
    setting = SETTINGS[params.setting]
    hazard = HAZARDS[params.hazard]
    rescue = RESCUES[params.rescue]
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero"))
    witness = world.add(Entity(id=params.witness, kind="character", type=params.witness_type, role="witness"))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder_type, role="elder"))
    lane = world.add(Entity(id="bike_lane", kind="thing", type="place", label=setting.place))
    hz = world.add(Entity(id="hazard", kind="thing", type="hazard", label=hazard.label))
    world.facts.update(hero=hero, witness=witness, elder=elder, lane=lane, hazard=hz, myth=myth, setting=setting, rescue=rescue)

    opening(world, myth, hero, witness, setting)
    world.para()
    tempt(world, hero, myth)
    warn(world, witness, hero, hazard)
    defy(world, hero, hazard)
    sound_alarm(world, witness, hero, elder, setting)
    world.para()
    if rescue.sense >= 2:
        rescue_success(world, elder, rescue, hazard)
        lesson(world, elder, hero, witness, myth)
    else:
        rescue_fail(world, elder, rescue, hazard)
    world.para()
    ending(world, hero, witness, elder, myth)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(M,S,H,R) :- myth(M), setting(S), hazard(H), rescue(R), bike_lane(S), makes_danger(H), sensible(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for mid in MYTHS:
        lines.append(asp.fact("myth", mid))
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        if sid == "bike_lane":
            lines.append(asp.fact("bike_lane", sid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.makes_danger:
            lines.append(asp.fact("makes_danger", hid))
    for rid, r in RESCUES.items():
        lines.append(asp.fact("rescue", rid))
        if r.sense >= 2:
            lines.append(asp.fact("sensible", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combo gates differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(myth=None, setting=None, hazard=None, rescue=None, hero=None, witness=None, elder=None, hero_type=None, witness_type=None, elder_type=None), random.Random(1)))
        assert sample.story
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    else:
        print("OK: validation matches and a normal generate/emit smoke test passed.")
    return rc


CURATED = [
    StoryParams(myth="sun_chariot", setting="bike_lane", hazard="fallen_branch", rescue="slow_down", hero="Aria", hero_type="girl", witness="Milo", witness_type="boy", elder="Grandmother", elder_type="woman"),
    StoryParams(myth="river_fox", setting="bike_lane", hazard="spilled_gravel", rescue="lift_around", hero="Tavi", hero_type="boy", witness="Nia", witness_type="girl", elder="Grandfather", elder_type="man"),
    StoryParams(myth="thunder_wheel", setting="bike_lane", hazard="loose_cone", rescue="signal_stop", hero="Sera", hero_type="girl", witness="Milo", witness_type="boy", elder="Grandmother", elder_type="woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible myth-story combos:")
        for item in asp_valid_combos():
            print("  ", item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid story combinations exist.)")
    if args.myth and args.setting and args.hazard and args.rescue:
        if not valid_combo(MYTHS[args.myth], SETTINGS[args.setting], HAZARDS[args.hazard], RESCUES[args.rescue]):
            raise StoryError(explain_combo(HAZARDS[args.hazard], RESCUES[args.rescue]))
    filtered = [c for c in combos
                if (args.myth is None or c[0] == args.myth)
                and (args.setting is None or c[1] == args.setting)
                and (args.hazard is None or c[2] == args.hazard)
                and (args.rescue is None or c[3] == args.rescue)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    myth, setting, hazard, rescue = rng.choice(filtered)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    witness_type = args.witness_type or rng.choice(["girl", "boy"])
    elder_type = args.elder_type or rng.choice(["woman", "man"])
    hero_pool = [n for n in ["Aria", "Tavi", "Nia", "Sera"] if hero_type in CHARACTERS[n]]
    witness_pool = [n for n in ["Milo", "Tavi", "Joren", "Nia"] if witness_type in CHARACTERS[n]]
    elder_pool = ["Grandmother", "Grandfather"]
    return StoryParams(
        myth=myth, setting=setting, hazard=hazard, rescue=rescue,
        hero=args.hero or rng.choice(hero_pool),
        hero_type=hero_type,
        witness=args.witness or rng.choice(witness_pool),
        witness_type=witness_type,
        elder=args.elder or rng.choice(elder_pool),
        elder_type=elder_type,
    )


if __name__ == "__main__":
    main()
