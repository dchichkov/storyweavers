#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/defy_cheetah_inner_monologue_mystery_to_solve.py
============================================================================

A standalone storyworld for a fable-like tiny domain: a young cheetah faces a
small mystery on the savannah, feels the urge to defy a wiser elder, and learns
to slow down long enough to solve the puzzle. The world is built around three
seed features:

* Inner Monologue
* Mystery to Solve
* Repetition

The repeated wisdom of this world is:

    "Look twice, leap once."

A story can branch between a heedful path and a defiant path, but every valid
sample still reads like a complete fable: a puzzling beginning, a risky turn,
and an ending image that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/defy_cheetah_inner_monologue_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/defy_cheetah_inner_monologue_mystery_to_solve.py --mystery muddy_pool --choice defy
    python storyworlds/worlds/gpt-5.4/defy_cheetah_inner_monologue_mystery_to_solve.py --place termite_field --mystery missing_eggs
    python storyworlds/worlds/gpt-5.4/defy_cheetah_inner_monologue_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/defy_cheetah_inner_monologue_mystery_to_solve.py --verify
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

# Make shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MOTTO = "Look twice, leap once."


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
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "female", "lioness", "gazelle", "bird"}
        male = {"boy", "father", "uncle", "male", "lion", "monkey"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Domain configs
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    opening: str
    detail: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    question: str
    oddity: str
    worry: str
    culprit: str
    truth: str
    risk: str
    lesson: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    sight: str
    reveals: str
    wrong_guess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    type: str
    title: str
    style: str
    help_action: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World and rules
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_clue_reveals(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue_cfg")
    mystery = world.facts.get("mystery_cfg")
    if not clue or not mystery:
        return out
    scout = world.get("hero")
    if scout.meters["noticed_clue"] < THRESHOLD:
        return out
    sig = ("clue_reveals", clue.id, mystery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if clue.reveals == mystery.culprit:
        scout.memes["insight"] += 1
        world.facts["solved_by_clue"] = True
        out.append("__solved__")
    return out


def _r_haste_makes_trouble(world: World) -> list[str]:
    out: list[str] = []
    scout = world.get("hero")
    if scout.memes["haste"] < THRESHOLD:
        return out
    sig = ("haste", "hero")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    scout.memes["fear"] += 1
    scout.meters["dusty"] += 1
    out.append("__trouble__")
    return out


CAUSAL_RULES = [
    Rule(name="clue_reveals", tag="reasoning", apply=_r_clue_reveals),
    Rule(name="haste_makes_trouble", tag="emotion", apply=_r_haste_makes_trouble),
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
            if not sent.startswith("__"):
                world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def valid_combo(place_id: str, mystery_id: str, clue_id: str) -> bool:
    if place_id not in PLACES or mystery_id not in MYSTERIES or clue_id not in CLUES:
        return False
    place = PLACES[place_id]
    mystery = MYSTERIES[mystery_id]
    clue = CLUES[clue_id]
    return mystery_id in place.affords and clue.id == mystery.clue and clue.reveals == mystery.culprit


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for mystery_id in sorted(place.affords):
            mystery = MYSTERIES[mystery_id]
            clue = CLUES[mystery.clue]
            if valid_combo(place_id, mystery_id, clue.id):
                combos.append((place_id, mystery_id, clue.id))
    return combos


def outcome_of(choice: str) -> str:
    return "smooth" if choice == "heed" else "dusty"


def explain_rejection(place_id: str, mystery_id: str, clue_id: str) -> str:
    if place_id in PLACES and mystery_id in MYSTERIES and mystery_id not in PLACES[place_id].affords:
        return (f"(No story: {PLACES[place_id].label} does not fit the mystery "
                f"'{mystery_id}'. Pick a place where that odd sign could really appear.)")
    if mystery_id in MYSTERIES and clue_id in CLUES:
        mystery = MYSTERIES[mystery_id]
        clue = CLUES[clue_id]
        if clue.id != mystery.clue:
            return (f"(No story: '{clue.label}' is the wrong clue for '{mystery_id}'. "
                    f"This world only tells mysteries whose solution follows the real trace.)")
    return "(No story: that combination does not make a reasonable mystery.)"


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    clue: str
    guide: str
    choice: str
    name: str
    trait: str
    elder_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story screenplay
# ---------------------------------------------------------------------------
def inner_line(hero: Entity, text: str) -> str:
    return f'{hero.id} thought, "{text}"'


def observe_intro(world: World, hero: Entity, place: Place, mystery: Mystery, guide: Entity) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"In {place.label}, a young cheetah named {hero.id} padded through the grass at dawn. "
        f"{place.opening} {place.detail}"
    )
    world.say(
        f"Beside {hero.pronoun('object')} walked {guide.id}, {guide.attrs['title']}, "
        f"who always said, \"{MOTTO}\""
    )
    world.say(
        f"That morning, something was wrong: {mystery.oddity} {mystery.question}"
    )


def brood(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] += 1
    world.say(inner_line(hero, f"What happened here? {mystery.worry}"))
    world.say(inner_line(hero, "I am fast. I could guess at once."))
    world.say(inner_line(hero, f"But should I defy {world.get('guide').id} and leap before I know?"))


def guide_repeats(world: World, guide: Entity) -> None:
    guide.memes["patience"] += 1
    world.say(
        f'"{MOTTO}" {guide.id} said again. "{guide.attrs["style"]}"'
    )


def predict_haste(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.memes["haste"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": hero.memes["fear"],
        "dusty": hero.meters["dusty"],
    }


def choose_path(world: World, hero: Entity, guide: Entity, choice: str) -> None:
    forecast = predict_haste(world)
    world.facts["predicted_haste_fear"] = forecast["fear"]
    if choice == "defy":
        hero.memes["defiance"] += 1
        hero.memes["haste"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{inner_line(hero, "I will solve it first and prove that speed is enough.")} '
            f'Then {hero.id} decided to defy {guide.id} and sprang ahead.'
        )
    else:
        hero.memes["restraint"] += 1
        world.say(
            f'{inner_line(hero, "I want to race ahead, but quick paws are not the same as clear eyes.")} '
            f'{hero.id} breathed once, twice, and stayed beside {guide.id}.'
        )


def wrong_guess(world: World, hero: Entity, mystery: Mystery, clue: Clue) -> None:
    hero.memes["certainty"] += 1
    world.say(
        f"From far off, {hero.id} made a quick guess. \"It must be {clue.wrong_guess},\" "
        f"{hero.pronoun()} cried."
    )
    world.say(
        f"But a hidden root caught one paw, and {hero.pronoun()} slid in the dust. "
        f"{mystery.risk}"
    )


def inspect_clue(world: World, hero: Entity, guide: Entity, clue: Clue) -> None:
    hero.meters["noticed_clue"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{guide.id} did not scold. {guide.help_action} Together they looked closely and found "
        f"{clue.sight}"
    )
    world.say(inner_line(hero, f"That is not a wild guess. That is a sign. {MOTTO}"))


def solve(world: World, hero: Entity, guide: Entity, mystery: Mystery, clue: Clue) -> None:
    hero.memes["relief"] += 1
    hero.memes["wisdom"] += 1
    world.say(
        f'"Now I see," {hero.id} said. "{clue.label} means {mystery.truth}"'
    )
    world.say(
        f"They followed the sign and learned the truth: {mystery.truth} No monster had come at all."
    )
    if clue.reveals == "snake":
        world.say(
            "The cheetah and the elder bird carefully warned the weaver birds, who rebuilt higher up where the branches were safer."
        )
    elif clue.reveals == "buffalo":
        world.say(
            "Soon the herd moved on, and clear water slid back into the pool like a sheet of sky."
        )
    else:
        world.say(
            "Soon the young zebras trotted away laughing, and the reeds stood up again in the bright wind."
        )
    world.say(
        f'{guide.id} smiled. "\"{MOTTO}\""'
    )


def resolution(world: World, hero: Entity, guide: Entity, mystery: Mystery, choice: str) -> None:
    if choice == "defy":
        hero.memes["humility"] += 1
        world.say(
            f'{hero.id} bowed {hero.pronoun("possessive")} head. '
            f'"I was so eager to run that I nearly ran past the answer," {hero.pronoun()} said.'
        )
    else:
        world.say(
            f'{hero.id} lifted {hero.pronoun("possessive")} spotted face with a quiet smile. '
            f'"Today my paws were slower, but my mind was faster," {hero.pronoun()} said.'
        )
    world.say(
        f"From then on, whenever a puzzle stirred the grass, the young cheetah whispered, "
        f'"{MOTTO}" and looked before leaping.'
    )
    world.say(
        f"And that is why {mystery.lesson}"
    )


def tell(place: Place, mystery: Mystery, clue: Clue, guide_cfg: Guide,
         choice: str, name: str, trait: str, elder_name: str) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type="cheetah",
        label=name,
        phrase=f"a young cheetah named {name}",
        role="hero",
        traits=[trait],
    ))
    guide = world.add(Entity(
        id="guide",
        kind="character",
        type=guide_cfg.type,
        label=elder_name,
        phrase=f"{guide_cfg.title} {elder_name}",
        role="guide",
        attrs={"title": guide_cfg.title, "style": guide_cfg.style},
        tags=set(guide_cfg.tags),
    ))
    world.add(Entity(id="place", type="place", label=place.label))
    world.facts.update(
        hero=hero,
        guide=guide,
        place_cfg=place,
        mystery_cfg=mystery,
        clue_cfg=clue,
        guide_cfg=guide_cfg,
        choice=choice,
    )

    observe_intro(world, hero, place, mystery, guide)
    brood(world, hero, mystery)

    world.para()
    guide_repeats(world, guide)
    choose_path(world, hero, guide, choice)

    world.para()
    if choice == "defy":
        wrong_guess(world, hero, mystery, clue)
    inspect_clue(world, hero, guide, clue)
    solve(world, hero, guide, mystery, clue)

    world.para()
    resolution(world, hero, guide, mystery, choice)

    world.facts.update(
        outcome=outcome_of(choice),
        solved=hero.memes["wisdom"] >= THRESHOLD,
        dusty=hero.meters["dusty"] >= THRESHOLD,
        culprit=mystery.culprit,
    )
    return _rename_entities_in_story(world, name, elder_name)


def _rename_entities_in_story(world: World, hero_name: str, elder_name: str) -> World:
    text = world.render().replace("hero", hero_name).replace("guide", elder_name)
    world.paragraphs = [[p] for p in text.split("\n\n")]
    world.get("hero").id = hero_name
    world.entities[hero_name] = world.entities.pop("hero")
    world.get("guide").id = elder_name
    world.entities[elder_name] = world.entities.pop("guide")
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "acacia_pool": Place(
        id="acacia_pool",
        label="the acacia pool",
        opening="A bent acacia tree leaned over a round pool",
        detail="Normally bee-eaters chattered there, but the morning sounded thin and watchful.",
        affords={"muddy_pool"},
        tags={"savannah", "water"},
    ),
    "termite_field": Place(
        id="termite_field",
        label="the termite field",
        opening="Red towers of baked earth stood like little castles",
        detail="The weaver nests above them usually swung and sang in the wind.",
        affords={"missing_eggs"},
        tags={"savannah", "birds"},
    ),
    "reed_bend": Place(
        id="reed_bend",
        label="the reed bend",
        opening="A stream curled through tall green reeds",
        detail="The grass there loved to whisper every secret except the one for today.",
        affords={"trampled_reeds"},
        tags={"savannah", "reeds"},
    ),
}

MYSTERIES = {
    "muddy_pool": Mystery(
        id="muddy_pool",
        question="Why was the pool brown when it had shone blue the day before?",
        oddity="the pool was churned to brown soup and the little birds would not land",
        worry="Did some terrible beast stir the whole watering place?",
        culprit="buffalo",
        truth="a heavy buffalo herd had wallowed there before sunrise",
        risk="Dust flew into the young cheetah's eyes, and for a moment the muddy bank felt as tricky as a trap.",
        lesson="clear seeing runs farther than quick guessing.",
        clue="wide_tracks",
        tags={"water", "tracks"},
    ),
    "missing_eggs": Mystery(
        id="missing_eggs",
        question="Why did the weaver birds circle and cry above one torn nest?",
        oddity="one nest hung open and the tiny eggs were gone",
        worry="Had some sky-shadow snatched them away?",
        culprit="snake",
        truth="a long tree snake had climbed softly in the night",
        risk="A thorny branch scratched the young cheetah's shoulder, and the rustle below sounded larger than it truly was.",
        lesson="even a swift heart must make room for patient eyes.",
        clue="shed_skin",
        tags={"birds", "nest"},
    ),
    "trampled_reeds": Mystery(
        id="trampled_reeds",
        question="Why were the reeds bent flat in a bright circle?",
        oddity="the reeds were pressed down and water drops still trembled on them",
        worry="Had a striped river spirit slept there?",
        culprit="zebra_foals",
        truth="young zebra foals had rolled and played there at dawn",
        risk="The slippery bank nearly tipped the young cheetah nose-first into the stream.",
        lesson="a calm mind can untangle what frightened feet only scatter.",
        clue="small_hoofprints",
        tags={"reeds", "tracks"},
    ),
}

CLUES = {
    "wide_tracks": Clue(
        id="wide_tracks",
        label="wide, moon-shaped tracks",
        sight="wide, moon-shaped tracks pressed deep around the bank",
        reveals="buffalo",
        wrong_guess="a river monster",
        tags={"tracks", "buffalo"},
    ),
    "shed_skin": Clue(
        id="shed_skin",
        label="a strip of pale shed skin",
        sight="a strip of pale shed skin caught on the bark",
        reveals="snake",
        wrong_guess="a hawk from the clouds",
        tags={"skin", "snake"},
    ),
    "small_hoofprints": Clue(
        id="small_hoofprints",
        label="a ring of tiny hoofprints",
        sight="a ring of tiny hoofprints, light and playful, all around the bent reeds",
        reveals="zebra_foals",
        wrong_guess="a river spirit",
        tags={"tracks", "zebra"},
    ),
}

GUIDES = {
    "hornbill": Guide(
        id="hornbill",
        type="bird",
        title="Old Hornbill",
        style="Sharp eyes can do what sharp claws cannot.",
        help_action="Old Hornbill hopped to a lower branch and tapped the ground with a patient beak.",
        tags={"bird", "elder"},
    ),
    "tortoise": Guide(
        id="tortoise",
        type="tortoise",
        title="Aunt Tortoise",
        style="The ground tells its tale to anyone who kneels long enough.",
        help_action="Aunt Tortoise lowered herself near the earth and pointed with one careful claw.",
        tags={"tortoise", "elder"},
    ),
}

CHEETAH_NAMES = ["Kito", "Piri", "Suri", "Tamu", "Lela", "Nia", "Rani", "Miro"]
TRAITS = ["swift", "eager", "bright", "restless", "curious"]
ELDER_NAMES = {
    "hornbill": ["Baba Beak", "Grey Wing", "High Perch"],
    "tortoise": ["Aunt Tula", "Old Moss", "Round Shell"],
}

CURATED = [
    StoryParams(
        place="acacia_pool",
        mystery="muddy_pool",
        clue="wide_tracks",
        guide="tortoise",
        choice="heed",
        name="Kito",
        trait="swift",
        elder_name="Aunt Tula",
    ),
    StoryParams(
        place="termite_field",
        mystery="missing_eggs",
        clue="shed_skin",
        guide="hornbill",
        choice="defy",
        name="Lela",
        trait="eager",
        elder_name="Grey Wing",
    ),
    StoryParams(
        place="reed_bend",
        mystery="trampled_reeds",
        clue="small_hoofprints",
        guide="tortoise",
        choice="defy",
        name="Miro",
        trait="curious",
        elder_name="Old Moss",
    ),
    StoryParams(
        place="termite_field",
        mystery="missing_eggs",
        clue="shed_skin",
        guide="hornbill",
        choice="heed",
        name="Nia",
        trait="bright",
        elder_name="Baba Beak",
    ),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "cheetah": [
        ("What is special about a cheetah?",
         "A cheetah is famous for running very fast. But speed helps most when it is guided by careful choices."),
    ],
    "tracks": [
        ("What can animal tracks tell you?",
         "Tracks can show who walked by, how heavy they were, and sometimes whether they were calm or running. Careful eyes can read the ground like a book."),
    ],
    "buffalo": [
        ("Why might a buffalo make water muddy?",
         "A buffalo is heavy and can churn mud with its hooves when it stands or rolls in a pool. That stirs the bottom and turns clear water brown."),
    ],
    "snake": [
        ("What does a snake's shed skin mean?",
         "A snake sometimes leaves behind its old skin when it grows. Finding shed skin tells you a snake was there, even if it has already slipped away."),
    ],
    "zebra": [
        ("Why would zebra foals bend reeds?",
         "Young zebra foals play, roll, and race together. Their small hooves can press reeds flat without meaning any harm."),
    ],
    "patience": [
        ("Why is patience useful when solving a mystery?",
         "Patience gives your eyes and mind time to notice real clues. Quick guesses can feel exciting, but they often miss the truth."),
    ],
}
KNOWLEDGE_ORDER = ["cheetah", "tracks", "buffalo", "snake", "zebra", "patience"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place_cfg"]
    mystery = f["mystery_cfg"]
    choice = f["choice"]
    hero = world.get(next(eid for eid, e in world.entities.items() if e.role == "hero"))
    guide = world.get(next(eid for eid, e in world.entities.items() if e.role == "guide"))
    base = (
        f'Write a short fable for a 3-to-5-year-old about a young cheetah in {place.label} '
        f'who faces a mystery: {mystery.question}'
    )
    if choice == "defy":
        return [
            base + ". Include the word 'defy', inner monologue, and the repeated line 'Look twice, leap once.'",
            f"Tell a fable where {hero.id} wants to solve a puzzle by speed alone, tries to defy {guide.id}, and learns that clues matter more than guessing.",
            "Write a mystery-to-solve story with repetition and a gentle lesson: quick feet can outrun good judgment.",
        ]
    return [
        base + ". Include inner monologue and the repeated line 'Look twice, leap once.'",
        f"Tell a calm fable where {hero.id} listens to {guide.id}, studies the clues, and solves the mystery without rushing.",
        "Write a mystery-to-solve story that teaches children to pause, look carefully, and think before acting.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = world.get(next(eid for eid, e in world.entities.items() if e.role == "hero"))
    guide = world.get(next(eid for eid, e in world.entities.items() if e.role == "guide"))
    mystery = f["mystery_cfg"]
    clue = f["clue_cfg"]
    choice = f["choice"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young cheetah, and {guide.id}, the older helper who repeats, "
            f'"{MOTTO}" They face a small mystery together on the savannah.'
        ),
        (
            "What was the mystery?",
            f"The mystery was this: {mystery.question} At first the strange scene made it easy to imagine something much scarier than the truth."
        ),
        (
            f"What clue helped {hero.id} solve the mystery?",
            f"{hero.id} and {guide.id} found {clue.label}. That clue mattered because it pointed to {mystery.culprit.replace('_', ' ')}, which explained what had happened."
        ),
    ]
    if choice == "defy":
        qa.append(
            (
                f"How did {hero.id} try to defy {guide.id}, and what happened?",
                f"{hero.id} rushed ahead and made a quick guess before really looking. That brought a small scare and left {hero.pronoun('object')} dusty, because haste made the ground feel more dangerous than it was."
            )
        )
    else:
        qa.append(
            (
                f"Why did listening help {hero.id}?",
                f"Listening helped because {hero.id} stayed close enough to notice the real sign instead of chasing a frightening idea. The mystery became clear once careful looking replaced guessing."
            )
        )
    qa.append(
        (
            "What was the real answer to the mystery?",
            f"The real answer was that {mystery.truth} The clue matched that answer, so the ending feels earned instead of guessed."
        )
    )
    qa.append(
        (
            "What lesson did the cheetah learn?",
            f'{hero.id} learned that speed is useful, but not when it runs ahead of thought. By the end, {hero.pronoun()} repeats "{MOTTO}" because careful seeing solves more than wild guessing.'
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"cheetah", "patience"}
    clue = f["clue_cfg"]
    if "buffalo" in clue.tags:
        tags.add("buffalo")
    if "snake" in clue.tags:
        tags.add("snake")
    if "zebra" in clue.tags:
        tags.add("zebra")
    if "tracks" in clue.tags:
        tags.add("tracks")
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


# ---------------------------------------------------------------------------
# Trace / CLI helpers
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} culprit={world.facts.get('culprit')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(P, M, C) :- place(P), mystery(M), clue(C), affords(P, M), needed_clue(M, C), reveals(C, X), culprit(M, X).

smooth :- chosen_choice(heed).
dusty  :- chosen_choice(defy).
outcome(smooth) :- smooth.
outcome(dusty) :- dusty.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for mid in sorted(place.affords):
            lines.append(asp.fact("affords", pid, mid))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("culprit", mid, mystery.culprit))
        lines.append(asp.fact("needed_clue", mid, mystery.clue))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("reveals", cid, clue.reveals))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(choice: str) -> str:
    import asp
    model = asp.one_model(asp_program(f"chosen_choice({choice}).", "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    a_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if a_valid == p_valid:
        print(f"OK: ASP gate matches valid_combos() ({len(a_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if a_valid - p_valid:
            print("  only in ASP:", sorted(a_valid - p_valid))
        if p_valid - a_valid:
            print("  only in Python:", sorted(p_valid - a_valid))

    for choice in ["heed", "defy"]:
        a_out = asp_outcome(choice)
        p_out = outcome_of(choice)
        if a_out == p_out:
            print(f"OK: outcome for {choice} matches ({a_out}).")
        else:
            rc = 1
            print(f"MISMATCH: choice={choice} asp={a_out} python={p_out}")

    # Smoke tests for ordinary generation.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generated and emitted.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Fable storyworld: a young cheetah, a small mystery, and the choice to defy or listen."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--guide", choices=sorted(GUIDES))
    ap.add_argument("--choice", choices=["heed", "defy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--elder-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, mystery, clue) combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery and args.clue:
        if not valid_combo(args.place, args.mystery, args.clue):
            raise StoryError(explain_rejection(args.place, args.mystery, args.clue))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.clue is None or combo[2] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, mystery_id, clue_id = rng.choice(sorted(combos))
    guide_id = args.guide or rng.choice(sorted(GUIDES))
    choice = args.choice or rng.choice(["heed", "defy"])
    name = args.name or rng.choice(CHEETAH_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    elder_name = args.elder_name or rng.choice(ELDER_NAMES[guide_id])

    return StoryParams(
        place=place_id,
        mystery=mystery_id,
        clue=clue_id,
        guide=guide_id,
        choice=choice,
        name=name,
        trait=trait,
        elder_name=elder_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(Unknown mystery: {params.mystery})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.guide not in GUIDES:
        raise StoryError(f"(Unknown guide: {params.guide})")
    if params.choice not in {"heed", "defy"}:
        raise StoryError(f"(Unknown choice: {params.choice})")
    if not valid_combo(params.place, params.mystery, params.clue):
        raise StoryError(explain_rejection(params.place, params.mystery, params.clue))

    world = tell(
        place=PLACES[params.place],
        mystery=MYSTERIES[params.mystery],
        clue=CLUES[params.clue],
        guide_cfg=GUIDES[params.guide],
        choice=params.choice,
        name=params.name,
        trait=params.trait,
        elder_name=params.elder_name,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mystery, clue) combos:\n")
        for place_id, mystery_id, clue_id in combos:
            print(f"  {place_id:14} {mystery_id:16} {clue_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = f"### {p.name}: {p.mystery} at {p.place} ({p.choice})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
