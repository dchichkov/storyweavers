#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/divine_bill_hiccing_sound_effects_rhyme_kindness.py
================================================================================

A standalone story world for a tiny space adventure built from the seed words
"divine, bill, hiccing" and the requested features Sound Effects, Rhyme, and
Kindness.

Premise
-------
A child space crew is following a rhyme-map through a bright part of space.
Their little helper creature starts hiccing, which makes the guidance song skip
and the ship wobble. The crew can only solve the problem with a kind response
that fits the cause of the hiccing. When they choose the fitting, gentle help,
the rhythm comes back, the route steadies, and the ending image proves that
kindness changed the world.

Why the constraint exists
-------------------------
Not every comforting action fits every problem. If a moon-moth is hiccing
because it gulped comet crumbs too fast, a slow sip of water or a pause to
breathe makes sense. If it is hiccing because it got scared by a loud clang,
then a soft hand, a calm count, or a reassuring rhyme makes sense instead. This
world refuses mismatched fixes. The story's turn must come from a plausible,
kind method, not a random nice-sounding gesture.

Run it
------
    python storyworlds/worlds/gpt-5.4/divine_bill_hiccing_sound_effects_rhyme_kindness.py
    python storyworlds/worlds/gpt-5.4/divine_bill_hiccing_sound_effects_rhyme_kindness.py --place moon_meadow --cause scared --response hand_hold
    python storyworlds/worlds/gpt-5.4/divine_bill_hiccing_sound_effects_rhyme_kindness.py --cause crumbs --response hand_hold
    python storyworlds/worlds/gpt-5.4/divine_bill_hiccing_sound_effects_rhyme_kindness.py --all
    python storyworlds/worlds/gpt-5.4/divine_bill_hiccing_sound_effects_rhyme_kindness.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/divine_bill_hiccing_sound_effects_rhyme_kindness.py --qa --json
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
KINDNESS_MIN = 2


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
        female = {"girl", "mother", "woman", "pilot_girl"}
        male = {"boy", "father", "man", "pilot_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    sky: str
    trail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    setup: str
    reason: str
    sound: str
    hic_rate: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    fixes: set[str] = field(default_factory=set)
    kindness: int = 0
    action: str = ""
    qa_text: str = ""
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


def _r_hic_wobble(world: World) -> list[str]:
    out: list[str] = []
    moth = world.entities.get("moth")
    ship = world.entities.get("ship")
    if moth is None or ship is None:
        return out
    if moth.meters["hiccing"] < THRESHOLD:
        return out
    sig = ("wobble", "moth")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ship.meters["wobble"] += 1
    ship.meters["song_skip"] += 1
    for ent in world.entities.values():
        if ent.kind == "character":
            ent.memes["concern"] += 1
    out.append("__wobble__")
    return out


def _r_kind_relief(world: World) -> list[str]:
    out: list[str] = []
    moth = world.entities.get("moth")
    ship = world.entities.get("ship")
    if moth is None or ship is None:
        return out
    if moth.meters["comforted"] < THRESHOLD:
        return out
    sig = ("relief", "moth")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    moth.meters["hiccing"] = 0.0
    ship.meters["wobble"] = 0.0
    ship.meters["song_skip"] = 0.0
    for ent in world.entities.values():
        if ent.kind == "character":
            ent.memes["relief"] += 1
            ent.memes["joy"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="hic_wobble", tag="physical", apply=_r_hic_wobble),
    Rule(name="kind_relief", tag="social", apply=_r_kind_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(s for s in items if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def cause_matches_response(cause: Cause, response: Response) -> bool:
    return cause.id in response.fixes and response.kindness >= KINDNESS_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for cause_id, cause in CAUSES.items():
            for response_id, response in RESPONSES.items():
                if cause_matches_response(cause, response):
                    combos.append((place_id, cause_id, response_id))
    return combos


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    moth = sim.get("moth")
    moth.meters["hiccing"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("ship").meters["wobble"] >= THRESHOLD,
        "song_skip": sim.get("ship").meters["song_skip"] >= THRESHOLD,
    }


def introduce(world: World, captain: Entity, pal: Entity, moth: Entity, bill_name: str) -> None:
    captain.memes["joy"] += 1
    pal.memes["joy"] += 1
    world.say(
        f"{captain.id} zipped through {world.place.label} in a small silver ship with "
        f"{pal.id} and a tiny moon-moth named {bill_name}. {world.place.sky}"
    )
    world.say(
        f"On the dashboard glowed a divine star chart that only opened when the crew sang "
        f"a rhyme together."
    )
    world.say(
        f'"Zoom-ziiip! Vroom-vree!" went the engine as they followed the shining trail. '
        f'{world.place.trail}'
    )
    world.facts["bill_name"] = bill_name


def sing_rhyme(world: World, captain: Entity, pal: Entity) -> None:
    world.say(
        f'{captain.id} tapped the wheel and sang, "Star so bright, guide our flight!" '
        f'{pal.id} answered, "Moon so gleam, steer our dream!"'
    )


def trouble_begins(world: World, moth: Entity, cause: Cause) -> None:
    moth.meters["hiccing"] += 1
    moth.meters["flutter"] += 1
    propagate(world, narrate=False)
    world.say(cause.setup)
    world.say(
        f"Then the little moon-moth began hiccing: {cause.sound} {cause.sound} {cause.sound}! "
        f"Its wings bobbled like soft paper stars."
    )


def warn(world: World, captain: Entity, pal: Entity, cause: Cause) -> None:
    pred = predict_wobble(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_song_skip"] = pred["song_skip"]
    if pred["wobble"]:
        world.say(
            f'{pal.id} looked at the dancing lights. "Oh no. When Bill starts hiccing, the rhyme-map skips, '
            f"and the ship wobbles too."'
        )
    else:
        world.say(
            f'{pal.id} listened closely. "Bill sounds upset. We should help before the path gets messy."'
        )
    captain.memes["concern"] += 1
    pal.memes["concern"] += 1


def choose_kindness(world: World, captain: Entity, moth: Entity, response: Response, cause: Cause) -> None:
    captain.memes["kindness"] += 1
    moth.meters["comforted"] += 1
    moth.memes["trust"] += 1
    propagate(world, narrate=False)
    world.say(response.action)
    world.say(
        f"Bill blinked at {captain.id}, slowed {moth.pronoun('possessive')} wings, and listened. "
        f"The kindness fit the trouble, because {cause.reason}"
    )


def calm_and_finish(world: World, captain: Entity, pal: Entity, moth: Entity) -> None:
    world.say(
        f'Soon the hiccing stopped. "Pip?" said Bill, and then, "Peep-peep!" much more smoothly.'
    )
    world.say(
        f'The ship settled from wobble to whisper. "Shhh... zoom," sang the little engine as the '
        f'divine chart opened wide again.'
    )
    world.say(
        f'{captain.id} and {pal.id} finished their rhyme together: "Kind and slow, and off we go!"'
    )
    world.say(
        f"Below them, the stars looked like lanterns on velvet, and Bill rode on the window rim, "
        f"quiet and proud."
    )


def tell(
    place: Place,
    cause: Cause,
    response: Response,
    *,
    captain_name: str = "Nova",
    captain_type: str = "girl",
    pal_name: str = "Bo",
    pal_type: str = "boy",
    bill_name: str = "Bill",
) -> World:
    world = World(place)
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_type, role="captain"))
    pal = world.add(Entity(id=pal_name, kind="character", type=pal_type, role="pal"))
    moth = world.add(Entity(id="moth", kind="thing", type="creature", label="moon-moth", role="helper"))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="ship", role="vehicle"))
    world.facts["captain"] = captain
    world.facts["pal"] = pal
    world.facts["moth"] = moth
    world.facts["ship"] = ship

    introduce(world, captain, pal, moth, bill_name)
    sing_rhyme(world, captain, pal)

    world.para()
    trouble_begins(world, moth, cause)
    warn(world, captain, pal, cause)

    world.para()
    choose_kindness(world, captain, moth, response, cause)
    calm_and_finish(world, captain, pal, moth)

    world.facts.update(
        place=place,
        cause=cause,
        response=response,
        resolved=moth.meters["hiccing"] < THRESHOLD and ship.meters["wobble"] < THRESHOLD,
        bill_name=bill_name,
    )
    return world


