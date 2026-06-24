#!/usr/bin/env python3
"""
storyworlds/worlds/demolition_mystery_to_solve_whodunit.py
==========================================================

A small child-facing mystery world about a demolition surprise and a tidy
whodunit-style solve.

Seed tale:
---
A little detective noticed that the old shed in the yard had been knocked down.
Everyone pointed at the demolition crew, but the detective saw a trail of chalk,
a bent ladder, and a boot print in the dust. The clues led to the foreman, who
had meant to bring down only the weak wall and had accidentally hit the support
beam instead. The detective explained the mistake, and the grown-ups fixed the
yard together.

World model:
---
This world tracks a tiny demolition site, a few named characters, one broken
structure, and a simple clue chain. The central question is always a whodunit:
who caused the big collapse, and how did the detective prove it?

The prose is generated from state, not from a frozen paragraph with swapped
nouns. The resolution depends on the culprit, the clue trail, and the repair
choice.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old yard"
    indoors: bool = False


@dataclass
class Clue:
    kind: str
    label: str
    witness_line: str


@dataclass
class DemolitionJob:
    target: str
    weak_spot: str
    tool: str
    mess: str
    danger: str
    repair: str


@dataclass
class StoryParams:
    place: str
    job: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    culprit_name: str
    culprit_type: str
    seed: Optional[int] = None


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTING = Setting(place="the old yard", indoors=False)

JOBS = {
    "shed": DemolitionJob(
        target="old shed",
        weak_spot="back support beam",
        tool="demolition hammer",
        mess="dusty rubble",
        danger="the wall could fall the wrong way",
        repair="build a new fence panel",
    ),
    "garage": DemolitionJob(
        target="tiny garage",
        weak_spot="roof beam",
        tool="wrecking bar",
        mess="broken boards",
        danger="the roof could sag into the wrong corner",
        repair="straighten the gate and sweep the boards away",
    ),
    "wall": DemolitionJob(
        target="stone wall",
        weak_spot="corner stones",
        tool="sledgehammer",
        mess="chalky stones",
        danger="the corner could crumble into the walkway",
        repair="stack the stones into a safe little pile",
    ),
}

CLUES = {
    "chalk": Clue(
        kind="chalk",
        label="chalk dust",
        witness_line="There was chalk dust on the culprit's sleeve.",
    ),
    "ladder": Clue(
        kind="ladder",
        label="a bent ladder",
        witness_line="The bent ladder matched the high spot on the wall.",
    ),
    "boot": Clue(
        kind="boot",
        label="one muddy boot print",
        witness_line="One muddy boot print pointed toward the gate.",
    ),
    "glove": Clue(
        kind="glove",
        label="a torn work glove",
        witness_line="A torn work glove had fresh gray dust on it.",
    ),
}

DETECTIVE_NAMES = ["Maya", "Nina", "Leo", "Finn", "Iris", "Theo", "Ava", "Milo"]
HELPER_NAMES = ["June", "Owen", "Pia", "Ben", "Sage", "Nora", "Eli", "Tess"]
CULPRIT_NAMES = ["Mr. Vale", "Ms. Reed", "Mr. Cobb", "Ms. Lane", "Mr. Finch", "Ms. Moss"]
TYPES = {"girl": "girl", "boy": "boy", "woman": "woman", "man": "man"}


class StoryWorldError(StoryError):
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small demolition whodunit for young readers."
    )
    ap.add_argument("--place", choices=list({"yard": "the old yard", "lot": "the empty lot", "courtyard": "the school courtyard"}.keys()))
    ap.add_argument("--job", choices=JOBS.keys())
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--culprit-name")
    ap.add_argument("--culprit-type", choices=["woman", "man"])
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
    job = args.job or rng.choice(list(JOBS))
    place = args.place or rng.choice(["yard", "lot", "courtyard"])
    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    culprit_type = args.culprit_type or rng.choice(["woman", "man"])

    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    culprit_name = args.culprit_name or rng.choice(CULPRIT_NAMES)

    if detective_name == helper_name:
        helper_name = helper_name + "y"

    return StoryParams(
        place=place,
        job=job,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_name=helper_name,
        helper_type=helper_type,
        culprit_name=culprit_name,
        culprit_type=culprit_type,
    )


def set_place(place: str) -> Setting:
    mapping = {
        "yard": "the old yard",
        "lot": "the empty lot",
        "courtyard": "the school courtyard",
    }
    if place not in mapping:
        raise StoryWorldError("Unknown place.")
    return Setting(place=mapping[place], indoors=False)


def mood_words() -> list[str]:
    return ["careful", "quiet", "sharp-eyed", "brave", "patient"]


def clue_path(job: DemolitionJob) -> list[Clue]:
    if job.target == "old shed":
        return [CLUES["chalk"], CLUES["ladder"], CLUES["boot"]]
    if job.target == "tiny garage":
        return [CLUES["boot"], CLUES["glove"], CLUES["chalk"]]
    return [CLUES["glove"], CLUES["ladder"], CLUES["boot"]]


def build_world(params: StoryParams) -> World:
    world = World(set_place(params.place))
    job = JOBS[params.job]

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        role="detective",
        meters={"curiosity": 2.0},
        memes={"focus": 2.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        role="helper",
        meters={"helpfulness": 1.5},
        memes={"trust": 1.5},
    ))
    culprit = world.add(Entity(
        id=params.culprit_name,
        kind="character",
        type=params.culprit_type,
        role="foreman",
        meters={"work": 2.0},
        memes={"worry": 1.0},
    ))
    structure = world.add(Entity(
        id="structure",
        kind="thing",
        type="structure",
        label=job.target,
        phrase=f"the {job.target}",
        meters={"standing": 1.0, "damage": 0.0},
    ))

    world.facts.update(
        detective=detective,
        helper=helper,
        culprit=culprit,
        structure=structure,
        job=job,
        clues=clue_path(job),
        solved=False,
        revealed=False,
    )

    return world


def narrate_setup(world: World) -> None:
    f = world.facts
    det: Entity = f["detective"]
    hel: Entity = f["helper"]
    cul: Entity = f["culprit"]
    job: DemolitionJob = f["job"]
    world.say(
        f"{det.id} was a {random.choice(mood_words())} little detective who liked solving puzzling things in {world.setting.place}."
    )
    world.say(
        f"That morning, {det.id} and {hel.id} found {job.target} standing in the yard, waiting for a careful demolition."
    )
    world.say(
        f"{cul.id}, the foreman, said the plan was simple: hit the weak spot, clear the path, and keep the rest safe."
    )


def apply_demolition(world: World) -> None:
    f = world.facts
    cul: Entity = f["culprit"]
    structure: Entity = f["structure"]
    job: DemolitionJob = f["job"]

    structure.meters["damage"] = 1.0
    structure.meters["standing"] = 0.0
    cul.memes["worry"] = 0.0
    world.say(
        f"But when the {job.tool} swung, it struck the {job.weak_spot} too hard."
    )
    world.say(
        f"The {job.target} came down in a boom of {job.mess}, and everyone blinked at the sudden mess."
    )
    world.say(
        f"It was a whodunit now, because no one had meant for {job.danger}."
    )


def reveal_clues(world: World) -> list[str]:
    clues = world.facts["clues"]
    out = []
    for clue in clues:
        out.append(clue.witness_line)
    return out


def solve_mystery(world: World) -> None:
    f = world.facts
    det: Entity = f["detective"]
    hel: Entity = f["helper"]
    cul: Entity = f["culprit"]
    job: DemolitionJob = f["job"]
    clues: list[Clue] = f["clues"]

    world.para()
    world.say(
        f"{det.id} did not guess. {det.pronoun().capitalize()} looked closely at the rubble, the ladder, and the dust."
    )
    for line in reveal_clues(world):
        world.say(line)

    evidence = []
    for clue in clues:
        evidence.append(clue.kind)

    if "chalk" in evidence and "ladder" in evidence:
        reason = f"the ladder had reached too high and the chalk dust showed where it scraped"
    elif "boot" in evidence and "glove" in evidence:
        reason = f"the boot print and the torn glove both pointed to the person who had climbed near the weak spot"
    else:
        reason = f"the clues all pointed to the foreman, who had been closest to the weak spot"

    world.say(
        f"{det.id} said the clues fit together: {reason}."
    )
    world.say(
        f'"The {cul.id} {cul.role} did it," {det.id} told the others, "but not on purpose. {cul.id} only meant to bring down the weak part."'
    )
    world.say(
        f"{hel.id} nodded, because the answer made sense: the wrong swing had caused the trouble."
    )
    f["solved"] = True


def resolve_world(world: World) -> None:
    f = world.facts
    job: DemolitionJob = f["job"]
    det: Entity = f["detective"]
    hel: Entity = f["helper"]
    cul: Entity = f["culprit"]
    structure: Entity = f["structure"]

    world.para()
    cul.memes["relief"] = 1.0
    structure.meters["damage"] = 1.0
    world.say(
        f"The grown-ups listened, and {cul.id} admitted the mistake."
    )
    world.say(
        f"Together, {det.id}, {hel.id}, and {cul.id} cleaned the {job.mess}, set the broken pieces aside, and {job.repair}."
    )
    world.say(
        f"In the end, the yard was safe again, and the mystery was solved."
    )


def generate_story_text(world: World) -> str:
    narrate_setup(world)
    world.para()
    apply_demolition(world)
    solve_mystery(world)
    resolve_world(world)
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    job: DemolitionJob = f["job"]
    det: Entity = f["detective"]
    return [
        f'Write a short whodunit for a child about a demolition mystery in {world.setting.place}.',
        f"Tell a mystery story where {det.id} investigates who caused the demolition of {job.target}.",
        f'Write a gentle detective story that includes the word "demolition" and ends with the clue that solves the case.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det: Entity = f["detective"]
    hel: Entity = f["helper"]
    cul: Entity = f["culprit"]
    job: DemolitionJob = f["job"]

    return [
        QAItem(
            question=f"Who was the little detective in the demolition mystery?",
            answer=f"The little detective was {det.id}. {det.pronoun().capitalize()} watched the yard carefully and looked at the clues.",
        ),
        QAItem(
            question=f"What was being demolished in the story?",
            answer=f"{job.target} was being demolished. It came down in a noisy boom of {job.mess}.",
        ),
        QAItem(
            question=f"Who turned out to be the one closest to the mistake?",
            answer=f"It was {cul.id}, the foreman. {cul.id} did not mean to cause trouble, but the wrong swing hit the weak spot.",
        ),
        QAItem(
            question=f"How did {det.id} solve the whodunit?",
            answer=f"{det.id} solved it by following the clues: {', '.join(c.label for c in f['clues'])}. The clues showed that the wrong tool hit the weak spot.",
        ),
        QAItem(
            question=f"What did the grown-ups do after the mystery was solved?",
            answer=f"They listened, fixed the mess together, and made the yard safe again. {det.id}, {hel.id}, and {cul.id} all helped clean up.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is demolition?",
            answer="Demolition is the careful breaking down of a building or wall that is too old, weak, or unwanted.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of evidence that helps a detective figure out what happened.",
        ),
        QAItem(
            question="What does a foreman do at a work site?",
            answer="A foreman helps lead the workers and makes sure the job is done safely.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  facts: solved={world.facts.get('solved')} revealed={world.facts.get('revealed')}")
    return "\n".join(lines)


ASP_RULES = r"""
place(yard).
place(lot).
place(courtyard).

