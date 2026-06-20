#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/perceptive_bobbin_bravery_sound_effects_space_adventure.py
=========================================================================================

A standalone storyworld for a small space-adventure tale about a perceptive child,
a bobbin, bravery, and sound effects.

Premise:
- Two little crew-mates are exploring a tiny spaceship or moon base.
- A bobbin is needed for a repair.
- Strange sound effects hint at a problem before anyone sees it.
- A perceptive child notices the real danger.
- Bravery means calling out, helping, and fixing the problem safely.
- The ending image proves the mission is back on track.

This script follows the Storyweavers storyworld contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python validity gate and an inline ASP twin
- emits three Q&A sets from world state

Run:
    python storyworlds/worlds/gpt-5.4-mini/perceptive_bobbin_bravery_sound_effects_space_adventure.py
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



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
    ship_prop: str
    goal: str
    dark_place: str
    adventurous_title: str
    crew_word: str
    ending: str

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
class Bobbin:
    id: str
    label: str
    phrase: str
    use: str
    sound: str
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
class SpaceHazard:
    id: str
    label: str
    danger: str
    sound_hint: str
    can_fail: bool = True
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


def _r_alert(world: World) -> list[str]:
    out: list[str] = []
    if world.get("alarm").meters["danger"] >= THRESHOLD:
        sig = ("alert", "alarm")
        if sig not in world.fired:
            world.fired.add(sig)
            for ch in world.characters():
                ch.memes["worry"] += 1
            out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("alert", "social", _r_alert)]


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


def danger_matches(hazard: SpaceHazard, bobbin: Bobbin) -> bool:
    return hazard.can_fail and "repair" in bobbin.tags


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for hid, hazard in HAZARDS.items():
            for bid, bobbin in BOBBINS.items():
                if danger_matches(hazard, bobbin):
                    combos.append((theme, hid, bid))
    return combos


def severity(hazard: SpaceHazard, delay: int) -> int:
    return 1 + delay


def is_contained(response: Response, hazard: SpaceHazard, delay: int) -> bool:
    return response.power >= severity(hazard, delay)


def _do_hazard(world: World, hazard: SpaceHazard) -> None:
    world.get("alarm").meters["danger"] += 1
    world.get("alarm").meters["buzzing"] += 1
    propagate(world, narrate=False)


def setup(world: World, theme: Theme, hero: Entity, friend: Entity) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a quiet afternoon aboard the {theme.scene}, {hero.id} and {friend.id} "
        f"were exploring like tiny space crew. {theme.ship_prop}"
    )
    world.say(
        f'"{theme.adventurous_title} {hero.id} and {friend.id}!" {hero.id} said. '
        f'"Let\'s reach {theme.goal}!"'
    )


def need_repair(world: World, theme: Theme, hazard: SpaceHazard, bobbin: Bobbin) -> None:
    world.say(
        f"But near {theme.dark_place}, something was not right. "
        f'{hazard.sound_hint} came from the wall panel, soft at first and then louder.'
    )
    world.say(
        f'{friend_name(world)} listened. "We need the {bobbin.label}," {friend_name(world)} said. '
        f'"It fixes the little spool inside the repair hatch."'
    )


def friend_name(world: World) -> str:
    return world.facts["friend"].id


def tempt(world: World, hero: Entity, bobbin: Bobbin) -> None:
    hero.memes["bravado"] += 1
    world.say(
        f'{hero.id} held up {bobbin.phrase}. "I know! {bobbin.sound} we can use '
        f'this {bobbin.label} and make the hatch turn."'
    )
    world.say("For one bright second, the idea felt like a daring mission trick.")


def warn(world: World, friend: Entity, hero: Entity, bobbin: Bobbin, hazard: SpaceHazard) -> None:
    friend.memes["perceptive"] += 1
    world.say(
        f'{friend.id} was perceptive. {friend.pronoun().capitalize()} leaned closer, '
        f'heard the {hazard.sound_hint} again, and frowned. "{hero.id}, that sound means '
        f"something is loose, not ready. We should look first."
    )


def defy(world: World, hero: Entity, bobbin: Bobbin) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"{bobbin.sound}!" {hero.id} said, and reached for the panel anyway.'
    )


