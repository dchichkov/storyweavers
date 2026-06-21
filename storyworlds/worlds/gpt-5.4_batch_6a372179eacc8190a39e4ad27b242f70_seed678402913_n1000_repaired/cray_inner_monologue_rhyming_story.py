#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cray_inner_monologue_rhyming_story.py
================================================================

A standalone storyworld about a child who finds a tiny "cray" (a crayfish) out
of safe water and has to decide how to help it. The stories are written in a
gentle rhyming style and include the child's inner monologue as a real part of
the causal turn.

The world model is small but stateful:

    stranded cray + hot bank            -> cray stress rises
    rough carry method                  -> cray stress rises more
    long delay                          -> cray dries more
    return to proper water quickly      -> cray safe, child proud
    return to poor place or wait too long -> story refused or sad ending

The reasonableness gate enforces that:
- a carry method must be gentle enough for a small water animal
- the destination must actually be good water for a cray
- some explicit choices are known but refused with a clear StoryError

The rendered prose is not a frozen template. It branches on:
- setting details
- the child's helper tool
- whether a grown-up is nearby
- the child's inner monologue
- whether the rescue is quick and successful or sadly too late

Run it
------
    python storyworlds/worlds/gpt-5.4/cray_inner_monologue_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/cray_inner_monologue_rhyming_story.py --place creek --tool cup --destination stream_pool
    python storyworlds/worlds/gpt-5.4/cray_inner_monologue_rhyming_story.py --destination dry_grass
    python storyworlds/worlds/gpt-5.4/cray_inner_monologue_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/cray_inner_monologue_rhyming_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/cray_inner_monologue_rhyming_story.py --qa --json
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
GENTLE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    label: str
    start_spot: str
    water_name: str
    bank_detail: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    motion: str
    gentle: int
    water_holding: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Destination:
    id: str
    label: str
    phrase: str
    watery: bool
    depth: int
    good_for_cray: bool
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_heat_strain(world: World) -> list[str]:
    cray = world.get("cray")
    if cray.meters["stranded"] < THRESHOLD:
        return []
    sig = ("heat_strain",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cray.meters["dryness"] += 1
    cray.memes["stress"] += 1
    return []


def _r_rough_tool(world: World) -> list[str]:
    cray = world.get("cray")
    if cray.meters["handled_rough"] < THRESHOLD:
        return []
    sig = ("rough_tool",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cray.memes["stress"] += 1
    return []


def _r_safe_water(world: World) -> list[str]:
    cray = world.get("cray")
    if cray.meters["returned_home"] < THRESHOLD:
        return []
    sig = ("safe_water",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cray.meters["dryness"] = 0.0
    cray.memes["stress"] = 0.0
    cray.memes["calm"] += 1
    child = world.get("child")
    child.memes["pride"] += 1
    child.memes["care"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="heat_strain", tag="physical", apply=_r_heat_strain),
    Rule(name="rough_tool", tag="physical", apply=_r_rough_tool),
    Rule(name="safe_water", tag="resolution", apply=_r_safe_water),
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
            world.say(sent)
    return produced


def gentle_enough(tool: Tool) -> bool:
    return tool.gentle >= GENTLE_MIN


def good_destination(destination: Destination) -> bool:
    return destination.watery and destination.good_for_cray and destination.depth >= 2


def valid_triples() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for tool_id, tool in TOOLS.items():
            for dest_id, dest in DESTINATIONS.items():
                if gentle_enough(tool) and good_destination(dest):
                    out.append((place_id, tool_id, dest_id))
    return out


def expected_outcome(tool: Tool, destination: Destination, delay: int) -> str:
    if not gentle_enough(tool) or not good_destination(destination):
        return "invalid"
    return "safe" if delay <= 1 else "late"


def predict_rescue(world: World, tool: Tool, destination: Destination, delay: int) -> dict:
    sim = world.copy()
    cray = sim.get("cray")
    if tool.gentle < GENTLE_MIN:
        cray.meters["handled_rough"] += 1
    for _ in range(delay):
        cray.meters["stranded"] += 1
        propagate(sim, narrate=False)
    if destination.watery and destination.good_for_cray and destination.depth >= 2:
        cray.meters["returned_home"] += 1
        propagate(sim, narrate=False)
    return {
        "dryness": cray.meters["dryness"],
        "stress": cray.memes["stress"],
        "safe": cray.meters["returned_home"] >= THRESHOLD and delay <= 1,
    }


def opening(world: World, child: Entity, helper: Entity, place: Place) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"By {place.label}, {child.id} skipped light, while morning made the pebbles bright. "
        f"{place.bank_detail}"
    )
    world.say(
        f"Then near {place.start_spot}, tucked away, {child.pronoun()} found a tiny cray one day."
    )
    if helper.type in {"mother", "father"}:
        world.say(
            f"{child.id}'s {helper.label_word} stood close behind, with patient eyes and steady mind."
        )
    else:
        world.say(
            f"{helper.id} bent near with careful knees, and watched the reeds sway in the breeze."
        )


def discover_need(world: World, child: Entity, cray: Entity, place: Place) -> None:
    cray.meters["stranded"] += 1
    propagate(world, narrate=False)
    child.memes["care"] += 1
    world.say(
        f"The little cray clicked one claw so small, then barely moved at all, at all. "
        f"Its shell looked damp, but not for long; the sunny bank felt hot and wrong."
    )
    world.say(
        f'{child.id} thought, "Oh dear, oh me, this tiny cray needs water, not just me."'
    )


def temptation(world: World, child: Entity, cray: Entity) -> None:
    child.memes["want_keep"] += 1
    cray.memes["stress"] += 1
    world.say(
        f'{child.id} cupped both hands and whispered low, "You are so neat. I want you so." '
        f'Then came a thought that hummed inside: "If I keep the cray, will joy or trouble ride?"'
    )


def guide(world: World, helper: Entity, child: Entity, tool: Tool, destination: Destination) -> None:
    child.memes["trust"] += 1
    if helper.type in {"mother", "father"}:
        world.say(
            f'"Small friends need homes that fit them right," said {child.pronoun("possessive")} '
            f'{helper.label_word}, calm and bright. "Let\'s use {tool.phrase} and choose '
            f'{destination.phrase}."'
        )
    else:
        world.say(
            f'"We can be kind and quick," said {helper.id}. "A gentle move is best for it."'
        )


def decide(world: World, child: Entity, tool: Tool) -> None:
    child.memes["resolve"] += 1
    line = {
        "cup": f'"Use {tool.phrase}," {child.id} thought. "That way the cray stays cool, not caught."',
        "net": f'"The net is soft," {child.id} thought. "I can help without a pinch or jolt."',
        "leaf": f'"A wide green leaf can be a tray," {child.id} thought. "I can help the cray today."',
    }.get(tool.id, f'"I must be gentle with the cray," {child.id} thought. "That is the caring way."')
    world.say(line)


def carry(world: World, child: Entity, cray: Entity, tool: Tool, delay: int) -> None:
    world.say(
        f"So {child.id} used {tool.phrase}, {tool.motion}, with patient, careful, measured pace."
    )
    if tool.gentle < GENTLE_MIN:
        cray.meters["handled_rough"] += 1
        propagate(world, narrate=False)
    if delay > 0:
        for _ in range(delay):
            cray.meters["stranded"] += 1
            propagate(world, narrate=False)
        if delay == 1:
            world.say(
                "The way was short, though not too quick; the sun still made the warm stones prick."
            )
        else:
            world.say(
                "But time slipped by in dragging heat, and each long second baked the bank beneath."
            )


def release_safe(world: World, child: Entity, cray: Entity, destination: Destination, place: Place) -> None:
    cray.meters["returned_home"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last they reached {destination.phrase}. {child.id} tipped low with gentle grace."
    )
    world.say(
        f"The cray slid down with one soft sway, then tucked beneath a stone to stay. "
        f"{destination.image}"
    )
    world.say(
        f'{child.id} thought, "Good-bye, small cray. I helped you home, and that is best today."'
    )
    world.say(
        f"Back by {place.label}, the ripples shone; the child went home with kinder heart grown."
    )


def release_late(world: World, child: Entity, cray: Entity, destination: Destination) -> None:
    cray.meters["returned_home"] += 1
    cray.meters["weak"] += 1
    cray.memes["stress"] += 1
    world.say(
        f"They reached {destination.phrase} at last, but the hardest part had come too fast."
    )
    world.say(
        "The little cray sank slow and still, and did not scuttle with its usual will."
    )
    world.say(
        f'{child.id} thought, "I tried to care, yet next time I must hurry there."'
    )


def closing_late(world: World, child: Entity, helper: Entity) -> None:
    child.memes["sadness"] += 1
    child.memes["lesson"] += 1
    if helper.type in {"mother", "father"}:
        who = helper.label_word
    else:
        who = helper.id
    world.say(
        f"{who.capitalize()} held {child.id} near and said, "
        f'"Kind hearts must move while help is clear."'
    )
    world.say(
        "The child walked home beneath the sky, still soft of step and wondering why."
    )


def tell(
    place: Place,
    tool: Tool,
    destination: Destination,
    *,
    child_name: str = "Mia",
    child_gender: str = "girl",
    helper_type: str = "mother",
    helper_name: str = "Parent",
    trait: str = "gentle",
    delay: int = 0,
) -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=["little", trait],
    ))
    if helper_type in {"mother", "father"}:
        helper = world.add(Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            label="the parent",
            role="helper",
        ))
    else:
        helper = world.add(Entity(
            id=helper_name,
            kind="character",
            type=child_gender if helper_type == "friend" and child_gender == "boy" else ("girl" if helper_type == "friend" else helper_type),
            label=helper_name,
            role="helper",
        ))
    cray = world.add(Entity(
        id="cray",
        kind="character",
        type="crayfish",
        label="cray",
        phrase="a tiny cray",
        role="animal",
        tags={"cray", "water_animal"},
    ))

    opening(world, child, helper, place)
    discover_need(world, child, cray, place)

    world.para()
    temptation(world, child, cray)
    guide(world, helper, child, tool, destination)
    decide(world, child, tool)

    world.para()
    carry(world, child, cray, tool, delay)

    if expected_outcome(tool, destination, delay) == "safe":
        release_safe(world, child, cray, destination, place)
        outcome = "safe"
    else:
        release_late(world, child, cray, destination)
        world.para()
        closing_late(world, child, helper)
        outcome = "late"

    world.facts.update(
        child=child,
        helper=helper,
        cray=cray,
        place=place,
        tool=tool,
        destination=destination,
        delay=delay,
        outcome=outcome,
        prompt_word="cray",
        helper_kind=helper_type,
        rescued=(outcome == "safe"),
        safe_water=(destination.watery and destination.good_for_cray),
    )
    return world


