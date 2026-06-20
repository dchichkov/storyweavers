#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jab_kraft_transformation_mystery.py
====================================================================

A standalone story world for a small mystery about a child, a kraft-paper clue,
and a strange transformation that turns one thing into another after a jab.

Seed words:
- jab
- kraft

Feature:
- Transformation

Style:
- Mystery

The world is built to generate short, complete, child-facing stories with a
clear setup, a strange change, a clue-following turn, and a revealing ending.
It also includes:
- typed entities with meters and memes,
- a reasonableness gate,
- an inline ASP twin,
- three Q&A sets grounded in world state,
- and CLI support matching the Storyweavers contract.
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
JAB_MIN = 1
KRAFT_MIN = 1


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
    mood: str
    clues: list[str]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class MysteryItem:
    id: str
    label: str
    phrase: str
    material: str
    transform_into: str
    clue: str
    transforms: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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
            value = defaultdict(float)
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


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["transformed"] < THRESHOLD:
            continue
        sig = ("reveal", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "mystery" in world.entities:
            world.get("mystery").memes["puzzle"] += 1
        out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("reveal", "story", _r_reveal)]


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


def predict_transform(world: World, target_id: str, tool_id: str) -> dict:
    sim = world.copy()
    _do_jab(sim, sim.get(target_id), sim.get(tool_id), narrate=False)
    tgt = sim.get(target_id)
    return {
        "transformed": tgt.meters["transformed"] >= THRESHOLD,
        "confused": tgt.memes["confused"],
    }


def _do_jab(world: World, target: Entity, tool: Entity, narrate: bool = True) -> None:
    target.meters["jabbed"] += 1
    if tool.attrs.get("can_transform"):
        target.meters["transformed"] += 1
        target.memes["surprise"] += 1
        target.attrs["new_form"] = tool.attrs.get("turns_into", "something new")
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} found a strange little mystery in "
        f"{world.setting.place}. {world.setting.mood}"
    )
    world.say(
        f"It began with a kraft-paper clue: {world.setting.clues[0]}. "
        f"{child.id} knew it meant something important."
    )


def inspect(world: World, child: Entity, item: MysteryItem) -> None:
    world.say(
        f"{child.id} lifted the {item.label} and noticed how {item.phrase} "
        f"looked ordinary, almost plain, but not quite."
    )
    world.say(
        f"It had one odd mark: {item.clue}. That was the kind of detail that "
        f"made {child.id} think like a detective."
    )


def ask_help(world: World, helper: Entity, child: Entity) -> None:
    helper.memes["calm"] += 1
    world.say(
        f'{helper.id} peered over {child.pronoun("possessive")} shoulder and '
        f'said, "First we look. Then we try one careful jab."'
    )


def predict_and_warn(world: World, child: Entity, item: MysteryItem, tool: Tool) -> None:
    pred = predict_transform(world, item.id, tool.id)
    child.memes["worry"] += 1
    world.facts["predicted_transform"] = pred["transformed"]
    world.say(
        f'{child.id} frowned. "If I jab the {item.label} with the {tool.label}, '
        f"what will it become?"
    )


def jab(world: World, child: Entity, item: MysteryItem, tool: Tool) -> None:
    child.memes["boldness"] += 1
    world.say(
        f'{child.id} took a breath and gave the {item.label} one small jab with '
        f'the {tool.label}.'
    )
    _do_jab(world, world.get(item.id), world.get(tool.id))
    new_form = world.get(item.id).attrs.get("new_form", item.transform_into)
    world.say(
        f"At once, the {item.label} shimmered and turned into {new_form}. "
        f"The change was tiny, but it felt magical."
    )


def reveal(world: World, child: Entity, helper: Entity, item: MysteryItem, tool: Tool) -> None:
    world.say(
        f"Then {helper.id} smiled. The clue made sense at last: the kraft-paper "
        f"mark was not a warning at all. It was a sign of a transformable object."
    )
    world.say(
        f"The {item.label} had been made to change when it was jabbed by a tool "
        f"like the {tool.label}. That was why it had seemed so mysterious."
    )
    child.memes["joy"] += 1
    helper.memes["joy"] += 1


def ending(world: World, child: Entity, item: MysteryItem) -> None:
    form = world.get(item.id).attrs.get("new_form", item.transform_into)
    world.say(
        f"After that, {child.id} put the new {form} on the table and grinned. "
        f"The mystery was solved, and the little kraft clue had done its job."
    )
    world.say(
        f"By the end of the day, {child.id} was no longer puzzled. {child.id} "
        f"was ready for the next mystery."
    )


SETTINGS = {
    "attic": Setting("attic", "the dusty attic", "The air smelled old and quiet, and a single lamp made soft circles of light.", ["a kraft note was tucked under the lamp"]),
    "workshop": Setting("workshop", "the back workshop", "Tools hung on the wall, and the shelves were full of careful little boxes.", ["a kraft tag hung from the nail"]),
    "library": Setting("library", "the library corner", "The room was hushed, and every shelf looked as if it knew a secret.", ["a kraft envelope waited on a chair"]),
}

