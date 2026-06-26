#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/seclude_mommy_lesson_learned_flashback_rhyming_story.py
===============================================================================================================================

A small story world in a rhyming-story style, built from the seed words
"seclude" and "mommy" with flashback and lesson-learned structure.

Premise:
- A child wants to seclude mommy in a quiet cozy nook so she can rest.
- The world tracks physical quiet/cosy state and emotional care/worry.

Turn:
- A noisy interruption reminds the child, through a flashback, why mommy needs
  a calm space.

Resolution:
- The child makes a better quiet place, and the story ends with the learned
  lesson: caring means making room for peace.

This script follows the Storyworld contract:
- self-contained stdlib script
- eager import of results.py
- lazy import of asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {
                "quiet": 0.0,
                "cozy": 0.0,
                "noisy": 0.0,
            }
        if not self.memes:
            self.memes = {
                "care": 0.0,
                "worry": 0.0,
                "joy": 0.0,
                "lesson": 0.0,
                "flashback": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "mommy"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class Setting:
    place: str
    indoors: bool = True
    feels: str = "soft and warm"


@dataclass
class Goal:
    id: str
    label: str
    verb: str
    rhyme: str
    effect: str
    requires_quiet: bool = True
    makes_cozy: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ComfortItem:
    id: str
    label: str
    phrase: str
    adds_cozy: float = 1.0
    adds_quiet: float = 1.0
    covers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    goal: str
    comfort: str
    child_name: str
    child_gender: str
    parent_role: str
    seed: Optional[int] = None


SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoors=True, feels="soft and hushy"),
    "livingroom": Setting(place="the living room", indoors=True, feels="bright and comfy"),
    "readingnook": Setting(place="the reading nook", indoors=True, feels="small and snug"),
}

GOALS = {
    "seclude": Goal(
        id="seclude",
        label="make a secluded spot",
        verb="seclude mommy",
        rhyme="hide from the jingle",
        effect="make a little hushy nest",
        tags={"quiet", "rest"},
    ),
    "rest": Goal(
        id="rest",
        label="help mommy rest",
        verb="help mommy rest",
        rhyme="slow down the tumble",
        effect="make a calm little corner",
        tags={"quiet", "rest"},
    ),
    "read": Goal(
        id="read",
        label="read a bedtime book",
        verb="read a bedtime book",
        rhyme="turn the page with grace",
        effect="make a cozy reading place",
        tags={"quiet", "book"},
    ),
}

COMFORTS = {
    "blanketfort": ComfortItem(
        id="blanketfort",
        label="a blanket fort",
        phrase="a soft blanket fort",
        adds_cozy=2.0,
        adds_quiet=1.0,
        tags={"cozy", "quiet"},
    ),
    "pillows": ComfortItem(
        id="pillows",
        label="pillows",
        phrase="plump pillows",
        adds_cozy=1.0,
        adds_quiet=0.5,
        tags={"cozy"},
    ),
    "curtain": ComfortItem(
        id="curtain",
        label="a curtain",
        phrase="a sleepy curtain",
        adds_cozy=0.5,
        adds_quiet=2.0,
        tags={"quiet"},
    ),
}

CHILD_NAMES = ["Mia", "Lily", "Nora", "Tia", "Eli", "Owen"]
TRAITS = ["tiny", "curious", "sweet", "brave", "gentle", "bouncy"]


