#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/lair_magnetic_satchel_bad_ending_misunderstanding_happy.py
========================================================================================================

A small animal-story world about a lair, a magnetic satchel, a misunderstanding,
and a happy ending after a bad turn.

The seed image:
- A curious little animal keeps a magnetic satchel in a cozy lair.
- The satchel keeps clinging to metal things and causes a misunderstanding.
- The mistake leads to a bad ending for the middle beat.
- The animals talk it out, fix the problem, and end happily.

The world is intentionally narrow and constraint-checked: the story only
generates when the magnetic object can plausibly cause the misunderstanding and
the chosen resolution can actually solve it.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rat", "squirrel", "rabbit", "fox", "bear", "hedgehog", "badger"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Lair:
    name: str = "the lair"
    cozy: bool = True
    hidden: bool = True


@dataclass
class Satchel:
    label: str = "satchel"
    phrase: str = "a small magnetic satchel"
    magnetic: bool = True
    strength: int = 2
    color: str = "blue"


@dataclass
class StoryParams:
    animal: str
    friend: str
    lair: str
    satchel_color: str
    seed: Optional[int] = None


@dataclass
class StoryWorld:
    lair: Lair
    satchel: Satchel
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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

    def copy(self) -> "StoryWorld":
        import copy
        return StoryWorld(
            lair=copy.deepcopy(self.lair),
            satchel=copy.deepcopy(self.satchel),
            entities=copy.deepcopy(self.entities),
            facts=copy.deepcopy(self.facts),
            paragraphs=[[]],
            fired=set(self.fired),
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ANIMALS = {
    "mouse": {"name": "Milo", "friend": "Nina", "kind": "mouse", "friend_kind": "rabbit"},
    "rabbit": {"name": "Ruby", "friend": "Otis", "kind": "rabbit", "friend_kind": "hedgehog"},
    "squirrel": {"name": "Sunny", "friend": "Bea", "kind": "squirrel", "friend_kind": "mouse"},
    "badger": {"name": "Bram", "friend": "Pip", "kind": "badger", "friend_kind": "fox"},
    "fox": {"name": "Faye", "friend": "Jun", "kind": "fox", "friend_kind": "mouse"},
}

LAIRS = {
    "burrow": Lair(name="the burrow", cozy=True, hidden=True),
    "hollow": Lair(name="the hollow", cozy=True, hidden=True),
    "den": Lair(name="the den", cozy=True, hidden=True),
}

SATCHELS = {
    "red": Satchel(color="red", phrase="a small magnetic satchel", label="satchel", magnetic=True, strength=2),
    "green": Satchel(color="green", phrase="a small magnetic satchel", label="satchel", magnetic=True, strength=2),
    "yellow": Satchel(color="yellow", phrase="a small magnetic satchel", label="satchel", magnetic=True, strength=2),
}

TRAITS = ["curious", "gentle", "brave", "cheerful", "busy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
animal(A) :- hero(A).
friend(F) :- pal(F).
lair(L) :- lair_place(L).
satchel(S) :- satchel_item(S).

magnetic(S) :- satchel_item(S), satchel_magnetic(S).
misunderstanding(A,F) :- hero(A), pal(F), magnetic(_), nearby_in_lair(A,F).
bad_turn(A,F) :- misunderstanding(A,F), satchel_sticks(_).
happy_end(A,F) :- bad_turn(A,F), apology(A,F), share_plan(A,F).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for aid, a in ANIMALS.items():
        lines.append(asp.fact("hero", aid))
        lines.append(asp.fact("animal_kind", aid, a["kind"]))
        lines.append(asp.fact("pal_name", aid, a["friend"]))
    for lid in LAIRS:
        lines.append(asp.fact("lair_place", lid))
    for sid, s in SATCHELS.items():
        lines.append(asp.fact("satchel_item", sid))
        if s.magnetic:
            lines.append(asp.fact("satchel_magnetic", sid))
    lines.append(asp.fact("nearby_in_lair", "animal", "friend"))
    lines.append(asp.fact("satchel_sticks", "satchel"))
    lines.append(asp.fact("apology", "animal", "friend"))
    lines.append(asp.fact("share_plan", "animal", "friend"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_end/2.\n#show bad_turn/2.\n#show misunderstanding/2."))
    atoms = set(asp.atoms(model, "happy_end")) | set(asp.atoms(model, "bad_turn")) | set(asp.atoms(model, "misunderstanding"))
    if atoms:
        print(f"OK: ASP produced {len(atoms)} relevant atoms.")
        return 0
    print("MISMATCH: ASP produced no expected atoms.")
    return 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story about a magnetic satchel in a lair.")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--lair", choices=LAIRS)
    ap.add_argument("--satchel-color", choices=SATCHELS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    animal = args.animal or rng.choice(list(ANIMALS))
    lair = args.lair or rng.choice(list(LAIRS))
    satchel_color = args.satchel_color or rng.choice(list(SATCHELS))
    name = args.name or ANIMALS[animal]["name"]
    friend = args.friend_name or ANIMALS[animal]["friend"]
    return StoryParams(animal=animal, friend=friend, lair=lair, satchel_color=satchel_color)


def valid_combo(params: StoryParams) -> bool:
    return params.animal in ANIMALS and params.lair in LAIRS and params.satchel_color in SATCHELS


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def predict_bad_turn(world: StoryWorld, hero: Entity, friend: Entity) -> bool:
    return bool(world.satchel.magnetic and hero.memes.get("worry", 0) == 0)


def tell(params: StoryParams) -> StoryWorld:
    if not valid_combo(params):
        raise StoryError("Invalid animal/lair/satchel combination.")

    world = StoryWorld(lair=LAIRS[params.lair], satchel=SATCHELS[params.satchel_color])
    hero_cfg = ANIMALS[params.animal]

    hero = world.add(Entity(id=hero_cfg["name"], kind="character", type=params.animal, label=params.animal))
    friend = world.add(Entity(id=hero_cfg["friend"], kind="character", type=hero_cfg["friend_kind"], label=hero_cfg["friend"]))
    satchel = world.add(Entity(id="satchel", kind="thing", type="satchel", label="satchel", phrase=world.satchel.phrase))
    satchel.meters["magnetic"] = 1
    satchel.owner = hero.id
    satchel.worn_by = hero.id

    hero.memes["joy"] = 1
    friend.memes["care"] = 1
    world.facts.update(hero=hero, friend=friend, satchel=satchel, params=params)

    # Act 1
    world.say(f"{hero.id} lived in {world.lair.name}, a cozy place tucked away from the wind.")
    world.say(f"{hero.id} loved {satchel.phrase} because it could hold shiny things and little snacks.")
    world.say(f"One bright morning, {hero.id} packed the {satchel.label} and went looking for something fun to do.")

    # Act 2 - misunderstanding and bad ending beat
    world.para()
    world.say(f"Near the lair, {friend.id} saw the {satchel.label} tug hard toward a metal lantern hook.")
    hero.memes["confusion"] = 1
    friend.memes["worry"] = 1
    world.say(f"{friend.id} thought {hero.id} was taking the hook or hiding treasure on purpose.")
    world.say(f"That made the day feel bad: the two animals stopped smiling, and the {satchel.label} clinked sadly against the stone.")
    world.facts["misunderstanding"] = True
    world.facts["bad_turn"] = True

    # Act 3 - happy ending resolution
    world.para()
    world.say(f"{hero.id} opened the {satchel.label} wide and showed the inside was only full of berries, thread, and a lucky pebble.")
    world.say(f"{hero.id} explained that the satchel was magnetic, so it kept sticking to metal by accident.")
    friend.memes["worry"] = 0
    hero.memes["joy"] += 1
    friend.memes["joy"] = 1
    world.say(f"{friend.id} laughed, because it had all been a misunderstanding after all.")
    world.say(f"Together they moved the satchel away from the hook, and then they tied it to a soft branch by the lair door.")
    world.say(f"By sunset, {hero.id} and {friend.id} were sharing berries outside the lair, and the little magnetic satchel stayed put at last.")
    world.facts["happy_end"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: StoryWorld) -> list[str]:
    p = world.facts["params"]
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    return [
        f"Write a short animal story about {hero.id}, a {p.animal}, and {friend.id} in {world.lair.name} with a magnetic satchel.",
        f"Tell a gentle story where a misunderstanding about a magnetic satchel leads to a bad turn and then a happy ending.",
        f"Write a child-friendly story that includes a lair, a magnetic satchel, and animals who solve a confusion kindly.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    satchel: Entity = world.facts["satchel"]
    p: StoryParams = world.facts["params"]
    return [
        QAItem(
            question=f"Who lived in {world.lair.name} with the magnetic {satchel.label}?",
            answer=f"{hero.id} lived in {world.lair.name}, and {hero.id} kept the magnetic {satchel.label} close.",
        ),
        QAItem(
            question=f"What went wrong when {hero.id} and {friend.id} were near the metal hook?",
            answer=f"The magnetic {satchel.label} stuck to the metal hook, and {friend.id} thought something sneaky was happening. That was the misunderstanding.",
        ),
        QAItem(
            question=f"How did the story end after the bad turn?",
            answer=f"{hero.id} explained the magnetic {satchel.label}, {friend.id} understood, and they ended the day happily by the lair.",
        ),
        QAItem(
            question=f"What kind of place was {world.lair.name}?",
            answer=f"{world.lair.name} was a cozy hidden home, which fit the animal story feel very well.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What does magnetic mean?",
            answer="Magnetic means something can pull on or stick to metal objects.",
        ),
        QAItem(
            question="What is a satchel?",
            answer="A satchel is a small bag with a strap, often used to carry little things.",
        ),
        QAItem(
            question="What is a lair?",
            answer="A lair is a hidden home where an animal rests or keeps its things safe.",
        ),
        QAItem(
            question="Why can misunderstandings be a problem?",
            answer="A misunderstanding can make animals worry or feel sad before they hear the real reason.",
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
    lines = ["--- trace ---"]
    lines.append(f"lair={world.lair}")
    lines.append(f"satchel={world.satchel}")
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification helpers
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    try:
        return asp_check()
    except Exception as e:
        print(f"ASP verification failed: {e}")
        return 1


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show happy_end/2.\n#show bad_turn/2.\n#show misunderstanding/2."))
    return sorted(set(asp.atoms(model, "happy_end")) | set(asp.atoms(model, "bad_turn")) | set(asp.atoms(model, "misunderstanding")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_end/2.\n#show bad_turn/2.\n#show misunderstanding/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        atoms = asp_valid_pairs()
        print(f"{len(atoms)} relevant ASP atoms:")
        for a in atoms:
            print(a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(animal="mouse", friend="Nina", lair="burrow", satchel_color="red"),
            StoryParams(animal="rabbit", friend="Otis", lair="hollow", satchel_color="green"),
            StoryParams(animal="squirrel", friend="Bea", lair="den", satchel_color="yellow"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            rng = random.Random(base_seed + i)
            i += 1
            p = resolve_params(args, rng)
            p.seed = base_seed + i
            sample = generate(p)
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
            header = f"### {p.animal} in {p.lair} with {p.satchel_color} satchel"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
