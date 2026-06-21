#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/culture_cocaine_bravery_whodunit.py
==============================================================

A small storyworld about a tiny whodunit at a neighborhood culture fair.

Premise
-------
A child arrives at a community event full of music, costumes, and food from many
families. Then a packet of white powder is found near a special festival object.
Some adults whisper the scary word "cocaine." A brave child does not touch the
powder, but notices clues, asks for help, and helps the organizer discover what
really happened.

This world is deliberately narrow and constraint-checked:
- the powder must have a plausible innocent source,
- the clue must actually point to the culprit,
- the child solves the mystery by careful observation and calling an adult,
  never by handling the powder.

The style aims at a gentle whodunit: a puzzle, rising worry, brave noticing, and
a clear ending image that proves the misunderstanding is resolved.

Run it
------
python storyworlds/worlds/gpt-5.4/culture_cocaine_bravery_whodunit.py
python storyworlds/worlds/gpt-5.4/culture_cocaine_bravery_whodunit.py --all
python storyworlds/worlds/gpt-5.4/culture_cocaine_bravery_whodunit.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/culture_cocaine_bravery_whodunit.py --qa --json
python storyworlds/worlds/gpt-5.4/culture_cocaine_bravery_whodunit.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_MIN = 5


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
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
        female = {"girl", "woman", "mother", "aunt", "teacher"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Festival:
    id: str
    place: str
    culture_line: str
    feature: str
    prized_object: str
    closing_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PowderSource:
    id: str
    label: str
    innocent_name: str
    suspect_line: str
    true_line: str
    trace_mark: str
    leaves_mark: str
    danger_level: int
    tags: set[str] = field(default_factory=set)


@dataclass
class SuspectRole:
    id: str
    title: str
    task: str
    reason_near_object: str
    item: str
    clue_mark: str
    clue_sentence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    action_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    festival: str
    powder: str
    culprit_role: str
    helper: str
    investigator_name: str
    investigator_gender: str
    organizer_type: str
    bravery: int
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


def valid_combo(powder: PowderSource, culprit: SuspectRole) -> bool:
    return powder.leaves_mark == culprit.clue_mark


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for powder_id, powder in POWDERS.items():
        for culprit_id, culprit in SUSPECTS.items():
            if valid_combo(powder, culprit):
                combos.append((powder_id, culprit_id))
    return combos


def explain_rejection(powder: PowderSource, culprit: SuspectRole) -> str:
    return (
        f"(No story: {powder.innocent_name} leaves {powder.leaves_mark}, but a "
        f"{culprit.title} would leave {culprit.clue_mark}. The clue would not fairly "
        f"identify the culprit, so this whodunit is rejected.)"
    )


def introduce(world: World, child: Entity, organizer: Entity, festival: Festival) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} went with {child.pronoun('possessive')} {organizer.label_word} to "
        f"{festival.place} for a culture fair. {festival.culture_line}"
    )
    world.say(
        f"There were songs, bright cloth, warm food, and people hurrying about to get "
        f"{festival.feature} ready."
    )
    world.say(
        f"{child.id} liked to notice little things, the way a story detective does."
    )


def show_object(world: World, child: Entity, festival: Festival) -> None:
    world.say(
        f"In the middle of the hall stood {festival.prized_object}, waiting for the opening walk."
    )
    world.say(
        f"{child.id} stopped to admire it and wondered who would get everything ready on time."
    )


def discover_powder(
    world: World,
    child: Entity,
    organizer: Entity,
    powder: PowderSource,
    festival: Festival,
) -> None:
    world.para()
    world.get("powder").meters["present"] += 1
    world.get("object").meters["at_risk"] += 1
    child.memes["worry"] += 1
    world.say(
        f"Then {child.id} saw a little torn packet on the floor beside {festival.prized_object}."
    )
    world.say(
        f"A white dust had spilled out in a crooked line. One grown-up whispered, "
        f'"Could it be cocaine?"'
    )
    world.say(
        f"{organizer.label_word.capitalize()} quickly moved everyone back and said not to touch the powder."
    )
    world.facts["panic_word"] = "cocaine"


