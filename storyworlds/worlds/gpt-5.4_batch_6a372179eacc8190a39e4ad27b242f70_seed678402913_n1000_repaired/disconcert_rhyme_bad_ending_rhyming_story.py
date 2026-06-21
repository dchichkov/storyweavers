#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/disconcert_rhyme_bad_ending_rhyming_story.py
=======================================================================

A standalone storyworld for small, child-facing rhyming cautionary tales with a
sad ending. A child carries a treat through a quiet place, longs to make a loud
little rhyme, ignores a warning, startles an animal, and loses the treat.

The key constraint is simple and physical:
- the noisemaker must be loud enough to startle the chosen animal
- the chosen place must plausibly contain that animal
- the animal's jolt must be strong enough to ruin the carried prize

Only combinations that support a believable problem and bad ending are allowed.

Run it
------
python storyworlds/worlds/gpt-5.4/disconcert_rhyme_bad_ending_rhyming_story.py
python storyworlds/worlds/gpt-5.4/disconcert_rhyme_bad_ending_rhyming_story.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/disconcert_rhyme_bad_ending_rhyming_story.py --all --qa
python storyworlds/worlds/gpt-5.4/disconcert_rhyme_bad_ending_rhyming_story.py --json
python storyworlds/worlds/gpt-5.4/disconcert_rhyme_bad_ending_rhyming_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    hush: str
    path_word: str
    animals: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class NoiseMaker:
    id: str
    label: str
    phrase: str
    sound_word: str
    loudness: int
    action: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AnimalCfg:
    id: str
    label: str
    phrase: str
    rest_line: str
    burst_line: str
    skittishness: int
    jolt: int
    tags: set[str] = field(default_factory=set)


