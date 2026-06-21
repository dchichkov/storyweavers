#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/flabbergast_graph_lesson_learned_surprise_myth.py
==============================================================================

A standalone storyworld for a tiny myth-shaped domain: a child temple helper
keeps a clay graph of a sacred river, notices a dangerous rise before a shrine
crossing, and helps the village choose a wiser path. The heart of the world is
simple and state-driven:

- a sacred river can rise for different reasons
- the hero marks water lines on a clay graph
- a crossing plan must actually fit the place and the surge
- careful noticing earns trust
- the ending includes a surprise and a lesson learned

The required seed words appear naturally in the rendered story:
"graph" is the clay chart the hero makes, and "flabbergast" appears in the
surprise ending when the village sees the graph was right.

Run it
------
    python storyworlds/worlds/gpt-5.4/flabbergast_graph_lesson_learned_surprise_myth.py
    python storyworlds/worlds/gpt-5.4/flabbergast_graph_lesson_learned_surprise_myth.py --place moon_river --omen hill_rain
    python storyworlds/worlds/gpt-5.4/flabbergast_graph_lesson_learned_surprise_myth.py --fix stepping_stones
    python storyworlds/worlds/gpt-5.4/flabbergast_graph_lesson_learned_surprise_myth.py --all
    python storyworlds/worlds/gpt-5.4/flabbergast_graph_lesson_learned_surprise_myth.py --qa --json
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
# from its nested directory: storyworlds/worlds/gpt-5.4/<this file>.
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
    kind: str = "thing"         # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "priestess"}
        male = {"boy", "man", "father", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"priestess": "priestess", "priest": "priest"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    place: str
    shrine: str
    river: str
    graph_surface: str
    child_title: str
    elder_title: str
    surprise: str
    fixes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Omen:
    id: str
    sign: str
    cause: str
    surge: int
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Offering:
    id: str
    label: str
    phrase: str
    fragility: int
    gift_line: str
    loss_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    power: int
    text: str
    success: str
    failure: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_river_danger(world: World) -> list[str]:
    out: list[str] = []
    river = world.entities.get("river")
    village = world.entities.get("village")
    hero = world.entities.get("hero")
    elder = world.entities.get("elder")
    offering = world.entities.get("offering")
    if not river or not village:
        return out
    if river.meters["high"] < THRESHOLD:
        return out
    sig = ("danger", "river")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    village.meters["danger"] += 1
    if hero:
        hero.memes["worry"] += 1
    if elder:
        elder.memes["worry"] += 1
    if offering:
        offering.meters["at_risk"] += 1
    out.append("__danger__")
    return out


def _r_soak_offering(world: World) -> list[str]:
    out: list[str] = []
    offering = world.entities.get("offering")
    hero = world.entities.get("hero")
    if not offering:
        return out
    if offering.meters["wet"] < THRESHOLD:
        return out
    sig = ("loss", offering.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    offering.meters["spoiled"] += 1
    if hero:
        hero.memes["sadness"] += 1
    out.append("__loss__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="river_danger", tag="physical", apply=_r_river_danger),
    Rule(name="soak_offering", tag="physical", apply=_r_soak_offering),
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
                produced.extend(x for x in result if not x.startswith("__"))
    if narrate:
        for text in produced:
            world.say(text)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------
def required_power(omen: Omen, offering: Offering, delay: int) -> int:
    return omen.surge + offering.fragility - 1 + delay


def fix_available(setting: Setting, fix_id: str) -> bool:
    return fix_id in setting.fixes


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def best_fix_ids_for(setting: Setting, omen: Omen, offering: Offering) -> list[str]:
    need = required_power(omen, offering, 0)
    return sorted(
        fix_id
        for fix_id in setting.fixes
        if fix_id in FIXES and FIXES[fix_id].sense >= SENSE_MIN and FIXES[fix_id].power >= need
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for omen_id, omen in OMENS.items():
            for offering_id, offering in OFFERINGS.items():
                if best_fix_ids_for(setting, omen, offering):
                    combos.append((place_id, omen_id, offering_id))
    return combos


def explain_fix_rejection(setting: Setting, fix: Fix) -> str:
    if fix.sense < SENSE_MIN:
        better = ", ".join(sorted(f.id for f in sensible_fixes()))
        return (
            f"(Refusing fix '{fix.id}': it scores too low on common sense "
            f"(sense={fix.sense} < {SENSE_MIN}). Try a wiser plan such as {better}.)"
        )
    if fix.id not in setting.fixes:
        return (
            f"(No story: {fix.label} does not belong in {setting.place}. "
            f"Pick a fix the place actually affords.)"
        )
    return "(No story: this fix is not available.)"


def explain_combo_rejection(setting: Setting, omen: Omen, offering: Offering) -> str:
    need = required_power(omen, offering, 0)
    return (
        f"(No story: in {setting.place}, no sensible available fix is strong enough "
        f"for {offering.phrase} when {omen.sign} raises the water "
        f"(required power {need}).)"
    )


def is_safe(setting: Setting, omen: Omen, offering: Offering, fix: Fix, delay: int) -> bool:
    if fix.id not in setting.fixes:
        return False
    return fix.power >= required_power(omen, offering, delay)


def outcome_of(params: "StoryParams") -> str:
    setting = SETTINGS[params.place]
    omen = OMENS[params.omen]
    offering = OFFERINGS[params.offering]
    fix = FIXES[params.fix]
    return "safe" if is_safe(setting, omen, offering, fix, params.delay) else "wet"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_crossing(world: World, omen: Omen, offering: Offering) -> dict:
    sim = world.copy()
    river = sim.get("river")
    river.meters["high"] += float(omen.surge)
    offering_ent = sim.get("offering")
    offering_ent.meters["risk_need"] = float(required_power(omen, offering, 0))
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("village").meters["danger"],
        "need": required_power(omen, offering, 0),
        "at_risk": offering_ent.meters["at_risk"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, elder: Entity, setting: Setting) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"In the old days, when stories still walked beside the water, "
        f"{hero.id} served as the {setting.child_title} at {setting.shrine}. "
        f"{elder.id}, the {setting.elder_title}, taught {hero.pronoun('object')} to watch the river with patient eyes."
    )


def teach_graph(world: World, hero: Entity, setting: Setting) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"Each morning {hero.pronoun()} pressed a reed into {setting.graph_surface} and drew a little graph of the river's height. "
        f"One mark meant calm water, two meant hurry, and three meant turn back."
    )
    world.say(
        f"Some villagers trusted songs more than marks, yet {hero.id} loved how the graph let yesterday speak to today."
    )


def mission(world: World, hero: Entity, elder: Entity, offering: Offering, setting: Setting) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"On the day of the moon offering, {elder.id} set {offering.phrase} into {hero.id}'s arms. "
        f"They had to carry it across {setting.river} before sunset."
    )
    world.say(offering.gift_line)


def omen_arrives(world: World, omen: Omen) -> None:
    river = world.get("river")
    river.meters["high"] += float(omen.surge)
    river.meters["glow"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But as they walked down to the water, {omen.sign} appeared. {omen.cause}."
    )
    world.say(omen.glow)


def read_graph(world: World, hero: Entity, elder: Entity, omen: Omen, offering: Offering) -> None:
    pred = predict_crossing(world, omen, offering)
    hero.memes["caution"] += 1
    world.facts["predicted_need"] = pred["need"]
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f"{hero.id} knelt beside the bank, looked from the river to the clay graph, and frowned. "
        f'"The marks are climbing in the same shape again," {hero.pronoun()} said. '
        f'"If we rush now, the water will bite at our knees and snatch at the offering."'
    )
    if pred["danger"] >= THRESHOLD:
        world.say(
            f"{elder.id} listened closely, because the river no longer looked like a friendly road."
        )


