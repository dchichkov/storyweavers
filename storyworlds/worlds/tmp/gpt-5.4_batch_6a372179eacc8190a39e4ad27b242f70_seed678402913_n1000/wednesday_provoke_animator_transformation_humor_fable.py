#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wednesday_provoke_animator_transformation_humor_fable.py
====================================================================================

A small storyworld about a boastful young animal, a patient village animator,
and a silly transformation on a Wednesday. It aims for a child-facing fable
shape: pride and teasing cause trouble; calm honesty fixes it.

The source tale imagined from the seed
--------------------------------------
On Wednesday, a vain little animal visits a village animator who makes moving
paper pictures. The child wants a grand poster and tries to provoke the
animator with rude teasing so the animator will draw something extra splendid.
Instead, the special ink answers the tease: the braggart begins to resemble the
boastful feature he demanded. The change is funny at first, then inconvenient.
Only by apologizing and accepting a modest drawing can the child return to normal.

World logic
-----------
This world models:
- typed entities with physical meters and emotional memes;
- a reasonableness gate over which boasts fit which animals;
- a simple outcome model:
    * if the teasing is mild, the animator simply teaches a lesson -> no magic mishap
    * if the teasing is sharp and the requested feature fits, the ink causes a funny
      partial transformation
    * if a helper remedy is strong enough, the change is washed / wiped / brushed away
- an inline ASP twin mirroring valid-combo and outcome checks.

Run it
------
    python storyworlds/worlds/gpt-5.4/wednesday_provoke_animator_transformation_humor_fable.py
    python storyworlds/worlds/gpt-5.4/wednesday_provoke_animator_transformation_humor_fable.py --animal fox --feature mane
    python storyworlds/worlds/gpt-5.4/wednesday_provoke_animator_transformation_humor_fable.py --animal turtle --feature antlers
    python storyworlds/worlds/gpt-5.4/wednesday_provoke_animator_transformation_humor_fable.py --all
    python storyworlds/worlds/gpt-5.4/wednesday_provoke_animator_transformation_humor_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4/wednesday_provoke_animator_transformation_humor_fable.py --verify
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
PROVOKE_MAGIC_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "vixen", "doe"}
        male = {"boy", "fox", "goat", "monkey", "turtle", "owl", "mole"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class AnimalCfg:
    id: str
    kind: str
    article: str
    style: str
    boast_feature: str
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)


