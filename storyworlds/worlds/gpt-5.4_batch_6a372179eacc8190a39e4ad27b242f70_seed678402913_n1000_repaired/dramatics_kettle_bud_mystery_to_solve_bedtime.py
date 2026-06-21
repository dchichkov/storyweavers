#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dramatics_kettle_bud_mystery_to_solve_bedtime.py
==============================================================================

A small bedtime storyworld about a tiny kitchen mystery: a flower bud keeps
appearing beside the bedtime kettle, and a child gently investigates until the
cause is found. The domain is built for close, constraint-checked variations
with a clear beginning, a state-driven middle mystery, and a calm ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4/dramatics_kettle_bud_mystery_to_solve_bedtime.py
    python storyworlds/worlds/gpt-5.4/dramatics_kettle_bud_mystery_to_solve_bedtime.py --plant jasmine --agent kitten --method pawprints
    python storyworlds/worlds/gpt-5.4/dramatics_kettle_bud_mystery_to_solve_bedtime.py --agent shadow
    python storyworlds/worlds/gpt-5.4/dramatics_kettle_bud_mystery_to_solve_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/dramatics_kettle_bud_mystery_to_solve_bedtime.py --qa --json
    python storyworlds/worlds/gpt-5.4/dramatics_kettle_bud_mystery_to_solve_bedtime.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
class Plant:
    id: str
    label: str
    phrase: str
    place: str
    scent: str
    color: str
    has_bud: bool = True
    fragile: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Kettle:
    id: str
    label: str
    phrase: str
    song: str
    steam: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Agent:
    id: str
    label: str
    phrase: str
    clue_tag: str
    clue_text: str
    reveal_text: str
    moves_bud: bool = True
    bedtime_sound: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    action: str
    works_for: set[str] = field(default_factory=set)
    clue_focus: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    apply: callable


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


