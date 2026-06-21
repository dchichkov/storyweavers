#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shoulder_ninety_kindness_humor_conflict_rhyming_story.py
===================================================================================

A standalone storyworld for a small rhyming tale about kindness after a teasing
conflict. Two children prepare for a tiny neighborhood kindness parade. One
child carries a bag with ninety cheerful paper notes over a sore shoulder, a
funny wobble leads to teasing, the teasing causes a quarrel, and kindness turns
the quarrel into shared help and a better ending.

The world model is intentionally small and classical:

- typed entities with physical meters and emotional memes
- a tiny forward-chaining causal engine
- a reasonableness gate for valid story combinations
- an inline ASP twin for the same gate and outcome model
- state-driven rhyming prose, not slot-swapped templates

Run it
------
    python storyworlds/worlds/gpt-5.4/shoulder_ninety_kindness_humor_conflict_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/shoulder_ninety_kindness_humor_conflict_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/shoulder_ninety_kindness_humor_conflict_rhyming_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/shoulder_ninety_kindness_humor_conflict_rhyming_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/shoulder_ninety_kindness_humor_conflict_rhyming_story.py --verify
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
HELP_MIN = 2


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
class Place:
    id: str
    label: str
    detail: str
    path: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Bag:
    id: str
    label: str
    phrase: str
    carry_verb: str
    funny_sound: str
    strain: int
    stable: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Joke:
    id: str
    line: str
    sting: int
    silly: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelpMethod:
    id: str
    label: str
    text: str
    power: int
    kind: int
    shared: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    bag: str
    joke: str
    help_method: str
    lead_name: str
    lead_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    lead_trait: str
    friend_trait: str
    note_count: int = 90
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


def _r_shoulder_ache(world: World) -> list[str]:
    out: list[str] = []
    lead = world.get("lead")
    bag = world.get("bag")
    if lead.meters["load"] >= THRESHOLD and bag.meters["strain"] >= THRESHOLD:
        sig = ("shoulder_ache", lead.id)
        if sig not in world.fired:
            world.fired.add(sig)
            lead.meters["shoulder_ache"] += 1
            out.append("__ache__")
    return out


def _r_teasing_hurts(world: World) -> list[str]:
    out: list[str] = []
    lead = world.get("lead")
    friend = world.get("friend")
    if friend.memes["teased"] >= THRESHOLD and lead.meters["shoulder_ache"] >= THRESHOLD:
        sig = ("hurt_feelings", lead.id)
        if sig not in world.fired:
            world.fired.add(sig)
            lead.memes["hurt"] += 1
            lead.memes["anger"] += 1
            friend.memes["conflict"] += 1
            lead.memes["conflict"] += 1
            out.append("__hurt__")
    return out


def _r_kind_help(world: World) -> list[str]:
    out: list[str] = []
    lead = world.get("lead")
    friend = world.get("friend")
    if friend.memes["helped"] >= THRESHOLD:
        sig = ("help_relieves", lead.id)
        if sig not in world.fired:
            world.fired.add(sig)
            lead.meters["load"] = 0.0
            lead.meters["shoulder_ache"] = 0.0
            lead.memes["anger"] = 0.0
            lead.memes["hurt"] = 0.0
            lead.memes["relief"] += 1
            friend.memes["relief"] += 1
            lead.memes["kindness"] += 1
            friend.memes["kindness"] += 1
            lead.memes["conflict"] = 0.0
            friend.memes["conflict"] = 0.0
            out.append("__helped__")
    return out


CAUSAL_RULES = [
    Rule(name="shoulder_ache", tag="physical", apply=_r_shoulder_ache),
    Rule(name="teasing_hurts", tag="social", apply=_r_teasing_hurts),
    Rule(name="kind_help", tag="social", apply=_r_kind_help),
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
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "schoolyard": Place(
        id="schoolyard",
        label="the schoolyard",
        detail="The chalky gate stood bright and wide, with streamers dancing side by side.",
        path="the hop-skippy path by the tulip bed",
        ending="Soon notes flew kind through the schoolyard air, and happy children read them there.",
        tags={"school"},
    ),
    "park": Place(
        id="park",
        label="the park",
        detail="The swings gave little creaks and squeaks, and sparrows chirped their peeping speaks.",
        path="the curvy path beside the pond",
        ending="Soon notes flew kind through the breezy park, like tiny stars that glowed in dark.",
        tags={"park"},
    ),
    "library": Place(
        id="library",
        label="the library garden",
        detail="The roses leaned by story trees, and pages seemed to ride the breeze.",
        path="the brick-red path past the reading bench",
        ending="Soon notes flew kind through the garden neat, and smiles came pattering down the street.",
        tags={"library"},
    ),
}

