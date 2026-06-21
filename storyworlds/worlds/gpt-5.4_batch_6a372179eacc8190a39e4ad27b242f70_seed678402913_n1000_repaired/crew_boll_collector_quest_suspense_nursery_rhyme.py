#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crew_boll_collector_quest_suspense_nursery_rhyme.py
==============================================================================

A standalone story world for a tiny nursery-rhyme-style quest: a little crew
helps a kindly boll collector chase one runaway cotton boll before it is lost.

The domain is deliberately small and constraint-checked. A place affords a
certain kind of hazard; a rescue tool is only allowed when it honestly matches
that hazard. The same logic is mirrored by an inline ASP twin for --verify.

Run it
------
python storyworlds/worlds/gpt-5.4/crew_boll_collector_quest_suspense_nursery_rhyme.py
python storyworlds/worlds/gpt-5.4/crew_boll_collector_quest_suspense_nursery_rhyme.py --place cotton_row --hazard thorn_bush
python storyworlds/worlds/gpt-5.4/crew_boll_collector_quest_suspense_nursery_rhyme.py --tool ladder_hook
python storyworlds/worlds/gpt-5.4/crew_boll_collector_quest_suspense_nursery_rhyme.py --all
python storyworlds/worlds/gpt-5.4/crew_boll_collector_quest_suspense_nursery_rhyme.py --qa --json
python storyworlds/worlds/gpt-5.4/crew_boll_collector_quest_suspense_nursery_rhyme.py --verify
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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
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
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "woman"}
        male = {"boy", "father", "man", "rooster"}
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
    opening: str
    path_word: str
    tags: set[str] = field(default_factory=set)
    hazards: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    danger: str
    chant: str
    risk: str
    verb: str
    harms: set[str] = field(default_factory=set)
    needed_tools: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use_line: str
    verbs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class CrewKind:
    id: str
    noun: str
    chant: str
    move_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CollectorKind:
    id: str
    type: str
    title: str
    basket: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hazard: str
    tool: str
    crew: str
    collector: str
    child_name: str
    child_gender: str
    collector_name: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_tangle(world: World) -> list[str]:
    boll = world.get("boll")
    if boll.meters["caught"] < THRESHOLD:
        return []
    sig = ("tangle", "boll")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("crew").memes["worry"] += 1
    world.get("child").memes["worry"] += 1
    world.get("collector").memes["worry"] += 1
    return ["The white boll hung still, and every heart gave a tiny thump."]


def _r_soggy(world: World) -> list[str]:
    boll = world.get("boll")
    if boll.meters["soggy"] < THRESHOLD:
        return []
    sig = ("soggy", "boll")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("collector").memes["sad"] += 1
    world.get("child").memes["worry"] += 1
    return ["The boll drank water like a sponge, and the basket song went quiet."]


def _r_wobble(world: World) -> list[str]:
    boll = world.get("boll")
    if boll.meters["teetering"] < THRESHOLD:
        return []
    sig = ("wobble", "boll")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("crew", "child", "collector"):
        world.get(eid).memes["worry"] += 1
    return ["The boll wobbled at the edge, not in and not out."]


def _r_chased(world: World) -> list[str]:
    boll = world.get("boll")
    if boll.meters["snatched"] < THRESHOLD:
        return []
    sig = ("chased", "boll")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("crew").memes["alarm"] += 1
    world.get("child").memes["alarm"] += 1
    return ["A greedy wing beat overhead, and the little crew held its breath."]


CAUSAL_RULES = [
    Rule(name="tangle", tag="hazard", apply=_r_tangle),
    Rule(name="soggy", tag="hazard", apply=_r_soggy),
    Rule(name="wobble", tag="hazard", apply=_r_wobble),
    Rule(name="chased", tag="hazard", apply=_r_chased),
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
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "cotton_row": Place(
        id="cotton_row",
        label="the cotton row",
        opening="Down by the cotton row, where white puffs bobbed to and fro,",
        path_word="row",
        tags={"farm", "cotton"},
        hazards={"thorn_bush", "mud_puddle"},
    ),
    "mill_path": Place(
        id="mill_path",
        label="the mill path",
        opening="Along the mill path, where the wind said hush-hush-low,",
        path_word="path",
        tags={"windmill", "path"},
        hazards={"ditch_edge", "crow_nest"},
    ),
    "pumpkin_patch": Place(
        id="pumpkin_patch",
        label="the pumpkin patch",
        opening="Round the pumpkin patch, where vines liked to curl and grow,",
        path_word="patch",
        tags={"garden", "vines"},
        hazards={"thorn_bush", "crow_nest", "mud_puddle"},
    ),
}

