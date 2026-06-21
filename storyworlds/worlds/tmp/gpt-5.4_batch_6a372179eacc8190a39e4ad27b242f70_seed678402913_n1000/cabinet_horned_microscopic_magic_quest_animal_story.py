#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cabinet_horned_microscopic_magic_quest_animal_story.py
=================================================================================

A standalone story world for a tiny animal-style magic quest:

A young animal notices a microscopic horned beetle family living beside a
cabinet. Their magic keeps the cabinet nook warm and bright, but one glowing
treasure has slipped into a hard-to-reach place. The hero promises to help,
tries the problem with an ordinary paw first, then succeeds only by choosing a
tool that actually fits the hiding place.

This world is intentionally small and constraint-checked. The core common-sense
rule is simple:

    cabinet location + quest tool must be compatible

A feather can sweep something from under a cabinet, a hook can lift something
out of a keyhole, and a ribbon ladder can reach a high cabinet ledge. Explicitly
asking for an unreasonable combination raises StoryError with an explanation.

Run it
------
    python storyworlds/worlds/gpt-5.4/cabinet_horned_microscopic_magic_quest_animal_story.py
    python storyworlds/worlds/gpt-5.4/cabinet_horned_microscopic_magic_quest_animal_story.py --location keyhole --tool hook
    python storyworlds/worlds/gpt-5.4/cabinet_horned_microscopic_magic_quest_animal_story.py --location top_ledge --tool feather
    python storyworlds/worlds/gpt-5.4/cabinet_horned_microscopic_magic_quest_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/cabinet_horned_microscopic_magic_quest_animal_story.py --qa --json
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "doe", "hen"}
        male = {"boy", "father", "buck", "stag"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class CabinetScene:
    id: str
    label: str
    phrase: str
    smell: str
    color: str
    height_m: float
    tags: set[str] = field(default_factory=lambda: {"cabinet"})


@dataclass
class MagicItem:
    id: str
    label: str
    phrase: str
    glow: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Location:
    id: str
    label: str
    phrase: str
    need: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use_text: str
    qa_text: str
    reaches: set[str] = field(default_factory=set)
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


def _r_stretch_frustration(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["stretching"] < THRESHOLD:
        return []
    loc = world.facts.get("location_cfg")
    if loc is None:
        return []
    sig = ("frustration", loc.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if loc.id in {"keyhole", "top_ledge"}:
        hero.memes["frustration"] += 1
        return ["__frustration__"]
    return []


def _r_retrieved(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["retrieved"] < THRESHOLD:
        return []
    sig = ("retrieved", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend = world.get("friend")
    hero = world.get("hero")
    cabinet = world.get("cabinet")
    friend.memes["relief"] += 1
    friend.memes["gratitude"] += 1
    hero.memes["pride"] += 1
    cabinet.meters["glow"] += 1
    return ["__retrieved__"]


def _r_glow_joy(world: World) -> list[str]:
    cabinet = world.get("cabinet")
    if cabinet.meters["glow"] < THRESHOLD:
        return []
    sig = ("joy", cabinet.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hero").memes["joy"] += 1
    world.get("friend").memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="stretch_frustration", tag="emotion", apply=_r_stretch_frustration),
    Rule(name="retrieved", tag="physical", apply=_r_retrieved),
    Rule(name="glow_joy", tag="emotion", apply=_r_glow_joy),
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
            if sent == "__frustration__":
                hero = world.get("hero")
                world.say(
                    f"{hero.id} stretched and stretched, but an ordinary paw could not reach so tiny a place."
                )
            elif sent == "__retrieved__":
                friend = world.get("friend")
                item_cfg = world.facts["item_cfg"]
                cabinet_cfg = world.facts["cabinet_cfg"]
                world.say(
                    f"At once, the {item_cfg.label} shone again, and warm magic ran in a soft line along {cabinet_cfg.phrase}."
                )
                world.say(
                    f"{friend.id}'s feelers gave a happy wiggle, and even {friend.pronoun('possessive')} little horn caught the light."
                )
    return produced


CABINETS = {
    "kitchen_blue": CabinetScene(
        id="kitchen_blue",
        label="cabinet",
        phrase="the blue kitchen cabinet",
        smell="cinnamon and warm oats",
        color="blue",
        height_m=1.2,
        tags={"cabinet", "kitchen"},
    ),
    "berry_red": CabinetScene(
        id="berry_red",
        label="cabinet",
        phrase="the berry-red pantry cabinet",
        smell="jam and dried berries",
        color="red",
        height_m=1.0,
        tags={"cabinet", "pantry"},
    ),
    "toy_green": CabinetScene(
        id="toy_green",
        label="cabinet",
        phrase="the moss-green toy cabinet",
        smell="cedar and clean cloth",
        color="green",
        height_m=0.9,
        tags={"cabinet", "room"},
    ),
}

ITEMS = {
    "moon_seed": MagicItem(
        id="moon_seed",
        label="moon-seed",
        phrase="a silver moon-seed",
        glow="like a curled bit of moonlight",
        effect="made the beetles' nook glow like evening stars",
        tags={"magic", "seed"},
    ),
    "pollen_pearl": MagicItem(
        id="pollen_pearl",
        label="pollen pearl",
        phrase="a golden pollen pearl",
        glow="like a drop of trapped sunshine",
        effect="kept tiny wings warm on cool nights",
        tags={"magic", "pollen"},
    ),
    "dew_spark": MagicItem(
        id="dew-spark",
        label="dew-spark",
        phrase="a blue dew-spark",
        glow="like a tiny star in a rain drop",
        effect="lit the beetles' supper table with blue firefly light",
        tags={"magic", "dew"},
    ),
}

LOCATIONS = {
    "under_cabinet": Location(
        id="under_cabinet",
        label="under the cabinet",
        phrase="under the cabinet where the dust bunnies slept",
        need="sweep",
        clue="A thread of light winked from the dark line beneath the cabinet.",
        tags={"under", "cabinet"},
    ),
    "keyhole": Location(
        id="keyhole",
        label="the cabinet keyhole",
        phrase="inside the cabinet keyhole",
        need="hook",
        clue="A tiny glimmer blinked from the round brass keyhole.",
        tags={"keyhole", "cabinet"},
    ),
    "top_ledge": Location(
        id="top_ledge",
        label="the top ledge of the cabinet",
        phrase="on the top ledge of the cabinet",
        need="climb",
        clue="Far above, a speck of light trembled on the cabinet's top ledge.",
        tags={"high", "cabinet"},
    ),
}

TOOLS = {
    "feather": Tool(
        id="feather",
        label="feather wand",
        phrase="a soft feather wand",
        use_text="slid the feather under the cabinet and gave one careful sweep",
        qa_text="used a soft feather to sweep the tiny treasure out",
        reaches={"under_cabinet"},
        tags={"feather", "tool"},
    ),
    "hook": Tool(
        id="hook",
        label="twine hook",
        phrase="a little twine hook",
        use_text="lowered the twine hook into the keyhole and lifted with the gentlest tug",
        qa_text="used a small hook to lift the treasure from the keyhole",
        reaches={"keyhole"},
        tags={"hook", "tool"},
    ),
    "ribbon_ladder": Tool(
        id="ribbon_ladder",
        label="ribbon ladder",
        phrase="a ribbon ladder with knot steps",
        use_text="propped the ribbon ladder against the cabinet and climbed until nose and paws reached the ledge",
        qa_text="used a ribbon ladder to climb to the high ledge",
        reaches={"top_ledge"},
        tags={"ladder", "tool"},
    ),
    "wooden_spoon": Tool(
        id="wooden_spoon",
        label="wooden spoon",
        phrase="a big wooden spoon",
        use_text="poked with the spoon",
        qa_text="tried a spoon",
        reaches=set(),
        tags={"spoon", "tool"},
    ),
}

HEROES = [
    {"name": "Mimi", "species": "mouse", "traits": ["gentle", "brisk"]},
    {"name": "Pip", "species": "rabbit", "traits": ["kind", "springy"]},
    {"name": "Tansy", "species": "squirrel", "traits": ["quick", "bright-eyed"]},
    {"name": "Nettle", "species": "hedgehog", "traits": ["careful", "patient"]},
]

FRIEND_NAMES = ["Bramble", "Clover", "Pico", "Thimble", "Mote", "Nip"]


def tool_fits(location: Location, tool: Tool) -> bool:
    return location.id in tool.reaches


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for cabinet_id in CABINETS:
        for item_id in ITEMS:
            for location_id, location in LOCATIONS.items():
                for tool_id, tool in TOOLS.items():
                    if tool_fits(location, tool):
                        combos.append((cabinet_id, item_id, location_id, tool_id))
    return combos


@dataclass
class StoryParams:
    cabinet: str
    item: str
    location: str
    tool: str
    hero_name: str
    hero_species: str
    hero_trait: str
    friend_name: str
    seed: Optional[int] = None


def explain_rejection(location: Location, tool: Tool) -> str:
    if location.id == "under_cabinet":
        return (
            f"(No story: {location.label} is a low, dusty gap. A {tool.label} will not slide and sweep there. "
            f"Try --tool feather.)"
        )
    if location.id == "keyhole":
        return (
            f"(No story: something stuck in {location.label} must be lifted, not brushed or climbed to. "
            f"Try --tool hook.)"
        )
    return (
        f"(No story: {location.label} is too high for a {tool.label}. "
        f"Try --tool ribbon_ladder.)"
    )


def _predict_retrieval(world: World, tool_id: str) -> bool:
    sim = world.copy()
    sim.facts["tool_cfg"] = TOOLS[tool_id]
    if tool_fits(sim.facts["location_cfg"], TOOLS[tool_id]):
        sim.get("item").meters["retrieved"] += 1
        propagate(sim, narrate=False)
    return sim.get("item").meters["retrieved"] >= THRESHOLD


def introduce(world: World, cabinet_cfg: CabinetScene) -> None:
    hero = world.get("hero")
    hero.memes["wonder"] += 1
    world.say(
        f"On a bright morning, {hero.id} the little {hero.type} padded into the room where {cabinet_cfg.phrase} stood smelling of {cabinet_cfg.smell}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} liked that cabinet because it always seemed to keep one small secret for the day."
    )


def discover(world: World, item_cfg: MagicItem, location_cfg: Location) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    friend.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"That day a bead of magic dew rolled across the floor. When {hero.id} peeped through it, the world near the cabinet turned microscopic and clear."
    )
    world.say(
        f"There, no taller than a crumb, stood {friend.id}, a microscopic horned beetle in a mossy cloak."
    )
    world.say(location_cfg.clue)
    world.say(
        f'"Oh dear," squeaked {friend.id}. "Our {item_cfg.label} is lost, and it {item_cfg.effect}."'
    )


def promise_quest(world: World, item_cfg: MagicItem) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    hero.memes["courage"] += 1
    friend.memes["hope"] += 1
    world.say(
        f'{hero.id} put a paw over {hero.pronoun("possessive")} heart. "Then this is a quest," {hero.pronoun()} said. "We will bring back the {item_cfg.label}."'
    )


def first_try(world: World, location_cfg: Location) -> None:
    hero = world.get("hero")
    hero.meters["stretching"] += 1
    world.say(
        f"First {hero.id} tried to help with nothing but a careful paw, reaching toward {location_cfg.label}."
    )
    propagate(world, narrate=True)


def choose_tool(world: World, tool_cfg: Tool, location_cfg: Location) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    world.say(
        f"{friend.id} pointed with one tiny feeler. Together they chose {tool_cfg.phrase}, because it could reach {location_cfg.label} without squashing anything small."
    )
    hero.memes["focus"] += 1


def use_tool(world: World, tool_cfg: Tool, item_cfg: MagicItem) -> None:
    hero = world.get("hero")
    item = world.get("item")
    world.say(
        f"{hero.id} {tool_cfg.use_text}. Out came {item_cfg.phrase}, glowing {item_cfg.glow}."
    )
    item.meters["retrieved"] += 1
    item.meters["visible"] = 1.0
    propagate(world, narrate=True)


def ending(world: World, cabinet_cfg: CabinetScene, item_cfg: MagicItem) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    friend.memes["love"] += 1
    world.say(
        f'{friend.id} hugged the {item_cfg.label} with both tiny arms. "You were brave and gentle," {friend.pronoun()} said.'
    )
    if cabinet_cfg.color == "blue":
        image = "the blue paint gleamed as if it were holding a piece of sky"
    elif cabinet_cfg.color == "red":
        image = "the red wood glowed like berry jam in sunshine"
    else:
        image = "the green doors shone softly like moss after rain"
    world.say(
        f"That evening the beetles' nook by the cabinet twinkled again, and {image}. {hero.id} smiled every time {hero.pronoun()} passed, knowing a quest had made the room kinder."
    )


def tell(params: StoryParams) -> World:
    cabinet_cfg = CABINETS[params.cabinet]
    item_cfg = ITEMS[params.item]
    location_cfg = LOCATIONS[params.location]
    tool_cfg = TOOLS[params.tool]

    if not tool_fits(location_cfg, tool_cfg):
        raise StoryError(explain_rejection(location_cfg, tool_cfg))

    world = World()
    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            type=params.hero_species,
            label=params.hero_species,
            traits=[params.hero_trait],
            tags={"hero", "animal"},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend_name,
            kind="character",
            type="beetle",
            label="beetle",
            phrase="a microscopic horned beetle",
            traits=["tiny", "horned"],
            tags={"beetle", "horned", "microscopic"},
        )
    )
    cabinet = world.add(
        Entity(
            id="cabinet",
            kind="thing",
            type="cabinet",
            label="cabinet",
            phrase=cabinet_cfg.phrase,
            tags=set(cabinet_cfg.tags),
        )
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="magic_item",
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            tags=set(item_cfg.tags) | {"magic"},
        )
    )
    tool = world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool_cfg.label,
            phrase=tool_cfg.phrase,
            tags=set(tool_cfg.tags),
        )
    )

    world.facts.update(
        cabinet_cfg=cabinet_cfg,
        item_cfg=item_cfg,
        location_cfg=location_cfg,
        tool_cfg=tool_cfg,
        hero=hero,
        friend=friend,
        cabinet=cabinet,
        item=item,
        tool=tool,
    )

    introduce(world, cabinet_cfg)
    discover(world, item_cfg, location_cfg)

    world.para()
    promise_quest(world, item_cfg)
    first_try(world, location_cfg)

    world.para()
    choose_tool(world, tool_cfg, location_cfg)
    use_tool(world, tool_cfg, item_cfg)

    world.para()
    ending(world, cabinet_cfg, item_cfg)

    world.facts.update(
        success=item.meters["retrieved"] >= THRESHOLD,
        frustrated=hero.memes["frustration"] >= THRESHOLD,
        glowing=cabinet.meters["glow"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "cabinet": [
        (
            "What is a cabinet?",
            "A cabinet is a piece of furniture with doors or drawers where people keep things. It can have little gaps, shelves, and corners."
        )
    ],
    "microscopic": [
        (
            "What does microscopic mean?",
            "Microscopic means so tiny that it is hard to see with ordinary eyes. You usually need something special, like a microscope or magic in a story, to see it clearly."
        )
    ],
    "horned": [
        (
            "What does horned mean?",
            "Horned means having a horn or horn-like point on the head. In stories, it can make a tiny creature look brave or special."
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic is something wonderful that cannot happen in ordinary life, like glowing seeds or a dew drop that helps someone see tiny things."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey or mission to solve an important problem. In many stories, the hero must be brave, careful, and kind to finish it."
        )
    ],
    "feather": [
        (
            "Why is a feather gentle?",
            "A feather is soft and light, so it can move tiny things without hitting them too hard. That makes it useful for careful jobs."
        )
    ],
    "hook": [
        (
            "What does a hook help you do?",
            "A hook helps you catch or lift something from a narrow place. It is good when your paw or hand cannot reach inside."
        )
    ],
    "ladder": [
        (
            "What is a ladder for?",
            "A ladder helps you climb up to a place that is too high to reach from the floor. The steps give your feet a safe way up."
        )
    ],
    "beetle": [
        (
            "What is a beetle?",
            "A beetle is a small insect with a hard outer shell. Many beetles have feelers, and some kinds have little horn-like shapes."
        )
    ],
}
KNOWLEDGE_ORDER = ["cabinet", "microscopic", "horned", "magic", "quest", "beetle", "feather", "hook", "ladder"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    item_cfg = world.facts["item_cfg"]
    location_cfg = world.facts["location_cfg"]
    cabinet_cfg = world.facts["cabinet_cfg"]
    return [
        'Write an animal story for a 3-to-5-year-old that includes the words "cabinet", "horned", and "microscopic", and make it a magic quest.',
        f"Tell a gentle quest story where {hero.id} the {hero.type} helps a microscopic horned beetle recover a magic {item_cfg.label} from {location_cfg.label} near {cabinet_cfg.phrase}.",
        "Write a child-facing animal tale with a clear beginning, a careful rescue in the middle, and an ending image that shows the room changed by kindness."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    cabinet_cfg = world.facts["cabinet_cfg"]
    item_cfg = world.facts["item_cfg"]
    location_cfg = world.facts["location_cfg"]
    tool_cfg = world.facts["tool_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type} and {friend.id}, a microscopic horned beetle beside {cabinet_cfg.phrase}. They meet because magic dew helps {hero.id} see a tiny problem."
        ),
        (
            f"Why did {friend.id} need help?",
            f"{friend.id} had lost the {item_cfg.label}, and it {item_cfg.effect}. Without it, the beetles' little home by the cabinet could not shine the same way."
        ),
        (
            "Why was this a quest?",
            f"It became a quest because the lost treasure was in a hard place to reach, so {hero.id} had to solve a real problem instead of just picking it up. {hero.pronoun().capitalize()} promised to be both brave and gentle."
        ),
    ]
    if world.facts.get("frustrated"):
        qa.append(
            (
                f"Why could {hero.id} not fix the problem with just a paw?",
                f"{hero.id} tried first, but {location_cfg.label} was too tiny or awkward for an ordinary reach. That is why {hero.pronoun()} needed the right tool for that place."
            )
        )
    if world.facts.get("success"):
        qa.append(
            (
                f"How did {hero.id} get the {item_cfg.label} back?",
                f"{hero.id} used {tool_cfg.phrase} and reached into {location_cfg.label} the careful way. The tool worked because it matched the hiding place instead of forcing a clumsy grab."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The quest ended happily: the {item_cfg.label} shone again, the cabinet nook glowed, and the tiny beetle family felt safe. The final image shows the room itself looking warmer because help arrived."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"cabinet", "microscopic", "horned", "magic", "quest"}
    tags |= world.facts["friend"].tags
    tags |= world.facts["tool"].tags
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        cabinet="kitchen_blue",
        item="moon_seed",
        location="under_cabinet",
        tool="feather",
        hero_name="Mimi",
        hero_species="mouse",
        hero_trait="gentle",
        friend_name="Bramble",
    ),
    StoryParams(
        cabinet="berry_red",
        item="pollen_pearl",
        location="keyhole",
        tool="hook",
        hero_name="Tansy",
        hero_species="squirrel",
        hero_trait="quick",
        friend_name="Clover",
    ),
    StoryParams(
        cabinet="toy_green",
        item="dew_spark",
        location="top_ledge",
        tool="ribbon_ladder",
        hero_name="Nettle",
        hero_species="hedgehog",
        hero_trait="patient",
        friend_name="Mote",
    ),
]


ASP_RULES = r"""
fits(Loc, Tool) :- location(Loc), tool(Tool), reaches(Tool, Loc).
valid(Cab, Item, Loc, Tool) :- cabinet(Cab), item(Item), location(Loc), tool(Tool), fits(Loc, Tool).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cabinet_id in CABINETS:
        lines.append(asp.fact("cabinet", cabinet_id))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for location_id in LOCATIONS:
        lines.append(asp.fact("location", location_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for location_id in sorted(tool.reaches):
            lines.append(asp.fact("reaches", tool_id, location_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Empty story from smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a microscopic magic quest beside a cabinet."
    )
    ap.add_argument("--cabinet", choices=sorted(CABINETS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--location", choices=sorted(LOCATIONS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--name")
    ap.add_argument("--species", choices=sorted({h["species"] for h in HEROES}))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.location and args.tool:
        location_cfg = LOCATIONS[args.location]
        tool_cfg = TOOLS[args.tool]
        if not tool_fits(location_cfg, tool_cfg):
            raise StoryError(explain_rejection(location_cfg, tool_cfg))

    combos = [
        combo
        for combo in valid_combos()
        if (args.cabinet is None or combo[0] == args.cabinet)
        and (args.item is None or combo[1] == args.item)
        and (args.location is None or combo[2] == args.location)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cabinet_id, item_id, location_id, tool_id = rng.choice(sorted(combos))

    hero_choices = [
        hero for hero in HEROES
        if (args.species is None or hero["species"] == args.species)
        and (args.name is None or hero["name"] == args.name)
    ]
    if not hero_choices and args.name is not None:
        species = args.species or rng.choice(sorted({h["species"] for h in HEROES}))
        trait = rng.choice(["gentle", "quick", "patient", "brave"])
        hero_name = args.name
        hero_species = species
        hero_trait = trait
    else:
        if not hero_choices:
            hero_choices = list(HEROES)
        hero_cfg = rng.choice(hero_choices)
        hero_name = hero_cfg["name"]
        hero_species = hero_cfg["species"]
        hero_trait = rng.choice(hero_cfg["traits"])

    friend_name = rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(
        cabinet=cabinet_id,
        item=item_id,
        location=location_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_species=hero_species,
        hero_trait=hero_trait,
        friend_name=friend_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.cabinet not in CABINETS:
        raise StoryError(f"(Unknown cabinet: {params.cabinet})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.location not in LOCATIONS:
        raise StoryError(f"(Unknown location: {params.location})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (cabinet, item, location, tool) combos:\n")
        for cabinet_id, item_id, location_id, tool_id in combos:
            print(f"  {cabinet_id:12} {item_id:12} {location_id:14} {tool_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.location} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
