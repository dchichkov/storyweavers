#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bellow_bobble_mop_inner_monologue_twist_humor.py
============================================================================

A small comedic storyworld about a child in a bobble hat who spills something,
grabs a mop, hears a great bellow, and fears the worst -- only to discover the
loud voice had a funny, harmless cause.

The simulation tracks a physical mess on the floor and emotional changes in the
child. The middle turn is driven by state: the spill makes the floor slippery,
the child worries, the mop only partly solves bigger spills alone, and a helper
must be reasonable for the chosen mess. The twist is grounded too: the bellow
really comes from a nearby rehearsal or warm-up, not from an angry grown-up.

Run it
------
    python storyworlds/worlds/gpt-5.4/bellow_bobble_mop_inner_monologue_twist_humor.py
    python storyworlds/worlds/gpt-5.4/bellow_bobble_mop_inner_monologue_twist_humor.py --place cafeteria --spill soup --helper cook
    python storyworlds/worlds/gpt-5.4/bellow_bobble_mop_inner_monologue_twist_humor.py --spill glitter
    python storyworlds/worlds/gpt-5.4/bellow_bobble_mop_inner_monologue_twist_humor.py --all
    python storyworlds/worlds/gpt-5.4/bellow_bobble_mop_inner_monologue_twist_humor.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bellow_bobble_mop_inner_monologue_twist_humor.py --verify
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
# from storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing | room
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "teacher_woman", "cook_woman", "janitor_woman"}
        male = {"boy", "man", "father", "teacher_man", "cook_man", "janitor_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        lookup = {
            "teacher_woman": "teacher",
            "teacher_man": "teacher",
            "cook_woman": "cook",
            "cook_man": "cook",
            "janitor_woman": "janitor",
            "janitor_man": "janitor",
        }
        return lookup.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    detail: str
    spills: set[str] = field(default_factory=set)
    noises: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Spill:
    id: str
    label: str
    phrase: str
    color: str
    severity: int
    sticky: bool = False
    moppable: bool = True
    splash: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    type: str
    label: str
    phrase: str
    power: int
    tool: str
    praise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Noise:
    id: str
    source: str
    bellow_line: str
    reveal: str
    funny_end: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spread_spill(world: World) -> list[str]:
    out: list[str] = []
    puddle = world.get("spill")
    floor = world.get("floor")
    child = world.get("child")
    if puddle.meters["present"] >= THRESHOLD and ("spread",) not in world.fired:
        world.fired.add(("spread",))
        floor.meters["wet"] += 1
        floor.meters["slippery"] += 1
        child.memes["worry"] += 1
        if puddle.attrs.get("sticky"):
            floor.meters["sticky"] += 1
        out.append("__spill__")
    return out


def _r_child_mop(world: World) -> list[str]:
    out: list[str] = []
    puddle = world.get("spill")
    floor = world.get("floor")
    child = world.get("child")
    if child.meters["mopping"] < THRESHOLD:
        return out
    if ("child_mop",) in world.fired:
        return out
    world.fired.add(("child_mop",))
    if puddle.meters["present"] >= THRESHOLD:
        puddle.meters["present"] = max(0.0, puddle.meters["present"] - 1.0)
        floor.meters["wet"] = max(0.0, floor.meters["wet"] - 0.5)
        floor.meters["slippery"] = max(0.0, floor.meters["slippery"] - 0.5)
        child.memes["hope"] += 1
        if puddle.meters["severity"] > 1:
            child.memes["worry"] += 1
            out.append("__partial__")
        else:
            floor.meters["clean"] += 1
            out.append("__clean__")
    return out


