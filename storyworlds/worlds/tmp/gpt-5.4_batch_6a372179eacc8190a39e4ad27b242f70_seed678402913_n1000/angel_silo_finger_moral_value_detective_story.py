#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/angel_silo_finger_moral_value_detective_story.py
============================================================================

A standalone storyworld about a small detective mystery at a farmyard silo.

Seed requirements rebuilt as a simulated domain:
- word/theme elements: angel, silo, finger
- feature: Moral Value
- style: Detective Story

Premise
-------
A child detective notices that a little angel keepsake has gone missing during a
farm day near a tall silo. A clue on someone's finger points toward the truth.
The culprit did not mean to steal; they borrowed the keepsake for a chore,
damaged or misplaced it, then hid it out of shame. The detective chooses how to
approach the mystery, and the ending proves the moral value that honesty and
gentleness make problems easier to fix.

Reasonableness gate
-------------------
Not every keepsake fits every chore:
- an angel ribbon can sensibly trim a scarecrow
- an angel bell or badge can sensibly decorate a gift basket
- only a sturdy angel badge makes sense on a painted sign by the silo ladder

The world rejects incompatible pairings instead of forcing a weak story.

Run it
------
python storyworlds/worlds/gpt-5.4/angel_silo_finger_moral_value_detective_story.py
python storyworlds/worlds/gpt-5.4/angel_silo_finger_moral_value_detective_story.py --item badge --case silo_sign
python storyworlds/worlds/gpt-5.4/angel_silo_finger_moral_value_detective_story.py --item ribbon --case gift_basket
python storyworlds/worlds/gpt-5.4/angel_silo_finger_moral_value_detective_story.py --all
python storyworlds/worlds/gpt-5.4/angel_silo_finger_moral_value_detective_story.py --qa --json
python storyworlds/worlds/gpt-5.4/angel_silo_finger_moral_value_detective_story.py --verify
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

# Make shared result containers importable when this nested script is run
# directly from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing | place
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class AngelItem:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    fragile: bool = False


@dataclass
class CaseFile:
    id: str
    title: str
    place_phrase: str
    chore: str
    chore_gerund: str
    clue: str
    finger_line: str
    hideout: str
    hideout_phrase: str
    use_purpose: str
    accident: str
    repair: str
    confession: str
    required_tags: set[str] = field(default_factory=set)
    safe_for_fragile: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Approach:
    id: str
    tone: str
    opening: str
    ask_line: str
    kind: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    item: str
    case: str
    approach: str
    detective_name: str
    detective_gender: str
    culprit_name: str
    culprit_gender: str
    helper_name: str
    helper_gender: str
    adult: str
    detective_trait: str
    culprit_trait: str
    pet: str = ""
    seed: Optional[int] = None


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_stirs_worry(world: World) -> list[str]:
    item = world.entities.get("item")
    if item is None or item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("detective").memes["curiosity"] += 1
    world.get("helper").memes["worry"] += 1
    world.get("culprit").memes["guilt"] += 1
    return []


