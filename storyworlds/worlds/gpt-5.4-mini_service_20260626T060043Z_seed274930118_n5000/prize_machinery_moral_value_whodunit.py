#!/usr/bin/env python3
"""
A small whodunit-style storyworld about a missing prize, a bit of machinery,
and a moral-value turn where honesty solves the puzzle.

The premise:
- A child celebrates with a prize at a small fair or workshop.
- A machine makes a confusing noise, a prize disappears, and everyone suspects
  a problem with the machinery.
- The true turn is revealed by tracing small physical clues and social cues.
- The ending proves a moral value: honesty, fairness, or responsibility.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    keeper: Optional[str] = None
    hidden_in: str = ""
    usable: bool = False
    broken: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    name: str
    indoors: bool
    has_machinery: bool
    machine_name: str
    clue_places: list[str]


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    value: str
    hidden_place: str


@dataclass
class StoryParams:
    place: str
    prize: str
    machine: str
    hero_name: str
    hero_type: str
    helper_type: str
    moral_value: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "fair": Place(
        name="the fair",
        indoors=False,
        has_machinery=True,
        machine_name="popcorn machine",
        clue_places=["under the counter", "behind the prize wheel", "near the popcorn tray"],
    ),
    "arcade": Place(
        name="the arcade",
        indoors=True,
        has_machinery=True,
        machine_name="ticket machine",
        clue_places=["under the bench", "behind the ticket counter", "beside the game cabinet"],
    ),
    "workshop": Place(
        name="the workshop",
        indoors=True,
        has_machinery=True,
        machine_name="pressing machine",
        clue_places=["under the table", "near the tool shelf", "beside the metal bin"],
    ),
}

PRIZES = {
    "ribbon": Prize(
        label="ribbon",
        phrase="a bright blue prize ribbon",
        type="ribbon",
        value="special",
        hidden_place="pinned to a board",
    ),
    "trophy": Prize(
        label="trophy",
        phrase="a little gold trophy",
        type="trophy",
        value="shiny",
        hidden_place="in a display case",
    ),
    "medal": Prize(
        label="medal",
        phrase="a round silver medal",
        type="medal",
        value="glittery",
        hidden_place="inside a small box",
    ),
}

MACHINES = {
    "popcorn machine": {
        "sound": "whirred and clicked",
        "clue": "buttered crumbs",
        "risk": "stuck lid",
    },
    "ticket machine": {
        "sound": "clanked and beeped",
        "clue": "tiny paper strips",
        "risk": "jammed roll",
    },
    "pressing machine": {
        "sound": "hummed and thumped",
        "clue": "flat little dents",
        "risk": "worn gear",
    },
}

MORAL_VALUES = {
    "honesty": {
        "lesson": "telling the truth helps people solve hard problems",
        "turn": "admitted",
    },
    "responsibility": {
        "lesson": "taking care of your own actions helps everyone trust you",
        "turn": "fessed up",
    },
    "fairness": {
        "lesson": "being fair means sharing clues and listening to everyone",
        "turn": "shared the clue",
    },
}

HERO_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Theo", "Lily", "Finn"]
HELPER_TYPES = ["mother", "father", "sister", "brother", "uncle", "aunt"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A prize is in danger if the machine area contains a clue that points away
% from the obvious suspect.
suspect(machinery) :- clue(C), machine_clue(C).
suspect(person) :- clue(C), human_clue(C).

moral_resolution(honesty) :- told_truth.
moral_resolution(responsibility) :- owned_mistake.
moral_resolution(fairness) :- shared_clue.

valid_story(P, Pr, M, V) :- place(P), prize(Pr), machine(M), moral(V).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        if p.has_machinery:
            lines.append(asp.fact("machine_place", pid, p.machine_name))
    for prid, pr in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("value", prid, pr.value))
    for m in MACHINES:
        lines.append(asp.fact("machine", m))
        lines.append(asp.fact("machine_clue", MACHINES[m]["clue"]))
    for v in MORAL_VALUES:
        lines.append(asp.fact("moral", v))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    # Reasonableness here is intentionally simple: every registry entry should
    # be representable, and the inline program should parse.
    try:
        import asp
        _ = asp.one_model(asp_program("#show valid_story/4."))
    except Exception as e:
        print(f"ASP verification failed: {e}")
        return 1
    print("OK: ASP program loaded.")
    return 0


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def intro(world: World, hero: Entity, helper: Entity, prize: Entity, machine_name: str) -> None:
    world.say(
        f"{hero.id} arrived at {world.place.name} with {helper.name_or_label()} and a proud smile, "
        f"because {hero.pronoun('possessive')} {prize.label} was a prize worth showing off."
    )
    world.say(
        f"Near the room's noisy {machine_name}, everyone could hear a sound that "
        f"made the place feel like a mystery waiting to be solved."
    )

def add_clue(world: World, clue_text: str) -> None:
    world.say(clue_text)

def suspect_scene(world: World, hero: Entity, helper: Entity, prize: Entity, machine_name: str, machine_info: dict) -> None:
    world.say(
        f"Then something odd happened: the {prize.label} was gone, and the {machine_name} "
        f"{machine_info['sound']} like it had swallowed the answer."
    )
    world.say(
        f"{helper.name_or_label()} pointed at the machine at once. "
        f'"Maybe the {machine_name} took it," {helper.pronoun()} said.'
    )
    world.say(
        f"{hero.id} frowned and looked at the floor instead of the machine, because the little clues "
        f"did not feel like a machine trick at all."
    )

def detect_turn(world: World, hero: Entity, helper: Entity, prize: Entity, machine_name: str, prize_cfg: Prize) -> None:
    world.say(
        f"{hero.id} noticed a trail of {world.facts['clue']} leading to {prize_cfg.hidden_place}, "
        f"not inside the {machine_name}."
    )
    world.say(
        f"When {hero.id} opened the hiding place, the {prize.label} was there, tucked away as neatly as a secret."
    )

def moral_turn(world: World, hero: Entity, helper: Entity, value: str) -> None:
    moral = MORAL_VALUES[value]
    if value == "honesty":
        world.say(
            f"{hero.id} finally {moral['turn']} that {hero.pronoun('possessive')} surprise was so big that "
            f"{hero.pronoun()} had moved the {world.facts['prize'].label} to keep it safe."
        )
    elif value == "responsibility":
        world.say(
            f"{hero.id} {moral['turn']} that {hero.pronoun('possessive')} own careful planning had caused the confusion, "
            f"because {hero.pronoun()} had hidden the {world.facts['prize'].label} and forgotten to say so."
        )
    else:
        world.say(
            f"{hero.id} {moral['turn']} the clue with {helper.name_or_label()}, so they could both follow it and share the answer."
        )
    world.say(
        f"That was the real solution: {moral['lesson']}, and the room felt kinder once the truth was spoken."
    )

def ending(world: World, hero: Entity, prize: Entity, helper: Entity, machine_name: str) -> None:
    world.say(
        f"In the end, the {machine_name} was only noisy, the prize was safe, and {hero.id} "
        f"stood a little taller beside {helper.name_or_label()}."
    )
    world.say(
        f"The mystery was solved, not by blaming the machine, but by telling the truth and looking carefully."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A kid-friendly whodunit storyworld about a missing prize and machinery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--machine", choices=list(MACHINES))
    ap.add_argument("--moral-value", choices=MORAL_VALUES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_TYPES)
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
    prize = args.prize or rng.choice(list(PRIZES))
    machine = args.machine or PLACES[place].machine_name
    if machine != PLACES[place].machine_name:
        raise StoryError("That machine does not belong in that setting.")
    moral_value = args.moral_value or rng.choice(list(MORAL_VALUES))
    name = args.name or rng.choice(HERO_NAMES)
    helper_type = args.helper or rng.choice(HELPER_TYPES)
    return StoryParams(
        place=place,
        prize=prize,
        machine=machine,
        hero_name=name,
        hero_type="girl" if name in {"Mia", "Nora", "Ava", "Lily"} else "boy",
        helper_type=helper_type,
        moral_value=moral_value,
    )


def _story_params_to_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    prize_cfg = PRIZES[params.prize]
    machine_info = MACHINES[params.machine]
    world = World(place)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=f"the {params.helper_type}"))
    prize = world.add(Entity(
        id="prize", kind="thing", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, hidden_in=prize_cfg.hidden_place
    ))
    machine = world.add(Entity(
        id="machine", kind="thing", type="machine", label=params.machine,
        usable=True, broken=False
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        machine=machine,
        prize_cfg=prize_cfg,
        machine_info=machine_info,
        moral_value=params.moral_value,
    )

    intro(world, hero, helper, prize, params.machine)
    world.para()
    suspect_scene(world, hero, helper, prize, params.machine, machine_info)
    world.para()

    clue_text = f"{hero.id} spotted {machine_info['clue']} near one of the {place.clue_places[0]}."
    world.facts["clue"] = machine_info["clue"]
    add_clue(world, clue_text)
    add_clue(world, f"That clue led {hero.id} away from the noisy machine and toward the hiding place.")
    world.para()

    detect_turn(world, hero, helper, prize, params.machine, prize_cfg)
    moral_turn(world, hero, helper, params.moral_value)
    world.para()
    ending(world, hero, prize, helper, params.machine)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["prize_cfg"]
    return [
        f"Write a short whodunit for young children about a missing {p.label} and a noisy machine.",
        f"Tell a mystery story where the clue is {world.facts['clue']} and the ending teaches {world.facts['moral_value']}.",
        f"Create a gentle detective story set at {world.place.name} that ends with the prize being found and the truth coming out.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    prize = world.facts["prize"]
    return [
        QAItem(
            question=f"What prize was missing in the story?",
            answer=f"The missing prize was {prize.phrase}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look for the missing prize?",
            answer=f"{helper.name_or_label()} helped {hero.id} look for it.",
        ),
        QAItem(
            question=f"What clue led the detective away from blaming the machine?",
            answer=f"The clue was {world.facts['clue']}.",
        ),
        QAItem(
            question=f"What moral value did the story teach?",
            answer=f"The story taught {world.facts['moral_value']}, because the truth solved the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is machinery?",
            answer="Machinery means machines and parts that work together to do a job.",
        ),
        QAItem(
            question="What does honesty mean?",
            answer="Honesty means telling the truth, even when it feels hard.",
        ),
        QAItem(
            question="Why do people check clues in a mystery?",
            answer="People check clues so they can figure out what really happened instead of guessing.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = _story_params_to_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(bits))
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        print(sorted(asp.atoms(model, "valid_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        curated = [
            StoryParams("fair", "ribbon", "popcorn machine", "Mia", "girl", "mother", "honesty"),
            StoryParams("arcade", "medal", "ticket machine", "Leo", "boy", "father", "fairness"),
            StoryParams("workshop", "trophy", "pressing machine", "Nora", "girl", "uncle", "responsibility"),
        ]
        samples = [generate(p) for p in curated]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
