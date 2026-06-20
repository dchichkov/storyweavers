#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/staple_ask_sound_effects_heartwarming.py
===================================================================

A standalone storyworld about a child making a small paper surprise. The child
wants to finish it with a staple, but the safe, loving turn is to ask a grown-up
for help. The world models simple materials, hand coordination, and the emotional
shift from worry to shared pride.

Run it
------
    python storyworlds/worlds/gpt-5.4/staple_ask_sound_effects_heartwarming.py
    python storyworlds/worlds/gpt-5.4/staple_ask_sound_effects_heartwarming.py --project crown --material glitter_card
    python storyworlds/worlds/gpt-5.4/staple_ask_sound_effects_heartwarming.py --project chain --material tissue
    python storyworlds/worlds/gpt-5.4/staple_ask_sound_effects_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/staple_ask_sound_effects_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/staple_ask_sound_effects_heartwarming.py --trace
    python storyworlds/worlds/gpt-5.4/staple_ask_sound_effects_heartwarming.py --json
    python storyworlds/worlds/gpt-5.4/staple_ask_sound_effects_heartwarming.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "sister", "woman"}
        male = {"boy", "father", "grandfather", "brother", "man"}
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
            "sister": "sister",
            "brother": "brother",
        }.get(self.type, self.type)


@dataclass
class Project:
    id: str
    label: str
    phrase: str
    pieces: str
    purpose: str
    place: str
    display: str
    allowed_materials: set[str] = field(default_factory=set)
    precision: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    color: str
    stiffness: int
    sturdy: bool
    staplable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    type: str
    warm_line: str
    closing_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AskTiming:
    id: str
    label: str
    hesitant: bool
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


