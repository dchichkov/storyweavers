#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/projector_flipper_racoon_moral_value_friendship_reconciliation.py
=============================================================================================

A small mystery-flavored story world about a missing flipper, a humming projector,
and a racoon in the dark. The core shape is a friendship story: one child jumps
to the wrong conclusion, clues from the simulated world change what they believe,
and the ending proves reconciliation.

Run it
------
    python storyworlds/worlds/gpt-5.4/projector_flipper_racoon_moral_value_friendship_reconciliation.py
    python storyworlds/worlds/gpt-5.4/projector_flipper_racoon_moral_value_friendship_reconciliation.py --setting boathouse --culprit racoon
    python storyworlds/worlds/gpt-5.4/projector_flipper_racoon_moral_value_friendship_reconciliation.py --setting attic_hall --culprit racoon
    python storyworlds/worlds/gpt-5.4/projector_flipper_racoon_moral_value_friendship_reconciliation.py --all
    python storyworlds/worlds/gpt-5.4/projector_flipper_racoon_moral_value_friendship_reconciliation.py --qa --json
    python storyworlds/worlds/gpt-5.4/projector_flipper_racoon_moral_value_friendship_reconciliation.py --verify
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        animal = {"racoon"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    screen_place: str
    beam_line: str
    hiding_place: str
    outside_nearby: bool = False
    racoon_possible: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    kind: str
    motive: str
    reveal_line: str
    apology_target: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    name: str
    needs_outside: bool
    works_for: set[str]
    intro: str
    inspect: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    culprit: str
    clue: str
    friend1: str
    friend1_gender: str
    friend2: str
    friend2_gender: str
    owner: str
    owner_gender: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_hurt_feelings(world: World) -> list[str]:
    owner = world.entities.get("owner")
    friend = world.entities.get("friend")
    if owner is None or friend is None:
        return []
    if owner.memes["accused_friend"] < THRESHOLD:
        return []
    sig = ("hurt", owner.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["hurt"] += 1
    owner.memes["guilt_risk"] += 1
    return []


def _r_found_item_relief(world: World) -> list[str]:
    flipper = world.entities.get("flipper")
    owner = world.entities.get("owner")
    friend = world.entities.get("friend")
    if flipper is None or owner is None or friend is None:
        return []
    if flipper.attrs.get("location") != "found":
        return []
    sig = ("relief", flipper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["relief"] += 1
    friend.memes["relief"] += 1
    return []


def _r_apology_repairs(world: World) -> list[str]:
    owner = world.entities.get("owner")
    friend = world.entities.get("friend")
    if owner is None or friend is None:
        return []
    if owner.memes["apologized"] < THRESHOLD:
        return []
    sig = ("repair", owner.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    friend.memes["hurt"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="hurt_feelings", tag="social", apply=_r_hurt_feelings),
    Rule(name="found_item_relief", tag="emotional", apply=_r_found_item_relief),
    Rule(name="apology_repairs", tag="social", apply=_r_apology_repairs),
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
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "boathouse": Setting(
        id="boathouse",
        place="the lake boathouse",
        opening="The old lake boathouse smelled like rope, wet wood, and secrets.",
        screen_place="a white sheet pinned between two oars",
        beam_line="The projector hummed, and its pale beam made dust look like floating stars.",
        hiding_place="under a stack of life jackets",
        outside_nearby=True,
        racoon_possible=True,
        tags={"lake", "mystery"},
    ),
    "clubhouse": Setting(
        id="clubhouse",
        place="the little camp clubhouse",
        opening="The little camp clubhouse felt extra mysterious after sunset, as if every cupboard held a clue.",
        screen_place="a white wall beside the game shelf",
        beam_line="The projector hummed, and a bright square of light waited on the wall.",
        hiding_place="behind the costume trunk",
        outside_nearby=True,
        racoon_possible=True,
        tags={"camp", "mystery"},
    ),
    "attic_hall": Setting(
        id="attic_hall",
        place="the attic hall above the library",
        opening="The attic hall was full of trunks and old curtains, perfect for a mystery night.",
        screen_place="a clean curtain hanging by the window",
        beam_line="The projector hummed softly, but the dark room stayed still around it.",
        hiding_place="inside an old travel basket",
        outside_nearby=False,
        racoon_possible=False,
        tags={"indoors", "mystery"},
    ),
}

CULPRITS = {
    "racoon": Culprit(
        id="racoon",
        kind="animal",
        motive="liked the salty rubber smell and dragged the flipper away like a prize",
        reveal_line="A striped little racoon slipped across the beam with the missing flipper bumping behind it.",
        apology_target="friend",
        tags={"racoon", "animal"},
    ),
    "friend_helping": Culprit(
        id="friend_helping",
        kind="friend",
        motive="had hidden the flipper for a moment to tape a loose strap and make it safe again",
        reveal_line="The tape on the strap shone in the projector light, and the truth was suddenly plain.",
        apology_target="friend",
        tags={"friendship", "repair"},
    ),
}

CLUES = {
    "muddy_tracks": Clue(
        id="muddy_tracks",
        name="muddy tracks",
        needs_outside=True,
        works_for={"racoon"},
        intro="Near the door, something dark marked the floorboards.",
        inspect="When the children tilted the projector down, the bright light showed tiny muddy handprints and a tail sweep.",
        reveal="The prints led straight to the hiding place.",
        tags={"tracks", "projector"},
    ),
    "shadow_silhouette": Clue(
        id="shadow_silhouette",
        name="shadow silhouette",
        needs_outside=False,
        works_for={"racoon"},
        intro="A rustle came from the dim edge of the room.",
        inspect="They turned the projector toward the sound, and a striped shadow stretched tall across the screen.",
        reveal="The shadow had round ears, nimble paws, and no doubt left in it.",
        tags={"shadow", "projector"},
    ),
    "silver_tape": Clue(
        id="silver_tape",
        name="silver tape",
        needs_outside=False,
        works_for={"friend_helping"},
        intro="Something on the missing flipper caught a sudden wink of light.",
        inspect="The projector beam flashed off a neat strip of silver tape near the strap.",
        reveal="Only a careful friend would have fixed it like that.",
        tags={"repair", "projector"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah"]
TRAITS = ["careful", "quick", "kind", "curious", "thoughtful", "brave"]


def valid_combo(setting_id: str, culprit_id: str, clue_id: str) -> bool:
    setting = SETTINGS[setting_id]
    clue = CLUES[clue_id]
    if culprit_id not in clue.works_for:
        return False
    if clue.needs_outside and not setting.outside_nearby:
        return False
    if culprit_id == "racoon" and not setting.racoon_possible:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for culprit_id in CULPRITS:
            for clue_id in CLUES:
                if valid_combo(setting_id, culprit_id, clue_id):
                    out.append((setting_id, culprit_id, clue_id))
    return out


def explain_rejection(setting_id: str, culprit_id: str, clue_id: str) -> str:
    setting = SETTINGS[setting_id]
    culprit = CULPRITS[culprit_id]
    clue = CLUES[clue_id]
    if culprit_id == "racoon" and not setting.racoon_possible:
        return (
            f"(No story: a racoon is not a reasonable culprit in {setting.place}, "
            f"so the mystery would feel made up instead of discovered.)"
        )
    if clue.needs_outside and not setting.outside_nearby:
        return (
            f"(No story: the clue '{clue.name}' needs nearby outdoor mud, but "
            f"{setting.place} does not provide that evidence.)"
        )
    if culprit_id not in clue.works_for:
        return (
            f"(No story: the clue '{clue.name}' cannot honestly reveal "
            f"'{culprit.id}', so the ending would not be fair.)"
        )
    return "(No story: this mystery setup is not reasonable.)"


def predict_reveal(world: World, culprit_id: str, clue_id: str) -> dict:
    sim = world.copy()
    culprit = CULPRITS[culprit_id]
    clue = CLUES[clue_id]
    if culprit.id == "racoon":
        sim.get("flipper").attrs["location"] = "hidden"
        sim.get("racoon").meters["present"] += 1
    else:
        sim.get("friend").attrs["fixed_strap"] = True
        sim.get("flipper").attrs["location"] = "hidden"
    fair = valid_combo(world.setting.id, culprit_id, clue_id)
    return {
        "fair": fair,
        "clue_name": clue.name,
        "culprit": culprit.id,
    }


def introduce(world: World, owner: Entity, friend: Entity, setting: Setting) -> None:
    owner.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(setting.opening)
    world.say(
        f"{owner.id} and {friend.id} were best friends, and tonight they had promised to make "
        f"a tiny mystery show for the younger campers."
    )
    world.say(
        f"They hung {setting.screen_place}, set a small projector on a crate, and whispered as if the room itself might answer back."
    )
    world.say(setting.beam_line)


def setup_flipper(world: World, owner: Entity, flipper: Entity) -> None:
    flipper.attrs["location"] = "crate"
    owner.memes["pride"] += 1
    world.say(
        f"{owner.id} had brought one bright blue flipper to use as a silly sea-monster clue in the show."
    )
    world.say(
        f"{owner.pronoun('possessive').capitalize()} flipper leaned beside the projector, easy to see a moment ago."
    )


def notice_missing(world: World, owner: Entity, friend: Entity, flipper: Entity) -> None:
    flipper.attrs["location"] = "missing"
    owner.memes["worry"] += 1
    world.say(
        f"But when {owner.id} reached for the flipper, it was gone."
    )
    world.say(
        f'"It was right here," {owner.id} whispered. The beam from the projector slid over the crate, the floor, and {friend.id}\'s surprised face.'
    )


def jump_to_blame(world: World, owner: Entity, friend: Entity) -> None:
    owner.memes["accused_friend"] += 1
    owner.memes["trust"] -= 1
    propagate(world, narrate=False)
    world.say(
        f'{owner.id} swallowed hard. "Did you move it, {friend.id}?"'
    )
    if friend.memes["hurt"] >= THRESHOLD:
        world.say(
            f'{friend.id} looked hurt at once. "No," {friend.pronoun()} said. "I would have told you."'
        )


def caretaker_warning(world: World, caretaker: Entity, owner: Entity, friend: Entity, clue: Clue, culprit_id: str) -> None:
    pred = predict_reveal(world, culprit_id, clue.id)
    world.facts["predicted_fair"] = pred["fair"]
    world.say(
        f'{caretaker.label_word.capitalize()} heard the whispering and came to the doorway with a lantern. '
        f'"A good mystery needs a fair clue," {caretaker.pronoun()} said softly. '
        f'"Look carefully before you blame a friend."'
    )


def search(world: World, owner: Entity, friend: Entity, clue: Clue) -> None:
    owner.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(clue.intro)
    world.say(clue.inspect)
    world.say(clue.reveal)


def reveal(world: World, culprit: Culprit, owner: Entity, friend: Entity, flipper: Entity, clue: Clue) -> None:
    flipper.attrs["location"] = "found"
    if culprit.id == "racoon":
        world.get("racoon").meters["present"] += 1
        world.say(culprit.reveal_line)
        world.say(
            f"The little thief had tugged the flipper all the way to {world.setting.hiding_place}."
        )
    else:
        friend.attrs["fixed_strap"] = True
        world.say(culprit.reveal_line)
        world.say(
            f'{friend.id} blushed. "{owner.id}, the strap was coming loose," {friend.pronoun()} said. '
            f'"I only wanted to fix it before the show."'
        )
    propagate(world, narrate=False)


def apology(world: World, owner: Entity, friend: Entity, culprit: Culprit) -> None:
    owner.memes["apologized"] += 1
    propagate(world, narrate=False)
    if culprit.id == "racoon":
        world.say(
            f'{owner.id} felt {owner.pronoun("possessive")} cheeks grow warm. "I am sorry I blamed you," '
            f'{owner.pronoun()} told {friend.id}. "I was scared, and I guessed instead of checking."'
        )
    else:
        world.say(
            f'{owner.id} took a slow breath. "I am sorry I blamed you," {owner.pronoun()} said. '
            f'"You were trying to help me, and I did not trust you first."'
        )
    world.say(
        f'{friend.id} gave a small nod. "Next time I will tell you sooner," {friend.pronoun()} said.'
    )


def reconcile(world: World, owner: Entity, friend: Entity, flipper: Entity, culprit: Culprit) -> None:
    owner.memes["trust"] += 2
    friend.memes["trust"] += 2
    world.say(
        f"Together they picked up the flipper and set it back beside the projector."
    )
    if culprit.id == "racoon":
        world.say(
            f"Outside, the racoon vanished into the reeds, and inside the room the friendship between {owner.id} and {friend.id} felt steady again."
        )
    else:
        world.say(
            f"The silver tape held the strap firm, and the friendship between {owner.id} and {friend.id} felt mended too."
        )
    world.say(
        f"When the show began, the projector threw brave bright shapes on the screen, and the two friends stood shoulder to shoulder to tell their mystery together."
    )


def tell(
    setting: Setting,
    culprit: Culprit,
    clue: Clue,
    owner_name: str,
    owner_gender: str,
    friend_name: str,
    friend_gender: str,
    caretaker_type: str,
    trait: str,
) -> World:
    world = World(setting)
    owner = world.add(Entity(id=owner_name, kind="character", type=owner_gender, role="owner", tags={"friend"}))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend", tags={"friend"}))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=caretaker_type, role="caretaker", label="the caretaker"))
    flipper = world.add(Entity(id="flipper", kind="thing", type="flipper", label="flipper", phrase="a bright blue flipper", tags={"flipper"}))
    projector = world.add(Entity(id="projector", kind="thing", type="projector", label="projector", phrase="a small projector", tags={"projector"}))
    world.add(Entity(id="racoon", kind="character", type="racoon", role="culprit", label="racoon", tags={"racoon"}))

    owner.attrs["trait"] = trait
    friend.attrs["trait"] = random.choice([t for t in TRAITS if t != trait])

    introduce(world, owner, friend, setting)
    setup_flipper(world, owner, flipper)

    world.para()
    notice_missing(world, owner, friend, flipper)
    jump_to_blame(world, owner, friend)
    caretaker_warning(world, caretaker, owner, friend, clue, culprit.id)

    world.para()
    search(world, owner, friend, clue)
    reveal(world, culprit, owner, friend, flipper, clue)

    world.para()
    apology(world, owner, friend, culprit)
    reconcile(world, owner, friend, flipper, culprit)

    world.facts.update(
        setting=setting,
        culprit=culprit,
        clue=clue,
        owner=owner,
        friend=friend,
        caretaker=caretaker,
        flipper=flipper,
        projector=projector,
        culprit_kind=culprit.id,
        friendship_repaired=owner.memes["friendship"] >= THRESHOLD and friend.memes["friendship"] >= THRESHOLD,
        initial_hurt=friend.memes["friendship"] >= THRESHOLD,
        found=flipper.attrs.get("location") == "found",
    )
    return world


KNOWLEDGE = {
    "projector": [
        (
            "What does a projector do?",
            "A projector shines light to make a big picture or shadow on a wall or screen. It helps small things look large and easy to see."
        )
    ],
    "flipper": [
        (
            "What is a flipper?",
            "A flipper is a swim fin that goes on a foot. It helps a swimmer push more water with each kick."
        )
    ],
    "racoon": [
        (
            "What is a racoon?",
            "A racoon is a small animal with a striped tail and clever paws. It often comes out at night to sniff around for interesting things."
        )
    ],
    "friendship": [
        (
            "Why is it important not to blame a friend too quickly?",
            "Blaming too quickly can hurt feelings and make trust wobble. Looking for the truth first is kinder and fairer."
        )
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means people come back together after hurt feelings or a quarrel. It often begins with truth, an apology, and kindness."
        )
    ],
    "mystery": [
        (
            "What makes a mystery fair?",
            "A fair mystery gives real clues that fit the answer. The ending should feel surprising but also make sense."
        )
    ],
}
KNOWLEDGE_ORDER = ["projector", "flipper", "racoon", "friendship", "reconciliation", "mystery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner = f["owner"]
    friend = f["friend"]
    setting = f["setting"]
    culprit = f["culprit"]
    return [
        'Write a short mystery story for a 3-to-5-year-old that includes the words "projector", "flipper", and "racoon".',
        f"Tell a gentle mystery set in {setting.place} where {owner.id} wrongly suspects {friend.id} after a flipper goes missing, but a projector helps reveal the truth.",
        f"Write a child-facing story about friendship and reconciliation where the real answer is {culprit.id}, and the ending shows the friends working together again.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    owner = f["owner"]
    friend = f["friend"]
    caretaker = f["caretaker"]
    setting = f["setting"]
    culprit = f["culprit"]
    clue = f["clue"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {owner.id} and {friend.id}, making a mystery show in {setting.place}. {caretaker.label_word.capitalize()} helps them slow down and look for the truth."
        ),
        (
            "What went missing?",
            f"{owner.id}'s bright blue flipper went missing from beside the projector. That missing prop is what started the mystery."
        ),
        (
            f"Why were {friend.id}'s feelings hurt?",
            f"{owner.id} asked if {friend.id} had moved the flipper before checking the clues. That quick blame hurt because {friend.id} had not been treated like a trusted friend."
        ),
        (
            "How did the projector help solve the mystery?",
            f"The projector made the clue easy to see by throwing bright light across the dark room. It turned {clue.name} into clear evidence instead of a frightened guess."
        ),
    ]
    if culprit.id == "racoon":
        qa.append(
            (
                "What was the real answer to the mystery?",
                f"A racoon had taken the flipper and dragged it to {setting.hiding_place}. The truth mattered because it showed that {friend.id} had been blamed unfairly."
            )
        )
    else:
        qa.append(
            (
                "What was the real answer to the mystery?",
                f"{friend.id} had hidden the flipper only long enough to fix a loose strap with tape. The clue showed help, not stealing, so the misunderstanding could end."
            )
        )
    qa.append(
        (
            "How did the friends make peace at the end?",
            f"{owner.id} apologized for blaming {friend.id} too quickly, and {friend.id} answered kindly. Then they stood together beside the projector and finished the show as friends again."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"projector", "flipper", "friendship", "reconciliation", "mystery"}
    if world.facts["culprit"].id == "racoon":
        tags.add("racoon")
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
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="boathouse",
        culprit="racoon",
        clue="muddy_tracks",
        friend1="Lily",
        friend1_gender="girl",
        friend2="Tom",
        friend2_gender="boy",
        owner="Lily",
        owner_gender="girl",
        caretaker="mother",
        trait="careful",
    ),
    StoryParams(
        setting="clubhouse",
        culprit="racoon",
        clue="shadow_silhouette",
        friend1="Ben",
        friend1_gender="boy",
        friend2="Mia",
        friend2_gender="girl",
        owner="Ben",
        owner_gender="boy",
        caretaker="father",
        trait="curious",
    ),
    StoryParams(
        setting="attic_hall",
        culprit="friend_helping",
        clue="silver_tape",
        friend1="Ava",
        friend1_gender="girl",
        friend2="Noah",
        friend2_gender="boy",
        owner="Ava",
        owner_gender="girl",
        caretaker="mother",
        trait="thoughtful",
    ),
]


ASP_RULES = r"""
valid(S, C, Cl) :- setting(S), culprit(C), clue(Cl), works_for(Cl, C),
                   not bad_outside(S, Cl), not bad_racoon(S, C).
bad_outside(S, Cl) :- clue_needs_outside(Cl), not outside_nearby(S).
bad_racoon(S, racoon) :- not racoon_possible(S).

outcome(S, C, Cl, reconciled) :- valid(S, C, Cl).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        if setting.outside_nearby:
            lines.append(asp.fact("outside_nearby", setting_id))
        if setting.racoon_possible:
            lines.append(asp.fact("racoon_possible", setting_id))
    for culprit_id in CULPRITS:
        lines.append(asp.fact("culprit", culprit_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        if clue.needs_outside:
            lines.append(asp.fact("clue_needs_outside", clue_id))
        for culprit_id in sorted(clue.works_for):
            lines.append(asp.fact("works_for", clue_id, culprit_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/3."))
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
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in asp:", sorted(cl - py))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        emit(sample, trace=False, qa=False, header="SMOKE TEST")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery storyworld: a missing flipper, a projector clue, and friendship repaired."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--caretaker", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.culprit and args.clue:
        if not valid_combo(args.setting, args.culprit, args.clue):
            raise StoryError(explain_rejection(args.setting, args.culprit, args.clue))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.clue is None or combo[2] == args.clue)
    ]
    if not combos:
        if args.setting and args.culprit and args.clue:
            raise StoryError(explain_rejection(args.setting, args.culprit, args.clue))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, culprit_id, clue_id = rng.choice(sorted(combos))
    owner_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    owner_name = _pick_name(rng, owner_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=owner_name)
    trait = rng.choice(TRAITS)
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        culprit=culprit_id,
        clue=clue_id,
        friend1=owner_name,
        friend1_gender=owner_gender,
        friend2=friend_name,
        friend2_gender=friend_gender,
        owner=owner_name,
        owner_gender=owner_gender,
        caretaker=caretaker,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Invalid culprit: {params.culprit})")
    if params.clue not in CLUES:
        raise StoryError(f"(Invalid clue: {params.clue})")
    if not valid_combo(params.setting, params.culprit, params.clue):
        raise StoryError(explain_rejection(params.setting, params.culprit, params.clue))

    world = tell(
        setting=SETTINGS[params.setting],
        culprit=CULPRITS[params.culprit],
        clue=CLUES[params.clue],
        owner_name=params.owner,
        owner_gender=params.owner_gender,
        friend_name=params.friend2,
        friend_gender=params.friend2_gender,
        caretaker_type=params.caretaker,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, culprit, clue) combos:\n")
        for setting_id, culprit_id, clue_id in combos:
            print(f"  {setting_id:10} {culprit_id:14} {clue_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.owner} and {p.friend2}: {p.culprit} with {p.clue} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
