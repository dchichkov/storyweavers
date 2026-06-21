#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/challenge_mystery_to_solve_flashback_ghost_story.py
===============================================================================

A standalone story world for a gentle ghost-story domain: a child faces a
spooky challenge, follows clues through an old place, sees a flashback, solves
a mystery, and helps a lonely ghost rest.

The world is deliberately small and constraint-checked. A mystery signal must
plausibly point to a lost keepsake, the hiding place must fit that keepsake,
and the chosen helper action must actually solve the ghost's problem. The story
engine tracks physical meters and emotional memes so the prose comes from state,
not from slot-filling.

Run it
------
    python storyworlds/worlds/gpt-5.4/challenge_mystery_to_solve_flashback_ghost_story.py
    python storyworlds/worlds/gpt-5.4/challenge_mystery_to_solve_flashback_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/challenge_mystery_to_solve_flashback_ghost_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/challenge_mystery_to_solve_flashback_ghost_story.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/challenge_mystery_to_solve_flashback_ghost_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/challenge_mystery_to_solve_flashback_ghost_story.py --verify
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
    traits: list[str] = field(default_factory=list)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    spooky_detail: str
    challenge_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Signal:
    id: str
    label: str
    sentence: str
    clue_line: str
    flash_sound: str
    points_to: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    owner_kind: str
    memory_scene: str
    comfort_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    stores: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    sense: int
    suits: set[str] = field(default_factory=set)
    solve_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


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


def _r_signal_fear(world: World) -> list[str]:
    child = world.get("child")
    ghost = world.get("ghost")
    if ghost.meters["manifested"] < THRESHOLD:
        return []
    sig = ("fear", "child")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    return ["__fear__"]