class StoryWorld(World):
    def __init__(self, place: str):
        super().__init__(place)
        self.fired: set[str] = set()
        self.flashback_seen = False


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _add_meter(e: Entity, key: str, amount: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


def _add_mem(e: Entity, key: str, amount: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


def rhyme_line(a: str, b: str) -> str:
    return f"{a}, {b}."


def setup_story(world: StoryWorld, child: Entity, mommy: Entity, goal: Goal, comfort: ComfortItem) -> None:
    world.say(
        f"{child.id} was a {child.memes.get('trait_word', 'little')} child who loved to rhyme and play."
    )
    world.say(
        f"{child.id} wanted to {goal.verb} and keep the noise away."
    )
    world.say(
        f"{child.id} found {comfort.phrase}, all tidy and bright, "
        f"and thought it would help make the room feel right."
    )
    _add_mem(child, "care", 1.0)
    _add_mem(mommy, "worry", 0.5)


def build_noise(world: StoryWorld, child: Entity, mommy: Entity) -> None:
    _add_meter(world.get("room"), "noisy", 1.5)
    _add_mem(mommy, "worry", 1.0)
    world.say(
        f"But a noisy toy jangled with a clatter and ring, "
        f"and mommy sighed softly, not wanting a thing."
    )


def flashback(world: StoryWorld, child: Entity, mommy: Entity) -> None:
    if world.flashback_seen:
        return
    world.flashback_seen = True
    _add_mem(child, "flashback", 1.0)
    world.say(
        f"{child.id} had a flashback then, clear as a bell: "
        f"last night mommy looked tired and not feeling well."
    )
    world.say(
        f"She had rested in hush after work and chores, "
        f"so the child knew quiet could open sweet doors."
    )


def make_better_space(world: StoryWorld, child: Entity, mommy: Entity, comfort: ComfortItem) -> None:
    room = world.get("room")
    _add_meter(room, "quiet", comfort.adds_quiet)
    _add_meter(room, "cozy", comfort.adds_cozy)
    _add_mem(child, "care", 1.0)
    if comfort.id == "blanketfort":
        world.say(
            f"{child.id} tucked in the blanket fort tight, "
            f"then whispered, \"Mommy, this nook feels just right!\""
        )
    elif comfort.id == "curtain":
        world.say(
            f"{child.id} drew the curtain down, soft as a dream, "
            f"to hush the room down to a moonbeam beam."
        )
    else:
        world.say(
            f"{child.id} stacked up the pillows in a little round row, "
            f"to make a soft castle where whispers could grow."
        )


def lesson_learned(world: StoryWorld, child: Entity, mommy: Entity, goal: Goal) -> None:
    child.memes["lesson"] = 1.0
    mommy.memes["joy"] += 1.0
    mommy.memes["worry"] = 0.0
    world.say(
        f"{child.id} learned a sweet lesson that day: "
        f"to care for mommy, make room for peace in play."
    )
    world.say(
        f"So mommy could rest in a cozy, calm light, "
        f"and {child.id} could still smile with rhymes held tight."
    )


def tell_world(params: StoryParams) -> StoryWorld:
    setting = SETTINGS[params.setting]
    goal = GOALS[params.goal]
    comfort = COMFORTS[params.comfort]
    world = StoryWorld(setting.place)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
    ))
    child.memes["trait_word"] = TRAITS[0]  # store a lightweight label in the emotional map
    mommy = world.add(Entity(
        id="Mommy",
        kind="character",
        type="mommy",
        label="mommy",
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label=setting.place,
    ))
    world.add(Entity(
        id=comfort.id,
        kind="thing",
        type="comfort",
        label=comfort.label,
        phrase=comfort.phrase,
    ))

    setup_story(world, child, mommy, goal, comfort)
    world.para()
    world.say(
        f"The room felt {setting.feels}, and {setting.place} was almost quiet as can be."
    )
    world.say(
        f"But then came the clatter that shook up the tree."
    )
    build_noise(world, child, mommy)
    flashback(world, child, mommy)
    world.para()
    make_better_space(world, child, mommy, comfort)
    lesson_learned(world, child, mommy, goal)
    world.para()
    world.say(
        f"Now mommy could rest in the hush of the night, "
        f"and {child.id} felt proud for choosing what's right."
    )

    world.facts.update(
        child=child,
        mommy=mommy,
        room=room,
        setting=setting,
        goal=goal,
        comfort=comfort,
    )
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    child = f["child"]
    goal = f["goal"]
    comfort = f["comfort"]
    return [
        f'Write a rhyming story for preschoolers about {child.id} trying to {goal.verb} with a {comfort.label}.',
        f"Tell a gentle flashback story where a child learns a lesson about giving mommy a quiet place.",
        f'Write a short rhyming tale using the words "seclude" and "mommy" and ending with a lesson learned.',
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    mommy = f["mommy"]
    goal = f["goal"]
    comfort = f["comfort"]
    return [
        QAItem(
            question=f"Who wanted to {goal.verb} in the story?",
            answer=f"{child.id} wanted to {goal.verb} because {child.id} was trying to help mommy have a quiet place.",
        ),
        QAItem(
            question="What happened in the flashback?",
            answer="The child remembered that mommy had looked tired before, so quiet time felt kind and important.",
        ),
        QAItem(
            question=f"What did {child.id} use to make the room better?",
            answer=f"{child.id} used {comfort.phrase} to make the room softer, quieter, and more cozy for mommy.",
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer="The child learned that caring means making space for peace, especially when mommy needs rest.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What does seclude mean?",
            answer="To seclude someone means to put them in a quiet, private place away from noise or busy crowds.",
        ),
        QAItem(
            question="Why do people want a quiet room sometimes?",
            answer="People want a quiet room sometimes because it helps them rest, think, or feel calm.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when the story remembers something that happened earlier.",
        ),
        QAItem(
            question="What is a lesson learned in a story?",
            answer="A lesson learned is the idea the main character understands by the end, like how to be kind or careful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if isinstance(v, (int, float)) and v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {', '.join(bits) if bits else 'quiet'}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(room).
goal(seclude).
comfort(blanketfort).
quiet_help(G,C) :- goal(G), comfort(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show setting/1. #show goal/1. #show comfort/1."))
    atoms = set()
    for pred in ("setting", "goal", "comfort"):
        atoms.update(asp.atoms(model, pred))
    expected = {(k,) for k in SETTINGS} | {(k,) for k in GOALS} | {(k,) for k in COMFORTS}
    if atoms == expected:
        print(f"OK: ASP registry parity check passed ({len(expected)} atoms).")
        return 0
    print("MISMATCH in ASP registry parity check.")
    print("expected:", sorted(expected))
    print("got:", sorted(atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world with seclude, mommy, flashback, and lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mommy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    goal = args.goal or rng.choice(list(GOALS))
    comfort = args.comfort or rng.choice(list(COMFORTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or "mommy"
    return StoryParams(
        setting=setting,
        goal=goal,
        comfort=comfort,
        child_name=name,
        child_gender=gender,
        parent_role=parent,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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
    StoryParams(setting="bedroom", goal="seclude", comfort="blanketfort", child_name="Mia", child_gender="girl", parent_role="mommy"),
    StoryParams(setting="livingroom", goal="rest", comfort="curtain", child_name="Owen", child_gender="boy", parent_role="mommy"),
    StoryParams(setting="readingnook", goal="read", comfort="pillows", child_name="Nora", child_gender="girl", parent_role="mommy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show setting/1. #show goal/1. #show comfort/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show setting/1. #show goal/1. #show comfort/1."))
        print(f"settings: {sorted(set(asp.atoms(model, 'setting')))}")
        print(f"goals: {sorted(set(asp.atoms(model, 'goal')))}")
        print(f"comforts: {sorted(set(asp.atoms(model, 'comfort')))}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
