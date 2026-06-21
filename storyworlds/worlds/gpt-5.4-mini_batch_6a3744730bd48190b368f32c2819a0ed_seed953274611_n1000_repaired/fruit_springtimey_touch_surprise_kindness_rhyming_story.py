#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fruit_springtimey_touch_surprise_kindness_rhyming_story.py
===========================================================================================

A tiny storyworld about a springtime fruit stand, a curious touch, a surprise,
and a kindness-led fix. The prose is rhyming, child-facing, and state-driven:
a child wants to touch shiny fruit, makes a small mess or a shy upset, then a
kind helper turns the moment into a surprise and a sweet ending.

This world keeps the simulation small:
- typed entities with meters and memes,
- a forward causal loop,
- a reasonableness gate,
- an ASP twin for parity checking,
- three Q&A sets grounded in the live world model.
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
CAN_TOUCH_MIN = 1
HELP_MIN = 2


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
class Fruit:
    id: str
    label: str
    color: str
    sweetness: str
    peelable: bool = True
    splishable: bool = False
    rhyme: str = ""
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
class Setting:
    id: str
    place: str
    bloom: str
    smell: str
    surprise_spot: str
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
class Touch:
    id: str
    label: str
    gesture: str
    careful: int
    messy: int
    surprise: str
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
class Help:
    id: str
    label: str
    sense: int
    effect: int
    text: str
    surprise_text: str
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
        c.facts = dict(self.facts)
        return c


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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["sticky"] < THRESHOLD:
            continue
        sig = ("spill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "bowl" in world.entities:
            world.get("bowl").meters["mess"] += 1
        out.append("__spill__")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("surprise_done"):
        return out
    if world.facts.get("help_used"):
        world.facts["surprise_done"] = True
        out.append("__surprise__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("surprise", "social", _r_surprise)]


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


def reasonableness_ok(fruit: Fruit, touch: Touch, setting: Setting) -> bool:
    return fruit.peelable and touch.careful >= CAN_TOUCH_MIN and setting.place != ""


def helpful_ok(help_item: Help) -> bool:
    return help_item.sense >= HELP_MIN


def predict_sticky(world: World, fruit_id: str, touch: Touch) -> bool:
    sim = world.copy()
    fruit = sim.get(fruit_id)
    fruit.meters["sticky"] += 1
    propagate(sim, narrate=False)
    return sim.get("bowl").meters["mess"] >= THRESHOLD


def build_rhyme_line(*parts: str) -> str:
    return " ".join(p.strip() for p in parts if p.strip())


def introduce(world: World, child: Entity, setting: Setting, fruit: Fruit) -> None:
    child.memes["joy"] += 1
    world.say(
        build_rhyme_line(
            f"On a springtimey day with a breeze soft and light,",
            f"{child.id} skipped to the stand, feeling cheerful and bright.",
        )
    )
    world.say(
        build_rhyme_line(
            f"At {setting.place}, with {setting.bloom} in the air,",
            f"there sat {fruit.label}, all shiny and fair.",
        )
    )


def want_touch(world: World, child: Entity, fruit: Fruit, touch: Touch) -> None:
    child.memes["curious"] += 1
    world.say(
        build_rhyme_line(
            f'"Can I {touch.gesture} {fruit.label}?" {child.id} asked with a grin,',
            f'"Its color looks lovely, I want to reach in."',
        )
    )


def warn(world: World, parent: Entity, child: Entity, fruit: Fruit, touch: Touch) -> None:
    world.say(
        build_rhyme_line(
            f'"A careful touch keeps the fruit neat and sweet,"',
            f"{parent.label_word} said. \"Too rough hands can make a small treat.",
        ) + "\""
    )


def do_touch(world: World, child: Entity, fruit: Fruit, touch: Touch) -> None:
    child.memes["defiance"] += 1
    fruit.meters["sticky"] += float(touch.messy)
    world.say(
        build_rhyme_line(
            f"But {child.id} leaned in with a curious twitch,",
            f"and gave {fruit.label} a little too rough of a {touch.gesture}.",
        )
    )
    propagate(world, narrate=False)


def surprise_help(world: World, helper: Entity, child: Entity, fruit: Fruit, help_item: Help) -> None:
    world.facts["help_used"] = True
    world.say(
        build_rhyme_line(
            f"Then {helper.id} came smiling, with kindness and cheer,",
            f"and made a sweet surprise appear.",
        )
    )
    world.say(
        build_rhyme_line(
            f"{helper.id} {help_item.text}, and the little mess faded away,",
            f"so {child.id} could still enjoy the bright spring day.",
        )
    )
    world.facts["surprise_done"] = True
    propagate(world, narrate=False)


def ending(world: World, child: Entity, helper: Entity, fruit: Fruit, setting: Setting) -> None:
    child.memes["relief"] += 1
    child.memes["love"] += 1
    helper.memes["kindness"] += 1
    world.say(
        build_rhyme_line(
            f"Now the fruit stood gleaming, still pretty and neat,",
            f"and the air smelled of blossoms, so fresh and sweet.",
        )
    )
    world.say(
        build_rhyme_line(
            f"{child.id} smiled at {helper.id} with a thankful heart,",
            f"for kindness and patience had made the best part.",
        )
    )


def tell(setting: Setting, fruit: Fruit, touch: Touch, help_item: Help,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_name: str = "Mom", helper_gender: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", label="the helper"))
    bowl = world.add(Entity(id="bowl", kind="thing", type="thing", label="the fruit bowl"))
    world.facts.update(setting=setting, fruit=fruit, touch=touch, help_item=help_item,
                       child=child, helper=helper, bowl=bowl)

    introduce(world, child, setting, fruit)
    world.para()
    want_touch(world, child, fruit, touch)
    warn(world, helper, child, fruit, touch)

    if fruit.id == "berries":
        world.say("The berries were tempting, with red dots like tiny suns.")
    do_touch(world, child, fruit, touch)

    if predict_sticky(world, fruit.id, touch):
        world.para()
        surprise_help(world, helper, child, fruit, help_item)
        ending(world, child, helper, fruit, setting)
    else:
        world.para()
        ending(world, child, helper, fruit, setting)

    world.facts["outcome"] = "surprise"
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the garden gate",
        bloom="flowers",
        smell="pollen and rain",
        surprise_spot="under the apple tree",
        tags={"springtimey"},
    ),
    "market": Setting(
        id="market",
        place="the little fruit market",
        bloom="tulips",
        smell="sweet baskets and leaves",
        surprise_spot="behind the berry crate",
        tags={"fruit"},
    ),
    "porch": Setting(
        id="porch",
        place="the sunny porch",
        bloom="potted daisies",
        smell="warm wood and herbs",
        surprise_spot="beside the lemonade jar",
        tags={"touch"},
    ),
}

FRUITS = {
    "apple": Fruit(
        id="apple",
        label="an apple",
        color="red",
        sweetness="crisp",
        peelable=True,
        splishable=False,
        rhyme="bright and nice",
        tags={"fruit"},
    ),
    "berries": Fruit(
        id="berries",
        label="a bowl of berries",
        color="ruby",
        sweetness="juicy",
        peelable=False,
        splishable=True,
        rhyme="little red beads",
        tags={"fruit", "surprise"},
    ),
    "peach": Fruit(
        id="peach",
        label="a peach",
        color="gold",
        sweetness="soft",
        peelable=True,
        splishable=True,
        rhyme="fuzzy and sweet",
        tags={"fruit"},
    ),
}

TOUCHES = {
    "tap": Touch(
        id="tap",
        label="tap",
        gesture="tap",
        careful=2,
        messy=1,
        surprise="a tiny wobble",
        tags={"touch"},
    ),
    "squeeze": Touch(
        id="squeeze",
        label="squeeze",
        gesture="squeeze",
        careful=1,
        messy=2,
        surprise="a sticky spot",
        tags={"touch"},
    ),
    "poke": Touch(
        id="poke",
        label="poke",
        gesture="poke",
        careful=2,
        messy=1,
        surprise="a popped drip",
        tags={"touch"},
    ),
}

HELPS = {
    "napkin": Help(
        id="napkin",
        label="a napkin",
        sense=2,
        effect=2,
        text="lifted a napkin and gently wiped the sticky shine",
        surprise_text="waved a napkin like a flag of care",
        tags={"kindness", "surprise"},
    ),
    "basket": Help(
        id="basket",
        label="a berry basket",
        sense=3,
        effect=2,
        text="pulled out a berry basket and set the fruit back in order",
        surprise_text="brought out a basket with a ribbon bow",
        tags={"kindness", "surprise"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nina", "Ivy", "Ava"]
BOY_NAMES = ["Theo", "Finn", "Max", "Owen", "Leo"]
TRAITS = ["gentle", "curious", "playful", "cheerful"]


@dataclass
class StoryParams:
    setting: str
    fruit: str
    touch: str
    help_item: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    trait: str = "curious"
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for fid, fruit in FRUITS.items():
            for tid, touch in TOUCHES.items():
                for hid, help_item in HELPS.items():
                    if reasonableness_ok(fruit, touch, setting) and helpful_ok(help_item):
                        combos.append((sid, fid, tid, hid))
    return combos


def explain_rejection(fruit: Fruit, touch: Touch) -> str:
    return (
        f"(No story: {touch.label} is too rough for this tiny fruit scene, or the "
        f"fruit choice does not fit a gentle springtime touch. Pick a peelable fruit "
        f"and a careful touch.)"
    )


def explain_help(help_id: str) -> str:
    h = HELPS[help_id]
    return f"(Refusing help '{help_id}': it is not kind or sensible enough for the surprise ending.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Springtime fruit touch storyworld with surprise and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--fruit", choices=FRUITS)
    ap.add_argument("--touch", choices=TOUCHES)
    ap.add_argument("--help-item", choices=HELPS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["mother", "father"])
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
    if args.fruit and args.touch and not reasonableness_ok(FRUITS[args.fruit], TOUCHES[args.touch], SETTINGS.get(args.setting or "garden", SETTINGS["garden"])):
        raise StoryError(explain_rejection(FRUITS[args.fruit], TOUCHES[args.touch]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.fruit is None or c[1] == args.fruit)
              and (args.touch is None or c[2] == args.touch)
              and (args.help_item is None or c[3] == args.help_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, fid, tid, hid = rng.choice(sorted(combos))
    fruit = FRUITS[fid]
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    helper_name = args.helper_name or ("Mom" if helper_gender == "mother" else "Dad")
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=sid,
        fruit=fid,
        touch=tid,
        help_item=hid,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        trait=trait,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a rhyming springtime story that includes the words fruit and touch, and ends with kindness.",
        f"Tell a small story where {f['child'].id} wants to touch {f['fruit'].label} but a kind helper turns it into a surprise.",
        f"Write a gentle surprise story in a springtimey setting with fruit, a touch, and a kind ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, fruit, touch, setting = f["child"], f["helper"], f["fruit"], f["touch"], f["setting"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {helper.id} at {setting.place}. {child.id} wanted to touch {fruit.label}, and the helper stayed close."),
        ("What did the child want to do?", f"{child.id} wanted to {touch.gesture} {fruit.label}. That curious touch made a little messy moment possible."),
        ("How did the helper respond?", f"{helper.id} answered with kindness and gave a calm surprise. The helper used a careful fix so the fruit stayed lovely."),
        ("How did the story end?", f"It ended with the fruit still neat, the child smiling, and kindness making the day feel bright and sweet."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["fruit"].tags) | set(f["touch"].tags) | set(f["help_item"].tags) | set(f["setting"].tags)
    out = []
    if "fruit" in tags:
        out.append(("What is fruit?", "Fruit grows on trees or plants, and people often eat it because it can be sweet, juicy, and good for a snack."))
    if "touch" in tags:
        out.append(("What does it mean to touch something gently?", "A gentle touch is soft and careful, so it does not squeeze, poke, or hurt the thing you are touching."))
    if "kindness" in tags:
        out.append(("What is kindness?", "Kindness means helping, sharing, and speaking softly so another person feels cared for."))
    if "surprise" in tags:
        out.append(("What is a surprise?", "A surprise is something you did not expect. It can make the story feel exciting and happy."))
    if "springtimey" in tags or "bloom" in tags:
        out.append(("What makes a place feel springtimey?", "Flowers, fresh air, and bright green leaves can make a place feel springtimey and new."))
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
fruit(F) :- fruit_fact(F).
touch(T) :- touch_fact(T).
help(H) :- help_fact(H).

reasonable(S,F,T,H) :- setting(S), fruit(F), touch(T), help(H),
                        peelable(F), careful(T), sense(H,SH), SH >= 2.
sticky(F) :- chosen(F), rough(T), touch_touch(T), fruit_fact(F), messy(T, M), M >= 1.
surprise_done :- helped.
kind_story :- surprise_done.
#show reasonable/4.
#show kind_story/0.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for fid, fruit in FRUITS.items():
        lines.append(asp.fact("fruit_fact", fid))
        if fruit.peelable:
            lines.append(asp.fact("peelable", fid))
    for tid, touch in TOUCHES.items():
        lines.append(asp.fact("touch_touch", tid))
        lines.append(asp.fact("careful", tid))
        lines.append(asp.fact("rough", tid))
        lines.append(asp.fact("messy", tid, touch.messy))
    for hid, help_item in HELPS.items():
        lines.append(asp.fact("help_fact", hid))
        lines.append(asp.fact("sense", hid, help_item.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/4."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
        print("OK: default generation smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams(setting="garden", fruit="berries", touch="tap", help_item="napkin", child_name="Mia", child_gender="girl", helper_name="Mom", helper_gender="mother", trait="gentle"),
    StoryParams(setting="market", fruit="peach", touch="poke", help_item="basket", child_name="Theo", child_gender="boy", helper_name="Dad", helper_gender="father", trait="curious"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.fruit not in FRUITS or params.touch not in TOUCHES or params.help_item not in HELPS:
        raise StoryError("Invalid params for this storyworld.")
    world = tell(SETTINGS[params.setting], FRUITS[params.fruit], TOUCHES[params.touch], HELPS[params.help_item],
                 child_name=params.child_name, child_gender=params.child_gender,
                 helper_name=params.helper_name, helper_gender=params.helper_gender)
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
        print(asp_program("", "#show reasonable/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} reasonable combos:")
        for c in combos:
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
