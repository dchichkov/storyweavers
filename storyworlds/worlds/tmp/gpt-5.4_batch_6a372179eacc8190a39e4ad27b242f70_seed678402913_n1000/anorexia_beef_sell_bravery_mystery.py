#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/anorexia_beef_sell_bravery_mystery.py
================================================================

A standalone storyworld about a small farm mystery: on market morning, a child
and an adult plan to sell something made with beef, but a frail calf has gone
missing. The calf has stopped eating -- the vet has called it animal anorexia --
so the mystery matters at once. A child follows a clue into a dim hiding place,
and bravery decides whether the child goes in first or calls the adult from the
doorway.

The world model is intentionally small and state-driven:
- clues point to plausible hiding places
- places afford only some hiding places
- each hiding place needs the right search tool
- bravery compared to darkness determines the turn

Run it
------
python storyworlds/worlds/gpt-5.4/anorexia_beef_sell_bravery_mystery.py
python storyworlds/worlds/gpt-5.4/anorexia_beef_sell_bravery_mystery.py --all
python storyworlds/worlds/gpt-5.4/anorexia_beef_sell_bravery_mystery.py --qa --seed 7
python storyworlds/worlds/gpt-5.4/anorexia_beef_sell_bravery_mystery.py --trace
python storyworlds/worlds/gpt-5.4/anorexia_beef_sell_bravery_mystery.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    weather: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    text: str
    points_to: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingSpot:
    id: str
    label: str
    phrase: str
    darkness: int = 1
    needs: set[str] = field(default_factory=set)
    clue_tags: set[str] = field(default_factory=set)
    risk_text: str = ""
    found_text: str = ""
    rescue_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    covers: set[str] = field(default_factory=set)
    use_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class MarketPlan:
    id: str
    label: str
    text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    clue: str
    hiding: str
    tool: str
    plan: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_type: str
    bravery: str
    calf_name: str
    seed: Optional[int] = None


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