def _r_hidden_keeps_guilt(world: World) -> list[str]:
    item = world.entities.get("item")
    culprit = world.entities.get("culprit")
    if item is None or culprit is None:
        return []
    if item.meters["hidden"] < THRESHOLD or culprit.memes["guilt"] < THRESHOLD:
        return []
    sig = ("hidden_guilt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit.memes["fear"] += 1
    return []


def _r_kindness_builds_courage(world: World) -> list[str]:
    detective = world.entities.get("detective")
    culprit = world.entities.get("culprit")
    if detective is None or culprit is None:
        return []
    if detective.memes["kindness"] < THRESHOLD or culprit.memes["guilt"] < THRESHOLD:
        return []
    sig = ("kindness_courage",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit.memes["courage"] += 1
    culprit.memes["trust"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="moral", apply=_r_missing_stirs_worry),
    Rule(name="hidden_guilt", tag="moral", apply=_r_hidden_keeps_guilt),
    Rule(name="kindness_courage", tag="moral", apply=_r_kindness_builds_courage),
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
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def item_fits_case(item: AngelItem, case: CaseFile) -> bool:
    if not case.required_tags.issubset(item.tags):
        return False
    if item.fragile and not case.safe_for_fragile:
        return False
    return True


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for item_id, item in ITEMS.items():
        for case_id, case in CASES.items():
            if item_fits_case(item, case):
                combos.append((item_id, case_id))
    return sorted(combos)


def outcome_of(params: StoryParams) -> str:
    return "confessed" if APPROACHES[params.approach].kind else "mended_after_adult"


def predict_case(world: World) -> dict:
    sim = world.copy()
    culprit = sim.get("culprit")
    item = sim.get("item")
    culprit.meters["clue_seen"] += 1
    propagate(sim, narrate=False)
    return {
        "culprit_guilty": culprit.memes["guilt"] >= THRESHOLD,
        "item_hidden": item.meters["hidden"] >= THRESHOLD,
    }


def opening_scene(world: World, detective: Entity, helper: Entity, adult: Entity,
                  item_cfg: AngelItem, case_cfg: CaseFile, silo: Entity) -> None:
    for kid in (detective, helper):
        kid.memes["interest"] += 1
    world.say(
        f"On market morning, {detective.id} and {helper.id} followed "
        f"{adult.label_word} past the big {silo.label} and into the yard. "
        f"They loved pretending they were detectives whenever the farm felt full of little clues."
    )
    world.say(
        f"On a crate by the door sat {item_cfg.phrase}. Everyone knew it belonged on the welcome table."
    )
    world.say(
        f"By noon the yard was busy with {case_cfg.chore_gerund}, laughing neighbors, and the warm smell of bread."
    )


def mystery_begins(world: World, detective: Entity, helper: Entity, item_cfg: AngelItem,
                   case_cfg: CaseFile) -> None:
    item = world.get("item")
    item.meters["missing"] += 1
    item.meters["hidden"] += 1
    culprit = world.get("culprit")
    culprit.memes["guilt"] += 1
    culprit.memes["fear"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {helper.id} stopped short. {helper.pronoun().capitalize()} pointed to the empty crate. "
        f'"The {item_cfg.label} is gone!" {helper.pronoun()} whispered.'
    )
    world.say(
        f"{detective.id} looked at the bare square of dust where it had been. "
        f"A detective story had just begun."
    )
    world.say(
        f'There was one more clue: {case_cfg.clue} on the edge of the crate, as if one hurried hand had touched it.'
    )


def inspect_clue(world: World, detective: Entity, helper: Entity, culprit: Entity,
                 case_cfg: CaseFile) -> None:
    pred = predict_case(world)
    world.facts["predicted_hidden"] = pred["item_hidden"]
    world.say(
        f"{detective.id} did not shout or accuse. {detective.pronoun().capitalize()} walked slowly around the yard, "
        f"past {case_cfg.place_phrase}, watching hands instead of faces."
    )
    culprit.meters["clue_seen"] += 1
    world.say(
        f"Soon {detective.id} noticed {case_cfg.finger_line} on {culprit.id}'s finger. "
        f'"That matches the mark on the crate," {helper.id} murmured.'
    )


def follow_trail(world: World, detective: Entity, helper: Entity, culprit: Entity,
                 item_cfg: AngelItem, case_cfg: CaseFile) -> None:
    culprit.meters["cornered"] += 1
    world.say(
        f"The clue led them toward {case_cfg.hideout_phrase}. Behind it, tucked out of sight, "
        f"lay {item_cfg.phrase}."
    )
    item = world.get("item")
    item.meters["found"] += 1
    world.say(
        f"{helper.id} gasped. '{culprit.id}, did you take it?'"
    )


def gentle_question(world: World, detective: Entity, culprit: Entity, approach: Approach) -> None:
    if approach.kind:
        detective.memes["kindness"] += 1
    else:
        detective.memes["sharpness"] += 1
    propagate(world, narrate=False)
    world.say(approach.opening.format(detective=detective.id, culprit=culprit.id))
    world.say(approach.ask_line.format(culprit=culprit.id))


def confess(world: World, culprit: Entity, item_cfg: AngelItem, case_cfg: CaseFile,
            approach: Approach) -> None:
    item = world.get("item")
    culprit.memes["confessed"] += 1
    item.meters["missing"] = 0.0
    item.meters["hidden"] = 0.0
    if approach.kind:
        culprit.memes["relief"] += 1
        world.say(
            f"{culprit.id}'s face crumpled. {culprit.pronoun().capitalize()} looked at the ground and nodded."
        )
        world.say(
            case_cfg.confession.format(culprit=culprit.id, item=item_cfg.label)
        )
    else:
        culprit.memes["fear"] += 1
        world.say(
            f"{culprit.id} hugged {culprit.pronoun('possessive')} elbows and blinked hard. "
            f"The truth came out in a shaky rush."
        )
        world.say(
            case_cfg.confession.format(culprit=culprit.id, item=item_cfg.label)
        )


def adult_resolution(world: World, adult: Entity, detective: Entity, culprit: Entity,
                     helper: Entity, item_cfg: AngelItem, case_cfg: CaseFile,
                     approach: Approach) -> None:
    adult.memes["care"] += 1
    culprit.memes["guilt"] = 0.0
    culprit.memes["relief"] += 1
    detective.memes["justice"] += 1
    helper.memes["relief"] += 1
    item = world.get("item")
    item.meters["safe"] += 1
    if approach.kind:
        adult.memes["trust"] += 1
        world.say(
            f"{adult.label_word.capitalize()} knelt beside the children and checked the {item_cfg.label}. "
            f"{case_cfg.repair}"
        )
        world.say(
            f'"Thank you for telling the truth," {adult.label_word} said. '
            f'"A mistake is easier to mend when honest words come first."'
        )
    else:
        adult.memes["mended_conflict"] += 1
        world.say(
            f"{adult.label_word.capitalize()} came over at once, listened to every voice, and lifted one calm hand."
        )
        world.say(
            f'"We will fix the {item_cfg.label} together," {adult.label_word} said, '
            f'"but next time tell the truth before fear grows bigger than the problem."'
        )
    world.say(
        f"{detective.id} helped {culprit.id} carry the {item_cfg.label} back to the table. "
        f"{helper.id} straightened the cloth, and the yard felt easy again."
    )


def ending_image(world: World, detective: Entity, culprit: Entity, helper: Entity,
                 item_cfg: AngelItem, case_cfg: CaseFile, silo: Entity,
                 approach: Approach, pet: str = "") -> None:
    if pet:
        pet_line = f"Even {pet} circled the crate once, as if checking that the case was closed."
    else:
        pet_line = ""
    if approach.kind:
        world.say(
            f"By evening, {item_cfg.phrase} shone once more beside the {silo.label}, and the mystery was no longer heavy. "
            f"{culprit.id} could smile again because honesty had opened the way home."
        )
    else:
        world.say(
            f"By evening, {item_cfg.phrase} was back in its place beside the {silo.label}. "
            f"The children had learned that truth told early is softer than truth dragged out by fear."
        )
    if pet_line:
        world.say(pet_line)


def tell(item_cfg: AngelItem, case_cfg: CaseFile, approach: Approach,
         detective_name: str = "Nora", detective_gender: str = "girl",
         culprit_name: str = "Ben", culprit_gender: str = "boy",
         helper_name: str = "Mila", helper_gender: str = "girl",
         adult_type: str = "mother", detective_trait: str = "careful",
         culprit_trait: str = "helpful", pet: str = "") -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name, kind="character", type=detective_gender, role="detective",
        traits=[detective_trait], label=detective_name,
    ))
    culprit = world.add(Entity(
        id=culprit_name, kind="character", type=culprit_gender, role="culprit",
        traits=[culprit_trait], label=culprit_name,
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type=helper_gender, role="helper",
        traits=["eager"], label=helper_name,
    ))
    adult = world.add(Entity(
        id="Adult", kind="character", type=adult_type, role="adult", label="the grown-up",
    ))
    silo = world.add(Entity(
        id="silo", kind="place", type="silo", role="place", label="red silo",
    ))
    item = world.add(Entity(
        id="item", kind="thing", type="keepsake", role="item",
        label=item_cfg.label, phrase=item_cfg.phrase, tags=set(item_cfg.tags),
    ))

    opening_scene(world, detective, helper, adult, item_cfg, case_cfg, silo)
    world.para()
    mystery_begins(world, detective, helper, item_cfg, case_cfg)
    inspect_clue(world, detective, helper, culprit, case_cfg)
    world.para()
    follow_trail(world, detective, helper, culprit, item_cfg, case_cfg)
    gentle_question(world, detective, culprit, approach)
    confess(world, culprit, item_cfg, case_cfg, approach)
    world.para()
    adult_resolution(world, adult, detective, culprit, helper, item_cfg, case_cfg, approach)
    ending_image(world, detective, culprit, helper, item_cfg, case_cfg, silo, approach, pet=pet)

    world.facts.update(
        detective=detective,
        culprit=culprit,
        helper=helper,
        adult=adult,
        silo=silo,
        item_cfg=item_cfg,
        case_cfg=case_cfg,
        approach=approach,
        pet=pet,
        outcome="confessed" if approach.kind else "mended_after_adult",
        honesty_helped=approach.kind,
        hidden_found=True,
    )
    return world


