#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/colon_rhyme_fable.py
===============================================

A standalone storyworld about a young animal at a woodland fair who learns that
a small mark can make a big difference: a colon can open a clear list.

The domain is intentionally tiny and constraint-checked. A seller prepares a
stall sign for a basket, tray, or pot that contains several things. If the sign
is written without a colon, the list runs together, customers hesitate, and the
food begins to cool or wilt. A patient helper teaches the seller to rewrite the
sign with a colon, and the fair goes well again. The prose leans toward a child-
facing fable and uses light rhyme in key beats.

Run it
------
    python storyworlds/worlds/gpt-5.4/colon_rhyme_fable.py
    python storyworlds/worlds/gpt-5.4/colon_rhyme_fable.py --stall soup --tool chalk
    python storyworlds/worlds/gpt-5.4/colon_rhyme_fable.py --stall honey   # rejected
    python storyworlds/worlds/gpt-5.4/colon_rhyme_fable.py --all
    python storyworlds/worlds/gpt-5.4/colon_rhyme_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/colon_rhyme_fable.py --verify
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
CLARITY_MIN = 1
HELP_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "goose"}
        male = {"boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Stall:
    id: str
    label: str
    phrase: str
    items: list[str] = field(default_factory=list)
    keeps: str = "fresh"
    article: str = "a"
    tags: set[str] = field(default_factory=set)

    @property
    def needs_colon(self) -> bool:
        return len(self.items) >= 2


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    clarity: int
    smudge_risk: int
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    animal: str
    title: str
    help_power: int
    lesson_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    stall: str
    tool: str
    helper: str
    seller_name: str
    seller_type: str
    helper_name: str
    weather: str
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


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    sign = world.get("sign")
    stall = world.get("stall")
    seller = world.get("seller")
    if sign.meters["clarity"] >= THRESHOLD:
        return out
    if ("confusion",) in world.fired:
        return out
    world.fired.add(("confusion",))
    stall.meters["waiting"] += 1
    stall.meters["cooling"] += 1
    seller.memes["worry"] += 1
    out.append("__customers_pause__")
    return out


def _r_success(world: World) -> list[str]:
    out: list[str] = []
    sign = world.get("sign")
    stall = world.get("stall")
    seller = world.get("seller")
    if sign.meters["clarity"] < THRESHOLD:
        return out
    if ("success",) in world.fired:
        return out
    world.fired.add(("success",))
    stall.meters["sold"] += 1
    seller.memes["pride"] += 1
    out.append("__customers_buy__")
    return out


CAUSAL_RULES = [
    Rule(name="confusion", tag="social", apply=_r_confusion),
    Rule(name="success", tag="social", apply=_r_success),
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


STALLS = {
    "soup": Stall(
        id="soup",
        label="soup pot",
        phrase="a warm soup pot",
        items=["peas", "beans", "carrots"],
        keeps="warm",
        article="a",
        tags={"soup", "list_food"},
    ),
    "basket": Stall(
        id="basket",
        label="berry basket",
        phrase="a woven berry basket",
        items=["red berries", "blue berries", "blackberries"],
        keeps="fresh",
        article="a",
        tags={"berries", "list_food"},
    ),
    "tray": Stall(
        id="tray",
        label="seed tray",
        phrase="a little seed tray",
        items=["sunflower seeds", "pumpkin seeds", "sesame seeds"],
        keeps="crisp",
        article="a",
        tags={"seeds", "list_food"},
    ),
    "honey": Stall(
        id="honey",
        label="honey jar",
        phrase="a shining honey jar",
        items=["honey"],
        keeps="golden",
        article="a",
        tags={"honey"},
    ),
}

TOOLS = {
    "chalk": Tool(
        id="chalk",
        label="chalk",
        phrase="a stick of blue chalk",
        clarity=1,
        smudge_risk=2,
        tags={"chalk", "writing"},
    ),
    "charcoal": Tool(
        id="charcoal",
        label="charcoal",
        phrase="a soft piece of charcoal",
        clarity=1,
        smudge_risk=1,
        tags={"charcoal", "writing"},
    ),
    "paint": Tool(
        id="paint",
        label="paintbrush",
        phrase="a fine paintbrush",
        clarity=2,
        smudge_risk=0,
        tags={"paintbrush", "writing"},
    ),
}

HELPERS = {
    "owl": HelperKind(
        id="owl",
        animal="owl",
        title="old Owl",
        help_power=2,
        lesson_line="A colon opens a gate for words to walk through in a neat row.",
        tags={"owl", "punctuation"},
    ),
    "beaver": HelperKind(
        id="beaver",
        animal="beaver",
        title="patient Beaver",
        help_power=1,
        lesson_line="A tidy sign helps hungry feet know where to stop.",
        tags={"beaver", "punctuation"},
    ),
    "tortoise": HelperKind(
        id="tortoise",
        animal="tortoise",
        title="steady Tortoise",
        help_power=2,
        lesson_line="Slow marks can still be wise marks when each one has a place.",
        tags={"tortoise", "punctuation"},
    ),
}

SELLERS = {
    "mouse": ["Mimi", "Moss", "Milo"],
    "sparrow": ["Pip", "Pia", "Peep"],
    "rabbit": ["Nell", "Nib", "Poppy"],
}

WEATHERS = {
    "sunny": "The fair leaves shone in the sun.",
    "breezy": "A small breeze skipped between the stalls.",
    "misty": "A cool mist curled around the mossy path.",
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for stall_id, stall in STALLS.items():
        if not stall.needs_colon:
            continue
        for tool_id in TOOLS:
            for helper_id, helper in HELPERS.items():
                if helper.help_power >= HELP_MIN and TOOLS[tool_id].clarity >= CLARITY_MIN:
                    combos.append((stall_id, tool_id, helper_id))
    return combos


def reason_needs_colon(stall: Stall) -> bool:
    return stall.needs_colon


def predict_market(world: World, use_colon: bool) -> dict:
    sim = world.copy()
    sign = sim.get("sign")
    if use_colon:
        sign.meters["clarity"] += 1
    propagate(sim, narrate=False)
    return {
        "clarity": sign.meters["clarity"],
        "waiting": sim.get("stall").meters["waiting"],
        "cooling": sim.get("stall").meters["cooling"],
        "sold": sim.get("stall").meters["sold"],
    }


def item_list_text(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def sloppy_list_text(items: list[str]) -> str:
    return " ".join(items)


def opening(world: World, seller: Entity, stall_cfg: Stall, weather: str) -> None:
    world.say(
        f"In a ferny clearing, {seller.id} the {seller.type} set out {stall_cfg.phrase} for the woodland fair."
    )
    world.say(WEATHERS[weather])
    world.say(
        f"{seller.pronoun('possessive').capitalize()} little heart beat quick with hope. "
        f'"If I sell well, I shall ring the bell; if I write clear, friends will draw near," '
        f"{seller.pronoun()} hummed."
    )


def arrange_goods(world: World, seller: Entity, stall_cfg: Stall) -> None:
    stall = world.get("stall")
    stall.meters["ready"] += 1
    world.say(
        f"Inside were {item_list_text(stall_cfg.items)}. They smelled {stall_cfg.keeps}, and every color looked fair and bright."
    )


def first_sign(world: World, seller: Entity, stall_cfg: Stall, tool: Tool) -> None:
    sign = world.get("sign")
    sign.attrs["first_line"] = f"{stall_cfg.label} {sloppy_list_text(stall_cfg.items)}"
    sign.meters["smudged"] += float(tool.smudge_risk)
    world.say(
        f"{seller.id} picked up {tool.phrase} and hurried over a board. "
        f'{seller.pronoun().capitalize()} wrote, "{stall_cfg.label} {sloppy_list_text(stall_cfg.items)}."'
    )
    world.say(
        "The words all leaned together in one busy string. There was no colon to open the list and no neat pause for the eye."
    )


def customers_pause(world: World, seller: Entity, stall_cfg: Stall) -> None:
    seller.memes["embarrassment"] += 1
    world.say(
        f"Soon a hedgehog, a wren, and a mole stopped in front of {stall_cfg.article} {stall_cfg.label} and tilted their heads."
    )
    world.say(
        '"Is this one thing or many things?" asked the mole. "I cannot quite tell," said the wren.'
    )
    world.say(
        f"{seller.id} saw the line slow down. Warm things would cool, fresh things would wilt, and worry sat where pride had sat."
    )


def helper_arrives(world: World, seller: Entity, helper: Entity, helper_cfg: HelperKind) -> None:
    seller.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Just then {helper.id}, {helper_cfg.title}, came by with calm steps and kinder eyes."
    )
    world.say(
        f'"Little friend," said {helper.id}, "{helper_cfg.lesson_line}"'
    )


def rewrite_sign(world: World, seller: Entity, stall_cfg: Stall, tool: Tool) -> None:
    sign = world.get("sign")
    sign.meters["clarity"] = float(tool.clarity)
    sign.attrs["final_line"] = f"{stall_cfg.label}: {item_list_text(stall_cfg.items)}"
    world.say(
        f'Together they rewrote the board: "{stall_cfg.label}: {item_list_text(stall_cfg.items)}."'
    )
    if tool.smudge_risk > 0:
        world.say(
            "The new line was simple enough that even the soft smudge could not hide its meaning."
        )
    else:
        world.say(
            "The clean marks stood still and clear, and the list looked glad to be understood."
        )


def market_recovers(world: World, seller: Entity, stall_cfg: Stall) -> None:
    seller.memes["relief"] += 1
    world.say(
        f"Now the waiting feet stepped forward. Buyers could see at once what lived in the {stall_cfg.label}, and coins clinked into the bowl."
    )
    world.say(
        f'{seller.id} laughed, "Near and clear, that is the way; a tiny mark can guide the day."'
    )


def moral_close(world: World, seller: Entity, helper: Entity, stall_cfg: Stall) -> None:
    seller.memes["lesson"] += 1
    world.say(
        f"When the sun bent low, {seller.id} shared the last spoonfuls and seeds with {helper.id}."
    )
    world.say(
        f"From that day on, {seller.pronoun()} never scorned small marks again. In fables as in forests, a little colon can carry a long train."
    )
    world.say("Moral: Small signs may be small in size, but clear signs make wise eyes.")


def tell(
    stall_cfg: Stall,
    tool_cfg: Tool,
    helper_cfg: HelperKind,
    seller_name: str,
    seller_type: str,
    helper_name: str,
    weather: str,
) -> World:
    world = World()
    seller = world.add(Entity(
        id=seller_name,
        kind="character",
        type=seller_type,
        role="seller",
        label=seller_type,
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_cfg.animal,
        role="helper",
        label=helper_cfg.animal,
    ))
    stall = world.add(Entity(
        id="stall",
        kind="thing",
        type="stall",
        label=stall_cfg.label,
        phrase=stall_cfg.phrase,
        tags=set(stall_cfg.tags),
    ))
    sign = world.add(Entity(
        id="sign",
        kind="thing",
        type="sign",
        label="sign",
        phrase="a little board sign",
        tags={"sign"},
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool_cfg.label,
        phrase=tool_cfg.phrase,
        tags=set(tool_cfg.tags),
    ))

    opening(world, seller, stall_cfg, weather)
    arrange_goods(world, seller, stall_cfg)

    world.para()
    first_sign(world, seller, stall_cfg, tool_cfg)
    propagate(world, narrate=False)
    customers_pause(world, seller, stall_cfg)

    world.para()
    helper_arrives(world, seller, helper, helper_cfg)
    before = predict_market(world, use_colon=False)
    after = predict_market(world, use_colon=True)
    world.facts["predicted_before"] = before
    world.facts["predicted_after"] = after
    rewrite_sign(world, seller, stall_cfg, tool_cfg)
    propagate(world, narrate=False)
    market_recovers(world, seller, stall_cfg)

    world.para()
    moral_close(world, seller, helper, stall_cfg)

    world.facts.update(
        seller=seller,
        helper=helper,
        stall_cfg=stall_cfg,
        tool_cfg=tool_cfg,
        weather=weather,
        sign=sign,
        tool=tool,
        waited=world.get("stall").meters["waiting"] >= THRESHOLD,
        sold=world.get("stall").meters["sold"] >= THRESHOLD,
        lesson=seller.memes["lesson"] >= THRESHOLD,
        first_line=sign.attrs.get("first_line", ""),
        final_line=sign.attrs.get("final_line", ""),
    )
    return world


KNOWLEDGE = {
    "colon": [(
        "What is a colon?",
        "A colon is a punctuation mark made of two dots, one above the other. It often comes before a list to show that the list is about to begin."
    )],
    "sign": [(
        "Why do signs need to be clear?",
        "A clear sign helps readers know what something means right away. When words are easy to read, people do not have to guess."
    )],
    "list": [(
        "What is a list?",
        "A list is a group of words or items written one after another because they belong together. A colon can help open the list and make that grouping clear."
    )],
    "owl": [(
        "Why are owls often shown as wise in fables?",
        "Fables often use animals to stand for ideas, and owls are commonly used to show patience and wisdom. The animal stands for the lesson, not for every real owl."
    )],
    "beaver": [(
        "Why might a beaver fit a story about tidy work?",
        "Beavers are often pictured as careful builders in stories. That makes them a good fable helper when a lesson is about neat, useful work."
    )],
    "tortoise": [(
        "Why is a tortoise a good helper in a patient story?",
        "A tortoise is often used in fables to show steady patience. Slow, careful help can solve a problem better than rushing."
    )],
    "chalk": [(
        "What is chalk used for?",
        "Chalk is used for writing or drawing on boards and stones. It can rub away or smudge, so clear writing matters even more."
    )],
    "charcoal": [(
        "What is charcoal?",
        "Charcoal is a black drawing stick made from burned wood. It can make dark marks that are easy to see."
    )],
    "paintbrush": [(
        "What does a paintbrush do?",
        "A paintbrush carries paint so a person can make smooth marks and pictures. It can help a sign look neat and easy to read."
    )],
    "fable": [(
        "What is a fable?",
        "A fable is a short story that often uses animals or simple characters to teach a lesson. Many fables end with a moral."
    )],
}
KNOWLEDGE_ORDER = [
    "colon",
    "sign",
    "list",
    "owl",
    "beaver",
    "tortoise",
    "chalk",
    "charcoal",
    "paintbrush",
    "fable",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seller = f["seller"]
    stall_cfg = f["stall_cfg"]
    helper = f["helper"]
    return [
        f'Write a short fable for a young child that includes the word "colon" and a light rhyme.',
        f"Tell a woodland market story where {seller.id} the {seller.type} writes an unclear sign for a {stall_cfg.label}, then learns to fix it with a colon.",
        f"Write a gentle animal fable in which {helper.id} teaches that a small punctuation mark can make a big difference.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seller = f["seller"]
    helper = f["helper"]
    stall_cfg = f["stall_cfg"]
    tool_cfg = f["tool_cfg"]
    before = f["predicted_before"]
    after = f["predicted_after"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {seller.id} the {seller.type}, who ran a fair stall, and {helper.id}, who stopped to help. The story follows how they turned a confusing sign into a clear one."
        ),
        (
            f"What was in the {stall_cfg.label}?",
            f"It held {item_list_text(stall_cfg.items)}. Those several items are exactly why the sign needed a colon before the list."
        ),
        (
            f"What did {seller.id} do wrong at first?",
            f"{seller.id} wrote all the words in one crowded line without a colon. That made the list run together, so readers could not tell quickly what was being sold."
        ),
        (
            "Why did the customers pause?",
            f"They paused because the sign was unclear, not because the food looked bad. In the world model, the unclear sign raised waiting and worry, while a clear sign would have let buying start sooner."
        ),
        (
            f"How did {helper.id} help?",
            f"{helper.id} explained that the list needed a colon and helped rewrite the board. After that change, the sign became clear enough for customers to understand at a glance."
        ),
        (
            "What changed after the sign was rewritten?",
            f"Before the fix, the predicted result was waiting={int(before['waiting'])} and sold={int(before['sold'])}. After the fix, the predicted result became waiting={int(after['waiting'])} and sold={int(after['sold'])}, showing that the clear sign helped the stall recover."
        ),
        (
            "What is the moral of the story?",
            "The moral is that small marks matter when they make meaning clear. A careful little fix can help many others at once."
        ),
    ]
    if tool_cfg.id == "chalk":
        qa.append((
            "Did the chalk cause all the trouble?",
            "Not all by itself. The real problem was leaving out the colon, though the soft chalk made neat writing even more important."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"colon", "sign", "list", "fable"}
    tags |= set(f["tool_cfg"].tags)
    tags |= set(HELPERS[f["helper"].type if f["helper"].type in HELPERS else f["helper"].attrs.get("kind", "")].tags) if False else set()
    helper_cfg = f["helper"]
    if helper_cfg.type == "owl":
        tags.add("owl")
    elif helper_cfg.type == "beaver":
        tags.add("beaver")
    elif helper_cfg.type == "tortoise":
        tags.add("tortoise")
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        stall="soup",
        tool="chalk",
        helper="owl",
        seller_name="Mimi",
        seller_type="mouse",
        helper_name="Olwen",
        weather="breezy",
    ),
    StoryParams(
        stall="basket",
        tool="paint",
        helper="tortoise",
        seller_name="Pip",
        seller_type="sparrow",
        helper_name="Toma",
        weather="sunny",
    ),
    StoryParams(
        stall="tray",
        tool="charcoal",
        helper="beaver",
        seller_name="Nib",
        seller_type="rabbit",
        helper_name="Bram",
        weather="misty",
    ),
]


def explain_rejection(stall_cfg: Stall) -> str:
    return (
        f"(No story: {stall_cfg.phrase} holds only {item_list_text(stall_cfg.items)}, "
        "so there is no real list to open with a colon. Pick a stall with several items.)"
    )


ASP_RULES = r"""
needs_colon(S) :- stall(S), item_count(S, N), N >= 2.
valid(S, T, H) :- stall(S), tool(T), helper(H), needs_colon(S),
                  clarity(T, C), clarity_min(M), C >= M,
                  help_power(H, P), help_min(HM), P >= HM.

pred_waiting(1) :- chosen_stall(S), not chosen_colon, needs_colon(S).
pred_waiting(0) :- chosen_stall(S), chosen_colon, needs_colon(S).

pred_sold(0) :- chosen_stall(S), not chosen_colon, needs_colon(S).
pred_sold(1) :- chosen_stall(S), chosen_colon, needs_colon(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for stall_id, stall in STALLS.items():
        lines.append(asp.fact("stall", stall_id))
        lines.append(asp.fact("item_count", stall_id, len(stall.items)))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("clarity", tool_id, tool.clarity))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("help_power", helper_id, helper.help_power))
    lines.append(asp.fact("clarity_min", CLARITY_MIN))
    lines.append(asp.fact("help_min", HELP_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_predict_waiting(stall_id: str, use_colon: bool) -> int:
    import asp
    extra = [asp.fact("chosen_stall", stall_id)]
    if use_colon:
        extra.append("chosen_colon.")
    model = asp.one_model(asp_program("\n".join(extra), "#show pred_waiting/1."))
    atoms = asp.atoms(model, "pred_waiting")
    return int(atoms[0][0]) if atoms else -1


def asp_predict_sold(stall_id: str, use_colon: bool) -> int:
    import asp
    extra = [asp.fact("chosen_stall", stall_id)]
    if use_colon:
        extra.append("chosen_colon.")
    model = asp.one_model(asp_program("\n".join(extra), "#show pred_sold/1."))
    atoms = asp.atoms(model, "pred_sold")
    return int(atoms[0][0]) if atoms else -1


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

    for stall_id, _, _ in sorted(python_set)[:3]:
        py_before = 1 if reason_needs_colon(STALLS[stall_id]) else 0
        py_after = 1 if reason_needs_colon(STALLS[stall_id]) else 0
        if asp_predict_waiting(stall_id, False) != py_before:
            rc = 1
            print(f"MISMATCH waiting-before on {stall_id}")
        if asp_predict_sold(stall_id, True) != py_after:
            rc = 1
            print(f"MISMATCH sold-after on {stall_id}")

    try:
        params = CURATED[0]
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a woodland seller learns what a colon can do."
    )
    ap.add_argument("--stall", choices=STALLS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--seller-type", choices=sorted(SELLERS))
    ap.add_argument("--seller-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--weather", choices=sorted(WEATHERS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.stall:
        stall_cfg = STALLS.get(args.stall)
        if stall_cfg is None:
            raise StoryError(f"(Unknown stall: {args.stall})")
        if not reason_needs_colon(stall_cfg):
            raise StoryError(explain_rejection(stall_cfg))
    combos = [
        combo for combo in valid_combos()
        if (args.stall is None or combo[0] == args.stall)
        and (args.tool is None or combo[1] == args.tool)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    stall_id, tool_id, helper_id = rng.choice(sorted(combos))
    seller_type = args.seller_type or rng.choice(sorted(SELLERS))
    seller_name = args.seller_name or rng.choice(SELLERS[seller_type])
    helper_name = args.helper_name or rng.choice(
        [name for name in ["Olwen", "Bram", "Toma", "Ivy", "Rowan", "Fern"] if name != seller_name]
    )
    weather = args.weather or rng.choice(sorted(WEATHERS))
    return StoryParams(
        stall=stall_id,
        tool=tool_id,
        helper=helper_id,
        seller_name=seller_name,
        seller_type=seller_type,
        helper_name=helper_name,
        weather=weather,
    )


def generate(params: StoryParams) -> StorySample:
    stall_cfg = STALLS.get(params.stall)
    tool_cfg = TOOLS.get(params.tool)
    helper_cfg = HELPERS.get(params.helper)
    if stall_cfg is None or tool_cfg is None or helper_cfg is None:
        raise StoryError("(Invalid params: unknown registry key.)")
    if not reason_needs_colon(stall_cfg):
        raise StoryError(explain_rejection(stall_cfg))

    world = tell(
        stall_cfg=stall_cfg,
        tool_cfg=tool_cfg,
        helper_cfg=helper_cfg,
        seller_name=params.seller_name,
        seller_type=params.seller_type,
        helper_name=params.helper_name,
        weather=params.weather,
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
        print(asp_program("", "#show valid/3.\n#show pred_waiting/1.\n#show pred_sold/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (stall, tool, helper) combos:\n")
        for stall_id, tool_id, helper_id in combos:
            print(f"  {stall_id:8} {tool_id:8} {helper_id}")
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
            header = f"### {p.seller_name}: {p.stall} with {p.tool} and {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