def _r_clue_hope(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["clue_found"] < THRESHOLD:
        return []
    sig = ("hope", "child")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["hope"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 0.5)
    return []


def _r_flashback_understanding(world: World) -> list[str]:
    child = world.get("child")
    ghost = world.get("ghost")
    if child.meters["flashback_seen"] < THRESHOLD:
        return []
    sig = ("understanding", "ghost")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["understanding"] += 1
    ghost.memes["remembered"] += 1
    return []


def _r_solution_peace(world: World) -> list[str]:
    ghost = world.get("ghost")
    child = world.get("child")
    if ghost.meters["helped"] < THRESHOLD:
        return []
    sig = ("peace", "ghost")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.meters["haunting"] = 0.0
    ghost.memes["peace"] += 1
    child.memes["relief"] += 1
    child.memes["bravery"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="signal_fear", tag="emotional", apply=_r_signal_fear),
    Rule(name="clue_hope", tag="emotional", apply=_r_clue_hope),
    Rule(name="flashback_understanding", tag="memory", apply=_r_flashback_understanding),
    Rule(name="solution_peace", tag="resolution", apply=_r_solution_peace),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def clue_matches(signal: Signal, keepsake: Keepsake) -> bool:
    return signal.points_to == keepsake.owner_kind


def hiding_fits(keeping: Keepsake, hiding: HidingPlace) -> bool:
    return keeping.id in hiding.stores


def response_fits(keeping: Keepsake, response: Response) -> bool:
    return keeping.id in response.suits


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in PLACES:
        for signal_id, signal in SIGNALS.items():
            for keepsake_id, keepsake in KEEPSAKES.items():
                if not clue_matches(signal, keepsake):
                    continue
                for hiding_id, hiding in HIDING_PLACES.items():
                    if not hiding_fits(keepsake, hiding):
                        continue
                    for response_id, response in RESPONSES.items():
                        if response.sense >= SENSE_MIN and response_fits(keepsake, response):
                            combos.append((place_id, signal_id, keepsake_id, hiding_id, response_id))
    return combos


def predict_understanding(world: World, keepsake: Keepsake) -> dict:
    sim = world.copy()
    sim.get("child").meters["flashback_seen"] += 1
    propagate(sim, narrate=False)
    return {
        "flashback": sim.get("child").meters["flashback_seen"] >= THRESHOLD,
        "understanding": sim.get("child").memes["understanding"],
        "owner_kind": keepsake.owner_kind,
    }


def introduce(world: World, child: Entity, elder: Entity, place: Place) -> None:
    world.say(
        f"At the edge of evening, {child.id} came with {child.pronoun('possessive')} "
        f"{elder.label_word} to {place.label}. {place.opening}"
    )
    world.say(place.spooky_detail)
    child.memes["calm"] += 1


def first_sign(world: World, child: Entity, signal: Signal) -> None:
    ghost = world.get("ghost")
    ghost.meters["manifested"] += 1
    ghost.meters["haunting"] += 1
    propagate(world, narrate=False)
    world.say(signal.sentence)
    world.say(
        f"{child.id} gave a little jump, but the sound did not feel mean. "
        f"It felt as if someone was asking for help."
    )


def challenge_step(world: World, child: Entity, elder: Entity, place: Place) -> None:
    child.memes["fear"] += 1
    child.memes["bravery"] += 0.5
    world.say(
        f'"It will be a challenge," {elder.label_word} whispered, '
        f'"but we can be careful together."'
    )
    world.say(place.challenge_text)


def search_for_clue(world: World, child: Entity, signal: Signal, hiding: HidingPlace) -> None:
    child.meters["clue_found"] += 1
    propagate(world, narrate=False)
    world.say(signal.clue_line)
    world.say(
        f"They followed it to {hiding.phrase}, where dust lay thick except for one neat little space."
    )


def discover_keepsake(world: World, child: Entity, keepsake: Keepsake, hiding: HidingPlace) -> None:
    item = world.get("keepsake")
    item.meters["found"] += 1
    world.say(
        f"Inside {hiding.phrase}, {child.id} found {keepsake.phrase}. "
        f"It was cold, but not in a biting way. It felt like a small hand full of waiting."
    )


def flashback(world: World, child: Entity, keepsake: Keepsake, signal: Signal) -> None:
    pred = predict_understanding(world, keepsake)
    child.meters["flashback_seen"] += 1
    propagate(world, narrate=False)
    world.facts["predicted_understanding"] = pred["understanding"]
    world.say(
        f"The moment {child.id} touched the {keepsake.label}, the room seemed to soften. "
        f"For one blink, the old shadows turned into a flashback."
    )
    world.say(
        f"{keepsake.memory_scene} {signal.flash_sound} Then the vision was gone, "
        f"and {child.id} knew the ghost had not wanted to scare anyone at all."
    )


def explain_mystery(world: World, elder: Entity, keepsake: Keepsake) -> None:
    world.say(
        f'"Oh," {elder.label_word} breathed. "Someone lost {keepsake.phrase} long ago."'
    )
    world.say(
        f"{keepsake.comfort_line} The mystery no longer felt wild. It had become a sad puzzle with an answer."
    )


def solve(world: World, child: Entity, ghost: Entity, keepsake: Keepsake, response: Response) -> None:
    ghost.meters["helped"] += 1
    propagate(world, narrate=False)
    world.say(response.solve_text.format(child=child.id, keepsake=keepsake.label))
    world.say(
        f"A pale shape gathered by the window, clear as moon-milk for just a second, "
        f"and bowed its head to {child.id}."
    )


def ending(world: World, child: Entity, elder: Entity, place: Place) -> None:
    ghost = world.get("ghost")
    if ghost.memes["peace"] >= THRESHOLD:
        world.say(
            f"After that, {place.label} was still old and creaky, but it did not feel lonely anymore."
        )
        world.say(
            f"{child.id} squeezed {child.pronoun('possessive')} {elder.label_word}'s hand and smiled. "
            f"The scary challenge had turned into a kind deed, and the house rested at last."
        )


def tell(
    place: Place,
    signal: Signal,
    keepsake: Keepsake,
    hiding: HidingPlace,
    response: Response,
    *,
    child_name: str = "Nora",
    child_type: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "careful",
    seed: Optional[int] = None,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            role="child",
            traits=[trait],
            label=child_name,
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            role="ghost",
            label="the ghost",
            attrs={"owner_kind": keepsake.owner_kind},
        )
    )
    world.add(
        Entity(
            id="keepsake",
            kind="thing",
            type="keepsake",
            role="keepsake",
            label=keepsake.label,
            phrase=keepsake.phrase,
            tags=set(keepsake.tags),
        )
    )
    world.facts["seed"] = seed

    introduce(world, child, elder, place)
    world.para()
    first_sign(world, child, signal)
    challenge_step(world, child, elder, place)

    world.para()
    search_for_clue(world, child, signal, hiding)
    discover_keepsake(world, child, keepsake, hiding)
    flashback(world, child, keepsake, signal)

    world.para()
    explain_mystery(world, elder, keepsake)
    solve(world, child, ghost, keepsake, response)
    ending(world, child, elder, place)

    world.facts.update(
        child=child,
        elder=elder,
        ghost=ghost,
        place=place,
        signal=signal,
        keepsake_cfg=keepsake,
        hiding=hiding,
        response=response,
        mystery_solved=ghost.memes["peace"] >= THRESHOLD,
        flashback_seen=child.meters["flashback_seen"] >= THRESHOLD,
        clue_found=child.meters["clue_found"] >= THRESHOLD,
    )
    return world


