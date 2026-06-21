#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/number_inner_monologue_happy_ending_magic_bedtime.py
===================================================================================

A small bedtime storyworld about a child, a magic number charm, and a gentle
inner-monologue turn that ends happily.

Seed prompt:
- Words: number
- Features: Inner Monologue, Happy Ending, Magic
- Style: Bedtime Story

World idea:
- A child is trying to fall asleep.
- They worry about a missing number in a counting game.
- A magical bedtime object helps them count softly, calm down, and drift to sleep.
- The ending proves what changed: the room is quiet, the worry is small, and the
  child falls asleep smiling with the number safely remembered.

This script follows the shared storyworld contract:
- stdlib only
- eager import of storyworlds/results.py for QAItem, StoryError, StorySample
- lazy import of storyworlds/asp.py in ASP helpers
- StoryParams, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    magical: bool = False
    gives_light: bool = False
    soothing: bool = False

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
class Theme:
    id: str
    room: str
    bedtime_line: str
    play_line: str
    dark_spot: str
    scene_noun: str
    ending_image: str
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
class MagicObject:
    id: str
    label: str
    phrase: str
    glow: str
    purpose: str
    magical: bool = True
    soothing: bool = True
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
class Worry:
    id: str
    label: str
    trigger: str
    inner_voice: str
    comfort_gain: int
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
class Comfort:
    id: str
    label: str
    action: str
    result: str
    calm_gain: int
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


def _r_comfort(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes["worry"] < THRESHOLD:
        return out
    sig = ("comfort",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] += 1
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1)
    out.append("__comfort__")
    return out