HAZARDS = {
    "thorn_bush": Hazard(
        id="thorn_bush",
        label="thorn bush",
        danger="caught",
        chant="Snip-snap, cling-clap, mind the prickly bush!",
        risk="The fluffy boll could snag in the thorn bush and tear.",
        verb="snag",
        harms={"torn"},
        needed_tools={"ribbon_loop", "ladder_hook"},
        tags={"thorn", "careful"},
    ),
    "mud_puddle": Hazard(
        id="mud_puddle",
        label="mud puddle",
        danger="soggy",
        chant="Plip-plop, slip-slop, mind the muddy pool!",
        risk="If the boll splashed into the mud puddle, it would turn soggy and brown.",
        verb="splash",
        harms={"wet", "muddy"},
        needed_tools={"reed_scoop", "umbrella_cover"},
        tags={"mud", "water"},
    ),
    "ditch_edge": Hazard(
        id="ditch_edge",
        label="ditch edge",
        danger="teetering",
        chant="Tip-tap, near-nap, mind the narrow side!",
        risk="The boll could tumble over the ditch edge where little hands could not reach.",
        verb="tumble",
        harms={"lost"},
        needed_tools={"ladder_hook", "reed_scoop"},
        tags={"ditch", "careful"},
    ),
    "crow_nest": Hazard(
        id="crow_nest",
        label="crow nest",
        danger="snatched",
        chant="Caw-call, dark shawl, mind the nesting crow!",
        risk="A crow might grab the soft boll for its nest and fly off with it.",
        verb="snatch",
        harms={"stolen"},
        needed_tools={"umbrella_cover", "ribbon_loop"},
        tags={"crow", "bird"},
    ),
}

TOOLS = {
    "reed_scoop": Tool(
        id="reed_scoop",
        label="reed scoop",
        phrase="a bendy reed scoop",
        use_line="slid the bendy scoop beneath the boll and lifted it up",
        verbs={"scoop", "lift"},
        tags={"scoop", "reach"},
    ),
    "ribbon_loop": Tool(
        id="ribbon_loop",
        label="ribbon loop",
        phrase="a blue ribbon loop",
        use_line="flipped the ribbon loop around the boll and drew it free",
        verbs={"loop", "draw"},
        tags={"ribbon", "gentle"},
    ),
    "ladder_hook": Tool(
        id="ladder_hook",
        label="ladder hook",
        phrase="a small ladder hook",
        use_line="reached with the little hook and tugged the boll back to safety",
        verbs={"hook", "tug"},
        tags={"hook", "reach"},
    ),
    "umbrella_cover": Tool(
        id="umbrella_cover",
        label="umbrella cover",
        phrase="a bright yellow umbrella",
        use_line="popped the umbrella open over the boll and guided it home beneath the shade",
        verbs={"cover", "shield"},
        tags={"umbrella", "shield"},
    ),
}

CREWS = {
    "ducklings": CrewKind(
        id="ducklings",
        noun="duckling crew",
        chant="Quack-quick, quack-quick, patter in a row!",
        move_line="The duckling crew pattered after it in a bobbing line.",
        tags={"duckling", "crew"},
    ),
    "mice": CrewKind(
        id="mice",
        noun="mouse crew",
        chant="Squeak-sneak, squeak-sneak, whiskers all aglow!",
        move_line="The mouse crew scampered after it with whiskers twitching.",
        tags={"mouse", "crew"},
    ),
    "lambs": CrewKind(
        id="lambs",
        noun="lamb crew",
        chant="Skip-step, skip-step, soft as winter snow!",
        move_line="The lamb crew skipped after it with tiny bells jingling.",
        tags={"lamb", "crew"},
    ),
}

