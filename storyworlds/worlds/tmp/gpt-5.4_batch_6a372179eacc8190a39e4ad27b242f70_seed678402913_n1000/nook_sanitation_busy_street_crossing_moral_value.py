#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nook_sanitation_busy_street_crossing_moral_value.py
==============================================================================

A standalone storyworld for a child-sized space adventure set at a busy street
crossing. A child spots litter jammed in a curb nook beside the crosswalk and
wants to fix it at once, but traffic makes that unsafe. A sanitation worker
helps with the right tool at the right moment, and the ending proves two linked
moral ideas: shared places stay safer when we keep them clean, and safety comes
before speed.

Run it
------
python storyworlds/worlds/gpt-5.4/nook_sanitation_busy_street_crossing_moral_value.py
python storyworlds/worlds/gpt-5.4/nook_sanitation_busy_street_crossing_moral_value.py --trash wrapper --tool grabber
python storyworlds/worlds/gpt-5.4/nook_sanitation_busy_street_crossing_moral_value.py --trash can --tool broom_pan
python storyworlds/worlds/gpt-5.4/nook_sanitation_busy_street_crossing_moral_value.py --all
python storyworlds/worlds/gpt-5.4/nook_sanitation_busy_street_crossing_moral_value.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/nook_sanitation_busy_street_crossing_moral_value.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sanitation_woman"}
        male = {"boy", "father", "man", "sanitation_man"}
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
            "sanitation_woman": "sanitation worker",
            "sanitation_man": "sanitation worker",
        }.get(self.type, self.label or self.type)


@dataclass
class Mission:
    id: str
    scene: str
    launch_line: str
    quest_name: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trash:
    id: str
    label: str
    phrase: str
    texture: str
    depth: int
    soggy: bool
    blocks: str
    drift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    reach: int
    good_for_wet: bool
    cleanup: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CrossingStyle:
    id: str
    place: str
    sound: str
    signal_phrase: str
    nook_phrase: str
    safe_spot: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, crossing: CrossingStyle) -> None:
        self.crossing = crossing
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
        clone = World(self.crossing)
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


def _r_blocked_drain(world: World) -> list[str]:
    out: list[str] = []
    trash = world.get("trash")
    crossing = world.get("crossing")
    if trash.meters["jammed"] >= THRESHOLD:
        sig = ("blocked", "drain")
        if sig not in world.fired:
            world.fired.add(sig)
            crossing.meters["blocked"] += 1
            crossing.meters["dirty"] += 1
            out.append("__blocked__")
    return out


