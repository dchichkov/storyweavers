#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | plant | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "sister", "woman"}
        male = {"boy", "father", "grandfather", "brother", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def be(self) -> str:
        return "are" if self.plural else "is"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    verse: str = ""


@dataclass
class PlantSpec:
    id: str
    label: str
    phrase: str
    need: str
    symptom: str
    reward: str
    rhyme: str


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    gives: set[str]
    prep: str
    finish: str
    rhyme: str


@dataclass
class StoryParams:
    place: str
    plant: str
    remedy: str
    name: str
    gender: str
    elder: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def plants(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "plant"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_lack_shows(world: World) -> list[str]:
    out: list[str] = []
    for plant in world.plants():
        if plant.meters["nutrient"] >= THRESHOLD:
            continue
        if ("lack", plant.id) in world.fired:
            continue
        world.fired.add(("lack", plant.id))
        plant.meters["pale"] += 1
        plant.meters["droop"] += 1
        out.append("__lack__")
    return out


def _r_plain_water_not_enough(world: World) -> list[str]:
    out: list[str] = []
    for plant in world.plants():
        if plant.meters["water"] < THRESHOLD or plant.meters["nutrient"] >= THRESHOLD:
            continue
        if ("water_only", plant.id) in world.fired:
            continue
        world.fired.add(("water_only", plant.id))
        plant.memes["still_hungry"] += 1
        out.append("__still_hungry__")
    return out


def _r_recover(world: World) -> list[str]:
    out: list[str] = []
    for plant in world.plants():
        if plant.meters["water"] < THRESHOLD or plant.meters["nutrient"] < THRESHOLD:
            continue
        if ("recover", plant.id) in world.fired:
            continue
        world.fired.add(("recover", plant.id))
        plant.meters["green"] += 1
        plant.meters["height"] += 1
        plant.meters["droop"] = 0.0
        plant.meters["pale"] = 0.0
        out.append("__recover__")
    return out


RULES = [
    Rule("lack_shows", _r_lack_shows),
    Rule("water_only", _r_plain_water_not_enough),
    Rule("recover", _r_recover),
]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    return produced


SETTINGS = {
    "garden_patch": Setting(
        place="the garden patch",
        affords={"compost", "worm_tea", "banana_mash"},
        verse="By the gate, not soon, not late, grew a patch beside the plate of stones.",
    ),
    "window_box": Setting(
        place="the window box",
        affords={"worm_tea", "banana_mash"},
        verse="By the pane, in sun and rain, sat a box with roots like little toes.",
    ),
    "greenhouse_corner": Setting(
        place="the greenhouse corner",
        affords={"compost", "worm_tea", "plant_food"},
        verse="In the warm green corner, leaf and steam made a tiny room of rows.",
    ),
}

PLANTS = {
    "bean": PlantSpec(
        id="bean",
        label="bean plant",
        phrase="a little bean plant with a curling stem",
        need="nitrogen",
        symptom="pale leaves",
        reward="new green vines with tiny pods to come",
        rhyme="Bean so lean, turn green, turn green.",
    ),
    "spinach": PlantSpec(
        id="spinach",
        label="spinach clump",
        phrase="a soft spinach clump with spoon-shaped leaves",
        need="nitrogen",
        symptom="small yellow leaves",
        reward="broad green leaves fit for picking",
        rhyme="Spinach bright, grow right, grow right.",
    ),
    "tomato": PlantSpec(
        id="tomato",
        label="tomato plant",
        phrase="a tomato plant with fuzzy stems",
        need="potassium",
        symptom="tired edges on the leaves",
        reward="strong stems and blossoms for round red fruit",
        rhyme="Tomato, don’t wait so; drink and glow.",
    ),
    "marigold": PlantSpec(
        id="marigold",
        label="marigold",
        phrase="a marigold with a tidy round head",
        need="balanced",
        symptom="thin stems and a sleepy bud",
        reward="a bright gold flower bobbing in the light",
        rhyme="Marigold, be brave and bold.",
    ),
}

REMEDIES = {
    "compost": Remedy(
        id="compost",
        label="crumbly compost",
        phrase="crumbly dark compost",
        gives={"balanced", "nitrogen"},
        prep="sprinkled crumbly compost around the roots",
        finish="the roots had richer supper to sip",
        rhyme="Crumbly, tumbly, feed the ground.",
    ),
    "worm_tea": Remedy(
        id="worm_tea",
        label="worm tea",
        phrase="a little can of worm tea",
        gives={"nitrogen", "balanced"},
        prep="mixed worm tea with water and poured it softly",
        finish="the roots drank a gentle, useful meal",
        rhyme="Pour it slow and watch it grow.",
    ),
    "banana_mash": Remedy(
        id="banana_mash",
        label="banana peel mash",
        phrase="banana peel mash from the kitchen bowl",
        gives={"potassium"},
        prep="stirred banana peel mash into the top soil",
        finish="the roots found the strength that flowers like",
        rhyme="Mash and mix for stems and sticks.",
    ),
    "plant_food": Remedy(
        id="plant_food",
        label="plant food",
        phrase="a careful spoon of plant food",
        gives={"balanced", "nitrogen", "potassium"},
        prep="measured a careful spoon of plant food into the watering can",
        finish="the soil held a full, balanced meal",
        rhyme="One small spoon by the moon at noon.",
    ),
}

GIRL_NAMES = ["Molly", "Daisy", "Nell", "Polly", "Tess", "Ruby", "Maisie", "Wren"]
BOY_NAMES = ["Ollie", "Toby", "Finn", "Bram", "Ned", "Jory", "Pip", "Robin"]
TRAITS = ["patient", "busy", "hopeful", "earnest", "bouncy", "gentle"]
ELDERS = ["mother", "father", "grandmother", "grandfather"]

KNOWLEDGE = {
    "nitrogen": [
        (
            "What is nitrogen for in a plant?",
            "Nitrogen is a nutrient that helps many plants make green leaves and steady new growth."
        )
    ],
    "potassium": [
        (
            "What is potassium for in a plant?",
            "Potassium is a nutrient that helps plants stay strong and helps flowers and fruit grow well."
        )
    ],
    "balanced": [
        (
            "What does balanced plant food mean?",
            "Balanced plant food gives a plant more than one useful nutrient, so the plant does not lack an important part of its meal."
        )
    ],
    "compost": [
        (
            "What is compost?",
            "Compost is old plant matter that has broken down into rich, dark food for soil."
        )
    ],
    "worm_tea": [
        (
            "What is worm tea?",
            "Worm tea is a gentle liquid made from worm compost, and gardeners use it to feed plants."
        )
    ],
    "banana_mash": [
        (
            "Why might someone use banana peel mash in soil?",
            "Banana peels can add useful nutrients, especially potassium, to help some plants grow."
        )
    ],
    "plant_food": [
        (
            "What is plant food?",
            "Plant food is a prepared mix of nutrients that helps a plant grow when the soil does not have enough."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "nitrogen",
    "potassium",
    "balanced",
    "compost",
    "worm_tea",
    "banana_mash",
    "plant_food",
]


def remedy_works(plant: PlantSpec, remedy: Remedy, setting: Setting) -> bool:
    return remedy.id in setting.affords and plant.need in remedy.gives


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for plant_id, plant in PLANTS.items():
            for remedy_id, remedy in REMEDIES.items():
                if remedy_works(plant, remedy, setting):
                    out.append((place, plant_id, remedy_id))
    return sorted(out)


def predict_repair(world: World, remedy: Remedy) -> bool:
    sim = world.copy()
    plant = sim.get("plant")
    feed(sim, plant, remedy, narrate=False)
    return plant.meters["green"] >= THRESHOLD and plant.meters["droop"] < THRESHOLD


def feed(world: World, plant: Entity, remedy: Remedy, narrate: bool = True) -> None:
    if "nitrogen" in remedy.gives:
        plant.meters["nitrogen"] += 1
    if "potassium" in remedy.gives:
        plant.meters["potassium"] += 1
    if "balanced" in remedy.gives:
        plant.meters["balanced"] += 1
    plant.meters["nutrient"] += 1
    plant.meters["water"] += 1
    propagate(world)
    if narrate:
        world.say(f"They {remedy.prep}, and {remedy.finish}.")


def opening_line(name: str, plant: PlantSpec, setting: Setting) -> str:
    return f"{name} kept {plant.phrase} in {setting.place}. {setting.verse}"


def love_line(hero: Entity, plant: PlantSpec) -> str:
    return (
        f'{hero.id} would pat the pot and sing, "{plant.rhyme}" '
        f'It was a little rhyme with a little ring.'
    )


def show_problem(world: World, hero: Entity, plant: Entity, plant_spec: PlantSpec) -> None:
    plant.meters["nutrient"] = 0.0
    plant.meters["water"] = 1.0
    propagate(world)
    hero.memes["worry"] += 1
    world.say(
        f"But one morning the leaves did not dance. They showed {plant_spec.symptom}, "
        f"and the stem gave a droopy bow. {hero.id} whispered, "
        f'"Oh dear, my {plant_spec.label} looks low."'
    )


def wrong_guess(world: World, hero: Entity, elder: Entity, plant_spec: PlantSpec) -> None:
    hero.memes["frustration"] += 1
    world.say(
        f'{hero.id} fetched plain water and said, "Drink, drink, do not delay!" '
        f"But {elder.label} knelt beside the pot and did not nod right away."
    )
    world.say(
        f'{elder.label.capitalize()} said, "A sip is nice, but this looks like a lack of nutrient, '
        f'not a lack of care. Water alone may leave the poor thing there."'
    )


def conflict(world: World, hero: Entity, elder: Entity) -> None:
    hero.memes["cross"] += 1
    world.say(
        f'{hero.id} frowned a tiny frown. "I watered it. I tried!" '
        f'{elder.label.capitalize()} touched {hero.pronoun("possessive")} shoulder and replied, '
        f'"You tried with love. Now let us try with sense."'
    )


def choose_remedy(world: World, hero: Entity, elder: Entity, remedy: Remedy, plant_spec: PlantSpec) -> None:
    hero.memes["hope"] += 1
    world.say(
        f'Together they looked for what the soil was missing. "{remedy.label} will help," '
        f'said {elder.label}. "Your {plant_spec.label} is hungry, not lazy."'
    )
    world.say(f'{hero.id} took a breath and answered, "Then let us feed it kindly, softly, and wisely."')


def resolution(world: World, hero: Entity, elder: Entity, plant: Entity, plant_spec: PlantSpec, remedy: Remedy) -> None:
    feed(world, plant, remedy, narrate=True)
    hero.memes["worry"] = 0.0
    hero.memes["cross"] = 0.0
    hero.memes["joy"] += 1
    elder.memes["pride"] += 1
    world.say(
        f"By the next bright check of day, the leaves looked greener. The stem stood straighter. "
        f"Soon there would be {plant_spec.reward}."
    )
    world.say(
        f'{hero.id} clapped and sang, "{remedy.rhyme}" Then {hero.pronoun()} added, '
        f'"Now I know: when roots lack nutrient, they need the right supper, not just a splash."'
    )
    world.say(
        f"In {world.setting.place}, the little plant no longer looked low. It lifted itself as if to say hello."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    plant_spec = PLANTS[params.plant]
    remedy = REMEDIES[params.remedy]

    if not remedy_works(plant_spec, remedy, setting):
        raise StoryError(
            f"{remedy.label.capitalize()} is not a reasonable fix for {plant_spec.label} in {setting.place}."
        )

    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        traits=["little", params.trait],
    ))
    elder_label = {
        "mother": "the mother",
        "father": "the father",
        "grandmother": "the grandmother",
        "grandfather": "the grandfather",
    }[params.elder]
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=params.elder,
        label=elder_label,
    ))
    plant = world.add(Entity(
        id="plant",
        kind="plant",
        type=params.plant,
        label=plant_spec.label,
        phrase=plant_spec.phrase,
        owner=hero.id,
        location=setting.place,
    ))

    world.say(opening_line(params.name, plant_spec, setting))
    world.say(love_line(hero, plant_spec))

    world.para()
    show_problem(world, hero, plant, plant_spec)
    wrong_guess(world, hero, elder, plant_spec)
    conflict(world, hero, elder)

    world.para()
    if not predict_repair(world, remedy):
        raise StoryError(f"{remedy.label.capitalize()} would not truly solve the plant's nutrient trouble here.")
    choose_remedy(world, hero, elder, remedy, plant_spec)
    resolution(world, hero, elder, plant, plant_spec, remedy)

    world.facts.update(
        hero=hero,
        elder=elder,
        plant=plant,
        plant_spec=plant_spec,
        remedy=remedy,
        setting=setting,
        conflict=True,
        solved=True,
        need=plant_spec.need,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    plant = f["plant_spec"]
    remedy = f["remedy"]
    setting = f["setting"]
    elder = f["elder"]
    return [
        f'Write a short nursery-rhyme-style story for ages 3 to 5 about a child who notices a plant has a lack of nutrient.',
        f"Tell a gentle story in {setting.place} where {hero.id} worries about a {plant.label}, has a small conflict with {elder.label}, and solves the problem with {remedy.label}.",
        f'Write a simple rhyming story that includes the words "lack" and "nutrient" and ends with a hungry plant looking healthy again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    plant = f["plant_spec"]
    remedy = f["remedy"]
    setting = f["setting"]
    pos = hero.pronoun("possessive")
    obj = hero.pronoun("object")
    qa = [
        QAItem(
            question=f"Who cared for the {plant.label} in {setting.place}?",
            answer=f"{hero.id} cared for the {plant.label} in {setting.place} and liked to sing to it."
        ),
        QAItem(
            question=f"What problem did {hero.id} notice with the {plant.label}?",
            answer=f"{hero.id} noticed that the {plant.label} looked weak, with {plant.symptom}, because the soil had a lack of nutrient."
        ),
        QAItem(
            question=f"Why did {elder.label} say plain water was not enough?",
            answer=f"{elder.label.capitalize()} said plain water was not enough because the plant was hungry for the right nutrient, not merely thirsty for a drink."
        ),
        QAItem(
            question=f"What caused the conflict between {hero.id} and {elder.label}?",
            answer=f"The conflict began when {hero.id} thought watering alone should fix the plant, but {elder.label} explained that the real problem was a lack of nutrient in the soil."
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem for {pos} {plant.label}?",
            answer=f"{hero.id} listened, used {remedy.label}, and fed the soil the nutrient the plant needed. That problem solving helped the leaves grow greener and the stem stand tall again."
        ),
        QAItem(
            question=f"How did the ending show that the {plant.label} was better?",
            answer=f"In the ending, the leaves were greener and the plant stood straighter, which showed that the hungry roots had finally been helped."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    need = world.facts["need"]
    remedy = world.facts["remedy"].id
    tags = [need]
    if need == "nitrogen":
        pass
    elif need == "potassium":
        pass
    else:
        tags.append("balanced")
    tags.append(remedy)
    out: list[QAItem] = []
    seen = set()
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag not in seen:
            seen.add(tag)
            for q, a in KNOWLEDGE[tag]:
                out.append(QAItem(question=q, answer=a))
    return out


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden_patch", plant="bean", remedy="worm_tea", name="Molly", gender="girl", elder="grandmother", trait="hopeful"),
    StoryParams(place="window_box", plant="tomato", remedy="banana_mash", name="Ollie", gender="boy", elder="mother", trait="earnest"),
    StoryParams(place="greenhouse_corner", plant="marigold", remedy="plant_food", name="Daisy", gender="girl", elder="grandfather", trait="gentle"),
    StoryParams(place="garden_patch", plant="spinach", remedy="compost", name="Finn", gender="boy", elder="father", trait="patient"),
]

ASP_RULES = r"""
needs(Plant,N) :- plant(Plant), need(Plant,N).
works(Plant,Remedy) :- needs(Plant,N), gives(Remedy,N).
available(Place,Remedy) :- affords(Place,Remedy).
valid(Place,Plant,Remedy) :- available(Place,Remedy), works(Plant,Remedy).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for remedy in sorted(setting.affords):
            lines.append(asp.fact("affords", place, remedy))
    for plant_id, plant in PLANTS.items():
        lines.append(asp.fact("plant", plant_id))
        lines.append(asp.fact("need", plant_id, plant.need))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        for g in sorted(remedy.gives):
            lines.append(asp.fact("gives", remedy_id, g))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES.replace('#show valid/3.', '')}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    status = 0
    if py != cl:
        print("MISMATCH between Python and ASP valid combos.")
        if py - cl:
            print("only in python:", sorted(py - cl))
        if cl - py:
            print("only in asp:", sorted(cl - py))
        status = 1
    else:
        print(f"OK: Python and ASP agree on {len(py)} valid combos.")
    for i, combo in enumerate(sorted(py)[:6]):
        place, plant, remedy = combo
        gender = "girl" if i % 2 == 0 else "boy"
        name = GIRL_NAMES[0] if gender == "girl" else BOY_NAMES[0]
        elder = ELDERS[i % len(ELDERS)]
        params = StoryParams(
            place=place,
            plant=plant,
            remedy=remedy,
            name=name,
            gender=gender,
            elder=elder,
            trait=TRAITS[0],
            seed=i,
        )
        sample = generate(params)
        if not sample.story.strip():
            print("Generated empty story during verify.")
            status = 1
            break
    if status == 0:
        print("OK: verification stories generated successfully.")
    return status


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme-style storyworld about a hungry plant, a small conflict, and problem solving."
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--plant", choices=sorted(PLANTS))
    ap.add_argument("--remedy", choices=sorted(REMEDIES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDERS)
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


def explain_rejection(place: Optional[str], plant: Optional[str], remedy: Optional[str]) -> str:
    if place and plant and remedy:
        setting = SETTINGS[place]
        p = PLANTS[plant]
        r = REMEDIES[remedy]
        if remedy not in setting.affords:
            return (
                f"{r.label.capitalize()} is not available in {setting.place}. "
                f"Choose a remedy that fits that place."
            )
        return (
            f"{r.label.capitalize()} does not match what the {p.label} lacks. "
            f"This story needs a true nutrient fix, not a pretend one."
        )
    return "No valid story matches the given options."


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.plant and args.remedy:
        if not remedy_works(PLANTS[args.plant], REMEDIES[args.remedy], SETTINGS[args.place]):
            raise StoryError(explain_rejection(args.place, args.plant, args.remedy))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.plant is None or c[1] == args.plant)
        and (args.remedy is None or c[2] == args.remedy)
    ]
    if not combos:
        raise StoryError(explain_rejection(args.place, args.plant, args.remedy))

    place, plant, remedy = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        plant=plant,
        remedy=remedy,
        name=name,
        gender=gender,
        elder=elder,
        trait=trait,
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for place, plant, remedy in asp_valid_combos():
            print(f"{place:18} {plant:10} {remedy}")
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
            header = f"### {p.name}: {p.plant} in {p.place} with {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