ITEMS = {
    "ribbon": AngelItem(
        id="ribbon",
        label="angel ribbon",
        phrase="a white angel ribbon with a gold edge",
        tags={"soft", "trim"},
        fragile=False,
    ),
    "bell": AngelItem(
        id="bell",
        label="angel bell",
        phrase="a tiny angel bell that gave a silver jingle",
        tags={"decor", "sound"},
        fragile=False,
    ),
    "badge": AngelItem(
        id="badge",
        label="angel badge",
        phrase="a little tin angel badge with a bright painted face",
        tags={"decor", "sturdy", "flat"},
        fragile=False,
    ),
}

CASES = {
    "scarecrow": CaseFile(
        id="scarecrow",
        title="The Scarecrow Clue",
        place_phrase="the scarecrow patch near the silo fence",
        chore="trim the scarecrow",
        chore_gerund="children carrying straw and tying ribbons",
        clue="a pinch of straw dust",
        finger_line="a line of straw dust and a loose gold thread",
        hideout="seed sack pocket",
        hideout_phrase="a folded seed sack hanging on a peg",
        use_purpose="to make the scarecrow look friendly",
        accident="The knot slipped and the ribbon dragged in the dirt",
        repair="Together they brushed the ribbon clean and tied it properly where it belonged.",
        confession='"I borrowed the {item} to make the scarecrow look kind," {culprit} said. '
                   '"Then it fell in the dirt, and I hid it because I was ashamed."',
        required_tags={"trim"},
        safe_for_fragile=True,
        tags={"straw", "honesty"},
    ),
    "gift_basket": CaseFile(
        id="gift_basket",
        title="The Basket Clue",
        place_phrase="the bread table by the warm kitchen door",
        chore="decorate the thank-you basket",
        chore_gerund="floury aprons, rolling pins, and soft voices",
        clue="a pale flour print",
        finger_line="a white flour crescent",
        hideout="apron pocket",
        hideout_phrase="a hanging apron with one pocket sagging",
        use_purpose="to make the thank-you basket look special",
        accident="A bit of jam touched the keepsake, and panic rushed in faster than sense",
        repair="They wiped the flour and jam away and set the keepsake where everyone could see it again.",
        confession='"I borrowed the {item} for the thank-you basket," {culprit} said. '
                   '"When I got it sticky, I hid it instead of telling the truth."',
        required_tags={"decor"},
        safe_for_fragile=True,
        tags={"flour", "honesty"},
    ),
    "silo_sign": CaseFile(
        id="silo_sign",
        title="The Silo Sign Clue",
        place_phrase="the paint bench under the silo ladder",
        chore="finish the welcome sign",
        chore_gerund="brushes clinking in jars and bright paint drying in the sun",
        clue="a neat blue fingerprint",
        finger_line="a dot of blue paint shaped exactly like a small fingerprint",
        hideout="tool crate",
        hideout_phrase="a wooden tool crate under the ladder",
        use_purpose="to brighten the welcome sign",
        accident="The paint smeared, and the hiding felt easier than the explaining",
        repair="A damp cloth cleaned the badge, and soon it gleamed safely above the sign again.",
        confession='"I borrowed the {item} for the welcome sign," {culprit} said. '
                   '"Then I got paint on it and hid it in the crate because I did not want anyone to see."',
        required_tags={"decor", "sturdy"},
        safe_for_fragile=False,
        tags={"paint", "silo", "honesty"},
    ),
}