PLACES = {
    "moon_meadow": Place(
        id="moon_meadow",
        label="the Moon Meadow",
        sky="Blue dust floated up from the ground, and far away Saturn wore a ring like a golden smile.",
        trail="Every star-marker blinked in time, blink-blink, wink-wink.",
        tags={"space", "moon"},
    ),
    "comet_dock": Place(
        id="comet_dock",
        label="the Comet Dock",
        sky="Tall ice comets stood in rows like shining boats, and the dark sky glittered behind them.",
        trail="The docking lights clicked in a neat row: tik-tik, tik-tik.",
        tags={"space", "comet"},
    ),
    "nebula_lane": Place(
        id="nebula_lane",
        label="Nebula Lane",
        sky="Pink and purple mist curled around the ship like soft paint in water.",
        trail="The star-buoys glowed one by one: plink, plink, plink.",
        tags={"space", "nebula"},
    ),
}

CAUSES = {
    "crumbs": Cause(
        id="crumbs",
        label="comet crumbs",
        setup="Bill had nibbled a pocketful of comet crumbs much too fast.",
        reason="Bill had gulped crumbs too quickly and needed help settling down.",
        sound='"Hic! Pip! Hic!"',
        hic_rate=2,
        tags={"hiccup", "eating"},
    ),
    "scared": Cause(
        id="scared",
        label="a clang in the hull",
        setup='A loose lunch tin rolled under a seat and went "CLANG!" against the hull.',
        reason="Bill had been startled and needed to feel safe again.",
        sound='"Eep-hic! Eep-hic!"',
        hic_rate=2,
        tags={"hiccup", "fear"},
    ),
    "lonely": Cause(
        id="lonely",
        label="being left out",
        setup="The children had been busy watching the chart, and tiny Bill had fluttered by the window all alone.",
        reason="Bill had felt left out and needed warm company.",
        sound='"Pip-hic... pip-hic..."',
        hic_rate=1,
        tags={"hiccup", "lonely"},
    ),
}

