#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rural_ostrich_cliff_lookout_moral_value_twist.py
============================================================================

A standalone story world for a rhyming rural cliff-lookout tale about a young
ostrich whose caution is mistaken for cowardice. The twist is gentle and moral:
the ostrich is not shrinking from the edge, but sensing real danger first and
choosing to speak up. In this world, honesty and care count as bravery.

The simulation keeps a small physical/emotional state:
- physical meters: wind, loose stones, fog, danger, stumble, guided
- emotional memes: joy, worry, trust, relief, pride, gratitude

Run it
------
    python storyworlds/worlds/gpt-5.4/rural_ostrich_cliff_lookout_moral_value_twist.py
    python storyworlds/worlds/gpt-5.4/rural_ostrich_cliff_lookout_moral_value_twist.py --hazard fog_bank
    python storyworlds/worlds/gpt-5.4/rural_ostrich_cliff_lookout_moral_value_twist.py --response bell_wait
    python storyworlds/worlds/gpt-5.4/rural_ostrich_cliff_lookout_moral_value_twist.py --response dash
    python storyworlds/worlds/gpt-5.4/rural_ostrich_cliff_lookout_moral_value_twist.py --all --qa
    python storyworlds/worlds/gpt-5.4/rural_ostrich_cliff_lookout_moral_value_twist.py --verify
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
CAREFUL_TRAITS = {"careful", "steady", "gentle", "thoughtful"}


