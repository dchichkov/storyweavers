#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shed_rosary_alternative_bravery_reconciliation_slice_of.py
=====================================================================================

A small storyworld about a child, a dark shed, a grandmother's rosary, and the
brave choice to tell the truth after a mistake. The story always ends in
reconciliation, but the world model tracks whether that peace comes quickly or
only after a wobble of hiding and blame.

The domain is intentionally narrow and child-facing:

- two children want a cord-like thing for a small shed-side project
- one child is tempted to borrow a rosary because it is pretty and close at hand
- the rosary is a poor tool for the job and breaks on a rough nail in the shed
- the child must be brave enough to confess
- the grown-up helps repair the harm and offers a proper alternative
- the ending image proves reconciliation: the project is finished with the safe
  alternative, and the restored rosary goes back where it belongs

Run it
------
    python storyworlds/worlds/gpt-5.4/shed_rosary_alternative_bravery_reconciliation_slice_of.py
    python storyworlds/worlds/gpt-5.4/shed_rosary_alternative_bravery_reconciliation_slice_of.py --project star_sign --alternative ribbon
    python storyworlds/worlds/gpt-5.4/shed_rosary_alternative_bravery_reconciliation_slice_of.py --project jar_lantern --alternative ribbon
    python storyworlds/worlds/gpt-5.4/shed_rosary_alternative_bravery_reconciliation_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/shed_rosary_alternative_bravery_reconciliation_slice_of.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    fragile: bool = False
    sacred: bool = False
    rough: bool = False
    portable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Project:
    id: str
    label: str
    opening: str
    goal: str
    action: str
    place_line: str
    need_strength: int
    need_soft: bool
    need_pretty: bool
    finish_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Alternative:
    id: str
    label: str
    phrase: str
    strength: int
    soft: bool
    pretty: bool
    source: str
    use_line: str
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def compatible(project: Project, alternative: Alternative) -> bool:
    if alternative.strength < project.need_strength:
        return False
    if project.need_soft and not alternative.soft:
        return False
    if project.need_pretty and not alternative.pretty:
        return False
    return True


def explain_rejection(project: Project, alternative: Alternative) -> str:
    reasons: list[str] = []
    if alternative.strength < project.need_strength:
        reasons.append(
            f"{alternative.label} is too weak for {project.goal}"
        )
    if project.need_soft and not alternative.soft:
        reasons.append(
            f"{alternative.label} would rub or scrape, but this job needs something soft"
        )
    if project.need_pretty and not alternative.pretty:
        reasons.append(
            f"{project.goal} is meant to look cheerful, and {alternative.label} is too plain"
        )
    joined = "; ".join(reasons) if reasons else "this alternative does not fit the project"
    return f"(No story: {joined}. Pick an alternative that can honestly do the job.)"


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for pid, project in PROJECTS.items():
        for aid, alt in ALTERNATIVES.items():
            if compatible(project, alt):
                combos.append((pid, aid))
    return combos


def outcome_of(params: "StoryParams") -> str:
    return "easy" if params.honesty == "quick" else "wobbly"


def cause_break(sim: World) -> bool:
    rosary = sim.get("rosary")
    shed = sim.get("shed")
    if rosary.meters["borrowed"] >= THRESHOLD and shed.meters["used_nail"] >= THRESHOLD:
        rosary.meters["broken"] += 1
        rosary.meters["scattered"] += 1
        return True
    return False


def predict_break(world: World) -> bool:
    sim = world.copy()
    sim.get("rosary").meters["borrowed"] += 1
    sim.get("shed").meters["used_nail"] += 1
    return cause_break(sim)


def setup_story(world: World, child: Entity, sibling: Entity, elder: Entity,
                project: Project) -> None:
    child.memes["eager"] += 1
    sibling.memes["eager"] += 1
    world.say(
        f"After lunch, {child.id} and {sibling.id} wandered to the little shed at the back of the yard. "
        f"{project.opening}"
    )
    world.say(project.place_line)
    world.say(
        f'"Let\'s {project.action}," {child.id} said. The dim shed made the plan feel bigger than it really was.'
    )
    world.facts["bravery_need"] = "dark shed"


