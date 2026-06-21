#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/quail_flashback_happy_ending_conflict_superhero_story.py
====================================================================================

A standalone storyworld for a tiny superhero-flavored rescue tale: a child in a
cape finds a frightened quail chick in trouble, clashes with a more reckless
friend about what to do, remembers an earlier lesson, and uses that memory to
make a calm plan that leads to a happy ending.

The world model is small on purpose:
- entities carry physical meters and emotional memes
- a reasonableness gate only allows rescue tools that actually meet the hazard
- the story always includes conflict, a flashback, and a happy ending
- an inline ASP twin mirrors the valid-combo gate

Run it
------
    python storyworlds/worlds/gpt-5.4/quail_flashback_happy_ending_conflict_superhero_story.py
    python storyworlds/worlds/gpt-5.4/quail_flashback_happy_ending_conflict_superhero_story.py --hazard busy_path --tool wagon
    python storyworlds/worlds/gpt-5.4/quail_flashback_happy_ending_conflict_superhero_story.py --hazard sprinkler --tool cape
    python storyworlds/worlds/gpt-5.4/quail_flashback_happy_ending_conflict_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/quail_flashback_happy_ending_conflict_superhero_story.py --verify
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    skyline: str
    quail_home: str
    helper_spot: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    scene: str
    threat: str
    motion: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    powers: set[str] = field(default_factory=set)
    action: str = ""
    ending: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Flashback:
    id: str
    source: str
    line: str
    lesson: str
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