def brave_choice(world: World, friend: Entity, hero: Entity) -> None:
    friend.memes["bravery"] += 1
    world.say(
        f"But {friend.id} took a brave breath and called, "
        f'"Stop! I think the bobbin belongs in the repair slot, not in our hands."'
    )


def alarm(world: World, hazard: SpaceHazard) -> None:
    world.say(
        f"Then {hazard.sound_hint} turned into a sharp {hazard.sound} and the alarm light blinked red."
    )


def fix(world: World, response: Response, hazard: SpaceHazard) -> None:
    world.get("alarm").meters["danger"] = 0.0
    body = response.text.replace("{hazard}", hazard.label)
    world.say(f"The captain came running and {body}.")
    world.say(
        f"The red light faded, the panel hummed, and the little ship grew calm again."
    )


def fail_fix(world: World, response: Response, hazard: SpaceHazard) -> None:
    world.get("alarm").meters["danger"] += 1
    body = response.fail.replace("{hazard}", hazard.label)
    world.say(f"The captain came running and {body}.")
    world.say(
        f"The noise got bigger, and the crew had to back away from the sparking panel."
    )


def lesson(world: World, captain: Entity, hero: Entity, friend: Entity, bobbin: Bobbin) -> None:
    for ch in (hero, friend):
        ch.memes["fear"] = 0.0
        ch.memes["relief"] += 1
        ch.memes["bravery"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then the captain knelt down and smiled. "
        f'"That was brave," {captain.pronoun()} said. "A bobbin is for a repair slot, '
        f'and you were right to call me before the problem grew."'
    )
    world.say(
        f'"We promise," whispered {hero.id} and {friend.id}.'
    )


def ending(world: World, theme: Theme, hero: Entity, friend: Entity) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"The next starry hour, the {theme.crew_word} floated on in their little ship. "
        f"{hero.id} held the flashlight, {friend.id} kept the map, and the bobbin sat safely "
        f"in the repair box where it belonged."
    )
    world.say(
        f"This time the mission went on -- bright, brave, and sound-effect free except "
        f"for a happy {theme.ending}."
    )


def tell(theme: Theme, bobbin: Bobbin, hazard: SpaceHazard, response: Response,
         hero_name: str = "Mira", hero_gender: str = "girl",
         friend_name_: str = "Toby", friend_gender: str = "boy",
         captain_type: str = "father", delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(friend_name_, kind="character", type=friend_gender, role="friend"))
    captain = world.add(Entity("Captain", kind="character", type=captain_type, role="captain"))
    alarm_ent = world.add(Entity("alarm", label="the alarm panel"))
    world.facts.update(hero=hero, friend=friend, captain=captain, theme=theme,
                       bobbin=bobbin, hazard=hazard, response=response, delay=delay)

    setup(world, theme, hero, friend)
    world.para()
    need_repair(world, theme, hazard, bobbin)
    tempt(world, hero, bobbin)
    warn(world, friend, hero, bobbin, hazard)
    brave_choice(world, friend, hero)
    defy(world, hero, bobbin)
    alarm(world, hazard)
    contained = is_contained(response, hazard, delay)
    if contained:
        fix(world, response, hazard)
        lesson(world, captain, hero, friend, bobbin)
    else:
        fail_fix(world, response, hazard)
        lesson(world, captain, hero, friend, bobbin)
    world.para()
    ending(world, theme, hero, friend)
    world.facts["contained"] = contained
    return world


THEMES = {
    "lunar": Theme("lunar", "Moonbase Lantern-9", "The tiny ship bobbed at the docking ring, and a silver map blinked on the wall.", "the crater on the map", "the shadowy repair hatch", "Space Crew", "crew", "soft whoosh"),
    "asteroid": Theme("asteroid", "Asteroid Station Pop-3", "The corridor hummed, the ceiling gleamed, and a paper star-chart floated near the desk.", "the bright cargo bay", "the rattling maintenance tunnel", "Star Cadets", "crew", "cheerful beep"),
    "comet": Theme("comet", "Comet Class Cabin", "The cabin windows showed a tail of glittering ice, and a toy rover slept by the console.", "the observation dome", "the blinking service nook", "Rocket Scouts", "crew", "happy ping"),
}