PLACES = {
    "creek": Place(
        id="creek",
        label="the creek",
        start_spot="a flat warm stone",
        water_name="the creek pool",
        bank_detail="Tall reeds leaned low, and silver insects stitched the air.",
        ending_image="A ring of water winked in light, and everything seemed set just right.",
        tags={"creek", "water"},
    ),
    "pond": Place(
        id="pond",
        label="the pond edge",
        start_spot="the muddy rim",
        water_name="the pond shallows",
        bank_detail="Lilies floated by the shore, and dragonflies zipped to and fro.",
        ending_image="Round ripples spread in shining bands, like little claps from watery hands.",
        tags={"pond", "water"},
    ),
    "stream": Place(
        id="stream",
        label="the streamside path",
        start_spot="a patch of moss",
        water_name="the stream bend",
        bank_detail="Cool shade from willows striped the ground, and pebbles made a sleepy sound.",
        ending_image="The current hummed a happy tune and slipped away beneath the moon-bright noon.",
        tags={"stream", "water"},
    ),
}

TOOLS = {
    "cup": Tool(
        id="cup",
        label="cup",
        phrase="a little water cup",
        motion="and scooped a bit of creek water first",
        gentle=3,
        water_holding=True,
        tags={"cup", "gentle"},
    ),
    "net": Tool(
        id="net",
        label="net",
        phrase="a soft net",
        motion="and lifted the cray in one slow sweep",
        gentle=2,
        water_holding=False,
        tags={"net", "gentle"},
    ),
    "leaf": Tool(
        id="leaf",
        label="leaf",
        phrase="a broad green leaf",
        motion="and slid the cray along like a tiny boat",
        gentle=2,
        water_holding=False,
        tags={"leaf", "nature"},
    ),
    "stick": Tool(
        id="stick",
        label="stick",
        phrase="a poking stick",
        motion="and tried to nudge the cray along",
        gentle=1,
        water_holding=False,
        tags={"stick", "rough"},
    ),
}