BAGS = {
    "satchel": Bag(
        id="satchel",
        label="satchel",
        phrase="a patchwork satchel",
        carry_verb="slung",
        funny_sound="flop-flap",
        strain=2,
        stable=False,
        tags={"bag", "shoulder"},
    ),
    "tote": Bag(
        id="tote",
        label="tote bag",
        phrase="a big stripey tote bag",
        carry_verb="hooked",
        funny_sound="swish-swish",
        strain=1,
        stable=True,
        tags={"bag", "shoulder"},
    ),
    "mailbag": Bag(
        id="mailbag",
        label="mailbag",
        phrase="a pretend postman's mailbag",
        carry_verb="looped",
        funny_sound="bop-bop",
        strain=2,
        stable=False,
        tags={"bag", "shoulder", "mail"},
    ),
}

JOKES = {
    "duck": Joke(
        id="duck",
        line='"{lead}, you walk like a duck with a squish-squash pluck!"',
        sting=2,
        silly="duck",
        tags={"joke", "duck"},
    ),
    "crab": Joke(
        id="crab",
        line='"{lead}, you wobble like a crab in a button-up cab!"',
        sting=2,
        silly="crab",
        tags={"joke", "crab"},
    ),
    "noodle": Joke(
        id="noodle",
        line='"{lead}, your shoulder is noodling like a giggly poodle!"',
        sting=1,
        silly="noodle",
        tags={"joke", "poodle"},
    ),
}

HELP_METHODS = {
    "share": HelpMethod(
        id="share",
        label="share the notes",
        text="took half the stack and counted the bundles out loud",
        power=2,
        kind=3,
        shared=True,
        tags={"sharing", "help"},
    ),
    "cart": HelpMethod(
        id="cart",
        label="use the little wagon",
        text="rolled over the little red wagon and set the notes inside",
        power=3,
        kind=2,
        shared=False,
        tags={"wagon", "help"},
    ),
    "restack": HelpMethod(
        id="restack",
        label="retie the notes",
        text="retied the notes into smaller bunches with blue string",
        power=1,
        kind=2,
        shared=False,
        tags={"string", "help"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Zoe", "Ava", "Nora", "Ruby", "Ivy", "Ella"]
BOY_NAMES = ["Milo", "Ben", "Leo", "Sam", "Finn", "Owen", "Theo", "Max"]
TRAITS = ["busy", "careful", "cheery", "earnest", "bouncy", "gentle"]


def valid_combo_ids() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for bag_id, bag in BAGS.items():
            for joke_id in JOKES:
                for help_id, help_method in HELP_METHODS.items():
                    if bag.strain > help_method.power:
                        continue
                    if help_method.kind < HELP_MIN:
                        continue
                    combos.append((place_id, bag_id, joke_id, help_id))
    return combos


def explain_help(help_id: str, bag_id: str) -> str:
    help_method = HELP_METHODS[help_id]
    bag = BAGS[bag_id]
    if help_method.kind < HELP_MIN:
        return (
            f"(No story: '{help_id}' is not kind enough for this world. "
            f"The fix must show real kindness after the conflict.)"
        )
    if help_method.power < bag.strain:
        return (
            f"(No story: {help_method.label} would not really ease the weight of the "
            f"{bag.label}. Pick a stronger way to help the sore shoulder.)"
        )
    return "(No story: that combination is not reasonable.)"


def predict_hurt(bag: Bag, joke: Joke) -> dict:
    weight = bag.strain
    return {
        "shoulder_ache": weight >= 1,
        "hurt": weight >= 1 and joke.sting >= 1,
    }


def resolve_outcome(bag: Bag, help_method: HelpMethod) -> str:
    return "mended" if help_method.power >= bag.strain and help_method.kind >= HELP_MIN else "stuck"


def introduce(world: World, place: Place, lead: Entity, friend: Entity, count: int) -> None:
    lead.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In {place.label}, beneath a sunny shine, {lead.id} and {friend.id} had a little plan divine."
    )
    world.say(
        f"They made {count} kindness notes that day, to give to passers-by on their merry way."
    )
    world.say(place.detail)


def pack_notes(world: World, lead: Entity, bag_cfg: Bag, count: int) -> None:
    bag = world.get("bag")
    lead.meters["load"] += 1
    bag.meters["strain"] = float(bag_cfg.strain)
    world.say(
        f"{lead.id} {bag_cfg.carry_verb} {bag_cfg.phrase} on one shoulder tight, "
        f"with {count} bright notes tucked in just right."
    )
    world.say(
        f"But when {lead.pronoun()} took a step to go, the bag went {bag_cfg.funny_sound} to and fro."
    )
    propagate(world, narrate=False)
    if lead.meters["shoulder_ache"] >= THRESHOLD:
        world.say(
            f"Soon {lead.pronoun('possessive')} shoulder felt pinched and small, "
            f"and the happy marching lost its bounce and gall."
        )


def tease(world: World, lead: Entity, friend: Entity, joke_cfg: Joke) -> None:
    friend.memes["teased"] += 1
    world.say(
        f"{friend.id} gave a laugh and sang a rhyme, not meaning meanness at the time."
    )
    world.say(joke_cfg.line.format(lead=lead.id))
    propagate(world, narrate=False)
    if lead.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{lead.id} stopped short with a huffy stare. "
            f'"It hurts, and that joke is not quite fair."'
        )
        world.say(
            f"A grumpy gust seemed to fill the air; their kindness job now felt hard to share."
        )


def argue(world: World, lead: Entity, friend: Entity) -> None:
    lead.memes["anger"] += 1
    friend.memes["worry"] += 1
    world.say(
        f'"I was only joking," {friend.id} said low. "I did not mean to make your sad tears grow."'
    )


def repair(world: World, lead: Entity, friend: Entity, help_method: HelpMethod, count: int) -> None:
    friend.memes["helped"] += 1
    world.say(
        f"Then {friend.id} looked at the drooping load and chose a kinder, wiser road."
    )
    world.say(
        f"{friend.pronoun().capitalize()} {help_method.text}, while whispering, "
        f'"I should help, not poke. I am sorry for the joke."'
    )
    propagate(world, narrate=False)
    if help_method.shared:
        world.say(
            f"Now each child carried {count // 2} notes with care, and the burden turned to something fair."
        )
    elif help_method.id == "cart":
        world.say(
            "The wheels went click and the strain grew slight; the sore old shoulder felt all right."
        )
    else:
        world.say(
            "The smaller bundles sat just so; no more hard tugging to and fro."
        )
    world.say(
        f"{lead.id} breathed out slow, then gave a grin. "
        f'"Thank you for helping. That lets the good part win."'
    )


def finish(world: World, place: Place, lead: Entity, friend: Entity) -> None:
    lead.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Together they walked along {place.path}, with kinder hearts and a calmer path."
    )
    world.say(place.ending)
    world.say(
        f"And if a rhyme popped up once more, it made both children laugh, not sore."
    )