BOBBINS = {
    "silver": Bobbin("silver", "silver bobbin", "a silver bobbin", "repair a loose spool", "clink-clink", {"repair", "metal"}),
    "red": Bobbin("red", "red bobbin", "a red bobbin", "repair a loose spool", "zip-zip", {"repair", "cloth"}),
    "blue": Bobbin("blue", "blue bobbin", "a blue bobbin", "repair a loose spool", "whirr-whirr", {"repair", "thread"}),
}

HAZARDS = {
    "rattle": SpaceHazard("rattle", "rattle in the wall", "something was loose", "rattle-rattle", True, {"sound"}),
    "click": SpaceHazard("click", "click in the panel", "a tiny part was sticking", "click-click", True, {"sound"}),
    "hum": SpaceHazard("hum", "hum in the hatch", "the hatch was not seated right", "hmmmmm", True, {"sound"}),
}

RESPONSES = {
    "tighten": Response("tighten", 3, 2,
                        "tightened the hatch screws and set the {hazard} right",
                        "tightened the screws, but the {hazard} was already too wild",
                        "tightened the hatch screws and set the problem right",
                        {"repair"}),
    "replace": Response("replace", 3, 3,
                        "replaced the broken spacer and calmed the {hazard}",
                        "replaced one piece, but the {hazard} still shook and sparked",
                        "replaced the broken spacer and calmed the problem",
                        {"repair"}),
    "patch": Response("patch", 2, 1,
                      "patched the crack with tape",
                      "patched the crack, but the {hazard} kept getting worse",
                      "patched the crack with tape",
                      {"repair"}),
}

GIRL_NAMES = ["Mira", "Nia", "Zora", "Ivy", "Lena", "Cleo"]
BOY_NAMES = ["Toby", "Jace", "Arlo", "Finn", "Pax", "Rowan"]


@dataclass
@dataclass
class StoryParams:
    theme: str
    bobbin: str
    hazard: str
    response: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    captain: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure storyworld about a perceptive child, a bobbin, bravery, and sound effects.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--bobbin", choices=BOBBINS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["father", "mother"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("(No story: that response is too weak for a brave space repair.)")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.bobbin is None or c[2] == args.bobbin)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, hazard, bobbin = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    friend = args.friend or rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    captain = args.captain or rng.choice(["father", "mother"])
    delay = args.delay
    return StoryParams(theme, bobbin, hazard, response, name, gender, friend, friend_gender, captain, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], BOBBINS[params.bobbin], HAZARDS[params.hazard], RESPONSES[params.response],
                 params.hero_name, params.hero_gender, params.friend_name, params.friend_gender, params.captain, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-facing space adventure story that includes the words "{f["hero"].id}", "{f["bobbin"].label}", and "perceptive".',
        f"Tell a story where {f['friend'].id} is perceptive about a strange sound, {f['hero'].id} is brave, and a bobbin helps fix a spaceship problem.",
        f'Write a tiny space repair story with sound effects and a calm ending after a brave call for help.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, captain, bobbin, hazard = f["hero"], f["friend"], f["captain"], f["bobbin"], f["hazard"]
    qa = [
        ("Who noticed the problem first?",
         f"{friend.id} noticed it first because {friend.pronoun()} was perceptive and listened to the strange sound. {friend.id} heard that the ship was not safe yet."),
        ("What did the children want to do with the bobbin?",
         f"They thought the bobbin could help the repair hatch turn, because it looked useful and shiny. But it was not the right thing to hold in their hands.") ,
        ("How was bravery shown in the story?",
         f"Bravery showed up when {friend.id} spoke up and asked for help instead of pretending the noise was nothing. {hero.id} was brave too because {hero.id} stayed close and helped fix the problem safely."),
    ]
    if f.get("contained"):
        qa.append(("How did the problem end?",
                   f"The captain fixed the panel, the alarm went quiet, and the ship calmed down. The little crew could keep their space adventure going." ))
        qa.append(("Why was the captain happy?",
                   f"The captain was happy because the children called for help early. That kept the bobbin in the repair box and stopped the problem from getting worse."))
    else:
        qa.append(("How did the problem end?",
                   f"The captain still fixed the panel, but it took longer because the noise had grown bigger. The children learned to call for help sooner next time."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["bobbin"].tags) | set(f["hazard"].tags) | {"bravery", "sound_effects"}
    out = []
    knowledge = {
        "repair": [("What is a bobbin for?", "A bobbin is a small object that can hold thread or be part of a machine. In this story, it belongs in the repair slot, not as a toy.")],
        "sound": [("What do sound effects do in a story?", "Sound effects help you imagine what is happening by copying the noises you would hear. They can make a space story feel lively and exciting.")],
        "bravery": [("What does bravery mean?", "Bravery means doing the right thing even when you feel nervous. It can mean speaking up, asking for help, or staying calm.")],
    }
    order = ["sound", "repair", "bravery"]
    for key in order:
        if key in tags:
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
        if bits:
            lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("lunar", "silver", "rattle", "tighten", "Mira", "girl", "Toby", "boy", "father", 0),
    StoryParams("asteroid", "red", "click", "replace", "Nia", "girl", "Arlo", "boy", "mother", 1),
    StoryParams("comet", "blue", "hum", "patch", "Pax", "boy", "Cleo", "girl", "father", 2),
]