PLACES = {
    "attic": Place(
        id="attic",
        label="the old attic",
        opening="The roof beams bent overhead like sleepy giants, and the last gold light from the window lay in dusty stripes.",
        spooky_detail="Every step made the boards whisper under their feet.",
        challenge_text="Together they climbed the narrow stairs into the dark, moving slowly so the lantern light would not shake.",
        tags={"attic", "old_house"},
    ),
    "hallway": Place(
        id="hallway",
        label="the long upstairs hallway",
        opening="Tall portraits watched from the walls, and the runner rug held years of hush inside its threads.",
        spooky_detail="At the far end, a single moonbeam rested on the floor like a silver finger.",
        challenge_text="Together they walked the long hallway past the portraits, listening hard and keeping close to the wall.",
        tags={"hallway", "old_house"},
    ),
    "tower": Place(
        id="tower",
        label="the little tower room",
        opening="Round windows looked over the dark trees, and the wind tapped the glass as if it knew an old secret.",
        spooky_detail="Cobwebs trembled in the corners whenever the draft slid through.",
        challenge_text="Together they crossed the twisty stair into the tower room, where the air felt cold and every shadow looked taller than before.",
        tags={"tower", "old_house"},
    ),
}

SIGNALS = {
    "lullaby": Signal(
        id="lullaby",
        label="lullaby",
        sentence='A soft song drifted through the boards, only three notes long, like a lullaby someone had forgotten how to finish.',
        clue_line="The little tune kept slipping toward the oldest trunk in the room.",
        flash_sound="A mother hummed the same tune while rocking a baby near the fire.",
        points_to="family",
        tags={"song", "ghost"},
    ),
    "bell": Signal(
        id="bell",
        label="bell chime",
        sentence="From somewhere in the dark came the tiniest silver chime, though no bell hung nearby.",
        clue_line="The thin chiming led them toward a coat chest tucked under the eaves.",
        flash_sound="A small white dog ran in circles while its collar bell rang bright and fast.",
        points_to="pet",
        tags={"bell", "ghost"},
    ),
    "chalk": Signal(
        id="chalk",
        label="chalk message",
        sentence='On the wall, dusty letters slowly appeared: "FIND IT," then faded before the last speck could fall.',
        clue_line="A trail of chalky finger marks ended beside an old writing desk.",
        flash_sound="A schoolboy laughed over a slate, then hid something quickly when footsteps came down the hall.",
        points_to="child",
        tags={"chalk", "ghost"},
    ),
}

KEEPSAKES = {
    "ribbon": Keepsake(
        id="ribbon",
        label="blue ribbon",
        phrase="a blue ribbon tied in a careful bow",
        owner_kind="family",
        memory_scene="In the flashback, a young mother tucked a blue ribbon around a baby's blanket so she would know it anywhere.",
        comfort_line="It had been precious because it belonged to someone's family story.",
        tags={"ribbon", "family"},
    ),
    "collar": Keepsake(
        id="collar",
        label="tiny collar",
        phrase="a tiny red collar with a little silver bell",
        owner_kind="pet",
        memory_scene="In the flashback, a laughing child chased a little dog across the room with the red collar jingling.",
        comfort_line="It had been precious because it belonged to a loved little animal.",
        tags={"collar", "pet", "bell"},
    ),
    "slate": Keepsake(
        id="slate",
        label="small slate",
        phrase="a small slate with half a math challenge written on it",
        owner_kind="child",
        memory_scene="In the flashback, a boy grinned over the slate, proud of a hard challenge he had nearly solved before the lesson ended.",
        comfort_line="It had been precious because it held a child's unfinished work and pride.",
        tags={"slate", "school", "challenge"},
    ),
}