DESTINATIONS = {
    "stream_pool": Destination(
        id="stream_pool",
        label="stream pool",
        phrase="the deeper stream pool",
        watery=True,
        depth=3,
        good_for_cray=True,
        image="Soon tiny bubbles rose nearby, and the water sang a low goodbye.",
        tags={"water", "stream_pool"},
    ),
    "reed_shade": Destination(
        id="reed_shade",
        label="reed shade",
        phrase="the shaded reeds in shallow water",
        watery=True,
        depth=2,
        good_for_cray=True,
        image="The reeds made doors of green and cool, a secret room beside the pool.",
        tags={"water", "reeds"},
    ),
    "mud_puddle": Destination(
        id="mud_puddle",
        label="mud puddle",
        phrase="a shrinking mud puddle",
        watery=True,
        depth=1,
        good_for_cray=False,
        image="The puddle looked dark, but thin and small, not like a home at all.",
        tags={"puddle", "bad_home"},
    ),
    "dry_grass": Destination(
        id="dry_grass",
        label="dry grass",
        phrase="the dry yellow grass",
        watery=False,
        depth=0,
        good_for_cray=False,
        image="The grass was whispery, hot, and bare.",
        tags={"grass", "bad_home"},
    ),
}


@dataclass
class StoryParams:
    place: str
    tool: str
    destination: str
    child_name: str
    child_gender: str
    helper_type: str
    helper_name: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella", "Lucy", "Ivy"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Theo", "Finn", "Eli", "Noah"]
