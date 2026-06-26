#!/usr/bin/env python3
"""
A tall-tale storyworld about a trooper in a repertory company, a flashback,
a quarrel, a reconciliation, and a happy ending.

The premise is simple: a traveling stage trooper keeps the repertory show on
track, but an old disagreement returns in a flashback. The world model tracks
who is carrying what, who feels proud or hurt, and whether the company can
finish the performance together.
"""

from __future__ import annotations

import argparse
import copy
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
    role: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother", "actress"}
        male = {"man", "boy", "father", "trooper", "actor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Show:
    title: str
    place: str
    prop: str
    prop_region: str
    danger: str
    danger_zone: set[str]


class World:
    def __init__(self, show: Show):
        self.show = show
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World(self.show)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_misread(world: World) -> list[str]:
    out: list[str] = []
    trooper = world.get("trooper")
    stage_mgr = world.get("manager")
    if trooper.memes.get("stubborn", 0.0) < THRESHOLD:
        return out
    sig = ("misread",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    trooper.memes["hurt"] = trooper.memes.get("hurt", 0.0) + 1.0
    stage_mgr.memes["worry"] = stage_mgr.memes.get("worry", 0.0) + 1.0
    out.append("The trooper bristled as if a horn had blown in an empty canyon.")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    trooper = world.get("trooper")
    if trooper.memes.get("hurt", 0.0) < THRESHOLD:
        return out
    sig = ("flashback",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    trooper.memes["flashback"] = trooper.memes.get("flashback", 0.0) + 1.0
    out.append(
        "That hurt tugged up a flashback to an earlier night, when the same stage "
        "lights had gone dim and the trooper had been blamed for a dropped cue."
    )
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    trooper = world.get("trooper")
    manager = world.get("manager")
    if trooper.memes.get("flashback", 0.0) < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    trooper.memes["softened"] = trooper.memes.get("softened", 0.0) + 1.0
    manager.memes["kind"] = manager.memes.get("kind", 0.0) + 1.0
    out.append(
        "Then the repertory manager set down the script, looked the trooper in the eye, "
        "and spoke plain as sunrise: nobody was meant to carry the whole troupe alone."
    )
    return out


def _r_happy_end(world: World) -> list[str]:
    out: list[str] = []
    trooper = world.get("trooper")
    manager = world.get("manager")
    prop = world.get("prop")
    sig = ("happy_end",)
    if sig in world.fired:
        return out
    if trooper.memes.get("softened", 0.0) < THRESHOLD or manager.memes.get("kind", 0.0) < THRESHOLD:
        return out
    world.fired.add(sig)
    trooper.memes["joy"] = trooper.memes.get("joy", 0.0) + 1.0
    manager.memes["joy"] = manager.memes.get("joy", 0.0) + 1.0
    prop.meters["ready"] = 1.0
    out.append(
        "The two of them fixed the repertory scene together, and the prop stood ready "
        "like a well-brushed horse at the county fair."
    )
    out.append(
        "When the curtain rose, the trooper delivered every line clean and sure, and the "
        "company ended in a happy ending that rang clear over the whole town."
    )
    return out


RULES = [
    _r_misread,
    _r_flashback,
    _r_reconcile,
    _r_happy_end,
]


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


@dataclass
class StoryParams:
    seed: Optional[int] = None
    place: str = "the repertory tent"
    trooper_name: str = "Mabel"
    manager_name: str = "Mr. Finch"
    prop_name: str = "the brass lantern"
    prop_kind: str = "lantern"


PLACES = {
    "tent": Show(
        title="The Repertory Trooper",
        place="the repertory tent",
        prop="brass lantern",
        prop_region="hand",
        danger="a sudden gust",
        danger_zone={"hand"},
    ),
    "hall": Show(
        title="The Repertory Trooper",
        place="the town hall stage",
        prop="tin lantern",
        prop_region="hand",
        danger="a rattling prompt rope",
        danger_zone={"hand"},
    ),
    "wagon": Show(
        title="The Repertory Trooper",
        place="the traveling wagon stage",
        prop="painted sign",
        prop_region="wall",
        danger="a bump in the road",
        danger_zone={"wall"},
    ),
}

NAMES = ["Mabel", "Annie", "Hank", "Cora", "June", "Eli", "Bea", "Silas"]
MANAGERS = ["Mr. Finch", "Mrs. Vale", "Mr. Lark", "Miss Reed"]
TRAITS = ["brave", "steady", "proud", "stubborn", "cheerful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: trooper and repertory company.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--manager", choices=MANAGERS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    name = args.name or rng.choice(NAMES)
    manager = args.manager or rng.choice(MANAGERS)
    return StoryParams(
        seed=None,
        place=place,
        trooper_name=name,
        manager_name=manager,
        prop_name=f"the {PLACES[place].prop}",
        prop_kind=PLACES[place].prop,
    )


def make_world(params: StoryParams) -> World:
    show = PLACES[params.place]
    world = World(show)
    trooper = world.add(Entity(
        id="trooper",
        kind="character",
        type="trooper",
        label=params.trooper_name,
        role="lead",
        meters={"steady": 1.0},
        memes={"pride": 1.0, "stubborn": 1.0},
    ))
    manager = world.add(Entity(
        id="manager",
        kind="character",
        type="man",
        label=params.manager_name,
        role="manager",
        meters={"care": 1.0},
        memes={"worry": 1.0},
    ))
    prop = world.add(Entity(
        id="prop",
        kind="thing",
        type="prop",
        label=params.prop_kind,
        phrase=params.prop_name,
        owner="manager",
        meters={"ready": 0.0},
    ))
    world.facts = {"show": show, "trooper": trooper, "manager": manager, "prop": prop}
    return world


def tell(world: World) -> None:
    trooper = world.get("trooper")
    manager = world.get("manager")
    prop = world.get("prop")
    show = world.show

    world.say(
        f"{trooper.label} was the kind of trooper who could carry a tune, a trunk, and a town's worth of hope."
    )
    world.say(
        f"Every season, {trooper.label} rode with the repertory company to {show.place}, where the same old show could still feel new."
    )
    world.say(
        f"{trooper.label} loved the {show.title.lower()}, especially the shining {prop.phrase}, because it made the stage look fit for a king's parade."
    )

    world.para()
    world.say(
        f"One evening, {trooper.label} reached for the {show.prop} while {manager.label} was counting cues."
    )
    world.say(
        f"That was enough to stir a worry, and the worry turned sharp when {trooper.label} took the correction hard."
    )
    trooper.memes["stubborn"] += 1.0
    propagate(world)

    world.para()
    world.say(
        f"In the flashback, {trooper.label} remembered a colder night when the repertory wagon had rattled, the lights had blinked, and everybody had pointed fingers before the applesauce was even served."
    )
    world.say(
        f"That memory made {trooper.label} softer, and {manager.label} noticed it right away."
    )
    propagate(world)

    world.para()
    world.say(
        f"{manager.label} set a hand on the script and said the sort of words that mend fences and hearts: \"We are a repertory company, not a one-person rodeo.\""
    )
    world.say(
        f"{trooper.label} nodded, and the old hurt began to loosen like a knot in a wet rope."
    )
    propagate(world)

    world.para()
    world.say(
        f"So they fixed the scene together. {trooper.label} checked the {show.prop}, {manager.label} straightened the prompt book, and the whole company found its step."
    )
    world.say(
        f"When the curtain rose, {trooper.label} marched in tall as a pine on a hill, and the repertory show ended with a happy ending that made even the lantern seem to grin."
    )


def generation_prompts(world: World) -> list[str]:
    show = world.show
    trooper = world.get("trooper")
    return [
        f"Write a tall tale about a trooper in a repertory company at {show.place}.",
        f"Tell a story where {trooper.label} has a flashback, then reconciles with the repertory manager.",
        f"Make a child-friendly happy-ending story with a trooper, a repertory show, and a fixed prop.",
    ]


def story_qa(world: World) -> list[QAItem]:
    trooper = world.get("trooper")
    manager = world.get("manager")
    show = world.show
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"It is mainly about {trooper.label}, a trooper who helps the repertory company at {show.place}.",
        ),
        QAItem(
            question=f"What happened after {trooper.label} felt hurt?",
            answer=f"{trooper.label} had a flashback to an earlier mistake, and then {manager.label} helped turn the trouble into reconciliation.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with the company fixing the scene together and finishing the repertory show in a happy ending.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a repertory company?",
            answer="A repertory company is a group of actors who perform a set of plays or scenes again and again, sometimes with the same players and sometimes with new ones.",
        ),
        QAItem(
            question="What is a trooper?",
            answer="A trooper is a brave, hardworking person who keeps going even when the road is rough or the work is heavy.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that shows something that happened earlier, so the reader can understand why a character feels the way they do now.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people who were upset make peace again and start working together kindly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
trooper(trooper).
manager(manager).
flashback :- hurt(trooper).
reconcile :- flashback, kind(manager).
happy_ending :- reconcile.
#show flashback/0.
#show reconcile/0.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("trooper", "trooper"),
        asp.fact("manager", "manager"),
        asp.fact("hurt", "trooper"),
        asp.fact("kind", "manager"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show flashback/0.\n#show reconcile/0.\n#show happy_ending/0."))
    atoms = {sym.name for sym in model}
    expected = {"flashback", "reconcile", "happy_ending"}
    if atoms == expected:
        print("OK: ASP twin matches Python rule chain.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  asp:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_show() -> str:
    return asp_program("#show flashback/0.\n#show reconcile/0.\n#show happy_ending/0.")


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show flashback/0.\n#show reconcile/0.\n#show happy_ending/0."))
        print("\n".join(str(s) for s in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [StoryParams(place=k) for k in PLACES]
        samples = [generate(p) for p in params_list]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
