#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/schooner_flashback_surprise_tall_tale.py
===================================================================

A standalone storyworld about a child, an old schooner, a runaway harbor-fair
treasure, and the sort of rescue that grows taller every time it is told.

This world is built for:
- seed word: "schooner"
- narrative features: Flashback, Surprise
- style: Tall Tale

The domain is small and deliberate: at a harbor fair, a gust or a tide carries
off one prized thing. A child and an elder remember an earlier lesson, launch
their little schooner, and use one sensible rescue tool. Some pairings are
refused by a common-sense gate: a boat hook should not be used on delicate cloth
things, and a trail line cannot scoop a floating lantern from the water.

Run it
------
python storyworlds/worlds/gpt-5.4/schooner_flashback_surprise_tall_tale.py
python storyworlds/worlds/gpt-5.4/schooner_flashback_surprise_tall_tale.py --all
python storyworlds/worlds/gpt-5.4/schooner_flashback_surprise_tall_tale.py --runaway kite --tool boat_hook
python storyworlds/worlds/gpt-5.4/schooner_flashback_surprise_tall_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/schooner_flashback_surprise_tall_tale.py --json
python storyworlds/worlds/gpt-5.4/schooner_flashback_surprise_tall_tale.py --verify
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
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def family_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Harbor:
    id: str
    place: str
    opener: str
    tall_detail: str
    water_bonus: int = 0
    air_bonus: int = 0
    tags: set[str] = field(default_factory=set)


@dataclass
class Weather:
    id: str
    line: str
    air_bonus: int = 0
    water_bonus: int = 0
    tags: set[str] = field(default_factory=set)


