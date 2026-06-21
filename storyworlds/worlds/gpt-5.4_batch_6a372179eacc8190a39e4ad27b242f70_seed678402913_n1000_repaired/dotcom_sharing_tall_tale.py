#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dotcom_sharing_tall_tale.py
======================================================

A standalone storyworld for tall-tale sharing stories centered on a child, an
enormous food, and a mule named dotcom.

Premise
-------
A child in an exaggerated frontier place makes or receives a wildly oversized
dish. Hungry people nearby need supper. The child could keep the marvel for a
contest or bragging rights, but instead loads it up with dotcom's help and
shares it. The world model tracks carrying, delivery, portioning, hunger,
gratitude, and what kind of ending image follows from the actual state.

Reasonableness gate
-------------------
Not every combination makes a plausible story. A transport must be able to
carry the giant food and suit the terrain. A sharing tool must actually match
the food's form and clear a minimum common-sense threshold. Those checks exist
both in Python and as an inline ASP twin.

Run it
------
python storyworlds/worlds/gpt-5.4/dotcom_sharing_tall_tale.py
python storyworlds/worlds/gpt-5.4/dotcom_sharing_tall_tale.py --all
python storyworlds/worlds/gpt-5.4/dotcom_sharing_tall_tale.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/dotcom_sharing_tall_tale.py --qa --json
python storyworlds/worlds/gpt-5.4/dotcom_sharing_tall_tale.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested world directory.
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
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        animal = {"mule", "horse", "pony"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.label or self.type)


@dataclass
class Setting:
    id: str
    place: str
    terrain: str
    sky: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Bounty:
    id: str
    label: str
    phrase: str
    form: str
    weight: int
    servings: int
    boast: str
    need_word: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transport:
    id: str
    label: str
    phrase: str
    capacity: int
    terrains: set[str] = field(default_factory=set)
    steadiness: int = 0
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareTool:
    id: str
    label: str
    phrase: str
    forms: set[str] = field(default_factory=set)
    sense: int = 0
    text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Crowd:
    id: str
    label: str
    phrase: str
    count: int
    need_line: str
    cheer_line: str
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


def available_servings(bounty: Bounty, transport: Transport, delay: int) -> int:
    loss = max(0, bounty.weight + delay - transport.steadiness)
    return max(1, bounty.servings - loss)


def enough_for_all(bounty: Bounty, transport: Transport, crowd: Crowd, delay: int) -> bool:
    return available_servings(bounty, transport, delay) >= crowd.count


def can_carry(bounty: Bounty, transport: Transport) -> bool:
    return transport.capacity >= bounty.weight


def fits_terrain(setting: Setting, transport: Transport) -> bool:
    return setting.terrain in transport.terrains


def tool_matches(bounty: Bounty, tool: ShareTool) -> bool:
    return bounty.form in tool.forms and tool.sense >= SENSE_MIN


def valid_story(setting: Setting, bounty: Bounty, transport: Transport, tool: ShareTool) -> bool:
    return can_carry(bounty, transport) and fits_terrain(setting, transport) and tool_matches(bounty, tool)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for bid, bounty in BOUNTIES.items():
            for tid, transport in TRANSPORTS.items():
                for uid, tool in SHARE_TOOLS.items():
                    if valid_story(setting, bounty, transport, tool):
                        combos.append((sid, bid, tid, uid))
    return combos


