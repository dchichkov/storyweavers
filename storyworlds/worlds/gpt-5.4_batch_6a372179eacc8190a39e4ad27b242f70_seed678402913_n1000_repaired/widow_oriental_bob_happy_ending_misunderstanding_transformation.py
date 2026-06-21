#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/widow_oriental_bob_happy_ending_misunderstanding_transformation.py
================================================================================================

A gentle whodunit-style storyworld about a missing sewing piece in a cozy parlor.

Seed instruments rebuilt as world state
--------------------------------------
Words:
    widow, oriental, bob

Features:
    Happy Ending, Misunderstanding, Transformation

Style:
    Whodunit

Premise
-------
A kind widow is preparing a small parlor event. In the room lies an old oriental
rug. A child named Bob quietly borrows one small item from the widow's sewing
basket so he can repair or decorate a surprise for her. The item seems to have
vanished. Because Bob was seen crossing the rug, a misunderstanding begins: it
looks as if Bob took something selfishly.

The detective child does not solve the mystery by magic or by parsing English.
They inspect the world, notice a clue that fits the missing object, and follow
that clue to the transformed object: the "missing" ribbon has become a bow, the
button has become part of a puppet coat, or the tassel has become a curtain tie.
The reveal clears Bob's name, the widow apologizes, and the repaired surprise is
used in the final scene.