COLLECTORS = {
    "robin": CollectorKind(
        id="robin",
        type="rooster",
        title="boll collector",
        basket="a willow basket",
        lesson="Soft things are safest when kind hands move slowly.",
        tags={"collector", "basket"},
    ),
    "hen": CollectorKind(
        id="hen",
        type="hen",
        title="boll collector",
        basket="a little patchwork basket",
        lesson="A careful crew can save a small thing from a big mishap.",
        tags={"collector", "basket"},
    ),
    "farmer": CollectorKind(
        id="farmer",
        type="father",
        title="boll collector",
        basket="a warm straw basket",
        lesson="When trouble tiptoes near, calm steps beat hurried feet.",
        tags={"collector", "basket"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Tom", "Max", "Leo", "Finn", "Eli"]


def valid_combo(place_id: str, hazard_id: str, tool_id: str) -> bool:
    if place_id not in PLACES or hazard_id not in HAZARDS or tool_id not in TOOLS:
        return False
    place = PLACES[place_id]
    hazard = HAZARDS[hazard_id]
    tool = TOOLS[tool_id]
    return hazard.id in place.hazards and tool.id in hazard.needed_tools


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for hazard_id in sorted(place.hazards):
            hazard = HAZARDS[hazard_id]
            for tool_id in sorted(hazard.needed_tools):
                if valid_combo(place_id, hazard_id, tool_id):
                    combos.append((place_id, hazard_id, tool_id))
    return combos


def explain_rejection(place_id: str, hazard_id: str, tool_id: Optional[str] = None) -> str:
    if place_id not in PLACES:
        return "(No story: that place is not known in this world.)"
    if hazard_id not in HAZARDS:
        return "(No story: that hazard is not known in this world.)"
    place = PLACES[place_id]
    hazard = HAZARDS[hazard_id]
    if hazard.id not in place.hazards:
        return (
            f"(No story: {hazard.label} does not fit {place.label}. "
            f"Choose a hazard that belongs on that {place.path_word}.)"
        )
    if tool_id is not None:
        if tool_id not in TOOLS:
            return "(No story: that tool is not known in this world.)"
        tool = TOOLS[tool_id]
        if tool.id not in hazard.needed_tools:
            good = ", ".join(sorted(hazard.needed_tools))
            return (
                f"(No story: {tool.label} is not a sensible fix for {hazard.label}. "
                f"Try one of: {good}.)"
            )
    return "(No story: this combination does not make a reasonable quest.)"


def predict_danger(world: World, hazard: Hazard) -> dict:
    sim = world.copy()
    boll = sim.get("boll")
    if hazard.danger == "caught":
        boll.meters["caught"] += 1
    elif hazard.danger == "soggy":
        boll.meters["soggy"] += 1
    elif hazard.danger == "teetering":
        boll.meters["teetering"] += 1
    elif hazard.danger == "snatched":
        boll.meters["snatched"] += 1
    propagate(sim, narrate=False)
    return {
        "worry": sum(sim.get(eid).memes["worry"] + sim.get(eid).memes["alarm"] for eid in ("crew", "child", "collector")),
        "danger": hazard.danger,
    }


def introduce(world: World, child: Entity, crew: Entity, collector: Entity, boll: Entity) -> None:
    place = world.place
    world.say(place.opening)
    world.say(
        f"{child.id} walked there with the {crew.label} and {collector.id} the {collector.attrs['title']}."
    )
    world.say(
        f"In {collector.pronoun('possessive')} {collector.attrs['basket']}, the soft white {boll.label} sat light as a cloud."
    )
    for eid in ("child", "crew", "collector"):
        world.get(eid).memes["hope"] += 1


def quest_call(world: World, child: Entity, crew: Entity, collector: Entity, boll: Entity) -> None:
    crew.memes["joy"] += 1
    child.memes["joy"] += 1
    world.say(
        f'"Count them, count them, one by one," sang {collector.id}. '
        f'"Every cotton boll we gather makes the morning work half done."'
    )
    world.say(crew.attrs["chant"])
    world.say(
        f"Then puff! a playful wind hopped up, and one tiny boll bounced from the basket and rolled away."
    )


def chase(world: World, crew: Entity) -> None:
    crew.memes["alert"] += 1
    world.say(crew.attrs["move_line"])


def warning(world: World, child: Entity, collector: Entity, hazard: Hazard) -> None:
    pred = predict_danger(world, hazard)
    world.facts["predicted_worry"] = pred["worry"]
    world.facts["risk"] = hazard.risk
    world.say(
        f'{collector.id} peered ahead and whispered, "{hazard.risk}"'
    )
    extra = " Even the breeze seemed to hush." if pred["worry"] >= 2 else ""
    world.say(f"{hazard.chant}{extra}")


def hazard_strikes(world: World, hazard: Hazard, boll: Entity) -> None:
    if hazard.danger == "caught":
        boll.meters["caught"] += 1
    elif hazard.danger == "soggy":
        boll.meters["soggy"] += 1
    elif hazard.danger == "teetering":
        boll.meters["teetering"] += 1
    elif hazard.danger == "snatched":
        boll.meters["snatched"] += 1
    propagate(world, narrate=True)
    if hazard.id == "thorn_bush":
        world.say("The runaway boll skipped once, twice, and snagged on a prickly branch.")
    elif hazard.id == "mud_puddle":
        world.say("The runaway boll spun at the rim of a muddy puddle and kissed the brown splash.")
    elif hazard.id == "ditch_edge":
        world.say("The runaway boll rolled to the ditch edge and tipped on the crumbly lip.")
    elif hazard.id == "crow_nest":
        world.say("A black crow swooped low, and the runaway boll rose in its beak like a stolen snowball.")


def rescue(world: World, child: Entity, collector: Entity, crew: Entity, tool: Tool, hazard: Hazard, boll: Entity) -> None:
    child.memes["bravery"] += 1
    collector.memes["relief"] += 1
    crew.memes["relief"] += 1
    boll.meters["safe"] += 1
    boll.meters["caught"] = 0.0
    boll.meters["soggy"] = 0.0
    boll.meters["teetering"] = 0.0
    boll.meters["snatched"] = 0.0
    world.say(
        f'{child.id} did not stomp or rush. {child.pronoun().capitalize()} took {tool.phrase} and {tool.use_line}.'
    )
    if hazard.id == "mud_puddle":
        world.say("Not a drop more touched the fluff, and the boll stayed bright enough for the basket.")
    elif hazard.id == "thorn_bush":
        world.say("The thorns let go with a tiny tick, and not one white thread was torn.")
    elif hazard.id == "ditch_edge":
        world.say("Back from the edge it came, safe from the dark little dip below.")
    elif hazard.id == "crow_nest":
        world.say("The startled crow flapped off with a cranky caw, and the boll drifted safely down.")
    world.say(
        f'Soon {collector.id} tucked the boll into {collector.attrs["basket"]} and let out a long, happy breath.'
    )


def ending(world: World, child: Entity, collector: Entity, crew: Entity, boll: Entity) -> None:
    for eid in ("child", "crew", "collector"):
        world.get(eid).memes["joy"] += 1
    world.say(
        f'"Round and sound, soft and small, back you go, dear little boll," sang {collector.id}.'
    )
    world.say(
        f'{child.id} and the {crew.label} marched home beside the basket, and the whole {crew.label} felt taller than before.'
    )
    world.say(
        f"From then on, whenever a breeze came nosing near, they remembered: {collector.attrs['lesson']}"
    )


def tell(
    place: Place,
    hazard: Hazard,
    tool: Tool,
    crew_cfg: CrewKind,
    collector_cfg: CollectorKind,
    child_name: str,
    child_gender: str,
    collector_name: str,
    parent_type: str,
) -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=["small", "steady"],
        tags={"child"},
    ))
    crew = world.add(Entity(
        id="Crew",
        kind="character",
        type="group",
        label=crew_cfg.noun,
        role="crew",
        attrs={"chant": crew_cfg.chant, "move_line": crew_cfg.move_line},
        tags=set(crew_cfg.tags),
    ))
    collector = world.add(Entity(
        id=collector_name,
        kind="character",
        type=collector_cfg.type,
        label=collector_name,
        role="collector",
        attrs={
            "title": collector_cfg.title,
            "basket": collector_cfg.basket,
            "lesson": collector_cfg.lesson,
            "parent_type": parent_type,
        },
        tags=set(collector_cfg.tags),
    ))
    boll = world.add(Entity(
        id="boll",
        kind="thing",
        type="boll",
        label="boll",
        phrase="a soft white cotton boll",
        owner=collector.id,
        tags={"boll", "cotton"},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))

    introduce(world, child, crew, collector, boll)
    world.para()
    quest_call(world, child, crew, collector, boll)
    chase(world, crew)
    warning(world, child, collector, hazard)
    world.para()
    hazard_strikes(world, hazard, boll)
    world.para()
    rescue(world, child, collector, crew, tool, hazard, boll)
    ending(world, child, collector, crew, boll)

    world.facts.update(
        child=child,
        crew=crew,
        collector=collector,
        boll=boll,
        parent=parent,
        place=place,
        hazard=hazard,
        tool=tool,
        safe=boll.meters["safe"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "boll": [
        ("What is a cotton boll?",
         "A cotton boll is the fluffy part of a cotton plant where the soft cotton grows. When it opens, it looks like a little white puff.")
    ],
    "collector": [
        ("What does a collector do?",
         "A collector gathers things carefully and keeps them together. In this story world, the boll collector gathers cotton bolls into a basket.")
    ],
    "crew": [
        ("What is a crew?",
         "A crew is a little team that works or travels together. A good crew watches one another and helps with the same job.")
    ],
    "thorn": [
        ("Why are thorns tricky?",
         "Thorns are sharp points on some plants. Soft things can catch on them and tear if you pull too hard.")
    ],
    "mud": [
        ("Why is mud hard on fluffy things?",
         "Mud is wet dirt, so it sticks and stains. A fluffy thing that falls into mud gets heavy and messy very quickly.")
    ],
    "ditch": [
        ("What is a ditch?",
         "A ditch is a narrow hollow or trench in the ground. Small things can tumble into it and become hard to reach.")
    ],
    "crow": [
        ("Why might a crow take soft fluff?",
         "Some birds carry soft bits to their nests. A crow might grab fluff because it seems useful for lining a nest.")
    ],
    "umbrella": [
        ("What does an umbrella do?",
         "An umbrella makes a cover over something. It can shield a thing from rain or from a bird swooping down.")
    ],
    "hook": [
        ("What is a hook tool for?",
         "A hook can catch something gently from a distance and pull it back. It helps when a thing is too far away for hands.")
    ],
    "scoop": [
        ("What is a scoop used for?",
         "A scoop slips underneath something and lifts it. It is useful when a thing is low, wet, or close to falling.")
    ],
    "ribbon": [
        ("Why use a ribbon loop gently?",
         "A ribbon is soft and bendy, so it can hold a delicate thing without scratching it. Gentle tools are best for gentle things.")
    ],
}
KNOWLEDGE_ORDER = ["crew", "collector", "boll", "thorn", "mud", "ditch", "crow", "umbrella", "hook", "scoop", "ribbon"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    hazard = f["hazard"]
    tool = f["tool"]
    crew = f["crew"]
    collector = f["collector"]
    return [
        f'Write a short nursery-rhyme-style quest story for a 3-to-5-year-old that includes the words "crew", "boll", and "collector".',
        f"Tell a suspenseful but gentle story where {child.id} and a {crew.label} help a boll collector recover one runaway boll at {place.label}.",
        f"Write a rhythmic story where a soft boll is nearly lost to a {hazard.label}, but {child.id} uses {tool.phrase} to save it."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    crew = f["crew"]
    collector = f["collector"]
    place = f["place"]
    hazard = f["hazard"]
    tool = f["tool"]
    risk = f.get("risk", hazard.risk)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a {crew.label}, and {collector.id} the boll collector. Together they go after one runaway cotton boll."
        ),
        (
            "What was their quest?",
            f"Their quest was to bring one little boll back to {collector.id}'s basket. The boll had bounced away, so they had to follow it across {place.label}."
        ),
        (
            f"Why did everyone feel suspense when the boll reached the {hazard.label}?",
            f"They felt suspense because {risk} The danger was close enough that one wrong moment could have spoiled or lost the boll."
        ),
        (
            f"How did {child.id} save the boll?",
            f"{child.id} used {tool.phrase} and {tool.use_line}. That worked because it matched the danger at the {hazard.label} instead of making the chase rougher."
        ),
        (
            "How did the story end?",
            f"The boll went safely back into the basket, and the whole crew walked home feeling proud. The ending shows they had changed from worried chasers into a calm, helpful team."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"crew", "collector", "boll"}
    hazard = f["hazard"]
    tool = f["tool"]
    if "thorn" in hazard.tags:
        tags.add("thorn")
    if "mud" in hazard.tags:
        tags.add("mud")
    if "ditch" in hazard.tags:
        tags.add("ditch")
    if "crow" in hazard.tags:
        tags.add("crow")
    if "umbrella" in tool.tags:
        tags.add("umbrella")
    if "hook" in tool.tags:
        tags.add("hook")
    if "scoop" in tool.tags:
        tags.add("scoop")
    if "ribbon" in tool.tags:
        tags.add("ribbon")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="cotton_row",
        hazard="thorn_bush",
        tool="ribbon_loop",
        crew="ducklings",
        collector="hen",
        child_name="Mia",
        child_gender="girl",
        collector_name="Henny",
        parent="mother",
        seed=1,
    ),
    StoryParams(
        place="mill_path",
        hazard="ditch_edge",
        tool="ladder_hook",
        crew="mice",
        collector="farmer",
        child_name="Ben",
        child_gender="boy",
        collector_name="Farmer Bo",
        parent="father",
        seed=2,
    ),
    StoryParams(
        place="pumpkin_patch",
        hazard="crow_nest",
        tool="umbrella_cover",
        crew="lambs",
        collector="robin",
        child_name="Nora",
        child_gender="girl",
        collector_name="Rufus",
        parent="mother",
        seed=3,
    ),
    StoryParams(
        place="cotton_row",
        hazard="mud_puddle",
        tool="reed_scoop",
        crew="mice",
        collector="hen",
        child_name="Leo",
        child_gender="boy",
        collector_name="Penny",
        parent="father",
        seed=4,
    ),
]


ASP_RULES = r"""
fits_place(P,H) :- place(P), hazard(H), place_has_hazard(P,H).
fits_tool(H,T)  :- hazard(H), tool(T), hazard_needs_tool(H,T).
valid(P,H,T)    :- fits_place(P,H), fits_tool(H,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for hazard_id in sorted(place.hazards):
            lines.append(asp.fact("place_has_hazard", place_id, hazard_id))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        for tool_id in sorted(hazard.needed_tools):
            lines.append(asp.fact("hazard_needs_tool", hazard_id, tool_id))
    for tool_id in TOOLS:
        lines.append(asp.fact("tool", tool_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Nursery-rhyme quest world: a crew helps a boll collector save one runaway boll."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hazard", choices=sorted(HAZARDS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--crew", choices=sorted(CREWS))
    ap.add_argument("--collector", choices=sorted(COLLECTORS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--collector-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (place, hazard, tool) set from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.hazard and not valid_combo(args.place, args.hazard, next(iter(HAZARDS[args.hazard].needed_tools))):
        raise StoryError(explain_rejection(args.place, args.hazard))
    if args.place and args.hazard and args.tool and not valid_combo(args.place, args.hazard, args.tool):
        raise StoryError(explain_rejection(args.place, args.hazard, args.tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, hazard_id, tool_id = rng.choice(sorted(combos))
    crew_id = args.crew or rng.choice(sorted(CREWS))
    collector_id = args.collector or rng.choice(sorted(COLLECTORS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    collector_name = args.collector_name or rng.choice(["Pip", "Moss", "Henny", "Bo", "Rufus", "Tilly"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        hazard=hazard_id,
        tool=tool_id,
        crew=crew_id,
        collector=collector_id,
        child_name=child_name,
        child_gender=gender,
        collector_name=collector_name,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(No story: unknown hazard '{params.hazard}'.)")
    if params.tool not in TOOLS:
        raise StoryError(f"(No story: unknown tool '{params.tool}'.)")
    if params.crew not in CREWS:
        raise StoryError(f"(No story: unknown crew '{params.crew}'.)")
    if params.collector not in COLLECTORS:
        raise StoryError(f"(No story: unknown collector '{params.collector}'.)")
    if not valid_combo(params.place, params.hazard, params.tool):
        raise StoryError(explain_rejection(params.place, params.hazard, params.tool))

    world = tell(
        place=PLACES[params.place],
        hazard=HAZARDS[params.hazard],
        tool=TOOLS[params.tool],
        crew_cfg=CREWS[params.crew],
        collector_cfg=COLLECTORS[params.collector],
        child_name=params.child_name,
        child_gender=params.child_gender,
        collector_name=params.collector_name,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, hazard, tool) combos:\n")
        for place_id, hazard_id, tool_id in combos:
            print(f"  {place_id:13} {hazard_id:12} {tool_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.place}, {p.hazard}, {p.tool}"
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