def was_or_were(entity: "Entity") -> str:
    return "were" if entity.pronoun() == "they" else "was"


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
        female = {"girl", "ewe", "hen", "woman"}
        male = {"boy", "ram", "rooster", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Goal:
    id: str
    wish: str
    shimmer: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    warning: str
    sign: str
    risk: str
    meter: str
    safe_responses: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    works_for: set[str]
    line: str
    helped_line: str
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


def _r_raise_danger(world: World) -> list[str]:
    lookout = world.get("lookout")
    out: list[str] = []
    for meter in ("wind", "loose", "fog"):
        if lookout.meters[meter] < THRESHOLD:
            continue
        sig = ("danger", meter)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        lookout.meters["danger"] += 1
        for ent in list(world.entities.values()):
            if ent.role in {"ostrich", "friend"}:
                ent.memes["worry"] += 1
        out.append("__danger__")
    return out


def _r_step_risk(world: World) -> list[str]:
    friend = world.get("friend")
    lookout = world.get("lookout")
    if friend.meters["edge_step"] < THRESHOLD or lookout.meters["danger"] < THRESHOLD:
        return []
    sig = ("stumble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.meters["stumble"] += 1
    friend.memes["fear"] += 1
    world.get("ostrich").memes["fear"] += 1
    return ["__stumble__"]


CAUSAL_RULES = [
    Rule("danger", "physical", _r_raise_danger),
    Rule("stumble", "physical", _r_step_risk),
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


def hazard_allows_response(hazard: Hazard, response: Response) -> bool:
    return hazard.id in response.works_for and response.id in hazard.safe_responses


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for goal in GOALS:
        for hid, hazard in HAZARDS.items():
            for rid, response in RESPONSES.items():
                if response.sense >= SENSE_MIN and hazard_allows_response(hazard, response):
                    combos.append((goal, hid, rid))
    return combos


def would_listen(trait: str, trust: int) -> bool:
    return trait in CAREFUL_TRAITS or trust >= 6


def outcome_of(params: "StoryParams") -> str:
    return "near_miss" if would_listen(params.friend_trait, params.trust) else "helped"


def predict_trouble(world: World, hazard: Hazard) -> dict:
    sim = world.copy()
    lookout = sim.get("lookout")
    lookout.meters[hazard.meter] += 1
    propagate(sim, narrate=False)
    sim.get("friend").meters["edge_step"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": lookout.meters["danger"],
        "stumble": sim.get("friend").meters["stumble"] >= THRESHOLD,
    }


def setup_scene(world: World, ostrich: Entity, friend: Entity, goal: Goal) -> None:
    ostrich.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"By a rural cliff lookout above the sheep-specked land, "
        f"{ostrich.id} the young ostrich and {friend.id} went hand in hand."
    )
    world.say(
        f"They came to {goal.wish}, where the far fields seemed to sing, "
        f"and the fence posts wore the sun like a copper ring."
    )


def notice_hazard(world: World, ostrich: Entity, friend: Entity, hazard: Hazard) -> None:
    lookout = world.get("lookout")
    lookout.meters[hazard.meter] += 1
    propagate(world, narrate=False)
    ostrich.memes["alert"] += 1
    world.say(
        f"But under the pretty morning, {hazard.sign}; "
        f"{ostrich.id} felt it first and whispered, \"Please stop by the line.\""
    )
    world.say(
        f"{friend.id} blinked at the brink and tilted {friend.pronoun('possessive')} head. "
        f"\"Why pause now, when the view ahead is spread?\""
    )


def warn(world: World, ostrich: Entity, friend: Entity, hazard: Hazard) -> None:
    pred = predict_trouble(world, hazard)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_stumble"] = pred["stumble"]
    ostrich.memes["honesty"] += 1
    world.say(
        f"{ostrich.id} tapped one long foot and answered in rhyme, "
        f"\"{hazard.warning} This is the careful time.\""
    )
    if pred["stumble"]:
        world.say(
            f"Then softly {ostrich.pronoun()} added, \"If we rush in a race, "
            f"one wrong little step could send fear to your face.\""
        )


def seeming_coward(world: World, friend: Entity, ostrich: Entity) -> None:
    friend.memes["impatience"] += 1
    world.say(
        f"{friend.id} gave a small huff. \"You bend and you sway. "
        f"Are you hiding from heights and from breezes today?\""
    )
    world.say(
        f"For one beat it sounded as if caution were small, "
        f"as if the first one to stop were not brave at all."
    )


def reveal_twist(world: World, ostrich: Entity, hazard: Hazard) -> None:
    ostrich.memes["pride"] += 1
    world.say(
        f"But here came the twist, bright and clear as a bell: "
        f"{ostrich.id} was not shrinking. {ostrich.pronoun().capitalize()} {was_or_were(ostrich)} reading the place well."
    )
    world.say(
        f"With tall, steady legs and a lookout-long view, "
        f"{ostrich.pronoun()} had sensed {hazard.risk} before anyone knew."
    )


def listen_branch(world: World, ostrich: Entity, friend: Entity, response: Response, goal: Goal) -> None:
    friend.memes["trust"] += 1
    friend.memes["relief"] += 1
    ostrich.memes["relief"] += 1
    world.say(
        f"{friend.id} looked once more, then stepped back from the drop. "
        f"\"I thought you were fearful. I see you were helping me stop.\""
    )
    world.say(response.line)
    world.say(
        f"Soon they were safe where the rail cast a stripe, "
        f"and {goal.ending} while the clouds drifted ripe."
    )


def step_then_help(world: World, ostrich: Entity, friend: Entity, helper: Entity,
                   response: Response, goal: Goal) -> None:
    friend.meters["edge_step"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But quick little feet took one daring step more; "
        f"loose pebbles went tick-tick and skipped toward the shore."
    )
    if friend.meters["stumble"] >= THRESHOLD:
        world.say(
            f"{friend.id} skidded and froze, all wobble and wide. "
            f"The cliff wind felt bigger than boasting or pride."
        )
    ostrich.memes["bravery"] += 1
    world.say(
        f"Then {ostrich.id} called, loud as a drum, "
        f"\"{helper.id}, please help us! Please quickly come!\""
    )
    helper.meters["guided"] += 1
    friend.memes["gratitude"] += 1
    ostrich.memes["gratitude"] += 1
    world.say(response.helped_line)
    world.say(
        f"When both hooves were steady and both hearts were light, "
        f"{goal.ending} from a safer new sight."
    )


def closing_moral(world: World, ostrich: Entity, friend: Entity) -> None:
    ostrich.memes["love"] += 1
    friend.memes["love"] += 1
    world.say(
        f"{friend.id} leaned close and said, \"Now I know what is true: "
        f"being brave can mean stopping, and speaking up too.\""
    )
    world.say(
        f"So at that rural lookout, where sky met the vale, "
        f"they learned honest care is the bravest detail."
    )


def tell(goal: Goal, hazard: Hazard, response: Response,
         ostrich_name: str = "Oona", friend_name: str = "Milo",
         friend_type: str = "kid", friend_trait: str = "bouncy",
         helper_type: str = "shepherd", trust: int = 5) -> World:
    world = World()
    ostrich = world.add(Entity(id=ostrich_name, kind="character", type="bird", role="ostrich"))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_type, role="friend",
        traits=[friend_trait]
    ))
    helper = world.add(Entity(id="Shepherd", kind="character", type=helper_type, role="helper"))
    lookout = world.add(Entity(id="lookout", type="place", label="cliff lookout"))

    setup_scene(world, ostrich, friend, goal)
    world.para()
    notice_hazard(world, ostrich, friend, hazard)
    warn(world, ostrich, friend, hazard)
    world.para()
    seeming_coward(world, friend, ostrich)
    reveal_twist(world, ostrich, hazard)
    world.para()

    listened = would_listen(friend_trait, trust)
    if listened:
        listen_branch(world, ostrich, friend, response, goal)
    else:
        step_then_help(world, ostrich, friend, helper, response, goal)

    world.para()
    closing_moral(world, ostrich, friend)

    world.facts.update(
        ostrich=ostrich,
        friend=friend,
        helper=helper,
        lookout=lookout,
        goal=goal,
        hazard=hazard,
        response=response,
        listened=listened,
        outcome="near_miss" if listened else "helped",
        trust=trust,
        friend_trait=friend_trait,
    )
    return world


