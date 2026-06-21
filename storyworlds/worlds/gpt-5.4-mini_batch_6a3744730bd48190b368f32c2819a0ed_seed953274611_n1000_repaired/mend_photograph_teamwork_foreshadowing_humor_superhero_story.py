#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mend_photograph_teamwork_foreshadowing_humor_superhero_story.py
===============================================================================================

A small superhero storyworld about a young hero team that must mend a broken
photograph before a community photo day. The world emphasizes teamwork,
foreshadowing, and a playful superhero tone.

Seed words:
- mend
- photograph
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class TeamMember:
    id: str
    type: str
    role: str
    power: str
    humor_style: str
    can_mend: bool = False
    can_snap: bool = False
    can_hold: bool = False
    can_calm: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    hero: str
    hero_type: str
    sidekick: str
    sidekick_type: str
    mentor: str
    mentor_type: str
    setting: str
    broken_item: str
    photo_goal: str
    humor_bit: str
    rescue_tool: str
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


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    light: str
    weather: str
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
class BrokenItem:
    id: str
    label: str
    important: str
    damage: str
    can_mend: bool = True
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
class Tool:
    id: str
    label: str
    verb: str
    flourish: str
    power: int
    sense: int
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


SETTINGS = {
    "rooftop": Setting("rooftop", "the rooftop", "the wind-bright rooftop", "sun-glint", "clear"),
    "museum": Setting("museum", "the museum hall", "the quiet hall by the statue", "lamp-glow", "still"),
    "street": Setting("street", "the city street", "the sidewalk under the billboard", "neon", "breezy"),
}

BROKEN_ITEMS = {
    "photograph": BrokenItem("photograph", "photograph", "photo wall", "a ripped corner and a tear across the middle"),
    "poster": BrokenItem("poster", "poster", "poster frame", "a bent edge and a crease"),
    "team_photo": BrokenItem("team_photo", "team photograph", "hero archive", "a torn seam and a missing corner"),
}

TOOLS = {
    "tape": Tool("tape", "sticker tape", "tape", "hummed like a tiny silver snake", 2, 2, {"mend"}),
    "glue": Tool("glue", "craft glue", "glue", "smelled like apples and patience", 3, 3, {"mend"}),
    "stapler": Tool("stapler", "mini stapler", "staple", "clicked like a tiny robot jaw", 1, 1, {"mend"}),
    "magnifier": Tool("magnifier", "magnifier", "inspect", "made every crumb look dramatic", 0, 1, {"inspect"}),
}


def hazard_at_risk(item: BrokenItem) -> bool:
    return item.can_mend


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for bid, item in BROKEN_ITEMS.items():
            for tid, tool in TOOLS.items():
                if item.can_mend and tool.sense >= 2:
                    out.append((sid, bid, tid))
    return out


def best_tool() -> Tool:
    return max(TOOLS.values(), key=lambda t: (t.sense, t.power))


def repair_needed(item: BrokenItem) -> bool:
    return item.can_mend


def repair_success(tool: Tool, item: BrokenItem) -> bool:
    return tool.power >= 2 and item.can_mend


def setting_line(setting: Setting) -> str:
    return f"{setting.place.capitalize()} shone under {setting.light}, and the air felt ready for action."


def foreshadow(world: World, mentor: Entity, item: Entity) -> None:
    mentor.memes["mystery"] += 1
    world.say(
        f"{mentor.id} pointed at the torn {item.label_word} and said, "
        f'"That split looks suspiciously like trouble."'
    )
    world.say(
        "At first, the heroes laughed, because the torn edge looked a bit like a cape that had lost an argument."
    )


def reveal_need(world: World, hero: Entity, sidekick: Entity, item: Entity, setting: Setting) -> None:
    hero.memes["concern"] += 1
    sidekick.memes["concern"] += 1
    world.say(
        f"In {setting.place}, the team found the broken {item.label_word}. "
        f"{hero.id} gasped, and {sidekick.id} said, "
        f'"We cannot let the city see the scrapbook of doom."'
    )
    world.say(
        f"The old photograph was supposed to guide {item.important}, so if it stayed broken, the whole display would look sad."
    )


def teamwork_plan(world: World, hero: Entity, sidekick: Entity, mentor: Entity, tool: Tool, item: Entity) -> None:
    hero.memes["teamwork"] += 1
    sidekick.memes["teamwork"] += 1
    world.say(
        f'{hero.id} held the torn {item.label_word}, {sidekick.id} lined up the edges, '
        f'and {mentor.id} passed over {tool.label}. "{tool.flourish}," {mentor.id} said.'
    )


