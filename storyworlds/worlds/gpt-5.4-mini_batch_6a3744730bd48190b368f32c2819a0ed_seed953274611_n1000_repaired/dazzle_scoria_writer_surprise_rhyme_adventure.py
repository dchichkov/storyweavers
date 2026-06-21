#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dazzle_scoria_writer_surprise_rhyme_adventure.py
===============================================================================

A small adventure storyworld about a young writer, a surprising cave of scoria,
and a bright dazzle that helps them finish a rhyme. The world is built as a
stateful simulation: typed entities accumulate physical meters and emotional
memes, a simple causal engine drives the turn, and the rendered story follows
the changed world.

The seed words are treated as the world's core nouns:
- dazzle: a bright, reflective treasure or glow
- scoria: rough volcanic stone in a cave
- writer: the child adventurer who wants to compose a rhyme

The story shape is kept close to Adventure: a child goes somewhere, meets a
problem, gets surprised, uses a clever tool, and ends with a vivid image of what
changed.
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Setting:
    id: str
    place: str
    description: str
    bright: bool
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
class Challenge:
    id: str
    name: str
    setup: str
    hazard: str
    surprise: str
    rhyme_need: str
    danger: str
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
class Treasure:
    id: str
    name: str
    phrase: str
    shine: str
    is_dazzle: bool = False
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
class Tool:
    id: str
    name: str
    phrase: str
    help_text: str
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
    setting: str = "canyon"
    challenge: str = "cave"
    treasure: str = "dazzle"
    tool: str = "lantern"
    writer_name: str = "Mina"
    writer_gender: str = "girl"
    helper_name: str = "Pip"
    helper_gender: str = "boy"
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


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    writer = world.get("writer")
    cave = world.get("challenge")
    treasure = world.get("treasure")
    if writer.meters["inside_cave"] < THRESHOLD or cave.meters["echo"] < THRESHOLD:
        return out
    sig = ("surprise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    writer.memes["surprise"] += 1
    writer.memes["focus"] += 1
    treasure.meters["gleam"] += 1
    out.append(f"The scoria walls answered with a sudden surprise, and the {treasure.label_word} flashed back at them.")
    return out


def _r_rhyme(world: World) -> list[str]:
    out: list[str] = []
    writer = world.get("writer")
    helper = world.get("helper")
    if writer.memes["surprise"] < THRESHOLD or helper.memes["help"] < THRESHOLD:
        return out
    sig = ("rhyme",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    writer.meters["rhyme_lines"] += 1
    writer.memes["joy"] += 1
    out.append(f"{helper.id} laughed and tapped the beat, and the rhyme came easy as a little song.")
    return out


CAUSAL_RULES = [Rule("surprise", _r_surprise), Rule("rhyme", _r_rhyme)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_for(sid: str) -> Setting:
    return SETTINGS[sid]


def challenge_for(cid: str) -> Challenge:
    return CHALLENGES[cid]


def treasure_for(tid: str) -> Treasure:
    return TREASURES[tid]


def tool_for(tid: str) -> Tool:
    return TOOLS[tid]


def valid_combo(setting: Setting, challenge: Challenge, treasure: Treasure, tool: Tool) -> bool:
    return challenge.name == "cave" and setting.bright is True and tool.id in {"lantern", "glowstick"} and treasure.is_dazzle


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for cid, c in CHALLENGES.items():
            for tid, t in TREASURES.items():
                for uid, u in TOOLS.items():
                    if valid_combo(s, c, t, u):
                        combos.append((sid, cid, tid, uid))
    return combos


def _setup_story(world: World, params: StoryParams) -> None:
    writer = world.add(Entity(id="writer", kind="character", type=params.writer_gender, role="writer", label=params.writer_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, role="helper", label=params.helper_name))
    setting = world.add(Entity(id="setting", kind="place", type="place", label=SETTINGS[params.setting].place))
    challenge = world.add(Entity(id="challenge", kind="thing", type="cave", label=CHALLENGES[params.challenge].name))
    treasure = world.add(Entity(id="treasure", kind="thing", type="treasure", label=TREASURES[params.treasure].name))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label=TOOLS[params.tool].name))

    world.facts.update(setting=setting, challenge=challenge, treasure=treasure, tool=tool, writer=writer, helper=helper)
    writer.memes["curiosity"] += 1
    helper.memes["trust"] += 1

    world.say(f"{writer.id} was a little writer who loved adventure and liked to keep notes about every strange place.")
    world.say(f"One bright morning, {writer.id} and {helper.id} walked to {SETTINGS[params.setting].description}.")
    world.say(CHALLENGES[params.challenge].setup)
    world.say(f"{writer.id} wanted to write a rhyme about the {TREASURES[params.treasure].name}, because the words felt like a spark of fun.")
    world.para()
    world.say(f"But inside the cave there was {CHALLENGES[params.challenge].hazard}, and that made the path feel tricky.")
    world.say(f"{helper.id} held up the {TOOLS[params.tool].name} and said it was the best way to see the way ahead.")


def _turn_story(world: World, params: StoryParams) -> None:
    writer = world.get("writer")
    helper = world.get("helper")
    challenge = world.get("challenge")
    treasure = world.get("treasure")
    tool = world.get("tool")

    writer.meters["inside_cave"] += 1
    challenge.meters["echo"] += 1
    helper.memes["help"] += 1
    world.para()
    world.say(f"The {challenge.label_word} gave a deep echo, and that was when the surprise happened.")
    propagate(world, narrate=True)
    world.say(f"{writer.id} blinked at the dazzle, then smiled because the glow showed {challenge.label_word} paths in the stone.")
    world.say(f"{helper.id} kept the {tool.label_word} steady while {writer.id} tried a rhyme out loud: {CHALLENGES[params.challenge].rhyme_need}.")


def _end_story(world: World, params: StoryParams) -> None:
    writer = world.get("writer")
    helper = world.get("helper")
    treasure = world.get("treasure")
    world.para()
    if writer.meters["rhyme_lines"] >= THRESHOLD:
        world.say(f"In the end, {writer.id} wrote the rhyme on a scrap of paper and tucked it beside the {treasure.label_word}.")
        world.say(f"The cave was still made of rough scoria, but now it felt like a friendly place with a bright secret inside it.")
        world.say(f"{helper.id} grinned, and the two adventurers walked home with the song in their pockets and the dazzle in their eyes.")
    else:
        world.say(f"In the end, the cave stayed quiet, and {writer.id} left with the idea of a rhyme still unfinished.")
        world.say(f"Even so, the bright light and the surprising scoria shapes had given the writer a story to finish later.")
        world.say(f"{helper.id} led the way back out, and the two friends carried the memory of the glow with them.")


def tell(params: StoryParams) -> World:
    world = World()
    _setup_story(world, params)
    _turn_story(world, params)
    _end_story(world, params)
    world.facts["outcome"] = "finished" if world.get("writer").meters["rhyme_lines"] >= THRESHOLD else "unfinished"
    return world


SETTINGS = {
    "canyon": Setting(id="canyon", place="the canyon trail", description="a narrow canyon trail with red cliffs", bright=True, tags={"adventure", "outdoor"}),
    "hill": Setting(id="hill", place="the high hill", description="a windy hill above the village", bright=True, tags={"adventure", "outdoor"}),
    "library": Setting(id="library", place="the old library", description="an old library with a dusty map room", bright=False, tags={"adventure", "indoor"}),
}

CHALLENGES = {
    "cave": Challenge(id="cave", name="cave", setup="At the end of the trail, they found a cave full of rough black scoria.", hazard="dark scoria shadows and slippery stones", surprise="a hidden echo in the rock", rhyme_need="bright lines for the dark cave", danger="the floor could snag little boots", tags={"scoria", "cave"}),
    "ruins": Challenge(id="ruins", name="ruins", setup="Past the ridge, they found old ruins with piles of broken stone.", hazard="windy corners and crumbling steps", surprise="a doorway that chimed in the wind", rhyme_need="words that fit the old stones", danger="the stairs could wobble", tags={"adventure", "stone"}),
}

TREASURES = {
    "dazzle": Treasure(id="dazzle", name="dazzle", phrase="the dazzle", shine="shone like a tiny sun", is_dazzle=True, tags={"dazzle"}),
    "coin": Treasure(id="coin", name="gold coin", phrase="the gold coin", shine="gleamed like honey", is_dazzle=False, tags={"treasure"}),
}

TOOLS = {
    "lantern": Tool(id="lantern", name="lantern", phrase="a lantern", help_text="showed the path", tags={"light"}),
    "glowstick": Tool(id="glowstick", name="glow stick", phrase="a glow stick", help_text="made a safe green light", tags={"light", "surprise"}),
    "torch": Tool(id="torch", name="torch", phrase="a torch", help_text="made a strong flame", tags={"fire"}),
}


GIRL_NAMES = ["Mina", "Ivy", "Luna", "Nina", "Ada"]
BOY_NAMES = ["Pip", "Owen", "Theo", "Finn", "Ezra"]
TRAITS = ["curious", "brave", "careful", "inventive", "cheerful"]


def explain_rejection(setting: Setting, challenge: Challenge, treasure: Treasure, tool: Tool) -> str:
    if not treasure.is_dazzle:
        return "(No story: this world is built around the seed word dazzle as the bright treasure."
    if tool.id == "torch":
        return "(No story: the adventure needs a safe light that fits the cave surprise, not a torch flame.)"
    if not setting.bright and challenge.name == "cave":
        return "(No story: this small adventure expects a bright trail leading into the cave, so the setup would not match.)"
    return "(No story: this combination does not fit the small adventure pattern.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    writer = f["writer"]
    challenge = f["challenge"]
    treasure = f["treasure"]
    tool = f["tool"]
    return [
        f'Write an adventure story for a young child that includes the words "dazzle", "scoria", and "writer".',
        f"Tell a short adventure where {writer.id} explores a cave of scoria, gets a surprise, and uses {tool.label_word} to finish a rhyme about {treasure.label_word}.",
        f"Write a child-friendly cave adventure with a surprise glow, a writer hero, and a happy ending that proves the rhyme got finished.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    writer = f["writer"]
    helper = f["helper"]
    challenge = f["challenge"]
    treasure = f["treasure"]
    tool = f["tool"]
    qa = [
        ("Who is the story about?", f"It is about {writer.id}, a young writer who goes on an adventure with {helper.id}."),
        ("What did they find in the cave?", f"They found rough scoria, a tricky cave, and the bright {treasure.label_word} hidden inside it."),
        ("Why was there a surprise?", f"The cave echoed back at them, and the dazzle suddenly flashed in the stone. That surprise helped the writer notice the path and keep going."),
        ("What helped the writer finish the rhyme?", f"{helper.id} held up {tool.phrase}, and the safe light made it easier for {writer.id} to say the rhyme out loud."),
    ]
    if world.facts.get("outcome") == "finished":
        qa.append(("How did the story end?", f"It ended with {writer.id} writing the rhyme and taking it home. The cave stayed rough and stony, but the adventure turned it into a friendly memory."))
        qa.append(("What changed by the end?", f"The cave did not change into something soft, but {writer.id} changed by becoming more confident. The dazzle turned from a surprise into a finished rhyme."))
    else:
        qa.append(("How did the story end?", f"It ended with {writer.id} still needing to finish the rhyme later. Even so, the bright cave gave {writer.id} a good idea to return to."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set()
    tags |= f["challenge"].tags
    tags |= f["treasure"].tags
    tags |= f["tool"].tags
    out: list[tuple[str, str]] = []
    knowledge = {
        "scoria": ("What is scoria?", "Scoria is rough volcanic rock with lots of holes in it. It can feel bumpy and crumbly in a cave or on a trail."),
        "dazzle": ("What does dazzle mean?", "Dazzle means a bright shine that catches your eye. It can make something look magical or exciting."),
        "light": ("Why do adventurers carry a lantern?", "A lantern helps people see in dark places without using a big flame. It makes the path easier and safer to follow."),
        "rhyme": ("What is a rhyme?", "A rhyme is when words sound alike at the ends, like 'light' and 'bright'. Writers use rhymes to make songs and poems fun."),
        "writer": ("What does a writer do?", "A writer puts words together to make stories, poems, notes, and rhymes. Writers notice details and shape them into something to read."),
    }
    order = ["scoria", "dazzle", "light", "rhyme", "writer"]
    for key in order:
        if key == "scoria" and "scoria" in tags:
            out.append(knowledge[key])
        elif key == "dazzle" and "dazzle" in tags:
            out.append(knowledge[key])
        elif key == "light" and "light" in tags:
            out.append(knowledge[key])
        elif key == "rhyme" and "surprise" in tags:
            out.append(knowledge[key])
        elif key == "writer" and True:
            out.append(knowledge[key])
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
surprised(writer) :- inside_cave(writer), echo(challenge).
rhyme_finished(writer) :- surprised(writer), help(helper).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for uid in TOOLS:
        lines.append(asp.fact("tool", uid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    p = set(valid_combos())
    c = set(asp_valid_combos())
    if p == c:
        print(f"OK: ASP gate matches valid_combos() ({len(p)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        if p - c:
            print("  only in python:", sorted(p - c))
        if c - p:
            print("  only in asp:", sorted(c - p))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


CURATED = [
    StoryParams(setting="canyon", challenge="cave", treasure="dazzle", tool="lantern", writer_name="Mina", writer_gender="girl", helper_name="Pip", helper_gender="boy"),
    StoryParams(setting="hill", challenge="cave", treasure="dazzle", tool="glowstick", writer_name="Ivy", writer_gender="girl", helper_name="Owen", helper_gender="boy"),
    StoryParams(setting="canyon", challenge="cave", treasure="dazzle", tool="glowstick", writer_name="Ezra", writer_gender="boy", helper_name="Nina", helper_gender="girl"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: a writer, scoria, and a surprising dazzle.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--writer-name")
    ap.add_argument("--writer-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    challenge = args.challenge or "cave"
    treasure = args.treasure or "dazzle"
    tool = args.tool or rng.choice(["lantern", "glowstick"])
    if args.treasure and not TREASURES[args.treasure].is_dazzle:
        raise StoryError("This world needs the seed word dazzle as the central treasure.")
    if tool == "torch":
        raise StoryError("A torch is too fiery for this gentle adventure.")
    if setting not in SETTINGS or challenge not in CHALLENGES or treasure not in TREASURES or tool not in TOOLS:
        raise StoryError("Invalid options.")
    if not valid_combo(SETTINGS[setting], CHALLENGES[challenge], TREASURES[treasure], TOOLS[tool]):
        raise StoryError("No valid adventure combination matches those choices.")
    writer_gender = args.writer_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if writer_gender == "girl" else "girl")
    writer_name = args.writer_name or rng.choice(GIRL_NAMES if writer_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != writer_name])
    return StoryParams(setting=setting, challenge=challenge, treasure=treasure, tool=tool, writer_name=writer_name, writer_gender=writer_gender, helper_name=helper_name, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.challenge not in CHALLENGES or params.treasure not in TREASURES or params.tool not in TOOLS:
        raise StoryError("Invalid StoryParams values.")
    if not valid_combo(SETTINGS[params.setting], CHALLENGES[params.challenge], TREASURES[params.treasure], TOOLS[params.tool]):
        raise StoryError("These parameters do not make a reasonable adventure.")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid adventure combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
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
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
