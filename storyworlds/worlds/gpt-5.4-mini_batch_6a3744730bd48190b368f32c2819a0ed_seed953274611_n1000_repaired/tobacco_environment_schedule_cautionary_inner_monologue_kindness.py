#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tobacco_environment_schedule_cautionary_inner_monologue_kindness.py
=====================================================================================================

A standalone storyworld about a pirate-style child adventure, where a tempting
old tobacco pouch, a worried inner monologue, a kind choice, and a fixed
schedule all shape the ending.

Seed words: tobacco, environment, schedule
Features: Cautionary, Inner Monologue, Kindness
Style: Pirate Tale
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
SENSE_MIN = 2


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
    harmed_env: bool = False
    helpful: bool = False

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
class Scene:
    id: str
    setting: str
    rig: str
    title: str
    goal: str
    dark_spot: str
    ship_word: str
    send_off: str
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
class TobaccoItem:
    id: str
    label: str
    phrase: str
    where: str
    smell: str
    caution: str
    tags: set[str] = field(default_factory=set)
    harmful: bool = True
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
class EnvironmentItem:
    id: str
    label: str
    phrase: str
    effect: str
    recovery: str
    tags: set[str] = field(default_factory=set)
    harmed_by_tobacco: bool = True
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
class ScheduleItem:
    id: str
    label: str
    phrase: str
    slot: str
    kindness: str
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


@dataclass
class StoryParams:
    scene: str
    tobacco: str
    environment: str
    schedule: str
    response: str
    hero: str
    hero_gender: str
    companion: str
    companion_gender: str
    parent: str
    trait: str
    delay: int = 0
    hero_age: int = 6
    companion_age: int = 5
    relation: str = "friends"
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_smoke(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["smoke"] < THRESHOLD:
            continue
        sig = ("smoke", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "deck" in world.entities:
            world.get("deck").meters["stale_air"] += 1
        for ent in list(world.entities.values()):
            if ent.role in {"hero", "companion"}:
                ent.memes["worry"] += 1
        out.append("__smoke__")
    return out


CAUSAL_RULES = [Rule("smoke", _r_smoke)]


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


def hazard_at_risk(tobacco: TobaccoItem, env: EnvironmentItem) -> bool:
    return tobacco.harmful and env.harmed_by_tobacco


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(delay: int) -> int:
    return 1 + delay


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= fire_severity(delay)


def predict_issue(world: World, env_id: str) -> dict:
    sim = world.copy()
    sim.get(env_id).meters["smoke"] += 1
    propagate(sim, narrate=False)
    return {
        "smoke": sim.get(env_id).meters["smoke"],
        "stale_air": sim.get("deck").meters["stale_air"],
    }


def _do_tobacco(world: World, tobacco_ent: Entity, env_ent: Entity, narrate: bool = True) -> None:
    tobacco_ent.meters["smoke"] += 1
    env_ent.meters["stale_air"] += 1
    env_ent.harmed_env = True
    propagate(world, narrate=narrate)


def tell_intro(world: World, hero: Entity, companion: Entity, scene: Scene) -> None:
    world.say(
        f"On a windy afternoon, {hero.id} and {companion.id} turned the deck into "
        f"{scene.setting}. {scene.rig}"
    )
    world.say(
        f'"{scene.title} {hero.id} and {scene.title.lower()} {companion.id}!" '
        f"{hero.id} shouted. \"Let's find {scene.goal}!\""
    )


def want_light(world: World, companion: Entity, scene: Scene, env: EnvironmentItem) -> None:
    world.say(
        f"But the {scene.dark_spot} was dim, and the salt air felt heavy over "
        f"{env.label}. {companion.id} peered in. \"We need a light,\" "
        f"{companion.pronoun()} said."
    )


def tempt(world: World, hero: Entity, tobacco: TobaccoItem) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f'{hero.id}\'s eyes lit up. \"I know! {tobacco.label}! I saw '
        f"{tobacco.phrase} {tobacco.where}.\""
    )
    world.say(
        f"In {hero.pronoun('possessive')} head, the thought hissed like a tricky wave: "
        f"It looked quick, but it did not look safe."
    )


def warn(world: World, companion: Entity, hero: Entity, tobacco: TobaccoItem,
         env: EnvironmentItem, parent: Entity) -> None:
    pred = predict_issue(world, "env")
    companion.memes["caution"] += 1
    world.facts["predicted_smoke"] = pred["smoke"]
    world.say(
        f'{companion.id} bit {companion.pronoun("possessive")} lip. '
        f'"{hero.id}, we\'re not allowed to touch {tobacco.label}. '
        f"{parent.label_word.capitalize()} said so. "
        f"It can spoil the {env.label} and make the air worse.""
    )


def choose_kindness(world: World, companion: Entity, hero: Entity, tobacco: TobaccoItem,
                    env: EnvironmentItem, schedule: ScheduleItem) -> None:
    companion.memes["kindness"] += 1
    world.say(
        f'"Let\'s not make a mess of the {env.label}," {companion.id} said kindly. '
        f'"We have a {schedule.label} later, and I want it to stay easy and calm."'
    )
    world.say(
        f'{hero.id} looked down, and the mean little spark in {hero.pronoun("possessive")} '
        f"chest grew smaller."
    )


def defy(world: World, hero: Entity, companion: Entity, tobacco: TobaccoItem) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"Don't be such a scaredy-cat," {hero.id} said, then reached toward '
        f"{tobacco.label} anyway."
    )


