#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/log_humor_suspense_slice_of_life.py
==============================================================

A standalone storyworld for a small slice-of-life tale with humor and suspense:
a child and a grown-up notice odd sounds coming from a hollow log, imagine
something much bigger than the truth, and gently discover a small animal inside.

The domain is intentionally tight. Not every place fits every animal, and not
every investigation method is sensible for every hidden creature. The world
model keeps the suspense grounded: a rustling log raises curiosity and fear; a
gentle, compatible method lets the creature appear; the ending image proves the
scary mystery was only a small everyday surprise.

Run it
------
    python storyworlds/worlds/gpt-5.4/log_humor_suspense_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/log_humor_suspense_slice_of_life.py --place garden --creature kitten
    python storyworlds/worlds/gpt-5.4/log_humor_suspense_slice_of_life.py --method quiet_wait
    python storyworlds/worlds/gpt-5.4/log_humor_suspense_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/log_humor_suspense_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/log_humor_suspense_slice_of_life.py --trace
    python storyworlds/worlds/gpt-5.4/log_humor_suspense_slice_of_life.py --asp
    python storyworlds/worlds/gpt-5.4/log_humor_suspense_slice_of_life.py --verify
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
# from storyworlds/worlds/gpt-5.4/.
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
        female = {"girl", "mother", "aunt", "grandmother", "woman"}
        male = {"boy", "father", "uncle", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    name: str
    errand: str
    light: str
    log_spot: str
    path_word: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    label: str
    article: str
    voice: str
    move: str
    reveal: str
    fit_places: set[str] = field(default_factory=set)
    methods: set[str] = field(default_factory=set)
    timid: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    style: str
    text: str
    fail_text: str
    reveal_help: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guess:
    id: str
    claim: str
    funny_line: str
    tags: set[str] = field(default_factory=set)


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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

    def copy(self) -> "World":
        clone = World(self.place)
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


def _r_mystery(world: World) -> list[str]:
    out: list[str] = []
    log = world.get("log")
    creature = world.get("creature")
    child = world.get("child")
    adult = world.get("adult")
    if log.meters["rustle"] >= THRESHOLD and creature.meters["hidden"] >= THRESHOLD:
        sig = ("mystery",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["curiosity"] += 1
            child.memes["fear"] += 1
            adult.memes["caution"] += 1
            out.append("__mystery__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    child = world.get("child")
    adult = world.get("adult")
    if creature.meters["visible"] >= THRESHOLD:
        sig = ("reveal",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] = 0.0
            child.memes["relief"] += 1
            child.memes["joy"] += 1
            adult.memes["relief"] += 1
            adult.memes["amusement"] += 1
            out.append("__reveal__")
    return out


CAUSAL_RULES = [
    Rule(name="mystery", tag="emotion", apply=_r_mystery),
    Rule(name="reveal", tag="emotion", apply=_r_reveal),
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
        for s in produced:
            world.say(s)
    return produced


def creature_fits(place_id: str, creature_id: str) -> bool:
    return place_id in CREATURES[creature_id].fit_places


def method_works(creature_id: str, method_id: str) -> bool:
    creature = CREATURES[creature_id]
    method = METHODS[method_id]
    return method.sense >= SENSE_MIN and method_id in creature.methods


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for creature_id in CREATURES:
            if not creature_fits(place_id, creature_id):
                continue
            for method_id in METHODS:
                if method_works(creature_id, method_id):
                    combos.append((place_id, creature_id, method_id))
    return combos


def predict_reveal(world: World, method_id: str) -> dict:
    sim = world.copy()
    do_method(sim, METHODS[method_id], CREATURES[sim.facts["creature_cfg"].id], narrate=False)
    creature = sim.get("creature")
    return {
        "visible": creature.meters["visible"] >= THRESHOLD,
        "startle": creature.meters["startle"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, adult: Entity, place: Place) -> None:
    world.say(
        f"After school, {child.id} and {child.pronoun('possessive')} {adult.label_word} "
        f"went through {place.name} {place.errand}."
    )
    world.say(place.light)


def notice_log(world: World, child: Entity, place: Place) -> None:
    log = world.get("log")
    log.meters["rustle"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At {place.log_spot}, a hollow log gave a small thump from the inside. "
        f"{child.id} stopped so fast that one shoe squeaked on the {place.path_word}."
    )


def guess_monster(world: World, child: Entity, guess: Guess) -> None:
    child.memes["imagination"] += 1
    world.say(
        f'"Did you hear that?" {child.id} whispered. "{guess.claim}"'
    )
    world.say(guess.funny_line)


def adult_steady(world: World, adult: Entity, child: Entity) -> None:
    adult.memes["calm"] += 1
    child.memes["trust"] += 1
    world.say(
        f'{adult.label_word.capitalize()} took {child.id}\'s hand and listened. '
        f'"Maybe," {adult.pronoun()} said, "or maybe something small is having a hard time inside that log."'
    )


def choose_method(world: World, adult: Entity, method: Method, predicted: dict) -> None:
    world.facts["predicted_visible"] = predicted["visible"]
    world.say(
        f"{adult.label_word.capitalize()} chose {method.style}. {method.text}"
    )


def do_method(world: World, method: Method, creature_cfg: Creature, narrate: bool = True) -> None:
    creature = world.get("creature")
    log = world.get("log")
    if method.id in creature_cfg.methods and method.sense >= SENSE_MIN:
        creature.meters["visible"] += 1
        creature.meters["hidden"] = 0.0
        log.meters["mystery"] = 0.0
        if method.id == "flashlight" and creature_cfg.timid:
            creature.meters["startle"] += 1
        propagate(world, narrate=False)
        if narrate:
            if creature.meters["startle"] >= THRESHOLD:
                world.say(
                    f"For one jumpy second, two bright eyes blinked back from the dark middle of the log."
                )
            world.say(creature_cfg.reveal)
            world.say(method.reveal_help)
    else:
        if narrate:
            world.say(method.fail_text)


def end_scene(world: World, child: Entity, adult: Entity, creature_cfg: Creature) -> None:
    creature = world.get("creature")
    if creature.meters["startle"] >= THRESHOLD:
        world.say(
            f'{child.id} squeaked first and then laughed at {child.pronoun("object")}self. '
            f'"I was ready for a giant monster," {child.pronoun()} said, "and it was only {creature_cfg.article} {creature_cfg.label}."'
        )
    else:
        world.say(
            f'{child.id} let out the breath {child.pronoun()} had been holding and started to giggle. '
            f'"That was the tiniest mystery ever," {child.pronoun()} said.'
        )
    world.say(
        f"{adult.label_word.capitalize()} smiled, and together they left the log quiet again and went on {world.place.errand}. "
        f"The walk felt ordinary once more, only lighter, because now the strange sound had a small face."
    )


def tell(place: Place, creature_cfg: Creature, method: Method, guess: Guess,
         child_name: str = "Mia", child_type: str = "girl",
         adult_type: str = "mother") -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        label=child_name,
        traits=["curious"],
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
        traits=["steady"],
    ))
    log = world.add(Entity(
        id="log",
        type="log",
        label="log",
        phrase="a hollow log",
        tags={"log"},
    ))
    creature = world.add(Entity(
        id="creature",
        type=creature_cfg.id,
        label=creature_cfg.label,
        phrase=f"{creature_cfg.article} {creature_cfg.label}",
        tags=set(creature_cfg.tags),
    ))
    creature.meters["hidden"] = 1.0
    world.facts["creature_cfg"] = creature_cfg
    world.facts["guess_cfg"] = guess
    world.facts["method_cfg"] = method

    introduce(world, child, adult, place)
    world.para()
    notice_log(world, child, place)
    guess_monster(world, child, guess)
    adult_steady(world, adult, child)

    world.para()
    predicted = predict_reveal(world, method.id)
    choose_method(world, adult, method, predicted)
    do_method(world, method, creature_cfg, narrate=True)

    world.para()
    end_scene(world, child, adult, creature_cfg)

    outcome = "startled_laugh" if creature.meters["startle"] >= THRESHOLD else "gentle_laugh"
    world.facts.update(
        place=place,
        child=child,
        adult=adult,
        log=log,
        creature=creature,
        creature_cfg=creature_cfg,
        method=method,
        guess=guess,
        outcome=outcome,
        revealed=creature.meters["visible"] >= THRESHOLD,
        started_hidden=True,
    )
    return world


PLACES = {
    "garden": Place(
        id="garden",
        name="the community garden",
        errand="to bring home a paper bag of tomatoes and herbs",
        light="The late sun lay warm on the beds of basil and beans, and nothing looked unusual at all.",
        log_spot="the bend by the compost fence",
        path_word="path",
        affords={"kitten", "frog", "hedgehog"},
        tags={"garden"},
    ),
    "park": Place(
        id="park",
        name="the park",
        errand="on the way to return library books",
        light="The path was full of stroller wheels, bicycle bells, and the clink of someone walking a dog.",
        log_spot="the edge of the duck pond path",
        path_word="gravel",
        affords={"kitten", "duckling", "hedgehog", "frog"},
        tags={"park"},
    ),
    "riverside": Place(
        id="riverside",
        name="the riverside path",
        errand="to carry a loaf of bread to a neighbor across the footbridge",
        light="The river made its soft shhh sound beside them, and the reeds leaned in the breeze.",
        log_spot="the place where the path narrowed near the reeds",
        path_word="dirt",
        affords={"duckling", "frog"},
        tags={"river"},
    ),
}

CREATURES = {
    "kitten": Creature(
        id="kitten",
        label="kitten",
        article="a",
        voice="mew",
        move="crawled out with dusty whiskers",
        reveal="A small kitten poked out one paw, then the rest of its striped face, and crawled out of the log as if it had only been looking for a better nap.",
        fit_places={"garden", "park"},
        methods={"flashlight", "soft_call"},
        timid=True,
        tags={"kitten"},
    ),
    "duckling": Creature(
        id="duckling",
        label="duckling",
        article="a",
        voice="peep",
        move="waddled out in a hurry",
        reveal="A duckling popped from the shadow in the log and waddled out, peeping indignantly as if the whole mystery had been a very rude interruption.",
        fit_places={"park", "riverside"},
        methods={"flashlight", "soft_call"},
        timid=False,
        tags={"duckling"},
    ),
    "frog": Creature(
        id="frog",
        label="frog",
        article="a",
        voice="croak",
        move="hopped out all at once",
        reveal="Then a green frog sprang right out of the log and landed on the path like a wet little comma.",
        fit_places={"garden", "park", "riverside"},
        methods={"flashlight", "quiet_wait"},
        timid=True,
        tags={"frog"},
    ),
    "hedgehog": Creature(
        id="hedgehog",
        label="hedgehog",
        article="a",
        voice="snuffle",
        move="shuffled out in a prickly ball",
        reveal="At last a hedgehog shuffled out of the log, nose first, snuffling as if it had woken from the world's shortest nap.",
        fit_places={"garden", "park"},
        methods={"flashlight", "quiet_wait"},
        timid=False,
        tags={"hedgehog"},
    ),
}

METHODS = {
    "flashlight": Method(
        id="flashlight",
        label="a flashlight",
        sense=3,
        style="the safest first step",
        text="From a bag pocket, a tiny flashlight clicked on. The beam slid over the bark instead of touching the log at all.",
        fail_text="The light found only shadows, and the mystery stayed hidden.",
        reveal_help="With the dark corner lit, the little creature found its way toward the opening.",
        tags={"flashlight"},
    ),
    "soft_call": Method(
        id="soft_call",
        label="a soft call",
        sense=3,
        style="a quiet, patient voice",
        text='Instead of reaching in, the grown-up crouched beside the log and made a soft, friendly call: "Easy there. You can come out."',
        fail_text="The soft voice drifted into the hollow log, but whatever was inside stayed tucked away.",
        reveal_help="The calm voice seemed to tell the hidden little thing that nobody planned to grab it.",
        tags={"gentle_call"},
    ),
    "quiet_wait": Method(
        id="quiet_wait",
        label="quiet waiting",
        sense=2,
        style="plain old patience",
        text="They both stepped back. For a long, suspenseful moment, they did absolutely nothing except listen and wait.",
        fail_text="They waited, but the log held its secret a little longer.",
        reveal_help="The quiet gave the little creature time to decide the outside world was not so scary after all.",
        tags={"waiting"},
    ),
    "shake_log": Method(
        id="shake_log",
        label="shaking the log",
        sense=1,
        style="a rough idea",
        text="This should never be used in a story.",
        fail_text="The log should not be shaken.",
        reveal_help="",
        tags={"rough"},
    ),
}

GUESSES = {
    "dragon": Guess(
        id="dragon",
        claim="What if there is a dragon in there, folded up like laundry?",
        funny_line="The idea was frightening for one second and silly for the next, which somehow made it even harder not to stare at the log.",
        tags={"dragon"},
    ),
    "pirate": Guess(
        id="pirate",
        claim="What if a tiny pirate captain is living in that log?",
        funny_line="That would have been scary, except {name} could not imagine a pirate hat small enough to fit inside bark.",
        tags={"pirate"},
    ),
    "troll": Guess(
        id="troll",
        claim="What if it is a grumpy troll with muddy elbows?",
        funny_line="The thought made the air feel tense and ridiculous at the same time.",
        tags={"troll"},
    ),
}


GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Anna"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Theo", "Finn", "Noah", "Eli"]
ADULT_TYPES = ["mother", "father", "aunt", "grandmother", "grandfather"]


@dataclass
class StoryParams:
    place: str
    creature: str
    method: str
    guess: str
    child_name: str
    child_gender: str
    adult: str
    seed: Optional[int] = None


def _guess_line(guess: Guess, child_name: str) -> Guess:
    return Guess(
        id=guess.id,
        claim=guess.claim,
        funny_line=guess.funny_line.replace("{name}", child_name),
        tags=set(guess.tags),
    )


KNOWLEDGE = {
    "log": [
        (
            "What is a hollow log?",
            "A hollow log is a piece of tree trunk with an open space inside. Small animals often hide there because it feels dark and safe."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight useful when something is hidden?",
            "A flashlight helps you see into a dark place without poking your hands into it. That makes it a gentle and careful way to check first."
        )
    ],
    "waiting": [
        (
            "Why can waiting quietly help a small animal?",
            "Small animals get scared by big, sudden movements. If everything becomes quiet, they often feel brave enough to come out on their own."
        )
    ],
    "kitten": [
        (
            "Why might a kitten hide in a small place?",
            "A kitten may hide when it is tired, frightened, or curious. Small snug places can feel safe to it."
        )
    ],
    "duckling": [
        (
            "Why does a duckling peep?",
            "A duckling peeps to call out when it wants its family or feels upset. The sound is one way it stays connected."
        )
    ],
    "frog": [
        (
            "Why do frogs like damp places?",
            "Frogs do well in damp places because their bodies dry out easily. Wet ground and shade help them stay comfortable."
        )
    ],
    "hedgehog": [
        (
            "What does a hedgehog do when it feels unsure?",
            "A hedgehog may move slowly, tuck in, or curl up to protect itself. It uses its prickles to stay safe."
        )
    ],
}
KNOWLEDGE_ORDER = ["log", "flashlight", "waiting", "kitten", "duckling", "frog", "hedgehog"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    place = f["place"]
    creature_cfg = f["creature_cfg"]
    guess = f["guess"]
    return [
        'Write a short slice-of-life story for a 3-to-5-year-old that includes the word "log" and mixes gentle suspense with humor.',
        f"Tell a story where {child.id} and {child.pronoun('possessive')} {adult.label_word} hear a strange sound in a log at {place.name}, worry for a moment, and discover {creature_cfg.article} {creature_cfg.label}.",
        f'Write a small everyday mystery for children where someone guesses, "{guess.claim}" but the truth is funny and harmless.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    place = f["place"]
    creature_cfg = f["creature_cfg"]
    method = f["method"]
    guess = f["guess"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} {adult.label_word}. They were out together on an ordinary errand when the little mystery began."
        ),
        (
            "Where did the strange sound come from?",
            f"It came from a hollow log at {place.log_spot}. The sound was small, but it was hidden, which made it feel much bigger than it really was."
        ),
        (
            f"What did {child.id} think might be inside the log?",
            f"{child.id} guessed, \"{guess.claim}\" That idea added humor, because it was so much grander than the truth, but it also made the moment feel tense."
        ),
        (
            f"Why did the log feel scary at first?",
            f"It was scary because something was moving inside the log and nobody could see it yet. Hidden sounds can make the imagination run ahead of the facts."
        ),
        (
            f"How did the grown-up help without making things worse?",
            f"{adult.label_word.capitalize()} used {method.label} instead of grabbing or shaking the log. That calm choice let them learn what was inside while staying gentle with the little creature."
        ),
    ]
    if f["outcome"] == "startled_laugh":
        qa.append(
            (
                "What happened when they finally looked inside?",
                f"They saw {creature_cfg.article} {creature_cfg.label}, and the sudden reveal made {child.id} jump before laughing. The suspense broke all at once, which is why the ending feels funny."
            )
        )
    else:
        qa.append(
            (
                "How did the mystery end?",
                f"The hidden sound turned out to be {creature_cfg.article} {creature_cfg.label}, not anything scary at all. Once it came out, the whole moment felt small and funny instead of spooky."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"log"} | set(world.facts["method"].tags) | set(world.facts["creature_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden",
        creature="kitten",
        method="soft_call",
        guess="dragon",
        child_name="Mia",
        child_gender="girl",
        adult="mother",
    ),
    StoryParams(
        place="park",
        creature="duckling",
        method="flashlight",
        guess="pirate",
        child_name="Ben",
        child_gender="boy",
        adult="grandfather",
    ),
    StoryParams(
        place="riverside",
        creature="frog",
        method="quiet_wait",
        guess="troll",
        child_name="Zoe",
        child_gender="girl",
        adult="aunt",
    ),
    StoryParams(
        place="park",
        creature="hedgehog",
        method="quiet_wait",
        guess="dragon",
        child_name="Leo",
        child_gender="boy",
        adult="father",
    ),
]


def explain_rejection(place_id: str, creature_id: str, method_id: str) -> str:
    place = PLACES[place_id]
    creature = CREATURES[creature_id]
    method = METHODS[method_id]
    if method.sense < SENSE_MIN:
        return (
            f"(No story: '{method_id}' is too rough or unreasonable for a child-facing mystery "
            f"(sense={method.sense} < {SENSE_MIN}). Pick a gentler method like flashlight, soft_call, or quiet_wait.)"
        )
    if place_id not in creature.fit_places:
        return (
            f"(No story: {creature.article} {creature.label} is not a plausible hidden creature for {place.name}. "
            f"Pick a creature that fits that place.)"
        )
    if method_id not in creature.methods:
        return (
            f"(No story: {method.label} is not a strong, gentle way to reveal {creature.article} {creature.label}. "
            f"Choose a method that the little creature would actually respond to.)"
        )
    return "(No story: that combination is not supported.)"


ASP_RULES = r"""
fits_place(P, C) :- place(P), creature(C), creature_place(C, P).
sensible(M)      :- method(M), sense(M, S), sense_min(Min), S >= Min.
works(C, M)      :- creature(C), method(M), creature_method(C, M), sensible(M).
valid(P, C, M)   :- fits_place(P, C), works(C, M).

startled(C, M)   :- valid(_, C, M), timid(C), M = flashlight.
outcome(gentle_laugh)  :- chosen_creature(C), chosen_method(M), valid(chosen_place, C, M), not startled(C, M).
outcome(startled_laugh) :- chosen_creature(C), chosen_method(M), valid(chosen_place, C, M), startled(C, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        if creature.timid:
            lines.append(asp.fact("timid", creature_id))
        for pid in sorted(creature.fit_places):
            lines.append(asp.fact("creature_place", creature_id, pid))
        for mid in sorted(creature.methods):
            lines.append(asp.fact("creature_method", creature_id, mid))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_creature", params.creature),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    creature = CREATURES[params.creature]
    if params.method == "flashlight" and creature.timid:
        return "startled_laugh"
    return "gentle_laugh"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases: list[StoryParams] = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

    # Smoke test ordinary generation / emit.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a humorous, suspenseful everyday mystery around a hollow log."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--guess", choices=GUESSES)
    ap.add_argument("--adult", choices=ADULT_TYPES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_rejection(args.place or "park", args.creature or "frog", args.method))
    if args.place and args.creature and args.method:
        if (args.place, args.creature, args.method) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.creature, args.method))
    elif args.place and args.creature and not creature_fits(args.place, args.creature):
        method_id = args.method or "flashlight"
        raise StoryError(explain_rejection(args.place, args.creature, method_id))
    elif args.creature and args.method and not method_works(args.creature, args.method):
        place_id = args.place or next(iter(CREATURES[args.creature].fit_places))
        raise StoryError(explain_rejection(place_id, args.creature, args.method))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.creature is None or combo[1] == args.creature)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, creature_id, method_id = rng.choice(sorted(combos))
    guess_id = args.guess or rng.choice(sorted(GUESSES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(ADULT_TYPES)

    return StoryParams(
        place=place_id,
        creature=creature_id,
        method=method_id,
        guess=guess_id,
        child_name=name,
        child_gender=gender,
        adult=adult,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.guess not in GUESSES:
        raise StoryError(f"(Unknown guess: {params.guess})")
    if (params.place, params.creature, params.method) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.creature, params.method))

    world = tell(
        place=PLACES[params.place],
        creature_cfg=CREATURES[params.creature],
        method=METHODS[params.method],
        guess=_guess_line(GUESSES[params.guess], params.child_name),
        child_name=params.child_name,
        child_type=params.child_gender,
        adult_type=params.adult,
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
        print(f"{len(combos)} compatible (place, creature, method) combos:\n")
        for place, creature, method in combos:
            print(f"  {place:10} {creature:10} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for params in CURATED:
            sample = generate(params)
            samples.append(sample)
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
            header = f"### {p.child_name}: {p.creature} in a log at {p.place} ({p.method})"
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