RESPONSES = {
    "water_sip": Response(
        id="water_sip",
        label="a sip of water",
        fixes={"crumbs"},
        kindness=3,
        action='Nova unclicked a tiny water bulb, held it carefully to Bill\'s curled bill, and whispered, "Small sip, little ship."',
        qa_text="gave Bill a tiny sip of water",
        tags={"water", "kindness"},
    ),
    "slow_count": Response(
        id="slow_count",
        label="a slow count",
        fixes={"crumbs", "scared"},
        kindness=2,
        action='The crew counted together in a hush: "One star, two star, breathe and float far," while Nova kept her hand near Bill without grabbing him.',
        qa_text="counted slowly and helped Bill breathe",
        tags={"breathing", "kindness", "counting"},
    ),
    "hand_hold": Response(
        id="hand_hold",
        label="a gentle hand-hold",
        fixes={"scared"},
        kindness=3,
        action='Nova set one finger by Bill\'s feet like a little perch. Bill stepped on, and Nova said, "You are safe with us."',
        qa_text="offered Bill a gentle perch and made him feel safe",
        tags={"comfort", "kindness"},
    ),
    "kind_rhyme": Response(
        id="kind_rhyme",
        label="a kind rhyme",
        fixes={"lonely"},
        kindness=3,
        action='Nova scooted close to the window and sang, "Bill, dear Bill, we love you still; come ride near and rest your will."',
        qa_text="sang Bill a kind rhyme so he would not feel left out",
        tags={"rhyme", "kindness"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Zuri", "Mira", "Astra", "Tia"]
BOY_NAMES = ["Bo", "Kai", "Milo", "Jett", "Nico", "Ollie"]


@dataclass
class StoryParams:
    place: str
    cause: str
    response: str
    captain_name: str
    captain_type: str
    pal_name: str
    pal_type: str
    bill_name: str = "Bill"
    seed: Optional[int] = None


KNOWLEDGE = {
    "hiccup": [
        (
            "What is a hiccup?",
            "A hiccup is a quick little jump in your breathing that can make a funny sound. It often goes away if you slow down and calm your body."
        )
    ],
    "fear": [
        (
            "Why can kindness help when someone feels scared?",
            "Kindness can help a scared person or animal feel safe. When they feel safe, their body can calm down."
        )
    ],
    "lonely": [
        (
            "What does it mean to feel lonely?",
            "Feeling lonely means you want company and do not want to be left by yourself. A kind voice or being included can help."
        )
    ],
    "water": [
        (
            "Why can a sip of water help after eating too fast?",
            "A small sip of water can help your throat and chest settle after gulping too quickly. It is a gentle way to slow down."
        )
    ],
    "breathing": [
        (
            "Why does slow breathing help the body?",
            "Slow breathing helps your body relax. When the body relaxes, jumpy feelings and quick hiccupy breaths can settle."
        )
    ],
    "counting": [
        (
            "Why do people count slowly when they want to calm down?",
            "Counting slowly gives your mind something steady to follow. The steady rhythm can help your breathing slow too."
        )
    ],
    "comfort": [
        (
            "How can a gentle touch help someone?",
            "A gentle touch can show that someone is nearby and caring. That can make a frightened friend feel safer."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words end with the same or almost the same sound, like light and bright. Rhymes can make songs easy to remember."
        )
    ],
    "space": [
        (
            "What is a star chart?",
            "A star chart is a map that helps travelers know where they are among stars and planets. In stories, it can guide a spaceship home."
        )
    ],
    "moon": [
        (
            "What is a moon?",
            "A moon is a round world that circles a planet. Some moons are rocky, icy, or dusty."
        )
    ],
    "comet": [
        (
            "What is a comet?",
            "A comet is a small icy body in space that can grow a bright tail when it gets warm. It travels around the sun."
        )
    ],
    "nebula": [
        (
            "What is a nebula?",
            "A nebula is a huge cloud of gas and dust in space. It can glow with beautiful colors."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help, include, or comfort someone gently. Kind actions can change how another person feels."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "kindness",
    "hiccup",
    "fear",
    "lonely",
    "water",
    "breathing",
    "counting",
    "comfort",
    "rhyme",
    "space",
    "moon",
    "comet",
    "nebula",
]


def generation_prompts(world: World) -> list[str]:
    captain = world.facts["captain"]
    place = world.facts["place"]
    cause = world.facts["cause"]
    response = world.facts["response"]
    return [
        'Write a short story for a 3-to-5-year-old in a space-adventure style that includes the words "divine", "Bill", and "hiccing".',
        f"Tell a gentle space story where {captain.id} helps a tiny creature named Bill when {cause.label} makes him start hiccing, and the fix must be kindness.",
        f"Write a child-facing adventure set in {place.label} with sound effects, a simple rhyme, and a happy ending where {response.label} solves the problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    pal = f["pal"]
    place = f["place"]
    cause = f["cause"]
    response = f["response"]
    bill_name = f["bill_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {captain.id}, {pal.id}, and a tiny moon-moth named {bill_name}. They are riding through {place.label} in a small spaceship."
        ),
        (
            f"Why did the ship start to wobble?",
            f"The ship started to wobble because {bill_name} began hiccing, and the rhyme-map skipped when his little sounds broke the rhythm. The trouble began because {cause.reason}"
        ),
        (
            f"What did {captain.id} do to help {bill_name}?",
            f"{captain.id} {response.qa_text}. That was the right kind of help for this problem, so Bill could calm down."
        ),
        (
            "How did kindness change the ending?",
            f"Kindness helped Bill feel better, so the hiccing stopped and the ship became steady again. After that, the crew could sing their rhyme and follow the divine star chart home."
        ),
    ]
    if f.get("resolved"):
        qa.append(
            (
                "How did the story end?",
                f"It ended with the ship gliding smoothly through space while Bill rode quietly by the window. The last image shows that the wobble was gone because the crew chose gentle help."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"kindness", "hiccup", "space"} | set(world.facts["response"].tags) | set(world.facts["cause"].tags) | set(world.facts["place"].tags)
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moon_meadow",
        cause="crumbs",
        response="water_sip",
        captain_name="Nova",
        captain_type="girl",
        pal_name="Bo",
        pal_type="boy",
        bill_name="Bill",
    ),
    StoryParams(
        place="comet_dock",
        cause="scared",
        response="hand_hold",
        captain_name="Kai",
        captain_type="boy",
        pal_name="Luna",
        pal_type="girl",
        bill_name="Bill",
    ),
    StoryParams(
        place="nebula_lane",
        cause="lonely",
        response="kind_rhyme",
        captain_name="Mira",
        captain_type="girl",
        pal_name="Nico",
        pal_type="boy",
        bill_name="Bill",
    ),
    StoryParams(
        place="moon_meadow",
        cause="scared",
        response="slow_count",
        captain_name="Astra",
        captain_type="girl",
        pal_name="Milo",
        pal_type="boy",
        bill_name="Bill",
    ),
]


def explain_rejection(cause: Cause, response: Response) -> str:
    if response.kindness < KINDNESS_MIN:
        return (
            f"(No story: {response.label} is not kind enough for this world. "
            f"The turn must come from gentle help.)"
        )
    return (
        f"(No story: {response.label} does not fit the cause {cause.label}. "
        f"The fix has to match why Bill is hiccing.)"
    )


ASP_RULES = r"""
fits(C, R) :- response(R), cause(C), fixes(R, C).
kind_enough(R) :- response(R), kindness(R, K), kindness_min(M), K >= M.
valid(P, C, R) :- place(P), cause(C), response(R), fits(C, R), kind_enough(R).

resolved :- chosen_cause(C), chosen_response(R), fits(C, R), kind_enough(R).
wobble   :- chosen_cause(C), cause(C), not resolved.

outcome(resolved) :- resolved.
outcome(wobbly)   :- wobble.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid in CAUSES:
        lines.append(asp.fact("cause", cid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("kindness", rid, response.kindness))
        for c in sorted(response.fixes):
            lines.append(asp.fact("fixes", rid, c))
    lines.append(asp.fact("kindness_min", KINDNESS_MIN))
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
            asp.fact("chosen_cause", params.cause),
            asp.fact("chosen_response", params.response),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    cause = CAUSES[params.cause]
    response = RESPONSES[params.response]
    return "resolved" if cause_matches_response(cause, response) else "wobbly"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print(f"MISMATCH in outcome for {params}")
            break
    else:
        print(f"OK: outcomes match on {len(cases)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny space adventure where kindness solves Bill's hiccing."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--captain-name")
    ap.add_argument("--captain-type", choices=["girl", "boy"])
    ap.add_argument("--pal-name")
    ap.add_argument("--pal-type", choices=["girl", "boy"])
    ap.add_argument("--bill-name", default=None)
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.response:
        cause = CAUSES[args.cause]
        response = RESPONSES[args.response]
        if not cause_matches_response(cause, response):
            raise StoryError(explain_rejection(cause, response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cause is None or combo[1] == args.cause)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, cause, response = rng.choice(sorted(combos))
    captain_type = args.captain_type or rng.choice(["girl", "boy"])
    pal_type = args.pal_type or rng.choice(["girl", "boy"])
    captain_name = args.captain_name or _pick_name(rng, captain_type)
    pal_name = args.pal_name or _pick_name(rng, pal_type, avoid=captain_name)
    bill_name = args.bill_name or "Bill"
    return StoryParams(
        place=place,
        cause=cause,
        response=response,
        captain_name=captain_name,
        captain_type=captain_type,
        pal_name=pal_name,
        pal_type=pal_type,
        bill_name=bill_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Invalid cause: {params.cause})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Invalid response: {params.response})")

    place = PLACES[params.place]
    cause = CAUSES[params.cause]
    response = RESPONSES[params.response]
    if not cause_matches_response(cause, response):
        raise StoryError(explain_rejection(cause, response))

    world = tell(
        place=place,
        cause=cause,
        response=response,
        captain_name=params.captain_name,
        captain_type=params.captain_type,
        pal_name=params.pal_name,
        pal_type=params.pal_type,
        bill_name=params.bill_name,
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
        print(f"{len(combos)} compatible (place, cause, response) combos:\n")
        for place, cause, response in combos:
            print(f"  {place:12} {cause:8} {response}")
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
            header = f"### {p.place}: {p.cause} -> {p.response}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