GOALS = {
    "sunrise": Goal(
        "sunrise",
        "watch the sunrise spill gold over the farms below",
        "gold light trembled over the fields",
        "they watched the sunrise paint every paddock aglow",
        tags={"sunrise", "farm"},
    ),
    "market": Goal(
        "market",
        "count the wagons rolling to the valley market",
        "wagon bells glinted in the morning",
        "they counted the wagons below, snug and bright as a locket",
        tags={"market", "farm"},
    ),
    "swallows": Goal(
        "swallows",
        "see the swallows loop above the valley grass",
        "small wings flashed over the grass",
        "they watched the swallows stitch blue ribbons through the pass",
        tags={"birds", "farm"},
    ),
}

HAZARDS = {
    "loose_stones": Hazard(
        "loose_stones",
        "The stones are sliding underfoot.",
        "small stones kept clicking and slipping under the fence",
        "the ground was loose enough to roll from under a child",
        "loose",
        {"rail_path", "shepherd_rope"},
        tags={"cliff", "stones"},
    ),
    "sudden_gust": Hazard(
        "sudden_gust",
        "The wind is tossing hard along the edge.",
        "the gusts came in wild little whistles along the ledge",
        "a sudden gust could shove a small body off balance",
        "wind",
        {"rail_path", "crouch_wait", "shepherd_rope"},
        tags={"cliff", "wind"},
    ),
    "fog_bank": Hazard(
        "fog_bank",
        "The fog is swallowing the edge from sight.",
        "a milk-white fog was curling up and hiding the drop",
        "the hidden edge could trick quick feet into the wrong place",
        "fog",
        {"bell_wait", "shepherd_rope"},
        tags={"cliff", "fog"},
    ),
}

RESPONSES = {
    "rail_path": Response(
        "rail_path",
        3,
        {"loose_stones", "sudden_gust"},
        "So they took the fenced rail path, slow and neat, where the broad flat boards were kind to their feet.",
        "The shepherd led them back by the fenced rail path, slow and neat, till the broad flat boards felt safe beneath their feet.",
        "they used the fenced rail path instead of the risky edge",
        tags={"rail", "path"},
    ),
    "bell_wait": Response(
        "bell_wait",
        3,
        {"fog_bank"},
        "So they stayed by the old bell post, close and still, till the fog slid away from the rim of the hill.",
        "The shepherd brought them to the old bell post, close and still, and they waited there until the fog slipped off the hill.",
        "they stayed by the bell post and waited for the fog to clear",
        tags={"fog", "waiting"},
    ),
    "crouch_wait": Response(
        "crouch_wait",
        2,
        {"sudden_gust"},
        "So they crouched beside the stout fence rail, low and wise, till the wind lost its push and softened its sighs.",
        "The shepherd tucked them beside the stout fence rail, low and wise, until the gusts grew gentle under calmer skies.",
        "they crouched by the fence until the gusts eased",
        tags={"wind", "waiting"},
    ),
    "shepherd_rope": Response(
        "shepherd_rope",
        3,
        {"loose_stones", "sudden_gust", "fog_bank"},
        "So they asked the shepherd for the guide rope there, and followed it safely with patient care.",
        "The shepherd came with a guide rope there and walked them back with patient care.",
        "they asked the shepherd for the guide rope and followed it safely",
        tags={"shepherd", "rope"},
    ),
    "dash": Response(
        "dash",
        1,
        {"loose_stones", "sudden_gust", "fog_bank"},
        "They simply dashed ahead.",
        "They simply dashed ahead.",
        "they dashed ahead",
        tags={"unsafe"},
    ),
}

