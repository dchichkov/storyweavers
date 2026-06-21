#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/happy_decongestant_sound_effects_conflict_mystery.py
==============================================================================

A small story world about a sniffly child, a mysterious nighttime sound, a wrong
guess, and a calm grown-up who helps solve the mystery.

The generated stories are intentionally narrow and reasoned:
a child with a stuffy nose hears a strange sound effect in the house, worries
about it, blames someone nearby, and then learns the real cause by investigating
carefully with a parent. The word "decongestant" is part of the world itself,
not a pasted-in token: it lowers the child's stuffed-up discomfort, helps them
breathe more easily, and gives the grown-up a gentle opening to slow the panic
down before the clue hunt.

Run it
------
    python storyworlds/worlds/gpt-5.4/happy_decongestant_sound_effects_conflict_mystery.py
    python storyworlds/worlds/gpt-5.4/happy_decongestant_sound_effects_conflict_mystery.py --place bedroom --source branch
    python storyworlds/worlds/gpt-5.4/happy_decongestant_sound_effects_conflict_mystery.py --source faucet
    python storyworlds/worlds/gpt-5.4/happy_decongestant_sound_effects_conflict_mystery.py --all --qa
    python storyworlds/worlds/gpt-5.4/happy_decongestant_sound_effects_conflict_mystery.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    walk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    sound: str
    effect: str
    places: set[str] = field(default_factory=set)
    clue: str = ""
    reveal: str = ""
    fix: str = ""
    truth: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_noise_stirs(world: World) -> list[str]:
    hero = world.get("hero")
    source = world.get("source")
    if source.meters["making_noise"] < THRESHOLD:
        return []
    sig = ("noise_stirs",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["curiosity"] += 1
    hero.memes["fear"] += 1
    world.get("house").meters["mystery"] += 1
    return ["__mystery__"]


def _r_blame_hurts(world: World) -> list[str]:
    hero = world.get("hero")
    sibling = world.get("sibling")
    if hero.memes["accusing"] < THRESHOLD:
        return []
    sig = ("blame_hurts",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sibling.memes["hurt"] += 1
    sibling.memes["conflict"] += 1
    hero.memes["conflict"] += 1
    return ["__conflict__"]


def _r_clear_breathing(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["decongestant"] < THRESHOLD:
        return []
    sig = ("clear_breathing",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["stuffy"] = max(0.0, hero.meters["stuffy"] - 1.0)
    hero.memes["calm"] += 1
    return ["__clear__"]


CAUSAL_RULES = [
    Rule(name="noise_stirs", tag="mystery", apply=_r_noise_stirs),
    Rule(name="blame_hurts", tag="social", apply=_r_blame_hurts),
    Rule(name="clear_breathing", tag="care", apply=_r_clear_breathing),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "bedroom": Place(
        id="bedroom",
        label="bedroom",
        phrase="the dark bedroom at the end of the hall",
        walk="padded to the bedroom window",
        tags={"bedroom"},
    ),
    "bathroom": Place(
        id="bathroom",
        label="bathroom",
        phrase="the little bathroom with the shiny sink",
        walk="tiptoed to the bathroom door",
        tags={"bathroom"},
    ),
    "kitchen": Place(
        id="kitchen",
        label="kitchen",
        phrase="the quiet kitchen with the moon on the tiles",
        walk="crept into the kitchen",
        tags={"kitchen"},
    ),
    "hallway": Place(
        id="hallway",
        label="hallway",
        phrase="the long hallway where shadows stretched on the wall",
        walk="walked into the hallway and looked up",
        tags={"hallway"},
    ),
}

SOURCES = {
    "branch": Source(
        id="branch",
        label="tree branch",
        sound="tap-tap... tap-tap",
        effect="a twig brushing the window glass in the wind",
        places={"bedroom", "hallway"},
        clue="a shadow bouncing across the curtain",
        reveal="A thin branch kept bobbing against the window.",
        fix="moved the curtain aside and latched the window snugly",
        truth="It had only been a windy branch, not anyone sneaking through the night.",
        tags={"wind", "window"},
    ),
    "faucet": Source(
        id="faucet",
        label="dripping faucet",
        sound="plink... plink",
        effect="a drop of water falling from the faucet into the metal drain",
        places={"bathroom", "kitchen"},
        clue="a tiny silver sparkle under the faucet",
        reveal="One drop of water swelled, trembled, and fell into the sink.",
        fix="turned the handle until the faucet stopped dripping",
        truth="It was only water making a sleepy sound in the sink.",
        tags={"water", "sink"},
    ),
    "spoon": Source(
        id="spoon",
        label="spoon and mug",
        sound="ting-ting",
        effect="a spoon wobbling against a mug when the old fridge hummed",
        places={"kitchen"},
        clue="a little cup shaking near the fruit bowl",
        reveal="The fridge gave a low hum, and the spoon in the mug danced again.",
        fix="lifted the spoon out of the mug and set it on a towel",
        truth="Nothing strange had been hiding there; the humming fridge had made the spoon ring.",
        tags={"kitchen", "hum"},
    ),
    "vent": Source(
        id="vent",
        label="loose vent cover",
        sound="clack-clack",
        effect="a loose vent cover shivering when warm air pushed through it",
        places={"hallway", "bedroom"},
        clue="a square shadow trembling near the floor",
        reveal="Warm air puffed out, and the vent cover rattled on its screws.",
        fix="pressed the cover still with one hand and tightened it",
        truth="The house itself had been making a tired little noise.",
        tags={"air", "house"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Ruby", "Ivy"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "careful", "bright", "sniffly", "gentle", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    source: str
    hero_name: str
    hero_gender: str
    sibling_name: str
    sibling_gender: str
    parent: str
    trait: str
    decongestant_flavor: str
    happy_thing: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="bedroom",
        source="branch",
        hero_name="Nora",
        hero_gender="girl",
        sibling_name="Ben",
        sibling_gender="boy",
        parent="mother",
        trait="curious",
        decongestant_flavor="cherry",
        happy_thing="the class picnic",
    ),
    StoryParams(
        place="bathroom",
        source="faucet",
        hero_name="Leo",
        hero_gender="boy",
        sibling_name="Mia",
        sibling_gender="girl",
        parent="father",
        trait="careful",
        decongestant_flavor="grape",
        happy_thing="Saturday pancakes",
    ),
    StoryParams(
        place="kitchen",
        source="spoon",
        hero_name="Ava",
        hero_gender="girl",
        sibling_name="Theo",
        sibling_gender="boy",
        parent="mother",
        trait="bright",
        decongestant_flavor="berry",
        happy_thing="making paper crowns tomorrow",
    ),
    StoryParams(
        place="hallway",
        source="vent",
        hero_name="Max",
        hero_gender="boy",
        sibling_name="Ruby",
        sibling_gender="girl",
        parent="father",
        trait="thoughtful",
        decongestant_flavor="orange",
        happy_thing="a visit from Grandma",
    ),
]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id in PLACES:
        for source_id, source in SOURCES.items():
            if place_id in source.places:
                combos.append((place_id, source_id))
    return sorted(combos)


def predict_noise(world: World, source_id: str) -> dict:
    sim = world.copy()
    sim.get("source").label = SOURCES[source_id].label
    sim.get("source").meters["making_noise"] += 1
    propagate(sim, narrate=False)
    return {
        "mystery": sim.get("house").meters["mystery"],
        "fear": sim.get("hero").memes["fear"],
    }


def bedtime_setup(world: World, hero: Entity, sibling: Entity, parent: Entity, happy_thing: str) -> None:
    hero.memes["happy"] += 1
    sibling.memes["sleepy"] += 1
    world.say(
        f"{hero.id} went to bed feeling happy because tomorrow would bring {happy_thing}."
    )
    world.say(
        f"But a cold had stuffed up {hero.pronoun('possessive')} nose, so each breath sounded thick and snuffly under the blanket."
    )
    world.say(
        f"{sibling.id} was already curled up nearby, trying to fall asleep without a peep."
    )
    world.say(
        f"{hero.id}'s {parent.label_word} brought a spoonful of {world.facts['decongestant_flavor']} decongestant and a sip of water."
    )


def give_decongestant(world: World, hero: Entity) -> None:
    hero.meters["decongestant"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} made a small face at the taste, then swallowed. In a minute, {hero.pronoun("possessive")} breathing felt a little easier.'
    )


def first_sound(world: World, source_cfg: Source) -> None:
    source = world.get("source")
    source.meters["making_noise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just when the room seemed quiet, {source_cfg.sound} came from {world.place.phrase}."
    )
    world.say(
        f"The sound was really {source_cfg.effect}, but nobody knew that yet."
    )


def accuse(world: World, hero: Entity, sibling: Entity, source_cfg: Source) -> None:
    pred = predict_noise(world, source_cfg.id)
    world.facts["predicted_mystery"] = pred["mystery"]
    hero.memes["accusing"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"{sibling.id}," {hero.id} whispered, "are you doing that?"'
    )
    if sibling.memes["hurt"] >= THRESHOLD:
        world.say(
            f'{sibling.id} sat up and frowned. "No, I am not," {sibling.pronoun()} said. The room felt tighter at once.'
        )


def calm_and_listen(world: World, parent: Entity, hero: Entity, sibling: Entity, source_cfg: Source) -> None:
    hero.memes["trust"] += 1
    sibling.memes["trust"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came in with soft steps instead of turning on every light."
    )
    world.say(
        f'"Let us be mystery-solvers, not finger-pointers," {parent.pronoun()} said. "First we listen. Then we look."'
    )
    if hero.meters["stuffy"] < THRESHOLD:
        world.say(
            f"Because the decongestant had helped {hero.id} breathe more clearly, {hero.pronoun()} could hold still and listen for the sound again."
        )
    else:
        world.say(
            f"{hero.id} sniffed hard and tried to listen past the stuffed-up feeling in {hero.pronoun('possessive')} nose."
        )
    world.say(
        f"Again it came: {source_cfg.sound}"
    )


def investigate(world: World, parent: Entity, source_cfg: Source) -> None:
    world.say(
        f"Together they {world.place.walk}. There they noticed {source_cfg.clue}."
    )
    world.say(source_cfg.reveal)
    world.say(
        f"{parent.label_word.capitalize()} {source_cfg.fix}."
    )


def resolve(world: World, hero: Entity, sibling: Entity, parent: Entity, source_cfg: Source) -> None:
    world.get("source").meters["making_noise"] = 0.0
    world.get("house").meters["mystery"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    sibling.memes["hurt"] = 0.0
    sibling.memes["relief"] += 1
    sibling.memes["joy"] += 1
    world.say(source_cfg.truth)
    world.say(
        f'{hero.id} looked at {sibling.id}. "I am sorry I blamed you," {hero.pronoun()} said.'
    )
    world.say(
        f'{sibling.id} nodded and scooted over to make room. "It did sound mysterious," {sibling.pronoun()} answered.'
    )
    world.say(
        f"{parent.label_word.capitalize()} tucked them in again, and this time the house stayed quiet."
    )
    world.say(
        f"Soon {hero.id}'s breathing was easy, the mystery was solved, and the two children fell asleep with small, happy smiles."
    )


def tell(
    place: Place,
    source_cfg: Source,
    hero_name: str,
    hero_gender: str,
    sibling_name: str,
    sibling_gender: str,
    parent_type: str,
    trait: str,
    decongestant_flavor: str,
    happy_thing: str,
) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    sibling = world.add(Entity(id="sibling", kind="character", type=sibling_gender, label=sibling_name, role="sibling"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    house = world.add(Entity(id="house", type="house", label="the house"))
    source = world.add(Entity(id="source", type="source", label=source_cfg.label))
    hero.attrs["name"] = hero_name
    sibling.attrs["name"] = sibling_name
    hero.traits = [trait] if hasattr(hero, "traits") else []
    hero.meters["stuffy"] = 1.0

    world.facts.update(
        place=place,
        source_cfg=source_cfg,
        hero=hero,
        sibling=sibling,
        parent=parent,
        house=house,
        decongestant_flavor=decongestant_flavor,
        happy_thing=happy_thing,
    )

    bedtime_setup(world, hero, sibling, parent, happy_thing)
    give_decongestant(world, hero)

    world.para()
    first_sound(world, source_cfg)
    accuse(world, hero, sibling, source_cfg)

    world.para()
    calm_and_listen(world, parent, hero, sibling, source_cfg)
    investigate(world, parent, source_cfg)

    world.para()
    resolve(world, hero, sibling, parent, source_cfg)
    world.facts["conflict"] = hero.memes["accusing"] >= THRESHOLD
    world.facts["solved"] = True
    return world


KNOWLEDGE = {
    "decongestant": [
        (
            "What does decongestant do?",
            "A decongestant helps open a stuffed-up nose so breathing feels easier. It is medicine, so a grown-up gives it carefully.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand yet, so you look for clues and answers. A good mystery gets clearer when you stay calm and notice details.",
        )
    ],
    "wind": [
        (
            "Why can a branch tap on a window?",
            "Wind can push a branch back and forth until it bumps the glass. That can make a tapping sound in the night.",
        )
    ],
    "water": [
        (
            "Why does a dripping faucet make noise?",
            "Each drop of water falls and hits the sink, so even a tiny drip can sound loud at night. Quiet rooms make little noises stand out more.",
        )
    ],
    "hum": [
        (
            "Why can a spoon ring by a mug?",
            "If something nearby shakes the table or cup, the spoon can wobble and tap the mug. Small bumps can make a bright little sound.",
        )
    ],
    "air": [
        (
            "Why can a vent rattle?",
            "Warm or cool air can push on a loose vent cover and make it shake. Then the cover can click or clack against the wall or floor.",
        )
    ],
    "apology": [
        (
            "Why is it good to say sorry after blaming someone unfairly?",
            "Saying sorry helps mend hurt feelings and shows you want to be kind again. It is an honest way to fix a mistake.",
        )
    ],
}
KNOWLEDGE_ORDER = ["decongestant", "mystery", "wind", "water", "hum", "air", "apology"]


def display_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    sibling = world.facts["sibling"]
    parent = world.facts["parent"]
    source_cfg = world.facts["source_cfg"]
    place = world.facts["place"]
    return [
        'Write a short mystery story for a 3-to-5-year-old that includes the words "happy" and "decongestant" and uses clear sound effects.',
        f"Tell a gentle nighttime mystery where {display_name(hero)} hears {source_cfg.sound} from {place.label}, blames {display_name(sibling)}, and then learns the real cause with {hero.pronoun('possessive')} {parent.label_word}.",
        f"Write a child-facing conflict story with clues, apology, and a cozy ending where the strange sound turns out to be {source_cfg.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    sibling = world.facts["sibling"]
    parent = world.facts["parent"]
    source_cfg = world.facts["source_cfg"]
    place = world.facts["place"]
    hero_name = display_name(hero)
    sibling_name = display_name(sibling)
    parent_word = parent.label_word

    qa = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, {sibling_name}, and their {parent_word}. The story follows them through one small nighttime mystery.",
        ),
        (
            f"Why was {hero_name} awake at bedtime?",
            f"{hero_name} had a stuffy nose from a cold, so settling down was harder than usual. {parent_word.capitalize()} gave {hero.pronoun('object')} decongestant to help {hero.pronoun('object')} breathe more easily.",
        ),
        (
            f"What started the mystery?",
            f"The mystery started when {source_cfg.sound} came from {place.phrase}. The strange sound made the quiet house feel bigger and more confusing.",
        ),
        (
            f"Why did {hero_name} and {sibling_name} have a conflict?",
            f"{hero_name} wrongly blamed {sibling_name} for making the sound, and that hurt {sibling_name}'s feelings. The conflict grew because nobody knew the real cause yet.",
        ),
        (
            "How was the mystery solved?",
            f"{parent_word.capitalize()} slowed everyone down, listened for the sound again, and followed the clue to its source. Then {parent.pronoun()} found {source_cfg.label} and fixed the little problem, so the noise stopped.",
        ),
        (
            f"What did {hero_name} learn at the end?",
            f"{hero_name} learned not to blame someone before checking the facts. After the mystery was solved, {hero.pronoun()} said sorry and the room felt peaceful again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"decongestant", "mystery", "apology"} | set(world.facts["source_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.label:
            bits.append(f"label={ent.label!r}")
        if ent.attrs:
            bits.append(f"attrs={dict(ent.attrs)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place_id: str, source_id: str) -> str:
    if place_id not in PLACES:
        return "(No story: unknown place.)"
    if source_id not in SOURCES:
        return "(No story: unknown source.)"
    source = SOURCES[source_id]
    return (
        f"(No story: {source.label} is not a plausible mystery source in the {PLACES[place_id].label}. "
        f"Try one of: {', '.join(sorted(source.places))}.)"
    )


ASP_RULES = r"""
valid(P, S) :- place(P), source(S), fits(S, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        for place_id in sorted(source.places):
            lines.append(asp.fact("fits", source_id, place_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in range(5):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            _ = generate(params)
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke tests passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime mystery story world with a sniffly child, a decongestant, a wrong guess, and a solved sound."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("--sibling-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sibling-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and QA")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (place, source) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source and (args.place, args.source) not in set(valid_combos()):
        raise StoryError(explain_rejection(args.place, args.source))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, source = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    sibling_gender = args.sibling_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    sibling_name = args.sibling_name or _pick_name(rng, sibling_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    flavor = rng.choice(["cherry", "grape", "berry", "orange", "honey-lemon"])
    happy_thing = rng.choice(
        [
            "the class picnic",
            "Saturday pancakes",
            "a library trip",
            "a blanket fort after school",
            "making paper crowns tomorrow",
            "a visit from Grandma",
        ]
    )
    return StoryParams(
        place=place,
        source=source,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sibling_name=sibling_name,
        sibling_gender=sibling_gender,
        parent=parent,
        trait=trait,
        decongestant_flavor=flavor,
        happy_thing=happy_thing,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        source_cfg = SOURCES[params.source]
    except KeyError as err:
        raise StoryError(f"(Invalid params: {err})") from err

    if params.place not in source_cfg.places:
        raise StoryError(explain_rejection(params.place, params.source))

    world = tell(
        place=place,
        source_cfg=source_cfg,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        sibling_name=params.sibling_name,
        sibling_gender=params.sibling_gender,
        parent_type=params.parent,
        trait=params.trait,
        decongestant_flavor=params.decongestant_flavor,
        happy_thing=params.happy_thing,
    )

    story_text = world.render()
    hero_name = display_name(world.facts["hero"])
    sibling_name = display_name(world.facts["sibling"])
    story_text = story_text.replace("hero", hero_name).replace("sibling", sibling_name)

    return StorySample(
        params=params,
        story=story_text,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(f"{len(combos)} compatible (place, source) combos:\n")
        for place, source in combos:
            print(f"  {place:8} {source}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.source} in the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