def suspect_round(world: World, festival: Festival) -> None:
    names = []
    for sid in world.facts["suspect_ids"]:
        suspect = world.get(sid)
        names.append(f"{suspect.id} the {suspect.attrs['title']}")
    lineup = ", ".join(names[:-1]) + f", and {names[-1]}" if len(names) > 1 else names[0]
    world.say(
        f"Near the display had been {lineup}. It felt like the beginning of a very small whodunit."
    )


def brave_choice(world: World, child: Entity, helper: Helper) -> None:
    world.para()
    if child.memes["bravery"] >= BRAVERY_MIN:
        child.memes["steady"] += 1
        world.say(
            f"{child.id}'s stomach gave a little flip, but bravery did not make "
            f"{child.pronoun('object')} rush in. It helped {child.pronoun('object')} stand still, "
            f"look carefully, and remember the safety rule."
        )
    else:
        world.say(
            f"{child.id} felt nervous and almost hid behind a chair, but stayed close enough to look."
        )
    world.say(
        f'"Do not touch it," {child.id} told {helper.label}. "But I think I see a clue."'
    )


def observe_clue(world: World, child: Entity, culprit: SuspectRole, powder: PowderSource) -> None:
    child.memes["focus"] += 1
    world.get("powder").attrs["mark_seen"] = culprit.clue_mark
    world.say(culprit.clue_sentence)
    world.say(
        f"The powder itself looked scary, but the mark in it looked even more useful."
    )
    world.facts["seen_mark"] = culprit.clue_mark
    world.facts["source_trace"] = powder.trace_mark


def ask_for_help(world: World, child: Entity, organizer: Entity, helper: Helper) -> None:
    child.memes["help_seeking"] += 1
    organizer.memes["trust_child"] += 1
    world.say(
        f"{child.id} did not try to solve the whole mystery alone. "
        f"{helper.action_line}, and then they called {organizer.label_word} over."
    )
    world.say(
        f'"Please look at the floor marks," {child.id} said. "They might tell us who was here."'
    )


def reveal(
    world: World,
    child: Entity,
    organizer: Entity,
    culprit_ent: Entity,
    powder: PowderSource,
    festival: Festival,
) -> None:
    world.para()
    culprit_ent.memes["embarrassed"] += 1
    world.get("powder").meters["identified"] += 1
    world.get("object").meters["safe"] += 1
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    organizer.memes["relief"] += 1
    world.say(
        f"{organizer.label_word.capitalize()} followed the clue to {culprit_ent.id}, "
        f"who was holding {culprit_ent.attrs['item']}."
    )
    world.say(
        f"{culprit_ent.id} blinked, then admitted what had happened. {powder.true_line}"
    )
    world.say(
        f"It was not cocaine at all. It was {powder.innocent_name}, spilled by mistake while "
        f"{culprit_ent.pronoun()} worked."
    )
    world.say(
        f"Everyone let out a long breath, and {festival.prized_object} was moved away while the floor was cleaned."
    )


def close_story(
    world: World,
    child: Entity,
    organizer: Entity,
    festival: Festival,
) -> None:
    world.para()
    child.memes["lesson"] += 1
    world.say(
        f'{organizer.label_word.capitalize()} knelt beside {child.id} and smiled. '
        f'"That was brave," {organizer.pronoun()} said. "You stayed calm, noticed the clue, and got help."'
    )
    world.say(
        f"{child.id} smiled back. {festival.closing_image}"
    )
    world.say(
        "The mystery was over, and the brave part had not been touching danger. "
        "The brave part had been thinking clearly when everyone else was frightened."
    )