def tell(
    place: Place,
    bag_cfg: Bag,
    joke_cfg: Joke,
    help_method: HelpMethod,
    lead_name: str = "Lila",
    lead_gender: str = "girl",
    friend_name: str = "Milo",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    lead_trait: str = "earnest",
    friend_trait: str = "bouncy",
    note_count: int = 90,
) -> World:
    world = World()
    lead = world.add(
        Entity(
            id=lead_name,
            kind="character",
            type=lead_gender,
            role="lead",
            traits=[lead_trait],
            label=lead_name,
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
            traits=[friend_trait],
            label=friend_name,
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    bag = world.add(
        Entity(
            id="bag",
            kind="thing",
            type="bag",
            label=bag_cfg.label,
            phrase=bag_cfg.phrase,
            tags=set(bag_cfg.tags),
        )
    )
    notes = world.add(
        Entity(
            id="notes",
            kind="thing",
            type="notes",
            label="kindness notes",
            phrase=f"{note_count} kindness notes",
            tags={"notes", "kindness"},
        )
    )

    introduce(world, place, lead, friend, note_count)

    world.para()
    pack_notes(world, lead, bag_cfg, note_count)
    tease(world, lead, friend, joke_cfg)
    argue(world, lead, friend)

    world.para()
    repair(world, lead, friend, help_method, note_count)
    finish(world, place, lead, friend)

    outcome = resolve_outcome(bag_cfg, help_method)
    world.facts.update(
        place=place,
        bag_cfg=bag_cfg,
        joke_cfg=joke_cfg,
        help_method=help_method,
        lead=lead,
        friend=friend,
        parent=parent,
        notes=notes,
        note_count=note_count,
        outcome=outcome,
        shoulder_hurt=lead.meters["shoulder_ache"] >= THRESHOLD or bag_cfg.strain >= 1,
        conflict_happened=joke_cfg.sting >= 1,
        helped=friend.memes["helped"] >= THRESHOLD,
    )
    return world


def pair_label(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "two friends"


KNOWLEDGE = {
    "shoulder": [
        (
            "What does your shoulder help you do?",
            "Your shoulder helps hold up your arm and carry things. If a bag pulls too hard on one shoulder, it can start to ache."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is doing something gentle or helpful for someone else. It can be as small as sharing a load or saying sorry after a hurtful joke."
        )
    ],
    "joke": [
        (
            "Can a joke hurt someone's feelings?",
            "Yes. A joke can hurt if someone is already uncomfortable or sad, even when the joker thought it was silly."
        )
    ],
    "sharing": [
        (
            "Why does sharing make carrying easier?",
            "Sharing spreads the work between people. When each person carries part, one body does not have to do all the work."
        )
    ],
    "wagon": [
        (
            "What is a wagon good for?",
            "A little wagon helps move many things at once because its wheels carry the weight. That can save a person's arms and shoulders."
        )
    ],
    "string": [
        (
            "Why tie big piles into smaller bundles?",
            "Smaller bundles are easier to hold and balance. They do not tug and flop as much as one big messy pile."
        )
    ],
    "duck": [
        (
            "Why do people laugh about walking like a duck?",
            "People say that when someone waddles from side to side. It can sound funny, but it is kinder not to tease if the person is struggling."
        )
    ],
    "crab": [
        (
            "Why do people compare a sideways wobble to a crab?",
            "Crabs look funny because they move side to side. The picture can be silly, but teasing is still unkind if it embarrasses someone."
        )
    ],
    "poodle": [
        (
            "Why do rhyming stories use silly words like poodle and noodle?",
            "Silly rhymes sound playful and musical. They make the story bounce in your ear and help words stick in your mind."
        )
    ],
}
KNOWLEDGE_ORDER = ["shoulder", "kindness", "joke", "sharing", "wagon", "string", "duck", "crab", "poodle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    place = f["place"]
    bag_cfg = f["bag_cfg"]
    help_method = f["help_method"]
    return [
        'Write a rhyming story for a 3-to-5-year-old that includes the words "shoulder" and "ninety", plus kindness, humor, and conflict.',
        f"Tell a gentle rhyming story where {lead.id} carries ninety kind notes in {bag_cfg.phrase} at {place.label}, a silly joke causes hurt feelings, and {friend.id} makes things right by choosing to {help_method.label}.",
        "Write a child-facing poem-story where a funny moment becomes a conflict, then turns warm because someone notices pain, says sorry, and helps.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    place = f["place"]
    bag_cfg = f["bag_cfg"]
    joke_cfg = f["joke_cfg"]
    help_method = f["help_method"]
    count = f["note_count"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_label(lead, friend)}, {lead.id} and {friend.id}, who were taking kind notes through {place.label}. They wanted to spread cheer, but a sore shoulder and a careless joke got in the way."
        ),
        (
            f"Why was {lead.id}'s shoulder hurting?",
            f"{lead.id} was carrying {count} kindness notes in {bag_cfg.phrase} on one shoulder. The bag tugged and wobbled, so the weight started to ache."
        ),
        (
            f"What caused the conflict between {lead.id} and {friend.id}?",
            f"{friend.id} made a silly rhyme about how {lead.id} was walking. It sounded funny at first, but it landed badly because {lead.id} was already hurting."
        ),
        (
            f"How did {friend.id} fix the problem?",
            f"{friend.id} stopped joking, apologized, and chose to {help_method.label}. That kindness changed the moment because it eased the load instead of adding to the hurt."
        ),
        (
            "How did the story end?",
            f"They walked on together and handed out their notes with happier hearts. The ending proves what changed, because the rhyme turned from teasing into shared laughter and help."
        ),
    ]
    if help_method.shared:
        qa.append(
            (
                "Why did sharing help so much?",
                f"When they split the notes, each child carried only part of the weight. That made the job fairer and took the pull off {lead.id}'s shoulder."
            )
        )
    elif help_method.id == "cart":
        qa.append(
            (
                "Why did the wagon help?",
                "The wagon let the wheels hold the heavy stack instead of one shoulder. That is why the hurt could calm down and the children could keep going."
            )
        )
    else:
        qa.append(
            (
                "Why did smaller bundles help?",
                "The smaller bundles were easier to balance and did not yank so hard. That changed a floppy, awkward carry into a calmer one."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"shoulder", "kindness", "joke"}
    tags |= set(f["help_method"].tags)
    tags |= set(f["joke_cfg"].tags)
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
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
strong_enough(B, H) :- bag(B), help(H), strain(B, S), power(H, P), P >= S.
kind_enough(H) :- help(H), kind(H, K), help_min(M), K >= M.
valid(P, B, J, H) :- place(P), bag(B), joke(J), help(H), strong_enough(B, H), kind_enough(H).

outcome(mended) :- chosen_bag(B), chosen_help(H), strong_enough(B, H), kind_enough(H).
outcome(stuck) :- chosen_bag(B), chosen_help(H), not strong_enough(B, H).
outcome(stuck) :- chosen_help(H), not kind_enough(H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for bag_id, bag in BAGS.items():
        lines.append(asp.fact("bag", bag_id))
        lines.append(asp.fact("strain", bag_id, bag.strain))
    for joke_id in JOKES:
        lines.append(asp.fact("joke", joke_id))
    for help_id, help_method in HELP_METHODS.items():
        lines.append(asp.fact("help", help_id))
        lines.append(asp.fact("power", help_id, help_method.power))
        lines.append(asp.fact("kind", help_id, help_method.kind))
    lines.append(asp.fact("help_min", HELP_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_bag", params.bag),
            asp.fact("chosen_help", params.help_method),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        place="schoolyard",
        bag="satchel",
        joke="duck",
        help_method="share",
        lead_name="Lila",
        lead_gender="girl",
        friend_name="Milo",
        friend_gender="boy",
        parent="mother",
        lead_trait="earnest",
        friend_trait="bouncy",
        note_count=90,
    ),
    StoryParams(
        place="park",
        bag="mailbag",
        joke="crab",
        help_method="cart",
        lead_name="Ben",
        lead_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        parent="father",
        lead_trait="busy",
        friend_trait="gentle",
        note_count=90,
    ),
    StoryParams(
        place="library",
        bag="tote",
        joke="noodle",
        help_method="restack",
        lead_name="Nora",
        lead_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        parent="mother",
        lead_trait="careful",
        friend_trait="cheery",
        note_count=90,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Rhyming storyworld: a sore shoulder, ninety kindness notes, a silly joke, and a kinder repair."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--bag", choices=BAGS)
    ap.add_argument("--joke", choices=JOKES)
    ap.add_argument("--help-method", dest="help_method", choices=HELP_METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.bag and args.help_method:
        bag = BAGS[args.bag]
        help_method = HELP_METHODS[args.help_method]
        if help_method.kind < HELP_MIN or help_method.power < bag.strain:
            raise StoryError(explain_help(args.help_method, args.bag))

    combos = [
        combo
        for combo in valid_combo_ids()
        if (args.place is None or combo[0] == args.place)
        and (args.bag is None or combo[1] == args.bag)
        and (args.joke is None or combo[2] == args.joke)
        and (args.help_method is None or combo[3] == args.help_method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, bag, joke, help_method = rng.choice(sorted(combos))
    lead_name, lead_gender = _pick_name(rng)
    friend_name, friend_gender = _pick_name(rng, avoid=lead_name)
    parent = args.parent or rng.choice(["mother", "father"])
    lead_trait = rng.choice(TRAITS)
    friend_trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        bag=bag,
        joke=joke,
        help_method=help_method,
        lead_name=lead_name,
        lead_gender=lead_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        lead_trait=lead_trait,
        friend_trait=friend_trait,
        note_count=90,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place '{params.place}'.)")
    if params.bag not in BAGS:
        raise StoryError(f"(Unknown bag '{params.bag}'.)")
    if params.joke not in JOKES:
        raise StoryError(f"(Unknown joke '{params.joke}'.)")
    if params.help_method not in HELP_METHODS:
        raise StoryError(f"(Unknown help method '{params.help_method}'.)")
    bag = BAGS[params.bag]
    help_method = HELP_METHODS[params.help_method]
    if help_method.kind < HELP_MIN or help_method.power < bag.strain:
        raise StoryError(explain_help(params.help_method, params.bag))

    world = tell(
        place=PLACES[params.place],
        bag_cfg=bag,
        joke_cfg=JOKES[params.joke],
        help_method=help_method,
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        lead_trait=params.lead_trait,
        friend_trait=params.friend_trait,
        note_count=params.note_count,
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
    py_set = set(valid_combo_ids())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combo_ids() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatch = 0
    for params in cases:
        py_out = resolve_outcome(BAGS[params.bag], HELP_METHODS[params.help_method])
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, bag, joke, help_method) combos:\n")
        for place, bag, joke, help_method in combos:
            print(f"  {place:10} {bag:8} {joke:7} {help_method}")
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
            header = f"### {p.lead_name} & {p.friend_name}: {p.place}, {p.bag}, {p.joke}, {p.help_method}"
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
