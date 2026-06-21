#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hornet_humility_hose_quest_flashback_problem_solving.py
===================================================================================

A standalone storyworld about a child on a spooky little quest who meets a real
problem: a hornet is guarding the path because something sweet spilled nearby.
The child first wants to act brave alone, then remembers an earlier mistake,
learns humility, asks for help, and solves the problem with a garden hose in a
safe, sensible way.

This world aims for a gentle Ghost Story mood: moonlight, shadows, old gates,
and hush -- but no real supernatural danger. The turn is driven by the world
state: a hornet is attracted to a sweet lure; a hose can wash the lure away and
make the path safe again; a proud child can become humble enough to ask for
help.

Run it
------
    python storyworlds/worlds/gpt-5.4/hornet_humility_hose_quest_flashback_problem_solving.py
    python storyworlds/worlds/gpt-5.4/hornet_humility_hose_quest_flashback_problem_solving.py --setting moon_garden --goal bell --lure jam --response wash_away
    python storyworlds/worlds/gpt-5.4/hornet_humility_hose_quest_flashback_problem_solving.py --response swat
    python storyworlds/worlds/gpt-5.4/hornet_humility_hose_quest_flashback_problem_solving.py --all --qa
    python storyworlds/worlds/gpt-5.4/hornet_humility_hose_quest_flashback_problem_solving.py --verify
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    ghost_image: str
    blocked_spot: str
    hose_place: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    hanging_place: str
    victory: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Lure:
    id: str
    label: str
    phrase: str
    where: str
    washed: str
    hornet_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    calms_hazard: bool
    text: str
    fail_text: str
    qa_text: str
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


