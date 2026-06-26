#!/usr/bin/env python3
"""
storyworlds/worlds/pip_steep_hill_path_inner_monologue_humor.py
===============================================================

A tiny fairy-tale storyworld about Pip on a steep hill path, where inner
monologue and humor are part of the turning of the tale.

The seed tale behind this world:
---
Once upon a time, little Pip had to climb a steep hill path to deliver a warm
bun to Grandma at the hilltop cottage. The path was narrow and windy, and Pip
kept slipping a little. Pip worried, then noticed a crooked walking stick,
thought a silly thought about the hill trying to tickle her boots, and finally
used the stick and a steady song to reach the top with the bun still safe.
---

The world model tracks:
- physical meters: balance, soreness, wobble, safe_delivery
- emotional memes: worry, courage, humor, relief, pride

The story is generated from state changes, not from a frozen paragraph.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the steep hill path"
    feature: str = "steep"


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    risk: str
    helps_with: str
    owner_kind: str = "any"


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    name: str
    companion: str
    item: str
    tool: str
    seed: Optional[int] = None


SETTING = Setting()
PIP_NAMES = ["Pip"]
COMPANIONS = {
    "goat": "a small goat named Moss",
    "mole": "a helpful mole named Dot",
    "sparrow": "a bright sparrow named Siskin",
}
ITEMS = {
    "bun": Item(id="bun", label="bun", phrase="a warm honey bun", risk="crumbles", helps_with="steady hands"),
    "honey_pail": Item(id="honey_pail", label="pail of honey", phrase="a little pail of honey", risk="spills", helps_with="balance"),
    "lantern": Item(id="lantern", label="lantern", phrase="a tiny brass lantern", risk="bumps", helps_with="careful steps"),
}
TOOLS = {
    "stick": Tool(id="stick", label="walking stick", phrase="a crooked walking stick", helps_with="balance"),
    "shawl": Tool(id="shawl", label="shawl", phrase="a soft shawl tied as a pack", helps_with="free hands"),
}
NAMES = ["Pip"]
COMPANION_TYPES = ["goat", "mole", "sparrow"]


def _m(world: World, eid: str, key: str, delta: float) -> None:
    ent = world.get(eid)
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _e(world: World, eid: str, key: str, delta: float) -> None:
    ent = world.get(eid)
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _story_name(name: str) -> str:
    return name if name.lower() != "pip" else "Pip"


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    pip = world.add(Entity(id="pip", kind="character", type="girl", label="Pip"))
    companion = world.add(Entity(id="companion", kind="character", type=params.companion))
    item = world.add(Entity(id="item", type="thing", label=ITEMS[params.item].label, phrase=ITEMS[params.item].phrase, owner="pip", caretaker="companion"))
    tool = world.add(Entity(id="tool", type="thing", label=TOOLS[params.tool].label, phrase=TOOLS[params.tool].phrase, owner="pip", protective=True))

    world.facts.update(pip=pip, companion=companion, item=item, tool=tool, setting=SETTING)
    world.facts["item_key"] = params.item
    world.facts["tool_key"] = params.tool

    # Act 1
    world.say(f"Once upon a time, {_story_name(params.name)} was a little traveler on the steep hill path.")
    world.say(f"{_story_name(params.name)} carried {item.phrase} and wanted to reach the cottage at the hilltop before the tea went cold.")
    _e(world, "pip", "worry", 1)
    _e(world, "pip", "humor", 1)
    world.say(f"Inside, Pip thought, 'This hill looks like it could swallow a pebble and ask for seconds.'")

    world.para()

    # Act 2
    _m(world, "pip", "wobble", 1)
    _m(world, "item", "risk", 1)
    _e(world, "pip", "worry", 1)
    world.say("The path grew steeper, and Pip's feet began to slide on the little stones.")
    world.say(f"She hugged {item.label} close, but that made every step wobblier.")
    world.say("Then Pip had a funny thought: maybe the hill was not mean at all, only very ticklish.")

    # helper arrives / fix
    _e(world, "companion", "kindness", 1)
    _e(world, "pip", "humor", 1)
    world.say(f"{COMPANIONS[params.companion]} came along the bend and offered {tool.phrase}.")
    world.say(f"'Let's make the hill respect your boots,' the companion said, and Pip laughed so hard she stopped wobbling for a moment.")
    _m(world, "pip", "balance", 1)
    _m(world, "pip", "wobble", -1)
    _m(world, "item", "risk", -1)

    world.para()

    # Act 3
    _m(world, "pip", "safe_delivery", 1)
    _e(world, "pip", "relief", 1)
    _e(world, "pip", "pride", 1)
    _e(world, "pip", "courage", 1)
    world.say(f"With the walking stick in one hand and a careful song in her heart, Pip climbed step by step.")
    world.say(f"At last she reached the cottage and delivered {item.phrase} without a crumb out of place.")
    world.say("Pip grinned at the hill, as if to say it could try its tricks again, but not today.")

    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short fairy tale about Pip on a steep hill path, using inner monologue and a little humor.',
        'Tell a child-friendly story where Pip climbs a steep hill path, worries a bit, then finds a funny brave way to keep going.',
        'Write a fairy-tale style story with Pip, a steep hill path, a helpful tool, and a happy ending at the hilltop cottage.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    item: Entity = f["item"]
    tool: Entity = f["tool"]
    companion: Entity = f["companion"]
    return [
        QAItem(
            question="Who was the little traveler in the story?",
            answer="The little traveler was Pip, who went along the steep hill path with a warm bundle to deliver.",
        ),
        QAItem(
            question="What did Pip worry about on the steep hill path?",
            answer=f"Pip worried that the steep path would make {item.label} hard to carry safely and that she might wobble or slip.",
        ),
        QAItem(
            question="What helped Pip keep going?",
            answer=f"A crooked {tool.label} helped Pip steady her steps, and the kind companion helped her laugh and focus.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with Pip reaching the cottage at the hilltop and delivering {item.phrase} safely, feeling proud and relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a steep hill path?",
            answer="A steep hill path is a slanted walking path that goes upward, so it can be tiring and tricky to climb.",
        ),
        QAItem(
            question="What does a walking stick do?",
            answer="A walking stick gives a person extra balance when a road is uneven, steep, or slippery.",
        ),
        QAItem(
            question="Why can a silly thought help on a hard climb?",
            answer="A silly thought can make a person laugh, and laughter can ease worry and give fresh courage.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if abs(v) > 0}
        memes = {k: round(v, 2) for k, v in e.memes.items() if abs(v) > 0}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {', '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A thing is at risk on the steep hill path if it is carried during the climb.
at_risk(I) :- item(I), carried_on_path(I).

% The walking stick is a good fix if it helps with balance.
good_fix(T) :- tool(T), helps_with(T,balance).

% A valid story needs Pip, a risky carried item, and a tool that helps with balance.
valid_story(pip, I, T) :- at_risk(I), good_fix(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "steep_hill_path"))
    lines.append(asp.fact("feature", "steep"))
    lines.append(asp.fact("hero", "pip"))
    lines.append(asp.fact("name_word", "pip"))
    lines.append(asp.fact("path", "steep_hill_path"))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("carried_on_path", iid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("helps_with", tid, tool.helps_with))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {( "pip", iid, tid) for iid in ITEMS for tid in TOOLS}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  asp:", sorted(asp_set))
    print("  py :", sorted(py_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: Pip on a steep hill path with inner monologue and humor.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--companion", choices=COMPANION_TYPES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
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
        pass
    name = args.name or "Pip"
    companion = args.companion or rng.choice(COMPANION_TYPES)
    item = args.item or rng.choice(list(ITEMS))
    tool = args.tool or rng.choice(list(TOOLS))
    return StoryParams(name=name, companion=companion, item=item, tool=tool)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible story tuples:")
        for row in vals:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for companion in COMPANION_TYPES:
            for item in ITEMS:
                for tool in TOOLS:
                    params = StoryParams(name="Pip", companion=companion, item=item, tool=tool)
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
