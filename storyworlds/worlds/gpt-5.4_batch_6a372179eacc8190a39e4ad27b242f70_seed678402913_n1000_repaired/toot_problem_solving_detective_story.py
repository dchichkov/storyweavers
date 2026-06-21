#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/toot_problem_solving_detective_story.py
==================================================================

A standalone story world for a tiny child-facing detective story: a small
mystery begins with a strange "toot" sound, a child detective gathers clues,
tests a sensible idea, and solves the problem.

The world model prefers a tight kind of story:
- something useful goes wrong,
- a concrete clue points to a likely cause,
- the child tries a matching fix,
- the ending image shows the sound is understood and peace returns.

Run it
------
python storyworlds/worlds/gpt-5.4/toot_problem_solving_detective_story.py
python storyworlds/worlds/gpt-5.4/toot_problem_solving_detective_story.py --place kitchen --source kettle
python storyworlds/worlds/gpt-5.4/toot_problem_solving_detective_story.py --source toy_trumpet --fix patch
python storyworlds/worlds/gpt-5.4/toot_problem_solving_detective_story.py --all
python storyworlds/worlds/gpt-5.4/toot_problem_solving_detective_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/toot_problem_solving_detective_story.py --verify
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    scene: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MysterySource:
    id: str
    label: str
    phrase: str
    noise: str
    clue: str
    problem: str
    cause: str
    fix_action: str
    ending_image: str
    place_ids: set[str] = field(default_factory=set)
    fix_ids: set[str] = field(default_factory=set)
    helper_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class FixMethod:
    id: str
    label: str
    phrase: str
    action_line: str
    result_line: str
    solves_sources: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperRole:
    id: str
    label: str
    phrase: str
    type: str
    help_line: str
    tags: set[str] = field(default_factory=set)


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


def valid_combo(place_id: str, source_id: str, fix_id: str, helper_id: str) -> bool:
    if place_id not in PLACES or source_id not in SOURCES or fix_id not in FIXES or helper_id not in HELPERS:
        return False
    src = SOURCES[source_id]
    fix = FIXES[fix_id]
    if place_id not in src.place_ids:
        return False
    if fix_id not in src.fix_ids:
        return False
    if source_id not in fix.solves_sources:
        return False
    if helper_id not in src.helper_ids:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place_id in sorted(PLACES):
        for source_id in sorted(SOURCES):
            for fix_id in sorted(FIXES):
                for helper_id in sorted(HELPERS):
                    if valid_combo(place_id, source_id, fix_id, helper_id):
                        out.append((place_id, source_id, fix_id, helper_id))
    return out


def explain_rejection(place_id: str, source_id: str, fix_id: str, helper_id: str) -> str:
    if place_id not in PLACES:
        return f"(No story: unknown place '{place_id}'.)"
    if source_id not in SOURCES:
        return f"(No story: unknown source '{source_id}'.)"
    if fix_id not in FIXES:
        return f"(No story: unknown fix '{fix_id}'.)"
    if helper_id not in HELPERS:
        return f"(No story: unknown helper '{helper_id}'.)"
    src = SOURCES[source_id]
    if place_id not in src.place_ids:
        return (
            f"(No story: {src.phrase} does not belong in {PLACES[place_id].phrase}. "
            f"Pick a place where that kind of toot could really happen.)"
        )
    if fix_id not in src.fix_ids:
        return (
            f"(No story: {FIXES[fix_id].phrase} does not match the clue for {src.label}. "
            f"A detective fix should follow from the cause, not be random.)"
        )
    if helper_id not in src.helper_ids:
        return (
            f"(No story: {HELPERS[helper_id].phrase} is not the sensible helper for this mystery. "
            f"Pick someone who could honestly help with the clue or the fix.)"
        )
    return "(No story: that combination does not make a reasonable little mystery.)"


def introduce(world: World, detective: Entity, place: Place, source: MysterySource, item: Entity) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"One soft afternoon, {detective.id} padded into {place.phrase}. {place.scene}"
    )
    world.say(
        f"{detective.pronoun('subject').capitalize()} liked pretending to be a detective, "
        f"the kind who noticed tiny things before anyone else did."
    )
    world.say(
        f"Then a small sound bounced through the room: \"{source.noise}!\" It came from somewhere near {item.phrase}."
    )


