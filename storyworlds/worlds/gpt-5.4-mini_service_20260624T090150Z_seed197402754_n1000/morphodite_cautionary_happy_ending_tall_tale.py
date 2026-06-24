#!/usr/bin/env python3
"""
A tiny tall-tale storyworld about a morphodite, caution, and a happy ending.

Seed tale:
---
A lanky morphodite named Marny could stretch taller than a fence post or shrink
smaller than a teacup, and that was mighty handy in a town of crooked hills.
One windy afternoon, Marny found a shiny berry cart on the road and wanted to
snatch a taste before asking. The cart belonged to Old Pine, who warned that
the berries were still hot from the sun and would sting a curious tongue.
Marny ignored the warning, turned long as a ladder to reach the cart, and
nearly knocked the whole pile into the ditch. Then Marny's grandpa hollered,
"Easy now, little wonder! A clever morphodite doesn't grab first and think
later." Marny stopped, apologized, and used a small shape and a basket hook to
lift the berries without spilling them. Old Pine laughed, filled a bowl for
Marny, and said the town had room for big wonder and small caution both.

World model:
---
The morphodite can change size and shape, but careless reaching risks a spill.
The cautionary turn is driven by a warning, a near-miss, and a safer method.
The happy ending proves the lesson by showing the creature choosing the right
size and the right tool, ending with shared laughter and intact berries.
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

# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

SIZE_ORDER = ["tiny", "small", "normal", "tall", "towering"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    elder_name: str
    item: str
    tool: str
    size: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "market": "the windy market",
    "orchard": "the orchard",
    "bridge": "the high bridge",
    "fair": "the county fair",
}

ITEMS = {
    "berries": {
        "label": "berry cart",
        "food": "berries",
        "risk": "spill",
        "reason": "they would tumble into the dust",
        "vivid": "shiny sun-warm berries",
    },
    "eggs": {
        "label": "egg crate",
        "food": "eggs",
        "risk": "crack",
        "reason": "they would crack in a blink",
        "vivid": "a stack of pale eggs",
    },
    "cookies": {
        "label": "cookie tray",
        "food": "cookies",
        "risk": "smash",
        "reason": "they would smash into crumbs",
        "vivid": "butter cookies with sugar on top",
    },
}

TOOLS = {
    "hook": {
        "label": "basket hook",
        "use": "hook the load safely from below",
        "fixes": {"berries", "eggs", "cookies"},
    },
    "ladder": {
        "label": "little step ladder",
        "use": "reach without tipping the cart",
        "fixes": {"berries", "cookies"},
    },
    "gloves": {
        "label": "soft gloves",
        "use": "steady the tray with careful hands",
        "fixes": {"eggs", "cookies"},
    },
}

HEROES = ["Marny", "Pip", "Tessa", "Jory", "Lula", "Wren"]
ELDERS = ["Grandpa Coble", "Aunt Nell", "Old Pine", "Uncle Tallow"]

TRAITS = ["lanky", "nimble", "curious", "spindly", "bouncy", "bright-eyed"]


# ---------------------------------------------------------------------------
# World helpers
# ---------------------------------------------------------------------------

def size_index(size: str) -> int:
    return SIZE_ORDER.index(size)


def can_fix(item: str, tool: str) -> bool:
    return item in TOOLS[tool]["fixes"]


def reasonableness_check(params: StoryParams) -> None:
    if params.item not in ITEMS:
        raise StoryError("Unknown item.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if not can_fix(params.item, params.tool):
        raise StoryError(
            f"(No story: a {TOOLS[params.tool]['label']} can't safely solve the "
            f"{ITEMS[params.item]['label']} problem.)"
        )


def setup_world(params: StoryParams) -> World:
    world = World(setting=PLACES[params.place])
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        props={"size": params.size, "trait": random.choice(TRAITS)},
        meters={"reach": size_index(params.size)},
        memes={"wonder": 1.0, "impulse": 1.0},
    ))
    elder = world.add(Entity(
        id=params.elder_name,
        kind="character",
        type="grandfather" if "Grandpa" in params.elder_name else "elder",
        label=params.elder_name,
        meters={"wisdom": 1.0},
        memes={"care": 1.0},
    ))
    item_cfg = ITEMS[params.item]
    item = world.add(Entity(
        id="item",
        kind="thing",
        type=params.item,
        label=item_cfg["label"],
        caretaker=elder.id,
        props=item_cfg,
        meters={"balance": 1.0},
    ))
    tool_cfg = TOOLS[params.tool]
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type=params.tool,
        label=tool_cfg["label"],
        props=tool_cfg,
    ))

    world.facts.update(hero=hero, elder=elder, item=item, tool=tool, params=params)
    return world


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------

def introduce(world: World) -> None:
    hero = world.facts["hero"]
    item = world.facts["item"]
    world.say(
        f"{hero.id} was a {hero.props['trait']} morphodite who could stretch "
        f"long as a gatepost or shrink small as a pocket pebble."
    )
    world.say(
        f"In {world.setting}, {hero.id} loved looking at {item.props['vivid']} "
        f"and every other thing that seemed to shine back."
    )


def temptation(world: World) -> None:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    item = world.facts["item"]
    world.para()
    world.say(
        f"One blustery afternoon, {hero.id} spotted {item.props['vivid']} and "
        f"wanted a taste before asking."
    )
    world.say(
        f"{elder.id} lifted a warning finger and said the {item.label} would "
        f"{item.props['risk']} if {hero.id} reached too fast."
    )


def near_miss(world: World) -> None:
    hero = world.facts["hero"]
    item = world.facts["item"]
    params: StoryParams = world.facts["params"]
    world.say(
        f"But {hero.id} grew {params.size} and long as a fence rail, trying to "
        f"grab the {item.label} in one grand gulp of motion."
    )
    world.say(
        f"The cart wobbled, and the {item.label} nearly toppled because {item.props['reason']}."
    )
    hero.memes["alarm"] = 1.0
    hero.memes["shame"] = 1.0


def lesson_and_fix(world: World) -> None:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    item = world.facts["item"]
    tool = world.facts["tool"]
    params: StoryParams = world.facts["params"]

    world.para()
    world.say(
        f"{elder.id} called, 'Easy now, little wonder. A clever morphodite "
        f"doesn't grab first and think later.'"
    )
    hero.memes["caution"] = 1.0
    hero.props["size"] = "small"
    hero.meters["reach"] = size_index("small")
    world.say(
        f"{hero.id} stopped, took a small shape, and used the {tool.label} to "
        f"{tool.props['use']}."
    )
    if not can_fix(params.item, params.tool):
        raise StoryError("Internal error: unsafe tool selected for the item.")
    hero.memes["care"] = 1.0
    item.meters["balance"] = 0.0
    world.say(
        f"This time the {item.label} stayed steady, and the {item.props['food']} "
        f"did not spill a single bit."
    )
    hero.memes["joy"] = 1.0
    world.say(
        f"{elder.id} laughed, filled a bowl for {hero.id}, and said the town had "
        f"room for big wonder and small caution both."
    )


def tell(params: StoryParams) -> World:
    reasonableness_check(params)
    world = setup_world(params)
    introduce(world)
    temptation(world)
    near_miss(world)
    lesson_and_fix(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write a cautionary but happy tall tale about a morphodite named {p.hero_name} '
        f"who wants to {ITEMS[p.item]['food']} at {world.setting}.",
        f"Tell a child-friendly story where {p.elder_name} warns {p.hero_name} "
        f"not to rush the {ITEMS[p.item]['label']}, but the ending turns out happy.",
        f'Write a small tall tale that uses the word "morphodite" and ends with '
        f"caution, cleverness, and shared laughter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, item, tool, params = f["hero"], f["elder"], f["item"], f["tool"], f["params"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a {hero.props['trait']} morphodite who can change size.",
        ),
        QAItem(
            question=f"Why did {elder.id} warn {hero.id} about the {item.label}?",
            answer=(
                f"{elder.id} warned {hero.id} because the {item.label} would "
                f"{item.props['risk']} if {hero.id} reached too fast."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} do to solve the problem?",
            answer=(
                f"{hero.id} took a smaller shape and used the {tool.label} so the "
                f"{item.label} stayed steady."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended happily, with the {item.label} safe, {hero.id} smiling, "
                f"and {elder.id} laughing."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        QAItem(
            question="What is a morphodite?",
            answer=(
                "In this storyworld, a morphodite is a shapeshifting creature that "
                "can grow tall, shrink small, and choose the shape that fits the job."
            ),
        ),
        QAItem(
            question="Why is it smart to use a basket hook for berries?",
            answer=(
                "A basket hook helps lift or steady a load from a safer distance, so "
                "the berries are less likely to spill."
            ),
        ),
        QAItem(
            question="Why should someone listen to a warning before grabbing food?",
            answer=(
                "A warning can stop a messy mistake before it starts, which keeps food "
                "clean and helps everyone stay calm."
            ),
        ),
        QAItem(
            question="What kind of story is this?",
            answer=(
                "It is a cautionary story with a happy ending, told in a tall-tale style "
                "where the hero learns to be careful without losing the fun."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid if the selected tool can solve the selected item problem.
valid_story(P, H, E, I, T) :-
    place(P), hero(H), elder(E), item(I), tool(T),
    fixes(T, I).

% The cautionary beat is triggered when the elder warns and the item is at risk.
at_risk(I) :- item(I), risk(I, spill).
cautionary(I) :- at_risk(I), warning(E, I).

% The happy ending happens when the hero switches to a smaller size and uses a tool.
happy_ending(H, I, T) :- hero(H), item(I), tool(T), fixes(T, I), shrinks(H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("setting_name", pid, place))
    for iid, cfg in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("label", iid, cfg["label"]))
        lines.append(asp.fact("food", iid, cfg["food"]))
        lines.append(asp.fact("risk", iid, "spill"))
        lines.append(asp.fact("vivid", iid, cfg["vivid"]))
    for tid, cfg in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_label", tid, cfg["label"]))
        for fix in sorted(cfg["fixes"]):
            lines.append(asp.fact("fixes", tid, fix))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for e in ELDERS:
        lines.append(asp.fact("elder", e))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    python_ok = {(p, h, e, i, t) for p in PLACES for h in HEROES for e in ELDERS for i in ITEMS for t in TOOLS if can_fix(i, t)}
    clingo_ok = set(asp_valid_stories())
    if python_ok == clingo_ok:
        print(f"OK: clingo gate matches Python ({len(python_ok)} valid stories).")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(python_ok - clingo_ok))
    print("only in clingo:", sorted(clingo_ok - python_ok))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale morphodite storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-name", choices=HEROES)
    ap.add_argument("--hero-type", choices=["boy", "girl", "child"])
    ap.add_argument("--elder-name", choices=ELDERS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--size", choices=SIZE_ORDER)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(i, t) for i in ITEMS for t in TOOLS if can_fix(i, t)]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.item and args.tool and not can_fix(args.item, args.tool):
        raise StoryError(
            f"(No story: the {TOOLS[args.tool]['label']} cannot safely fix the "
            f"{ITEMS[args.item]['label']} problem.)"
        )
    combos = [
        (i, t) for i, t in combos
        if (args.item is None or i == args.item)
        and (args.tool is None or t == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item, tool = rng.choice(sorted(combos))
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        hero_name=args.hero_name or rng.choice(HEROES),
        hero_type=args.hero_type or rng.choice(["boy", "girl", "child"]),
        elder_name=args.elder_name or rng.choice(ELDERS),
        item=item,
        tool=tool,
        size=args.size or rng.choice(SIZE_ORDER[1:4]),
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.props:
            bits.append(f"props={e.props}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_stories())} valid stories.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for item in ITEMS:
            for tool in TOOLS:
                if can_fix(item, tool):
                    params = StoryParams(
                        place=args.place or "market",
                        hero_name=args.hero_name or "Marny",
                        hero_type=args.hero_type or "child",
                        elder_name=args.elder_name or "Old Pine",
                        item=item,
                        tool=tool,
                        size=args.size or "tall",
                    )
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