@dataclass
class Runaway:
    id: str
    label: str
    phrase: str
    mode: str
    fragile: bool = False
    opener: str = ""
    chase: str = ""
    image: str = ""
    difficulty: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    modes: set[str] = field(default_factory=set)
    gentle: bool = False
    power: int = 1
    surprise: str = ""
    action: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    item = world.entities.get("item")
    if item is None:
        return []
    if item.meters["loose"] < THRESHOLD or item.meters["recovered"] >= THRESHOLD:
        return []
    sig = ("worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role in {"child", "elder"}:
            ent.memes["worry"] += 1
    if "harbor" in world.entities:
        world.get("harbor").meters["commotion"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    item = world.entities.get("item")
    if item is None:
        return []
    if item.meters["recovered"] < THRESHOLD:
        return []
    sig = ("relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role in {"child", "elder"}:
            ent.memes["relief"] += 1
            ent.memes["pride"] += 1
            ent.memes["worry"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="worry", tag="emotion", apply=_r_worry),
    Rule(name="relief", tag="emotion", apply=_r_relief),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
        now = len(world.fired)
        if now > len(world.fired) - 1:
            changed = changed or False


def difficulty(runaway: Runaway, harbor: Harbor, weather: Weather) -> int:
    bonus = weather.air_bonus if runaway.mode == "air" else weather.water_bonus
    bonus += harbor.air_bonus if runaway.mode == "air" else harbor.water_bonus
    return runaway.difficulty + bonus


def compatible(runaway: Runaway, tool: Tool) -> bool:
    if runaway.mode not in tool.modes:
        return False
    if runaway.fragile and not tool.gentle:
        return False
    return True


def clean_recovery(runaway: Runaway, tool: Tool, harbor: Harbor, weather: Weather) -> bool:
    return tool.power >= difficulty(runaway, harbor, weather)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for harbor_id in HARBORS:
        for runaway_id, runaway in RUNAWAYS.items():
            for tool_id, tool in TOOLS.items():
                if compatible(runaway, tool):
                    combos.append((harbor_id, runaway_id, tool_id))
    return combos


def explain_rejection(runaway: Runaway, tool: Tool) -> str:
    if runaway.mode not in tool.modes:
        if runaway.mode == "air":
            return (
                f"(No story: {tool.label} is for things in the water, but {runaway.phrase} "
                f"gets carried through the air. Pick a tool that can catch a flying thing.)"
            )
        return (
            f"(No story: {tool.label} cannot scoop up {runaway.phrase} from the water. "
            f"Pick a net or hook made for floating things.)"
        )
    if runaway.fragile and not tool.gentle:
        return (
            f"(No story: {runaway.phrase} is too delicate for {tool.label}. "
            f"A rough hook would tear it, so the world refuses that rescue.)"
        )
    return "(No story: that rescue plan is not reasonable here.)"


def memory_text(runaway: Runaway, child: Entity, elder: Entity) -> str:
    if runaway.mode == "air":
        return (
            f"Just then, {child.id} remembered a day from last summer. "
            f"{elder.family_word.capitalize()} had once pointed at the family schooner and said, "
            f'"When the wind grows proud, a sailor must grow patient. This little schooner once '
            f'chased a runaway picnic cloth clear across the bay, and the cloth was flapping so hard '
            f'it looked like a red dragon trying to learn manners."'
        )
    return (
        f"Just then, {child.id} remembered a day from last autumn. "
        f"{elder.family_word.capitalize()} had once tapped the rail of the schooner and said, "
        f'"The water likes to brag too. This little schooner once followed a drifting pumpkin pie '
        f'clear to the reeds, and the pie floated along as calm as a king in a gravy boat."'
    )


def introduce(world: World, child: Entity, elder: Entity, harbor: Harbor, weather: Weather) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On harbor-fair morning, {harbor.opener} {weather.line} "
        f"{child.id} stood beside {elder.family_word} and the family schooner, "
        f'"Morning Star."'
    )
    world.say(
        f"The little schooner was not much bigger than a wagon, but in that harbor it looked "
        f"grand enough to pull the moon by a rope. {harbor.tall_detail}"
    )


def admire(world: World, child: Entity, elder: Entity) -> None:
    world.say(
        f'{child.id} ran a hand along the smooth rail. "{elder.family_word.capitalize()}, your '
        f'schooner looks ready to outrun a cloud," {child.pronoun()} said.'
    )
    world.say(
        f'{elder.family_word.capitalize()} laughed. "Only if the cloud is polite," '
        f'{elder.pronoun()} said.'
    )


def trouble(world: World, child: Entity, elder: Entity, runaway: Runaway) -> None:
    item = world.get("item")
    item.meters["loose"] += 1
    child.memes["alarm"] += 1
    world.say(runaway.opener)
    world.say(
        f"In one blink, {runaway.phrase} was off and away. {runaway.chase}"
    )
    propagate(world)


def flashback(world: World, child: Entity, elder: Entity, runaway: Runaway) -> None:
    child.memes["memory"] += 1
    world.say(memory_text(runaway, child, elder))
    world.say(
        f"Back in the bright present, {child.id} straightened up. If the schooner had taught "
        f"{elder.family_word} a trick once, maybe it could teach one again."
    )


def launch(world: World, child: Entity, elder: Entity, runaway: Runaway) -> None:
    boat = world.get("schooner")
    boat.meters["moving"] += 1
    child.memes["courage"] += 1
    elder.memes["courage"] += 1
    world.say(
        f'{elder.family_word.capitalize()} untied the painter, and the little schooner slid from the '
        f'dock as neatly as a spoon into soup. {child.id} hopped aboard, heart thumping, while '
        f'{runaway.label} danced farther off.'
    )


def reveal_tool(world: World, elder: Entity, tool: Tool) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["ready"] += 1
    world.say(
        f"Then came the surprise. {elder.family_word.capitalize()} flipped open the starboard locker, "
        f"and out came {tool.phrase}. {tool.surprise}"
    )


def rescue(world: World, child: Entity, elder: Entity, runaway: Runaway, tool: Tool,
           harbor: Harbor, weather: Weather) -> None:
    item = world.get("item")
    clean = clean_recovery(runaway, tool, harbor, weather)
    item.meters["recovered"] += 1
    item.meters["loose"] = 0.0
    if not clean:
        item.meters["scruffy"] += 1
    propagate(world)
    world.say(tool.action)
    if clean:
        world.say(
            f"It worked on the first brave try. In another moment {runaway.label} was safe aboard, "
            f"and the schooner rocked with the happy sort of pride that makes wood creak like a smile."
        )
    else:
        world.say(
            f"The first reach missed, and the second reach made everyone suck in a breath. "
            f"But on the third try the schooner nosed close enough, and {runaway.label} came back "
            f"aboard a little rumpled and dripping, but rescued all the same."
        )


def ending(world: World, child: Entity, elder: Entity, runaway: Runaway, tool: Tool) -> None:
    item = world.get("item")
    child.memes["lesson"] += 1
    if item.meters["scruffy"] >= THRESHOLD:
        world.say(
            f"People on the dock clapped hard enough to startle the gulls. {child.id} hugged "
            f"{elder.family_word}'s middle and laughed when a few drops from {runaway.label} "
            f"spattered both their shoes."
        )
        world.say(
            f'"Next time," {child.id} said, "we tie things down before they try to become legends." '
            f'{elder.family_word.capitalize()} nodded, and together they set {runaway.image} where the '
            f"whole fair could see it had come home."
        )
    else:
        world.say(
            f"Back at the dock, the crowd cheered as if the little schooner had hauled in a whale the "
            f"size of the town hall. {child.id} stood taller than the mast felt."
        )
        world.say(
            f'"Next time," {child.id} promised, "I will remember the calm trick before the trouble starts." '
            f'{elder.family_word.capitalize()} squeezed {child.pronoun("possessive")} shoulder, and together '
            f"they set {runaway.image} where the whole fair could shine around it."
        )
    world.facts["clean"] = item.meters["scruffy"] < THRESHOLD


def tell(harbor: Harbor, runaway: Runaway, tool: Tool, weather: Weather,
         child_name: str = "Mina", child_gender: str = "girl",
         elder_type: str = "grandfather") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, role="elder", label="the elder"))
    world.add(Entity(id="harbor", type="place", label=harbor.place))
    world.add(Entity(id="schooner", type="boat", label="schooner", phrase="the family schooner"))
    world.add(Entity(id="item", type="runaway", label=runaway.label, phrase=runaway.phrase, tags=set(runaway.tags)))
    world.add(Entity(id="tool", type="tool", label=tool.label, phrase=tool.phrase, tags=set(tool.tags)))

    introduce(world, child, elder, harbor, weather)
    admire(world, child, elder)

    world.para()
    trouble(world, child, elder, runaway)
    flashback(world, child, elder, runaway)

    world.para()
    launch(world, child, elder, runaway)
    reveal_tool(world, elder, tool)
    rescue(world, child, elder, runaway, tool, harbor, weather)

    world.para()
    ending(world, child, elder, runaway, tool)

    world.facts.update(
        child=child,
        elder=elder,
        harbor_cfg=harbor,
        runaway_cfg=runaway,
        tool_cfg=tool,
        weather_cfg=weather,
        difficulty=difficulty(runaway, harbor, weather),
        clean=world.get("item").meters["scruffy"] < THRESHOLD,
    )
    return world