def choose_fix(world: World, hero: Entity, elder: Entity, setting: Setting, fix: Fix) -> None:
    elder.memes["trust"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"{elder.id} studied the graph, then the river, then {hero.id}. "
        f'"Small marks can hold big wisdom," {elder.pronoun()} said.'
    )
    world.say(fix.text.format(hero=hero.id, elder=elder.id, shrine=setting.shrine))


def carry_out_fix(world: World, hero: Entity, elder: Entity, setting: Setting, fix: Fix, safe: bool) -> None:
    offering = world.get("offering")
    river = world.get("river")
    if safe:
        hero.memes["relief"] += 1
        hero.memes["awe"] += 1
        elder.memes["relief"] += 1
        world.say(fix.success.format(hero=hero.id, elder=elder.id, shrine=setting.shrine))
        river.meters["high"] = max(0.0, river.meters["high"] - 1.0)
    else:
        offering.meters["wet"] += 1
        propagate(world, narrate=False)
        hero.memes["relief"] += 1
        world.say(fix.failure.format(hero=hero.id, elder=elder.id, shrine=setting.shrine))
        world.say(offering.attrs.get("loss_line", "The river splashed the gift and left it spoiled on the stones."))


def surprise_ending(world: World, hero: Entity, elder: Entity, setting: Setting, safe: bool) -> None:
    hero.memes["lesson"] += 1
    hero.memes["awe"] += 1
    village = world.get("village")
    village.memes["astonishment"] += 1
    if safe:
        world.say(
            f"When the water bent away at last, {setting.surprise}."
        )
        world.say(
            f"The villagers were flabbergast. The old graph had spoken true, and a path no one had seen at noon shone clear by evening."
        )
        world.say(
            f"{elder.id} laid a warm hand on {hero.id}'s shoulder. "
            f'"Lesson learned," {elder.pronoun()} said. '
            f'"Even in a myth, wonder loves the child who watches carefully."'
        )
    else:
        world.say(
            f"Even so, the river left a surprise behind: {setting.surprise.lower()} after the spoiled gift had drifted away."
        )
        world.say(
            f"The villagers were flabbergast that the graph had warned them so plainly, and sorry they had not moved soon enough."
        )
        world.say(
            f"{elder.id} sighed, then nodded to {hero.id}. "
            f'"Lesson learned," {elder.pronoun()} said. '
            f'"The river gives second chances, but not to hasty feet."'
        )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    omen: Omen,
    offering_cfg: Offering,
    fix: Fix,
    hero_name: str = "Nara",
    hero_gender: str = "girl",
    elder_name: str = "Oren",
    elder_gender: str = "priest",
    delay: int = 0,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    river = world.add(Entity(id="river", kind="place", type="river", label=setting.river, phrase=setting.river))
    village = world.add(Entity(id="village", kind="place", type="village", label=setting.place))
    offering = world.add(
        Entity(
            id="offering",
            kind="thing",
            type="offering",
            label=offering_cfg.label,
            phrase=offering_cfg.phrase,
            attrs={"loss_line": offering_cfg.loss_line},
        )
    )

    introduce(world, hero, elder, setting)
    teach_graph(world, hero, setting)
    world.para()
    mission(world, hero, elder, offering_cfg, setting)
    omen_arrives(world, omen)
    read_graph(world, hero, elder, omen, offering_cfg)
    world.para()
    choose_fix(world, hero, elder, setting, fix)

    safe = is_safe(setting, omen, offering_cfg, fix, delay)
    carry_out_fix(world, hero, elder, setting, fix, safe)
    world.para()
    surprise_ending(world, hero, elder, setting, safe)

    world.facts.update(
        hero=hero,
        elder=elder,
        setting=setting,
        omen=omen,
        offering_cfg=offering_cfg,
        offering=offering,
        fix=fix,
        delay=delay,
        safe=safe,
        outcome="safe" if safe else "wet",
        predicted_need=world.facts.get("predicted_need", required_power(omen, offering_cfg, 0)),
    )
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "moon_river": Setting(
        id="moon_river",
        place="the Moon River crossing",
        shrine="the Moon Temple on the small island",
        river="the silver Moon River",
        graph_surface="a flat clay tablet by the shrine steps",
        child_title="lamp-keeper's apprentice",
        elder_title="keeper of tides",
        surprise="old stepping stones shaped like stars rose from the riverbed",
        fixes={"wait_bell", "rope_ferry", "hill_path"},
        tags={"river", "graph", "myth"},
    ),
    "reed_ford": Setting(
        id="reed_ford",
        place="the Reed Ford",
        shrine="the Shrine of Quiet Herons",
        river="the green reed river",
        graph_surface="a sun-baked clay square under a willow",
        child_title="reed-counter",
        elder_title="heron priestess",
        surprise="the reeds parted in a bright lane, as if making a doorway",
        fixes={"wait_bell", "rope_ferry"},
        tags={"river", "graph", "myth"},
    ),
    "shell_cove": Setting(
        id="shell_cove",
        place="the Shell Cove path",
        shrine="the Shrine of the Listening Sea",
        river="the tide channel below Shell Cove",
        graph_surface="a tablet of damp clay tucked near the sea wall",
        child_title="shell-tally child",
        elder_title="tide priest",
        surprise="the tide laid down a shell-white path no one had seen that morning",
        fixes={"wait_bell", "hill_path"},
        tags={"tide", "graph", "myth"},
    ),
}