def mend_item(world: World, tool: Tool, item: Entity) -> None:
    item.meters["mended"] += 1
    item.meters["neat"] += 1
    world.say(
        f"{tool.label.capitalize()} went to work, and soon the tear was mended. "
        f"The crack became a neat line instead of a dramatic disaster."
    )


def humor(world: World, hero: Entity, sidekick: Entity, bit: str) -> None:
    world.say(
        f"{sidekick.id} made a face and declared, \"I am too powerful for paper enemies.\" "
        f"{hero.id} snorted, because the torn {bit} looked less scary once everyone had a job."
    )


def finale(world: World, hero: Entity, sidekick: Entity, mentor: Entity, item: Entity) -> None:
    for ent in (hero, sidekick, mentor):
        ent.memes["joy"] += 1
    world.say(
        f"At last, the {item.label_word} was whole again. The team held it up like a trophy, "
        f"and {mentor.id} smiled, proud of the teamwork."
    )
    world.say(
        f"Under the bright light, the photograph looked as if it had never been torn at all, "
        f"except now everyone knew the heroes had saved it together."
    )


def tell(setting: Setting, item: BrokenItem, tool: Tool, hero_name: str, hero_type: str,
         sidekick_name: str, sidekick_type: str, mentor_name: str, mentor_type: str,
         humor_bit: str) -> World:
    world = World()
    hero = world.add(Entity(hero_name, "character", hero_type, label=hero_name, role="hero"))
    sidekick = world.add(Entity(sidekick_name, "character", sidekick_type, label=sidekick_name, role="sidekick"))
    mentor = world.add(Entity(mentor_name, "character", mentor_type, label=mentor_name, role="mentor"))

    hero.memes["brave"] = 1
    sidekick.memes["clever"] = 1
    mentor.memes["calm"] = 1

    world.say(
        f"{hero.id}, {sidekick.id}, and {mentor.id} patrolled {setting.place} like a small superhero squad."
    )
    world.say(setting_line(setting))
    foreshadow(world, mentor, Entity("shadow", label=item.label, type="thing"))
    world.para()
    reveal_need(world, hero, sidekick, Entity("photo", label=item.label, type="thing"), setting)
    teamwork_plan(world, hero, sidekick, mentor, tool, Entity("photo", label=item.label, type="thing"))
    world.para()
    humor(world, hero, sidekick, humor_bit)
    mend_item(world, tool, Entity("photo", label=item.label, type="thing"))
    finale(world, hero, sidekick, mentor, Entity("photo", label=item.label, type="thing"))
    world.facts.update(hero=hero, sidekick=sidekick, mentor=mentor, setting=setting, item=item, tool=tool, humor_bit=humor_bit)
    return world


KNOWLEDGE = {
    "mend": [("What does it mean to mend something?",
              "To mend something means to fix it or make it whole again after it breaks or tears.")],
    "photograph": [("What is a photograph?",
                   "A photograph is a picture made by a camera that can keep a moment from the past.")],
    "teamwork": [("What is teamwork?",
                  "Teamwork is when people help each other and use their different strengths to solve a problem together.")],
    "foreshadowing": [("What is foreshadowing?",
                       "Foreshadowing is a hint that something important or funny may happen later in the story.")],
    "humor": [("Why do stories use humor?",
                "Humor makes a story playful and fun, and it can help characters stay cheerful when things go wrong.")],
    "camera": [("Why should you keep a photograph safe?",
                 "A photograph can help you remember people and special moments, so it is nice to keep it clean and whole.")],
}