HARBORS = {
    "wharf": Harbor(
        id="wharf",
        place="the old wharf",
        opener="At the old wharf, bunting fluttered from every post",
        tall_detail="Even the pilings looked as if they were trying to stand on tiptoe and see over the sea.",
        water_bonus=0,
        air_bonus=0,
        tags={"harbor"},
    ),
    "cove": Harbor(
        id="cove",
        place="lighthouse cove",
        opener="At lighthouse cove, the striped tower winked over the water",
        tall_detail="The gulls swooped around it so slowly they might have been turning the whole sky with string.",
        water_bonus=1,
        air_bonus=0,
        tags={"harbor", "lighthouse"},
    ),
    "river_mouth": Harbor(
        id="river_mouth",
        place="the river mouth dock",
        opener="At the river mouth dock, boats bumped the pilings like eager horses",
        tall_detail="The tide there always hurried as if it had somewhere grand to be before supper.",
        water_bonus=0,
        air_bonus=1,
        tags={"harbor", "river"},
    ),
}

WEATHERS = {
    "bright": Weather(
        id="bright",
        line="The sun was bright, and a playful breeze kept patting the flags.",
        air_bonus=0,
        water_bonus=0,
        tags={"wind"},
    ),
    "gusty": Weather(
        id="gusty",
        line="The wind kept puffing its cheeks and shoving at every loose thing it could find.",
        air_bonus=1,
        water_bonus=0,
        tags={"wind"},
    ),
    "choppy": Weather(
        id="choppy",
        line="The bay wore short choppy waves, each one slapping the next as if racing for first place.",
        air_bonus=0,
        water_bonus=1,
        tags={"water"},
    ),
}

