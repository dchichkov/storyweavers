#!/usr/bin/env python3
"""
storyworlds/worlds/wage_moral_value_cautionary_rhyme_mystery.py
================================================================

A small storyworld about a child, a promised wage, and a tiny mystery.

Premise:
- A child does a careful job to earn a wage.
- A little mystery appears when the money seems missing.
- The child follows clues instead of panicking.
- The ending proves the value of honesty, caution, and patience.

The prose keeps a mystery tone, but the world model stays concrete:
physical meters track coins, pockets, and places; emotional memes track worry,
pride, suspicion, and relief.

This world also includes a gentle rhyme element in the narrated lines.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    name: str
    indoors: bool = True
    clue_words: set[str] = field(default_factory=set)


@dataclass
class Job:
    id: str
    verb: str
    gerund: str
    clue: str
    wage: int
    risk: str
    caution: str
    keyword: str = "wage"


@dataclass
class StoryParams:
    place: str
    job: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, job: Job) -> None:
        self.place = place
        self.job = job
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
        import copy as _copy
        clone = World(self.place, self.job)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "bakery": Place("bakery", "the bakery", indoors=True, clue_words={"flour", "tray", "counter"}),
    "market": Place("market", "the market", indoors=False, clue_words={"stall", "basket", "coin"}),
    "library": Place("library", "the library", indoors=True, clue_words={"book", "card", "shelf"}),
}

JOBS = {
    "sweep": Job(
        id="sweep",
        verb="sweep the floor",
        gerund="sweeping the floor",
        clue="flour near the broom",
        wage=3,
        risk="dusty",
        caution="look before you leap",
    ),
    "deliver": Job(
        id="deliver",
        verb="deliver the parcel",
        gerund="delivering the parcel",
        clue="a dropped note",
        wage=4,
        risk="lost",
        caution="check the path twice",
    ),
    "sort": Job(
        id="sort",
        verb="sort the jars",
        gerund="sorting the jars",
        clue="labels on the jars",
        wage=2,
        risk="mixed-up",
        caution="slow hands make safe hands",
    ),
}

NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Ivy", "June"],
    "boy": ["Eli", "Noah", "Finn", "Owen", "Theo"],
}

HELPERS = {
    "cat": ("cat", "the cat"),
    "grandpa": ("father", "Grandpa"),
    "neighbor": ("woman", "the neighbor"),
}


def rhyme_line(job: Job, place: Place) -> str:
    return {
        "sweep": "Sweep and keep, neat and sweet, till the dusty floor looks bright and neat.",
        "deliver": "Step by step, keep to the path; a careful pace can dodge the wrath.",
        "sort": "Sort with care, and do not rush; one calm glance keeps jars from a crush.",
    }[job.id]


def setup_line(hero: Entity, helper: Entity, job: Job, place: Place) -> str:
    return f"{hero.id} went to {place.name} with {helper.label} to {job.gerund}."


def mystery_hint(job: Job, place: Place) -> str:
    return f"There was a clue: {job.clue} near {place.name}."


def predict_mystery(world: World, hero: Entity) -> dict[str, bool]:
    sim = world.copy()
    sim.get(hero.id).memes["worry"] = sim.get(hero.id).memes.get("worry", 0) + 1
    # If the helper is careless, the wage could seem missing.
    missing = bool(sim.facts.get("hidden_coin"))
    found = bool(sim.facts.get("clue_followed"))
    return {"missing": missing and not found}


def build_world(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    job = JOBS[params.job]
    world = World(place, job)

    gender = params.gender
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=gender,
        meters={"money": 0.0},
        memes={"hope": 1.0, "worry": 0.0, "pride": 0.0, "relief": 0.0},
    ))
    helper_type, helper_label = HELPERS[params.helper]
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label=helper_label,
        memes={"calm": 1.0},
    ))
    wage = world.add(Entity(
        id="wage",
        kind="thing",
        type="coins",
        label="small silver coins",
        phrase=f"{job.wage} silver coins",
        owner=hero.id,
        meters={"count": float(job.wage)},
    ))
    pouch = world.add(Entity(
        id="pouch",
        kind="thing",
        type="pouch",
        label="cloth pouch",
        owner=hero.id,
        meters={"sealed": 1.0},
    ))
    world.facts.update(hero=hero, helper=helper, wage=wage, pouch=pouch, place=place, job=job)

    world.say(f"{hero.id} was promised a wage for {job.gerund}, and {hero.pronoun('possessive')} heart felt brave.")
    world.say(f"{rhyme_line(job, place)}")
    world.say(setup_line(hero, helper, job, place))

    world.para()
    world.say(f"But then the little mystery began.")
    world.say(mystery_hint(job, place))

    if job.id == "deliver":
        world.facts["hidden_coin"] = True
        hero.memes["worry"] += 1
        world.say(f"{hero.id} thought the wage had vanished, and {hero.pronoun('possessive')} worry grew as dark as rain.")
        world.say(f"{helper.label} said, \"Look before you leap; keep calm and be wise.\"")
        world.say(f"{hero.id} followed the clue, found a coin under a mat, and saw the rest tucked safe in the pouch.")
        world.facts["clue_followed"] = True
    elif job.id == "sweep":
        world.facts["hidden_coin"] = False
        hero.memes["worry"] += 1
        world.say(f"A shiny coin gleamed by the broom, and {hero.id} wondered if it was lost wage.")
        world.say(f"{helper.label} told {hero.id} not to grab it fast, because a careful hand sees best.")
        world.say(f"{hero.id} brushed the dust aside and found the real wage still waiting on the counter.")
        world.facts["clue_followed"] = True
    else:
        world.facts["hidden_coin"] = True
        hero.memes["worry"] += 1
        world.say(f"One jar had a crooked label, and the missing wage seemed to be part of a mix-up.")
        world.say(f"{helper.label} reminded {hero.id} that slow hands make safe hands.")
        world.say(f"{hero.id} checked each shelf, sorted the jars again, and found the coin under the register.")
        world.facts["clue_followed"] = True

    world.para()
    hero.meters["money"] += job.wage
    hero.memes["pride"] += 1
    hero.memes["worry"] = 0
    hero.memes["relief"] += 1
    world.say(f"In the end, {hero.id} earned the wage after all, and {hero.pronoun('possessive')} pouch felt pleasantly heavy.")
    world.say(f"{helper.label} smiled, and the mystery turned small and clear: honest work, careful eyes, and a safe reward.")
    world.say(f"{hero.id} went home with {job.wage} coins and a wiser grin.")

    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in SETTINGS.items():
        for job_id in place.clue_words or JOBS:
            if job_id in JOBS:
                pass
        for job_id in JOBS:
            combos.append((place_id, job_id, "any"))
    return [(p, j, "any") for p in SETTINGS for j in JOBS]


def explain_rejection() -> str:
    return "(No story: the chosen options do not describe a workable wage mystery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery storyworld about earning a wage, finding clues, and learning caution.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--job", choices=JOBS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(list(SETTINGS))
    job = args.job or rng.choice(list(JOBS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, job=job, name=name, gender=gender, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child about a {f["hero"].type} earning a wage at {f["place"].name}.',
        f"Tell a gentle cautionary rhyme about {f['hero'].id}, {f['job'].gerund}, and a clue that seems to hide the wage.",
        f'Write a story that ends with honesty and relief, and includes the word "wage".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, job, place = f["hero"], f["helper"], f["job"], f["place"]
    return [
        QAItem(
            question=f"Why did {hero.id} go to {place.name}?",
            answer=f"{hero.id} went to {place.name} to {job.gerund} and earn a wage.",
        ),
        QAItem(
            question=f"What was the mystery about?",
            answer=f"The mystery was about the wage seeming missing, even though {hero.id} had done the job carefully.",
        ),
        QAItem(
            question=f"Who helped {hero.id} stay calm?",
            answer=f"{helper.label} helped {hero.id} stay calm and reminded {hero.id} to look carefully before acting.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{hero.id} found the wage, earned {job.wage} coins, and went home relieved and proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wage?",
            answer="A wage is money you earn for doing a job or helping with work.",
        ),
        QAItem(
            question="Why should a person be careful when something is missing?",
            answer="Being careful helps you look for clues, avoid mistakes, and solve the problem safely.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling or not yet understood that makes people look for clues.",
        ),
        QAItem(
            question="Why is honesty important?",
            answer="Honesty matters because it helps people trust each other and keeps work fair and clear.",
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
job(J) :- task(J).
hero(H) :- child(H).

promised_wage(H,J) :- hero(H), job(J).
clue_present(J) :- clue(J).
mystery(H,J) :- promised_wage(H,J), clue_present(J).

careful(H) :- child(H).
good_end(H,J) :- mystery(H,J), careful(H).

#show promised_wage/2.
#show mystery/2.
#show good_end/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for j in JOBS:
        lines.append(asp.fact("task", j))
        lines.append(asp.fact("clue", j))
    lines.append(asp.fact("child", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery/2.\n"))
    return sorted(set(asp.atoms(model, "mystery")))


def asp_verify() -> int:
    py = {( "child", j) for j in JOBS}
    cl = set(asp_valid())
    if cl == py:
        print(f"OK: ASP matches Python ({len(cl)} mysteries).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  only in ASP:", sorted(cl - py))
    print("  only in Python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(place="bakery", job="sweep", name="Mina", gender="girl", helper="cat"),
    StoryParams(place="market", job="deliver", name="Eli", gender="boy", helper="neighbor"),
    StoryParams(place="library", job="sort", name="Nora", gender="girl", helper="grandpa"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for this world's mystery gate.")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.job} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