def _r_crooked_to_worry(world: World) -> list[str]:
    child = world.get("child")
    project = world.get("project")
    if project.meters["crooked"] < THRESHOLD:
        return []
    sig = ("crooked_to_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    return []


def _r_help_to_together(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    project = world.get("project")
    if child.memes["asked"] < THRESHOLD or helper.memes["helping"] < THRESHOLD:
        return []
    sig = ("help_to_together",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["together"] += 1
    helper.memes["together"] += 1
    project.meters["steady"] += 1
    return []


def _r_finished_to_pride(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    project = world.get("project")
    if project.meters["finished"] < THRESHOLD:
        return []
    sig = ("finished_to_pride",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["pride"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule("crooked_to_worry", "emotional", _r_crooked_to_worry),
    Rule("help_to_together", "social", _r_help_to_together),
    Rule("finished_to_pride", "emotional", _r_finished_to_pride),
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


PROJECTS = {
    "chain": Project(
        "chain",
        "paper chain",
        "a paper chain for the kitchen window",
        "paper loops",
        "to make the kitchen look cheerful before dinner",
        "the kitchen table",
        "the finished chain swayed in the window and caught the late gold light",
        allowed_materials={"paper", "construction_paper"},
        precision=1,
        tags={"paper_chain", "window"},
    ),
    "crown": Project(
        "crown",
        "paper crown",
        "a shiny paper crown for a stuffed bear",
        "paper points",
        "to make a favorite stuffed bear look ready for a tiny parade",
        "the living-room rug",
        "the little bear wore the crown crooked and proud on the cushion",
        allowed_materials={"construction_paper", "glitter_card"},
        precision=2,
        tags={"crown", "toy"},
    ),
    "booklet": Project(
        "booklet",
        "little booklet",
        "a little booklet of family drawings",
        "folded pages",
        "to tuck small pictures together as a surprise gift",
        "the coffee table",
        "the booklet rested by the lamp with its pages neat and ready to share",
        allowed_materials={"paper", "construction_paper"},
        precision=2,
        tags={"booklet", "gift"},
    ),
}

MATERIALS = {
    "paper": Material(
        "paper",
        "paper",
        "soft colored paper",
        "soft blue",
        stiffness=0,
        sturdy=True,
        staplable=True,
        tags={"paper"},
    ),
    "construction_paper": Material(
        "construction_paper",
        "construction paper",
        "thick construction paper",
        "bright red",
        stiffness=1,
        sturdy=True,
        staplable=True,
        tags={"paper"},
    ),
    "glitter_card": Material(
        "glitter_card",
        "glitter card",
        "sparkly glitter card",
        "silver",
        stiffness=2,
        sturdy=True,
        staplable=True,
        tags={"glitter", "paper"},
    ),
    "tissue": Material(
        "tissue",
        "tissue paper",
        "whisper-thin tissue paper",
        "pale pink",
        stiffness=0,
        sturdy=False,
        staplable=False,
        tags={"paper"},
    ),
}

HELPERS = {
    "mother": HelperKind(
        "mother",
        "mother",
        'said, "Good asking. We can do the pressing together."',
        'smiled and said, "Look what we made together."',
        tags={"family"},
    ),
    "father": HelperKind(
        "father",
        "father",
        'said, "That was smart. Let me hold it steady with you."',
        'grinned and said, "Now it is ready."',
        tags={"family"},
    ),
    "grandmother": HelperKind(
        "grandmother",
        "grandmother",
        'said, "Oh, sweetheart, I am glad you came to ask."',
        'beamed and said, "Your careful hands helped make it lovely."',
        tags={"family"},
    ),
    "grandfather": HelperKind(
        "grandfather",
        "grandfather",
        'said, "That is what I like to hear. We ask first and then we build."',
        'chuckled and said, "That little staple did its job."',
        tags={"family"},
    ),
}

ASK_TIMINGS = {
    "early": AskTiming("early", "before pressing", hesitant=False, tags={"ask"}),
    "after_wobble": AskTiming("after_wobble", "after a wobbly try", hesitant=True, tags={"ask"}),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Lucy", "Zoe", "Ella", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Noah", "Finn", "Theo", "Max", "Eli"]
TRAITS = ["careful", "hopeful", "gentle", "busy", "thoughtful", "eager"]


def valid_combo(project_id: str, material_id: str) -> bool:
    project = PROJECTS[project_id]
    material = MATERIALS[material_id]
    return material.staplable and material.sturdy and material_id in project.allowed_materials


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for pid in PROJECTS:
        for mid in MATERIALS:
            if valid_combo(pid, mid):
                out.append((pid, mid))
    return out


def risk_score(project: Project, material: Material) -> int:
    return project.precision + material.stiffness


def outcome_of(params: "StoryParams") -> str:
    project = PROJECTS[params.project]
    material = MATERIALS[params.material]
    if params.ask_timing == "early":
        return "smooth"
    return "redo" if risk_score(project, material) >= 3 else "smooth"


def explain_rejection(project: Project, material: Material) -> str:
    if not material.staplable:
        return (
            f"(No story: {material.label} is too delicate for a staple. "
            f"It would tear instead of holding, so pick a sturdier paper.)"
        )
    if material.id not in project.allowed_materials:
        return (
            f"(No story: {project.label} is not a good fit for {material.label} in this world. "
            f"The project needs a material that can fold and hold its shape.)"
        )
    if not material.sturdy:
        return (
            f"(No story: {material.label} is too flimsy to finish this project with a staple.)"
        )
    return "(No story: that project and material do not make a reasonable stapled craft.)"


def predict_try(project: Project, material: Material, ask_timing: AskTiming) -> dict:
    wobble = ask_timing.id == "after_wobble"
    bent = wobble and risk_score(project, material) >= 3
    return {"wobble": wobble, "bent": bent}


def introduce(world: World, child: Entity, helper: Entity, project: Project, material: Material) -> None:
    child.memes["joy"] += 1
    world.say(
        f"One cozy afternoon, {child.id} sat at {project.place} with {material.phrase}, "
        f"a small silver stapler, and a big idea."
    )
    world.say(
        f"{child.pronoun().capitalize()} wanted to make {project.phrase} {project.purpose}."
    )
    world.say(
        f"Little sounds filled the room: snip-snip went the scissors, swish went the paper, "
        f"and tap-tap went {child.id}'s fingers as {child.pronoun()} lined up the {project.pieces}."
    )
    world.facts["setting_sound"] = "snip-snip, swish, tap-tap"
    world.facts["goal_text"] = project.purpose
    world.facts["helper_name"] = helper.label_word


def last_step(world: World, child: Entity, project: Project) -> None:
    world.say(
        f"Soon only one last step was left. The {project.label} needed one neat staple to stay together."
    )
    child.memes["focus"] += 1


def hesitate(world: World, child: Entity, helper: Entity, project: Project, material: Material, ask_timing: AskTiming) -> None:
    prediction = predict_try(project, material, ask_timing)
    world.facts["predicted_wobble"] = prediction["wobble"]
    world.facts["predicted_bent"] = prediction["bent"]
    world.say(
        f"{child.id} picked up the stapler and listened to its little metal mouth click when it opened."
    )
    if ask_timing.id == "early":
        child.memes["care"] += 1
        world.say(
            f"{child.pronoun().capitalize()} paused. The papers felt slippery in one hand and the stapler felt heavy in the other."
        )
        world.say(
            f'"Can I ask {helper.label_word} for help with the staple?" {child.pronoun()} whispered to {child.pronoun("object")}.'
        )
    else:
        child.memes["impatience"] += 1
        world.say(
            f"{child.pronoun().capitalize()} tried to keep everything straight alone."
        )


def wobbly_try(world: World, child: Entity, project_ent: Entity, project: Project, material: Material, ask_timing: AskTiming) -> None:
    if ask_timing.id != "after_wobble":
        return
    project_ent.meters["attempted"] += 1
    pred = predict_try(project, material, ask_timing)
    if pred["bent"]:
        project_ent.meters["crooked"] += 1
        project_ent.meters["redo_needed"] += 1
        child.memes["surprise"] += 1
        world.say(
            "Ka-thunk! The stapler came down, but the papers scooted sideways."
        )
        world.say(
            "Instead of lying flat, the staple bent like a tiny silver elbow."
        )
        world.say(
            f"{child.id} blinked at it. Nothing hurt, but the last corner would not sit nicely anymore."
        )
    else:
        project_ent.meters["wobbly"] += 1
        world.say(
            "Ka-chik! The stapler nipped the edge, but the pieces landed a little crooked."
        )
        world.say(
            f"{child.id} looked at the slant and knew the last part still needed steadier hands."
        )
    propagate(world, narrate=False)


def ask_for_help(world: World, child: Entity, helper: Entity) -> None:
    child.memes["asked"] += 1
    helper.memes["helping"] += 1
    child.memes["relief"] += 1
    world.say(
        f'So {child.id} took a breath and went to ask. "{helper.label_word.capitalize()}, will you help me with the stapler?"'
    )
    world.say(
        f"{helper.label_word.capitalize()} came close at once and {HELPERS[helper.type].warm_line}"
    )
    propagate(world, narrate=False)


def steady_and_fix(world: World, child: Entity, helper: Entity, project_ent: Entity, project: Project, material: Material) -> None:
    if project_ent.meters["redo_needed"] >= THRESHOLD:
        world.say(
            f"Together they eased out the bent staple and smoothed the {material.label} flat again."
        )
        project_ent.meters["redo_needed"] = 0.0
        project_ent.meters["crooked"] = 0.0
        child.memes["worry"] = 0.0
    elif project_ent.meters["wobbly"] >= THRESHOLD:
        world.say(
            f"{helper.label_word.capitalize()} held the {project.pieces} steady while {child.id} straightened the edge."
        )
    else:
        world.say(
            f"{helper.label_word.capitalize()} held the {project.pieces} still while {child.id} slid them into place."
        )
    project_ent.meters["steady"] += 1
    world.say(
        f'Then both of them pressed together. "Ka-chunk!" went the stapler, neat and sure.'
    )
    project_ent.meters["joined"] += 1
    project_ent.meters["finished"] += 1
    world.facts["final_sound"] = "Ka-chunk!"
    propagate(world, narrate=False)


def celebrate(world: World, child: Entity, helper: Entity, project: Project) -> None:
    child.memes["love"] += 1
    helper.memes["love"] += 1
    world.say(
        f"{child.id} smiled so wide that {child.pronoun('possessive')} cheeks lifted."
    )
    world.say(
        f"{helper.label_word.capitalize()} {HELPERS[helper.type].closing_line}"
    )
    world.say(
        f"They stepped back to look, and {project.display}."
    )


def tell(project: Project, material: Material, helper_kind: HelperKind, ask_timing: AskTiming,
         child_name: str = "Lily", child_type: str = "girl", trait: str = "careful") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", traits=[trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_kind.type, role="helper", label="the helper"))
    project_ent = world.add(Entity(id="project", kind="thing", type="craft", label=project.label))
    material_ent = world.add(Entity(id="material", kind="thing", type="material", label=material.label))
    tool = world.add(Entity(id="tool", kind="thing", type="stapler", label="stapler"))

    introduce(world, child, helper, project, material)
    last_step(world, child, project)

    world.para()
    hesitate(world, child, helper, project, material, ask_timing)
    wobbly_try(world, child, project_ent, project, material, ask_timing)

    world.para()
    ask_for_help(world, child, helper)
    steady_and_fix(world, child, helper, project_ent, project, material)

    world.para()
    celebrate(world, child, helper, project)

    world.facts.update(
        child=child,
        helper=helper,
        project_cfg=project,
        material_cfg=material,
        tool=tool,
        ask_timing=ask_timing,
        outcome=outcome_of(
            StoryParams(
                project=project.id,
                material=material.id,
                helper=helper_kind.id,
                ask_timing=ask_timing.id,
                child=child_name,
                gender=child_type,
                trait=trait,
            )
        ),
        wobbled=ask_timing.id == "after_wobble",
        bent=project_ent.meters["redo_needed"] >= THRESHOLD or predict_try(project, material, ask_timing)["bent"],
        finished=project_ent.meters["finished"] >= THRESHOLD,
        together=child.memes["together"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "staple": [(
        "What is a staple?",
        "A staple is a tiny bent piece of metal that can hold papers together. A grown-up or a careful helper should be nearby when a child uses a stapler."
    )],
    "ask": [(
        "Why is it good to ask for help?",
        "Asking for help is smart because another person can make a hard job safer and steadier. It also lets people solve a problem together."
    )],
    "paper_chain": [(
        "What is a paper chain?",
        "A paper chain is made from paper loops joined together. People hang it up as a simple decoration."
    )],
    "crown": [(
        "What is a paper crown?",
        "A paper crown is a pretend crown made from paper or card. Children often use one in dress-up play."
    )],
    "booklet": [(
        "What is a booklet?",
        "A booklet is a few pages fastened together so you can turn them like a tiny book. It is a nice way to keep drawings in one place."
    )],
    "glitter": [(
        "What is glitter card?",
        "Glitter card is stiff paper with a sparkly surface. It looks pretty, but it can be a little harder to bend neatly."
    )],
    "family": [(
        "How can a family help with a craft?",
        "A family member can hold, cut, or steady the pieces while a child works. Doing it together can make the craft safer and calmer."
    )],
}

KNOWLEDGE_ORDER = ["staple", "ask", "paper_chain", "crown", "booklet", "glitter", "family"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    project = f["project_cfg"]
    helper = f["helper"]
    material = f["material_cfg"]
    outcome = f["outcome"]
    if outcome == "redo":
        turn = "makes one wobbly try first, then asks for help and fixes it together"
    else:
        turn = "pauses to ask for help before the hard last step"
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the words "staple" and "ask", and uses sound effects.',
        f"Tell a gentle craft story where {child.id} is making a {project.label} from {material.label}, {turn}, and ends with a loving family moment.",
        f'Write a small homey story with sounds like "snip-snip" and "ka-chunk" where a child chooses to ask {helper.label_word} for help instead of struggling alone.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    project = f["project_cfg"]
    material = f["material_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who wanted to make a {project.label}, and {helper.label_word} who helped at the last step."
        ),
        (
            f"What was {child.id} trying to make?",
            f"{child.pronoun().capitalize()} was making {project.phrase}. The project mattered because {project.purpose}."
        ),
        (
            "What sounds were in the story?",
            f"The room had craft sounds like snip-snip, swish, and tap-tap, and later the stapler went {f.get('final_sound', 'Ka-chunk!')}. Those sounds make the quiet work feel alive and close."
        ),
        (
            f"Why did {child.id} ask for help?",
            f"{child.id} asked for help because the last staple needed steadier hands than one small hand could give. Asking made the job calmer and helped the project come together neatly."
        ),
    ]
    if f["wobbled"]:
        if f["outcome"] == "redo":
            qa.append((
                f"What happened before {child.id} asked for help?",
                f"{child.id} made one wobbly try, and the staple bent instead of lying flat. Nothing hurt, but the paper would not sit neatly, so asking for help was the best next step."
            ))
        else:
            qa.append((
                f"What happened before {child.id} asked for help?",
                f"{child.id} tried once and the edge landed a little crooked. That small wobble showed {child.pronoun('object')} that the last step would be easier with help."
            ))
    else:
        qa.append((
            f"Did {child.id} use the stapler alone?",
            f"No. {child.id} paused before pressing and chose to ask {helper.label_word} for help first. That choice kept the moment gentle and careful."
        ))
    qa.append((
        "How did the story end?",
        f"It ended warmly, with the craft finished and both of them stepping back to admire it. The ending image shows that asking for help turned worry into shared pride."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"staple", "ask"}
    project = world.facts["project_cfg"]
    material = world.facts["material_cfg"]
    helper = world.facts["helper"]
    tags |= set(project.tags)
    tags |= set(material.tags)
    tags |= set(HELPERS[helper.type].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    project: str
    material: str
    helper: str
    ask_timing: str
    child: str
    gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("chain", "paper", "mother", "early", "Lily", "girl", "careful"),
    StoryParams("crown", "glitter_card", "grandfather", "after_wobble", "Ben", "boy", "eager"),
    StoryParams("booklet", "construction_paper", "grandmother", "early", "Maya", "girl", "thoughtful"),
    StoryParams("crown", "construction_paper", "father", "after_wobble", "Leo", "boy", "hopeful"),
    StoryParams("chain", "construction_paper", "mother", "after_wobble", "Nora", "girl", "gentle"),
]


ASP_RULES = r"""
valid(P, M) :- project(P), material(M), allowed(P, M), staplable(M), sturdy(M).

risk(P, M, R) :- precision(P, PP), stiffness(M, MM), R = PP + MM.

outcome(smooth) :- chosen_timing(early).
outcome(redo)   :- chosen_timing(after_wobble), chosen_project(P), chosen_material(M), risk(P, M, R), R >= 3.
outcome(smooth) :- chosen_timing(after_wobble), chosen_project(P), chosen_material(M), risk(P, M, R), R < 3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("precision", pid, p.precision))
        for mid in sorted(p.allowed_materials):
            lines.append(asp.fact("allowed", pid, mid))
    for mid, m in MATERIALS.items():
        lines.append(asp.fact("material", mid))
        lines.append(asp.fact("stiffness", mid, m.stiffness))
        if m.staplable:
            lines.append(asp.fact("staplable", mid))
        if m.sturdy:
            lines.append(asp.fact("sturdy", mid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for tid in ASK_TIMINGS:
        lines.append(asp.fact("timing", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_project", params.project),
        asp.fact("chosen_material", params.material),
        asp.fact("chosen_timing", params.ask_timing),
    ])
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
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    mismatches = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child finishes a paper surprise by asking for help with a staple."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--ask-timing", choices=ASK_TIMINGS, dest="ask_timing")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--child")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible project/material pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against the Python logic and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.material:
        if not valid_combo(args.project, args.material):
            raise StoryError(explain_rejection(PROJECTS[args.project], MATERIALS[args.material]))

    combos = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.material is None or combo[1] == args.material)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project, material = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    ask_timing = args.ask_timing or rng.choice(sorted(ASK_TIMINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(project, material, helper, ask_timing, child, gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PROJECTS[params.project],
        MATERIALS[params.material],
        HELPERS[params.helper],
        ASK_TIMINGS[params.ask_timing],
        params.child,
        params.gender,
        params.trait,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (project, material) combos:\n")
        for project, material in combos:
            print(f"  {project:8} {material}")
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
            header = f"### {p.child}: {p.project} with {p.material} ({p.ask_timing})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
