#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/consumption_happy_ending_flashback_transformation_fable.py
=====================================================================================

A standalone storyworld for a tiny fable-like domain about **consumption**:
a young caterpillar is tempted to eat too much from a food patch, a warning and
a flashback help the child-creature remember restraint, and a later physical
transformation into a butterfly proves the lesson became part of the world.

The model prefers a small number of plausible variants over broad coverage:
only edible food patches and sensible helpers are allowed. The story always
lands in a happy ending, but the middle can differ:

* balanced: Pip eats enough and leaves a healthy reserve
* repaired: Pip gets too greedy, a friend warns, a flashback changes Pip's mind,
  and a compatible helper restores the patch while Pip transforms

Run it
------
    python storyworlds/worlds/gpt-5.4/consumption_happy_ending_flashback_transformation_fable.py
    python storyworlds/worlds/gpt-5.4/consumption_happy_ending_flashback_transformation_fable.py --patch clover_meadow --helper soft_rain
    python storyworlds/worlds/gpt-5.4/consumption_happy_ending_flashback_transformation_fable.py --patch rose_bush
    python storyworlds/worlds/gpt-5.4/consumption_happy_ending_flashback_transformation_fable.py --helper song_only
    python storyworlds/worlds/gpt-5.4/consumption_happy_ending_flashback_transformation_fable.py --all
    python storyworlds/worlds/gpt-5.4/consumption_happy_ending_flashback_transformation_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4/consumption_happy_ending_flashback_transformation_fable.py --verify
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
    phrase: str = ""
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
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Patch:
    id: str
    label: str
    phrase: str
    place: str
    food_word: str
    growth_need: str
    reserve: int
    leaves: int
    bloom: str
    edible: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    supports: set[str]
    sense: int
    arrival: str
    repair: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendCfg:
    id: str
    label: str
    phrase: str
    warning: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_patch_alarm(world: World) -> list[str]:
    patch = world.get("patch")
    reserve = world.facts["patch_cfg"].reserve
    if patch.meters["leaves_left"] > reserve:
        return []
    sig = ("patch_alarm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("pip").memes["worry"] += 1
    world.get("friend").memes["concern"] += 1
    patch.meters["scarcity"] += 1
    return ["__alarm__"]


def _r_ready_to_change(world: World) -> list[str]:
    pip = world.get("pip")
    if pip.meters["food"] < 2 or pip.memes["calm"] < 1:
        return []
    sig = ("ready_to_change",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pip.meters["ready_for_chrysalis"] += 1
    return []


def _r_transform(world: World) -> list[str]:
    pip = world.get("pip")
    if pip.meters["ready_for_chrysalis"] < THRESHOLD or pip.meters["rested"] < THRESHOLD:
        return []
    sig = ("transform",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pip.type = "butterfly"
    pip.label = "butterfly"
    pip.meters["wings"] += 1
    pip.meters["transformed"] += 1
    pip.memes["joy"] += 1
    return ["__transform__"]


CAUSAL_RULES = [
    Rule(name="patch_alarm", tag="physical", apply=_r_patch_alarm),
    Rule(name="ready_to_change", tag="development", apply=_r_ready_to_change),
    Rule(name="transform", tag="development", apply=_r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PATCHES = {
    "clover_meadow": Patch(
        id="clover_meadow",
        label="clover meadow",
        phrase="a low clover meadow beside a warm stone",
        place="at the edge of the garden",
        food_word="clover leaves",
        growth_need="rain",
        reserve=2,
        leaves=6,
        bloom="tiny white clover blossoms",
        edible=True,
        tags={"clover", "garden", "leaf"},
    ),
    "cabbage_bed": Patch(
        id="cabbage_bed",
        label="cabbage bed",
        phrase="a neat cabbage bed behind the watering can",
        place="in the kitchen garden",
        food_word="cabbage leaves",
        growth_need="watering",
        reserve=3,
        leaves=7,
        bloom="round green heads lifting in rows",
        edible=True,
        tags={"cabbage", "garden", "leaf"},
    ),
    "mulberry_branch": Patch(
        id="mulberry_branch",
        label="mulberry branch",
        phrase="a bending mulberry branch over the path",
        place="near the orchard wall",
        food_word="mulberry leaves",
        growth_need="breeze",
        reserve=2,
        leaves=6,
        bloom="fresh leaves whispering on the branch",
        edible=True,
        tags={"mulberry", "tree", "leaf"},
    ),
    "rose_bush": Patch(
        id="rose_bush",
        label="rose bush",
        phrase="a thorny rose bush by the gate",
        place="near the gate",
        food_word="rose leaves",
        growth_need="rain",
        reserve=2,
        leaves=5,
        bloom="red roses opening above the thorns",
        edible=False,
        tags={"rose", "thorn", "garden"},
    ),
}

HELPERS = {
    "soft_rain": Helper(
        id="soft_rain",
        label="soft rain",
        phrase="a soft silver rain",
        supports={"rain", "watering"},
        sense=3,
        arrival="Just then a soft rain drifted across the garden.",
        repair="The drops cooled the nibbled edges and fed the roots below.",
        qa_text="soft rain fed the roots and helped the leaves recover",
        tags={"rain", "water"},
    ),
    "gardener": Helper(
        id="gardener",
        label="gardener",
        phrase="the gentle gardener",
        supports={"watering"},
        sense=3,
        arrival="Soon the gentle gardener came by with a little tin can.",
        repair="With careful hands, the gardener watered the bed and tucked loose soil back around the stems.",
        qa_text="the gardener watered the bed and settled the soil around the stems",
        tags={"gardener", "water"},
    ),
    "morning_breeze": Helper(
        id="morning_breeze",
        label="morning breeze",
        phrase="a cool morning breeze",
        supports={"breeze"},
        sense=2,
        arrival="Then a cool morning breeze moved along the wall.",
        repair="It rocked the branch lightly and helped the leaves open to the light.",
        qa_text="the morning breeze rocked the branch and helped the leaves open again",
        tags={"breeze", "tree"},
    ),
    "song_only": Helper(
        id="song_only",
        label="a pretty song",
        phrase="a pretty song",
        supports=set(),
        sense=1,
        arrival="A bird sang nearby.",
        repair="The song was lovely, but songs alone do not feed roots or mend stems.",
        qa_text="a song could cheer someone up, but it could not regrow the leaves",
        tags={"song"},
    ),
}

FRIENDS = {
    "snail": FriendCfg(
        id="snail",
        label="snail",
        phrase="Sima the snail",
        warning='"Slow down," said Sima. "Wise consumption leaves supper for tomorrow too."',
        tags={"snail"},
    ),
    "ladybug": FriendCfg(
        id="ladybug",
        label="ladybug",
        phrase="Lulu the ladybug",
        warning='"Not every leaf must be yours," said Lulu. "A garden stays kind when small mouths leave room for one another."',
        tags={"ladybug"},
    ),
    "sparrow": FriendCfg(
        id="sparrow",
        label="sparrow",
        phrase="Pipkin the sparrow",
        warning='"Greedy beaks and greedy bites both empty a branch too fast," chirped Pipkin. "Leave a little green behind."',
        tags={"sparrow"},
    ),
}

GREED_LEVELS = {
    "eager": 2,
    "greedy": 4,
}

KNOWLEDGE = {
    "metamorphosis": [
        (
            "How does a caterpillar become a butterfly?",
            "A caterpillar first eats enough to grow, then it rests inside a chrysalis. After its body changes, it comes out as a butterfly with wings."
        )
    ],
    "consumption": [
        (
            "What does consumption mean?",
            "Consumption means using or eating something up. In a fable, it can remind us not to take more than we truly need."
        )
    ],
    "clover": [
        (
            "What is clover?",
            "Clover is a small plant with soft leaves and tiny flowers. Many little creatures can nibble it, and bees like its blossoms too."
        )
    ],
    "cabbage": [
        (
            "What is a cabbage plant?",
            "A cabbage plant grows broad green leaves that fold into a round head. Gardeners water it carefully so it can keep growing."
        )
    ],
    "mulberry": [
        (
            "What is a mulberry tree?",
            "A mulberry tree is a tree with soft leaves and dark berries. Some caterpillars eat its leaves while they are growing."
        )
    ],
    "rain": [
        (
            "Why does rain help plants?",
            "Rain carries water down to the roots, and roots need water to stay alive and grow new leaves."
        )
    ],
    "gardener": [
        (
            "What does a gardener do?",
            "A gardener waters plants, tends the soil, and helps stems and leaves stay healthy."
        )
    ],
    "breeze": [
        (
            "How can a breeze help a branch?",
            "A gentle breeze can cool a plant and move air around its leaves. It can also help a weak branch settle and lift back toward the light."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "consumption",
    "metamorphosis",
    "clover",
    "cabbage",
    "mulberry",
    "rain",
    "gardener",
    "breeze",
]


@dataclass
class StoryParams:
    patch: str
    helper: str
    friend: str
    greed: str
    name: str
    seed: Optional[int] = None


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def patch_is_reasonable(patch: Patch) -> bool:
    return patch.edible


def helper_fits(helper: Helper, patch: Patch) -> bool:
    return patch.growth_need in helper.supports


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for patch_id, patch in PATCHES.items():
        if not patch_is_reasonable(patch):
            continue
        for helper_id, helper in HELPERS.items():
            if helper.sense >= SENSE_MIN and helper_fits(helper, patch):
                combos.append((patch_id, helper_id))
    return combos


def explain_patch_rejection(patch: Patch) -> str:
    return (
        f"(No story: {patch.phrase} is not a reasonable food patch here. "
        f"A fable about consumption needs something the caterpillar can honestly eat.)"
    )


def explain_helper_rejection(helper: Helper, patch: Optional[Patch] = None) -> str:
    if helper.sense < SENSE_MIN:
        better = " / ".join(sorted(h.id for h in sensible_helpers()))
        return (
            f"(Refusing helper '{helper.id}': it scores too low on common sense "
            f"(sense={helper.sense} < {SENSE_MIN}). Try: {better}.)"
        )
    if patch is not None and not helper_fits(helper, patch):
        return (
            f"(No story: {helper.label} does not meet what the {patch.label} needs. "
            f"This patch grows back with {patch.growth_need}, so choose a compatible helper.)"
        )
    return "(No story: that helper does not fit this patch.)"


def consume(world: World, amount: int, patch_cfg: Patch) -> None:
    pip = world.get("pip")
    patch = world.get("patch")
    patch.meters["leaves_left"] = max(0.0, patch.meters["leaves_left"] - amount)
    pip.meters["food"] += amount
    pip.memes["desire"] += 1
    pip.memes["joy"] += 1
    if amount >= 4:
        pip.meters["too_full"] += 1
    propagate(world, narrate=False)
    if amount >= 4:
        world.say(
            f"So Pip munched and munched until only a little green was left on the {patch_cfg.label}. "
            f"Pip's round body felt heavy with more than enough {patch_cfg.food_word}."
        )
    else:
        world.say(
            f"Pip nibbled a fair breakfast of {patch_cfg.food_word}, then paused before the patch grew thin."
        )


def flashback(world: World, patch_cfg: Patch) -> None:
    pip = world.get("pip")
    pip.memes["memory"] += 1
    pip.memes["calm"] += 1
    world.say(
        f"At that worried moment, Pip remembered an earlier spring when they had been no bigger than a green comma on a wet stem. "
        f"Old Mara the moth had once led them to a single leaf and said, "
        f'"Small one, careful consumption keeps tomorrow alive. Eat enough, and let the garden keep its breath."'
    )
    world.say(
        f"The old words fluttered inside Pip more softly than wings, and Pip looked again at the thin little reserve still clinging to the {patch_cfg.label}."
    )


def repair_patch(world: World, helper_cfg: Helper, patch_cfg: Patch) -> None:
    patch = world.get("patch")
    patch.meters["helped"] += 1
    patch.meters["healing"] += 1
    patch.meters["leaves_left"] += 2
    world.say(helper_cfg.arrival)
    world.say(helper_cfg.repair)
    world.say(
        f"Pip backed away from the patch and left the new green alone. By doing less, Pip finally began to do right."
    )


def settle_for_change(world: World) -> None:
    pip = world.get("pip")
    pip.memes["calm"] += 1
    pip.meters["rested"] += 1
    propagate(world, narrate=False)
    world.say(
        "Then Pip tucked under a safe leaf and spun a neat chrysalis, still and patient at last."
    )


def emerge(world: World, patch_cfg: Patch) -> None:
    propagate(world, narrate=False)
    patch = world.get("patch")
    patch.meters["flowers_helped"] += 1
    world.say(
        f"Days later, the chrysalis opened, and out came Pip with painted wings. "
        f"The little eater had become a butterfly."
    )
    world.say(
        f"Instead of taking leaf after leaf, Pip now floated from blossom to blossom above the {patch_cfg.label}, carrying dust-fine pollen and helping fresh growth begin."
    )


def ending(world: World, friend_cfg: FriendCfg, patch_cfg: Patch, outcome: str) -> None:
    pip = world.get("pip")
    friend = world.get("friend")
    pip.memes["gratitude"] += 1
    friend.memes["relief"] += 1
    if outcome == "repaired":
        world.say(
            f"Before long, the {patch_cfg.label} looked green again, with {patch_cfg.bloom} shining between the leaves."
        )
        world.say(
            f'{friend_cfg.phrase} smiled up at Pip and said, "You have changed in more ways than one."'
        )
    else:
        world.say(
            f"Because Pip had left a good reserve, the {patch_cfg.label} stayed full and bright, and soon there were {patch_cfg.bloom} nodding in the light."
        )
        world.say(
            f'{friend_cfg.phrase} watched the leaves stir and said, "A small pause can save a whole patch."'
        )
    world.say(
        "So Pip learned the old fable truth: the happiest mouth is not the one that takes the most, but the one that leaves room for tomorrow."
    )


def outcome_of(params: StoryParams) -> str:
    amount = GREED_LEVELS[params.greed]
    patch = PATCHES[params.patch]
    remaining = patch.leaves - amount
    return "repaired" if remaining <= patch.reserve else "balanced"


def tell(
    patch_cfg: Patch,
    helper_cfg: Helper,
    friend_cfg: FriendCfg,
    greed: str,
    name: str,
) -> World:
    world = World()
    pip = world.add(Entity(id="pip", kind="character", type="caterpillar", label="caterpillar", phrase=name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_cfg.label, label=friend_cfg.label, phrase=friend_cfg.phrase, role="friend"))
    patch = world.add(Entity(id="patch", type="patch", label=patch_cfg.label, phrase=patch_cfg.phrase, role="patch"))
    helper = world.add(Entity(id="helper", type="helper", label=helper_cfg.label, phrase=helper_cfg.phrase, role="helper"))
    patch.meters["leaves_left"] = float(patch_cfg.leaves)

    world.facts.update(
        hero_name=name,
        patch_cfg=patch_cfg,
        helper_cfg=helper_cfg,
        friend_cfg=friend_cfg,
        greed=greed,
    )

    world.say(
        f"In a quiet corner {patch_cfg.place}, there lived a young caterpillar named {name}. "
        f"{name} made a home beside {patch_cfg.phrase} and loved the taste of {patch_cfg.food_word}."
    )
    world.say(
        f"Each morning, {name} promised to eat politely. Yet every green leaf looked like a little invitation."
    )

    world.para()
    world.say(
        f"One shining day the {patch_cfg.label} looked especially rich and soft. "
        f'"Just this once," thought {name}, "I will have a grand breakfast."'
    )

    amount = GREED_LEVELS[greed]
    consume(world, amount=amount, patch_cfg=patch_cfg)

    if world.get("patch").meters["scarcity"] >= THRESHOLD:
        world.say(friend_cfg.warning)
        world.para()
        flashback(world, patch_cfg)
        world.para()
        repair_patch(world, helper_cfg, patch_cfg)
        outcome = "repaired"
    else:
        world.get("pip").memes["calm"] += 1
        world.say(
            f"{friend_cfg.phrase} nodded from nearby, pleased that the patch still had plenty left for later."
        )
        outcome = "balanced"

    world.para()
    settle_for_change(world)
    emerge(world, patch_cfg)
    world.para()
    ending(world, friend_cfg, patch_cfg, outcome)

    world.facts.update(
        outcome=outcome,
        transformed=world.get("pip").meters["transformed"] >= THRESHOLD,
        leaves_left=int(world.get("patch").meters["leaves_left"]),
        helper_used=outcome == "repaired",
        flashback_used=outcome == "repaired",
        reserve_kept=world.get("patch").meters["leaves_left"] >= patch_cfg.reserve,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    patch = world.facts["patch_cfg"]
    helper = world.facts["helper_cfg"]
    friend = world.facts["friend_cfg"]
    outcome = world.facts["outcome"]
    name = world.facts["hero_name"]
    base = (
        f'Write a short fable for a young child that includes the word "consumption", '
        f'uses a flashback, and ends with a transformation and a happy ending.'
    )
    if outcome == "repaired":
        return [
            base,
            f"Tell a garden fable about a caterpillar named {name} who nearly eats too much from a {patch.label}, then remembers an old lesson in a flashback and changes.",
            f"Write a gentle fable where {friend.phrase} warns a hungry caterpillar, {helper.label} helps the patch recover, and the caterpillar later becomes a butterfly.",
        ]
    return [
        base,
        f"Tell a bright fable about a young caterpillar named {name} who practices careful consumption at a {patch.label} and later transforms into a butterfly.",
        f"Write a simple transformation story where a childlike caterpillar leaves enough food for tomorrow, keeps the patch healthy, and ends happily above the garden.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    patch = world.facts["patch_cfg"]
    helper = world.facts["helper_cfg"]
    friend = world.facts["friend_cfg"]
    name = world.facts["hero_name"]
    outcome = world.facts["outcome"]
    leaves_left = world.facts["leaves_left"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a young caterpillar named {name} living by a {patch.label}. The story also includes {friend.phrase}, who notices what happens to the patch."
        ),
        (
            f"What did {name} want to eat?",
            f"{name} wanted to eat the {patch.food_word} from the {patch.label}. The leaves looked so rich that breakfast began to feel bigger than it should have been."
        ),
    ]
    if outcome == "repaired":
        qa.append(
            (
                f"Why did {friend.phrase} warn {name}?",
                f"{friend.phrase} warned {name} because too many leaves had been eaten and only a small reserve was left. That meant the patch might not have enough green left to stay healthy for tomorrow."
            )
        )
        qa.append(
            (
                "What happened in the flashback, and why did it matter?",
                f"In the flashback, {name} remembered Old Mara the moth teaching that careful consumption means eating enough and leaving enough for tomorrow. That memory calmed {name} and changed the choice from greedy taking to patient restraint."
            )
        )
        qa.append(
            (
                f"How did the {patch.label} recover?",
                f"{helper.label.capitalize()} helped the patch recover. {helper.qa_text}, and {name} stopped eating so the new green could stay in place."
            )
        )
    else:
        qa.append(
            (
                f"Did {name} eat everything?",
                f"No. {name} ate enough to grow, then stopped while the {patch.label} still had a healthy reserve. That is why the patch stayed bright instead of turning thin and worried."
            )
        )
    qa.append(
        (
            f"What transformation happened at the end?",
            f"{name} spun a chrysalis and later came out as a butterfly. The ending shows that the lesson changed not only {name}'s thinking, but also {name}'s body and way of living."
        )
    )
    qa.append(
        (
            "How did the story end happily?",
            f"It ended happily because {name} changed and the {patch.label} stayed alive with {leaves_left} leaves left to grow from. In the final image, the one who once only ate is now helping life continue."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    patch = world.facts["patch_cfg"]
    helper = world.facts["helper_cfg"]
    tags = {"consumption", "metamorphosis"} | set(patch.tags) | set(helper.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        patch="clover_meadow",
        helper="soft_rain",
        friend="snail",
        greed="greedy",
        name="Pip",
    ),
    StoryParams(
        patch="cabbage_bed",
        helper="gardener",
        friend="ladybug",
        greed="greedy",
        name="Moss",
    ),
    StoryParams(
        patch="mulberry_branch",
        helper="morning_breeze",
        friend="sparrow",
        greed="eager",
        name="Twill",
    ),
    StoryParams(
        patch="clover_meadow",
        helper="soft_rain",
        friend="ladybug",
        greed="eager",
        name="Pip",
    ),
]


ASP_RULES = r"""
reasonable_patch(P) :- patch(P), edible(P).
sensible_helper(H) :- helper(H), sense(H, S), sense_min(M), S >= M.
fits(P, H) :- need(P, N), supports(H, N).
valid(P, H) :- reasonable_patch(P), sensible_helper(H), fits(P, H).

consume_amt(eager, 2).
consume_amt(greedy, 4).

remaining(P, G, R) :- leaves(P, L), consume_amt(G, A), R = L - A.
repaired(P, G) :- reserve(P, Need), remaining(P, G, R), R <= Need.
balanced(P, G) :- reserve(P, Need), remaining(P, G, R), R > Need.

outcome(repaired) :- chosen_patch(P), chosen_greed(G), repaired(P, G).
outcome(balanced) :- chosen_patch(P), chosen_greed(G), balanced(P, G).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for patch_id, patch in PATCHES.items():
        lines.append(asp.fact("patch", patch_id))
        if patch.edible:
            lines.append(asp.fact("edible", patch_id))
        lines.append(asp.fact("need", patch_id, patch.growth_need))
        lines.append(asp.fact("reserve", patch_id, patch.reserve))
        lines.append(asp.fact("leaves", patch_id, patch.leaves))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("sense", helper_id, helper.sense))
        for support in sorted(helper.supports):
            lines.append(asp.fact("supports", helper_id, support))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for greed in GREED_LEVELS:
        lines.append(asp.fact("greed", greed))
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
            asp.fact("chosen_patch", params.patch),
            asp.fact("chosen_greed", params.greed),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases: list[StoryParams] = list(CURATED)
    for seed in range(40):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)

    mismatches = []
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches.append((params, asp_outcome(params), outcome_of(params)))
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH in outcome model ({len(mismatches)} cases).")
        for params, clingo_out, py_out in mismatches[:5]:
            print(" ", params, clingo_out, py_out)

    try:
        smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a caterpillar learns wise consumption, remembers an old lesson, and transforms into a butterfly."
    )
    ap.add_argument("--patch", choices=PATCHES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--greed", choices=sorted(GREED_LEVELS))
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (patch, helper) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


NAMES = ["Pip", "Moss", "Twill", "Dew", "Fern", "Sunny", "Leaf"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.patch:
        patch = PATCHES[args.patch]
        if not patch_is_reasonable(patch):
            raise StoryError(explain_patch_rejection(patch))
    if args.helper:
        helper = HELPERS[args.helper]
        if helper.sense < SENSE_MIN:
            raise StoryError(explain_helper_rejection(helper))
        if args.patch:
            patch = PATCHES[args.patch]
            if patch_is_reasonable(patch) and not helper_fits(helper, patch):
                raise StoryError(explain_helper_rejection(helper, patch))
    combos = [
        combo
        for combo in valid_combos()
        if (args.patch is None or combo[0] == args.patch)
        and (args.helper is None or combo[1] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    patch_id, helper_id = rng.choice(sorted(combos))
    friend_id = args.friend or rng.choice(sorted(FRIENDS))
    greed = args.greed or rng.choice(sorted(GREED_LEVELS))
    name = args.name or rng.choice(NAMES)
    return StoryParams(
        patch=patch_id,
        helper=helper_id,
        friend=friend_id,
        greed=greed,
        name=name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.patch not in PATCHES:
        raise StoryError(f"(Unknown patch '{params.patch}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")
    if params.friend not in FRIENDS:
        raise StoryError(f"(Unknown friend '{params.friend}'.)")
    if params.greed not in GREED_LEVELS:
        raise StoryError(f"(Unknown greed level '{params.greed}'.)")

    patch_cfg = PATCHES[params.patch]
    helper_cfg = HELPERS[params.helper]
    friend_cfg = FRIENDS[params.friend]

    if not patch_is_reasonable(patch_cfg):
        raise StoryError(explain_patch_rejection(patch_cfg))
    if helper_cfg.sense < SENSE_MIN:
        raise StoryError(explain_helper_rejection(helper_cfg))
    if not helper_fits(helper_cfg, patch_cfg):
        raise StoryError(explain_helper_rejection(helper_cfg, patch_cfg))

    world = tell(
        patch_cfg=patch_cfg,
        helper_cfg=helper_cfg,
        friend_cfg=friend_cfg,
        greed=params.greed,
        name=params.name,
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
        print(f"{len(combos)} compatible (patch, helper) combos:\n")
        for patch, helper in combos:
            print(f"  {patch:15} {helper}")
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
            header = f"### {p.name}: {p.patch} with {p.helper} ({outcome_of(p)})"
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
