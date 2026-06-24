#!/usr/bin/env python3
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


@dataclass
class Person:
    id: str
    kind: str = "character"
    role: str = "child"
    name: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label(self) -> str:
        return self.name or self.id


@dataclass
class Item:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: str = ""
    caretaker: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str


@dataclass
class StoryParams:
    setting: str
    seed: Optional[int] = None
    name: str = "Milo"
    friend: str = "Jun"
    snack: str = "cheddar"
    condiment: str = "tartar"
    mood: str = "intense"


@dataclass
class World:
    place: Place
    people: dict[str, Person] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "kitchen": Place(id="kitchen", label="the kitchen"),
    "picnic_table": Place(id="picnic_table", label="the picnic table"),
    "school_lunch": Place(id="school_lunch", label="the school lunch table"),
}

NAMES = ["Milo", "Nina", "Ari", "Pip", "Lena", "Kai", "Tess", "Owen"]
FRIENDS = ["Jun", "Rae", "Bea", "Sol", "Ivy", "Finn", "Mira", "Noah"]


ASP_RULES = r"""
#show valid_setting/1.
valid_setting(kitchen).
valid_setting(picnic_table).
valid_setting(school_lunch).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("setting", s) for s in SETTINGS)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_setting/1."))
    got = sorted(set(asp.atoms(model, "valid_setting")))
    want = [(s,) for s in sorted(SETTINGS)]
    if got == want:
        print(f"OK: clingo gate matches settings ({len(got)} settings).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  clingo:", got)
    print("  python:", want)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life story world about a small lesson learned and reconciliation."
    )
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in FRIENDS if n != name])
    return StoryParams(setting=setting, seed=None, name=name, friend=friend)


def generate(params: StoryParams) -> StorySample:
    place = SETTINGS[params.setting]
    world = World(place=place)

    child = Person(id="child", role="child", name=params.name, traits=["curious", "intense"])
    friend = Person(id="friend", role="friend", name=params.friend, traits=["gentle", "patient"])
    parent = Person(id="parent", role="parent", name="Mom", traits=["calm", "kind"])

    cheddar = Item(
        id="cheddar",
        label="cheddar",
        phrase="a sharp orange block of cheddar",
        owner=child.id,
    )
    tartar = Item(
        id="tartar",
        label="tartar sauce",
        phrase="a little cup of tartar sauce",
        owner=friend.id,
        caretaker=parent.id,
    )

    world.people = {"child": child, "friend": friend, "parent": parent}
    world.items = {"cheddar": cheddar, "tartar": tartar}

    child.memes["curiosity"] = 1
    child.memes["intensity"] = 1
    friend.memes["care"] = 1
    parent.memes["patience"] = 1

    world.say(
        f"{child.label} was a curious kid who liked simple snack-time experiments, and "
        f"{friend.label} was the kind of friend who noticed every little detail."
    )
    world.say(
        f"One afternoon at {place.label}, {child.label} brought out {cheddar.phrase}, "
        f"while {friend.label} set down {tartar.phrase} beside a plate of crackers."
    )

    world.para()
    child.memes["desire"] = 1
    child.memes["intensity"] += 1
    world.say(
        f"{child.label} got intense about the idea and wanted to try a brave bite right away."
    )
    world.say(
        f"{friend.label} wrinkled {friend.pronoun('possessive')} nose and said, "
        f'"Cheddar and tartar sauce sound like they should not go together."'
    )
    child.memes["hurt"] = 1
    world.say(
        f"That made {child.label} go quiet, because {child.label} had only wanted to share something fun."
    )

    world.para()
    parent.memes["reconciliation"] = 1
    world.say(
        f"{parent.label} sat down between them and said that snack time did not have to be perfect to be kind."
    )
    world.say(
        f"{parent.label} cut the cheddar into tiny squares, and {friend.label} offered the crackers instead of arguing."
    )
    child.memes["lesson_learned"] = 1
    child.memes["hurt"] = 0
    friend.memes["regret"] = 1
    friend.memes["reconciliation"] = 1

    world.say(
        f"{child.label} took a careful bite, then laughed at the surprising mix, while {friend.label} tried one too."
    )
    world.say(
        f"The tartar sauce stayed on the side, but the three of them shared the plate and the table felt warm again."
    )

    world.facts = {
        "child": child,
        "friend": friend,
        "parent": parent,
        "cheddar": cheddar,
        "tartar": tartar,
        "setting": place,
        "lesson": True,
        "reconciliation": True,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a slice-of-life story about a child, a strange snack idea, and a gentle apology.",
        f"Tell a warm story where {f['child'].label} gets intense about {f['cheddar'].label} and {f['friend'].label} learns a lesson.",
        "Write a small everyday story with cheddar, tartar sauce, and reconciliation at snack time.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Person = f["child"]
    friend: Person = f["friend"]
    parent: Person = f["parent"]
    return [
        QAItem(
            question=f"Who wanted to try the snack idea first?",
            answer=f"{child.label} wanted to try it first, because {child.label} got intense about the idea.",
        ),
        QAItem(
            question=f"What did {friend.label} think about the cheddar and tartar sauce at first?",
            answer=f"At first, {friend.label} thought cheddar and tartar sauce sounded like they should not go together.",
        ),
        QAItem(
            question=f"How did the adults help the children get along again?",
            answer=f"{parent.label} helped by staying calm, cutting the cheddar into small pieces, and reminding them that snack time could still be kind.",
        ),
        QAItem(
            question="What lesson was learned by the end?",
            answer="They learned that friends can disagree, talk kindly, and still share a snack together.",
        ),
        QAItem(
            question="What was the reconciliation in the story?",
            answer=f"The reconciliation happened when {friend.label} apologized with actions, {child.label} took a careful bite, and they shared the plate again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cheddar?",
            answer="Cheddar is a kind of cheese. It is firm, tasty, and often cut into slices or cubes for snacks.",
        ),
        QAItem(
            question="What is tartar sauce?",
            answer="Tartar sauce is a creamy condiment often served with fish. People usually dip food into it instead of eating it by itself.",
        ),
        QAItem(
            question="What does it mean to be intense?",
            answer="If someone is intense, they feel something very strongly or focus on it very hard.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means people make peace after a disagreement and start getting along again.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand something important from what happened, so you can do better next time.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for person in world.people.values():
        lines.append(
            f"  {person.label:8} ({person.role:7}) "
            f"meters={person.meters} memes={person.memes}"
        )
    for item in world.items.values():
        lines.append(f"  {item.label:8} ({item.kind:7}) owner={item.owner} caretaker={item.caretaker}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", name="Milo", friend="Jun"),
    StoryParams(setting="school_lunch", name="Nina", friend="Rae"),
    StoryParams(setting="picnic_table", name="Ari", friend="Bea"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_settings() -> list[str]:
    return sorted(SETTINGS)


def asp_valid_settings() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_setting/1."))
    return sorted(set(asp.atoms(model, "valid_setting")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_settings()
        print(f"{len(vals)} valid settings:\n")
        for (s,) in vals:
            print(f"  {s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = seed
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