def _r_hornet_blocks(world: World) -> list[str]:
    out: list[str] = []
    hornet = world.get("hornet")
    path = world.get("path")
    if hornet.meters["attracted"] >= THRESHOLD and path.meters["blocked"] < THRESHOLD:
        sig = ("hornet_blocks",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        path.meters["blocked"] += 1
        hornet.memes["agitated"] += 1
        child = world.get("child")
        child.memes["fear"] += 1
        out.append("__blocked__")
    return out


def _r_humility_unlocks_help(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["humility"] >= THRESHOLD and helper.memes["asked"] < THRESHOLD:
        sig = ("ask_help",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        helper.memes["asked"] += 1
        helper.memes["care"] += 1
        child.memes["relief"] += 1
        out.append("__asked__")
    return out


def _r_washed_path_safe(world: World) -> list[str]:
    out: list[str] = []
    lure = world.get("lure")
    hornet = world.get("hornet")
    path = world.get("path")
    if lure.meters["gone"] >= THRESHOLD and path.meters["blocked"] >= THRESHOLD:
        sig = ("path_safe",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hornet.meters["attracted"] = 0.0
        hornet.memes["agitated"] = 0.0
        path.meters["blocked"] = 0.0
        child = world.get("child")
        child.memes["confidence"] += 1
        out.append("__safe__")
    return out


CAUSAL_RULES = [
    Rule(name="hornet_blocks", tag="physical", apply=_r_hornet_blocks),
    Rule(name="humility_unlocks_help", tag="social", apply=_r_humility_unlocks_help),
    Rule(name="washed_path_safe", tag="physical", apply=_r_washed_path_safe),
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


def hazard_present(lure: Lure) -> bool:
    return bool(lure.label)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN and r.calms_hazard]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for setting_id in SETTINGS:
        for goal_id in GOALS:
            for lure_id, lure in LURES.items():
                if hazard_present(lure):
                    combos.append((setting_id, goal_id, lure_id))
    return combos


def response_succeeds(response: Response) -> bool:
    return response.calms_hazard


def explain_response(response_id: str) -> str:
    resp = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is not a calm, sensible fix for a hornet problem "
        f"(sense={resp.sense} < {SENSE_MIN} or it does not really make the path safe). "
        f"Try one of: {better}.)"
    )


def predict_problem(world: World) -> dict:
    sim = world.copy()
    sim.get("hornet").meters["attracted"] += 1
    propagate(sim, narrate=False)
    return {
        "blocked": sim.get("path").meters["blocked"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
    }


def introduce(world: World, child: Entity, helper: Entity, setting: Setting, goal: Goal) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"At dusk, {child.id} stood in {setting.place}, where {setting.ghost_image}. "
        f"{child.pronoun().capitalize()} had a quest: to reach {goal.phrase} {goal.hanging_place}."
    )
    world.say(setting.opening)
    world.say(
        f"{helper.label_word.capitalize()} had said the old place only sounded haunted when the wind whispered through it, "
        f"but to {child.id} it still felt like the start of a ghost story."
    )


def spot_goal(world: World, child: Entity, goal: Goal, setting: Setting) -> None:
    world.say(
        f"Across {setting.blocked_spot}, {child.id} saw {goal.phrase} gleaming faintly. "
        f"If {child.pronoun()} could touch it, the quest would be complete."
    )


def reveal_hazard(world: World, child: Entity, lure: Lure, setting: Setting) -> None:
    hornet = world.get("hornet")
    hornet.meters["attracted"] += 1
    world.get("lure").meters["sweet"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But near {lure.where}, one hornet circled with a sharp, sewing-machine buzz. "
        f"{lure.hornet_line}"
    )
    if world.get("path").meters["blocked"] >= THRESHOLD:
        world.say(
            f"The narrow way to the goal no longer felt brave and thrilling. It felt blocked."
        )


def boast(world: World, child: Entity) -> None:
    child.memes["pride"] += 1
    world.say(
        f'"I can do it myself," {child.id} whispered, trying to sound bigger than {child.pronoun()} felt.'
    )


def flashback(world: World, child: Entity, helper: Entity, lure: Lure) -> None:
    child.memes["memory"] += 1
    child.memes["humility"] += 1
    child.memes["pride"] = 0.0
    world.say(
        f"Then a flashback rose in {child.pronoun('possessive')} mind: that afternoon, "
        f"{child.pronoun()} had boasted about never needing help and had rushed toward {lure.phrase} anyway."
    )
    world.say(
        f"It had ended with a frightened hop backward, a buzzing chase of only two steps, "
        f"and {helper.label_word}'s calm voice saying, "
        f'"Real bravery has humility in it. First you look, then you think, then you ask."'
    )


def choose_humility(world: World, child: Entity, helper: Entity) -> None:
    propagate(world, narrate=False)
    world.say(
        f"Remembering that, {child.id} stopped pretending to be fearless. "
        f'"{helper.label_word.capitalize()}, will you help me solve it?" {child.pronoun()} called.'
    )


def bring_hose(world: World, helper: Entity, setting: Setting) -> None:
    helper.meters["at_hose"] += 1
    world.say(
        f"{helper.label_word.capitalize()} came from {setting.hose_place} with the garden hose curled over one arm like a green snake."
    )


def solve(world: World, child: Entity, helper: Entity, lure: Lure, response: Response) -> None:
    hose = world.get("hose")
    hose.meters["water"] += 1
    if response_succeeds(response):
        world.get("lure").meters["gone"] += 1
        world.get("lure").meters["sweet"] = 0.0
        propagate(world, narrate=False)
        world.say(response.text.format(lure=lure.label))
        world.say(
            f"The sweet smell thinned and slid away. After a moment, the hornet lost interest and lifted off toward the flowers."
        )
    else:
        world.say(response.fail_text.format(lure=lure.label))


def finish_quest(world: World, child: Entity, goal: Goal, setting: Setting) -> None:
    child.memes["joy"] += 1
    world.say(
        f"When the path was quiet again, {child.id} walked across, reached up, and {goal.victory}."
    )
    world.say(
        f"{setting.ending_image} The place still looked ghostly, but now it felt friendly instead of frightening."
    )


def lesson(world: World, child: Entity) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} smiled because the quest had not been won by pretending to be the boldest person in the world. "
        f"It had been won by noticing the real problem, using the hose the right way, and having enough humility to ask for help."
    )


def tell(
    setting: Setting,
    goal: Goal,
    lure: Lure,
    response: Response,
    *,
    child_name: str = "Mira",
    child_gender: str = "girl",
    helper_type: str = "father",
    trait: str = "curious",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=[trait],
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            label="the helper",
            role="helper",
        )
    )
    hornet = world.add(
        Entity(
            id="hornet",
            type="hornet",
            label="hornet",
            phrase="a striped hornet",
            tags={"hornet"},
        )
    )
    path = world.add(
        Entity(
            id="path",
            type="path",
            label="path",
            phrase="the narrow path",
        )
    )
    hose = world.add(
        Entity(
            id="hose",
            type="hose",
            label="hose",
            phrase="the garden hose",
            tags={"hose"},
        )
    )
    world.add(
        Entity(
            id="lure",
            type="spill",
            label=lure.label,
            phrase=lure.phrase,
            tags=set(lure.tags),
        )
    )
    world.add(
        Entity(
            id="goal",
            type="goal",
            label=goal.label,
            phrase=goal.phrase,
            tags=set(goal.tags),
        )
    )

    introduce(world, child, helper, setting, goal)
    spot_goal(world, child, goal, setting)

    world.para()
    reveal_hazard(world, child, lure, setting)
    boast(world, child)

    world.para()
    flashback(world, child, helper, lure)
    choose_humility(world, child, helper)
    bring_hose(world, helper, setting)

    world.para()
    solve(world, child, helper, lure, response)
    if not response_succeeds(response) or world.get("path").meters["blocked"] >= THRESHOLD:
        raise StoryError("The chosen response did not make the quest path safe.")
    finish_quest(world, child, goal, setting)
    lesson(world, child)

    world.facts.update(
        child=child,
        helper=helper,
        setting=setting,
        goal_cfg=goal,
        lure_cfg=lure,
        response=response,
        hornet=hornet,
        path=path,
        hose=hose,
        humility=child.memes["humility"] >= THRESHOLD,
        solved=world.get("path").meters["blocked"] < THRESHOLD,
        asked_for_help=helper.memes["asked"] >= THRESHOLD,
        flashback_used=child.memes["memory"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "moon_garden": Setting(
        id="moon_garden",
        place="the moon garden behind the shed",
        opening="White stones made a crooked trail under the beans, and an old gate clicked softly whenever the wind touched it.",
        ghost_image="the bean poles cast long bars like the ribs of a sleeping ghost",
        blocked_spot="the white-stone path",
        hose_place="the shed door",
        ending_image="The bell gave one clear ring that floated through the leaves like a small, kind ghost saying good night.",
        tags={"garden", "ghost"},
    ),
    "ivy_path": Setting(
        id="ivy_path",
        place="the ivy path beside the old wall",
        opening="The wall was patched with moon-pale ivy, and a cracked birdbath shone like a little haunted pond.",
        ghost_image="the ivy trembled in the breeze like a row of green sleeves",
        blocked_spot="the ivy-edged stepping stones",
        hose_place="the spigot by the old wall",
        ending_image="The ribbon fluttered in the dim air, and even the shadows seemed to settle down and listen.",
        tags={"ivy", "ghost"},
    ),
    "orchard_gate": Setting(
        id="orchard_gate",
        place="the orchard gate at the edge of the yard",
        opening="The apple trees rustled overhead, and the gate's iron curl looked like a black question mark against the sky.",
        ghost_image="the branches made slow shapes on the ground like wandering spirits",
        blocked_spot="the gate path",
        hose_place="the pump near the pears",
        ending_image="The key clicked in the lock-box with a tidy little sound, and the whole orchard seemed to exhale.",
        tags={"orchard", "ghost"},
    ),
}

GOALS = {
    "bell": Goal(
        id="bell",
        label="bell",
        phrase="the tiny silver bell",
        hanging_place="from the old gate latch",
        victory="rang the tiny silver bell",
        tags={"bell", "quest"},
    ),
    "ribbon": Goal(
        id="ribbon",
        label="ribbon",
        phrase="the pale ribbon",
        hanging_place="from a low branch",
        victory="untied the pale ribbon and tucked it safely into a pocket",
        tags={"ribbon", "quest"},
    ),
    "key": Goal(
        id="key",
        label="key",
        phrase="the brass key",
        hanging_place="inside a little lock-box on the post",
        victory="opened the little box and claimed the brass key",
        tags={"key", "quest"},
    ),
}

LURES = {
    "jam": Lure(
        id="jam",
        label="jam",
        phrase="the sticky jam",
        where="a shiny patch of jam on one stepping stone",
        washed="the jam streamed off the stone",
        hornet_line="It kept returning to the sticky sweetness as if the path belonged to it now.",
        tags={"sweet", "jam"},
    ),
    "peach": Lure(
        id="peach",
        label="fallen peach",
        phrase="the split fallen peach",
        where="a split peach under the gate post",
        washed="the peachy pulp washed into the grass",
        hornet_line="The hornet bobbed over the split fruit, guarding the smell of sugar in the dusk.",
        tags={"sweet", "peach"},
    ),
    "juice": Lure(
        id="juice",
        label="juice spill",
        phrase="the sugary juice spill",
        where="a little juice spill beside the path",
        washed="the juice ran away in a thin, shining stream",
        hornet_line="Each time it drifted away, the hornet zipped back to the sweet puddle again.",
        tags={"sweet", "juice"},
    ),
}

RESPONSES = {
    "wash_away": Response(
        id="wash_away",
        sense=3,
        calms_hazard=True,
        text="Together they opened the hose just enough to send a smooth ribbon of water over the {lure}, washing the sweetness away without chasing the hornet.",
        fail_text="They fumbled with the hose and did not wash the sweet spot away.",
        qa_text="They used the hose to wash away the sweet spill that was attracting the hornet.",
        tags={"hose", "problem_solving"},
    ),
    "wait_then_wash": Response(
        id="wait_then_wash",
        sense=2,
        calms_hazard=True,
        text="First they stood still and watched where the hornet was circling. Then they used the hose to rinse the {lure} away when the air was clear.",
        fail_text="They waited, but never removed the sweet spot, so the hornet stayed.",
        qa_text="They watched calmly and then used the hose to rinse away the sweet lure.",
        tags={"hose", "problem_solving", "patience"},
    ),
    "swat": Response(
        id="swat",
        sense=1,
        calms_hazard=False,
        text="They swung at the hornet.",
        fail_text="Swatting only made the hornet angrier and left the sweet lure where it was.",
        qa_text="They tried to swat at the hornet.",
        tags={"bad_idea"},
    ),
    "spray_hornet": Response(
        id="spray_hornet",
        sense=1,
        calms_hazard=False,
        text="They sprayed the hornet itself.",
        fail_text="Spraying at the hornet was a poor idea and did not solve why it was there.",
        qa_text="They sprayed at the hornet instead of fixing the real problem.",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Mira", "Nora", "Lila", "Zoe", "Ava", "Tess", "June", "Ella"]
BOY_NAMES = ["Owen", "Theo", "Max", "Finn", "Leo", "Sam", "Eli", "Noah"]
TRAITS = ["curious", "careful", "dreamy", "brave", "thoughtful", "quiet"]


@dataclass
class StoryParams:
    setting: str
    goal: str
    lure: str
    response: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "hornet": [
        (
            "What is a hornet?",
            "A hornet is a kind of large wasp with a strong buzz and a sting. It is best to give a hornet space and let a grown-up help with the problem."
        )
    ],
    "hose": [
        (
            "What does a garden hose do?",
            "A garden hose carries water from a spigot so people can water plants or rinse things clean. Used carefully, it can wash away a mess without hurting anything."
        )
    ],
    "humility": [
        (
            "What is humility?",
            "Humility means knowing you do not have to act bigger or smarter than you really are. It helps you ask for help and listen when there is a real problem."
        )
    ],
    "ghost": [
        (
            "Why can a garden look spooky at night?",
            "At night, shadows get longer and small sounds seem bigger, so familiar places can look mysterious. That does not mean they are dangerous or truly haunted."
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means noticing what is really wrong and choosing a step that fixes that cause. Good problem solving is calm, careful, and kind."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is when a story briefly remembers something from earlier. It can help a character make a better choice in the present."
        )
    ],
}
KNOWLEDGE_ORDER = ["hornet", "hose", "humility", "ghost", "problem_solving", "flashback"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    goal = f["goal_cfg"]
    lure = f["lure_cfg"]
    return [
        f'Write a gentle ghost-story quest for a 3-to-5-year-old that includes the words "hornet," "humility," and "hose."',
        f"Tell a spooky-but-safe story where {child.id} tries to reach {goal.phrase} in {setting.place}, but a hornet is guarding the way because of {lure.phrase}.",
        "Write a story that uses a flashback to teach humility and ends with calm problem solving instead of fighting.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    setting = f["setting"]
    goal = f["goal_cfg"]
    lure = f["lure_cfg"]
    response = f["response"]
    pw = helper.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child on a small quest, and {pw} who helps when the path turns tricky."
        ),
        (
            f"What was {child.id}'s quest?",
            f"{child.id}'s quest was to reach {goal.phrase}. The goal waited across {setting.blocked_spot}, which made the trip feel like an adventure."
        ),
        (
            "What made the place feel like a ghost story?",
            f"The story happens at dusk in {setting.place}, with shadows, soft sounds, and old garden shapes that looked spooky. The setting felt haunted in a playful way, even though the real problem was not a ghost at all."
        ),
        (
            "Why was the hornet there?",
            f"The hornet was circling because of {lure.phrase}. It stayed near the sweet smell, so the path felt blocked until the real cause was removed."
        ),
    ]
    if f.get("flashback_used"):
        qa.append(
            (
                "What did the flashback help the child remember?",
                f"The flashback reminded {child.id} about an earlier moment of bragging and rushing before thinking. Remembering that helped {child.pronoun()} choose humility instead of pretending to be fearless."
            )
        )
    if f.get("asked_for_help"):
        qa.append(
            (
                f"How did {child.id} show humility?",
                f"{child.id} stopped insisting on doing everything alone and asked {pw} for help. That was humble because {child.pronoun()} admitted the problem was real and worth solving carefully."
            )
        )
    if f.get("solved"):
        qa.append(
            (
                "How did they solve the hornet problem?",
                f"{pw.capitalize()} and {child.id} did not try to fight the hornet. {response.qa_text} Once the sweetness was gone, the hornet drifted away and the path became safe again."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with {child.id} finishing the quest and the spooky place feeling gentle instead of scary. The ending shows that the child changed by using humility and smart problem solving."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"hornet", "hose", "humility", "ghost", "problem_solving", "flashback"}
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moon_garden",
        goal="bell",
        lure="jam",
        response="wash_away",
        name="Mira",
        gender="girl",
        helper="father",
        trait="curious",
    ),
    StoryParams(
        setting="ivy_path",
        goal="ribbon",
        lure="peach",
        response="wait_then_wash",
        name="Theo",
        gender="boy",
        helper="mother",
        trait="thoughtful",
    ),
    StoryParams(
        setting="orchard_gate",
        goal="key",
        lure="juice",
        response="wash_away",
        name="Lila",
        gender="girl",
        helper="uncle",
        trait="dreamy",
    ),
]


def explain_rejection(lure: Lure) -> str:
    return (
        f"(No story: without a real sweet lure like {lure.label}, the hornet would not have a grounded reason to guard the path. "
        f"This world only tells stories where the problem has a clear cause.)"
    )


ASP_RULES = r"""
hazard(L) :- lure(L).

sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M, calms(R).
valid(S,G,L) :- setting(S), goal(G), lure(L), hazard(L), some_sensible.

some_sensible :- sensible(_).

solved(R) :- chosen_response(R), calms(R), sense(R,S), sense_min(M), S >= M.
bad_choice(R) :- chosen_response(R), not solved(R).

#show valid/3.
#show sensible/1.
#show solved/1.
#show bad_choice/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for goal_id in GOALS:
        lines.append(asp.fact("goal", goal_id))
    for lure_id in LURES:
        lines.append(asp.fact("lure", lure_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        if response.calms_hazard:
            lines.append(asp.fact("calms", response_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_solved(response_id: str) -> bool:
    import asp

    model = asp.one_model(asp_program(f"chosen_response({asp.quote(response_id)})."))
    return bool(asp.atoms(model, "solved"))


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    emit(sample, trace=False, qa=False)


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    cl_valid = set(asp_valid_combos())
    if py_valid == cl_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - cl_valid:
            print("  only in python:", sorted(py_valid - cl_valid))
        if cl_valid - py_valid:
            print("  only in clingo:", sorted(cl_valid - py_valid))

    py_sensible = {r.id for r in sensible_responses()}
    cl_sensible = set(asp_sensible())
    if py_sensible == cl_sensible:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sensible)} clingo={sorted(cl_sensible)}")

    mismatches = []
    for response_id, response in RESPONSES.items():
        if asp_solved(response_id) != response_succeeds(response):
            mismatches.append(response_id)
    if not mismatches:
        print("OK: response success model matches for all responses.")
    else:
        rc = 1
        print("MISMATCH in response success:", sorted(mismatches))

    try:
        smoke_test()
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story quest world: a hornet blocks the path until a child uses humility and a hose to solve the real problem."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and args.response in RESPONSES and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.response and args.response in RESPONSES and not RESPONSES[args.response].calms_hazard:
        raise StoryError(explain_response(args.response))
    if args.lure and args.lure not in LURES:
        raise StoryError("(Unknown lure.)")

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.goal is None or combo[1] == args.goal)
        and (args.lure is None or combo[2] == args.lure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, goal_id, lure_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    helper = args.helper or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        goal=goal_id,
        lure=lure_id,
        response=response_id,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting '{params.setting}'.)")
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal '{params.goal}'.)")
    if params.lure not in LURES:
        raise StoryError(f"(Unknown lure '{params.lure}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response '{params.response}'.)")
    if params.response not in {r.id for r in sensible_responses()}:
        raise StoryError(explain_response(params.response))

    world = tell(
        SETTINGS[params.setting],
        GOALS[params.goal],
        LURES[params.lure],
        RESPONSES[params.response],
        child_name=params.name,
        child_gender=params.gender,
        helper_type=params.helper,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible()
        print(f"sensible responses: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (setting, goal, lure) combos:\n")
        for setting_id, goal_id, lure_id in combos:
            print(f"  {setting_id:12} {goal_id:7} {lure_id}")
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
            header = f"### {p.name}: {p.goal} at {p.setting} ({p.lure}, {p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
