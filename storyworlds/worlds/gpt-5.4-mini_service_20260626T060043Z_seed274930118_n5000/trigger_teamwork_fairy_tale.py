#!/usr/bin/env python3
"""
storyworlds/worlds/trigger_teamwork_fairy_tale.py
==================================================

A small fairy-tale storyworld about a gentle trigger, a shared task, and the
way teamwork turns a stuck moment into a happy ending.

Seed idea:
- A child-sized hero wants to reach a magical place.
- A trigger is needed to make the helpful magic start.
- The trigger only works when two characters cooperate.
- The story ends with a fairy-tale image proving the change happened.

The world keeps one simple causal model:
- A task can be difficult enough that one character cannot do it alone.
- A cooperative partner can help meet the requirement.
- When the trigger is successfully activated, the magical path opens.
- The ending should show the shared success and the changed emotional state.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "fairy", "woman", "mother"}
        male = {"boy", "prince", "king", "knight", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    atmosphere: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    difficulty: int
    trigger: str
    effect: str
    helper_needed: bool = True
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    place: str
    keyword: str = ""


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    hero_name: str
    hero_type: str
    partner_name: str
    partner_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "forest": Place(name="the forest", atmosphere="The forest was green and hush-quiet, with mossy roots and birdsong.", affords={"rope", "bell", "bridge"}),
    "castle": Place(name="the castle courtyard", atmosphere="The castle courtyard shone with pale stones and tall banners fluttering in the wind.", affords={"rope", "bell", "bridge", "lantern"}),
    "garden": Place(name="the moon garden", atmosphere="The moon garden glimmered with silver flowers and little paths of dew.", affords={"rope", "bell", "lantern"}),
}

TASKS = {
    "open_gate": Task(
        id="open_gate",
        verb="open the moon gate",
        gerund="opening the moon gate",
        difficulty=2,
        trigger="silver bell",
        effect="the moon gate swung open with a golden sigh",
        helper_needed=True,
        keyword="trigger",
        tags={"gate", "bell", "moon"},
    ),
    "raise_bridge": Task(
        id="raise_bridge",
        verb="raise the sleepy bridge",
        gerund="raising the sleepy bridge",
        difficulty=2,
        trigger="rope knot",
        effect="the bridge lifted and the path turned safe",
        helper_needed=True,
        keyword="trigger",
        tags={"bridge", "rope", "teamwork"},
    ),
    "light_path": Task(
        id="light_path",
        verb="light the lantern path",
        gerund="lighting the lantern path",
        difficulty=2,
        trigger="matching spark",
        effect="the lanterns woke up one by one like small stars",
        helper_needed=True,
        keyword="trigger",
        tags={"lantern", "spark", "night"},
    ),
}

PRIZES = {
    "crown": Prize(id="crown", label="crown", phrase="a tiny golden crown", place="castle"),
    "rose": Prize(id="rose", label="rose", phrase="a white rose for the moon garden", place="garden"),
    "key": Prize(id="key", label="key", phrase="a silver key with a flower-shaped handle", place="forest"),
}

GIRL_NAMES = ["Lina", "Mina", "Tala", "Sera", "Nora", "Ivy"]
BOY_NAMES = ["Finn", "Theo", "Oren", "Jasper", "Eli", "Robin"]
PARTNER_NAMES = ["Pip", "Bram", "Luna", "Moss", "Wren", "Nell"]
FAIRY_TRAITS = ["gentle", "brave", "kind", "sparkly", "cheerful", "steady"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for task_id, task in TASKS.items():
            if task_id == "open_gate" and place_id == "garden":
                pass
            if task_id in {"open_gate", "raise_bridge", "light_path"} and place.affords:
                for prize_id, prize in PRIZES.items():
                    if prize.place == place_id:
                        combos.append((place_id, task_id, prize_id))
    return combos


def task_requires_teamwork(task: Task) -> bool:
    return task.helper_needed and task.difficulty >= 2


def select_partner(task: Task) -> bool:
    return task_requires_teamwork(task)


def setup_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, memes={"hope": 1.0, "worry": 0.0, "joy": 0.0, "pride": 0.0, "together": 0.0}))
    partner = world.add(Entity(id=params.partner_name, kind="character", type=params.partner_type, memes={"hope": 1.0, "worry": 0.0, "joy": 0.0, "pride": 0.0, "together": 1.0}))
    prize = world.add(Entity(id="prize", kind="thing", type=PRIZES[params.prize].label, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase))
    task = TASKS[params.task]
    world.facts.update(hero=hero, partner=partner, prize=prize, task=task, place=place)
    return world


def tell_story(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    partner: Entity = world.facts["partner"]  # type: ignore[assignment]
    prize: Entity = world.facts["prize"]  # type: ignore[assignment]
    task: Task = world.facts["task"]  # type: ignore[assignment]

    world.say(f"{hero.id} was a little {hero.type} who lived near {world.place.name}.")
    world.say(f"{partner.id} was a {partner.pronoun('subject')} little friend who loved helping with clever plans.")
    world.say(f"One morning, they found {prize.phrase} waiting at the edge of {world.place.name}.")
    world.say(world.place.atmosphere)

    world.para()
    hero.memes["hope"] += 1.0
    hero.memes["worry"] += 1.0
    world.say(
        f"{hero.id} wanted to {task.verb}, because that was the only way to reach {prize.obj()}."
    )
    world.say(
        f"But the old magic would not wake up for one pair of hands alone; it waited for a {task.trigger} and a true bit of teamwork."
    )
    world.say(
        f"{hero.id} tried once, then twice, and the stone stayed still."
    )

    world.para()
    partner.memes["joy"] += 1.0
    world.say(
        f"Then {partner.id} stepped beside {hero.id} and said, \"We can do it together.\""
    )
    world.say(
        f"They took a breath, counted to three, and pulled at the {task.trigger} at the same time."
    )
    hero.memes["together"] += 1.0
    partner.memes["together"] += 1.0
    hero.memes["pride"] += 1.0
    partner.memes["pride"] += 1.0

    world.para()
    world.say(f"At once, {task.effect}.")
    hero.memes["joy"] += 2.0
    partner.memes["joy"] += 2.0
    hero.memes["worry"] = 0.0
    partner.memes["worry"] = 0.0
    world.say(
        f"{hero.id} and {partner.id} walked the opened path side by side, and the morning felt bright and kind."
    )
    world.say(
        f"In the end, {hero.id} held {prize.obj()} up like a treasure from a fairy tale, and {partner.id} smiled because the best magic had been teamwork all along."
    )

    world.facts["resolved"] = True
    world.facts["opened"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    partner: Entity = world.facts["partner"]  # type: ignore[assignment]
    task: Task = world.facts["task"]  # type: ignore[assignment]
    prize: Entity = world.facts["prize"]  # type: ignore[assignment]
    return [
        f"Write a short fairy tale about {hero.id} and {partner.id} using the word \"trigger\" and a feeling of teamwork.",
        f"Tell a child-friendly story where {hero.id} cannot {task.verb} alone, but {partner.id} helps and the magic wakes up.",
        f"Write a simple fairy tale ending in which {prize.phrase} is reached only after a shared effort.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    partner: Entity = world.facts["partner"]  # type: ignore[assignment]
    task: Task = world.facts["task"]  # type: ignore[assignment]
    prize: Entity = world.facts["prize"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The story was about {hero.id} and {partner.id}, two friends who solved the problem together.",
        ),
        QAItem(
            question=f"What did they need teamwork for?",
            answer=f"They needed teamwork to {task.verb}, because the old magic only woke up when both of them helped at the same time.",
        ),
        QAItem(
            question=f"What was the trigger in the story?",
            answer=f"The trigger was the {task.trigger}, and it worked when {hero.id} and {partner.id} used it together.",
        ),
        QAItem(
            question=f"What did they gain at the end?",
            answer=f"They reached {prize.phrase} in {place.name}, and the path opened because they cooperated.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    task: Task = world.facts["task"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together to do something that is hard to do alone.",
        ),
        QAItem(
            question="What does a trigger do?",
            answer="A trigger is something that starts a change or makes a special action happen.",
        ),
        QAItem(
            question="Why can two helpers be better than one?",
            answer="Two helpers can share the work, make a plan, and finish a hard job more safely and quickly.",
        ),
        QAItem(
            question=f"Why was the {task.trigger} important?",
            answer=f"The {task.trigger} was important because it was the part of the magic that needed both friends to act together.",
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


# ---------------------------------------------------------------------------
# Verification / ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
task(T) :- task_id(T).
prize(PZ) :- prize_id(PZ).

valid_combo(Place, Task, Prize) :- affords(Place, Task), prize_in(Prize, Place), teamwork_task(Task).
needs_teamwork(Task) :- teamwork_task(Task).
triggered(Task) :- needs_teamwork(Task).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task_id", tid))
        lines.append(asp.fact("teamwork_task", tid))
        lines.append(asp.fact("trigger_word", tid, task.trigger))
    for prid, prize in PRIZES.items():
        lines.append(asp.fact("prize_id", prid))
        lines.append(asp.fact("prize_in", prid, prize.place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP gate matches Python valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python valid_combos():")
    if python_set - asp_set:
        print("  only in Python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about trigger, teamwork, and a magical shared success.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "princess", "prince", "fairy", "knight"], default=None)
    ap.add_argument("--partner-name")
    ap.add_argument("--partner-type", choices=["girl", "boy", "princess", "prince", "fairy", "knight"], default=None)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, prize = rng.choice(sorted(combos))

    hero_name = args.hero_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    partner_name = args.partner_name or rng.choice([n for n in PARTNER_NAMES if n != hero_name])
    if args.hero_type:
        hero_type = args.hero_type
    else:
        hero_type = rng.choice(["girl", "boy", "princess", "prince", "fairy", "knight"])
    if args.partner_type:
        partner_type = args.partner_type
    else:
        partner_type = rng.choice(["girl", "boy", "princess", "prince", "fairy", "knight"])

    return StoryParams(
        place=place,
        task=task,
        prize=prize,
        hero_name=hero_name,
        hero_type=hero_type,
        partner_name=partner_name,
        partner_type=partner_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
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
        print()
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"  {e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for item in combos:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams(place="forest", task="raise_bridge", prize="key", hero_name="Lina", hero_type="girl", partner_name="Moss", partner_type="fairy"),
        StoryParams(place="castle", task="open_gate", prize="crown", hero_name="Finn", hero_type="boy", partner_name="Luna", partner_type="fairy"),
        StoryParams(place="garden", task="light_path", prize="rose", hero_name="Nora", hero_type="girl", partner_name="Wren", partner_type="knight"),
    ]

    if args.all:
        for p in curated:
            samples.append(generate(p))
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.task} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