def rescue(world: World, parent: Entity, response: Response, tobacco_ent: Entity,
           env: EnvironmentItem) -> None:
    tobacco_ent.meters["smoke"] = 0
    env.meters["stale_air"] = 0
    env.harmed_env = False
    world.say(
        f"{parent.label_word.capitalize()} came running. In a flash {parent.pronoun()} "
        f"{response.text.replace('{target}', env.label)}."
    )
    world.say(
        f"The bad smell drifted away, and the deck felt cleaner and safer again."
    )


def rescue_fail(world: World, parent: Entity, response: Response, env: EnvironmentItem) -> None:
    world.say(
        f"{parent.label_word.capitalize()} came running, but {response.fail.replace('{target}', env.label)}."
    )
    world.say(
        f"The smoke hung over the deck, and the little ship had to stop and wait."
    )


def lesson(world: World, parent: Entity, hero: Entity, companion: Entity,
           tobacco: TobaccoItem, env: EnvironmentItem, schedule: ScheduleItem) -> None:
    hero.memes["lesson"] += 1
    companion.memes["lesson"] += 1
    hero.memes["relief"] += 1
    companion.memes["relief"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {parent.label_word.capitalize()} knelt down and spoke softly. "
        f"\"I am glad you called me. But remember: {tobacco.caution}. "
        f"We keep the air kind for everyone, and we keep our {schedule.label} calm.\""
    )
    world.say(
        f'"We promise," whispered {companion.id} and {hero.id} together.'
    )
    world.say(
        f"They helped wipe the deck, and the {env.label} smelled better by the time "
        f"{schedule.slot} came."
    )


def ending_good(world: World, parent: Entity, hero: Entity, companion: Entity,
                schedule: ScheduleItem) -> None:
    hero.memes["joy"] += 1
    companion.memes["joy"] += 1
    world.say(
        f"Later, right on {schedule.slot}, {parent.label_word.capitalize()} praised "
        f"their kindness. The two pirates sailed on with clear eyes and a tidy deck."
    )


def ending_bad(world: World, hero: Entity, companion: Entity, env: EnvironmentItem,
               schedule: ScheduleItem) -> None:
    hero.memes["fear"] += 1
    companion.memes["fear"] += 1
    world.say(
        f"They had to leave the {env.label} alone for a while, and their {schedule.label} "
        f"was delayed until the air was safe again."
    )


SCENES = {
    "pirates": Scene("pirates", "a wild island deck", "The sail was a curtain, a crate held treasure, and a crayon map marked the hidden cove.", "Captain", "the treasure cove", "captain's cabin", "ship", "sailed off"),
    "harbor": Scene("harbor", "a busy harbor ship", "The rope was a ladder, a barrel held cookies, and a paper map pointed to the lighthouse.", "Captain", "the lighthouse", "lamp nook", "ship", "set out"),
    "cove": Scene("cove", "a moonlit cove deck", "The lantern was a star, a bucket held shells, and a folded map showed the secret inlet.", "Captain", "the secret inlet", "shadowy galley", "ship", "glided out"),
}