RUNAWAYS = {
    "kite": Runaway(
        id="kite",
        label="the giant kite",
        phrase="the giant kite shaped like a blue marlin",
        mode="air",
        fragile=True,
        opener="A fair helper let go for one tiny second, and the giant kite shaped like a blue marlin gave one mighty tug.",
        chase="It skimmed over the water so fast that even the gulls seemed surprised to be left behind.",
        image="the blue marlin kite, still proud and fluttering",
        difficulty=2,
        tags={"kite", "wind"},
    ),
    "banner": Runaway(
        id="banner",
        label="the mayor's banner",
        phrase="the long silk banner from the mayor's stand",
        mode="air",
        fragile=True,
        opener="A gust barged in like an uninvited giant and yanked the silk banner straight off the mayor's stand.",
        chase="The banner streamed out over the harbor, curling and snapping like a bright red river in the sky.",
        image="the long silk banner, smooth again and glowing in the light",
        difficulty=2,
        tags={"banner", "wind"},
    ),
    "lantern": Runaway(
        id="lantern",
        label="the parade lantern",
        phrase="the painted parade lantern shaped like a moon",
        mode="water",
        fragile=False,
        opener="A bump from the crowd nudged the painted parade lantern off its table and plop into the bay it went.",
        chase="It bobbed away between the pilings, looking far too pleased with itself.",
        image="the moon lantern, hung high and shining again",
        difficulty=2,
        tags={"lantern", "water"},
    ),
    "pie_pan": Runaway(
        id="pie_pan",
        label="the pie pan",
        phrase="the shiny pie pan from the baking tent",
        mode="water",
        fragile=False,
        opener="Someone set a cooling pie pan too near the edge, and the tide stole it as neatly as a fox steals a nap.",
        chase="The pan spun over the water, flashing silver in the sun like a fish that had learned table manners.",
        image="the pie pan, safe at last with its blue ribbon tied to the handle",
        difficulty=1,
        tags={"pie", "water"},
    ),
}

