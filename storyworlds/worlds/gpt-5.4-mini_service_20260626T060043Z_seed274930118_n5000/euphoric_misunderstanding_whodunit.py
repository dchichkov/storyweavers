#!/usr/bin/env python3
"""
A small whodunit-style story world built around a misunderstanding and a euphoric reveal.

Seed premise:
- A child detective notices something missing.
- A clue points to the wrong suspect.
- The misunderstanding is resolved by a careful look at the evidence.
- The ending is euphoric because the lost thing is found and nobody is guilty after all.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    hides: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    hide_zone: str
    clue: str
    clue_place: str
    culprit_role: str
    culprit_reason: str
    scene_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    type: str
    label: str
    role_word: str
    innocence_hint: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace_log: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "museum": Setting(place="the museum", indoor=True, hides={"drawer", "display", "case"}),
    "library": Setting(place="the library", indoor=True, hides={"desk", "shelf", "cart"}),
    "garden": Setting(place="the garden", indoor=False, hides={"bush", "bench", "pot"}),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        label="brass bell",
        phrase="a tiny brass bell with a blue ribbon",
        hide_zone="drawer",
        clue="a blue ribbon snagged on a chair leg",
        clue_place="chair",
        culprit_role="helper",
        culprit_reason="to polish it for the show",
        scene_word="polish",
        tags={"blue", "metal", "ribbon"},
    ),
    "mask": Mystery(
        id="mask",
        label="paper mask",
        phrase="a painted paper mask with a gold star",
        hide_zone="shelf",
        clue="gold dust on a nearby window ledge",
        clue_place="window",
        culprit_role="wind",
        culprit_reason="to blow it behind the shelf",
        scene_word="wind",
        tags={"gold", "paper", "star"},
    ),
    "key": Mystery(
        id="key",
        label="small key",
        phrase="a small key tied to a green string",
        hide_zone="desk",
        clue="a green string looped around a teacup handle",
        clue_place="cup",
        culprit_role="pet",
        culprit_reason="to carry it like a toy",
        scene_word="string",
        tags={"green", "string", "metal"},
    ),
}

SUSPECTS = {
    "helper": Suspect("helper", "mother", "Mom", "helper", "was only cleaning up"),
    "wind": Suspect("wind", "thing", "the wind", "wind", "could move light things around"),
    "pet": Suspect("pet", "cat", "the cat", "pet", "liked to bat shiny things"),
}

NAMES = ["Mina", "Levi", "Nora", "Ezra", "Ivy", "Owen", "Lila", "Theo"]
TRAITS = ["curious", "careful", "brave", "bright", "patient", "quick-thinking"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mystery_id, m in MYSTERIES.items():
            if m.hide_zone in setting.hides:
                combos.append((place, mystery_id))
    return combos


def explain_rejection(place: str, mystery_id: str) -> str:
    m = MYSTERIES[mystery_id]
    return (
        f"(No story: {m.label} cannot reasonably vanish in {place} because "
        f"there is no good hiding spot there for a {m.hide_zone} clue to matter.)"
    )


# ---------------------------------------------------------------------------
# Storyworld logic
# ---------------------------------------------------------------------------

def is_hidden(world: World, mystery: Mystery) -> bool:
    obj = world.get(mystery.id)
    return obj.hidden_in is not None and obj.held_by is None


def suspicion_level(ent: Entity) -> float:
    return ent.memes.get("suspicion", 0.0)


def build_scene(world: World, params: StoryParams) -> None:
    mystery = MYSTERIES[params.mystery]

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Mina", "Nora", "Ivy", "Lila"} else "boy",
        label=params.name,
        meters={"attention": 1.0},
        memes={"curiosity": 1.0, "joy": 0.0, "euphoric": 0.0},
    ))
    helper = world.add(Entity(
        id="Mom",
        kind="character",
        type="mother",
        label="Mom",
        memes={"worry": 0.0, "relief": 0.0},
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="character" if mystery.culprit_role == "helper" else "thing",
        type=SUSPECTS[mystery.culprit_role].type,
        label=SUSPECTS[mystery.culprit_role].label,
        memes={"suspicion": 0.0},
    ))
    obj = world.add(Entity(
        id=mystery.id,
        kind="thing",
        type=mystery.label,
        label=mystery.label,
        phrase=mystery.phrase,
        owner=hero.id,
        caretaker=helper.id,
        hidden_in=mystery.hide_zone,
    ))

    world.facts.update(hero=hero, helper=helper, culprit=culprit, mystery=mystery, object=obj)

    world.say(f"{hero.id} was a {params.trait} little detective who loved neat clues and quiet corners.")
    world.say(f"At {world.setting.place}, {hero.id} was proud of {mystery.phrase}.")
    world.say(f"Then the {mystery.label} was gone.")

    world.para()
    world.say(f"{hero.id} looked near the {mystery.hide_zone}, then under a {mystery.hide_zone}, but the spot was empty.")
    world.say(f"On the floor nearby, there was {mystery.clue}.")
    world.say(f"That made {hero.id} think {SUSPECTS[mystery.culprit_role].label} had done it.")

    culprit.memes["suspicion"] += 1.0
    helper.memes["worry"] += 1.0

    world.para()
    world.say(f"But {SUSPECTS[mystery.culprit_role].innocence_hint}.")
    world.say(f"{hero.id} paused and looked more carefully.")
    if mystery.culprit_role == "helper":
        world.say("Mom had been helping before the show, so her hands had touched the ribbon.")
    elif mystery.culprit_role == "wind":
        world.say("The window had been open, and the breeze could reach the shelf.")
    else:
        world.say("The cat had a habit of chasing string and shiny bits across the room.")

    world.para()
    obj.hidden_in = None
    obj.held_by = hero.id
    helper.memes["worry"] = 0.0
    helper.memes["relief"] = 1.0
    hero.memes["euphoric"] = 1.0
    hero.memes["joy"] = 1.0

    world.say(
        f"At last, {hero.id} found {mystery.phrase} tucked in the {mystery.hide_zone}, "
        f"right where {mystery.culprit_reason}."
    )
    world.say(
        f"The clue had been a misunderstanding: it pointed to {SUSPECTS[mystery.culprit_role].label}, "
        f"but it was only a sign of where the {mystery.label} had slipped."
    )
    world.say(
        f"{hero.id} grinned with euphoric relief, and {helper.id} laughed too. "
        f"The little mystery was solved, and the room felt bright again."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]
    return [
        f'Write a child-friendly whodunit with a misunderstanding, using the word "euphoric".',
        f"Tell a short mystery story where {f['hero'].id} searches for {m.phrase} and a clue points to the wrong suspect.",
        f"Write a gentle detective story that begins with a missing {m.label} and ends in happy relief.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"What did {hero.id} notice was missing?",
            answer=f"{hero.id} noticed that {mystery.phrase} was missing.",
        ),
        QAItem(
            question=f"What clue caused the misunderstanding?",
            answer=f"The clue was {mystery.clue}, so {hero.id} first suspected {SUSPECTS[mystery.culprit_role].label}.",
        ),
        QAItem(
            question=f"What finally solved the mystery?",
            answer=(
                f"{hero.id} looked carefully and found the {mystery.label} tucked in the {mystery.hide_zone}. "
                f"That showed the clue was only a misunderstanding."
            ),
        ),
        QAItem(
            question=f"How did {helper.id} feel at the end?",
            answer=f"{helper.id} felt relieved and happy when the truth came out.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of evidence that helps someone solve a mystery.",
        ),
        QAItem(
            question="What does misunderstanding mean?",
            answer="A misunderstanding happens when someone thinks the wrong thing at first.",
        ),
        QAItem(
            question="What does euphoric mean?",
            answer="Euphoric means feeling very, very happy, as if the good news is glowing inside you.",
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
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
mystery(M) :- object(M).
valid(P,M) :- place(P), mystery(M), hides(P,Z), hide_zone(M,Z).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for z in sorted(s.hides):
            lines.append(asp.fact("hides", pid, z))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("object", mid))
        lines.append(asp.fact("hide_zone", mid, m.hide_zone))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit story world with a misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name", choices=NAMES)
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
    combos = valid_combos()
    if args.place or args.mystery:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.mystery is None or c[1] == args.mystery)
        ]
    if not combos:
        if args.place and args.mystery:
            raise StoryError(explain_rejection(args.place, args.mystery))
        raise StoryError("(No valid combination matches the given options.)")

    place, mystery = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    build_scene(world, params)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            if e.hidden_in:
                bits.append(f"hidden_in={e.hidden_in}")
            if e.held_by:
                bits.append(f"held_by={e.held_by}")
            print(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mystery) combos:\n")
        for place, mystery in combos:
            print(f"  {place:10} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, mystery in sorted(valid_combos()):
            p = StoryParams(
                place=place,
                mystery=mystery,
                name=random.Random(base_seed + len(samples)).choice(NAMES),
                trait=random.Random(base_seed + len(samples) + 1).choice(TRAITS),
                seed=base_seed + len(samples),
            )
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
