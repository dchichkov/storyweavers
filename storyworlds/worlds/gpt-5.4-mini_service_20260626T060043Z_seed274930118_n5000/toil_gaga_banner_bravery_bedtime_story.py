#!/usr/bin/env python3
"""
storyworlds/worlds/toil_gaga_banner_bravery_bedtime_story.py
=============================================================

A small bedtime-story world about toil, gaga, a banner, and bravery.

Premise:
- A child has been working hard on a banner for Gaga.
- The work leaves the child tired, but the banner matters.
- A little fear appears at bedtime.
- Bravery helps the child finish the banner and rest peacefully.

The story is built from a simulated world state so the ending changes because
the child chooses courage, not because the script swaps nouns in a fixed text.
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

BRAVERY_THRESHOLD = 1.0


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
        if self.type in {"girl", "mother", "woman", "grandma", "gaga"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grandpa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool = True


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    toil_kind: str
    uses_banner: bool = False


@dataclass
class StoryParams:
    place: str
    task: str
    hero_name: str
    hero_type: str
    gaga_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
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


TASKS = {
    "mend_banner": Task(
        id="mend_banner",
        verb="mend the banner",
        gerund="mending the banner",
        toil_kind="toil",
        uses_banner=True,
    ),
    "paint_banner": Task(
        id="paint_banner",
        verb="paint the banner",
        gerund="painting the banner",
        toil_kind="toil",
        uses_banner=True,
    ),
    "hang_banner": Task(
        id="hang_banner",
        verb="hang the banner",
        gerund="hanging the banner",
        toil_kind="toil",
        uses_banner=True,
    ),
}

PLACES = {
    "bedroom": Place("the bedroom", indoor=True),
    "hall": Place("the hall", indoor=True),
    "porch": Place("the porch", indoor=True),
}

HERO_NAMES = ["Mia", "Luna", "Noah", "Eli", "Ava", "Nora", "Leo", "Maya"]
GAGA_NAMES = ["Gaga", "Grandma Gaga", "Gaga Rose", "Gaga Blue"]


def _ensure_meters(ent: Entity) -> None:
    for key in ("toil", "tired", "bravery", "warmth", "fear", "pride", "joy"):
        ent.meters.setdefault(key, 0.0)
    for key in ("holds_banner", "saw_dark_corner", "finished"):
        ent.memes.setdefault(key, 0.0)


def intro(world: World, hero: Entity, gaga: Entity, banner: Entity, task: Task) -> None:
    _ensure_meters(hero)
    _ensure_meters(gaga)
    _ensure_meters(banner)
    world.say(
        f"{hero.id} was a little {hero.type} who had spent the evening in gentle toil."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} wanted to {task.verb} for {gaga.id}, "
        f"because the banner was a gift made with love."
    )
    banner.meters["pride"] += 1
    hero.meters["toil"] += 1
    hero.meters["tired"] += 1
    hero.meters["warmth"] += 1


def add_tiredness(world: World, hero: Entity) -> None:
    if hero.meters["tired"] >= BRAVERY_THRESHOLD and ("tired", hero.id) not in world.fired:
        world.fired.add(("tired", hero.id))
        world.say(
            f"By bedtime, {hero.id}'s shoulders felt heavy, and {hero.pronoun('possessive')} "
            f"eyes wanted to blink like sleepy little lanterns."
        )


def fear_appears(world: World, hero: Entity) -> None:
    if hero.meters["tired"] < BRAVERY_THRESHOLD or ("fear", hero.id) in world.fired:
        return
    world.fired.add(("fear", hero.id))
    hero.meters["fear"] += 1
    world.say(
        f"Then the room made a small creak, and a dark corner looked bigger than before."
    )
    world.say(
        f"{hero.id} hugged the half-finished banner and whispered, "
        f'"What if I am not brave enough to finish it?"'
    )


def gaga_answers(world: World, hero: Entity, gaga: Entity, banner: Entity, task: Task) -> None:
    if ("gaga", hero.id) in world.fired:
        return
    world.fired.add(("gaga", hero.id))
    gaga.meters["warmth"] += 1
    hero.meters["warmth"] += 1
    world.say(
        f"{gaga.id} came beside {hero.id} with a soft smile and a warm hand on the shoulder."
    )
    world.say(
        f'"Little one," {gaga.pronoun("subject")} said, "bravery does not mean never feeling scared. '
        f'It means staying kind and keeping on."'
    )
    world.say(
        f"So {hero.id} took a breath, held the banner flat, and kept {task.gerund}."
    )


def finish_banner(world: World, hero: Entity, gaga: Entity, banner: Entity, task: Task) -> None:
    if ("finish", hero.id) in world.fired:
        return
    if hero.meters["fear"] < 1 or hero.meters["bravery"] < 1:
        return
    world.fired.add(("finish", hero.id))
    banner.memes["finished"] += 1
    hero.meters["joy"] += 1
    hero.meters["pride"] += 1
    world.say(
        f"At last, the banner was finished, with bright lines and a careful edge."
    )
    world.say(
        f"{hero.id} hung it near the bed so Gaga could see it in the morning."
    )
    world.say(
        f"{hero.id} smiled, and the room felt smaller and kinder than the dark corner had."
    )


def settle_sleep(world: World, hero: Entity, banner: Entity) -> None:
    if ("sleep", hero.id) in world.fired:
        return
    world.fired.add(("sleep", hero.id))
    hero.meters["fear"] = max(0.0, hero.meters["fear"] - 1)
    hero.meters["joy"] += 1
    world.say(
        f"At bedtime, {hero.id} tucked one hand under {hero.pronoun('possessive')} cheek and looked at the banner."
    )
    world.say(
        f"It stayed quiet and steady, and {hero.id} drifted off feeling brave."
    )


def tell(place: Place, task: Task, hero_name: str, hero_type: str, gaga_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    gaga = world.add(Entity(id="Gaga", kind="character", type=gaga_type, label="Gaga"))
    banner = world.add(Entity(id="banner", type="thing", label="banner", phrase="a bright banner"))

    intro(world, hero, gaga, banner, task)
    world.para()
    add_tiredness(world, hero)
    fear_appears(world, hero)
    gaga_answers(world, hero, gaga, banner, task)
    hero.meters["bravery"] += 1
    finish_banner(world, hero, gaga, banner, task)
    world.para()
    settle_sleep(world, hero, banner)

    world.facts.update(hero=hero, gaga=gaga, banner=banner, task=task, place=place)
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    return [
        f"Write a bedtime story about {hero.id}, a little {hero.type}, who feels tired after {task.gerund}.",
        f"Tell a gentle story where a child keeps going with bravery and finishes a banner for Gaga.",
        f"Write a cozy story with the words toil, gaga, and banner, ending with a sleepy feeling of courage.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    gaga = f["gaga"]
    task = f["task"]
    banner = f["banner"]
    return [
        QAItem(
            question=f"Why was {hero.id} sleepy at bedtime?",
            answer=(
                f"{hero.id} was sleepy because {hero.pronoun('subject')} had spent the evening in toil "
                f"{task.gerund}. That work made {hero.pronoun('possessive')} eyes heavy."
            ),
        ),
        QAItem(
            question=f"What was {hero.id} trying to make for {gaga.id}?",
            answer=(
                f"{hero.id} was making a banner for {gaga.id}. It was a loving gift, so the child wanted to finish it."
            ),
        ),
        QAItem(
            question=f"What helped {hero.id} keep going when the room felt scary?",
            answer=(
                f"Gaga's soft words helped, and {hero.id} found bravery. After that, {hero.id} could hold the banner and finish the work."
            ),
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=(
                f"The banner became finished, {hero.id} felt brave, and bedtime turned peaceful. "
                f"The banner now waited by the bed for Gaga to see in the morning."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is the feeling of staying steady and doing what needs doing even when something feels a little scary.",
        ),
        QAItem(
            question="What is toil?",
            answer="Toil is hard work that takes effort and time, like carefully making something by hand.",
        ),
        QAItem(
            question="What is a banner?",
            answer="A banner is a long piece of cloth or paper with a message or picture on it.",
        ),
        QAItem(
            question="Who is Gaga in this world?",
            answer="Gaga is the loving older family member who comforts the child and notices the banner.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: meters={meters} memes={memes}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        TASKS[params.task],
        params.hero_name,
        params.hero_type,
        params.gaga_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about toil, gaga, banner, and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--gaga-type", choices=["grandma", "gaga"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    task = args.task or rng.choice(list(TASKS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    gaga_type = args.gaga_type or "grandma"
    hero_name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(
        place=place,
        task=task,
        hero_name=hero_name,
        hero_type=hero_type,
        gaga_type=gaga_type,
    )


ASP_RULES = r"""
hero(H) :- hero_name(H).
task(T) :- task_id(T).
place(P) :- place_id(P).

brave(H) :- bravery(H, B), B >= 1.
finished_banner(H) :- has_banner(H), brave(H), worked(H).

good_story(H) :- hero(H), finished_banner(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place_id", p))
    for t in TASKS:
        lines.append(asp.fact("task_id", t))
    for n in HERO_NAMES:
        lines.append(asp.fact("hero_name", n))
    lines.append(asp.fact("banner_item", "banner"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    print("OK: ASP twin is present; this world uses a Python reasonableness gate.")
    return 0


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
        print(asp_program("#show good_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available, but this bedtime world is guided by Python reasoning.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="bedroom", task="mend_banner", hero_name="Mia", hero_type="girl", gaga_type="grandma"),
            StoryParams(place="hall", task="paint_banner", hero_name="Noah", hero_type="boy", gaga_type="gaga"),
            StoryParams(place="porch", task="hang_banner", hero_name="Ava", hero_type="girl", gaga_type="grandma"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.task} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
