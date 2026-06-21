#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/snowpan_meddlesome_duckling_twist_pirate_tale.py
=================================================================================

A tiny storyworld in the spirit of a pirate tale: a child crew on a snowy shore,
a meddlesome duckling, a snowpan, a risky shortcut, and a twist that turns the
mess into a rescue.

The world is built from state, not a frozen paragraph: characters have meters
and memes, props and weather matter, and the ending depends on what the crew
chooses to do with the snowpan.

Seed words: snowpan, meddlesome, duckling
Feature: Twist
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

    carries: bool = False
    flammable: object | None = None
    helpful: bool = False
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Setting:
    id: str
    place: str
    weather: str
    details: str
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
class CrewTask:
    id: str
    verb: str
    goal: str
    danger: str
    zone: set[str]
    twist_use: str
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    kind: str
    flammable: bool = False
    carries: bool = False
    helpful: bool = False
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


def _r_scare(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["soaked"] >= THRESHOLD and ("deck" in world.entities):
            sig = ("scare", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.get("deck").meters["slip"] += 1
            for e in list(world.entities.values()):
                if e.kind == "character":
                    e.memes["alarm"] += 1
            out.append("__alarm__")
    return out


def _r_twist(world: World) -> list[str]:
    out = []
    duck = world.entities.get("duckling")
    pan = world.entities.get("snowpan")
    if not duck or not pan:
        return out
    if duck.meters["scooped"] >= THRESHOLD and pan.meters["used"] >= THRESHOLD:
        sig = ("twist",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        pan.meters["cleared"] += 1
        world.get("cargo").meters["saved"] += 1
        out.append("__twist__")
    return out


CAUSAL_RULES = [Rule("scare", _r_scare), Rule("twist", _r_twist)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combo(task: CrewTask, target: ObjectCfg) -> bool:
    return task.danger == "soak" and target.kind == "cargo" and target.flammable


def outcome_of(params: "StoryParams") -> str:
    resp = RESPONSES[params.response]
    if resp.power >= params.delay + 1:
        return "saved"
    return "lost"


def predict(world: World, target_id: str) -> dict:
    sim = world.copy()
    sim.get(target_id).meters["soaked"] += 1
    propagate(sim, narrate=False)
    return {
        "slip": sim.get("deck").meters["slip"],
        "saved": sim.get("cargo").meters["saved"],
    }


def _do_task(world: World, task: CrewTask, narrate: bool = True) -> None:
    worker = world.get("worker")
    worker.meters["soaked"] += 1
    worker.memes["eager"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, duckling: Entity, mate: Entity, setting: Setting, task: CrewTask) -> None:
    world.say(
        f"On a bright snowy morning, {hero.id}, {mate.id}, and a meddlesome duckling "
        f"watched {setting.place} shine white under {setting.weather} skies."
    )
    world.say(
        f"The crew had turned a crate into a little pirate boat, and the snowpan "
        f"waited like a curious spoon beside the drift."
    )
    world.say(
        f'\"We need a way to cross the drift and reach {task.goal},\" {hero.id} said, '
        f'while the duckling peered at the snowpan with bright, greedy eyes.'
    )
    hero.memes["hope"] += 1
    mate.memes["caution"] += 1
    duckling.memes["mischief"] += 1


def meddle(world: World, duckling: Entity, task: CrewTask) -> None:
    duckling.memes["meddlesome"] += 1
    world.say(
        f"The meddlesome duckling nudged the snowpan and quacked as if it had found "
        f"treasure."
    )
    world.say(
        f'\"No, no,\" {world.get("mate").id} warned. \"That pan is for safe snow, '
        f'not for silly splashing near {task.danger}.\"'
    )


def attempt(world: World, hero: Entity, task: CrewTask) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} still reached for the {task.twist_use}, thinking it might make a "
        f"better pirate trick."
    )


def accident(world: World, hero: Entity, target: Entity, task: CrewTask) -> None:
    target.meters["soaked"] += 1
    hero.meters["soaked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Whoosh! The {task.twist_use} tipped, the snowy splash slid across the deck, "
        f"and the cargo box got wet."
    )
    world.say(f"{hero.id} stared as the little ship began to slip.")


def call_help(world: World, mate: Entity) -> None:
    mate.memes["alarm"] += 1
    world.say(f"\"Help!\" {mate.id} shouted. \"The deck is getting slippery!\"")


def response_scene(world: World, parent: Entity, response: Response, cargo: Entity, task: CrewTask) -> None:
    cargo.meters["wet"] = 0
    world.get("deck").meters["slip"] = 0
    world.get("snowpan").meters["used"] = 1
    world.get("snowpan").meters["cleared"] = 1
    body = response.text.replace("{target}", cargo.label)
    world.say(
        f"{parent.label_word.capitalize()} came running and {body}."
    )
    world.say(
        f"Then {world.get('duckling').id} gave the snowpan a proud little wobble, and "
        f"the crew used it to scoop snow away from the wet spot."
    )


def twist_end(world: World, hero: Entity, duckling: Entity, mate: Entity, task: CrewTask, setting: Setting) -> None:
    hero.memes["relief"] += 1
    mate.memes["relief"] += 1
    duckling.memes["pride"] += 1
    world.say(
        f"For a blink, everyone thought the day was ruined. But the twist was this: "
        f"the meddlesome duckling had pushed the snowpan right toward a drift that was "
        f"melting into the path."
    )
    world.say(
        f"{hero.id} used the snowpan to pack fresh snow over the slick patch, and the "
        f"little boat slid safely to {task.goal} instead."
    )
    world.say(
        f"By sunset, {setting.place} looked calm again, and the snowpan was no longer a "
        f"toy to grab -- it was the crew's best tool for keeping the pirate game safe."
    )


def rescue_fail(world: World, response: Response, cargo: Entity, task: CrewTask) -> None:
    world.get("deck").meters["slip"] += 2
    world.say(
        f"{response.fail.replace('{target}', cargo.label)}"
    )
    world.say(
        f"The tiny boat skidded across the wet boards, and the treasure chest bumped "
        f"hard against the rail."
    )


def lost_end(world: World, hero: Entity, mate: Entity, setting: Setting) -> None:
    hero.memes["sadness"] += 1
    mate.memes["sadness"] += 1
    world.say(
        f"Still, the crew got everyone back to shore safely, and the captain promised "
        f"to keep the snowpan away from slippery tricks after that."
    )
    world.say(
        f"The snow stayed bright on {setting.place}, but the pirate game ended early, "
        f"with soggy boards and very quiet boots."
    )


def tell(setting: Setting, task: CrewTask, target: ObjectCfg, response: Response,
         hero_name: str = "Mara", hero_gender: str = "girl",
         mate_name: str = "Ned", mate_gender: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="captain"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    duckling = world.add(Entity(id="duckling", kind="character", type="thing", role="troublemaker"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    world.add(Entity(id="deck", type="deck", label="the deck"))
    world.add(Entity(id="cargo", type="cargo", label=target.label, flammable=target.flammable))
    snowpan = world.add(Entity(id="snowpan", type="tool", label="snowpan", carries=True, helpful=True))

    setup(world, hero, duckling, mate, setting, task)
    world.para()
    meddle(world, duckling, task)
    attempt(world, hero, task)
    world.para()
    accident(world, hero, world.get("cargo"), task)
    call_help(world, mate)

    severity = task.zone and (1 + delay) or 1
    world.get("cargo").meters["severity"] = float(severity)
    contained = response.power >= severity

    world.para()
    if contained:
        response_scene(world, parent, response, world.get("cargo"), task)
        twist_end(world, hero, duckling, mate, task, setting)
        outcome = "saved"
    else:
        rescue_fail(world, response, world.get("cargo"), task)
        lost_end(world, hero, mate, setting)
        outcome = "lost"

    world.facts.update(
        hero=hero, mate=mate, duckling=duckling, parent=parent, setting=setting,
        task=task, target=target, response=response, outcome=outcome,
        delayed=delay, snowpan=snowpan, contained=contained,
    )
    return world


SETTINGS = {
    "harbor": Setting(id="harbor", place="the harbor", weather="steady north wind", details="icy planks"),
    "island": Setting(id="island", place="the little island", weather="bright frost", details="snowy stones"),
    "cove": Setting(id="cove", place="the cold cove", weather="soft snow", details="a slippery dock"),
}

TASKS = {
    "bridge": CrewTask(
        id="bridge", verb="cross the drift", goal="the treasure crate", danger="soak",
        zone={"deck"}, twist_use="snowpan", tags={"snow", "pirate", "twist"},
    ),
    "rescue": CrewTask(
        id="rescue", verb="reach the dock", goal="the stranded boat", danger="soak",
        zone={"deck"}, twist_use="snowpan", tags={"snow", "pirate", "twist"},
    ),
}

OBJECTS = {
    "crate": ObjectCfg(
        id="crate", label="the treasure crate", phrase="a treasure crate", kind="cargo",
        flammable=True, tags={"cargo", "treasure"},
    ),
    "map": ObjectCfg(
        id="map", label="the map bundle", phrase="a map bundle", kind="cargo",
        flammable=True, tags={"cargo", "paper"},
    ),
}

RESPONSES = {
    "towel": Response(
        id="towel", sense=3, power=2,
        text="grabbed a dry towel and pressed the water away from {target}",
        fail="tried to dry {target} with a towel, but the splash was too wide",
        qa_text="grabbed a dry towel and pressed the water away from {target}",
        tags={"dry", "help"},
    ),
    "bucket": Response(
        id="bucket", sense=4, power=3,
        text="used a bucket to scoop the worst water off {target}",
        fail="used a bucket, but the water kept sloshing back over {target}",
        qa_text="used a bucket to scoop the worst water off {target}",
        tags={"scoop", "help"},
    ),
    "snowpan": Response(
        id="snowpan", sense=5, power=4,
        text="turned the snowpan into a little shovel and packed fresh snow over {target}",
        fail="tried to use the snowpan, but the slip had already grown too fast",
        qa_text="turned the snowpan into a little shovel and packed fresh snow over {target}",
        tags={"snowpan", "twist"},
    ),
    "sail": Response(
        id="sail", sense=2, power=1,
        text="flapped a sail over {target}",
        fail="flapped a sail over {target}, but that did not stop the wet boards",
        qa_text="flapped a sail over {target}",
        tags={"sail"},
    ),
}

SENSE_MIN = 3


@dataclass
class StoryParams:
    setting: str
    task: str
    target: str
    response: str
    hero_name: str
    hero_gender: str
    mate_name: str
    mate_gender: str
    parent: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for task_id in TASKS:
            task = TASKS[task_id]
            for oid, obj in OBJECTS.items():
                if valid_combo(task, obj):
                    combos.append((sid, task_id, oid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale snowworld with a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--target", choices=OBJECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--mate")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("(No story: that response is too silly for a safe tale.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_gender = rng.choice(["girl", "boy"])
    mate_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = args.name or rng.choice(["Mara", "Nina", "Tess", "Jax", "Pip"])
    mate_name = args.mate or rng.choice(["Ned", "Otto", "Rue", "Finn", "Bo"])
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting, task=task, target=target, response=response,
        hero_name=hero_name, hero_gender=hero_gender,
        mate_name=mate_name, mate_gender=mate_gender, parent=parent, delay=delay,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate-tale style story that includes the words "snowpan" and '
        f'"duckling", with a twist ending.',
        f"Tell a snowy pirate adventure where {f['hero'].id} has a snowpan, a "
        f"meddlesome duckling causes trouble, and the crew finds a clever rescue.",
        f'Write a child-friendly story about a pirate crew on snow that uses the '
        f'word "meddlesome" and ends with the snowpan becoming useful.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, mate, duckling, parent = f["hero"], f["mate"], f["duckling"], f["parent"]
    task, target = f["task"], f["target"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, {mate.id}, and a meddlesome duckling on a snowy pirate day."),
        ("Why did the duckling cause trouble?",
         f"The duckling was meddlesome and kept nudging the snowpan as if it were a toy. That tiny push helped start the problem on the deck."),
        ("What was the twist?",
         f"The snowpan that caused trouble also became the tool that fixed the mess. The crew used it to pack snow away from the slippery spot."),
    ]
    if f["outcome"] == "saved":
        qa.append((
            "How did the story end?",
            f"It ended safely, with the cargo saved and the little boat steady again. The snowpan turned from a nuisance into the crew's best help."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended with the crew safe, but the pirate game stopped early because the wet boards were too slippery. The snowpan never got a chance to save the cargo."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["task"].tags) | set(f["target"].tags) | set(f["response"].tags)
    out = []
    knowledge = {
        "snowpan": [("What is a snowpan?",
                     "A snowpan is a made-up little tool for scooping or packing snow. In this story, the crew uses it like a small shovel.")],
        "duckling": [("What is a duckling?",
                      "A duckling is a baby duck. Ducklings are small, fluffy, and love to waddle around and peep.")],
        "twist": [("What is a twist in a story?",
                    "A twist is a surprise turn where something changes in a way you did not expect. It can make the ending feel clever or exciting.")],
        "pirate": [("What do pirates usually do in stories?",
                    "Pirates in stories often sail, search for treasure, and speak in a bold, adventurous way.")],
    }
    for key in ["snowpan", "duckling", "twist", "pirate"]:
        if key in tags or key in {"snowpan", "duckling", "twist", "pirate"}:
            out.extend(knowledge[key])
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    for key, mapping in [("setting", SETTINGS), ("task", TASKS), ("target", OBJECTS), ("response", RESPONSES)]:
        if getattr(params, key) not in mapping:
            raise StoryError(f"(Invalid {key}: {getattr(params, key)!r})")
    world = tell(
        SETTINGS[params.setting], TASKS[params.task], OBJECTS[params.target],
        RESPONSES[params.response], params.hero_name, params.hero_gender,
        params.mate_name, params.mate_gender, params.parent, params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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
    StoryParams(
        setting="harbor", task="bridge", target="crate", response="snowpan",
        hero_name="Mara", hero_gender="girl", mate_name="Ned", mate_gender="boy",
        parent="mother", delay=0,
    ),
    StoryParams(
        setting="cove", task="rescue", target="map", response="bucket",
        hero_name="Pip", hero_gender="boy", mate_name="Rue", mate_gender="girl",
        parent="father", delay=1,
    ),
]


ASP_RULES = r"""
% A task is valid when the danger is water-like and the target is cargo that can get wet.
valid(T, O) :- task(T), object(O), soak_danger(T), cargo(O), flammable(O).

% Responses are sensible only if their common-sense score meets the minimum.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

% Ending model: a response contains the mess when its power beats the delay.
saved(R, D) :- response(R), power(R, P), delay(D), P >= D + 1.
lost(R, D) :- response(R), power(R, P), delay(D), P < D + 1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("soak_danger", tid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.kind == "cargo":
            lines.append(asp.fact("cargo", oid))
        if o.flammable:
            lines.append(asp.fact("flammable", oid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set((t, o) for _, t, o in valid_combos()):
        rc = 1
        print("MISMATCH: ASP gate differs from Python.")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH: ASP sensible responses differ from Python.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, task=None, target=None, response=None,
            name=None, mate=None, parent=None, delay=None,
        ), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: verify passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Snowy pirate tale with a meddlesome duckling and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--target", choices=OBJECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--mate")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("(No story: that response is too silly for this tale.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_gender = rng.choice(["girl", "boy"])
    mate_gender = "boy" if hero_gender == "girl" else "girl"
    return StoryParams(
        setting=setting,
        task=task,
        target=target,
        response=response,
        hero_name=args.name or rng.choice(["Mara", "Pip", "Nell", "Jory"]),
        hero_gender=hero_gender,
        mate_name=args.mate or rng.choice(["Ned", "Rue", "Bo", "Tess"]),
        mate_gender=mate_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        delay=args.delay if args.delay is not None else rng.randint(0, 2),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show saved/2.\n#show lost/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible task/object pairs")
        for t, o in asp_valid_combos():
            print(f"  {t} {o}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} & {p.mate_name}: {p.setting}, {p.task}, {outcome_of(p)}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