def explain_rejection() -> str:
    return "(No story: this space repair would not have a real sound problem that the bobbin can help fix.)"


ASP_RULES = r"""
valid(T, H, B) :- theme(T), hazard(H), bobbin(B), hazard_ok(H, B).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
outcome(contained) :- chosen_response(R), chosen_hazard(H), chosen_delay(D), power(R, P), severity(H, D, V), P >= V.
outcome(failed) :- chosen_response(R), chosen_hazard(H), chosen_delay(D), power(R, P), severity(H, D, V), P < V.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for b in BOBBINS:
        lines.append(asp.fact("bobbin", b))
        lines.append(asp.fact("hazard_ok", "rattle", b))
        lines.append(asp.fact("hazard_ok", "click", b))
        lines.append(asp.fact("hazard_ok", "hum", b))
    for h in HAZARDS:
        lines.append(asp.fact("hazard", h))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("chosen_hazard", params.hazard),
        asp.fact("chosen_delay", params.delay),
        asp.fact("severity", params.hazard, params.delay, severity(HAZARDS[params.hazard], params.delay)),
    ])
    model = asp.one_model(asp_program(extra=extra, show="#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    # smoke test ordinary generation
    try:
        sample = generate(resolve_params(argparse.Namespace(theme=None, bobbin=None, hazard=None, response=None, name=None, friend=None, gender=None, friend_gender=None, captain=None, delay=0), random.Random(7)))
        assert sample.story
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    cases = [p for p in CURATED]
    bad = sum(1 for p in cases if asp_outcome(p) not in {"contained", "failed"})
    if bad:
        rc = 1
        print("MISMATCH in outcomes.")
    else:
        print("OK: outcome model exercised.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld about a perceptive child, a bobbin, bravery, and sound effects.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--bobbin", choices=BOBBINS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("(No story: that response is too weak for this space repair.)")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.bobbin is None or c[2] == args.bobbin)
              and (args.hazard is None or c[1] == args.hazard)]
    if not combos:
        raise StoryError(explain_rejection())
    theme, hazard, bobbin = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    friend = args.friend or rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    captain = args.captain or rng.choice(["mother", "father"])
    return StoryParams(theme, bobbin, hazard, response, name, gender, friend, friend_gender, captain, args.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], BOBBINS[params.bobbin], HAZARDS[params.hazard], RESPONSES[params.response],
                 params.hero_name, params.hero_gender, params.friend_name, params.friend_gender, params.captain, params.delay)
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
        print(asp_program(show="#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
        if args.all:
            header = f"### {sample.params.hero_name} and {sample.params.friend_name}: {sample.params.theme}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def story_qa(world: World) -> list[tuple[str, str]]:
    return story_qa(world)


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return world_knowledge_qa(world)


def generation_prompts(world: World) -> list[str]:
    return generation_prompts(world)
if __name__ == "__main__":
    main()