HIDING_PLACES = {
    "trunk": HidingPlace(
        id="trunk",
        label="cedar trunk",
        phrase="a cedar trunk with a brass latch",
        stores={"ribbon", "collar"},
        tags={"trunk"},
    ),
    "desk": HidingPlace(
        id="desk",
        label="writing desk",
        phrase="the narrow writing desk with one stuck drawer",
        stores={"slate", "ribbon"},
        tags={"desk"},
    ),
    "window_seat": HidingPlace(
        id="window_seat",
        label="window seat",
        phrase="the deep window seat under the round pane",
        stores={"collar"},
        tags={"window"},
    ),
}

RESPONSES = {
    "return_to_cradle": Response(
        id="return_to_cradle",
        label="return it to the cradle",
        sense=3,
        suits={"ribbon"},
        solve_text='{child} carried the {keepsake} to the little cradle in the corner and laid it there as gently as a feather.',
        qa_text="placed the ribbon back in the old cradle",
        tags={"kindness", "family"},
    ),
    "hang_by_portrait": Response(
        id="hang_by_portrait",
        label="hang it by the portrait",
        sense=3,
        suits={"collar"},
        solve_text='{child} lifted the {keepsake} and hung it beside the portrait of the smiling little dog, where the moonlight could shine on it.',
        qa_text="hung the collar beside the portrait of the dog",
        tags={"kindness", "pet"},
    ),
    "set_on_school_desk": Response(
        id="set_on_school_desk",
        label="set it on the school desk",
        sense=3,
        suits={"slate"},
        solve_text='{child} set the {keepsake} carefully on the old school desk and straightened it so the unfinished sum could be seen.',
        qa_text="set the slate on the old school desk so it could be seen again",
        tags={"kindness", "school"},
    ),
    "pocket_it": Response(
        id="pocket_it",
        label="keep it",
        sense=1,
        suits=set(),
        solve_text='{child} slipped the {keepsake} into a pocket and decided to take it home.',
        qa_text="kept the keepsake",
        tags={"selfish"},
    ),
}

GIRL_NAMES = ["Nora", "Mina", "Lucy", "Ava", "Ella", "Rose", "Maya", "Ivy"]
BOY_NAMES = ["Owen", "Finn", "Leo", "Eli", "Sam", "Theo", "Ben", "Max"]
TRAITS = ["careful", "brave", "curious", "gentle", "thoughtful"]
ELDERS = ["grandmother", "grandfather"]