def _r_served(world: World) -> list[str]:
    crowd = world.get("crowd")
    bounty = world.get("bounty")
    town = world.get("town")
    hero = world.get("hero")
    if bounty.meters["ready_to_share"] < THRESHOLD:
        return []
    sig = ("served", int(bounty.meters["ready_to_share"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    served = min(int(bounty.meters["portions"]), int(crowd.meters["hunger"]))
    crowd.meters["fed"] += served
    crowd.meters["hunger"] -= served
    hero.memes["generous"] += 1
    town.memes["gratitude"] += 1
    if crowd.meters["hunger"] <= 0:
        town.memes["celebration"] += 1
    else:
        town.memes["sharing_spirit"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="served", tag="social", apply=_r_served),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True


def predict_trip(setting: Setting, bounty: Bounty, transport: Transport, crowd: Crowd, delay: int) -> dict:
    portions = available_servings(bounty, transport, delay)
    return {
        "portions": portions,
        "enough": portions >= crowd.count,
    }


def giant_setup(world: World, hero: Entity, helper: Entity, bounty: Bounty) -> None:
    hero.memes["pride"] += 1
    helper.memes["steady"] += 1
    world.say(
        f"In {world.setting.place}, where {world.setting.sky}, {hero.id} made {bounty.phrase}. "
        f"Folks said it was so big {bounty.boast}."
    )
    world.say(
        f"Only {hero.id}'s mule, dotcom, could stand beside it without looking surprised. "
        f"dotcom blinked once, as if giant suppers were part of every ordinary morning."
    )


def need_appears(world: World, crowd_ent: Entity, crowd: Crowd) -> None:
    crowd_ent.meters["hunger"] = float(crowd.count)
    world.say(crowd.need_line)


def temptation(world: World, hero: Entity, bounty: Bounty) -> None:
    hero.memes["tempted"] += 1
    world.say(
        f"{hero.id} could have kept {bounty.label} for showing off. "
        f"A blue ribbon and a week of bragging were already dancing in {hero.pronoun('possessive')} mind."
    )


def decision(world: World, hero: Entity, helper: Entity, crowd: Crowd) -> None:
    hero.memes["generous"] += 1
    helper.memes["helpful"] += 1
    world.say(
        f"But when {hero.id} heard about {crowd.label}, {hero.pronoun()} set bragging aside. "
        f'"If a thing is big enough to be a tall tale," {hero.pronoun()} said, "it is big enough to share."'
    )
    world.say(
        f"dotcom stamped once, which was his way of agreeing before anybody else had finished thinking."
    )


def load_and_roll(world: World, hero: Entity, helper: Entity, bounty: Bounty,
                  transport: Transport, crowd: Crowd, tool: ShareTool, delay: int) -> None:
    trip = predict_trip(world.setting, bounty, transport, crowd, delay)
    world.facts["predicted_portions"] = trip["portions"]
    world.facts["predicted_enough"] = trip["enough"]
    world.say(
        f"They heaved {bounty.label} onto {transport.phrase}. "
        f"dotcom leaned into the straps, and {transport.label} started moving with a groan fit to wake fence posts."
    )
    if delay == 0:
        world.say(
            f"The road behaved itself for once, and not a crumb dared jump away."
        )
    elif delay == 1:
        world.say(
            f"A windy bend slowed them down, and a little of the feast jiggled loose before they reached the hungry folks."
        )
    else:
        world.say(
            f"Two long bumps and a stubborn creek crossing stole part of the supper on the way, "
            f"though dotcom kept pulling as steady as a courthouse clock."
        )
    world.say(
        f"When they arrived, {hero.id} took {tool.phrase} and {tool.text}."
    )


def share(world: World, hero: Entity, bounty_ent: Entity, crowd_ent: Entity,
          crowd: Crowd, bounty: Bounty, transport: Transport, delay: int) -> None:
    portions = available_servings(bounty, transport, delay)
    bounty_ent.meters["portions"] = float(portions)
    bounty_ent.meters["ready_to_share"] = 1.0
    propagate(world)
    fed = int(crowd_ent.meters["fed"])
    hungry = int(crowd_ent.meters["hunger"])
    if hungry <= 0:
        world.say(
            f"Plate after plate went out until every one of the {crowd.count} hungry mouths had enough. "
            f"{crowd.cheer_line}"
        )
    else:
        world.say(
            f"There was not a mountain of supper left by then, only {fed} good portions. "
            f"So the crowd passed small helpings hand to hand, and even the last bite tasted bigger because it was shared."
        )


def ending(world: World, hero: Entity, helper: Entity, crowd_ent: Entity,
           bounty: Bounty) -> None:
    if crowd_ent.meters["hunger"] <= 0:
        hero.memes["joy"] += 1
        world.say(
            f"By sunset, the whole place smelled of supper and laughter. "
            f"{bounty.ending_image} dotcom stood in the middle of it all with crumbs on his whiskers, "
            f"looking pleased with the work of sharing."
        )
    else:
        hero.memes["joy"] += 1
        world.say(
            f"By sunset, nobody was rich in leftovers, but everybody was rich in neighbors. "
            f"{hero.id} scratched dotcom behind the ears and saw smiles where hungry faces had been."
        )


def tell(setting: Setting, bounty: Bounty, transport: Transport, tool: ShareTool,
         crowd: Crowd, hero_name: str = "Mara", hero_gender: str = "girl",
         elder_type: str = "aunt", delay: int = 0) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id="dotcom", kind="character", type="mule", label="dotcom", role="helper"))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="the elder", role="elder"))
    bounty_ent = world.add(Entity(id="bounty", type="food", label=bounty.label, phrase=bounty.phrase))
    crowd_ent = world.add(Entity(id="crowd", type="group", label=crowd.label, phrase=crowd.phrase))
    town = world.add(Entity(id="town", type="place", label=setting.place))
    vehicle = world.add(Entity(id="transport", type="transport", label=transport.label, phrase=transport.phrase))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label, phrase=tool.phrase))

    giant_setup(world, hero, helper, bounty)
    world.say(
        f"{hero.id}'s {elder.label_word} shaded {elder.pronoun('possessive')} eyes and said the thing could feed "
        f"a marching band, a hay crew, and maybe one polite cloud."
    )

    world.para()
    need_appears(world, crowd_ent, crowd)
    temptation(world, hero, bounty)
    decision(world, hero, helper, crowd)

    world.para()
    load_and_roll(world, hero, helper, bounty, transport, crowd, tool, delay)
    share(world, hero, bounty_ent, crowd_ent, crowd, bounty, transport, delay)

    world.para()
    ending(world, hero, helper, crowd_ent, bounty)

    outcome = "enough" if crowd_ent.meters["hunger"] <= 0 else "stretched"
    world.facts.update(
        hero=hero,
        helper=helper,
        elder=elder,
        bounty=bounty,
        transport=transport,
        tool=tool,
        crowd=crowd,
        setting=setting,
        outcome=outcome,
        delay=delay,
        portions=int(bounty_ent.meters["portions"]),
        fed=int(crowd_ent.meters["fed"]),
        hungry=int(crowd_ent.meters["hunger"]),
        all_fed=crowd_ent.meters["hunger"] <= 0,
    )
    return world


