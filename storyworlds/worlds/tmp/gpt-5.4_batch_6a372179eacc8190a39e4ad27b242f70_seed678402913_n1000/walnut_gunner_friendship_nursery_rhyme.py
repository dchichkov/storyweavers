#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/walnut_gunner_friendship_nursery_rhyme.py
====================================================================

A tiny storyworld about Gunner and a friend finding a walnut, losing it to a
small garden trouble, and fixing the trouble together. The prose leans toward a
nursery-rhyme voice: patterned, concrete, and gentle.

The world model keeps two axes of state:

* physical meters on entities (stuck, wet, cracked, safe)
* emotional memes on characters (pride, worry, gratitude, friendship)

The central constraint is simple and explicit: each kind of trouble needs the
right sort of rescue method. A leaf scoop is good for a puddle, a hook is good
for a hole, and a soft loop is good for a briar patch. The generator refuses
mismatched or low-sense choices.

Run it
------
    python storyworlds/worlds/gpt-5.4/walnut_gunner_friendship_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/walnut_gunner_friendship_nursery_rhyme.py --trouble puddle
    python storyworlds/worlds/gpt-5.4/walnut_gunner_friendship_nursery_rhyme.py --method boot_nudge
    python storyworlds/worlds/gpt-5.4/walnut_gunner_friendship_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/walnut_gunner_friendship_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/walnut_gunner_friendship_nursery_rhyme.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "wren"}
        male = {"boy", "gosling", "mouse", "mole", "frog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Trouble:
    id: str = ""
    label: str = ""
    place: str = ""
    need: str = ""
    risk: int = 1
    bump: int = 0
    fall_line: str = ""
    rescue_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str = ""
    label: str = ""
    phrase: str = ""
    need: str = ""
    sense: int = 2
    power: int = 1
    gentleness: int = 1
    action_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendCfg:
    id: str = ""
    name: str = ""
    kind: str = ""
    type: str = ""
    step: str = ""
    trait: str = ""
    rhyme: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    trouble: str
    method: str
    friend: str
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


def _r_stuck_worry(world: World) -> list[str]:
    walnut = world.get("walnut")
    if walnut.meters["stuck"] < THRESHOLD:
        return []
    sig = ("stuck_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("Gunner").memes["worry"] += 1
    world.get("Friend").memes["concern"] += 1
    return []


def _r_rescue_bond(world: World) -> list[str]:
    walnut = world.get("walnut")
    if walnut.meters["safe"] < THRESHOLD:
        return []
    sig = ("rescue_bond",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("Gunner").memes["gratitude"] += 1
    world.get("Gunner").memes["friendship"] += 1
    world.get("Friend").memes["friendship"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="stuck_worry", tag="emotion", apply=_r_stuck_worry),
    Rule(name="rescue_bond", tag="emotion", apply=_r_rescue_bond),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


TROUBLES = {
    "puddle": Trouble(
        id="puddle",
        label="puddle",
        place="a rain puddle by the bean rows",
        need="water",
        risk=1,
        bump=0,
        fall_line="plip-plopped off his wing and into a silver puddle",
        rescue_image="the water gave one cold blink",
        tags={"puddle", "water"},
    ),
    "burrow": Trouble(
        id="burrow",
        label="burrow mouth",
        place="the dark mouth of an old burrow",
        need="hole",
        risk=2,
        bump=1,
        fall_line="rolled round and round to the lip of a burrow hole",
        rescue_image="the hole looked black as a button box",
        tags={"burrow", "hole"},
    ),
    "briar": Trouble(
        id="briar",
        label="briar patch",
        place="a rose briar under the fence",
        need="briar",
        risk=2,
        bump=2,
        fall_line="bounced under the briars with a prickly little clack",
        rescue_image="the thorns held it in a scratchy ring",
        tags={"briar", "thorn"},
    ),
}

METHODS = {
    "leaf_scoop": Method(
        id="leaf_scoop",
        label="leaf scoop",
        phrase="a curled dock leaf",
        need="water",
        sense=3,
        power=2,
        gentleness=2,
        action_text="slid a curled dock leaf under the walnut and lifted it up like a little green spoon",
        qa_text="used a curled leaf to scoop the walnut out",
        tags={"leaf", "water"},
    ),
    "bark_boat": Method(
        id="bark_boat",
        label="bark boat",
        phrase="a chip of bark",
        need="water",
        sense=2,
        power=1,
        gentleness=1,
        action_text="floated a chip of bark beside the walnut and nudged it to shore",
        qa_text="floated a chip of bark and nudged the walnut to shore",
        tags={"bark", "water"},
    ),
    "twig_hook": Method(
        id="twig_hook",
        label="twig hook",
        phrase="a bent twig",
        need="hole",
        sense=3,
        power=2,
        gentleness=1,
        action_text="lowered a bent twig, caught the shell, and drew it up with careful little tugs",
        qa_text="used a bent twig like a hook to pull the walnut up",
        tags={"twig", "hook"},
    ),
    "ribbon_loop": Method(
        id="ribbon_loop",
        label="ribbon loop",
        phrase="a dropped ribbon loop",
        need="hole",
        sense=2,
        power=2,
        gentleness=2,
        action_text="dangled a ribbon loop, settled it around the walnut, and lifted it softly from the dark",
        qa_text="looped a ribbon around the walnut and lifted it out",
        tags={"ribbon", "hook"},
    ),
    "grass_loop": Method(
        id="grass_loop",
        label="grass loop",
        phrase="a plait of long grass",
        need="briar",
        sense=3,
        power=2,
        gentleness=2,
        action_text="threaded a plait of long grass under the shell and drew it free without a scratch to either friend",
        qa_text="used a soft grass loop to draw the walnut out",
        tags={"grass", "briar"},
    ),
    "forked_stick": Method(
        id="forked_stick",
        label="forked stick",
        phrase="a forked stick",
        need="briar",
        sense=2,
        power=2,
        gentleness=1,
        action_text="reached in with a forked stick and eased the walnut out from the thorns",
        qa_text="used a forked stick to ease the walnut out",
        tags={"stick", "briar"},
    ),
    "boot_nudge": Method(
        id="boot_nudge",
        label="boot nudge",
        phrase="the toe of a boot",
        need="any",
        sense=1,
        power=1,
        gentleness=0,
        action_text="gave the walnut a rough nudge with a boot",
        qa_text="nudged the walnut roughly with a boot",
        tags={"rough"},
    ),
}

FRIENDS = {
    "pip": FriendCfg(
        id="pip",
        name="Pip",
        kind="character",
        type="mouse",
        step="tip-tap",
        trait="nimble",
        rhyme="quick as a whisper",
        tags={"mouse"},
    ),
    "dot": FriendCfg(
        id="dot",
        name="Dot",
        kind="character",
        type="wren",
        step="skip-skip",
        trait="bright",
        rhyme="light as a feather",
        tags={"bird"},
    ),
    "moss": FriendCfg(
        id="moss",
        name="Moss",
        kind="character",
        type="mole",
        step="pat-pat",
        trait="steady",
        rhyme="slow and sure",
        tags={"mole"},
    ),
}


def suitable_method(trouble: Trouble, method: Method) -> bool:
    if method.sense < SENSE_MIN:
        return False
    return method.need == trouble.need and method.power >= trouble.risk


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for tid, trouble in TROUBLES.items():
        for mid, method in METHODS.items():
            if suitable_method(trouble, method):
                combos.append((tid, mid))
    return sorted(combos)


def outcome_of(params: StoryParams) -> str:
    trouble = TROUBLES[params.trouble]
    method = METHODS[params.method]
    return "plant" if trouble.bump > method.gentleness else "share"


def explain_combo_rejection(trouble: Trouble, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it is too rough for this gentle world "
            f"(sense={method.sense} < {SENSE_MIN}). Pick a calmer rescue method.)"
        )
    return (
        f"(No story: {method.label} does not sensibly solve a {trouble.label}. "
        f"This trouble needs a {trouble.need}-style rescue.)"
    )


def introduce(world: World, gunner: Entity, friend: Entity) -> None:
    world.say(
        f"Gunner Goose went patter-pat through the kitchen garden at first light. "
        f"Beside him came {friend.id} {friend.attrs['species_label']}, "
        f"{friend.attrs['step']} and {friend.attrs['rhyme']}."
    )
    world.say(
        f"They were the kind of friends who noticed shiny things, soft songs, "
        f"and good places to sit side by side."
    )


def find_walnut(world: World, gunner: Entity, friend: Entity) -> None:
    walnut = world.get("walnut")
    gunner.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Under the broad cabbages they found a walnut, round and brown, "
        f"with a shell striped like a tiny wooden moon."
    )
    world.say(
        f'"A breakfast ball! A drum! A treasure!" sang Gunner. '
        f'"Let me carry it, and I shall lead the way."'
    )
    walnut.attrs["owner_first"] = gunner.id


def boast_and_drop(world: World, gunner: Entity, trouble: Trouble) -> None:
    walnut = world.get("walnut")
    gunner.memes["pride"] += 1
    world.say(
        f"Gunner tucked the walnut high on his wing and marched with a "
        f"brave little bounce."
    )
    world.say(
        f"But walnuts are smooth, and pride can be slippery. Soon it {trouble.fall_line}."
    )
    walnut.meters["stuck"] += 1
    if trouble.id == "puddle":
        walnut.meters["wet"] += 1
    propagate(world, narrate=False)


def trouble_beat(world: World, gunner: Entity, friend: Entity, trouble: Trouble) -> None:
    world.say(
        f"There it lay in {trouble.place}, and {trouble.rescue_image}."
    )
    if gunner.memes["worry"] >= THRESHOLD:
        world.say(
            f'Gunner made a small sound. "Oh dear," he whispered. '
            f'"I wanted the walnut to look grand in my wing, not lost from my wing."'
        )
    world.say(
        f'{friend.id} did not laugh. {friend.pronoun().capitalize()} stood close enough '
        f"for friendship to feel warm."
    )


def offer_help(world: World, friend: Entity, method: Method) -> None:
    friend.memes["care"] += 1
    world.say(
        f'"Do not huff and do not fret," said {friend.id}. '
        f'"Two small friends can do more than one. I can fetch {method.phrase}."'
    )


def rescue(world: World, gunner: Entity, friend: Entity, trouble: Trouble, method: Method) -> None:
    walnut = world.get("walnut")
    world.say(
        f"So {friend.id} found {method.phrase} and {method.action_text}."
    )
    walnut.meters["stuck"] = 0.0
    walnut.meters["safe"] += 1
    if trouble.bump > method.gentleness:
        walnut.meters["cracked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The walnut came back at last, and Gunner let out the breath he had been holding."
    )


def thanks(world: World, gunner: Entity, friend: Entity) -> None:
    gunner.memes["pride"] = 0.0
    gunner.memes["gratitude"] += 1
    world.say(
        f'"Thank you," said Gunner. "I tried to march ahead alone, '
        f"but the day went better when you marched beside me."'
    )


def share_end(world: World, gunner: Entity, friend: Entity) -> None:
    walnut = world.get("walnut")
    gunner.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    walnut.meters["eaten"] += 1
    world.say(
        f"They tapped the shell on a flat warm stone. Crack went the walnut, "
        f"not in sorrow but in supper."
    )
    world.say(
        f"Gunner took one sweet bite and gave the next to {friend.id}. "
        f"Then they sang, soft and silly, shoulder to shoulder in the sun."
    )
    world.say(
        "From then on, whenever Gunner found something fine, he made room beside it for a friend."
    )


def plant_end(world: World, gunner: Entity, friend: Entity) -> None:
    walnut = world.get("walnut")
    gunner.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    walnut.meters["planted"] += 1
    world.say(
        f"But the shell had split the hard way, and the walnut was no tidy breakfast."
    )
    world.say(
        f'"Then let us plant it," said {friend.id}. "A cracked thing can still begin." '
        f"So together they tucked it under a patch of soft earth and patted the soil down neat."
    )
    world.say(
        "They went home humming that friendship is like a little tree: it grows best when two small hands are kind."
    )


def tell(trouble: Trouble, method: Method, friend_cfg: FriendCfg) -> World:
    world = World()
    gunner = world.add(
        Entity(
            id="Gunner",
            kind="character",
            type="gosling",
            label="Gunner Goose",
            phrase="Gunner Goose",
            role="hero",
            attrs={"species_label": "Mouse" if False else "Goose"},
            tags={"friendship"},
        )
    )
    friend = world.add(
        Entity(
            id=friend_cfg.name,
            kind="character",
            type=friend_cfg.type,
            label=friend_cfg.name,
            phrase=friend_cfg.name,
            role="friend",
            attrs={
                "step": friend_cfg.step,
                "trait": friend_cfg.trait,
                "rhyme": friend_cfg.rhyme,
                "species_label": friend_cfg.kind,
            },
            tags=set(friend_cfg.tags),
        )
    )
    walnut = world.add(
        Entity(
            id="walnut",
            kind="thing",
            type="walnut",
            label="walnut",
            phrase="a walnut",
            tags={"walnut"},
        )
    )

    introduce(world, gunner, friend)
    find_walnut(world, gunner, friend)

    world.para()
    boast_and_drop(world, gunner, trouble)
    trouble_beat(world, gunner, friend, trouble)

    world.para()
    offer_help(world, friend, method)
    rescue(world, gunner, friend, trouble, method)
    thanks(world, gunner, friend)

    world.para()
    if walnut.meters["cracked"] >= THRESHOLD:
        plant_end(world, gunner, friend)
        outcome = "plant"
    else:
        share_end(world, gunner, friend)
        outcome = "share"

    world.facts.update(
        gunner=gunner,
        friend=friend,
        friend_cfg=friend_cfg,
        walnut=walnut,
        trouble=trouble,
        method=method,
        outcome=outcome,
        helped=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    gunner = world.facts["gunner"]
    friend = world.facts["friend"]
    trouble = world.facts["trouble"]
    outcome = world.facts["outcome"]
    if outcome == "share":
        return [
            'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "walnut" and "Gunner" and centers on friendship.',
            f"Tell a gentle garden story where Gunner drops a walnut into {trouble.place} and {friend.id} helps him get it back, ending with the friends sharing it.",
            "Write a sing-song tale in which a proud child learns that treasures feel better when shared with a friend.",
        ]
    return [
        'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "walnut" and "Gunner" and centers on friendship.',
        f"Tell a gentle garden story where Gunner drops a walnut into {trouble.place} and {friend.id} helps him recover it, but the shell cracks and the friends plant it together.",
        "Write a simple rhyming-feeling tale where a small mistake turns into a kinder ending because two friends work together.",
    ]


KNOWLEDGE = {
    "walnut": [
        (
            "What is a walnut?",
            "A walnut is a round nut with a hard shell. People and animals can open the shell to get the food inside.",
        )
    ],
    "puddle": [
        (
            "What is a puddle?",
            "A puddle is a little pool of water on the ground. It often appears after rain.",
        )
    ],
    "burrow": [
        (
            "What is a burrow?",
            "A burrow is a hole in the ground where some animals live or hide. It can be dark and deep for little things that roll near it.",
        )
    ],
    "briar": [
        (
            "What is a briar patch?",
            "A briar patch is a place full of thorny stems. The thorns can scratch, so it is better to reach in carefully.",
        )
    ],
    "leaf": [
        (
            "Why can a leaf be useful?",
            "A big leaf can act like a tiny scoop or tray. It is soft, so it can lift small things gently.",
        )
    ],
    "twig": [
        (
            "What can a bent twig do?",
            "A bent twig can work a little like a hook. It can catch or pull something small from a tight place.",
        )
    ],
    "grass": [
        (
            "How can long grass help?",
            "Long grass can be plaited or looped into a soft strap. That lets you pull something without scraping it too hard.",
        )
    ],
    "friendship": [
        (
            "What is friendship?",
            "Friendship is when people or animals care about each other and help each other. A good friend stays kind when something goes wrong.",
        )
    ],
    "plant": [
        (
            "Why do people plant nuts or seeds?",
            "People plant nuts or seeds so they can grow into new plants. A small thing in the soil can become something much bigger later.",
        )
    ],
}
KNOWLEDGE_ORDER = ["walnut", "puddle", "burrow", "briar", "leaf", "twig", "grass", "friendship", "plant"]


def story_qa(world: World) -> list[tuple[str, str]]:
    gunner = world.facts["gunner"]
    friend = world.facts["friend"]
    trouble = world.facts["trouble"]
    method = world.facts["method"]
    walnut = world.facts["walnut"]
    outcome = world.facts["outcome"]

    items = [
        (
            "Who is the story about?",
            f"It is about Gunner Goose and {friend.id}, his friend in the garden. They spend the morning together and face a small problem together.",
        ),
        (
            "What did Gunner and his friend find?",
            "They found a walnut under the cabbages. Gunner thought it looked like a tiny treasure.",
        ),
        (
            "What went wrong with the walnut?",
            f"Gunner tried to carry the walnut by himself, but it slipped away and landed in {trouble.place}. That happened because the shell was smooth and Gunner was marching too proudly to hold it well.",
        ),
        (
            f"How did {friend.id} help?",
            f"{friend.id} {method.qa_text}. {friend.pronoun().capitalize()} stayed calm instead of teasing Gunner, which is why the rescue worked so gently.",
        ),
        (
            "What did Gunner learn?",
            f'Gunner learned that going alone is not always best. He thanked {friend.id} and saw that friendship makes hard moments softer.',
        ),
    ]
    if outcome == "share":
        items.append(
            (
                "How did the story end?",
                f"The friends opened the walnut and shared it together. The ending shows the change clearly, because Gunner stops trying to keep the treasure all to himself.",
            )
        )
    else:
        items.append(
            (
                "How did the story end?",
                f"The walnut shell was too cracked to eat neatly, so the friends planted it together. The ending shows that even a mistake can grow into something hopeful when friends stay kind.",
            )
        )
    if walnut.meters["wet"] >= THRESHOLD:
        items.append(
            (
                "Why was the walnut cold and wet?",
                "It had fallen into a puddle. The water made the rescue feel urgent, because the walnut could not stay there if the friends wanted it back.",
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    trouble = world.facts["trouble"]
    method = world.facts["method"]
    outcome = world.facts["outcome"]

    tags = {"walnut", "friendship"} | set(trouble.tags) | set(method.tags)
    if outcome == "plant":
        tags.add("plant")

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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(trouble="puddle", method="leaf_scoop", friend="pip"),
    StoryParams(trouble="burrow", method="ribbon_loop", friend="dot"),
    StoryParams(trouble="briar", method="grass_loop", friend="moss"),
    StoryParams(trouble="burrow", method="twig_hook", friend="pip"),
    StoryParams(trouble="briar", method="forked_stick", friend="dot"),
]


ASP_RULES = r"""
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
valid(T, M) :- trouble(T), method(M), sensible(M),
               need(T, N), need_m(M, N),
               risk(T, R), power(M, P), P >= R.

cracked :- chosen_trouble(T), chosen_method(M),
           bump(T, B), gentle(M, G), B > G.

outcome(plant) :- cracked.
outcome(share) :- not cracked.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("need", tid, trouble.need))
        lines.append(asp.fact("risk", tid, trouble.risk))
        lines.append(asp.fact("bump", tid, trouble.bump))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("need_m", mid, method.need))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("power", mid, method.power))
        lines.append(asp.fact("gentle", mid, method.gentleness))
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
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_trouble", params.trouble),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sensible = set(asp_sensible())
    python_sensible = {m.id for m in sensible_methods()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible methods match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible methods: clingo={sorted(clingo_sensible)} "
            f"python={sorted(python_sensible)}"
        )

    cases = list(CURATED)
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

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
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(11)))
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True)
        print("OK: smoke test generated and emitted a story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"VERIFY smoke test failed: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: Gunner, a walnut, and a friendship rescue."
    )
    ap.add_argument("--trouble", choices=sorted(TROUBLES))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_combo_rejection(TROUBLES.get(args.trouble or "puddle"), METHODS[args.method]))

    if args.trouble and args.method:
        trouble = TROUBLES[args.trouble]
        method = METHODS[args.method]
        if not suitable_method(trouble, method):
            raise StoryError(explain_combo_rejection(trouble, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.trouble is None or combo[0] == args.trouble)
        and (args.method is None or combo[1] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    trouble_id, method_id = rng.choice(sorted(combos))
    friend_id = args.friend or rng.choice(sorted(FRIENDS))
    return StoryParams(trouble=trouble_id, method=method_id, friend=friend_id)


def generate(params: StoryParams) -> StorySample:
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.friend not in FRIENDS:
        raise StoryError(f"(Unknown friend: {params.friend})")
    trouble = TROUBLES[params.trouble]
    method = METHODS[params.method]
    if not suitable_method(trouble, method):
        raise StoryError(explain_combo_rejection(trouble, method))

    world = tell(trouble=trouble, method=method, friend_cfg=FRIENDS[params.friend])
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (trouble, method) combos:\n")
        for trouble, method in combos:
            print(f"  {trouble:8} {method}")
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
            header = f"### {p.friend} helps Gunner with {p.trouble} using {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