def tell(
    festival: Festival,
    powder: PowderSource,
    culprit: SuspectRole,
    helper: Helper,
    investigator_name: str,
    investigator_gender: str,
    organizer_type: str,
    bravery: int,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=investigator_name,
            kind="character",
            type=investigator_gender,
            role="investigator",
            label=investigator_name,
        )
    )
    organizer = world.add(
        Entity(
            id="Organizer",
            kind="character",
            type=organizer_type,
            role="organizer",
            label="the organizer",
        )
    )
    powder_ent = world.add(Entity(id="powder", type="powder", label="the white powder"))
    object_ent = world.add(Entity(id="object", type="display", label=festival.prized_object))
    child.memes["bravery"] = float(bravery)
    world.facts["festival"] = festival
    world.facts["powder_cfg"] = powder
    world.facts["helper_cfg"] = helper
    world.facts["culprit_cfg"] = culprit
    world.facts["investigator"] = child
    world.facts["organizer"] = organizer

    suspect_ids: list[str] = []
    decoys = [s for s in SUSPECTS.values() if s.id != culprit.id]
    random_decoys = sorted(decoys, key=lambda s: s.id)[:2]
    cast = [culprit] + random_decoys
    for idx, suspect_role in enumerate(cast, 1):
        name = world.facts.get(f"suspect_name_{idx}")
        if not name:
            name = suspect_role.title.capitalize()
        ent = world.add(
            Entity(
                id=name,
                kind="character",
                type="woman" if idx % 2 else "man",
                role="suspect",
                label=name,
                attrs={
                    "title": suspect_role.title,
                    "task": suspect_role.task,
                    "item": suspect_role.item,
                    "reason": suspect_role.reason_near_object,
                    "clue_mark": suspect_role.clue_mark,
                },
                tags=set(suspect_role.tags),
            )
        )
        if suspect_role.id == culprit.id:
            world.facts["culprit"] = ent
        suspect_ids.append(ent.id)
    world.facts["suspect_ids"] = suspect_ids

    introduce(world, child, organizer, festival)
    show_object(world, child, festival)
    discover_powder(world, child, organizer, powder, festival)
    suspect_round(world, festival)
    brave_choice(world, child, helper)
    observe_clue(world, child, culprit, powder)
    ask_for_help(world, child, organizer, helper)
    reveal(world, child, organizer, world.facts["culprit"], powder, festival)
    close_story(world, child, organizer, festival)

    world.facts.update(
        bravery_used=child.memes["bravery"] >= BRAVERY_MIN,
        solved=world.get("powder").meters["identified"] >= THRESHOLD,
        safe=world.get("object").meters["safe"] >= THRESHOLD,
    )
    return world


FESTIVALS = {
    "parade": Festival(
        id="parade",
        place="the neighborhood center",
        culture_line="Families had brought dances, songs, and recipes from many parts of the world, and each table showed a piece of family culture.",
        feature="the parade dragon",
        prized_object="a long red parade dragon with paper scales",
        closing_image="Soon the dragon swayed through the room again, and its paper scales flashed under the lights.",
        tags={"culture", "festival"},
    ),
    "market": Festival(
        id="market",
        place="the school gym",
        culture_line="Grandparents, cousins, and neighbors had set up a culture market with woven cloth, drums, and stories from home.",
        feature="the welcome lantern arch",
        prized_object="a lantern arch made with painted stars",
        closing_image="Soon the lantern arch glowed over the doorway, and children walked under it with round, happy eyes.",
        tags={"culture", "festival"},
    ),
    "museum_day": Festival(
        id="museum_day",
        place="the town museum hall",
        culture_line="The museum had opened its doors for a culture day, with masks, music, and old family crafts to share.",
        feature="the mask table",
        prized_object="a giant festival mask with gold ribbons",
        closing_image="Soon the giant mask stood proud again, and the gold ribbons trembled when the drummers began.",
        tags={"culture", "museum"},
    ),
}

