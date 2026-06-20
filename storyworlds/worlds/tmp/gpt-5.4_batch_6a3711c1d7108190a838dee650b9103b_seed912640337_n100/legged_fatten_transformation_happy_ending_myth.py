#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/legged_fatten_transformation_happy_ending_myth.py
=============================================================================

A small myth-flavoured storyworld about a hungry little creature who thinks it
can fatten itself into greatness, then learns that a generous heart brings the
true transformation. Every generated sample keeps the same strong shape:

- a slight, legged creature receives a sacred task
- hunger and doubt tempt the creature to solve the problem by eating more
- a hidden god appears as a hungry stranger
- the creature shares its food instead of hoarding it
- gratitude unlocks a fitting transformation
- the task is completed, and the land is blessed

The reasonableness gate is narrow on purpose. Not every sacred form can solve
every task, and not every offering leaves enough food to share. This world
prefers a few solid myths over many weak permutations.
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested directory under storyworlds/worlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"        # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    # Physical meters and emotional memes live side by side.
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "goddess", "mother"}
        male = {"boy", "man", "god", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# World knobs
# ---------------------------------------------------------------------------
@dataclass
class Creature:
    id: str
    kind: str
    title: str
    opening: str
    gait: str
    natural_traits: set[str]
    hunger: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    burden: str
    place: str
    danger: str
    need: str
    approach: set[str]
    blessing: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Offering:
    id: str
    label: str
    phrase: str
    portions: int
    richness: int
    shine: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Boon:
    id: str
    title: str
    phrase: str
    grants: set[str]
    arrival: str
    triumph: str
    image: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fullness_slows(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["full"] < 2:
        return []
    sig = ("slowed", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["slowness"] += 1
    hero.memes["worry"] += 1
    return []


def _r_generosity_blesses(world: World) -> list[str]:
    hero = world.get("hero")
    stranger = world.get("stranger")
    if hero.memes["generosity"] < THRESHOLD or stranger.memes["gratitude"] < THRESHOLD:
        return []
    sig = ("blessed", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["blessed"] += 1
    hero.memes["hope"] += 1
    return []


CAUSAL_RULES = [
    Rule("fullness_slows", "physical", _r_fullness_slows),
    Rule("generosity_blesses", "mythic", _r_generosity_blesses),
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
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def share_possible(offering: Offering) -> bool:
    return offering.portions >= 2


def can_reach_task(creature: Creature, task: Task) -> bool:
    return bool(creature.natural_traits & task.approach)


def boon_fits_task(boon: Boon, task: Task) -> bool:
    return task.need in boon.grants


def valid_combo(creature: Creature, task: Task, offering: Offering, boon: Boon) -> bool:
    return share_possible(offering) and can_reach_task(creature, task) and boon_fits_task(boon, task)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for cid, creature in CREATURES.items():
        for tid, task in TASKS.items():
            for oid, offering in OFFERINGS.items():
                for bid, boon in BOONS.items():
                    if valid_combo(creature, task, offering, boon):
                        combos.append((cid, tid, oid, bid))
    return combos


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_attempt(world: World, task: Task) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    success = task.need in hero.attrs.get("current_traits", set()) and hero.meters["slowness"] < THRESHOLD
    return {
        "success": success,
        "slowness": hero.meters["slowness"],
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, creature: Creature, task: Task, guide: Entity) -> None:
    hero.attrs["current_traits"] = set(creature.natural_traits)
    hero.meters["hunger"] = float(creature.hunger)
    world.say(
        f"In the first age, when streams still listened and hills still answered, "
        f"there lived {creature.opening} named {hero.id}. {creature.gait}"
    )
    world.say(
        f"One dawn, {guide.id}, keeper of the old shrine, placed {task.burden} before "
        f"{hero.id} and said that it must be carried to {task.place} before sunset, "
        f"or {task.danger}."
    )


def desire_strength(world: World, hero: Entity, creature: Creature, offering: Offering) -> None:
    hero.memes["duty"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} looked at the long road and the sacred burden, and fear fluttered in "
        f"{hero.pronoun('possessive')} chest. On a stone dish beside the path lay {offering.phrase}, "
        f"{offering.shine}, meant for the journey."
    )
    world.say(
        f'"If I eat enough, perhaps I can fatten myself strong enough for this work," '
        f"{hero.id} whispered."
    )


def eat_to_fatten(world: World, hero: Entity, offering: Offering) -> None:
    eaten = max(1, offering.portions - 1)
    hero.meters["full"] += float(offering.richness)
    hero.meters["strength"] += 1
    hero.attrs["left_portions"] = offering.portions - eaten
    hero.attrs["eaten_portions"] = eaten
    propagate(world, narrate=False)
    if hero.meters["slowness"] >= THRESHOLD:
        world.say(
            f"{hero.id} ate quickly, hoping the sweet food would make {hero.pronoun('object')} mighty. "
            f"But the meal sat heavy, and those small legged steps grew slower instead of surer."
        )
    else:
        world.say(
            f"{hero.id} ate one share and felt warmer for a moment. Still, the old doubt remained."
        )


def warning(world: World, guide: Entity, hero: Entity) -> None:
    if hero.meters["slowness"] >= THRESHOLD:
        world.say(
            f'{guide.id} touched the shrine gate and said, "A full belly is good, little one, '
            f'but too much food can only burden your feet. The road asks for more than that."'
        )
    else:
        world.say(
            f'{guide.id} watched kindly and said, "Food can steady a traveler, but it cannot turn '
            f'fear into wisdom all by itself."'
        )


def first_attempt(world: World, hero: Entity, task: Task) -> None:
    pred = predict_attempt(world, task)
    world.facts["attempt_success"] = pred["success"]
    if pred["success"]:
        world.say(
            f"{hero.id} started up the road at once, and for a little while the path obeyed "
            f"{hero.pronoun('object')}. Yet the last stretch toward {task.place} still shimmered "
            f"with sacred difficulty."
        )
    else:
        world.say(
            f"{hero.id} set out toward {task.place}, but the way soon proved too hard. "
            f"{task.danger[0].upper()}{task.danger[1:]}, and the sacred burden trembled in "
            f"{hero.pronoun('possessive')} grasp."
        )


def stranger_appears(world: World, stranger: Entity) -> None:
    world.say(
        f"Then, from the edge of the path, came {stranger.label}. Dust clung to "
        f"{stranger.pronoun('possessive')} hem, and hunger shone plainly in "
        f"{stranger.pronoun('possessive')} eyes."
    )
    world.say(f'"Traveler," {stranger.pronoun()} asked softly, "have you a share to spare?"')


def share(world: World, hero: Entity, stranger: Entity, offering: Offering) -> None:
    hero.attrs["left_portions"] -= 1
    hero.memes["generosity"] += 1
    stranger.memes["gratitude"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} looked at the last of {offering.label}, then at the hungry stranger, and "
        f"held out the final share. {hero.pronoun().capitalize()} chose kindness over fear."
    )


def reveal_and_transform(world: World, hero: Entity, stranger: Entity, boon: Boon) -> None:
    hero.attrs["current_traits"] = set(hero.attrs.get("current_traits", set())) | set(boon.grants)
    hero.attrs["form"] = boon.title
    hero.meters["slowness"] = 0.0
    hero.memes["wonder"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"The stranger smiled, and the dust-faded cloak fell away like mist. "
        f"{stranger.id} was no wanderer at all, but a hidden god of the road."
    )
    world.say(
        f"{boon.arrival} At once {hero.id} was transformed into {boon.phrase}, and "
        f"{hero.pronoun('possessive')} heart felt light instead of afraid."
    )


def triumph(world: World, hero: Entity, task: Task, boon: Boon) -> None:
    hero.meters["completed"] += 1
    world.say(
        f"Now {boon.triumph}, {hero.id} carried {task.burden} to {task.place}. "
        f"There {hero.pronoun()} laid it down before the waiting altar."
    )
    world.say(
        f"At once {task.blessing}, and the people below lifted their faces in relief."
    )


def ending(world: World, hero: Entity, creature: Creature, boon: Boon, task: Task) -> None:
    world.say(
        f"From that day on, the old songs remembered {hero.id} not as the frightened "
        f"{creature.kind} of the morning, but as {boon.title}, {boon.image}."
    )
    world.say(
        f"And whenever little creatures feared they were too small for holy work, elders told "
        f"this myth: do not try only to fatten your body; let generosity change your shape, and "
        f"the road may open beneath your feet."
    )
    world.facts["moral"] = (
        "Generosity changed the hero more deeply than stuffing a hungry belly ever could."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    creature: Creature,
    task: Task,
    offering: Offering,
    boon: Boon,
    hero_name: str = "Iris",
    guide_name: str = "Thaleia",
    guide_type: str = "goddess",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="creature", role="hero"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_type, role="guide", label="the shrine-keeper"))
    stranger = world.add(Entity(id="Selene", kind="character", type="goddess", role="stranger", label="a bent old traveler"))

    introduce(world, hero, creature, task, guide)
    world.para()
    desire_strength(world, hero, creature, offering)
    eat_to_fatten(world, hero, offering)
    warning(world, guide, hero)
    first_attempt(world, hero, task)
    world.para()
    stranger_appears(world, stranger)
    share(world, hero, stranger, offering)
    reveal_and_transform(world, hero, stranger, boon)
    world.para()
    triumph(world, hero, task, boon)
    ending(world, hero, creature, boon, task)

    world.facts.update(
        hero=hero,
        guide=guide,
        stranger=stranger,
        creature=creature,
        task=task,
        offering=offering,
        boon=boon,
        shared=True,
        transformed=hero.attrs.get("form", "") == boon.title,
        completed=hero.meters["completed"] >= THRESHOLD,
        final_form=hero.attrs.get("form", boon.title),
        left_portions=hero.attrs.get("left_portions", 0),
        slowness_before=1 if offering.richness >= 2 else 0,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
CREATURES = {
    "foxling": Creature(
        "foxling",
        "foxling",
        "a nimble foxling with ember-bright ears",
        "Though small, the foxling had quick two-legged hops when climbing stones and scrambling roots.",
        "Its paws were swift on rough ground, but its body was still slight.",
        {"quick", "climber"},
        hunger=2,
        tags={"fox", "small_creature"},
    ),
    "goatling": Creature(
        "goatling",
        "goatling",
        "a pale goatling with bright eyes and a brave little chin",
        "The goatling was sure on steep places, a sturdy four-legged child of the cliffs.",
        "It trusted rock more than water, and height more than wind.",
        {"surefooted", "climber"},
        hunger=2,
        tags={"goat", "small_creature"},
    ),
    "reed_fawn": Creature(
        "reed_fawn",
        "fawn",
        "a reed-fawn, all ears and trembling knees",
        "The fawn's long legged shadow looked elegant at dawn, yet youth still made it uncertain.",
        "It could pick its way through marsh grass, though not yet through sacred danger.",
        {"longlegged", "marshwalker"},
        hunger=1,
        tags={"deer", "small_creature"},
    ),
}

TASKS = {
    "stair_of_sun": Task(
        "stair_of_sun",
        "the Bowl of Dawn",
        "the Stair of the Sun",
        "the steep black steps would throw the bowl back into the ravine",
        "surefooted",
        {"climber", "surefooted"},
        "the first light spilled cleanly across the valley fields",
        "a gold band lay on every roof tile before evening",
        tags={"mountain", "sun"},
    ),
    "reed_ford": Task(
        "reed_ford",
        "the Ember Seed",
        "the Reed Ford of Morning",
        "the flooded reeds would swallow it under the silver water",
        "longlegged",
        {"marshwalker", "longlegged"},
        "warmth returned to the river villages",
        "lantern-fish flashed again in the channels",
        tags={"marsh", "river"},
    ),
    "bridge_of_wind": Task(
        "bridge_of_wind",
        "the Bell of First Rain",
        "the Bridge of Wind",
        "the hanging bridge would sway so wildly that the bell would be lost to the clouds",
        "winged",
        {"climber", "quick"},
        "soft rain began to fall over the thirsty orchards",
        "every fig leaf held a shining drop",
        tags={"sky", "rain"},
    ),
}

OFFERINGS = {
    "moon_figs": Offering(
        "moon_figs",
        "moon figs",
        "three moon figs, cool and pale as little moons",
        portions=3,
        richness=2,
        shine="their skins silvered with dew",
        tags={"fig", "food"},
    ),
    "honey_cakes": Offering(
        "honey_cakes",
        "honey cakes",
        "two honey cakes stamped with a star-wheel",
        portions=2,
        richness=2,
        shine="their edges glimmering with amber glaze",
        tags={"cake", "food"},
    ),
    "barley_loaf": Offering(
        "barley_loaf",
        "barley loaf",
        "a round barley loaf already cut into two warm halves",
        portions=2,
        richness=1,
        shine="steam curling from the cracked crust",
        tags={"bread", "food"},
    ),
    "single_pear": Offering(
        "single_pear",
        "the star pear",
        "one star pear set alone on the dish",
        portions=1,
        richness=1,
        shine="its skin bright as polished green glass",
        tags={"pear", "food"},
    ),
}

BOONS = {
    "moon_stag": Boon(
        "moon_stag",
        "the Moon Stag",
        "a moon-white stag with calm, sure legs and a bright brow",
        {"surefooted", "longlegged"},
        "Silver antlers arched above the hero like new crescents.",
        "each careful step rang true on the hard ascent",
        "whose hooves learned the language of high stone",
        tags={"deer", "transformation"},
    ),
    "reed_heron": Boon(
        "reed_heron",
        "the Reed Heron",
        "a tall heron with long shining legs and patient wings",
        {"longlegged", "winged"},
        "Feathers streamed down in a circle, smelling of river mist and lotus pollen.",
        "the marsh opened in narrow shining paths beneath those long steps",
        "whose feet could read the depth of hidden water",
        tags={"bird", "transformation"},
    ),
    "storm_swallow": Boon(
        "storm_swallow",
        "the Storm Swallow",
        "a dark swallow with a breast like wet sapphire and tireless wings",
        {"winged", "quick"},
        "A ring of rain-bright feathers spun through the air.",
        "the wind itself bent kindly around those wings",
        "whose flight stitched sky to orchard",
        tags={"bird", "transformation"},
    ),
}

NAMES = ["Iris", "Nysa", "Theron", "Damon", "Lyra", "Petra", "Aster", "Calla"]
GUIDES = [
    ("Thaleia", "goddess"),
    ("Maron", "god"),
    ("Eirene", "goddess"),
    ("Lykos", "god"),
]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    creature: str
    task: str
    offering: str
    boon: str
    hero_name: str
    guide_name: str
    guide_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "fig": [(
        "What is a fig?",
        "A fig is a soft fruit full of tiny seeds. In stories, figs often feel rich and special because they are sweet and full of life."
    )],
    "cake": [(
        "Why would honey cakes feel rich after a long walk?",
        "Honey cakes are sweet and heavy, so they can make a hungry traveler feel full very quickly. Too much rich food can also make a body feel slow."
    )],
    "bread": [(
        "What is barley bread made from?",
        "Barley bread is made from grain. It is simple, filling food that travelers and workers can carry on a journey."
    )],
    "pear": [(
        "Why is one piece of food hard to share?",
        "One piece of food may not leave enough for two hungry people. Sharing becomes easier when there is more than one portion."
    )],
    "mountain": [(
        "Why do steep stairs need sure feet?",
        "Steep stairs are hard because one wrong step can make you slip or drop what you are carrying. Sure feet help you place each step safely."
    )],
    "marsh": [(
        "Why are long legs helpful in a marsh?",
        "A marsh is wet and soft, so long legs help you step above deep puddles and hidden mud. They let you reach firmer ground."
    )],
    "sky": [(
        "Why would wings help on a windy bridge?",
        "Wings can help a creature balance and move through air. In a myth, wings also show that the sky itself is helping."
    )],
    "rain": [(
        "Why is rain a blessing in a myth?",
        "Rain helps trees, crops, and rivers. In myths, good rain often shows that the land has been put back into balance."
    )],
    "transformation": [(
        "What is a transformation in a myth?",
        "A transformation is when someone changes shape in a magical way. In myths, the new shape usually fits a lesson the person has learned."
    )],
    "food": [(
        "Why does this myth warn against trying only to fatten yourself?",
        "Food can help a body, but it cannot solve every problem. The myth teaches that kindness and wisdom matter more than stuffing yourself."
    )],
}
KNOWLEDGE_ORDER = [
    "fig", "cake", "bread", "pear", "mountain", "marsh", "sky", "rain",
    "transformation", "food"
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    creature, task, boon, offering = f["creature"], f["task"], f["boon"], f["offering"]
    return [
        f'Write a short child-facing myth that includes the words "legged" and "fatten". '
        f'The hero is a small {creature.kind} who must carry {task.burden} to {task.place}.',
        f"Tell a transformation myth where a hungry little creature first tries to solve a sacred task "
        f"by eating {offering.label}, then shares the last portion with a disguised god and becomes {boon.title}.",
        f"Write a happy-ending myth about kindness changing a hero more deeply than food does, ending with "
        f"{task.blessing}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    creature = f["creature"]
    task = f["task"]
    offering = f["offering"]
    boon = f["boon"]
    guide = f["guide"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {creature.opening}, who was given the holy task of carrying "
            f"{task.burden} to {task.place}. {guide.id} sent {hero.pronoun('object')} on the journey."
        ),
        (
            f"Why did {hero.id} eat the {offering.label} at first?",
            f"{hero.id} was afraid of failing the task and thought more food might make {hero.pronoun('object')} strong enough. "
            f"{hero.pronoun().capitalize()} hoped to fatten {hero.pronoun('possessive')} body into bravery."
        ),
        (
            "Why did that plan not solve the problem?",
            f"The food filled the hero, but it did not give the exact gift the road required. "
            f"The task needed someone {task.need}, not simply someone with a fuller belly."
        ),
        (
            "What changed the story?",
            f"The turning point came when the hungry stranger asked for food and {hero.id} shared the last portion. "
            f"That act of generosity brought gratitude, blessing, and then the transformation."
        ),
        (
            f"What did {hero.id} become?",
            f"{hero.id} became {boon.phrase}. The new form matched the task, which is why the sacred journey could finally be finished."
        ),
        (
            "How did the story end?",
            f"It ended happily: {hero.id} reached {task.place}, set down {task.burden}, and {task.blessing}. "
            f"The ending proves that the land changed for the better after the hero changed too."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["offering"].tags) | set(f["task"].tags) | set(f["boon"].tags) | {"transformation", "food"}
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        attrs = {k: v for k, v in e.attrs.items() if v}
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("goatling", "stair_of_sun", "moon_figs", "moon_stag", "Iris", "Thaleia", "goddess"),
    StoryParams("reed_fawn", "reed_ford", "barley_loaf", "reed_heron", "Nysa", "Eirene", "goddess"),
    StoryParams("foxling", "bridge_of_wind", "honey_cakes", "storm_swallow", "Theron", "Maron", "god"),
    StoryParams("foxling", "reed_ford", "moon_figs", "reed_heron", "Lyra", "Lykos", "god"),
]


def explain_rejection(creature: Creature, task: Task, offering: Offering, boon: Boon) -> str:
    if not share_possible(offering):
        return (
            f"(No story: {offering.phrase} leaves no honest spare portion to share with the hungry stranger. "
            f"This myth needs generosity to cause the transformation.)"
        )
    if not can_reach_task(creature, task):
        return (
            f"(No story: a {creature.kind} in this world cannot even begin the road to {task.place}. "
            f"The hero must be able to reach the sacred challenge before the miracle changes the ending.)"
        )
    if not boon_fits_task(boon, task):
        return (
            f"(No story: {boon.title} does not solve the problem at {task.place}. "
            f"The transformed shape must grant a trait that truly fits the task.)"
        )
    return "(No story: this combination does not make a reasonable myth.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
shareable(O) :- offering(O), portions(O, P), P >= 2.
reachable(C, T) :- creature(C), task(T), approach(T, A), natural(C, A).
fits(B, T) :- boon(B), task(T), need(T, N), grants(B, N).

valid(C, T, O, B) :- creature(C), task(T), offering(O), boon(B),
                     shareable(O), reachable(C, T), fits(B, T).

outcome(happy) :- chosen_creature(C), chosen_task(T), chosen_offering(O), chosen_boon(B),
                  valid(C, T, O, B).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, c in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        for tr in sorted(c.natural_traits):
            lines.append(asp.fact("natural", cid, tr))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("need", tid, t.need))
        for ap in sorted(t.approach):
            lines.append(asp.fact("approach", tid, ap))
    for oid, o in OFFERINGS.items():
        lines.append(asp.fact("offering", oid))
        lines.append(asp.fact("portions", oid, o.portions))
    for bid, b in BOONS.items():
        lines.append(asp.fact("boon", bid))
        for g in sorted(b.grants):
            lines.append(asp.fact("grants", bid, g))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_creature", params.creature),
        asp.fact("chosen_task", params.task),
        asp.fact("chosen_offering", params.offering),
        asp.fact("chosen_boon", params.boon),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "none"


def asp_verify() -> int:
    rc = 0
    a_set, p_set = set(asp_valid_combos()), set(valid_combos())
    if a_set == p_set:
        print(f"OK: gate matches valid_combos() ({len(a_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if a_set - p_set:
            print("  only in clingo:", sorted(a_set - p_set))
        if p_set - a_set:
            print("  only in python:", sorted(p_set - a_set))

    smoke_cases = list(CURATED)
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: generate() smoke test succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for params in smoke_cases:
        if asp_outcome(params) != "happy":
            rc = 1
            print(f"MISMATCH: ASP did not derive a happy outcome for {params}")
            break
    else:
        print(f"OK: ASP derives happy outcome for {len(smoke_cases)} curated stories.")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Myth storyworld: a small creature, a sacred task, a generous transformation."
    )
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--boon", choices=BOONS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.creature and args.task and args.offering and args.boon:
        c = CREATURES[args.creature]
        t = TASKS[args.task]
        o = OFFERINGS[args.offering]
        b = BOONS[args.boon]
        if not valid_combo(c, t, o, b):
            raise StoryError(explain_rejection(c, t, o, b))

    combos = [
        c for c in valid_combos()
        if (args.creature is None or c[0] == args.creature)
        and (args.task is None or c[1] == args.task)
        and (args.offering is None or c[2] == args.offering)
        and (args.boon is None or c[3] == args.boon)
    ]
    if not combos:
        if args.creature and args.task and args.offering and args.boon:
            c = CREATURES[args.creature]
            t = TASKS[args.task]
            o = OFFERINGS[args.offering]
            b = BOONS[args.boon]
            raise StoryError(explain_rejection(c, t, o, b))
        raise StoryError("(No valid combination matches the given options.)")

    creature, task, offering, boon = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(NAMES)
    guide_name, guide_type = rng.choice(GUIDES)
    return StoryParams(creature, task, offering, boon, hero_name, guide_name, guide_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        CREATURES[params.creature],
        TASKS[params.task],
        OFFERINGS[params.offering],
        BOONS[params.boon],
        hero_name=params.hero_name,
        guide_name=params.guide_name,
        guide_type=params.guide_type,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (creature, task, offering, boon) combos:\n")
        for c, t, o, b in combos:
            print(f"  {c:10} {t:14} {o:12} {b}")
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
            header = f"### {p.hero_name}: {p.creature} -> {p.boon} for {p.task}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