@dataclass
class PrizeCfg:
    id: str
    label: str
    phrase: str
    carry: str
    ruin_line: str
    stability: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.events = list(self.events)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_startle(world: World) -> list[str]:
    child = world.get("child")
    animal = world.get("animal")
    noise = world.facts["noise"]
    animal_cfg = world.facts["animal_cfg"]
    if child.meters["noise_done"] < THRESHOLD:
        return []
    if noise.loudness < animal_cfg.skittishness:
        return []
    sig = ("startle", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.meters["startled"] += 1
    child.memes["fear"] += 1
    world.events.append("animal_startled")
    return ["__startled__"]


def _r_bolt(world: World) -> list[str]:
    animal = world.get("animal")
    prize = world.get("prize")
    animal_cfg = world.facts["animal_cfg"]
    if animal.meters["startled"] < THRESHOLD:
        return []
    sig = ("bolt", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.meters["bolting"] += 1
    prize.meters["tipped"] += float(animal_cfg.jolt)
    world.events.append("animal_bolted")
    return ["__bolted__"]


def _r_ruin(world: World) -> list[str]:
    prize = world.get("prize")
    prize_cfg = world.facts["prize_cfg"]
    if prize.meters["tipped"] < prize_cfg.stability:
        return []
    sig = ("ruin", prize.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    prize.meters["ruined"] += 1
    world.get("child").memes["regret"] += 1
    world.events.append("prize_ruined")
    return ["__ruined__"]


CAUSAL_RULES = [
    Rule(name="startle", tag="physical", apply=_r_startle),
    Rule(name="bolt", tag="physical", apply=_r_bolt),
    Rule(name="ruin", tag="physical", apply=_r_ruin),
]


def propagate(world: World, narrate: bool = False) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


def place_has_animal(place: Place, animal: AnimalCfg) -> bool:
    return animal.id in place.animals


def startles(noise: NoiseMaker, animal: AnimalCfg) -> bool:
    return noise.loudness >= animal.skittishness


def ruins_prize(animal: AnimalCfg, prize: PrizeCfg) -> bool:
    return animal.jolt >= prize.stability


def valid_story(place: Place, noise: NoiseMaker, animal: AnimalCfg, prize: PrizeCfg) -> bool:
    return place_has_animal(place, animal) and startles(noise, animal) and ruins_prize(animal, prize)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for noise_id, noise in NOISES.items():
            for animal_id, animal in ANIMALS.items():
                for prize_id, prize in PRIZES.items():
                    if valid_story(place, noise, animal, prize):
                        combos.append((place_id, noise_id, animal_id, prize_id))
    return combos


def predict_mishap(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["noise_done"] += 1
    propagate(sim, narrate=False)
    return {
        "startled": sim.get("animal").meters["startled"] >= THRESHOLD,
        "ruined": sim.get("prize").meters["ruined"] >= THRESHOLD,
    }


def opening_scene(world: World, child: Entity, parent: Entity, place: Place, prize: PrizeCfg) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} walked with {child.pronoun('possessive')} {parent.label_word} by {place.label} one dim, drifting day. "
        f"{place.opening}"
    )
    world.say(
        f"In {child.pronoun('possessive')} hands was {prize.phrase}; {prize.carry}, and {child.pronoun()} held it proud and gay."
    )


def quiet_set(world: World, place: Place, animal: AnimalCfg) -> None:
    world.say(
        f"{place.hush} Nearby, {animal.rest_line}, tucked in soft and gray."
    )


def temptation(world: World, child: Entity, noise: NoiseMaker) -> None:
    child.memes["mischief"] += 1
    world.say(
        f"Then {child.id} found {noise.phrase} and grinned, "
        f'"I know a bouncing rhyme to {noise.action} away!"'
    )


def warn(world: World, child: Entity, parent: Entity, noise: NoiseMaker, animal: AnimalCfg, prize: PrizeCfg) -> None:
    pred = predict_mishap(world)
    world.facts["predicted_startled"] = pred["startled"]
    world.facts["predicted_ruined"] = pred["ruined"]
    child.memes["caution_heard"] += 1
    world.say(
        f'{parent.label_word.capitalize()} spoke low: "Not here, my dear. '
        f'{animal.label.capitalize()} startle fast at {noise.sound_word} play. '
        f'If they leap, your {prize.label} may fly, and then our treat is lost today."'
    )


def defy(world: World, child: Entity, noise: NoiseMaker) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But the rhyme felt bright inside {child.pronoun("object")}, and caution blew like thistledown away. "
        f"{child.id} lifted {noise.phrase} up high and chose to {noise.action} anyway."
    )


def perform_noise(world: World, child: Entity, noise: NoiseMaker) -> None:
    child.meters["noise_done"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{noise.sound_word.capitalize()} went the {noise.label} -- "clatter, chatter, patter-spray!" -- '
        f'and the sound came back in scraps that did not feel like merry play.'
    )


def burst(world: World, animal: AnimalCfg) -> None:
    world.say(
        f"{animal.burst_line} The sudden flap and scrabble made a disconcert display."
    )


def loss(world: World, child: Entity, prize: PrizeCfg) -> None:
    child.memes["sadness"] += 1
    world.say(
        f"{prize.ruin_line} Sweet hopes that rode so high a moment back were spoiled without delay."
    )


def ending(world: World, child: Entity, parent: Entity, place: Place, prize: PrizeCfg) -> None:
    child.memes["lesson"] += 1
    world.say(
        f'{parent.label_word.capitalize()} took {child.pronoun("possessive")} hand and said, '
        f'"Some songs must wait for safer ground and brighter, kinder play."'
    )
    world.say(
        f"So home they went by {place.path_word}, slow and small at close of day; "
        f"{child.id} carried only the empty cloth where {prize.label} used to sway."
    )


def tell(
    *,
    place: Place,
    noise: NoiseMaker,
    animal_cfg: AnimalCfg,
    prize_cfg: PrizeCfg,
    child_name: str,
    child_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        label=child_name,
        attrs={"trait": trait},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    animal = world.add(Entity(
        id="animal",
        type="animal",
        label=animal_cfg.label,
        phrase=animal_cfg.phrase,
        tags=set(animal_cfg.tags),
    ))
    prize = world.add(Entity(
        id="prize",
        type="prize",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        tags=set(prize_cfg.tags),
    ))

    world.facts.update(
        place=place,
        noise=noise,
        animal_cfg=animal_cfg,
        prize_cfg=prize_cfg,
        child=child,
        parent=parent,
        animal=animal,
        prize=prize,
        trait=trait,
    )

    opening_scene(world, child, parent, place, prize_cfg)
    quiet_set(world, place, animal_cfg)

    world.para()
    temptation(world, child, noise)
    warn(world, child, parent, noise, animal_cfg, prize_cfg)
    defy(world, child, noise)

    world.para()
    perform_noise(world, child, noise)
    burst(world, animal_cfg)
    loss(world, child, prize_cfg)

    world.para()
    ending(world, child, parent, place, prize_cfg)

    world.facts.update(
        ruined=prize.meters["ruined"] >= THRESHOLD,
        startled=animal.meters["startled"] >= THRESHOLD,
        bad_ending=True,
    )
    return world


PLACES = {
    "reed_bank": Place(
        id="reed_bank",
        label="the reed bank",
        opening="Mist stitched the water to the sky, and even the rushes seemed to sway in rhyme.",
        hush="The bank was hushed in a listening way",
        path_word="the reed bank",
        animals={"goose", "swan"},
        tags={"marsh"},
    ),
    "stable_lane": Place(
        id="stable_lane",
        label="the stable lane",
        opening="The lane smelled warm with straw and hay, and wagon ruts made crooked lines of clay.",
        hush="The lane lay still in a sleepy way",
        path_word="the stable lane",
        animals={"pony", "donkey"},
        tags={"stable"},
    ),
    "mill_pond": Place(
        id="mill_pond",
        label="the mill pond",
        opening="The old wheel dripped a silver thread, and willow leaves bent low above the spray.",
        hush="The pond was calm in a cloudy way",
        path_word="the mill pond",
        animals={"goose", "donkey"},
        tags={"pond"},
    ),
}

NOISES = {
    "tin_whistle": NoiseMaker(
        id="tin_whistle",
        label="tin whistle",
        phrase="a tin whistle",
        sound_word="peep-peep",
        loudness=3,
        action="pipe",
        tags={"sound", "whistle"},
    ),
    "pan_lid": NoiseMaker(
        id="pan_lid",
        label="pan lid",
        phrase="a shiny pan lid and spoon",
        sound_word="clang-clang",
        loudness=3,
        action="bang",
        tags={"sound", "clang"},
    ),
    "reed_flute": NoiseMaker(
        id="reed_flute",
        label="reed flute",
        phrase="a little reed flute",
        sound_word="tootle-toot",
        loudness=2,
        action="tootle",
        tags={"sound", "flute"},
    ),
    "hand_clap": NoiseMaker(
        id="hand_clap",
        label="hands",
        phrase="her own two hands" if False else "two eager hands",
        sound_word="clap-clap",
        loudness=1,
        action="clap",
        tags={"sound", "clap"},
    ),
}

ANIMALS = {
    "goose": AnimalCfg(
        id="goose",
        label="goose",
        phrase="a goose",
        rest_line="a goose sat with its neck tucked under one wing",
        burst_line="Up sprang the goose with a harsh white flap, hissing and hopping across the way",
        skittishness=2,
        jolt=2,
        tags={"goose"},
    ),
    "swan": AnimalCfg(
        id="swan",
        label="swan",
        phrase="a swan",
        rest_line="a swan floated near the reeds, quiet as folded cream",
        burst_line="The swan beat the water hard with its wings, and cold drops slapped the path in spray",
        skittishness=3,
        jolt=3,
        tags={"swan"},
    ),
    "pony": AnimalCfg(
        id="pony",
        label="pony",
        phrase="a pony",
        rest_line="a pony dozed by the fence with one back hoof tipped in hay",
        burst_line="The pony jerked, snorted, and kicked the rail so sharply that pebbles skipped away",
        skittishness=2,
        jolt=2,
        tags={"pony"},
    ),
    "donkey": AnimalCfg(
        id="donkey",
        label="donkey",
        phrase="a donkey",
        rest_line="a donkey stood half asleep beside a post, ears drooping in the gray",
        burst_line="The donkey brayed and lurched aside, knocking the path with a thudding sway",
        skittishness=1,
        jolt=3,
        tags={"donkey"},
    ),
}

PRIZES = {
    "berry_tart": PrizeCfg(
        id="berry_tart",
        label="berry tart",
        phrase="a berry tart on a flat blue cloth",
        carry="jam shone dark as little stars, and sugar dusted the crust like May",
        ruin_line="Down went the berry tart in the mud, red and brown in a sorry array",
        stability=2,
        tags={"tart", "food"},
    ),
    "cream_buns": PrizeCfg(
        id="cream_buns",
        label="cream buns",
        phrase="a paper tray of cream buns",
        carry="their soft tops wobbled like little clouds, and the cream looked ready to sway",
        ruin_line="The cream buns slid from the paper tray and landed squashed in the grit and clay",
        stability=2,
        tags={"buns", "food"},
    ),
    "honey_jar": PrizeCfg(
        id="honey_jar",
        label="honey jar",
        phrase="a warm honey jar wrapped in cloth",
        carry="gold gleamed through the glass, and it smelled of flowers stored away",
        ruin_line="The honey jar struck a stone and cracked, and amber tears ran thick away",
        stability=3,
        tags={"honey", "glass"},
    ),
    "egg_basket": PrizeCfg(
        id="egg_basket",
        label="egg basket",
        phrase="a willow basket of eggs",
        carry="the shells were pale as moons, and each one needed a careful way",
        ruin_line="The egg basket tipped and the shells all broke, yellow and white on the path astray",
        stability=1,
        tags={"eggs", "basket"},
    ),
}

GIRL_NAMES = ["Nell", "Mina", "Tess", "Ruby", "Lila", "Cora", "Wren", "Ivy"]
BOY_NAMES = ["Finn", "Milo", "Jude", "Owen", "Ned", "Theo", "Gus", "Arlo"]
TRAITS = ["curious", "eager", "bouncy", "stubborn", "restless"]


@dataclass
class StoryParams:
    place: str
    noise: str
    animal: str
    prize: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="reed_bank",
        noise="tin_whistle",
        animal="goose",
        prize="berry_tart",
        child_name="Nell",
        child_gender="girl",
        parent="mother",
        trait="eager",
    ),
    StoryParams(
        place="stable_lane",
        noise="pan_lid",
        animal="pony",
        prize="cream_buns",
        child_name="Finn",
        child_gender="boy",
        parent="father",
        trait="bouncy",
    ),
    StoryParams(
        place="mill_pond",
        noise="reed_flute",
        animal="goose",
        prize="egg_basket",
        child_name="Ruby",
        child_gender="girl",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        place="reed_bank",
        noise="pan_lid",
        animal="swan",
        prize="honey_jar",
        child_name="Theo",
        child_gender="boy",
        parent="father",
        trait="stubborn",
    ),
    StoryParams(
        place="stable_lane",
        noise="reed_flute",
        animal="donkey",
        prize="berry_tart",
        child_name="Mina",
        child_gender="girl",
        parent="mother",
        trait="restless",
    ),
]