POWDERS = {
    "rice_flour": PowderSource(
        id="rice_flour",
        label="rice flour",
        innocent_name="rice flour for festival sweets",
        suspect_line='Aunties glanced at one another and nobody liked hearing the word "cocaine" in a place meant for songs and snacks.',
        true_line="A bag of rice flour for sweet dumplings had split open after brushing a sharp chair corner.",
        trace_mark="softy white dust",
        leaves_mark="floury handprint",
        danger_level=1,
        tags={"food", "powder"},
    ),
    "chalk": PowderSource(
        id="chalk",
        label="stage chalk",
        innocent_name="stage chalk for dance shoes",
        suspect_line='The grown-ups frowned; even a rumor about cocaine made the room feel suddenly cold.',
        true_line="A packet of stage chalk for dance shoes had torn while someone hurried past the display.",
        trace_mark="powdery shoe print",
        leaves_mark="powdery footprint",
        danger_level=1,
        tags={"dance", "powder"},
    ),
    "cornstarch": PowderSource(
        id="cornstarch",
        label="cornstarch",
        innocent_name="cornstarch for puppet paste",
        suspect_line='The scary word "cocaine" spread faster than the powder itself, and children were gently moved back.',
        true_line="A bag of cornstarch for puppet paste had slipped from a stack of craft things.",
        trace_mark="sticky paste smear",
        leaves_mark="pastey finger streak",
        danger_level=1,
        tags={"craft", "powder"},
    ),
}

SUSPECTS = {
    "baker": SuspectRole(
        id="baker",
        title="baker",
        task="carrying a tray for the sweets table",
        reason_near_object="to bring snacks to the opening line",
        item="a dented mixing bowl",
        clue_mark="floury handprint",
        clue_sentence="Beside the packet, there was a pale handprint on the shiny floor, as if someone with baking flour on their fingers had steadied themselves.",
        tags={"food", "kitchen"},
    ),
    "dancer": SuspectRole(
        id="dancer",
        title="dancer",
        task="practicing a quick spin before the music started",
        reason_near_object="to line up for the first dance",
        item="soft dance shoes dusted at the soles",
        clue_mark="powdery footprint",
        clue_sentence="Across the floor ran a half-moon footprint, the kind a soft shoe might leave after stepping in powder and turning fast.",
        tags={"dance", "shoe"},
    ),
    "puppeteer": SuspectRole(
        id="puppeteer",
        title="puppeteer",
        task="fixing a paper puppet at the craft table",
        reason_near_object="to carry decorations toward the front",
        item="a glue brush and a paper puppet",
        clue_mark="pastey finger streak",
        clue_sentence="On the leg of the display, a white finger streak shone where someone had touched it with sticky craft paste on their hand.",
        tags={"craft", "puppet"},
    ),
    "drummer": SuspectRole(
        id="drummer",
        title="drummer",
        task="testing a drum strap",
        reason_near_object="to warm up beside the front line",
        item="a polished hand drum",
        clue_mark="drum-string fiber",
        clue_sentence="A tiny string fiber clung to the packet, as if it had brushed against a drum strap.",
        tags={"music", "drum"},
    ),
}

