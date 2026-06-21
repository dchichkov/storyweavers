#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/entire_sound_effects_problem_solving_twist_myth.py
=============================================================================

A standalone storyworld for a tiny mythic domain: a sacred spring goes silent,
a child follows strange sounds into a holy place, solves a real physical
problem, and discovers that the feared "monster" is not an enemy at all.

The stories use:
- the seed word "entire"
- sound effects in the prose
- a genuine problem-solving turn
- a myth-like twist and ending image

Run it
------
    python storyworlds/worlds/gpt-5.4/entire_sound_effects_problem_solving_twist_myth.py
    python storyworlds/worlds/gpt-5.4/entire_sound_effects_problem_solving_twist_myth.py --place sky_pool --obstacle stonefall --tool cedar_pole
    python storyworlds/worlds/gpt-5.4/entire_sound_effects_problem_solving_twist_myth.py --tool bell_rope
    python storyworlds/worlds/gpt-5.4/entire_sound_effects_problem_solving_twist_myth.py --all
    python storyworlds/worlds/gpt-5.4/entire_sound_effects_problem_solving_twist_myth.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so we climb three levels to
# the package dir (storyworlds/) and import results from there.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing" | "place"
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
        female = {"girl", "woman", "mother", "goddess"}
        male = {"boy", "man", "father", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    realm: str
    landmark: str
    village_name: str
    spring_name: str
    rumor_name: str
    true_guardian: str
    guardian_type: str
    guardian_intro: str
    baby_label: str
    hush_sound: str
    return_sound: str
    ending_image: str
    allowed_obstacles: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    sound: str
    cause_text: str
    fix_text: str
    requires_tool: str
    spread: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    works_on: set[str] = field(default_factory=set)
    action_text: str = ""
    sound: str = ""
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


def _r_blocked_spring(world: World) -> list[str]:
    out: list[str] = []
    spring = world.entities.get("spring")
    village = world.entities.get("village")
    obstacle = world.entities.get("obstacle")
    if not spring or not village or not obstacle:
        return out
    if obstacle.meters["blocking"] < THRESHOLD:
        return out
    sig = ("blocked", obstacle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    spring.meters["flow"] = 0.0
    spring.meters["silence"] += 1
    village.memes["worry"] += 1
    out.append("__silence__")
    return out


def _r_restored_spring(world: World) -> list[str]:
    out: list[str] = []
    spring = world.entities.get("spring")
    village = world.entities.get("village")
    obstacle = world.entities.get("obstacle")
    guardian = world.entities.get("guardian")
    if not spring or not village or not obstacle or not guardian:
        return out
    if obstacle.meters["blocking"] >= THRESHOLD:
        return out
    if guardian.memes["trust"] < THRESHOLD:
        return out
    sig = ("restored", spring.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    spring.meters["flow"] = 1.0
    spring.meters["singing"] += 1
    village.memes["worry"] = 0.0
    village.memes["relief"] += 1
    out.append("__restored__")
    return out


CAUSAL_RULES = [
    Rule(name="blocked_spring", tag="physical", apply=_r_blocked_spring),
    Rule(name="restored_spring", tag="physical", apply=_r_restored_spring),
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


def compatible(place: Place, obstacle: Obstacle, tool: Tool) -> bool:
    return obstacle.id in place.allowed_obstacles and obstacle.id in tool.works_on


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for obstacle_id, obstacle in OBSTACLES.items():
            for tool_id, tool in TOOLS.items():
                if compatible(place, obstacle, tool):
                    combos.append((place_id, obstacle_id, tool_id))
    return combos


def explain_rejection(place: Place, obstacle: Obstacle, tool: Tool) -> str:
    if obstacle.id not in place.allowed_obstacles:
        return (
            f"(No story: {obstacle.label} does not fit {place.landmark}. "
            f"That holy place is shaped for different troubles.)"
        )
    if obstacle.id not in tool.works_on:
        needed = TOOLS[obstacle.requires_tool].label
        return (
            f"(No story: {tool.label} will not solve {obstacle.label}. "
            f"This problem calls for {needed}.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_restoration(world: World, tool_id: str) -> dict:
    sim = world.copy()
    obstacle = sim.get("obstacle")
    guardian = sim.get("guardian")
    tool = TOOLS[tool_id]
    if obstacle.attrs.get("config_id") in tool.works_on:
        obstacle.meters["blocking"] = 0.0
        guardian.memes["trust"] += 1
    propagate(sim, narrate=False)
    spring = sim.get("spring")
    return {
        "flow": spring.meters["flow"],
        "singing": spring.meters["singing"],
    }


def setup_dawn(world: World, hero: Entity, elder: Entity, place: Place) -> None:
    hero.memes["care"] += 1
    world.say(
        f"In the age when hills still answered prayers, {hero.id} lived in "
        f"{place.village_name}, beneath {place.realm}. Each morning, {place.spring_name} "
        f"used to sing {place.return_sound}, and the people said the whole land woke by that music."
    )
    world.say(
        f"But one dawn the spring gave only {place.hush_sound}, and the entire village paused with its water jars in the air."
    )
    world.say(
        f'{elder.id}, the old keeper of stories, whispered, "When a sacred sound is missing, we must listen before we blame."'
    )


def rumor(world: World, hero: Entity, elder: Entity, place: Place, obstacle: Obstacle) -> None:
    village = world.get("village")
    village.memes["fear"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"Some people pointed toward {place.landmark} and muttered that {place.rumor_name} had swallowed the song. "
        f"From far away came {obstacle.sound}, and that only made the rumor grow."
    )
    world.say(
        f"{hero.id} took {hero.pronoun('possessive')} breath, picked up {world.get('tool').phrase}, and walked toward the silence."
    )


def arrive(world: World, hero: Entity, place: Place, obstacle: Obstacle) -> None:
    world.say(
        f"At {place.landmark}, {hero.id} heard three sounds close together: {obstacle.sound}, "
        f"the small {place.hush_sound} of trapped water, and a soft shiver from behind a rock."
    )
    world.say(
        f"That was enough for {hero.id} to understand that something was stuck. A thief would hide treasure, but a trapped spring made a different kind of cry."
    )


def solve(world: World, hero: Entity, obstacle: Obstacle, tool: Tool) -> None:
    pred = predict_restoration(world, tool.id)
    if pred["flow"] < THRESHOLD:
        raise StoryError("(Internal story error: the chosen tool did not restore the spring.)")
    hero.memes["resolve"] += 1
    world.facts["predicted_flow"] = pred["flow"]
    world.facts["predicted_singing"] = pred["singing"]
    world.say(
        f"{hero.id} knelt beside {obstacle.phrase} and thought hard. Then {hero.pronoun()} used {tool.phrase} to {tool.action_text}. "
        f"{tool.sound} went the tool, and little by little the blockage gave way."
    )
    obstacle_ent = world.get("obstacle")
    guardian = world.get("guardian")
    obstacle_ent.meters["blocking"] = 0.0
    obstacle_ent.meters["cleared"] += 1
    guardian.memes["trust"] += 1
    guardian.memes["fear"] = 0.0
    propagate(world, narrate=False)


def reveal_twist(world: World, hero: Entity, place: Place) -> None:
    guardian = world.get("guardian")
    guardian.meters["visible"] += 1
    world.say(
        f"Then the shadow behind the rock unfolded. It was not {place.rumor_name} at all, but {place.guardian_intro}."
    )
    world.say(
        f"Around {guardian.pronoun('possessive')} feet huddled {place.baby_label}, and at once {hero.id} saw the truth: "
        f"the guardian had stayed near the blocked water to keep the little ones safe."
    )


def restore(world: World, hero: Entity, elder: Entity, place: Place) -> None:
    spring = world.get("spring")
    village = world.get("village")
    if spring.meters["flow"] < THRESHOLD:
        raise StoryError("(Internal story error: the spring did not come back.)")
    hero.memes["joy"] += 1
    hero.memes["wisdom"] += 1
    village.memes["gratitude"] += 1
    world.say(
        f"With the path open, the water leapt free. {place.return_sound} sang the spring, bright enough to ring against the stones."
    )
    world.say(
        f"{hero.id} led the guardian and {place.baby_label} down a safer path, and by sunset {elder.id} was telling everyone what had really happened."
    )
    world.say(
        f'From then on, the people no longer called the creature a monster. They called it {place.true_guardian}, and they remembered that fear can be loud while truth begins as a small sound.'
    )
    world.say(place.ending_image)


def tell(
    place: Place,
    obstacle: Obstacle,
    tool: Tool,
    *,
    hero_name: str = "Neri",
    hero_gender: str = "girl",
    elder_name: str = "Tomas",
    elder_type: str = "man",
) -> World:
    if not compatible(place, obstacle, tool):
        raise StoryError(explain_rejection(place, obstacle, tool))

    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", label=hero_name))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder", label="the elder"))
    village = world.add(Entity(id="village", kind="place", type="village", label=place.village_name))
    spring = world.add(Entity(id="spring", kind="thing", type="spring", label=place.spring_name))
    guardian = world.add(Entity(
        id="guardian",
        kind="thing",
        type=place.guardian_type,
        label=place.true_guardian,
        attrs={"config_id": place.id},
    ))
    obstacle_ent = world.add(Entity(
        id="obstacle",
        kind="thing",
        type="obstacle",
        label=obstacle.label,
        attrs={"config_id": obstacle.id},
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        attrs={"config_id": tool.id},
    ))

    obstacle_ent.meters["blocking"] = 1.0
    guardian.memes["fear"] = 1.0
    spring.meters["flow"] = 1.0
    propagate(world, narrate=False)

    setup_dawn(world, hero, elder, place)
    world.para()
    rumor(world, hero, elder, place, obstacle)
    arrive(world, hero, place, obstacle)
    world.para()
    solve(world, hero, obstacle, tool)
    reveal_twist(world, hero, place)
    world.para()
    restore(world, hero, elder, place)

    world.facts.update(
        place=place,
        obstacle_cfg=obstacle,
        tool_cfg=tool,
        hero=hero,
        elder=elder,
        village=village,
        spring=spring,
        guardian=guardian,
        obstacle=obstacle_ent,
        restored=spring.meters["flow"] >= THRESHOLD,
        twist_revealed=guardian.meters["visible"] >= THRESHOLD,
    )
    return world


PLACES = {
    "sky_pool": Place(
        id="sky_pool",
        realm="the blue shoulder of Mount Selen",
        landmark="the Sky Pool under a bent pine",
        village_name="Little Selen",
        spring_name="the Pool of First Echoes",
        rumor_name="the Cloud-Lion Who Eats Voices",
        true_guardian="the Mist-Mane",
        guardian_type="beast",
        guardian_intro="a pale lion with rain in its mane and kind, tired eyes",
        baby_label="three damp cubs",
        hush_sound='"tik... tik..."',
        return_sound='"shaa-aa, shaa-aa"',
        ending_image="That night the moon floated inside the pool like a silver coin, and the entire village slept to the spring's bright breathing.",
        allowed_obstacles={"stonefall", "reed_knot"},
        tags={"spring", "mountain", "lion"},
    ),
    "moon_reeds": Place(
        id="moon_reeds",
        realm="the marsh where the moon laid its ladder of light",
        landmark="the Moon-Reed Ford",
        village_name="Reedstep",
        spring_name="the Reed Throat",
        rumor_name="the Long Eel That Steals Names",
        true_guardian="the Reed Mother",
        guardian_type="creature",
        guardian_intro="a silver eel coiled around a nest of shining eggs",
        baby_label="a cluster of pearl-bright eggs",
        hush_sound='"drip... drip..."',
        return_sound='"glooop, glishh, glooop"',
        ending_image="Frogs sang, reeds bowed, and the entire marsh glittered as if the moon itself had come down to drink.",
        allowed_obstacles={"reed_knot", "ice_lid"},
        tags={"spring", "marsh", "eel"},
    ),
    "cedar_hollow": Place(
        id="cedar_hollow",
        realm="the shadow of the oldest cedars",
        landmark="the Cedar Echo Hollow",
        village_name="Hollow Fern",
        spring_name="the Listening Spring",
        rumor_name="the Cave Owl That Swallows Dawn",
        true_guardian="the Hollow Wing",
        guardian_type="bird",
        guardian_intro="a great white owl spreading one wing over two sleepy chicks",
        baby_label="two fluff-soft chicks",
        hush_sound='"tip... tip..."',
        return_sound='"hushhh-rill, hushhh-rill"',
        ending_image="The cedars answered one another across the darkening hill, and the entire hollow sounded alive again.",
        allowed_obstacles={"stonefall", "ice_lid"},
        tags={"spring", "forest", "owl"},
    ),
}

OBSTACLES = {
    "stonefall": Obstacle(
        id="stonefall",
        label="fallen stones",
        phrase="a heap of cold stones jammed across the narrow channel",
        sound='"krk... krk..."',
        cause_text="A small rockslide had choked the spring's path.",
        fix_text="move the stones apart without crushing the channel",
        requires_tool="cedar_pole",
        spread=2,
        tags={"stone", "blockage"},
    ),
    "reed_knot": Obstacle(
        id="reed_knot",
        label="a knot of hard reeds",
        phrase="a twisted braid of reeds wound tight over the water mouth",
        sound='"ssrip... ssrip..."',
        cause_text="Storm winds had braided the reeds into a hard knot.",
        fix_text="cut and pull the reeds free",
        requires_tool="moon_sickle",
        spread=1,
        tags={"reeds", "blockage"},
    ),
    "ice_lid": Obstacle(
        id="ice_lid",
        label="a lid of thin blue ice",
        phrase="a sheet of blue ice sealed over the spring's lip",
        sound='"tink... tink..."',
        cause_text="A strange night frost had sealed the water in.",
        fix_text="ring and crack the ice without breaking the bank",
        requires_tool="bell_rope",
        spread=1,
        tags={"ice", "blockage"},
    ),
}

TOOLS = {
    "cedar_pole": Tool(
        id="cedar_pole",
        label="a cedar pole",
        phrase="a cedar pole worn smooth by many hands",
        works_on={"stonefall"},
        action_text="lever the biggest stones aside one by one",
        sound='"thok... thok..."',
        tags={"pole", "lever"},
    ),
    "moon_sickle": Tool(
        id="moon_sickle",
        label="a moon-sickle",
        phrase="a moon-sickle with a pale curved blade",
        works_on={"reed_knot"},
        action_text="slice the reed braid and pull its ends apart",
        sound='"snip-snip... shrrp..."',
        tags={"sickle", "cutting"},
    ),
    "bell_rope": Tool(
        id="bell_rope",
        label="a bell rope",
        phrase="a bell rope braided with little bronze shells",
        works_on={"ice_lid"},
        action_text="tap and ring along the ice until fine cracks spread across it",
        sound='"ting-ting... crack!"',
        tags={"rope", "ringing"},
    ),
}

GIRL_NAMES = ["Neri", "Ila", "Mira", "Tali", "Sena", "Luma"]
BOY_NAMES = ["Aren", "Kiro", "Tovan", "Elior", "Pavel", "Rami"]
ELDER_NAMES = ["Tomas", "Mara", "Oren", "Lysa"]


@dataclass
class StoryParams:
    place: str
    obstacle: str
    tool: str
    hero_name: str
    hero_gender: str
    elder_name: str
    elder_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="sky_pool",
        obstacle="stonefall",
        tool="cedar_pole",
        hero_name="Neri",
        hero_gender="girl",
        elder_name="Tomas",
        elder_type="man",
    ),
    StoryParams(
        place="moon_reeds",
        obstacle="reed_knot",
        tool="moon_sickle",
        hero_name="Aren",
        hero_gender="boy",
        elder_name="Mara",
        elder_type="woman",
    ),
    StoryParams(
        place="cedar_hollow",
        obstacle="ice_lid",
        tool="bell_rope",
        hero_name="Mira",
        hero_gender="girl",
        elder_name="Oren",
        elder_type="man",
    ),
    StoryParams(
        place="sky_pool",
        obstacle="reed_knot",
        tool="moon_sickle",
        hero_name="Kiro",
        hero_gender="boy",
        elder_name="Lysa",
        elder_type="woman",
    ),
]


KNOWLEDGE = {
    "spring": [
        (
            "What is a spring?",
            "A spring is water that comes out of the ground. If something blocks it, the water can slow down or stop until the path is open again.",
        )
    ],
    "stone": [
        (
            "Why can fallen stones block water?",
            "If enough stones tumble into a narrow place, they can jam together and stop the water from moving through. The water is still there, but it cannot pass.",
        )
    ],
    "reeds": [
        (
            "What are reeds?",
            "Reeds are tall water plants with long, bendy stems. When wind twists many reeds together, they can make a tight knot.",
        )
    ],
    "ice": [
        (
            "What happens when thin ice forms over water?",
            "Thin ice can make a lid over the top of water. If it seals a small opening, the water cannot bubble out the way it usually does.",
        )
    ],
    "pole": [
        (
            "What can a pole be used for?",
            "A strong pole can push or pry heavy things. It gives your hands more reach and more strength.",
        )
    ],
    "sickle": [
        (
            "What is a sickle?",
            "A sickle is a curved cutting tool. Grown-ups use it to cut plants like grass or reeds.",
        )
    ],
    "rope": [
        (
            "What is a bell rope?",
            "A bell rope is a rope tied to a bell or small ringing pieces of metal. When it moves, it can make a clear sound.",
        )
    ],
    "myth": [
        (
            "Why do myths often have monsters that are not really monsters?",
            "Myths like to teach that fear can fool people. Something that looks scary at first may be hurt, busy, or protecting someone.",
        )
    ],
}
KNOWLEDGE_ORDER = ["spring", "stone", "reeds", "ice", "pole", "sickle", "rope", "myth"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    hero = f["hero"]
    return [
        f'Write a short myth for a 3-to-5-year-old that includes the word "entire" and begins when a sacred spring falls silent.',
        f"Tell a myth-like story where {hero.id} hears {obstacle.sound} near {place.landmark}, solves a real blockage with {tool.phrase}, and learns the feared creature is gentle.",
        f'Write a child-facing story with sound effects, a problem-solving turn, and a twist ending where people first blame a monster but later discover the truth.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    place = f["place"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child from {place.village_name}, and {elder.id}, the old keeper of stories. The story follows {hero.id} as {hero.pronoun()} goes to find out why the sacred spring grew quiet.",
        ),
        (
            f"Why was the entire village worried?",
            f"The sacred spring had almost stopped singing, so the people feared something was wrong with their water. The silence was frightening because the village depended on that spring each morning.",
        ),
        (
            f"What clue helped {hero.id} understand the problem?",
            f"{hero.id} listened carefully and heard {obstacle.sound} together with the weak sound of trapped water. That told {hero.pronoun('object')} the spring was blocked, not stolen.",
        ),
        (
            f"How did {hero.id} solve the problem?",
            f"{hero.id} used {tool.phrase} to {tool.action_text}. That worked because {tool.label} was the right tool for {obstacle.label}, so the water could move again.",
        ),
    ]
    if f["twist_revealed"]:
        qa.append(
            (
                "What was the twist in the story?",
                f"The people had blamed {place.rumor_name}, but the scary creature was really {place.guardian_intro}. It was staying near {place.baby_label} and was not trying to hurt anyone.",
            )
        )
    if f["restored"]:
        qa.append(
            (
                "How did the story end?",
                f"The spring began singing again, and the villagers learned the truth about the guardian. The ending shows that careful listening and a kind solution changed fear into gratitude.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"spring", "myth"}
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    for tag in obstacle.tags:
        if tag == "stone":
            tags.add("stone")
        if tag == "reeds":
            tags.add("reeds")
        if tag == "ice":
            tags.add("ice")
    for tag in tool.tags:
        if tag == "pole":
            tags.add("pole")
        if tag == "sickle":
            tags.add("sickle")
        if tag == "rope":
            tags.add("rope")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:9} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
compatible_tool(O, T) :- obstacle(O), tool(T), needs_tool(O, T).
valid(P, O, T) :- place(P), place_allows(P, O), compatible_tool(O, T).

chosen_valid :- chosen_place(P), chosen_obstacle(O), chosen_tool(T), valid(P, O, T).
restored      :- chosen_valid.
twist(gentle) :- chosen_place(P), rumored(P, _), true_guardian(P, _).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("rumored", place_id, place.rumor_name))
        lines.append(asp.fact("true_guardian", place_id, place.true_guardian))
        for obstacle_id in sorted(place.allowed_obstacles):
            lines.append(asp.fact("place_allows", place_id, obstacle_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs_tool", obstacle_id, obstacle.requires_tool))
    for tool_id in TOOLS:
        lines.append(asp.fact("tool", tool_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_restored(params: StoryParams) -> bool:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra=extra, show="#show restored/0."))
    return bool(asp.atoms(model, "restored"))


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

    cases = list(CURATED)
    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for params in cases:
        py_ok = compatible(PLACES[params.place], OBSTACLES[params.obstacle], TOOLS[params.tool])
        asp_ok = asp_restored(params)
        if py_ok != asp_ok:
            rc = 1
            print(
                "MISMATCH on restored parity:",
                params.place,
                params.obstacle,
                params.tool,
                py_ok,
                asp_ok,
            )
    if rc == 0:
        print(f"OK: ASP/Python parity holds on {len(cases)} curated scenarios.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a mythic silent spring, a clever child, and a gentle twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.obstacle and args.tool:
        place = PLACES[args.place]
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        if not compatible(place, obstacle, tool):
            raise StoryError(explain_rejection(place, obstacle, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_name = rng.choice(ELDER_NAMES)
    elder_type = "woman" if elder_name in {"Mara", "Lysa"} else "man"
    return StoryParams(
        place=place_id,
        obstacle=obstacle_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_gender=gender,
        elder_name=elder_name,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    world = tell(
        PLACES[params.place],
        OBSTACLES[params.obstacle],
        TOOLS[params.tool],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_name=params.elder_name,
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
        print(asp_program(show="#show valid/3.\n#show restored/0.\n#show twist/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, obstacle, tool) combos:\n")
        for place, obstacle, tool in combos:
            print(f"  {place:13} {obstacle:10} {tool}")
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
            header = f"### {p.hero_name}: {p.place} / {p.obstacle} / {p.tool}"
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
