#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tuna_mystery_to_solve_twist_folk_tale.py
===================================================================

A small folk-tale storyworld about a vanished tuna, a false suspicion, and the
twist hidden inside a trail of clues.

The domain is a seaside village preparing a lantern feast. A fine tuna is set
aside for the meal, then disappears in the night. The village jumps to the
wrong conclusion, but a child seeker follows physical clues with a wise helper,
finds the true cause, and chooses a remedy that fits the culprit's need. The
ending proves what changed: the feast is saved, the wrongly blamed creature is
cleared, and the village learns to look twice before accusing.

Run it
------
    python storyworlds/worlds/gpt-5.4/tuna_mystery_to_solve_twist_folk_tale.py
    python storyworlds/worlds/gpt-5.4/tuna_mystery_to_solve_twist_folk_tale.py --culprit otter
    python storyworlds/worlds/gpt-5.4/tuna_mystery_to_solve_twist_folk_tale.py --suspect cat --culprit cat
    python storyworlds/worlds/gpt-5.4/tuna_mystery_to_solve_twist_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/tuna_mystery_to_solve_twist_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tuna_mystery_to_solve_twist_folk_tale.py --verify
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

# Make the shared result containers importable when this script is run directly.
_THIS = os.path.abspath(__file__)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(_THIS))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "animal" | "thing" | "spirit"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "mother"}
        male = {"boy", "man", "grandfather", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    village: str
    storage_place: str
    trail_place: str
    reveal_place: str
    ending_image: str


@dataclass
class Suspect:
    id: str
    label: str
    phrase: str
    blame_sign: str
    innocent_line: str
    type: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    phrase: str
    type: str                  # animal | spirit
    motive: str
    trail: str
    reveal: str
    need: str                  # hungry_family | forgotten_offering | trapped_friend
    twist_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    type: str
    skill: set[str]
    wisdom: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    action: str
    solves: set[str]
    ending: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def entity_by_role(world: World, role: str, fallback_id: str) -> Entity:
    for ent in world.entities.values():
        if ent.role == role:
            return ent
    return world.get(fallback_id)


def _r_missing_worry(world: World) -> list[str]:
    tuna = world.get("tuna")
    if tuna.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    entity_by_role(world, "seeker", "seeker").memes["concern"] += 1
    world.get("village").memes["worry"] += 1
    return []


def _r_false_blame(world: World) -> list[str]:
    village = world.get("village")
    suspect = world.get("suspect")
    if village.memes["blame"] < THRESHOLD:
        return []
    sig = ("false_blame", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["sadness"] += 1
    return []


def _r_clues_to_knowledge(world: World) -> list[str]:
    seeker = entity_by_role(world, "seeker", "seeker")
    helper = world.get("helper")
    culprit = world.get("culprit")
    if seeker.meters["clues_seen"] < 2:
        return []
    if culprit.attrs.get("need") not in helper.attrs.get("skill", set()):
        return []
    sig = ("knowledge", culprit.id, helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.meters["understands"] += 1
    seeker.memes["wonder"] += 1
    return []


def _r_remedy_success(world: World) -> list[str]:
    remedy = world.get("remedy")
    culprit = world.get("culprit")
    if entity_by_role(world, "seeker", "seeker").meters["understands"] < THRESHOLD:
        return []
    if culprit.attrs.get("need") not in remedy.attrs.get("solves", set()):
        return []
    sig = ("remedy_success", remedy.id, culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("tuna").meters["restored"] += 1
    world.get("village").memes["peace"] += 1
    world.get("suspect").memes["sadness"] = 0.0
    world.get("suspect").memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule("missing_worry", "social", _r_missing_worry),
    Rule("false_blame", "social", _r_false_blame),
    Rule("knowledge", "epistemic", _r_clues_to_knowledge),
    Rule("remedy_success", "social", _r_remedy_success),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            made = rule.apply(world)
            if made:
                changed = True
                out.extend(made)
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def culprit_matches_suspect(culprit_id: str, suspect_id: str) -> bool:
    return culprit_id == suspect_id


def helper_can_read(helper: Helper, culprit: Culprit) -> bool:
    return culprit.need in helper.skill


def remedy_fits(remedy: Remedy, culprit: Culprit) -> bool:
    return culprit.need in remedy.solves


def valid_combo(suspect_id: str, culprit_id: str, helper_id: str, remedy_id: str) -> bool:
    if culprit_matches_suspect(culprit_id, suspect_id):
        return False
    return (
        helper_can_read(HELPERS[helper_id], CULPRITS[culprit_id])
        and remedy_fits(REMEDIES[remedy_id], CULPRITS[culprit_id])
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for suspect_id in SUSPECTS:
        for culprit_id in CULPRITS:
            for helper_id in HELPERS:
                for remedy_id in REMEDIES:
                    if valid_combo(suspect_id, culprit_id, helper_id, remedy_id):
                        combos.append((suspect_id, culprit_id, helper_id, remedy_id))
    return combos


def explain_rejection(suspect_id: str, culprit_id: str, helper_id: str, remedy_id: str) -> str:
    if culprit_matches_suspect(culprit_id, suspect_id):
        return (
            f"(No story: the twist would collapse because the village suspects "
            f"{SUSPECTS[suspect_id].label}, and {CULPRITS[culprit_id].label} would "
            "really be the culprit. Pick a different true culprit.)"
        )
    if not helper_can_read(HELPERS[helper_id], CULPRITS[culprit_id]):
        return (
            f"(No story: {HELPERS[helper_id].label} does not know how to read the "
            f"signs left by {CULPRITS[culprit_id].label}. Choose a helper whose "
            "wisdom fits the mystery.)"
        )
    if not remedy_fits(REMEDIES[remedy_id], CULPRITS[culprit_id]):
        return (
            f"(No story: {REMEDIES[remedy_id].label} would not solve "
            f"{CULPRITS[culprit_id].label}'s need. The ending must repair the real "
            "cause of the disappearance.)"
        )
    return "(No story: this combination does not make a coherent mystery.)"


# ---------------------------------------------------------------------------
# Simulation verbs
# ---------------------------------------------------------------------------
def open_tale(world: World, setting: Setting, seeker: Entity, elder: Entity) -> None:
    seeker.memes["care"] += 1
    world.say(
        f"In {setting.village}, where people said the sea listened at night, "
        f"there lived a child named {seeker.id}. {elder.id}, the village elder, "
        f"used to say that every honest feast begins with a "
        f"thank-you."
    )


def feast_setup(world: World, setting: Setting, tuna_desc: str) -> None:
    world.say(
        f"On the eve of the lantern feast, the fishers brought home {tuna_desc} "
        f"and laid it in {setting.storage_place}. Everyone expected tuna stew to "
        "steam in the square by moonrise."
    )


def disappearance(world: World, setting: Setting) -> None:
    tuna = world.get("tuna")
    tuna.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when the dawn bell rang, the tuna was gone. In its place lay only "
        f"{setting.trail_place}."
    )


def blame(world: World, suspect: Suspect) -> None:
    world.get("village").memes["blame"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"It was {suspect.phrase}," the neighbors cried, because they had seen '
        f"{suspect.blame_sign}."
    )


def seeker_refuses_haste(world: World, seeker: Entity, elder: Entity) -> None:
    seeker.memes["resolve"] += 1
    world.say(
        f"But {seeker.id} remembered {elder.id}'s old lesson: quick blame can be "
        "quicker than truth. So the child took a basket lantern and went to look."
    )


def observe_clues(world: World, culprit: Culprit, helper: Entity, helper_cfg: Helper) -> None:
    seeker = entity_by_role(world, "seeker", "seeker")
    seeker.meters["clues_seen"] += 2
    propagate(world, narrate=False)
    world.say(
        f"At the edge of the village path, {seeker.id} found {culprit.trail}. "
        f"There {helper_cfg.phrase} was waiting, and {helper.pronoun()} said, "
        f'"{helper_cfg.wisdom}"'
    )


def revelation(world: World, setting: Setting, culprit: Culprit, suspect: Suspect) -> None:
    seeker = entity_by_role(world, "seeker", "seeker")
    world.say(
        f"Together they followed the signs to {setting.reveal_place}. There they "
        f"saw {culprit.reveal}. {culprit.twist_line}"
    )
    suspect_ent = world.get("suspect")
    if suspect_ent.memes["sadness"] >= THRESHOLD:
        world.say(
            f"So {suspect.phrase} had not stolen anything at all. {suspect.innocent_line}"
        )
    if seeker.meters["understands"] >= THRESHOLD:
        world.say(
            f"Then {seeker.id} understood the whole mystery. The tuna had not "
            f"vanished out of meanness. {culprit.motive}"
        )


def remedy_scene(world: World, remedy: Remedy, culprit: Culprit, elder: Entity) -> None:
    world.get("remedy").attrs["used"] = True
    propagate(world, narrate=False)
    seeker = entity_by_role(world, "seeker", "seeker")
    world.say(
        f"{elder.id} came when {seeker.id} called, and together they "
        f"{remedy.action}. At once the hard feeling in the air softened."
    )
    world.say(remedy.ending)
    if world.get("tuna").meters["restored"] >= THRESHOLD:
        world.say(
            f"By evening, the village had enough tuna for the feast, and enough "
            "wisdom for a better story than blame."
        )


def ending_image(world: World, setting: Setting, suspect: Suspect) -> None:
    suspect_ent = world.get("suspect")
    relief = ""
    if suspect_ent.memes["relief"] >= THRESHOLD:
        relief = f" Nearby, {suspect.phrase} rested easy at last."
    world.say(
        f"That night, lanterns shone across {setting.ending_image}, and the people "
        "spoke more softly before naming a thief." + relief
    )


# ---------------------------------------------------------------------------
# Story driver
# ---------------------------------------------------------------------------
def tell(setting: Setting, suspect: Suspect, culprit: Culprit, helper: Helper,
         remedy: Remedy, seeker_name: str = "Mira", seeker_type: str = "girl",
         elder_name: str = "Nana", elder_type: str = "grandmother",
         tuna_desc: str = "a bright silver tuna") -> World:
    world = World()
    seeker = world.add(Entity(id=seeker_name, kind="character", type=seeker_type, role="seeker"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder"))
    village = world.add(Entity(id="village", kind="thing", type="village", label="the village"))
    tuna = world.add(Entity(id="tuna", kind="thing", type="fish", label="tuna"))
    suspect_ent = world.add(Entity(
        id="suspect", kind="animal", type=suspect.type, label=suspect.label, role="suspect"
    ))
    culprit_ent = world.add(Entity(
        id="culprit", kind="animal" if culprit.type == "animal" else "spirit",
        type=culprit.type, label=culprit.label, role="culprit",
        attrs={"need": culprit.need},
    ))
    helper_ent = world.add(Entity(
        id="helper", kind="character" if helper.type in {"grandmother", "grandfather", "child"} else "animal",
        type=helper.type, label=helper.label, role="helper",
        attrs={"skill": set(helper.skill)},
    ))
    remedy_ent = world.add(Entity(
        id="remedy", kind="thing", type="remedy", label=remedy.label,
        attrs={"solves": set(remedy.solves)},
    ))

    open_tale(world, setting, seeker, elder)
    feast_setup(world, setting, tuna_desc)

    world.para()
    disappearance(world, setting)
    blame(world, suspect)
    seeker_refuses_haste(world, seeker, elder)

    world.para()
    observe_clues(world, culprit, helper_ent, helper)
    revelation(world, setting, culprit, suspect)

    world.para()
    remedy_scene(world, remedy, culprit, elder)
    ending_image(world, setting, suspect)

    world.facts.update(
        setting=setting,
        suspect_cfg=suspect,
        culprit_cfg=culprit,
        helper_cfg=helper,
        remedy_cfg=remedy,
        seeker=seeker,
        elder=elder,
        suspect=suspect_ent,
        culprit=culprit_ent,
        helper=helper_ent,
        tuna=tuna,
        tuna_desc=tuna_desc,
        twist=True,
        restored=tuna.meters["restored"] >= THRESHOLD,
        false_blame=suspect_ent.memes["sadness"] >= 0 or village.memes["blame"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "cove": Setting(
        "cove",
        "Shell-Cove",
        "a cool stone trough beside the market gate",
        "a wet curve of prints and one silver scale",
        "the reed bank where the tide whispered",
        "the harbor water like a bowl of gold",
    ),
    "harbor": Setting(
        "harbor",
        "Moon-Harbor",
        "a cedar table under the fish awning",
        "a line of drips, kelp threads, and one bent shell",
        "the old pier where the waves tapped the posts",
        "the long pier and the sleeping boats",
    ),
    "inlet": Setting(
        "inlet",
        "Lantern-Inlet",
        "a woven tray in the shade of the net shed",
        "a dark track of water leading toward the marsh grass",
        "the marsh edge where water met moonlight",
        "the inlet path and the salt grass",
    ),
}

SUSPECTS = {
    "cat": Suspect(
        "cat", "village cat", "the village cat", "little paw marks by the gate",
        "The cat only sat licking a paw and blinking in surprise.", "cat",
        tags={"cat"},
    ),
    "gull": Suspect(
        "gull", "white gull", "the white gull", "a harsh cry over the roofs",
        "The gull had only been calling at sunrise, as gulls always do.", "gull",
        tags={"gull"},
    ),
    "fox": Suspect(
        "fox", "red fox", "the red fox", "a red shadow near the fence",
        "The fox had passed by the path, but never touched the fish.",
        "fox", tags={"fox"},
    ),
}

CULPRITS = {
    "otter": Culprit(
        "otter", "river otter", "a river otter", "animal",
        "The otter had dragged the fish away because her little pups were crying with hunger.",
        "small wet prints, a dragged line in the sand, and crushed reeds",
        "an otter mother nosing the tuna toward three squeaking pups",
        "hungry_family",
        "It was not a greedy thief at all, but a mother trying to feed her babies.",
        tags={"otter", "hunger"},
    ),
    "tide_spirit": Culprit(
        "tide_spirit", "tide spirit", "the tide spirit", "spirit",
        "The tide spirit had taken the fish because the village had forgotten the first-bowl thanks once given to the sea.",
        "no footprints at all, only a shining thread of seawater and shells turned face-up",
        "a pale tide spirit cradling the tuna in water bright as glass",
        "forgotten_offering",
        "The thief was no beast of claw or wing, but the old tide itself wearing a face.",
        tags={"spirit", "sea"},
    ),
    "crane": Culprit(
        "crane", "marsh crane", "a marsh crane", "animal",
        "The crane had carried the tuna in pieces to feed an old turtle tangled in fishing twine.",
        "long bird tracks, clipped rushes, and a feather stuck to wet mud",
        "a tall crane laying fish beside a tired turtle caught in twine",
        "trapped_friend",
        "The mystery was stranger than theft: the fish had become a rescue gift.",
        tags={"crane", "rescue"},
    ),
}

HELPERS = {
    "crab": Helper(
        "crab", "crab", "the old crab from the tide steps", "animal",
        {"forgotten_offering", "trapped_friend"},
        "Tracks tell only who passed by; water tells who was welcomed.",
        tags={"crab"},
    ),
    "net_mender": Helper(
        "net_mender", "net-mender", "the bent old net-mender", "grandfather",
        {"hungry_family", "trapped_friend"},
        "When reeds bend low and the scales lie in a line, someone pulled more than they could carry.",
        tags={"net"},
    ),
    "herb_grandmother": Helper(
        "herb_grandmother", "herb grandmother", "the herb grandmother", "grandmother",
        {"hungry_family", "forgotten_offering"},
        "The world leaves two kinds of signs, child: hungry signs and hurt signs.",
        tags={"grandmother"},
    ),
}

REMEDIES = {
    "share_bowls": Remedy(
        "share_bowls", "shared bowls",
        "cooked smaller bowls of tuna stew and sent the first warm bowl to the hungry nest in the reeds",
        {"hungry_family"},
        "The otter pups ate, and the mother left the rest untouched beside the shore.",
        tags={"sharing"},
    ),
    "sea_thanks": Remedy(
        "sea_thanks", "sea thanks",
        "set a little blue bowl at the water's edge and thanked the sea before touching the fish again",
        {"forgotten_offering"},
        "The tide spirit smiled, returned the fish, and the water folded back into an ordinary wave.",
        tags={"gratitude", "sea"},
    ),
    "cut_twine": Remedy(
        "cut_twine", "cut twine",
        "freed the old turtle from the biting twine and promised to keep torn nets off the marsh path",
        {"trapped_friend"},
        "The crane dipped its head, and what remained of the tuna was given back for the feast.",
        tags={"rescue"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Sana", "Nuri", "Tala", "Ami"]
BOY_NAMES = ["Ivo", "Niko", "Toma", "Rin", "Pavel", "Sami"]
TUNA_DESCS = [
    "a bright silver tuna",
    "a moon-fat tuna",
    "a great blue-backed tuna",
]
ELDER_CHOICES = [
    ("Nana", "grandmother"),
    ("Grandfather Bo", "grandfather"),
    ("Auntie Sora", "woman"),
]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    suspect: str
    culprit: str
    helper: str
    remedy: str
    seeker: str
    seeker_type: str
    elder: str
    elder_type: str
    tuna_desc: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "tuna": [(
        "What is a tuna?",
        "A tuna is a big fish that lives in the sea. People catch tuna for food."
    )],
    "cat": [(
        "Why should you not blame an animal too quickly?",
        "Because the first guess can be wrong. It is better to look for real clues before saying who did something."
    )],
    "gull": [(
        "What is a gull?",
        "A gull is a seabird that likes the shore. It can cry loudly and fly over fishing boats."
    )],
    "fox": [(
        "What is a fox?",
        "A fox is a wild animal with a pointed face and a bushy tail. Foxes are quick and careful."
    )],
    "otter": [(
        "What is an otter?",
        "An otter is an animal that loves water and can swim very well. Otters often catch food near rivers and shores."
    )],
    "sea": [(
        "Why do folk tales thank the sea?",
        "In folk tales, people thank the sea to show respect for the place that feeds them. The thanks also remind them not to act proud."
    )],
    "rescue": [(
        "Why is helping a trapped animal important?",
        "A trapped animal can be hurt and frightened. Helping it is a kind way to stop more pain."
    )],
    "sharing": [(
        "Why can sharing solve a problem?",
        "Sharing can calm hunger and stop anger before it grows. Sometimes a fair gift fixes what grabbing cannot."
    )],
    "gratitude": [(
        "What is gratitude?",
        "Gratitude means saying thank you and meaning it. It helps people remember that good things are gifts, not just things to take."
    )],
    "clue": [(
        "What is a clue?",
        "A clue is a small sign that helps you understand a mystery. Footprints, feathers, or drops of water can all be clues."
    )],
}
KNOWLEDGE_ORDER = ["tuna", "clue", "cat", "gull", "fox", "otter", "sea", "rescue", "sharing", "gratitude"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    suspect = f["suspect_cfg"]
    culprit = f["culprit_cfg"]
    remedy = f["remedy_cfg"]
    seeker = f["seeker"]
    return [
        'Write a folk tale for a 3-to-5-year-old about a missing tuna and a child who solves a mystery.',
        f"Tell a seaside folk tale where everyone blames {suspect.phrase}, but {seeker.id} follows clues and discovers {culprit.label} instead.",
        f"Write a gentle twist story in a folk-tale voice set in {setting.village}, where a vanished tuna is restored by {remedy.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    elder = f["elder"]
    setting = f["setting"]
    suspect = f["suspect_cfg"]
    culprit = f["culprit_cfg"]
    helper = f["helper_cfg"]
    remedy = f["remedy_cfg"]
    tuna_desc = f["tuna_desc"]
    items: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {seeker.id}, a child in {setting.village}, and {elder.id}, who taught {seeker.pronoun('object')} to look for truth before blame."
        ),
        (
            "What went missing?",
            f"{tuna_desc[0].upper()}{tuna_desc[1:]} meant for the lantern feast disappeared at dawn. That missing tuna started the whole mystery."
        ),
        (
            "Who did the village blame first?",
            f"They blamed {suspect.phrase} first. The neighbors hurried because they thought they had seen {suspect.blame_sign}."
        ),
        (
            f"How did {seeker.id} solve the mystery?",
            f"{seeker.id} did not trust the first guess. {seeker.pronoun().capitalize()} followed the trail, listened to {helper.phrase}, and used the clues to find the true cause."
        ),
        (
            "What was the twist?",
            f"The one everyone blamed was innocent. The real cause was {culprit.label}. {culprit.motive}"
        ),
        (
            "How was the problem fixed?",
            f"{seeker.id} called {elder.id}, and together they {remedy.action}. That fit the real need behind the mystery, so the hard feeling ended and the feast could go on."
        ),
        (
            "How did the story end?",
            f"The tuna was restored to the village feast, and the people learned to speak more carefully before naming a thief. The lanterns over {setting.ending_image} showed that peace had come back."
        ),
    ]
    return items


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    suspect = f["suspect_cfg"]
    culprit = f["culprit_cfg"]
    remedy = f["remedy_cfg"]
    tags = {"tuna", "clue"} | set(suspect.tags) | set(culprit.tags) | set(remedy.tags)
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
            shown = {}
            for k, v in e.attrs.items():
                if isinstance(v, set):
                    shown[k] = sorted(v)
                elif v:
                    shown[k] = v
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
different_culprit(S, C) :- suspect(S), culprit(C), S != C.

helper_can(H, C) :- helper(H), culprit(C), need(C, N), skill(H, N).
remedy_fits(R, C) :- remedy(R), culprit(C), need(C, N), solves(R, N).

valid(S, C, H, R) :- suspect(S), culprit(C), helper(H), remedy(R),
                     different_culprit(S, C), helper_can(H, C), remedy_fits(R, C).

% outcome is always restored for a valid story in this domain.
outcome(restored) :- chosen(S, C, H, R), valid(S, C, H, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for cid, c in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        lines.append(asp.fact("need", cid, c.need))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for skill in sorted(h.skill):
            lines.append(asp.fact("skill", hid, skill))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for solve in sorted(r.solves):
            lines.append(asp.fact("solves", rid, solve))
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
        asp.fact("chosen", params.suspect, params.culprit, params.helper, params.remedy),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: ASP gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    # smoke tests: ordinary generation must not crash
    try:
        sample = generate(CURATED[0])
        if not sample.story or "tuna" not in sample.story.lower():
            raise StoryError("(Verify failed: smoke story did not render a tuna story.)")
        print("OK: smoke generation rendered a story.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for p in cases:
        if asp_outcome(p) != "restored":
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches restored ending on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes failed.")
    return rc


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("cove", "cat", "otter", "net_mender", "share_bowls",
                "Mira", "girl", "Nana", "grandmother", "a bright silver tuna"),
    StoryParams("harbor", "gull", "tide_spirit", "herb_grandmother", "sea_thanks",
                "Niko", "boy", "Grandfather Bo", "grandfather", "a moon-fat tuna"),
    StoryParams("inlet", "fox", "crane", "crab", "cut_twine",
                "Lina", "girl", "Auntie Sora", "woman", "a great blue-backed tuna"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: a missing tuna, a wrong suspicion, and a twist solved by clues."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--seeker")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid mystery combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit_suspect = args.suspect
    explicit_culprit = args.culprit
    explicit_helper = args.helper
    explicit_remedy = args.remedy

    if all(x is not None for x in [explicit_suspect, explicit_culprit, explicit_helper, explicit_remedy]):
        if not valid_combo(explicit_suspect, explicit_culprit, explicit_helper, explicit_remedy):
            raise StoryError(explain_rejection(
                explicit_suspect, explicit_culprit, explicit_helper, explicit_remedy
            ))

    combos = [
        c for c in valid_combos()
        if (args.suspect is None or c[0] == args.suspect)
        and (args.culprit is None or c[1] == args.culprit)
        and (args.helper is None or c[2] == args.helper)
        and (args.remedy is None or c[3] == args.remedy)
    ]
    if not combos:
        # Try to explain with best available explicit pins.
        suspect_id = args.suspect or next(iter(SUSPECTS))
        culprit_id = args.culprit or next(iter(CULPRITS))
        helper_id = args.helper or next(iter(HELPERS))
        remedy_id = args.remedy or next(iter(REMEDIES))
        raise StoryError(explain_rejection(suspect_id, culprit_id, helper_id, remedy_id))

    suspect_id, culprit_id, helper_id, remedy_id = rng.choice(sorted(combos))
    setting_id = args.setting or rng.choice(sorted(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    seeker = args.seeker or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_name, elder_type = rng.choice(ELDER_CHOICES)
    tuna_desc = rng.choice(TUNA_DESCS)
    return StoryParams(
        setting_id, suspect_id, culprit_id, helper_id, remedy_id,
        seeker, gender, elder_name, elder_type, tuna_desc
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        SUSPECTS[params.suspect],
        CULPRITS[params.culprit],
        HELPERS[params.helper],
        REMEDIES[params.remedy],
        params.seeker,
        params.seeker_type,
        params.elder,
        params.elder_type,
        params.tuna_desc,
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
        print(f"{len(combos)} valid (suspect, culprit, helper, remedy) combos:\n")
        for suspect, culprit, helper, remedy in combos:
            print(f"  {suspect:6} {culprit:11} {helper:16} {remedy}")
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
            header = (
                f"### {p.seeker}: suspect {p.suspect}, true culprit {p.culprit}, "
                f"helper {p.helper}, remedy {p.remedy}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
