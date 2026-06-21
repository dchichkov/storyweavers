#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dishonest_beautician_transformation_lesson_learned_teamwork_superhero.py
====================================================================================================

A standalone story world about a child who wants a superhero transformation,
meets a dishonest beautician who promises powers through a flashy makeover, and
learns through teamwork that real hero work comes from honest helping, not fake
claims.

The domain is deliberately small and constraint-checked:

- A town event presents one practical helper mission.
- A beautician offers a makeover that only *looks* heroic.
- The makeover can create a specific failure mode when the child tries to use it
  as if it were real power.
- A teammate brings a real tool that must actually fit the mission.
- The ending teaches a lesson about honesty and teamwork.

Run it
------
    python storyworlds/worlds/gpt-5.4/dishonest_beautician_transformation_lesson_learned_teamwork_superhero.py
    python storyworlds/worlds/gpt-5.4/dishonest_beautician_transformation_lesson_learned_teamwork_superhero.py --mission dark_shed
    python storyworlds/worlds/gpt-5.4/dishonest_beautician_transformation_lesson_learned_teamwork_superhero.py --makeover wing_glitter
    python storyworlds/worlds/gpt-5.4/dishonest_beautician_transformation_lesson_learned_teamwork_superhero.py --tool flashlight
    python storyworlds/worlds/gpt-5.4/dishonest_beautician_transformation_lesson_learned_teamwork_superhero.py --all
    python storyworlds/worlds/gpt-5.4/dishonest_beautician_transformation_lesson_learned_teamwork_superhero.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/dishonest_beautician_transformation_lesson_learned_teamwork_superhero.py --trace
    python storyworlds/worlds/gpt-5.4/dishonest_beautician_transformation_lesson_learned_teamwork_superhero.py --verify
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
HONESTY_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "beautician"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "mother":
            return "mom"
        if self.type == "father":
            return "dad"
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    image: str
    crowd: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    need: str
    item: str
    place: str
    problem: str
    call: str
    success: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Makeover:
    id: str
    hero_name: str
    boast: str
    look: str
    fake_power: str
    failure: str
    weakness: str
    claims_need: str
    honesty: int
    tags: set[str] = field(default_factory=set)