OMENS = {
    "hill_rain": Omen(
        id="hill_rain",
        sign="far hill rain darkened the pines",
        cause="Though no drop touched the village, cold water hurried down from the high places",
        surge=2,
        glow="The river wore a hard shining skin and licked higher at the stones.",
        tags={"rain", "river"},
    ),
    "full_moon": Omen(
        id="full_moon",
        sign="the full moon pulled the water into a silver swell",
        cause="The channel breathed in long, slow gulps, as if a giant below were drinking the shore",
        surge=1,
        glow="Even the minnows turned their noses upstream, uneasy in the bright pull.",
        tags={"moon", "tide"},
    ),
    "storm_wind": Omen(
        id="storm_wind",
        sign="a storm wind came prowling over the water",
        cause="It shoved wave after wave into the crossing and made the banks mutter",
        surge=3,
        glow="Foam gathered in the grass, and the stepping place vanished under churning gray.",
        tags={"wind", "storm"},
    ),
}

OFFERINGS = {
    "moon_figs": Offering(
        id="moon_figs",
        label="moon figs",
        phrase="a basket of moon figs wrapped in leaves",
        fragility=1,
        gift_line="The figs smelled of honey and dusk, and the whole village hoped for a sweet year.",
        loss_line="The figs bobbed away like little boats, and the leaves came back empty.",
        tags={"fruit", "offering"},
    ),
    "painted_scroll": Offering(
        id="painted_scroll",
        label="painted scroll",
        phrase="a painted scroll for the shrine wall",
        fragility=2,
        gift_line="Blue cranes and gold stars curled across it, waiting for temple light.",
        loss_line="Water bled the painted cranes into blue tears, and the scroll sagged like a tired wing.",
        tags={"scroll", "paper", "offering"},
    ),
    "ember_lamp": Offering(
        id="ember_lamp",
        label="ember lamp",
        phrase="a tiny ember lamp in a copper bowl",
        fragility=2,
        gift_line="Its flame was meant to greet the shrine before the evening bells.",
        loss_line="The water kissed the little flame, and the lamp went dark with a sad hiss.",
        tags={"lamp", "fire", "offering"},
    ),
}