FRIENDS = {
    "kid": ("kid", ["bouncy", "careful", "steady", "hasty"]),
    "lamb": ("lamb", ["bouncy", "gentle", "hasty", "thoughtful"]),
    "calf": ("calf", ["bouncy", "steady", "hasty", "careful"]),
}

OSTRICH_NAMES = ["Oona", "Pip", "Talli", "Nell", "Kito", "Luma"]
FRIEND_NAMES = ["Milo", "Bram", "Tess", "Rina", "Poppy", "Glen"]


@dataclass
class StoryParams:
    goal: str
    hazard: str
    response: str
    ostrich_name: str
    friend_name: str
    friend_type: str
    friend_trait: str
    trust: int
    seed: Optional[int] = None


KNOWLEDGE = {
    "ostrich": [(
        "What is an ostrich?",
        "An ostrich is a very large bird with long legs and a long neck. It cannot fly, but it can run fast and notice things from far away."
    )],
    "cliff": [(
        "Why should children stay back from a cliff edge?",
        "A cliff edge can crumble, be slippery, or hide danger in wind or fog. Staying back gives your feet and your eyes more room to be safe."
    )],
    "wind": [(
        "Why can strong wind be dangerous on a high place?",
        "Strong wind can push your body or make you lose balance. On a high place, even a small shove can be a big problem."
    )],
    "fog": [(
        "Why is fog tricky near an edge?",
        "Fog hides where the ground ends, so you may think there is more path than there really is. That is why waiting or getting help is wise."
    )],
    "stones": [(
        "Why are loose stones risky on a cliff path?",
        "Loose stones can roll under your feet and make you slip. Near an edge, that makes careful walking extra important."
    )],
    "shepherd": [(
        "What does a shepherd do?",
        "A shepherd watches over animals and helps keep them safe. In stories set in the countryside, a shepherd often knows the land very well."
    )],
    "bravery": [(
        "Is stopping because something feels unsafe a brave choice?",
        "Yes. Real bravery is not showing off; it is choosing what protects people, even if someone laughs for a moment."
    )],
}
KNOWLEDGE_ORDER = ["ostrich", "cliff", "wind", "fog", "stones", "shepherd", "bravery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ostrich = f["ostrich"]
    friend = f["friend"]
    hazard = f["hazard"]
    goal = f["goal"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the words "rural" and "ostrich" and takes place at a cliff lookout.',
        f"Tell a gentle twist story where {ostrich.id} the ostrich seems scared at first, but is actually the first to notice {hazard.risk}, and saves {friend.id} by speaking up.",
        f"Write a moral-value story about children going to {goal.wish}, where caution turns out to be courage and the ending shows a safer kind of happiness.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    ostrich = f["ostrich"]
    friend = f["friend"]
    helper = f["helper"]
    hazard = f["hazard"]
    response = f["response"]
    goal = f["goal"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {ostrich.id}, a young ostrich, and {friend.id}, {friend.pronoun('possessive')} friend, at a rural cliff lookout. They went there to {goal.wish}."
        ),
        (
            "What problem did the ostrich notice?",
            f"{ostrich.id} noticed that {hazard.risk}. {ostrich.pronoun().capitalize()} paid attention to the place before anyone rushed closer to the edge."
        ),
        (
            f"Why did {friend.id} think {ostrich.id} was afraid?",
            f"{friend.id} first saw the pause and thought it meant fear. The twist is that {ostrich.id} was not shrinking back at all; {ostrich.pronoun()} {was_or_were(ostrich)} reading the danger correctly."
        ),
    ]
    if f["outcome"] == "near_miss":
        out.append((
            "How was the problem solved?",
            f"They listened before anyone got hurt, and {response.qa_text}. Because {friend.id} trusted the warning in time, the danger stayed only a near miss."
        ))
    else:
        out.append((
            f"How did {ostrich.id} help when things got scary?",
            f"{friend.id} took a risky step and began to wobble, so {ostrich.id} called {helper.id} for help right away. Asking for help quickly was the brave choice because it turned a worse accident into a safe ending."
        ))
    out.append((
        "What is the moral of the story?",
        "The story teaches that honest caution can be brave. Speaking up, listening, and asking for help are wiser than showing off near danger."
    ))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ostrich", "cliff", "bravery"}
    hazard = world.facts["hazard"]
    if hazard.id == "sudden_gust":
        tags.add("wind")
    if hazard.id == "fog_bank":
        tags.add("fog")
    if hazard.id == "loose_stones":
        tags.add("stones")
    if world.facts["response"].id == "shepherd_rope" or world.facts["outcome"] == "helped":
        tags.add("shepherd")
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("sunrise", "loose_stones", "rail_path", "Oona", "Milo", "kid", "careful", 5),
    StoryParams("market", "fog_bank", "bell_wait", "Pip", "Tess", "lamb", "hasty", 3),
    StoryParams("swallows", "sudden_gust", "crouch_wait", "Luma", "Bram", "calf", "steady", 4),
    StoryParams("market", "fog_bank", "shepherd_rope", "Nell", "Poppy", "kid", "bouncy", 2),
]


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of the safer responses: {better}.)"
    )