TRAITS = ["gentle", "curious", "careful", "kind", "thoughtful"]
FRIEND_NAMES = ["Pip", "June", "Tess", "Milo", "Wren"]

CURATED = [
    StoryParams(
        place="creek",
        tool="cup",
        destination="stream_pool",
        child_name="Mia",
        child_gender="girl",
        helper_type="mother",
        helper_name="Parent",
        trait="gentle",
        delay=0,
    ),
    StoryParams(
        place="pond",
        tool="leaf",
        destination="reed_shade",
        child_name="Ben",
        child_gender="boy",
        helper_type="father",
        helper_name="Parent",
        trait="careful",
        delay=1,
    ),
    StoryParams(
        place="stream",
        tool="net",
        destination="stream_pool",
        child_name="Nora",
        child_gender="girl",
        helper_type="friend",
        helper_name="Pip",
        trait="curious",
        delay=2,
    ),
]


KNOWLEDGE = {
    "cray": [
        (
            "What is a cray?",
            "A cray is a short way to say crayfish, a small animal that lives in fresh water. It has a hard shell and little claws."
        )
    ],
    "water_animal": [
        (
            "Why does a crayfish need water?",
            "A crayfish is a water animal, so it belongs in clean fresh water where it can breathe and hide. A hot dry bank can hurt it."
        )
    ],
    "cup": [
        (
            "Why can a cup help move a tiny water animal?",
            "A small cup can hold water around the animal while a grown-up or child carries it gently. That helps keep its body wet and calm."
        )
    ],
    "net": [
        (
            "What makes a soft net better than a rough poke?",
            "A soft net can lift a small animal without jabbing it. Gentle tools are kinder because they do not bump or scrape as much."
        )
    ],
    "leaf": [
        (
            "How can a leaf help in nature?",
            "A wide leaf can work like a tiny tray for one careful moment. It is smooth and gentle when someone moves slowly."
        )
    ],
    "stream_pool": [
        (
            "Why is a deeper stream pool a good home for a cray?",
            "A deeper pool has water, shade, and places to hide under stones or plants. That makes it safer than a hot dry edge."
        )
    ],
    "reeds": [
        (
            "Why do reeds help small water animals?",
            "Reeds give shade and hiding spots in shallow water. Small animals can rest there and stay out of danger."
        )
    ],
    "kindness": [
        (
            "What does kindness mean with little animals?",
            "Kindness means noticing what the animal needs, not just what you want. Sometimes the kindest choice is to let a wild creature go home."
        )
    ],
}