KNOWLEDGE = {
    "sound": [
        (
            "Why can loud noise bother animals?",
            "Many animals rest lightly and listen for danger, so a sudden loud sound can startle them fast. When they jump or flap, they may knock into nearby things."
        )
    ],
    "goose": [
        (
            "Why can a goose be hard to surprise gently?",
            "A goose notices quick changes around it and can hiss or flap when it feels alarmed. That is why people should move calmly and quietly near geese."
        )
    ],
    "swan": [
        (
            "Why should people stay calm near a swan?",
            "Swans are large birds, and when they are frightened they can beat the water and wings strongly. Quiet voices help them stay settled."
        )
    ],
    "pony": [
        (
            "Why should you not make a loud noise near a pony?",
            "A pony can jump or kick when it is startled. Loud surprises can make even a gentle pony move suddenly."
        )
    ],
    "donkey": [
        (
            "What happens when a donkey gets startled?",
            "A startled donkey may bray loudly and lurch sideways. That quick movement can bump people or things nearby."
        )
    ],
    "eggs": [
        (
            "Why do eggs break easily?",
            "Eggshells are thin and hard, but they crack when they hit something or get squeezed. That is why they must be carried carefully."
        )
    ],
    "glass": [
        (
            "Why can a glass jar break?",
            "Glass is hard but brittle, so a sharp hit can crack it. Once it cracks, what was inside can spill out."
        )
    ],
    "food": [
        (
            "Why can dropped treats be ruined?",
            "When food falls into mud or grit, it gets dirty and is no longer good to eat. A fall can also squash soft treats flat."
        )
    ],
}
KNOWLEDGE_ORDER = ["sound", "goose", "swan", "pony", "donkey", "eggs", "glass", "food"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    place = world.facts["place"]
    noise = world.facts["noise"]
    animal = world.facts["animal_cfg"]
    prize = world.facts["prize_cfg"]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the word "disconcert" and ends sadly.',
        f"Tell a rhyming cautionary tale where {child.id} makes {noise.sound_word} noise at {place.label}, startles a {animal.label}, and loses {prize.phrase}.",
        f"Write a gentle-but-sad poem story in couplets where a child ignores a warning, scares an animal, and walks home without the treat."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    place = world.facts["place"]
    noise = world.facts["noise"]
    animal = world.facts["animal_cfg"]
    prize = world.facts["prize_cfg"]
    pw = parent.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {pw}, a resting {animal.label}, and the treat {child.pronoun()} was carrying. The trouble begins because {child.id} wants to make noise in a quiet place."
        ),
        (
            f"What was {child.id} carrying?",
            f"{child.id} was carrying {prize.phrase}. That prize matters because it is the thing that gets ruined when the startled animal jolts."
        ),
        (
            f"Why did {child.id}'s {pw} warn {child.pronoun('object')}?",
            f"{pw.capitalize()} warned {child.pronoun('object')} because the place was quiet and a {animal.label} was resting nearby. {noise.label.capitalize()} sounds were strong enough to startle it, and then the prize could be lost."
        ),
        (
            f"What happened after {child.id} used the {noise.label}?",
            f"The {animal.label} was startled and burst into sudden motion. That jolt tipped the {prize.label}, so the treat was spoiled instead of saved."
        ),
        (
            "Why is the ending a bad ending?",
            f"It ends badly because nobody can fix the ruined {prize.label}. {child.id} goes home sad, carrying only the empty cloth or basket instead of the treat."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"sound"}
    tags |= set(world.facts["animal_cfg"].tags)
    tags |= set(world.facts["prize_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  events: {world.events}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Optional[Place], noise: Optional[NoiseMaker], animal: Optional[AnimalCfg], prize: Optional[PrizeCfg]) -> str:
    if place and animal and not place_has_animal(place, animal):
        return (
            f"(No story: {animal.phrase} does not belong naturally at {place.label} here, "
            f"so the warning would feel made up. Pick an animal the place actually affords.)"
        )
    if noise and animal and not startles(noise, animal):
        return (
            f"(No story: {noise.phrase} is not loud enough to startle {animal.phrase}, "
            f"so there is no believable turn. Pick a louder noisemaker or an easier-to-startle animal.)"
        )
    if animal and prize and not ruins_prize(animal, prize):
        return (
            f"(No story: a {animal.label}'s jolt is too small to ruin {prize.phrase}, "
            f"so the bad ending would not be earned. Pick a more fragile prize or a stronger jolt.)"
        )
    return "(No story: the chosen options do not make a reasonable cautionary tale.)"


ASP_RULES = r"""
valid(P, N, A, R) :-
    place(P), noise(N), animal(A), prize(R),
    habitat(P, A),
    loudness(N, L), skittishness(A, S), L >= S,
    jolt(A, J), stability(R, T), J >= T.

startled(N, A) :-
    noise(N), animal(A),
    loudness(N, L), skittishness(A, S), L >= S.

ruined(A, R) :-
    animal(A), prize(R),
    jolt(A, J), stability(R, T), J >= T.

bad_ending(P, N, A, R) :- valid(P, N, A, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for animal_id in sorted(place.animals):
            lines.append(asp.fact("habitat", place_id, animal_id))
    for noise_id, noise in NOISES.items():
        lines.append(asp.fact("noise", noise_id))
        lines.append(asp.fact("loudness", noise_id, noise.loudness))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        lines.append(asp.fact("skittishness", animal_id, animal.skittishness))
        lines.append(asp.fact("jolt", animal_id, animal.jolt))
    for prize_id, prize in PRIZES.items():
        lines.append(asp.fact("prize", prize_id))
        lines.append(asp.fact("stability", prize_id, prize.stability))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "disconcert" not in sample.story.lower():
            raise StoryError("smoke test failed: generated story missing expected content")
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=False, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming bad-ending storyworld: a loud little rhyme startles an animal and ruins a treat."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--noise", choices=NOISES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = PLACES.get(args.place) if args.place else None
    noise = NOISES.get(args.noise) if args.noise else None
    animal = ANIMALS.get(args.animal) if args.animal else None
    prize = PRIZES.get(args.prize) if args.prize else None

    if args.place and args.animal and not place_has_animal(place, animal):
        raise StoryError(explain_rejection(place, noise, animal, prize))
    if args.noise and args.animal and not startles(noise, animal):
        raise StoryError(explain_rejection(place, noise, animal, prize))
    if args.animal and args.prize and not ruins_prize(animal, prize):
        raise StoryError(explain_rejection(place, noise, animal, prize))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.noise is None or combo[1] == args.noise)
        and (args.animal is None or combo[2] == args.animal)
        and (args.prize is None or combo[3] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, noise_id, animal_id, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        noise=noise_id,
        animal=animal_id,
        prize=prize_id,
        child_name=name,
        child_gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        noise = NOISES[params.noise]
        animal = ANIMALS[params.animal]
        prize = PRIZES[params.prize]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if not valid_story(place, noise, animal, prize):
        raise StoryError(explain_rejection(place, noise, animal, prize))

    world = tell(
        place=place,
        noise=noise,
        animal_cfg=animal,
        prize_cfg=prize,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, noise, animal, prize) combos:\n")
        for place, noise, animal, prize in combos:
            print(f"  {place:12} {noise:11} {animal:8} {prize}")
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
            header = f"### {p.child_name}: {p.noise} at {p.place} ({p.animal}, {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