def notice_problem(world: World, detective: Entity, source: MysterySource) -> None:
    detective.memes["concern"] += 1
    world.say(
        f"{detective.id} stopped and listened again. The funny toot did not sound silly now. {source.problem}"
    )


def gather_clue(world: World, detective: Entity, helper: Entity, source: MysterySource, item: Entity) -> None:
    detective.meters["clue"] += 1
    helper.memes["support"] += 1
    world.say(
        f'"A mystery," whispered {detective.id}. {detective.pronoun("subject").capitalize()} bent close to {item.phrase} and saw something important: {source.clue}'
    )
    world.say(helper.attrs["help_line"])


def reason_it_out(world: World, detective: Entity, source: MysterySource) -> None:
    detective.meters["theory"] += 1
    world.say(
        f'{detective.id} put one finger on {detective.pronoun("possessive")} chin. '
        f'"The toot is a clue," {detective.pronoun("subject")} said. "If {source.clue.lower()}, then maybe {source.cause}."'
    )


def try_fix(world: World, detective: Entity, helper: Entity, fix: FixMethod, source: MysterySource, item: Entity) -> None:
    detective.meters["attempted_fix"] += 1
    item.meters["being_fixed"] += 1
    world.say(
        f"So the little detective made a plan. With {helper.phrase} nearby, {detective.id} {fix.action_line.format(item=item.label)}"
    )
    world.say(source.fix_action)


def solve(world: World, detective: Entity, helper: Entity, fix: FixMethod, source: MysterySource, item: Entity) -> None:
    item.meters["problem"] = 0.0
    item.meters["solved"] += 1
    detective.memes["relief"] += 1
    detective.memes["pride"] += 1
    helper.memes["relief"] += 1
    world.say(
        fix.result_line.format(item=item.label)
    )
    world.say(
        f"The room waited for another toot, but this time there was only the nice, ordinary sound it was supposed to make."
    )
    world.say(
        f'{helper.phrase.capitalize()} smiled. "Case closed," {helper.pronoun("subject")} said.'
    )
    world.say(
        f"{source.ending_image} {detective.id} grinned, because solving the mystery felt even better than guessing."
    )


def tell(
    place: Place,
    source: MysterySource,
    fix: FixMethod,
    helper_cfg: HelperRole,
    detective_name: str = "Mina",
    detective_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    pet_name: str = "",
) -> World:
    world = World()
    detective = world.add(
        Entity(
            id=detective_name,
            kind="character",
            type=detective_gender,
            role="detective",
            traits=[trait],
            tags={"detective", "child"},
        )
    )
    if helper_cfg.type in {"mother", "father"}:
        helper_name = "Parent"
    else:
        helper_name = "Pip" if helper_cfg.type == "duck" else "Noodle"
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_cfg.type,
            label=helper_cfg.label,
            phrase=helper_cfg.phrase,
            role="helper",
            attrs={"help_line": helper_cfg.help_line},
            tags=set(helper_cfg.tags),
        )
    )
    if helper_cfg.type in {"mother", "father"}:
        helper.type = parent_type
        helper.label = {"mother": "the parent", "father": "the parent"}[parent_type]
        helper.phrase = f"{detective.id}'s {helper.label_word}"
        helper.attrs["help_line"] = (
            f'{helper.phrase.capitalize()} knelt beside {detective.pronoun("object")} and said, '
            f'"Let us look for the clue before we touch anything."'
        )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="object",
            label=source.label,
            phrase=source.phrase,
            tags=set(source.tags),
        )
    )
    item.meters["problem"] = 1.0

    introduce(world, detective, place, source, item)
    notice_problem(world, detective, source)

    world.para()
    gather_clue(world, detective, helper, source, item)
    reason_it_out(world, detective, source)

    world.para()
    try_fix(world, detective, helper, fix, source, item)
    solve(world, detective, helper, fix, source, item)

    world.facts.update(
        detective=detective,
        helper=helper,
        helper_cfg=helper_cfg,
        place=place,
        source=source,
        fix=fix,
        item=item,
        parent_type=parent_type,
        pet_name=pet_name,
        solved=item.meters["solved"] >= THRESHOLD,
        clue_found=detective.meters["clue"] >= THRESHOLD,
        theory_made=detective.meters["theory"] >= THRESHOLD,
    )
    if pet_name:
        world.say(f"Even {pet_name} settled down at the end, as if the little detective had solved the whole house.")
    return world


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="kitchen",
        phrase="the sunny kitchen",
        scene="A striped towel hung from the oven handle, and a window made bright squares on the floor.",
        tags={"kitchen"},
    ),
    "playroom": Place(
        id="playroom",
        label="playroom",
        phrase="the playroom",
        scene="Blocks rested in a neat tower, and the toy shelf waited by the rug.",
        tags={"playroom"},
    ),
    "garden": Place(
        id="garden",
        label="garden",
        phrase="the back garden",
        scene="The peas climbed their strings, and a little breeze brushed the leaves together.",
        tags={"garden"},
    ),
}

