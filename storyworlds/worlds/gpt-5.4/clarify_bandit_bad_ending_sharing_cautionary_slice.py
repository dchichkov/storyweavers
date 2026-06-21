#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/clarify_bandit_bad_ending_sharing_cautionary_slice.py
================================================================================

A standalone story world for a small slice-of-life cautionary tale about sharing,
misunderstanding, and a bad ending. Two children are doing an everyday activity
together. One child has a needed item, refuses to share it, and calls the other
child a "bandit" when the item goes missing or gets borrowed. A grown-up may try
to clarify the misunderstanding, but if that clarification comes too late, the
shared plan falls apart and the ending stays sad.

The world is intentionally narrow. It prefers a few plausible stories over many
weak ones:

* the activity must be one where a single tool or supply is genuinely needed by
  both children;
* the item must be safely shareable;
* the misunderstanding only works when the item is personally owned enough to
  trigger possessiveness;
* the ending is cautionary: the children lose the chance to finish together, and
  the closing image proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/clarify_bandit_bad_ending_sharing_cautionary_slice.py
    python storyworlds/worlds/gpt-5.4/clarify_bandit_bad_ending_sharing_cautionary_slice.py --activity coloring --item markers
    python storyworlds/worlds/gpt-5.4/clarify_bandit_bad_ending_sharing_cautionary_slice.py --item tablet
    python storyworlds/worlds/gpt-5.4/clarify_bandit_bad_ending_sharing_cautionary_slice.py --all --qa
    python storyworlds/worlds/gpt-5.4/clarify_bandit_bad_ending_sharing_cautionary_slice.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/clarify_bandit_bad_ending_sharing_cautionary_slice.py --verify
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
_WORLD_DIR = os.path.dirname(_THIS)
_PKG_DIR = os.path.dirname(os.path.dirname(_WORLD_DIR))
sys.path.insert(0, _PKG_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    owner: Optional[str] = None
    needed_for: set[str] = field(default_factory=set)
    shareable: bool = False
    personal: bool = False
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


# ---------------------------------------------------------------------------
# World knobs
# ---------------------------------------------------------------------------
@dataclass
class Activity:
    id: str
    place: str
    opener: str
    project: str
    together_line: str
    need_line: str
    loss_image: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareItem:
    id: str
    label: str
    phrase: str
    plural: bool
    needed_for: set[str]
    shareable: bool
    personal: bool
    borrow_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clarifier:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"holder", "waiter"}]

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
        return c


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_exclusion(world: World) -> list[str]:
    out: list[str] = []
    holder = world.get("holder")
    waiter = world.get("waiter")
    item = world.get("item")
    if holder.memes["refusal"] < THRESHOLD:
        return out
    if waiter.memes["need"] < THRESHOLD:
        return out
    sig = ("exclusion", holder.id, waiter.id, item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    waiter.memes["hurt"] += 1
    waiter.memes["left_out"] += 1
    holder.memes["possessive"] += 1
    world.get("project").meters["stalled"] += 1
    out.append("__stalled__")
    return out


def _r_accusation(world: World) -> list[str]:
    out: list[str] = []
    holder = world.get("holder")
    waiter = world.get("waiter")
    item = world.get("item")
    if item.meters["moved"] < THRESHOLD:
        return out
    if holder.memes["suspicion"] < THRESHOLD:
        return out
    sig = ("accusation", holder.id, waiter.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    waiter.memes["shame"] += 1
    waiter.memes["hurt"] += 1
    holder.memes["anger"] += 1
    out.append("__bandit__")
    return out


def _r_rift(world: World) -> list[str]:
    out: list[str] = []
    holder = world.get("holder")
    waiter = world.get("waiter")
    if waiter.memes["hurt"] < THRESHOLD:
        return out
    if holder.memes["anger"] < THRESHOLD and holder.memes["possessive"] < THRESHOLD:
        return out
    sig = ("rift",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    holder.memes["distance"] += 1
    waiter.memes["distance"] += 1
    world.get("project").meters["ruined"] += 1
    out.append("__rift__")
    return out


CAUSAL_RULES = [
    Rule("exclusion", "social", _r_exclusion),
    Rule("accusation", "social", _r_accusation),
    Rule("rift", "social", _r_rift),
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
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------
def item_fits(activity: Activity, item: ShareItem) -> bool:
    return activity.id in item.needed_for and item.shareable


def sensible_clarifiers() -> list[Clarifier]:
    return [c for c in CLARIFIERS.values() if c.sense >= SENSE_MIN]


def misunderstanding_severity(item: ShareItem, delay: int) -> int:
    return (2 if item.personal else 1) + delay


def is_cleared(clarifier: Clarifier, item: ShareItem, delay: int) -> bool:
    return clarifier.power >= misunderstanding_severity(item, delay)


def explain_rejection(activity: Activity, item: ShareItem) -> str:
    if activity.id not in item.needed_for:
        return (
            f"(No story: {item.label} is not actually needed for {activity.project}, "
            f"so refusing to share it would not honestly stall the shared plan.)"
        )
    if not item.shareable:
        return (
            f"(No story: {item.label} is not a simple shareable object in this world. "
            f"The conflict here depends on a child reasonably being able to take turns with it.)"
        )
    return "(No story: this combination does not form the intended sharing problem.)"


def explain_clarifier(cid: str) -> str:
    c = CLARIFIERS[cid]
    better = ", ".join(sorted(x.id for x in sensible_clarifiers()))
    return (
        f"(Refusing clarifier '{cid}': it scores too low on common sense "
        f"(sense={c.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_rift(world: World, delay: int) -> dict:
    sim = world.copy()
    holder = sim.get("holder")
    waiter = sim.get("waiter")
    item = sim.get("item")
    holder.memes["refusal"] += 1
    waiter.memes["need"] += 1
    if delay > 0:
        item.meters["moved"] += 1
        holder.memes["suspicion"] += 1
    propagate(sim, narrate=False)
    project = sim.get("project")
    return {
        "stalled": project.meters["stalled"] >= THRESHOLD,
        "ruined": project.meters["ruined"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def setup_scene(world: World, holder: Entity, waiter: Entity, activity: Activity) -> None:
    for kid in (holder, waiter):
        kid.memes["joy"] += 1
    world.say(
        f"After school, {holder.id} and {waiter.id} sat together in {activity.place}. "
        f"{activity.opener}"
    )
    world.say(activity.together_line)


def name_item(world: World, holder: Entity, item: ShareItem) -> None:
    world.say(
        f"In the middle of the work lay {item.phrase}, the one thing both children needed most."
    )
    world.say(
        f"{holder.id} had brought {item.label} from home and kept {('them' if item.plural else 'it')} close."
    )


def need_turn(world: World, waiter: Entity, holder: Entity, activity: Activity, item: ShareItem) -> None:
    waiter.memes["need"] += 1
    world.say(
        f'Soon {waiter.id} leaned nearer. "{activity.need_line}" {waiter.pronoun()} asked.'
    )
    world.say(item.borrow_line.format(waiter=waiter.id, holder=holder.id))


def refuse(world: World, holder: Entity, waiter: Entity, item: ShareItem) -> None:
    holder.memes["refusal"] += 1
    propagate(world, narrate=False)
    word = "them" if item.plural else "it"
    world.say(
        f'{holder.id} pulled {word} back and shook {holder.pronoun("possessive")} head. '
        f'"No. They are mine," {holder.pronoun()} said.'
        if item.plural
        else f'{holder.id} pulled it back and shook {holder.pronoun("possessive")} head. '
             f'"No. It is mine," {holder.pronoun()} said.'
    )
    if waiter.memes["left_out"] >= THRESHOLD:
        world.say(
            f"{waiter.id} tried to keep helping, but the shared project slowed and the cheerful room felt smaller."
        )


def move_item(world: World, waiter: Entity, item: Entity) -> None:
    item.meters["moved"] += 1
    waiter.memes["impatience"] += 1
    world.say(
        f"After waiting and waiting, {waiter.id} quietly moved the {item.label} a little closer, hoping for just one quick turn."
    )


def accuse_bandit(world: World, holder: Entity, waiter: Entity) -> None:
    holder.memes["suspicion"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{holder.id} looked down, saw that the supplies had shifted, and frowned. '
        f'"Did you take them? Don\'t be a little bandit," {holder.pronoun()} snapped.'
    )


def clarify_attempt(world: World, parent: Entity, holder: Entity, waiter: Entity,
                    clarifier: Clarifier, item: ShareItem, delay: int) -> bool:
    pred = predict_rift(world, delay)
    world.facts["predicted_stalled"] = pred["stalled"]
    world.facts["predicted_ruined"] = pred["ruined"]
    world.say(
        f"{parent.label_word.capitalize()} heard the sharp voices from the next room and came over."
    )
    world.say(
        f"{parent.pronoun().capitalize()} tried to clarify what had happened before anyone cried harder."
    )
    cleared = is_cleared(clarifier, item, delay)
    if cleared:
        world.say(
            f"{parent.pronoun().capitalize()} {clarifier.text}"
        )
    else:
        world.say(
            f"{parent.pronoun().capitalize()} {clarifier.fail}"
        )
    return cleared


def late_hurt(world: World, holder: Entity, waiter: Entity, activity: Activity) -> None:
    propagate(world, narrate=False)
    world.say(
        f"The explanation came too late. {waiter.id}'s face had already gone stiff, and {holder.id} was too cross to listen kindly."
    )
    world.say(
        f"Instead of finishing the {activity.project}, each child turned away and worked alone for a moment, then not at all."
    )


def bad_ending(world: World, holder: Entity, waiter: Entity, activity: Activity, item: ShareItem) -> None:
    holder.memes["regret"] += 1
    waiter.memes["sadness"] += 1
    world.say(
        f"No one said sorry in time. The chance to share had slipped away, and the room stayed quiet in the wrong way."
    )
    world.say(activity.loss_image)
    world.say(
        f"The unfinished {activity.project} sat between them, and even the {item.label} no longer looked special."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(activity: Activity, item_cfg: ShareItem, clarifier: Clarifier,
         holder_name: str = "Lila", holder_gender: str = "girl",
         waiter_name: str = "Ben", waiter_gender: str = "boy",
         parent_type: str = "mother", delay: int = 1) -> World:
    world = World()
    holder = world.add(Entity(id="holder", kind="character", type=holder_gender, label=holder_name, role="holder"))
    waiter = world.add(Entity(id="waiter", kind="character", type=waiter_gender, label=waiter_name, role="waiter"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    item = world.add(Entity(
        id="item",
        type="item",
        label=item_cfg.label,
        owner="holder",
        needed_for=set(item_cfg.needed_for),
        shareable=item_cfg.shareable,
        personal=item_cfg.personal,
    ))
    project = world.add(Entity(id="project", type="project", label=activity.project))

    setup_scene(world, holder, waiter, activity)
    name_item(world, holder, item_cfg)

    world.para()
    need_turn(world, waiter, holder, activity, item_cfg)
    refuse(world, holder, waiter, item_cfg)

    world.para()
    move_item(world, waiter, item)
    accuse_bandit(world, holder, waiter)
    cleared = clarify_attempt(world, parent, holder, waiter, clarifier, item_cfg, delay)

    world.para()
    if cleared:
        # This world stays cautionary/bad-ending oriented: even a decent attempt can be too late
        # when delay has already allowed hurt and accusation to set in.
        late_hurt(world, holder, waiter, activity)
    else:
        late_hurt(world, holder, waiter, activity)
    bad_ending(world, holder, waiter, activity, item_cfg)

    world.facts.update(
        activity=activity,
        item_cfg=item_cfg,
        clarifier=clarifier,
        holder=holder,
        waiter=waiter,
        parent=parent,
        item=item,
        project=project,
        delay=delay,
        outcome="bad",
        cleared=cleared,
        accused=item.meters["moved"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ACTIVITIES = {
    "coloring": Activity(
        "coloring",
        "the kitchen",
        "Sunlight lay across the table, and two half-finished paper houses waited beside a bowl of apple slices.",
        "street scene",
        "They were coloring one big street scene together, trading ideas about windows, doors, and tiny pets in the yards.",
        "Could I use the bright ones for the roof now?",
        "At the end, the paper street was still pale on one side, and the apple slices had gone soft while nobody ate them.",
        "color",
        tags={"sharing", "art"},
    ),
    "sticker_album": Activity(
        "sticker_album",
        "the living room",
        "The rug was warm under their knees, and an open album lay between them with empty spaces waiting to be filled.",
        "album page",
        "They were making one sticker album page together, lining up stars, animals, and shiny circles in careful rows.",
        "Can I have a turn with those for this empty corner?",
        "At the end, the album page still had a blank square in the middle, and the shiny stickers stayed stuck to their backing sheet.",
        "sticker",
        tags={"sharing", "stickers"},
    ),
    "cardboard_town": Activity(
        "cardboard_town",
        "the den",
        "A laundry basket of boxes stood nearby, and the room smelled faintly of tape and crayons.",
        "cardboard town",
        "They were building a cardboard town together, each child folding little shops while planning where the pretend bakery should go.",
        "May I use that for the sign and the bakery door?",
        "At the end, the cardboard town had one crooked shop and one flat box, and the pretend bakery never opened at all.",
        "town",
        tags={"sharing", "crafts"},
    ),
}

ITEMS = {
    "markers": ShareItem(
        "markers",
        "markers",
        "a fat box of bright markers",
        True,
        {"coloring", "cardboard_town"},
        True,
        True,
        '"{waiter}, can I please use just the red and blue for one minute?"',
        tags={"markers", "art"},
    ),
    "stickers": ShareItem(
        "stickers",
        "stickers",
        "a sheet of shiny stickers",
        True,
        {"sticker_album"},
        True,
        True,
        '"{holder}, I only need one small star for my side," {waiter} said.',
        tags={"stickers", "sharing"},
    ),
    "tape": ShareItem(
        "tape",
        "tape",
        "a roll of striped tape",
        False,
        {"cardboard_town"},
        True,
        False,
        '"Can I use the tape for one door and then pass it right back?" {waiter} asked.',
        tags={"tape", "crafts"},
    ),
    # Known object, but not a good sharing-tool story here.
    "tablet": ShareItem(
        "tablet",
        "tablet",
        "a glowing tablet",
        False,
        set(),
        False,
        True,
        '"Can I use that next?" {waiter} asked.',
        tags={"screen"},
    ),
}

CLARIFIERS = {
    "ask_both": Clarifier(
        "ask_both",
        3,
        3,
        "asked both children to stop, take one breath, and tell the whole story from the beginning.",
        "spoke too generally about being nice, but did not ask enough questions to sort out what had happened.",
        "asked both children to explain what happened before deciding",
        tags={"clarify"},
    ),
    "show_turns": Clarifier(
        "show_turns",
        3,
        2,
        "put a small cup in the middle of the table and suggested taking turns after each color or sticker.",
        "suggested turns, but only after the children had already stopped trusting each other enough to try.",
        "suggested a clear turn-taking plan",
        tags={"clarify", "sharing"},
    ),
    "hush": Clarifier(
        "hush",
        1,
        1,
        "told them to quiet down without really sorting out who felt hurt or why.",
        "only hushed the room, so the misunderstanding stayed tangled.",
        "hushed them without clarifying the misunderstanding",
        tags={"quiet"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Zoe", "Ella", "Ruby", "Nora", "Anna", "Maya"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Noah", "Eli", "Finn", "Jack"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for act_id, act in ACTIVITIES.items():
        for item_id, item in ITEMS.items():
            if item_fits(act, item):
                combos.append((act_id, item_id))
    return combos


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    activity: str
    item: str
    clarifier: str
    holder_name: str
    holder_gender: str
    waiter_name: str
    waiter_gender: str
    parent: str
    delay: int = 1
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "sharing": [
        ("Why is sharing important when two children are making something together?",
         "Sharing lets both children keep working, so the activity stays a together-thing instead of turning into a fight. When one child keeps the needed item all to themself, the shared plan usually stalls.")
    ],
    "clarify": [
        ("What does clarify mean?",
         "To clarify means to make something clearer by explaining it carefully. People clarify misunderstandings by slowing down and telling what really happened.")
    ],
    "markers": [
        ("Why can markers cause a sharing problem?",
         "A box of markers has many colors children may both want at the same time. Taking turns helps each child use the colors they need.")
    ],
    "stickers": [
        ("Why do children sometimes argue over stickers?",
         "Stickers can feel special because there may be only a few favorite ones. That can make a child cling to them instead of sharing.")
    ],
    "tape": [
        ("Why is tape often passed back and forth during crafts?",
         "A roll of tape is one tool that many hands may need for different little jobs. Passing it back and forth helps everyone keep building.")
    ],
    "art": [
        ("What can happen if children do not share art supplies?",
         "The project can stop in the middle, and hurt feelings can grow fast. Then the work and the friendship both suffer.")
    ],
    "crafts": [
        ("Why do crafts go better with turn-taking?",
         "Turn-taking gives each person a fair chance to use the needed tools. It also makes the work feel calmer and kinder.")
    ],
}
KNOWLEDGE_ORDER = ["sharing", "clarify", "markers", "stickers", "tape", "art", "crafts"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    holder = f["holder"].label
    waiter = f["waiter"].label
    act = f["activity"]
    item = f["item_cfg"]
    return [
        f'Write a slice-of-life cautionary story for a 3-to-5-year-old that includes the words "clarify" and "bandit".',
        f"Tell a sad everyday story where {holder} refuses to share {item.label} with {waiter} during {act.project}, and a grown-up tries to clarify the misunderstanding too late.",
        f"Write a sharing story with a bad ending: one child calls another child a bandit, the project falls apart, and the quiet ending shows what refusing to share cost them.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    holder = f["holder"]
    waiter = f["waiter"]
    parent = f["parent"]
    act = f["activity"]
    item = f["item_cfg"]
    clarifier = f["clarifier"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {holder.label} and {waiter.label}, two children trying to make {act.project} together, and their {parent.label_word} who came to help. The trouble began because they both needed the same {item.label}."
        ),
        (
            f"Why did {waiter.label} want the {item.label}?",
            f"{waiter.label} wanted a turn because the {item.label} were part of the shared work. Without them, {waiter.pronoun('subject')} could not finish {waiter.pronoun('possessive')} side of the project."
            if item.plural
            else f"{waiter.label} wanted a turn because the {item.label} was part of the shared work. Without it, {waiter.pronoun('subject')} could not finish {waiter.pronoun('possessive')} side of the project."
        ),
        (
            f"Why did {holder.label} call {waiter.label} a bandit?",
            f"{holder.label} saw that the {item.label} had been moved and jumped to the wrong idea. Instead of asking calmly what happened, {holder.pronoun('subject')} accused {waiter.label} of trying to steal a turn."
        ),
        (
            "What did the grown-up try to do?",
            f"{parent.label_word.capitalize()} tried to clarify the argument by stepping in and sorting out the story. {parent.pronoun().capitalize()} {clarifier.qa_text}, but the hurt feelings were already strong."
        ),
        (
            "How did the story end?",
            f"It ended sadly: the children did not share in time, and they never finished {act.project}. The last image shows the lost chance clearly, because {act.loss_image.lower()}"
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sharing"} | set(f["activity"].tags) | set(f["item_cfg"].tags) | set(f["clarifier"].tags)
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
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.shareable:
            bits.append("shareable=True")
        if e.personal:
            bits.append("personal=True")
        if e.needed_for:
            bits.append(f"needed_for={sorted(e.needed_for)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("coloring", "markers", "ask_both", "Lila", "girl", "Ben", "boy", "mother", 1),
    StoryParams("sticker_album", "stickers", "show_turns", "Maya", "girl", "Leo", "boy", "father", 2),
    StoryParams("cardboard_town", "tape", "ask_both", "Nora", "girl", "Max", "boy", "mother", 1),
    StoryParams("coloring", "markers", "show_turns", "Sam", "boy", "Ruby", "girl", "father", 2),
]


def outcome_of(params: StoryParams) -> str:
    return "bad"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(A, I) :- activity(A), item(I), needed_for(I, A), shareable(I).
sensible(C) :- clarifier(C), sense(C, S), sense_min(M), S >= M.

% --- outcome-related helpers ----------------------------------------------
severity(V) :- chosen_item(I), personal(I), delay(D), V = 2 + D.
severity(V) :- chosen_item(I), not personal(I), delay(D), V = 1 + D.
cleared :- chosen_clarifier(C), power(C, P), severity(V), P >= V.

% This world is intentionally cautionary: once the accusation beat has happened,
% the ending remains bad even if a reasonable grown-up nearly clears it.
outcome(bad).
late_too_late :- cleared.
late_too_late :- not cleared.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.shareable:
            lines.append(asp.fact("shareable", iid))
        if item.personal:
            lines.append(asp.fact("personal", iid))
        for need in sorted(item.needed_for):
            lines.append(asp.fact("needed_for", iid, need))
    for cid, clar in CLARIFIERS.items():
        lines.append(asp.fact("clarifier", cid))
        lines.append(asp.fact("sense", cid, clar.sense))
        lines.append(asp.fact("power", cid, clar.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_clarifier", params.clarifier),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {c.id for c in sensible_clarifiers()}
    if c_sens == p_sens:
        print(f"OK: sensible clarifiers match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible clarifiers: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for s in range(20):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    # Smoke test: ordinary generation must not crash.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story in smoke test")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generated and emitted a story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: sharing trouble, a late clarification, and a bad ending."
    )
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clarifier", choices=CLARIFIERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[1, 2], help="how late the grown-up clarifies")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.item:
        act, item = ACTIVITIES[args.activity], ITEMS[args.item]
        if not item_fits(act, item):
            raise StoryError(explain_rejection(act, item))
    if args.clarifier and CLARIFIERS[args.clarifier].sense < SENSE_MIN:
        raise StoryError(explain_clarifier(args.clarifier))

    combos = [
        c for c in valid_combos()
        if (args.activity is None or c[0] == args.activity)
        and (args.item is None or c[1] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    activity, item = rng.choice(sorted(combos))
    clarifier = args.clarifier or rng.choice(sorted(c.id for c in sensible_clarifiers()))
    holder_name, holder_gender = _pick_kid(rng)
    waiter_name, waiter_gender = _pick_kid(rng, avoid=holder_name)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.choice([1, 2])
    return StoryParams(
        activity=activity,
        item=item,
        clarifier=clarifier,
        holder_name=holder_name,
        holder_gender=holder_gender,
        waiter_name=waiter_name,
        waiter_gender=waiter_gender,
        parent=parent,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        ACTIVITIES[params.activity],
        ITEMS[params.item],
        CLARIFIERS[params.clarifier],
        params.holder_name,
        params.holder_gender,
        params.waiter_name,
        params.waiter_gender,
        params.parent,
        params.delay,
    )

    # Replace internal ids in the child-facing story.
    story = world.render().replace("holder", params.holder_name).replace("waiter", params.waiter_name)

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible clarifiers: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (activity, item) combos:\n")
        for activity, item in combos:
            print(f"  {activity:14} {item}")
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
            header = f"### {p.holder_name} & {p.waiter_name}: {p.activity} with {p.item} ({p.clarifier}, bad ending)"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