TOOLS = {
    "trail_line": Tool(
        id="trail_line",
        label="the bright trail line",
        phrase="a bright coil of trail line",
        modes={"air"},
        gentle=True,
        power=2,
        surprise="It was so neatly wound that it looked like a cinnamon roll made by a sailor.",
        action="With one careful cast, the bright line drifted over the flying prize, and Elder drew it in hand over hand, calm as if reeling in a sleepy cloud.",
        qa_text="used the bright trail line to catch it gently",
        tags={"rope"},
    ),
    "spare_sail": Tool(
        id="spare_sail",
        label="the spare sail",
        phrase="the little spare sail",
        modes={"air"},
        gentle=True,
        power=3,
        surprise="Folded small, it had been hiding there like a secret white bird waiting for its cue.",
        action="Elder snapped the spare sail open, and the cloth bellied out in the wind until it became a soft white wall. The runaway thing blundered right into it and settled down as meek as a napkin in a drawer.",
        qa_text="opened the spare sail like a soft catching wall",
        tags={"sail"},
    ),
    "scoop_net": Tool(
        id="scoop_net",
        label="the scoop net",
        phrase="a wide scoop net with a smooth rim",
        modes={"water"},
        gentle=True,
        power=2,
        surprise="The net had been tucked behind a coil of rope, quiet as a sleeping cat.",
        action="Child held the rail while Elder dipped the scoop net low and slid it beneath the drifting prize without even splashing the paint.",
        qa_text="slid the scoop net under it",
        tags={"net"},
    ),
    "boat_hook": Tool(
        id="boat_hook",
        label="the boat hook",
        phrase="a long ash boat hook",
        modes={"water"},
        gentle=False,
        power=3,
        surprise="Its polished handle shone as if it had spent the morning swallowing sunshine.",
        action="Elder reached out with the boat hook and caught the runaway prize by its handle, then swung it aboard in one smooth pull.",
        qa_text="caught it with the boat hook and pulled it aboard",
        tags={"hook"},
    ),
}


GIRL_NAMES = ["Mina", "Lila", "Tess", "Nora", "June", "Ava", "Mabel", "Ruth"]
BOY_NAMES = ["Owen", "Finn", "Cal", "Eli", "Miles", "Theo", "Jude", "Beck"]


@dataclass
class StoryParams:
    harbor: str
    runaway: str
    tool: str
    weather: str
    child_name: str
    child_gender: str
    elder_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        harbor="wharf",
        runaway="kite",
        tool="spare_sail",
        weather="gusty",
        child_name="Mina",
        child_gender="girl",
        elder_type="grandfather",
    ),
    StoryParams(
        harbor="cove",
        runaway="lantern",
        tool="scoop_net",
        weather="choppy",
        child_name="Owen",
        child_gender="boy",
        elder_type="grandmother",
    ),
    StoryParams(
        harbor="river_mouth",
        runaway="banner",
        tool="trail_line",
        weather="gusty",
        child_name="Lila",
        child_gender="girl",
        elder_type="grandfather",
    ),
    StoryParams(
        harbor="wharf",
        runaway="pie_pan",
        tool="boat_hook",
        weather="bright",
        child_name="Finn",
        child_gender="boy",
        elder_type="grandmother",
    ),
    StoryParams(
        harbor="cove",
        runaway="kite",
        tool="trail_line",
        weather="gusty",
        child_name="June",
        child_gender="girl",
        elder_type="grandmother",
    ),
]