MYSTERY_ITEMS = {
    "box": MysteryItem("box", "box", "a small kraft box", "kraft", "tiny bird", "a jab-shaped dent on the lid", True, {"kraft", "transformation"}),
    "key": MysteryItem("key", "key", "a brass key in a kraft sleeve", "kraft", "silver key", "a paper label that said 'tap once'", True, {"kraft", "transformation"}),
    "token": MysteryItem("token", "token", "a round kraft token", "kraft", "bright coin", "three tiny arrows drawn around the edge", True, {"kraft", "transformation"}),
}

TOOLS = {
    "stylus": Tool("stylus", "stylus", "a thin stylus", "jab", 1, {"jab"}),
    "stick": Tool("stick", "stick", "a smooth little stick", "jab", 1, {"jab"}),
    "pointer": Tool("pointer", "pointer", "a wooden pointer", "jab", 1, {"jab"}),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    item: str
    tool: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        for iid, item in MYSTERY_ITEMS.items():
            for tid, tool in TOOLS.items():
                if item.transforms and "jab" in tool.tags and "kraft" in item.tags:
                    combos.append((sid, iid, tid))
    return combos


def reason_rejection(item: MysteryItem, tool: Tool) -> str:
    return f"(No story: this mystery needs a kraft object that can transform when jabbed, and the chosen parts do not fit.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld with a kraft clue and a transforming jab.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=MYSTERY_ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.item and args.tool:
        item, tool = MYSTERY_ITEMS[args.item], TOOLS[args.tool]
        if not (item.transforms and "jab" in tool.tags):
            raise StoryError(reason_rejection(item, tool))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, tool = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    child = args.name or rng.choice(["Lily", "Mia", "Noah", "Eli", "Ava", "Ben"])
    helper_gender = "woman" if child_gender == "girl" else "man"
    helper = args.helper or rng.choice(["Mina", "Ruth", "Mr. Kraft", "Uncle Jo"])
    return StoryParams(setting, item, tool, child, child_gender, helper, helper_gender)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="detective"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    item_cfg = MYSTERY_ITEMS[params.item]
    tool_cfg = TOOLS[params.tool]
    item = world.add(Entity(id="item", type=item_cfg.label, label=item_cfg.label, attrs={"new_form": item_cfg.transform_into}))
    tool = world.add(Entity(id="tool", type=tool_cfg.label, label=tool_cfg.label, attrs={"can_transform": True, "turns_into": item_cfg.transform_into}))
    opening(world, child)
    world.para()
    inspect(world, child, item_cfg)
    ask_help(world, helper, child)
    predict_and_warn(world, child, item_cfg, tool_cfg)
    world.para()
    jab(world, child, item_cfg, tool_cfg)
    reveal(world, child, helper, item_cfg, tool_cfg)
    ending(world, child, item_cfg)
    world.facts.update(child=child, helper=helper, item_cfg=item_cfg, tool_cfg=tool_cfg, outcome="transformed")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child that includes the words "jab" and "kraft" and ends with a transformation being understood.',
        f"Tell a gentle mystery where {f['child'].id} finds a kraft clue, gives one careful jab, and discovers that the object can change form.",
        f"Write a story with a puzzling kraft-paper object, a jab, and a clear solved ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, item_cfg, tool_cfg = f["child"], f["helper"], f["item_cfg"], f["tool_cfg"]
    new_form = world.get("item").attrs.get("new_form", item_cfg.transform_into)
    return [
        QAItem(
            question="What made the story feel like a mystery?",
            answer=f"{child.id} found a kraft clue, and the object did not make sense until it was examined carefully. The odd clue and the strange change both made the scene feel mysterious."
        ),
        QAItem(
            question=f"What happened when {child.id} gave the item a jab?",
            answer=f"The {item_cfg.label} changed into {new_form}. The jab was the careful move that made the transformation happen."
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{helper.id} helped {child.id} notice the clue and understand that the kraft object was meant to transform when jabbed. Once they saw that, the strange part of the story finally made sense."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kraft mean here?",
            answer="Kraft means plain brown paper material. It often looks simple, but in a mystery it can hide an important clue."
        ),
        QAItem(
            question="What does jab mean?",
            answer="A jab is a quick, small poke. In this story it is the careful action that makes the transformation happen."
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when one thing changes into another form. In mystery stories, that change can reveal an answer."
        ),
    ]


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
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={dict(m)}")
        if mm:
            bits.append(f"memes={dict(mm)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
valid(S, I, T) :- setting(S), item(I), tool(T), has_kraft(I), can_jab(T), transforms(I).
outcome(transformed) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for i, item in MYSTERY_ITEMS.items():
        lines.append(asp.fact("item", i))
        if item.transforms:
            lines.append(asp.fact("transforms", i))
        if "kraft" in item.tags:
            lines.append(asp.fact("has_kraft", i))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
        lines.append(asp.fact("can_jab", t))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
    sample = generate(resolve_params(build_parser().parse_args([]), _random.Random(7)))
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: empty story.")
    else:
        print("OK: smoke-test generation succeeded.")
    return rc


CURATED = [
    StoryParams("attic", "box", "stylus", "Lily", "girl", "Mina", "woman"),
    StoryParams("workshop", "key", "stick", "Noah", "boy", "Mr. Kraft", "man"),
    StoryParams("library", "token", "pointer", "Ava", "girl", "Ruth", "woman"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            header = f"### {s.params.child}: {s.params.item} in {s.params.setting}"
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