FIXES = {
    "wait_bell": Fix(
        id="wait_bell",
        label="waiting for the low-water bell",
        sense=3,
        power=3,
        text='"We will wait for the low-water bell and cross when the river has finished boasting," {elder} said.',
        success="They waited on the bank, and when the bell finally rang, the water had laid down its shoulders enough for a careful crossing to {shrine}.",
        failure="They waited, but they had already lingered too long. When they finally crossed toward {shrine}, the late swell slapped cold water over the offering.",
        tags={"wait", "river"},
    ),
    "rope_ferry": Fix(
        id="rope_ferry",
        label="the rope ferry",
        sense=3,
        power=2,
        text='"Take the rope ferry," said {elder}. "If the river wants to pull, let the ferry pull back."',
        success="Hand over hand, they guided the rope ferry across. The boat rocked, but it kept the offering high and dry all the way to {shrine}.",
        failure="They climbed into the rope ferry, but the current had grown wild. It slewed sideways, and river water sloshed over the rim onto the offering.",
        tags={"boat", "river"},
    ),
    "hill_path": Fix(
        id="hill_path",
        label="the hill path",
        sense=2,
        power=4,
        text='"We will climb the hill path and come down by the back steps of {shrine}," {elder} decided.',
        success="Up the hill they went among thyme and stone pines, and down they came behind {shrine}, far from the angriest water.",
        failure="They turned for the hill path, but the sky delayed them with thorny dusk. By the time they reached the back stream, a stray surge had already splashed the offering.",
        tags={"path", "hill"},
    ),
    "stepping_stones": Fix(
        id="stepping_stones",
        label="hurrying over the stepping stones",
        sense=1,
        power=1,
        text='"We will just hurry over the stepping stones," someone said.',
        success="They skipped over the stones before the river could think of mischief.",
        failure="They tried to dash over the stepping stones, and the river laughed first.",
        tags={"stones", "risky"},
    ),
}