job(shed).
job(garage).
job(wall).

detective(girl).
detective(boy).

culprit(woman).
culprit(man).

valid_story(P, J, D, C) :- place(P), job(J), detective(D), culprit(C).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in ["yard", "lot", "courtyard"]:
        lines.append(asp.fact("place", p))
    for j in JOBS:
        lines.append(asp.fact("job", j))
    lines.append(asp.fact("detective", "girl"))
    lines.append(asp.fact("detective", "boy"))
    lines.append(asp.fact("culprit", "woman"))
    lines.append(asp.fact("culprit", "man"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    asp_count = len(set(asp.atoms(model, "valid_story")))
    py_count = 3 * len(JOBS) * 2 * 2
    if asp_count == py_count:
        print(f"OK: ASP gate matches Python world space ({asp_count} combos).")
        return 0
    print(f"MISMATCH: ASP={asp_count}, Python={py_count}")
    return 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for p in ["yard", "lot", "courtyard"]:
        for j in JOBS:
            for d in ["girl", "boy"]:
                for c in ["woman", "man"]:
                    out.append((p, j, d, c))
    return out


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story_text(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def resolve_seeded_name(rng: random.Random, options: list[str]) -> str:
    return rng.choice(options)


def explain_rejection(reason: str) -> str:
    return f"(No story: {reason})"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for place in ["yard", "lot", "courtyard"]:
            for job in list(JOBS):
                params = StoryParams(
                    place=place,
                    job=job,
                    detective_name="Maya",
                    detective_type="girl",
                    helper_name="Owen",
                    helper_type="boy",
                    culprit_name="Mr. Vale",
                    culprit_type="man",
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.detective_name}: {p.job} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
