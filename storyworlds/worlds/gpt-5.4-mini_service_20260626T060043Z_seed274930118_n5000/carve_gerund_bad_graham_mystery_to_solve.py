#!/usr/bin/env python3
"""
storyworlds/worlds/carve_gerund_bad_graham_mystery_to_solve.py
==============================================================

A gentle ghost-story world with a small mystery to solve.

Seed words and narrative instruments:
- carve-gerund
- bad
- graham
- Mystery to Solve
- Ghost Story

Premise:
A child visits a spooky old place to carve a lantern for a quiet night.
A mysterious "bad" problem keeps ruining the plan, and the ghost Graham
helps solve it by finding the true cause.

The world is intentionally tiny: one setting, one carving activity, one
mystery, and one resolution path. State changes drive the prose:
- carving raises delight and light
- bad drafts/snags/extinguishers increase fear and confusion
- solving the mystery reduces fear and proves Graham is helpful, not bad
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    cause: str
    solution: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    delight: str
    light: str
    mess: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting, mystery: Mystery):
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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

        w = World(self.setting, self.mystery)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _meter(entity: Entity, key: str) -> float:
    return float(entity.meters.get(key, 0.0))


def _mem(entity: Entity, key: str) -> float:
    return float(entity.memes.get(key, 0.0))


def _add_meter(entity: Entity, key: str, amount: float) -> None:
    entity.meters[key] = _meter(entity, key) + amount


def _add_mem(entity: Entity, key: str, amount: float) -> None:
    entity.memes[key] = _mem(entity, key) + amount


def _set_mem(entity: Entity, key: str, value: float) -> None:
    entity.memes[key] = value


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (rule_bad_clue, rule_ghost_helps, rule_reveal, rule_relief):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def rule_bad_clue(world: World) -> list[str]:
    child = world.get(world.facts["child"])
    clue = world.facts["mystery"].clue
    if _mem(child, "confused") < THRESHOLD:
        return []
    sig = ("bad_clue",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    _add_mem(child, "fear", 1.0)
    return [f"The clue looked bad and strange, and {child.id} shivered beside the {clue}."]


def rule_ghost_helps(world: World) -> list[str]:
    graham = world.get("Graham")
    child = world.get(world.facts["child"])
    if _mem(child, "fear") < THRESHOLD or _mem(graham, "kindness") < THRESHOLD:
        return []
    sig = ("ghost_helps",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    _add_mem(child, "trust", 1.0)
    return ["Graham drifted close and pointed at the right place, gentle as a candle flame."]


def rule_reveal(world: World) -> list[str]:
    child = world.get(world.facts["child"])
    if _mem(child, "trust") < THRESHOLD:
        return []
    sig = ("reveal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mystery = world.mystery
    return [mystery.reveal]


def rule_relief(world: World) -> list[str]:
    child = world.get(world.facts["child"])
    graham = world.get("Graham")
    if _mem(child, "trust") < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    _set_mem(child, "fear", 0.0)
    _add_mem(child, "joy", 1.0)
    _add_mem(graham, "pride", 1.0)
    return ["After that, the bad feeling slipped away, and the room seemed warm again."]


SETTING = Setting(
    place="the old house on Pine Street",
    mood="spooky",
    affords={"carve"},
)

ACTIVITY = Activity(
    id="carve",
    verb="carve a pumpkin lantern",
    gerund="carving a pumpkin lantern",
    rush="hurry to finish the face",
    delight="the sweet scrape of the knife made the pumpkin feel like it was smiling back",
    light="the candle inside made a small orange glow",
    mess="pumpkin pulp",
    tags={"carve", "pumpkin", "light"},
)

MYSTERY = Mystery(
    id="missing-light",
    clue="the lantern window",
    cause="a bad draft from a loose cellar door",
    solution="the cellar door was pushing cold air through the hall",
    reveal="Graham found the real trouble: a loose cellar door was making a bad draft, so the candle kept flickering out.",
    tags={"draft", "door", "candle"},
)

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Theo", "Finn", "Ben", "Max", "Owen"]
TRAITS = ["curious", "brave", "gentle", "quiet", "careful", "hopeful"]


@dataclass
class StoryParams:
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("setting", "old_house"))
    lines.append(asp.fact("mood", "old_house", SETTING.mood))
    lines.append(asp.fact("affords", "old_house", "carve"))
    lines.append(asp.fact("activity", "carve"))
    lines.append(asp.fact("mess_of", "carve", ACTIVITY.mess))
    lines.append(asp.fact("light_of", "carve", "candle"))
    lines.append(asp.fact("mystery", MYSTERY.id))
    lines.append(asp.fact("cause", MYSTERY.id, "bad_draft"))
    lines.append(asp.fact("solution", MYSTERY.id, "loose_cellar_door"))
    lines.append(asp.fact("ghost", "Graham"))
    lines.append(asp.fact("helps", "Graham", MYSTERY.id))
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is solvable if the ghost helps and the true cause is discovered.
solvable(M) :- mystery(M), ghost("Graham"), helps("Graham", M), cause(M, C), solution(M, S), C != S.

% A good story needs a spooky setting and a solved mystery.
good_story(P, M) :- setting(P), mood(P, spooky), solvable(M), mystery(M).
#show solvable/1.
#show good_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp

    model = asp.one_model(asp_program("#show good_story/2."))
    return bool(asp.atoms(model, "good_story"))


def asp_verify() -> int:
    ok = asp_valid()
    py = reasonableness_gate()
    if ok == py:
        print("OK: ASP and Python agree on the mystery being solvable.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


def reasonableness_gate() -> bool:
    return (
        SETTING.place.startswith("the old house")
        and SETTING.mood == "spooky"
        and MYSTERY.cause != MYSTERY.solution
        and "carve" in SETTING.affords
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story world with a mystery to solve.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    gender = args.gender
    if gender is None:
        gender = rng.choice(["girl", "boy"])
    if args.name is None:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    else:
        name = args.name
    if args.name and args.gender:
        if (args.name in GIRL_NAMES and args.gender != "girl") or (args.name in BOY_NAMES and args.gender != "boy"):
            raise StoryError("The chosen name and gender do not match this world.")
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, trait=trait)


def _introduce(world: World, hero: Entity, graham: Entity) -> None:
    world.say(
        f"On a spooky evening, {hero.id} came to {world.setting.place} to see a ghost story come alive."
    )
    world.say(
        f"Inside, {graham.id} the ghost floated by the window. He was not bad at all, just shy and pale as moonlight."
    )


def _carve(world: World, hero: Entity) -> None:
    _add_meter(hero, "carving", 1.0)
    _add_mem(hero, "joy", 1.0)
    world.say(
        f"{hero.id} began {ACTIVITY.gerund}, and {ACTIVITY.delight}."
    )
    world.say(
        f"At last, {ACTIVITY.light}."
    )


def _mystery_turn(world: World, hero: Entity) -> None:
    _add_mem(hero, "confused", 1.0)
    _add_mem(hero, "worry", 1.0)
    world.say(
        f"But then the lantern kept going dim, and that felt bad. {hero.id} frowned and looked for the reason."
    )
    world.say(
        f"The little flame flickered whenever {hero.id} tried to {ACTIVITY.rush}."
    )


def _solve(world: World, hero: Entity, graham: Entity) -> None:
    _add_mem(graham, "kindness", 1.0)
    _add_mem(graham, "help", 1.0)
    _add_mem(hero, "trust", 1.0)
    propagate(world, narrate=True)
    world.say(
        f"{hero.id} smiled at Graham, because the ghost had turned the bad mystery into a simple one."
    )
    world.say(
        f"Together they shut the loose cellar door, and the lantern glowed steady and bright."
    )


def tell(name: str, gender: str, trait: str) -> World:
    world = World(SETTING, MYSTERY)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        traits=["little", trait],
        meters={"carving": 0.0},
        memes={"joy": 0.0, "confused": 0.0, "worry": 0.0, "trust": 0.0, "fear": 0.0},
    ))
    graham = world.add(Entity(
        id="Graham",
        kind="character",
        type="ghost",
        label="Graham",
        traits=["shy", "kind"],
        memes={"kindness": 1.0, "pride": 0.0},
    ))
    world.facts.update(child=hero.id, graham=graham.id, mystery=MYSTERY, activity=ACTIVITY, setting=SETTING)
    _introduce(world, hero, graham)
    world.para()
    _carve(world, hero)
    world.para()
    _mystery_turn(world, hero)
    _solve(world, hero, graham)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.get(world.facts["child"])
    return [
        'Write a short Ghost Story for a child who is carving a pumpkin lantern in a spooky old house.',
        f"Tell a mystery to solve where {hero.id} keeps seeing a bad flicker and Graham the ghost helps find the cause.",
        f"Write a gentle spooky story that includes the word 'carving' and ends with the mystery solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get(world.facts["child"])
    return [
        QAItem(
            question=f"What was {hero.id} doing in the old house?",
            answer=f"{hero.id} was carving a pumpkin lantern in the old house on Pine Street.",
        ),
        QAItem(
            question="Why did the lantern keep going dim?",
            answer="It kept going dim because a bad draft from a loose cellar door was blowing through the hall.",
        ),
        QAItem(
            question="Who helped solve the mystery?",
            answer="Graham the ghost helped solve the mystery, and he was kind rather than bad.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="The loose cellar door was shut, the bad draft stopped, and the lantern glowed steady and bright.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a draft?",
            answer="A draft is a flow of air that sneaks through cracks or open doors and can make a room feel cold.",
        ),
        QAItem(
            question="What does carving mean?",
            answer="Carving means cutting a shape or picture into something like wood, fruit, or a pumpkin.",
        ),
        QAItem(
            question="Why do people use a candle inside a pumpkin lantern?",
            answer="People use a candle inside a pumpkin lantern to make the carved face glow from the inside.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for (n,) in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.trait)
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
    StoryParams(name="Mia", gender="girl", trait="curious"),
    StoryParams(name="Leo", gender="boy", trait="brave"),
    StoryParams(name="Nora", gender="girl", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show good_story/2."))
        atoms = asp.atoms(model, "good_story")
        print(f"{len(atoms)} compatible story shape(s).")
        for a in atoms:
            print(a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

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
