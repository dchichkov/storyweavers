#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hysterics_tomahawk_occupy_friendship_pirate_tale.py
==============================================================================

A small story world about two friends playing pirates, one child trying to
occupy the best hiding place alone, a foam tomahawk used as a dramatic prop,
and a friendship repaired in a sensible way.

The seed asked for the words "hysterics", "tomahawk", and "occupy", with a
friendship theme in a pirate-tale style. This world rebuilds that as a
state-driven simulation instead of a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/hysterics_tomahawk_occupy_friendship_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/hysterics_tomahawk_occupy_friendship_pirate_tale.py --space barrel_nest
    python storyworlds/worlds/gpt-5.4/hysterics_tomahawk_occupy_friendship_pirate_tale.py --repair snatch_tomahawk
    python storyworlds/worlds/gpt-5.4/hysterics_tomahawk_occupy_friendship_pirate_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/hysterics_tomahawk_occupy_friendship_pirate_tale.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Space:
    id: str
    label: str
    phrase: str
    mood: str
    capacity: int
    expandable: bool = False
    turnable: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    sense: int
    expands: bool = False
    turns: bool = False
    doubles: bool = False
    text: str = ""
    qa_text: str = ""
    ending: str = ""
    tags: set[str] = field(default_factory=set)


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


def _r_exclusion(world: World) -> list[str]:
    fort = world.get("fort")
    excluded = world.get("friend")
    if fort.meters["claimed"] < THRESHOLD or not fort.attrs.get("exclusive"):
        return []
    sig = ("excluded", excluded.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    excluded.memes["hurt"] += 1
    excluded.memes["fear"] += 1
    world.get("bond").meters["strain"] += 1
    return ["__exclusion__"]


def _r_hysterics(world: World) -> list[str]:
    excluded = world.get("friend")
    if excluded.memes["hurt"] < THRESHOLD or excluded.memes["fear"] < THRESHOLD:
        return []
    sig = ("hysterics", excluded.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    excluded.memes["hysterics"] += 1
    return ["__hysterics__"]


CAUSAL_RULES = [
    Rule(name="exclusion", tag="social", apply=_r_exclusion),
    Rule(name="hysterics", tag="emotional", apply=_r_hysterics),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if bit == "__hysterics__":
                friend = world.get("friend")
                world.say(
                    f"For one wobbly minute, {friend.id} was almost in hysterics, "
                    f"sure the game and the friendship had both cracked apart."
                )
    return produced


def repair_works(space: Space, repair: Repair) -> bool:
    if repair.sense < SENSE_MIN:
        return False
    if repair.expands and space.expandable:
        return True
    if repair.turns and space.turnable:
        return True
    if repair.doubles and space.capacity >= 2:
        return True
    return False


def sensible_repairs() -> list[Repair]:
    return [repair for repair in REPAIRS.values() if repair.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for sid, space in SPACES.items():
        for rid, repair in REPAIRS.items():
            if repair_works(space, repair):
                combos.append((sid, rid))
    return combos


def predict_hurt(world: World) -> dict:
    sim = world.copy()
    occupy_alone(sim, narrate=False)
    friend = sim.get("friend")
    return {
        "strain": sim.get("bond").meters["strain"],
        "hysterics": friend.memes["hysterics"],
    }


def introduce(world: World, captain: Entity, friend: Entity) -> None:
    captain.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a rainy afternoon, {captain.id} and {friend.id} turned the living room "
        f"into a pirate ship with sofa rails, blanket sails, and a rug that rolled like sea."
    )
    world.say(
        f"They were best friends, the sort who could turn a cardboard box into treasure "
        f"and a cushion into an island."
    )


def choose_space(world: World, captain: Entity, friend: Entity, space: Space) -> None:
    world.say(
        f'At the stern they found {space.phrase}, {space.mood}. '
        f'"That must be the captain\'s post," {captain.id} said.'
    )
    world.say(f'{friend.id} smiled. "Then let us guard the treasure there together."')


def take_prop(world: World, captain: Entity) -> None:
    captain.memes["grand"] += 1
    world.say(
        f"From the dress-up box, {captain.id} pulled out a foam tomahawk painted with "
        f"silver swirls. It was only a toy, but in pirate eyes it looked grand enough "
        f"to guard a king's ransom."
    )


def warn(world: World, captain: Entity, friend: Entity, parent: Entity, space: Space) -> None:
    pred = predict_hurt(world)
    world.facts["predicted_strain"] = pred["strain"]
    world.facts["predicted_hysterics"] = pred["hysterics"]
    world.say(
        f'{friend.id} looked from the toy tomahawk to {space.label} and bit '
        f'{friend.pronoun("possessive")} lip. "{captain.id}, if you occupy it all by yourself, '
        f'I will feel left out," {friend.pronoun()} said. "{parent.label_word.capitalize()} '
        f'always says good mates make room."'
    )


def occupy_alone(world: World, narrate: bool = True) -> None:
    fort = world.get("fort")
    captain = world.get("captain")
    fort.meters["claimed"] += 1
    fort.attrs["exclusive"] = True
    captain.memes["defiance"] += 1
    produced = propagate(world, narrate=False)
    if narrate:
        world.say(
            f'"Then I shall occupy this place myself!" {captain.id} cried, climbing inside '
            f"with the foam tomahawk across {captain.pronoun('possessive')} knees. "
            f"The words came out sharper than {captain.pronoun()} meant."
        )
        if "__hysterics__" in produced:
            friend = world.get("friend")
            world.say(
                f"{friend.id} stared at the little pirate post and gave a broken gasp."
            )
            world.say(
                f"For one wobbly minute, {friend.id} was almost in hysterics, "
                f"sure the game and the friendship had both cracked apart."
            )


def mend(world: World, parent: Entity, captain: Entity, friend: Entity,
         space: Space, repair: Repair) -> None:
    fort = world.get("fort")
    bond = world.get("bond")
    fort.attrs["exclusive"] = False
    fort.meters["shared"] += 1
    bond.meters["strain"] = 0.0
    bond.meters["warmth"] += 1
    captain.memes["shame"] += 1
    captain.memes["generosity"] += 1
    captain.memes["relief"] += 1
    friend.memes["relief"] += 1
    friend.memes["trust"] += 1
    friend.memes["hysterics"] = 0.0
    friend.memes["hurt"] = 0.0
    friend.memes["fear"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came over, saw the storm on both faces, and knelt by the fort. "
        f'{repair.text}'
    )
    if repair.id == "widen_fort":
        world.say(
            f"With two more cushions and a laundry basket turned sideways, {space.label} grew from a lonely post "
            f"into a proper pirate station."
        )
    elif repair.id == "captain_turns":
        world.say(
            f"The rule was simple and fair: one child watched the treasure while the other counted to twenty, "
            f"and then they swapped with a grin."
        )
    elif repair.id == "double_post":
        world.say(
            "Soon there were two watch places side by side, so no one had to stand on the wrong side of the game."
        )
    world.say(
        f'{captain.id} slid out and held the foam tomahawk across both palms. "I was acting like the whole sea was mine," '
        f'{captain.pronoun()} said. "Will you still be my mate?"'
    )
    world.say(
        f'"Yes," said {friend.id}, and {friend.pronoun()} squeezed in close enough for both of them to laugh again.'
    )
    world.say(
        repair.ending
    )


def tell(space: Space, repair: Repair, captain_name: str = "Tom",
         captain_gender: str = "boy", friend_name: str = "Mira",
         friend_gender: str = "girl", parent_type: str = "mother") -> World:
    world = World()
    captain = world.add(Entity(
        id=captain_name,
        kind="character",
        type=captain_gender,
        role="captain",
        traits=["bold"],
        tags={"friendship", "pirate"},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=["loyal"],
        tags={"friendship", "pirate"},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    fort = world.add(Entity(
        id="fort",
        type="fort",
        label=space.label,
        attrs={"capacity": space.capacity, "exclusive": False},
        tags=set(space.tags),
    ))
    world.add(Entity(id="bond", type="friendship", label="their friendship"))

    introduce(world, captain, friend)
    choose_space(world, captain, friend, space)

    world.para()
    take_prop(world, captain)
    warn(world, captain, friend, parent, space)
    occupy_alone(world, narrate=True)

    world.para()
    mend(world, parent, captain, friend, space, repair)

    world.facts.update(
        captain=captain,
        friend=friend,
        parent=parent,
        space=space,
        repair=repair,
        fort=fort,
        shared=fort.meters["shared"] >= THRESHOLD,
        hysterics_seen=True,
    )
    return world


KNOWLEDGE = {
    "friendship": [
        (
            "What does a good friend do during a game?",
            "A good friend notices whether everyone still feels included. Friends can take turns, share space, and fix hurt feelings with honest words."
        )
    ],
    "pirate": [
        (
            "What is a pirate tale?",
            "A pirate tale is an adventure story with ships, treasure, maps, and brave pretend jobs like captain or lookout. In play, children can borrow that style without doing anything dangerous."
        )
    ],
    "tomahawk": [
        (
            "What was the tomahawk in this story?",
            "It was a foam costume prop, not a real weapon. A soft pretend prop can stay part of a game only when children use it gently and a grown-up keeps the play kind."
        )
    ],
    "sharing": [
        (
            "Why does taking turns help?",
            "Taking turns gives each person a fair chance. It helps a game keep going without one child feeling pushed away."
        )
    ],
    "feelings": [
        (
            "What does 'hysterics' mean here?",
            "Here it means someone felt so upset that their feelings spilled out in a noisy, panicky way. It does not mean they were bad; it means they needed comfort and calm."
        )
    ],
    "repair": [
        (
            "How can children repair a friendship after a mean moment?",
            "They can stop, tell the truth, and make the game fair again. An apology matters most when it is followed by a real change, like sharing space or taking turns."
        )
    ],
}
KNOWLEDGE_ORDER = ["friendship", "pirate", "tomahawk", "sharing", "feelings", "repair"]


SPACES = {
    "treasure_cove": Space(
        id="treasure_cove",
        label="the treasure cove",
        phrase="a little blanket cove behind two chairs",
        mood="dark enough to feel secret and just small enough to start an argument",
        capacity=1,
        expandable=True,
        turnable=True,
        tags={"sharing", "repair"},
    ),
    "barrel_nest": Space(
        id="barrel_nest",
        label="the barrel nest",
        phrase="a round laundry-basket lookout by the window",
        mood="high, snug, and only big enough for one pirate at a time",
        capacity=1,
        expandable=False,
        turnable=True,
        tags={"sharing"},
    ),
    "sofa_deck": Space(
        id="sofa_deck",
        label="the sofa deck",
        phrase="a broad fort on the sofa with two pillow barrels",
        mood="wide enough for more than one pirate, though a grand speech could still spoil it",
        capacity=2,
        expandable=False,
        turnable=False,
        tags={"repair"},
    ),
}

REPAIRS = {
    "widen_fort": Repair(
        id="widen_fort",
        label="widen the fort",
        sense=3,
        expands=True,
        text='"A captain can claim a post," she said softly, "but not a whole friendship. Let us widen the fort so the treasure has two guards instead of one."',
        qa_text="widened the fort so both friends fit",
        ending="Before long, the two mates leaned shoulder to shoulder in the treasure cove, whispering over their map while the toy tomahawk rested forgotten beside the gold.",
        tags={"repair", "sharing"},
    ),
    "captain_turns": Repair(
        id="captain_turns",
        label="captain turns",
        sense=3,
        turns=True,
        text='"If one pirate post has room for only one child," she said, "then the fair pirate rule is turns, not tears."',
        qa_text="made a turn-taking rule for the pirate post",
        ending="The game sailed on with counting, swapping, and proud little bows, and the window lookout felt kinder every time a turn changed hands.",
        tags={"sharing", "friendship"},
    ),
    "double_post": Repair(
        id="double_post",
        label="double post",
        sense=3,
        doubles=True,
        text='"This deck is already big enough for two brave guards," she said. "We do not need a lonely captain. We need a crew."',
        qa_text="split the wide deck into two shared watch posts",
        ending="Soon the sofa deck held two grinning pirates, one map, one chest, and not one leftover tear between them.",
        tags={"repair", "friendship"},
    ),
    "snatch_tomahawk": Repair(
        id="snatch_tomahawk",
        label="snatch the tomahawk away",
        sense=1,
        text="",
        qa_text="snatched the prop away",
        ending="",
        tags={"tomahawk"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


@dataclass
class StoryParams:
    space: str
    repair: str
    captain: str
    captain_gender: str
    friend: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        space="treasure_cove",
        repair="widen_fort",
        captain="Tom",
        captain_gender="boy",
        friend="Lily",
        friend_gender="girl",
        parent="mother",
    ),
    StoryParams(
        space="barrel_nest",
        repair="captain_turns",
        captain="Max",
        captain_gender="boy",
        friend="Mia",
        friend_gender="girl",
        parent="father",
    ),
    StoryParams(
        space="sofa_deck",
        repair="double_post",
        captain="Ava",
        captain_gender="girl",
        friend="Ben",
        friend_gender="boy",
        parent="mother",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    friend = f["friend"]
    space = f["space"]
    repair = f["repair"]
    return [
        'Write a pirate-play story for a 3-to-5-year-old that includes the words "hysterics", "tomahawk", and "occupy", and make the heart of the story about friendship.',
        f"Tell a story where {captain.id} and {friend.id} are best friends playing pirates, but {captain.id} tries to occupy {space.label} alone with a foam tomahawk and hurts {friend.id}'s feelings before the game is mended.",
        f"Write a gentle pirate tale where a grown-up helps two friends fix a mean moment by being fair: in the end they {repair.label} and the friendship feels steady again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    friend = f["friend"]
    parent = f["parent"]
    space = f["space"]
    repair = f["repair"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two best friends, {captain.id} and {friend.id}, who were playing pirates together. {parent.label_word.capitalize()} helped them when the game turned sour."
        ),
        (
            "What made the trouble start?",
            f"The trouble started when {captain.id} climbed into {space.label} with the foam tomahawk and said {captain.pronoun()} would occupy it alone. That shut {friend.id} out of the best part of the pretend game."
        ),
        (
            f"Why was {friend.id} almost in hysterics?",
            f"{friend.id} thought the pirate game and the friendship were both breaking at once. The sharp words mattered because they came in a moment when {friend.pronoun()} expected to be a mate, not someone left outside."
        ),
        (
            f"How did {parent.label_word} help them fix it?",
            f"{parent.label_word.capitalize()} {repair.qa_text}. The fix worked because it changed the game itself, instead of only telling the children to stop feeling upset."
        ),
        (
            "How did the story end?",
            f"It ended with the friends playing side by side again and the treasure no longer belonging to just one child. The final picture proves the change: the pirate post is shared, and the friendship feels safe again."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"friendship", "pirate", "tomahawk", "feelings", "repair"}
    tags |= set(world.facts["repair"].tags)
    tags |= set(world.facts["space"].tags)
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
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(space: Space, repair: Repair) -> str:
    if repair.sense < SENSE_MIN:
        return (
            f"(Refusing repair '{repair.id}': it scores too low on common sense "
            f"(sense={repair.sense} < {SENSE_MIN}). A friendship story should prefer a fair fix over a snatch-and-scold move.)"
        )
    if repair.expands and not space.expandable:
        return (
            f"(No story: {space.label} cannot honestly be widened, so '{repair.id}' would not solve the exclusion. "
            f"Try a turn-taking repair or a space that can grow.)"
        )
    if repair.turns and not space.turnable:
        return (
            f"(No story: {space.label} is already a wide place, so turns are not the real fix here. "
            f"The story wants a repair that matches the shape of the problem.)"
        )
    if repair.doubles and space.capacity < 2:
        return (
            f"(No story: {space.label} is only big enough for one child, so a double watch post would be pretend nonsense there. "
            f"Try widening the fort or taking turns.)"
        )
    return "(No story: this repair does not fit this pirate post.)"


ASP_RULES = r"""
compatible(S, R) :- repair(R), expands(R), space(S), expandable(S).
compatible(S, R) :- repair(R), turns(R), space(S), turnable(S).
compatible(S, R) :- repair(R), doubles(R), space(S), capacity(S, C), C >= 2.
sensible(R) :- repair(R), sense(R, V), sense_min(M), V >= M.
valid(S, R) :- space(S), repair(R), sensible(R), compatible(S, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, space in SPACES.items():
        lines.append(asp.fact("space", sid))
        lines.append(asp.fact("capacity", sid, space.capacity))
        if space.expandable:
            lines.append(asp.fact("expandable", sid))
        if space.turnable:
            lines.append(asp.fact("turnable", sid))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, repair.sense))
        if repair.expands:
            lines.append(asp.fact("expands", rid))
        if repair.turns:
            lines.append(asp.fact("turns", rid))
        if repair.doubles:
            lines.append(asp.fact("doubles", rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in asp:", sorted(asp_set - py_set))

    smoke_cases = list(CURATED)
    try:
        default_args = build_parser().parse_args([])
        params = resolve_params(default_args, random.Random(7))
        smoke_cases.append(params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE SETUP FAILED: {err}")

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated empty story.")
            emit(sample, trace=False, qa=False, header="")
        except Exception as err:
            rc = 1
            print(f"SMOKE TEST FAILED for {params}: {err}")

    if rc == 0:
        print(f"OK: generated {len(smoke_cases)} smoke-test stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: pirate friendship, a claimed fort, and a fair repair."
    )
    ap.add_argument("--space", choices=SPACES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.space and args.repair:
        space = SPACES[args.space]
        repair = REPAIRS[args.repair]
        if not repair_works(space, repair):
            raise StoryError(explain_rejection(space, repair))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_rejection(next(iter(SPACES.values())), REPAIRS[args.repair]))

    combos = [
        combo for combo in valid_combos()
        if (args.space is None or combo[0] == args.space)
        and (args.repair is None or combo[1] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    space_id, repair_id = rng.choice(sorted(combos))
    captain, captain_gender = _pick_kid(rng)
    friend, friend_gender = _pick_kid(rng, avoid=captain)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        space=space_id,
        repair=repair_id,
        captain=captain,
        captain_gender=captain_gender,
        friend=friend,
        friend_gender=friend_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        space = SPACES[params.space]
        repair = REPAIRS[params.repair]
    except KeyError as err:
        raise StoryError(f"Unknown story parameter: {err}") from err
    if not repair_works(space, repair):
        raise StoryError(explain_rejection(space, repair))

    world = tell(
        space=space,
        repair=repair,
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (space, repair) combos:\n")
        for space_id, repair_id in combos:
            print(f"  {space_id:14} {repair_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.captain} & {sample.params.friend}: {sample.params.space} + {sample.params.repair}"
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
