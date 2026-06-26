#!/usr/bin/env python3
"""
A standalone story world for a tiny Animal Story with moral value and problem
solving. The seed word is licorice: the stories revolve around a small animal
desiring licorice, a fair choice, and a concrete fix that changes the world.
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
    kind: str = "thing"  # animal | thing | helper
    species: str = "thing"
    name: str = ""
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little meadow"
    affords: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    verb: str
    gerund: str
    risk: str
    problem: str
    clue: str
    moral: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    owner_kind: str = "animal"
    edible: bool = True


@dataclass
class Tool:
    id: str
    label: str
    use: str
    helps: set[str]


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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the little meadow", affords={"share", "search"}),
    "forest": Setting(place="the shady forest", affords={"share", "search"}),
    "pond": Setting(place="the blue pond", affords={"share", "search"}),
    "garden": Setting(place="the bright garden", affords={"share", "search"}),
}

GOALS = {
    "licorice_share": Goal(
        id="licorice_share",
        verb="get the licorice",
        gerund="getting licorice",
        risk="taken by mistake",
        problem="one friend has too little and another has too much",
        clue="the empty basket by the stump",
        moral="It is kinder to share than to grab.",
    ),
    "licorice_help": Goal(
        id="licorice_help",
        verb="reach the licorice",
        gerund="reaching the licorice",
        risk="spilled into the mud",
        problem="the jar is stuck up high",
        clue="a small stick and a steady paw",
        moral="A calm plan can solve a hard problem.",
    ),
    "licorice_honest": Goal(
        id="licorice_honest",
        verb="return the licorice",
        gerund="returning the licorice",
        risk="kept without asking",
        problem="it was found on the path",
        clue="a leaf tag with the owner’s name",
        moral="Being honest makes the right choice clear.",
    ),
}

PRIZES = {
    "licorice": Prize(
        id="licorice",
        label="licorice",
        phrase="a little bundle of black licorice",
        owner_kind="animal",
    )
}

TOOLS = {
    "stick": Tool(
        id="stick",
        label="a small stick",
        use="hook the basket down",
        helps={"licorice_help"},
    ),
    "leaf_note": Tool(
        id="leaf_note",
        label="a leaf note",
        use="find the owner",
        helps={"licorice_honest"},
    ),
    "sharing_pile": Tool(
        id="sharing_pile",
        label="a sharing pile",
        use="divide the treats fairly",
        helps={"licorice_share"},
    ),
}

ANIMAL_SPECIES = ["rabbit", "mouse", "squirrel", "hedgehog", "fox", "otter", "beaver"]
ANIMAL_NAMES = ["Pip", "Milo", "Nia", "Toby", "Luna", "Mara", "Bix", "Ollie"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the goal, setting, and tool agree.
goal_valid(G) :- goal(G).

needs_tool(licorice_help, stick).
needs_tool(licorice_honest, leaf_note).
needs_tool(licorice_share, sharing_pile).

tool_ok(G, T) :- needs_tool(G, T), tool(T).

valid_story(S, G, T) :- setting(S), goal(G), tool(T), tool_ok(G, T), affords(S, share).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("affords", sid, "share"))
        lines.append(asp.fact("affords", sid, "search"))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
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
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for g in GOALS:
            tool = next((t for t in TOOLS.values() if t.id in {"stick", "leaf_note", "sharing_pile"} and g == t.helps.pop() if False), None)
    return [(s, g, tool.id) for s in SETTINGS for g in GOALS for tool in TOOLS.values() if g in tool.helps]


def choose_tool(goal: Goal) -> Optional[Tool]:
    for tool in TOOLS.values():
        if goal.id in tool.helps:
            return tool
    return None


def explain_rejection(goal: Goal) -> str:
    return (
        f"(No story: {goal.problem}. The fix must use a tool that actually helps, "
        f"so this combination is rejected.)"
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    goal: str
    name: str
    species: str
    seed: Optional[int] = None


def _choose_name(rng: random.Random, species: str) -> str:
    return rng.choice(ANIMAL_NAMES)


def _intro(world: World, hero: Entity, goal: Goal, prize: Prize) -> None:
    world.say(
        f"{hero.name} was a small {hero.species} who loved little treats and sunny paths."
    )
    world.say(
        f"One day, {hero.name} spotted {prize.phrase} and wanted to {goal.verb}."
    )
    hero.memes["want"] = hero.memes.get("want", 0) + 1


def _problem(world: World, hero: Entity, goal: Goal, prize: Prize) -> None:
    hero.memes["trouble"] = hero.memes.get("trouble", 0) + 1
    world.para()
    if goal.id == "licorice_share":
        world.say(
            f"But there was a problem: {goal.problem}. {hero.name} had only one shiny bag."
        )
        world.say(
            f"{hero.name} saw {goal.clue}, but knew grabbing first would not be fair."
        )
    elif goal.id == "licorice_help":
        world.say(
            f"But there was a problem: {goal.problem}. The licorice basket sat on a high branch."
        )
        world.say(
            f"{hero.name} looked up and noticed {goal.clue} nearby."
        )
    else:
        world.say(
            f"But there was a problem: {goal.problem}. The licorice had no owner in sight."
        )
        world.say(
            f"{hero.name} noticed {goal.clue} and felt a tug to do the right thing."
        )


def _solve(world: World, hero: Entity, goal: Goal, prize: Prize, tool: Tool) -> None:
    world.para()
    if goal.id == "licorice_share":
        world.say(
            f"{hero.name} took a breath and made {tool.label} instead of a grabby pile."
        )
        world.say(
            f"Then {hero.name} divided the licorice so every friend got a fair piece."
        )
        hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    elif goal.id == "licorice_help":
        world.say(
            f"{hero.name} used {tool.label} to {tool.use}."
        )
        world.say(
            f"The basket came down safely, and the licorice stayed clean."
        )
        hero.memes["care"] = hero.memes.get("care", 0) + 1
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    else:
        world.say(
            f"{hero.name} tied on {tool.label} and walked to the leaf tag."
        )
        world.say(
            f"After asking politely, {hero.name} returned the licorice to its owner."
        )
        hero.memes["honest"] = hero.memes.get("honest", 0) + 1
        hero.memes["peace"] = hero.memes.get("peace", 0) + 1

    world.say(
        f"In the end, {goal.moral} {hero.name} felt proud, and the little meadow seemed brighter."
    )


def tell(world: World, params: StoryParams) -> World:
    goal = GOALS[params.goal]
    prize = PRIZES["licorice"]
    hero = world.add(
        Entity(
            id="hero",
            kind="animal",
            species=params.species,
            name=params.name,
            label=params.name,
        )
    )
    tool = choose_tool(goal)
    if tool is None:
        raise StoryError(explain_rejection(goal))

    world.facts.update(
        setting=params.setting,
        goal=goal.id,
        tool=tool.id,
        hero=hero.name,
        species=hero.species,
    )

    _intro(world, hero, goal, prize)
    _problem(world, hero, goal, prize)
    _solve(world, hero, goal, prize, tool)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    goal = GOALS[f["goal"]]
    return [
        f'Write a short animal story for a child that includes licorice and shows "{goal.moral}".',
        f"Tell a gentle story about {f['hero']}, a {f['species']}, who wants to {goal.verb} but must solve a problem fairly.",
        f"Write a simple story where licorice causes a small problem and a kind animal fixes it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    goal = GOALS[f["goal"]]
    hero = f["hero"]
    return [
        QAItem(
            question=f"What did {hero} want to do with the licorice?",
            answer=f"{hero} wanted to {goal.verb}, and the story showed how the animal solved the problem kindly.",
        ),
        QAItem(
            question=f"What was the problem in the story?",
            answer=f"The problem was that {goal.problem}. That made the licorice hard to deal with at first.",
        ),
        QAItem(
            question=f"How was the problem solved?",
            answer=f"The animal used {TOOLS[f['tool']].label} to fix the problem in a careful way, and the licorice ended up safe and fair.",
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer=goal.moral,
        ),
    ]


KNOWLEDGE = {
    "licorice": [
        (
            "What is licorice?",
            "Licorice is a chewy candy with a strong sweet taste. Some people like it a lot, and some people do not.",
        )
    ],
    "share": [
        (
            "Why is sharing kind?",
            "Sharing is kind because it helps everyone get a fair turn and makes it easier for friends to enjoy the same thing.",
        )
    ],
    "honest": [
        (
            "Why is honesty important?",
            "Honesty is important because people can trust you when you tell the truth and return things that are not yours.",
        )
    ],
    "care": [
        (
            "What does it mean to be careful?",
            "Being careful means paying attention so you do not drop, break, or lose something valuable.",
        )
    ],
    "problem": [
        (
            "What is a problem?",
            "A problem is something that is hard to do or figure out, and it often needs a plan to fix it.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"licorice", "problem"}
    goal = GOALS[world.facts["goal"]]
    if goal.id == "licorice_share":
        tags.add("share")
    if goal.id == "licorice_honest":
        tags.add("honest")
    if goal.id == "licorice_help":
        tags.add("care")
    out: list[QAItem] = []
    for tag in ("licorice", "share", "honest", "care", "problem"):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with licorice, moral value, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--name")
    ap.add_argument("--species", choices=ANIMAL_SPECIES)
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
    if args.goal:
        goal = GOALS[args.goal]
        if choose_tool(goal) is None:
            raise StoryError(explain_rejection(goal))
    valid = valid_combos()
    filtered = [
        c for c in valid
        if (args.setting is None or c[0] == args.setting)
        and (args.goal is None or c[1] == args.goal)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, goal, _tool = rng.choice(sorted(filtered))
    species = args.species or rng.choice(ANIMAL_SPECIES)
    name = args.name or _choose_name(rng, species)
    return StoryParams(setting=setting, goal=goal, name=name, species=species)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    world = tell(world, params)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, g, t.id) for s in SETTINGS for g in GOALS for t in TOOLS.values() if g in t.helps]


def asp_program_text(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_text("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible (setting, goal, tool) combos:\n")
        for s, g, t in combos:
            print(f"  {s:8} {g:16} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for setting in SETTINGS:
            for goal in GOALS:
                tool = choose_tool(GOALS[goal])
                if tool is None:
                    continue
                params = StoryParams(
                    setting=setting,
                    goal=goal,
                    name=random.choice(ANIMAL_NAMES),
                    species=random.choice(ANIMAL_SPECIES),
                    seed=base_seed,
                )
                samples.append(generate(params))
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
