#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/menagerie_complexity_thesis_moral_value_tall_tale.py
===============================================================================

A standalone storyworld about a child who tries to prove a grand thesis with an
impossible parade wagon and learns that kindness and simplicity beat noisy
complexity. The voice leans into a gentle tall-tale style: huge boasts, comic
images, and a moral ending grounded in simulated state.

Reference seed ingredients:
- required words: menagerie, complexity, thesis
- feature: Moral Value
- style: Tall Tale

Run it
------
python storyworlds/worlds/gpt-5.4/menagerie_complexity_thesis_moral_value_tall_tale.py
python storyworlds/worlds/gpt-5.4/menagerie_complexity_thesis_moral_value_tall_tale.py --venue fair --load mountain --fix pare_down
python storyworlds/worlds/gpt-5.4/menagerie_complexity_thesis_moral_value_tall_tale.py --load cloud
python storyworlds/worlds/gpt-5.4/menagerie_complexity_thesis_moral_value_tall_tale.py --all
python storyworlds/worlds/gpt-5.4/menagerie_complexity_thesis_moral_value_tall_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/menagerie_complexity_thesis_moral_value_tall_tale.py --verify
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Venue:
    id: str
    place: str
    crowd: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Load:
    id: str
    count: int
    brag: str
    animals: list[str]
    image: str
    safe_capacity: int
    wildness: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    text: str
    qa_text: str
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_tangle(world: World) -> list[str]:
    wagon = world.get("wagon")
    herd = world.get("herd")
    if wagon.meters["overfull"] < THRESHOLD or herd.meters["moving"] < THRESHOLD:
        return []
    sig = ("tangle",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    herd.meters["tangled"] += 1
    herd.meters["noise"] += 1
    wagon.meters["stalled"] += 1
    child = world.get("child")
    child.memes["worry"] += 1
    return ["__tangle__"]


def _r_scare(world: World) -> list[str]:
    herd = world.get("herd")
    if herd.meters["noise"] < THRESHOLD:
        return []
    sig = ("scare",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child = world.get("child")
    helper = world.get("helper")
    child.memes["embarrassment"] += 1
    helper.memes["concern"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="tangle", tag="physical", apply=_r_tangle),
    Rule(name="scare", tag="social", apply=_r_scare),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


VENUES = {
    "fair": Venue(
        id="fair",
        place="the county fair",
        crowd="a ring of children on fence rails and grown-ups under bright bunting",
        image="every flag in the fairground snapping like it wanted a turn in the story",
        tags={"fair", "crowd"},
    ),
    "parade": Venue(
        id="parade",
        place="the Founders Day parade route",
        crowd="drummers, pie judges, and neighbors lined up along the chalky street",
        image="the brass band shining so hard it looked polished by the sun itself",
        tags={"parade", "crowd"},
    ),
    "schoolyard": Venue(
        id="schoolyard",
        place="the schoolyard exhibition",
        crowd="teachers by folding tables and children standing on tiptoe to see",
        image="paper ribbons twitching on the fence as if even they were curious",
        tags={"school", "crowd"},
    ),
}

LOADS = {
    "porch": Load(
        id="porch",
        count=2,
        brag="two animals, neat as spoons in a drawer",
        animals=["goat", "goose"],
        image="a goat and a goose stepping along like they had practiced all morning",
        safe_capacity=3,
        wildness=1,
        tags={"goat", "goose", "small"},
    ),
    "barn": Load(
        id="barn",
        count=3,
        brag="three animals and a bell with opinions about everything",
        animals=["goat", "goose", "lamb"],
        image="a goat, a goose, and a lamb arranged like a tidy little barnyard band",
        safe_capacity=3,
        wildness=2,
        tags={"goat", "goose", "lamb", "medium"},
    ),
    "mountain": Load(
        id="mountain",
        count=5,
        brag="half the barn and one feather short of a storm cloud",
        animals=["goat", "goose", "lamb", "calf", "duck"],
        image="a wobbling mountain of horns, hooves, wool, and feathers",
        safe_capacity=3,
        wildness=4,
        tags={"goat", "goose", "lamb", "calf", "duck", "large"},
    ),
    "cloud": Load(
        id="cloud",
        count=6,
        brag="so many animals the wagon looked like it had tried to swallow a whole weather system",
        animals=["goat", "goose", "lamb", "calf", "duck", "pony"],
        image="a puffing, snorting, flapping cloud of barnyard feelings",
        safe_capacity=3,
        wildness=5,
        tags={"goat", "goose", "lamb", "calf", "duck", "pony", "huge"},
    ),
}

FIXES = {
    "pare_down": Fix(
        id="pare_down",
        sense=3,
        text="asked for a halter, a scoop of oats, and a little patience, then chose only the calmest pair for the wagon",
        qa_text="pared the load down to the calmest pair and settled them with oats",
        kind="simplify",
        tags={"simple", "kindness"},
    ),
    "walk_beside": Fix(
        id="walk_beside",
        sense=3,
        text="unhitched the side ropes, walked beside the wagon, and gave each animal room and a gentle hand",
        qa_text="walked beside the wagon and gave the animals room and a gentle hand",
        kind="care",
        tags={"simple", "kindness"},
    ),
    "add_more": Fix(
        id="add_more",
        sense=1,
        text="tied on another crate because the child insisted a bigger pile would surely behave better",
        qa_text="added still more crates",
        kind="worse",
        tags={"complexity"},
    ),
}

GIRL_NAMES = ["Mabel", "Tess", "Ivy", "Nell", "Ada", "Willa", "Ruth", "June"]
BOY_NAMES = ["Eli", "Beau", "Cal", "Otis", "Jeb", "Milo", "Ned", "Finn"]
TRAITS = ["bold", "hopeful", "showy", "cheerful", "eager", "stubborn"]


def load_is_reasonable(load: Load) -> bool:
    return load.count >= 2


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def is_overfull(load: Load) -> bool:
    return load.count > load.safe_capacity


def outcome_of(params: "StoryParams") -> str:
    load = LOADS[params.load]
    fix = FIXES[params.fix]
    if not is_overfull(load):
        return "smooth"
    if fix.kind in {"simplify", "care"} and fix.sense >= SENSE_MIN:
        return "mended"
    return "jumble"


def predict_jumble(world: World, load: Load) -> dict:
    sim = world.copy()
    herd = sim.get("herd")
    wagon = sim.get("wagon")
    herd.meters["moving"] += 1
    herd.meters["count"] = float(load.count)
    if is_overfull(load):
        wagon.meters["overfull"] += 1
    propagate(sim, narrate=False)
    return {
        "tangled": herd.meters["tangled"] >= THRESHOLD,
        "noise": herd.meters["noise"],
        "stalled": wagon.meters["stalled"],
    }


def load_animals_phrase(load: Load) -> str:
    names = list(load.animals)
    if len(names) == 2:
        return f"a {names[0]} and a {names[1]}"
    if len(names) == 3:
        return f"a {names[0]}, a {names[1]}, and a {names[2]}"
    head = ", ".join(f"a {n}" for n in names[:-1])
    return f"{head}, and a {names[-1]}"


def introduce(world: World, child: Entity, venue: Venue) -> None:
    world.say(
        f"In the valley below Thunder-Tall Hill lived {child.id}, a {child.type} whose ideas usually arrived wearing boots too big for the porch."
    )
    world.say(
        f"When talk of {venue.place} came rolling down the road, {child.id} decided to arrive so grandly that even {venue.image} would have to blink."
    )


def announce_thesis(world: World, child: Entity, load: Load) -> None:
    child.memes["pride"] += 1
    world.say(
        f'"I have a thesis," {child.id} declared, puffing up like a parade trumpet. '
        f'"If one nice animal makes folks smile, then {load.brag} will make them cheer clear past supper."'
    )
    world.say(
        f"So {child.pronoun()} planned a menagerie for the wagon: {load_animals_phrase(load)}."
    )


def build_wagon(world: World, child: Entity, load: Load) -> None:
    wagon = world.get("wagon")
    herd = world.get("herd")
    wagon.meters["cargo"] = float(load.count)
    herd.meters["count"] = float(load.count)
    herd.meters["moving"] += 1
    if is_overfull(load):
        wagon.meters["overfull"] += 1
    world.say(
        f"By breakfast, the little red wagon looked less like a wagon and more like {load.image}."
    )
    if is_overfull(load):
        world.say(
            f"The plan had a smell of complexity about it. There were too many ropes to remember, too many feet to place, and too many opinions for one set of wheels."
        )


def warn(world: World, child: Entity, helper: Entity, venue: Venue, load: Load) -> None:
    pred = predict_jumble(world, load)
    world.facts["predicted_tangled"] = pred["tangled"]
    world.facts["predicted_noise"] = pred["noise"]
    if pred["tangled"]:
        helper.memes["care"] += 1
        world.say(
            f'{helper.id}, {child.pronoun("possessive")} {helper.label_word}, squinted at the wagon and said, '
            f'"That many creatures may reach {venue.place}, but they will not reach it politely. A kind parade is better than a crowded one."'
        )
    else:
        world.say(
            f'{helper.id}, {child.pronoun("possessive")} {helper.label_word}, tipped a hat and said, '
            f'"That looks lively, but not mean. Keep your hands gentle and your voice low."'
        )


def set_off(world: World, child: Entity, venue: Venue) -> None:
    world.say(
        f"Off they went toward {venue.place}, with {venue.crowd} waiting ahead."
    )


def tangle(world: World, child: Entity) -> None:
    herd = world.get("herd")
    herd.meters["moving"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the whole wagon argued with itself. The goose wanted sky, the goat wanted thistles, and the calf wanted yesterday. Ropes crossed, hooves shuffled, feathers burst upward, and the brave wagon stopped as if it had planted its own wheels."
    )
    world.say(
        f"{child.id}'s cheeks went pink. All at once {child.pronoun()} saw that a big pile of wonders can still be a muddle."
    )


def fix_scene(world: World, child: Entity, helper: Entity, fix: Fix, load: Load) -> None:
    herd = world.get("herd")
    wagon = world.get("wagon")
    world.say(
        f"{helper.id} did not scold. {helper.pronoun().capitalize()} {fix.text}."
    )
    if fix.kind == "simplify":
        herd.meters["count"] = 2.0
        wagon.meters["cargo"] = 2.0
    wagon.meters["stalled"] = 0.0
    wagon.meters["overfull"] = 0.0
    herd.meters["tangled"] = 0.0
    herd.meters["noise"] = 0.0
    child.memes["relief"] += 1
    child.memes["learning"] += 1
    world.say(
        f'Soon the noise shrank to snuffles and soft steps. "{child.id}," said {helper.id}, "kindness makes a straighter road than showiness."'
    )


def smooth_arrival(world: World, child: Entity, venue: Venue, load: Load) -> None:
    child.memes["joy"] += 1
    child.memes["learning"] += 1
    world.say(
        f"And what do you know? {load.image.capitalize()} rolled into {venue.place} as neatly as a ribbon through a ring."
    )
    world.say(
        f"People laughed, not because the wagon was foolish, but because it was merry and gentle."
    )


def ending(world: World, child: Entity, venue: Venue, outcome: str) -> None:
    if outcome == "smooth":
        world.say(
            f"That evening, with dust on the wheels and sunset on the rails, {child.id} changed the thesis in {child.pronoun('possessive')} head. It was not the biggest display that won the day at {venue.place}. It was the one that kept every creature calm."
        )
    elif outcome == "mended":
        world.say(
            f"When the wagon finally rolled into {venue.place}, it held fewer animals and more peace. From then on, {child.id} told everyone that the finest menagerie is the one you can guide with kind hands."
        )
    else:
        world.say(
            f"They did reach {venue.place}, but only after a long, noisy shuffle and several apologies. On the way home, {child.id} admitted that bragging can grow faster than wisdom, and promised next time to choose kindness before complexity."
        )


def tell(
    venue: Venue,
    load: Load,
    fix: Fix,
    child_name: str = "Mabel",
    child_type: str = "girl",
    helper_type: str = "aunt",
    trait: str = "bold",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        attrs={"trait": trait},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
    ))
    wagon = world.add(Entity(
        id="wagon",
        type="wagon",
        label="wagon",
        phrase="the red wagon",
    ))
    herd = world.add(Entity(
        id="herd",
        type="animals",
        label="menagerie",
        phrase="the menagerie",
    ))

    introduce(world, child, venue)
    announce_thesis(world, child, load)

    world.para()
    build_wagon(world, child, load)
    warn(world, child, helper, venue, load)
    set_off(world, child, venue)

    outcome = outcome_of(StoryParams(
        venue=venue.id,
        load=load.id,
        fix=fix.id,
        name=child_name,
        gender=child_type,
        helper=helper_type,
        trait=trait,
        seed=None,
    ))

    world.para()
    if outcome == "smooth":
        smooth_arrival(world, child, venue, load)
    else:
        tangle(world, child)
        if outcome == "mended":
            fix_scene(world, child, helper, fix, load)
        else:
            if fix.kind == "worse":
                world.say(
                    f'{helper.id} tried to help, but {child.id} still believed a bigger pile would somehow turn into better manners. It did not.'
                )
            else:
                world.say(
                    f'{helper.id} reached for the ropes, but the wagon had already spent its good sense for the day.'
                )

    world.para()
    ending(world, child, venue, outcome)

    moral = {
        "smooth": "A gentle plan can be grand without becoming a muddle.",
        "mended": "When a plan grows too tangled, kindness and simplicity can set it right.",
        "jumble": "Boasting and extra fuss do not make a kinder or better parade.",
    }[outcome]

    world.facts.update(
        child=child,
        helper=helper,
        wagon=wagon,
        herd=herd,
        venue=venue,
        load=load,
        fix=fix,
        outcome=outcome,
        moral=moral,
        tangled=herd.meters["tangled"] >= THRESHOLD or outcome == "jumble",
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for venue_id in VENUES:
        for load_id, load in LOADS.items():
            if not load_is_reasonable(load):
                continue
            for fix_id, fix in FIXES.items():
                if is_overfull(load):
                    if fix.sense >= SENSE_MIN or fix.kind == "worse":
                        combos.append((venue_id, load_id, fix_id))
                else:
                    if fix.sense >= SENSE_MIN:
                        combos.append((venue_id, load_id, fix_id))
    return combos


@dataclass
class StoryParams:
    venue: str
    load: str
    fix: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "menagerie": [
        (
            "What is a menagerie?",
            "A menagerie is a collection of different animals gathered together in one place. It can look exciting, but it also takes a lot of care to keep all the animals calm and safe.",
        )
    ],
    "complexity": [
        (
            "What does complexity mean?",
            "Complexity means something has many parts to manage at once. When a plan grows too complex, it is easier to forget something important or let it become a muddle.",
        )
    ],
    "thesis": [
        (
            "What is a thesis?",
            "A thesis is the main idea someone is trying to prove. In a simple story, it can be the big claim a character starts with before learning whether it is true.",
        )
    ],
    "kindness": [
        (
            "Why can a simpler plan be kinder?",
            "A simpler plan is easier to guide and safer for everyone in it. When people or animals are calmer, they are less likely to get scared or tangled up.",
        )
    ],
    "wagon": [
        (
            "Why should you not put too much on a wagon?",
            "If a wagon is too full, it can become hard to pull or steer. Too much weight or too many moving parts can make the ride wobbly and unsafe.",
        )
    ],
    "goat": [
        (
            "What is a goat like?",
            "A goat is a farm animal with quick feet and a curious mind. Goats like to nibble and poke into things, so they need watching.",
        )
    ],
    "goose": [
        (
            "Why can a goose be noisy?",
            "A goose has a strong voice and uses it when it feels excited or bothered. That can make a place feel busy in a hurry.",
        )
    ],
    "calf": [
        (
            "What is a calf?",
            "A calf is a young cow. Calves can be sweet, but they are still strong and need gentle handling.",
        )
    ],
    "pony": [
        (
            "What is a pony?",
            "A pony is a small horse. Even a small horse is powerful, so it needs space and careful handling.",
        )
    ],
}
KNOWLEDGE_ORDER = ["menagerie", "complexity", "thesis", "kindness", "wagon", "goat", "goose", "calf", "pony"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    venue = f["venue"]
    load = f["load"]
    outcome = f["outcome"]
    base = (
        f'Write a tall-tale story for a young child that includes the words "menagerie", '
        f'"complexity", and "thesis". The story should take place at {venue.place}.'
    )
    if outcome == "smooth":
        return [
            base,
            f"Tell a playful tall tale where {child.id} brings {load.brag} to {venue.place}, but the animals stay gentle and the child learns that calm care matters more than bragging.",
            'Write a story with a moral value showing that a grand idea can still stay simple and kind.',
        ]
    if outcome == "mended":
        return [
            base,
            f"Tell a tall tale where {child.id} tries to prove a grand thesis with a crowded wagon, the plan becomes too full of complexity, and a caring grown-up helps untangle it.",
            'Write a story whose moral is that kindness and simplicity can rescue a boastful plan.',
        ]
    return [
        base,
        f"Tell a tall tale where {child.id} makes a wagon so crowded it becomes a muddle on the way to {venue.place}, and the child learns that bigger is not always better.",
        'Write a moral story showing that showy fuss and extra complexity do not make a kinder success.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    venue = f["venue"]
    load = f["load"]
    fix = f["fix"]
    outcome = f["outcome"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child with a giant idea, and {helper.label_word} {helper.id}, who tries to guide that idea kindly. The story follows them on the way to {venue.place}.",
        ),
        (
            "What was the child's thesis at the start?",
            f"{child.id} believed that a bigger menagerie would make everyone cheer more. That thesis sounded bold, but it had not yet been tested against what the animals could handle.",
        ),
        (
            "Why did the wagon start to feel full of complexity?",
            f"The wagon had too many animals, ropes, and opinions to manage at once. That made it hard to keep every creature calm and moving in the same direction.",
        ),
    ]
    if outcome == "smooth":
        qa.append(
            (
                "Did the wagon get tangled?",
                f"No. The load was small enough to stay calm, so the wagon rolled in gently instead of turning into a jumble. The child still learned that a kind, manageable plan is better than a boastful one.",
            )
        )
    elif outcome == "mended":
        qa.append(
            (
                f"How did {helper.label_word} {helper.id} solve the problem?",
                f"{helper.id} {fix.qa_text}. That lowered the crowding and helped the animals settle down, so the parade could continue in a kinder way.",
            )
        )
        qa.append(
            (
                "What changed by the end of the story?",
                f"By the end, the wagon held less fuss and more peace. {child.id} stopped trying to impress everyone with size alone and began to value calm care instead.",
            )
        )
    else:
        qa.append(
            (
                "Why did the plan turn into a jumble?",
                f"It turned into a jumble because the wagon was too crowded and the child kept trusting size more than sense. The extra fuss did not help the animals cooperate; it only made the muddle louder.",
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{child.id} learned that bragging and piling on more do not make a better parade. A plan should be gentle enough for the people and animals in it, not just big enough to boast about.",
            )
        )
    qa.append(
        (
            "What is the moral of the story?",
            f'{f["moral"]} That is why the ending proves the child changed, not just the wagon.',
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"menagerie", "complexity", "thesis", "kindness", "wagon"} | set(f["load"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        venue="fair",
        load="porch",
        fix="pare_down",
        name="Mabel",
        gender="girl",
        helper="aunt",
        trait="hopeful",
    ),
    StoryParams(
        venue="parade",
        load="barn",
        fix="walk_beside",
        name="Eli",
        gender="boy",
        helper="uncle",
        trait="eager",
    ),
    StoryParams(
        venue="schoolyard",
        load="mountain",
        fix="pare_down",
        name="Tess",
        gender="girl",
        helper="mother",
        trait="showy",
    ),
    StoryParams(
        venue="fair",
        load="cloud",
        fix="walk_beside",
        name="Beau",
        gender="boy",
        helper="father",
        trait="bold",
    ),
    StoryParams(
        venue="parade",
        load="cloud",
        fix="add_more",
        name="June",
        gender="girl",
        helper="aunt",
        trait="stubborn",
    ),
]


def explain_rejection(load: Load, fix: Fix) -> str:
    if not load_is_reasonable(load):
        return "(No story: the wagon needs at least a small menagerie to make this tale.)"
    if fix.sense < SENSE_MIN and not is_overfull(load):
        return (
            f"(No story: fix '{fix.id}' is too unreasonable here. When the load is already manageable, the storyworld refuses to make things worse on purpose.)"
        )
    return "(No story: this combination does not describe a sensible tall-tale scenario.)"


def explain_fix(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense for a default request "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


ASP_RULES = r"""
reasonable_load(L) :- load(L), count(L, C), C >= 2.
overfull(L) :- load(L), count(L, C), safe_capacity(L, S), C > S.
sensible(F) :- fix(F), sense(F, V), sense_min(M), V >= M.

valid(Vn, L, F) :- venue(Vn), reasonable_load(L), not overfull(L), sensible(F).
valid(Vn, L, F) :- venue(Vn), reasonable_load(L), overfull(L), fix(F).

smooth :- chosen_load(L), not overfull(L).
mended :- chosen_load(L), overfull(L), chosen_fix(F), fix_kind(F, simplify), sensible(F).
mended :- chosen_load(L), overfull(L), chosen_fix(F), fix_kind(F, care), sensible(F).
jumble :- chosen_load(L), overfull(L), chosen_fix(F), fix_kind(F, worse).
outcome(smooth) :- smooth.
outcome(mended) :- mended.
outcome(jumble) :- jumble.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id in VENUES:
        lines.append(asp.fact("venue", venue_id))
    for load_id, load in LOADS.items():
        lines.append(asp.fact("load", load_id))
        lines.append(asp.fact("count", load_id, load.count))
        lines.append(asp.fact("safe_capacity", load_id, load.safe_capacity))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("fix_kind", fix_id, fix.kind))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_load", params.load),
        asp.fact("chosen_fix", params.fix),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {f.id for f in sensible_fixes()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible fixes match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a child, a wagon menagerie, too much complexity, and a moral about kindness."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.load and args.load not in LOADS:
        raise StoryError(f"(Unknown load: {args.load})")
    if args.fix and args.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {args.fix})")
    if args.venue and args.venue not in VENUES:
        raise StoryError(f"(Unknown venue: {args.venue})")

    if args.load and args.fix:
        load = LOADS[args.load]
        fix = FIXES[args.fix]
        if not load_is_reasonable(load) or (fix.sense < SENSE_MIN and not is_overfull(load)):
            raise StoryError(explain_rejection(load, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.load is None or combo[1] == args.load)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, load_id, fix_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    helper = args.helper or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        venue=venue_id,
        load=load_id,
        fix=fix_id,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.venue not in VENUES:
        raise StoryError(f"(Unknown venue: {params.venue})")
    if params.load not in LOADS:
        raise StoryError(f"(Unknown load: {params.load})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    load = LOADS[params.load]
    fix = FIXES[params.fix]
    if not load_is_reasonable(load):
        raise StoryError(explain_rejection(load, fix))
    if fix.sense < SENSE_MIN and not is_overfull(load):
        raise StoryError(explain_rejection(load, fix))

    world = tell(
        venue=VENUES[params.venue],
        load=load,
        fix=fix,
        child_name=params.name,
        child_type=params.gender,
        helper_type=params.helper,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, load, fix) combos:\n")
        for venue_id, load_id, fix_id in combos:
            print(f"  {venue_id:10} {load_id:10} {fix_id}")
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
            header = f"### {p.name}: {p.load} load at {p.venue} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