APPROACHES = {
    "gentle": Approach(
        id="gentle",
        tone="gentle",
        opening='"{culprit}," {detective} said softly, "I think this story has a mistake in it, not a villain."',
        ask_line='"Will you tell us what happened?"',
        kind=True,
        tags={"kindness", "honesty"},
    ),
    "firm": Approach(
        id="firm",
        tone="firm",
        opening='"{culprit}," {detective} said, standing very straight, "the clues all point to you."',
        ask_line='"Please tell the truth now before the grown-up has to untangle it for us."',
        kind=False,
        tags={"honesty"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna"]
BOY_NAMES = ["Ben", "Max", "Theo", "Finn", "Sam", "Leo", "Eli", "Noah"]
TRAITS = ["careful", "curious", "patient", "thoughtful", "bright", "steady"]
CULPRIT_TRAITS = ["helpful", "hasty", "eager", "busy", "worried"]
PETS = ["the barn cat", "the little sheepdog", "the gray kitten"]


CURATED = [
    StoryParams(
        item="ribbon",
        case="scarecrow",
        approach="gentle",
        detective_name="Nora",
        detective_gender="girl",
        culprit_name="Ben",
        culprit_gender="boy",
        helper_name="Mia",
        helper_gender="girl",
        adult="mother",
        detective_trait="careful",
        culprit_trait="helpful",
        pet="the barn cat",
    ),
    StoryParams(
        item="bell",
        case="gift_basket",
        approach="gentle",
        detective_name="Theo",
        detective_gender="boy",
        culprit_name="Lucy",
        culprit_gender="girl",
        helper_name="Max",
        helper_gender="boy",
        adult="father",
        detective_trait="thoughtful",
        culprit_trait="eager",
        pet="",
    ),
    StoryParams(
        item="badge",
        case="silo_sign",
        approach="firm",
        detective_name="Ava",
        detective_gender="girl",
        culprit_name="Finn",
        culprit_gender="boy",
        helper_name="Ella",
        helper_gender="girl",
        adult="mother",
        detective_trait="steady",
        culprit_trait="worried",
        pet="the little sheepdog",
    ),
    StoryParams(
        item="badge",
        case="gift_basket",
        approach="gentle",
        detective_name="Leo",
        detective_gender="boy",
        culprit_name="Anna",
        culprit_gender="girl",
        helper_name="Zoe",
        helper_gender="girl",
        adult="father",
        detective_trait="patient",
        culprit_trait="busy",
        pet="the gray kitten",
    ),
]


KNOWLEDGE = {
    "silo": [
        (
            "What is a silo?",
            "A silo is a tall farm building used to store grain or feed. It stands high above the yard, so children often notice it right away."
        )
    ],
    "fingerprint": [
        (
            "What is a fingerprint?",
            "A fingerprint is the tiny pattern of lines on the tip of your finger. If your finger has paint or dust on it, it can leave a print behind."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective notices clues and asks careful questions. A good detective tries to learn the truth instead of guessing too fast."
        )
    ],
    "honesty": [
        (
            "Why is honesty important after a mistake?",
            "Honesty helps people fix a problem while it is still small. When you tell the truth, others can help you mend what went wrong."
        )
    ],
    "kindness": [
        (
            "Why can a kind question help someone tell the truth?",
            "A kind question makes a worried person feel safer. When fear shrinks, honest words can come out more easily."
        )
    ],
    "paint": [
        (
            "Why does paint make a good clue?",
            "Paint is bright and easy to spot. If it gets on a finger, it can leave a clear mark on other things."
        )
    ],
    "flour": [
        (
            "Why can flour show where someone has been?",
            "Flour is powdery and light, so it sticks to hands and clothes. It can leave pale marks that point back to the kitchen."
        )
    ],
    "straw": [
        (
            "Why is straw easy to notice?",
            "Straw is dry, scratchy, and pale, so little bits of it cling to clothes and fingers. That makes it a useful clue."
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "fingerprint", "silo", "honesty", "kindness", "paint", "flour", "straw"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    item = f["item_cfg"]
    case = f["case_cfg"]
    approach = f["approach"]
    return [
        f'Write a detective story for a 3-to-5-year-old that includes the words "angel", "silo", and "finger".',
        f"Tell a gentle farm mystery where {detective.id} notices a clue on someone's finger and solves the case of the missing {item.label}.",
        f'Write a short moral detective story in which a child learns that honesty is better than hiding a mistake after borrowing an {item.label} for {case.use_purpose}.',
        f"Make the detective's approach {approach.tone}, and end with an image that proves the truth has set things right.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    culprit = f["culprit"]
    helper = f["helper"]
    adult = f["adult"]
    item = f["item_cfg"]
    case = f["case_cfg"]
    approach = f["approach"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child detective, {helper.id}, a helper, and {culprit.id}, who hid the {item.label}. The grown-up near the silo helps turn the mystery into a lesson."
        ),
        (
            f"What mystery did {detective.id} solve?",
            f"{detective.id} solved the case of the missing {item.label}. The keepsake had been hidden after {culprit.id} borrowed it for {case.use_purpose}."
        ),
        (
            "What clue pointed to the truth?",
            f"The clue was {case.clue} on the crate and the same kind of mark on {culprit.id}'s finger. That matched the missing keepsake to the chore happening nearby."
        ),
        (
            f"Where was the missing {item.label}?",
            f"It was hidden in {case.hideout_phrase}. The hiding place sat close to the chore, which is why the clue trail made sense."
        ),
    ]
    if approach.kind:
        qa.append(
            (
                f"How did {detective.id} help {culprit.id} tell the truth?",
                f"{detective.id} spoke gently and treated the problem like a mistake, not a crime. That made {culprit.id} feel safe enough to confess instead of hiding behind fear."
            )
        )
    else:
        qa.append(
            (
                f"Why did the grown-up step in before the ending felt calm?",
                f"The detective spoke firmly, so the truth came out with more fear still in it. The grown-up helped slow everyone down and show that honesty should come before worry grows."
            )
        )
    qa.append(
        (
            "What is the moral value in the story?",
            f"The story teaches honesty. When {culprit.id} finally told the truth, the {item.label} could be cleaned, returned, and mended, and everyone's feelings grew lighter."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    case = world.facts["case_cfg"]
    approach = world.facts["approach"]
    tags = {"detective", "fingerprint", "silo", "honesty"} | set(case.tags)
    if approach.kind:
        tags.add("kindness")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(item: AngelItem, case: CaseFile) -> str:
    needs = ", ".join(sorted(case.required_tags))
    has = ", ".join(sorted(item.tags)) if item.tags else "no matching tags"
    if not case.required_tags.issubset(item.tags):
        return (
            f"(No story: {item.phrase} does not fit {case.title.lower()}. "
            f"That case needs an item with tags [{needs}], but this one has [{has}].)"
        )
    if item.fragile and not case.safe_for_fragile:
        return (
            f"(No story: {item.phrase} is too fragile for {case.hideout_phrase}. "
            f"The world refuses a version where the clue setup would break the item.)"
        )
    return "(No story: that combination is not reasonable.)"


ASP_RULES = r"""
fits(Item, Case) :- item(Item), case(Case),
                    required_tags_satisfied(Item, Case),
                    not blocked_fragile(Item, Case).

required_tags_satisfied(Item, Case) :-
    item(Item), case(Case),
    not missing_needed_tag(Item, Case).

missing_needed_tag(Item, Case) :-
    needs(Case, Tag),
    not has(Item, Tag).

blocked_fragile(Item, Case) :-
    fragile(Item),
    not safe_for_fragile(Case).

kind_ending(confessed) :- chosen_approach(gentle).
kind_ending(mended_after_adult) :- chosen_approach(firm).
outcome(O) :- kind_ending(O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.fragile:
            lines.append(asp.fact("fragile", item_id))
        for tag in sorted(item.tags):
            lines.append(asp.fact("has", item_id, tag))
    for case_id, case in CASES.items():
        lines.append(asp.fact("case", case_id))
        if case.safe_for_fragile:
            lines.append(asp.fact("safe_for_fragile", case_id))
        for tag in sorted(case.required_tags):
            lines.append(asp.fact("needs", case_id, tag))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show fits/2."))
    return sorted(set(asp.atoms(model, "fits")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_approach", params.approach)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during random resolve at seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child detective solves the case of a missing angel keepsake near a silo."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (item, case) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item is not None and args.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{args.item}'.)")
    if args.case is not None and args.case not in CASES:
        raise StoryError(f"(No story: unknown case '{args.case}'.)")
    if args.approach is not None and args.approach not in APPROACHES:
        raise StoryError(f"(No story: unknown approach '{args.approach}'.)")

    if args.item and args.case:
        item = ITEMS[args.item]
        case = CASES[args.case]
        if not item_fits_case(item, case):
            raise StoryError(explain_rejection(item, case))

    combos = [
        pair for pair in valid_combos()
        if (args.item is None or pair[0] == args.item)
        and (args.case is None or pair[1] == args.case)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, case_id = rng.choice(sorted(combos))
    approach = args.approach or rng.choice(sorted(APPROACHES))
    detective_gender = rng.choice(["girl", "boy"])
    culprit_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])

    detective_name = _pick_name(rng, detective_gender, avoid=set())
    culprit_name = _pick_name(rng, culprit_gender, avoid={detective_name})
    helper_name = _pick_name(rng, helper_gender, avoid={detective_name, culprit_name})
    adult = args.adult or rng.choice(["mother", "father"])
    detective_trait = rng.choice(TRAITS)
    culprit_trait = rng.choice(CULPRIT_TRAITS)
    pet = rng.choice(PETS + ["", ""])
    return StoryParams(
        item=item_id,
        case=case_id,
        approach=approach,
        detective_name=detective_name,
        detective_gender=detective_gender,
        culprit_name=culprit_name,
        culprit_gender=culprit_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        adult=adult,
        detective_trait=detective_trait,
        culprit_trait=culprit_trait,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{params.item}'.)")
    if params.case not in CASES:
        raise StoryError(f"(No story: unknown case '{params.case}'.)")
    if params.approach not in APPROACHES:
        raise StoryError(f"(No story: unknown approach '{params.approach}'.)")
    item_cfg = ITEMS[params.item]
    case_cfg = CASES[params.case]
    if not item_fits_case(item_cfg, case_cfg):
        raise StoryError(explain_rejection(item_cfg, case_cfg))

    world = tell(
        item_cfg=item_cfg,
        case_cfg=case_cfg,
        approach=APPROACHES[params.approach],
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        culprit_name=params.culprit_name,
        culprit_gender=params.culprit_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        adult_type=params.adult,
        detective_trait=params.detective_trait,
        culprit_trait=params.culprit_trait,
        pet=params.pet,
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
        print(asp_program("", "#show fits/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, case) combos:\n")
        for item_id, case_id in combos:
            print(f"  {item_id:8} {case_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.item} / {p.case} / {p.approach}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
