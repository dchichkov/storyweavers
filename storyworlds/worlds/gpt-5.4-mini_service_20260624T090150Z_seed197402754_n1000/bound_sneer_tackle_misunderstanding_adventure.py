#!/usr/bin/env python3
"""
A small adventure storyworld about a misunderstanding on a trail.

A child and a helper set out on a little quest with a map, a rope, and a
stubborn obstacle. The tension comes from a misunderstanding: one character
thinks the other is sneering at the plan, but the expression is really about
something else. The resolution uses a careful tackle of the obstacle and a
renewed bound forward into the adventure.
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
# World model
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)   # physical
    memes: dict[str, float] = field(default_factory=dict)    # emotional

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    feature: str = "trail"
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    challenge: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    kind: str = "tool"


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    blocks: set[str]
    needs: set[str]


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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "trail": Setting(place="the pine trail", feature="trail", outdoors=True, affords={"climb", "cross", "race"}),
    "cave": Setting(place="the little cave", feature="cave", outdoors=True, affords={"climb", "cross"}),
    "harbor": Setting(place="the windy harbor path", feature="path", outdoors=True, affords={"cross", "race"}),
}

ACTIONS = {
    "climb": Action(
        id="climb",
        verb="climb the ridge",
        gerund="climbing the ridge",
        rush="bound up the rocks",
        challenge="steep stones",
        keyword="ridge",
        tags={"rock", "adventure"},
    ),
    "cross": Action(
        id="cross",
        verb="cross the stream",
        gerund="crossing the stream",
        rush="tackle the wet stones",
        challenge="slippery stones",
        keyword="stream",
        tags={"water", "adventure"},
    ),
    "race": Action(
        id="race",
        verb="race to the old flag",
        gerund="racing to the old flag",
        rush="bound toward the flag",
        challenge="a long path",
        keyword="flag",
        tags={"race", "adventure"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a sturdy rope",
        helps={"climb"},
    ),
    "boots": Tool(
        id="boots",
        label="boots",
        phrase="a pair of boots with good grip",
        helps={"cross"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a small lantern",
        helps={"cave"},
    ),
}

OBSTACLES = {
    "wall": Obstacle(
        id="wall",
        label="wall",
        phrase="a high stone wall",
        blocks={"climb"},
        needs={"rope"},
    ),
    "stream": Obstacle(
        id="stream",
        label="stream",
        phrase="a shallow stream full of slick stones",
        blocks={"cross"},
        needs={"boots"},
    ),
    "dark": Obstacle(
        id="dark",
        label="darkness",
        phrase="a dark bend inside the cave",
        blocks={"cave"},
        needs={"lantern"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tessa", "June", "Ivy"]
BOY_NAMES = ["Eli", "Theo", "Milo", "Finn", "Ari", "Jude"]
TRAITS = ["brave", "curious", "spirited", "cheerful", "bold"]

CURATED = [
    ("trail", "climb", "rope"),
    ("trail", "cross", "boots"),
    ("cave", "cross", "boots"),
]

# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    place: str
    action: str
    tool: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
action(A) :- act(A).
tool(T) :- item(T).
setting(P) :- place(P).

needs_tool(A,T) :- action(A), tool(T), helps(T,A).
valid(P,A,T) :- setting(P), action(A), tool(T), affords(P,A), needs_tool(A,T).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("act", aid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("item", tid))
        for a in sorted(t.helps):
            lines.append(asp.fact("helps", tid, a))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for action_id in s.affords:
            if action_id not in ACTIONS:
                continue
            for tool_id, tool in TOOLS.items():
                if action_id in tool.helps:
                    combos.append((place, action_id, tool_id))
    return combos


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1

# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------


def predict_safety(world: World, hero: Entity, action: Action, tool: Tool, obstacle: Obstacle) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters[action.id] = 1.0
    return tool.id in obstacle.needs


def introduce(world: World, hero: Entity, helper: Entity, action: Action, tool: Tool) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved adventure.")
    world.say(f"{hero.pronoun().capitalize()} and {helper.label} were set to {action.gerund} with {tool.phrase} ready.")


def misunderstanding(world: World, hero: Entity, helper: Entity, action: Action) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(f"At the trail, {hero.id} wanted to {action.verb}.")
    world.say(f"Then {helper.label} gave a quick sneer at the rocky path, and {hero.id} thought it was at the plan.")


def explain(world: World, helper: Entity, hero: Entity) -> None:
    hero.memes["worry"] = 0
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.say(f'But the sneer was only because a pebble had slipped into {helper.pronoun("possessive")} shoe.')
    world.say(f'{helper.label} shook {helper.pronoun("possessive")} head and said, "I was not sneering at you. I was sneering at that pebble!"')


def tackle_obstacle(world: World, hero: Entity, helper: Entity, action: Action, tool: Tool, obstacle: Obstacle) -> None:
    hero.meters[action.id] = hero.meters.get(action.id, 0) + 1
    hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1
    world.say(f"With the mix-up cleared up, they used {tool.phrase} to tackle {obstacle.phrase}.")
    if action.id == "climb":
        world.say(f"{hero.id} could bound up one rock at a time, and the rope kept every step safe.")
    elif action.id == "cross":
        world.say(f"{hero.id} had to tackle the slippery stones carefully, but the boots kept the feet steady.")
    else:
        world.say(f"They moved fast, and {hero.id} could bound ahead while {helper.label} kept pace.")


def resolution(world: World, hero: Entity, helper: Entity, action: Action) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(f"In the end, {hero.id} grinned, because the trail did not win the day.")
    world.say(f"{hero.id} went on {action.gerund}, and {helper.label} stayed beside {hero.pronoun('object')} with a proud smile.")


def tell(setting: Setting, action: Action, tool: Tool, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    obstacle = next((o for o in OBSTACLES.values() if action.id in o.blocks and tool.id in o.needs), None)
    if obstacle is None:
        raise StoryError("No obstacle/tool pairing can support this adventure.")
    world.facts.update(hero=hero, helper=helper, action=action, tool=tool, obstacle=obstacle, setting=setting)
    introduce(world, hero, helper, action, tool)
    world.para()
    misunderstanding(world, hero, helper, action)
    explain(world, helper, hero)
    world.para()
    tackle_obstacle(world, hero, helper, action, tool, obstacle)
    resolution(world, hero, helper, action)
    return world

# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, action, tool = f["hero"], f["helper"], f["action"], f["tool"]
    return [
        f'Write a short adventure story for a young child about {hero.id} and {helper.label} who {action.verb} with {tool.phrase}.',
        f'Create a gentle story with a misunderstanding, a sneer that is not rude, and a brave tackle of {action.keyword}.',
        f'Write a small adventure where a child named {hero.id} uses {tool.label} to solve a trail problem after a misunderstanding.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, action, tool, obstacle = f["hero"], f["helper"], f["action"], f["tool"], f["obstacle"]
    return [
        QAItem(
            question=f"What did {hero.id} think when {helper.label} sneered at the trail?",
            answer=f"{hero.id} thought the sneer was about the plan, so {hero.pronoun('subject')} felt worried for a moment.",
        ),
        QAItem(
            question=f"Why was the sneer really not mean?",
            answer=f"It was not mean because {helper.label} was only reacting to a pebble in {helper.pronoun('possessive')} shoe.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.label} tackle {obstacle.phrase}?",
            answer=f"They used {tool.phrase} to tackle {obstacle.phrase}, and that helped them keep going on the adventure.",
        ),
        QAItem(
            question=f"What did {hero.id} do after the misunderstanding was fixed?",
            answer=f"{hero.id} went on {action.gerund} with a grin, feeling brave again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to tackle a problem?",
            answer="To tackle a problem means to face it directly and work on it instead of walking away from it.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing about what another person meant.",
        ),
        QAItem(
            question="What is a sneer?",
            answer="A sneer is a face or sound that looks rude or annoyed, even if the reason is something small.",
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

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with a misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "friend"])
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


def explain_rejection(place: str, action: str, tool: str) -> str:
    return f"(No story: {tool} does not fit {action} at {place} in this adventure world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.action and args.tool:
        if (args.place, args.action, args.tool) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.action, args.tool))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "friend"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, action=action, tool=tool, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], TOOLS[params.tool], params.name, params.gender, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, action, tool) combos:\n")
        for p, a, t in combos:
            print(f"  {p:8} {a:8} {t:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, (place, action, tool) in enumerate(CURATED):
            params = StoryParams(
                place=place,
                action=action,
                tool=tool,
                name=GIRL_NAMES[i % len(GIRL_NAMES)],
                gender="girl" if i % 2 == 0 else "boy",
                helper="friend",
                trait=TRAITS[i % len(TRAITS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.action} at {p.place} ({p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