TOBACCO = {
    "pipe": TobaccoItem("pipe", "old pipe tobacco", "a tin of old pipe tobacco", "in a small pouch", "sharp and smoky", "Tobacco is not for children and not for play", tags={"tobacco", "smoke"}),
    "leaf": TobaccoItem("leaf", "tobacco leaf", "dry tobacco leaves", "in a cloth bundle", "dry and bitter", "Tobacco belongs far away from kids", tags={"tobacco", "smoke"}),
    "cigar": TobaccoItem("cigar", "cigar tobacco", "a cigar tin", "by the captain's hat", "strong and smoky", "Smoke can hurt the air and the lungs", tags={"tobacco", "smoke"}),
}

ENVIRONMENT = {
    "deck": EnvironmentItem("deck", "deck", "the wooden deck", "stale air", "fresh air", tags={"environment", "deck"}),
    "cabin": EnvironmentItem("cabin", "cabin", "the cabin room", "smoky air", "open air", tags={"environment", "cabin"}),
    "harbor": EnvironmentItem("harbor", "harbor", "the harbor breeze", "bad air", "clean breeze", tags={"environment", "harbor"}),
}

SCHEDULE = {
    "watch": ScheduleItem("watch", "watch schedule", "the evening watch", "sunset", "kindness keeps the watch calm", tags={"schedule"}),
    "supper": ScheduleItem("supper", "supper schedule", "supper time", "supper", "kindness keeps supper peaceful", tags={"schedule"}),
    "dock": ScheduleItem("dock", "dock schedule", "the docking time", "dusk", "kindness keeps the dock orderly", tags={"schedule"}),
}

RESPONSES = {
    "air_out": Response("air_out", 3, 3, "opened the porthole and fanned the smoke out into the sea air", "tried to air it out, but the smoke stayed too thick", "opened the porthole and let the smoke drift out"),
    "seal_pouch": Response("seal_pouch", 2, 2, "closed the pouch fast, carried it outside, and set it well away from the deck", "closed the pouch, but the smell had already spread", "closed the pouch and moved it outside"),
    "call_adult": Response("call_adult", 3, 4, "called for help, opened the deck hatch, and got the air moving again", "called for help, but the smoke had already spread too much", "called for help and cleared the air"),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Finn", "Eli"]
TRAITS = ["careful", "curious", "kind", "cautious", "gentle", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SCENES:
        for t_id, t in TOBACCO.items():
            for e_id, e in ENVIRONMENT.items():
                if hazard_at_risk(t, e):
                    combos.append((s, t_id, e_id))
    return combos


def pair_name(a: Entity, b: Entity, relation: str) -> str:
    return "two friends" if relation == "friends" else "two pirates"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words "tobacco", "environment", and "schedule".',
        f"Tell a cautionary pirate tale where {f['hero'].id} is tempted by tobacco, "
        f"but {f['companion'].id} uses an inner monologue and kindness to keep the environment safe.",
        f"Write a gentle story with a fixed schedule, a smoky warning, and a kind ending on a ship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    parent: Entity = f["parent"]
    tobacco: TobaccoItem = f["tobacco_cfg"]
    env: EnvironmentItem = f["env_cfg"]
    sched: ScheduleItem = f["sched_cfg"]
    answers = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {companion.id}, who are pretending to be pirates on the deck. {parent.label_word.capitalize()} comes in to help when the tobacco causes trouble.",
        ),
        QAItem(
            question="Why did the companion worry?",
            answer=f"{companion.id} worried because the tobacco could spoil the {env.label} and make the air bad. In the companion's head, the warning felt clear: the deck needed kindness, not smoke.",
        ),
        QAItem(
            question="What did the hero learn?",
            answer=f"{hero.id} learned that {tobacco.caution.lower()}. The hero also learned to respect the schedule and choose the kinder, safer choice for everyone on the ship.",
        ),
    ]
    if f.get("outcome") == "contained":
        answers.append(QAItem(
            question="How did they fix the problem?",
            answer=f"{parent.label_word.capitalize()} {f['response'].qa_text.replace('{target}', env.label)}. That helped the {env.label} clear and let the schedule stay on time.",
        ))
        answers.append(QAItem(
            question="How did kindness show up in the story?",
            answer=f"{companion.id} spoke gently, kept the hero from making the smoke worse, and helped clean up the deck. Kindness made the warning easier to hear.",
        ))
    else:
        answers.append(QAItem(
            question="How did the story end?",
            answer=f"The smoke spread too far, so the pirates had to stop and wait for the air to clear. They were safe, but the schedule was delayed and the deck was not ready for play yet.",
        ))
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["tobacco_cfg"].tags) | set(world.facts["env_cfg"].tags) | set(world.facts["sched_cfg"].tags)
    out: list[QAItem] = []
    if "tobacco" in tags:
        out.append(QAItem("What is tobacco?", "Tobacco is a plant people do not use as a child's toy. Smoke from tobacco can be harmful and should be kept away from children."))
    if "environment" in tags:
        out.append(QAItem("What does environment mean?", "Environment means the place and air around you. Keeping the environment clean and safe helps everyone breathe easier."))
    if "schedule" in tags:
        out.append(QAItem("What is a schedule?", "A schedule is a plan for when things happen. It helps people know what comes next and keeps the day orderly."))
    out.append(QAItem("Why should children avoid tobacco?", "Children should avoid tobacco because it is not safe to play with or breathe in. Keeping tobacco away protects the air and the people nearby."))
    return out


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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tobacco and args.environment:
        if not hazard_at_risk(TOBACCO[args.tobacco], ENVIRONMENT[args.environment]):
            raise StoryError("(No story: this tobacco choice does not meaningfully threaten this environment.)")
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.tobacco is None or c[1] == args.tobacco)
              and (args.environment is None or c[2] == args.environment)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, tobacco, environment = rng.choice(sorted(combos))
    schedule = args.schedule or rng.choice(sorted(SCHEDULE))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    hero_gender = args.hero_gender or ("girl" if hero in GIRL_NAMES else "boy")
    companion = args.companion or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    companion_gender = args.companion_gender or ("girl" if companion in GIRL_NAMES else "boy")
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        scene=scene,
        tobacco=tobacco,
        environment=environment,
        schedule=schedule,
        response=response,
        hero=hero,
        hero_gender=hero_gender,
        companion=companion,
        companion_gender=companion_gender,
        parent=parent,
        trait=trait,
    )