SETTINGS = {
    "prairie": Setting(
        id="prairie",
        place="the long yellow prairie",
        terrain="flat",
        sky="the wind could comb the grass into waves",
        tags={"sharing", "frontier"},
    ),
    "canyon": Setting(
        id="canyon",
        place="the red canyon rim",
        terrain="rocky",
        sky="the echoes were so loud they sounded like extra cousins",
        tags={"sharing", "frontier"},
    ),
    "riverside": Setting(
        id="riverside",
        place="the willowy riverside",
        terrain="soft",
        sky="the river shone like a silver ribbon all afternoon",
        tags={"sharing", "frontier"},
    ),
}

BOUNTIES = {
    "biscuit": Bounty(
        id="biscuit",
        label="the mile-high biscuit",
        phrase="a biscuit so tall the butter had to slide downhill",
        form="solid",
        weight=2,
        servings=8,
        boast="its shadow reached supper before the biscuit did",
        need_word="biscuit",
        ending_image="Children drummed on empty plates while grown-ups laughed at the story of the butter slide.",
        tags={"food", "bread"},
    ),
    "pie": Bounty(
        id="pie",
        label="the thunderberry pie",
        phrase="a thunderberry pie broad as a wagon wheel and twice as proud",
        form="pie",
        weight=3,
        servings=10,
        boast="two crows tried to nest on the crust before they realized it was dessert",
        need_word="pie",
        ending_image="Purple smiles shone up and down the tables like lanterns lit from inside.",
        tags={"food", "pie"},
    ),
    "stew": Bounty(
        id="stew",
        label="the bean-pot stew",
        phrase="a bean-pot stew that steamed like a friendly little weather system",
        form="stew",
        weight=4,
        servings=12,
        boast="the lid rattled like a train whenever the beans started bragging",
        need_word="stew",
        ending_image="The last warm steam curled above the bowls while folks leaned back as happy as fence cats in sun.",
        tags={"food", "stew"},
    ),
}