def _r_weak_calf(world: World) -> list[str]:
    calf = world.entities.get("calf")
    if calf is None:
        return []
    if calf.meters["missed_meal"] < THRESHOLD:
        return []
    sig = ("weak", calf.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    calf.meters["weak"] += 1
    calf.memes["fear"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    calf = world.entities.get("calf")
    child = world.entities.get("child")
    adult = world.entities.get("adult")
    if calf is None or child is None or adult is None:
        return []
    if calf.meters["found"] < THRESHOLD:
        return []
    sig = ("relief", calf.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    calf.memes["relief"] += 1
    child.memes["relief"] += 1
    adult.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="weak_calf", tag="physical", apply=_r_weak_calf),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
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
            world.say(bit)
    return produced


SETTINGS = {
    "foggy_farm": Setting(
        id="foggy_farm",
        place="the hill farm",
        mood="Fog lay low over the pens and made every fence post look secret.",
        weather="misty",
        affords={"hay_loft", "old_stall"},
        tags={"farm", "fog"},
    ),
    "market_yard": Setting(
        id="market_yard",
        place="the market yard behind the barn",
        mood="The yard was busy, but the corners under the eaves still held shadows.",
        weather="cool",
        affords={"old_stall", "wagon_shed"},
        tags={"market", "shadow"},
    ),
    "orchard_barn": Setting(
        id="orchard_barn",
        place="the orchard barn",
        mood="Leaves clicked outside, and the barn sounded bigger than it looked.",
        weather="breezy",
        affords={"hay_loft", "wagon_shed"},
        tags={"barn", "orchard"},
    ),
}

CLUES = {
    "hoofprints": Clue(
        id="hoofprints",
        label="small hoofprints",
        text="In the damp dust, small hoofprints curved away from the feed bucket.",
        points_to={"hay_loft", "old_stall"},
        tags={"tracks", "mystery"},
    ),
    "bell": Clue(
        id="bell",
        label="a faint bell",
        text="Somewhere in the hush, a calf bell gave one thin jingle and then went quiet.",
        points_to={"hay_loft", "wagon_shed"},
        tags={"sound", "mystery"},
    ),
    "spilled_feed": Clue(
        id="spilled_feed",
        label="a trail of feed",
        text="A trail of dry feed peeped past the door, like crumbs in a puzzle.",
        points_to={"old_stall", "wagon_shed"},
        tags={"feed", "mystery"},
    ),
}

HIDING_SPOTS = {
    "hay_loft": HidingSpot(
        id="hay_loft",
        label="hay loft",
        phrase="the hay loft above the big beams",
        darkness=3,
        needs={"light", "climb"},
        clue_tags={"hoofprints", "bell"},
        risk_text="The ladder shook a little, and the loft was deep with shadow.",
        found_text="curled behind a stack of hay, with one hoof caught in loose baling twine",
        rescue_text="held the light steady while the twine was slipped free",
        tags={"loft", "dark"},
    ),
    "old_stall": HidingSpot(
        id="old_stall",
        label="old stall",
        phrase="the old stall at the far end of the barn",
        darkness=2,
        needs={"light"},
        clue_tags={"hoofprints", "spilled_feed"},
        risk_text="The door stood half shut, and the gap beyond it looked gray and still.",
        found_text="pressed into the straw behind the trough, too weak and worried to come out",
        rescue_text="lifted the lantern and spoke softly until the calf stepped forward",
        tags={"stall", "dark"},
    ),
    "wagon_shed": HidingSpot(
        id="wagon_shed",
        label="wagon shed",
        phrase="the wagon shed behind the market cart",
        darkness=1,
        needs={"light", "reach"},
        clue_tags={"bell", "spilled_feed"},
        risk_text="Dusty wheels made little caves of shade under the shed roof.",
        found_text="standing beside an axle, with the lead rope looped tight around a spoke",
        rescue_text="helped reach the knot so the rope could be loosened",
        tags={"shed", "rope"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a brass lantern",
        covers={"light"},
        use_text="Its gold circle of light pushed the shadows back.",
        tags={"light"},
    ),
    "ladder_lantern": Tool(
        id="ladder_lantern",
        label="hook lantern",
        phrase="a hook lantern with a shoulder strap",
        covers={"light", "climb"},
        use_text="It left one hand free for the ladder while the light swung ahead.",
        tags={"light", "ladder"},
    ),
    "crook_lantern": Tool(
        id="crook_lantern",
        label="crook and lantern",
        phrase="a lantern and the lamb crook",
        covers={"light", "reach"},
        use_text="The light showed the knot, and the crook reached what small fingers could not.",
        tags={"light", "reach"},
    ),
}

PLANS = {
    "pies": MarketPlan(
        id="pies",
        label="beef pies",
        text="At dawn, they were meant to sell beef pies at the village market.",
        tags={"beef", "sell", "market"},
    ),
    "stew": MarketPlan(
        id="stew",
        label="beef stew",
        text="At dawn, they were meant to sell jars of beef stew at the village market.",
        tags={"beef", "sell", "market"},
    ),
    "sandwiches": MarketPlan(
        id="sandwiches",
        label="beef sandwiches",
        text="At dawn, they were meant to sell hot beef sandwiches at the village market.",
        tags={"beef", "sell", "market"},
    ),
}

BRAVERY_SCORES = {"hesitant": 1, "steady": 2, "bold": 3}

GIRL_NAMES = ["Mira", "Nora", "Lila", "Tess", "Ivy", "June"]
BOY_NAMES = ["Owen", "Eli", "Max", "Theo", "Finn", "Jude"]
CALF_NAMES = ["Clover", "Maple", "Pip", "Bramble", "Daisy", "Moss"]


def valid_combo(setting_id: str, clue_id: str, hiding_id: str, tool_id: str) -> bool:
    setting = SETTINGS[setting_id]
    clue = CLUES[clue_id]
    hiding = HIDING_SPOTS[hiding_id]
    tool = TOOLS[tool_id]
    if hiding_id not in setting.affords:
        return False
    if hiding_id not in clue.points_to:
        return False
    return hiding.needs.issubset(tool.covers)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for clue_id in CLUES:
            for hiding_id in HIDING_SPOTS:
                for tool_id in TOOLS:
                    if valid_combo(setting_id, clue_id, hiding_id, tool_id):
                        combos.append((setting_id, clue_id, hiding_id, tool_id))
    return combos


def bravery_enough(bravery: str, hiding: HidingSpot) -> bool:
    return BRAVERY_SCORES[bravery] >= hiding.darkness


def predict_search(world: World, bravery: str, hiding_id: str) -> dict:
    sim = world.copy()
    calf = sim.get("calf")
    calf.meters["missing"] += 1
    calf.meters["missed_meal"] += 1
    propagate(sim, narrate=False)
    direct = bravery_enough(bravery, HIDING_SPOTS[hiding_id])
    return {"direct": direct, "weak": calf.meters["weak"] >= THRESHOLD}


def introduce(world: World, child: Entity, adult: Entity, plan: MarketPlan) -> None:
    world.say(
        f"Before the sun had burned the mist away, {child.id} helped {adult.id} in {world.setting.place}. "
        f"{plan.text}"
    )
    world.say(world.setting.mood)


def calf_setup(world: World, child: Entity, adult: Entity, calf: Entity) -> None:
    calf.meters["missed_meal"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {child.id} kept glancing at {calf.id}, the small brown calf in the corner pen. "
        f"The vet had used the hard word \"anorexia\" for animals, meaning {calf.id} had stopped eating and was growing weak."
    )
    world.say(
        f"{adult.id} had left a warm pail of mash by the gate, hoping the smell might tempt {calf.pronoun('object')}."
    )


def disappearance(world: World, child: Entity, adult: Entity, calf: Entity, clue: Clue) -> None:
    calf.meters["missing"] += 1
    world.say(
        f"When {child.id} came back with a clean cloth, the pail was untouched and {calf.id} was gone."
    )
    world.say(
        f'"Stay close," {adult.id} said, looking under the rails. But the yard had gone oddly quiet.'
    )
    world.say(clue.text)


def warning(world: World, child: Entity, adult: Entity, hiding: HidingSpot, tool: Tool, bravery: str) -> None:
    pred = predict_search(world, bravery, hiding.id)
    child.memes["curiosity"] += 1
    world.facts["predicted_direct"] = pred["direct"]
    world.facts["predicted_weak"] = pred["weak"]
    world.say(
        f'{child.id} lifted {tool.phrase}. {tool.use_text}'
    )
    world.say(
        f"{hiding.risk_text}"
    )


def choose_search(world: World, child: Entity, adult: Entity, hiding: HidingSpot, bravery: str) -> str:
    child.memes["bravery"] = float(BRAVERY_SCORES[bravery])
    if bravery_enough(bravery, hiding):
        child.memes["courage"] += 1
        world.say(
            f'{child.id} swallowed once, then said, "I am scared, but I can go a little way."'
        )
        world.say(
            f"Step by careful step, {child.pronoun()} went toward {hiding.phrase} first, with {adult.id} close behind."
        )
        return "direct"
    child.memes["prudence"] += 1
    world.say(
        f'{child.id} felt the dark press close and stopped at the doorway. "{adult.id}, please come with me," {child.pronoun()} whispered.'
    )
    world.say(
        f"That was brave too, because {child.pronoun()} did not hide the fear or run from the clue."
    )
    return "calls_help"


def discover(world: World, child: Entity, adult: Entity, calf: Entity, hiding: HidingSpot) -> None:
    calf.meters["found"] += 1
    calf.meters["trapped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"There, in {hiding.phrase}, was {calf.id}, {hiding.found_text}."
    )
    world.say(
        f'{child.id} gasped. "That is why the clue stopped here."'
    )


def rescue(world: World, child: Entity, adult: Entity, calf: Entity, hiding: HidingSpot) -> None:
    calf.meters["trapped"] = 0.0
    calf.meters["safe"] += 1
    calf.meters["eating"] += 1
    calf.memes["fear"] = 0.0
    child.memes["relief"] += 1
    adult.memes["care"] += 1
    world.say(
        f"Together they moved slowly. {child.id} {hiding.rescue_text}, and {adult.id} eased {calf.id} free."
    )
    world.say(
        f"Back in the light, {calf.id} nosed the warm mash and finally took a few small bites."
    )


def resolution(world: World, child: Entity, adult: Entity, calf: Entity, plan: MarketPlan) -> None:
    adult.memes["decision"] += 1
    world.say(
        f'{adult.id} let out a long breath. "We will not sell {plan.label} first thing today," {adult.pronoun()} said. "Caring for {calf.id} comes first."'
    )
    world.say(
        f"{child.id} stroked {calf.id}'s neck and watched the little jaw work. The mystery was over, and the bravest sound in the barn was the quiet munching at last."
    )


def tell(
    setting: Setting,
    clue: Clue,
    hiding: HidingSpot,
    tool: Tool,
    plan: MarketPlan,
    child_name: str = "Mira",
    child_gender: str = "girl",
    adult_name: str = "Aunt June",
    adult_type: str = "aunt",
    bravery: str = "steady",
    calf_name: str = "Clover",
) -> World:
    world = World(setting=setting)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label=adult_name, role="adult"))
    calf = world.add(Entity(id="calf", kind="thing", type="calf", label=calf_name, role="calf"))

    world.facts["child_name"] = child_name
    world.facts["adult_name"] = adult_name
    world.facts["calf_name"] = calf_name

    introduce(world, child, adult, plan)
    calf_setup(world, child, adult, calf)

    world.para()
    disappearance(world, child, adult, calf, clue)
    warning(world, child, adult, hiding, tool, bravery)
    path = choose_search(world, child, adult, hiding, bravery)

    world.para()
    discover(world, child, adult, calf, hiding)
    rescue(world, child, adult, calf, hiding)

    world.para()
    resolution(world, child, adult, calf, plan)

    world.facts.update(
        child=child,
        adult=adult,
        calf=calf,
        setting=setting,
        clue=clue,
        hiding=hiding,
        tool=tool,
        plan=plan,
        bravery=bravery,
        search_path=path,
        direct=(path == "direct"),
        rescued=(calf.meters["safe"] >= THRESHOLD),
    )
    return world


KNOWLEDGE = {
    "anorexia": [(
        "What does anorexia mean in this story?",
        "In this story, the word anorexia is used the way a vet might use it for an animal that has stopped eating. It tells us the calf was weak and needed care right away."
    )],
    "beef": [(
        "What is beef?",
        "Beef is meat that comes from cattle. In the story, the market food was made with beef."
    )],
    "sell": [(
        "What does sell mean?",
        "To sell means to give something to a buyer in exchange for money. The grown-up planned to sell food at the market."
    )],
    "clue": [(
        "What is a clue?",
        "A clue is a small sign that helps you solve a puzzle or mystery. A clue can be a sound, a track, or a trail."
    )],
    "bravery": [(
        "What is bravery?",
        "Bravery means doing the right thing even when you feel scared. Sometimes bravery means going forward carefully, and sometimes it means asking for help out loud."
    )],
    "lantern": [(
        "Why is a lantern helpful in a dark place?",
        "A lantern makes a steady light so you can see safely. In a mystery, light helps turn shadows into useful facts."
    )],
    "market": [(
        "What is a market?",
        "A market is a place where people bring things to buy and sell. Farmers and cooks might carry food there in the morning."
    )],
}
KNOWLEDGE_ORDER = ["anorexia", "beef", "sell", "clue", "bravery", "lantern", "market"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child_name = f["child_name"]
    adult_name = f["adult_name"]
    calf_name = f["calf_name"]
    plan = f["plan"]
    hiding = f["hiding"]
    clue = f["clue"]
    bravery = f["bravery"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old that includes the words "anorexia", "beef", and "sell".',
        f"Tell a farm mystery where {child_name} notices {clue.label}, finds a missing calf named {calf_name}, and bravery matters in the search.",
        f"Write a short mystery in which {adult_name} plans to sell {plan.label}, but the real problem is hidden in {hiding.label}, and the ending image shows what changed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    calf = f["calf"]
    clue = f["clue"]
    hiding = f["hiding"]
    tool = f["tool"]
    plan = f["plan"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {f['child_name']}, {f['adult_name']}, and a calf named {f['calf_name']}. They begin the day thinking about the market, but the missing calf becomes the real center of the story."
        ),
        (
            "What made the morning feel like a mystery?",
            f"The mash was untouched, the calf was missing, and {clue.label} appeared where no one expected it. Those details turned an ordinary farm morning into a puzzle to solve."
        ),
        (
            f"Why did the calf's anorexia matter in the story?",
            f"It meant {f['calf_name']} had stopped eating and was already weak. Because of that, the search had to happen quickly, not just curiously."
        ),
        (
            f"What clue helped them search for {f['calf_name']}?",
            f"The clue was {clue.label}. It mattered because it pointed them toward {hiding.phrase} instead of letting them waste time looking everywhere."
        ),
    ]
    if f["direct"]:
        qa.append((
            f"How did bravery change what {f['child_name']} did?",
            f"{f['child_name']} felt afraid but still went toward {hiding.phrase} first with {tool.phrase}. The brave choice made the rescue start quickly, before the calf grew weaker."
        ))
    else:
        qa.append((
            f"How was {f['child_name']} brave even without going in alone?",
            f"{f['child_name']} stopped at the dark place and called {f['adult_name']} instead of pretending not to be scared. That was brave because asking for help was the safest honest thing to do."
        ))
    qa.append((
        f"Why did {f['adult_name']} decide not to sell {plan.label} right away?",
        f"{f['adult_name']} saw that {f['calf_name']} needed care more than the market needed food. The ending proves the choice mattered, because the calf finally began to eat."
    ))
    qa.append((
        "How did the story end?",
        f"It ended with the mystery solved and the calf safe in the light. The last change we can see is {f['calf_name']} quietly eating warm mash."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"anorexia", "beef", "sell", "clue", "bravery", "market"}
    if "light" in world.facts["tool"].covers:
        tags.add("lantern")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="foggy_farm",
        clue="bell",
        hiding="hay_loft",
        tool="ladder_lantern",
        plan="pies",
        child_name="Mira",
        child_gender="girl",
        adult_name="Aunt June",
        adult_type="aunt",
        bravery="bold",
        calf_name="Clover",
    ),
    StoryParams(
        setting="market_yard",
        clue="spilled_feed",
        hiding="wagon_shed",
        tool="crook_lantern",
        plan="stew",
        child_name="Owen",
        child_gender="boy",
        adult_name="Uncle Reed",
        adult_type="uncle",
        bravery="steady",
        calf_name="Maple",
    ),
    StoryParams(
        setting="foggy_farm",
        clue="hoofprints",
        hiding="old_stall",
        tool="lantern",
        plan="sandwiches",
        child_name="Lila",
        child_gender="girl",
        adult_name="Dad Rowan",
        adult_type="father",
        bravery="steady",
        calf_name="Pip",
    ),
    StoryParams(
        setting="orchard_barn",
        clue="bell",
        hiding="wagon_shed",
        tool="crook_lantern",
        plan="pies",
        child_name="Finn",
        child_gender="boy",
        adult_name="Mom Elsie",
        adult_type="mother",
        bravery="hesitant",
        calf_name="Bramble",
    ),
]


def explain_rejection(setting_id: str, clue_id: str, hiding_id: str, tool_id: str) -> str:
    if hiding_id not in SETTINGS[setting_id].affords:
        return (
            f"(No story: {HIDING_SPOTS[hiding_id].label} does not belong in {SETTINGS[setting_id].place}. "
            f"Pick a hiding place the setting actually affords.)"
        )
    if hiding_id not in CLUES[clue_id].points_to:
        return (
            f"(No story: {CLUES[clue_id].label} would not honestly point to {HIDING_SPOTS[hiding_id].label}. "
            f"A mystery clue must lead somewhere plausible.)"
        )
    missing = sorted(HIDING_SPOTS[hiding_id].needs - TOOLS[tool_id].covers)
    return (
        f"(No story: {TOOLS[tool_id].label} cannot handle {HIDING_SPOTS[hiding_id].label}. "
        f"It is missing {missing}, so the search would not make sense.)"
    )


def outcome_of(params: StoryParams) -> str:
    hiding = HIDING_SPOTS[params.hiding]
    return "direct" if bravery_enough(params.bravery, hiding) else "calls_help"


ASP_RULES = r"""
% A place may host only its afforded hiding spots.
valid_place(S, H) :- affords(S, H).

% A clue is good only if it points to the hiding place.
valid_clue(C, H) :- points_to(C, H).

% A tool works only if it covers every need of the hiding place.
missing_need(H, T, N) :- needs(H, N), not covers(T, N).
tool_ok(H, T) :- hiding(H), tool(T), not missing_need(H, T, _).

valid(S, C, H, T) :- setting(S), clue(C), hiding(H), tool(T),
                     valid_place(S, H), valid_clue(C, H), tool_ok(H, T).

direct :- chosen_hiding(H), chosen_bravery(B), darkness(H, D), bravery_score(B, S), S >= D.
outcome(direct) :- direct.
outcome(calls_help) :- not direct.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, hid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for hid in sorted(clue.points_to):
            lines.append(asp.fact("points_to", cid, hid))
    for hid, hiding in HIDING_SPOTS.items():
        lines.append(asp.fact("hiding", hid))
        lines.append(asp.fact("darkness", hid, hiding.darkness))
        for need in sorted(hiding.needs):
            lines.append(asp.fact("needs", hid, need))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for cover in sorted(tool.covers):
            lines.append(asp.fact("covers", tid, cover))
    for bravery, score in BRAVERY_SCORES.items():
        lines.append(asp.fact("bravery_score", bravery, score))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_hiding", params.hiding),
            asp.fact("chosen_bravery", params.bravery),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_emit(sample: StorySample) -> str:
    parts = [sample.story]
    if sample.prompts:
        parts.append(sample.prompts[0])
    if sample.story_qa:
        parts.append(sample.story_qa[0].answer)
    return "\n".join(parts)


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {s}.")
            continue
        cases.append(params)

    mismatches = []
    for params in cases:
        po = outcome_of(params)
        ao = asp_outcome(params)
        if po != ao:
            mismatches.append((params, po, ao))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH in outcomes ({len(mismatches)} cases).")
        for params, po, ao in mismatches[:5]:
            print(f"  {params} python={po} asp={ao}")

    try:
        sample = generate(CURATED[0])
        blob = _smoke_emit(sample)
        if not blob.strip():
            raise StoryError("empty smoke output")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a farm mystery about a missing calf, market plans, and bravery."
    )
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--hiding", choices=sorted(HIDING_SPOTS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--plan", choices=sorted(PLANS))
    ap.add_argument("--bravery", choices=sorted(BRAVERY_SCORES))
    ap.add_argument("--child-name")
    ap.add_argument("--adult-name")
    ap.add_argument("--calf-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-type", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combo set from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.clue and args.hiding and args.tool:
        if not valid_combo(args.setting, args.clue, args.hiding, args.tool):
            raise StoryError(explain_rejection(args.setting, args.clue, args.hiding, args.tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.clue is None or combo[1] == args.clue)
        and (args.hiding is None or combo[2] == args.hiding)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, clue_id, hiding_id, tool_id = rng.choice(sorted(combos))
    plan_id = args.plan or rng.choice(sorted(PLANS))
    bravery = args.bravery or rng.choice(sorted(BRAVERY_SCORES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    adult_type = args.adult_type or rng.choice(["mother", "father", "aunt", "uncle"])
    default_adult_name = {
        "mother": f"Mom {rng.choice(['Elsie', 'Ruth', 'Mara'])}",
        "father": f"Dad {rng.choice(['Rowan', 'Milo', 'Glen'])}",
        "aunt": f"Aunt {rng.choice(['June', 'Wren', 'Ada'])}",
        "uncle": f"Uncle {rng.choice(['Reed', 'Cal', 'Ned'])}",
    }[adult_type]
    adult_name = args.adult_name or default_adult_name
    calf_name = args.calf_name or rng.choice(CALF_NAMES)

    return StoryParams(
        setting=setting_id,
        clue=clue_id,
        hiding=hiding_id,
        tool=tool_id,
        plan=plan_id,
        child_name=child_name,
        child_gender=child_gender,
        adult_name=adult_name,
        adult_type=adult_type,
        bravery=bravery,
        calf_name=calf_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.hiding not in HIDING_SPOTS:
        raise StoryError(f"(Unknown hiding place: {params.hiding})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown market plan: {params.plan})")
    if params.bravery not in BRAVERY_SCORES:
        raise StoryError(f"(Unknown bravery level: {params.bravery})")
    if not valid_combo(params.setting, params.clue, params.hiding, params.tool):
        raise StoryError(explain_rejection(params.setting, params.clue, params.hiding, params.tool))

    world = tell(
        setting=SETTINGS[params.setting],
        clue=CLUES[params.clue],
        hiding=HIDING_SPOTS[params.hiding],
        tool=TOOLS[params.tool],
        plan=PLANS[params.plan],
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_name=params.adult_name,
        adult_type=params.adult_type,
        bravery=params.bravery,
        calf_name=params.calf_name,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, clue, hiding, tool) combos:\n")
        for setting_id, clue_id, hiding_id, tool_id in combos:
            print(f"  {setting_id:12} {clue_id:12} {hiding_id:10} {tool_id}")
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
            header = (
                f"### {p.child_name}: {p.clue} -> {p.hiding} "
                f"({p.setting}, {p.tool}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