GIRL_NAMES = ["Nara", "Tila", "Mira", "Suri", "Luma", "Etta", "Riva", "Dara"]
BOY_NAMES = ["Oren", "Kelan", "Ivo", "Tarin", "Milo", "Rami", "Daren", "Solen"]
ELDER_GIRL_NAMES = ["Yara", "Seri", "Maela", "Tovan"]
ELDER_BOY_NAMES = ["Oren", "Pelar", "Soren", "Bram"]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    omen: str
    offering: str
    fix: str
    hero_name: str
    hero_gender: str
    elder_name: str
    elder_gender: str
    delay: int = 0
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "graph": [
        (
            "What is a graph?",
            "A graph is a picture made of marks or lines that helps you notice a pattern. It can show whether something is going up, down, or staying the same.",
        )
    ],
    "river": [
        (
            "Why can a river become dangerous quickly?",
            "A river can rise fast when more water rushes into it from rain, wind, or tide. Then it moves harder and can knock people or things over.",
        )
    ],
    "moon": [
        (
            "How can the moon affect water?",
            "The moon pulls on the sea and some shore water, making tides rise and fall. That is why some crossings are safer at one time than another.",
        )
    ],
    "storm": [
        (
            "Why is storm wind a problem near water?",
            "Strong wind can shove water into waves and make it splash higher than usual. That makes a crossing rough and slippery.",
        )
    ],
    "wait": [
        (
            "Why is waiting sometimes the safest plan?",
            "Waiting gives danger time to shrink. A wise person does not hurry just because they want something right away.",
        )
    ],
    "boat": [
        (
            "What does a ferry do?",
            "A ferry carries people or goods across water. A rope ferry is held by a rope so it does not drift wherever the current wants.",
        )
    ],
    "hill": [
        (
            "Why might a hill path be safer than a water crossing?",
            "A hill path stays above the water. It may take longer, but it keeps you away from the strongest current.",
        )
    ],
    "offering": [
        (
            "What is an offering?",
            "An offering is a gift people bring with care, often to show thanks or hope. In stories and myths, offerings are treated gently and respectfully.",
        )
    ],
    "lesson": [
        (
            "What does 'lesson learned' mean?",
            "It means someone understood something important after what happened. The lesson helps them make a wiser choice next time.",
        )
    ],
}
KNOWLEDGE_ORDER = ["graph", "river", "moon", "storm", "wait", "boat", "hill", "offering", "lesson"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    omen = f["omen"]
    offering = f["offering_cfg"]
    fix = f["fix"]
    outcome = f["outcome"]
    base = (
        f'Write a short myth for a 3-to-5-year-old that includes the words "graph" and "flabbergast". '
        f"The story should involve a child noticing a pattern in a sacred river."
    )
    if outcome == "safe":
        return [
            base,
            f"Tell a mythic story where {hero.id} uses a clay graph to warn an elder that {omen.sign}, and the village reaches {setting.shrine} by choosing {fix.label}.",
            f"Write a gentle Lesson Learned story with a Surprise ending, where careful noticing saves {offering.phrase} and leaves the villagers amazed.",
        ]
    return [
        base,
        f"Tell a mythic cautionary story where {hero.id} reads a graph correctly, but the crossing still goes wrong because help comes too late and {offering.phrase} gets wet.",
        f"Write a Lesson Learned myth with a sad turn and a surprising sign from the river, showing that wise warnings should be heeded early.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    setting = f["setting"]
    omen = f["omen"]
    offering = f["offering_cfg"]
    fix = f["fix"]
    need = f["predicted_need"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child helper at {setting.shrine}, and {elder.id}, the elder who listens to the river. They are trying to carry {offering.phrase} safely across the water.",
        ),
        (
            "What was the graph for?",
            f"The graph showed how high the river had been on different days. {hero.id} used those marks to notice that the water was rising in a dangerous pattern.",
        ),
        (
            f"Why did {hero.id} warn {elder.id}?",
            f"{hero.id} saw that {omen.sign} matched the climbing shape on the graph. That meant the crossing needed power {need} or more to stay safe, so hurrying across would put the offering at risk.",
        ),
        (
            f"What plan did they choose?",
            f"They chose {fix.label}. The choice mattered because a good plan had to fit both the place and the strength of the water.",
        ),
    ]
    if outcome == "safe":
        qa.append(
            (
                "How did the story end?",
                f"They reached {setting.shrine} safely, and then a hidden path appeared as a surprise. The villagers were flabbergast because the graph had been right all along.",
            )
        )
        qa.append(
            (
                "What lesson was learned?",
                f"The lesson was that careful watching can be a kind of wisdom. Small marks on a graph helped the grown-up make a better choice before danger grew bigger.",
            )
        )
    else:
        qa.append(
            (
                "Did the warning matter even though the offering got wet?",
                f"Yes. The warning showed that {hero.id} had understood the river correctly, even though the help came too late. That is why the villagers felt both sorry and amazed when the surprise sign appeared.",
            )
        )
        qa.append(
            (
                "What lesson was learned?",
                f"The lesson was not to wait too long after a wise warning. The graph told the truth, and everyone learned that careful noticing should be trusted quickly.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"graph", "river", "offering", "lesson"}
    omen = world.facts["omen"]
    fix = world.facts["fix"]
    if "moon" in omen.tags or "tide" in omen.tags:
        tags.add("moon")
    if "storm" in omen.tags or "wind" in omen.tags:
        tags.add("storm")
    if fix.id == "wait_bell":
        tags.add("wait")
    if fix.id == "rope_ferry":
        tags.add("boat")
    if fix.id == "hill_path":
        tags.add("hill")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="moon_river",
        omen="hill_rain",
        offering="painted_scroll",
        fix="hill_path",
        hero_name="Nara",
        hero_gender="girl",
        elder_name="Oren",
        elder_gender="priest",
        delay=0,
    ),
    StoryParams(
        place="reed_ford",
        omen="full_moon",
        offering="moon_figs",
        fix="wait_bell",
        hero_name="Tila",
        hero_gender="girl",
        elder_name="Yara",
        elder_gender="priestess",
        delay=0,
    ),
    StoryParams(
        place="shell_cove",
        omen="storm_wind",
        offering="ember_lamp",
        fix="wait_bell",
        hero_name="Milo",
        hero_gender="boy",
        elder_name="Soren",
        elder_gender="priest",
        delay=1,
    ),
    StoryParams(
        place="moon_river",
        omen="storm_wind",
        offering="painted_scroll",
        fix="rope_ferry",
        hero_name="Riva",
        hero_gender="girl",
        elder_name="Pelar",
        elder_gender="priest",
        delay=1,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% sensible and available fixes
sensible_fix(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
available_fix(P,F) :- setting(P), allows(P,F).

% minimum power a scenario needs
need(O, G, N) :- omen(O), offering(G), surge(O,S), fragility(G,Fg), N = S + Fg - 1.

% a story combo is valid when the place has some sensible available fix
% already strong enough for the no-delay version of the danger.
valid(P, O, G) :- setting(P), omen(O), offering(G),
                  available_fix(P,F), sensible_fix(F),
                  need(O,G,N), power(F, Pw), Pw >= N.

% runtime scenario: include delay and chosen fix
actual_need(N) :- chosen_omen(O), chosen_offering(G), delay(D),
                  surge(O,S), fragility(G,Fg), N = S + Fg - 1 + D.
safe :- chosen_place(P), chosen_fix(F), available_fix(P,F), sensible_fix(F),
        actual_need(N), power(F,Pw), Pw >= N.
outcome(safe) :- safe.
outcome(wet) :- not safe.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place_id))
        for fix_id in sorted(setting.fixes):
            lines.append(asp.fact("allows", place_id, fix_id))
    for omen_id, omen in OMENS.items():
        lines.append(asp.fact("omen", omen_id))
        lines.append(asp.fact("surge", omen_id, omen.surge))
    for offering_id, offering in OFFERINGS.items():
        lines.append(asp.fact("offering", offering_id))
        lines.append(asp.fact("fragility", offering_id, offering.fragility))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("power", fix_id, fix.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_omen", params.omen),
            asp.fact("chosen_offering", params.offering),
            asp.fact("chosen_fix", params.fix),
            asp.fact("delay", params.delay),
        ]
    )
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

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for s in range(80):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            continue

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a river graph, a lesson, and a surprise."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-gender", choices=["priestess", "priest"])
    ap.add_argument("--hero-name")
    ap.add_argument("--elder-name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how late the group acts after the warning")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, elder: bool = False, avoid: str = "") -> str:
    if elder:
        pool = ELDER_GIRL_NAMES if gender == "priestess" else ELDER_BOY_NAMES
    else:
        pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.fix:
        setting = SETTINGS[args.place]
        fix = FIXES[args.fix]
        if args.fix not in setting.fixes or fix.sense < SENSE_MIN:
            raise StoryError(explain_fix_rejection(setting, fix))

    if args.fix and not args.place and FIXES[args.fix].sense < SENSE_MIN:
        # explicit low-sense fix is still invalid even without a pinned place
        raise StoryError(explain_fix_rejection(next(iter(SETTINGS.values())), FIXES[args.fix]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.omen is None or combo[1] == args.omen)
        and (args.offering is None or combo[2] == args.offering)
    ]
    if not combos:
        if args.place and args.omen and args.offering:
            raise StoryError(explain_combo_rejection(SETTINGS[args.place], OMENS[args.omen], OFFERINGS[args.offering]))
        raise StoryError("(No valid combination matches the given options.)")

    place, omen_id, offering_id = rng.choice(sorted(combos))
    setting = SETTINGS[place]
    omen = OMENS[omen_id]
    offering = OFFERINGS[offering_id]

    if args.fix:
        fix_id = args.fix
    else:
        candidates = [
            fix_id
            for fix_id in sorted(setting.fixes)
            if fix_id in FIXES and FIXES[fix_id].sense >= SENSE_MIN
        ]
        if not candidates:
            raise StoryError(explain_combo_rejection(setting, omen, offering))
        # Sometimes choose a merely possible fix, not always the strongest one.
        fix_id = rng.choice(candidates)

    if fix_id not in setting.fixes or FIXES[fix_id].sense < SENSE_MIN:
        raise StoryError(explain_fix_rejection(setting, FIXES[fix_id]))

    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["priestess", "priest"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender, elder=False)
    elder_name = args.elder_name or _pick_name(rng, elder_gender, elder=True, avoid=hero_name)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        place=place,
        omen=omen_id,
        offering=offering_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_name=elder_name,
        elder_gender=elder_gender,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.omen not in OMENS:
        raise StoryError(f"(Invalid omen: {params.omen})")
    if params.offering not in OFFERINGS:
        raise StoryError(f"(Invalid offering: {params.offering})")
    if params.fix not in FIXES:
        raise StoryError(f"(Invalid fix: {params.fix})")

    setting = SETTINGS[params.place]
    omen = OMENS[params.omen]
    offering = OFFERINGS[params.offering]
    fix = FIXES[params.fix]

    if fix.id not in setting.fixes or fix.sense < SENSE_MIN:
        raise StoryError(explain_fix_rejection(setting, fix))

    world = tell(
        setting=setting,
        omen=omen,
        offering_cfg=offering,
        fix=fix,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_name=params.elder_name,
        elder_gender=params.elder_gender,
        delay=params.delay,
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
        print(f"{len(combos)} compatible (place, omen, offering) combos:\n")
        for place, omen, offering in combos:
            print(f"  {place:11} {omen:11} {offering}")
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
            header = f"### {p.hero_name}: {p.omen} at {p.place} with {p.offering} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