def _r_risk_from_block(world: World) -> list[str]:
    out: list[str] = []
    crossing = world.get("crossing")
    child = world.get("child")
    if crossing.meters["blocked"] >= THRESHOLD:
        sig = ("risk", "crossing")
        if sig not in world.fired:
            world.fired.add(sig)
            crossing.meters["puddle_risk"] += 1
            child.memes["care"] += 1
            out.append("__risk__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="blocked_drain", tag="physical", apply=_r_blocked_drain),
    Rule(name="risk_from_block", tag="physical", apply=_r_risk_from_block),
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


def valid_tool(tool: Tool, trash: Trash) -> bool:
    if tool.reach < trash.depth:
        return False
    if trash.soggy and not tool.good_for_wet:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for trash_id, trash in TRASH.items():
            for tool_id, tool in TOOLS.items():
                if valid_tool(tool, trash):
                    combos.append((mission_id, trash_id, tool_id))
    return combos


def explain_rejection(tool: Tool, trash: Trash) -> str:
    if tool.reach < trash.depth:
        return (
            f"(No story: {tool.label} cannot reach deep enough into the curb nook "
            f"to lift the {trash.label}. Pick a longer tool like a grabber.)"
        )
    if trash.soggy and not tool.good_for_wet:
        return (
            f"(No story: {tool.label} is too weak for the soggy {trash.label}. "
            f"Pick a sanitation tool that can lift wet litter safely.)"
        )
    return "(No story: that cleanup plan is not reasonable for this crossing.)"


def predict_danger(world: World) -> dict:
    sim = world.copy()
    trash = sim.get("trash")
    crossing = sim.get("crossing")
    child = sim.get("child")
    trash.meters["jammed"] += 1
    propagate(sim, narrate=False)
    child.memes["impulse"] += 1
    crossing.meters["traffic"] += 1
    return {
        "blocked": crossing.meters["blocked"] >= THRESHOLD,
        "puddle_risk": crossing.meters["puddle_risk"] >= THRESHOLD,
        "traffic": crossing.meters["traffic"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, guardian: Entity, mission: Mission) -> None:
    world.say(
        f"After school, {child.id} and {child.pronoun('possessive')} {guardian.label_word} "
        f"reached {world.crossing.place}. {world.crossing.sound}"
    )
    world.say(
        f"To {child.id}, the corner did not look ordinary at all. It looked like "
        f"{mission.scene}, and today's quest was called {mission.quest_name}."
    )
    world.say(mission.launch_line)


def spot_problem(world: World, child: Entity, trash: Trash) -> None:
    nook = world.crossing.nook_phrase
    world.say(
        f"Then {child.id} spotted {trash.phrase} tucked into {nook}. "
        f"It had drifted there {trash.drift}."
    )
    trash_ent = world.get("trash")
    trash_ent.meters["jammed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The little nook looked small, but the {trash.label} was {trash.blocks}, "
        f"and the corner suddenly seemed important."
    )


def want_to_help(world: World, child: Entity, mission: Mission) -> None:
    child.memes["quest"] += 1
    child.memes["care"] += 1
    world.say(
        f'"Commander {child.id} can fix it," {child.pronoun()} said. '
        f"In {child.pronoun('possessive')} mind, this was the heart of the mission."
    )


def warn(world: World, guardian: Entity, child: Entity, crossing: CrossingStyle) -> None:
    pred = predict_danger(world)
    world.facts["predicted_blocked"] = pred["blocked"]
    world.facts["predicted_puddle_risk"] = pred["puddle_risk"]
    world.facts["predicted_traffic"] = pred["traffic"]
    child.memes["impulse"] += 1
    world.say(
        f'But {guardian.label_word} held {child.pronoun("possessive")} sleeve and pointed '
        f"to the traffic. \"A busy street crossing is not a place to dash,\" "
        f"{guardian.pronoun()} said. \"We wait for {crossing.signal_phrase}, and we ask for help.\""
    )


def press_button(world: World, child: Entity, guardian: Entity) -> None:
    child.memes["patience"] += 1
    world.say(
        f"So instead of lunging toward the curb, {child.id} stayed in {world.crossing.safe_spot} "
        f"and pressed the walk button with {guardian.pronoun('possessive')} help."
    )


def call_helper(world: World, worker: Entity, child: Entity) -> None:
    worker.memes["helpfulness"] += 1
    world.say(
        f"Just then a sanitation cart rattled up beside the corner. "
        f"{worker.id}, the sanitation worker, saw where {child.id} was looking."
    )
    world.say(
        f'"Good eyes, Space Scout," {worker.pronoun()} said. '
        f'"Keeping a crossing clean helps everyone."'
    )


def clean_nook(world: World, worker: Entity, tool: Tool, trash: Trash) -> None:
    trash_ent = world.get("trash")
    crossing_ent = world.get("crossing")
    trash_ent.meters["jammed"] = 0.0
    trash_ent.meters["removed"] += 1
    crossing_ent.meters["blocked"] = 0.0
    crossing_ent.meters["dirty"] = 0.0
    crossing_ent.meters["puddle_risk"] = 0.0
    crossing_ent.meters["clean"] += 1
    worker.memes["care"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When the signal changed and the worker could reach safely from the curb, "
        f"{worker.pronoun()} used {tool.phrase} and {tool.cleanup.replace('{trash}', trash.label)}."
    )
    world.say(
        "The tiny nook was clear again, and the water path to the drain looked open."
    )


def resolve(world: World, child: Entity, guardian: Entity, worker: Entity, mission: Mission) -> None:
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    child.memes["care"] += 1
    child.memes["impulse"] = 0.0
    child.memes["patience"] += 1
    guardian.memes["love"] += 1
    world.say(
        f'{guardian.label_word.capitalize()} smiled down at {child.id}. '
        f'"You were kind to notice the mess," {guardian.pronoun()} said. '
        f'"And you were wise to wait."'
    )
    world.say(
        f"{child.id} nodded. The quest was not just about being fast. "
        f"It was about helping the whole corner stay safe and clean."
    )
    world.say(
        f"Then {mission.ending_image} The crossing no longer felt like a problem. "
        f"It felt like a place people were taking care of together."
    )


def tell(
    mission: Mission,
    trash: Trash,
    tool: Tool,
    crossing: CrossingStyle,
    *,
    child_name: str = "Nova",
    child_type: str = "girl",
    guardian_type: str = "mother",
    worker_name: str = "Mara",
    worker_type: str = "sanitation_woman",
    trait: str = "observant",
) -> World:
    world = World(crossing=crossing)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            label=child_name,
            role="child",
            traits=["little", trait],
        )
    )
    guardian = world.add(
        Entity(
            id="Guardian",
            kind="character",
            type=guardian_type,
            label="the parent",
            role="guardian",
        )
    )
    worker = world.add(
        Entity(
            id=worker_name,
            kind="character",
            type=worker_type,
            label=worker_name,
            role="worker",
        )
    )
    world.add(
        Entity(
            id="crossing",
            type="crossing",
            label="crossing",
        )
    )
    world.add(
        Entity(
            id="trash",
            type="trash",
            label=trash.label,
        )
    )

    introduce(world, child, guardian, mission)
    world.para()
    spot_problem(world, child, trash)
    want_to_help(world, child, mission)
    warn(world, guardian, child, crossing)
    press_button(world, child, guardian)
    world.para()
    call_helper(world, worker, child)
    clean_nook(world, worker, tool, trash)
    world.para()
    resolve(world, child, guardian, worker, mission)

    world.facts.update(
        mission=mission,
        trash_cfg=trash,
        tool=tool,
        crossing_cfg=crossing,
        child=child,
        guardian=guardian,
        worker=worker,
        lesson="Care for shared places, and choose the safe way to help.",
        success=world.get("crossing").meters["clean"] >= THRESHOLD,
    )
    return world