def need_and_tempt(world: World, child: Entity, sibling: Entity, elder: Entity,
                   project: Project, rosary: Entity) -> None:
    world.say(
        f"They needed something to help with {project.goal}, and {child.id} noticed {elder.label_word}'s rosary "
        f"resting on the hallway hook by the back door."
    )
    world.say(
        f'"It is round and strong enough," {child.id} whispered. "We can borrow it for one minute."'
    )
    sibling.memes["concern"] += 1
    child.memes["tempted"] += 1
    risk = predict_break(world)
    world.facts["predicted_break"] = risk
    if risk:
        world.say(
            f'{sibling.id} shook {sibling.pronoun("possessive")} head. "{elder.label_word.capitalize()} uses that rosary for praying. '
            f'The shed nail could catch it."'
        )


def borrow_and_break(world: World, child: Entity, sibling: Entity, rosary: Entity,
                     shed: Entity) -> None:
    rosary.meters["borrowed"] += 1
    child.memes["defiance"] += 1
    world.say(
        f"But the idea felt easy, so {child.id} slipped the rosary into {child.pronoun('possessive')} hand and carried it to the shed."
    )
    world.para()
    child.memes["bravery"] += 1
    world.say(
        f"The shed was cool and shadowy. {child.id} took a brave breath, stepped past the rakes, "
        f"and reached for the old nail inside."
    )
    shed.meters["used_nail"] += 1
    if cause_break(world):
        child.memes["shock"] += 1
        child.memes["guilt"] += 1
        sibling.memes["upset"] += 1
        world.say(
            "The beads clicked once, then the string caught on the rough nail and snapped. "
            "Small dark beads skipped across the floorboards and under a flowerpot."
        )


def blame_or_hide(world: World, child: Entity, sibling: Entity, params: "StoryParams") -> None:
    if params.honesty == "quick":
        child.memes["bravery"] += 1
        world.say(
            f'{child.id} went pale. "{sibling.id}, I broke it," {child.pronoun()} said at once. '
            f'"I have to tell {world.get("elder").label_word}."'
        )
        world.facts["confession_style"] = "at once"
        return

    child.memes["fear"] += 1
    child.memes["hiding"] += 1
    sibling.memes["hurt"] += 1
    world.say(
        f'{child.id} knelt fast and tried to scoop the beads into {child.pronoun("possessive")} pocket. '
        f'"Maybe we can fix it before anyone knows," {child.pronoun()} whispered.'
    )
    world.say(
        f'"That is worse," {sibling.id} said, with tears starting in {sibling.pronoun("possessive")} eyes. '
        f'"It was not ours."'
    )
    world.facts["confession_style"] = "after hiding"


def confess(world: World, child: Entity, sibling: Entity, elder: Entity,
            params: "StoryParams") -> None:
    world.para()
    if params.honesty == "quick":
        world.say(
            f"With the broken string in {child.pronoun('possessive')} hand, {child.id} walked back to the kitchen where "
            f"{elder.label_word} was trimming beans."
        )
    else:
        child.memes["bravery"] += 1
        child.memes["guilt"] += 1
        world.say(
            f"The beads felt heavy in {child.pronoun('possessive')} pocket. At last {child.id} took a long breath, "
            f"looked at {sibling.id}, and said, \"Come with me.\""
        )
        world.say(
            f"Together they went to the kitchen, and {child.id} opened {child.pronoun('possessive')} hand over the table."
        )
    world.say(
        f'"{elder.label_word.capitalize()}," {child.id} said, "I took your rosary to the shed and it broke. I am sorry."'
    )
    elder.memes["sad"] += 1
    world.facts["apologized"] = True


