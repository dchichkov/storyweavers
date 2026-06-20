#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gangster_pants_dim_absolute_curiosity_happy_ending.py
=====================================================================================

A small superhero-flavored story world about a curious kid, a dim pair of pants,
and an "absolute" choice to do the brave, kind thing.

Seed words and features:
- gangster
- pants-dim
- absolute
- Curiosity
- Happy Ending
- Style: Superhero Story

This world models a child who wants to peek into a shadowy basement stage where a
toy "gangster" costume box has been left behind. The curiosity can either lead to
a harmless surprise or a small scare, but the ending is always happy: a helper
shares a bright idea, the child uses a safe light, and the hidden thing becomes a
fun costume rather than a mystery.

The simulation uses typed entities with physical meters and emotional memes.
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

BRAVERY_INIT = 5.0
CURIOUS_INIT = 4.0


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
    safe_light: bool = False
    dim: bool = False
    costume: bool = False

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
    dark_spot: str
    hero_frame: str
    curious_frame: str
    opening: str

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
class Item:
    id: str
    label: str
    phrase: str
    note: str
    dim: bool = False
    costume: bool = False
    safe_light: bool = False
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
    text: str
    ending: str
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


def _r_shadow(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["shadow"] < THRESHOLD:
            continue
        sig = ("shadow", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "child" in world.entities:
            world.get("child").memes["curious_fear"] += 1
        out.append("__shadow__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["scary"] < THRESHOLD:
            continue
        sig = ("relief", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "child" in world.entities:
            world.get("child").memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("shadow", "physical", _r_shadow), Rule("relief", "emotional", _r_relief)]


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


def reasonable_response(r: Response) -> bool:
    return r.sense >= SENSE_MIN


def dim_pant_risk(item: Item) -> bool:
    return item.dim


def choice_is_reasonable(setting: Setting, pant: Item) -> bool:
    return setting.id in {"alley", "attic", "stage"} and pant.dim


def predict(world: World, item_id: str) -> dict:
    sim = world.copy()
    _peek(sim, sim.get(item_id), narrate=False)
    return {"shadow": sim.get(item_id).meters["shadow"] >= THRESHOLD, "scary": sim.get("basement").meters["scary"]}


def _peek(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["shadow"] += 1
    target.meters["mystery"] += 1
    propagate(world, narrate=narrate)


def open_scene(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"On a bright afternoon, {child.id} and {helper.id} turned {setting.place} "
        f"into a superhero hideout. {setting.opening}"
    )
    world.say(
        f"{child.id} loved that kind of adventure, because {setting.curious_frame}."
    )


def notice_dark(world: World, child: Entity, setting: Setting, pant: Item) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"But behind {setting.dark_spot}, something looked {pant.note}. "
        f"{child.id} leaned closer, because curiosity pulled like a cape in the wind."
    )


def worry(world: World, helper: Entity, child: Entity, pant: Item, parent: Entity) -> None:
    pred = predict(world, "pants")
    world.facts["predicted_shadow"] = pred["shadow"]
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} blinked. "{child.id}, we should be careful," {helper.pronoun()} said. '
        f'"That old costume could be hiding in the dark, and {pant.label} is way too dim to trust."'
    )
    world.say(
        f'"Let\'s ask {parent.label_word} before we go any farther," {helper.id} added.'
    )


def insist(world: World, child: Entity) -> None:
    child.memes["bravery"] += 1
    world.say(
        f'{child.id} took a deep breath. "I want to know for sure," {child.pronoun()} said. '
        f'"That mystery is absolutely calling me."'
    )


def gather_light(world: World, helper: Entity, child: Entity, light: Item) -> None:
    helper.meters["light"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{helper.id} found {light.phrase} and switched it on. It {light.note}, "
        f"and the dark spot stopped looking scary."
    )


def peek_and_reveal(world: World, child: Entity, item: Item) -> None:
    target = world.get("pants")
    _peek(world, target)
    world.say(
        f"{child.id} peered in and saw that the strange shape was just {item.phrase}. "
        f"It had been hiding in the shadows all along."
    )


def happy_turn(world: World, parent: Entity, child: Entity, helper: Entity, item: Item) -> None:
    parent.memes["pride"] += 1
    child.memes["joy"] += 1
    child.memes["bravery"] += 1
    world.say(
        f"Then {parent.label_word} came over with a smile. \"You were curious, and you asked for help -- "
        f"that was an absolutely brave choice,\" {parent.pronoun()} said."
    )
    world.say(
        f"{parent.id} lifted out the costume box and showed them the surprise: a gangster hat, "
        f"a fake badge, and {item.phrase}. \"It is only a costume,\" {parent.pronoun()} said, "
        f"\"and now you can try it on safely.\""
    )
    world.say(
        f"{child.id} laughed, because the mystery had turned into a game instead of a worry."
    )


def ending_image(world: World, child: Entity, item: Item, light: Item) -> None:
    world.say(
        f"In the end, {child.id} stood in the safe light, holding the badge and the bright flashlight, "
        f"with the dim pants folded neatly on the table. The superhero hideout was calm, "
        f"and the whole room felt warm and happy."
    )


def tell(setting: Setting, pant: Item, light: Item, response: Response,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_name: str = "Jay", helper_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    pants = world.add(Entity(id="pants", type="thing", label=pant.label, dim=True))
    lamp = world.add(Entity(id="light", type="thing", label=light.label, safe_light=True))
    bas = world.add(Entity(id="basement", type="room", label=setting.place))
    child.memes["bravery"] = BRAVERY_INIT
    child.memes["curiosity"] = CURIOUS_INIT

    open_scene(world, child, helper, setting)
    world.para()
    notice_dark(world, child, setting, pant)
    worry(world, helper, child, pant, parent)
    insist(world, child)
    gather_light(world, helper, child, light)
    peek_and_reveal(world, child, pant)
    world.para()
    happy_turn(world, parent, child, helper, pant)
    ending_image(world, child, pant, light)

    world.facts.update(
        child=child, helper=helper, parent=parent, setting=setting, pant_cfg=pant,
        light_cfg=light, response=response, outcome="happy", revealed=True
    )
    return world


SETTINGS = {
    "alley": Setting(
        "alley", "the alley behind the school", "a cardboard box",
        "the alley felt like a superhero base", "the shadows invited a closer look",
        "The cracked pavement and tall fence made it feel secret."
    ),
    "attic": Setting(
        "attic", "the dusty attic", "an old trunk",
        "the attic felt like a secret headquarters", "the quiet made every sound interesting",
        "The rafters were high, and old boxes sat like sleeping giants."
    ),
    "stage": Setting(
        "stage", "the school stage", "the curtain corner",
        "the stage felt like a heroic command center", "the half-lit props begged to be explored",
        "The stage lights were dim, and the props were stacked in a neat row."
    ),
}

ITEMS = {
    "pants": Item(
        "pants", "pants", "a pair of pants", "dim and dusty",
        dim=True, costume=True, tags={"gangster", "pants-dim"}
    ),
    "vest": Item(
        "vest", "vest", "a little costume vest", "dim and wrinkled",
        dim=True, costume=True, tags={"gangster"}
    ),
    "hat": Item(
        "hat", "hat", "a gangster hat", "dim on the shelf",
        dim=True, costume=True, tags={"gangster"}
    ),
}

LIGHTS = {
    "flashlight": Item(
        "flashlight", "flashlight", "a flashlight", "shone like a star",
        safe_light=True, tags={"curiosity"}
    ),
    "lamp": Item(
        "lamp", "lamp", "a small lamp", "glowed bright and warm",
        safe_light=True, tags={"curiosity"}
    ),
}

RESPONSES = {
    "ask_parent": Response(
        "ask_parent", 3,
        "asked the parent for help and waited by the doorway",
        "asked for help, and the mystery turned safe right away",
        "asked the parent for help and waited"
    ),
    "flashlight": Response(
        "flashlight", 3,
        "used a flashlight to look carefully",
        "used the flashlight and found a harmless costume",
        "used a flashlight to look carefully"
    ),
    "leave_it": Response(
        "leave_it", 2,
        "closed the box and left the dark spot alone until a grown-up came",
        "closed the box and left it for later",
        "closed the box and waited for a grown-up"
    ),
}



@dataclass
class StoryParams:
    setting: str
    item: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent: str
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
    for s in SETTINGS:
        for i in ITEMS:
            if choice_is_reasonable(SETTINGS[s], ITEMS[i]):
                for r in RESPONSES:
                    if reasonable_response(RESPONSES[r]):
                        combos.append((s, i, r))
    return combos


KNOWLEDGE = {
    "gangster": [("What is a gangster in a story?",
                 "In a story, a gangster can mean a pretend costume or a dramatic pretend character. It is not real trouble when the story is playing make-believe.")],
    "flashlight": [("What does a flashlight do?",
                    "A flashlight makes a safe light with batteries, so you can see in the dark without a flame.")],
    "curiosity": [("What is curiosity?",
                    "Curiosity is the feeling that makes you want to learn more and ask questions.")],
    "costume": [("What is a costume?",
                  "A costume is special clothing you wear for pretend play, shows, or dress-up.")],
    "dark": [("Why do people use a light in the dark?",
              "People use a light in the dark so they can see what is there and stay safe while exploring.")],
}


@dataclass
class StoryParams:
    setting: str
    item: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent: str
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

CURATED = [
    StoryParams("stage", "pants", "flashlight", "Mia", "girl", "Jay", "boy", "mother"),
    StoryParams("attic", "vest", "lamp", "Noah", "boy", "Ava", "girl", "father"),
    StoryParams("alley", "hat", "flashlight", "Lena", "girl", "Max", "boy", "mother"),
]



def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes the words "{f["pant_cfg"].label}", "gangster", and "absolute".',
        f"Tell a happy-ending story where {f['child'].id}'s curiosity leads to a shadowy costume surprise and a safe light helps.",
        f'Write a short story about a curious hero who finds {f["pant_cfg"].phrase} in a dark place and learns to ask for help.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    parent = f["parent"]
    pant = f["pant_cfg"]
    light = f["light_cfg"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, who was full of curiosity, and {helper.id}, who helped keep the adventure safe."),
        ("Why did the child want to look in the dark place?",
         f"{child.id} wanted to know what was hiding there, because curiosity made the mystery feel important. The dark spot looked strange, so {child.pronoun()} wanted to find out for sure."),
        ("How did they solve the problem?",
         f"They used {light.phrase} and asked the parent for help. That let them see that the scary shape was only {pant.phrase}."),
        ("How did the story end?",
         f"It ended happily, with the costume revealed and everyone smiling. {child.id} got to stay brave and safe at the same time."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["pant_cfg"].tags) | {"curiosity", "dark"}
    out: list[tuple[str, str]] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(items)
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
        if e.safe_light:
            bits.append("safe_light=True")
        if e.dim:
            bits.append("dim=True")
        if e.costume:
            bits.append("costume=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, pant: Item) -> str:
    return f"(No story: the dim-pants mystery needs a shadowy place, and this setting/item pair doesn't fit the curious superhero setup.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style curiosity story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.response and not reasonable_response(RESPONSES[args.response]):
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, response = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if child_gender == "girl" else "girl"
    child_name = args.child_name or rng.choice(["Mia", "Lena", "Ava", "Noah", "Kai", "Zoe"])
    helper_name = args.helper_name or rng.choice(["Jay", "Max", "Iris", "Nina", "Eli", "Ada"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, item, response, child_name, child_gender, helper_name, helper_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], LIGHTS["flashlight"], RESPONSES[params.response],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
reasonable_response(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, I, R) :- setting(S), item(I), response(R), shadow_fit(S, I), reasonable_response(R).
shadow_fit(S, I) :- dim(I), story_place(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("story_place", sid))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if i.dim:
            lines.append(asp.fact("dim", iid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3.\n#show reasonable_response/1."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if asp_set != py_set:
        print("MISMATCH")
        return 1
    print(f"OK: {len(asp_set)} combos match.")
    return 0


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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show reasonable_response/1."))
        return
    if args.asp:
        print(asp_program("#show valid/3.\n#show reasonable_response/1."))
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
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