MISSIONS = {
    "runway": Mission(
        id="runway",
        scene="a bright spaceport runway painted with white stripes and blinking signals",
        launch_line='"Mission Control," {child} whispered, "I am ready for cleanup orbit."',
        quest_name='"The Clean Corner Quest"',
        ending_image="the white crossing lines gleamed like landing strips under the evening sun",
        tags={"space", "quest"},
    ),
    "star_map": Mission(
        id="star_map",
        scene="a city star map where every lane was a silver path between planets",
        launch_line='"Captain," {child} whispered to the button pole, "show us the safe path."',
        quest_name='"The Sanitation Star Mission"',
        ending_image="the signal box blinked green like a tiny friendly satellite",
        tags={"space", "quest"},
    ),
    "moon_gate": Mission(
        id="moon_gate",
        scene="a moon gate where buses rumbled past like careful cargo ships",
        launch_line='"Crew report," {child} said, standing tall, "we protect the landing zone together."',
        quest_name='"The Nook Rescue Quest"',
        ending_image="the cleared curb shone like a neat little moon harbor",
        tags={"space", "quest"},
    ),
}

TRASH = {
    "wrapper": Trash(
        id="wrapper",
        label="wrapper",
        phrase="a crinkly silver wrapper",
        texture="crinkly",
        depth=1,
        soggy=False,
        blocks="catching grit and leaves against the drain edge",
        drift="after a swirl of wind from a passing bus",
        tags={"litter", "cleanliness"},
    ),
    "flyer": Trash(
        id="flyer",
        label="flyer",
        phrase="a folded paper flyer",
        texture="papery",
        depth=1,
        soggy=False,
        blocks="spreading over the mouth of the drain",
        drift="from the side of a mailbox",
        tags={"litter", "paper"},
    ),
    "pouch": Trash(
        id="pouch",
        label="juice pouch",
        phrase="a sticky juice pouch",
        texture="sticky",
        depth=2,
        soggy=True,
        blocks="wedged low in the drain nook where dirty water would gather",
        drift="until its corner caught in the curb",
        tags={"litter", "sticky"},
    ),
    "can": Trash(
        id="can",
        label="crushed can",
        phrase="a crushed can",
        texture="metal",
        depth=2,
        soggy=True,
        blocks="jammed deep enough to trap soggy leaves beside it",
        drift="until it clinked into the little concrete hollow",
        tags={"litter", "metal"},
    ),
}

TOOLS = {
    "grabber": Tool(
        id="grabber",
        label="grabber",
        phrase="a long sanitation grabber",
        reach=2,
        good_for_wet=True,
        cleanup="lifted the {trash} free and dropped it into the collection bag",
        qa_text="used a long grabber to lift the litter out of the nook",
        tags={"tool", "sanitation"},
    ),
    "claw": Tool(
        id="claw",
        label="litter claw",
        phrase="a springy litter claw",
        reach=2,
        good_for_wet=True,
        cleanup="pinched the {trash} and carried it neatly to the cart",
        qa_text="used a litter claw to pinch the litter and carry it away",
        tags={"tool", "sanitation"},
    ),
    "broom_pan": Tool(
        id="broom_pan",
        label="street broom and pan",
        phrase="a street broom and pan",
        reach=1,
        good_for_wet=False,
        cleanup="swept the {trash} out of the nook and into the pan",
        qa_text="swept the litter out with a street broom and pan",
        tags={"tool", "broom"},
    ),
}