def _r_kettle_sings(world: World) -> list[str]:
    kettle = world.entities.get("kettle")
    child = world.entities.get("child")
    if kettle is None or child is None:
        return []
    if kettle.meters["warm"] < THRESHOLD:
        return []
    sig = ("kettle_sings",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    kettle.meters["singing"] += 1
    child.memes["wonder"] += 1
    return []


def _r_bud_mystery(world: World) -> list[str]:
    bud = world.entities.get("bud")
    child = world.entities.get("child")
    if bud is None or child is None:
        return []
    if bud.meters["fallen"] < THRESHOLD:
        return []
    if world.facts.get("solved"):
        return []
    sig = ("bud_mystery",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="kettle_sings", apply=_r_kettle_sings),
    Rule(name="bud_mystery", apply=_r_bud_mystery),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


PLANTS = {
    "jasmine": Plant(
        id="jasmine",
        label="jasmine vine",
        phrase="a sleepy jasmine vine",
        place="on the windowsill above the tea tray",
        scent="sweet",
        color="white",
        has_bud=True,
        fragile=True,
        tags={"flower", "bud", "plant"},
    ),
    "rose": Plant(
        id="rose",
        label="mini rose",
        phrase="a tiny rose in a blue pot",
        place="beside the lamp near the tray",
        scent="soft",
        color="pink",
        has_bud=True,
        fragile=True,
        tags={"flower", "bud", "plant"},
    ),
    "pea": Plant(
        id="pea",
        label="sweet-pea vine",
        phrase="a little sweet-pea vine",
        place="on a hook by the half-open window",
        scent="light",
        color="purple",
        has_bud=True,
        fragile=True,
        tags={"flower", "bud", "plant"},
    ),
    "cactus": Plant(
        id="cactus",
        label="cactus",
        phrase="a prickly little cactus",
        place="on the shelf over the cups",
        scent="none",
        color="green",
        has_bud=False,
        fragile=False,
        tags={"plant"},
    ),
}

KETTLES = {
    "blue": Kettle(
        id="blue",
        label="blue kettle",
        phrase="a round blue kettle",
        song="began to hum before it whistled",
        steam="a silver ribbon of steam",
        tags={"kettle", "steam"},
    ),
    "copper": Kettle(
        id="copper",
        label="copper kettle",
        phrase="a polished copper kettle",
        song="made a tiny high singing sound",
        steam="a soft curl of steam",
        tags={"kettle", "steam"},
    ),
    "striped": Kettle(
        id="striped",
        label="striped kettle",
        phrase="a striped kettle with a sleepy spout",
        song="whispered a thin tea-song",
        steam="a pale puff of steam",
        tags={"kettle", "steam"},
    ),
}

AGENTS = {
    "kitten": Agent(
        id="kitten",
        label="kitten",
        phrase="the gray kitten",
        clue_tag="pawprints",
        clue_text="tiny pawprints dotted the floury patch by the tray",
        reveal_text="the gray kitten rose on tiptoe, patted the vine with one soft paw, and sent a bud tumbling down beside the kettle",
        moves_bud=True,
        bedtime_sound="a tiny purr under the chair",
        tags={"cat", "pawprints"},
    ),
    "breeze": Agent(
        id="breeze",
        label="breeze",
        phrase="the window breeze",
        clue_tag="curtain",
        clue_text="the curtain puffed in and out like a sleepy breath",
        reveal_text="the breeze slipped through the cracked window, rocked the plant, and shook one small bud loose onto the tray",
        moves_bud=True,
        bedtime_sound="a hush-hush sound at the curtain",
        tags={"wind", "curtain"},
    ),
    "moth": Agent(
        id="moth",
        label="moth",
        phrase="a pale moth",
        clue_tag="flutter",
        clue_text="something fluttered once near the lamp shade",
        reveal_text="a pale moth bumped the stem and made the plant tremble until a loose bud dropped down",
        moves_bud=True,
        bedtime_sound="a papery flutter near the light",
        tags={"moth", "flutter"},
    ),
    "shadow": Agent(
        id="shadow",
        label="shadow",
        phrase="a wandering shadow",
        clue_tag="none",
        clue_text="no real clue waited there",
        reveal_text="",
        moves_bud=False,
        bedtime_sound="",
        tags={"shadow"},
    ),
}

METHODS = {
    "pawprints": Method(
        id="pawprints",
        label="follow the pawprints",
        action="knelt by the tray and followed the tiny pawprints with one careful finger",
        works_for={"kitten"},
        clue_focus="marks on the floor",
        tags={"investigate", "pawprints"},
    ),
    "curtain": Method(
        id="curtain",
        label="watch the curtain",
        action="sat very still and watched the curtain instead of the tray",
        works_for={"breeze"},
        clue_focus="the moving curtain",
        tags={"investigate", "curtain"},
    ),
    "listen": Method(
        id="listen",
        label="wait and listen",
        action="held very still and listened for the smallest bedtime sound",
        works_for={"kitten", "breeze", "moth"},
        clue_focus="a small sound in the room",
        tags={"investigate", "listen"},
    ),
    "lamp": Method(
        id="lamp",
        label="watch the lamp",
        action="turned the lamp low and watched the soft circle of light on the wall",
        works_for={"moth"},
        clue_focus="the lamp light",
        tags={"investigate", "lamp"},
    ),
}


def valid_combo(plant: Plant, agent: Agent, method: Method) -> bool:
    return plant.has_bud and plant.fragile and agent.moves_bud and agent.id in method.works_for


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for plant_id, plant in PLANTS.items():
        for agent_id, agent in AGENTS.items():
            for method_id, method in METHODS.items():
                if valid_combo(plant, agent, method):
                    out.append((plant_id, agent_id, method_id))
    return out


@dataclass
class StoryParams:
    plant: str
    kettle: str
    agent: str
    method: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        plant="jasmine",
        kettle="blue",
        agent="kitten",
        method="pawprints",
        child_name="Mira",
        child_gender="girl",
        parent="mother",
        trait="dramatic",
        seed=1,
    ),
    StoryParams(
        plant="rose",
        kettle="copper",
        agent="breeze",
        method="curtain",
        child_name="Ben",
        child_gender="boy",
        parent="father",
        trait="careful",
        seed=2,
    ),
    StoryParams(
        plant="pea",
        kettle="striped",
        agent="moth",
        method="lamp",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        trait="curious",
        seed=3,
    ),
    StoryParams(
        plant="jasmine",
        kettle="copper",
        agent="breeze",
        method="listen",
        child_name="Leo",
        child_gender="boy",
        parent="father",
        trait="thoughtful",
        seed=4,
    ),
]

