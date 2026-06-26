#!/usr/bin/env python3
"""
storyworlds/worlds/reflexology_mystery_to_solve_heartwarming.py
===============================================================

A small heartwarming story world about a gentle mystery that gets solved with
reflexology, warm care, and a cozy ending.

Premise:
- A child notices that a loved one is moving slowly and seems puzzled by sore,
  tired feet.
- The child gathers a few clues about what happened during the day.
- A kind helper explains a simple reflexology routine.
- The feet feel better, the mystery becomes clear, and the home feels warm
  again.

The world is intentionally tiny and classical: a few typed entities, physical
meters for tiredness and comfort, and emotional memes for worry, curiosity, and
relief. The prose is driven from the simulated state rather than from a fixed
template.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "helper"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self):
        for k in ["tired", "comfort", "warmth", "clean", "fuzz", "care"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "curiosity", "relief", "love", "hope", "calm"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def be(self) -> str:
        return "are" if self.plural else "is"

    def have(self) -> str:
        return "have" if self.plural else "has"


@dataclass
class Setting:
    place: str
    indoor: bool = True
    cozy: bool = True
    items: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    answer: str
    trigger: str
    diagnosis: str
    solved_by: str = "reflexology"
    tags: set[str] = field(default_factory=set)


@dataclass
class CareAction:
    id: str
    label: str
    verb: str
    prep: str
    effect_tired: float
    effect_comfort: float
    effect_worry: float
    effect_relief: float
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, items={"tea", "chair", "table"}),
    "living_room": Setting(place="the living room", indoor=True, items={"couch", "blanket", "lamp"}),
    "sunroom": Setting(place="the sunroom", indoor=True, items={"rug", "potted plant", "window"}),
    "clinic": Setting(place="the cozy clinic", indoor=True, items={"bench", "towel", "stool"}),
}

MYSTERIES = {
    "tired_feet": Mystery(
        id="tired_feet",
        clue="slow steps and a little sigh",
        answer="a long day of walking and standing",
        trigger="after the market trip",
        diagnosis="tired feet",
        solved_by="reflexology",
        tags={"feet", "walking", "tired"},
    ),
    "grumpy_mood": Mystery(
        id="grumpy_mood",
        clue="a frown that would not go away",
        answer="a body that needed rest and care",
        trigger="after a busy afternoon",
        diagnosis="a weary feeling",
        solved_by="reflexology",
        tags={"mood", "care", "rest"},
    ),
    "sleepy_evening": Mystery(
        id="sleepy_evening",
        clue="yawns and droopy shoulders",
        answer="a day that was simply a little too full",
        trigger="before bedtime",
        diagnosis="sleepy feet and a sleepy heart",
        solved_by="reflexology",
        tags={"sleep", "feet", "soft"},
    ),
}

ACTIONS = {
    "foot_rub": CareAction(
        id="foot_rub",
        label="reflexology",
        verb="press the gentle points on the feet",
        prep="warm your hands and trace the soft spots on each foot",
        effect_tired=-1.0,
        effect_comfort=1.2,
        effect_worry=-0.8,
        effect_relief=1.1,
        tags={"reflexology", "feet", "touch"},
    ),
    "warm_towel": CareAction(
        id="warm_towel",
        label="warm towel",
        verb="wrap the feet in a warm towel",
        prep="dip a towel in warm water and fold it carefully",
        effect_tired=-0.4,
        effect_comfort=0.8,
        effect_worry=-0.2,
        effect_relief=0.4,
        tags={"warm", "care"},
    ),
}

HERO_NAMES = ["Mina", "Luca", "Iris", "Noah", "June", "Eli", "Nora", "Pia"]
HELPER_NAMES = ["Mrs. Bell", "Grandma", "Grandpa", "Auntie Rose", "Mr. Pine"]
TRAITS = ["curious", "gentle", "thoughtful", "patient", "brave"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    mystery: str
    action: str
    hero_name: str
    hero_gender: str
    hero_trait: str
    loved_one: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World helpers
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for mystery_id, mystery in MYSTERIES.items():
            for action_id, action in ACTIONS.items():
                if mystery.solved_by == "reflexology" and action_id == "foot_rub":
                    combos.append((place, mystery_id, action_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming reflexology mystery story world."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--loved-one", choices=["grandma", "grandpa", "mother", "father", "auntie", "neighbor"])
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
    if args.action and args.action not in ACTIONS:
        raise StoryError("Unknown action.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")

    if args.action == "warm_towel" and args.mystery == "tired_feet":
        raise StoryError("A warm towel alone does not fully solve this mystery; use reflexology.")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, mystery_id, action_id = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    hero_trait = args.trait or rng.choice(TRAITS)
    loved_one = args.loved_one or rng.choice(["grandma", "grandpa", "mother", "father", "auntie", "neighbor"])
    return StoryParams(
        place=place,
        mystery=mystery_id,
        action=action_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        hero_trait=hero_trait,
        loved_one=loved_one,
    )


def _build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero_type = "girl" if params.hero_gender == "girl" else "boy"
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=hero_type,
        label=params.hero_name,
        traits=["little", params.hero_trait],
    ))
    loved = world.add(Entity(
        id=params.loved_one,
        kind="character",
        type=params.loved_one if params.loved_one in {"grandma", "grandpa", "mother", "father"} else "woman",
        label=params.loved_one,
    ))
    mystery = MYSTERIES[params.mystery]
    action = ACTIONS[params.action]
    feet = world.add(Entity(
        id="feet",
        kind="thing",
        type="feet",
        label="feet",
        phrase="tired feet",
        owner=loved.id,
        caretaker=hero.id,
    ))
    world.facts.update(hero=hero, loved=loved, mystery=mystery, action=action, feet=feet)
    return world


def _solve_mystery(world: World) -> None:
    hero: Entity = world.facts["hero"]
    loved: Entity = world.facts["loved"]
    mystery: Mystery = world.facts["mystery"]
    action: CareAction = world.facts["action"]
    feet: Entity = world.facts["feet"]

    hero.memes["curiosity"] += 1
    loved.memes["worry"] += 1
    feet.meters["tired"] += 1.2
    feet.memes["worry"] += 0.6

    world.say(
        f"{hero.id} was a little {hero.traits[1]} {hero.type} who noticed everything."
    )
    world.say(
        f"One {mystery.trigger}, {hero.id} saw {loved.id} moving with {mystery.clue}."
    )
    world.say(
        f"{hero.id} wondered what was making the day feel so heavy."
    )

    world.para()
    world.say(
        f"{hero.id} asked gentle questions and found a clue: {mystery.answer}."
    )
    world.say(
        f"{hero.id} thought the answer sounded simple, but the feet still needed care."
    )

    world.para()
    world.say(
        f"So {hero.id} helped {loved.id} sit down in {world.setting.place}."
    )
    world.say(
        f"Then {hero.id} chose to {action.prep}, because {action.label} could help the body settle."
    )
    feet.meters["tired"] = max(0.0, feet.meters["tired"] + action.effect_tired)
    feet.meters["comfort"] += action.effect_comfort
    loved.memes["worry"] = max(0.0, loved.memes["worry"] + action.effect_worry)
    loved.memes["relief"] += action.effect_relief
    loved.memes["calm"] += 1.0
    hero.memes["love"] += 1.0

    world.say(
        f"With each soft press, {loved.id} stopped frowning and let out a happy sigh."
    )
    world.say(
        f"The mystery was solved: {mystery.diagnosis} needed caring hands and a quiet moment."
    )

    world.para()
    world.say(
        f"At the end, {hero.id} smiled up at {loved.id}, and {loved.id} smiled back."
    )
    world.say(
        f"The room felt warm, the feet felt better, and the whole home seemed softer than before."
    )

    world.facts["solved"] = True


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    _solve_mystery(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    loved: Entity = f["loved"]
    mystery: Mystery = f["mystery"]
    action: CareAction = f["action"]
    return [
        f'Write a warm story for a young child about a mystery in {world.setting.place} that gets solved with "{action.label}".',
        f"Tell a heartwarming tale where {hero.id} notices {loved.id}'s {mystery.clue} and helps them feel better.",
        f'Write a simple mystery story that includes the word "{action.label}" and ends with relief and smiles.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    loved: Entity = f["loved"]
    mystery: Mystery = f["mystery"]
    action: CareAction = f["action"]
    feet: Entity = f["feet"]

    return [
        QAItem(
            question=f"What mystery did {hero.id} notice about {loved.id}?",
            answer=f"{hero.id} noticed that {loved.id} seemed to have {mystery.diagnosis}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} start solving the mystery?",
            answer=f"The clue was {mystery.clue}. That made {hero.id} curious enough to look closer.",
        ),
        QAItem(
            question=f"What did {hero.id} do to help {loved.id} feel better?",
            answer=f"{hero.id} used {action.label} to gently care for the feet and help the body relax.",
        ),
        QAItem(
            question=f"How did {loved.id} feel at the end?",
            answer=f"{loved.id} felt calmer and relieved, and the tired feet felt much better too.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is reflexology?",
            answer="Reflexology is a gentle kind of touch that presses parts of the feet or hands to help someone relax and feel cared for.",
        ),
        QAItem(
            question="Why can warm hands help before a foot rub?",
            answer="Warm hands feel gentle and comforting, so they help someone relax before touch begins.",
        ),
        QAItem(
            question="Why do tired feet sometimes need rest?",
            answer="Tired feet need rest because walking and standing all day can make them sore and heavy.",
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the reflexology action solves the mystery.
valid_story(P, M, A) :- setting(P), mystery(M), action(A), solves(A, M), heartwarming(M).
solves(foot_rub, M) :- mystery(M), solved_by(M, reflexology).
heartwarming(M) :- mystery(M), clue(M, _), answer(M, _).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("solved_by", mid, m.solved_by))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("answer", mid, m.answer))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((p, m, a) for p, m, a in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="kitchen", mystery="tired_feet", action="foot_rub", hero_name="Mina", hero_gender="girl", hero_trait="curious", loved_one="grandma"),
    StoryParams(place="living_room", mystery="grumpy_mood", action="foot_rub", hero_name="Luca", hero_gender="boy", hero_trait="gentle", loved_one="grandpa"),
    StoryParams(place="sunroom", mystery="sleepy_evening", action="foot_rub", hero_name="Iris", hero_gender="girl", hero_trait="thoughtful", loved_one="mother"),
]


def explain_rejection(action_id: str) -> str:
    if action_id != "foot_rub":
        return "(No story: this mystery is solved by reflexology, not by a different action.)"
    return "(No story: the selected combination does not fit the heartwarming reflexology mystery.)"


def build_valid_pool(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = valid_combos()
    out = []
    for p, m, a in combos:
        if args.place and p != args.place:
            continue
        if args.mystery and m != args.mystery:
            continue
        if args.action and a != args.action:
            continue
        out.append((p, m, a))
    return out


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, m, a) for p in SETTINGS for m in MYSTERIES for a in ACTIONS if a == "foot_rub"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.action != "foot_rub":
        raise StoryError(explain_rejection(args.action))
    pool = build_valid_pool(args)
    if not pool:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, action = rng.choice(sorted(pool))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    loved_one = args.loved_one or rng.choice(["grandma", "grandpa", "mother", "father", "auntie", "neighbor"])
    return StoryParams(place=place, mystery=mystery, action=action, hero_name=name, hero_gender=gender, hero_trait=trait, loved_one=loved_one)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mystery, action) combos:\n")
        for p, m, a in combos:
            print(f"  {p:12} {m:14} {a}")
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
            header = f"### {p.hero_name}: {p.mystery} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
