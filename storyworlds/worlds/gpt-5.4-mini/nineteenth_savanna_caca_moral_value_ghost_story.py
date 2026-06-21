#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nineteenth_savanna_caca_moral_value_ghost_story.py
==================================================================================

A small storyworld about a spooky night on the savanna, where a child learns a
moral value: honesty and kindness can quiet fear better than cruelty.

The seed words are intentionally woven into the world:
- nineteenth: the night / day marker of the haunting
- savanna: the open setting
- caca: a childish word used for a mean prank and a messy scare

This script follows the storyworld contract:
- standalone stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp

The world is simulated with typed entities, physical meters, and emotional memes.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
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
class Setting:
    id: str
    place: str
    dark_place: str
    mood: str
    allows: set[str] = field(default_factory=set)

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
class Haunt:
    id: str
    name: str
    sound: str
    sign: str
    moral: str
    eerie: str
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
class Trouble:
    id: str
    action: str
    noun: str
    effect: str
    shame: str
    risk: int
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
class Comfort:
    id: str
    label: str
    phrase: str
    glow: str
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
class Response:
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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["haunted"] >= THRESHOLD and (("fear",) not in world.fired):
            world.fired.add(("fear",))
            for ent in list(world.entities.values()):
                if ent.kind == "character":
                    ent.memes["fear"] += 1
            out.append("__fear__")
    return out


def _r_smell(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["dirty"] >= THRESHOLD and ("smell", e.id) not in world.fired:
            world.fired.add(("smell", e.id))
            out.append(f"The air carried a caca smell near {e.label or e.id}.")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("smell", "physical", _r_smell)]


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


def reasonableness_ok(haunt: Haunt, trouble: Trouble) -> bool:
    return "ghost" in haunt.tags and "mess" in trouble.tags


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(trouble: Trouble, delay: int) -> int:
    return trouble.risk + delay


def is_contained(response: Response, trouble: Trouble, delay: int) -> bool:
    return response.power >= fire_severity(trouble, delay)


def predict_scare(world: World, trouble_id: str) -> dict:
    sim = world.copy()
    _do_trouble(sim, sim.get(trouble_id), narrate=False)
    return {
        "haunted": sim.get(trouble_id).meters["haunted"] >= THRESHOLD,
        "fear": sum(e.memes["fear"] for e in sim.entities.values() if e.kind == "character"),
    }


def _do_trouble(world: World, ent: Entity, narrate: bool = True) -> None:
    ent.meters["dirty"] += 1
    ent.meters["haunted"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, friend: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"On the nineteenth night over the {setting.place}, {child.id} and {friend.id} "
        f"walked beside the tall grass while the moon made the world look pale and still."
    )
    world.say(
        f"They whispered about the old path near {setting.dark_place}, where the wind "
        f"seemed to breathe like a ghost story."
    )


def lure(world: World, haunt: Haunt, child: Entity) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Then they heard a soft {haunt.sound} from the dark. A lonely shape drifted "
        f"near the reeds, and {child.id} said it must be a ghost with a secret."
    )


def prank(world: World, child: Entity, trouble: Trouble) -> None:
    child.memes["mischief"] += 1
    world.say(
        f"{child.id} grinned and pointed at a muddy clump. 'Caca!' {child.pronoun()} "
        f"laughed, hoping the joke would scare {child.pronoun('object')} friends."
    )
    world.say(
        f"{child.id} tried to {trouble.action}, and the little trick looked mean rather than funny."
    )


def warning(world: World, friend: Entity, child: Entity, haunt: Haunt, trouble: Trouble) -> None:
    pred = predict_scare(world, "trouble")
    friend.memes["kindness"] += 1
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f"{friend.id} held up a hand. 'If you make fun of that, it will not feel brave. "
        f"Ghosts in stories can teach us a moral value too: be gentle, tell the truth, "
        f"and do not use a nasty joke to hurt someone.'"
    )
    if pred["haunted"] and trouble.effect:
        world.say(
            f"{friend.id} also noticed the place would become {trouble.effect}, and that would only make the night messier."
        )