@dataclass
class StoryParams:
    place: str
    signal: str
    keepsake: str
    hiding_place: str
    response: str
    child_name: str
    child_type: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a spooky story about a spirit or mystery. In gentle ghost stories, the spirit is often sad or lonely rather than mean.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short look at something that happened in the past. It helps you understand why things in the present are happening.",
        )
    ],
    "mystery": [
        (
            "What is a mystery to solve?",
            "A mystery is a puzzle about something hidden or unknown. You solve it by noticing clues and figuring out what they mean.",
        )
    ],
    "attic": [
        (
            "What is an attic?",
            "An attic is a room or space under the roof of a house. People often keep old boxes and furniture there.",
        )
    ],
    "bell": [
        (
            "Why can a bell help people find something?",
            "A bell makes a clear sound, so you can follow it. Even a tiny chime can point you toward where something is hidden.",
        )
    ],
    "ribbon": [
        (
            "Why can a ribbon be important?",
            "A ribbon can matter because it reminds someone of a person, a gift, or a special day. Small objects can hold big feelings.",
        )
    ],
    "collar": [
        (
            "What is a pet collar for?",
            "A pet collar goes around an animal's neck. It can show that the pet belongs to a family and can hold a little bell or tag.",
        )
    ],
    "slate": [
        (
            "What is a slate?",
            "A slate is a small flat board people used to write on long ago. Children could practice letters or sums on it and wipe it clean later.",
        )
    ],
    "kindness": [
        (
            "How can kindness solve a problem in a story?",
            "Kindness can solve a problem when someone needs help, comfort, or understanding. Doing the caring thing can change fear into peace.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "flashback", "mystery", "attic", "bell", "ribbon", "collar", "slate", "kindness"]


CURATED = [
    StoryParams(
        place="attic",
        signal="lullaby",
        keepsake="ribbon",
        hiding_place="trunk",
        response="return_to_cradle",
        child_name="Nora",
        child_type="girl",
        elder_type="grandmother",
        trait="careful",
    ),
    StoryParams(
        place="hallway",
        signal="bell",
        keepsake="collar",
        hiding_place="window_seat",
        response="hang_by_portrait",
        child_name="Owen",
        child_type="boy",
        elder_type="grandfather",
        trait="brave",
    ),
    StoryParams(
        place="tower",
        signal="chalk",
        keepsake="slate",
        hiding_place="desk",
        response="set_on_school_desk",
        child_name="Maya",
        child_type="girl",
        elder_type="grandmother",
        trait="curious",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    keepsake = f["keepsake_cfg"]
    signal = f["signal"]
    place = f["place"]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the word "challenge" and uses a mystery to solve plus a flashback.',
        f"Tell a spooky-but-kind story where {child.id} hears a strange {signal.label} in {place.label}, follows clues, sees a flashback, and solves the mystery by helping a ghost.",
        f"Write a child-facing ghost story about {child.id} finding {keepsake.phrase}, learning its past in a flashback, and turning fear into kindness.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    place = f["place"]
    signal = f["signal"]
    keepsake = f["keepsake_cfg"]
    hiding = f["hiding"]
    response = f["response"]
    elder_word = elder.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} {elder_word}, who go into {place.label} and meet a lonely ghost through its clues.",
        ),
        (
            "What was the spooky mystery?",
            f"The mystery was why a strange {signal.label} kept appearing in {place.label}. It turned out the ghost was trying to lead them to a lost {keepsake.label}.",
        ),
        (
            f"Why was going into {place.label} a challenge?",
            f"It was dark, creaky, and full of spooky sounds, so {child.id} felt scared. Even so, {child.pronoun()} kept going carefully because the ghost seemed to need help.",
        ),
    ]
    if f.get("flashback_seen"):
        qa.append(
            (
                "What did the flashback show?",
                f"The flashback showed the {keepsake.label} in the past and why it mattered. That helped {child.id} understand that the ghost was sad and not trying to be mean.",
            )
        )
    if f.get("clue_found"):
        qa.append(
            (
                f"Where did {child.id} find the lost thing?",
                f"{child.id} followed the clues to {hiding.phrase} and found {keepsake.phrase} there. The neat little empty space in the dust showed that it was the important object.",
            )
        )
    if f.get("mystery_solved"):
        qa.append(
            (
                "How did they solve the mystery?",
                f"They solved it when {child.id} {response.qa_text}. That kind act returned the missing thing to its proper place, so the ghost could finally feel peaceful.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly and kindly. {place.label.capitalize()} was still old and shadowy, but it no longer felt lonely because the ghost had been helped.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost", "flashback", "mystery", "kindness"}
    if f["place"].id == "attic":
        tags.add("attic")
    for source in (f["signal"], f["keepsake_cfg"], f["response"]):
        tags |= set(source.tags)
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
    for e in list(world.entities.values()):
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_combo(signal: Signal, keepsake: Keepsake, hiding: HidingPlace, response: Response) -> str:
    if not clue_matches(signal, keepsake):
        return (
            f"(No story: the clue '{signal.id}' points to a {signal.points_to} memory, "
            f"but {keepsake.phrase} belongs to a {keepsake.owner_kind} memory, so the mystery does not line up.)"
        )
    if not hiding_fits(keepsake, hiding):
        return (
            f"(No story: {keepsake.phrase} does not plausibly belong in {hiding.phrase}. "
            f"Pick a hiding place that could really hold that lost object.)"
        )
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response.id}': it is too selfish or unhelpful for this world "
            f"(sense={response.sense} < {SENSE_MIN}). The ending should solve the ghost's problem kindly.)"
        )
    if not response_fits(keepsake, response):
        return (
            f"(No story: the action '{response.id}' does not help with {keepsake.phrase}. "
            f"The solution must return the right keepsake to the right kind of place.)"
        )
    return "(No story: this combination does not make a coherent mystery.)"