GIRL_NAMES = ["Mira", "Lina", "Tessa", "Nora", "Ava", "Ella", "Mina", "Ruby"]
BOY_NAMES = ["Ben", "Theo", "Leo", "Sam", "Noah", "Eli", "Finn", "Max"]
TRAITS = ["dramatic", "careful", "curious", "sleepy", "thoughtful", "gentle"]

KNOWLEDGE = {
    "kettle": [
        (
            "What does a kettle do?",
            "A kettle heats water until it is hot enough for tea or cocoa. Some kettles hum or whistle when the water gets very hot.",
        )
    ],
    "steam": [
        (
            "What is steam?",
            "Steam is warm water vapor that rises when water gets hot. It looks like a misty cloud.",
        )
    ],
    "bud": [
        (
            "What is a bud on a plant?",
            "A bud is a flower that has not opened yet. It is a little beginning that can grow into a blossom.",
        )
    ],
    "pawprints": [
        (
            "What are pawprints?",
            "Pawprints are the little marks an animal's feet leave behind. They can be clues that show where the animal went.",
        )
    ],
    "curtain": [
        (
            "Why does a curtain move when a window is open?",
            "Air can blow through the room and push the curtain. Even a small breeze can make light cloth sway.",
        )
    ],
    "moth": [
        (
            "What is a moth?",
            "A moth is a small flying insect. Many moths come near lights at night.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand yet. You solve it by noticing clues and thinking carefully.",
        )
    ],
}

KNOWLEDGE_ORDER = ["mystery", "kettle", "steam", "bud", "pawprints", "curtain", "moth"]


def explain_rejection(plant: Plant, agent: Agent, method: Method) -> str:
    if not plant.has_bud:
        return (
            f"(No story: {plant.phrase} does not have a soft flower bud to drop, "
            f"so there is no bedtime bud mystery to solve.)"
        )
    if not agent.moves_bud:
        return (
            f"(No story: {agent.phrase} is not a physical cause in this world. "
            f"The mystery needs a real cause that can move a bud.)"
        )
    return (
        f"(No story: the method '{method.id}' does not fit {agent.phrase}. "
        f"The child needs a clue-following method that could honestly reveal the cause.)"
    )


