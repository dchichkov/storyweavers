#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/coop_event_glisten_conflict_surprise_fairy_tale.py
==============================================================================

A small fairy-tale storyworld about a child, a bird from a coop, and a village
event that almost goes wrong before a cooperative fix and a gentle surprise
make it right.

Seed words / instruments
------------------------
Words: coop, event, glisten
Features: Conflict, Surprise
Style: Fairy Tale

World premise
-------------
In a little village, a child and a beloved bird keep a special festival object
in the coop. On the morning of an important event, something blocks their way.
They must solve the right kind of problem with the right kind of help. If they
choose wisely, the event begins and the ending image proves what changed: what
was stuck, muddy, or blocked becomes bright and shared.

Run it
------
python storyworlds/worlds/gpt-5.4/coop_event_glisten_conflict_surprise_fairy_tale.py
python storyworlds/worlds/gpt-5.4/coop_event_glisten_conflict_surprise_fairy_tale.py --all
python storyworlds/worlds/gpt-5.4/coop_event_glisten_conflict_surprise_fairy_tale.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/coop_event_glisten_conflict_surprise_fairy_tale.py --qa
python storyworlds/worlds/gpt-5.4/coop_event_glisten_conflict_surprise_fairy_tale.py --trace
python storyworlds/worlds/gpt-5.4/coop_event_glisten_conflict_surprise_fairy_tale.py --asp
python storyworlds/worlds/gpt-5.4/coop_event_glisten_conflict_surprise_fairy_tale.py --verify
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

# Make shared results importable when run directly from this nested directory.
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"hen", "goose", "rooster", "duck"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.label or self.type)