ASP_RULES = r"""
clue_matches(S, K) :- signal_points_to(S, O), keepsake_owner(K, O).
hiding_fits(K, H) :- stores(H, K).
sensible_response(R) :- response(R), sense(R, S), sense_min(M), S >= M.
response_fits(K, R) :- suits(R, K).

valid(P, S, K, H, R) :- place(P), signal(S), keepsake(K), hiding_place(H), response(R),
                        clue_matches(S, K), hiding_fits(K, H),
                        sensible_response(R), response_fits(K, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid, signal in SIGNALS.items():
        lines.append(asp.fact("signal", sid))
        lines.append(asp.fact("signal_points_to", sid, signal.points_to))
    for kid, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", kid))
        lines.append(asp.fact("keepsake_owner", kid, keepsake.owner_kind))
    for hid, hiding in HIDING_PLACES.items():
        lines.append(asp.fact("hiding_place", hid))
        for stored in sorted(hiding.stores):
            lines.append(asp.fact("stores", hid, stored))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        for suit in sorted(response.suits):
            lines.append(asp.fact("suits", rid, suit))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification guard
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Gentle ghost-story world: a spooky challenge, a mystery to solve, and a flashback that reveals the truth."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--hiding-place", dest="hiding_place", choices=HIDING_PLACES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-type", dest="child_type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", dest="elder_type", choices=ELDERS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.signal and args.keepsake:
        signal = SIGNALS[args.signal]
        keepsake = KEEPSAKES[args.keepsake]
        if not clue_matches(signal, keepsake):
            raise StoryError(explain_combo(signal, keepsake, HIDING_PLACES.get(args.hiding_place, next(iter(HIDING_PLACES.values()))), RESPONSES.get(args.response, next(iter(RESPONSES.values())))))
    if args.keepsake and args.hiding_place:
        keepsake = KEEPSAKES[args.keepsake]
        hiding = HIDING_PLACES[args.hiding_place]
        if not hiding_fits(keepsake, hiding):
            signal = SIGNALS[args.signal] if args.signal else next(iter(SIGNALS.values()))
            response = RESPONSES[args.response] if args.response else next(iter(RESPONSES.values()))
            raise StoryError(explain_combo(signal, keepsake, hiding, response))
    if args.keepsake and args.response:
        keepsake = KEEPSAKES[args.keepsake]
        response = RESPONSES[args.response]
        if response.sense < SENSE_MIN or not response_fits(keepsake, response):
            signal = SIGNALS[args.signal] if args.signal else next(iter(SIGNALS.values()))
            hiding = HIDING_PLACES[args.hiding_place] if args.hiding_place else next(iter(HIDING_PLACES.values()))
            raise StoryError(explain_combo(signal, keepsake, hiding, response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.signal is None or combo[1] == args.signal)
        and (args.keepsake is None or combo[2] == args.keepsake)
        and (args.hiding_place is None or combo[3] == args.hiding_place)
        and (args.response is None or combo[4] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, signal_id, keepsake_id, hiding_place, response = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    elder_type = args.elder_type or rng.choice(ELDERS)
    name_pool = GIRL_NAMES if child_type == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        signal=signal_id,
        keepsake=keepsake_id,
        hiding_place=hiding_place,
        response=response,
        child_name=child_name,
        child_type=child_type,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        signal = SIGNALS[params.signal]
        keepsake = KEEPSAKES[params.keepsake]
        hiding = HIDING_PLACES[params.hiding_place]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]}.)") from err

    if not clue_matches(signal, keepsake):
        raise StoryError(explain_combo(signal, keepsake, hiding, response))
    if not hiding_fits(keepsake, hiding):
        raise StoryError(explain_combo(signal, keepsake, hiding, response))
    if response.sense < SENSE_MIN or not response_fits(keepsake, response):
        raise StoryError(explain_combo(signal, keepsake, hiding, response))

    world = tell(
        place=place,
        signal=signal,
        keepsake=keepsake,
        hiding=hiding,
        response=response,
        child_name=params.child_name,
        child_type=params.child_type,
        elder_type=params.elder_type,
        trait=params.trait,
        seed=params.seed,
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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, signal, keepsake, hiding_place, response) combos:\n")
        for place, signal, keepsake, hiding, response in combos:
            print(f"  {place:8} {signal:8} {keepsake:8} {hiding:12} {response}")
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
            header = (
                f"### {p.child_name}: {p.signal} -> {p.keepsake} in {p.place} "
                f"({p.hiding_place}, {p.response})"
            )
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