def _r_magic_glow(world: World) -> list[str]:
    out = []
    if world.get("charm").meters["glow"] < THRESHOLD:
        return out
    sig = ("glow",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    child.memes["wonder"] += 1
    out.append("The little charm glowed like a tiny star.")
    return out


CAUSAL_RULES = [Rule("comfort", "social", _r_comfort), Rule("glow", "magical", _r_magic_glow)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme_id, theme in THEMES.items():
        for worry_id, worry in WORRIES.items():
            for magic_id, magic in MAGICS.items():
                for comfort_id, comfort in COMFORTS.items():
                    if magic.purpose in worry.trigger and comfort.calm_gain >= worry.comfort_gain:
                        combos.append((theme_id, worry_id, magic_id))
    return combos


def reasonableness_ok(worry: Worry, magic: MagicObject) -> bool:
    return magic.purpose in worry.trigger


def calmable(worry: Worry, comfort: Comfort) -> bool:
    return comfort.calm_gain >= worry.comfort_gain


def would_sleep(world: World) -> bool:
    c = world.get("child")
    return c.memes["worry"] < 1 and c.meters["sleep"] >= 1


def predict_settle(world: World, magic_id: str, comfort_id: str) -> dict:
    sim = world.copy()
    _use_magic(sim, sim.get("charm"), MAGICS[magic_id], narrate=False)
    _comfort(sim, sim.get("child"), COMFORTS[comfort_id], narrate=False)
    return {"calm": sim.get("child").memes["calm"], "worry": sim.get("child").memes["worry"]}


def _use_magic(world: World, charm_ent: Entity, magic: MagicObject, narrate: bool = True) -> None:
    charm_ent.meters["glow"] += 1
    propagate(world, narrate=narrate)


def _comfort(world: World, child: Entity, comfort: Comfort, narrate: bool = True) -> None:
    child.memes["calm"] += comfort.calm_gain
    child.meters["sleep"] += 1
    if narrate:
        world.say(comfort.result)


def bedtime_setup(world: World, child: Entity, parent: Entity, theme: Theme) -> None:
    child.memes["love"] += 1
    world.say(f"At bedtime, {child.id} snuggled under the blanket in {theme.room}. {theme.bedtime_line}")
    world.say(f"{theme.play_line}")


def worry_inner_voice(world: World, child: Entity, worry: Worry) -> None:
    child.memes["worry"] += 1
    world.say(f"{child.id} looked at the dark corner and thought, \"{worry.inner_voice}\"")


def magic_answer(world: World, child: Entity, charm: Entity, magic: MagicObject) -> None:
    world.say(f"Then {child.id} held up {magic.phrase}. It {magic.glow}.")
    charm.meters["glow"] += 1
    propagate(world, narrate=False)


def calming_turn(world: World, child: Entity, parent: Entity, comfort: Comfort) -> None:
    world.say(f"{parent.id} smiled and said, \"{comfort.action}.\"")
    _comfort(world, child, comfort, narrate=True)


def happy_end(world: World, child: Entity, parent: Entity, theme: Theme, number_word: str) -> None:
    child.meters["sleep"] += 1
    child.memes["worry"] = 0.0
    child.memes["peace"] += 1
    world.say(f"{child.id} counted softly, {number_word}, and the room felt smaller and kinder.")
    world.say(f"Soon {child.id} was asleep, with {theme.ending_image} in {parent.pronoun('possessive')} quiet dreams.")


def tell(theme: Theme, worry: Worry, magic: MagicObject, comfort: Comfort,
         child_name: str = "Mia", child_gender: str = "girl",
         parent_name: str = "Mom", parent_gender: str = "mother",
         number_word: str = "one") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    charm = world.add(Entity(id="charm", type="thing", label=magic.label, magical=True, gives_light=True))
    world.facts.update(theme=theme, worry=worry, magic=magic, comfort=comfort, number_word=number_word)

    bedtime_setup(world, child, parent, theme)
    world.para()
    worry_inner_voice(world, child, worry)
    world.say(f"{child.id} wished the {theme.dark_spot} would not feel so big.")

    world.para()
    magic_answer(world, child, charm, magic)
    world.say(f"{child.id} breathed in slowly and listened to the little glow.")
    calming_turn(world, child, parent, comfort)

    world.para()
    happy_end(world, child, parent, theme, number_word)

    world.facts.update(child=child, parent=parent, charm=charm, outcome="happy")
    return world


THEMES = {
    "moon_room": Theme(
        id="moon_room",
        room="the moonlit bedroom",
        bedtime_line="A silver moonbeam made a soft line on the floor.",
        play_line="Earlier, the room had been full of giggles and shadow-puppets.",
        dark_spot="the corner by the curtains",
        scene_noun="bedtime room",
        ending_image="the moonbeam on the floor and the blanket tucked up to the chin",
    ),
    "storybook_nook": Theme(
        id="storybook_nook",
        room="the storybook nook",
        bedtime_line="The bookshelf made a little cave of shadows and pages.",
        play_line="Earlier, there had been whisper-games and a tower of pillows.",
        dark_spot="the space behind the pillow tower",
        scene_noun="storybook nook",
        ending_image="the pillow tower, neat and still, beside a sleepy smile",
    ),
    "star_nursery": Theme(
        id="star_nursery",
        room="the star nursery",
        bedtime_line="Tiny stars shimmered on the wall like friendly eyes.",
        play_line="Earlier, the toy basket had been a castle full of brave knights.",
        dark_spot="the space under the rocking chair",
        scene_noun="star nursery",
        ending_image="the stars on the wall and one tiny hand resting peacefully",
    ),
}

WORRIES = {
    "missing_number": Worry(
        id="missing_number",
        label="the missing number",
        trigger="number game",
        inner_voice="What if I forget the number?",
        comfort_gain=1,
        tags={"number", "worry"},
    ),
    "wrong_number": Worry(
        id="wrong_number",
        label="the wrong number",
        trigger="number rhyme",
        inner_voice="What if I say the number wrong?",
        comfort_gain=1,
        tags={"number", "worry"},
    ),
    "too_dark": Worry(
        id="too_dark",
        label="the dark corner",
        trigger="dark corner",
        inner_voice="What if the dark corner is too big?",
        comfort_gain=1,
        tags={"dark", "worry"},
    ),
}

MAGICS = {
    "counting_star": MagicObject(
        id="counting_star",
        label="a counting star",
        phrase="a little counting star",
        glow="blinked blue and gold",
        purpose="number",
        tags={"magic", "number"},
    ),
    "number_pebble": MagicObject(
        id="number_pebble",
        label="a number pebble",
        phrase="a warm little number pebble",
        glow="glimmered like honey",
        purpose="number",
        tags={"magic", "number"},
    ),
    "gentle_lantern": MagicObject(
        id="gentle_lantern",
        label="a gentle lantern",
        phrase="a tiny magic lantern",
        glow="shone softly without any spark",
        purpose="sleep",
        tags={"magic", "sleep"},
    ),
}

COMFORTS = {
    "breathing": Comfort(
        id="breathing",
        label="breathing slowly",
        action="Let's take three slow breaths together",
        result="They breathed in and out, and the worry got smaller.",
        calm_gain=2,
        tags={"calm"},
    ),
    "song": Comfort(
        id="song",
        label="a bedtime song",
        action="Let's hum a soft bedtime song",
        result="The hum turned the room gentle and warm.",
        calm_gain=2,
        tags={"calm"},
    ),
    "count_back": Comfort(
        id="count_back",
        label="counting backward",
        action="Let's count backward from three",
        result="Three, two, one. The number sat safely in memory, and the worry melted away.",
        calm_gain=3,
        tags={"number", "calm"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Noah", "Finn", "Leo", "Theo", "Sam"]
TRAITS = ["sleepy", "curious", "gentle", "thoughtful", "brave"]


@dataclass
class StoryParams:
    theme: str
    worry: str
    magic: str
    comfort: str
    child_name: str = "Mia"
    child_gender: str = "girl"
    parent_name: str = "Mom"
    parent_gender: str = "mother"
    number_word: str = "one"
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime magic storyworld about a number and a gentle inner monologue.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--worry", choices=WORRIES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
    ap.add_argument("--number-word", default="one")
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
    theme = args.theme or rng.choice(list(THEMES))
    worry = args.worry or rng.choice(list(WORRIES))
    magic = args.magic or rng.choice(list(MAGICS))
    comfort = args.comfort or rng.choice(list(COMFORTS))
    if not reasonableness_ok(WORRIES[worry], MAGICS[magic]):
        raise StoryError("That magic does not fit the worry in a reasonable bedtime story.")
    if not calmable(WORRIES[worry], COMFORTS[comfort]):
        raise StoryError("That comfort is not strong enough to settle the worry.")
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    parent_name = args.parent_name or ("Mom" if parent_gender == "mother" else "Dad")
    number_word = args.number_word
    return StoryParams(
        theme=theme,
        worry=worry,
        magic=magic,
        comfort=comfort,
        child_name=child_name,
        child_gender=child_gender,
        parent_name=parent_name,
        parent_gender=parent_gender,
        number_word=number_word,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES or params.worry not in WORRIES or params.magic not in MAGICS or params.comfort not in COMFORTS:
        raise StoryError("Invalid story parameters.")
    if not reasonableness_ok(WORRIES[params.worry], MAGICS[params.magic]):
        raise StoryError("That magic does not fit the worry.")
    if not calmable(WORRIES[params.worry], COMFORTS[params.comfort]):
        raise StoryError("That comfort is too weak for the worry.")
    world = tell(THEMES[params.theme], WORRIES[params.worry], MAGICS[params.magic], COMFORTS[params.comfort],
                 child_name=params.child_name, child_gender=params.child_gender,
                 parent_name=params.parent_name, parent_gender=params.parent_gender,
                 number_word=params.number_word)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a small child that includes the word "{f["number_word"]}" and a little magic glow.',
        f'Tell a gentle story about {f["child"].id} worrying about a number, then calming down with magic and a loving grown-up.',
        f'Write a happy bedtime story where the child thinks about a number, uses a magic helper, and falls asleep peacefully.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, worry, magic = f["child"], f["parent"], f["worry"], f["magic"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and {parent.id}, at bedtime in a gentle, sleepy room."),
        (f"What was {child.id} worried about?", f"{child.id} was worried about {worry.label}. The worry felt bigger in the dark, so the child needed comfort."),
        (f"What magical thing helped {child.id}?", f"{magic.phrase} helped {child.id}. It glowed softly and made the room feel safe."),
        (f"How did the story end?", f"It ended happily, with {child.id} calm and asleep. The number was remembered safely, and the dark felt kind instead of scary."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["worry"].tags) | set(world.facts["magic"].tags) | set(world.facts["comfort"].tags)
    out = []
    if "number" in tags:
        out.extend([
            ("What is a number?", "A number is a word or symbol used for counting and telling how many things there are."),
            ("Why do people count things?", "People count things to keep track of how many there are. Counting helps you remember and compare them."),
        ])
    if "magic" in tags:
        out.extend([
            ("What is magic in a bedtime story?", "Magic in a bedtime story is something special and gentle that helps the characters in a wonderful way."),
        ])
    if "calm" in tags:
        out.extend([
            ("Why do slow breaths help?", "Slow breaths can help a person calm down. When you breathe slowly, your body feels less tense and your mind can settle."),
        ])
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
        if e.magical:
            bits.append("magical")
        if e.gives_light:
            bits.append("gives_light")
        if e.soothing:
            bits.append("soothing")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(theme="moon_room", worry="missing_number", magic="counting_star", comfort="count_back", child_name="Mia", child_gender="girl", parent_name="Mom", parent_gender="mother", number_word="one"),
    StoryParams(theme="storybook_nook", worry="wrong_number", magic="number_pebble", comfort="breathing", child_name="Noah", child_gender="boy", parent_name="Dad", parent_gender="father", number_word="two"),
    StoryParams(theme="star_nursery", worry="too_dark", magic="gentle_lantern", comfort="song", child_name="Lily", child_gender="girl", parent_name="Mom", parent_gender="mother", number_word="three"),
]


ASP_RULES = r"""
% A reasonable story matches a worry with a magic helper and a calming comfort.
valid(theme(T), worry(W), magic(M)) :- theme(T), worry(W), magic(M), fits(W, M).
fits(W, M) :- worry(W), magic(M), trigger(W, T), purpose(M, P), T = P.
settled :- comfort(C), calm_gain(C, G), G >= 2.
outcome(happy) :- settled.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for wid, w in WORRIES.items():
        lines.append(asp.fact("worry", wid))
        lines.append(asp.fact("trigger", wid, w.trigger))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("purpose", mid, m.purpose))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        lines.append(asp.fact("calm_gain", cid, c.calm_gain))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python valid_combos().")
    try:
        params = CURATED[0]
        sample = generate(params)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False)
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: verify passed and normal generation/emit succeeded.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime magic storyworld with number, inner monologue, and a happy ending.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--worry", choices=WORRIES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
    ap.add_argument("--number-word", default="one")
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
    theme = args.theme or rng.choice(list(THEMES))
    worry = args.worry or rng.choice(list(WORRIES))
    magic = args.magic or rng.choice(list(MAGICS))
    comfort = args.comfort or rng.choice(list(COMFORTS))
    if not reasonableness_ok(WORRIES[worry], MAGICS[magic]):
        raise StoryError("That magic does not fit the worry.")
    if not calmable(WORRIES[worry], COMFORTS[comfort]):
        raise StoryError("That comfort is too weak for the worry.")
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    parent_name = args.parent_name or ("Mom" if parent_gender == "mother" else "Dad")
    return StoryParams(
        theme=theme, worry=worry, magic=magic, comfort=comfort,
        child_name=child_name, child_gender=child_gender,
        parent_name=parent_name, parent_gender=parent_gender,
        number_word=args.number_word,
    )


def generate_story_world(params: StoryParams) -> StorySample:
    return generate(params)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], WORRIES[params.worry], MAGICS[params.magic], COMFORTS[params.comfort],
                 child_name=params.child_name, child_gender=params.child_gender,
                 parent_name=params.parent_name, parent_gender=params.parent_gender,
                 number_word=params.number_word)
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
        print(asp_program("#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for combo in combos:
            print("  ", combo)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def reasonableness_ok(worry: Worry, magic: MagicObject) -> bool:
    return magic.purpose in worry.trigger or (worry.id == "too_dark" and magic.purpose == "sleep")


def calmable(worry: Worry, comfort: Comfort) -> bool:
    return comfort.calm_gain >= worry.comfort_gain


if __name__ == "__main__":
    main()