def _r_hazard_fear(world: World) -> list[str]:
    quail = world.get("quail")
    if quail.meters["threatened"] < THRESHOLD:
        return []
    sig = ("hazard_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    quail.memes["fear"] += 1
    world.get("hero").memes["worry"] += 1
    world.get("friend").memes["urgency"] += 1
    return []


def _r_shelter_quiets(world: World) -> list[str]:
    quail = world.get("quail")
    if quail.meters["sheltered"] < THRESHOLD:
        return []
    sig = ("shelter_quiets",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    quail.memes["fear"] = 0.0
    quail.memes["calm"] += 1
    return []


def _r_reunion(world: World) -> list[str]:
    quail = world.get("quail")
    if quail.meters["moved_safe"] < THRESHOLD or quail.memes["calm"] < THRESHOLD:
        return []
    sig = ("reunion",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    quail.meters["reunited"] += 1
    world.get("hero").memes["relief"] += 1
    world.get("friend").memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="hazard_fear", tag="emotional", apply=_r_hazard_fear),
    Rule(name="shelter_quiets", tag="emotional", apply=_r_shelter_quiets),
    Rule(name="reunion", tag="resolution", apply=_r_reunion),
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
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "park": Setting(
        id="park",
        place="the city park",
        skyline="the climbing frame looked like a silver watchtower",
        quail_home="the tall grass beside the flower bed",
        helper_spot="the gardener by the tool shed",
        affords={"barking_dog", "busy_path"},
        tags={"park"},
    ),
    "schoolyard": Setting(
        id="schoolyard",
        place="the school garden",
        skyline="the painted wall looked like a line of bright hero shields",
        quail_home="the herb patch behind the bench",
        helper_spot="the teacher by the gate",
        affords={"busy_path", "sprinkler"},
        tags={"school"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the little orchard behind the library",
        skyline="the rows of trees looked like a secret green headquarters",
        quail_home="the soft straw under a berry bush",
        helper_spot="the groundskeeper near the water barrels",
        affords={"barking_dog", "sprinkler"},
        tags={"orchard"},
    ),
}

HAZARDS = {
    "barking_dog": Hazard(
        id="barking_dog",
        label="a barking dog",
        scene="A tiny quail chick crouched beside the path while a barking dog strained at its leash.",
        threat="The sharp barking made the chick flatten low and tremble.",
        motion="Every bark felt like a boom in a comic-book battle.",
        needs={"cover", "quiet"},
        tags={"dog", "noise"},
    ),
    "busy_path": Hazard(
        id="busy_path",
        label="a busy scooter path",
        scene="A tiny quail chick stood at the edge of a busy scooter path where wheels kept zipping past.",
        threat="The little bird did not know which way to dart.",
        motion="Bright scooter wheels flashed by like spinning villain disks.",
        needs={"cover", "move"},
        tags={"scooter", "path"},
    ),
    "sprinkler": Hazard(
        id="sprinkler",
        label="a snapping sprinkler",
        scene="A tiny quail chick huddled near a snapping sprinkler that kept spraying cold water over the dirt.",
        threat="Each hiss of water made the chick duck lower into the mud.",
        motion="The silver spray whipped around like a wild robot arm.",
        needs={"cover", "dry"},
        tags={"water", "sprinkler"},
    ),
}

TOOLS = {
    "cape": Tool(
        id="cape",
        label="cape",
        phrase="a red superhero cape",
        powers={"cover", "quiet"},
        action="spread the cape low like a soft little tunnel so the chick could hide in the shadow",
        ending="The cape fluttered like a brave flag, but it stayed gentle enough for tiny feathers.",
        tags={"cape"},
    ),
    "box": Tool(
        id="box",
        label="box",
        phrase="a cardboard snack box",
        powers={"cover", "quiet", "move", "dry"},
        action="set the box on its side, making a calm hideout, then nudged it slowly toward safety",
        ending="The box looked plain, but for one small bird it became a perfect rescue chamber.",
        tags={"box"},
    ),
    "wagon": Tool(
        id="wagon",
        label="wagon",
        phrase="a little red wagon",
        powers={"move", "cover"},
        action="rolled the wagon close, shaded the chick with both hands, and guided it into the wagon before pulling it away from trouble",
        ending="Its red wheels looked heroic, yet the best part was how slowly they moved.",
        tags={"wagon"},
    ),
    "umbrella": Tool(
        id="umbrella",
        label="umbrella",
        phrase="a yellow umbrella",
        powers={"cover", "dry"},
        action="tilted the umbrella low to block the spray and made a dry pocket of air beside the grass",
        ending="The umbrella shone like a hero shield against the water.",
        tags={"umbrella"},
    ),
}

FLASHBACKS = {
    "grandpa": Flashback(
        id="grandpa",
        source="Grandpa",
        line='"Little quail feel safer in quiet shade," Grandpa had said one morning while they watched birds near the tomatoes.',
        lesson="quiet_shade",
        tags={"grandpa", "quail"},
    ),
    "ranger": Flashback(
        id="ranger",
        source="Ranger Tessa",
        line='"If you rush at a small bird, it gets more scared. First make a calm shelter, then let it choose safety," Ranger Tessa had taught during nature day.',
        lesson="calm_shelter",
        tags={"ranger", "quail"},
    ),
    "mom": Flashback(
        id="mom",
        source="Mom",
        line='"Being a hero is not about being loud. It is about noticing what a tiny creature needs," Mom had whispered after they found a nest last spring.',
        lesson="notice_need",
        tags={"mom", "quail"},
    ),
}

GIRL_NAMES = ["Nova", "Maya", "Luna", "Zoe", "Ava", "Ruby", "Skye", "Nina"]
BOY_NAMES = ["Leo", "Max", "Finn", "Theo", "Eli", "Sam", "Kai", "Jude"]
TRAITS = ["brave", "quick", "careful", "bright", "steady", "kind"]


def tool_works(hazard: Hazard, tool: Tool) -> bool:
    return hazard.needs.issubset(tool.powers)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for hid in sorted(setting.affords):
            hazard = HAZARDS[hid]
            for tid, tool in TOOLS.items():
                if tool_works(hazard, tool):
                    combos.append((sid, hid, tid))
    return sorted(combos)


@dataclass
class StoryParams:
    setting: str
    hazard: str
    tool: str
    flashback: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    grownup_type: str
    hero_trait: str
    seed: Optional[int] = None


def superhero_title(hero: Entity) -> str:
    return {
        "brave": "Captain Comet",
        "quick": "Flash Feather",
        "careful": "Shield Star",
        "bright": "Sunbeam Scout",
        "steady": "Thunder Guard",
        "kind": "Captain Kindlight",
    }.get(hero.traits[0] if hero.traits else "", "Star Hero")


def friend_push_line(friend: Entity, hazard: Hazard) -> str:
    if hazard.id == "barking_dog":
        return (
            f'"I can scare the dog away with my biggest roar!" {friend.id} cried. '
            f'"Real heroes charge first!"'
        )
    if hazard.id == "busy_path":
        return (
            f'"Let\'s dash in, scoop it up, and leap out before the scooters even blink!" '
            f'{friend.id} said.'
        )
    return (
        f'"I\'ll run through the spray and grab it!" {friend.id} said. '
        f'"Fast is the most heroic!"'
    )


def explain_rejection(setting: Setting, hazard: Hazard, tool: Tool) -> str:
    missing = sorted(hazard.needs - tool.powers)
    return (
        f"(No story: {tool.phrase} cannot handle {hazard.label} in {setting.place}. "
        f"It is missing {missing}, so the rescue would not be honest or safe.)"
    )


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    title = superhero_title(hero)
    world.say(
        f"{hero.id} tied on {hero.attrs['costume']} and called {hero.pronoun('object')}self {title}."
    )
    world.say(
        f"In {setting.place}, {setting.skyline}, and {friend.id} raced beside {hero.pronoun('object')} as the trusty sidekick."
    )
    world.say(
        f"They were not flying for real, but with capes, brave voices, and pumping knees, it felt wonderfully close."
    )


def discover(world: World, hero: Entity, hazard: Hazard) -> None:
    quail = world.get("quail")
    quail.meters["threatened"] += 1
    hero.memes["duty"] += 1
    propagate(world, narrate=False)
    world.say(hazard.scene)
    world.say(hazard.threat)
    world.say(hazard.motion)


def conflict(world: World, hero: Entity, friend: Entity, hazard: Hazard) -> None:
    hero.memes["conflict"] += 1
    friend.memes["conflict"] += 1
    world.say(friend_push_line(friend, hazard))
    world.say(
        f'{hero.id} took one step forward, then stopped. The chick was so small that even a heroic hurry could feel huge and frightening.'
    )


def flashback(world: World, hero: Entity, fb: Flashback) -> None:
    hero.memes["memory"] += 1
    hero.memes["calm"] += 1
    world.say(
        f"Then a memory flashed across {hero.pronoun('possessive')} mind like a bright panel in a comic book."
    )
    world.say(fb.line)


def choose_plan(world: World, hero: Entity, friend: Entity, tool: Tool, grownup: Entity) -> None:
    hero.memes["leadership"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'"No roaring," {hero.id} said. "A real hero makes the world feel safer first."'
    )
    world.say(
        f"{hero.pronoun().capitalize()} pointed to {tool.phrase} and asked {friend.id} to stand still and keep a quiet space open."
    )
    world.say(
        f'{hero.id} also waved to {grownup.label_word} at {world.setting.helper_spot}, because even superheroes know when to ask a grown-up to watch over the rescue.'
    )


def use_tool(world: World, hero: Entity, tool: Tool, hazard: Hazard) -> None:
    quail = world.get("quail")
    if "cover" in tool.powers:
        quail.meters["sheltered"] += 1
    if "move" in tool.powers:
        quail.meters["moved_safe"] += 1
    if "dry" in tool.powers or hazard.id != "sprinkler":
        quail.meters["moved_safe"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Very slowly, {hero.id} {tool.action}."
    )
    world.say(tool.ending)


def reunion(world: World, hero: Entity, friend: Entity, setting: Setting, grownup: Entity) -> None:
    quail = world.get("quail")
    if quail.meters["reunited"] < THRESHOLD:
        quail.meters["reunited"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In another moment, the chick slipped into {setting.quail_home}, and a soft answering call came from the leaves."
    )
    world.say(
        f"A grown quail stepped out, bobbed once, and led the chick deeper into the safe grass."
    )
    world.say(
        f'{friend.id} let out the breath {friend.pronoun()} had been holding. "{hero.id}, that was a better super move than a charge," {friend.pronoun()} said.'
    )
    world.say(
        f"{grownup.label_word.capitalize()} smiled from {setting.helper_spot}. The city felt ordinary again, but to {hero.id} it gleamed like a saved world."
    )


def closing(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["pride"] += 1
    friend.memes["admiration"] += 1
    world.say(
        f"After that, when {hero.id} and {friend.id} played heroes, their bravest power was not loudness. It was calm hands, sharp eyes, and room for small creatures to feel safe."
    )
    world.say(
        f"And every time a cape snapped in the wind, {hero.id} remembered that even a quail chick could teach a superhero how to be gentle."
    )


def tell(
    setting: Setting,
    hazard: Hazard,
    tool: Tool,
    fb: Flashback,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    grownup_type: str,
    hero_trait: str,
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=[hero_trait],
            attrs={"costume": "a red cape and a cardboard star badge"},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
            traits=["bold"],
        )
    )
    grownup = world.add(
        Entity(
            id="Grownup",
            kind="character",
            type=grownup_type,
            role="grownup",
            label="the grown-up",
        )
    )
    quail = world.add(
        Entity(
            id="quail",
            kind="thing",
            type="bird",
            label="quail chick",
            phrase="a tiny quail chick",
            tags={"quail"},
        )
    )

    introduce(world, hero, friend, setting)
    world.para()
    discover(world, hero, hazard)
    conflict(world, hero, friend, hazard)
    world.para()
    flashback(world, hero, fb)
    choose_plan(world, hero, friend, tool, grownup)
    use_tool(world, hero, tool, hazard)
    world.para()
    reunion(world, hero, friend, setting, grownup)
    closing(world, hero, friend)

    world.facts.update(
        hero=hero,
        friend=friend,
        grownup=grownup,
        quail=quail,
        setting=setting,
        hazard=hazard,
        tool=tool,
        flashback=fb,
        happy=quail.meters["reunited"] >= THRESHOLD,
        conflict=hero.memes["conflict"] >= THRESHOLD,
        flashback_used=hero.memes["memory"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "quail": [
        (
            "What is a quail?",
            "A quail is a small ground bird with quick little legs. Baby quail stay safer when they can hide in grass or under cover."
        )
    ],
    "dog": [
        (
            "Why can barking scare a tiny bird?",
            "A barking dog is big, loud, and sudden to a tiny bird. Even if the dog never touches it, the noise can make the bird panic."
        )
    ],
    "scooter": [
        (
            "Why is a busy path dangerous for a small bird?",
            "Fast wheels can surprise a small bird before it knows where to run. A tiny animal needs time and a clear safe place to move."
        )
    ],
    "sprinkler": [
        (
            "Why can a sprinkler bother a baby bird?",
            "Cold water and sudden hissing sounds can frighten a baby bird. If the ground gets muddy, it can also be harder for the bird to move safely."
        )
    ],
    "cape": [
        (
            "Can a cape help in a rescue?",
            "Sometimes it can help as soft cover or shade if you use it gently. It is only useful when it makes the small animal feel calmer, not when it startles it."
        )
    ],
    "box": [
        (
            "Why can a box help a tiny bird?",
            "A box can make a quiet little shelter and can help guide the bird slowly. The dark shade inside can help the bird feel less exposed."
        )
    ],
    "wagon": [
        (
            "Why must a wagon move slowly near a tiny animal?",
            "A wagon has wheels, so it can seem big and noisy up close. Moving it slowly keeps it from feeling like another danger."
        )
    ],
    "umbrella": [
        (
            "How can an umbrella help in the rain or spray?",
            "An umbrella can block water and make a dry patch underneath. That can give a small creature a calmer place to pause."
        )
    ],
    "hero": [
        (
            "What makes someone a real hero?",
            "A real hero notices what will actually help. Sometimes the bravest choice is the calmest one."
        )
    ],
}
KNOWLEDGE_ORDER = ["quail", "dog", "scooter", "sprinkler", "cape", "box", "wagon", "umbrella", "hero"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    hazard = f["hazard"]
    tool = f["tool"]
    fb = f["flashback"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the word "quail", a conflict, a flashback, and a happy ending.',
        f"Tell a superhero-style rescue story where {hero.id} and {friend.id} find a quail chick facing {hazard.label}, argue about what to do, and then solve it with {tool.phrase}.",
        f"Write a child-facing story where a hero remembers advice from {fb.source}, chooses a gentle plan instead of a loud one, and ends with the quail safe."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    grownup = f["grownup"]
    hazard = f["hazard"]
    tool = f["tool"]
    fb = f["flashback"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child pretending to be a superhero, {friend.id}, the bold sidekick, and a tiny quail chick in trouble."
        ),
        (
            "What problem did they find?",
            f"They found a quail chick facing {hazard.label} in {setting.place}. The danger felt big because the chick was tiny and frightened."
        ),
        (
            f"Why did {hero.id} and {friend.id} disagree?",
            f"{friend.id} wanted to rush in with a loud, fast rescue, but {hero.id} worried that hurrying would scare the quail even more. Their conflict came from wanting to help in different ways."
        ),
        (
            f"What was the flashback about?",
            f"{hero.id} remembered advice from {fb.source}. The memory said a tiny bird needs calm shelter, not noisy heroics."
        ),
        (
            f"How did {hero.id} help the quail?",
            f"{hero.id} used {tool.phrase} and moved slowly to make the space feel safe. That worked because the tool matched what the quail needed in that moment."
        ),
        (
            "How did the story end?",
            f"It ended happily: the quail chick reached {setting.quail_home} and a grown quail called back from safety. The children learned that gentle help can be the most heroic power of all."
        ),
    ]
    if f.get("flashback_used"):
        qa.append(
            (
                f"Why did the flashback matter?",
                f"The flashback changed what {hero.id} did next. Instead of charging forward, {hero.pronoun()} chose a calmer rescue that let the quail feel safe enough to move."
            )
        )
    if grownup:
        qa.append(
            (
                f"Why did {hero.id} wave to the {grownup.label_word} too?",
                f"{hero.id} wanted a grown-up nearby while the rescue happened. That showed the story's hero knew bravery and asking for help can belong together."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"quail", "hero"} | set(world.facts["hazard"].tags) | set(world.facts["tool"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="park",
        hazard="barking_dog",
        tool="cape",
        flashback="grandpa",
        hero_name="Nova",
        hero_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        grownup_type="mother",
        hero_trait="kind",
    ),
    StoryParams(
        setting="schoolyard",
        hazard="busy_path",
        tool="wagon",
        flashback="ranger",
        hero_name="Leo",
        hero_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        grownup_type="father",
        hero_trait="steady",
    ),
    StoryParams(
        setting="orchard",
        hazard="sprinkler",
        tool="umbrella",
        flashback="mom",
        hero_name="Skye",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        grownup_type="grandfather",
        hero_trait="bright",
    ),
    StoryParams(
        setting="schoolyard",
        hazard="busy_path",
        tool="box",
        flashback="grandpa",
        hero_name="Eli",
        hero_gender="boy",
        friend_name="Maya",
        friend_gender="girl",
        grownup_type="mother",
        hero_trait="careful",
    ),
]


ASP_RULES = r"""
works(H, T) :- need(H, Need), power(T, Need), not missing(H, T).
missing(H, T) :- need(H, Need), not power(T, Need).

valid(S, H, T) :- setting(S), hazard(H), tool(T), affords(S, H), works(H, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, hid))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        for need in sorted(hazard.needs):
            lines.append(asp.fact("need", hid, need))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for power in sorted(tool.powers):
            lines.append(asp.fact("power", tid, power))
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
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "quail" not in sample.story.lower():
            raise StoryError("smoke test story missing text or required quail content")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero child rescues a tiny quail with help from a flashback."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.hazard and args.hazard not in SETTINGS[args.setting].affords:
        raise StoryError(
            f"(No story: {HAZARDS[args.hazard].label} does not fit {SETTINGS[args.setting].place} in this world.)"
        )
    if args.hazard and args.tool:
        dummy_setting = SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values()))
        if not tool_works(HAZARDS[args.hazard], TOOLS[args.tool]):
            raise StoryError(explain_rejection(dummy_setting, HAZARDS[args.hazard], TOOLS[args.tool]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, hazard_id, tool_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    friend_name = args.friend_name or pick_name(rng, friend_gender, avoid=hero_name)
    flashback_id = args.flashback or rng.choice(sorted(FLASHBACKS))
    grownup_type = args.grownup or rng.choice(["mother", "father", "grandmother", "grandfather"])
    hero_trait = rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        hazard=hazard_id,
        tool=tool_id,
        flashback=flashback_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        grownup_type=grownup_type,
        hero_trait=hero_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hazard not in HAZARDS:
        raise StoryError(f"Unknown hazard: {params.hazard}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")
    if params.flashback not in FLASHBACKS:
        raise StoryError(f"Unknown flashback: {params.flashback}")
    if params.hazard not in SETTINGS[params.setting].affords:
        raise StoryError(
            f"(No story: {HAZARDS[params.hazard].label} does not fit {SETTINGS[params.setting].place} in this world.)"
        )
    if not tool_works(HAZARDS[params.hazard], TOOLS[params.tool]):
        raise StoryError(explain_rejection(SETTINGS[params.setting], HAZARDS[params.hazard], TOOLS[params.tool]))

    world = tell(
        setting=SETTINGS[params.setting],
        hazard=HAZARDS[params.hazard],
        tool=TOOLS[params.tool],
        fb=FLASHBACKS[params.flashback],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        grownup_type=params.grownup_type,
        hero_trait=params.hero_trait,
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
        print(f"{len(combos)} compatible (setting, hazard, tool) combos:\n")
        for setting_id, hazard_id, tool_id in combos:
            print(f"  {setting_id:10} {hazard_id:12} {tool_id}")
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
            header = f"### {p.hero_name}: {p.hazard} in {p.setting} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