TRANSPORTS = {
    "handcart": Transport(
        id="handcart",
        label="the handcart",
        phrase="a stout handcart",
        capacity=2,
        terrains={"flat", "soft"},
        steadiness=2,
        tags={"cart"},
    ),
    "mule_wagon": Transport(
        id="mule_wagon",
        label="the mule wagon",
        phrase="dotcom's broad mule wagon",
        capacity=4,
        terrains={"flat", "rocky", "soft"},
        steadiness=4,
        tags={"wagon"},
    ),
    "river_sled": Transport(
        id="river_sled",
        label="the river sled",
        phrase="a smooth-bottom river sled",
        capacity=3,
        terrains={"soft"},
        steadiness=3,
        tags={"sled"},
    ),
}

SHARE_TOOLS = {
    "long_knife": ShareTool(
        id="long_knife",
        label="the long knife",
        phrase="a long shining knife",
        forms={"solid", "pie"},
        sense=3,
        text="cut neat generous pieces instead of show-off slivers",
        qa_text="cut the giant food into generous pieces",
        tags={"knife"},
    ),
    "pie_spade": ShareTool(
        id="pie_spade",
        label="the pie spade",
        phrase="a pie spade with a handle like a little shovel",
        forms={"pie"},
        sense=3,
        text="lifted wedges as wide as hats and set them onto waiting plates",
        qa_text="lifted wide pie slices onto plates",
        tags={"pie_server"},
    ),
    "big_ladle": ShareTool(
        id="big_ladle",
        label="the big ladle",
        phrase="a ladle with a bowl deep enough to float a biscuit",
        forms={"stew"},
        sense=3,
        text="dipped and poured until bowls began steaming all along the table",
        qa_text="ladled the stew into waiting bowls",
        tags={"ladle"},
    ),
    "teaspoon": ShareTool(
        id="teaspoon",
        label="the teaspoon",
        phrase="a tiny silver teaspoon",
        forms={"stew", "pie"},
        sense=1,
        text="pecked at the feast one thimble at a time",
        qa_text="tried to serve it with a tiny spoon",
        tags={"spoon"},
    ),
}

CROWDS = {
    "schoolhouse": Crowd(
        id="schoolhouse",
        label="the hungry children from the schoolhouse",
        phrase="the schoolhouse children",
        count=6,
        need_line="Right then came word that the hungry children from the schoolhouse were waiting on a late supper after the cookfire went out.",
        cheer_line="Soon the schoolyard rang with happy stomping and thanks.",
        tags={"children", "sharing"},
    ),
    "haycrew": Crowd(
        id="haycrew",
        label="the hay crew by the barn",
        phrase="the hay crew",
        count=9,
        need_line="Then a rider brought news that the hay crew by the barn had worked clean through dinner and had empty bellies to prove it.",
        cheer_line="Hats flew up, boots thumped, and even the barn swallows circled lower to listen.",
        tags={"workers", "sharing"},
    ),
    "band": Crowd(
        id="band",
        label="the parade band at the depot",
        phrase="the parade band",
        count=12,
        need_line="Before the crust had finished cooling, somebody hollered that the parade band at the depot had played past mealtime and was hungry as winter.",
        cheer_line="Trombones burped, drums bounced, and the whole depot sounded glad.",
        tags={"music", "sharing"},
    ),
}

