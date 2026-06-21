#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/prohibit_curiosity_rhyming_story.py
==============================================================

A standalone story world about curiosity, a gentle prohibition, and a kinder way
to look closely. The prose aims for a light rhyming-story feel while still being
driven by simulated state.

Premise
-------
A curious child finds something small and living or growing. A caring grown-up
does not prohibit curiosity itself, but does prohibit grabbing or poking with
bare hands. The child either reaches anyway and causes a small upset, or listens
and uses a safe observing tool. The ending proves what changed: curiosity stays,
but it becomes careful.

Constraint idea
---------------
Not every safe tool answers every kind of curiosity. A magnifying glass helps
with tiny still things. Binoculars help with a nest that should be viewed from a
distance. A step stool helps a child see a high wonder safely. The story world
refuses pairings where the offered tool would not honestly solve the child's
problem.

Run it
------
    python storyworlds/worlds/gpt-5.4/prohibit_curiosity_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/prohibit_curiosity_rhyming_story.py --wonder chrysalis
    python storyworlds/worlds/gpt-5.4/prohibit_curiosity_rhyming_story.py --tool notebook
    python storyworlds/worlds/gpt-5.4/prohibit_curiosity_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/prohibit_curiosity_rhyming_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/prohibit_curiosity_rhyming_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    fragile: bool = False
    reachable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    phrase: str
    line: str
    allows: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Wonder:
    id: str
    label: str
    phrase: str
    home: str
    tiny_word: str
    caution_line: str
    upset_line: str
    calm_line: str
    ending_line: str
    observe_need: str
    reach: str = "low"
    fragile: bool = True
    living: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str] = field(default_factory=set)
    for_height: set[str] = field(default_factory=set)
    action_line: str = ""
    ending_line: str = ""
    tags: set[str] = field(default_factory=set)


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


