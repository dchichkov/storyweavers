#!/usr/bin/env python3
"""
A tall-tale storyworld about a mother, her agency, and a conflict on a fallen
tree trail.

Seed image:
- A mother and child find a huge fallen tree blocking a trail.
- The child wants to turn back, but the mother keeps her agency steady.
- She studies the obstacle, finds a clever path, and turns the trouble into a
  brave crossing.
- The story ends with the trail opened again and the family feeling taller than
  the trees.

This world is built as a small classical simulation:
- typed entities with meters and memes
- causal state updates that drive narration
- a reasonableness gate for only coherent story variants
- an inline ASP twin for parity checking
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"mother", "mom", "woman", "girl"}
        male = {"father", "dad", "man", "boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the fallen tree trail"
    affords: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    size: str
    risk: str
    block: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    help_text: str
    fix_text: str
    guards: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


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
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "fallen_tree_trail": Setting(place="the fallen tree trail", affords={"cross", "climb", "clear"}),
}

OBSTACLES = {
    "fallen_tree": Obstacle(
        id="fallen_tree",
        label="a giant fallen tree",
        size="giant",
        risk="blocked",
        block="blocks the trail",
        tags={"tree", "trail", "conflict"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="a long rope",
        help_text="tie a steady line around the trunk",
        fix_text="made a safe handhold over the log",
        guards={"fallen_tree"},
        tags={"rope", "trail"},
    ),
    "hatchet": Tool(
        id="hatchet",
        label="a small hatchet",
        help_text="chip away a loose branch",
        fix_text="opened a little path beside the trunk",
        guards={"fallen_tree"},
        tags={"wood", "trail"},
    ),
    "boots": Tool(
        id="boots",
        label="sturdy boots",
        help_text="step up without slipping",
        fix_text="kept the crossing steady",
        guards={"fallen_tree"},
        tags={"trail"},
    ),
}

GIRL_NAMES = ["Mabel", "June", "Nora", "Ruby", "Clara", "Ivy"]
BOY_NAMES = ["Tommy", "Ben", "Eli", "Sam", "Noah", "Theo"]
TRAITS = ["brave", "spry", "sturdy", "clever", "steady"]


@dataclass
class StoryParams:
    place: str
    obstacle: str
    tool: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def reasonableness_gate(obstacle: Obstacle, tool: Tool) -> bool:
    return obstacle.id in tool.guards


def explain_rejection(obstacle: Obstacle, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not honestly help with {obstacle.label}. "
        f"The fix has to fit the trouble on the fallen tree trail.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a mother, agency, and a conflict on a fallen tree trail."
    )
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--obstacle", choices=OBSTACLES.keys())
    ap.add_argument("--tool", choices=TOOLS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.obstacle and args.tool:
        if not reasonableness_gate(OBSTACLES[args.obstacle], TOOLS[args.tool]):
            raise StoryError(explain_rejection(OBSTACLES[args.obstacle], TOOLS[args.tool]))
    place = args.place or "fallen_tree_trail"
    obstacle = args.obstacle or "fallen_tree"
    tool = args.tool or rng.choice(list(TOOLS.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if not reasonableness_gate(OBSTACLES[obstacle], TOOLS[tool]):
        raise StoryError(explain_rejection(OBSTACLES[obstacle], TOOLS[tool]))
    return StoryParams(place=place, obstacle=obstacle, tool=tool, name=name, gender=gender, trait=trait)


def _do_conflict(world: World, hero: Entity, child: Entity, obstacle: Obstacle) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    hero.memes["agency"] = hero.memes.get("agency", 0.0) + 1
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} stood before {obstacle.label} like a queen before a mountain, "
        f"and {hero.pronoun('possessive')} agency shone brighter than a lantern in the pines."
    )
    world.say(
        f"Still, {child.id} worried the trail was too blocked to cross."
    )
    world.say(
        f'That was the start of the conflict: one heart wanted to turn back, while {hero.id} wanted to solve it.'
    )


def _attempt_fix(world: World, hero: Entity, child: Entity, obstacle: Obstacle, tool: Tool) -> bool:
    tool_ent = world.add(Entity(
        id=tool.id, type="tool", label=tool.label, owner=hero.id,
        carried_by=hero.id, plural=False
    ))
    hero.meters["effort"] = hero.meters.get("effort", 0.0) + 1
    world.say(
        f"{hero.id} grabbed {tool_ent.label} and used it to {tool.help_text}."
    )
    world.say(
        f"{tool.fix_text.capitalize()}, and the path began to open."
    )
    world.facts["tool"] = tool_ent
    return True


def _resolve(world: World, hero: Entity, child: Entity, obstacle: Obstacle, tool: Tool) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    child.memes["worry"] = 0.0
    child.memes["wonder"] = child.memes.get("wonder", 0.0) + 1
    world.say(
        f"At last, {hero.id} and {child.id} crossed together, and the great fallen tree seemed less like a wall and more like a bridge."
    )
    world.say(
        f"By the time they were done, {hero.id} had kept {hero.pronoun('possessive')} agency, "
        f"the conflict had melted away, and the trail looked proud to be walked again."
    )


def tell(setting: Setting, obstacle: Obstacle, tool: Tool, hero_name: str, hero_gender: str, trait: str) -> World:
    world = World(setting)
    hero_type = "mother" if hero_gender == "girl" else "mother"
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label="mother"))
    child = world.add(Entity(id="Child", kind="character", type="child", label="child"))
    obs = world.add(Entity(id=obstacle.id, type="obstacle", label=obstacle.label, plural=False))

    world.say(
        f"On the fallen tree trail, {hero.id} was a {trait} mother with a big, bright agency that never sat still."
    )
    world.say(
        f"She and the child came upon {obs.label}, which {obstacle.block}."
    )
    world.para()
    _do_conflict(world, hero, child, obstacle)
    world.para()
    _attempt_fix(world, hero, child, obstacle, tool)
    _resolve(world, hero, child, obstacle, tool)

    world.facts.update(hero=hero, child=child, obstacle=obs, tool_def=tool, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obstacle = f["obstacle"]
    return [
        'Write a tall tale for a small child about a mother with strong agency on a fallen tree trail.',
        f"Tell a story where {hero.id} meets {obstacle.label} and solves the conflict without giving up.",
        "Write a short, child-friendly tall tale about turning a blocked trail into a brave crossing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    child = f["child"]
    obstacle = f["obstacle"]
    tool = f["tool_def"]
    return [
        QAItem(
            question=f"Who kept calm when the fallen tree blocked the trail?",
            answer=f"{hero.id} kept calm. She was the mother in the story, and her agency helped her look for a way through."
        ),
        QAItem(
            question=f"What was the conflict on the trail?",
            answer=f"The conflict was that the trail was blocked by {obstacle.label}, and the child worried they should turn back."
        ),
        QAItem(
            question=f"What did {hero.id} use to solve the problem?",
            answer=f"She used {tool.label}. It helped her {tool.help_text} and made the crossing safe enough for the child."
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the child?",
            answer=f"They crossed together, the conflict faded, and the trail was open again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fallen tree?",
            answer="A fallen tree is a tree that has toppled over and is lying on the ground."
        ),
        QAItem(
            question="What does agency mean?",
            answer="Agency means being able to choose and act for yourself."
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="fallen_tree_trail", obstacle="fallen_tree", tool="rope", name="Mabel", gender="girl", trait="brave"),
    StoryParams(place="fallen_tree_trail", obstacle="fallen_tree", tool="hatchet", name="June", gender="girl", trait="clever"),
    StoryParams(place="fallen_tree_trail", obstacle="fallen_tree", tool="boots", name="Tommy", gender="boy", trait="steady"),
]


ASP_RULES = r"""
needs_fix(O,T) :- obstacle(O), tool(T), guards(T,O).
valid_story(P,O,T) :- place(P), obstacle(O), tool(T), affords(P,cross), needs_fix(O,T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for oid, o in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", tid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, o, t) for p in SETTINGS for o, obs in OBSTACLES.items() for t, tool in TOOLS.items() if reasonableness_gate(obs, tool)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], OBSTACLES[params.obstacle], TOOLS[params.tool], params.name, params.gender, params.trait)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("fallen_tree_trail", o, t) for o in OBSTACLES for t in TOOLS if reasonableness_gate(OBSTACLES[o], TOOLS[t])]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.tool and not reasonableness_gate(OBSTACLES[args.obstacle], TOOLS[args.tool]):
        raise StoryError(explain_rejection(OBSTACLES[args.obstacle], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.obstacle is None or c[1] == args.obstacle)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obstacle, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, obstacle=obstacle, tool=tool, name=name, gender=gender, trait=trait)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
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