def defy(world: World, child: Entity, trouble: Trouble) -> None:
    child.memes["defiance"] += 1
    world.say(f"Still, {child.id} went ahead anyway, because the joke felt exciting for one breath.")


def make_mess(world: World, trouble_ent: Entity, trouble: Trouble) -> None:
    _do_trouble(world, trouble_ent)
    world.say(
        f"The prank landed badly. The ground turned {trouble.effect}, and the caca smell drifted into the grass."
    )


def ghost_reply(world: World, haunt: Haunt, child: Entity, friend: Entity) -> None:
    world.say(
        f"From the dark, the ghostly whisper came again: '{haunt.sign}' said the wind, not to scare them, but to remind them."
    )
    world.say(
        f"{child.id} and {friend.id} froze, and then they understood the lesson: a joke that makes a mess or hurts a friend is not kind."
    )


def clean_up(world: World, adult: Entity, child: Entity, friend: Entity, comfort: Comfort) -> None:
    child.memes["relief"] += 1
    friend.memes["relief"] += 1
    child.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f"Later, {adult.label_word.capitalize()} came with {comfort.phrase} that {comfort.glow}, "
        f"and together they cleaned the spot until the savanna looked calm again."
    )
    world.say(
        f"{adult.label_word.capitalize()} said, 'A good heart is stronger than a mean prank. "
        f"If you want to be brave, be honest and help instead.'"
    )
    world.say(
        f"{child.id} nodded, ashamed but wiser, while {friend.id} watched the moon rise over the grass."
    )


def ending_image(world: World, setting: Setting, haunt: Haunt, child: Entity, friend: Entity, comfort: Comfort) -> None:
    world.say(
        f"By the end, the nineteenth night felt less spooky. The savanna was quiet, the ghost story had turned into a lesson, "
        f"and even the wind seemed kinder as {child.id} walked home with {friend.id} and {comfort.label} held close."
    )


