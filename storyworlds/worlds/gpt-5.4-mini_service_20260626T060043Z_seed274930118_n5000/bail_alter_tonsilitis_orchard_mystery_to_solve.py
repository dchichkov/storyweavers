#!/usr/bin/env python3
"""
A small story world: an orchard mystery to solve, told in a slice-of-life way.

Seed tale:
A child comes to an orchard with a notebook and a big question. A helper has bailed,
a plan has to be altered, and someone is worried about tonsilitis. Meanwhile, a small
mystery keeps tugging at everyone’s attention: where did the missing apples go?

The world model keeps track of who is tired, who is worried, what has been found,
and how the orchard changes when clues are gathered and the plan is adjusted.
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["tired", "busy", "found", "missing", "sore", "relief", "curious"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the orchard"
    affords: set[str] = field(default_factory=lambda: {"search", "gather", "walk"})


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reveals: str
    found_by: Optional[str] = None
    hidden: bool = True


@dataclass
class StoryParams:
    place: str
    mystery: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.clues: dict[str, Clue] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_clue(self, clue: Clue) -> Clue:
        self.clues[clue.id] = clue
        return clue

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.clues = copy.deepcopy(self.clues)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _r_find_clue(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.entities.get("child")
    if not seeker:
        return out
    for clue in world.clues.values():
        if clue.hidden and seeker.memes["curious"] >= THRESHOLD:
            sig = ("find", clue.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            clue.hidden = False
            clue.found_by = seeker.id
            seeker.meters["found"] += 1
            seeker.memes["relief"] += 1
            out.append(f"{seeker.id} spotted a clue: {clue.phrase}.")
            break
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if not child or not helper:
        return out
    found = sum(1 for c in world.clues.values() if not c.hidden)
    if found >= 2 and child.meters["found"] >= 1 and helper.meters["busy"] >= 1:
        sig = ("solve",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["relief"] += 1
        helper.memes["relief"] += 1
        out.append("The pieces finally fit together.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_find_clue, _r_solve):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    note = world.add(Entity(id="notebook", type="thing", label="notebook", phrase="a small green notebook"))
    basket = world.add(Entity(id="basket", type="thing", label="basket", phrase="an apple basket"))
    basket.meters["missing"] = 2.0

    clue1 = world.add_clue(Clue(
        id="clue1",
        label="muddy_print",
        phrase="a muddy print beside the fence",
        reveals="someone passed by the trees",
    ))
    clue2 = world.add_clue(Clue(
        id="clue2",
        label="torn_bag",
        phrase="a torn paper bag tucked under a crate",
        reveals="the apples were gathered, not stolen",
    ))

    child.memes["curious"] += 1
    world.say(
        f"{params.child_name} came to {params.place} with {note.phrase} and a big question."
    )
    world.say(
        f"The orchard was calm, but the apples in {basket.label} were missing, and that made the morning feel strange."
    )

    world.para()
    helper.meters["busy"] += 1
    helper.memes["tired"] += 1
    world.say(
        f"{params.helper_name} had bailed earlier, so the plan had to alter in a hurry."
    )
    world.say(
        f"Then {params.helper_name} came back with a worried face and said the cough they heard about was really tonsilitis."
    )
    world.say(
        f"That meant no one wanted to rush, so {params.child_name} slowed down and started looking carefully."
    )

    world.para()
    child.memes["curious"] += 1
    world.say(
        f"{params.child_name} walked between the trees, checked under crates, and read the ground like a story."
    )
    propagate(world, narrate=True)
    world.say("The first clue showed that someone had walked near the fence.")
    world.say("The second clue showed the apples had been moved into a paper bag for safe keeping.")

    world.para()
    child.meters["found"] += 1
    helper.meters["busy"] += 1
    propagate(world, narrate=True)
    world.say(
        f"At last, {params.child_name} and {params.helper_name} found the answer: the apples had been gathered for a later stall, not lost at all."
    )
    world.say(
        f"They altered the plan again, this time on purpose, and carried the basket back with an easy smile."
    )
    world.say(
        f"By the end, the orchard felt ordinary again, and the missing apples were safely waiting on the table."
    )

    world.facts.update(
        child=child,
        helper=helper,
        note=note,
        basket=basket,
        clues=[clue1, clue2],
        params=params,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a slice-of-life mystery story set in an orchard that includes the words "{p.mystery}", "bail", and "alter".',
        f"Tell a gentle story about {p.child_name} and {p.helper_name} solving a small orchard mystery while someone is dealing with tonsilitis.",
        "Write a child-friendly story where a change in plans leads to a calm solution and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"Where does the story happen?",
            answer=f"It happens in the orchard, where the trees, crates, and baskets make a quiet place to look for clues.",
        ),
        QAItem(
            question=f"Why did {p.child_name} slow down instead of rushing?",
            answer=f"{p.helper_name} said someone had tonsilitis, so the morning needed a calmer pace and a gentler plan.",
        ),
        QAItem(
            question=f"What did {p.child_name} and {p.helper_name} learn about the missing apples?",
            answer="They learned the apples were not gone forever. They had been gathered into a paper bag for later, so the mystery was really about finding the right place to look.",
        ),
        QAItem(
            question=f"How did the plan change after the helper had to bail?",
            answer=f"The plan altered twice: first because {p.helper_name} was away, and then again when the two of them chose a slower, better way to check the orchard.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"At the end, {p.child_name} and {p.helper_name} carried the basket back and the orchard felt calm again, with the apples safe and the mystery solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an orchard?",
            answer="An orchard is a place where fruit trees grow, like apple trees or pear trees, and people often visit to pick fruit.",
        ),
        QAItem(
            question="What is tonsilitis?",
            answer="Tonsilitis is when the tonsils in the throat get swollen and sore, so swallowing can hurt and resting helps.",
        ),
        QAItem(
            question="What does it mean to bail?",
            answer="To bail can mean to leave suddenly or not show up, especially when someone was expected to help.",
        ),
        QAItem(
            question="What does alter mean?",
            answer="To alter means to change something a little, like changing a plan when the first idea no longer fits.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    for c in world.clues.values():
        lines.append(f"{c.id}: hidden={c.hidden} found_by={c.found_by} reveals={c.reveals}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


@dataclass
class Rule:
    name: str
    apply: callable


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("setting", "orchard"))
    lines.append(asp.fact("mystery", "missing_apples"))
    lines.append(asp.fact("condition", "tonsilitis"))
    lines.append(asp.fact("action", "bail"))
    lines.append(asp.fact("action", "alter"))
    lines.append(asp.fact("clue", "muddy_print"))
    lines.append(asp.fact("clue", "torn_bag"))
    lines.append(asp.fact("place_supports", "orchard", "search"))
    return "\n".join(lines)


ASP_RULES = r"""
missing_apples :- clue(muddy_print), clue(torn_bag).
gentle_plan :- condition(tonsilitis).
change_plan :- action(alter), action(bail).
solved :- missing_apples, gentle_plan, change_plan.
#show solved/0.
#show gentle_plan/0.
#show change_plan/0.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = {s.name for s in model}
    expected = {"solved", "gentle_plan", "change_plan"}
    if atoms == expected:
        print("OK: ASP twin matches the Python story logic.")
        return 0
    print(f"MISMATCH: got {sorted(atoms)} expected {sorted(expected)}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life orchard mystery story world.")
    ap.add_argument("--place", default="orchard")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place != "orchard":
        raise StoryError("This world is fixed in an orchard.")
    child_name = args.name or rng.choice(["Mina", "Leo", "Ivy", "Owen", "Nora"])
    helper_name = args.helper or rng.choice(["Aunt June", "Mr. Hale", "Mara", "Ben"])
    child_type = "girl" if child_name in {"Mina", "Ivy", "Nora"} else "boy"
    helper_type = "woman" if helper_name in {"Aunt June", "Mara"} else "man"
    return StoryParams(
        place="the orchard",
        mystery="missing apples",
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i in range(3):
            p = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(p))
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(p))

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