KNOWLEDGE_ORDER = ["mend", "photograph", "teamwork", "foreshadowing", "humor", "camera"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story where {f['hero'].id}, {f['sidekick'].id}, and {f['mentor'].id} work together to mend a photograph.",
        f"Tell a funny hero story in {f['setting'].place} that includes the words mend and photograph.",
        f"Write a story with foreshadowing, teamwork, and humor about fixing a torn photograph.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, sidekick, mentor = f["hero"], f["sidekick"], f["mentor"]
    item, tool, setting = f["item"], f["tool"], f["setting"]
    return [
        ("Who worked together in the story?",
         f"{hero.id}, {sidekick.id}, and {mentor.id} worked together as a small superhero team."),
        ("What did they mend?",
         f"They mended a {item.label_word} so the torn piece would be whole again."),
        ("How did the mentor hint at trouble?",
         f"{mentor.id} noticed the torn edge first, which was foreshadowing. That hint made the team pay attention before the problem got worse."),
        ("Why was the story funny?",
         f"It was funny because {sidekick.id} joked like a tiny superhero and the torn {item.label_word} looked dramatically serious for something made of paper."),
        ("Where did the story happen?",
         f"It happened in {setting.place}, where the team could see the broken {item.label_word} clearly."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mend", "photograph", "teamwork", "foreshadowing", "humor", "camera"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(hero="Nova", hero_type="girl", sidekick="Zip", sidekick_type="boy", mentor="Captain Comet", mentor_type="man",
                setting="rooftop", broken_item="photograph", photo_goal="the city scrapbook", humor_bit="photograph", rescue_tool="glue"),
    StoryParams(hero="Mira", hero_type="girl", sidekick="Bo", sidekick_type="boy", mentor="Aunt Orbit", mentor_type="woman",
                setting="museum", broken_item="team_photo", photo_goal="the hero hall", humor_bit="mend", rescue_tool="tape"),
]


def explain_rejection(item: BrokenItem, tool: Tool) -> str:
    return f"(No story: the chosen tool {tool.label} is not sensible enough to mend the {item.label}.)"


def valid_story_choices() -> list[tuple[str, str, str]]:
    return valid_combos()


@dataclass
class AspStub:
    pass
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


def asp_facts() -> str:
    import asp
    parts = []
    for sid in SETTINGS:
        parts.append(asp.fact("setting", sid))
    for iid, item in BROKEN_ITEMS.items():
        parts.append(asp.fact("item", iid))
        if item.can_mend:
            parts.append(asp.fact("can_mend", iid))
    for tid, tool in TOOLS.items():
        parts.append(asp.fact("tool", tid))
        parts.append(asp.fact("sense", tid, tool.sense))
        parts.append(asp.fact("power", tid, tool.power))
    return "\n".join(parts)


ASP_RULES = r"""
sensible(T) :- tool(T), sense(T, S), S >= 2.
valid(S, I, T) :- setting(S), item(I), can_mend(I), sensible(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_sensible()) == {t.id for t in sensible_tools()}:
        print("OK: sensible tools match.")
    else:
        rc = 1
        print("MISMATCH in sensible tools.")
    try:
        sample = generate(resolve_params(argparse.Namespace(hero=None, hero_type=None, sidekick=None, sidekick_type=None, mentor=None, mentor_type=None, setting=None, broken_item=None, photo_goal=None, humor_bit=None, rescue_tool=None), random.Random(1)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: generate smoke test failed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld about teamwork, foreshadowing, and humor.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--broken-item", choices=BROKEN_ITEMS)
    ap.add_argument("--rescue-tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--mentor")
    ap.add_argument("--mentor-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    broken_item = args.broken_item or rng.choice(list(BROKEN_ITEMS))
    rescue_tool = args.rescue_tool or rng.choice([t.id for t in sensible_tools()])
    if rescue_tool not in TOOLS:
        raise StoryError("Unknown rescue tool.")
    if not BROKEN_ITEMS[broken_item].can_mend or TOOLS[rescue_tool].sense < 2:
        raise StoryError(explain_rejection(BROKEN_ITEMS[broken_item], TOOLS[rescue_tool]))
    hero = args.hero or rng.choice(["Nova", "Mira", "Ace", "Pip", "Rex", "Zara"])
    sidekick = args.sidekick or rng.choice(["Zip", "Bo", "Jet", "Luma", "Blink", "Scout"])
    mentor = args.mentor or rng.choice(["Captain Comet", "Aunt Orbit", "Dr. Halo", "Major Marble"])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    sidekick_type = args.sidekick_type or rng.choice(["girl", "boy"])
    mentor_type = args.mentor_type or rng.choice(["woman", "man"])
    return StoryParams(hero=hero, hero_type=hero_type, sidekick=sidekick, sidekick_type=sidekick_type,
                       mentor=mentor, mentor_type=mentor_type, setting=setting, broken_item=broken_item,
                       photo_goal="the city scrapbook", humor_bit=broken_item, rescue_tool=rescue_tool)


def generate(params: StoryParams) -> StorySample:
    for field_name in ("hero", "sidekick", "mentor", "setting", "broken_item", "rescue_tool"):
        if not getattr(params, field_name, None):
            raise StoryError(f"Missing required param: {field_name}")
    setting = SETTINGS[params.setting]
    item = BROKEN_ITEMS[params.broken_item]
    tool = TOOLS[params.rescue_tool]
    if tool.sense < 2:
        raise StoryError(explain_rejection(item, tool))
    world = tell(setting, item, tool, params.hero, params.hero_type, params.sidekick, params.sidekick_type,
                 params.mentor, params.mentor_type, params.humor_bit)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            if sample.story not in seen:
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