@dataclass
class EventCfg:
    id: str
    title: str
    place: str
    opening: str
    close: str
    accepted_prizes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class PrizeCfg:
    id: str
    label: str
    phrase: str
    shine: str
    use: str
    accepted_by: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ProblemCfg:
    id: str
    label: str
    scene: str
    risk: str
    need: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str
    phrase: str
    fixes: set[str] = field(default_factory=set)
    power: int = 0
    action: str = ""
    qa_action: str = ""
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_problem_worry(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.get("obstacle")
    if obstacle.meters["blocked"] < THRESHOLD:
        return out
    for eid in ("child", "bird"):
        sig = ("worry", eid, obstacle.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent = world.get(eid)
        ent.memes["worry"] += 1
    return out


def _r_fix_relief(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.get("obstacle")
    if obstacle.meters["cleared"] < THRESHOLD:
        return out
    for eid in ("child", "bird"):
        sig = ("relief", eid, obstacle.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent = world.get(eid)
        ent.memes["relief"] += 1
        ent.memes["worry"] = 0.0
    return out


def _r_arrival_joy(world: World) -> list[str]:
    prize = world.get("prize")
    if prize.meters["arrived"] < THRESHOLD:
        return []
    out: list[str] = []
    for eid in ("child", "bird"):
        sig = ("joy", eid, prize.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent = world.get(eid)
        ent.memes["joy"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="problem_worry", tag="emotion", apply=_r_problem_worry),
    Rule(name="fix_relief", tag="emotion", apply=_r_fix_relief),
    Rule(name="arrival_joy", tag="emotion", apply=_r_arrival_joy),
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


def prize_fits_event(event_id: str, prize_id: str) -> bool:
    return prize_id in EVENTS[event_id].accepted_prizes and event_id in PRIZES[prize_id].accepted_by


def helper_can_fix(problem_id: str, helper_id: str) -> bool:
    helper = HELPERS[helper_id]
    problem = PROBLEMS[problem_id]
    return problem_id in helper.fixes and helper.power >= problem.severity


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for event_id in EVENTS:
        for prize_id in PRIZES:
            if not prize_fits_event(event_id, prize_id):
                continue
            for problem_id in PROBLEMS:
                for helper_id in HELPERS:
                    if helper_can_fix(problem_id, helper_id):
                        combos.append((event_id, prize_id, problem_id, helper_id))
    return combos


def predict_trouble(world: World, helper_id: str) -> dict:
    sim = world.copy()
    obstacle = sim.get("obstacle")
    helper = HELPERS[helper_id]
    if helper_can_fix(sim.facts["problem"].id, helper_id):
        obstacle.meters["blocked"] = 0.0
        obstacle.meters["cleared"] += 1
    propagate(sim, narrate=False)
    return {
        "cleared": obstacle.meters["cleared"] >= THRESHOLD,
        "worry_left": sim.get("child").memes["worry"] + sim.get("bird").memes["worry"],
    }


def introduce(world: World, child: Entity, bird: Entity, event: EventCfg, prize: PrizeCfg) -> None:
    world.say(
        f"Once, at the edge of a bright little village, {child.id} hurried to the coop before sunrise. "
        f"Inside, {bird.id} the {bird.type} guarded {prize.phrase}, which would open {event.title} in {event.place}."
    )
    world.say(
        f"When the first gold light touched it, {prize.phrase} began to glisten, "
        f"and even the straw looked as if tiny stars had fallen into it."
    )


def bond(world: World, child: Entity, bird: Entity, event: EventCfg) -> None:
    child.memes["care"] += 1
    bird.memes["trust"] += 1
    world.say(
        f"{child.id} and {bird.id} had practiced for this event all week. "
        f"{bird.id} would carry the proud part, and {child.id} would carry the careful part."
    )


def present_need(world: World, prize: Entity, event: EventCfg) -> None:
    world.say(
        f"If they reached {event.place} in time, {event.opening}."
    )


def trouble_appears(world: World, child: Entity, bird: Entity, problem: ProblemCfg) -> None:
    obstacle = world.get("obstacle")
    obstacle.meters["blocked"] += 1
    child.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(problem.scene)
    world.say(
        f'"Oh no," whispered {child.id}. "{problem.risk}"'
    )
    world.say(
        f"{bird.id} gave a worried cluck, and for one uneasy moment the morning felt smaller than before."
    )


def choose_help(world: World, child: Entity, bird: Entity, helper: HelperCfg, problem: ProblemCfg) -> None:
    pred = predict_trouble(world, helper.id)
    world.facts["predicted_cleared"] = pred["cleared"]
    world.say(
        f'"Then we must help each other," said {child.id}. {child.pronoun().capitalize()} reached for {helper.phrase}, "
        f"because {problem.need}."
    )


def use_helper(world: World, child: Entity, bird: Entity, helper: HelperCfg, problem: ProblemCfg) -> None:
    obstacle = world.get("obstacle")
    helper_ent = world.add(Entity(
        id="helper",
        type="helper",
        label=helper.label,
        phrase=helper.phrase,
        tags=set(helper.tags),
    ))
    child.attrs["helper"] = helper_ent.label
    obstacle.meters["blocked"] = 0.0
    obstacle.meters["cleared"] += 1
    child.memes["cooperation"] += 1
    bird.memes["cooperation"] += 1
    propagate(world, narrate=False)
    world.say(helper.action)
    world.say(
        f"The trouble did not disappear by magic. It gave way because {child.id} and {bird.id} worked together."
    )


def arrive(world: World, child: Entity, bird: Entity, prize: Entity, event: EventCfg) -> None:
    prize.meters["arrived"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Soon they came out from the coop yard and crossed into {event.place} just as the village bells stirred."
    )
    world.say(
        f"There, under the waking sky, {prize.label} seemed to glisten even more brightly than before."
    )


def surprise(world: World, child: Entity, bird: Entity, problem: ProblemCfg, event: EventCfg) -> None:
    if problem.id == "stuck_latch":
        surprise_text = (
            f"But the finest surprise was waiting behind them: three fluffy chicks tumbled out of the coop after {bird.id}, "
            f"peeping as if they meant to join the procession. The crowd laughed with delight, and the opening looked merrier than anyone had planned."
        )
    elif problem.id == "muddy_rut":
        surprise_text = (
            f"And then came the surprise: the plank they had laid over the rut reflected the pink morning sky like a little river of glass, "
            f"so every child crossing behind them looked as if walking through light."
        )
    else:
        surprise_text = (
            f"And then came the surprise: the greedy goat that had blocked the path trotted after them quite meekly, carrying a string of paper lanterns on its back. "
            f"What had been the quarrel of the morning became the funniest sight of the whole festival."
        )
    world.say(surprise_text)
    world.say(
        f"{event.close} {child.id} bowed, {bird.id} fluffed her feathers, and the whole square felt kinder than it had at dawn."
    )


def tell(
    event: EventCfg,
    prize_cfg: PrizeCfg,
    problem: ProblemCfg,
    helper: HelperCfg,
    child_name: str = "Mira",
    child_gender: str = "girl",
    bird_name: str = "Pip",
    bird_type: str = "hen",
    elder_type: str = "mother",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    bird = world.add(Entity(id="bird", kind="character", type=bird_type, label=bird_name, role="bird"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label="the elder", role="elder"))
    coop = world.add(Entity(id="coop", type="place", label="coop", phrase="the little coop by the plum tree"))
    prize = world.add(Entity(id="prize", type="prize", label=prize_cfg.label, phrase=prize_cfg.phrase, tags=set(prize_cfg.tags)))
    obstacle = world.add(Entity(id="obstacle", type="problem", label=problem.label, tags=set(problem.tags)))

    child.id = child_name
    bird.id = bird_name
    elder.id = "Elder"

    introduce(world, child, bird, event, prize_cfg)
    bond(world, child, bird, event)
    world.say(
        f'At the cottage door, {elder.label_word.capitalize()} called, "Hurry gently, little ones. The village is waiting."'
    )
    present_need(world, prize, event)

    world.para()
    trouble_appears(world, child, bird, problem)
    choose_help(world, child, bird, helper, problem)

    world.para()
    use_helper(world, child, bird, helper, problem)
    arrive(world, child, bird, prize, event)

    world.para()
    world.say(
        f"{child.id} lifted {prize.phrase}, and {bird.id} stepped proudly beside {child.pronoun('object')}."
    )
    world.say(
        f"Together they began {event.opening.lower()}, and every face turned toward the bright beginning they had saved."
    )
    surprise(world, child, bird, problem, event)

    world.facts.update(
        event=event,
        prize_cfg=prize_cfg,
        problem=problem,
        helper=helper,
        child=child,
        bird=bird,
        elder=elder,
        coop=coop,
        prize=prize,
        obstacle=obstacle,
        success=prize.meters["arrived"] >= THRESHOLD and obstacle.meters["cleared"] >= THRESHOLD,
    )
    return world


EVENTS = {
    "lantern_walk": EventCfg(
        id="lantern_walk",
        title="the Lantern Walk",
        place="the cobbled square",
        opening="the first lanterns could be lifted high",
        close="So the Lantern Walk began with song instead of sighs.",
        accepted_prizes={"silver_bell", "star_ribbon"},
        tags={"event", "lantern"},
    ),
    "sunrise_feast": EventCfg(
        id="sunrise_feast",
        title="the Sunrise Feast",
        place="the green by the well",
        opening="the feast table could be blessed and the loaves shared",
        close="So the Sunrise Feast began with warm bread and warmer smiles.",
        accepted_prizes={"golden_egg", "silver_bell"},
        tags={"event", "feast"},
    ),
    "wishing_fair": EventCfg(
        id="wishing_fair",
        title="the Wishing Fair",
        place="the willow market",
        opening="the children could hang their wishes and clap for luck",
        close="So the Wishing Fair began with hopeful hands and shining eyes.",
        accepted_prizes={"star_ribbon", "golden_egg"},
        tags={"event", "fair"},
    ),
}

PRIZES = {
    "silver_bell": PrizeCfg(
        id="silver_bell",
        label="the silver bell",
        phrase="the silver bell with a blue cord",
        shine="silver",
        use="ring to open the day",
        accepted_by={"lantern_walk", "sunrise_feast"},
        tags={"bell", "glisten"},
    ),
    "golden_egg": PrizeCfg(
        id="golden_egg",
        label="the golden egg",
        phrase="the golden egg painted with tiny leaves",
        shine="gold",
        use="set at the center of the table",
        accepted_by={"sunrise_feast", "wishing_fair"},
        tags={"egg", "glisten"},
    ),
    "star_ribbon": PrizeCfg(
        id="star_ribbon",
        label="the star ribbon",
        phrase="the star ribbon sewn with little silver threads",
        shine="silver",
        use="tie above the crowd",
        accepted_by={"lantern_walk", "wishing_fair"},
        tags={"ribbon", "glisten"},
    ),
}

PROBLEMS = {
    "stuck_latch": ProblemCfg(
        id="stuck_latch",
        label="the stuck latch",
        scene="But when they reached the coop door, the old wooden latch would not lift. It held fast as if the night itself still wanted to keep them in.",
        risk="The coop door is stuck. We may miss the opening if we stay here.",
        need="a slippery little bit of oil could persuade a stubborn latch",
        severity=1,
        tags={"latch"},
    ),
    "muddy_rut": ProblemCfg(
        id="muddy_rut",
        label="the muddy rut",
        scene="But beyond the gate, last night's rain had made a muddy rut as wide as a cart wheel. One wrong step, and the precious thing from the coop would sink into the brown mess.",
        risk="If we slip there, the festival treasure could be spoiled.",
        need="a firm path must be made before careful feet could pass",
        severity=2,
        tags={"mud"},
    ),
    "goat_block": ProblemCfg(
        id="goat_block",
        label="the goat in the path",
        scene="But on the narrow lane stood the miller's goat, chewing and staring and refusing to let anyone pass. It planted its hooves as if it meant to be the grandest creature at the event.",
        risk="That goat will not move, and the whole village is waiting beyond her.",
        need="a tempting treat might turn stubborn hooves into willing ones",
        severity=2,
        tags={"goat"},
    ),
}

HELPERS = {
    "oil_flask": HelperCfg(
        id="oil_flask",
        label="oil flask",
        phrase="a tiny oil flask from the windowsill",
        fixes={"stuck_latch"},
        power=1,
        action="Mira tipped the oil flask carefully while Pip pecked the latch from the other side. With a small creak and a bright little pop, the latch let go.",
        qa_action="used a small oil flask to loosen the stuck latch",
        tags={"oil"},
    ),
    "oak_plank": HelperCfg(
        id="oak_plank",
        label="oak plank",
        phrase="the old oak plank by the fence",
        fixes={"muddy_rut"},
        power=2,
        action="They dragged the oak plank together, one pushing and one tugging, until it lay straight across the mud. Pip tested it with one neat step, and then the safe way was ready.",
        qa_action="laid an oak plank across the muddy rut",
        tags={"plank"},
    ),
    "cabbage_leaf": HelperCfg(
        id="cabbage_leaf",
        label="cabbage leaf",
        phrase="a sweet cabbage leaf from the garden basket",
        fixes={"goat_block"},
        power=2,
        action="Mira held out the cabbage leaf while Pip fluttered and clucked toward the hedge. The goat forgot all about blocking the lane and trotted after the treat at once.",
        qa_action="used a cabbage leaf to coax the goat out of the lane",
        tags={"cabbage"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Asha", "Nora", "Talia", "Elsa", "Runa", "Pia"]
BOY_NAMES = ["Oren", "Tobin", "Milo", "Finn", "Evan", "Rafi", "Nico", "Hugo"]
BIRD_NAMES = ["Pip", "Daisy", "Pearl", "Clover", "Dot", "Sunny", "Poppy"]
TRAITLESS_BIRDS = ["hen", "duck"]
PARENT_TYPES = ["mother", "father"]


@dataclass
class StoryParams:
    event: str
    prize: str
    problem: str
    helper: str
    child_name: str
    child_gender: str
    bird_name: str
    bird_type: str
    elder_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        event="lantern_walk",
        prize="silver_bell",
        problem="stuck_latch",
        helper="oil_flask",
        child_name="Mira",
        child_gender="girl",
        bird_name="Pip",
        bird_type="hen",
        elder_type="mother",
    ),
    StoryParams(
        event="sunrise_feast",
        prize="golden_egg",
        problem="muddy_rut",
        helper="oak_plank",
        child_name="Oren",
        child_gender="boy",
        bird_name="Pearl",
        bird_type="hen",
        elder_type="father",
    ),
    StoryParams(
        event="wishing_fair",
        prize="star_ribbon",
        problem="goat_block",
        helper="cabbage_leaf",
        child_name="Lina",
        child_gender="girl",
        bird_name="Clover",
        bird_type="hen",
        elder_type="mother",
    ),
]


KNOWLEDGE = {
    "coop": [
        (
            "What is a coop?",
            "A coop is a little house or pen where chickens live. It keeps them safe and gives them a place to sleep and lay eggs.",
        )
    ],
    "bell": [
        (
            "Why does a bell make a good beginning for an event?",
            "A bell is loud and clear, so many people can hear it at once. That makes it a good signal that something special is starting.",
        )
    ],
    "egg": [
        (
            "Why are eggs often treated gently?",
            "Eggs have thin shells that can crack easily. That is why people carry them carefully and keep them away from mud and bumps.",
        )
    ],
    "ribbon": [
        (
            "What is a ribbon?",
            "A ribbon is a soft strip of cloth used for tying or decorating things. When it is shiny, it can flutter and catch the light beautifully.",
        )
    ],
    "mud": [
        (
            "Why is mud slippery?",
            "Mud is wet earth, so shoes and feet can slide on it. That makes walking with something precious much harder.",
        )
    ],
    "plank": [
        (
            "What does a plank do over mud?",
            "A plank can make a firm path across a soft place. It spreads your weight and gives your feet a drier surface to step on.",
        )
    ],
    "oil": [
        (
            "Why can a little oil help a stuck latch?",
            "Oil can make two rubbing pieces slide more easily. That is why a tiny bit sometimes helps a stiff latch move again.",
        )
    ],
    "goat": [
        (
            "Why might a goat follow a leaf?",
            "Goats are curious and often like to nibble tasty plants. A tempting leaf can draw a goat away from where it was standing.",
        )
    ],
    "event": [
        (
            "What is an event?",
            "An event is a special happening that people gather for, like a fair, a feast, or a parade. It usually has a beginning everyone notices together.",
        )
    ],
}
KNOWLEDGE_ORDER = ["coop", "event", "bell", "egg", "ribbon", "mud", "plank", "oil", "goat"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    event = f["event"]
    problem = f["problem"]
    prize = f["prize_cfg"]
    child = f["child"]
    bird = f["bird"]
    return [
        f'Write a fairy tale for a young child that includes the words "coop", "event", and "glisten".',
        f"Tell a gentle fairy tale where {child.id} and {bird.id} must carry {prize.phrase} from a coop to {event.title}, but {problem.label} causes a conflict first.",
        f"Write a story with a small surprise ending in which a child and a helpful bird save a village event by working together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    bird = f["bird"]
    event = f["event"]
    prize_cfg = f["prize_cfg"]
    problem = f["problem"]
    helper = f["helper"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {bird.id} the {bird.type}, and the village waiting for {event.title}. {child.id} and {bird.id} had to carry {prize_cfg.phrase} from the coop.",
        ),
        (
            f"What special thing were they bringing to the event?",
            f"They were bringing {prize_cfg.phrase}. It mattered because it would help open {event.title}.",
        ),
        (
            "What was the conflict in the story?",
            f"The conflict was {problem.label}. {problem.risk[0].upper()}{problem.risk[1:]}",
        ),
        (
            f"How did {child.id} and {bird.id} solve the problem?",
            f"They {helper.qa_action}. The trouble changed because they cooperated instead of giving up.",
        ),
        (
            "Why did the object glisten?",
            f"It glistened when the early light touched it. That shining look made the festival object feel magical and important.",
        ),
    ]
    if problem.id == "stuck_latch":
        qa.append(
            (
                "What was the surprise at the end?",
                "Three fluffy chicks came out after the hen and joined the procession. The villagers had expected a simple opening, so the tiny parade felt like a happy surprise.",
            )
        )
    elif problem.id == "muddy_rut":
        qa.append(
            (
                "What was the surprise at the end?",
                "The plank over the mud reflected the pink sky like glass. That made the path itself look magical, so the rescue became part of the beauty of the morning.",
            )
        )
    else:
        qa.append(
            (
                "What was the surprise at the end?",
                "The goat that caused the trouble ended up following along with lanterns on its back. What had begun as a quarrel turned into the funniest part of the fair.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"coop", "event"}
    prize_id = f["prize_cfg"].id
    problem_id = f["problem"].id
    helper_id = f["helper"].id
    if prize_id == "silver_bell":
        tags.add("bell")
    elif prize_id == "golden_egg":
        tags.add("egg")
    else:
        tags.add("ribbon")
    if problem_id == "muddy_rut":
        tags.add("mud")
    if helper_id == "oak_plank":
        tags.add("plank")
    if helper_id == "oil_flask":
        tags.add("oil")
    if problem_id == "goat_block":
        tags.add("goat")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(event_id: str, prize_id: str, problem_id: str, helper_id: str) -> str:
    if not prize_fits_event(event_id, prize_id):
        return (
            f"(No story: {PRIZES[prize_id].label} does not fit {EVENTS[event_id].title}. "
            f"That event needs the right kind of opening treasure.)"
        )
    if problem_id not in HELPERS[helper_id].fixes:
        return (
            f"(No story: {HELPERS[helper_id].label} does not solve {PROBLEMS[problem_id].label}. "
            f"Choose help that matches the problem.)"
        )
    if HELPERS[helper_id].power < PROBLEMS[problem_id].severity:
        return (
            f"(No story: {HELPERS[helper_id].label} is too weak for {PROBLEMS[problem_id].label}. "
            f"The fix must be strong enough to clear the way.)"
        )
    return "(No story: this combination does not make sense in this world.)"


ASP_RULES = r"""
fits_event(E, P) :- event(E), prize(P), event_accepts(E, P), prize_accepts(P, E).
fixes_problem(H, Pr) :- helper(H), problem(Pr), can_fix(H, Pr), power(H, HP), severity(Pr, PS), HP >= PS.
valid(E, P, Pr, H) :- fits_event(E, P), fixes_problem(H, Pr).

chosen_valid :- chosen_event(E), chosen_prize(P), chosen_problem(Pr), chosen_helper(H), valid(E, P, Pr, H).
#show valid/4.
#show chosen_valid/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for event_id, event in EVENTS.items():
        lines.append(asp.fact("event", event_id))
        for prize_id in sorted(event.accepted_prizes):
            lines.append(asp.fact("event_accepts", event_id, prize_id))
    for prize_id, prize in PRIZES.items():
        lines.append(asp.fact("prize", prize_id))
        for event_id in sorted(prize.accepted_by):
            lines.append(asp.fact("prize_accepts", prize_id, event_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("severity", problem_id, problem.severity))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("power", helper_id, helper.power))
        for problem_id in sorted(helper.fixes):
            lines.append(asp.fact("can_fix", helper_id, problem_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_is_valid(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_event", params.event),
            asp.fact("chosen_prize", params.prize),
            asp.fact("chosen_problem", params.problem),
            asp.fact("chosen_helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(extra=extra, show="#show chosen_valid/0."))
    return bool(asp.atoms(model, "chosen_valid"))


def smoke_check() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    if "{" in sample.story or "}" in sample.story:
        raise StoryError("Smoke test failed: unresolved braces in story.")
    if "coop" not in sample.story.lower() or "glisten" not in sample.story.lower():
        raise StoryError("Smoke test failed: required seed words missing from story text.")


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    for params in CURATED:
        if not asp_is_valid(params):
            rc = 1
            print(f"MISMATCH: curated params rejected by ASP: {params}")
    try:
        smoke_check()
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    try:
        p = resolve_params(build_parser().parse_args([]), random.Random(123))
        s = generate(p)
        if not s.story.strip():
            raise StoryError("random generate produced empty story")
        print("OK: random generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"RANDOM GENERATION FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a child and a coop bird save a village event with the right help."
    )
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--bird-name")
    ap.add_argument("--elder-type", choices=PARENT_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if all(v is not None for v in (args.event, args.prize, args.problem, args.helper)):
        if not prize_fits_event(args.event, args.prize) or not helper_can_fix(args.problem, args.helper):
            raise StoryError(explain_rejection(args.event, args.prize, args.problem, args.helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.event is None or combo[0] == args.event)
        and (args.prize is None or combo[1] == args.prize)
        and (args.problem is None or combo[2] == args.problem)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        e = args.event or next(iter(EVENTS))
        p = args.prize or next(iter(PRIZES))
        pr = args.problem or next(iter(PROBLEMS))
        h = args.helper or next(iter(HELPERS))
        raise StoryError(explain_rejection(e, p, pr, h))

    event_id, prize_id, problem_id, helper_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    bird_name = args.bird_name or rng.choice(BIRD_NAMES)
    elder_type = args.elder_type or rng.choice(PARENT_TYPES)
    return StoryParams(
        event=event_id,
        prize=prize_id,
        problem=problem_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=child_gender,
        bird_name=bird_name,
        bird_type="hen",
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        event = EVENTS[params.event]
        prize = PRIZES[params.prize]
        problem = PROBLEMS[params.problem]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(No story: unknown parameter {err!s}.)") from err
    if not prize_fits_event(params.event, params.prize) or not helper_can_fix(params.problem, params.helper):
        raise StoryError(explain_rejection(params.event, params.prize, params.problem, params.helper))

    world = tell(
        event=event,
        prize_cfg=prize,
        problem=problem,
        helper=helper,
        child_name=params.child_name,
        child_gender=params.child_gender,
        bird_name=params.bird_name,
        bird_type=params.bird_type,
        elder_type=params.elder_type,
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
        print(asp_program(show="#show valid/4.\n#show chosen_valid/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (event, prize, problem, helper) combos:\n")
        for event_id, prize_id, problem_id, helper_id in combos:
            print(f"  {event_id:13} {prize_id:12} {problem_id:12} {helper_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.event}: {p.prize}, {p.problem}, {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