Run it
------
    python storyworlds/worlds/gpt-5.4/widow_oriental_bob_happy_ending_misunderstanding_transformation.py
    python storyworlds/worlds/gpt-5.4/widow_oriental_bob_happy_ending_misunderstanding_transformation.py --item ribbon --project kite_tail --search thread_trail
    python storyworlds/worlds/gpt-5.4/widow_oriental_bob_happy_ending_misunderstanding_transformation.py --item button --search thread_trail
    python storyworlds/worlds/gpt-5.4/widow_oriental_bob_happy_ending_misunderstanding_transformation.py --all
    python storyworlds/worlds/gpt-5.4/widow_oriental_bob_happy_ending_misunderstanding_transformation.py --qa --json
    python storyworlds/worlds/gpt-5.4/widow_oriental_bob_happy_ending_misunderstanding_transformation.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    owner: str = ""
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "widow", "mother", "aunt"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    clue: str
    transform_verb: str
    result_noun: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    label: str
    phrase: str
    need: str
    place: str
    event: str
    result_line: str
    use_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Search:
    id: str
    label: str
    needs_clue: str
    notice: str
    follow: str
    qa_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    item: str
    project: str
    search: str
    blame: str
    widow_name: str
    detective_name: str
    detective_gender: str
    tea_treat: str
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_worry(world: World) -> list[str]:
    out: list[str] = []
    widow = world.entities.get("widow")
    room = world.entities.get("room")
    item = world.entities.get("item")
    if widow is None or room is None or item is None:
        return out
    if item.meters["missing"] < THRESHOLD:
        return out
    sig = ("missing_worry", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    widow.memes["worry"] += 1
    room.meters["mystery"] += 1
    out.append("__missing__")
    return out


def _r_suspicion_hurts(world: World) -> list[str]:
    out: list[str] = []
    bob = world.entities.get("Bob")
    if bob is None or bob.memes["suspected"] < THRESHOLD:
        return out
    sig = ("suspicion_hurts", bob.id, int(bob.memes["suspected"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bob.memes["hurt"] += 1
    out.append("__hurt__")
    return out


def _r_reveal_clears(world: World) -> list[str]:
    out: list[str] = []
    bob = world.entities.get("Bob")
    widow = world.entities.get("widow")
    room = world.entities.get("room")
    item = world.entities.get("item")
    if bob is None or widow is None or room is None or item is None:
        return out
    if item.meters["found"] < THRESHOLD:
        return out
    sig = ("reveal_clears", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bob.memes["hurt"] = 0.0
    bob.memes["relief"] += 1
    widow.memes["worry"] = 0.0
    widow.memes["trust"] += 1
    room.meters["mystery"] = 0.0
    out.append("__cleared__")
    return out


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="social", apply=_r_missing_worry),
    Rule(name="suspicion_hurts", tag="social", apply=_r_suspicion_hurts),
    Rule(name="reveal_clears", tag="social", apply=_r_reveal_clears),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            new = rule.apply(world)
            if new:
                changed = True
                produced.extend(s for s in new if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


ITEMS = {
    "ribbon": Item(
        id="ribbon",
        label="ribbon",
        phrase="a blue silk ribbon",
        kind="strip",
        clue="thread",
        transform_verb="tied",
        result_noun="a bright bow",
        tags={"ribbon", "sewing", "clue_thread"},
    ),
    "button": Item(
        id="button",
        label="button",
        phrase="a moon-bright pearl button",
        kind="fastener",
        clue="shine",
        transform_verb="sewed",
        result_noun="a neat button",
        tags={"button", "sewing", "clue_shine"},
    ),
    "tassel": Item(
        id="tassel",
        label="tassel",
        phrase="a red tassel",
        kind="trim",
        clue="fringe",
        transform_verb="knotted",
        result_noun="a smart tieback",
        tags={"tassel", "sewing", "clue_fringe"},
    ),
}

PROJECTS = {
    "kite_tail": Project(
        id="kite_tail",
        label="kite tail",
        phrase="the little paper kite Bob was mending",
        need="strip",
        place="the window seat",
        event="show",
        result_line="The missing ribbon had been tied into a dancing tail on Bob's little kite.",
        use_line="Soon the kite bobbed at the open window, its tail flicking like a happy clue at last solved.",
        tags={"kite", "repair", "show"},
    ),
    "puppet_coat": Project(
        id="puppet_coat",
        label="puppet coat",
        phrase="the fox puppet for the parlor show",
        need="fastener",
        place="the toy stage",
        event="show",
        result_line="The missing button had been sewed onto the fox puppet's tiny green coat.",
        use_line="That evening the fox puppet bowed from the little stage, its coat fastened neatly at the middle.",
        tags={"puppet", "repair", "show"},
    ),
    "curtain_tie": Project(
        id="curtain_tie",
        label="curtain tie",
        phrase="the tiny velvet curtain over the toy stage",
        need="trim",
        place="the toy stage",
        event="gift",
        result_line="The missing tassel had been knotted into a fine tieback for the toy-stage curtain.",
        use_line="When the curtain opened, the little stage looked grand, and everyone clapped at Bob's careful surprise.",
        tags={"curtain", "gift", "stage"},
    ),
    "bear_bow": Project(
        id="bear_bow",
        label="bear bow",
        phrase="the old teddy bear on the sofa",
        need="strip",
        place="the sofa",
        event="gift",
        result_line="The missing ribbon had been tied into a soft bow around the old teddy bear's neck.",
        use_line="The widow set the bear beside the teapot, and the new bow made the whole room look loved again.",
        tags={"bear", "gift", "repair"},
    ),
}

SEARCHES = {
    "thread_trail": Search(
        id="thread_trail",
        label="thread trail",
        needs_clue="thread",
        notice="a loose blue thread caught in the edge of the oriental rug",
        follow="The thread led from the rug to the window seat.",
        qa_line="The detective noticed a loose thread on the rug and followed it to where Bob had been fixing his surprise.",
        tags={"thread", "clue"},
    ),
    "shine_glint": Search(
        id="shine_glint",
        label="shine glint",
        needs_clue="shine",
        notice="a tiny pearly glint winking between the rug's dark patterns",
        follow="The glint pointed the detective's eyes toward the toy stage.",
        qa_line="The detective saw a tiny pearly glint on the rug and realized the missing thing must be close to the stage.",
        tags={"shine", "clue"},
    ),
    "fringe_match": Search(
        id="fringe_match",
        label="fringe match",
        needs_clue="fringe",
        notice="a red fringe fiber resting on the oriental rug's border",
        follow="That little fringe match drew the detective straight to the curtain by the toy stage.",
        qa_line="The detective compared the rug's border with a stray red fringe fiber and used that clue to find the curtain.",
        tags={"fringe", "clue"},
    ),
}

BLAMES = {
    "public": {
        "accuse": 'Aunt {widow} sighed. "Bob, were you the one who took it?"',
        "crowd": 'The question hung in the room so plainly that even the teacups seemed to listen.',
        "apology": '{widow} put a hand on Bob\'s shoulder. "I was wrong to ask that in front of everyone," she said.',
        "kind": "grand_apology",
    },
    "quiet": {
        "accuse": '{detective} heard Aunt {widow} whisper, "I hope Bob did not pocket it by mistake."',
        "crowd": 'It was a small suspicion, but it still made Bob look down at his shoes.',
        "apology": '{widow} bent close to Bob. "I should have trusted you first," she said softly.',
        "kind": "soft_apology",
    },
}

WIDOW_NAMES = ["Vale", "Morrow", "Hale", "Pine", "Wren"]
GIRL_NAMES = ["Nora", "Mina", "Lucy", "Ada", "Tess", "Ivy"]
BOY_NAMES = ["Ned", "Finn", "Theo", "Milo", "Evan", "Hugo"]
TREATS = ["honey buns", "jam tarts", "butter cookies", "small seed cakes"]


def valid_combo(item_id: str, project_id: str, search_id: str) -> bool:
    item = ITEMS[item_id]
    project = PROJECTS[project_id]
    search = SEARCHES[search_id]
    return item.kind == project.need and item.clue == search.needs_clue


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for item_id in ITEMS:
        for project_id in PROJECTS:
            for search_id in SEARCHES:
                if valid_combo(item_id, project_id, search_id):
                    out.append((item_id, project_id, search_id))
    return out


def outcome_of(params: StoryParams) -> str:
    project = PROJECTS[params.project]
    if params.blame == "public" or project.event == "show":
        return "grand_apology"
    return "soft_apology"


def explain_rejection(item_id: str, project_id: str, search_id: str) -> str:
    item = ITEMS[item_id]
    project = PROJECTS[project_id]
    search = SEARCHES[search_id]
    reasons: list[str] = []
    if item.kind != project.need:
        reasons.append(
            f"{item.phrase} would not sensibly repair or decorate {project.phrase}"
        )
    if item.clue != search.needs_clue:
        reasons.append(
            f"the search '{search.label}' does not match the clue this {item.label} would leave"
        )
    return "(No story: " + "; ".join(reasons) + ".)"


def introduce(world: World, widow: Entity, detective: Entity, bob: Entity, treat: str) -> None:
    world.say(
        f"In the parlor of Mrs. {widow.id}, a kind widow, the afternoon smelled of tea and {treat}. "
        f"An old oriental rug glowed under the table like a map in a mystery book."
    )
    world.say(
        f"{detective.id} had come to help set the room to rights, and Bob was already there, "
        f"moving quietly as if he carried a secret in his pockets."
    )


def set_up_event(world: World, widow: Entity, project: Project) -> None:
    if project.event == "show":
        world.say(
            f"Mrs. {widow.id} was preparing a tiny parlor show, and every chair seemed to lean forward with excitement."
        )
    else:
        world.say(
            f"Mrs. {widow.id} was arranging the room for a gentle tea, and she wanted one small surprise to make it feel extra bright."
        )


def place_item(world: World, widow: Entity, item: Item) -> None:
    world.say(
        f"On a side table sat her sewing basket, where {item.phrase} rested on top as plain as a clue waiting to matter."
    )


def bob_borrows(world: World, bob: Entity, item_ent: Entity, project_ent: Entity, item: Item, project: Project) -> None:
    item_ent.meters["missing"] += 1
    item_ent.meters["altered"] += 1
    project_ent.meters["mended"] += 1
    bob.memes["intent_help"] += 1
    bob.memes["nervous"] += 1
    world.facts["borrowed_for_help"] = True
    propagate(world, narrate=False)
    world.say(
        f"While no one was looking, Bob borrowed it. He only meant to help, but in a mystery, a good secret can still look like a bad one."
    )


def notice_loss(world: World, widow: Entity, item: Item) -> None:
    world.say(
        f"A moment later Mrs. {widow.id} opened the basket again and stopped. {item.phrase.capitalize()} was gone."
    )
    world.say(
        f'"That is odd," she murmured. "I was sure it was right here."'
    )


def suspect_bob(world: World, widow: Entity, detective: Entity, bob: Entity, blame: str) -> None:
    bob.memes["suspected"] += 1
    propagate(world, narrate=False)
    script = BLAMES[blame]
    world.say(script["accuse"].format(widow=widow.id, detective=detective.id))
    world.say(script["crowd"])
    world.say(
        f'Bob\'s face turned pink. "I did take something," he said, "but not for the reason you think."'
    )


def inspect_rug(world: World, detective: Entity, search: Search) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"{detective.id} did not answer at once. Good detectives, {detective.pronoun()} thought, look down before they point fingers."
    )
    world.say(
        f"Near the edge of the oriental rug, {detective.pronoun()} spotted {search.notice}."
    )
    world.say(search.follow)


def find_transformation(
    world: World,
    detective: Entity,
    bob: Entity,
    item_ent: Entity,
    project_ent: Entity,
    project: Project,
) -> None:
    item_ent.meters["found"] += 1
    item_ent.location = project.place
    world.facts["found_place"] = project.place
    propagate(world, narrate=False)
    world.say(
        f"There, by {project.place}, stood {project.phrase}."
    )
    world.say(project.result_line)
    world.say(
        f"{detective.id} blinked once, then smiled. This was no theft at all. The missing thing had been transformed into part of Bob's surprise."
    )
    bob.memes["pride"] += 1
    bob.memes["nervous"] = 0.0


def explain_bob(world: World, bob: Entity, widow: Entity, project: Project) -> None:
    world.say(
        f'"I wanted to make it nice for you," Bob said. "I should have asked first. I only wanted {project.phrase} to be ready before your guests saw it."'
    )


def apologize(world: World, widow: Entity, bob: Entity, blame: str) -> None:
    widow.memes["kindness"] += 1
    bob.memes["trust"] += 1
    line = BLAMES[blame]["apology"].format(widow=widow.id)
    world.say(line)
    world.say(
        f'Bob let out a breath he had been holding far too long. "Next time I will ask," he promised.'
    )


def ending(world: World, widow: Entity, detective: Entity, bob: Entity, project: Project, treat: str) -> None:
    widow.memes["relief"] += 1
    detective.memes["satisfaction"] += 1
    bob.memes["joy"] += 1
    world.say(
        f"Then everyone finished setting the room together. {project.use_line}"
    )
    world.say(
        f"Mrs. {widow.id} poured the tea, set out the {treat}, and winked at {detective.id}. "
        f'The case of the missing piece was closed, and Bob was smiling again.'
    )


def tell(
    item: Item,
    project: Project,
    search: Search,
    blame: str,
    widow_name: str,
    detective_name: str,
    detective_gender: str,
    tea_treat: str,
) -> World:
    world = World()
    widow = world.add(Entity(
        id=widow_name,
        kind="character",
        type="widow",
        label="the widow",
        role="widow",
        tags={"widow"},
    ))
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        label="the detective child",
        role="detective",
        tags={"detective"},
    ))
    bob = world.add(Entity(
        id="Bob",
        kind="character",
        type="boy",
        label="Bob",
        role="helper",
        tags={"bob"},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="parlor",
        label="parlor",
        phrase="the quiet parlor",
        tags={"parlor", "oriental"},
    ))
    rug = world.add(Entity(
        id="rug",
        kind="thing",
        type="rug",
        label="oriental rug",
        phrase="the old oriental rug",
        location="parlor",
        tags={"oriental", "rug"},
    ))
    item_ent = world.add(Entity(
        id="item",
        kind="thing",
        type="sewing_piece",
        label=item.label,
        phrase=item.phrase,
        owner=widow.id,
        location="basket",
        tags=set(item.tags),
    ))
    project_ent = world.add(Entity(
        id="project",
        kind="thing",
        type="project",
        label=project.label,
        phrase=project.phrase,
        location=project.place,
        tags=set(project.tags),
    ))

    introduce(world, widow, detective, bob, tea_treat)
    set_up_event(world, widow, project)
    place_item(world, widow, item)

    world.para()
    bob_borrows(world, bob, item_ent, project_ent, item, project)
    notice_loss(world, widow, item)
    suspect_bob(world, widow, detective, bob, blame)

    world.para()
    inspect_rug(world, detective, search)
    find_transformation(world, detective, bob, item_ent, project_ent, project)
    explain_bob(world, bob, widow, project)

    world.para()
    apologize(world, widow, bob, blame)
    ending(world, widow, detective, bob, project, tea_treat)

    world.facts.update(
        widow=widow,
        detective=detective,
        bob=bob,
        room=room,
        rug=rug,
        item_cfg=item,
        project_cfg=project,
        search_cfg=search,
        blame=blame,
        tea_treat=tea_treat,
        item=item_ent,
        project=project_ent,
        mystery_started=room.meters["mystery"] <= 0.0 or item_ent.meters["missing"] >= THRESHOLD,
        found=item_ent.meters["found"] >= THRESHOLD,
        outcome=outcome_of(StoryParams(
            item=item.id,
            project=project.id,
            search=search.id,
            blame=blame,
            widow_name=widow_name,
            detective_name=detective_name,
            detective_gender=detective_gender,
            tea_treat=tea_treat,
        )),
    )
    return world


KNOWLEDGE = {
    "widow": [
        (
            "What is a widow?",
            "A widow is a woman whose husband has died. She can still have a warm, busy home full of friends and family."
        )
    ],
    "rug": [
        (
            "What is a rug?",
            "A rug is a thick piece of cloth that lies on the floor. It can make a room feel warm and soft."
        )
    ],
    "oriental": [
        (
            "What is an oriental rug?",
            "An oriental rug is a patterned woven rug. In stories, people often notice its colors, borders, and tiny details when looking for clues."
        )
    ],
    "ribbon": [
        (
            "What is a ribbon?",
            "A ribbon is a long, soft strip of cloth. People use ribbons for tying, decorating, and making bows."
        )
    ],
    "button": [
        (
            "What does a button do?",
            "A button helps hold clothes closed. If a button is missing, a coat or shirt may not stay neat."
        )
    ],
    "tassel": [
        (
            "What is a tassel?",
            "A tassel is a bunch of hanging threads tied at one end. It is often used as trim or decoration."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Good detectives notice clues before they guess."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when people think something means one thing, but the truth is different. Asking kindly can clear it up."
        )
    ],
    "apology": [
        (
            "Why does an apology help?",
            "An apology helps because it shows you know you hurt someone and want to make things right. It can help trust grow again."
        )
    ],
    "puppet": [
        (
            "What is a puppet?",
            "A puppet is a toy figure that people move with their hands or strings to tell a story."
        )
    ],
    "kite": [
        (
            "What is a kite tail for?",
            "A kite tail helps a kite balance in the wind, and it can make the kite look bright and lively too."
        )
    ],
    "stage": [
        (
            "What is a stage curtain for?",
            "A stage curtain opens and closes to begin a little show. It can make even a tiny play feel special."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "widow",
    "rug",
    "oriental",
    "clue",
    "misunderstanding",
    "apology",
    "ribbon",
    "button",
    "tassel",
    "puppet",
    "kite",
    "stage",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    widow = f["widow"]
    item = f["item_cfg"]
    project = f["project_cfg"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old that includes the words "widow", "oriental", and "Bob".',
        f"Tell a cozy mystery where a widow named Mrs. {widow.id} thinks Bob took {item.phrase}, but the clue on the oriental rug leads to {project.phrase}.",
        f"Write a story with a misunderstanding and a happy ending, where a missing {item.label} is transformed into part of a surprise and no one turns out to be a thief.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    widow = f["widow"]
    detective = f["detective"]
    bob = f["bob"]
    item = f["item_cfg"]
    project = f["project_cfg"]
    search = f["search_cfg"]
    blame = f["blame"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Mrs. {widow.id}, a widow in a cozy parlor, Bob, and {detective.id}, who acts like a little detective. They are gathered in a room with an old oriental rug while a small mystery begins."
        ),
        (
            f"What went missing?",
            f"The missing thing was {item.phrase}. It seemed important because it had been sitting in the widow's sewing basket just before it disappeared."
        ),
        (
            "Why did people think Bob had done something wrong?",
            f"They thought that because Bob had been moving quietly and the missing item vanished right after he borrowed it. The misunderstanding grew before anyone knew he meant to help."
        ),
        (
            f"How did {detective.id} solve the mystery?",
            f"{search.qa_line} That clue led to {project.phrase}, where the missing thing had been changed into something useful."
        ),
        (
            "What was the real truth?",
            f"Bob had borrowed the item to improve a surprise for Mrs. {widow.id}, not to steal it. The missing piece had been transformed into part of {project.label}, so the mystery was really a misunderstanding."
        ),
    ]
    if blame == "public":
        qa.append(
            (
                "Why did the apology matter so much?",
                f"It mattered because the suspicion had been spoken out loud, and that hurt Bob's feelings. When Mrs. {widow.id} apologized in front of everyone, she cleared his name in front of everyone too."
            )
        )
    else:
        qa.append(
            (
                "How did the misunderstanding end?",
                f"It ended quietly and kindly. Mrs. {widow.id} admitted she should have trusted Bob first, and Bob promised he would ask before borrowing things next time."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily, with the room set right again and the repaired surprise ready to be enjoyed. Bob was smiling, the widow was relieved, and the last picture shows the mystery turned into a warm family moment."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"widow", "rug", "oriental", "clue", "misunderstanding", "apology"}
    item = f["item_cfg"]
    project = f["project_cfg"]
    if item.id == "ribbon":
        tags.add("ribbon")
    if item.id == "button":
        tags.add("button")
    if item.id == "tassel":
        tags.add("tassel")
    if project.id == "puppet_coat":
        tags.add("puppet")
    if project.id == "kite_tail":
        tags.add("kite")
    if project.id == "curtain_tie":
        tags.add("stage")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.location:
            bits.append(f"location={ent.location}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
compatible(I, P) :- item_kind(I, K), project_need(P, K).
search_fits(I, S) :- item_clue(I, C), search_needs(S, C).
valid(I, P, S) :- item(I), project(P), search(S), compatible(I, P), search_fits(I, S).

grand_apology :- blame(public).
grand_apology :- chosen_project(P), project_event(P, show).
soft_apology  :- not grand_apology.

outcome(grand_apology) :- grand_apology.
outcome(soft_apology)  :- soft_apology.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_kind", item_id, item.kind))
        lines.append(asp.fact("item_clue", item_id, item.clue))
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        lines.append(asp.fact("project_need", project_id, project.need))
        lines.append(asp.fact("project_event", project_id, project.event))
    for search_id, search in SEARCHES.items():
        lines.append(asp.fact("search", search_id))
        lines.append(asp.fact("search_needs", search_id, search.needs_clue))
    for blame in BLAMES:
        lines.append(asp.fact("blame_kind", blame))
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
            asp.fact("chosen_project", params.project),
            asp.fact("blame", params.blame),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue

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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        _ = sample.to_json()
        print("OK: smoke generation and JSON serialization succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


CURATED = [
    StoryParams(
        item="ribbon",
        project="kite_tail",
        search="thread_trail",
        blame="public",
        widow_name="Vale",
        detective_name="Nora",
        detective_gender="girl",
        tea_treat="jam tarts",
    ),
    StoryParams(
        item="button",
        project="puppet_coat",
        search="shine_glint",
        blame="quiet",
        widow_name="Morrow",
        detective_name="Theo",
        detective_gender="boy",
        tea_treat="butter cookies",
    ),
    StoryParams(
        item="tassel",
        project="curtain_tie",
        search="fringe_match",
        blame="quiet",
        widow_name="Pine",
        detective_name="Ada",
        detective_gender="girl",
        tea_treat="small seed cakes",
    ),
    StoryParams(
        item="ribbon",
        project="bear_bow",
        search="thread_trail",
        blame="quiet",
        widow_name="Wren",
        detective_name="Finn",
        detective_gender="boy",
        tea_treat="honey buns",
    ),
    StoryParams(
        item="button",
        project="puppet_coat",
        search="shine_glint",
        blame="public",
        widow_name="Hale",
        detective_name="Lucy",
        detective_gender="girl",
        tea_treat="jam tarts",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Cozy whodunit storyworld: a widow, an oriental rug, Bob, and a misunderstanding with a happy ending."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--search", choices=SEARCHES)
    ap.add_argument("--blame", choices=sorted(BLAMES))
    ap.add_argument("--widow-name", choices=WIDOW_NAMES)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--tea-treat", choices=TREATS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.project and args.search:
        if not valid_combo(args.item, args.project, args.search):
            raise StoryError(explain_rejection(args.item, args.project, args.search))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.project is None or combo[1] == args.project)
        and (args.search is None or combo[2] == args.search)
    ]
    if not combos:
        if args.item and args.project and args.search:
            raise StoryError(explain_rejection(args.item, args.project, args.search))
        raise StoryError("(No valid combination matches the given options.)")

    item_id, project_id, search_id = rng.choice(sorted(combos))
    blame = args.blame or rng.choice(sorted(BLAMES))
    widow_name = args.widow_name or rng.choice(WIDOW_NAMES)
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    detective_pool = GIRL_NAMES if detective_gender == "girl" else BOY_NAMES
    detective_name = args.detective_name or rng.choice(detective_pool)
    if detective_name == "Bob":
        detective_name = rng.choice([n for n in detective_pool if n != "Bob"])
    tea_treat = args.tea_treat or rng.choice(TREATS)
    return StoryParams(
        item=item_id,
        project=project_id,
        search=search_id,
        blame=blame,
        widow_name=widow_name,
        detective_name=detective_name,
        detective_gender=detective_gender,
        tea_treat=tea_treat,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.search not in SEARCHES:
        raise StoryError(f"(Unknown search: {params.search})")
    if params.blame not in BLAMES:
        raise StoryError(f"(Unknown blame style: {params.blame})")
    if not valid_combo(params.item, params.project, params.search):
        raise StoryError(explain_rejection(params.item, params.project, params.search))

    world = tell(
        item=ITEMS[params.item],
        project=PROJECTS[params.project],
        search=SEARCHES[params.search],
        blame=params.blame,
        widow_name=params.widow_name,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        tea_treat=params.tea_treat,
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
        print(f"{len(combos)} compatible (item, project, search) combos:\n")
        for item_id, project_id, search_id in combos:
            print(f"  {item_id:7} {project_id:12} {search_id}")
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.item} -> {p.project} ({p.search}, {p.blame}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