@dataclass
class TeamTool:
    id: str
    label: str
    phrase: str
    works_for: str
    action: str
    ending: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_false_promise(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["attempted_fake_power"] < THRESHOLD:
        return []
    sig = ("false_promise",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["disappointment"] += 1
    world.get("scene").meters["stuck"] += 1
    return ["__failure__"]


def _r_teamwork(world: World) -> list[str]:
    child = world.get("child")
    pal = world.get("teammate")
    scene = world.get("scene")
    if child.meters["real_help"] < THRESHOLD:
        return []
    if pal.meters["real_help"] < THRESHOLD:
        return []
    sig = ("teamwork",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    scene.meters["problem_solved"] += 1
    child.memes["trust"] += 1
    pal.memes["trust"] += 1
    child.memes["lesson"] += 1
    pal.memes["joy"] += 1
    return ["__teamwork__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="false_promise", tag="social", apply=_r_false_promise),
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
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


SETTINGS = {
    "plaza": Setting(
        id="plaza",
        place="the bright town plaza",
        image="Colorful capes fluttered between paper stars and cardboard buildings.",
        crowd="families clapped around the Hero Helper Day stage",
        tags={"town", "festival"},
    ),
    "library": Setting(
        id="library",
        place="the library courtyard",
        image="Banners with lightning bolts hung between the trees and the book cart.",
        crowd="neighbors gathered for the Hero Helper Day game",
        tags={"town", "library"},
    ),
    "park": Setting(
        id="park",
        place="the park by the fountain",
        image="Long ribbons snapped in the breeze beside the little hero tents.",
        crowd="children lined up for the Hero Helper Day challenge",
        tags={"town", "park"},
    ),
}

MISSIONS = {
    "dark_shed": Mission(
        id="dark_shed",
        need="light",
        item="a lost box of bandages",
        place="the dim tool shed",
        problem="A helper needed to find a lost box of bandages in the dim tool shed.",
        call='"A real hero should shine like a star!"',
        success="together they found the box of bandages tucked behind a bucket",
        risk="The shed was too dark to search by guessing.",
        tags={"light", "helping", "bandages"},
    ),
    "high_branch": Mission(
        id="high_branch",
        need="reach",
        item="a kitten's ribbon",
        place="the low maple branch",
        problem="A helper needed to reach a kitten's ribbon that had snagged on a low maple branch.",
        call='"A real hero should reach up high!"',
        success="together they lifted the ribbon down without tearing it",
        risk="The ribbon was above small hands, but not far enough to need magic.",
        tags={"reach", "helping", "ribbon"},
    ),
    "heavy_box": Mission(
        id="heavy_box",
        need="carry",
        item="a box of juice packs",
        place="the refreshment table",
        problem="A helper needed to move a box of juice packs back to the refreshment table.",
        call='"A real hero should carry the heavy things!"',
        success="together they moved the box of juice packs back to the table",
        risk="The box was awkward for one child but easy for two careful helpers.",
        tags={"carry", "helping", "juice"},
    ),
}

MAKEOVERS = {
    "star_gel": Makeover(
        id="star_gel",
        hero_name="Star Flash",
        boast='"One dab of sparkle gel and you will glow strongly enough to do the job all by yourself," the beautician promised.',
        look="She combed silver gel through the child's hair until it shone under the bunting.",
        fake_power="The child believed the shining hair could light the way.",
        failure="the silver shine only glittered on the outside and could not brighten the dark place at all",
        weakness="Shiny hair is not the same as a real light.",
        claims_need="light",
        honesty=1,
        tags={"beauty", "dishonest", "light"},
    ),
    "wing_glitter": Makeover(
        id="wing_glitter",
        hero_name="Sky Zip",
        boast='"These glitter wings will make you float just high enough to reach anything," the beautician said with a quick smile.',
        look="She dusted the child's shoulders with bright glitter and pinned on paper wings.",
        fake_power="The child believed the paper wings would lift them upward.",
        failure="the paper wings only fluttered and bent, and they did not lift the child even a tiny bit",
        weakness="Pretty wings can twinkle, but they cannot help a child fly.",
        claims_need="reach",
        honesty=1,
        tags={"beauty", "dishonest", "reach"},
    ),
    "power_blush": Makeover(
        id="power_blush",
        hero_name="Mighty Glow",
        boast='"This power blush will fill your arms with superhero strength," the beautician declared.',
        look="She brushed rosy powder across the child's cheeks and tied on a satin cape.",
        fake_power="The child believed the glowing cheeks meant giant strength had arrived.",
        failure="the cape swished nicely, but the child still could not budge the heavy box alone",
        weakness="A brave look is not the same as strong hands and shared work.",
        claims_need="carry",
        honesty=1,
        tags={"beauty", "dishonest", "carry"},
    ),
    "kind_paint": Makeover(
        id="kind_paint",
        hero_name="Kind Spark",
        boast='"I can make you look heroic, but you will still need real tools and a teammate to help anyone," the beautician said honestly.',
        look="She painted a neat star on the child's cheek and straightened the child's cape.",
        fake_power="The child knew the star was only for fun.",
        failure="nothing failed, because the child never expected pretend paint to do a real job",
        weakness="Decorations are for dress-up, not for powers.",
        claims_need="any",
        honesty=3,
        tags={"beauty", "honest", "dressup"},
    ),
}

TOOLS = {
    "flashlight": TeamTool(
        id="flashlight",
        label="flashlight",
        phrase="a sturdy flashlight",
        works_for="light",
        action="clicked on the flashlight and swept a warm beam across the shelves",
        ending="the flashlight made a bright path on the shed wall",
        tags={"flashlight", "teamwork"},
    ),
    "step_stool": TeamTool(
        id="step_stool",
        label="step stool",
        phrase="a folding step stool",
        works_for="reach",
        action="opened the step stool and held it steady while the child reached carefully",
        ending="the step stool stood square and safe beneath the branch",
        tags={"stool", "teamwork"},
    ),
    "wagon": TeamTool(
        id="wagon",
        label="wagon",
        phrase="a little red wagon",
        works_for="carry",
        action="pulled the wagon close so they could load the box together and roll it instead of dragging it",
        ending="the wagon rattled gently behind them over the path",
        tags={"wagon", "teamwork"},
    ),
}

GIRL_NAMES = ["Lily", "Maya", "Nora", "Ava", "Zoe", "Ella", "Lucy", "Mia"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Theo", "Finn", "Jack", "Noah"]
TRAITS = ["eager", "curious", "hopeful", "brave", "helpful", "quick"]
TEAM_TRAITS = ["steady", "calm", "thoughtful", "careful", "cheerful"]


def mission_fits_tool(mission: Mission, tool: TeamTool) -> bool:
    return mission.need == tool.works_for


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for mission_id, mission in MISSIONS.items():
            for makeover_id, makeover in MAKEOVERS.items():
                for tool_id, tool in TOOLS.items():
                    if mission_fits_tool(mission, tool):
                        combos.append((setting_id, mission_id, makeover_id, tool_id))
    return combos


def predicts_failure(makeover: Makeover, mission: Mission) -> bool:
    return makeover.honesty < HONESTY_MIN and makeover.claims_need == mission.need


def predict_scene(mission: Mission, makeover: Makeover, tool: TeamTool) -> dict:
    return {
        "false_promise": predicts_failure(makeover, mission),
        "tool_works": mission_fits_tool(mission, tool),
        "resolved": mission_fits_tool(mission, tool),
    }


def explain_rejection(mission: Mission, tool: TeamTool) -> str:
    return (
        f"(No story: {tool.phrase} helps with {tool.works_for}, but this mission needs "
        f"{mission.need}. The teamwork fix must really solve the problem.)"
    )


@dataclass
class StoryParams:
    setting: str
    mission: str
    makeover: str
    tool: str
    child_name: str
    child_gender: str
    teammate_name: str
    teammate_gender: str
    parent: str
    child_trait: str
    teammate_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="plaza",
        mission="dark_shed",
        makeover="star_gel",
        tool="flashlight",
        child_name="Lily",
        child_gender="girl",
        teammate_name="Ben",
        teammate_gender="boy",
        parent="mother",
        child_trait="eager",
        teammate_trait="steady",
    ),
    StoryParams(
        setting="library",
        mission="high_branch",
        makeover="wing_glitter",
        tool="step_stool",
        child_name="Max",
        child_gender="boy",
        teammate_name="Maya",
        teammate_gender="girl",
        parent="father",
        child_trait="hopeful",
        teammate_trait="careful",
    ),
    StoryParams(
        setting="park",
        mission="heavy_box",
        makeover="power_blush",
        tool="wagon",
        child_name="Ava",
        child_gender="girl",
        teammate_name="Theo",
        teammate_gender="boy",
        parent="mother",
        child_trait="brave",
        teammate_trait="cheerful",
    ),
    StoryParams(
        setting="plaza",
        mission="dark_shed",
        makeover="kind_paint",
        tool="flashlight",
        child_name="Leo",
        child_gender="boy",
        teammate_name="Nora",
        teammate_gender="girl",
        parent="father",
        child_trait="curious",
        teammate_trait="calm",
    ),
]


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def _do_fake_attempt(world: World) -> None:
    child = world.get("child")
    child.meters["attempted_fake_power"] += 1
    propagate(world, narrate=False)


def _do_real_help(world: World) -> None:
    world.get("child").meters["real_help"] += 1
    world.get("teammate").meters["real_help"] += 1
    propagate(world, narrate=False)


def opening(world: World, setting: Setting, child: Entity, teammate: Entity, parent: Entity) -> None:
    world.say(
        f"On Hero Helper Day at {setting.place}, {setting.image} Around them, "
        f"{setting.crowd}."
    )
    world.say(
        f"{child.id} was a {next(iter([t for t in child.traits if t] or ['little']))} {child.type} "
        f"who wanted to look like the grandest hero of all. Beside {child.pronoun('object')}, "
        f"{teammate.id} stayed close, ready to help."
    )
    world.say(
        f"{child.id}'s {parent.label_word} smiled and said, "
        f'"Remember, real heroes help with true hands and honest hearts."'
    )


def beautician_scene(world: World, child: Entity, beautician: Entity, makeover: Makeover) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Near the stage stood a beautician named Mira, with jars of shimmer and trays of ribbons."
    )
    if makeover.honesty < HONESTY_MIN:
        beautician.memes["dishonesty"] += 1
        world.say(
            f"Mira was a dishonest beautician that day, more interested in sounding marvelous than in telling the truth."
        )
    else:
        beautician.memes["honesty"] += 1
        world.say(
            f"Mira was a careful beautician that day, happy to make costumes pretty without pretending they were magic."
        )
    world.say(makeover.boast)
    world.say(makeover.look)
    world.say(
        f'"You are {makeover.hero_name} now," Mira said. {makeover.fake_power}'
    )


def mission_call(world: World, mission: Mission, child: Entity) -> None:
    child.memes["desire"] += 1
    world.say(mission.problem)
    world.say(
        f"{child.id} puffed up proudly and whispered, {mission.call}"
    )
    world.say(mission.risk)


def fake_turn(world: World, child: Entity, makeover: Makeover, mission: Mission) -> None:
    _do_fake_attempt(world)
    child.memes["embarrassment"] += 1
    world.say(
        f"{child.id} hurried toward {mission.place}, trusting the makeover."
    )
    world.say(
        f"But {makeover.failure}."
    )
    world.say(
        f"{child.id} stopped short. {makeover.weakness}"
    )


def teammate_steps_in(world: World, teammate: Entity, tool: TeamTool) -> None:
    teammate.memes["care"] += 1
    world.say(
        f'"Wait," said {teammate.id}, the {teammate.attrs.get("trait_word", "steady")} teammate. '
        f'"We do not need pretend powers. I brought {tool.phrase}."'
    )


def teamwork_fix(world: World, child: Entity, teammate: Entity, tool: TeamTool, mission: Mission) -> None:
    _do_real_help(world)
    child.memes["humility"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{teammate.id} {tool.action}, and {child.id} worked beside {teammate.pronoun('object')} instead of trying to shine alone."
    )
    world.say(
        f"Soon {mission.success}."
    )
    world.say(
        f"{tool.ending}, and the two young heroes grinned at each other."
    )


def lesson_scene(world: World, child: Entity, teammate: Entity, beautician: Entity, parent: Entity, makeover: Makeover) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"Mira the beautician looked at the finished job and her cheeks turned pink."
    )
    if makeover.honesty < HONESTY_MIN:
        world.say(
            f'"I was dishonest," she admitted softly. "I promised powers that a pretty makeover cannot give."'
        )
    else:
        world.say(
            f'"I am glad I only helped with the costume," she said softly.'
        )
    world.say(
        f"{parent.label_word.capitalize()} knelt beside {child.id} and {teammate.id}. "
        f'"That is the lesson real heroes learn," {parent.pronoun()} said. '
        f'"A transformation can start on the outside, but the truest transformation happens when people choose honesty and teamwork."'
    )
    world.say(
        f"{child.id} nodded. \"Next time I will listen for the truth first, and then help with a team.\""
    )


def ending_image(world: World, child: Entity, teammate: Entity, makeover: Makeover, tool: TeamTool) -> None:
    world.say(
        f"Then {child.id} and {teammate.id} walked back under the fluttering banners, still wearing the {makeover.hero_name} costume pieces, "
        f"but now carrying {tool.phrase} between them like real helper gear."
    )
    world.say(
        "They looked less like children pretending to have powers and more like a small superhero team ready to do the next kind thing together."
    )


def tell(
    setting: Setting,
    mission: Mission,
    makeover: Makeover,
    tool: TeamTool,
    child_name: str,
    child_gender: str,
    teammate_name: str,
    teammate_gender: str,
    parent_type: str,
    child_trait: str,
    teammate_trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=[child_trait],
            attrs={"trait_word": child_trait},
        )
    )
    teammate = world.add(
        Entity(
            id="teammate",
            kind="character",
            type=teammate_gender,
            label=teammate_name,
            role="teammate",
            traits=[teammate_trait],
            attrs={"trait_word": teammate_trait},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    beautician = world.add(
        Entity(
            id="beautician",
            kind="character",
            type="beautician",
            label="Mira",
            role="beautician",
        )
    )
    scene = world.add(
        Entity(
            id="scene",
            kind="thing",
            type="scene",
            label=setting.place,
            role="scene",
        )
    )

    child.attrs["name"] = child_name
    teammate.attrs["name"] = teammate_name
    parent.attrs["name"] = parent.label_word
    beautician.attrs["name"] = "Mira"

    opening(world, setting, child, teammate, parent)
    world.para()
    beautician_scene(world, child, beautician, makeover)
    mission_call(world, mission, child)

    world.para()
    if predicts_failure(makeover, mission):
        fake_turn(world, child, makeover, mission)
    else:
        world.say(
            f"{child_name} admired the costume, but remembered that dress-up was still dress-up."
        )
        world.say(
            f"So {child_name} did not expect the makeover to solve {mission.problem[0].lower() + mission.problem[1:]}"
        )

    teammate_steps_in(world, teammate, tool)
    teamwork_fix(world, child, teammate, tool, mission)

    world.para()
    lesson_scene(world, child, teammate, beautician, parent, makeover)
    ending_image(world, child, teammate, makeover, tool)

    outcome = "lesson_learned"
    world.facts.update(
        setting=setting,
        mission=mission,
        makeover=makeover,
        tool=tool,
        child=child,
        teammate=teammate,
        parent=parent,
        beautician=beautician,
        false_promise=predicts_failure(makeover, mission),
        solved=world.get("scene").meters["problem_solved"] >= THRESHOLD,
        outcome=outcome,
    )
    return world


def display_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    teammate = world.facts["teammate"]
    mission = world.facts["mission"]
    makeover = world.facts["makeover"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the words "dishonest" and "beautician."',
        f"Tell a gentle superhero story where {display_name(child)} wants a big transformation, but learns that {mission.need} problems are solved with teamwork instead of pretend powers.",
        f"Write a story in which a beautician offers a {makeover.hero_name} makeover, a child believes it for a moment, and then two children solve the problem together and learn an honest lesson.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    teammate = world.facts["teammate"]
    parent = world.facts["parent"]
    beautician = world.facts["beautician"]
    mission = world.facts["mission"]
    makeover = world.facts["makeover"]
    tool = world.facts["tool"]
    child_name = display_name(child)
    teammate_name = display_name(teammate)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, a child who wanted to look like a superhero, {teammate_name}, a teammate who stayed ready to help, and Mira the beautician at Hero Helper Day.",
        ),
        (
            "What problem needed to be solved?",
            f"{mission.problem} The job really needed {mission.need}, not just a fancy costume.",
        ),
        (
            "Why was the beautician called dishonest?",
            f"Mira was called dishonest because she promised that the makeover would give real powers. Her words sounded exciting, but the makeover only changed how {child_name} looked.",
        ),
    ]
    if world.facts.get("false_promise"):
        qa.append(
            (
                f"What happened when {child_name} trusted the makeover?",
                f"{child_name} tried to solve the problem by trusting the makeover, but {makeover.failure}. That moment showed that pretend superhero powers could not do a real helper job.",
            )
        )
    else:
        qa.append(
            (
                f"Did the makeover itself solve the problem?",
                f"No. {child_name} enjoyed the costume, but understood it was only dress-up. The real solution still came from teamwork and the useful tool.",
            )
        )
    qa.append(
        (
            f"How did {child_name} and {teammate_name} solve the problem?",
            f"They used {tool.phrase}, and {teammate_name} worked beside {child_name} instead of leaving {child.pronoun('object')} alone. Because the tool matched the job, the two children could help for real.",
        )
    )
    qa.append(
        (
            "What lesson did the child learn?",
            f"{child_name} learned that a shiny transformation on the outside is not the same as real power. {parent.label_word.capitalize()} explained that honesty and teamwork make someone a true hero.",
        )
    )
    return qa


KNOWLEDGE = {
    "beautician": [
        (
            "What does a beautician do?",
            "A beautician helps people with hair, makeup, or other beauty care. A beautician can make someone look fancy, but cannot give real superpowers.",
        )
    ],
    "dishonest": [
        (
            "What does dishonest mean?",
            "Dishonest means not telling the truth. When someone is dishonest, people may believe something that is not real.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other on the same job. A hard task often becomes easier when everyone shares the work.",
        )
    ],
    "flashlight": [
        (
            "What is a flashlight for?",
            "A flashlight makes light in a dark place so you can see safely. It works much better than pretending your hair can glow like a lamp.",
        )
    ],
    "stool": [
        (
            "What is a step stool for?",
            "A step stool helps a person reach something a little higher up. It gives safe height without needing anyone to jump or pretend to fly.",
        )
    ],
    "wagon": [
        (
            "What is a wagon good for?",
            "A wagon helps carry heavy things by letting wheels do the hard part. That makes teamwork safer and easier.",
        )
    ],
    "honesty": [
        (
            "Why is honesty important?",
            "Honesty helps people trust each other and make good choices. If someone lies about what a thing can do, others may get disappointed or make a poor plan.",
        )
    ],
}
KNOWLEDGE_ORDER = ["beautician", "dishonest", "teamwork", "flashlight", "stool", "wagon", "honesty"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tool = world.facts["tool"]
    tags = {"beautician", "honesty", "teamwork"}
    if world.facts.get("false_promise"):
        tags.add("dishonest")
    tags |= set(tool.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% A valid story needs a real teamwork tool that matches the mission.
valid(S, M, Mk, T) :- setting(S), mission(M), makeover(Mk), tool(T),
                      need(M, N), works_for(T, N).

% Failure happens only when the makeover is dishonest and claims to solve
% the same need as the mission.
false_promise(M, Mk) :- need(M, N), claims_need(Mk, N),
                        honesty(Mk, H), honesty_min(Min), H < Min.

% Every valid story is solved because the teammate brings the fitting tool.
solved(M, T) :- need(M, N), works_for(T, N).

outcome(lesson_learned) :- chosen_mission(M), chosen_makeover(Mk), chosen_tool(T),
                           valid(_, M, Mk, T), solved(M, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("need", mid, mission.need))
    for mkid, makeover in MAKEOVERS.items():
        lines.append(asp.fact("makeover", mkid))
        lines.append(asp.fact("honesty", mkid, makeover.honesty))
        lines.append(asp.fact("claims_need", mkid, makeover.claims_need))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("works_for", tid, tool.works_for))
    lines.append(asp.fact("honesty_min", HONESTY_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_false_promise(mission_id: str, makeover_id: str) -> bool:
    import asp

    extra = "\n".join([
        asp.fact("chosen_mission", mission_id),
        asp.fact("chosen_makeover", makeover_id),
    ])
    model = asp.one_model(asp_program(extra, "#show false_promise/2."))
    atoms = set(asp.atoms(model, "false_promise"))
    return (mission_id, makeover_id) in atoms


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_mission", params.mission),
        asp.fact("chosen_makeover", params.makeover),
        asp.fact("chosen_tool", params.tool),
        asp.fact("setting", params.setting),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_generation() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("(Smoke test failed: empty story.)")
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

    bad_fp = []
    for mission_id, mission in MISSIONS.items():
        for makeover_id, makeover in MAKEOVERS.items():
            py = predicts_failure(makeover, mission)
            asp_val = asp_false_promise(mission_id, makeover_id)
            if py != asp_val:
                bad_fp.append((mission_id, makeover_id, py, asp_val))
    if not bad_fp:
        print("OK: false-promise model matches predicts_failure().")
    else:
        rc = 1
        print("MISMATCH in false-promise model:")
        for row in bad_fp[:10]:
            print(" ", row)

    cases = list(CURATED)
    for s in range(20):
        rng = random.Random(s)
        args = build_parser().parse_args([])
        params = resolve_params(args, rng)
        params.seed = s
        cases.append(params)

    bad_outcomes = []
    for params in cases:
        py = "lesson_learned"
        asp_val = asp_outcome(params)
        if py != asp_val:
            bad_outcomes.append((params, py, asp_val))
    if not bad_outcomes:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print("MISMATCH in outcomes:")
        for params, py, asp_val in bad_outcomes[:10]:
            print(" ", params, py, asp_val)

    try:
        _smoke_generation()
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a dishonest beautician, a superhero makeover, and a teamwork lesson."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--makeover", choices=MAKEOVERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mission and args.tool:
        mission = MISSIONS[args.mission]
        tool = TOOLS[args.tool]
        if not mission_fits_tool(mission, tool):
            raise StoryError(explain_rejection(mission, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.mission is None or combo[1] == args.mission)
        and (args.makeover is None or combo[2] == args.makeover)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mission_id, makeover_id, tool_id = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    teammate_gender = rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender)
    teammate_name = _pick_name(rng, teammate_gender, avoid=child_name)
    parent = args.parent or rng.choice(["mother", "father"])
    child_trait = rng.choice(TRAITS)
    teammate_trait = rng.choice(TEAM_TRAITS)
    return StoryParams(
        setting=setting_id,
        mission=mission_id,
        makeover=makeover_id,
        tool=tool_id,
        child_name=child_name,
        child_gender=child_gender,
        teammate_name=teammate_name,
        teammate_gender=teammate_gender,
        parent=parent,
        child_trait=child_trait,
        teammate_trait=teammate_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.makeover not in MAKEOVERS:
        raise StoryError(f"(Unknown makeover: {params.makeover})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    mission = MISSIONS[params.mission]
    tool = TOOLS[params.tool]
    if not mission_fits_tool(mission, tool):
        raise StoryError(explain_rejection(mission, tool))

    world = tell(
        setting=SETTINGS[params.setting],
        mission=mission,
        makeover=MAKEOVERS[params.makeover],
        tool=tool,
        child_name=params.child_name,
        child_gender=params.child_gender,
        teammate_name=params.teammate_name,
        teammate_gender=params.teammate_gender,
        parent_type=params.parent,
        child_trait=params.child_trait,
        teammate_trait=params.teammate_trait,
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
        print(asp_program("", "#show valid/4.\n#show false_promise/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mission, makeover, tool) combos:\n")
        for setting_id, mission_id, makeover_id, tool_id in combos:
            fp = predicts_failure(MAKEOVERS[makeover_id], MISSIONS[mission_id])
            marker = "false-promise" if fp else "costume-only"
            print(f"  {setting_id:8} {mission_id:11} {makeover_id:12} {tool_id:10} [{marker}]")
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
            p = sample.params
            header = f"### {p.child_name} & {p.teammate_name}: {p.mission} with {p.makeover} and {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