KNOWLEDGE = {
    "harbor": [
        (
            "What is a harbor?",
            "A harbor is a safe place by the water where boats can stop, tie up, and load things."
        )
    ],
    "lighthouse": [
        (
            "What does a lighthouse do?",
            "A lighthouse shines a strong light to help boats know where the shore and rocks are."
        )
    ],
    "river": [
        (
            "What is a river mouth?",
            "A river mouth is the place where river water meets bigger water like a bay or the sea."
        )
    ],
    "rope": [
        (
            "What is a line on a boat?",
            "On a boat, a line is a rope. Sailors use lines to tie things, pull things, and keep things from blowing away."
        )
    ],
    "sail": [
        (
            "What does a sail do?",
            "A sail catches the wind and helps move a boat. A small spare sail can also help block or catch a light flying thing."
        )
    ],
    "net": [
        (
            "What is a scoop net for?",
            "A scoop net is for lifting something out of the water gently. The wide net helps hold the thing without poking it."
        )
    ],
    "hook": [
        (
            "What is a boat hook?",
            "A boat hook is a long pole with a hook on the end. Grown-ups use it to pull floating things closer to the boat."
        )
    ],
    "kite": [
        (
            "Why does wind carry a kite away?",
            "A kite is light and broad, so the wind can push and lift it. If it is not held tight, it can fly off."
        )
    ],
    "banner": [
        (
            "Why can a silk banner blow away?",
            "A silk banner is light cloth, and wind can grab cloth like a hand grabbing a blanket."
        )
    ],
    "lantern": [
        (
            "Why does a floating lantern drift?",
            "A floating thing drifts because the water and little waves keep pushing it along."
        )
    ],
    "pie": [
        (
            "Why does a metal pan float away on water?",
            "A shallow pan can bob and slide along if the water carries it. If nobody catches it, the current can move it farther."
        )
    ],
    "wind": [
        (
            "What is a gust?",
            "A gust is a quick strong burst of wind. It can shove loose things all at once."
        )
    ],
    "water": [
        (
            "Why are choppy waves harder for small boats?",
            "Choppy waves make the boat bounce and wobble more. That makes it trickier to reach a drifting thing neatly."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "harbor",
    "lighthouse",
    "river",
    "wind",
    "water",
    "kite",
    "banner",
    "lantern",
    "pie",
    "rope",
    "sail",
    "net",
    "hook",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    runaway = f["runaway_cfg"]
    harbor = f["harbor_cfg"]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the word "schooner" and has a flashback and a surprise.',
        f"Tell a harbor story where {child.id} and {elder.family_word} use a little schooner to chase {runaway.label} at {harbor.place}.",
        f"Write a warm exaggerated story about a runaway fair prize, an old lesson remembered in a flashback, and a surprising rescue tool aboard a schooner.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    runaway = f["runaway_cfg"]
    tool = f["tool_cfg"]
    harbor = f["harbor_cfg"]
    weather = f["weather_cfg"]
    clean = f["clean"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {elder.family_word}, and the family schooner called Morning Star. They were at {harbor.place} for the harbor fair."
        ),
        (
            f"What went wrong at the harbor fair?",
            f"{runaway.label.capitalize()} got loose and rushed away over the harbor. That made the grown-up and child worry because the water or wind could carry it farther."
        ),
        (
            "What was the flashback about?",
            f"{child.id} remembered an older lesson from {elder.family_word} about the schooner handling braggy wind or water. The memory helped {child.pronoun('object')} stay calm enough to try a smart rescue instead of only panicking."
        ),
        (
            "What was the surprise?",
            f"The surprise was that {elder.family_word} opened the locker and pulled out {tool.phrase}. It had been hidden aboard the schooner until just the right moment."
        ),
        (
            f"How did they rescue {runaway.label}?",
            f"They launched the schooner and {tool.qa_text}. That fit the kind of trouble they were chasing in {weather.id} weather."
        ),
    ]
    if clean:
        qa.append(
            (
                "How did the story end?",
                f"It ended happily, with {runaway.label} coming back aboard in good shape and the dock crowd cheering. The ending shows that {child.id} learned to remember a calm lesson before the trouble grows."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended happily but a little soggy or rumpled, because {runaway.label} was rescued after a harder chase. Even so, the safe tool and the schooner brought it home."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["harbor_cfg"].tags) | set(f["weather_cfg"].tags) | set(f["runaway_cfg"].tags) | set(f["tool_cfg"].tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:9} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Tool compatibility.
valid(H, R, T) :- harbor(H), runaway(R), tool(T), supports(T, M), mode(R, M),
                  not fragile(R), not rough_block(R, T).
valid(H, R, T) :- harbor(H), runaway(R), tool(T), supports(T, M), mode(R, M),
                  fragile(R), gentle(T), not rough_block(R, T).

rough_block(R, T) :- fragile(R), not gentle(T).

% Difficulty and outcome.
diff(R, H, W, D0 + HB + WB) :- base_difficulty(R, D0), mode(R, air), air_harbor(H, HB), air_weather(W, WB).
diff(R, H, W, D0 + HB + WB) :- base_difficulty(R, D0), mode(R, water), water_harbor(H, HB), water_weather(W, WB).

clean(R, H, T, W) :- power(T, P), diff(R, H, W, D), P >= D.
outcome(R, H, T, W, clean) :- valid(H, R, T), clean(R, H, T, W).
outcome(R, H, T, W, scruffy) :- valid(H, R, T), not clean(R, H, T, W).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for harbor_id, harbor in HARBORS.items():
        lines.append(asp.fact("harbor", harbor_id))
        lines.append(asp.fact("air_harbor", harbor_id, harbor.air_bonus))
        lines.append(asp.fact("water_harbor", harbor_id, harbor.water_bonus))
    for weather_id, weather in WEATHERS.items():
        lines.append(asp.fact("weather", weather_id))
        lines.append(asp.fact("air_weather", weather_id, weather.air_bonus))
        lines.append(asp.fact("water_weather", weather_id, weather.water_bonus))
    for runaway_id, runaway in RUNAWAYS.items():
        lines.append(asp.fact("runaway", runaway_id))
        lines.append(asp.fact("mode", runaway_id, runaway.mode))
        lines.append(asp.fact("base_difficulty", runaway_id, runaway.difficulty))
        if runaway.fragile:
            lines.append(asp.fact("fragile", runaway_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("power", tool_id, tool.power))
        if tool.gentle:
            lines.append(asp.fact("gentle", tool_id))
        for mode in sorted(tool.modes):
            lines.append(asp.fact("supports", tool_id, mode))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_harbor", params.harbor),
            asp.fact("chosen_runaway", params.runaway),
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_weather", params.weather),
            "picked_outcome(K) :- outcome(R,H,T,W,K), chosen_runaway(R), chosen_harbor(H), chosen_tool(T), chosen_weather(W).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show picked_outcome/1."))
    atoms = asp.atoms(model, "picked_outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    runaway = RUNAWAYS[params.runaway]
    tool = TOOLS[params.tool]
    harbor = HARBORS[params.harbor]
    weather = WEATHERS[params.weather]
    return "clean" if clean_recovery(runaway, tool, harbor, weather) else "scruffy"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for seed in range(20):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print("Unexpected StoryError during random resolve.")
            break

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcome cases differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive in CLI verify
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Tall-tale storyworld: a child, a schooner, a flashback, a surprise rescue."
    )
    ap.add_argument("--harbor", choices=HARBORS)
    ap.add_argument("--runaway", choices=RUNAWAYS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.runaway and args.tool:
        runaway = RUNAWAYS[args.runaway]
        tool = TOOLS[args.tool]
        if not compatible(runaway, tool):
            raise StoryError(explain_rejection(runaway, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.harbor is None or combo[0] == args.harbor)
        and (args.runaway is None or combo[1] == args.runaway)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    harbor_id, runaway_id, tool_id = rng.choice(sorted(combos))
    weather_id = args.weather or rng.choice(sorted(WEATHERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])

    return StoryParams(
        harbor=harbor_id,
        runaway=runaway_id,
        tool=tool_id,
        weather=weather_id,
        child_name=child_name,
        child_gender=gender,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.harbor not in HARBORS:
        raise StoryError(f"(Unknown harbor: {params.harbor})")
    if params.runaway not in RUNAWAYS:
        raise StoryError(f"(Unknown runaway item: {params.runaway})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.weather not in WEATHERS:
        raise StoryError(f"(Unknown weather: {params.weather})")

    runaway = RUNAWAYS[params.runaway]
    tool = TOOLS[params.tool]
    if not compatible(runaway, tool):
        raise StoryError(explain_rejection(runaway, tool))

    world = tell(
        harbor=HARBORS[params.harbor],
        runaway=runaway,
        tool=tool,
        weather=WEATHERS[params.weather],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
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
        print(asp_program("", "#show valid/3.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (harbor, runaway, tool) combos:\n")
        for harbor, runaway, tool in combos:
            print(f"  {harbor:12} {runaway:10} {tool}")
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
            header = f"### {p.child_name}: {p.runaway} at {p.harbor} with {p.tool} ({outcome_of(p)})"
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