CROSSINGS = {
    "downtown": CrossingStyle(
        id="downtown",
        place="a busy street crossing downtown",
        sound="Cars hummed, buses sighed, and the walk signal clicked above them.",
        signal_phrase="the walk sign and the grown-up's okay",
        nook_phrase="a little curb nook beside the crosswalk pole",
        safe_spot="the dry square behind the curb line",
        tags={"crosswalk", "traffic"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Ava", "Zoe", "Nora"]
BOY_NAMES = ["Leo", "Finn", "Max", "Theo", "Eli", "Sam"]
TRAITS = ["observant", "curious", "thoughtful", "careful", "bright"]
WORKER_NAMES = ["Mara", "Tess", "Ruben", "Jules", "Niko"]
WORKER_TYPES = ["sanitation_woman", "sanitation_man"]


@dataclass
class StoryParams:
    mission: str
    trash: str
    tool: str
    crossing: str
    child_name: str
    child_type: str
    guardian_type: str
    worker_name: str
    worker_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        mission="runway",
        trash="wrapper",
        tool="broom_pan",
        crossing="downtown",
        child_name="Nova",
        child_type="girl",
        guardian_type="mother",
        worker_name="Mara",
        worker_type="sanitation_woman",
        trait="observant",
    ),
    StoryParams(
        mission="star_map",
        trash="pouch",
        tool="grabber",
        crossing="downtown",
        child_name="Leo",
        child_type="boy",
        guardian_type="father",
        worker_name="Ruben",
        worker_type="sanitation_man",
        trait="thoughtful",
    ),
    StoryParams(
        mission="moon_gate",
        trash="can",
        tool="claw",
        crossing="downtown",
        child_name="Luna",
        child_type="girl",
        guardian_type="mother",
        worker_name="Niko",
        worker_type="sanitation_man",
        trait="curious",
    ),
]


KNOWLEDGE = {
    "crosswalk": [
        (
            "What is a crosswalk?",
            "A crosswalk is the marked part of the road where people are meant to walk across. It helps drivers and walkers know where crossing should happen.",
        )
    ],
    "traffic": [
        (
            "Why is it important to wait at a busy street crossing?",
            "Cars and buses move fast, so a busy crossing can change quickly. Waiting for the signal and a grown-up's okay keeps your body out of danger.",
        )
    ],
    "sanitation": [
        (
            "What does sanitation mean?",
            "Sanitation means keeping places clean and healthy, like picking up trash and helping water flow where it should. Clean places are safer and nicer for everyone.",
        )
    ],
    "drain": [
        (
            "Why should litter stay out of a drain?",
            "Litter can block the path water needs to travel. Then puddles and dirty water can collect where people walk.",
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber is a long tool that lets a worker reach and pick something up without leaning into a dangerous place. It helps people clean safely.",
        )
    ],
    "broom": [
        (
            "What does a street broom help with?",
            "A street broom helps sweep light, dry litter from the ground. It works best when the mess is close and not stuck deep.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a job or mission someone cares about and tries hard to finish. In stories, a quest often teaches the hero something important.",
        )
    ],
}

KNOWLEDGE_ORDER = ["crosswalk", "traffic", "sanitation", "drain", "grabber", "broom", "quest"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    trash = f["trash_cfg"]
    return [
        'Write a short story for a 3-to-5-year-old in a Space Adventure style set at a busy street crossing that includes the words "nook" and "sanitation".',
        f"Tell a gentle quest story where a child named {child.id} notices a {trash.label} stuck in a curb nook and wants to help, but learns to choose the safe way first.",
        "Write a moral-value story about caring for a shared city corner, waiting for the walk signal, and helping sanitation workers keep the place clean.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    worker = f["worker"]
    trash = f["trash_cfg"]
    tool = f["tool"]
    crossing = f["crossing_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {guardian.label_word}, and {worker.id} the sanitation worker. Together they help a busy crossing become cleaner and safer.",
        ),
        (
            f"What problem did {child.id} notice?",
            f"{child.id} noticed {trash.phrase} stuck in {crossing.nook_phrase}. It was blocking the place where water and bits of leaves should pass.",
        ),
        (
            f"Why didn't {child.id} run to fix it right away?",
            f"{child.id} wanted to help fast, but the crossing was busy with traffic. {guardian.label_word.capitalize()} reminded {child.pronoun('object')} that being helpful also means waiting for the safe moment.",
        ),
        (
            "How was the problem solved?",
            f"{worker.id} used {tool.phrase} and {tool.cleanup.replace('{trash}', trash.label)}. That cleared the nook so the corner looked clean again and the drain path was open.",
        ),
        (
            "What did the child learn?",
            f"{child.id} learned that kindness is not only noticing a mess. It also means choosing a safe way to help other people take care of a shared place.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"crosswalk", "traffic", "sanitation", "drain", "quest"}
    if f["tool"].id == "grabber" or f["tool"].id == "claw":
        tags.add("grabber")
    if f["tool"].id == "broom_pan":
        tags.add("broom")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:17}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
reachable(Tool, Trash) :- tool(Tool), trash(Trash), reach(Tool, R), depth(Trash, D), R >= D.
wet_ok(Tool, Trash)    :- tool(Tool), trash(Trash), wet(Trash), good_for_wet(Tool).
wet_ok(Tool, Trash)    :- tool(Tool), trash(Trash), not wet(Trash).
valid(Mission, Trash, Tool) :- mission(Mission), trash(Trash), tool(Tool),
                               reachable(Tool, Trash), wet_ok(Tool, Trash).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for trash_id, trash in TRASH.items():
        lines.append(asp.fact("trash", trash_id))
        lines.append(asp.fact("depth", trash_id, trash.depth))
        if trash.soggy:
            lines.append(asp.fact("wet", trash_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("reach", tool_id, tool.reach))
        if tool.good_for_wet:
            lines.append(asp.fact("good_for_wet", tool_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    if sample.world is None:
        raise StoryError("Smoke test failed: world model missing.")
    emit(sample, trace=False, qa=False, header="")


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
        smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    for params in CURATED:
        try:
            sample = generate(params)
        except Exception as err:
            rc = 1
            print(f"CURATED GENERATION FAILED for {params}: {err}")
            continue
        if not sample.story.strip():
            rc = 1
            print(f"CURATED GENERATION FAILED for {params}: empty story")
    if rc == 0:
        print(f"OK: curated generation passed ({len(CURATED)} scenarios).")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a small space-style sanitation quest at a busy street crossing."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--trash", choices=TRASH)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--crossing", choices=CROSSINGS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trash and args.tool:
        trash = TRASH[args.trash]
        tool = TOOLS[args.tool]
        if not valid_tool(tool, trash):
            raise StoryError(explain_rejection(tool, trash))

    combos = [
        combo
        for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.trash is None or combo[1] == args.trash)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, trash_id, tool_id = rng.choice(sorted(combos))
    crossing = args.crossing or "downtown"
    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    guardian_type = args.guardian or rng.choice(["mother", "father"])
    worker_type = rng.choice(WORKER_TYPES)
    worker_name = rng.choice([name for name in WORKER_NAMES if name != child_name])
    trait = rng.choice(TRAITS)

    return StoryParams(
        mission=mission_id,
        trash=trash_id,
        tool=tool_id,
        crossing=crossing,
        child_name=child_name,
        child_type=child_type,
        guardian_type=guardian_type,
        worker_name=worker_name,
        worker_type=worker_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Invalid mission: {params.mission})")
    if params.trash not in TRASH:
        raise StoryError(f"(Invalid trash: {params.trash})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Invalid tool: {params.tool})")
    if params.crossing not in CROSSINGS:
        raise StoryError(f"(Invalid crossing: {params.crossing})")

    mission = MISSIONS[params.mission]
    trash = TRASH[params.trash]
    tool = TOOLS[params.tool]
    crossing = CROSSINGS[params.crossing]
    if not valid_tool(tool, trash):
        raise StoryError(explain_rejection(tool, trash))

    mission_line = mission.launch_line.format(child=params.child_name)
    mission = Mission(
        id=mission.id,
        scene=mission.scene,
        launch_line=mission_line,
        quest_name=mission.quest_name,
        ending_image=mission.ending_image,
        tags=set(mission.tags),
    )

    world = tell(
        mission=mission,
        trash=trash,
        tool=tool,
        crossing=crossing,
        child_name=params.child_name,
        child_type=params.child_type,
        guardian_type=params.guardian_type,
        worker_name=params.worker_name,
        worker_type=params.worker_type,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, trash, tool) combos:\n")
        for mission, trash, tool in combos:
            print(f"  {mission:10} {trash:8} {tool}")
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
            header = f"### {p.child_name}: {p.mission} / {p.trash} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