def tell(setting: Setting, haunt: Haunt, trouble: Trouble, comfort: Comfort, response: Response,
         child_name: str = "Mina", child_gender: str = "girl",
         friend_name: str = "Kofi", friend_gender: str = "boy",
         adult_type: str = "mother", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the adult"))
    trouble_ent = world.add(Entity(id="trouble", type="thing", label=trouble.noun))
    comfort_ent = world.add(Entity(id=comfort.id, type="thing", label=comfort.label))
    opening(world, child, friend, setting)
    world.para()
    lure(world, haunt, child)
    warning(world, friend, child, haunt, trouble)
    world.para()
    defy(world, child, trouble)
    make_mess(world, trouble_ent, trouble)
    ghost_reply(world, haunt, child, friend)
    severity = fire_severity(trouble, delay)
    contained = is_contained(response, trouble, delay)
    world.para()
    if contained:
        world.say(
            f"{adult.label_word.capitalize()} arrived calmly and {response.text.replace('{trouble}', trouble.noun)}."
        )
        clean_up(world, adult, child, friend, comfort)
        ending_image(world, setting, haunt, child, friend, comfort)
    else:
        world.say(
            f"{adult.label_word.capitalize()} rushed in and {response.fail.replace('{trouble}', trouble.noun)}."
        )
        world.say(
            f"The night stayed scary for a little while, but the family got everyone safe and washed the dirt away."
        )
        world.say(
            f"Afterward, {child.id} understood that the ghostly warning had been a moral one: mean tricks do not make anyone proud."
        )
        ending_image(world, setting, haunt, child, friend, comfort)
    world.facts.update(
        child=child, friend=friend, adult=adult, setting=setting, haunt=haunt,
        trouble=trouble, comfort=comfort, response=response, severity=severity,
        contained=contained, delay=delay, lesson=True
    )
    return world


SETTINGS = {
    "savanna": Setting("savanna", "the savanna", "the tall grass near the old path", "wide and moonlit", {"ghost"}),
    "camp": Setting("camp", "the camp", "the fire circle", "small and sleepy", {"ghost"}),
    "watering_hole": Setting("watering_hole", "the watering hole", "the reeds by the water", "still and echoing", {"ghost"}),
}

HAUNTS = {
    "moon_whisper": Haunt("moon_whisper", "the moon whisper", "whispering", "hush", "kindness", "soft", {"ghost", "moral"}),
    "lantern_ghost": Haunt("lantern_ghost", "the lantern ghost", "fluttering", "glow", "honesty", "gentle", {"ghost", "moral"}),
}

TROUBLES = {
    "caca_prank": Trouble("caca_prank", "smear caca on a rock", "the muddy clump", "dirty and gross", "mean", 2, {"mess"}),
    "fake_howl": Trouble("fake_howl", "make a fake howl", "the empty night", "more frightened", "mean", 1, {"mess"}),
}

COMFORTS = {
    "blanket": Comfort("blanket", "blanket", "a warm blanket", "glowed softly", {"comfort"}),
    "lantern": Comfort("lantern", "lantern", "a small lantern", "shone warmly", {"comfort"}),
}

RESPONSES = {
    "soft_tone": Response("soft_tone", 3, 3, "spoke softly and wiped the mess away with a cloth", "spoke too sharply, but the family still cleaned the mess", "spoke softly and wiped the mess away", {"kind"}),
    "tell_truth": Response("tell_truth", 3, 4, "told the truth and cleaned the spot with calm hands", "tried to blame the wind, but the mess still needed cleaning", "told the truth and cleaned the spot", {"kind"}),
    "apologize": Response("apologize", 2, 2, "apologized and helped scrub the dirt from the grass", "apologized too late to stop the worry", "apologized and helped scrub the dirt from the grass", {"kind"}),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    haunt: str
    trouble: str
    comfort: str
    response: str
    child: str
    child_gender: str
    friend: str
    friend_gender: str
    adult: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for hid, h in HAUNTS.items():
            for tid, t in TROUBLES.items():
                if reasonableness_ok(h, t):
                    combos.append((sid, hid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world with a moral lesson on the savanna.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--haunt", choices=HAUNTS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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
    pool = GIRLS if gender == "girl" else BOYS
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.haunt and args.trouble:
        if not reasonableness_ok(HAUNTS[args.haunt], TROUBLES[args.trouble]):
            raise StoryError("(No story: this ghost and trouble do not fit the moral-value ghost story world.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.haunt is None or c[1] == args.haunt)
              and (args.trouble is None or c[2] == args.trouble)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, haunt, trouble = rng.choice(sorted(combos))
    comfort = args.comfort or rng.choice(sorted(COMFORTS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or _pick_name(rng, child_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=child)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(setting, haunt, trouble, comfort, response, child, child_gender, friend, friend_gender, adult)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short ghost story for a child on the savanna that teaches a moral value.",
        f"Tell a spooky but gentle story where {f['child'].id} hears a ghost sound on the nineteenth night and learns not to use a caca prank.",
        f"Write a moral-value ghost story using the words nineteenth, savanna, and caca.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, friend, adult = f["child"], f["friend"], f["adult"]
    haunt, trouble, comfort = f["haunt"], f["trouble"], f["comfort"]
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {friend.id} on the savanna, and the adult who helps them understand the spooky night."
        ),
        QAItem(
            question="Why did the friend warn about the prank?",
            answer=(
                f"{friend.id} could tell that the caca prank would make the night mean instead of funny. "
                f"{friend.id} wanted the story to stay kind, so {friend.pronoun()} chose honesty and helped stop the mess."
            )
        ),
        QAItem(
            question="What moral value does the ghost story teach?",
            answer=(
                f"It teaches kindness and honesty. The ghostly warning shows that being gentle and telling the truth is better than doing a nasty prank."
            )
        ),
    ]
    if f.get("contained"):
        items.append(QAItem(
            question="How did the adult help at the end?",
            answer=(
                f"{adult.label_word.capitalize()} came calmly and cleaned the mess, then talked about the right choice. "
                f"That made the fear smaller and helped the children learn from what happened."
            )
        ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["haunt"].tags) | set(f["trouble"].tags) | set(f["comfort"].tags)
    out: list[QAItem] = []
    if "ghost" in tags:
        out.append(QAItem("What is a ghost story?", "A ghost story is a spooky tale about strange sounds, shadows, or spirits. It can still teach a good lesson."))
    if "moral" in tags:
        out.append(QAItem("What is a moral value?", "A moral value is a good way to act, like being kind, honest, or helpful. Stories often use them to teach children what matters."))
    if "mess" in tags:
        out.append(QAItem("What does caca mean in a child's story?", "It is a silly childish word for something gross or dirty. In this story it marks a mean prank rather than a kind joke."))
    if "comfort" in tags:
        out.append(QAItem("What is a comfort object?", "A comfort object is something soft or familiar, like a blanket or lantern, that helps children feel safe."))
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(r[0] if isinstance(r, tuple) and r else str(r) for r in world.fired))}")
    return "\n".join(lines)


def explain_rejection(haunt: Haunt, trouble: Trouble) -> str:
    return f"(No story: {haunt.name} and {trouble.noun} do not make a good moral ghost-story conflict.)"


GIRLS = ["Mina", "Asha", "Nia", "Zuri", "Lina", "Tia"]
BOYS = ["Kofi", "Jalen", "Timo", "Rafi", "Niko", "Omar"]

CURATED = [
    StoryParams("savanna", "moon_whisper", "caca_prank", "blanket", "tell_truth", "Mina", "girl", "Kofi", "boy", "mother", 0),
    StoryParams("camp", "lantern_ghost", "fake_howl", "lantern", "apologize", "Jalen", "boy", "Nia", "girl", "father", 0),
    StoryParams("watering_hole", "moon_whisper", "caca_prank", "blanket", "soft_tone", "Asha", "girl", "Rafi", "boy", "mother", 1),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for hid, h in HAUNTS.items():
        lines.append(asp.fact("haunt", hid))
        for t in h.tags:
            lines.append(asp.fact("tag", hid, t))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        for tg in t.tags:
            lines.append(asp.fact("tag", tid, tg))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
good_conflict(H, T) :- tag(H, ghost), tag(T, mess).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, H, T) :- setting(S), haunt(H), trouble(T), good_conflict(H, T).
"""


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
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    if {r.id for r in sensible_responses()} == set(asp_sensible()):
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        _ = generate(resolve_params(argparse.Namespace(
            setting=None, haunt=None, trouble=None, comfort=None, response=None,
            child=None, child_gender=None, friend=None, friend_gender=None,
            adult=None, seed=None, all=False, trace=False, qa=False, json=False,
            asp=False, verify=False, show_asp=False), random.Random(7)))
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"FAIL: generation smoke test crashed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A spooky savanna ghost-story world with a moral lesson.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--haunt", choices=HAUNTS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], HAUNTS[params.haunt], TROUBLES[params.trouble],
        COMFORTS[params.comfort], RESPONSES[params.response],
        params.child, params.child_gender, params.friend, params.friend_gender,
        params.adult, params.delay,
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.haunt is None or c[1] == args.haunt)
              and (args.trouble is None or c[2] == args.trouble)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, haunt, trouble = rng.choice(sorted(combos))
    comfort = args.comfort or rng.choice(sorted(COMFORTS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(GIRLS if child_gender == "girl" else BOYS)
    friend_pool = GIRLS if friend_gender == "girl" else BOYS
    friend = args.friend or rng.choice([n for n in friend_pool if n != child])
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(setting, haunt, trouble, comfort, response, child, child_gender, friend, friend_gender, adult)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for setting, haunt, trouble in asp_valid_combos():
            print(f"{setting:14} {haunt:14} {trouble}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and {p.friend}: {p.setting} / {p.haunt} / {p.trouble}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