def reconcile(world: World, child: Entity, sibling: Entity, elder: Entity,
              rosary: Entity, alternative: Alternative, project: Project,
              params: "StoryParams") -> None:
    world.para()
    elder.memes["forgiveness"] += 1
    child.memes["relief"] += 1
    sibling.memes["relief"] += 1
    sibling.memes["forgiveness"] += 1
    child.memes["reconciled"] += 1
    sibling.memes["reconciled"] += 1
    elder.memes["reconciled"] += 1
    rosary.meters["gathered"] += 1
    rosary.meters["mended"] += 1
    world.say(
        f"{elder.label_word.capitalize()} looked at the scattered beads in silence for a moment, then pulled out a chair. "
        f'"Thank you for telling me the truth," {elder.pronoun()} said softly. '
        f'"I am sad the rosary broke, but I am glad you came to me."'
    )
    if params.honesty == "hesitant":
        world.say(
            f"{child.id}'s shoulders shook once. {sibling.id} leaned close, no longer angry, and helped count the beads on the table."
        )
    else:
        world.say(
            f"{sibling.id} let out the tight breath {sibling.pronoun()} had been holding and reached for the fallen beads too."
        )
    world.say(
        f"Together they found every bead, and {elder.label_word} showed them how to slide them back onto a fresh cord."
    )
    world.say(
        f'"And for the shed project," {elder.pronoun()} added, "let us find an alternative that belongs there."'
    )
    alt_ent = world.get("alternative")
    alt_ent.meters["chosen"] += 1
    alt_ent.meters["used"] += 1
    world.say(
        f"{elder.label_word.capitalize()} opened the old drawer in the shed and found {alternative.phrase} {alternative.source}. "
        f"{alternative.use_line}"
    )
    world.para()
    world.say(
        f"By evening, the rosary was resting safely back on its hook, and {project.finish_line}"
    )
    world.say(
        f"{child.id} smiled at {sibling.id}, and {sibling.id} smiled back. The shed no longer felt spooky, only small and familiar."
    )


PROJECTS = {
    "star_sign": Project(
        id="star_sign",
        label="star sign",
        opening="They had painted a paper star and wanted to hang it over the shed door.",
        goal="hanging the paper star over the shed door",
        action="hang our star where everyone can see it",
        place_line="The door was crooked, the wood smelled warm, and one bent nail stuck out beside the frame.",
        need_strength=1,
        need_soft=False,
        need_pretty=True,
        finish_line="their bright paper star swung over the shed door on a cheerful ribbon",
        tags={"shed", "ribbon", "craft"},
    ),
    "seed_bundle": Project(
        id="seed_bundle",
        label="seed bundle",
        opening="They wanted to tie seed packets into a neat bundle for spring planting.",
        goal="tying the seed packets together",
        action="tie the seed packets in one bundle for grandma",
        place_line="Inside the shed, little envelopes of seeds sat in a biscuit tin beside a row of clay pots.",
        need_strength=2,
        need_soft=False,
        need_pretty=False,
        finish_line="the seed packets were tied in one tidy bundle with garden twine on the workbench",
        tags={"shed", "garden", "twine"},
    ),
    "jar_lantern": Project(
        id="jar_lantern",
        label="jar lantern",
        opening="They had made a tiny jar lantern with paper leaves and wanted a loop to carry it into the shed.",
        goal="making a soft loop for the jar lantern",
        action="carry our lantern into the shed and see it glow",
        place_line="The shed corners were dusky, and an old nail waited by the shelf where they meant to hang the lantern for a moment.",
        need_strength=2,
        need_soft=True,
        need_pretty=False,
        finish_line="their little jar lantern hung safely for a moment from a soft cloth loop and shone like honey",
        tags={"shed", "light", "loop"},
    ),
}

