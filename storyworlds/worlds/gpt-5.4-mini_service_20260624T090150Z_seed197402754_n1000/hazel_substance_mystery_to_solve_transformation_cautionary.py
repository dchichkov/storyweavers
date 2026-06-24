#!/usr/bin/env python3
"""
storyworlds/worlds/hazel_substance_mystery_to_solve_transformation_cautionary.py
=================================================================================

A small adventure story world about a hazel-colored substance, a mystery to
solve, a cautious choice, and a gentle transformation.

Seed tale:
---
Hazel and her brother Bram found a strange hazel substance glittering in the
old garden shed. Wherever the substance touched something damp, it changed:
a fallen leaf curled into a paper-thin map, and a pebble turned smooth and warm.

Hazel wanted to poke it with her bare finger, but Bram told her to stop.
"What if it's a bad substance?" he said. "We should be careful."

Together they fetched a jar, gloves, and a spoon. They followed the little
trail of hazel dust to its source: a cracked clay pot where a squirrel had
stored walnut shells and pollen. The mysterious substance was only dry tree
dust, but it could still make a mess and surprise anyone who touched it.

Hazel smiled as they cleaned it up. She kept one tiny curled leaf-map in the
jar so she would remember to ask first when something strange glowed on the
floor.

World model:
---
    unknown substance found -> curiosity +1, caution warning
    touching unknown substance bare -> transformation happens, caution risk rises
    gloves + spoon + jar    -> safe investigation, mystery solved
    mystery solved          -> fear drops, pride rises, ending keeps one sample sealed

Story contract:
---
    * classic beginning / middle turn / ending
    * state drives prose
    * child-facing cautionary adventure tone
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
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
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Substance:
    id: str
    label: str
    phrase: str
    color: str
    effect: str
    touch_effect: str
    danger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    covers: set[str]
    keeps_safe_from: set[str]
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trail_found: bool = False
        self.mystery_solved: bool = False

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.trail_found = self.trail_found
        clone.mystery_solved = self.mystery_solved
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.meters.get("covers", []) for item in self.worn_items(actor))


SETTINGS = {
    "garden_shed": Setting(place="the old garden shed", indoors=True, affords={"search"}),
    "woodshed": Setting(place="the woodshed", indoors=True, affords={"search"}),
    "attic": Setting(place="the attic", indoors=True, affords={"search"}),
}

SUBSTANCES = {
    "hazel_dust": Substance(
        id="hazel_dust",
        label="hazel dust",
        phrase="a hazel-colored substance",
        color="hazel",
        effect="changed into a strange new shape",
        touch_effect="moved and changed",
        danger="could surprise someone who touched it",
        tags={"hazel", "substance", "mystery", "transformation"},
    ),
    "amber_slime": Substance(
        id="amber_slime",
        label="amber slime",
        phrase="a hazel-amber substance",
        color="hazel",
        effect="grew into a soft, curled shape",
        touch_effect="shivered and changed",
        danger="could smear on fingers and clothes",
        tags={"hazel", "substance", "mystery", "transformation"},
    ),
}

GEAR = {
    "gloves": Gear(
        id="gloves",
        label="gloves",
        phrase="a pair of little gloves",
        covers={"hands"},
        keeps_safe_from={"hazel_dust", "amber_slime"},
        tags={"caution"},
    ),
    "jar": Gear(
        id="jar",
        label="jar",
        phrase="a clear jar with a lid",
        covers=set(),
        keeps_safe_from={"hazel_dust", "amber_slime"},
        tags={"caution"},
    ),
    "spoon": Gear(
        id="spoon",
        label="spoon",
        phrase="a spoon with a long handle",
        covers={"hands"},
        keeps_safe_from={"hazel_dust", "amber_slime"},
        tags={"caution"},
    ),
}

GIRL_NAMES = ["Hazel", "Mina", "Nora", "Lily", "Ava"]
BOY_NAMES = ["Bram", "Otto", "Finn", "Leo", "Theo"]
ADULTS = ["mother", "father", "aunt", "uncle"]
TRAITS = ["curious", "bold", "careful", "brave", "quick-thinking"]


def story_setup_seed() -> list[tuple[str, str]]:
    return [("garden_shed", "hazel_dust"), ("woodshed", "amber_slime"), ("attic", "hazel_dust")]


@dataclass
class StoryParams:
    place: str
    substance: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def reasonableness_gate(place: str, substance: str) -> bool:
    return place in SETTINGS and substance in SUBSTANCES


def explain_invalid(place: str, substance: str) -> str:
    return f"(No story: this world only supports a mystery with one of {sorted(SETTINGS)} and one of {sorted(SUBSTANCES)}.)"


def _find_substance(world: World, hero: Entity, helper: Entity, substance: Substance) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.memes["unease"] = hero.memes.get("unease", 0.0) + 0.5
    world.say(
        f"{hero.id} spotted {substance.phrase} on the floor of {world.setting.place}."
    )
    world.say(
        f"It gleamed like treasure, but {substance.danger}."
    )


def _warn_caution(world: World, helper: Entity, hero: Entity, substance: Substance) -> None:
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1
    world.say(
        f'"Wait," {helper.id} said. "Unknown things can be tricky. We should not touch {substance.label} with bare hands."'
    )


def _touch_bare(world: World, hero: Entity, substance: Substance) -> None:
    hero.memes["risk"] = hero.memes.get("risk", 0.0) + 1
    hero.meters["changed"] = hero.meters.get("changed", 0.0) + 1
    world.say(
        f"Even so, {hero.id} leaned closer, and the {substance.label} brushed {hero.pronoun('possessive')} finger."
    )
    world.say(
        f"At once, {hero.pronoun('possessive').capitalize()} fingertip {substance.touch_effect}, and the mystery got bigger."
    )


def _fetch_gear(world: World, helper: Entity, hero: Entity) -> tuple[Entity, Entity, Entity]:
    gloves = world.add(Entity(id="gloves", type="thing", label="gloves", phrase=GEAR["gloves"].phrase, protective=True))
    jar = world.add(Entity(id="jar", type="thing", label="jar", phrase=GEAR["jar"].phrase, protective=True))
    spoon = world.add(Entity(id="spoon", type="thing", label="spoon", phrase=GEAR["spoon"].phrase, protective=True))
    world.say(
        f"{helper.id} fetched {gloves.label}, {jar.label}, and {spoon.label}, and {hero.id} waited this time."
    )
    return gloves, jar, spoon


def _solve_mystery(world: World, hero: Entity, helper: Entity, substance: Substance, gear: tuple[Entity, Entity, Entity]) -> None:
    world.mystery_solved = True
    world.say(
        f"Using the {gear[0].label} and the {gear[2].label}, {hero.id} and {helper.id} lifted the {substance.label} into the {gear[1].label}."
    )
    world.say(
        f"They followed the tiny trail to a cracked pot, where pollen and dry shell dust had spilled together."
    )
    world.say(
        f"The strange {substance.color} substance was not magic at all, but it still taught {hero.id} to be careful with new things."
    )


def _resolve(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(
        f"{hero.id} sealed one little sample in the jar to remember the lesson."
    )
    world.say(
        f"By the time they walked home, {hero.id} felt proud, and the mystery was safely solved."
    )


def tell(setting: Setting, substance: Substance, hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type))
    world.facts.update(hero=hero, helper=helper, substance=substance, setting=setting)

    world.say(
        f"One afternoon, {hero.id} and {helper.type} went to {setting.place} after hearing a strange rumor."
    )
    world.say(
        f"{hero.id} was a {trait} {hero.type} who loved solving little puzzles."
    )
    world.para()

    _find_substance(world, hero, helper, substance)
    _warn_caution(world, helper, hero, substance)
    _touch_bare(world, hero, substance)
    world.para()

    gear = _fetch_gear(world, helper, hero)
    _solve_mystery(world, hero, helper, substance, gear)
    _resolve(world, hero, helper)
    world.facts["solved"] = True
    return world


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world: a hazel substance mystery with caution and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--substance", choices=SUBSTANCES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=ADULTS)
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
    place = args.place or rng.choice(list(SETTINGS))
    substance = args.substance or rng.choice(list(SUBSTANCES))
    if not reasonableness_gate(place, substance):
        raise StoryError(explain_invalid(place, substance))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(ADULTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, substance=substance, name=name, gender=gender, helper=helper, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sub = f["substance"]
    return [
        f'Write a short adventure story for a small child about {hero.id} finding a hazel mystery in {f["setting"].place}.',
        f'Write a cautionary story where {hero.id} learns not to touch the {sub.label} with bare hands.',
        f'Write a gentle mystery story that ends with the hazel substance safely sealed in a jar.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, substance = f["hero"], f["helper"], f["substance"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {f['setting'].place}?",
            answer=f"{hero.id} found {substance.phrase}, which looked mysterious and shiny.",
        ),
        QAItem(
            question=f"Why did {helper.type} tell {hero.id} not to touch it right away?",
            answer=f"{helper.id} warned {hero.id} because unknown substances can be tricky, and bare fingers could make a mess or cause a surprise.",
        ),
        QAItem(
            question=f"What did {hero.id} and {helper.id} use to solve the mystery safely?",
            answer=f"They used gloves, a spoon, and a jar so they could study the {substance.label} without touching it bare-handed.",
        ),
        QAItem(
            question=f"What changed after {hero.id} touched the substance with a bare finger?",
            answer=f"{hero.id}'s fingertip changed at once, which made the mystery feel more serious and showed why caution mattered.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"The mystery was solved, one sample was sealed in a jar, and {hero.id} went home feeling proud and careful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood yet, so people have to look for clues to solve it.",
        ),
        QAItem(
            question="Why should you be careful with unknown substances?",
            answer="Unknown substances can stain, sting, or cause trouble, so it is smarter to ask an adult and use tools instead of bare hands.",
        ),
        QAItem(
            question="What does a jar do in a careful investigation?",
            answer="A jar can hold a found substance safely so people can look at it without spreading it around.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a change from one form or state into another, like when something becomes a new shape.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:8} ({e.kind:9} {e.type:7}) {' '.join(bits)}")
    lines.append(f"  mystery_solved: {world.mystery_solved}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden_shed", substance="hazel_dust", name="Hazel", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="woodshed", substance="amber_slime", name="Bram", gender="boy", helper="father", trait="brave"),
    StoryParams(place="attic", substance="hazel_dust", name="Mina", gender="girl", helper="aunt", trait="careful"),
]


ASP_RULES = r"""
place(garden_shed). place(woodshed). place(attic).
substance(hazel_dust). substance(amber_slime).

hazel(hazel_dust).
hazel(amber_slime).

supports(P,S) :- place(P), substance(S).
valid_story(P,S) :- supports(P,S).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for s in SUBSTANCES:
        lines.append(asp.fact("substance", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    py = sorted((p, s) for p in SETTINGS for s in SUBSTANCES)
    if atoms == py:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("clingo:", atoms)
    print("python:", py)
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], SUBSTANCES[params.substance], params.name, params.gender, params.helper, params.trait)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for place, substance in stories:
            print(f"  {place:12} {substance}")
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