SOURCES = {
    "kettle": MysterySource(
        id="kettle",
        label="kettle",
        phrase="the round silver kettle",
        noise="toot",
        clue="a ribbon of steam was slipping from the spout",
        problem="Tea water was getting hotter and hotter, and nobody had come back yet.",
        cause="the kettle is calling because the water is ready",
        fix_action="Very carefully, the detective did not touch the hot metal alone.",
        ending_image="Soon warm cups sat on the table, and the kettle was quiet again.",
        place_ids={"kitchen"},
        fix_ids={"call_adult"},
        helper_ids={"parent"},
        tags={"kettle", "steam", "hot"},
    ),
    "toy_trumpet": MysterySource(
        id="toy_trumpet",
        label="toy trumpet",
        phrase="the red toy trumpet",
        noise="toot",
        clue="the rubber horn was squashed under a pile of books",
        problem="Every time the shelf wobbled, the trumpet cried out by itself and startled everyone.",
        cause="something is pressing the horn and making it toot",
        fix_action="The plan was gentle and simple, because little mysteries often are.",
        ending_image="The trumpet rested safely on the low toy shelf, and the room felt peaceful.",
        place_ids={"playroom"},
        fix_ids={"lift_obstacle"},
        helper_ids={"friend", "pet_duck"},
        tags={"toy", "sound", "shelf"},
    ),
    "reed_whistle": MysterySource(
        id="reed_whistle",
        label="garden whistle",
        phrase="the green garden whistle",
        noise="toot",
        clue="a tiny leaf was stuck in the mouth hole",
        problem="The breeze kept blowing through it and making fussy little noises near the beans.",
        cause="the wind is sneaking through the whistle because a leaf is holding it the wrong way",
        fix_action="The detective worked slowly, because yanking at clues can break the thing you are trying to help.",
        ending_image="After that, the breeze only rustled the garden instead of making mystery music.",
        place_ids={"garden"},
        fix_ids={"clear_leaf"},
        helper_ids={"grandparent"},
        tags={"garden", "wind", "leaf"},
    ),
}

FIXES = {
    "call_adult": FixMethod(
        id="call_adult",
        label="call for a grown-up",
        phrase="calling for a grown-up",
        action_line='pointed at the clue and called for help instead of grabbing the hot {item} alone.',
        result_line="The grown-up turned the stove knob off and moved the kettle to a safe place.",
        solves_sources={"kettle"},
        tags={"safety", "adult_help"},
    ),
    "lift_obstacle": FixMethod(
        id="lift_obstacle",
        label="lift the books away",
        phrase="lifting the books away",
        action_line='carefully lifted the books off the {item}.',
        result_line="At once the silly self-tooting stopped, and the toy trumpet could rest without being squashed.",
        solves_sources={"toy_trumpet"},
        tags={"tidy", "pressure"},
    ),
    "clear_leaf": FixMethod(
        id="clear_leaf",
        label="pull the leaf free",
        phrase="pulling the leaf free",
        action_line='pinched the tiny leaf and eased it out of the {item}.',
        result_line="The whistle gave one last tiny toot, then went still in the kind breeze.",
        solves_sources={"reed_whistle"},
        tags={"garden", "careful_hands"},
    ),
    "patch": FixMethod(
        id="patch",
        label="patch it",
        phrase="patching it",
        action_line='looked for tape to patch the {item}.',
        result_line="The patch looked neat, but the mystery was not really that kind of problem.",
        solves_sources=set(),
        tags={"wrong_fix"},
    ),
}