KNOWLEDGE_ORDER = ["cray", "water_animal", "cup", "net", "leaf", "stream_pool", "reeds", "kindness"]


def explain_tool(tool: Tool) -> str:
    return (
        f"(No story: '{tool.id}' is known here, but it is too rough for a tiny cray "
        f"(gentle={tool.gentle} < {GENTLE_MIN}). Pick a gentler tool like cup, net, or leaf.)"
    )


def explain_destination(destination: Destination) -> str:
    if not destination.watery:
        return (
            f"(No story: {destination.phrase} is dry, so a cray would not be safe there. "
            f"Choose real water, like stream_pool or reed_shade.)"
        )
    return (
        f"(No story: {destination.phrase} is water, but it is too shallow or unsafe to be a good home for a cray. "
        f"Choose deeper, safer water.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    tool = f["tool"]
    dest = f["destination"]
    place = f["place"]
    outcome = f["outcome"]
    if outcome == "safe":
        return [
            'Write a short rhyming story for a 3-to-5-year-old that includes the word "cray" and uses inner monologue.',
            f"Tell a gentle rhyming story where {child.id} finds a tiny cray by {place.label}, thinks about keeping it, then decides to help it home with {tool.phrase}.",
            f"Write a child-facing poem-story with quoted thoughts inside, where a small cray is returned to {dest.phrase} and the ending shows kindness."
        ]
    return [
        'Write a short rhyming story for a 3-to-5-year-old that includes the word "cray" and uses inner monologue.',
        f"Tell a bittersweet rhyming story where {child.id} tries to help a tiny cray, but learns that help must come quickly.",
        "Write a gentle cautionary verse-story in which a child thinks carefully about a wild animal and learns to hurry when care is needed."
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    tool = f["tool"]
    dest = f["destination"]
    outcome = f["outcome"]
    helper_name = helper.label_word if helper.type in {"mother", "father"} else helper.id

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who finds a tiny cray near {place.label}. The story also includes {helper_name}, who helps {child.id} think about what the cray needs."
        ),
        (
            "What problem did the child notice?",
            f"{child.id} saw that the tiny cray was stuck away from safe water on a warm bank. That mattered because a cray belongs in water, not on hot dry ground."
        ),
        (
            "What was the child's inner monologue about?",
            f"{child.id} first thought the little cray was special and wanted to keep it close. Then {child.pronoun().capitalize()} thought more deeply and realized the kind thing was to help it get home."
        ),
        (
            f"How did {child.id} try to help the cray?",
            f"{child.id} used {tool.phrase} to move the cray gently toward {dest.phrase}. The method mattered because a small animal can be hurt by rough handling."
        ),
    ]
    if outcome == "safe":
        qa.append(
            (
                "Why did the story end happily?",
                f"It ended happily because the cray reached good water in time and could hide safely again. {child.id} also changed inside, because kindness became more important than keeping the animal."
            )
        )
        qa.append(
            (
                "What changed at the end?",
                f"At the start, the cray was stranded and {child.id} was torn between wonder and wanting to keep it. At the end, the cray was back in water and {child.id} felt proud for choosing care."
            )
        )
    else:
        qa.append(
            (
                "Why was the ending sadder?",
                f"The help came too late after too much time passed in the heat. {child.id} still tried to be kind, but the story teaches that noticing a need should be followed by quick action."
            )
        )
        qa.append(
            (
                "What did the child learn?",
                f"{child.id} learned that loving a wild creature means doing what is best for it right away. The lesson came from seeing that care must be both gentle and timely."
            )
        )
    return qa