def _r_upset(world: World) -> list[str]:
    out: list[str] = []
    wonder = world.get("wonder")
    child = world.get("child")
    if wonder.meters["jostled"] < THRESHOLD:
        return out
    sig = ("upset", wonder.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    wonder.meters["needs_calm"] += 1
    child.memes["worry"] += 1
    out.append("__upset__")
    return out


def _r_repair_relief(world: World) -> list[str]:
    out: list[str] = []
    wonder = world.get("wonder")
    grown = world.get("grown")
    child = world.get("child")
    if wonder.meters["settled"] < THRESHOLD:
        return out
    sig = ("settled", wonder.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["relief"] += 1
    grown.memes["care"] += 1
    out.append("__settled__")
    return out


CAUSAL_RULES = [
    Rule(name="upset", tag="physical", apply=_r_upset),
    Rule(name="settled", tag="social", apply=_r_repair_relief),
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


def tool_fits(wonder: Wonder, tool: Tool) -> bool:
    return wonder.observe_need in tool.helps_with and wonder.reach in tool.for_height


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for wonder_id in sorted(place.allows):
            wonder = WONDERS[wonder_id]
            for tool_id, tool in TOOLS.items():
                if tool_fits(wonder, tool):
                    combos.append((place_id, wonder_id, tool_id))
    return combos


def predict_upset(world: World) -> bool:
    sim = world.copy()
    wonder = sim.get("wonder")
    wonder.meters["jostled"] += 1
    propagate(sim, narrate=False)
    return wonder.meters["needs_calm"] >= THRESHOLD


def introduce(world: World, child: Entity, grown: Entity, wonder: Wonder) -> None:
    world.say(
        f"{world.place.line} {child.id} skipped close with curious eyes, "
        f"while {grown.label_word} walked at {child.pronoun('possessive')} side."
    )
    world.say(
        f"There, in {wonder.home}, {child.pronoun()} found {wonder.phrase}; "
        f"it looked so small and secret that it seemed to hum a little song."
    )


def admire(world: World, child: Entity, wonder: Wonder) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'"What is that?" asked {child.id}. "It is so {wonder.tiny_word}, '
        f'so still, so neat. I want to see it up close and feel it with my hand and feet."'
    )


def prohibit_touch(world: World, grown: Entity, child: Entity, wonder: Wonder) -> None:
    child.memes["frustration"] += 1
    grown.memes["care"] += 1
    predicted = predict_upset(world)
    world.facts["predicted_upset"] = predicted
    world.say(
        f'{grown.label_word.capitalize()} knelt beside {child.id} and softly said, '
        f'"I do not prohibit your wondering, little one, not one bright bit in your head. '
        f'But I must prohibit poking {wonder.label}, because {wonder.caution_line}."'
    )


def reach_anyway(world: World, child: Entity, wonder_ent: Entity, wonder: Wonder) -> None:
    child.memes["impulse"] += 1
    wonder_ent.meters["jostled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But curiosity bounced like a drum in {child.id}'s chest, and "
        f"{child.pronoun()} reached one finger out on a restless little quest."
    )
    world.say(wonder.upset_line)


def listen_first(world: World, child: Entity, grown: Entity) -> None:
    child.memes["careful"] += 1
    child.memes["trust"] += 1
    world.say(
        f"{child.id} curled {child.pronoun('possessive')} fingers back and took a slower breath. "
        f'"All right," {child.pronoun()} whispered. "I can be gentle instead of swift."'
    )
    world.say(
        f"{grown.label_word.capitalize()} smiled, because curiosity had stayed, "
        f"but rough little grabbing had kindly been delayed."
    )


def calm_and_repair(world: World, grown: Entity, wonder_ent: Entity, wonder: Wonder) -> None:
    wonder_ent.meters["settled"] += 1
    wonder_ent.meters["needs_calm"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{grown.label_word.capitalize()} moved with careful hands and {wonder.calm_line}."
    )


def offer_tool(world: World, grown: Entity, child: Entity, tool: Tool) -> None:
    child.memes["hope"] += 1
    world.say(
        f'Then {grown.label_word} said, "Come, here is a better way to look and learn today."'
    )
    world.say(
        f"{tool.action_line} {child.id}'s eyes grew round and bright, "
        f"for now the little mystery could stay safe in sight."
    )


def observe_safely(world: World, child: Entity, wonder_ent: Entity, tool: Tool, wonder: Wonder) -> None:
    child.memes["joy"] += 1
    child.memes["careful"] += 1
    wonder_ent.meters["observed"] += 1
    world.say(
        f"{child.id} looked, and looked again, with patient, shining eyes. "
        f"{tool.ending_line} Soon {child.pronoun()} noticed tiny details like a soft and secret prize."
    )
    world.say(wonder.ending_line)


def moral_end(world: World, child: Entity, grown: Entity, wonder: Wonder, tool: Tool) -> None:
    child.memes["lesson"] += 1
    world.say(
        f'So {child.id} learned that day beneath the open sky: curiosity need not grab or pry. '
        f'When hands stay kind and tools stay wise, small wonders can grow up before our eyes.'
    )
    world.say(
        f"And {grown.label_word} hugged {child.pronoun('object')} close and said with quiet delight, "
        f'"You may ask and watch and wonder all you want, just do it soft and right."'
    )


def tell(
    place: Place,
    wonder: Wonder,
    tool: Tool,
    *,
    child_name: str = "Mina",
    child_gender: str = "girl",
    grown_type: str = "mother",
    child_trait: str = "curious",
    outcome: str = "reach",
) -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        label=child_name,
        traits=[child_trait],
    ))
    grown = world.add(Entity(
        id="Parent",
        kind="character",
        type=grown_type,
        role="grown",
        label="the parent",
    ))
    wonder_ent = world.add(Entity(
        id="wonder",
        kind="thing",
        type="wonder",
        label=wonder.label,
        phrase=wonder.phrase,
        role="wonder",
        tags=set(wonder.tags),
        fragile=wonder.fragile,
        reachable=(wonder.reach == "low"),
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        role="tool",
        tags=set(tool.tags),
    ))

    introduce(world, child, grown, wonder)
    admire(world, child, wonder)

    world.para()
    prohibit_touch(world, grown, child, wonder)

    if outcome == "reach":
        reach_anyway(world, child, wonder_ent, wonder)
        world.para()
        calm_and_repair(world, grown, wonder_ent, wonder)
        offer_tool(world, grown, child, tool)
    else:
        listen_first(world, child, grown)
        world.para()
        offer_tool(world, grown, child, tool)

    observe_safely(world, child, wonder_ent, tool, wonder)
    moral_end(world, child, grown, wonder, tool)

    world.facts.update(
        child=child,
        grown=grown,
        wonder_cfg=wonder,
        wonder=wonder_ent,
        tool_cfg=tool,
        tool=tool_ent,
        place=place,
        outcome=outcome,
        upset=wonder_ent.meters["jostled"] >= THRESHOLD,
        settled=wonder_ent.meters["settled"] >= THRESHOLD or outcome == "listen",
    )
    return world


