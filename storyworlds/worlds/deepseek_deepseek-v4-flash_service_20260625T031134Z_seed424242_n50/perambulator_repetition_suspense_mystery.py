#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/perambulator_repetition_suspense_mystery.py
============================================================================================================================

A standalone story world sketch for a mystery tale involving a perambulator, 
repetition, and suspense. A child discovers an old perambulator that appears 
in different places each morning, and the story builds toward revealing its secret.
"""

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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "auntie", "uncle": "uncle"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the old garden"
    indoor: bool = False


@dataclass
class StoryParams:
    place: str
    object_name: str
    mystery_type: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.mystery_count: int = 0
        self.found_count: int = 0

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.mystery_count = self.mystery_count
        clone.found_count = self.found_count
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_notice(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if world.found_count >= 1 and actor.memes["noticed"] < THRESHOLD:
            actor.memes["noticed"] += 1
            out.append(f"{actor.id} noticed something odd.")
    return out


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["noticed"] >= THRESHOLD and actor.memes["curious"] < THRESHOLD:
            actor.memes["curious"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} curiosity grew.")
    return out


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if world.found_count >= 2 and actor.memes["suspense"] < THRESHOLD:
            actor.memes["suspense"] += 1
            out.append(f"A shiver of suspense ran through {actor.pronoun('object')}.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="notice", tag="mystery", apply=_r_notice),
    Rule(name="curiosity", tag="mystery", apply=_r_curiosity),
    Rule(name="suspense", tag="mystery", apply=_r_suspense),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Mystery catalog
# ---------------------------------------------------------------------------
MYSTERIES = {
    "perambulator": {
        "object": "perambulator",
        "object_phrase": "an old wicker perambulator with a silent wheel",
        "sound": "a soft creak at midnight",
        "trail": "a faint wheel track on the morning dew",
        "locations": ["the garden shed", "under the oak tree", "by the stone wall", "near the old fountain"],
        "repeats": ["Again the perambulator had moved.", "Once more the perambulator stood in a different spot."],
        "resolution": "It was a family of hedgehogs nesting underneath, carrying leaves that rolled the wheel slightly each night.",
        "tags": {"perambulator", "wheel", "hedgehog"}
    },
    "lantern": {
        "object": "lantern",
        "object_phrase": "an old copper lantern with a cracked glass",
        "sound": "a faint glow at dusk",
        "trail": "a smudge of ash on the windowsill",
        "locations": ["the porch", "the attic window", "the garden table", "the top of the stairs"],
        "repeats": ["Again the lantern had changed position.", "Once more the lantern flickered in a new place."],
        "resolution": "A tiny firefly had found its way inside the glass and returned each evening, making the lantern seem alive.",
        "tags": {"lantern", "light", "firefly"}
    },
    "key": {
        "object": "key",
        "object_phrase": "a small brass key with a blue ribbon",
        "sound": "a metallic tinkle at twilight",
        "trail": "a faint scratch on the floorboards",
        "locations": ["the hallway rug", "the kitchen shelf", "the library desk", "the piano bench"],
        "repeats": ["Again the key appeared somewhere new.", "Once more the key glinted in an unexpected place."],
        "resolution": "A clever mouse had been collecting shiny things to line its nest behind the old clock.",
        "tags": {"key", "metal", "mouse"}
    }
}


# ---------------------------------------------------------------------------
# Storytelling verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved exploring every corner of {world.setting.place}.")


def first_discovery(world: World, hero: Entity, adult: Entity, mystery: dict) -> None:
    loc = random.choice(mystery["locations"])
    world.facts["first_location"] = loc
    world.facts["mystery_object"] = mystery["object"]
    world.mystery_count += 1
    world.found_count += 1
    world.say(f"One morning, {hero.id} found {mystery['object_phrase']} sitting in {loc}.")
    world.say(f"\"That wasn't there yesterday,\" {hero.id} whispered, feeling curious about the {mystery['object']}.")
    propagate(world)


def repetition(world: World, hero: Entity, adult: Entity, mystery: dict) -> None:
    loc = random.choice(mystery["locations"])
    world.say(f"The next day, the {mystery['object']} was in {loc} instead.")
    world.say(random.choice(mystery["repeats"]))
    world.mystery_count += 1
    world.found_count += 1
    propagate(world)


def second_repetition(world: World, hero: Entity, adult: Entity, mystery: dict) -> None:
    loc = random.choice(mystery["locations"])
    world.say(f"On the third morning, {hero.id} went straight to {loc}, and yes — the {mystery['object']} waited there.")
    world.say(f"\"This is strange,\" {hero.id} said. \"It keeps moving.\"")
    world.mystery_count += 1
    world.found_count += 1
    propagate(world)


def suspense_build(world: World, hero: Entity, adult: Entity, mystery: dict) -> None:
    world.say(f"That night, {hero.id} stayed awake, listening for {mystery['sound']}.")
    world.say(f"A {mystery['trail']} marked where the {mystery['object']} had been.")
    world.say(f"{hero.pronoun().capitalize()} felt a shiver of mystery creep into {hero.pronoun('possessive')} room.")
    hero.memes["suspense"] += 1
    propagate(world)


def investigation(world: World, hero: Entity, adult: Entity, mystery: dict) -> None:
    world.say(f"{hero.id} decided to solve the puzzle of the moving {mystery['object']}.")
    world.say(f"With {hero.pronoun('possessive')} {adult.label_word}, {hero.pronoun()} searched for clues.")
    propagate(world)


def reveal(world: World, hero: Entity, adult: Entity, mystery: dict) -> None:
    world.say(f"And then they discovered the secret: {mystery['resolution']}")
    world.say(f"{hero.id} laughed and hugged {hero.pronoun('possessive')} {adult.label_word}. "
              f"The mystery of the {mystery['object']} was solved, and {world.setting.place} felt safe again.")
    hero.memes["joy"] += 1
    hero.memes["solved"] += 1
    hero.memes["suspense"] = 0.0
    propagate(world)


def tell(setting: Setting, mystery_key: str, hero_name: str = "Emma",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None,
         adult_type: str = "aunt") -> World:
    world = World(setting)
    mystery = MYSTERIES[mystery_key]

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "brave"]),
    ))
    adult = world.add(Entity(
        id="Adult", kind="character", type=adult_type, label="the adult"
    ))

    world.facts["mystery"] = mystery

    introduce(world, hero)
    world.para()

    first_discovery(world, hero, adult, mystery)
    world.para()

    repetition(world, hero, adult, mystery)
    world.para()

    second_repetition(world, hero, adult, mystery)
    world.para()

    suspense_build(world, hero, adult, mystery)
    world.para()

    investigation(world, hero, adult, mystery)
    world.para()

    reveal(world, hero, adult, mystery)

    world.facts.update(hero=hero, adult=adult, mystery=mystery)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the old garden"),
    "cottage": Setting(place="the cottage by the woods"),
    "farm": Setting(place="the family farm"),
    "village": Setting(place="the little village square"),
}

GIRL_NAMES = ["Emma", "Clara", "Ivy", "Rose", "Hazel"]
BOY_NAMES = ["Leo", "Owen", "Finn", "Jasper", "Miles"]
TRAITS = ["curious", "brave", "thoughtful", "observant", "patient"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for mystery in MYSTERIES:
            combos.append((place, mystery))
    return combos


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f"Write a gentle mystery story for a child about a {mystery['object']} that keeps appearing in different places.",
        f"Tell a story with repetition and suspense where {hero.id} discovers the secret of a moving {mystery['object']}.",
        f"Create a short mystery about a {mystery['object']} in {world.setting.place} that builds curiosity and ends with a warm solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    adult = f["adult"]
    mystery = f["mystery"]
    pos = hero.pronoun("possessive")
    sub = hero.pronoun("subject")
    obj = hero.pronoun("object")

    qa = [
        QAItem(
            question=f"What did {hero.id} find in {world.setting.place} that kept moving?",
            answer=f"{hero.id} found {mystery['object_phrase']} in {world.setting.place}, and it appeared in different spots each morning."
        ),
        QAItem(
            question=f"How did {hero.id} feel when the {mystery['object']} moved again and again?",
            answer=f"{hero.id} felt curious and a little spooked by the repetition. {pos.capitalize()} curiosity grew each time {sub} saw the {mystery['object']} in a new place."
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the mystery of the {mystery['object']}?",
            answer=f"{pos.capitalize()} {adult.label_word} helped {obj} search for clues in {world.setting.place}."
        ),
        QAItem(
            question=f"What was the real secret behind the moving {mystery['object']}?",
            answer=f"The secret was that {mystery['resolution']}"
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = world.facts["mystery"]["tags"]
    qa = []
    if "perambulator" in tags:
        qa.append(QAItem(
            question="What is a perambulator?",
            answer="A perambulator is another word for a baby carriage or stroller, often made of wicker, that you push to carry a baby."
        ))
        qa.append(QAItem(
            question="Why might a perambulator move by itself?",
            answer="A perambulator might move by itself if a small animal like a hedgehog or a gust of wind nudges it, making it roll slightly."
        ))
    if "hedgehog" in tags:
        qa.append(QAItem(
            question="What is a hedgehog?",
            answer="A hedgehog is a small, spiky mammal that comes out at night to eat insects and snails. It curls into a ball when scared."
        ))
    if "lantern" in tags:
        qa.append(QAItem(
            question="What is a lantern?",
            answer="A lantern is a portable light source with a glass case around the flame or bulb, used to see in the dark."
        ))
    if "firefly" in tags:
        qa.append(QAItem(
            question="What is a firefly?",
            answer="A firefly is a small beetle that glows at night using a special chemical in its body. People also call it a lightning bug."
        ))
    if "key" in tags:
        qa.append(QAItem(
            question="Why do mice collect shiny objects?",
            answer="Mice collect shiny objects because they are curious and like to bring soft or glittering things to their nests for warmth or decoration."
        ))
    if "mouse" in tags:
        qa.append(QAItem(
            question="Where do mice usually live in a house?",
            answer="Mice live in small hidden spaces like behind walls, under floors, in attics, or behind old furniture where they can build nests."
        ))
    return qa


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_story(Place, Mystery) :- setting(Place), mystery(Mystery).
"""


def asp_facts() -> str:
    import asp as _asp
    lines = []
    for pid in SETTINGS:
        lines.append(_asp.fact("setting", pid))
    for mid in MYSTERIES:
        lines.append(_asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
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
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery story world: a child investigates a moving object with repetition and suspense.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["aunt", "uncle"])
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
    combos = [(p, m) for p in SETTINGS for m in MYSTERIES
              if (args.place is None or p == args.place)
              and (args.mystery is None or m == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        object_name=mystery,
        mystery_type=mystery,
        name=name,
        gender=gender,
        adult=adult,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        params.object_name,
        params.name,
        params.gender,
        [params.trait, "brave"],
        params.adult,
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
        lines = ["--- world model state ---"]
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
        print("\n".join(lines))
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World knowledge ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="garden", object_name="perambulator", mystery_type="perambulator",
                name="Emma", gender="girl", adult="aunt", trait="curious"),
    StoryParams(place="cottage", object_name="lantern", mystery_type="lantern",
                name="Owen", gender="boy", adult="uncle", trait="observant"),
    StoryParams(place="farm", object_name="key", mystery_type="key",
                name="Clara", gender="girl", adult="uncle", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for place, mystery in stories:
            print(f"  {place:9} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.object_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