GIRL_NAMES = ["Mara", "June", "Elsie", "Nell", "Dora", "Willa"]
BOY_NAMES = ["Beau", "Cal", "Jesse", "Toby", "Hank", "Milo"]
ELDERS = ["mother", "father", "aunt", "uncle"]


@dataclass
class StoryParams:
    setting: str
    bounty: str
    transport: str
    tool: str
    crowd: str
    hero_name: str
    hero_gender: str
    elder_type: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "sharing": [
        (
            "Why is sharing a big meal kind?",
            "Sharing a big meal helps more people feel safe and cared for. It turns one good thing into comfort for a whole group."
        )
    ],
    "mule": [
        (
            "What does a mule do?",
            "A mule is a strong animal that can pull or carry heavy things. People use mules when they need steady help on a trip."
        )
    ],
    "wagon": [
        (
            "What is a wagon for?",
            "A wagon is used to carry heavy things from one place to another. Strong wheels make big loads easier to move."
        )
    ],
    "ladle": [
        (
            "What is a ladle?",
            "A ladle is a deep spoon used for serving soup or stew. It helps pour warm food into bowls without spilling too much."
        )
    ],
    "knife": [
        (
            "Why do people cut food into pieces to share it?",
            "Cutting food into pieces makes it easier for many people to have some. It is one way to turn one large dish into many servings."
        )
    ],
    "pie": [
        (
            "What is a pie slice?",
            "A pie slice is one piece cut from a whole pie. The pie is divided so different people can each have a serving."
        )
    ],
    "stew": [
        (
            "What is stew?",
            "Stew is a warm food with liquid and soft pieces cooked together in a pot. People often scoop it into bowls with a ladle."
        )
    ],
}
KNOWLEDGE_ORDER = ["sharing", "mule", "wagon", "knife", "pie", "ladle", "stew"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    bounty = f["bounty"]
    crowd = f["crowd"]
    setting = f["setting"]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the word "dotcom" and is about sharing a giant {bounty.need_word}.',
        f"Tell a frontier-style exaggeration where {hero.id} and a mule named dotcom bring an enormous meal across {setting.place} to feed {crowd.label}.",
        f"Write a warm sharing story in a tall-tale voice where bragging matters less than making sure hungry neighbors get supper.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    bounty = f["bounty"]
    crowd = f["crowd"]
    tool = f["tool"]
    transport = f["transport"]
    fed = f["fed"]
    hungry = f["hungry"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child with a giant food to share, and a mule named dotcom who helps carry it. The story is also about {crowd.label}, who need supper."
        ),
        (
            f"Why did {hero.id} decide to share the food?",
            f"{hero.id} first felt tempted to keep the giant dish for bragging, but hearing about {crowd.label} changed {hero.pronoun('possessive')} mind. {hero.pronoun().capitalize()} decided a tall-tale-sized meal should help hungry people instead of sitting there to be admired."
        ),
        (
            "How did dotcom help?",
            f"dotcom helped pull {transport.phrase} so the giant food could reach the hungry crowd. Without dotcom's steady work, the meal would have been much harder to move."
        ),
        (
            f"How was the food shared?",
            f"{hero.id} used {tool.label} and {tool.qa_text}. That changed one huge dish into portions real people could eat."
        ),
    ]
    if hungry <= 0:
        qa.append(
            (
                "Did everyone get enough to eat?",
                f"Yes. There were {f['portions']} portions after the trip, which was enough for all {crowd.count} people in the crowd. The ending proves it because the whole place turns noisy with thanks and full bellies."
            )
        )
    else:
        qa.append(
            (
                "Did everyone get a full portion?",
                f"Not quite. The trip left {f['portions']} portions for a crowd of {crowd.count}, so the meal had to be stretched and shared in smaller helpings. Even so, the sharing mattered because hungry faces turned into grateful ones."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sharing", "mule"}
    transport = world.facts["transport"]
    tool = world.facts["tool"]
    bounty = world.facts["bounty"]
    if "wagon" in transport.tags:
        tags.add("wagon")
    if "ladle" in tool.tags:
        tags.add("ladle")
    if "knife" in tool.tags or "pie_server" in tool.tags:
        tags.add("knife")
    if bounty.id == "pie":
        tags.add("pie")
    if bounty.id == "stew":
        tags.add("stew")
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
        bits: list[str] = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="prairie",
        bounty="biscuit",
        transport="handcart",
        tool="long_knife",
        crowd="schoolhouse",
        hero_name="June",
        hero_gender="girl",
        elder_type="aunt",
        delay=0,
    ),
    StoryParams(
        setting="prairie",
        bounty="pie",
        transport="mule_wagon",
        tool="pie_spade",
        crowd="haycrew",
        hero_name="Beau",
        hero_gender="boy",
        elder_type="father",
        delay=1,
    ),
    StoryParams(
        setting="canyon",
        bounty="stew",
        transport="mule_wagon",
        tool="big_ladle",
        crowd="band",
        hero_name="Mara",
        hero_gender="girl",
        elder_type="mother",
        delay=2,
    ),
    StoryParams(
        setting="riverside",
        bounty="pie",
        transport="river_sled",
        tool="pie_spade",
        crowd="schoolhouse",
        hero_name="Cal",
        hero_gender="boy",
        elder_type="uncle",
        delay=0,
    ),
]


