#!/usr/bin/env python3
"""
self_inner_monologue_mystery.py
===============================

A small mystery story world with inner monologue:
a child notices a puzzling event, thinks through clues privately, and
finds a reasonable answer.

The domain is intentionally tiny and classical:
- one protagonist
- one missing or misplaced object
- a few clue-bearing locations and helpers
- a detective turn driven by self-talk

The story is written from simulated world state rather than as a frozen
template. Inner monologue appears as short, child-friendly thoughts that
reflect the protagonist's guesses, doubts, and reasoning.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden_in: str = ""
    found_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    clue_spots: list[str]
    ambient: str


@dataclass
class Mystery:
    id: str
    item_label: str
    item_phrase: str
    hiding_spot: str
    clue: str
    false_lead: str
    reveal_spot: str
    ending_image: str


@dataclass
class StoryParams:
    mystery: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


MYSTERIES = {
    "missing_note": Mystery(
        id="missing_note",
        item_label="note",
        item_phrase="a little blue note",
        hiding_spot="under the lamp",
        clue="a blue corner peeking from the lamp",
        false_lead="the basket",
        reveal_spot="under the lamp",
        ending_image="the little blue note sitting safely by the lamp",
    ),
    "missing_key": Mystery(
        id="missing_key",
        item_label="key",
        item_phrase="a small brass key",
        hiding_spot="inside the teacup",
        clue="a tiny clink from the teacup",
        false_lead="the drawer",
        reveal_spot="inside the teacup",
        ending_image="the small brass key glinting inside the teacup",
    ),
    "missing_marble": Mystery(
        id="missing_marble",
        item_label="marble",
        item_phrase="a shiny glass marble",
        hiding_spot="behind the book",
        clue="a bright round spark behind the book",
        false_lead="the rug",
        reveal_spot="behind the book",
        ending_image="the shiny glass marble tucked behind the book",
    ),
}

SETTINGS = {
    "bedroom": Setting(place="the bedroom", clue_spots=["under the lamp", "behind the book", "under the bed"], ambient="quiet"),
    "kitchen": Setting(place="the kitchen", clue_spots=["inside the teacup", "near the sink", "under the chair"], ambient="still"),
    "library": Setting(place="the little library", clue_spots=["behind the book", "under the table", "by the shelf"], ambient="soft"),
}

TRAITS = ["curious", "careful", "quiet", "brave", "thoughtful"]
NAMES_BOY = ["Milo", "Noah", "Eli", "Finn", "Theo"]
NAMES_GIRL = ["Mia", "Nora", "Zoe", "Lily", "Ava"]


def inner_thought(world: World, hero: Entity, text: str) -> None:
    hero.memes["thinking"] = hero.memes.get("thinking", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} thought, \"{text}\"")


def setup_story(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["interest"] = 1.0
    world.say(
        f"{hero.id} was a little {hero.traits[0]} {hero.type} who liked quiet places and small puzzles."
    )
    world.say(
        f"{helper.id} lived nearby and always had a calm way of looking at things."
    )
    world.say(
        f"One afternoon, {hero.id} noticed that {mystery.item_phrase} was gone."
    )
    inner_thought(world, hero, "That is strange. I remember seeing it a moment ago.")
    world.say(
        f"The room felt {world.setting.ambient}, but the missing thing made everything seem louder in {hero.id}'s head."
    )


def inspect_false_lead(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"{hero.id} looked in the {mystery.false_lead} first."
    )
    inner_thought(world, hero, f"It could be here, but this does not feel right.")
    world.say(
        f"There was nothing useful there, only dust and a few still things."
    )
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 0.25)


def notice_clue(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["certainty"] = hero.memes.get("certainty", 0.0) + 1
    world.say(
        f"Then {hero.id} spotted {mystery.clue}."
    )
    inner_thought(world, hero, "A clue! The missing thing must be close.")
    world.say(
        f"{hero.id} followed the clue slowly, one careful step at a time."
    )


def reveal(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    item = world.get("missing_item")
    item.found_by = hero.id
    item.hidden_in = mystery.reveal_spot
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["worry"] = 0.0
    world.say(
        f"At last, {hero.id} found the {mystery.item_label} {mystery.reveal_spot}."
    )
    inner_thought(world, hero, "I knew the clue was telling the truth.")
    world.say(
        f"{helper.id} smiled and nodded as if the answer had been waiting there all along."
    )
    world.say(
        f"In the end, the mystery was solved, and there was {mystery.ending_image}."
    )


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str, trait: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=[trait, "careful"],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        traits=["calm"],
    ))
    world.add(Entity(
        id="missing_item",
        type=mystery.id,
        label=mystery.item_label,
        phrase=mystery.item_phrase,
        hidden_in=mystery.hiding_spot,
    ))

    setup_story(world, hero, helper, mystery)
    world.para()
    inspect_false_lead(world, hero, mystery)
    notice_clue(world, hero, mystery)
    world.para()
    reveal(world, hero, helper, mystery)

    world.facts.update(
        hero=hero,
        helper=helper,
        mystery=mystery,
        setting=setting,
    )
    return world


def valid_story_choices() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


@dataclass
class StoryParams2:
    mystery: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly mystery world with inner monologue.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "neighbor", "teacher"])
    ap.add_argument("--trait", choices=TRAITS)
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
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(["mother", "father", "neighbor", "teacher"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(mystery=mystery, name=name, gender=gender, helper=helper, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f"Write a short mystery story for a small child about {hero.id} and a missing {mystery.item_label}.",
        f"Tell a story where {hero.id} thinks quietly, looks for clues, and finds the answer.",
        f"Write a gentle mystery with inner monologue and a happy ending in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{hero.id} could not find {mystery.item_phrase}, so that was the missing thing.",
        ),
        QAItem(
            question=f"What did {hero.id} think after noticing the clue?",
            answer="The thought was that the missing thing must be close, because the clue was pointing the way.",
        ),
        QAItem(
            question=f"Who smiled when the mystery was solved?",
            answer=f"{helper.id} smiled when {hero.id} found the answer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a small piece of information that helps someone figure something out.",
        ),
        QAItem(
            question="What does it mean to think to yourself?",
            answer="Thinking to yourself means you talk inside your own head without saying the words out loud.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H).
missing(I) :- thing(I).
clue_at(M) :- clue(M).
solved(H,I) :- hero(H), missing(I), clue_at(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show solved/2."))
    atoms = set(asp.atoms(model, "solved"))
    if atoms:
        print("OK: ASP program runs.")
        return 0
    print("MISMATCH or empty ASP output.")
    return 1


def generate(params: StoryParams) -> StorySample:
    mystery = MYSTERIES[params.mystery]
    setting = SETTINGS["library" if params.mystery == "missing_key" else "bedroom" if params.mystery != "missing_key" else "kitchen"]
    if params.mystery == "missing_key":
        setting = SETTINGS["kitchen"]
    world = tell(
        setting=setting,
        mystery=mystery,
        hero_name=params.name,
        hero_type=params.gender,
        trait=params.trait,
        helper_type=params.helper,
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


CURATED = [
    StoryParams(mystery="missing_note", name="Mia", gender="girl", helper="mother", trait="curious"),
    StoryParams(mystery="missing_key", name="Noah", gender="boy", helper="father", trait="careful"),
    StoryParams(mystery="missing_marble", name="Lily", gender="girl", helper="neighbor", trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show solved/2."))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
