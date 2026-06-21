#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gag_lesson_learned_rhyme_detective_story.py
======================================================================

A standalone story world about a child detective club, a missing case item, and a
silly gag clue that sends the search the wrong way before honesty puts it right.

This world aims for a TinyStories-style detective tale with:
- a clear case to solve,
- a state-driven middle turn,
- a rhyming gag clue,
- and a gentle lesson learned about jokes, trust, and telling the truth quickly.

Run it
------
    python storyworlds/worlds/gpt-5.4/gag_lesson_learned_rhyme_detective_story.py
    python storyworlds/worlds/gpt-5.4/gag_lesson_learned_rhyme_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/gag_lesson_learned_rhyme_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/gag_lesson_learned_rhyme_detective_story.py --trace --seed 12
    python storyworlds/worlds/gpt-5.4/gag_lesson_learned_rhyme_detective_story.py --asp
    python storyworlds/worlds/gpt-5.4/gag_lesson_learned_rhyme_detective_story.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    locations: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    size: str
    use: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Location:
    id: str
    label: str
    phrase: str
    accepts: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class GagClue:
    id: str
    decoy: str
    rhyme: str
    lead: str
    admit: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class HonestyMode:
    id: str
    quick: bool
    line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def fits(item: MissingItem, location: Location) -> bool:
    return item.size in location.accepts


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            for real_id in sorted(setting.locations):
                real = LOCATIONS[real_id]
                if not fits(item, real):
                    continue
                for gag_id, gag in GAGS.items():
                    if gag.decoy not in setting.locations:
                        continue
                    if gag.decoy == real_id:
                        continue
                    combos.append((setting_id, item_id, real_id, gag_id))
    return combos


def explain_combo_rejection(setting: Setting, item: MissingItem, real: Location, gag: GagClue) -> str:
    if real.id not in setting.locations:
        return (
            f"(No story: {real.phrase} is not part of {setting.place}, so the missing "
            f"{item.label} could not honestly be found there.)"
        )
    if gag.decoy not in setting.locations:
        decoy = LOCATIONS[gag.decoy]
        return (
            f"(No story: the gag rhyme points to {decoy.phrase}, but that place is not in "
            f"{setting.place}, so the detective would not follow that clue there.)"
        )
    if gag.decoy == real.id:
        return (
            f"(No story: the gag clue points to the real hiding place, so it would not be a "
            f"misleading gag at all.)"
        )
    if not fits(item, real):
        return (
            f"(No story: {item.phrase} is too big or awkward for {real.phrase}. Pick a place "
            f"that can really hold the missing object.)"
        )
    return "(No story: this combination does not make a reasonable detective case.)"


def outcome_of(honesty: HonestyMode) -> str:
    return "quick" if honesty.quick else "late"