ALTERNATIVES = {
    "ribbon": Alternative(
        id="ribbon",
        label="ribbon",
        phrase="a spool of red ribbon",
        strength=1,
        soft=True,
        pretty=True,
        source="from the cookie tin of saved wrapping things",
        use_line="It was the right thing for decoration, light in the fingers and pretty enough to make the paper star dance.",
        tags={"ribbon", "alternative"},
    ),
    "garden_twine": Alternative(
        id="garden_twine",
        label="garden twine",
        phrase="a roll of garden twine",
        strength=2,
        soft=False,
        pretty=False,
        source="from the shelf beside the trowel",
        use_line="It was plain, but it held the seed packets firmly and belonged with the real work of the shed.",
        tags={"twine", "alternative", "garden"},
    ),
    "cloth_loop": Alternative(
        id="cloth_loop",
        label="cloth loop",
        phrase="a strip of soft cloth cord",
        strength=2,
        soft=True,
        pretty=False,
        source="from a jar of saved ties and straps",
        use_line="It was gentle on the jar handle and strong enough to hold the lantern without scraping it.",
        tags={"cloth", "alternative", "light"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Ella", "Rose", "Nina", "Ava", "Lucy", "Tara"]
BOY_NAMES = ["Ben", "Noah", "Sam", "Eli", "Leo", "Owen", "Finn", "Max"]
ELDER_NAMES = {
    "grandmother": ["Grandma June", "Grandma Rosa", "Grandma Elsie"],
    "grandfather": ["Grandpa Joe", "Grandpa Luis", "Grandpa Ben"],
}
TRAITS = ["careful", "curious", "quiet", "thoughtful", "gentle", "steady"]


@dataclass
class StoryParams:
    project: str
    alternative: str
    honesty: str
    child_name: str
    child_gender: str
    sibling_name: str
    sibling_gender: str
    elder_type: str
    elder_name: str
    child_trait: str
    sibling_trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "rosary": [
        (
            "What is a rosary?",
            "A rosary is a string of beads some people use while they pray. It can be very special, so it should be handled with care and respect.",
        )
    ],
    "shed": [
        (
            "What is a shed?",
            "A shed is a small building in a yard where people keep tools, pots, and garden things. It can feel dark inside because it has less light than the house.",
        )
    ],
    "alternative": [
        (
            "What is an alternative?",
            "An alternative is another choice you can use instead of the first one. A good alternative solves the same problem in a safer or kinder way.",
        )
    ],
    "bravery": [
        (
            "What can bravery look like for a child?",
            "Bravery does not always mean doing something loud or dangerous. Sometimes it means telling the truth when you are scared you might be in trouble.",
        )
    ],
    "apology": [
        (
            "Why does saying sorry matter?",
            "A real apology shows that you understand the hurt or trouble you caused. It helps people trust you again, especially when you also try to fix the problem.",
        )
    ],
    "reconciliation": [
        (
            "What is reconciliation?",
            "Reconciliation is when people who were hurt or upset make peace again. It usually happens after truth, listening, and kindness.",
        )
    ],
    "ribbon": [
        (
            "What is ribbon good for?",
            "Ribbon is soft and pretty, so it is good for decoration and light tying jobs. It is not the best choice for heavy work.",
        )
    ],
    "twine": [
        (
            "What is garden twine for?",
            "Garden twine is a strong string used to tie plants, bundles, or garden things together. It is useful because it is stronger than ribbon.",
        )
    ],
    "cloth": [
        (
            "Why might a soft cloth loop be useful?",
            "A soft cloth loop can hold something without scratching it much. That makes it useful when a job needs both strength and gentleness.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "shed",
    "rosary",
    "alternative",
    "bravery",
    "apology",
    "reconciliation",
    "ribbon",
    "twine",
    "cloth",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    sibling = f["sibling"]
    elder = f["elder"]
    project = f["project"]
    alternative = f["alternative_cfg"]
    if f["outcome"] == "easy":
        mid = "confesses right away after the rosary breaks"
    else:
        mid = "first wants to hide the mistake, then finds the courage to confess"
    return [
        'Write a slice-of-life story for a 3-to-5-year-old that includes the words "shed", "rosary", and "alternative".',
        f"Tell a gentle story where {child.id} and {sibling.id} need something for {project.goal}, borrow {elder.label_word}'s rosary by mistake, and then use {alternative.label} as a better alternative.",
        f"Write a child-facing story about bravery and reconciliation where a mistake in a dark shed leads to an apology, and {child.id} {mid}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    sibling = f["sibling"]
    elder = f["elder"]
    project = f["project"]
    alternative = f["alternative_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {sibling.id}, two children working on a small shed project with {elder.label_word}. The trouble begins when they borrow a rosary that was not meant for the job.",
        ),
        (
            "Why did the children take the rosary to the shed?",
            f"They needed something for {project.goal}, and the rosary looked close at hand. It seemed easy to use, even though it was special and did not belong to them.",
        ),
        (
            "What went wrong in the shed?",
            "The rosary caught on a rough nail and the string snapped, so the beads scattered over the floor. The dark, crowded shed made the mistake happen quickly.",
        ),
    ]
    if f["outcome"] == "easy":
        qa.append(
            (
                f"How did {child.id} show bravery?",
                f"{child.id} told the truth right away, even though {child.pronoun()} felt scared and guilty. That kind of bravery matters because it gave the family a chance to fix the problem together.",
            )
        )
    else:
        qa.append(
            (
                f"How did {child.id} show bravery, even after a bad start?",
                f"At first {child.id} tried to hide the broken beads because {child.pronoun()} was afraid. Then {child.pronoun()} took a deep breath, confessed to {elder.label_word}, and chose honesty over hiding.",
            )
        )
    qa.append(
        (
            "What was the alternative?",
            f"The alternative was {alternative.phrase}, which really belonged with the shed supplies. It could do the job without risking the rosary again.",
        )
    )
    qa.append(
        (
            "How did the story end in reconciliation?",
            f"{elder.label_word.capitalize()} listened, accepted the apology, and helped restring the rosary. By the end, the children were smiling together again, and the project was finished the right way.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"shed", "rosary", "alternative", "bravery", "apology", "reconciliation"}
    alt = world.facts["alternative_cfg"]
    if "ribbon" in alt.tags:
        tags.add("ribbon")
    if "twine" in alt.tags:
        tags.add("twine")
    if "cloth" in alt.tags:
        tags.add("cloth")
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


def tell(params: StoryParams) -> World:
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.alternative not in ALTERNATIVES:
        raise StoryError(f"(Unknown alternative: {params.alternative})")

    project = PROJECTS[params.project]
    alternative = ALTERNATIVES[params.alternative]
    if not compatible(project, alternative):
        raise StoryError(explain_rejection(project, alternative))

    world = World()
    child = world.add(
        Entity(
            id=params.child_name,
            kind="character",
            type=params.child_gender,
            role="child",
            traits=[params.child_trait],
            label=params.child_name,
        )
    )
    sibling = world.add(
        Entity(
            id=params.sibling_name,
            kind="character",
            type=params.sibling_gender,
            role="sibling",
            traits=[params.sibling_trait],
            label=params.sibling_name,
        )
    )
    elder = world.add(
        Entity(
            id="elder",
            kind="character",
            type=params.elder_type,
            role="elder",
            label=params.elder_name,
        )
    )
    rosary = world.add(
        Entity(
            id="rosary",
            type="rosary",
            label="rosary",
            phrase=f"{elder.label_word}'s rosary",
            fragile=True,
            sacred=True,
            tags={"rosary"},
        )
    )
    shed = world.add(
        Entity(
            id="shed",
            type="shed",
            label="shed",
            phrase="the little shed",
            rough=True,
            tags={"shed"},
        )
    )
    world.add(
        Entity(
            id="alternative",
            type="tool",
            label=alternative.label,
            phrase=alternative.phrase,
            tags=set(alternative.tags),
        )
    )

    setup_story(world, child, sibling, elder, project)
    world.para()
    need_and_tempt(world, child, sibling, elder, project, rosary)
    borrow_and_break(world, child, sibling, rosary, shed)
    blame_or_hide(world, child, sibling, params)
    confess(world, child, sibling, elder, params)
    reconcile(world, child, sibling, elder, rosary, alternative, project, params)

    world.facts.update(
        child=child,
        sibling=sibling,
        elder=elder,
        project=project,
        alternative_cfg=alternative,
        rosary=rosary,
        outcome=outcome_of(params),
        honesty=params.honesty,
        used_alternative=True,
        reconciliation=True,
    )
    return world


CURATED = [
    StoryParams(
        project="star_sign",
        alternative="ribbon",
        honesty="quick",
        child_name="Maya",
        child_gender="girl",
        sibling_name="Ben",
        sibling_gender="boy",
        elder_type="grandmother",
        elder_name="Grandma June",
        child_trait="curious",
        sibling_trait="careful",
    ),
    StoryParams(
        project="seed_bundle",
        alternative="garden_twine",
        honesty="hesitant",
        child_name="Leo",
        child_gender="boy",
        sibling_name="Rose",
        sibling_gender="girl",
        elder_type="grandmother",
        elder_name="Grandma Rosa",
        child_trait="thoughtful",
        sibling_trait="gentle",
    ),
    StoryParams(
        project="jar_lantern",
        alternative="cloth_loop",
        honesty="quick",
        child_name="Ella",
        child_gender="girl",
        sibling_name="Max",
        sibling_gender="boy",
        elder_type="grandfather",
        elder_name="Grandpa Joe",
        child_trait="steady",
        sibling_trait="quiet",
    ),
    StoryParams(
        project="jar_lantern",
        alternative="cloth_loop",
        honesty="hesitant",
        child_name="Finn",
        child_gender="boy",
        sibling_name="Ava",
        sibling_gender="girl",
        elder_type="grandmother",
        elder_name="Grandma Elsie",
        child_trait="curious",
        sibling_trait="careful",
    ),
]


ASP_RULES = r"""
fits(P, A) :- project(P), alternative(A),
              need_strength(P, PS), alt_strength(A, AS), AS >= PS,
              not need_soft(P), not need_pretty(P).
fits(P, A) :- project(P), alternative(A),
              need_strength(P, PS), alt_strength(A, AS), AS >= PS,
              need_soft(P), alt_soft(A),
              not need_pretty(P).
fits(P, A) :- project(P), alternative(A),
              need_strength(P, PS), alt_strength(A, AS), AS >= PS,
              need_pretty(P), alt_pretty(A),
              not need_soft(P).
fits(P, A) :- project(P), alternative(A),
              need_strength(P, PS), alt_strength(A, AS), AS >= PS,
              need_soft(P), alt_soft(A),
              need_pretty(P), alt_pretty(A).

valid(P, A) :- fits(P, A).

outcome(easy) :- honesty(quick).
outcome(wobbly) :- honesty(hesitant).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, project in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("need_strength", pid, project.need_strength))
        if project.need_soft:
            lines.append(asp.fact("need_soft", pid))
        if project.need_pretty:
            lines.append(asp.fact("need_pretty", pid))
    for aid, alt in ALTERNATIVES.items():
        lines.append(asp.fact("alternative", aid))
        lines.append(asp.fact("alt_strength", aid, alt.strength))
        if alt.soft:
            lines.append(asp.fact("alt_soft", aid))
        if alt.pretty:
            lines.append(asp.fact("alt_pretty", aid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    model = asp.one_model(
        asp_program(
            f"honesty({params.honesty}).",
            "#show outcome/1.",
        )
    )
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if ent.fragile:
            flags.append("fragile")
        if ent.sacred:
            flags.append("sacred")
        if ent.rough:
            flags.append("rough")
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:11} ({ent.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in asp:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    for honesty in ("quick", "hesitant"):
        for pid, aid in valid_combos():
            cases.append(
                StoryParams(
                    project=pid,
                    alternative=aid,
                    honesty=honesty,
                    child_name="Maya",
                    child_gender="girl",
                    sibling_name="Ben",
                    sibling_gender="boy",
                    elder_type="grandmother",
                    elder_name="Grandma June",
                    child_trait="curious",
                    sibling_trait="careful",
                )
            )
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a shed, a rosary, a better alternative, and brave reconciliation."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--alternative", choices=ALTERNATIVES)
    ap.add_argument("--honesty", choices=["quick", "hesitant"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--sibling-name")
    ap.add_argument("--sibling-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (project, alternative) pairs from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.alternative:
        project = PROJECTS[args.project]
        alternative = ALTERNATIVES[args.alternative]
        if not compatible(project, alternative):
            raise StoryError(explain_rejection(project, alternative))

    combos = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.alternative is None or combo[1] == args.alternative)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, alt_id = rng.choice(sorted(combos))
    honesty = args.honesty or rng.choice(["quick", "hesitant"])
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    sibling_gender = args.sibling_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or pick_name(rng, child_gender)
    sibling_name = args.sibling_name or pick_name(rng, sibling_gender, avoid=child_name)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])
    elder_name = rng.choice(ELDER_NAMES[elder_type])
    child_trait = rng.choice(TRAITS)
    sibling_trait = rng.choice([t for t in TRAITS if t != child_trait] or TRAITS)

    return StoryParams(
        project=project_id,
        alternative=alt_id,
        honesty=honesty,
        child_name=child_name,
        child_gender=child_gender,
        sibling_name=sibling_name,
        sibling_gender=sibling_gender,
        elder_type=elder_type,
        elder_name=elder_name,
        child_trait=child_trait,
        sibling_trait=sibling_trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(f"{len(combos)} compatible (project, alternative) pairs:\n")
        for project, alternative in combos:
            print(f"  {project:12} {alternative}")
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
            header = f"### {p.child_name} and {p.sibling_name}: {p.project} with {p.alternative} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
