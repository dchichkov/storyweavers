#!/usr/bin/env python3
"""
storyworlds/worlds/harrow_vocabulary_perimeter_misunderstanding_cautionary_mystery.py
======================================================================================

A small mystery-style storyworld about a child, a garden perimeter, a harrow,
and a misunderstanding that turns caution into understanding.

The core premise:
- A child notices strange marks and a scary-looking tool near a perimeter.
- They misread the scene and jump to the wrong conclusion.
- A cautious adult explains the real meaning.
- The child learns a new vocabulary word and the mystery is solved.

The world is intentionally compact, child-facing, and state-driven:
physical state tracks locations, objects, and signs; emotional state tracks
curiosity, worry, caution, and relief. The story text is assembled from the
world's live state, not from a frozen template.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    inner: str
    perimeter: str


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    scary: bool
    location: str
    reveals: str
    keyword: str


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "garden": Setting(place="the garden", inner="the seedbeds", perimeter="the fence"),
    "schoolyard": Setting(place="the schoolyard", inner="the little beds", perimeter="the painted line"),
    "orchard": Setting(place="the orchard", inner="the sapling rows", perimeter="the stone path"),
}

CLUES = {
    "harrow": Clue(
        id="harrow",
        label="harrow",
        phrase="a metal harrow with long teeth",
        scary=True,
        location="by the perimeter",
        reveals="it was used to smooth the dirt",
        keyword="harrow",
    ),
    "vocabulary": Clue(
        id="vocabulary",
        label="vocabulary cards",
        phrase="a stack of vocabulary cards",
        scary=False,
        location="near the bench",
        reveals="the word on top was perimeter",
        keyword="vocabulary",
    ),
    "perimeter": Clue(
        id="perimeter",
        label="perimeter sign",
        phrase="a bright sign that said perimeter",
        scary=False,
        location="at the edge",
        reveals="it marked the safe line around the garden",
        keyword="perimeter",
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Ava", "Lily", "Zoe"]
BOY_NAMES = ["Finn", "Leo", "Eli", "Theo", "Max"]
TRAITS = ["curious", "careful", "brave", "quiet", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, clue) for place in SETTINGS for clue in CLUES]


ASP_RULES = r"""
valid(Place, Clue) :- place(Place), clue(Clue).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary mystery about harrow, vocabulary, and perimeter.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, clue=clue, name=name, gender=gender, parent=parent, trait=trait)


def _say_intro(world: World, hero: Entity, parent: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.id} was a little {next(t for t in hero.memes.get('traits', ['']) if t) if False else world.facts['trait']} "
        f"{hero.type} who loved noticing small things."
    )
    world.say(
        f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.type} walked toward {world.setting.place}."
    )
    world.say(
        f"{hero.id} spotted {clue.phrase} {clue.location} and stopped to stare."
    )


def tell(setting: Setting, clue: Clue, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    world.facts["trait"] = trait

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"curiosity": 1.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    clue_ent = world.add(Entity(id=clue.id, type="thing", label=clue.label, phrase=clue.phrase, location=clue.location))

    world.say(f"{hero.id} was a {trait} {hero.type} who liked new words and little mysteries.")
    world.say(f"At {setting.place}, {hero.id} noticed {clue_ent.phrase} {clue_ent.location}.")
    world.say(
        f"It looked odd, and {hero.id} whispered the new vocabulary word, "
        f'"{clue.keyword}."'
    )

    world.para()
    world.say(
        f"{hero.id} thought the harrow-like marks meant something dangerous had happened at {setting.perimeter}."
        if clue.id == "harrow"
        else f"{hero.id} thought the sign or cards meant someone had hidden a secret at {setting.perimeter}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} did not want to cross {setting.perimeter} without asking."
    )
    world.say(
        f"That was a cautious choice, because the edge of {setting.place} could hide sharp tools, soft soil, or quiet surprises."
    )

    world.para()
    if clue.id == "harrow":
        world.say(
            f"{hero.id}'s {parent.type} came closer and smiled. "
            f'"That is a harrow," {hero.pronoun("possessive")} {parent.type} said. '
            f'"It is not a monster. {clue.reveals}."'
        )
        world.say(
            f"The scratchy lines were only the harrow's tracks across the dirt, and the mystery got smaller right away."
        )
    elif clue.id == "vocabulary":
        world.say(
            f"{hero.id}'s {parent.type} pointed at the cards and said, "
            f'"Those are vocabulary cards. They are there to teach a word, not to warn about danger."'
        )
        world.say(
            f"One card had the word perimeter, and the mystery turned into a lesson."
        )
    else:
        world.say(
            f"{hero.id}'s {parent.type} read the sign and said, "
            f'"Perimeter means the edge around something. It helps everyone stay safe."'
        )
        world.say(
            f"{hero.id} nodded, because the sign was not a clue about trouble after all."
        )

    world.para()
    world.say(
        f"After that, {hero.id} walked beside {setting.perimeter} and pointed to the {clue.label} with a sure finger."
    )
    world.say(
        f"The strange thing had become a clear thing, and {hero.id} carried the new word home like a little treasure."
    )

    world.facts.update(hero=hero, parent=parent, clue=clue_ent, clue_cfg=clue, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a child that uses the word "{f["clue_cfg"].keyword}".',
        f"Tell a cautionary story about a child named {f['hero'].id} who misunderstands something near {f['setting'].perimeter'] if False else f['setting'].perimeter}.",
        f"Write a gentle mystery where a {f['hero'].type} learns what {f['clue_cfg'].label} means.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    clue_cfg: Clue = f["clue_cfg"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"What did {hero.id} see at {setting.place}?",
            answer=f"{hero.id} saw {clue_cfg.phrase} {clue_cfg.location}, and it made {hero.id} curious.",
        ),
        QAItem(
            question=f"Why did {hero.id} hesitate near {setting.perimeter}?",
            answer=f"{hero.id} was being cautious. {hero.id} thought the strange thing might be dangerous, so {hero.pronoun()} did not cross the edge right away.",
        ),
        QAItem(
            question=f"What did {hero.id}'s {parent.type} explain about the mystery?",
            answer=f"The {parent.type} explained that {clue_cfg.keyword} was a real vocabulary word, and the strange object was only {clue_cfg.reveals}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The mystery became clear, {hero.id} learned a new word, and the {clue_cfg.label} was no longer scary.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "harrow": [
        QAItem(
            question="What is a harrow?",
            answer="A harrow is a farm or garden tool with teeth or tines that helps smooth and break up soil.",
        )
    ],
    "vocabulary": [
        QAItem(
            question="What does vocabulary mean?",
            answer="Vocabulary means the words a person knows and uses.",
        )
    ],
    "perimeter": [
        QAItem(
            question="What is a perimeter?",
            answer="A perimeter is the outside edge or boundary around a space.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tag = world.facts["clue_cfg"].keyword
    return list(WORLD_KNOWLEDGE.get(tag, []))


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.kind == "character":
            bits.append("character")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", clue="harrow", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="schoolyard", clue="vocabulary", name="Finn", gender="boy", parent="father", trait="thoughtful"),
    StoryParams(place="orchard", clue="perimeter", name="Lily", gender="girl", parent="mother", trait="careful"),
]


def explain_rejection() -> str:
    return "(No story: that combination does not fit this mystery world.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CLUES[params.clue],
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, clue) combos:\n")
        for place, clue in combos:
            print(f"  {place:10} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
