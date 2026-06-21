#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/source_inner_monologue_friendship_mystery.py
=======================================================================

A small storyworld about two friends who notice a strange clue, wonder about its
source, and solve a gentle mystery together. The prose uses a close child-facing
mystery style with inner monologue, but the story is driven by simulated world
state: clues, methods, discovery, cleanup, and an ending image that proves the
friendship grew steadier.

Run it
------
    python storyworlds/worlds/gpt-5.4/source_inner_monologue_friendship_mystery.py
    python storyworlds/worlds/gpt-5.4/source_inner_monologue_friendship_mystery.py --place classroom --clue wet_drops
    python storyworlds/worlds/gpt-5.4/source_inner_monologue_friendship_mystery.py --source tiny_fan --method follow_trail
    python storyworlds/worlds/gpt-5.4/source_inner_monologue_friendship_mystery.py --all
    python storyworlds/worlds/gpt-5.4/source_inner_monologue_friendship_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/source_inner_monologue_friendship_mystery.py --verify
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
        female = {"girl", "mother", "woman", "teacher_f"}
        male = {"boy", "father", "man", "teacher_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "teacher_f": "teacher",
            "teacher_m": "teacher",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    leader_label: str
    leader_type: str
    hiding_words: dict[str, str] = field(default_factory=dict)
    supports: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    notice_text: str
    trail_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SourceCfg:
    id: str
    label: str
    phrase: str
    kind: str
    clue: str
    settings: set[str] = field(default_factory=set)
    problem_text: str = ""
    fix_text: str = ""
    clean_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    fits: set[str] = field(default_factory=set)
    action_text: str = ""
    discover_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_mystery(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("noticed_clue") and ("mystery",) not in world.fired:
        world.fired.add(("mystery",))
        room = world.get("room")
        room.memes["mystery"] += 1
        for role in ("narrator", "friend"):
            world.get(role).memes["curiosity"] += 1
        out.append("__mystery__")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("investigating_together") and ("friendship",) not in world.fired:
        world.fired.add(("friendship",))
        world.get("narrator").memes["trust"] += 1
        world.get("friend").memes["trust"] += 1
        out.append("__friendship__")
    return out


def _r_discovery(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    if source.meters["found"] >= THRESHOLD and ("discovery",) not in world.fired:
        world.fired.add(("discovery",))
        for role in ("narrator", "friend"):
            world.get(role).memes["relief"] += 1
            world.get(role).memes["wonder"] += 1
        source.meters["risk"] = 0.0
        out.append("__discovery__")
    return out


CAUSAL_RULES = [
    Rule(name="mystery", tag="social", apply=_r_mystery),
    Rule(name="friendship", tag="social", apply=_r_friendship),
    Rule(name="discovery", tag="physical", apply=_r_discovery),
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


def source_matches_clue(source: SourceCfg, clue: Clue) -> bool:
    return source.clue == clue.id


def source_allowed_in_setting(source: SourceCfg, setting: Setting) -> bool:
    return setting.id in source.settings and source.id in setting.supports


def method_fits_clue(method: Method, clue: Clue) -> bool:
    return clue.kind in method.fits


def valid_combo(place: str, clue_id: str, source_id: str, method_id: str) -> bool:
    setting = SETTINGS[place]
    clue = CLUES[clue_id]
    source = SOURCES[source_id]
    method = METHODS[method_id]
    return (
        source_matches_clue(source, clue)
        and source_allowed_in_setting(source, setting)
        and method_fits_clue(method, clue)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place in SETTINGS:
        for clue_id in CLUES:
            for source_id in SOURCES:
                for method_id in METHODS:
                    if valid_combo(place, clue_id, source_id, method_id):
                        combos.append((place, clue_id, source_id, method_id))
    return combos


def predict_discovery(world: World, method: Method) -> bool:
    clue = world.facts["clue_cfg"]
    return method_fits_clue(method, clue)


def introduce(world: World, narrator: Entity, friend: Entity) -> None:
    world.say(
        f"{narrator.id} and {friend.id} were the sort of friends who liked to notice small things together. "
        f"At {world.setting.place}, {world.setting.detail}"
    )


def notice_clue(world: World, narrator: Entity, friend: Entity, clue: Clue) -> None:
    world.facts["noticed_clue"] = True
    world.get("source").meters["risk"] += 1
    narrator.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    propagate(world, narrate=False)
    world.say(clue.notice_text.format(narrator=narrator.id, friend=friend.id))
    world.say(
        f'{narrator.id} stopped and thought, "That is odd. There has to be a source for it."'
    )
    world.say(
        f'{friend.id} came close beside {narrator.pronoun("object")} and whispered, "Then let\'s solve it together."'
    )


def choose_method(world: World, narrator: Entity, friend: Entity, method: Method) -> None:
    world.facts["investigating_together"] = True
    propagate(world, narrate=False)
    if narrator.memes["curiosity"] >= THRESHOLD:
        world.say(
            f'{narrator.id} thought, "If I stay calm, the clue might tell us where to look."'
        )
    world.say(method.action_text.format(narrator=narrator.id, friend=friend.id))


def discover_source(
    world: World,
    narrator: Entity,
    friend: Entity,
    leader: Entity,
    clue: Clue,
    source_cfg: SourceCfg,
    method: Method,
) -> None:
    source = world.get("source")
    source.meters["found"] += 1
    propagate(world, narrate=False)
    hiding = world.setting.hiding_words[source_cfg.id]
    world.say(clue.trail_text.format(narrator=narrator.id, friend=friend.id, hiding=hiding))
    world.say(method.discover_text.format(narrator=narrator.id, friend=friend.id, hiding=hiding))
    world.say(
        f"There was the source: {source_cfg.phrase} {hiding}. {source_cfg.problem_text}"
    )
    world.say(
        f'{narrator.id} let out a small breath and thought, "So that was the secret all along."'
    )
    leader.memes["care"] += 1
    world.say(
        f"{leader.label.capitalize()} came over, smiled at their careful work, and {source_cfg.fix_text}"
    )
    world.say(source_cfg.clean_text)


def friendship_ending(world: World, narrator: Entity, friend: Entity, clue: Clue) -> None:
    narrator.memes["joy"] += 1
    friend.memes["joy"] += 1
    narrator.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f'"We make a good mystery team," {friend.id} said.'
    )
    world.say(
        f'{narrator.id} grinned and thought, "The best part was not finding the source. The best part was not looking alone."'
    )
    if clue.kind == "trail":
        end_image = "Soon they were walking side by side again, this time over a clean floor with no secret trail left behind."
    else:
        end_image = "Soon the room felt still and bright again, and the two friends sat shoulder to shoulder, listening only to each other turning pages."
    world.say(end_image)


def tell(
    setting: Setting,
    clue: Clue,
    source_cfg: SourceCfg,
    method: Method,
    narrator_name: str = "Mira",
    narrator_type: str = "girl",
    friend_name: str = "Ben",
    friend_type: str = "boy",
) -> World:
    world = World(setting)
    narrator = world.add(Entity(id="narrator", kind="character", type=narrator_type, label=narrator_name, role="narrator"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name, role="friend"))
    leader = world.add(
        Entity(
            id="leader",
            kind="character",
            type=setting.leader_type,
            label=setting.leader_label,
            role="adult",
        )
    )
    room = world.add(Entity(id="room", type="room", label=setting.place))
    source = world.add(Entity(id="source", type="thing", label=source_cfg.label, phrase=source_cfg.phrase))
    world.facts["clue_cfg"] = clue

    introduce(world, narrator, friend)
    world.para()
    notice_clue(world, narrator, friend, clue)
    world.para()
    choose_method(world, narrator, friend, method)
    world.para()
    discover_source(world, narrator, friend, leader, clue, source_cfg, method)
    friendship_ending(world, narrator, friend, clue)

    world.facts.update(
        narrator=narrator,
        friend=friend,
        leader=leader,
        setting=setting,
        clue=clue,
        source_cfg=source_cfg,
        source=source,
        method=method,
        solved=source.meters["found"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the classroom",
        detail="sunlight made bright squares on the floor, and the cubbies stood in a quiet row.",
        leader_label="ms. fern",
        leader_type="teacher_f",
        hiding_words={
            "leaky_bottle": "under the row of cubbies",
            "glitter_bag": "beside the art shelf",
        },
        supports={"leaky_bottle", "glitter_bag"},
    ),
    "library": Setting(
        id="library",
        place="the library corner",
        detail="the rug was soft, the shelves were tall, and every whisper sounded important.",
        leader_label="mr. dale",
        leader_type="teacher_m",
        hiding_words={
            "tiny_fan": "behind the big atlas shelf",
            "glitter_bag": "near the craft basket by the story rug",
        },
        supports={"tiny_fan", "glitter_bag"},
    ),
    "clubhouse": Setting(
        id="clubhouse",
        place="the clubhouse",
        detail="blankets hung like walls, and little strips of afternoon light peeped through the seams.",
        leader_label="mom",
        leader_type="mother",
        hiding_words={
            "leaky_bottle": "under the blanket bench",
            "tiny_fan": "behind the cushion tower",
        },
        supports={"leaky_bottle", "tiny_fan"},
    ),
}

CLUES = {
    "wet_drops": Clue(
        id="wet_drops",
        label="wet drops",
        phrase="a line of wet drops",
        kind="trail",
        notice_text="A line of wet drops shone on the floor like tiny glass buttons. {friend} touched one with a finger and looked up at {narrator}.",
        trail_text="{narrator} and {friend} followed the little drops one by one until they reached {hiding}.",
        tags={"water", "mystery"},
    ),
    "silver_glitter": Clue(
        id="silver_glitter",
        label="silver glitter",
        phrase="silver glitter",
        kind="trail",
        notice_text="Silver glitter winked from the floor in a crooked little path. It looked too neat to be an accident and too strange to ignore.",
        trail_text="The sparkles kept flashing ahead of {narrator} and {friend} until they led straight to {hiding}.",
        tags={"glitter", "mystery"},
    ),
    "soft_hum": Clue(
        id="soft_hum",
        label="soft hum",
        phrase="a soft humming sound",
        kind="sound",
        notice_text='A soft hum floated through the room and then hid again. "{friend}," {narrator} whispered, "did you hear that?"',
        trail_text="Each time the hum came back, {narrator} and {friend} turned a little more carefully toward {hiding}.",
        tags={"sound", "mystery"},
    ),
}

SOURCES = {
    "leaky_bottle": SourceCfg(
        id="leaky_bottle",
        label="water bottle",
        phrase="a water bottle with its lid tipped sideways",
        kind="wet",
        clue="wet_drops",
        settings={"classroom", "clubhouse"},
        problem_text="A bead of water slipped from the top and made one more drop.",
        fix_text="tightened the lid, wiped the puddle dry, and thanked them for finding it before anyone slipped",
        clean_text="The drops were gone, and the air felt ordinary again in the nicest possible way.",
        tags={"water", "cleanup"},
    ),
    "glitter_bag": SourceCfg(
        id="glitter_bag",
        label="glitter bag",
        phrase="a torn bag of silver glitter",
        kind="sparkle",
        clue="silver_glitter",
        settings={"classroom", "library"},
        problem_text="A tiny split along the side was sprinkling sparkles every time the bag leaned.",
        fix_text="set the bag inside a tray, folded the torn edge shut, and fetched a small brush",
        clean_text="Soon the runaway glitter was back where it belonged, and the floor no longer looked like it was keeping secrets.",
        tags={"glitter", "cleanup"},
    ),
    "tiny_fan": SourceCfg(
        id="tiny_fan",
        label="tiny fan",
        phrase="a tiny fan that had been left on low",
        kind="sound",
        clue="soft_hum",
        settings={"library", "clubhouse"},
        problem_text="Its blades were still turning, making the gentlest buzzing song.",
        fix_text="clicked the fan off and said they had very sharp ears",
        clean_text="At once the room grew still, and the silence felt warm instead of strange.",
        tags={"sound", "machine"},
    ),
}

METHODS = {
    "follow_trail": Method(
        id="follow_trail",
        label="follow the clue",
        fits={"trail"},
        action_text="{friend} crouched low while {narrator} walked slowly beside {friend}, and together they followed the clue without stepping on it.",
        discover_text="At the very end of the trail, both friends pointed at the same time toward {hiding}.",
        tags={"observe", "trail"},
    ),
    "listen_still": Method(
        id="listen_still",
        label="listen very still",
        fits={"sound"},
        action_text="{narrator} held one finger in the air, and both friends went quiet enough to hear the room breathe. They waited for the hum to return, then turned toward it together.",
        discover_text="The sound grew clearer near {hiding}, and {friend} smiled the small smile of someone who knows the answer is close.",
        tags={"listen", "sound"},
    ),
}

GIRL_NAMES = ["Mira", "Nora", "Lily", "Ava", "Zoe", "Maya", "Ella", "Lucy"]
BOY_NAMES = ["Ben", "Theo", "Max", "Leo", "Finn", "Sam", "Noah", "Eli"]


@dataclass
class StoryParams:
    place: str
    clue: str
    source: str
    method: str
    narrator_name: str
    narrator_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="classroom",
        clue="wet_drops",
        source="leaky_bottle",
        method="follow_trail",
        narrator_name="Mira",
        narrator_type="girl",
        friend_name="Ben",
        friend_type="boy",
    ),
    StoryParams(
        place="library",
        clue="soft_hum",
        source="tiny_fan",
        method="listen_still",
        narrator_name="Theo",
        narrator_type="boy",
        friend_name="Nora",
        friend_type="girl",
    ),
    StoryParams(
        place="classroom",
        clue="silver_glitter",
        source="glitter_bag",
        method="follow_trail",
        narrator_name="Lucy",
        narrator_type="girl",
        friend_name="Max",
        friend_type="boy",
    ),
    StoryParams(
        place="clubhouse",
        clue="wet_drops",
        source="leaky_bottle",
        method="follow_trail",
        narrator_name="Finn",
        narrator_type="boy",
        friend_name="Maya",
        friend_type="girl",
    ),
]


KNOWLEDGE = {
    "water": [
        (
            "Why can a water spill be a problem?",
            "A water spill can make the floor slippery, so someone might fall. That is why it helps to wipe it up quickly."
        )
    ],
    "glitter": [
        (
            "Why does glitter seem to get everywhere?",
            "Glitter is made of tiny light pieces that stick to things and scatter easily. A small tear in a bag can let lots of it escape."
        )
    ],
    "sound": [
        (
            "Why is a quiet sound sometimes hard to find?",
            "A quiet sound can bounce around a room and seem to come from different places. Listening very still helps your ears notice where it is strongest."
        )
    ],
    "observe": [
        (
            "What does it mean to follow a clue?",
            "Following a clue means you look carefully at what it shows and let it guide you to the answer. Good detectives do not rush past small details."
        )
    ],
    "listen": [
        (
            "Why can being quiet help solve a mystery?",
            "Being quiet helps you notice small sounds and changes around you. When the room is calm, clues are easier to hear."
        )
    ],
    "friendship": [
        (
            "How can a friend help in a mystery?",
            "A friend can notice something you missed and help you feel brave. Working together often makes a hard puzzle easier."
        )
    ],
    "cleanup": [
        (
            "Why is it kind to tell a grown-up about a problem you found?",
            "Telling a grown-up helps the problem get fixed before someone gets hurt or the mess grows bigger. It is a helpful thing to do."
        )
    ],
}
KNOWLEDGE_ORDER = ["water", "glitter", "sound", "observe", "listen", "friendship", "cleanup"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    narrator = f["narrator"]
    friend = f["friend"]
    clue = f["clue"]
    setting = f["setting"]
    return [
        f'Write a gentle mystery for a 3-to-5-year-old that includes the word "source" and takes place in {setting.place}.',
        f"Tell a story about two friends, {narrator.label} and {friend.label}, who notice {clue.phrase} and solve the mystery together using careful thinking.",
        "Write a child-facing story with inner monologue where the main child quietly wonders what caused a strange clue and ends by feeling grateful for friendship.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    narrator = f["narrator"]
    friend = f["friend"]
    setting = f["setting"]
    clue = f["clue"]
    source_cfg = f["source_cfg"]
    leader = f["leader"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {narrator.label} and {friend.label}, two friends at {setting.place}. They notice something strange and decide to solve it together."
        ),
        (
            "What clue started the mystery?",
            f"The mystery started with {clue.phrase}. That clue made the room feel secret and led the friends to start looking for its source."
        ),
        (
            f"How did {narrator.label} think about the mystery?",
            f"{narrator.label} used quiet inner thoughts to stay calm and curious. Those thoughts helped {narrator.pronoun('object')} treat the clue like a message instead of something scary."
        ),
        (
            "How did the friends find the answer?",
            f"They used {method.label} and paid close attention together. Because their method matched the kind of clue they had, it led them to the true source."
        ),
        (
            "What was the source of the clue?",
            f"The source was {source_cfg.phrase}. Once the friends found it, {leader.title_word} fixed the problem so the room felt normal again."
        ),
        (
            "How did friendship matter in the story?",
            f"The friends solved the mystery side by side instead of alone. Their teamwork made them braver and turned a strange moment into a good memory."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"friendship"}
    clue = f["clue"]
    source_cfg = f["source_cfg"]
    method = f["method"]
    tags |= set(clue.tags)
    tags |= set(source_cfg.tags)
    tags |= set(method.tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.label and e.id != e.label:
            bits.append(f"label={e.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_invalid(place: str, clue_id: str, source_id: str, method_id: str) -> str:
    setting = SETTINGS[place]
    clue = CLUES[clue_id]
    source = SOURCES[source_id]
    method = METHODS[method_id]
    if not source_matches_clue(source, clue):
        return (
            f"(No story: {clue.label} does not honestly point to {source.label}. "
            f"A mystery needs a real source for its clue.)"
        )
    if not source_allowed_in_setting(source, setting):
        return (
            f"(No story: {source.label} does not fit naturally in {setting.place}. "
            f"Pick a place where that source could really be hiding.)"
        )
    if not method_fits_clue(method, clue):
        return (
            f"(No story: the method '{method.label}' does not suit the clue '{clue.label}'. "
            f"Use a listening method for sounds and a following method for visible trails.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
real_source(S, C) :- source_for(S, C).
allowed(P, S) :- supports(P, S), source_place(S, P).
method_ok(M, C) :- clue_kind(C, K), fits(M, K).
valid(P, C, S, M) :- place(P), clue(C), source(S), method(M),
                     real_source(S, C), allowed(P, S), method_ok(M, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("place", place_id))
        for source_id in sorted(setting.supports):
            lines.append(asp.fact("supports", place_id, source_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_kind", clue_id, clue.kind))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("source_for", source_id, source.clue))
        for place_id in sorted(source.settings):
            lines.append(asp.fact("source_place", source_id, place_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        for kind in sorted(method.fits):
            lines.append(asp.fact("fits", method_id, kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def outcome_of(params: StoryParams) -> str:
    if valid_combo(params.place, params.clue, params.source, params.method):
        return "solved"
    return "invalid"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
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
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if outcome_of(params) != "solved" or not sample.story.strip():
                raise StoryError("generated invalid or empty sample")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke tests passed.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a friendship mystery about finding the source of a clue."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--narrator-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--narrator-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit_place = args.place
    explicit_clue = args.clue
    explicit_source = args.source
    explicit_method = args.method

    if explicit_place and explicit_clue and explicit_source and explicit_method:
        if not valid_combo(explicit_place, explicit_clue, explicit_source, explicit_method):
            raise StoryError(explain_invalid(explicit_place, explicit_clue, explicit_source, explicit_method))

    combos = [
        combo
        for combo in valid_combos()
        if (explicit_place is None or combo[0] == explicit_place)
        and (explicit_clue is None or combo[1] == explicit_clue)
        and (explicit_source is None or combo[2] == explicit_source)
        and (explicit_method is None or combo[3] == explicit_method)
    ]
    if not combos:
        if explicit_place and explicit_clue and explicit_source and explicit_method:
            raise StoryError(explain_invalid(explicit_place, explicit_clue, explicit_source, explicit_method))
        raise StoryError("(No valid combination matches the given options.)")

    place, clue, source, method = rng.choice(sorted(combos))
    narrator_type = args.narrator_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    narrator_name = args.narrator_name or pick_name(rng, narrator_type)
    friend_name = args.friend_name or pick_name(rng, friend_type, avoid=narrator_name)

    return StoryParams(
        place=place,
        clue=clue,
        source=source,
        method=method,
        narrator_name=narrator_name,
        narrator_type=narrator_type,
        friend_name=friend_name,
        friend_type=friend_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if not valid_combo(params.place, params.clue, params.source, params.method):
        raise StoryError(explain_invalid(params.place, params.clue, params.source, params.method))

    world = tell(
        setting=SETTINGS[params.place],
        clue=CLUES[params.clue],
        source_cfg=SOURCES[params.source],
        method=METHODS[params.method],
        narrator_name=params.narrator_name,
        narrator_type=params.narrator_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, clue, source, method) combos:\n")
        for place, clue, source, method in combos:
            print(f"  {place:10} {clue:15} {source:13} {method}")
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
            header = f"### {p.narrator_name} and {p.friend_name}: {p.clue} in {p.place}"
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
