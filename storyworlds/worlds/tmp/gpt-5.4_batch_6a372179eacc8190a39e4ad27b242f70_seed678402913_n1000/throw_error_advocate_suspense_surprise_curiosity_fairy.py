#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/throw_error_advocate_suspense_surprise_curiosity_fairy.py
====================================================================================

A standalone story world for a small fairy-tale domain built from the seed words
"throw", "error", and "advocate".

Premise
-------
A curious child in an enchanted place finds a sealed fairy door. The child first
tries an impatient move and throws the wrong object, which wakes the door's red
error light and creates suspense. A kindly magical advocate speaks up for the
child, explains the true rule of the door, and helps make things right. The
surprise is that the door does not hide treasure at all, but a gentle wonder
meant to be shared.

World logic
-----------
Each enchanted door accepts one kind of gift:

* moon door   -> silver bell
* rose door   -> dew pearl
* seed door   -> acorn

Throwing a wrong item at the door produces an error glow and locks the latch.
A story is only valid when:
1) the place plausibly contains the chosen door,
2) the chosen wrong item is truly wrong for that door, and
3) the chosen advocate knows the right calming rhyme for that kind of door.

The advocate then guides the child to offer the correct gift gently instead of
throwing things, clearing the error and opening the door.

Run it
------
python storyworlds/worlds/gpt-5.4/throw_error_advocate_suspense_surprise_curiosity_fairy.py
python storyworlds/worlds/gpt-5.4/throw_error_advocate_suspense_surprise_curiosity_fairy.py --door moon --wrong acorn --advocate owl
python storyworlds/worlds/gpt-5.4/throw_error_advocate_suspense_surprise_curiosity_fairy.py --door seed --wrong acorn
python storyworlds/worlds/gpt-5.4/throw_error_advocate_suspense_surprise_curiosity_fairy.py --all --qa
python storyworlds/worlds/gpt-5.4/throw_error_advocate_suspense_surprise_curiosity_fairy.py --verify
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "fairy", "woman"}
        male = {"boy", "father", "king", "wizard", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    scene: str
    doors: set[str] = field(default_factory=set)
    surprise: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class DoorKind:
    id: str
    label: str
    phrase: str
    mark: str
    likes: str
    hint: str
    reveal: str
    accepted_gift: str
    places: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    soft: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class AdvocateKind:
    id: str
    label: str
    phrase: str
    title: str
    knows: set[str] = field(default_factory=set)
    arrival: str = ""
    comfort: str = ""
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_error_fear(world: World) -> list[str]:
    door = world.get("door")
    child = world.get("child")
    if door.meters["error"] < THRESHOLD:
        return []
    sig = ("error_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    child.memes["suspense"] += 1
    return ["__error__"]


def _r_open_relief(world: World) -> list[str]:
    door = world.get("door")
    child = world.get("child")
    adv = world.get("advocate")
    if door.meters["open"] < THRESHOLD:
        return []
    sig = ("open_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    adv.memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="error_fear", tag="emotional", apply=_r_error_fear),
    Rule(name="open_relief", tag="emotional", apply=_r_open_relief),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "glade": Place(
        id="glade",
        label="the moonlit glade",
        scene="At the edge of the moonlit glade, mushrooms shone like little lamps and fern tips held silver drops.",
        doors={"moon", "rose"},
        surprise="Behind it waited a round room full of sleeping fireflies in glass-free lantern flowers.",
        tags={"forest", "fairy"},
    ),
    "tower": Place(
        id="tower",
        label="the ivy tower garden",
        scene="In the ivy tower garden, the stones were warm, and vines curled around steps no one had climbed in years.",
        doors={"moon", "seed"},
        surprise="Behind it waited a tiny stair winding up to a window where the stars looked close enough to pat.",
        tags={"tower", "fairy"},
    ),
    "brook": Place(
        id="brook",
        label="the singing brook",
        scene="Beside the singing brook, the water made bright little songs against the roots of an old willow.",
        doors={"rose", "seed"},
        surprise="Behind it waited a hidden nook where teacups of petals sat ready on a mossy table.",
        tags={"brook", "fairy"},
    ),
}

DOORS = {
    "moon": DoorKind(
        id="moon",
        label="moon door",
        phrase="a little moon door set into a white stone",
        mark="a silver crescent",
        likes="soft ringing",
        hint="The carved crescent looked as if it were listening for a gentle chime.",
        reveal="the moon door swung inward with a pale blue glow",
        accepted_gift="bell",
        places={"glade", "tower"},
        tags={"moon", "door"},
    ),
    "rose": DoorKind(
        id="rose",
        label="rose door",
        phrase="a little rose door woven through with thornless vines",
        mark="a curled rosebud",
        likes="dew",
        hint="The rosebud carving held one hollow drop, as if it wanted a bead of dew.",
        reveal="the rose door sighed open and a warm pink light poured out",
        accepted_gift="pearl",
        places={"glade", "brook"},
        tags={"rose", "door"},
    ),
    "seed": DoorKind(
        id="seed",
        label="seed door",
        phrase="a little seed door tucked under thick roots",
        mark="a tiny oak leaf",
        likes="planting gifts",
        hint="The oak-leaf mark sat above a thumb-sized cup of soil.",
        reveal="the seed door clicked open, and green light twined around the latch",
        accepted_gift="acorn",
        places={"tower", "brook"},
        tags={"seed", "door"},
    ),
}

GIFTS = {
    "bell": Gift(
        id="bell",
        label="silver bell",
        phrase="a silver bell no bigger than a plum stone",
        soft=True,
        tags={"bell"},
    ),
    "pearl": Gift(
        id="pearl",
        label="dew pearl",
        phrase="a dew pearl cupped in a leaf",
        soft=True,
        tags={"pearl"},
    ),
    "acorn": Gift(
        id="acorn",
        label="golden acorn",
        phrase="a golden acorn from under the old oak",
        soft=True,
        tags={"acorn"},
    ),
}

ADVOCATES = {
    "owl": AdvocateKind(
        id="owl",
        label="owl advocate",
        phrase="an owl advocate in a velvet cap",
        title="Advocate Owl",
        knows={"moon", "seed"},
        arrival="Down from a branch drifted an owl with bright round eyes and a velvet cap.",
        comfort="\"Do not hide,\" said the owl. \"Curiosity can make a quick hand, but a quick hand can learn to be gentle.\"",
        tags={"owl", "advocate"},
    ),
    "fox": AdvocateKind(
        id="fox",
        label="fox advocate",
        phrase="a fox advocate with a fern-green sash",
        title="Advocate Fox",
        knows={"rose", "moon"},
        arrival="From behind a fern stepped a fox with neat paws and a fern-green sash.",
        comfort="\"Little hearts often hurry before they understand,\" said the fox softly. \"I will speak for you.\"",
        tags={"fox", "advocate"},
    ),
    "cricket": AdvocateKind(
        id="cricket",
        label="cricket advocate",
        phrase="a cricket advocate with a reed violin",
        title="Advocate Cricket",
        knows={"rose", "seed"},
        arrival="A cricket in a tiny cloak sprang onto a stone, carrying a reed violin under one arm.",
        comfort="\"An error is not the end of a story,\" sang the cricket. \"It is only the part where we listen better.\"",
        tags={"cricket", "advocate"},
    ),
}

GIRL_NAMES = ["Elin", "Mira", "Tansy", "Nella", "Poppy", "Wren"]
BOY_NAMES = ["Rowan", "Alder", "Pip", "Milo", "Bram", "Hollis"]
TRAITS = ["curious", "gentle", "bold", "patient", "wide-eyed", "hopeful"]


def correct_gift_for(door_id: str) -> str:
    return DOORS[door_id].accepted_gift


def door_fits_place(place_id: str, door_id: str) -> bool:
    return door_id in PLACES[place_id].doors and place_id in DOORS[door_id].places


def wrong_for_door(door_id: str, wrong_id: str) -> bool:
    return correct_gift_for(door_id) != wrong_id


def advocate_can_help(advocate_id: str, door_id: str) -> bool:
    return door_id in ADVOCATES[advocate_id].knows


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for door_id in DOORS:
            if not door_fits_place(place_id, door_id):
                continue
            for wrong_id in GIFTS:
                if not wrong_for_door(door_id, wrong_id):
                    continue
                for advocate_id in ADVOCATES:
                    if advocate_can_help(advocate_id, door_id):
                        combos.append((place_id, door_id, wrong_id, advocate_id))
    return combos


def explain_rejection(place_id: str, door_id: str, wrong_id: str, advocate_id: str) -> str:
    if not door_fits_place(place_id, door_id):
        return (
            f"(No story: {DOORS[door_id].label} does not belong in {PLACES[place_id].label}. "
            "Pick a door that fits the place.)"
        )
    if not wrong_for_door(door_id, wrong_id):
        return (
            f"(No story: {GIFTS[wrong_id].label} is the correct gift for the {DOORS[door_id].label}. "
            "This world needs a real mistake first, so choose a different wrong item.)"
        )
    if not advocate_can_help(advocate_id, door_id):
        return (
            f"(No story: {ADVOCATES[advocate_id].title} does not know the calming rhyme for the "
            f"{DOORS[door_id].label}. Pick an advocate who can truly help.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_error(world: World, thrown_id: str) -> dict:
    sim = world.copy()
    do_throw(sim, GIFTS[thrown_id], narrate=False)
    door = sim.get("door")
    return {
        "error": door.meters["error"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
    }


def do_throw(world: World, gift: Gift, narrate: bool = True) -> None:
    door = world.get("door")
    if gift.id == world.facts["correct_gift"].id:
        door.meters["open"] += 1
    else:
        door.meters["error"] += 1
        door.meters["locked"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity, place: Place, door: DoorKind) -> None:
    child.memes["curiosity"] += 1
    world.say(f"Once, in {place.label}, {child.id} wandered where only brave little feet and moths liked to go.")
    world.say(place.scene)
    world.say(
        f"There {child.pronoun()} found {door.phrase}. On it gleamed {door.mark}, "
        f"and {door.hint}"
    )


def wonder(world: World, child: Entity, door: DoorKind) -> None:
    world.say(
        f"{child.id} stood very still. {child.pronoun().capitalize()} was full of curiosity and wanted to know what slept behind the door."
    )
    world.say(
        f'Because fairy doors are never plain, {child.pronoun()} whispered, "What do you like, little door? Is it {door.likes} or moonbeams or secrets?"'
    )


def choose_wrong(world: World, child: Entity, wrong_gift: Gift) -> None:
    pred = predict_error(world, wrong_gift.id)
    world.facts["predicted_error"] = pred["error"]
    child.memes["impatience"] += 1
    world.say(
        f"Near the roots lay {wrong_gift.phrase}. {child.id} wondered if that might please the hidden latch."
    )
    world.say(
        f"But wanting to know at once can make a hand too quick. Instead of waiting, {child.id} decided to throw the {wrong_gift.label} at the shining mark."
    )


def error_beat(world: World, child: Entity, door: DoorKind, wrong_gift: Gift) -> None:
    do_throw(world, wrong_gift)
    world.say(
        f"The {wrong_gift.label} tapped the wood, and at once a red spark blinked above the latch."
    )
    world.say(
        f'Then a tiny bell inside the door rang three hard notes: "Error, error, error."'
    )
    world.say(
        f"{child.id}'s heart thumped. The {door.label} did not open. It only shivered and held itself tighter shut."
    )


def advocate_arrives(world: World, child: Entity, advocate: Entity, advocate_kind: AdvocateKind) -> None:
    child.memes["hope"] += 1
    world.say(advocate_kind.arrival)
    world.say(
        f"It was {advocate_kind.title}, the small kingdom's kind advocate for muddled children and startled doors."
    )
    world.say(advocate_kind.comfort)


def advocate_explains(world: World, child: Entity, advocate: Entity, door: DoorKind, correct_gift: Gift) -> None:
    child.memes["trust"] += 1
    world.say(
        f'{advocate_kind_name(advocate)} tilted {advocate.pronoun("possessive")} head and studied {door.mark}.'
    )
    world.say(
        f'"This is not a naughty door," {advocate.pronoun()} said. "It is a careful one. '
        f'It heard a throw when it was waiting for an offering."'
    )
    world.say(
        f'"The {door.label} opens for {correct_gift.label}, placed gently. '
        f'I will speak for you, if you are ready to try again with kinder hands."'
    )


def clear_error(world: World, child: Entity, advocate: Entity, correct_gift: Gift, door: DoorKind) -> None:
    door_ent = world.get("door")
    child.memes["care"] += 1
    advocate.memes["care"] += 1
    door_ent.meters["error"] = 0.0
    door_ent.meters["locked"] = 0.0
    world.say(
        f"{child.id} nodded. Together they found {correct_gift.phrase}."
    )
    world.say(
        f'Then {advocate_kind_name(advocate)} spoke to the latch: "Little door, this child made an error, '
        f'but not a cruel one. Open for honest wonder."'
    )
    world.say(
        f"{child.id} set the {correct_gift.label} by the mark instead of trying to throw anything at all."
    )
    do_throw(world, correct_gift)


def reveal(world: World, child: Entity, advocate: Entity, place: Place, door: DoorKind) -> None:
    world.say(f"At once, {door.reveal}.")
    world.say(
        "For half a breath, " + child.id + " expected heaps of gold or a crown of jewels."
    )
    world.say(
        f"But the surprise was sweeter than that. {place.surprise}"
    )
    world.say(
        f'{advocate_kind_name(advocate)} smiled. "Some fairy doors keep treasure," {advocate.pronoun()} said, '
        f'"and some keep wonder. Wonder is the better gift to share."'
    )
    world.say(
        f"So {child.id} went home shining inside, having learned that curiosity grows brightest when it is gentle."
    )


def advocate_kind_name(advocate: Entity) -> str:
    return advocate.attrs.get("title", advocate.id)


def tell(
    place: Place,
    door_kind: DoorKind,
    wrong_gift: Gift,
    advocate_kind: AdvocateKind,
    child_name: str = "Elin",
    child_gender: str = "girl",
    child_trait: str = "curious",
) -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[child_trait],
        label=child_name,
    ))
    advocate = world.add(Entity(
        id=advocate_kind.title,
        kind="character",
        type="creature",
        role="advocate",
        label=advocate_kind.label,
        attrs={"title": advocate_kind.title},
        tags=set(advocate_kind.tags),
    ))
    door = world.add(Entity(
        id="door",
        kind="thing",
        type="door",
        label=door_kind.label,
        phrase=door_kind.phrase,
        tags=set(door_kind.tags),
    ))

    correct = GIFTS[door_kind.accepted_gift]
    world.facts.update(
        place=place,
        door_kind=door_kind,
        wrong_gift=wrong_gift,
        advocate_kind=advocate_kind,
        correct_gift=correct,
        child=child,
        advocate=advocate,
        door=door,
        error_happened=False,
        opened=False,
    )

    introduce(world, child, place, door_kind)
    wonder(world, child, door_kind)

    world.para()
    choose_wrong(world, child, wrong_gift)
    error_beat(world, child, door_kind, wrong_gift)

    world.para()
    advocate_arrives(world, child, advocate, advocate_kind)
    advocate_explains(world, child, advocate, door_kind, correct)
    clear_error(world, child, advocate, correct, door_kind)

    world.para()
    reveal(world, child, advocate, place, door_kind)

    world.facts["error_happened"] = world.get("door").meters["open"] >= THRESHOLD
    world.facts["opened"] = world.get("door").meters["open"] >= THRESHOLD
    return world


KNOWLEDGE = {
    "advocate": [
        (
            "What is an advocate?",
            "An advocate is someone who speaks up to help another person be understood. A kind advocate tries to make things fair and calm."
        )
    ],
    "error": [
        (
            "What does error mean?",
            "An error is a mistake. It means something was done the wrong way, but it can often be fixed."
        )
    ],
    "moon": [
        (
            "Why do fairy tales use moon symbols?",
            "Moon symbols often make things feel quiet, magical, and a little mysterious. They are good for suspense because they hide things in silver light."
        )
    ],
    "rose": [
        (
            "Why is dew gentle?",
            "Dew is made of tiny drops of water resting softly on leaves and petals. Because it is light and careful, it fits gentle fairy magic."
        )
    ],
    "seed": [
        (
            "Why is an acorn a good seed gift?",
            "An acorn is a little beginning for a great oak tree. Fairy tales often use small seed gifts to show patience and growth."
        )
    ],
    "door": [
        (
            "Why are secret doors exciting in stories?",
            "A secret door makes readers wonder what is hidden behind it. That feeling of wondering is called curiosity."
        )
    ],
    "surprise": [
        (
            "What is a surprise ending?",
            "A surprise ending is when the story gives you something you did not expect. It feels best when the new thing still makes sense."
        )
    ],
}
KNOWLEDGE_ORDER = ["advocate", "error", "door", "moon", "rose", "seed", "surprise"]


@dataclass
class StoryParams:
    place: str
    door: str
    wrong: str
    advocate: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    door = f["door_kind"]
    advocate = f["advocate_kind"]
    wrong = f["wrong_gift"]
    correct = f["correct_gift"]
    place = f["place"]
    return [
        f'Write a short fairy tale for a 3-to-5-year-old that includes the words "throw", "error", and "advocate".',
        f"Tell a suspenseful but gentle fairy story where {child.id} finds a {door.label} in {place.label}, throws the wrong gift, and then gets help from {advocate.title}.",
        f"Write a curious fairy-tale story where a child makes an error with {wrong.label}, learns the right way with {correct.label}, and discovers a surprising wonder behind a secret door.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    door = f["door_kind"]
    advocate = f["advocate_kind"]
    wrong = f["wrong_gift"]
    correct = f["correct_gift"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious child, and {advocate.title}, who comes to help. They meet beside a secret {door.label} in {place.label}."
        ),
        (
            f"What made {child.id} curious?",
            f"{child.id} found {door.phrase} with {door.mark} on it and wanted to know what was behind it. The hidden door made the moment feel mysterious and full of suspense."
        ),
        (
            f"What error did {child.id} make?",
            f"{child.id} tried to throw the {wrong.label} at the door instead of offering the right gift gently. That made the latch ring out 'Error' and shut itself tighter."
        ),
        (
            f"How did the advocate help?",
            f"{advocate.title} spoke kindly for {child.id} and explained what the door truly needed. Then the advocate helped {child.id} try again with gentle hands instead of a throw."
        ),
        (
            f"What opened the {door.label} in the end?",
            f"The door opened when {child.id} placed the {correct.label} gently by the mark. It worked because that was the true gift the door was waiting for."
        ),
        (
            "What was the surprise behind the door?",
            f"It was not piles of treasure at all. {place.surprise}."
        ),
        (
            "What did the child learn?",
            f"{child.id} learned that curiosity is good, but quick hands can cause an error. The story ends by showing that wonder comes more easily when someone is gentle and listens."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"advocate", "error", "door", "surprise"}
    tags |= set(f["door_kind"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:16} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="glade",
        door="moon",
        wrong="acorn",
        advocate="owl",
        name="Elin",
        gender="girl",
        trait="curious",
    ),
    StoryParams(
        place="brook",
        door="rose",
        wrong="bell",
        advocate="fox",
        name="Rowan",
        gender="boy",
        trait="wide-eyed",
    ),
    StoryParams(
        place="tower",
        door="seed",
        wrong="pearl",
        advocate="owl",
        name="Mira",
        gender="girl",
        trait="hopeful",
    ),
    StoryParams(
        place="brook",
        door="seed",
        wrong="bell",
        advocate="cricket",
        name="Pip",
        gender="boy",
        trait="gentle",
    ),
    StoryParams(
        place="glade",
        door="rose",
        wrong="acorn",
        advocate="fox",
        name="Tansy",
        gender="girl",
        trait="patient",
    ),
]


ASP_RULES = r"""
door_fits_place(P, D) :- place(P), door(D), place_has(P, D), door_in_place(D, P).
wrong_for_door(D, W) :- door(D), gift(W), wants(D, C), C != W.
helpful(A, D) :- advocate(A), knows(A, D).
valid(P, D, W, A) :- door_fits_place(P, D), wrong_for_door(D, W), helpful(A, D).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for door_id in sorted(place.doors):
            lines.append(asp.fact("place_has", place_id, door_id))
    for door_id, door in DOORS.items():
        lines.append(asp.fact("door", door_id))
        lines.append(asp.fact("wants", door_id, door.accepted_gift))
        for place_id in sorted(door.places):
            lines.append(asp.fact("door_in_place", door_id, place_id))
    for gift_id in GIFTS:
        lines.append(asp.fact("gift", gift_id))
    for advocate_id, advocate in ADVOCATES.items():
        lines.append(asp.fact("advocate", advocate_id))
        for door_id in sorted(advocate.knows):
            lines.append(asp.fact("knows", advocate_id, door_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child makes a magical error at a fairy door, and a kind advocate helps put it right."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--door", choices=DOORS)
    ap.add_argument("--wrong", choices=GIFTS, help="the wrong gift that gets thrown first")
    ap.add_argument("--advocate", choices=ADVOCATES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches valid_combos() and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = args.place
    door_id = args.door
    wrong_id = args.wrong
    advocate_id = args.advocate

    if place_id and door_id and not door_fits_place(place_id, door_id):
        probe_wrong = wrong_id or next(iter(GIFTS))
        probe_adv = advocate_id or next(iter(ADVOCATES))
        raise StoryError(explain_rejection(place_id, door_id, probe_wrong, probe_adv))
    if door_id and wrong_id and not wrong_for_door(door_id, wrong_id):
        probe_place = place_id or next(iter(sorted(DOORS[door_id].places)))
        probe_adv = advocate_id or next(iter(ADVOCATES))
        raise StoryError(explain_rejection(probe_place, door_id, wrong_id, probe_adv))
    if door_id and advocate_id and not advocate_can_help(advocate_id, door_id):
        probe_place = place_id or next(iter(sorted(DOORS[door_id].places)))
        probe_wrong = wrong_id or next(g for g in GIFTS if wrong_for_door(door_id, g))
        raise StoryError(explain_rejection(probe_place, door_id, probe_wrong, advocate_id))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.door is None or c[1] == args.door)
        and (args.wrong is None or c[2] == args.wrong)
        and (args.advocate is None or c[3] == args.advocate)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, door_id, wrong_id, advocate_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        door=door_id,
        wrong=wrong_id,
        advocate=advocate_id,
        name=name,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.door not in DOORS:
        raise StoryError(f"(Unknown door: {params.door})")
    if params.wrong not in GIFTS:
        raise StoryError(f"(Unknown wrong gift: {params.wrong})")
    if params.advocate not in ADVOCATES:
        raise StoryError(f"(Unknown advocate: {params.advocate})")
    if not door_fits_place(params.place, params.door):
        raise StoryError(explain_rejection(params.place, params.door, params.wrong, params.advocate))
    if not wrong_for_door(params.door, params.wrong):
        raise StoryError(explain_rejection(params.place, params.door, params.wrong, params.advocate))
    if not advocate_can_help(params.advocate, params.door):
        raise StoryError(explain_rejection(params.place, params.door, params.wrong, params.advocate))

    world = tell(
        place=PLACES[params.place],
        door_kind=DOORS[params.door],
        wrong_gift=GIFTS[params.wrong],
        advocate_kind=ADVOCATES[params.advocate],
        child_name=params.name,
        child_gender=params.gender,
        child_trait=params.trait,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, door, wrong, advocate) combos:\n")
        for place_id, door_id, wrong_id, advocate_id in combos:
            print(f"  {place_id:6} {door_id:5} {wrong_id:5} {advocate_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for params in CURATED:
            samples.append(generate(params))
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
            header = f"### {p.name}: {p.door} door in {p.place} (wrong: {p.wrong}, advocate: {p.advocate})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