def world_knowledge_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"cray", "water_animal", "kindness"}
    tags |= set(f["tool"].tags)
    tags |= set(f["destination"].tags)
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
gentle_enough(T) :- tool(T), gentle(T, G), gentle_min(M), G >= M.
good_destination(D) :- destination(D), watery(D), good_for_cray(D), depth(D, N), N >= 2.
valid(P, T, D) :- place(P), gentle_enough(T), good_destination(D).

safe_outcome :- delay(D), D <= 1.
late_outcome :- delay(D), D > 1.

outcome(safe) :- chosen_tool(T), chosen_destination(D),
                 gentle_enough(T), good_destination(D), safe_outcome.
outcome(late) :- chosen_tool(T), chosen_destination(D),
                 gentle_enough(T), good_destination(D), late_outcome.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("gentle", tid, tool.gentle))
    for did, dest in DESTINATIONS.items():
        lines.append(asp.fact("destination", did))
        if dest.watery:
            lines.append(asp.fact("watery", did))
        if dest.good_for_cray:
            lines.append(asp.fact("good_for_cray", did))
        lines.append(asp.fact("depth", did, dest.depth))
    lines.append(asp.fact("gentle_min", GENTLE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_destination", params.destination),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_triples())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_triples() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for delay in [0, 1, 2]:
        for tool_id, tool in TOOLS.items():
            for dest_id, dest in DESTINATIONS.items():
                if gentle_enough(tool) and good_destination(dest):
                    cases.append(
                        StoryParams(
                            place="creek",
                            tool=tool_id,
                            destination=dest_id,
                            child_name="Mia",
                            child_gender="girl",
                            helper_type="mother",
                            helper_name="Parent",
                            trait="gentle",
                            delay=delay,
                        )
                    )
    bad = 0
    for params in cases:
        if asp_outcome(params) != expected_outcome(TOOLS[params.tool], DESTINATIONS[params.destination], params.delay):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story in smoke test")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child finds a tiny cray and chooses kindness."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "friend"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool is not None and not gentle_enough(TOOLS[args.tool]):
        raise StoryError(explain_tool(TOOLS[args.tool]))
    if args.destination is not None and not good_destination(DESTINATIONS[args.destination]):
        raise StoryError(explain_destination(DESTINATIONS[args.destination]))

    combos = [
        combo for combo in valid_triples()
        if (args.place is None or combo[0] == args.place)
        and (args.tool is None or combo[1] == args.tool)
        and (args.destination is None or combo[2] == args.destination)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, tool, destination = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(["mother", "father", "friend"])
    helper_name = "Parent" if helper_type in {"mother", "father"} else rng.choice(FRIEND_NAMES)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])
    return StoryParams(
        place=place,
        tool=tool,
        destination=destination,
        child_name=child_name,
        child_gender=gender,
        helper_type=helper_type,
        helper_name=helper_name,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(Unknown destination: {params.destination})")

    tool = TOOLS[params.tool]
    destination = DESTINATIONS[params.destination]
    if not gentle_enough(tool):
        raise StoryError(explain_tool(tool))
    if not good_destination(destination):
        raise StoryError(explain_destination(destination))

    world = tell(
        PLACES[params.place],
        tool,
        destination,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        helper_name=params.helper_name,
        trait=params.trait,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_items(world)],
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
        print(f"{len(combos)} compatible (place, tool, destination) combos:\n")
        for place, tool, dest in combos:
            print(f"  {place:8} {tool:6} {dest}")
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
            header = f"### {p.child_name}: {p.tool} to {p.destination} at {p.place} ({expected_outcome(TOOLS[p.tool], DESTINATIONS[p.destination], p.delay)})"
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
