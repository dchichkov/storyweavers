#!/usr/bin/env python3
"""
storyworlds/worlds/high_suspense_bravery_twist_slice_of_life.py
===============================================================

A small storyworld about a child, a height-related worry, a brave choice,
and a gentle twist that turns the day into a calm slice of life story.

The seed idea:
- A child wants something from a high place.
- The child feels suspense because the item seems hard or scary to reach.
- A brave helper or the child themselves solves it in a careful way.
- A twist changes what they think they need or what is actually important.

This world stays small and concrete: a few typed entities, meters for physical
state, memes for emotions, and a simple causal engine that drives the prose.

Features:
- Suspense: something is out of reach or uncertain.
- Bravery: the hero acts despite worry.
- Twist: the final solution is not the first thing the hero expected.
- Slice of life: the stakes are small, familiar, and child-facing.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    height: str = ""
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Place:
    name: str
    high_place: str
    supports: set[str] = field(default_factory=set)  # what can be reached here
    height_words: tuple[str, ...] = ("high", "tall", "top")


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    location: str
    height: str
    wants: str
    surprise: str
    accessible_with: set[str] = field(default_factory=set)
    is_reward: bool = False


@dataclass
class HelperTool:
    id: str
    label: str
    phrase: str
    helps_with: set[str] = field(default_factory=set)
    safe: bool = True


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    tools: dict[str, HelperTool] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_item(self, i: Item) -> Item:
        self.items[i.id] = i
        return i

    def add_tool(self, t: HelperTool) -> HelperTool:
        self.tools[t.id] = t
        return t

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    item: str
    tool: str
    seed: Optional[int] = None


PLACES = {
    "library_stairs": Place(name="the library stairs", high_place="the high shelf", supports={"book", "box"}),
    "kitchen_step": Place(name="the kitchen", high_place="the high cabinet", supports={"jar", "bowl"}),
    "porch": Place(name="the porch", high_place="the top hook", supports={"coat", "lantern"}),
    "classroom": Place(name="the classroom", high_place="the tall cupboard", supports={"paper", "game"}),
}

ITEMS = {
    "book": Item(
        id="book",
        label="picture book",
        phrase="a picture book with bright blue whales",
        location="high shelf",
        height="high",
        wants="read it before dinner",
        surprise="it was only a library book that had to go back",
        accessible_with={"step", "stool"},
    ),
    "jar": Item(
        id="jar",
        label="cookie jar",
        phrase="the cookie jar with the red lid",
        location="high cabinet",
        height="high",
        wants="open it for a snack",
        surprise="it held buttons instead of cookies",
        accessible_with={"step", "reach"},
    ),
    "coat": Item(
        id="coat",
        label="raincoat",
        phrase="a yellow raincoat",
        location="top hook",
        height="high",
        wants="wear it outside",
        surprise="it belonged to the helper",
        accessible_with={"hook", "reach"},
    ),
    "box": Item(
        id="box",
        label="toy box",
        phrase="a small toy box",
        location="high shelf",
        height="high",
        wants="find the missing train",
        surprise="the train was in the pocket of a jacket instead",
        accessible_with={"step", "stool"},
    ),
}

TOOLS = {
    "stepstool": HelperTool(
        id="stepstool",
        label="step stool",
        phrase="a sturdy little step stool",
        helps_with={"step", "reach", "stool"},
    ),
    "chair": HelperTool(
        id="chair",
        label="chair",
        phrase="a kitchen chair",
        helps_with={"step", "reach"},
    ),
    "tongs": HelperTool(
        id="tongs",
        label="tongs",
        phrase="a pair of kitchen tongs",
        helps_with={"hook"},
    ),
    "ladder": HelperTool(
        id="ladder",
        label="ladder",
        phrase="a short folding ladder",
        helps_with={"step", "reach", "hook", "stool"},
    ),
}

HERO_NAMES = ["Mina", "Owen", "Lia", "Theo", "Nina", "Ari", "Maya", "Finn"]
HELPER_NAMES = ["Mom", "Dad", "Grandma", "Grandpa", "Aunt June", "Uncle Ray"]
TRAITS = ["curious", "quiet", "careful", "brave", "gentle", "patient"]


class WorldState:
    def __init__(self, world: World) -> None:
        self.world = world
        self.hero = world.entities["hero"]
        self.helper = world.entities["helper"]
        self.item = world.items[world.facts["item"]]
        self.tool = world.tools[world.facts["tool"]]

    def item_is_high(self) -> bool:
        return self.item.height == "high"

    def safe_tool_available(self) -> bool:
        return bool(self.tool.helps_with & self.item.accessible_with)

    def suspense_level(self) -> float:
        return self.hero.memes.get("worry", 0.0) + self.item.meters.get("out_of_reach", 0.0)

    def resolved(self) -> bool:
        return self.world.facts.get("resolved", False)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small slice-of-life storyworld about height, suspense, bravery, and a twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["mother", "father", "grandmother", "grandfather", "aunt", "uncle"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for i in ITEMS:
            for t in TOOLS:
                item = ITEMS[i]
                tool = TOOLS[t]
                if tool.helps_with & item.accessible_with:
                    combos.append((p, i, t))
    return combos


def select_name(rng: random.Random, gender: str) -> str:
    return rng.choice(HERO_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, tool = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(list({k for k in ["mother", "father", "grandmother", "grandfather", "aunt", "uncle"]}))
    return StoryParams(
        place=place,
        hero=args.hero or select_name(rng, hero_type),
        hero_type=hero_type,
        helper=args.helper or rng.choice(HELPER_NAMES),
        helper_type=helper_type,
        item=item,
        tool=tool,
    )


def _narrate_setup(world: World) -> None:
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    item = world.items[world.facts["item"]]
    world.say(
        f"{hero.id} was a {world.facts['trait']} {hero.type} who noticed small things, especially when something sat high up."
    )
    world.say(
        f"One afternoon, {hero.id} saw {item.phrase} up on {item.location} and wanted to {item.wants}."
    )
    world.say(
        f"{helper.id} was nearby too, folding laundry and listening, because in this house even little requests could turn into tiny adventures."
    )


def _narrate_suspense(world: World) -> None:
    hero = world.entities["hero"]
    item = world.items[world.facts["item"]]
    world.say(
        f"{hero.id} looked up and felt a quiet suspense. {item.label.capitalize()} was just high enough to be tempting, but not quite easy to reach."
    )
    hero.memes["worry"] += 1
    item.meters["out_of_reach"] = 1.0
    world.say(
        f"{hero.id} stood on tiptoe, then took a careful breath. {hero.pronoun().capitalize()} did not want to wobble or bump anything."
    )


def _narrate_bravery(world: World) -> None:
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    tool = world.tools[world.facts["tool"]]
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} got brave and asked, 'Could we use {tool.phrase}?'"
    )
    world.say(
        f"{helper.id} smiled. 'That is a good idea. Brave does not have to mean fast.'"
    )


def _narrate_twist(world: World) -> None:
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    item = world.items[world.facts["item"]]
    tool = world.tools[world.facts["tool"]]
    world.say(
        f"Together they used {tool.phrase}, and the high thing came down safely."
    )
    world.say(
        f"But then came the twist: {item.surprise}, so the whole rush had been about the wrong guess."
    )
    hero.memes["surprise"] += 1
    hero.memes["relief"] = 1.0
    world.facts["resolved"] = True
    world.say(
        f"{hero.id} laughed in relief, and {helper.id} laughed too, because sometimes the best part of a day is learning what the thing really was."
    )


def tell(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])

    hero = world.add_entity(Entity(id=params.hero, kind="character", type=params.hero_type))
    helper = world.add_entity(Entity(id=params.helper, kind="character", type=params.helper_type))
    item = world.add_item(ITEMS[params.item])
    tool = world.add_tool(TOOLS[params.tool])

    world.facts.update(
        hero=hero,
        helper=helper,
        item=params.item,
        tool=params.tool,
        trait=params.hero_type if params.hero_type in {"girl", "boy"} else "curious",
        place=params.place,
    )

    hero.memes["curiosity"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["bravery"] = 0.0
    helper.meters["care"] = 1.0

    _narrate_setup(world)
    world.para()
    _narrate_suspense(world)
    world.para()
    _narrate_bravery(world)
    world.para()
    _narrate_twist(world)

    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    item = world.items[world.facts["item"]]
    return [
        f"Write a gentle story about {hero.id} and a high-up surprise at {world.place.name}.",
        f"Tell a slice-of-life story where {hero.id} feels suspense, asks for help, and stays brave.",
        f"Write a child-friendly story that ends with a twist about {item.label} and {helper.id}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    item = world.items[world.facts["item"]]
    tool = world.tools[world.facts["tool"]]
    return [
        QAItem(
            question=f"Why did {hero.id} feel suspense in the story?",
            answer=f"{hero.id} felt suspense because {item.label} was high up and not easy to reach right away."
        ),
        QAItem(
            question=f"What brave thing did {hero.id} do before anything was taken down?",
            answer=f"{hero.id} got brave and asked to use {tool.phrase} instead of climbing unsafely."
        ),
        QAItem(
            question=f"What was the twist at the end?",
            answer=f"The twist was that {item.surprise}, so they had been worried about the wrong thing."
        ),
        QAItem(
            question=f"Who helped {hero.id}?",
            answer=f"{helper.id} helped by staying calm and using {tool.phrase} carefully."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when something is high up?",
            answer="Something high up is far above the ground or placed where you have to stretch or use a helper to reach it."
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next, especially when something might go wrong."
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing something careful and useful even when you feel a little scared."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what the reader thought was happening."
        ),
    ]


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
    for e in world.entities.values():
        lines.append(f"  entity {e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    for i in world.items.values():
        lines.append(f"  item {i.id}: height={i.height} meters={i.meters}")
    for t in world.tools.values():
        lines.append(f"  tool {t.id}: helps_with={sorted(t.helps_with)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
item(I) :- prize(I).
tool(T) :- gear(T).

high_item(I) :- prize(I), worn_on(I, high).
can_help(T, I) :- gear(T), prize(I), helps(T, M), accessible(I, M).
valid_story(P, I, T) :- setting(P), prize(I), gear(T), can_help(T, I).

% The declarative twin of the reasonableness gate:
% a story is valid when the item is high and the tool can help reach it.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("prize", iid))
        lines.append(asp.fact("worn_on", iid, item.height))
        for a in sorted(item.accessible_with):
            lines.append(asp.fact("accessible", iid, a))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("gear", tid))
        for h in sorted(tool.helps_with):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_story_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_story_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_story_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="library_stairs", hero="Mina", hero_type="girl", helper="Mom", helper_type="mother", item="book", tool="stepstool"),
    StoryParams(place="kitchen_step", hero="Owen", hero_type="boy", helper="Dad", helper_type="father", item="jar", tool="chair"),
    StoryParams(place="porch", hero="Lia", hero_type="girl", helper="Grandma", helper_type="grandmother", item="coat", tool="tongs"),
    StoryParams(place="classroom", hero="Theo", hero_type="boy", helper="Aunt June", helper_type="aunt", item="box", tool="ladder"),
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, tool) combos:\n")
        for place, item, tool in combos:
            print(f"  {place:15} {item:8} {tool:10}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.hero}: {p.item} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
