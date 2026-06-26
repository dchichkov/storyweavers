#!/usr/bin/env python3
"""
storyworlds/worlds/cage_convenience_magic_teamwork_animal_story.py
===================================================================

A small animal-story world about a worried pet, a cage, and a magical,
teamwork-based convenience fix.

Premise:
- A small animal is uneasy in a cage or pen.
- A caretaker notices the trouble.
- The caretakers use a little magic plus teamwork to make the cage feel
  convenient and safe.
- The animal settles in, and the ending proves the change.

This is intentionally compact and deterministic in structure, with a handful of
constraint-checked variations.
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
    species: str = ""
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    cozy: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Animal:
    species: str
    noun: str
    sound: str
    size: str
    place_pref: str
    cage_need: str
    convenience_need: str


@dataclass
class MagicTool:
    id: str
    label: str
    effect: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    animal: str
    magic: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "barn": Setting(place="the barn", cozy=True, affords={"cage", "magic", "teamwork"}),
    "room": Setting(place="the warm room", cozy=True, affords={"cage", "magic", "teamwork"}),
    "yard": Setting(place="the yard", cozy=False, affords={"cage", "magic", "teamwork"}),
    "clinic": Setting(place="the animal clinic", cozy=True, affords={"cage", "magic", "teamwork"}),
}

ANIMALS = {
    "kitten": Animal(
        species="kitten",
        noun="kitten",
        sound="mew",
        size="small",
        place_pref="soft blanket",
        cage_need="small cage",
        convenience_need="easy water bowl",
    ),
    "puppy": Animal(
        species="puppy",
        noun="puppy",
        sound="woof",
        size="small",
        place_pref="low bed",
        cage_need="small cage",
        convenience_need="easy food dish",
    ),
    "bunny": Animal(
        species="bunny",
        noun="bunny",
        sound="thump",
        size="small",
        place_pref="hay nest",
        cage_need="pet pen",
        convenience_need="easy hay rack",
    ),
    "duckling": Animal(
        species="duckling",
        noun="duckling",
        sound="peep",
        size="tiny",
        place_pref="warm towel",
        cage_need="little pen",
        convenience_need="shallow water tray",
    ),
}

MAGIC = {
    "blanket_spell": MagicTool(
        id="blanket_spell",
        label="a blanket spell",
        effect="made the cage feel soft and cozy",
        prep="spoke a quiet spell and tucked in a warm blanket",
        tail="the blanket spell made the cage feel kind and soft",
        helps={"soft", "warm", "cozy"},
    ),
    "light_spell": MagicTool(
        id="light_spell",
        label="a lantern spell",
        effect="made the cage bright and easy to see",
        prep="waved a hand and lit a tiny lantern spell",
        tail="the lantern spell made everything easy to see",
        helps={"bright", "easy", "safe"},
    ),
    "water_spell": MagicTool(
        id="water_spell",
        label="a water spell",
        effect="made the water dish fill itself when needed",
        prep="tapped the dish and whispered a water spell",
        tail="the water spell kept the dish ready and full",
        helps={"water", "drink", "ready"},
    ),
    "helper_spell": MagicTool(
        id="helper_spell",
        label="a helper spell",
        effect="made the cage feel convenient for everyone",
        prep="smiled and cast a helper spell with a friend",
        tail="the helper spell made the whole job feel easy",
        helps={"help", "easy", "convenient"},
    ),
}

HERO_NAMES = ["Mina", "Theo", "Ruby", "Pip", "Nia", "Ollie", "June", "Tess"]
HELPER_NAMES = ["Mara", "Ben", "Lena", "Noah", "Iris", "Sam", "Cara", "Finn"]
TRAITS = ["gentle", "quick", "kind", "patient", "brave", "cheerful"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the place supports the needed actions,
% the animal has a cage-related need, and the chosen magic helps convenience.
needs_cage(A) :- animal(A), cage_need(A,_).
needs_magic(M) :- magic(M).
needs_teamwork(T) :- teamwork(T).

valid_story(P, A, M) :- place(P), animal(A), magic(M),
    affords(P, cage), affords(P, magic), affords(P, teamwork),
    needs_cage(A), helps(M, convenience).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.cozy:
            lines.append(asp.fact("cozy", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        lines.append(asp.fact("cage_need", aid, a.cage_need))
        lines.append(asp.fact("convenience_need", aid, a.convenience_need))
    for mid, m in MAGIC.items():
        lines.append(asp.fact("magic", mid))
        for h in sorted(m.helps):
            lines.append(asp.fact("helps", mid, h))
    lines.append(asp.fact("teamwork", "teamwork"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
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
# Story logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if not {"cage", "magic", "teamwork"}.issubset(setting.affords):
            continue
        for animal in ANIMALS:
            for magic in MAGIC:
                if "convenience" in MAGIC[magic].helps or "easy" in MAGIC[magic].helps:
                    combos.append((place, animal, magic))
    return combos


def cage_is_reasonable(animal: Animal, place: Setting) -> bool:
    return "cage" in place.affords and "magic" in place.affords and "teamwork" in place.affords and bool(animal.cage_need)


def select_magic(animal: Animal) -> MagicTool:
    if animal.species in {"kitten", "puppy"}:
        return MAGIC["blanket_spell"]
    if animal.species == "bunny":
        return MAGIC["helper_spell"]
    return MAGIC["water_spell"]


def story_setup(world: World, hero: Entity, helper: Entity, animal: Entity, magic_tool: MagicTool) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} helper who cared for a little {animal.label} in {world.setting.place}."
    )
    world.say(
        f"The {animal.label} liked soft corners, but the cage felt plain and awkward at first."
    )
    world.say(
        f"{helper.id} wanted the cage to be easier to use, because a good setup should bring convenience to the whole team."
    )
    world.say(
        f"Together, they decided to try {magic_tool.label}."
    )


def story_turn(world: World, hero: Entity, helper: Entity, animal: Entity, magic_tool: MagicTool) -> None:
    animal.memes["uneasy"] = animal.memes.get("uneasy", 0.0) + 1
    world.para()
    world.say(
        f"The {animal.label} pressed close to the bars and gave a small {animal.meters.get('sound', 1) and animal.species != 'duckling' and 'mew' or 'peep'}."
    )
    world.say(
        f"{hero.id} and {helper.id} saw that the cage needed a kinder, more convenient plan."
    )
    world.say(
        f"{hero.id} whispered, \"We can fix this together.\""
    )
    world.say(
        f"{helper.id} nodded and helped make space for the magic."
    )


def story_resolution(world: World, hero: Entity, helper: Entity, animal: Entity, magic_tool: MagicTool) -> None:
    world.para()
    animal.memes["uneasy"] = 0.0
    animal.memes["safe"] = 1.0
    animal.memes["happy"] = animal.memes.get("happy", 0.0) + 1
    world.say(f"Then {hero.id} {magic_tool.prep}, and {helper.id} held the door steady.")
    world.say(f"At once, {magic_tool.tail}.")
    world.say(
        f"The little {animal.label} stepped inside, found {animal.pronoun('possessive')} cozy spot, and settled down without fuss."
    )
    world.say(
        f"By the end, the cage was not just safe; it was convenient, gentle, and ready for the team to use again."
    )


def tell(setting: Setting, animal_cfg: Animal, magic_tool: MagicTool,
         hero_name: str = "Mina", helper_name: str = "Mara",
         trait: str = "kind") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", label=hero_name, traits=[trait, "careful"]))
    helper = world.add(Entity(id=helper_name, kind="character", label=helper_name, traits=["helpful"]))
    animal = world.add(Entity(id=animal_cfg.noun, kind="thing", label=animal_cfg.noun))

    world.facts.update(hero=hero, helper=helper, animal=animal, animal_cfg=animal_cfg, magic_tool=magic_tool)

    story_setup(world, hero, helper, animal, magic_tool)
    story_turn(world, hero, helper, animal, magic_tool)
    story_resolution(world, hero, helper, animal, magic_tool)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal_cfg: Animal = f["animal_cfg"]
    magic_tool: MagicTool = f["magic_tool"]
    return [
        f'Write a short animal story for a young child that includes a cage and the word "convenience".',
        f"Tell a gentle story where {f['hero'].id} and {f['helper'].id} use {magic_tool.label} to help a {animal_cfg.noun} feel safe in a cage.",
        f"Write a simple story about teamwork and magic making a cage easier for a little {animal_cfg.noun}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    animal_cfg: Animal = f["animal_cfg"]
    magic_tool: MagicTool = f["magic_tool"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    animal: Entity = f["animal"]
    return [
        QAItem(
            question=f"What did {hero.id} and {helper.id} want to make easier for the {animal_cfg.noun}?",
            answer=f"They wanted to make the cage easier and kinder to use, so the {animal_cfg.noun} could settle in safely.",
        ),
        QAItem(
            question=f"What magic did they use to help the {animal_cfg.noun}?",
            answer=f"They used {magic_tool.label}, which helped with convenience and made the cage feel better.",
        ),
        QAItem(
            question=f"How did the {animal_cfg.noun} feel at the end of the story?",
            answer=f"The {animal_cfg.noun} felt safe and happy, and it settled down in the cozy cage.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cage used for?",
            answer="A cage is a small enclosed space used to keep an animal safe, contained, or resting for a while.",
        ),
        QAItem(
            question="What does convenience mean?",
            answer="Convenience means something is easy to use or makes a job simpler.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and work together toward the same goal.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is a special kind of power that can make surprising things happen.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Validation and generation
# ---------------------------------------------------------------------------
def explain_rejection(place: str, animal: Animal, magic_tool: MagicTool) -> str:
    return (
        f"(No story: {place} does not make a reasonable cage-and-convenience tale with "
        f"{animal.noun} and {magic_tool.label}.)"
    )


def valid_story_combo(place: str, animal: str, magic: str) -> bool:
    s = SETTINGS[place]
    a = ANIMALS[animal]
    m = MAGIC[magic]
    return cage_is_reasonable(a, s) and ("convenience" in m.helps or "easy" in m.helps)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.animal and args.magic:
        if not valid_story_combo(args.place, args.animal, args.magic):
            raise StoryError(explain_rejection(args.place, ANIMALS[args.animal], MAGIC[args.magic]))

    combos = [
        (p, a, m)
        for p, a, m in valid_combos()
        if (args.place is None or p == args.place)
        and (args.animal is None or a == args.animal)
        and (args.magic is None or m == args.magic)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, animal, magic = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, animal=animal, magic=magic, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ANIMALS[params.animal], MAGIC[params.magic], params.name, params.helper, params.trait)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="barn", animal="kitten", magic="blanket_spell", name="Mina", helper="Mara", trait="gentle"),
    StoryParams(place="room", animal="bunny", magic="helper_spell", name="Theo", helper="Ben", trait="kind"),
    StoryParams(place="clinic", animal="duckling", magic="water_spell", name="Ruby", helper="Lena", trait="patient"),
    StoryParams(place="yard", animal="puppy", magic="light_spell", name="Pip", helper="Noah", trait="cheerful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: cage, convenience, magic, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible story combos:\n")
        for place, animal, magic in stories:
            print(f"  {place:8} {animal:10} {magic}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.animal} + {p.magic} at {p.place}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