def _r_helper_finish(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    puddle = world.get("spill")
    floor = world.get("floor")
    child = world.get("child")
    if helper.meters["helping"] < THRESHOLD:
        return out
    if ("helper_finish",) in world.fired:
        return out
    world.fired.add(("helper_finish",))
    puddle.meters["present"] = 0.0
    floor.meters["wet"] = 0.0
    floor.meters["slippery"] = 0.0
    floor.meters["sticky"] = 0.0
    floor.meters["clean"] += 1
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    child.memes["worry"] = 0.0
    out.append("__fixed__")
    return out


def _r_hear_bellow(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["heard_bellow"] < THRESHOLD:
        return []
    if ("heard_bellow",) in world.fired:
        return []
    world.fired.add(("heard_bellow",))
    child.memes["worry"] += 1
    child.memes["imagination"] += 1
    return ["__bellow__"]


def _r_reveal(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["truth_known"] < THRESHOLD:
        return []
    if ("truth_known",) in world.fired:
        return []
    world.fired.add(("truth_known",))
    child.memes["relief"] += 1
    child.memes["laughter"] += 1
    child.memes["worry"] = 0.0
    return ["__reveal__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="spread_spill", tag="physical", apply=_r_spread_spill),
    Rule(name="child_mop", tag="physical", apply=_r_child_mop),
    Rule(name="helper_finish", tag="physical", apply=_r_helper_finish),
    Rule(name="hear_bellow", tag="social", apply=_r_hear_bellow),
    Rule(name="reveal", tag="social", apply=_r_reveal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            result = rule.apply(world)
            if result:
                changed = True
                produced.extend(result)
    return produced


PLACES = {
    "hallway": Place(
        id="hallway",
        label="the school hallway",
        detail="Sunlight made bright stripes on the floor outside the classroom doors.",
        spills={"juice"},
        noises={"dragon", "opera"},
        tags={"school"},
    ),
    "cafeteria": Place(
        id="cafeteria",
        label="the cafeteria",
        detail="Lunch trays clicked softly, and the long floor looked much too shiny for accidents.",
        spills={"juice", "soup"},
        noises={"dragon", "megaphone"},
        tags={"school", "lunch"},
    ),
    "art_room": Place(
        id="art_room",
        label="the art room",
        detail="Paint jars lined the counter like little rainbow soldiers.",
        spills={"paint_water"},
        noises={"opera", "megaphone"},
        tags={"school", "art"},
    ),
}

SPILLS = {
    "juice": Spill(
        id="juice",
        label="juice",
        phrase="a cup of orange juice",
        color="orange",
        severity=1,
        sticky=True,
        splash="It made a bright little river race across the tiles.",
        tags={"juice", "spill"},
    ),
    "soup": Spill(
        id="soup",
        label="soup",
        phrase="a bowl of tomato soup",
        color="red",
        severity=2,
        sticky=True,
        splash="It spread in a warm red loop that looked far too proud of itself.",
        tags={"soup", "spill"},
    ),
    "paint_water": Spill(
        id="paint_water",
        label="paint water",
        phrase="a jar of cloudy blue paint water",
        color="blue",
        severity=2,
        sticky=False,
        splash="It swirled into a blue puddle that looked like a tiny storm cloud on the floor.",
        tags={"paint", "spill"},
    ),
    "glitter": Spill(
        id="glitter",
        label="glitter",
        phrase="a tub of silver glitter",
        color="silver",
        severity=1,
        sticky=False,
        moppable=False,
        splash="The glitter skittered everywhere at once.",
        tags={"glitter", "spill"},
    ),
}

HELPERS = {
    "teacher": Helper(
        id="teacher",
        type="teacher_woman",
        label="teacher",
        phrase="Ms. June, the teacher",
        power=1,
        tool="paper towels",
        praise="That was honest and helpful.",
        tags={"teacher"},
    ),
    "cook": Helper(
        id="cook",
        type="cook_man",
        label="cook",
        phrase="Mr. Pip, the cook",
        power=2,
        tool="a giant dry cloth",
        praise="Good eyes. A slippery floor is sneaky.",
        tags={"cook", "kitchen"},
    ),
    "janitor": Helper(
        id="janitor",
        type="janitor_man",
        label="janitor",
        phrase="Mr. Bell, the janitor",
        power=3,
        tool="an extra mop and a wobbling yellow caution sign",
        praise="You saw a mess and got to work before anyone fell.",
        tags={"janitor", "cleaning"},
    ),
}

NOISES = {
    "dragon": Noise(
        id="dragon",
        source="the auditorium",
        bellow_line='"BELLOW LIKE A DRAGON, NOT LIKE A SLEEPY DUCK!"',
        reveal="the drama teacher was coaching the school play, and three children in cardboard scales were roaring with all their might",
        funny_end="One dragon sneezed in the middle of the roar and made everybody laugh harder.",
        tags={"play", "dragon", "bellow"},
    ),
    "opera": Noise(
        id="opera",
        source="the music room",
        bellow_line='"BELLOW FROM YOUR TOES!"',
        reveal="the music teacher was leading a silly warm-up, and the older kids were trying to sing like enormous opera bears",
        funny_end="The deepest note made a stack of paper stars tremble on the wall.",
        tags={"music", "bellow"},
    ),
    "megaphone": Noise(
        id="megaphone",
        source="the gym",
        bellow_line='"WHO TOOK MY MEGAPHONE TEST VOICE ALL THE WAY TO TEN?"',
        reveal="the coach was laughing because the megaphone had turned a normal sentence into a giant booming honk",
        funny_end="When the coach tapped it again, it squeaked like a startled rubber chicken.",
        tags={"gym", "bellow"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Theo", "Noah", "Eli", "Sam"]
TRAITS = ["careful", "busy", "cheerful", "curious", "earnest", "bouncy"]


@dataclass
class StoryParams:
    place: str
    spill: str
    helper: str
    noise: str
    child_name: str
    child_gender: str
    trait: str
    seed: Optional[int] = None


def helper_can_fix(spill: Spill, helper: Helper) -> bool:
    return spill.moppable and helper.power >= spill.severity


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for spill_id in sorted(place.spills):
            spill = SPILLS[spill_id]
            for helper_id, helper in HELPERS.items():
                if not helper_can_fix(spill, helper):
                    continue
                for noise_id in sorted(place.noises):
                    combos.append((place_id, spill_id, helper_id, noise_id))
    return combos


def explain_rejection(place: Optional[Place], spill: Spill, helper: Optional[Helper], noise: Optional[Noise]) -> str:
    if not spill.moppable:
        return (
            f"(No story: {spill.label} does not make a tidy mop-and-puddle problem. "
            f"A mop helps with liquid spills like juice, soup, or paint water, not loose glitter.)"
        )
    if helper is not None and helper.power < spill.severity:
        return (
            f"(No story: {helper.label.title()} is too lightly equipped for {spill.label}. "
            f"That spill is bigger than this helper can reasonably finish.)"
        )
    if place is not None and spill.id not in place.spills:
        return (
            f"(No story: {spill.label} is not a natural spill for {place.label}. "
            f"Pick a spill that fits the setting.)"
        )
    if place is not None and noise is not None and noise.id not in place.noises:
        return (
            f"(No story: the funny bellow from {noise.source} does not fit nearby in {place.label}. "
            f"Pick a noise that belongs near this place.)"
        )
    return "(No story: this combination does not fit the world.)"


def introduce(world: World, child: Entity, spill: Spill) -> None:
    world.say(
        f"{child.id} hurried through {world.place.label} in a wool hat with a round bobble on top. "
        f"Every quick step made the bobble bounce like it was trying to keep its own schedule."
    )
    world.say(world.place.detail)
    world.say(
        f"{child.pronoun().capitalize()} was supposed to carry {spill.phrase} carefully, "
        f"which felt simple for exactly three steps."
    )


def accident(world: World, child: Entity, spill_cfg: Spill) -> None:
    spill = world.get("spill")
    spill.meters["present"] = float(spill_cfg.severity)
    spill.meters["severity"] = float(spill_cfg.severity)
    spill.attrs["sticky"] = spill_cfg.sticky
    propagate(world, narrate=False)
    world.say(
        f"Then {child.pronoun('possessive')} shoe kissed a crooked tile, the cup tipped, and "
        f"{spill_cfg.phrase} splashed down. {spill_cfg.splash}"
    )
    if world.get("floor").meters["slippery"] >= THRESHOLD:
        world.say("At once, the floor looked glossy and slippery.")
    if spill_cfg.sticky:
        world.say("It was the kind of mess that tried to cling to everything.")


def inner_monologue(world: World, child: Entity, helper: Helper) -> None:
    worry = world.get("child").memes["worry"]
    line = (
        f"{child.id} froze. Inside {child.pronoun('possessive')} head, a tiny voice began to sprint. "
        f'"Oh no. That puddle is growing. If {helper.phrase} sees this, maybe {child.pronoun("subject")} '
        f'will bellow my whole name. Maybe I will have to live here forever as a mop person."'
    )
    if worry >= 2:
        line += f" {child.pronoun().capitalize()} imagined the bobble on the hat drooping with shame."
    world.say(line)


def start_mopping(world: World, child: Entity) -> None:
    child.meters["mopping"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But standing still would not dry anything, so {child.id} grabbed a mop from the closet and pushed it in brave little zigzags."
    )
    if world.get("spill").meters["present"] > 0:
        world.say(
            f"The mop helped, but the spill still gleamed back as if it had opinions."
        )
    else:
        world.say("The mop swept the puddle away in one tidy swish.")


def hear_noise(world: World, child: Entity, noise: Noise) -> None:
    child.meters["heard_bellow"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just then, from {noise.source}, a huge voice burst out: {noise.bellow_line}"
    )
    world.say(
        f"{child.id}'s hands stopped on the mop handle. "
        f'"That is it," {child.pronoun()} thought. "The universe has started shouting."'
    )


def call_helper(world: World, child: Entity, helper_ent: Entity, helper_cfg: Helper, spill_cfg: Spill) -> None:
    helper_ent.meters["helping"] += 1
    propagate(world, narrate=False)
    if spill_cfg.severity > 1:
        world.say(
            f"{child.id} took a breath, lifted a sticky hand, and called, "
            f'"I spilled something big, and I started mopping, but I need help!"'
        )
        world.say(
            f"{helper_cfg.phrase} came over with {helper_cfg.tool}. Together they worked from the outside of the puddle toward the middle."
        )
    else:
        world.say(
            f"{helper_cfg.phrase} stepped over, saw the mop, and nodded. "
            f'"Good catch," {helper_ent.pronoun()} said, taking {helper_cfg.tool}.'
        )


def reveal_twist(world: World, child: Entity, helper_ent: Entity, helper_cfg: Helper, noise: Noise) -> None:
    child.meters["truth_known"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then they both glanced toward {noise.source} and saw the truth: {noise.reveal}."
    )
    world.say(
        f"So the great bellow had nothing to do with the spill at all. {noise.funny_end}"
    )
    world.say(
        f"{helper_ent.pronoun().capitalize()} smiled at {child.id} and said, "
        f'"{helper_cfg.praise}"'
    )


def ending(world: World, child: Entity) -> None:
    floor = world.get("floor")
    child_state = world.get("child")
    if floor.meters["clean"] >= THRESHOLD:
        world.say(
            f"Soon the floor shone safely again, and {child.id}'s bobble began to bounce for happy reasons instead of worried ones."
        )
    world.say(
        f"{child.id} gave the mop one last proud push and decided that being honest felt much better than being secretly dramatic."
    )
    if child_state.memes["laughter"] >= THRESHOLD:
        world.say(
            f"On the way back, {child.pronoun()} tried a tiny dragon bellow of {child.pronoun('possessive')} own. "
            f"It came out more like a squeaky goose, which made {child.pronoun('object')} laugh all over again."
        )


def tell(
    place: Place,
    spill_cfg: Spill,
    helper_cfg: Helper,
    noise_cfg: Noise,
    child_name: str = "Lily",
    child_gender: str = "girl",
    trait: str = "careful",
) -> World:
    world = World(place)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="child",
        attrs={"display": child_name, "trait": trait},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        role="helper",
    ))
    floor = world.add(Entity(id="floor", kind="room", type="floor", label="floor"))
    spill = world.add(Entity(id="spill", kind="thing", type="spill", label=spill_cfg.label))
    world.add(Entity(id="mop", kind="thing", type="tool", label="mop"))
    world.add(Entity(id="hat", kind="thing", type="hat", label="bobble hat"))

    # Human-readable names for prose and QA.
    child.attrs["name"] = child_name
    helper.attrs["name"] = helper_cfg.phrase

    introduce(world, child, spill_cfg)

    world.para()
    accident(world, child, spill_cfg)
    inner_monologue(world, child, helper_cfg)

    world.para()
    start_mopping(world, child)
    hear_noise(world, child, noise_cfg)
    call_helper(world, child, helper, helper_cfg, spill_cfg)

    world.para()
    reveal_twist(world, child, helper, helper_cfg, noise_cfg)
    ending(world, child)

    world.facts.update(
        place=place,
        spill_cfg=spill_cfg,
        helper_cfg=helper_cfg,
        noise_cfg=noise_cfg,
        child=child,
        helper=helper,
        floor=floor,
        spill=spill,
        resolved=floor.meters["clean"] >= THRESHOLD,
        asked_for_help=helper.meters["helping"] >= THRESHOLD,
        heard_bellow=child.meters["heard_bellow"] >= THRESHOLD,
        twist_known=child.meters["truth_known"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    spill = f["spill_cfg"]
    helper = f["helper_cfg"]
    noise = f["noise_cfg"]
    place = f["place"]
    name = child.attrs.get("name", child.label)
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "bellow", "bobble", and "mop".',
        f"Tell a comedy story set in {place.label} where a child named {name} spills {spill.label}, worries in an inner monologue, and then discovers a loud bellow from {noise.source} was not about the mess at all.",
        f"Write a short twist story where {name} tries to clean up with a mop, expects {helper.label} trouble, and ends by laughing instead.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    spill_cfg = f["spill_cfg"]
    place = f["place"]
    noise = f["noise_cfg"]
    floor = f["floor"]
    name = child.attrs.get("name", child.label)
    helper_name = helper.phrase
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a child in a bobble hat, and {helper_name}. The story begins when {name} spills {spill_cfg.label} in {place.label}.",
        ),
        (
            f"What problem did {name} have?",
            f"{name} accidentally spilled {spill_cfg.phrase}, which made the floor slippery. That is why {name} grabbed the mop instead of walking away.",
        ),
        (
            f"What was {name} thinking when the mess happened?",
            f"{name} had a worried inner monologue and imagined terrible trouble. {child.pronoun().capitalize()} thought the loud grown-up bellow might be about the spill, which made the mess feel even bigger.",
        ),
        (
            "Why did the mop not solve everything at once?",
            (
                f"The mop helped right away, but {spill_cfg.label} was still on the floor for a while."
                if spill_cfg.severity == 1
                else f"The spill was big enough that the first mopping only partly fixed it. {name} needed help to make the floor fully safe again."
            ),
        ),
        (
            "What was the twist?",
            f"The big bellow was not angry at {name} at all. It came from {noise.source}, where {noise.reveal}.",
        ),
        (
            f"How did the story end?",
            f"The floor ended up clean, and {name} felt relieved and proud. The ending proves what changed because the bobble on the hat bounced for happy reasons, not worried ones.",
        ),
    ]
    if floor.meters["clean"] >= THRESHOLD and helper.meters["helping"] >= THRESHOLD:
        qa.append(
            (
                f"How did {helper_name} help?",
                f"{helper_name} finished the cleanup with {f['helper_cfg'].tool}. The help mattered because a slippery floor can make someone fall.",
            )
        )
    return qa


KNOWLEDGE = {
    "spill": [
        (
            "Why should you clean up a spill quickly?",
            "A spill can make the floor slippery, so someone might slip and fall. Cleaning it quickly helps keep everybody safe.",
        )
    ],
    "mop": [
        (
            "What is a mop for?",
            "A mop is a cleaning tool you push across the floor to soak up liquid and dirt. It helps make a wet floor dry and safe again.",
        )
    ],
    "bellow": [
        (
            "What does bellow mean?",
            "Bellow means to shout in a very loud, booming way. People can bellow because they are acting, calling out, or being silly, not only because they are angry.",
        )
    ],
    "bobble": [
        (
            "What is a bobble on a hat?",
            "A bobble is the round fluffy ball on top of some hats. It jiggles and bounces when you move.",
        )
    ],
    "honesty": [
        (
            "Why is it good to tell a grown-up about a mess?",
            "Telling the truth helps the right person fix the problem quickly. It also means you do not have to stay worried all by yourself.",
        )
    ],
    "play": [
        (
            "Why can loud rehearsal sounds be surprising?",
            "Rehearsals can sound huge because people practice big voices for songs or plays. A loud sound can seem scary until you know what it is for.",
        )
    ],
}
KNOWLEDGE_ORDER = ["spill", "mop", "bellow", "bobble", "honesty", "play"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"spill", "mop", "bellow", "bobble", "honesty"}
    tags |= set(world.facts["noise_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for (name, *_) in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="hallway",
        spill="juice",
        helper="teacher",
        noise="dragon",
        child_name="Lily",
        child_gender="girl",
        trait="careful",
    ),
    StoryParams(
        place="cafeteria",
        spill="soup",
        helper="cook",
        noise="megaphone",
        child_name="Ben",
        child_gender="boy",
        trait="earnest",
    ),
    StoryParams(
        place="art_room",
        spill="paint_water",
        helper="janitor",
        noise="opera",
        child_name="Mia",
        child_gender="girl",
        trait="curious",
    ),
    StoryParams(
        place="cafeteria",
        spill="juice",
        helper="janitor",
        noise="dragon",
        child_name="Theo",
        child_gender="boy",
        trait="bouncy",
    ),
]


ASP_RULES = r"""
mop_problem(P, S, H, N) :- place(P), spill(S), helper(H), noise(N),
                           allows_spill(P, S), nearby_noise(P, N),
                           moppable(S), severity(S, V), power(H, Pw), Pw >= V.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for spill_id in sorted(place.spills):
            lines.append(asp.fact("allows_spill", place_id, spill_id))
        for noise_id in sorted(place.noises):
            lines.append(asp.fact("nearby_noise", place_id, noise_id))
    for spill_id, spill in SPILLS.items():
        lines.append(asp.fact("spill", spill_id))
        lines.append(asp.fact("severity", spill_id, spill.severity))
        if spill.moppable:
            lines.append(asp.fact("moppable", spill_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("power", helper_id, helper.power))
    for noise_id in NOISES:
        lines.append(asp.fact("noise", noise_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show mop_problem/4."))
    return sorted(set(asp.atoms(model, "mop_problem")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    # Smoke-test ordinary story generation.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generated and emitted.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a spill, a mop, a misunderstood bellow, and a comic twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--spill", choices=SPILLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--noise", choices=NOISES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place is not None and args.spill is not None:
        place = PLACES[args.place]
        spill = SPILLS[args.spill]
        helper = HELPERS[args.helper] if args.helper else None
        noise = NOISES[args.noise] if args.noise else None
        if args.spill not in place.spills:
            raise StoryError(explain_rejection(place, spill, helper, noise))
        if args.noise is not None and args.noise not in place.noises:
            raise StoryError(explain_rejection(place, spill, helper, noise))
    if args.spill is not None:
        spill = SPILLS[args.spill]
        helper = HELPERS[args.helper] if args.helper else None
        if not spill.moppable:
            raise StoryError(explain_rejection(None, spill, helper, None))
        if args.helper is not None and not helper_can_fix(spill, helper):
            raise StoryError(explain_rejection(None, spill, helper, None))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.spill is None or combo[1] == args.spill)
        and (args.helper is None or combo[2] == args.helper)
        and (args.noise is None or combo[3] == args.noise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, spill_id, helper_id, noise_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        spill=spill_id,
        helper=helper_id,
        noise=noise_id,
        child_name=name,
        child_gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.spill not in SPILLS:
        raise StoryError(f"(Invalid spill: {params.spill})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if params.noise not in NOISES:
        raise StoryError(f"(Invalid noise: {params.noise})")

    place = PLACES[params.place]
    spill = SPILLS[params.spill]
    helper = HELPERS[params.helper]
    noise = NOISES[params.noise]

    if (params.place, params.spill, params.helper, params.noise) not in set(valid_combos()):
        raise StoryError(explain_rejection(place, spill, helper, noise))

    world = tell(
        place=place,
        spill_cfg=spill,
        helper_cfg=helper,
        noise_cfg=noise,
        child_name=params.child_name,
        child_gender=params.child_gender,
        trait=params.trait,
    )

    # Replace id labels with display names in the final prose.
    story = world.render().replace("child", params.child_name)

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show mop_problem/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, spill, helper, noise) combos:\n")
        for place, spill, helper, noise in combos:
            print(f"  {place:10} {spill:11} {helper:8} {noise}")
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
            header = f"### {p.child_name}: {p.spill} in {p.place} ({p.helper}, {p.noise})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
