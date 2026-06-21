#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ingenue_shed_mystery_to_solve_inner_monologue.py
===========================================================================

A small storyworld about a curious child who notices something odd around the
garden shed and tries to solve the little mystery in a calm, everyday way.

The domain is intentionally narrow and state-driven:
- a child notices one clue near the shed
- curiosity rises, with a little inner monologue
- the child chooses a sensible way to investigate
- the hidden cause is revealed
- the ending image shows what changed in the yard and in the child's heart

Run it
------
    python storyworlds/worlds/gpt-5.4/ingenue_shed_mystery_to_solve_inner_monologue.py
    python storyworlds/worlds/gpt-5.4/ingenue_shed_mystery_to_solve_inner_monologue.py --clue glow --cause lantern
    python storyworlds/worlds/gpt-5.4/ingenue_shed_mystery_to_solve_inner_monologue.py --response rush_door
    python storyworlds/worlds/gpt-5.4/ingenue_shed_mystery_to_solve_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4/ingenue_shed_mystery_to_solve_inner_monologue.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from inside this nested world directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "grandmother", "woman", "aunt", "sister"}
        male = {"boy", "father", "grandfather", "man", "uncle", "brother"}
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


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
@dataclass
class Clue:
    id: str
    seen_text: str
    wonder_text: str
    inner_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    reveal_text: str
    fix_text: str
    ending_image: str
    clues: set[str] = field(default_factory=set)
    living: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    phrase: str
    helper: bool = False
    light: bool = False
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_curiosity(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["clue_seen"] < THRESHOLD:
        return []
    sig = ("curiosity", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    return []


def _r_dark_worry(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["clue_seen"] < THRESHOLD:
        return []
    if world.facts.get("time") != "dusk":
        return []
    if child.meters["visibility"] >= THRESHOLD:
        return []
    sig = ("dusk_worry", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    return []


def _r_solved_relief(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["mystery_solved"] < THRESHOLD:
        return []
    sig = ("relief", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["worry"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="curiosity", tag="emotion", apply=_r_curiosity),
    Rule(name="dusk_worry", tag="emotion", apply=_r_dark_worry),
    Rule(name="relief", tag="emotion", apply=_r_solved_relief),
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


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def clue_matches(clue: Clue, cause: Cause) -> bool:
    return clue.id in cause.clues


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def outcome_of(params: "StoryParams") -> str:
    return "care" if CAUSES[params.cause].living else "explain"


def explain_combo(clue: Clue, cause: Cause) -> str:
    good = ", ".join(sorted(cause.clues))
    return (
        f"(No story: the clue '{clue.id}' does not fit the cause '{cause.id}'. "
        f"That cause naturally makes {good}, so this mystery would feel fake.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a calmer choice like {better}.)"
    )


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for clue_id, clue in CLUES.items():
        for cause_id, cause in CAUSES.items():
            if clue_matches(clue, cause):
                combos.append((clue_id, cause_id))
    return combos


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def predict_feeling(world: World, response: Response) -> dict:
    sim = world.copy()
    child = sim.get("child")
    if response.light or response.helper:
        child.meters["visibility"] += 1
    propagate(sim, narrate=False)
    return {
        "worry": child.memes["worry"],
        "curiosity": child.memes["curiosity"],
    }


def introduce(world: World, child: Entity, helper: Entity, trait: str, time: str) -> None:
    light = "golden" if time == "afternoon" else "blue-gray"
    helper_word = helper.label_word
    world.say(
        f"On a {light} {time}, {child.id} was in the backyard with {helper_word}."
    )
    world.say(
        f"{helper_word.capitalize()} sometimes laughed and called {child.pronoun('object')} "
        f"the family's little ingenue detective, because ordinary things always turned into "
        f"questions in {child.pronoun('possessive')} mind."
    )
    if trait == "careful":
        world.say(f"{child.id} liked to look twice before doing anything.")
    elif trait == "dreamy":
        world.say(f"{child.id} often paused in the middle of chores to wonder about small things.")
    else:
        world.say(f"{child.id} noticed details that other people walked past.")


def notice_clue(world: World, child: Entity, clue: Clue) -> None:
    child.meters["clue_seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {child.pronoun()} noticed something odd near the shed: {clue.seen_text}."
    )


def wonder(world: World, child: Entity, clue: Clue, response: Response) -> None:
    feeling = predict_feeling(world, response)
    extra = ""
    if feeling["worry"] >= THRESHOLD:
        extra = " The late light made the boards look darker than they really were."
    world.say(
        f"{child.id} stopped with one hand on the watering can. {clue.wonder_text}.{extra}"
    )
    world.say(f'{child.pronoun().capitalize()} thought, "{clue.inner_line}"')
    if child.memes["curiosity"] >= THRESHOLD:
        world.say(
            f"The question tugged at {child.pronoun('object')} more strongly than the chore did."
        )


def choose_response(world: World, child: Entity, helper: Entity, response: Response, time: str) -> None:
    if response.id == "ask_adult":
        child.memes["trust"] += 1
        helper.memes["care"] += 1
        child.meters["visibility"] += 1
        world.say(
            f"Instead of guessing, {child.id} went to {helper.label_word} and said, "
            f'"Something strange is happening by the shed. Will you come see?"'
        )
        world.say(
            f"{helper.label_word.capitalize()} put down the basket and came along slowly, "
            f"the way grown-ups do when they want to keep a small worry from growing."
        )
    elif response.id == "bring_flashlight":
        child.meters["visibility"] += 1
        world.say(
            f"{child.id} remembered the flashlight by the back step and fetched it before going closer."
        )
        if time == "dusk":
            world.say(
                f"The white beam made the path to the shed look ordinary again."
            )
        else:
            world.say(
                f"It felt a little silly to use a flashlight in daylight, but it also felt smart."
            )


def reveal(world: World, child: Entity, helper: Entity, cause: Cause, response: Response) -> None:
    child.meters["mystery_solved"] += 1
    propagate(world, narrate=False)
    if response.helper:
        world.say(
            f"Together they eased the shed door open. {cause.reveal_text}"
        )
    else:
        world.say(
            f"{child.id} stepped close, took a breath, and peeped inside. {cause.reveal_text}"
        )


def resolve(world: World, child: Entity, helper: Entity, cause: Cause) -> None:
    if cause.living:
        child.memes["kindness"] += 1
        helper.memes["care"] += 1
        world.say(cause.fix_text)
        world.say(
            f"{child.id} felt the last bit of worry loosen in {child.pronoun('possessive')} chest."
        )
    else:
        child.memes["understanding"] += 1
        world.say(cause.fix_text)
        world.say(
            f"It was almost funny how a mystery could shrink once it had a plain reason."
        )


def ending(world: World, child: Entity, helper: Entity, cause: Cause) -> None:
    if cause.living:
        world.say(
            f"After that, the backyard sounded gentle again, and {cause.ending_image}"
        )
    else:
        world.say(
            f"A little later, the yard went back to its soft evening noises, and {cause.ending_image}"
        )


def tell(
    clue: Clue,
    cause: Cause,
    response: Response,
    child_name: str = "June",
    child_type: str = "girl",
    helper_type: str = "grandfather",
    trait: str = "curious",
    time: str = "afternoon",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label="the helper", role="helper"))
    shed = world.add(Entity(id="shed", kind="thing", type="shed", label="shed"))
    child.attrs["name"] = child_name
    helper.attrs["relation"] = helper.label_word
    world.facts["time"] = time

    introduce(world, child, helper, trait, time)

    world.para()
    notice_clue(world, child, clue)
    wonder(world, child, clue, response)
    choose_response(world, child, helper, response, time)

    world.para()
    reveal(world, child, helper, cause, response)
    resolve(world, child, helper, cause)

    world.para()
    ending(world, child, helper, cause)

    world.facts.update(
        child=child,
        helper=helper,
        shed=shed,
        clue=clue,
        cause=cause,
        response=response,
        child_name=child_name,
        trait=trait,
        time=time,
        solved=child.meters["mystery_solved"] >= THRESHOLD,
        outcome="care" if cause.living else "explain",
    )
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
CLUES = {
    "scratch": Clue(
        id="scratch",
        seen_text="a soft scratch-scratch came from behind the lower shelf",
        wonder_text="It sounded too small to be a rake and too steady to be the wind",
        inner_line="What is making that tiny scratch in the shed?",
        tags={"shed", "sound", "curiosity"},
    ),
    "glow": Clue(
        id="glow",
        seen_text="a warm stripe of light lay under the shed door",
        wonder_text="The shed was supposed to be dark with the sun going down",
        inner_line="Why is the shed glowing when nobody is in there?",
        tags={"shed", "light", "curiosity"},
    ),
    "seed_trail": Clue(
        id="seed_trail",
        seen_text="sunflower seeds were scattered in a little trail right to the shed",
        wonder_text="The trail looked almost like a secret path",
        inner_line="Who carried all these seeds to the shed?",
        tags={"shed", "seeds", "curiosity"},
    ),
    "creak": Clue(
        id="creak",
        seen_text="the door gave a patient creak every few breaths",
        wonder_text="Nothing else in the yard was moving very much",
        inner_line="Why does the shed keep creaking all by itself?",
        tags={"shed", "sound", "wind"},
    ),
}

CAUSES = {
    "kitten": Cause(
        id="kitten",
        reveal_text="A dusty gray kitten blinked up from an empty flowerpot tray and let out a very proud, very tiny mew.",
        fix_text="Grandpa wrapped the kitten in an old towel, and June carried over a shallow bowl of water. In a little while they found the kitten's mother waiting by the fence, so they left the door propped open for an easy walk home.",
        ending_image="June kept looking back at the open shed door, hoping for one more tiny mew, and smiling when none came because that meant the kitten was safe",
        clues={"scratch", "seed_trail"},
        living=True,
        tags={"kitten", "animal", "care"},
    ),
    "lantern": Cause(
        id="lantern",
        reveal_text="A solar lantern had tipped off a hook and switched itself on, glowing inside an old bucket like a secret moon.",
        fix_text="June set the lantern upright and clicked it off. Grandpa showed her how the little switch could catch when something bumped it.",
        ending_image="the shed looked plain and sleepy again, with no secret moon under the door",
        clues={"glow"},
        living=False,
        tags={"lantern", "light"},
    ),
    "sparrows": Cause(
        id="sparrows",
        reveal_text="Two sparrows burst up from a torn seed bag, fluttering so fast that one feather floated right onto June's sleeve.",
        fix_text="June and Grandma tied the torn seed bag shut and sprinkled the loose seeds in the far corner of the yard instead. The sparrows hopped after them as if the whole thing had been their idea.",
        ending_image="the birds pecked at the seeds in the corner while the shed stood quiet behind them",
        clues={"seed_trail", "scratch"},
        living=True,
        tags={"bird", "animal", "seeds"},
    ),
    "wind_latch": Cause(
        id="wind_latch",
        reveal_text="The top latch was loose, and each small puff of wind nudged it against the wood with a careful little tap.",
        fix_text="Dad tightened the latch with a screwdriver while June held the screws in her palm. When he was done, the door stayed still even when the breeze passed by.",
        ending_image="only the leaves moved now, and the shed kept its own counsel without any spooky creaks",
        clues={"creak"},
        living=False,
        tags={"wind", "shed"},
    ),
}

RESPONSES = {
    "ask_adult": Response(
        id="ask_adult",
        sense=3,
        phrase="ask a grown-up to come along",
        helper=True,
        light=True,
        qa_text="asked a grown-up to come and look with her",
        tags={"adult_help"},
    ),
    "bring_flashlight": Response(
        id="bring_flashlight",
        sense=3,
        phrase="bring a flashlight and look carefully",
        helper=False,
        light=True,
        qa_text="brought a flashlight before checking the shed",
        tags={"flashlight"},
    ),
    "rush_door": Response(
        id="rush_door",
        sense=1,
        phrase="dash straight to the door without thinking",
        helper=False,
        light=False,
        qa_text="ran right to the door without thinking first",
        tags={"unsafe"},
    ),
}

CHILD_NAMES = ["June", "Nora", "Mila", "Ruby", "Ivy", "Clara", "Maisie", "Leo", "Sam", "Ben"]
CHILD_TYPES = {
    "June": "girl",
    "Nora": "girl",
    "Mila": "girl",
    "Ruby": "girl",
    "Ivy": "girl",
    "Clara": "girl",
    "Maisie": "girl",
    "Leo": "boy",
    "Sam": "boy",
    "Ben": "boy",
}
HELPERS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["curious", "careful", "dreamy"]
TIMES = ["afternoon", "dusk"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    clue: str
    cause: str
    response: str
    name: str
    child_type: str
    helper: str
    trait: str
    time: str
    seed: Optional[int] = None


# Curated set
CURATED = [
    StoryParams(
        clue="scratch",
        cause="kitten",
        response="ask_adult",
        name="June",
        child_type="girl",
        helper="grandfather",
        trait="curious",
        time="dusk",
    ),
    StoryParams(
        clue="glow",
        cause="lantern",
        response="bring_flashlight",
        name="Leo",
        child_type="boy",
        helper="father",
        trait="careful",
        time="dusk",
    ),
    StoryParams(
        clue="seed_trail",
        cause="sparrows",
        response="ask_adult",
        name="Ruby",
        child_type="girl",
        helper="grandmother",
        trait="dreamy",
        time="afternoon",
    ),
    StoryParams(
        clue="creak",
        cause="wind_latch",
        response="bring_flashlight",
        name="Sam",
        child_type="boy",
        helper="mother",
        trait="curious",
        time="afternoon",
    ),
]


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "shed": [(
        "What is a shed?",
        "A shed is a small outdoor building where people keep tools, pots, and garden things."
    )],
    "curiosity": [(
        "What is curiosity?",
        "Curiosity is the feeling that makes you want to know more. It helps people ask questions and learn."
    )],
    "kitten": [(
        "What should you do if you find a kitten alone?",
        "Stay calm and get a grown-up to help. Tiny animals need gentle hands and a safe plan."
    )],
    "bird": [(
        "Why do birds come for seeds?",
        "Seeds are food for many birds. If seeds spill, birds often hop over to peck them up."
    )],
    "lantern": [(
        "What is a lantern?",
        "A lantern is a lamp that gives light. Some lanterns use the sun to charge and can glow later."
    )],
    "wind": [(
        "Why can wind make doors creak?",
        "A breeze can push on a loose door or latch again and again. That small movement can make a creaking sound."
    )],
    "adult_help": [(
        "Why is it smart to ask a grown-up for help with a mystery?",
        "A grown-up can help you stay calm and look carefully. Small mysteries feel less scary when you solve them safely."
    )],
    "flashlight": [(
        "Why does a flashlight help in a dark place?",
        "A flashlight makes it easier to see what is really there. Good light can turn a worry into an ordinary answer."
    )],
}
KNOWLEDGE_ORDER = ["shed", "curiosity", "adult_help", "flashlight", "kitten", "bird", "lantern", "wind"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue = f["clue"]
    cause = f["cause"]
    child = f["child"]
    helper = f["helper"]
    time = f["time"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the words "ingenue" and "shed". Make the mystery begin with {clue.seen_text}.',
        f"Tell a gentle mystery story where a {child.type} named {f['child_name']} notices something odd near the shed on a {time} and follows {child.pronoun('possessive')} curiosity to a calm answer.",
        f"Write a story with inner monologue in which {helper.label_word} helps {f['child_name']} discover that the strange shed mystery is really about {cause.id.replace('_', ' ')}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    clue = f["clue"]
    cause = f["cause"]
    response = f["response"]
    name = f["child_name"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a curious child, and {helper_word} in the backyard by the shed."
        ),
        (
            "What made the mystery begin?",
            f"The mystery began when {name} noticed that {clue.seen_text} near the shed. That small, odd clue made {child.pronoun('object')} stop and wonder what could be hiding behind it."
        ),
        (
            f"What did {name} think to {child.pronoun('object')}self?",
            f"{child.pronoun().capitalize()} thought, \"{clue.inner_line}\" That inner question shows how curiosity pushed the story forward."
        ),
        (
            f"How did {name} choose to investigate?",
            f"{name} {response.qa_text}. That choice mattered because it kept the mystery gentle instead of making it bigger and scarier."
        ),
    ]
    if cause.living:
        qa.append((
            "What was really inside or around the shed?",
            f"It turned out to be {cause.id.replace('_', ' ')}. When the mystery was solved, the strange clue changed from something spooky into something alive and understandable."
        ))
        qa.append((
            f"How did {name} feel at the end?",
            f"{name} felt relieved and tender. Once {child.pronoun()} knew what the clue meant, the worry in {child.pronoun('possessive')} chest turned into a wish to help."
        ))
    else:
        qa.append((
            "What was the real answer to the mystery?",
            f"The real answer was {cause.id.replace('_', ' ')}, not anything magical or scary. The story shows how an ordinary reason can hide behind a strange sound or glow."
        ))
        qa.append((
            f"What changed for {name} by the end?",
            f"{name} stopped imagining many possibilities and understood one plain answer. Solving the mystery made the shed feel familiar again."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"shed", "curiosity"} | set(f["cause"].tags) | set(f["response"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
matches(C, K) :- cause(C), clue(K), produces(C, K).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

outcome(care) :- chosen_cause(C), living(C).
outcome(explain) :- chosen_cause(C), not living(C).

valid_story(K, C, R) :- matches(C, K), sensible(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for clue_id in sorted(cause.clues):
            lines.append(asp.fact("produces", cause_id, clue_id))
        if cause.living:
            lines.append(asp.fact("living", cause_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show matches/2."))
    return sorted((k, c) for (c, k) in asp.atoms(model, "matches"))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_cause", params.cause),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for case in cases:
        if asp_outcome(case) != outcome_of(case):
            rc = 1
            print(f"MISMATCH in outcome for {case}: asp={asp_outcome(case)} python={outcome_of(case)}")

    if rc == 0:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")

    # Smoke test ordinary generation.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child notices a small mystery by the shed and solves it calmly."
    )
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--time", choices=TIMES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible clue/cause pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.clue and args.cause:
        clue = CLUES[args.clue]
        cause = CAUSES[args.cause]
        if not clue_matches(clue, cause):
            raise StoryError(explain_combo(clue, cause))

    combos = [
        combo for combo in valid_combos()
        if (args.clue is None or combo[0] == args.clue)
        and (args.cause is None or combo[1] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid clue/cause combination matches the given options.)")

    clue_id, cause_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    name = args.name or rng.choice(CHILD_NAMES)
    child_type = args.child_type or CHILD_TYPES[name]
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    time = args.time or rng.choice(TIMES)
    return StoryParams(
        clue=clue_id,
        cause=cause_id,
        response=response_id,
        name=name,
        child_type=child_type,
        helper=helper,
        trait=trait,
        time=time,
    )


def generate(params: StoryParams) -> StorySample:
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if params.time not in TIMES:
        raise StoryError(f"(Unknown time: {params.time})")

    clue = CLUES[params.clue]
    cause = CAUSES[params.cause]
    response = RESPONSES[params.response]
    if not clue_matches(clue, cause):
        raise StoryError(explain_combo(clue, cause))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        clue=clue,
        cause=cause,
        response=response,
        child_name=params.name,
        child_type=params.child_type,
        helper_type=params.helper,
        trait=params.trait,
        time=params.time,
    )
    return StorySample(
        params=params,
        story=world.render().replace("child", params.name),
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
        print(asp_program("", "#show matches/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (clue, cause) pairs:\n")
        for clue_id, cause_id in combos:
            print(f"  {clue_id:10} {cause_id}")
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
            header = f"### {p.name}: {p.clue} at the shed ({p.cause}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
