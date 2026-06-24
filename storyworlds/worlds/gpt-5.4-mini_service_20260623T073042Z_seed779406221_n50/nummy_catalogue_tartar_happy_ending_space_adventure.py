#!/usr/bin/env python3
"""
storyworlds/worlds/nummy_catalogue_tartar_happy_ending_space_adventure.py
========================================================================

A small standalone story world for a Space Adventure-style tale about a child
who wants a nummy treat from a catalogue, but first must deal with tartar in a
gentle, happy-ending way.

Premise:
- A little astronaut loves a pictured snack called a "nummy".
- The catalogue shows shiny space goodies and a treat shop on the station.
- The problem is tartar: sticky teeth gunk that makes the snack feel wrong and
  worries the grown-up.

Turn:
- The child wants the nummy right away.
- The grown-up notices the tartar and explains that the teeth need help first.

Resolution:
- They brush, rinse, and then choose the nummy from the catalogue.
- The ending proves the state changed: clean teeth, happy child, snack enjoyed.

This world uses typed entities with physical meters and emotional memes, a
simple forward-chaining causal model, and an inline ASP twin for verification.
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
TARTAR_LIMIT = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    sky: str
    affords: set[str] = field(default_factory=set)


@dataclass
class CatalogueItem:
    id: str
    label: str
    phrase: str
    sparkle: str
    price: int
    tags: set[str] = field(default_factory=set)


@dataclass
class DentalTool:
    id: str
    label: str
    phrase: str
    action: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.teeth_clean: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.teeth_clean = self.teeth_clean
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_tartar_to_discomfort(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child is None:
        return out
    if child.meters["tartar"] < TARTAR_LIMIT:
        return out
    sig = ("tartar_discomfort",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["uneasy"] += 1
    out.append("The child felt sticky and uneasy.")
    return out


def _r_clean_teeth(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child is None:
        return out
    if child.meters["brushed"] < THRESHOLD:
        return out
    sig = ("clean_teeth",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["tartar"] = 0.0
    child.meters["clean"] += 1
    child.memes["pride"] += 1
    world.teeth_clean = True
    out.append("The tartar was gone, and the teeth were clean.")
    return out


CAUSAL_RULES = [
    Rule("tartar_to_discomfort", "social", _r_tartar_to_discomfort),
    Rule("clean_teeth", "physical", _r_clean_teeth),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def reasonableness_ok(item: CatalogueItem, tool: DentalTool) -> bool:
    return "tartar" in item.tags and "brush" in tool.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for item_id, item in CATALOGUE.items():
            for tool_id, tool in TOOLS.items():
                if reasonableness_ok(item, tool):
                    combos.append((setting, item_id, tool_id))
    return combos


def setting_line(setting: Setting, child: Entity) -> str:
    return f"{setting.place.capitalize()} floated under {setting.sky}, bright as a storybook sky."


def catalog_intro(item: CatalogueItem) -> str:
    return f"The catalogue showed {item.phrase}, and {item.sparkle} made it look extra special."


def predict_choice(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["tartar"] += 1
    propagate(sim, narrate=False)
    return {"clean": sim.teeth_clean, "uneasy": sim.get("child").memes["uneasy"]}


def tell(setting: Setting, item: CatalogueItem, tool: DentalTool,
         name: str = "Mina", gender: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=gender,
        label=name,
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
    ))
    nummy = world.add(Entity(
        id="nummy",
        type="food",
        label="nummy",
        phrase=item.phrase,
        owner=child.id,
    ))
    brush = world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
    ))
    child.meters["tartar"] = 1.0
    child.meters["brushed"] = 0.0
    child.memes["want"] = 1.0
    child.memes["joy"] = 0.0
    parent.memes["care"] = 1.0

    world.say(f"{child.label} was a little astronaut who loved shiny things and sweet snacks.")
    world.say(catalog_intro(item))
    world.say(f"{child.label} pointed at the picture and said, \"I want the {nummy.label_word}!\"")
    world.para()
    world.say(setting_line(setting, child))
    world.say(f"{parent.label_word.capitalize()} smiled, but noticed the tartar on {child.label}'s teeth.")
    predicted = predict_choice(world)
    if predicted["uneasy"] >= 1:
        world.say(f"\"Let's clean your teeth first,\" {parent.label_word} said. \"Then the {nummy.label_word} will taste better.\"")
    world.para()
    child.meters["brushed"] += 1
    world.say(f"{child.label} used {tool.phrase} and followed {tool.action}.")
    propagate(world, narrate=True)
    world.para()
    child.memes["joy"] += 1
    world.say(f"After that, {child.label} picked the {nummy.label_word} from the catalogue and took a happy bite.")
    world.say(f"{child.label}'s smile sparkled in the station light, and {parent.label_word} was proud.")
    world.facts.update(
        child=child,
        parent=parent,
        item=item,
        tool=tool,
        nummy=nummy,
        setting=setting,
        resolved=world.teeth_clean,
    )
    return world


SETTINGS = {
    "space_station": Setting(place="the space station market", sky="the dome above the station", affords={"catalogue"}),
    "moon_shop": Setting(place="the moon shop", sky="the silver moon ceiling", affords={"catalogue"}),
    "ship_bay": Setting(place="the starship bay", sky="the glowing bay lights", affords={"catalogue"}),
}

CATALOGUE = {
    "astro_cookie": CatalogueItem(
        id="astro_cookie",
        label="astro-cookie",
        phrase="a crumbly astro-cookie with tiny star sprinkles",
        sparkle="the sugar stars shimmered on the page",
        price=3,
        tags={"tartar", "sweet"},
    ),
    "moon_muffin": CatalogueItem(
        id="moon_muffin",
        label="moon muffin",
        phrase="a moon muffin with a round silver wrapper",
        sparkle="the wrapper glinted like a little moon",
        price=4,
        tags={"tartar", "soft"},
    ),
    "comet_cup": CatalogueItem(
        id="comet_cup",
        label="comet cup",
        phrase="a comet cup with orange cream",
        sparkle="the orange swirl looked fast and fun",
        price=2,
        tags={"tartar", "bright"},
    ),
}

TOOLS = {
    "brush": DentalTool(
        id="brush",
        label="toothbrush",
        phrase="a small toothbrush",
        action="brushed in gentle circles",
        tags={"brush", "clean"},
    ),
    "rinse_cup": DentalTool(
        id="rinse_cup",
        label="rinse cup",
        phrase="a tiny rinse cup",
        action="rinsed away the foam",
        tags={"brush", "clean"},
    ),
}


GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nia", "Zoe", "Ari", "Tia"]
BOY_NAMES = ["Kai", "Noah", "Leo", "Milo", "Finn", "Ray", "Ezra"]


@dataclass
class StoryParams:
    setting: str
    item: str
    tool: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Happy Ending Space Adventure story for a 3-to-5-year-old about a child named {f["child"].label} who wants a {f["item"].label} from a catalogue but needs to handle tartar first.',
        f"Tell a gentle space story where {f['child'].label} looks at the catalogue, cleans tartar with {f['tool'].phrase}, and then gets the nummy snack.",
        f'Write a simple story with the words "nummy", "catalogue", and "tartar" that ends with a bright smile and a happy bite.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, item, tool = f["child"], f["parent"], f["item"], f["tool"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.label}, a little astronaut who wanted the snack from the catalogue.",
        ),
        QAItem(
            question=f"What did {child.label} want from the catalogue?",
            answer=f"{child.label} wanted the {item.label}, a tasty nummy snack from the catalogue.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} ask to clean up first?",
            answer=f"{parent.label_word.capitalize()} noticed tartar on {child.label}'s teeth and wanted them clean before the snack.",
        ),
        QAItem(
            question=f"How did {child.label} fix the tartar?",
            answer=f"{child.label} used {tool.phrase} and brushed until the tartar was gone.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The teeth were clean, the nummy was enjoyed, and everyone ended happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tartar?",
            answer="Tartar is sticky gunk that can build up on teeth if they are not cleaned well.",
        ),
        QAItem(
            question="What is a catalogue?",
            answer="A catalogue is a book or page with pictures of things you can choose or buy.",
        ),
        QAItem(
            question="Why do people brush their teeth?",
            answer="People brush their teeth to help remove food bits and tartar and keep their mouths clean.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
need_clean(X) :- tartar(X), not brushed(X).
happy_end(X) :- brushed(X), tartar_gone(X).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in CATALOGUE:
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("tartar_item", iid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("brush_tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(valid_combos()) == set(asp_valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("Mismatch between ASP and Python combos.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure story world about nummy, catalogue, and tartar.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=CATALOGUE)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, item=item, tool=tool, name=name, gender=gender, parent=parent)


def valid_combo_set() -> list[tuple[str, str, str]]:
    return [(s, i, t) for s in SETTINGS for i in CATALOGUE for t in TOOLS if reasonableness_ok(CATALOGUE[i], TOOLS[t])]


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    item = CATALOGUE[params.item]
    tool = TOOLS[params.tool]
    world = tell(setting, item, tool, params.name, params.gender, params.parent)
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


CURATED = [
    StoryParams(setting="space_station", item="astro_cookie", tool="brush", name="Mina", gender="girl", parent="mother"),
    StoryParams(setting="moon_shop", item="moon_muffin", tool="rinse_cup", name="Kai", gender="boy", parent="father"),
    StoryParams(setting="ship_bay", item="comet_cup", tool="brush", name="Luna", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
