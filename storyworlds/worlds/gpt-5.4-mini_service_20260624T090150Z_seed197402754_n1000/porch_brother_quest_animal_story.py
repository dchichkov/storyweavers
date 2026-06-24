#!/usr/bin/env python3
"""
A small storyworld about a porch, a brother, and an animal quest.

A child and a brother want to help a small animal finish a quest on the porch.
The quest starts with a missing object, builds a little worry, and ends with a
quiet success image showing what changed.
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
    kind: str = "thing"  # "character" | "animal" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "sister", "mother", "mom", "woman"}
        male = {"boy", "brother", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the porch"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    title: str
    goal: str
    clue: str
    missing: str
    found_by: str
    finish: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    quest: str
    name: str
    gender: str
    brother_name: str
    parent_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


QUESTS = {
    "shell": Quest(
        id="shell",
        title="the shell quest",
        goal="find the shiny shell",
        clue="a tiny glint near the porch step",
        missing="shell",
        found_by="the breeze",
        finish="held the shell up like a little treasure",
        tags={"animal", "shore"},
    ),
    "key": Quest(
        id="key",
        title="the key quest",
        goal="find the small brass key",
        clue="a soft clink under the porch mat",
        missing="key",
        found_by="the brother",
        finish="slid the key into the pocket and smiled",
        tags={"home", "finding"},
    ),
    "bell": Quest(
        id="bell",
        title="the bell quest",
        goal="find the lost dinner bell",
        clue="a bright ring hiding by the porch rail",
        missing="bell",
        found_by="the puppy",
        finish="set the bell back on the hook",
        tags={"animal", "sound"},
    ),
}

SETTINGS = {
    "porch": Setting(place="the porch", affords={"shell", "key", "bell"}),
}

ANIMALS = {
    "puppy": ("puppy", "floppy ears", "wagged"),
    "kitten": ("kitten", "soft paws", "purred"),
    "bunny": ("bunny", "quick feet", "twitched"),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ruby", "Ella"]
BOY_NAMES = ["Max", "Leo", "Finn", "Noah", "Owen"]
BROTHER_NAMES = ["Ben", "Jack", "Sam", "Theo", "Eli"]
PARENT_NAMES = ["Mom", "Dad", "Mira", "Toby"]
QUEST_ORDER = ["shell", "key", "bell"]


def create_world(params: StoryParams) -> World:
    setting = SETTINGS["porch"]
    q = QUESTS[params.quest]
    w = World(setting)

    child = w.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        owner=params.parent_name,
        meters={"joy": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0},
    ))
    brother = w.add(Entity(
        id=params.brother_name,
        kind="character",
        type="brother",
        label=params.brother_name,
        owner=params.parent_name,
        meters={"help": 0.0},
        memes={"care": 1.0, "patience": 1.0},
    ))
    animal_type, animal_desc, animal_action = ANIMALS["puppy"]
    animal = w.add(Entity(
        id="animal",
        kind="animal",
        type=animal_type,
        label=f"the {animal_type}",
        phrase=f"the {animal_type} with {animal_desc}",
        meters={"tired": 0.0, "joy": 0.0},
        memes={"hope": 1.0, "worry": 0.0},
    ))
    missing = w.add(Entity(
        id="missing",
        type=q.missing,
        label=q.missing,
        phrase=f"the {q.missing}",
        owner=animal.id,
    ))

    w.facts.update(child=child, brother=brother, animal=animal, missing=missing, quest=q)

    w.say(
        f"On {w.setting.place}, {params.name} found {animal.phrase} sitting very still."
    )
    w.say(
        f"{animal.pronoun().capitalize()} looked worried because {animal.pronoun('possessive')} "
        f"{q.missing} was gone, and the little quest could not begin."
    )

    w.para()
    w.say(
        f"{params.brother_name} came onto the porch and listened. "
        f'"We can help," he said, and {params.name} felt brave enough to search.'
    )
    animal.memes["hope"] += 1.0
    child.meters["joy"] += 0.5
    brother.meters["help"] += 1.0

    w.para()
    if q.id == "shell":
        child.memes["worry"] += 1.0
        w.say(
            f"They looked by the step, where {q.clue} flashed for just a moment."
        )
        w.say(
            f"{params.brother_name} lifted the mat gently, and {params.name} bent down beside the porch rail."
        )
        animal.meters["joy"] += 1.0
        w.say(
            f"At last, {params.name} found {q.missing} tucked in a dry crack, and {animal.pronoun()} "
            f"{q.finish}."
        )
    elif q.id == "key":
        w.say(
            f"They followed {q.clue} and looked under the mat together."
        )
        brother.meters["help"] += 1.0
        w.say(
            f"{params.name} spotted the small brass {q.missing} first, and {params.brother_name} "
            f"laughed because the quest was easier with two sets of eyes."
        )
        child.meters["joy"] += 1.0
        animal.meters["joy"] += 0.5
        w.say(
            f"Then {params.name} {q.finish} while the porch felt bright and calm."
        )
    else:
        child.memes["worry"] += 0.5
        w.say(
            f"They heard {q.clue} near the porch rail, and the puppy began to wiggle."
        )
        w.say(
            f"{params.brother_name} reached up, {params.name} pointed, and together they found the lost bell."
        )
        animal.meters["joy"] += 1.0
        child.meters["joy"] += 1.0
        w.say(
            f"The puppy barked once, and {q.finish} made the whole porch feel like a happy place."
        )

    w.facts["resolved"] = True
    w.facts["animal_action"] = animal_action
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q: Quest = f["quest"]
    child: Entity = f["child"]
    brother: Entity = f["brother"]
    animal: Entity = f["animal"]
    return [
        f'Write a gentle animal story about a porch and a quest using the word "{q.missing}".',
        f"Tell a short story where {child.id} and {brother.id} help {animal.label} finish {q.title}.",
        f"Write a child-friendly story set on the porch where a brother and a small animal solve a tiny problem together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    q: Quest = f["quest"]
    child: Entity = f["child"]
    brother: Entity = f["brother"]
    animal: Entity = f["animal"]
    return [
        QAItem(
            question=f"Where did {child.id} find {animal.label} at the start of the story?",
            answer=f"{child.id} found {animal.label} on the porch, where the little quest could begin.",
        ),
        QAItem(
            question=f"Why did {animal.label} need help?",
            answer=f"{animal.label} was worried because {animal.pronoun('possessive')} {q.missing} was missing.",
        ),
        QAItem(
            question=f"Who helped search during the quest?",
            answer=f"{child.id} and {brother.id} helped search together, and that made the quest easier.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The missing {q.missing} was found, {animal.label} felt happier, and the porch felt calm again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a porch?",
            answer="A porch is a covered space at the front of a house where people can sit, wait, or visit.",
        ),
        QAItem(
            question="Why can working together help on a quest?",
            answer="Working together helps because two helpers can look in different places and solve a problem faster.",
        ),
        QAItem(
            question="What do animals like puppies often do when they are happy?",
            answer="Puppies often wag, bounce, or bark a little when they feel happy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"{e.id}: {e.kind} {e.type} {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
quest(Quest) :- quest_id(Quest).
helped(Child,Brother) :- child(Child), brother(Brother), quest(Quest), on_porch(Quest).
resolved(Quest) :- missing_found(Quest), helped(_, _).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for qid in QUESTS:
        lines.append(asp.fact("quest_id", qid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("brother", "brother"))
    lines.append(asp.fact("on_porch", "shell"))
    lines.append(asp.fact("on_porch", "key"))
    lines.append(asp.fact("on_porch", "bell"))
    lines.append(asp.fact("missing_found", "shell"))
    lines.append(asp.fact("missing_found", "key"))
    lines.append(asp.fact("missing_found", "bell"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show resolved/1.\n#show helped/2."))
    atoms = asp.atoms(model, "resolved")
    if atoms:
        print("OK: ASP program derives a resolved quest.")
        return 0
    print("MISMATCH: ASP program did not derive the expected resolution.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A porch storyworld with a brother and an animal quest.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--brother-name")
    ap.add_argument("--parent-name")
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
    quest = args.quest or rng.choice(list(QUESTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    brother_name = args.brother_name or rng.choice([n for n in BROTHER_NAMES if n != name])
    parent_name = args.parent_name or rng.choice(PARENT_NAMES)
    return StoryParams(
        quest=quest,
        name=name,
        gender=gender,
        brother_name=brother_name,
        parent_name=parent_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = create_world(params)
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


def asp_valid_quests() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show resolved/1."))
    return sorted(set(asp.atoms(model, "resolved")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_quests())} resolved quest model(s)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for qid in QUEST_ORDER:
            p = StoryParams(
                quest=qid,
                name=GIRL_NAMES[0] if qid == "shell" else BOY_NAMES[0],
                gender="girl" if qid == "shell" else "boy",
                brother_name=BROTHER_NAMES[0],
                parent_name=PARENT_NAMES[0],
                seed=base_seed,
            )
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