def explain_rejection(setting: Setting, bounty: Bounty, transport: Transport, tool: ShareTool) -> str:
    if not can_carry(bounty, transport):
        return (
            f"(No story: {transport.label} cannot carry {bounty.label}. "
            f"The load is too heavy for a sensible tall tale in this world.)"
        )
    if not fits_terrain(setting, transport):
        return (
            f"(No story: {transport.label} does not suit {setting.place}. "
            f"Pick a transport that fits {setting.terrain} ground.)"
        )
    if tool.sense < SENSE_MIN:
        return (
            f"(No story: {tool.label} is too silly for serving a giant meal here. "
            f"Pick a sturdier sharing tool.)"
        )
    if bounty.form not in tool.forms:
        return (
            f"(No story: {tool.label} does not match {bounty.label}. "
            f"The sharing tool must suit the food's shape.)"
        )
    return "(No story: this combination is not reasonable in the world.)"


def outcome_of(params: StoryParams) -> str:
    bounty = BOUNTIES[params.bounty]
    transport = TRANSPORTS[params.transport]
    crowd = CROWDS[params.crowd]
    return "enough" if enough_for_all(bounty, transport, crowd, params.delay) else "stretched"


ASP_RULES = r"""
can_carry(B, T) :- weight(B, W), capacity(T, C), C >= W.
fits(S, T)      :- terrain(S, R), works_on(T, R).
sensible(U)     :- tool(U), sense(U, V), sense_min(M), V >= M.
tool_matches(B, U) :- form(B, F), serves(U, F), sensible(U).

valid(S, B, T, U) :- setting(S), bounty(B), transport(T), tool(U),
                     can_carry(B, T), fits(S, T), tool_matches(B, U).

portion_loss(B, T, D, L) :- weight(B, W), steady(T, S), delay(D), L = W + D - S, L > 0.
portion_loss(B, T, D, 0) :- weight(B, W), steady(T, S), delay(D), W + D - S <= 0.
available(B, T, D, A)    :- servings(B, P), portion_loss(B, T, D, L), A = P - L, A > 0.
available(B, T, D, 1)    :- servings(B, P), portion_loss(B, T, D, L), P - L <= 0.

enough :- chosen_bounty(B), chosen_transport(T), chosen_crowd(C), delay(D),
          available(B, T, D, A), crowd_size(C, N), A >= N.

outcome(enough)    :- enough.
outcome(stretched) :- not enough.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("terrain", sid, setting.terrain))
    for bid, bounty in BOUNTIES.items():
        lines.append(asp.fact("bounty", bid))
        lines.append(asp.fact("form", bid, bounty.form))
        lines.append(asp.fact("weight", bid, bounty.weight))
        lines.append(asp.fact("servings", bid, bounty.servings))
    for tid, transport in TRANSPORTS.items():
        lines.append(asp.fact("transport", tid))
        lines.append(asp.fact("capacity", tid, transport.capacity))
        lines.append(asp.fact("steady", tid, transport.steadiness))
        for terrain in sorted(transport.terrains):
            lines.append(asp.fact("works_on", tid, terrain))
    for uid, tool in SHARE_TOOLS.items():
        lines.append(asp.fact("tool", uid))
        lines.append(asp.fact("sense", uid, tool.sense))
        for form in sorted(tool.forms):
            lines.append(asp.fact("serves", uid, form))
    for cid, crowd in CROWDS.items():
        lines.append(asp.fact("crowd", cid))
        lines.append(asp.fact("crowd_size", cid, crowd.count))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("chosen_bounty", params.bounty),
            asp.fact("chosen_transport", params.transport),
            asp.fact("chosen_crowd", params.crowd),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale sharing storyworld with a mule named dotcom."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bounty", choices=BOUNTIES)
    ap.add_argument("--transport", choices=TRANSPORTS)
    ap.add_argument("--tool", choices=SHARE_TOOLS)
    ap.add_argument("--crowd", choices=CROWDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="travel trouble before the food arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting_id = args.setting
    bounty_id = args.bounty
    transport_id = args.transport
    tool_id = args.tool

    if setting_id and bounty_id and transport_id and tool_id:
        setting = SETTINGS[setting_id]
        bounty = BOUNTIES[bounty_id]
        transport = TRANSPORTS[transport_id]
        tool = SHARE_TOOLS[tool_id]
        if not valid_story(setting, bounty, transport, tool):
            raise StoryError(explain_rejection(setting, bounty, transport, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.bounty is None or combo[1] == args.bounty)
        and (args.transport is None or combo[2] == args.transport)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, bounty_id, transport_id, tool_id = rng.choice(sorted(combos))
    crowd_id = args.crowd or rng.choice(sorted(CROWDS))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder_type = args.elder or rng.choice(ELDERS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        bounty=bounty_id,
        transport=transport_id,
        tool=tool_id,
        crowd=crowd_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_type=elder_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.bounty not in BOUNTIES:
        raise StoryError(f"Unknown bounty: {params.bounty}")
    if params.transport not in TRANSPORTS:
        raise StoryError(f"Unknown transport: {params.transport}")
    if params.tool not in SHARE_TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")
    if params.crowd not in CROWDS:
        raise StoryError(f"Unknown crowd: {params.crowd}")

    setting = SETTINGS[params.setting]
    bounty = BOUNTIES[params.bounty]
    transport = TRANSPORTS[params.transport]
    tool = SHARE_TOOLS[params.tool]
    if not valid_story(setting, bounty, transport, tool):
        raise StoryError(explain_rejection(setting, bounty, transport, tool))

    world = tell(
        setting=setting,
        bounty=bounty,
        transport=transport,
        tool=tool,
        crowd=CROWDS[params.crowd],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder_type,
        delay=params.delay,
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
        print(f"{len(combos)} compatible (setting, bounty, transport, tool) combos:\n")
        for setting, bounty, transport, tool in combos:
            print(f"  {setting:10} {bounty:8} {transport:10} {tool}")
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
                f"### {p.hero_name}: {p.bounty} for {p.crowd} "
                f"({p.setting}, {p.transport}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