def explain_rejection(hazard: Hazard, response: Response) -> str:
    return (
        f"(No story: '{response.id}' is not a reasonable fix for '{hazard.id}'. "
        f"For this hazard, try one of: {', '.join(sorted(hazard.safe_responses))}.)"
    )


ASP_RULES = r"""
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
compatible(H, R) :- hazard(H), response(R), works_for(R, H), safe_response(H, R), sensible(R).
valid(G, H, R) :- goal(G), compatible(H, R).

listens :- trait(T), careful_trait(T).
listens :- trust(V), V >= 6.
near_miss :- listens.
helped :- not listens.
outcome(near_miss) :- near_miss.
outcome(helped) :- helped.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        for rid in sorted(h.safe_responses):
            lines.append(asp.fact("safe_response", hid, rid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        for hid in sorted(r.works_for):
            lines.append(asp.fact("works_for", rid, hid))
    for t in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", t))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("trait", params.friend_trait),
        asp.fact("trust", params.trust),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    csens, psens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if csens == psens:
        print(f"OK: sensible responses match ({sorted(csens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(csens)} python={sorted(psens)}")

    cases = list(CURATED)
    for seed in range(30):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive CLI verification
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming rural cliff-lookout story world with a brave ostrich and a gentle twist."
    )
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--friend-type", choices=FRIENDS)
    ap.add_argument("--friend-trait")
    ap.add_argument("--trust", type=int, choices=range(0, 11), metavar="[0-10]")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.hazard and args.response:
        hazard = HAZARDS[args.hazard]
        response = RESPONSES[args.response]
        if not hazard_allows_response(hazard, response):
            raise StoryError(explain_rejection(hazard, response))

    combos = [
        c for c in valid_combos()
        if (args.goal is None or c[0] == args.goal)
        and (args.hazard is None or c[1] == args.hazard)
        and (args.response is None or c[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    goal_id, hazard_id, response_id = rng.choice(sorted(combos))
    friend_type = args.friend_type or rng.choice(sorted(FRIENDS))
    allowed_traits = FRIENDS[friend_type][1]
    if args.friend_trait and args.friend_trait not in allowed_traits:
        raise StoryError(
            f"(No story: trait '{args.friend_trait}' does not fit friend type '{friend_type}'. "
            f"Try one of: {', '.join(sorted(allowed_traits))}.)"
        )
    friend_trait = args.friend_trait or rng.choice(sorted(allowed_traits))
    trust = args.trust if args.trust is not None else rng.randint(0, 10)
    ostrich_name = rng.choice(OSTRICH_NAMES)
    friend_name = rng.choice([n for n in FRIEND_NAMES if n != ostrich_name])
    return StoryParams(
        goal=goal_id,
        hazard=hazard_id,
        response=response_id,
        ostrich_name=ostrich_name,
        friend_name=friend_name,
        friend_type=friend_type,
        friend_trait=friend_trait,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        GOALS[params.goal],
        HAZARDS[params.hazard],
        RESPONSES[params.response],
        params.ostrich_name,
        params.friend_name,
        params.friend_type,
        params.friend_trait,
        "shepherd",
        params.trust,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (goal, hazard, response) combos:\n")
        for goal, hazard, response in combos:
            print(f"  {goal:8} {hazard:12} {response}")
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
            header = f"### {p.ostrich_name} and {p.friend_name}: {p.hazard} with {p.response} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
