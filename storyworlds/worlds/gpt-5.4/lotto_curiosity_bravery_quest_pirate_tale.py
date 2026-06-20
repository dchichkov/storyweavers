#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lotto_curiosity_bravery_quest_pirate_tale.py
========================================================================

A standalone story world for a small pirate-flavored tale built around one
unusual object: a lost lotto ticket. Two children at a seaside fair are playing
pirates when they find the ticket, notice a clue about its owner, and choose a
brave little quest to return it safely.

The world model enforces two pieces of common sense:

* A clue must actually match the owner it is supposed to identify.
* The chosen helper must genuinely make the obstacle safe enough to cross.

That means the story never asks children to solve the wrong problem with the
wrong tool. The point is not "finding treasure" but learning that curiosity can
turn into care, and bravery can mean returning something important.

Run it
------
    python storyworlds/worlds/gpt-5.4/lotto_curiosity_bravery_quest_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/lotto_curiosity_bravery_quest_pirate_tale.py --place pier --challenge dog --helper biscuit_tin
    python storyworlds/worlds/gpt-5.4/lotto_curiosity_bravery_quest_pirate_tale.py --challenge gangplank --helper biscuit_tin
    python storyworlds/worlds/gpt-5.4/lotto_curiosity_bravery_quest_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/lotto_curiosity_bravery_quest_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/lotto_curiosity_bravery_quest_pirate_tale.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
    intro: str
    play: str
    route: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Owner:
    id: str
    label: str
    role_word: str
    stall: str
    worry_line: str
    thanks: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    mark: str
    sentence: str
    owner: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    label: str
    scene: str
    fear_line: str
    safe_with: str
    need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    works_for: set[str]
    action: str
    qa_action: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World and rules
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
        return [e for e in self.entities.values() if e.role in {"seeker", "mate"}]

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


def _r_search_worry(world: World) -> list[str]:
    out: list[str] = []
    ticket = world.get("ticket")
    owner = world.get("owner")
    if ticket.meters["lost"] >= THRESHOLD and owner.meters["searching"] >= THRESHOLD:
        sig = ("search_worry", owner.id)
        if sig not in world.fired:
            world.fired.add(sig)
            owner.memes["worry"] += 1
            for kid in world.kids():
                kid.memes["concern"] += 1
            out.append("__worry__")
    return out