def tell(
    plant_cfg: Plant,
    kettle_cfg: Kettle,
    agent_cfg: Agent,
    method_cfg: Method,
    child_name: str,
    child_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=child_gender,
            label=child_name,
            phrase=child_name,
            role="child",
            attrs={"name": child_name, "trait": trait},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            phrase="the parent",
            role="parent",
        )
    )
    kettle = world.add(
        Entity(
            id="kettle",
            type="kettle",
            label=kettle_cfg.label,
            phrase=kettle_cfg.phrase,
            tags=set(kettle_cfg.tags),
        )
    )
    plant = world.add(
        Entity(
            id="plant",
            type="plant",
            label=plant_cfg.label,
            phrase=plant_cfg.phrase,
            tags=set(plant_cfg.tags),
            attrs={"place": plant_cfg.place, "scent": plant_cfg.scent, "color": plant_cfg.color},
        )
    )
    bud = world.add(
        Entity(
            id="bud",
            type="bud",
            label=f"{plant_cfg.color} bud",
            phrase=f"a small {plant_cfg.color} bud",
            tags={"bud"},
        )
    )
    room = world.add(
        Entity(
            id="room",
            type="room",
            label="kitchen",
            phrase="the warm kitchen",
        )
    )

    child.memes["sleepiness"] += 1
    room.memes["cozy"] += 1

    world.say(
        f"At bedtime, {child_name} padded into the kitchen while {parent.label_word} warmed water in {kettle_cfg.phrase}. "
        f"Near the tray sat {plant_cfg.phrase}, {plant_cfg.place}, and the whole room smelled {plant_cfg.scent} and clean."
    )
    if trait == "dramatic":
        world.say(
            f"{child_name} loved a little bedtime dramatics and always felt that a humming kettle might be the start of a secret."
        )
    else:
        world.say(
            f"{child_name} was a {trait} child and liked to notice quiet things before sleep."
        )

    world.para()
    kettle.meters["warm"] += 1
    bud.meters["fallen"] += 1
    propagate(world)
    world.say(
        f"Tonight, though, something was different. {kettle_cfg.phrase.capitalize()} {kettle_cfg.song}, "
        f"and there on the tray lay {bud.phrase}, as if it had tiptoed there by itself."
    )
    world.say(
        f'"A mystery," whispered {child_name}. "{child.pronoun("subject").capitalize()} was not here a minute ago."'
    )
    world.say(
        f"{parent.label_word.capitalize()} looked at the bud and smiled. "
        f'"Then let us solve it softly," {parent.pronoun("subject")} said. "Bedtime mysteries do not need big stomping feet."'
    )

    world.para()
    child.memes["bravery"] += 1
    world.say(
        f"{child_name} {method_cfg.action}. "
        f"{agent_cfg.clue_text.capitalize()}, and {kettle_cfg.steam} curled above the spout."
    )
    if agent_cfg.bedtime_sound:
        world.say(
            f"After a moment, {child_name} heard {agent_cfg.bedtime_sound}."
        )

    world.para()
    world.say(
        f"Then the answer came. {agent_cfg.reveal_text.capitalize()}."
    )
    world.facts["solved"] = True
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    world.say(
        f'{child_name} gave a tiny laugh. "So that is all," {child.pronoun("subject")} said. '
        f'"Not a midnight visitor at all."'
    )
    if agent_cfg.id == "kitten":
        world.say(
            f"{parent.label_word.capitalize()} lifted the bud, set it in a little saucer, and scratched the kitten behind one ear."
        )
    elif agent_cfg.id == "breeze":
        world.say(
            f"{parent.label_word.capitalize()} closed the window a little more and tucked the loose curtain back into place."
        )
    else:
        world.say(
            f"{parent.label_word.capitalize()} dimmed the lamp a little so the room grew calmer again."
        )

    world.para()
    world.say(
        f"Together they carried the warm cup to the table and left the bud safe in its saucer. "
        f"Then {parent.label_word} tucked {child_name} into bed with the mystery solved, "
        f"the kettle quiet at last, and one gentle clue-story to dream about."
    )

    world.facts.update(
        child=child,
        parent=parent,
        kettle_cfg=kettle_cfg,
        plant_cfg=plant_cfg,
        agent_cfg=agent_cfg,
        method_cfg=method_cfg,
        bud=bud,
        room=room,
        child_name=child_name,
        solution_text=agent_cfg.reveal_text,
        clue_text=agent_cfg.clue_text,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    plant = f["plant_cfg"]
    agent = f["agent_cfg"]
    method = f["method_cfg"]
    kettle = f["kettle_cfg"]
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the words "dramatics", "kettle", and "bud", and centers on a tiny mystery to solve.',
        f"Tell a gentle mystery where {f['child_name']} finds a flower bud beside a {kettle.label} at bedtime and solves the puzzle by using the method {method.label}.",
        f"Write a calm bedtime story about a {child.type} who notices clues near {plant.phrase} and learns that {agent.label} caused the mystery, not anything spooky.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    plant = f["plant_cfg"]
    agent = f["agent_cfg"]
    method = f["method_cfg"]
    kettle = f["kettle_cfg"]
    name = f["child_name"]
    pw = parent.label_word
    qa = [
        (
            "Who is the story about?",
            f"It is about {name}, {('a little girl' if child.type == 'girl' else 'a little boy')}, and {name}'s {pw}. Together they pause at bedtime to solve a tiny kitchen mystery.",
        ),
        (
            "What was the mystery?",
            f"The mystery was why a small flower bud had appeared beside the {kettle.label}. The bud looked as if it had moved there all by itself.",
        ),
        (
            f"Why did {name} think something secret might be happening?",
            f"{name} heard the kettle singing and saw a bud lying on the tray where it had not been before. Those two small surprises together made the room feel mysterious for a moment.",
        ),
        (
            f"How did {name} investigate the mystery?",
            f"{name} {method.action} This helped {child.pronoun('object')} pay attention to {method.clue_focus} instead of guessing wildly.",
        ),
        (
            "What was really happening?",
            f"{agent.reveal_text.capitalize()}. The mystery was solved by noticing the real clue instead of believing it was magic.",
        ),
        (
            f"How did the story end?",
            f"It ended quietly and safely, with the bud resting in a saucer and the kettle growing quiet. Then {pw} tucked {name} into bed with the mystery solved.",
        ),
    ]
    if child.attrs.get("trait") == "dramatic":
        qa.append(
            (
                f"How were dramatics part of the story?",
                f"{name} liked a little bedtime dramatics and first imagined the humming kettle might mean a secret visitor. After finding the clue, {child.pronoun('subject')} felt calmer because the mystery had an ordinary answer.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "kettle", "bud"} | set(f["kettle_cfg"].tags) | set(f["agent_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(name for (name, *_) in world.fired)}")
    lines.append(f"  solved: {world.facts.get('solved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
has_story_plant(P) :- plant(P), has_bud(P), fragile(P).
valid(P, A, M) :- has_story_plant(P), agent(A), moves_bud(A), method(M), method_works_for(M, A).

chosen_valid :- chosen_plant(P), chosen_agent(A), chosen_method(M), valid(P, A, M).
outcome(solved) :- chosen_valid.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for plant_id, plant in PLANTS.items():
        lines.append(asp.fact("plant", plant_id))
        if plant.has_bud:
            lines.append(asp.fact("has_bud", plant_id))
        if plant.fragile:
            lines.append(asp.fact("fragile", plant_id))
    for kettle_id in KETTLES:
        lines.append(asp.fact("kettle", kettle_id))
    for agent_id, agent in AGENTS.items():
        lines.append(asp.fact("agent", agent_id))
        if agent.moves_bud:
            lines.append(asp.fact("moves_bud", agent_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        for agent_id in sorted(method.works_for):
            lines.append(asp.fact("method_works_for", method_id, agent_id))
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
            asp.fact("chosen_plant", params.plant),
            asp.fact("chosen_agent", params.agent),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "solved" if valid_combo(PLANTS[params.plant], AGENTS[params.agent], METHODS[params.method]) else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime mystery storyworld about a kettle, a bud, and a small clue to follow."
    )
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--kettle", choices=KETTLES)
    ap.add_argument("--agent", choices=AGENTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plant and args.agent and args.method:
        if not valid_combo(PLANTS[args.plant], AGENTS[args.agent], METHODS[args.method]):
            raise StoryError(explain_rejection(PLANTS[args.plant], AGENTS[args.agent], METHODS[args.method]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.plant is None or combo[0] == args.plant)
        and (args.agent is None or combo[1] == args.agent)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        if args.plant and args.agent and args.method:
            raise StoryError(explain_rejection(PLANTS[args.plant], AGENTS[args.agent], METHODS[args.method]))
        raise StoryError("(No valid combination matches the given options.)")

    plant_id, agent_id, method_id = rng.choice(sorted(combos))
    kettle_id = args.kettle or rng.choice(sorted(KETTLES.keys()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        plant=plant_id,
        kettle=kettle_id,
        agent=agent_id,
        method=method_id,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.plant not in PLANTS:
        raise StoryError(f"(Unknown plant: {params.plant})")
    if params.kettle not in KETTLES:
        raise StoryError(f"(Unknown kettle: {params.kettle})")
    if params.agent not in AGENTS:
        raise StoryError(f"(Unknown agent: {params.agent})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    plant = PLANTS[params.plant]
    kettle = KETTLES[params.kettle]
    agent = AGENTS[params.agent]
    method = METHODS[params.method]
    if not valid_combo(plant, agent, method):
        raise StoryError(explain_rejection(plant, agent, method))

    world = tell(
        plant_cfg=plant,
        kettle_cfg=kettle,
        agent_cfg=agent,
        method_cfg=method,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        trait=params.trait,
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

    for params in CURATED:
        ao = asp_outcome(params)
        po = outcome_of(params)
        if ao != po:
            rc = 1
            print(f"MISMATCH in outcome for {params}: asp={ao} python={po}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (plant, agent, method) combos:\n")
        for plant, agent, method in combos:
            print(f"  {plant:8} {agent:8} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.child_name}: {p.plant} / {p.agent} / {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