PLACES = {
    "garden": Place(
        id="garden",
        label="garden",
        phrase="the garden",
        line="In the garden where the sweet peas curled, bees made loops through the waking world.",
        allows={"chrysalis", "nest", "snail_eggs"},
        tags={"garden"},
    ),
    "porch": Place(
        id="porch",
        label="porch",
        phrase="the porch",
        line="On the porch where the shadows lay, the morning light made silver play.",
        allows={"chrysalis", "nest"},
        tags={"home"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="greenhouse",
        phrase="the greenhouse",
        line="In the greenhouse warm and bright, leaves held drops of glassy light.",
        allows={"sprout", "chrysalis"},
        tags={"garden"},
    ),
}

WONDERS = {
    "chrysalis": Wonder(
        id="chrysalis",
        label="the chrysalis",
        phrase="a green chrysalis hanging under a leaf",
        home="the folded shade of a broad green leaf",
        tiny_word="quiet",
        caution_line="a bump can shake the sleeper inside before it is ready to glide",
        upset_line="The leaf gave a wobble and a trembly swing; the little green case rocked on its string.",
        calm_line="cupped the leaf's stem, held the shake still, and waited until the tiny case rested again",
        ending_line="The chrysalis stayed safe, snug on its thread, while wonder and patience danced on in its stead.",
        observe_need="tiny_close",
        reach="low",
        tags={"chrysalis", "butterfly", "gentle"},
    ),
    "nest": Wonder(
        id="nest",
        label="the nest",
        phrase="a robin nest tucked high in the vine",
        home="a curl of ivy above the fence",
        tiny_word="high",
        caution_line="hands and faces too near can scare the parent bird away",
        upset_line="The ivy shook, a mother robin flashed, and into the air her red breast dashed.",
        calm_line="stepped back, stood still as a tree, and waited for the robin to settle where she could see",
        ending_line="Soon the robin returned with a twig and a peep, and the nest kept its calm in the cradle of sleep.",
        observe_need="far_look",
        reach="high",
        tags={"bird", "nest", "gentle"},
    ),
    "sprout": Wonder(
        id="sprout",
        label="the sprout",
        phrase="a pale bean sprout lifting out of the soil",
        home="a clay pot by the warm wet pane",
        tiny_word="new",
        caution_line="a squeeze can bend the tender stem before it learns to stand",
        upset_line="A little stem bent low with a frightened sway, and one bead of water slid away.",
        calm_line="patted the soil around the stem and tied it with soft garden twine so it could stand straight again",
        ending_line="The sprout stood small but brave and bright, drinking the greenhouse morning light.",
        observe_need="tiny_close",
        reach="low",
        tags={"plant", "sprout", "garden"},
    ),
    "snail_eggs": Wonder(
        id="snail_eggs",
        label="the snail eggs",
        phrase="a pearl-like clutch of snail eggs under a flowerpot rim",
        home="the cool dim lip of an upside-down flowerpot",
        tiny_word="round",
        caution_line="their clear little shells are so soft that a poke can break them",
        upset_line="The pot rim clicked and the pearls gave a shiver; even a tiny touch made the cluster quiver.",
        calm_line="set the pot rim gently back and shaded the clutch so the ground stayed cool and still",
        ending_line="The snail eggs gleamed like moon-drops in a row, safe to rest and safe to grow.",
        observe_need="tiny_close",
        reach="low",
        tags={"snail", "eggs", "gentle"},
    ),
}

TOOLS = {
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        phrase="a round magnifying glass",
        helps_with={"tiny_close"},
        for_height={"low"},
        action_line="Out came a round magnifying glass that made the little wonder look grand instead of small.",
        ending_line="Through the glass the lines and colors grew clear without one poke at all.",
        tags={"magnifier", "observe"},
    ),
    "binoculars": Tool(
        id="binoculars",
        label="binoculars",
        phrase="small binoculars with a soft strap",
        helps_with={"far_look"},
        for_height={"high"},
        action_line="Out came small binoculars with a soft blue strap, so far-away feathers could fill a careful lap of sight.",
        ending_line="Through the lenses the high place seemed near, though their feet stayed kindly down here.",
        tags={"binoculars", "observe"},
    ),
    "step_stool": Tool(
        id="step_stool",
        label="step stool",
        phrase="a sturdy step stool",
        helps_with={"tiny_close"},
        for_height={"high"},
        action_line="Out came a sturdy step stool, so eyes could rise while hands stayed by a grown-up's side.",
        ending_line="From the stool the child could see much more, yet still kept gentle feet upon the floor.",
        tags={"stool", "observe"},
    ),
    "notebook": Tool(
        id="notebook",
        label="notebook",
        phrase="a little notebook",
        helps_with={"remember"},
        for_height={"low", "high"},
        action_line="Out came a little notebook for drawing what they saw in careful lines.",
        ending_line="The pages filled with guesses and shapes, but the hidden wonder stayed just as it was.",
        tags={"notebook", "observe"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Poppy", "Zoe", "Ivy", "Ella", "Ruby"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Theo", "Leo", "Ben", "Eli", "Jude"]
TRAITS = ["curious", "eager", "bright", "careful", "lively"]


@dataclass
class StoryParams:
    place: str
    wonder: str
    tool: str
    name: str
    gender: str
    grown: str
    trait: str
    outcome: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="garden",
        wonder="chrysalis",
        tool="magnifier",
        name="Mina",
        gender="girl",
        grown="mother",
        trait="curious",
        outcome="reach",
    ),
    StoryParams(
        place="garden",
        wonder="nest",
        tool="binoculars",
        name="Owen",
        gender="boy",
        grown="father",
        trait="bright",
        outcome="listen",
    ),
    StoryParams(
        place="greenhouse",
        wonder="sprout",
        tool="magnifier",
        name="Ivy",
        gender="girl",
        grown="mother",
        trait="eager",
        outcome="reach",
    ),
    StoryParams(
        place="garden",
        wonder="snail_eggs",
        tool="magnifier",
        name="Leo",
        gender="boy",
        grown="father",
        trait="curious",
        outcome="listen",
    ),
    StoryParams(
        place="porch",
        wonder="nest",
        tool="binoculars",
        name="Ruby",
        gender="girl",
        grown="mother",
        trait="careful",
        outcome="listen",
    ),
]