def _r_safe_crossing(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("challenge_safe"):
        sig = ("safe_cross",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.kids():
                kid.memes["bravery"] += 1
            out.append("__safe__")
    return out


def _r_return_relief(world: World) -> list[str]:
    out: list[str] = []
    ticket = world.get("ticket")
    owner = world.get("owner")
    if ticket.meters["returned"] >= THRESHOLD:
        sig = ("returned", owner.id)
        if sig not in world.fired:
            world.fired.add(sig)
            owner.memes["relief"] += 1
            owner.meters["searching"] = 0.0
            for kid in world.kids():
                kid.memes["pride"] += 1
                kid.memes["concern"] = 0.0
            out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("search_worry", "social", _r_search_worry),
    Rule("safe_crossing", "quest", _r_safe_crossing),
    Rule("return_relief", "social", _r_return_relief),
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


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def clue_matches_owner(clue: Clue, owner: Owner) -> bool:
    return clue.owner == owner.id


def helper_supports(challenge: Challenge, helper: Helper) -> bool:
    return challenge.need in helper.works_for


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in PLACES:
        for clue_id, clue in CLUES.items():
            for owner_id, owner in OWNERS.items():
                if not clue_matches_owner(clue, owner):
                    continue
                for challenge_id, challenge in CHALLENGES.items():
                    for helper_id, helper in HELPERS.items():
                        if helper_supports(challenge, helper):
                            combos.append((place_id, owner_id, clue_id, challenge_id, helper_id))
    return combos


def explain_clue_mismatch(clue: Clue, owner: Owner) -> str:
    return (
        f"(No story: {clue.sentence} points to {OWNERS[clue.owner].label}, "
        f"not {owner.label}. The clue has to identify the real owner.)"
    )


def explain_helper_mismatch(challenge: Challenge, helper: Helper) -> str:
    good = ", ".join(sorted(h.id for h in HELPERS.values() if helper_supports(challenge, h)))
    return (
        f"(No story: {helper.label} does not make '{challenge.label}' safely passable. "
        f"Try one of: {good}.)"
    )


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def play_setup(world: World, seeker: Entity, mate: Entity, place: Place) -> None:
    seeker.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a bright afternoon by {place.label}, {seeker.id} and {mate.id} turned "
        f"the day into a pirate game. {place.intro}"
    )
    world.say(
        f"{place.play} {seeker.id} called {mate.id} the first mate, lifted a driftwood "
        f"stick like a captain's pointer, and whispered that every real pirate watched for clues."
    )


def find_ticket(world: World, seeker: Entity, mate: Entity) -> None:
    ticket = world.get("ticket")
    ticket.meters["found"] += 1
    seeker.memes["curiosity"] += 1
    mate.memes["curiosity"] += 1
    world.say(
        f"Then something fluttered against a rope post and caught {seeker.id}'s eye. "
        f"It was a little lotto ticket, bent at one corner and dancing in the sea breeze."
    )
    world.say(
        f'"A treasure slip!" {seeker.id} said. But {mate.id} crouched beside {seeker.pronoun("object")} '
        f"and looked closer instead of grabbing it."
    )


def inspect_clue(world: World, seeker: Entity, mate: Entity, clue: Clue) -> None:
    seeker.memes["curiosity"] += 1
    mate.memes["curiosity"] += 1
    world.say(
        f"On the back was {clue.mark}. {clue.sentence} "
        f"That made the ticket feel less like treasure and more like somebody's missing thing."
    )


def hear_owner(world: World, owner_cfg: Owner) -> None:
    ticket = world.get("ticket")
    owner = world.get("owner")
    ticket.meters["lost"] += 1
    owner.meters["searching"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just then, from {owner_cfg.stall}, a worried voice floated over the boards: "
        f'{owner_cfg.worry_line}'
    )


def choose_quest(world: World, seeker: Entity, mate: Entity, owner_cfg: Owner) -> None:
    seeker.memes["care"] += 1
    mate.memes["care"] += 1
    world.say(
        f'{mate.id} touched the ticket with one finger. "It belongs to {owner_cfg.label}," '
        f'{mate.pronoun()} said. "{owner_cfg.role_word.capitalize()} sounds sad."'
    )
    world.say(
        f"{seeker.id} swallowed, felt curious and nervous all at once, and then nodded. "
        f'"Then our pirate quest is not to keep it," {seeker.pronoun()} said. "It is to bring it back."'
    )


def face_challenge(world: World, seeker: Entity, mate: Entity, challenge: Challenge) -> None:
    for kid in (seeker, mate):
        kid.memes["fear"] += 1
    world.say(challenge.scene)
    world.say(challenge.fear_line)


def use_helper(world: World, seeker: Entity, mate: Entity, challenge: Challenge, helper: Helper) -> None:
    world.facts["challenge_safe"] = True
    propagate(world, narrate=False)
    for kid in (seeker, mate):
        kid.memes["fear"] = 0.0
    world.say(
        f"But {mate.id} remembered {helper.phrase}. Together they {helper.action}."
    )
    world.say(
        f"The scary part did not vanish, but it became manageable, and that is when "
        f"{seeker.id} felt brave enough to keep going."
    )


def return_ticket(world: World, seeker: Entity, owner_cfg: Owner) -> None:
    ticket = world.get("ticket")
    owner = world.get("owner")
    ticket.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last {seeker.id} held out the lotto ticket to {owner_cfg.label}. "
        f'"We found this on our quest," {seeker.pronoun()} said.'
    )
    world.say(owner_cfg.thanks)


