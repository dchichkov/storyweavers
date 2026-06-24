#!/usr/bin/env python3
"""
storyworlds/worlds/cognitive_reconciliation_comedy.py
=====================================================

A small storyworld about a child, a silly misunderstanding, and a cheerful
reconciliation.

Seed tale inspiration:
---
A little kid tries to follow a set of instructions, but the page is confusing
and a harmless mix-up turns into a funny mess. The grown-up notices the problem,
they pause, compare clues, laugh at the mistake, and then work together until
the thing is set right.

This world keeps the action concrete and state-driven:
- the child's confusion rises when clues do not match
- the grown-up's concern rises when the mix-up would waste time or break the plan
- a helpful cognitive tool or simple check creates reconciliation
- the ending image proves the misunderstanding is over
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    indoor: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    problem: str
    repair: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Puzzle:
    label: str
    phrase: str
    type: str
    affects: set[str] = field(default_factory=set)
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("confusion", 0) < THRESHOLD:
            continue
        if ("confusion", actor.id) in world.fired:
            continue
        world.fired.add(("confusion", actor.id))
        actor.memes["fluster"] = actor.memes.get("fluster", 0) + 1
        out.append(f"{actor.id} got more and more flustered.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("reconcile", 0) < THRESHOLD:
            continue
        if ("reconcile", actor.id) in world.fired:
            continue
        world.fired.add(("reconcile", actor.id))
        actor.memes["confusion"] = 0
        actor.memes["trust"] = actor.memes.get("trust", 0) + 1
        actor.memes["joy"] = actor.memes.get("joy", 0) + 1
        out.append(f"{actor.id} felt calm again.")
    return out


def _r_cleanup(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("messy", 0) < THRESHOLD:
            continue
        if ("cleanup", item.id) in world.fired:
            continue
        world.fired.add(("cleanup", item.id))
        item.meters["messy"] = 0
        out.append(f"The little mess got put right.")
    return out


RULES = [_r_confusion, _r_reconcile, _r_cleanup]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def activity_risks(activity: Activity, puzzle: Puzzle) -> bool:
    return puzzle.type in activity.tags or any(t in activity.tags for t in puzzle.affects)


def select_tool(activity: Activity, puzzle: Puzzle) -> Optional[Tool]:
    for tool in TOOLS:
        if activity.id in tool.helps or puzzle.type in tool.helps:
            return tool
    return None


def predict_fix(world: World, actor: Entity, activity: Activity, puzzle_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    puzzle = sim.get(puzzle_id)
    return {
        "messy": bool(puzzle.meters.get("messy", 0) >= THRESHOLD),
        "confusion": actor.memes.get("confusion", 0) + 1,
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters["busy"] = actor.meters.get("busy", 0) + 1
    actor.memes["confusion"] = actor.memes.get("confusion", 0) + 1
    world.say(f"{actor.id} tried to {activity.verb}.")
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved anything with a clear answer.")


def setup(world: World, hero: Entity, parent: Entity, activity: Activity, puzzle: Entity) -> None:
    hero.memes["curious"] = hero.memes.get("curious", 0) + 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, because {activity.gerund} looked like a grand idea."
    )
    world.say(
        f"But the page for {puzzle.label} was {activity.problem}, and that made the plan wobble."
    )
    world.say(
        f"{hero.id}'s {parent.label} noticed the wobble and leaned closer to help."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, puzzle: Entity) -> bool:
    pred = predict_fix(world, hero, activity, puzzle.id)
    if not pred["messy"]:
        return False
    world.facts["predicted_fix"] = activity.repair
    world.say(
        f"\"Careful,\" {parent.pronoun('possessive')} {parent.label} said. "
        f"\"If you rush, the whole thing could turn into a silly jumble.\""
    )
    return True


def misunderstand(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0) + 1
    world.say(
        f"{hero.id} puffed out {hero.pronoun('possessive')} cheeks and tried to {activity.rush}."
    )


def offer_tool(world: World, parent: Entity, hero: Entity, activity: Activity, puzzle: Entity) -> Optional[Tool]:
    tool = select_tool(activity, puzzle)
    if tool is None:
        return None
    hero.memes["reconcile"] = hero.memes.get("reconcile", 0) + 1
    world.say(
        f"Then {parent.id} held up {tool.label} and said, "
        f"\"How about we {tool.prep}?\""
    )
    return tool


def accept(world: World, hero: Entity, parent: Entity, activity: Activity, puzzle: Entity, tool: Tool) -> None:
    hero.memes["reconcile"] = hero.memes.get("reconcile", 0) + 1
    hero.memes["confusion"] = 0
    world.say(
        f"{hero.id} stared at the clue, then grinned. "
        f"\"Oh! That makes sense,\" {hero.pronoun()} said."
    )
    world.say(
        f"They {tool.tail}. Soon {hero.id} was {activity.gerund}, "
        f"{puzzle.label} was neat again, and everybody laughed at the mix-up."
    )


def tell(setting: Setting, activity: Activity, puzzle_cfg: Puzzle,
         hero_name: str = "Milo", hero_type: str = "boy",
         parent_type: str = "mother", trait: str = "curious") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, memes={"curious": 1.0, "trust": 0.0}
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label="parent", memes={"patience": 1.0}
    ))
    puzzle = world.add(Entity(
        id="Puzzle", type=puzzle_cfg.type, label=puzzle_cfg.label, phrase=puzzle_cfg.phrase
    ))
    puzzle.meters["messy"] = 0

    world.say(f"{hero.id} was a little {trait} {hero.type} who liked thinking things through.")
    world.say(f"One afternoon, {hero.id} found {puzzle.phrase} on the table.")
    world.say(f"It looked simple at first, which was exactly how the trouble began.")
    world.para()

    setup(world, hero, parent, activity, puzzle)
    warn(world, parent, hero, activity, puzzle)
    misunderstand(world, hero, activity)
    world.say(f"{parent.id} stepped in just in time before the idea got too tangled.")
    world.para()

    tool = offer_tool(world, parent, hero, activity, puzzle)
    if tool is not None:
        accept(world, hero, parent, activity, puzzle, tool)

    world.facts.update(
        hero=hero, parent=parent, puzzle=puzzle, puzzle_cfg=puzzle_cfg,
        activity=activity, setting=setting, tool=tool,
        resolved=tool is not None
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"recipe", "sort"}),
    "classroom": Setting(place="the classroom", affords={"puzzle", "sort"}),
    "bedroom": Setting(place="the bedroom", affords={"build", "sort"}),
}

ACTIVITIES = {
    "recipe": Activity(
        id="recipe",
        verb="follow the recipe",
        gerund="following the recipe",
        rush="mix everything at once",
        problem="full of tiny words and upside-down arrows",
        repair="read it carefully",
        keyword="recipe",
        tags={"recipe", "words", "sort"},
    ),
    "puzzle": Activity(
        id="puzzle",
        verb="finish the puzzle",
        gerund="finishing puzzles",
        rush="force the last piece in",
        problem="so twisty it looked like a joke",
        repair="match the shapes",
        keyword="puzzle",
        tags={"puzzle", "shapes", "sort"},
    ),
    "build": Activity(
        id="build",
        verb="build the paper castle",
        gerund="building paper castles",
        rush="fold the pieces all crooked",
        problem="a little wobbly and very dramatic",
        repair="fold the corners the right way",
        keyword="castle",
        tags={"build", "fold", "sort"},
    ),
    "sort": Activity(
        id="sort",
        verb="sort the buttons",
        gerund="sorting buttons",
        rush="dump the whole bowl",
        problem="mixed up like a bunch of tiny confetti",
        repair="separate the colors",
        keyword="buttons",
        tags={"sort", "colors"},
    ),
}

PUZZLES = {
    "card": Puzzle(
        label="a recipe card",
        phrase="a recipe card with wiggly letters",
        type="recipe",
        affects={"words"},
    ),
    "jigsaw": Puzzle(
        label="a jigsaw puzzle",
        phrase="a jigsaw puzzle with smiling stars",
        type="puzzle",
        affects={"shapes"},
    ),
    "castle": Puzzle(
        label="a paper castle kit",
        phrase="a paper castle kit with neat folds",
        type="build",
        affects={"fold"},
    ),
    "buttons": Puzzle(
        label="a button bowl",
        phrase="a bowl of bright buttons",
        type="sort",
        affects={"colors"},
    ),
}

TOOLS = [
    Tool(id="glasses", label="a pair of reading glasses", prep="put on the reading glasses first", tail="carefully read the recipe card", helps={"recipe", "card"}),
    Tool(id="corner", label="the picture corner", prep="compare the picture corner with the page", tail="matched the shapes and finished the puzzle", helps={"puzzle", "jigsaw"}),
    Tool(id="ruler", label="a little ruler", prep="use a little ruler to line up the folds", tail="lined up the folds and built the paper castle", helps={"build", "castle"}),
    Tool(id="cups", label="two small cups", prep="sort the buttons into two small cups", tail="sorted the buttons into neat little piles", helps={"sort", "buttons"}),
]

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Lila", "Ruby", "Zoe"]
BOY_NAMES = ["Milo", "Finn", "Toby", "Eli", "Noah", "Theo"]
TRAITS = ["curious", "careful", "silly", "patient", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for puzzle_id, puzzle in PUZZLES.items():
                if activity_risks(act, puzzle) and select_tool(act, puzzle):
                    combos.append((place, act_id, puzzle_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    puzzle: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, puzzle = f["hero"], f["parent"], f["activity"], f["puzzle_cfg"]
    return [
        f'Write a short comedy story for a young child about "{act.keyword}" and a mix-up that turns into a reconciliation.',
        f"Tell a funny story where {hero.id} tries to {act.verb} but {parent.label} helps fix a silly misunderstanding about {puzzle.phrase}.",
        f"Write a child-friendly story about confusion, a helpful grown-up, and a happy ending with {act.gerund}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, puzzle = f["hero"], f["parent"], f["activity"], f["puzzle"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do before the mix-up got funny?",
            answer=f"{hero.id} wanted to {act.verb}. But the page was tricky, so the plan wobbled before it could work.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the {puzzle.label}?",
            answer=f"{parent.id} worried because the instructions looked confusing and {hero.id} might make a silly jumble if {hero.pronoun('subject')} rushed.",
        ),
        QAItem(
            question=f"How did the grown-up help {hero.id} fix the problem?",
            answer=f"The grown-up helped by offering {f['tool'].label if f.get('tool') else 'a careful clue'}, and that let {hero.id} slow down and set things right.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{hero.id} stopped feeling flustered, the confusion disappeared, and the whole thing ended with everyone laughing at the misunderstanding.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("tool"):
        tags.add(f["tool"].id)
    out: list[QAItem] = []
    knowledge = {
        "recipe": [("What is a recipe?", "A recipe is a set of instructions that tells you how to make food or another project step by step.")],
        "puzzle": [("What is a puzzle?", "A puzzle is a game or problem where you have to figure out how the pieces or clues fit together.")],
        "build": [("What does it mean to build something?", "To build something means to put parts together to make one thing, like a tower or a castle.")],
        "sort": [("What does it mean to sort things?", "To sort things means to put them into groups that go together, like by color or shape.")],
        "glasses": [("What are reading glasses for?", "Reading glasses help people see words more clearly when the print is small.")],
    }
    for tag, items in knowledge.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], ""]
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
activity_risks(A, P) :- activity(A), puzzle(P), tags(A, T), affects(P, T).
tool_fits(TL, A, P) :- tool(TL), activity_risks(A, P), helps(TL, A).
valid(Place, A, P) :- affords(Place, A), activity_risks(A, P), tool_fits(_, A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tags", aid, t))
    for pid, p in PUZZLES.items():
        lines.append(asp.fact("puzzle", pid))
        for t in sorted(p.affects):
            lines.append(asp.fact("affects", pid, t))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", t.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a cognitive mix-up, comedy, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--puzzle", choices=PUZZLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def explain_rejection(act: Activity, puzzle: Puzzle) -> str:
    return f"(No story: {act.gerund} does not create a sensible problem for {puzzle.label}, so there is nothing to reconcile.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.puzzle:
        if not activity_risks(ACTIVITIES[args.activity], PUZZLES[args.puzzle]):
            raise StoryError(explain_rejection(ACTIVITIES[args.activity], PUZZLES[args.puzzle]))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.puzzle is None or c[2] == args.puzzle)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, puzzle_id = rng.choice(sorted(combos))
    puzzle = PUZZLES[puzzle_id]
    gender = args.gender or rng.choice(sorted(puzzle.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, puzzle=puzzle_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PUZZLES[params.puzzle], params.name, params.gender, params.parent, params.trait)
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
    StoryParams(place="kitchen", activity="recipe", puzzle="card", name="Milo", gender="boy", parent="mother", trait="curious"),
    StoryParams(place="classroom", activity="puzzle", puzzle="jigsaw", name="Mina", gender="girl", parent="father", trait="careful"),
    StoryParams(place="bedroom", activity="build", puzzle="castle", name="Theo", gender="boy", parent="mother", trait="silly"),
    StoryParams(place="kitchen", activity="sort", puzzle="buttons", name="Ivy", gender="girl", parent="mother", trait="bright"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, act, puzzle in combos:
            print(f"  {place:10} {act:8} {puzzle:8}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (puzzle: {p.puzzle})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