@dataclass
class FeatureCfg:
    id: str
    label: str
    phrase: str
    wears_on: str
    fits: set[str] = field(default_factory=set)
    funny_line: str = ""
    inconvenient_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ProvokeCfg:
    id: str
    level: int
    tease: str
    nudge: str
    apology: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RemedyCfg:
    id: str
    power: int
    use_text: str
    fix_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    animal: str
    feature: str
    provoke: str
    remedy: str
    name: str
    animator_name: str
    day: str = "Wednesday"
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_embarrassment(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["transformed"] < THRESHOLD:
        return []
    sig = ("embarrassed", "hero")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["embarrassment"] += 1
    hero.memes["pride"] -= 1
    return ["__embarrassed__"]


CAUSAL_RULES = [
    Rule(name="embarrassment", tag="social", apply=_r_embarrassment),
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
        for item in produced:
            world.say(item)
    return produced


ANIMATORS = [
    "Mori the mole animator",
    "Otis the owl animator",
    "Pip the porcupine animator",
]

ANIMATOR_SHORT = {
    "Mori the mole animator": "Mori",
    "Otis the owl animator": "Otis",
    "Pip the porcupine animator": "Pip",
}

ANIMAL_NAMES = {
    "fox": ["Felix", "Rusty", "Fern"],
    "goat": ["Gus", "Pico", "Nell"],
    "monkey": ["Momo", "Bibi", "Tavi"],
    "turtle": ["Tuck", "Myrtle", "Pebbles"],
}

ANIMALS = {
    "fox": AnimalCfg(
        id="fox",
        kind="fox",
        article="a young fox",
        style="quick-footed and pleased with himself",
        boast_feature="mane",
        traits=["proud", "quick"],
        tags={"fox"},
    ),
    "goat": AnimalCfg(
        id="goat",
        kind="goat",
        article="a springy little goat",
        style="bouncy and noisy",
        boast_feature="antlers",
        traits=["proud", "bouncy"],
        tags={"goat"},
    ),
    "monkey": AnimalCfg(
        id="monkey",
        kind="monkey",
        article="a nimble little monkey",
        style="restless and fond of applause",
        boast_feature="tail_plume",
        traits=["proud", "playful"],
        tags={"monkey"},
    ),
    "turtle": AnimalCfg(
        id="turtle",
        kind="turtle",
        article="a careful young turtle",
        style="slow, neat, and secretly vain",
        boast_feature="shell_glitter",
        traits=["careful", "proud"],
        tags={"turtle"},
    ),
}

FEATURES = {
    "mane": FeatureCfg(
        id="mane",
        label="mane",
        phrase="a golden lion mane",
        wears_on="neck",
        fits={"fox"},
        funny_line="Soon a puff of golden fluff stood all around his neck, so wide that he sneezed when he turned.",
        inconvenient_line="The mane kept tickling his nose and bumping into the paper rack.",
        tags={"mane", "lion"},
    ),
    "antlers": FeatureCfg(
        id="antlers",
        label="antlers",
        phrase="a pair of grand antlers",
        wears_on="head",
        fits={"goat"},
        funny_line="Two curly antlers popped up and got tangled in the hanging flip-books.",
        inconvenient_line="Every proud nod made the antlers clack against the studio doorframe.",
        tags={"antlers", "deer"},
    ),
    "tail_plume": FeatureCfg(
        id="tail_plume",
        label="tail plume",
        phrase="a peacock-like tail plume",
        wears_on="tail",
        fits={"monkey"},
        funny_line="His tail unfurled into a bright fan so enormous that he turned in a slow, surprised circle to stare at it.",
        inconvenient_line="The tail plume swept ink pots, pencils, and one very shocked radish off a shelf.",
        tags={"tail", "peacock"},
    ),
    "shell_glitter": FeatureCfg(
        id="shell_glitter",
        label="sparkling shell",
        phrase="a shell bright with bouncing silver glitter",
        wears_on="shell",
        fits={"turtle"},
        funny_line="His shell flashed so brightly that the whole room winked when he moved.",
        inconvenient_line="The glitter made him look grand, but it also made every stool, broom, and doorknob notice him at once.",
        tags={"shell", "glitter"},
    ),
}

PROVOKES = {
    "tease": ProvokeCfg(
        id="tease",
        level=1,
        tease='said, "Perhaps an animator needs all week to draw one brave face."',
        nudge="It was rude, but still light enough to float away if nobody grabbed it.",
        apology='said, "I was showing off. I should not have teased you."',
        tags={"provoke", "tease"},
    ),
    "mock": ProvokeCfg(
        id="mock",
        level=2,
        tease='said, "If your paws are so slow, perhaps the picture will grow old before it can blink."',
        nudge="That was sharper, meant to provoke a laugh at the animator's expense.",
        apology='said, "I tried to provoke you, and the joke turned on me."',
        tags={"provoke", "mock"},
    ),
    "crow": ProvokeCfg(
        id="crow",
        level=3,
        tease='said, "Maybe I should flap the pages myself, since your whiskers seem too sleepy for real animation."',
        nudge="The words strutted out like a tiny parade of pride.",
        apology='said, "My tongue was louder than my wisdom, and I am sorry."',
        tags={"provoke", "boast"},
    ),
}

REMEDIES = {
    "wet_cloth": RemedyCfg(
        id="wet_cloth",
        power=2,
        use_text="took up a soft wet cloth and dabbed the bright ink before it could settle deeper",
        fix_text="The funny extra feature faded into a plain, honest face again",
        qa_text="dabbed the enchanted ink away with a wet cloth",
        tags={"cloth", "cleaning"},
    ),
    "mirror_lesson": RemedyCfg(
        id="mirror_lesson",
        power=1,
        use_text="held up a hand mirror and asked for one quiet look instead of one more loud word",
        fix_text="The change softened, but little traces still twinkled until the hero finished apologizing properly",
        qa_text="used a mirror and a calm lesson to soften the spell",
        tags={"mirror", "lesson"},
    ),
    "eraser_brush": RemedyCfg(
        id="eraser_brush",
        power=3,
        use_text="swirled the studio's eraser-brush in a neat silver circle over the blot of magic ink",
        fix_text="At once the borrowed boast slipped off and the hero looked like himself again",
        qa_text="brushed the magic away with the eraser-brush",
        tags={"brush", "magic"},
    ),
}


def feature_fits(animal_id: str, feature_id: str) -> bool:
    return animal_id in FEATURES[feature_id].fits


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for animal_id in ANIMALS:
        for feature_id in FEATURES:
            if feature_fits(animal_id, feature_id):
                combos.append((animal_id, feature_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    provoke = PROVOKES[params.provoke]
    remedy = REMEDIES[params.remedy]
    if provoke.level < PROVOKE_MAGIC_MIN:
        return "lesson"
    return "fixed" if remedy.power >= provoke.level else "lingers"


def predicted_magic(animal_id: str, feature_id: str, provoke_id: str) -> dict:
    return {
        "fits": feature_fits(animal_id, feature_id),
        "fires": PROVOKES[provoke_id].level >= PROVOKE_MAGIC_MIN and feature_fits(animal_id, feature_id),
    }


def introduce(world: World, hero: Entity, animator: Entity, animal_cfg: AnimalCfg) -> None:
    world.say(
        f"On Wednesday, {hero.id}, {animal_cfg.article} who was {animal_cfg.style}, skipped to the paper studio of {animator.id}, the village animator."
    )
    world.say(
        f"{animator.id} made little books whose pictures fluttered and seemed to walk when the pages were flipped fast."
    )


def desire(world: World, hero: Entity, feature: FeatureCfg) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} wanted a grand portrait with {feature.phrase}, because plain admiration no longer felt large enough to him."
    )


def studio_detail(world: World) -> None:
    world.say(
        "The studio smelled of paste, paper, and berry ink, and every shelf seemed full of blinking birds, prancing carrots, and dancing teapots drawn in tiny rows."
    )


def request_picture(world: World, hero: Entity, animator: Entity, feature: FeatureCfg) -> None:
    world.say(
        f'"Please draw me with {feature.phrase}," {hero.id} said. "{animator.id}, make me look like the champion of every lane and hill."'
    )


def provoke(world: World, hero: Entity, animator: Entity, provoke_cfg: ProvokeCfg, animal_id: str, feature_id: str) -> None:
    pred = predicted_magic(animal_id, feature_id, provoke_cfg.id)
    world.facts["predicted_magic"] = pred["fires"]
    hero.memes["provoking"] += 1
    world.say(f"But waiting felt slower than pride likes, so {hero.id} {provoke_cfg.tease}")
    world.say(provoke_cfg.nudge)
    if pred["fires"]:
        world.say(
            f"{animator.id} set down the brush and warned, \"In this room, boastful ink likes to answer boastful mouths.\""
        )


def animator_reply(world: World, animator: Entity) -> None:
    animator.memes["patience"] += 1
    world.say(
        f'{animator.id} only blinked once and said, "A lively picture is easier to draw than a peaceful heart."'
    )


def transform(world: World, hero: Entity, feature: FeatureCfg) -> None:
    hero.meters["transformed"] += 1
    hero.meters[feature.id] += 1
    hero.memes["shock"] += 1
    propagate(world, narrate=False)
    world.say(
        "Then a dot of bright ink hopped from the page, spun through the air, and landed exactly where the foolish wish belonged."
    )
    world.say(feature.funny_line)
    world.say(feature.inconvenient_line)


def no_magic_lesson(world: World, hero: Entity, animator: Entity, feature: FeatureCfg) -> None:
    hero.memes["embarrassment"] += 1
    world.say(
        f'{animator.id} did not use magic at all. Instead {animator.pronoun()} turned the paper around and sketched {hero.id} just as he was: bright eyes, quick paws, and no borrowed splendor.'
    )
    world.say(
        f'"That is enough for a good portrait," {animator.id} said. {hero.id} looked at the plain picture and felt his hot cheeks cool.'
    )


def remedy_apply(world: World, hero: Entity, animator: Entity, remedy: RemedyCfg, feature: FeatureCfg) -> None:
    world.say(
        f'{animator.id} {remedy.use_text}.'
    )
    if remedy.power >= PROVOKES[world.facts["provoke_cfg"].id].level:
        hero.meters["transformed"] = 0.0
        hero.meters[feature.id] = 0.0
        hero.memes["relief"] += 1
        world.say(remedy.fix_text + ".")
    else:
        hero.meters["transformed"] += 1
        hero.memes["worry"] += 1
        world.say(remedy.fix_text + ".")
        world.say(
            "Still, the room could see that the boast had not fully melted yet."
        )


def apology(world: World, hero: Entity, animator: Entity, provoke_cfg: ProvokeCfg) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f'At last {hero.id} bowed his head and {provoke_cfg.apology}'
    )
    world.say(
        f'{animator.id} nodded. "A clever tongue should not be used to provoke kindness," {animator.pronoun()} said.'
    )


def ending_fixed(world: World, hero: Entity, animator: Entity) -> None:
    hero.memes["humility"] += 1
    world.say(
        f"After that, {hero.id} chose a smaller portrait and smiled at it for a long time. It moved when the pages flipped, but the finest change was that his manners moved first."
    )
    world.say(
        f"So the village remembered this: on Wednesday or any other day, pride can make a joke, but only humility lets the joke end."
    )


def ending_lingers(world: World, hero: Entity, feature: FeatureCfg) -> None:
    hero.memes["humility"] += 1
    world.say(
        f"{hero.id} went home mostly himself, though one faint sign remained to remind him of the hour: a little shimmer, a tiny fluff, or a proud extra swish whenever he boasted too loudly."
    )
    world.say(
        f"So the village remembered this: whoever uses words to provoke for sport may wear the joke longer than expected."
    )


def tell(params: StoryParams) -> World:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.feature not in FEATURES:
        raise StoryError(f"(Unknown feature: {params.feature})")
    if params.provoke not in PROVOKES:
        raise StoryError(f"(Unknown provoke level: {params.provoke})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if not feature_fits(params.animal, params.feature):
        raise StoryError(explain_rejection(ANIMALS[params.animal], FEATURES[params.feature]))

    animal_cfg = ANIMALS[params.animal]
    feature = FEATURES[params.feature]
    provoke_cfg = PROVOKES[params.provoke]
    remedy = REMEDIES[params.remedy]

    world = World()
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=animal_cfg.kind,
            label=animal_cfg.kind,
            role="hero",
            traits=list(animal_cfg.traits),
            tags=set(animal_cfg.tags),
        )
    )
    animator = world.add(
        Entity(
            id=params.animator_name,
            kind="character",
            type="mole",
            label="animator",
            role="animator",
            traits=["patient", "crafty"],
            tags={"animator", "artist"},
        )
    )
    page = world.add(Entity(id="page", type="paper", label="portrait page"))
    ink = world.add(Entity(id="ink", type="ink", label="berry ink"))
    world.facts["provoke_cfg"] = provoke_cfg
    world.facts["animal_cfg"] = animal_cfg
    world.facts["feature_cfg"] = feature
    world.facts["remedy_cfg"] = remedy
    world.facts["hero"] = hero
    world.facts["animator"] = animator
    world.facts["day"] = params.day

    introduce(world, hero, animator, animal_cfg)
    desire(world, hero, feature)
    studio_detail(world)

    world.para()
    request_picture(world, hero, animator, feature)
    animator_reply(world, animator)
    provoke(world, hero, animator, provoke_cfg, params.animal, params.feature)

    world.para()
    current_outcome = outcome_of(params)
    if current_outcome == "lesson":
        no_magic_lesson(world, hero, animator, feature)
        apology(world, hero, animator, provoke_cfg)
        world.para()
        ending_fixed(world, hero, animator)
    else:
        transform(world, hero, feature)
        world.say(
            f'"Oh!" cried {hero.id}. "I only wanted to look grand on paper, not to wear my boasting in the middle of the room!"'
        )
        world.para()
        remedy_apply(world, hero, animator, remedy, feature)
        apology(world, hero, animator, provoke_cfg)
        world.para()
        if current_outcome == "fixed":
            ending_fixed(world, hero, animator)
        else:
            ending_lingers(world, hero, feature)

    world.facts.update(
        outcome=current_outcome,
        transformed=hero.meters["transformed"] >= THRESHOLD or PROVOKES[params.provoke].level >= PROVOKE_MAGIC_MIN,
        fully_restored=hero.meters["transformed"] < THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    feature = world.facts["feature_cfg"]
    animator = world.facts["animator"]
    outcome = world.facts["outcome"]
    prompts = [
        'Write a short fable for a 3-to-5-year-old that includes the words "Wednesday", "provoke", and "animator".',
        f"Tell a funny fable where {hero.id}, a little {hero.type}, visits an animator, boasts too much, and learns that rude teasing can change the whole day.",
        f"Write a child-facing story with a magical transformation involving {feature.phrase}, but end with a clear lesson about manners.",
    ]
    if outcome == "lingers":
        prompts.append(
            f"Make the ending gently cautionary: the animator helps, but a small trace of the silly transformation stays to remind {hero.id} not to provoke people for fun."
        )
    elif outcome == "lesson":
        prompts.append(
            f"Keep the magic light or absent: the animator teaches the lesson before the trouble grows."
        )
    else:
        prompts.append(
            f"Let the animator fix the funny transformation after an apology, so the ending feels warm and wise."
        )
    return prompts


KNOWLEDGE = {
    "animator": [
        (
            "What does an animator do?",
            "An animator makes pictures seem to move by changing them a little bit from one drawing to the next. When the pictures are shown in order, they can look alive."
        )
    ],
    "provoke": [
        (
            "What does provoke mean?",
            "To provoke someone means to poke at their feelings on purpose, trying to make them upset or make them react. It is not a kind way to use words."
        )
    ],
    "fable": [
        (
            "What is a fable?",
            "A fable is a short story, often with talking animals, that ends with a lesson about how to behave."
        )
    ],
    "mane": [
        (
            "What is a mane?",
            "A mane is a lot of long hair growing around an animal's neck, like on a lion."
        )
    ],
    "antlers": [
        (
            "What are antlers?",
            "Antlers are bony branches that grow on the heads of some animals, like deer."
        )
    ],
    "tail": [
        (
            "What is a tail plume?",
            "A tail plume is a tail with big fancy feathers or fluff spread out wide."
        )
    ],
    "glitter": [
        (
            "Why is glitter funny in a story?",
            "Glitter can be funny because it shines everywhere and sticks to everything, even when you did not mean it to."
        )
    ],
    "apology": [
        (
            "Why does saying sorry help?",
            "A real apology shows that you understand the hurt you caused and want to do better. It helps trust begin to mend."
        )
    ],
}
KNOWLEDGE_ORDER = ["fable", "animator", "provoke", "mane", "antlers", "tail", "glitter", "apology"]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    animator = world.facts["animator"]
    feature = world.facts["feature_cfg"]
    provoke_cfg = world.facts["provoke_cfg"]
    remedy = world.facts["remedy_cfg"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young {hero.type} who wanted to look grand, and {animator.id}, the patient animator in the paper studio."
        ),
        (
            f"Why did {hero.id} go to the animator on Wednesday?",
            f"{hero.id} wanted a portrait that looked especially splendid, with {feature.phrase}. That wish for extra praise is what brought him to the studio."
        ),
        (
            f"How did {hero.id} try to provoke the animator?",
            f"{hero.id} used teasing words instead of patient words. He was showing off and trying to hurry the animator by making a rude joke."
        ),
    ]
    if outcome == "lesson":
        qa.append(
            (
                "Did a magical transformation happen?",
                f"Not really. The animator stopped the trouble early, and {hero.id} felt embarrassed by the plain honest portrait instead. The lesson came before the magic could leap."
            )
        )
    else:
        qa.append(
            (
                f"What happened after {hero.id} tried to provoke {animator.id}?",
                f"The special ink answered the boast, and {hero.id} began to wear the very thing he had demanded. The change was funny at first, but it quickly became inconvenient."
            )
        )
        if outcome == "fixed":
            qa.append(
                (
                    f"How did {animator.id} fix the transformation?",
                    f"{animator.id} {remedy.qa_text}. That worked because the remedy was strong enough to undo the boastful magic."
                )
            )
        else:
            qa.append(
                (
                    f"Did the remedy fully fix {hero.id}?",
                    f"No. It helped, but a small trace remained. The boast had gone too far for that weaker remedy to clean away all at once."
                )
            )
    qa.append(
        (
            f"What did {hero.id} learn at the end?",
            f"{hero.id} learned that a clever tongue should not be used to provoke kind people. Pride made the joke begin, but humility was needed to end it."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"fable", "animator", "provoke", "apology"}
    feature = world.facts["feature_cfg"]
    if feature.id == "mane":
        tags.add("mane")
    elif feature.id == "antlers":
        tags.add("antlers")
    elif feature.id == "tail_plume":
        tags.add("tail")
    elif feature.id == "shell_glitter":
        tags.add("glitter")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        animal="fox",
        feature="mane",
        provoke="mock",
        remedy="wet_cloth",
        name="Felix",
        animator_name="Mori",
        day="Wednesday",
    ),
    StoryParams(
        animal="goat",
        feature="antlers",
        provoke="crow",
        remedy="mirror_lesson",
        name="Gus",
        animator_name="Otis",
        day="Wednesday",
    ),
    StoryParams(
        animal="monkey",
        feature="tail_plume",
        provoke="crow",
        remedy="eraser_brush",
        name="Momo",
        animator_name="Pip",
        day="Wednesday",
    ),
    StoryParams(
        animal="turtle",
        feature="shell_glitter",
        provoke="tease",
        remedy="mirror_lesson",
        name="Tuck",
        animator_name="Mori",
        day="Wednesday",
    ),
]