def tell(scene: Scene, tobacco: TobaccoItem, env: EnvironmentItem, sched: ScheduleItem,
         response: Response, hero_name: str, hero_gender: str, companion_name: str,
         companion_gender: str, parent_type: str, trait: str, delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait]))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_gender, role="companion", traits=["kind", "careful"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    deck = world.add(Entity(id="deck", type="place", label="the deck"))
    tobacco_ent = world.add(Entity(id="tobacco", type="thing", label=tobacco.label))
    env_ent = world.add(Entity(id="env", type="thing", label=env.label))
    sched_ent = world.add(Entity(id="sched", type="thing", label=sched.label))

    tell_intro(world, hero, companion, scene)
    want_light(world, companion, scene, env)
    world.para()
    tempt(world, hero, tobacco)
    warn(world, companion, hero, tobacco, env, parent)
    choose_kindness(world, companion, hero, tobacco, env, sched)

    world.para()
    hero.memes["inner_monologue"] += 1
    averted = hero.memes["defiance"] < THRESHOLD
    if averted:
        world.say(
            f"{hero.id} listened to the small quiet voice in {hero.pronoun('possessive')} head. "
            f"It said the kinder path was the brave one."
        )
        world.say(
            f"{hero.id} left the tobacco alone and helped {companion.id} tidy the deck instead."
        )
        ending_good(world, parent, hero, companion, sched)
        outcome = "averted"
        contained = True
    else:
        defy(world, hero, companion, tobacco)
        _do_tobacco(world, tobacco_ent, env_ent, narrate=False)
        world.para()
        if is_contained(response, delay):
            rescue(world, parent, response, tobacco_ent, env)
            lesson(world, parent, hero, companion, tobacco, env, sched)
            world.para()
            ending_good(world, parent, hero, companion, sched)
            outcome = "contained"
            contained = True
        else:
            rescue_fail(world, parent, response, env)
            ending_bad(world, hero, companion, env, sched)
            outcome = "burned"
            contained = False

    world.facts.update(
        hero=hero,
        companion=companion,
        parent=parent,
        scene=scene,
        tobacco_cfg=tobacco,
        env_cfg=env,
        sched_cfg=sched,
        response=response,
        delay=delay,
        outcome=outcome,
        contained=contained,
    )
    return world


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def outcome_of(params: StoryParams) -> str:
    return "contained" if is_contained(RESPONSES[params.response], params.delay) else "burned"


ASP_RULES = r"""
hazard(T, E) :- tobacco(T), environment(E), harmful_tobacco(T), harmed_by_tobacco(E).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
outcome(contained) :- chosen_response(R), chosen_delay(D), response(R), power(R,P), severity(D,V), P >= V.
outcome(burned) :- chosen_response(R), chosen_delay(D), response(R), power(R,P), severity(D,V), P < V.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for tid, t in TOBACCO.items():
        lines.append(asp.fact("tobacco", tid))
        if t.harmful:
            lines.append(asp.fact("harmful_tobacco", tid))
    for eid, e in ENVIRONMENT.items():
        lines.append(asp.fact("environment", eid))
        if e.harmed_by_tobacco:
            lines.append(asp.fact("harmed_by_tobacco", eid))
    for sid in SCHEDULE:
        lines.append(asp.fact("schedule", sid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for d in [0, 1, 2]:
        lines.append(asp.fact("severity", d, 1 + d))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("chosen_response", params.response), asp.fact("chosen_delay", params.delay)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    python_sens = {r.id for r in sensible_responses()}
    clingo_sens = set(asp_sensible())
    if python_sens != clingo_sens:
        print("MISMATCH in sensible responses")
        rc = 1
    else:
        print(f"OK: sensible responses match ({sorted(python_sens)}).")
    cases = [resolve_params(argparse.Namespace(scene=None, tobacco=None, environment=None, schedule=None, response=None, hero=None, hero_gender=None, companion=None, companion_gender=None, parent=None, trait=None), random.Random(7))]
    cases.append(StoryParams(scene="pirates", tobacco="pipe", environment="deck", schedule="watch", response="air_out", hero="Tom", hero_gender="boy", companion="Lily", companion_gender="girl", parent="mother", trait="careful"))
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad:
        print("MISMATCH in outcomes")
        rc = 1
    else:
        print("OK: outcome model matches Python logic.")
    try:
        sample = generate(cases[0])
        assert sample.story
        print("OK: generate smoke test produced a story.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-style cautionary story world with tobacco, environment, and schedule.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--tobacco", choices=TOBACCO)
    ap.add_argument("--environment", choices=ENVIRONMENT)
    ap.add_argument("--schedule", choices=SCHEDULE)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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


CURATED = [
    StoryParams(scene="pirates", tobacco="pipe", environment="deck", schedule="watch", response="air_out", hero="Tom", hero_gender="boy", companion="Lily", companion_gender="girl", parent="mother", trait="careful"),
    StoryParams(scene="harbor", tobacco="leaf", environment="harbor", schedule="dock", response="call_adult", hero="Mia", hero_gender="girl", companion="Ben", companion_gender="boy", parent="father", trait="kind"),
    StoryParams(scene="cove", tobacco="cigar", environment="cabin", schedule="supper", response="seal_pouch", hero="Eli", hero_gender="boy", companion="Nora", companion_gender="girl", parent="mother", trait="thoughtful"),
]


def generate(params: StoryParams) -> StorySample:
    for key in ("scene", "tobacco", "environment", "schedule", "response"):
        if getattr(params, key) not in globals()[key.upper()]:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(
        SCENES[params.scene],
        TOBACCO[params.tobacco],
        ENVIRONMENT[params.environment],
        SCHEDULE[params.schedule],
        RESPONSES[params.response],
        params.hero,
        params.hero_gender,
        params.companion,
        params.companion_gender,
        params.parent,
        params.trait,
        params.delay,
    )
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
        print(asp_program("", "#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(f"sensible responses: {', '.join(asp_sensible())}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