def ending(world: World, seeker: Entity, mate: Entity, owner_cfg: Owner, place: Place) -> None:
    ticket = world.get("ticket")
    ticket.attrs["kept_by_kids"] = False
    for kid in (seeker, mate):
        kid.memes["joy"] += 1
        kid.memes["wonder"] += 1
    world.say(
        f"{owner_cfg.label} tucked the ticket safely into {owner_cfg.pronoun('possessive')} pocket "
        f"and gave them each a shiny chocolate coin wrapped in gold paper."
    )
    world.say(
        f'Soon the harbor bell rang for the evening drawing, but {seeker.id} and {mate.id} did not wait to learn '
        f"whether the lotto ticket won. They were already racing back along {place.route}, "
        f"calling themselves the kind of pirates who returned what they found."
    )
    world.say(
        f"The sea flashed silver beside them, and their quest felt bigger than treasure."
    )


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    owner_cfg: Owner,
    clue: Clue,
    challenge: Challenge,
    helper: Helper,
    seeker_name: str = "Tom",
    seeker_gender: str = "boy",
    mate_name: str = "Lily",
    mate_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World()
    seeker = world.add(Entity(id=seeker_name, kind="character", type=seeker_gender, role="seeker"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    owner = world.add(Entity(id="owner", kind="character", type="woman", role="owner", label=owner_cfg.label))
    ticket = world.add(Entity(id="ticket", type="ticket", label="lotto ticket"))

    world.facts["challenge_safe"] = False

    play_setup(world, seeker, mate, place)
    find_ticket(world, seeker, mate)
    inspect_clue(world, seeker, mate, clue)

    world.para()
    hear_owner(world, owner_cfg)
    choose_quest(world, seeker, mate, owner_cfg)
    face_challenge(world, seeker, mate, challenge)
    use_helper(world, seeker, mate, challenge, helper)

    world.para()
    return_ticket(world, seeker, owner_cfg)
    ending(world, seeker, mate, owner_cfg, place)

    world.facts.update(
        place=place,
        owner_cfg=owner_cfg,
        clue=clue,
        challenge=challenge,
        helper=helper,
        seeker=seeker,
        mate=mate,
        owner=owner,
        ticket=ticket,
        returned=ticket.meters["returned"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "pier": Place(
        "pier",
        "the old pier",
        "The striped awnings snapped overhead, gulls cried, and the wooden planks thumped under small running feet.",
        "A coil of rope became their anchor, and the long railing became the side of a grand ship.",
        "the pier boards",
        tags={"pier", "harbor"},
    ),
    "boardwalk": Place(
        "boardwalk",
        "the boardwalk by the harbor fair",
        "Bright booths shone in a row, and the smell of warm pretzels floated through the salt air.",
        "The benches became their ship's deck, and every fluttering flag looked like a pirate signal.",
        "the boardwalk",
        tags={"boardwalk", "harbor"},
    ),
    "fish_market": Place(
        "fish_market",
        "the market docks",
        "Nets hung to dry, boats knocked softly together, and little puddles of sunlight shivered on the water.",
        "An empty crate became a treasure chest, and the stacked baskets became islands on a map.",
        "the dockside path",
        tags={"dock", "harbor"},
    ),
}

OWNERS = {
    "shell_auntie": Owner(
        "shell_auntie",
        "the shell seller",
        "the shell seller",
        "the shell booth with strings of pink shells",
        '"My harbor lotto ticket was here a minute ago. I promised myself I would not lose it before the drawing!"',
        '"Oh, my dears, you found it! I was searching everywhere. Thank you for bringing it back instead of pocketing it."',
        tags={"shells", "lotto"},
    ),
    "lemonade_dad": Owner(
        "lemonade_dad",
        "the lemonade man",
        "the lemonade man",
        "the lemonade cart with a blue striped roof",
        '"My lotto ticket is gone, and tonight is the town drawing. I must have dropped it while pouring drinks!"',
        '"There it is! I was heartsick over that little slip of paper. You two were honest and very brave."',
        tags={"lemonade", "lotto"},
    ),
    "kite_grandma": Owner(
        "kite_grandma",
        "the kite grandma",
        "the kite grandma",
        "the kite stand full of ribbons and tails",
        '"My little lotto ticket has blown off somewhere. I tucked it beside my strings, and now I cannot see it at all!"',
        '"Bless my buttons, that is my ticket. Thank you, pirates. Curiosity led you to it, but kindness brought it home."',
        tags={"kites", "lotto"},
    ),
}

CLUES = {
    "pink_shell_stamp": Clue(
        "pink_shell_stamp",
        "a tiny pink shell stamp and a sprinkle of glitter",
        "That looked just like the cards hanging at the shell booth.",
        "shell_auntie",
        tags={"shells"},
    ),
    "blue_lemon_spot": Clue(
        "blue_lemon_spot",
        "a pale yellow lemon spot and one blue sugar crystal",
        "It looked as if it had rested on the lemonade cart.",
        "lemonade_dad",
        tags={"lemonade"},
    ),
    "ribbon_knot": Clue(
        "ribbon_knot",
        "a short rainbow ribbon knot tied through the corner",
        "Only the kite stand used ribbon knots like that.",
        "kite_grandma",
        tags={"kites"},
    ),
}

CHALLENGES = {
    "gangplank": Challenge(
        "gangplank",
        "the wobbly gangplank",
        "Between them and the stall lay a wobbly gangplank over a narrow strip of water, rocking every time someone stepped on it.",
        f'"The boards are shaking," whispered one child. "It looks like a jumpy bridge for real pirates."',
        "steady_hand",
        "balance",
        tags={"gangplank", "bridge"},
    ),
    "dog": Challenge(
        "dog",
        "the barking dog",
        "A small dock dog was tied beside a barrel, barking at every swishing ribbon and every quick footstep.",
        f'"He is loud," murmured one child, taking a half-step back.',
        "calm_animal",
        "animal",
        tags={"dog"},
    ),
    "crowd": Challenge(
        "crowd",
        "the busy crowd",
        "A thick crowd pressed around the drawing board, all elbows and baskets and rustling coats.",
        f'"If we run in there, we'll lose each other," said one child.',
        "stay_together",
        "crowd",
        tags={"crowd"},
    ),
}

HELPERS = {
    "grownup_hand": Helper(
        "grownup_hand",
        "a grown-up hand",
        "the harbor master's steady hand nearby",
        {"balance"},
        "asked the harbor master to walk beside them while they crossed, one careful step after another",
        "a harbor master walked beside them and kept them steady on the gangplank",
        tags={"adult_help", "gangplank"},
    ),
    "biscuit_tin": Helper(
        "biscuit_tin",
        "a biscuit tin",
        "the little biscuit tin on the barrel top",
        {"animal"},
        "shook the tin softly and let the dock dog sniff a biscuit before they passed",
        "they calmed the dog with a biscuit so it stopped barking at them",
        tags={"dog"},
    ),
    "red_scarf": Helper(
        "red_scarf",
        "a bright red scarf",
        "the bright red scarf tied around the first mate's neck",
        {"crowd"},
        "held tight to the red scarf between them, so they moved through the crowd like one small ship",
        "they held onto a bright scarf so they could stay together in the crowd",
        tags={"crowd"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]

PARENT_TYPES = ["mother", "father"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    owner: str
    clue: str
    challenge: str
    helper: str
    seeker: str
    seeker_gender: str
    mate: str
    mate_gender: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "lotto": [
        (
            "What is a lotto ticket?",
            "A lotto ticket is a small paper slip used for a drawing or number game. Even though it looks tiny, it can be important to the person who owns it.",
        )
    ],
    "pier": [
        (
            "What is a pier?",
            "A pier is a long walkway built out over the water. Boats can stop beside it, and people can walk along it.",
        )
    ],
    "gangplank": [
        (
            "What is a gangplank?",
            "A gangplank is a narrow board or bridge people use to go from land to a boat or dock. You have to cross it carefully so you do not wobble or slip.",
        )
    ],
    "dog": [
        (
            "Why might a dog bark at people walking by?",
            "Dogs bark when they feel excited, surprised, or protective. A calm voice and slow movements can help them settle down.",
        )
    ],
    "crowd": [
        (
            "How can children stay safe in a big crowd?",
            "They can stay close together, hold on to each other or a grown-up, and move slowly. That way nobody gets lost.",
        )
    ],
    "adult_help": [
        (
            "Why is it smart to ask a grown-up for help on something tricky?",
            "A grown-up can make a hard thing safer and calmer. Asking for help is a brave choice, not a weak one.",
        )
    ],
    "honesty": [
        (
            "What should you do if you find something that belongs to someone else?",
            "You should try to return it to the owner or tell a grown-up. Keeping it would not be honest.",
        )
    ],
}
KNOWLEDGE_ORDER = ["lotto", "pier", "gangplank", "dog", "crowd", "adult_help", "honesty"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    mate = f["mate"]
    challenge = f["challenge"]
    owner_cfg = f["owner_cfg"]
    return [
        'Write a short pirate-flavored story for a 3-to-5-year-old that includes the word "lotto" and turns curiosity into kindness.',
        f"Tell a gentle quest story where {seeker.id} and {mate.id} find a lost lotto ticket near the harbor and bravely return it to {owner_cfg.label}.",
        f"Write a child-facing tale with curiosity, bravery, and a small quest: two pretend pirates notice a clue, face {challenge.label}, and choose honesty over treasure.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    return "a boy and a girl"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    mate = f["mate"]
    place = f["place"]
    owner_cfg = f["owner_cfg"]
    clue = f["clue"]
    challenge = f["challenge"]
    helper = f["helper"]
    pair = pair_noun(seeker, mate)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {seeker.id} and {mate.id}, who were playing pirates by {place.label}. Their game turns into a real little quest when they find the lost ticket.",
        ),
        (
            "What did the children find?",
            "They found a lost lotto ticket fluttering near the water. At first it looked like treasure, but then they studied it more carefully.",
        ),
        (
            "How did curiosity help them?",
            f"Curiosity made them look closely at the ticket instead of stuffing it into a pocket. Because they noticed {clue.mark}, they could guess who the owner was.",
        ),
        (
            f"Why did they decide to return the lotto ticket to {owner_cfg.label}?",
            f"They heard {owner_cfg.label} worrying from {owner_cfg.stall}, so they knew the ticket mattered to someone real. That changed the game from a hunt for treasure into a quest to help.",
        ),
        (
            "What brave thing did they do on the quest?",
            f"They faced {challenge.label} instead of giving up. They used {helper.label} so the hard part became safe enough to cross.",
        ),
        (
            "How did they get past the obstacle safely?",
            f"They used {helper.qa_action}. The helper matched the problem, so bravery worked together with good sense.",
        ),
        (
            "How did the story end?",
            f"They returned the lotto ticket, and {owner_cfg.label} felt relieved and grateful. The children ran off feeling proud because they had been honest pirates, not grabby ones.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"lotto", "honesty"} | set(f["place"].tags) | set(f["challenge"].tags) | set(f["helper"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
matches(C, O) :- clue_owner(C, O).
supports(H, Ch) :- helper(H), challenge(Ch), needs(Ch, N), works_for(H, N).

valid(P, O, C, Ch, H) :- place(P), owner(O), clue(C), challenge(Ch), helper(H),
                         matches(C, O), supports(H, Ch).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid in OWNERS:
        lines.append(asp.fact("owner", oid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_owner", cid, clue.owner))
    for chid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", chid))
        lines.append(asp.fact("needs", chid, ch.need))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for need in sorted(helper.works_for):
            lines.append(asp.fact("works_for", hid, need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test failed: generated empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("pier", "shell_auntie", "pink_shell_stamp", "gangplank", "grownup_hand", "Tom", "boy", "Lily", "girl", "mother"),
    StoryParams("boardwalk", "lemonade_dad", "blue_lemon_spot", "crowd", "red_scarf", "Max", "boy", "Mia", "girl", "father"),
    StoryParams("fish_market", "kite_grandma", "ribbon_knot", "dog", "biscuit_tin", "Sam", "boy", "Zoe", "girl", "mother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate play, curiosity, bravery, and a lost lotto ticket."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--owner", choices=OWNERS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.owner:
        clue = CLUES[args.clue]
        owner = OWNERS[args.owner]
        if not clue_matches_owner(clue, owner):
            raise StoryError(explain_clue_mismatch(clue, owner))
    if args.challenge and args.helper:
        challenge = CHALLENGES[args.challenge]
        helper = HELPERS[args.helper]
        if not helper_supports(challenge, helper):
            raise StoryError(explain_helper_mismatch(challenge, helper))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.owner is None or c[1] == args.owner)
        and (args.clue is None or c[2] == args.clue)
        and (args.challenge is None or c[3] == args.challenge)
        and (args.helper is None or c[4] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, owner, clue, challenge, helper = rng.choice(sorted(combos))
    seeker, sg = _pick_kid(rng)
    mate, mg = _pick_kid(rng, avoid=seeker)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(place, owner, clue, challenge, helper, seeker, sg, mate, mg, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        OWNERS[params.owner],
        CLUES[params.clue],
        CHALLENGES[params.challenge],
        HELPERS[params.helper],
        params.seeker,
        params.seeker_gender,
        params.mate,
        params.mate_gender,
        params.parent,
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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, owner, clue, challenge, helper) combos:\n")
        for place, owner, clue, challenge, helper in combos:
            print(f"  {place:11} {owner:13} {clue:17} {challenge:10} {helper}")
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
                f"### {p.seeker} & {p.mate}: {p.owner} / {p.clue} / "
                f"{p.challenge} with {p.helper}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