def explain_rejection(animal_cfg: AnimalCfg, feature_cfg: FeatureCfg) -> str:
    return (
        f"(No story: {feature_cfg.phrase} does not fit a {animal_cfg.kind} in this little world. "
        f"The transformation should exaggerate what the animal already longs to be, not attach a random boast.)"
    )


ASP_RULES = r"""
valid(A, F) :- animal(A), feature(F), fits(A, F).

magic(P) :- provoke(P), level(P, L), magic_min(M), L >= M.
fixed(P, R) :- magic(P), level(P, L), remedy(R), power(R, Pw), Pw >= L.
lingers(P, R) :- magic(P), level(P, L), remedy(R), power(R, Pw), Pw < L.

outcome(lesson) :- chosen_provoke(P), not magic(P).
outcome(fixed) :- chosen_provoke(P), chosen_remedy(R), fixed(P, R).
outcome(lingers) :- chosen_provoke(P), chosen_remedy(R), lingers(P, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for animal_id in ANIMALS:
        lines.append(asp.fact("animal", animal_id))
    for feature_id, feature in FEATURES.items():
        lines.append(asp.fact("feature", feature_id))
        for animal_id in sorted(feature.fits):
            lines.append(asp.fact("fits", animal_id, feature_id))
    for provoke_id, provoke in PROVOKES.items():
        lines.append(asp.fact("provoke", provoke_id))
        lines.append(asp.fact("level", provoke_id, provoke.level))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("power", remedy_id, remedy.power))
    lines.append(asp.fact("magic_min", PROVOKE_MAGIC_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_provoke", params.provoke),
        asp.fact("chosen_remedy", params.remedy),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: ASP valid combos match Python ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = []
    for params in cases:
        ao = asp_outcome(params)
        po = outcome_of(params)
        if ao != po:
            mismatches.append((params, ao, po))
    if not mismatches:
        print(f"OK: ASP outcomes match Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH in outcomes on {len(mismatches)} scenarios.")
        for params, ao, po in mismatches[:5]:
            print(f"  {params} -> asp={ao} python={po}")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a boastful animal, an animator, and a funny transformation. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--feature", choices=FEATURES)
    ap.add_argument("--provoke", choices=PROVOKES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--animator-name", dest="animator_name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (animal, feature) pairs from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal and args.feature and not feature_fits(args.animal, args.feature):
        raise StoryError(explain_rejection(ANIMALS[args.animal], FEATURES[args.feature]))

    combos = [
        combo for combo in valid_combos()
        if (args.animal is None or combo[0] == args.animal)
        and (args.feature is None or combo[1] == args.feature)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal_id, feature_id = rng.choice(sorted(combos))
    provoke_id = args.provoke or rng.choice(sorted(PROVOKES))
    remedy_id = args.remedy or rng.choice(sorted(REMEDIES))
    name = args.name or rng.choice(ANIMAL_NAMES[animal_id])
    animator_name = args.animator_name or rng.choice(sorted(ANIMATOR_SHORT.values()))
    return StoryParams(
        animal=animal_id,
        feature=feature_id,
        provoke=provoke_id,
        remedy=remedy_id,
        name=name,
        animator_name=animator_name,
        day="Wednesday",
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.feature not in FEATURES:
        raise StoryError(f"(Unknown feature: {params.feature})")
    if not feature_fits(params.animal, params.feature):
        raise StoryError(explain_rejection(ANIMALS[params.animal], FEATURES[params.feature]))
    if params.provoke not in PROVOKES:
        raise StoryError(f"(Unknown provoke level: {params.provoke})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")

    world = tell(params)
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (animal, feature) pairs:\n")
        for animal_id, feature_id in combos:
            print(f"  {animal_id:8} {feature_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.animal} wanting {p.feature} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