KNOWLEDGE = {
    "garden": [
        (
            "Why do many tiny living things hide in gardens?",
            "Gardens have leaves, stems, damp soil, and quiet corners. Those places can feel safe for small creatures and new plants."
        )
    ],
    "chrysalis": [
        (
            "What is a chrysalis?",
            "A chrysalis is the hard case some caterpillars rest inside while they change into butterflies. It needs time and gentle stillness."
        )
    ],
    "butterfly": [
        (
            "Why should you not shake a chrysalis?",
            "The little animal inside is changing and needs to stay safe. Shaking it can hurt that quiet growing work."
        )
    ],
    "bird": [
        (
            "Why should people look at bird nests from a distance?",
            "A parent bird can feel scared if people come too close. Watching from farther away helps the bird keep caring for the nest."
        )
    ],
    "nest": [
        (
            "What is a bird nest for?",
            "A nest is a small home where a bird keeps eggs or babies warm and safe. It holds them while they grow."
        )
    ],
    "plant": [
        (
            "Why are new sprouts easy to bend?",
            "A new sprout has a soft young stem. It has not grown strong and woody yet, so it bends easily."
        )
    ],
    "snail": [
        (
            "What is a snail egg like?",
            "A snail egg is tiny and soft and can look a little clear or pearly. It must be handled very gently, or not handled at all."
        )
    ],
    "eggs": [
        (
            "Why are many eggs fragile?",
            "Eggs protect something growing inside, but their shells can be delicate. That is why rough poking can break them."
        )
    ],
    "magnifier": [
        (
            "What does a magnifying glass do?",
            "A magnifying glass makes a small thing look bigger to your eyes. It helps you see details without touching."
        )
    ],
    "binoculars": [
        (
            "What are binoculars for?",
            "Binoculars help you see far-away things more clearly. They are useful when you want to look closely while staying back."
        )
    ],
    "stool": [
        (
            "Why can a step stool be useful?",
            "A step stool can lift your eyes higher in a steady way. With a grown-up nearby, it can help you see something above you more safely."
        )
    ],
    "observe": [
        (
            "What does it mean to observe something carefully?",
            "To observe means to look closely and notice details. Careful observing lets you learn without grabbing or breaking."
        )
    ],
    "gentle": [
        (
            "Why is being gentle important with small living things?",
            "Small living things can be easy to frighten, bend, or break. Gentle behavior helps keep them safe while you learn about them."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "garden",
    "chrysalis",
    "butterfly",
    "bird",
    "nest",
    "plant",
    "snail",
    "eggs",
    "magnifier",
    "binoculars",
    "stool",
    "observe",
    "gentle",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    wonder = f["wonder_cfg"]
    tool = f["tool_cfg"]
    place = f["place"]
    outcome = f["outcome"]
    if outcome == "reach":
        return [
            f'Write a short rhyming story for a 3-to-5-year-old that includes the word "prohibit" and shows a curious child learning to look without touching.',
            f"Tell a gentle rhyming story set in {place.phrase} where {child.id} is curious about {wonder.label}, reaches too soon, and then learns to use {tool.phrase}.",
            f"Write a child-facing poem-story where a grown-up says they do not prohibit wondering, only poking, and the ending shows curiosity becoming careful.",
        ]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the word "prohibit" and centers on curiosity handled kindly.',
        f"Tell a gentle rhyming story set in {place.phrase} where {child.id} wants to get close to {wonder.label} but listens and uses {tool.phrase} instead.",
        f"Write a child-facing poem-story where a grown-up does not prohibit questions, only rough touching, and the ending shows safe observing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grown = f["grown"]
    wonder = f["wonder_cfg"]
    tool = f["tool_cfg"]
    place = f["place"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious little {child.type}, and {child.pronoun('possessive')} {grown.label_word} in {place.phrase}. Together they find {wonder.phrase} and decide how to treat it."
        ),
        (
            f"What made {child.id} curious?",
            f"{child.id} found {wonder.phrase}, and it looked small, hidden, and mysterious. That made {child.pronoun('object')} want to get very close and learn more."
        ),
        (
            "What did the grown-up prohibit?",
            f"{grown.label_word.capitalize()} did not prohibit wondering or asking questions. {grown.pronoun().capitalize()} prohibited poking {wonder.label}, because {wonder.caution_line}."
        ),
    ]
    if outcome == "reach":
        qa.append(
            (
                f"What happened when {child.id} reached out?",
                f"{child.id} touched too soon, and {wonder.upset_line[:-1] if wonder.upset_line.endswith('.') else wonder.upset_line}. The small upset showed why gentle hands mattered."
            )
        )
        qa.append(
            (
                f"How did {child.id}'s {grown.label_word} help fix the problem?",
                f"{grown.label_word.capitalize()} moved carefully and {wonder.calm_line}. Then {grown.pronoun()} offered {tool.phrase} so {child.id} could still look closely without another touch."
            )
        )
    else:
        qa.append(
            (
                f"What did {child.id} do after hearing the warning?",
                f"{child.id} pulled back {child.pronoun('possessive')} hand and listened. That choice kept {wonder.label} calm before anything went wrong."
            )
        )
    qa.append(
        (
            f"How did the story end?",
            f"It ended with {child.id} using {tool.phrase} to observe safely. The ending proves {child.pronoun('possessive')} curiosity stayed strong, but became kinder and more careful."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["place"].tags) | set(world.facts["wonder_cfg"].tags) | set(world.facts["tool_cfg"].tags)
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.fragile:
            bits.append("fragile=True")
        if ent.reachable is not True:
            bits.append(f"reachable={ent.reachable}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Optional[str], wonder: Optional[str], tool: Optional[str]) -> str:
    if wonder and tool and not tool_fits(WONDERS[wonder], TOOLS[tool]):
        w = WONDERS[wonder]
        t = TOOLS[tool]
        return (
            f"(No story: {t.label} does not honestly solve this curiosity problem. "
            f"{w.label.capitalize()} needs {w.observe_need} at {w.reach} height, "
            f"but {t.label} supports {sorted(t.helps_with)} at {sorted(t.for_height)}.)"
        )
    if place and wonder and wonder not in PLACES[place].allows:
        return (
            f"(No story: {WONDERS[wonder].label} is not one of the small wonders found in {PLACES[place].phrase} here.)"
        )
    return "(No valid combination matches the given options.)"


ASP_RULES = r"""
fits(W, T) :- wonder(W), tool(T), needs(W, N), helps(T, N), reach(W, H), height(T, H).
valid(P, W, T) :- place(P), allows(P, W), fits(W, T).

outcome(reach)  :- choice(reach).
outcome(listen) :- choice(listen).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for wonder_id in sorted(place.allows):
            lines.append(asp.fact("allows", place_id, wonder_id))
    for wonder_id, wonder in WONDERS.items():
        lines.append(asp.fact("wonder", wonder_id))
        lines.append(asp.fact("needs", wonder_id, wonder.observe_need))
        lines.append(asp.fact("reach", wonder_id, wonder.reach))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for need in sorted(tool.helps_with):
            lines.append(asp.fact("helps", tool_id, need))
        for height in sorted(tool.for_height):
            lines.append(asp.fact("height", tool_id, height))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("choice", params.outcome)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    for p in cases:
        if asp_outcome(p) != p.outcome:
            rc = 1
            print(f"MISMATCH in outcome for curated case: {p}")
            break
    else:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story or "prohibit" not in smoke.story.lower():
            raise StoryError("(Smoke test failed: story missing content.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: curiosity, prohibition, and a safer way to look closely."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--wonder", choices=WONDERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--grown", choices=["mother", "father"])
    ap.add_argument("--outcome", choices=["reach", "listen"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.wonder and args.wonder not in PLACES[args.place].allows:
        raise StoryError(explain_rejection(args.place, args.wonder, args.tool))
    if args.wonder and args.tool and not tool_fits(WONDERS[args.wonder], TOOLS[args.tool]):
        raise StoryError(explain_rejection(args.place, args.wonder, args.tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.wonder is None or combo[1] == args.wonder)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError(explain_rejection(args.place, args.wonder, args.tool))

    place, wonder, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grown = args.grown or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    outcome = args.outcome or rng.choice(["reach", "listen", "listen"])
    return StoryParams(
        place=place,
        wonder=wonder,
        tool=tool,
        name=name,
        gender=gender,
        grown=grown,
        trait=trait,
        outcome=outcome,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.wonder not in WONDERS:
        raise StoryError(f"(Unknown wonder: {params.wonder})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.outcome not in {"reach", "listen"}:
        raise StoryError(f"(Unknown outcome: {params.outcome})")
    if params.wonder not in PLACES[params.place].allows:
        raise StoryError(explain_rejection(params.place, params.wonder, params.tool))
    if not tool_fits(WONDERS[params.wonder], TOOLS[params.tool]):
        raise StoryError(explain_rejection(params.place, params.wonder, params.tool))

    world = tell(
        PLACES[params.place],
        WONDERS[params.wonder],
        TOOLS[params.tool],
        child_name=params.name,
        child_gender=params.gender,
        grown_type=params.grown,
        child_trait=params.trait,
        outcome=params.outcome,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, wonder, tool) combos:\n")
        for place, wonder, tool in combos:
            print(f"  {place:10} {wonder:12} {tool}")
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
            header = f"### {p.name}: {p.wonder} at {p.place} with {p.tool} ({p.outcome})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