HELPERS = {
    "guard": Helper(
        id="guard",
        label="the hall guard",
        action_line="The hall guard bent down from a safe distance to block the path with a rope stand",
        tags={"adult_help"},
    ),
    "teacher": Helper(
        id="teacher",
        label="the dance teacher",
        action_line="The dance teacher gently waved younger children back",
        tags={"adult_help"},
    ),
    "janitor": Helper(
        id="janitor",
        label="the janitor",
        action_line="The janitor set out a bright warning cone beside the spill",
        tags={"adult_help"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Zuri", "Asha", "Eva", "Rina", "Sana"]
BOY_NAMES = ["Leo", "Milo", "Omar", "Tariq", "Ben", "Noah", "Samir", "Eli"]

KNOWLEDGE = {
    "culture": [
        (
            "What does culture mean?",
            "Culture means the songs, foods, stories, clothes, and ways of celebrating that people share with one another. Families can have different cultures, and fairs can help people learn from each other."
        )
    ],
    "cocaine": [
        (
            "What is cocaine?",
            "Cocaine is a dangerous illegal drug. If a child ever sees an unknown powder, the safe thing is not to touch it and to tell a grown-up right away."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery does not mean grabbing danger with your hands. It means staying calm, making a safe choice, and asking for help even when something feels scary."
        )
    ],
    "clue": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you figure out what happened. Good clues come from real things you can notice, like marks, footprints, or where an object was left."
        )
    ],
    "powder": [
        (
            "Why should you not touch unknown powder?",
            "Because you do not know what it is, and some powders can be unsafe. A grown-up with the right tools should check it instead."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["investigator"]
    festival = f["festival"]
    culprit = f["culprit_cfg"]
    powder = f["powder_cfg"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old that includes the words "culture" and "cocaine" and shows bravery as careful thinking.',
        f"Tell a mystery story where {child.id} is at {festival.place} for a culture celebration, hears a scary whisper about cocaine, and bravely helps an adult solve the puzzle.",
        f"Write a small whodunit where the real answer is that the white powder came from a {culprit.title}'s {powder.innocent_name}, not from anything criminal."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["investigator"]
    organizer = f["organizer"]
    festival = f["festival"]
    powder = f["powder_cfg"]
    culprit = f["culprit_cfg"]
    culprit_ent = f["culprit"]
    helper = f["helper_cfg"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child at a culture fair, and {organizer.label_word} who listens when the mystery begins."
        ),
        (
            "What was the problem at the fair?",
            f"A torn packet of white powder was found beside {festival.prized_object}. The word cocaine was whispered, so everyone worried the fair might not be safe."
        ),
        (
            f"How did {child.id} show bravery?",
            f"{child.id} did not touch the powder or rush in. {child.pronoun().capitalize()} stayed calm, noticed a clue, and asked adults for help, which is the safest kind of bravery."
        ),
        (
            "What clue solved the mystery?",
            f"The clue was {f['seen_mark']}. That matched the kind of mark a {culprit.title} would leave, so it pointed the organizer toward the right person."
        ),
        (
            "Who spilled the powder, and what was it really?",
            f"It was {culprit_ent.id} the {culprit.title}, and the powder was really {powder.innocent_name}. It looked scary at first, but the clue showed it came from ordinary fair work."
        ),
        (
            "How did the story end?",
            f"The organizer learned it was not cocaine, the spill was cleaned up, and {festival.prized_object} was safe again. The fair could begin, and everyone felt relieved."
        ),
    ]
    if helper.id:
        out.append(
            (
                f"Why did {child.id} speak to {helper.label}?",
                f"{child.id} wanted grown-up help before anyone got too close to the spill. That helped keep people safe while the clue was checked."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = ["culture", "cocaine", "bravery", "clue", "powder"]
    out: list[tuple[str, str]] = []
    for tag in tags:
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
    for ent in list(world.entities.values()):
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  solved={world.facts.get('solved')} safe={world.facts.get('safe')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        festival="parade",
        powder="chalk",
        culprit_role="dancer",
        helper="teacher",
        investigator_name="Maya",
        investigator_gender="girl",
        organizer_type="mother",
        bravery=7,
    ),
    StoryParams(
        festival="market",
        powder="rice_flour",
        culprit_role="baker",
        helper="guard",
        investigator_name="Leo",
        investigator_gender="boy",
        organizer_type="father",
        bravery=6,
    ),
    StoryParams(
        festival="museum_day",
        powder="cornstarch",
        culprit_role="puppeteer",
        helper="janitor",
        investigator_name="Asha",
        investigator_gender="girl",
        organizer_type="teacher",
        bravery=8,
    ),
]


ASP_RULES = r"""
valid(Powder, Culprit) :- powder(Powder), suspect(Culprit),
                          leaves_mark(Powder, M), clue_mark(Culprit, M).

brave_case :- bravery(B), bravery_min(M), B >= M.
solved :- valid(chosen_powder, chosen_culprit), brave_case.
safe :- solved.
outcome(resolved) :- solved, safe.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("bravery_min", BRAVERY_MIN))
    for powder_id, powder in POWDERS.items():
        lines.append(asp.fact("powder", powder_id))
        lines.append(asp.fact("leaves_mark", powder_id, powder.leaves_mark))
    for culprit_id, culprit in SUSPECTS.items():
        lines.append(asp.fact("suspect", culprit_id))
        lines.append(asp.fact("clue_mark", culprit_id, culprit.clue_mark))
    for festival_id in FESTIVALS:
        lines.append(asp.fact("festival", festival_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_powder", params.powder),
            asp.fact("chosen_culprit", params.culprit_role),
            asp.fact("bravery", params.bravery),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    powder = POWDERS.get(params.powder)
    culprit = SUSPECTS.get(params.culprit_role)
    if powder is None or culprit is None:
        return "?"
    if valid_combo(powder, culprit) and params.bravery >= BRAVERY_MIN:
        return "resolved"
    return "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "culture" not in sample.story.lower() or "cocaine" not in sample.story.lower():
        raise StoryError("(Smoke test failed: generated story was missing expected content.)")


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for seed in range(12):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a gentle culture-fair whodunit with a brave child and a scary powder misunderstanding."
    )
    ap.add_argument("--festival", choices=FESTIVALS)
    ap.add_argument("--powder", choices=POWDERS)
    ap.add_argument("--culprit-role", choices=SUSPECTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--organizer", choices=["mother", "father", "teacher"])
    ap.add_argument("--bravery", type=int, choices=list(range(3, 10)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid powder/culprit pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.powder and args.culprit_role:
        powder = POWDERS[args.powder]
        culprit = SUSPECTS[args.culprit_role]
        if not valid_combo(powder, culprit):
            raise StoryError(explain_rejection(powder, culprit))

    combos = [
        combo
        for combo in valid_combos()
        if (args.powder is None or combo[0] == args.powder)
        and (args.culprit_role is None or combo[1] == args.culprit_role)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    powder_id, culprit_id = rng.choice(sorted(combos))
    festival_id = args.festival or rng.choice(sorted(FESTIVALS))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    organizer_type = args.organizer or rng.choice(["mother", "father", "teacher"])
    bravery = args.bravery if args.bravery is not None else rng.randint(BRAVERY_MIN, 9)
    investigator_gender = rng.choice(["girl", "boy"])
    investigator_name = rng.choice(GIRL_NAMES if investigator_gender == "girl" else BOY_NAMES)
    return StoryParams(
        festival=festival_id,
        powder=powder_id,
        culprit_role=culprit_id,
        helper=helper_id,
        investigator_name=investigator_name,
        investigator_gender=investigator_gender,
        organizer_type=organizer_type,
        bravery=bravery,
    )


def generate(params: StoryParams) -> StorySample:
    if params.festival not in FESTIVALS:
        raise StoryError(f"(Unknown festival: {params.festival})")
    if params.powder not in POWDERS:
        raise StoryError(f"(Unknown powder: {params.powder})")
    if params.culprit_role not in SUSPECTS:
        raise StoryError(f"(Unknown culprit role: {params.culprit_role})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    powder = POWDERS[params.powder]
    culprit = SUSPECTS[params.culprit_role]
    if not valid_combo(powder, culprit):
        raise StoryError(explain_rejection(powder, culprit))
    world = tell(
        festival=FESTIVALS[params.festival],
        powder=powder,
        culprit=culprit,
        helper=HELPERS[params.helper],
        investigator_name=params.investigator_name,
        investigator_gender=params.investigator_gender,
        organizer_type=params.organizer_type,
        bravery=params.bravery,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (powder, culprit) pairs:\n")
        for powder_id, culprit_id in combos:
            print(f"  {powder_id:12} {culprit_id}")
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
            header = (
                f"### {p.investigator_name}: {p.powder} / {p.culprit_role} "
                f"at {p.festival} (bravery {p.bravery})"
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
