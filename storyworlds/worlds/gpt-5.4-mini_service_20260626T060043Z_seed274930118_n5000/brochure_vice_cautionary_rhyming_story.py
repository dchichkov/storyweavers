#!/usr/bin/env python3
"""
Brochure & Vice: a tiny cautionary rhyming storyworld.

A child wants to make a bright brochure for a small sale. A workshop vice
could help flatten the paper, but it can also pinch fingers and crease the
pages if used carelessly. The story turns on a gentle warning, a near-miss,
and a safer choice that keeps the brochure neat and the fingers safe.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    danger: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    owner_item: bool = True


@dataclass
class Tool:
    id: str
    label: str
    use: str
    caution: str
    safe: str
    dangerous: bool = True
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "shop": Setting(place="the little shop", indoor=True, affords={"fold_brochure"}),
    "classroom": Setting(place="the classroom corner", indoor=True, affords={"fold_brochure"}),
    "library": Setting(place="the library table", indoor=True, affords={"fold_brochure"}),
}

ACTIVITIES = {
    "fold": Activity(
        id="fold",
        verb="fold the brochure",
        gerund="folding the brochure",
        rush="rush to flatten the brochure",
        mess="creased",
        soil="creased and bent",
        danger="a pinch from the vice",
        keyword="brochure",
        tags={"brochure"},
    )
}

PRIZES = {
    "brochure": Prize(
        label="brochure",
        phrase="a bright paper brochure with neat pictures",
        type="brochure",
    )
}

TOOLS = {
    "vice": Tool(
        id="vice",
        label="a steel vice",
        use="hold the paper flat",
        caution="could pinch fingers and crush the edges",
        safe="clamp the paper only with an adult's help",
        dangerous=True,
        tags={"vice"},
    ),
    "clipboard": Tool(
        id="clipboard",
        label="a clipboard",
        use="press the brochure flat",
        caution="keeps the page flat without pinching",
        safe="press the paper gently on the board",
        dangerous=False,
        tags={"safe"},
    ),
}

NAMES = ["Mina", "Toby", "June", "Iris", "Eli", "Pia", "Noah", "Luna"]
TRAITS = ["cheery", "careful", "curious", "brave"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize, tool: Tool) -> bool:
    return activity.id == "fold" and prize.label == "brochure" and tool.id == "vice"


def select_safe_tool(activity: Activity, prize: Prize) -> Optional[Tool]:
    if activity.id == "fold" and prize.label == "brochure":
        return TOOLS["clipboard"]
    return None


def explain_rejection(activity: Activity, prize: Prize, tool: Tool) -> str:
    return (
        f"(No story: {activity.gerund} with {tool.label} is not a reasonable cautionary "
        f"scene for {prize.label}. Try the vice with the brochure, or use the safer board.)"
    )


# ---------------------------------------------------------------------------
# World helpers
# ---------------------------------------------------------------------------
def setup_world(setting: Setting, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, memes={"joy": 0.0, "worry": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    hero.memes["trait"] = 1.0
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    world.facts["trait"] = trait
    return world


def predict_mess(world: World, hero: Entity, activity: Activity, prize: Entity, tool: Tool) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["worry"] += 1
    if tool.dangerous:
        return {"soiled": True, "pinch": True}
    return {"soiled": False, "pinch": False}


def intro(world: World, hero: Entity, trait: str, prize: Entity, tool: Tool) -> None:
    world.say(
        f"{hero.id} was a {trait} child with a plan so keen, "
        f"to make a brochure that looked bright and clean."
    )
    world.say(
        f"{hero.id} loved {prize.label}s with pictures and cheer, "
        f"and liked neat paper that held its shape near."
    )


def arrives(world: World, hero: Entity, setting: Setting, activity: Activity) -> None:
    world.say(
        f"One day at {setting.place}, the pages were near, "
        f"and {hero.id} said, '{activity.verb.capitalize()}!' with hope and with cheer."
    )


def warns(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, tool: Tool) -> None:
    pred = predict_mess(world, hero, activity, prize, tool)
    world.facts["pred"] = pred
    if pred["pinch"] or pred["soiled"]:
        world.say(
            f'"Careful," said {parent.label}, "that vice can bite, '
            f'and crease your brochure if you squeeze too tight."'
        )
        hero.memes["worry"] += 1.0
        hero.memes["curiosity"] = 1.0
        world.say(
            f"{hero.id} looked at the vice with a nervous glance, "
            f"for shiny steel jaws can tempt a quick dance."
        )


def near_miss(world: World, hero: Entity, tool: Tool) -> None:
    hero.memes["reach"] = 1.0
    world.say(
        f"{hero.id} reached for the vice, as if to begin, "
        f"but noticed the jaws and the pinch they could spin."
    )
    world.say(
        f"One finger was close to the cold metal seam, "
        f"and {hero.id} stopped short with a tiny alarmed gleam."
    )


def choose_safe_way(world: World, parent: Entity, hero: Entity, prize: Entity, tool: Tool) -> Optional[Tool]:
    safe_tool = select_safe_tool(world.facts["activity"], prize)
    if safe_tool is None:
        return None
    world.say(
        f'"Let us use the clipboard," the parent said true, '
        f'"It presses the page flat without hurting you."'
    )
    world.say(
        f"{hero.id} nodded and smiled at the kinder new plan, "
        f"for safe ways are better than quick, clumsy hands."
    )
    return safe_tool


def resolve(world: World, hero: Entity, parent: Entity, prize: Entity, safe_tool: Tool) -> None:
    hero.memes["joy"] += 1.0
    hero.memes["worry"] = 0.0
    world.say(
        f"They placed the brochure on board, neat and still, "
        f"and pressed it with care by a gentle small skill."
    )
    world.say(
        f"The pages stayed smooth, with no pinch and no tear; "
        f"{hero.id} could keep working with bright, steady cheer."
    )
    world.say(
        f"In the end the brochure looked crisp as a star, "
        f"and the vice stayed unused, just waiting nearby in the jar."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, tool: Tool,
         name: str = "Mina", gender: str = "girl", parent_type: str = "mother",
         trait: str = "careful") -> World:
    world = setup_world(setting, name, gender, parent_type, trait)
    hero = world.get(name)
    parent = world.get("Parent")
    prize = world.add(Entity(
        id=prize_cfg.label,
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
    ))
    world.facts["activity"] = activity
    world.facts["prize"] = prize
    world.facts["tool"] = tool

    intro(world, hero, trait, prize, tool)
    world.para()
    arrives(world, hero, setting, activity)
    warns(world, parent, hero, activity, prize, tool)
    near_miss(world, hero, tool)
    world.para()
    safe_tool = choose_safe_way(world, parent, hero, prize, tool)
    if safe_tool is None:
        raise StoryError("No safe alternative exists for this brochure-and-vice story.")
    resolve(world, hero, parent, prize, safe_tool)
    world.facts["safe_tool"] = safe_tool
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    activity = f["activity"]
    prize = f["prize"]
    tool = f["tool"]
    return [
        'Write a short rhyming cautionary story for a young child about a brochure and a vice.',
        f"Tell a gentle rhyming tale where {hero.id} wants to {activity.verb} with {tool.label}, "
        f"but {parent.label} warns that the vice could hurt the brochure.",
        f"Write a simple story that ends with a safer tool helping keep the {prize.label} neat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    activity = f["activity"]
    tool = f["tool"]
    safe_tool = f["safe_tool"]
    trait = world.facts["trait"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {tool.label}?",
            answer=f"{hero.id} wanted to {activity.verb}, but the vice was not the safest way to do it.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {hero.id} about the vice?",
            answer=(
                f"{parent.label} warned {hero.id} because the vice could pinch fingers "
                f"and crease the {prize.label}. That made the plan risky."
            ),
        ),
        QAItem(
            question=f"What safer tool helped {hero.id} finish the brochure?",
            answer=(
                f"The safer tool was {safe_tool.label}. It let {hero.id} keep the {prize.label} flat "
                f"without getting fingers caught."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} feel when the safer plan worked?",
            answer=(
                f"{hero.id} felt happy and calmer because the careful plan worked, and the brochure stayed neat."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a brochure?",
            answer="A brochure is a small folded paper with pictures and words, often used to share information.",
        ),
        QAItem(
            question="What is a vice?",
            answer="A vice is a tool with two jaws that hold something very tightly, so fingers must stay clear.",
        ),
        QAItem(
            question="Why should children be careful around a vice?",
            answer="Children should be careful because the jaws can pinch, squeeze, or crush paper and skin.",
        ),
    ]
    return out


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(fold, brochure) :- tool(vice).
has_safe_fix(fold, brochure) :- safe_tool(clipboard).
valid_story(Place, fold, brochure, Gender) :- setting(Place), wears(Gender, brochure),
                                             prize_at_risk(fold, brochure),
                                             has_safe_fix(fold, brochure).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("wears", "girl", pid))
        lines.append(asp.fact("wears", "boy", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if not t.dangerous:
            lines.append(asp.fact("safe_tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = {(place, "fold", "brochure", gender) for place in SETTINGS for gender in ("girl", "boy")}
    if clingo_set == python_set:
        print(f"OK: ASP matches Python story gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in ASP:", sorted(clingo_set - python_set))
    print("only in Python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming cautionary brochure-and-vice storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.activity and args.prize and args.tool:
        act = ACTIVITIES[args.activity]
        pr = PRIZES[args.prize]
        tl = TOOLS[args.tool]
        if not prize_at_risk(act, pr, tl):
            raise StoryError(explain_rejection(act, pr, tl))
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or "fold"
    prize = args.prize or "brochure"
    tool = args.tool or "vice"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, tool=tool,
                       name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        TOOLS[params.tool],
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="shop", activity="fold", prize="brochure", tool="vice", name="Mina", gender="girl", parent="mother", trait="careful"),
    StoryParams(place="library", activity="fold", prize="brochure", tool="vice", name="Eli", gender="boy", parent="father", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
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
            params = resolve_params(args, random.Random(seed))
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