def propagate(world: World) -> None:
    detective = world.get("detective")
    joker = world.get("joker")
    if world.facts.get("followed_gag") and not world.facts.get("confessed"):
        sig = ("wrong_search", world.facts["gag"].id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["worry"] += 1
            joker.memes["guilt"] += 1
            world.facts["worry_from_wrong_search"] = True
    if detective.memes["worry"] >= THRESHOLD and world.facts.get("confessed"):
        sig = ("repair", world.facts["real_location"].id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["trust"] += 1
            joker.memes["relief"] += 1
    if world.facts.get("found_real"):
        sig = ("case_closed", world.facts["item_cfg"].id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["joy"] += 1
            joker.memes["joy"] += 1
            detective.memes["worry"] = 0.0


def open_case(world: World, detective: Entity, joker: Entity, parent: Entity, item: MissingItem) -> None:
    detective.memes["curious"] += 1
    joker.memes["playful"] += 1
    world.say(
        f"On a bright afternoon, {detective.id} and {joker.id} turned {world.setting.place} "
        f"into a detective office. {world.setting.detail}"
    )
    world.say(
        f"They were getting ready for the Junior Sleuth Parade, and the most important thing "
        f"was {item.phrase}. They needed it because {item.use}."
    )
    world.say(
        f'When {detective.id} reached for it, the spot where it should have been was empty. '
        f'"A case!" {detective.pronoun().capitalize()} whispered.'
    )
    world.facts["opened_case"] = True
    world.facts["parent"] = parent


def plant_gag(world: World, joker: Entity, gag: GagClue) -> None:
    joker.memes["mischief"] += 1
    world.say(
        f"Before the search could begin, {joker.id} remembered a silly gag {joker.pronoun()} "
        f"had made: a folded paper clue with a rhyme on it."
    )
    world.say(f'The note said, "{gag.rhyme}"')
    world.facts["gag_note_seen"] = True


def inspect_decoy(world: World, detective: Entity, joker: Entity, gag: GagClue) -> None:
    decoy = LOCATIONS[gag.decoy]
    world.facts["followed_gag"] = True
    propagate(world)
    world.say(
        f"{detective.id} narrowed {detective.pronoun('possessive')} eyes and followed the clue "
        f"to {decoy.phrase}. {gag.lead}"
    )
    world.say(
        f"But the place held only dust, a marble, and one crumpled leaf. The missing thing was "
        f"not there."
    )
    if detective.memes["worry"] >= THRESHOLD:
        world.say(
            f"{detective.id}'s detective voice went small. This had stopped feeling like a game."
        )
    world.facts["decoy_checked"] = decoy.id


def confess(world: World, detective: Entity, joker: Entity, honesty: HonestyMode, gag: GagClue) -> None:
    world.facts["confessed"] = True
    joker.memes["honesty"] += 1
    world.say(honesty.line)
    world.say(
        f'"I made that rhyme as a gag," {joker.id} admitted. "{gag.admit}"'
    )
    if honesty.quick:
        world.say(
            f"{joker.id} told the truth before the worry grew any bigger."
        )
    else:
        detective.memes["worry"] += 1
        joker.memes["guilt"] += 1
        world.say(
            f"By the time {joker.id} said it, {detective.id} already looked close to tears, "
            f"and the joke felt heavy instead of funny."
        )
    propagate(world)


def solve_real_case(world: World, detective: Entity, joker: Entity, item: MissingItem, real: Location) -> None:
    world.facts["found_real"] = True
    world.get("item").attrs["location"] = real.id
    world.get("item").meters["found"] += 1
    propagate(world)
    world.say(
        f"Now they looked for real clues. A bent corner of paper and a faint ribbon scrap led "
        f"them to {real.phrase}."
    )
    world.say(
        f"There sat {item.phrase}, safe and waiting. {detective.id} lifted it up like a true "
        f"detective closing a case."
    )


def lesson(world: World, detective: Entity, joker: Entity, parent: Entity, item: MissingItem, honesty: HonestyMode) -> None:
    detective.memes["lesson"] += 1
    joker.memes["lesson"] += 1
    if honesty.quick:
        tone = "softly"
        extra = "A joke can wait when a friend is worried."
    else:
        tone = "gently"
        extra = "A gag that makes someone truly scared is not a good joke anymore."
    world.say(
        f"{parent.label_word.capitalize()} had been watching from nearby and knelt beside them. "
        f'"Good detectives love clues," {parent.pronoun()} said {tone}, "but the best detectives '
        f'also tell the truth. {extra}"'
    )
    world.say(
        f'{joker.id} nodded. "{item.label.capitalize()} matters, but so does trust," '
        f'{joker.pronoun()} said.'
    )
    world.say(
        f'{detective.id} nodded too. "Next time," {detective.pronoun()} said, '
        f'"we solve the real case first and save the rhyme for later."'
    )
    world.facts["promised"] = True


def ending(world: World, detective: Entity, joker: Entity, item: MissingItem) -> None:
    detective.memes["calm"] += 1
    joker.memes["calm"] += 1
    world.say(
        f"Soon {item.phrase} was where it belonged, and the parade practice could begin."
    )
    world.say(
        f"{detective.id} pinned on a paper badge, {joker.id} tapped the table like a tiny drum, "
        f"and together they made a new club rule in rhyme:"
    )
    world.say(
        '"First be true in all you do; then let the funny part peek through."'
    )
    world.say(
        f"After that, their detective office felt bright again, and even the word gag sounded "
        f"gentler when it came after the case was solved."
    )


def tell(
    setting: Setting,
    item: MissingItem,
    real_location: Location,
    gag: GagClue,
    honesty: HonestyMode,
    detective_name: str = "Nora",
    detective_gender: str = "girl",
    joker_name: str = "Max",
    joker_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World(setting=setting)
    detective = world.add(
        Entity(
            id=detective_name,
            kind="character",
            type=detective_gender,
            label=detective_name,
            role="detective",
            traits=["careful", "observant"],
        )
    )
    joker = world.add(
        Entity(
            id=joker_name,
            kind="character",
            type=joker_gender,
            label=joker_name,
            role="joker",
            traits=["funny", "playful"],
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    item_ent = world.add(
        Entity(
            id="item",
            kind="thing",
            type="case_item",
            label=item.label,
            attrs={"location": "", "home": real_location.id},
        )
    )
    detective.memes["trust"] = 4.0
    detective.memes["worry"] = 0.0
    joker.memes["guilt"] = 0.0
    joker.memes["relief"] = 0.0
    item_ent.meters["found"] = 0.0
    world.facts.update(
        setting=setting,
        item_cfg=item,
        real_location=real_location,
        gag=gag,
        honesty=honesty,
        outcome=outcome_of(honesty),
        found_real=False,
        followed_gag=False,
        confessed=False,
        promised=False,
        detective=detective,
        joker=joker,
        parent=parent,
    )

    open_case(world, detective, joker, parent, item)
    world.para()
    plant_gag(world, joker, gag)
    inspect_decoy(world, detective, joker, gag)
    world.para()
    confess(world, detective, joker, honesty, gag)
    solve_real_case(world, detective, joker, item, real_location)
    world.para()
    lesson(world, detective, joker, parent, item, honesty)
    ending(world, detective, joker, item)
    return world


SETTINGS = {
    "clubhouse": Setting(
        id="clubhouse",
        place="the clubhouse",
        detail="A cardboard map hung on the wall, and a toy lantern sat beside a stack of case files.",
        locations={"shelf", "hatbox", "bench"},
        tags={"clubhouse", "detective"},
    ),
    "porch": Setting(
        id="porch",
        place="the back porch",
        detail="A striped rug lay by the door, and a row of boots waited under a low bench.",
        locations={"rug", "bench", "hatbox"},
        tags={"porch", "detective"},
    ),
    "reading_nook": Setting(
        id="reading_nook",
        place="the reading nook",
        detail="Pillows made a tiny office, and a paper sign said CASES OPEN in crooked letters.",
        locations={"shelf", "bench", "rug"},
        tags={"nook", "detective"},
    ),
}

ITEMS = {
    "badge_box": MissingItem(
        id="badge_box",
        label="badge box",
        phrase="the shiny badge box",
        size="small",
        use="the parade could not start until each detective had a badge",
        tags={"badge", "parade"},
    ),
    "magnifier": MissingItem(
        id="magnifier",
        label="magnifying glass",
        phrase="the big plastic magnifying glass",
        size="medium",
        use="every detective wanted a turn looking through it for clues",
        tags={"magnifier", "detective"},
    ),
    "notebook": MissingItem(
        id="notebook",
        label="clue notebook",
        phrase="the red clue notebook",
        size="small",
        use="it held every suspect list and every important scribble",
        tags={"notebook", "detective"},
    ),
}

LOCATIONS = {
    "shelf": Location(
        id="shelf",
        label="shelf",
        phrase="the low shelf beside the lantern",
        accepts={"small", "medium"},
        tags={"shelf"},
    ),
    "hatbox": Location(
        id="hatbox",
        label="hat box",
        phrase="the round hat box",
        accepts={"small"},
        tags={"hat", "box"},
    ),
    "bench": Location(
        id="bench",
        label="bench",
        phrase="under the wooden bench",
        accepts={"small", "medium"},
        tags={"bench"},
    ),
    "rug": Location(
        id="rug",
        label="rug",
        phrase="under the striped rug",
        accepts={"small"},
        tags={"rug"},
    ),
}

GAGS = {
    "hat_cat": GagClue(
        id="hat_cat",
        decoy="hatbox",
        rhyme="If you're a sleuthy acrobat, inspect the hat and question the cat!",
        lead="The rhyme made it sound as if a sneaky cat had hidden the prize.",
        admit="I thought a detective rhyme would sound funny, but I did not mean to make the case feel scary.",
        tags={"rhyme", "hat", "gag"},
    ),
    "shelf_elf": GagClue(
        id="shelf_elf",
        decoy="shelf",
        rhyme="Check the shelf by the tiny elf; crack the case all by yourself!",
        lead="The clue sounded bold enough to feel almost official.",
        admit="I only wanted to make you laugh with a silly fake clue.",
        tags={"rhyme", "shelf", "gag"},
    ),
    "rug_bug": GagClue(
        id="rug_bug",
        decoy="rug",
        rhyme="Give the room a shrug and look under the rug for a whispering bug!",
        lead="For one moment, even the wrong clue felt clever.",
        admit="I should have said it was a joke right away instead of letting you worry.",
        tags={"rhyme", "rug", "gag"},
    ),
}

HONESTY = {
    "quick": HonestyMode(
        id="quick",
        quick=True,
        line="Max bit his lip almost at once.",
        tags={"honesty", "quick"},
    ),
    "late": HonestyMode(
        id="late",
        quick=False,
        line="Max shuffled his shoes and waited a little too long.",
        tags={"honesty", "late"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ella", "Zoe", "Ava", "Ruby", "June"]
BOY_NAMES = ["Max", "Ben", "Leo", "Theo", "Finn", "Sam", "Eli", "Jack"]


@dataclass
class StoryParams:
    setting: str
    item: str
    real_location: str
    gag: str
    honesty: str
    detective_name: str
    detective_gender: str
    joker_name: str
    joker_gender: str
    parent: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "detective": [
        (
            "What does a detective do?",
            "A detective looks carefully for clues and tries to solve a mystery. Good detectives pay attention and tell the truth about what they find."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words sound alike, like cat and hat. Rhymes can make a clue feel playful and easy to remember."
        )
    ],
    "gag": [
        (
            "What is a gag?",
            "A gag is a silly joke or trick meant to make people laugh. A gag should stop being used if it makes someone worried or upset."
        )
    ],
    "magnifier": [
        (
            "What is a magnifying glass for?",
            "A magnifying glass makes small things look bigger, so it helps you inspect tiny details. Detectives in stories often use one to study clues."
        )
    ],
    "notebook": [
        (
            "Why does a detective keep a notebook?",
            "A notebook helps a detective remember clues, ideas, and questions. Writing things down keeps the case from getting mixed up."
        )
    ],
    "badge": [
        (
            "Why do clubs use badges?",
            "Badges can show who belongs to a club or team. They also make a pretend job, like detective work, feel special and official."
        )
    ],
    "honesty": [
        (
            "Why is honesty important in a mystery?",
            "Honesty matters because false clues waste time and can hurt trust. A true answer helps everyone solve the real problem faster."
        )
    ],
}

KNOWLEDGE_ORDER = ["detective", "rhyme", "gag", "magnifier", "notebook", "badge", "honesty"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    joker = f["joker"]
    item = f["item_cfg"]
    gag = f["gag"]
    outcome = f["outcome"]
    base = (
        f'Write a gentle detective story for a 3-to-5-year-old about a missing {item.label}, '
        f'a rhyming gag clue, and a lesson about honesty. Include the word "gag".'
    )
    if outcome == "quick":
        return [
            base,
            f"Tell a detective story where {joker.id} makes a silly rhyme as a gag, but confesses quickly when {detective.id} starts to worry, and together they solve the real case.",
            f'Write a mystery with a playful rhyme clue that turns out to be a joke, then end with the children making a wiser rule about telling the truth first.',
        ]
    return [
        base,
        f"Tell a detective story where {joker.id} waits too long to admit a gag clue was fake, so {detective.id} grows worried before the truth comes out and the real clue is found.",
        f'Write a gentle mystery that teaches a lesson: funny rhymes are fine, but not when they scare a friend or hide the real answer.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    joker = f["joker"]
    parent = f["parent"]
    item = f["item_cfg"]
    gag = f["gag"]
    real = f["real_location"]
    decoy = LOCATIONS[gag.decoy]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two children playing detective, {detective.id} and {joker.id}. Their {parent.label_word} stays nearby and helps them think about what good detectives should do."
        ),
        (
            f"What was missing?",
            f"The missing thing was {item.phrase}. It mattered because {item.use}."
        ),
        (
            "What was the rhyming clue?",
            f'The clue said, "{gag.rhyme}" It sounded clever, but it was really a silly gag instead of a true clue.'
        ),
        (
            f"Why did {detective.id} get worried?",
            f"{detective.id} followed the rhyme to {decoy.phrase}, but the missing {item.label} was not there. That false lead made the case feel real and made the game stop feeling fun."
        ),
    ]
    if outcome == "quick":
        qa.append(
            (
                f"What did {joker.id} do to help once the joke went too far?",
                f"{joker.id} confessed quickly that the rhyme was a gag and not a real clue. Telling the truth early kept the worry from growing bigger and helped the children search honestly."
            )
        )
    else:
        qa.append(
            (
                f"What made the lesson stronger in this story?",
                f"{joker.id} waited too long to confess, so {detective.id} became much more worried first. That is why the joke felt heavy instead of funny by the time the truth came out."
            )
        )
    qa.append(
        (
            "Where was the missing item really found?",
            f"They found it at {real.phrase}. Real clues led them there after the fake rhyme was confessed."
        )
    )
    qa.append(
        (
            "What lesson did they learn?",
            f"They learned that funny rhymes and a gag can wait until the real problem is solved. Trust matters in a mystery, so the truth should come first."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    item = f["item_cfg"]
    tags: set[str] = {"detective", "rhyme", "gag", "honesty"}
    tags |= set(item.tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="clubhouse",
        item="badge_box",
        real_location="bench",
        gag="shelf_elf",
        honesty="quick",
        detective_name="Nora",
        detective_gender="girl",
        joker_name="Max",
        joker_gender="boy",
        parent="mother",
    ),
    StoryParams(
        setting="porch",
        item="notebook",
        real_location="bench",
        gag="hat_cat",
        honesty="late",
        detective_name="Mia",
        detective_gender="girl",
        joker_name="Leo",
        joker_gender="boy",
        parent="father",
    ),
    StoryParams(
        setting="reading_nook",
        item="magnifier",
        real_location="shelf",
        gag="rug_bug",
        honesty="quick",
        detective_name="Ella",
        detective_gender="girl",
        joker_name="Finn",
        joker_gender="boy",
        parent="mother",
    ),
    StoryParams(
        setting="clubhouse",
        item="notebook",
        real_location="hatbox",
        gag="shelf_elf",
        honesty="late",
        detective_name="Ava",
        detective_gender="girl",
        joker_name="Sam",
        joker_gender="boy",
        parent="father",
    ),
]


ASP_RULES = r"""
fits(Item, Loc) :- item(Item), location(Loc), accepts(Loc, Size), size(Item, Size).
present(Set, Loc) :- setting(Set), location(Loc), in_setting(Set, Loc).
valid(Set, Item, Real, Gag) :- setting(Set), item(Item), location(Real), gag(Gag),
                               present(Set, Real), fits(Item, Real),
                               decoy(Gag, Dec), present(Set, Dec), Dec != Real.

outcome(quick) :- honesty_choice(quick).
outcome(late)  :- honesty_choice(late).

#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for loc in sorted(setting.locations):
            lines.append(asp.fact("in_setting", sid, loc))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("size", iid, item.size))
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        for size in sorted(loc.accepts):
            lines.append(asp.fact("accepts", lid, size))
    for gid, gag in GAGS.items():
        lines.append(asp.fact("gag", gid))
        lines.append(asp.fact("decoy", gid, gag.decoy))
    for hid in HONESTY:
        lines.append(asp.fact("honesty", hid))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(honesty_id: str) -> str:
    import asp

    model = asp.one_model(asp_program(asp.fact("honesty_choice", honesty_id)))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a detective game, a rhyming gag clue, and a lesson about honesty."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--real-location", choices=LOCATIONS)
    ap.add_argument("--gag", choices=GAGS)
    ap.add_argument("--honesty", choices=HONESTY)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.item and args.real_location and args.gag:
        setting = SETTINGS[args.setting]
        item = ITEMS[args.item]
        real = LOCATIONS[args.real_location]
        gag = GAGS[args.gag]
        if (args.setting, args.item, args.real_location, args.gag) not in valid_combos():
            raise StoryError(explain_combo_rejection(setting, item, real, gag))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.real_location is None or combo[2] == args.real_location)
        and (args.gag is None or combo[3] == args.gag)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, real_id, gag_id = rng.choice(sorted(combos))
    honesty_id = args.honesty or rng.choice(sorted(HONESTY))
    detective_gender = rng.choice(["girl", "boy"])
    joker_gender = "boy" if detective_gender == "girl" else "girl"
    detective_name = _pick_name(rng, detective_gender)
    joker_name = _pick_name(rng, joker_gender, avoid=detective_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        item=item_id,
        real_location=real_id,
        gag=gag_id,
        honesty=honesty_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        joker_name=joker_name,
        joker_gender=joker_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        item = ITEMS[params.item]
        real = LOCATIONS[params.real_location]
        gag = GAGS[params.gag]
        honesty = HONESTY[params.honesty]
    except KeyError as exc:
        raise StoryError(f"(Invalid story parameter: {exc.args[0]}.)") from exc

    if (params.setting, params.item, params.real_location, params.gag) not in valid_combos():
        raise StoryError(explain_combo_rejection(setting, item, real, gag))

    world = tell(
        setting=setting,
        item=item,
        real_location=real,
        gag=gag,
        honesty=honesty,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        joker_name=params.joker_name,
        joker_gender=params.joker_gender,
        parent_type=params.parent,
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


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid combos match ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    for honesty_id in HONESTY:
        py = outcome_of(HONESTY[honesty_id])
        asp_res = asp_outcome(honesty_id)
        if py != asp_res:
            rc = 1
            print(f"MISMATCH in honesty outcome for {honesty_id}: python={py} asp={asp_res}")
    if rc == 0:
        print("OK: honesty outcomes match.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke-tested normal generation.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, item, real_location, gag) combos:\n")
        for setting_id, item_id, real_id, gag_id in combos:
            print(f"  {setting_id:12} {item_id:10} {real_id:10} {gag_id}")
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
                f"### {p.detective_name} & {p.joker_name}: {p.item} in {p.setting} "
                f"({p.gag}, honesty={p.honesty})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
