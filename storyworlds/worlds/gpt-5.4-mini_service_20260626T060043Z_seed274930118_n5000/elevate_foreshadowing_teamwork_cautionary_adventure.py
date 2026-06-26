#!/usr/bin/env python3
"""
A small adventure storyworld about climbing, foreshadowing, teamwork, and
cautionary care around an elevated path.

This world is built from a simple seed premise:
a pair of children carry something important up a hill, notice a warning sign
and a loose strap before trouble, and work together to safely elevate the load
without putting anyone at risk.
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
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"risk": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "teamwork": 0.0, "caution": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    elevated: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    can_be_elevated: bool = True
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    goal: str
    name1: str
    name2: str
    gender1: str
    gender2: str
    caretaker: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


SETTINGS = {
    "hill": Setting(place="the hill road", elevated=True, affords={"lift_box", "raise_flag"}),
    "tower": Setting(place="the old tower", elevated=True, affords={"lift_box", "raise_flag"}),
    "bridge": Setting(place="the rope bridge", elevated=True, affords={"lift_box"}),
    "dock": Setting(place="the high dock", elevated=True, affords={"lift_box", "raise_flag"}),
}

GOALS = {
    "lantern": Goal(id="lantern", label="lantern", phrase="a brass lantern with a glass door", type="lantern", region="hand"),
    "crate": Goal(id="crate", label="crate", phrase="a small wooden crate of apples", type="crate", region="hand"),
    "flag": Goal(id="flag", label="flag", phrase="a bright trail flag", type="flag", region="hand"),
}

GEAR = [
    Gear(id="rope", label="a rope sling", covers={"hand"}, guards={"drop", "scrape"}, prep="tie the rope sling around the load", tail="carefully lowered the load together"),
    Gear(id="basket", label="a woven basket", covers={"hand"}, guards={"drop"}, prep="put the load in a woven basket", tail="lifted the basket by both handles"),
    Gear(id="gloves", label="work gloves", covers={"hand"}, guards={"scrape"}, prep="put on work gloves first", tail="gripped the handles more safely"),
]

NAMES = ["Mia", "Noah", "Ava", "Leo", "Nina", "Theo", "Ivy", "Max"]
TRAITS = ["brave", "careful", "curious", "eager", "steady", "bold"]


def setup_story(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    goal = GOALS[params.goal]
    if not goal.can_be_elevated:
        raise StoryError("This goal cannot be safely elevated.")
    world = World(setting)
    hero1 = world.add(Entity(id=params.name1, kind="character", type=params.gender1, memes={"hope": 0.0, "worry": 0.0, "teamwork": 0.0, "caution": 0.0}))
    hero2 = world.add(Entity(id=params.name2, kind="character", type=params.gender2, memes={"hope": 0.0, "worry": 0.0, "teamwork": 0.0, "caution": 0.0}))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=params.caretaker, label=f"the {params.caretaker}"))
    target = world.add(Entity(id="goal", type=goal.type, label=goal.label, phrase=goal.phrase, owner=caretaker.id, caretaker=caretaker.id, region=goal.region, plural=goal.plural))
    world.facts.update(hero1=hero1, hero2=hero2, caretaker=caretaker, goal=target, goal_cfg=goal, setting=setting)
    return world


def foreshadow(world: World) -> None:
    caretaker = world.facts["caretaker"]
    goal = world.facts["goal"]
    world.say(f"At {world.setting.place}, {caretaker.label} pointed to a sign that said the path was steep and slippery.")
    world.say(f"Nearby, a loose strap fluttered against {goal.phrase}, as if the day were warning them to slow down.")


def team_start(world: World) -> None:
    h1, h2 = world.facts["hero1"], world.facts["hero2"]
    goal = world.facts["goal"]
    h1.memes["hope"] += 1
    h2.memes["hope"] += 1
    world.say(f"{h1.id} and {h2.id} wanted to bring {goal.label} higher up the road, because the view from above would be perfect.")
    world.say(f"They looked at each other and nodded, ready to work as a team.")


def caution_event(world: World) -> None:
    h1, h2 = world.facts["hero1"], world.facts["hero2"]
    goal = world.facts["goal"]
    h1.memes["caution"] += 1
    h2.memes["caution"] += 1
    h1.memes["worry"] += 0.5
    h2.memes["worry"] += 0.5
    world.say(f"Then {goal.label} tipped a little when the path dipped, and both children remembered the warning on the sign.")
    world.say("They stopped right away, because rushing on a steep place could make everything tumble down.")


def choose_gear(goal: Goal) -> Optional[Gear]:
    for gear in GEAR:
        if goal.region in gear.covers:
            return gear
    return None


def resolve(world: World) -> None:
    h1, h2 = world.facts["hero1"], world.facts["hero2"]
    goal = world.facts["goal"]
    gear = choose_gear(goal)
    if gear is None:
        raise StoryError("No safe gear exists for this goal.")
    h1.memes["teamwork"] += 1
    h2.memes["teamwork"] += 1
    world.say(f"{h1.id} brought {gear.label}, and {h2.id} held the other side.")
    world.say(f"Together they {gear.prep}, then {gear.tail}.")
    world.say(f"With careful steps, they lifted {goal.phrase} to the top without a single bump.")
    world.say(f"At last, {goal.label} stayed safe and steady, and the two friends smiled at the view they had earned.")


def tell_story(world: World) -> None:
    foreshadow(world)
    world.para()
    team_start(world)
    caution_event(world)
    world.para()
    resolve(world)


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        if not setting.elevated:
            continue
        for goal_id in GOALS:
            out.append((place, goal_id))
    return out


def valid_stories() -> list[tuple[str, str, str, str]]:
    out = []
    for place, goal_id in valid_combos():
        for g1 in ("girl", "boy"):
            for g2 in ("girl", "boy"):
                out.append((place, goal_id, g1, g2))
    return out


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    goal = args.goal or rng.choice(list(GOALS))
    name1 = args.name1 or rng.choice(NAMES)
    name2 = args.name2 or rng.choice([n for n in NAMES if n != name1])
    gender1 = args.gender1 or rng.choice(["girl", "boy"])
    gender2 = args.gender2 or rng.choice(["girl", "boy"])
    caretaker = args.caretaker or rng.choice(["mother", "father", "guide"])
    if gender1 not in {"girl", "boy"} or gender2 not in {"girl", "boy"}:
        raise StoryError("Invalid gender choice.")
    if goal not in GOALS:
        raise StoryError("Unknown goal.")
    return StoryParams(place=place, goal=goal, name1=name1, name2=name2, gender1=gender1, gender2=gender2, caretaker=caretaker)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story about {f["hero1"].id} and {f["hero2"].id} on {world.setting.place} that includes the word "elevate".',
        f"Tell a cautionary teamwork story where two children safely elevate {f['goal'].label} after noticing a warning sign.",
        f"Write a child-friendly adventure with foreshadowing, teamwork, and a careful ending at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What were {f['hero1'].id} and {f['hero2'].id} trying to do with {f['goal'].label}?",
            answer=f"They were trying to elevate {f['goal'].label} higher up the path so they could reach the top safely.",
        ),
        QAItem(
            question=f"What warning helped the children avoid a mistake?",
            answer=f"They noticed a sign about the steep, slippery path, and that warning helped them slow down instead of rushing.",
        ),
        QAItem(
            question=f"How did the children solve the problem together?",
            answer=f"They worked as a team, used {choose_gear(f['goal']).label}, and lifted the load carefully so nothing fell.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does elevate mean?", answer="To elevate something means to lift it up to a higher place."),
        QAItem(question="Why should you be careful on a steep path?", answer="A steep path can make people slip or drop things, so careful steps help keep everyone safe."),
        QAItem(question="What is teamwork?", answer="Teamwork means people help each other and share the work to reach a goal."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world trace ---"]
    for e in world.entities.values():
        parts.append(f"{e.id}: type={e.type} kind={e.kind} meters={e.meters} memes={e.memes}")
    return "\n".join(parts)


def generate(params: StoryParams) -> StorySample:
    world = setup_story(params)
    tell_story(world)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with foreshadowing, teamwork, and caution.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--goal", choices=list(GOALS))
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--gender2", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["mother", "father", "guide"])
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
    return build_story_params(args, rng)


ASP_RULES = r"""
place(P) :- setting(P).
goal(G) :- goal_name(G).
compatible(P,G) :- place(P), goal(G).
#show compatible/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for g in GOALS:
        lines.append(asp.fact("goal_name", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - asp_set:
        print("Only in Python:", sorted(py - asp_set))
    if asp_set - py:
        print("Only in ASP:", sorted(asp_set - py))
    return 1


CURATED = [
    StoryParams(place="hill", goal="crate", name1="Mia", name2="Leo", gender1="girl", gender2="boy", caretaker="mother"),
    StoryParams(place="tower", goal="lantern", name1="Ava", name2="Theo", gender1="girl", gender2="boy", caretaker="father"),
    StoryParams(place="bridge", goal="flag", name1="Nina", name2="Max", gender1="girl", gender2="boy", caretaker="guide"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for p, g in combos:
            print(f"{p} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