HELPERS = {
    "parent": HelperRole(
        id="parent",
        label="the parent",
        phrase="the parent",
        type="mother",
        help_line='A calm grown-up voice came from the doorway: "A good detective looks, thinks, and stays safe."',
        tags={"adult_help"},
    ),
    "friend": HelperRole(
        id="friend",
        label="the friend",
        phrase="her friend Bo",
        type="boy",
        help_line='Bo crouched beside the shelf and whispered, "The toot happens when the books wobble. That must matter."',
        tags={"friend"},
    ),
    "grandparent": HelperRole(
        id="grandparent",
        label="the grandparent",
        phrase="her grandpa",
        type="man",
        help_line='Grandpa shaded his eyes, peered at the whistle, and said, "I think the wind is only half the story."',
        tags={"grandparent"},
    ),
    "pet_duck": HelperRole(
        id="pet_duck",
        label="the duck",
        phrase="a waddly duck named Pip",
        type="duck",
        help_line='Pip the duck gave the books an annoyed look and stepped away from the shelf as if he had solved half the case already.',
        tags={"pet"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Zoe", "Maya"]
BOY_NAMES = ["Ben", "Theo", "Sam", "Max", "Eli", "Leo"]
TRAITS = ["careful", "curious", "thoughtful", "quiet", "clever"]


@dataclass
class StoryParams:
    place: str
    source: str
    fix: str
    helper: str
    detective_name: str
    detective_gender: str
    parent_type: str
    trait: str
    pet_name: str = ""
    seed: Optional[int] = None


KNOWLEDGE = {
    "kettle": [
        (
            "Why can a kettle make a sound?",
            "A kettle can whistle or toot when the water inside gets very hot. The sound tells grown-ups the water is ready."
        )
    ],
    "steam": [
        (
            "What is steam?",
            "Steam is warm water that has turned into a misty gas. You often see it rising from very hot water."
        )
    ],
    "hot": [
        (
            "Why should children be careful around hot things?",
            "Hot things can burn skin very quickly. If something is hot, it is smart to ask a grown-up for help."
        )
    ],
    "toy": [
        (
            "Why can a toy make a sound by accident?",
            "A toy can make a sound if something presses on it or squeezes it. Then the sound happens even when nobody meant to play it."
        )
    ],
    "sound": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Detectives look for clues before they decide what happened."
        )
    ],
    "leaf": [
        (
            "Why can a leaf change how air moves?",
            "A leaf can block a little hole or bend the air in a new direction. Then the air may make a sound it was not making before."
        )
    ],
    "safety": [
        (
            "When should you call a grown-up instead of fixing something yourself?",
            "Call a grown-up when something is hot, sharp, high up, or otherwise unsafe. Good problem solving means noticing danger too."
        )
    ],
    "tidy": [
        (
            "How can tidying solve a problem?",
            "Tidying can solve a problem when objects are pressing, blocking, or bumping one another. Putting things back in a calm place can stop the trouble."
        )
    ],
    "garden": [
        (
            "What can wind do in a garden?",
            "Wind can move leaves, seeds, and light toys. It can also push air through little holes and make soft sounds."
        )
    ],
}
KNOWLEDGE_ORDER = ["kettle", "steam", "hot", "toy", "sound", "leaf", "safety", "tidy", "garden"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    source = f["source"]
    place = f["place"]
    fix = f["fix"]
    return [
        f'Write a short detective story for a 3-to-5-year-old that includes the word "toot" and takes place in {place.phrase}.',
        f"Tell a gentle mystery where {detective.id} hears a strange toot, studies a clue, and uses problem solving to discover what is wrong with the {source.label}.",
        f"Write a story in a detective style where the solution is {fix.phrase}, and the ending proves the sound has finally stopped for a good reason.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    source = f["source"]
    place = f["place"]
    fix = f["fix"]
    item = f["item"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a little detective, and {helper.phrase} who helps with the case. Together they listen, look closely, and solve the mystery."
        ),
        (
            "What mystery started the story?",
            f"The mystery started when a strange \"{source.noise}\" sound came from {item.phrase} in {place.phrase}. That toot told {detective.id} something was wrong and needed to be understood."
        ),
        (
            f"What clue did {detective.id} find?",
            f'{detective.id} found this clue: {source.clue}. That clue mattered because it pointed toward the real cause instead of a random guess.'
        ),
        (
            f"How did {detective.id} solve the problem?",
            f"{detective.id} did not just guess. {detective.pronoun('subject').capitalize()} used the clue to decide on {fix.phrase}, and that matched what was really causing the toot."
        ),
    ]
    if f.get("solved"):
        qa.append(
            (
                "How did the story end?",
                f"The problem was solved, and the toot stopped for the right reason. The last quiet moment showed that the detective's careful thinking had worked."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["source"].tags) | set(world.facts["fix"].tags)
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="kitchen",
        source="kettle",
        fix="call_adult",
        helper="parent",
        detective_name="Mina",
        detective_gender="girl",
        parent_type="mother",
        trait="careful",
        pet_name="the cat",
    ),
    StoryParams(
        place="playroom",
        source="toy_trumpet",
        fix="lift_obstacle",
        helper="friend",
        detective_name="Ben",
        detective_gender="boy",
        parent_type="father",
        trait="curious",
        pet_name="",
    ),
    StoryParams(
        place="garden",
        source="reed_whistle",
        fix="clear_leaf",
        helper="grandparent",
        detective_name="Nora",
        detective_gender="girl",
        parent_type="mother",
        trait="thoughtful",
        pet_name="the rabbit",
    ),
    StoryParams(
        place="playroom",
        source="toy_trumpet",
        fix="lift_obstacle",
        helper="pet_duck",
        detective_name="Theo",
        detective_gender="boy",
        parent_type="father",
        trait="quiet",
        pet_name="Pip",
    ),
]

ASP_RULES = r"""
valid_combo(P,S,F,H) :- place(P), source(S), fix(F), helper(H),
                        source_place(S,P), source_fix(S,F), helper_ok(S,H),
                        fix_solves(F,S).

#show valid_combo/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in sorted(PLACES):
        lines.append(asp.fact("place", pid))
    for sid, src in SOURCES.items():
        lines.append(asp.fact("source", sid))
        for pid in sorted(src.place_ids):
            lines.append(asp.fact("source_place", sid, pid))
        for fid in sorted(src.fix_ids):
            lines.append(asp.fact("source_fix", sid, fid))
        for hid in sorted(src.helper_ids):
            lines.append(asp.fact("helper_ok", sid, hid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for sid in sorted(fix.solves_sources):
            lines.append(asp.fact("fix_solves", fid, sid))
    for hid in sorted(HELPERS):
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_combo/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_combo/4."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verify failed: generated story was empty.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"VERIFY SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a small detective mystery about a toot and a practical solution."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source and args.fix and args.helper:
        if not valid_combo(args.place, args.source, args.fix, args.helper):
            raise StoryError(explain_rejection(args.place, args.source, args.fix, args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.fix is None or combo[2] == args.fix)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        place_id = args.place or next(iter(PLACES))
        source_id = args.source or next(iter(SOURCES))
        fix_id = args.fix or next(iter(FIXES))
        helper_id = args.helper or next(iter(HELPERS))
        raise StoryError(explain_rejection(place_id, source_id, fix_id, helper_id))

    place_id, source_id, fix_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    pet_name = rng.choice(["", "", "the cat", "the dog", "the rabbit"])
    return StoryParams(
        place=place_id,
        source=source_id,
        fix=fix_id,
        helper=helper_id,
        detective_name=name,
        detective_gender=gender,
        parent_type=parent_type,
        trait=trait,
        pet_name=pet_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.source not in SOURCES:
        raise StoryError(f"(No story: unknown source '{params.source}'.)")
    if params.fix not in FIXES:
        raise StoryError(f"(No story: unknown fix '{params.fix}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if not valid_combo(params.place, params.source, params.fix, params.helper):
        raise StoryError(explain_rejection(params.place, params.source, params.fix, params.helper))

    world = tell(
        place=PLACES[params.place],
        source=SOURCES[params.source],
        fix=FIXES[params.fix],
        helper_cfg=HELPERS[params.helper],
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        parent_type=params.parent_type,
        trait=params.trait,
        pet_name=params.pet_name,
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
        print(asp_program("#show valid_combo/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source, fix, helper) combos:\n")
        for place_id, source_id, fix_id, helper_id in combos:
            print(f"  {place_id:9} {source_id:12} {fix_id:14} {helper_id}")
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
            header = f"### {p.detective_name}: {p.source} in {p.place} ({p.fix}, helper: {p.helper})"
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
