#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022423Z_seed424242_n1/burro_mister_magenta_bad_ending_comedy.py
==============================================================================================================

Storyworld sketch for "The Burro, the Magenta Hat, and the Long, Funny Bad Day":
a TinyStories-style comedy about a stubborn little burro, a polite man called
Mr. Magenta, and a very risky new hat -- with a deliberately *bad ending* (the
comedy lands on a lesson, not a win).

The world is a small set of typed entities (a burro, a caretaker, a hat, maybe
a friend) with physical meters and emotional memes. A few causal rules forward-
chain the state, and the screenplay narrates that state. Three Q&A sets
(generation prompts, story-grounded, and child-level world knowledge) plus an
inline ASP twin gate the generated combinations.

The "Bad Ending" feature is enforced by the rules -- when a story picks
``--ending bad``, the burro's attempt fails (the magenta hat ends up ruined in
a ridiculous way) and the lesson is the punchline. ``--ending good`` is still
available for variety, but the default seed below produces the bad ending.
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MAGIC_TINT = "magenta"

# ---- Body regions the activities can mess up. ------------------------------
REGIONS = {"feet", "legs", "back", "ears", "head"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"                # "character" | "thing"
    type: str = "thing"                # burro, man, hat, friend ...
    label: str = ""                    # short ref
    phrase: str = ""                   # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""                   # body region the item sits on
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "lady"}
        male = {"boy", "father", "dad", "man", "mister", "mr"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "burro":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mister": "Mr. Magenta", "mr": "Mr. Magenta",
                "mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str                # the physical meter that the activity bumps
    soil: str                # the human-readable soiling clause
    zone: set[str]           # body regions the activity splashes / touches
    weather: str = ""        # "rainy" | "sunny" | ""
    risk: str = ""           # one-line "what could go wrong" used in bad endings
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    gendered: bool = True    # does this prize obviously belong to a gender?
    genders: set[str] = field(default_factory=lambda: {"boy", "girl", "man", "woman"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.ending: str = "bad"           # bad | good
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.ending = self.ending
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            if actor.meters[world.zone_mess] < THRESHOLD:
                continue
            sig = ("soak", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters[world.zone_mess] += 1
            item.meters["dirty"] += 1
            out.append(
                f"{actor.pronoun('possessive').capitalize()} {item.label} "
                f"got {item.meters[world.zone_mess]:.0f} step messier."
            )
    return out


def _r_tint(world: World) -> list[str]:
    """Magenta paint / dye stamps the item a memorable colour when it gets wet."""
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["wet"] < THRESHOLD:
            continue
        if item.meters["magenta_dye"] >= THRESHOLD:
            continue
        if MAGIC_TINT not in item.label and "magenta_dye" not in item.meters:
            continue
        sig = ("tint", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["magenta_dye"] += 1
        out.append(f"The wet made {item.label} a loud, funny {MAGIC_TINT}.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more scrubbing for {carer.label}.")
    return out


def _r_defiance_grab(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["grabbed_by"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


def _r_lesson(world: World) -> list[str]:
    """If the burro's prized item is ruined, the 'lesson' meter ticks up."""
    for actor in world.characters():
        if actor.type != "burro":
            continue
        if actor.meters["lesson"] >= THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.meters["dirty"] >= THRESHOLD and "lesson" not in [
                k for k, _ in world.fired if k == "lesson"
            ]:
                actor.meters["lesson"] += 1
                world.fired.add(("lesson", actor.id))
                return [f"{actor.id} finally learned why grown-ups ask first."]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="tint", tag="physical", apply=_r_tint),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="defiance_grab", tag="social", apply=_r_defiance_grab),
    Rule(name="lesson", tag="lesson", apply=_r_lesson),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            for s in rule.apply(world):
                if s == "__conflict__":
                    changed = True
                elif s:
                    changed = True
                    produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    sim.zone_mess = activity.mess
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "tinted": bool(prize and prize.meters["magenta_dye"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "puddles": "every plop felt like a tiny drum",
        "rain": "the drops tickled his fuzzy ears",
        "mud": "the squelch under his hooves made him giggle",
        "paint": "the bright pots looked like sweets",
        "berries": "the little bushes glowed like jewels",
        "hay": "the bales smelled like warm bread",
    }.get(activity.id, "it made his heart go thump-thump")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was snug, and a soft light came through the window."
    if activity.weather == "rainy":
        return f"The air smelled fresh, and {setting.place} shone after the rain."
    if setting.place == "the meadow":
        return "The meadow was wide, and the flowers nodded as if they remembered his name."
    return f"{setting.place.capitalize()} looked wide and ready for play."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    world.zone_mess = activity.mess
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(
        f"{hero.id} was a {desc} with big soft ears and a nose that twitched "
        f"whenever he smelled something interesting."
    )


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(
        f"He loved {activity.gerund} more than almost anything; {activity_delight(activity)}."
    )


def gets_hat(world: World, giver: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One morning, {giver.id} gave {hero.id} a brand-new "
        f"{prize.phrase} for his birthday."
    )


def loves_hat(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {prize.it()} right away. He wore {prize.it()} on his head "
        f"and looked at his reflection in the watering trough."
    )


def arrive(world: World, hero: Entity, giver: Entity, activity: Activity) -> None:
    day = {"rainy": "One rainy day, ", "sunny": "One sunny day, "}.get(world.weather, "One day, ")
    world.say(
        f"{day}{hero.id} went to {world.setting.place} with {giver.id}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} saw the {activity.id} and wanted to {activity.verb} right away."
    )


def warn(world: World, giver: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    world.facts["predicted_tint"] = pred["tinted"]
    clause = f"You'll get your {prize.label} {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then I'll have to clean {prize.it()}"
    world.say(
        f'"{clause}," {giver.id} said. "And I just polished it this morning!"'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But {hero.id} was very stubborn. He twitched his nose and tried to {activity.rush}."
    )


def grab(world: World, giver: Entity, hero: Entity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{giver.id} caught his halter just in time and said, "
        f'"We can still do something fun, but let\'s do it the safe way."'
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{hero.id} stamped a small hoof. "But I really want to {activity.verb}!" he brayed.'
        )


def compromise(world: World, giver: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    """Bad endings: refuse the compromise and the story collapses.
    Good endings: the gear actually helps."""
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=giver.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{giver.id} smiled. "How about we {gear_def.prep} first, and then '
        f'{activity.verb} together?"'
    )
    return gear_def


def bad_ending(world: World, hero: Entity, giver: Entity, activity: Activity,
               prize: Entity) -> None:
    """The comedy lands: the burro's hat ends up ruined in a ridiculous way,
    and the lesson is the punchline."""
    world.ending = "bad"
    world.say(
        f"{hero.id} shook his head, the way burros do when they do not want to wait."
    )
    world.say(
        f"He went to {activity.verb} anyway, and the {activity.id} splashed "
        f"all over his brand-new {prize.label}."
    )
    # Fire the causal rules for real this time, with narration on, so the rules
    # are visible in the prose and in --trace.
    _do_activity(world, hero, activity, narrate=True)
    world.say(
        f"Now his {prize.label} was dripping, dirty, and the brightest {MAGIC_TINT} "
        f"anyone in the valley had ever seen."
    )
    world.say(
        f"{giver.id} tried very hard not to laugh. He failed. He laughed so much "
        f"his hat fell off too."
    )
    world.say(
        f"From that day on, {hero.id} was called {hero.id} the {MAGIC_TINT.capitalize()}, "
        f"and he never, ever wore a new hat to the {activity.id} again."
    )
    world.say(
        f"It was a bad day for the hat -- but a very good lesson for the little burro."
    )


def good_ending(world: World, hero: Entity, giver: Entity, activity: Activity,
                prize: Entity, gear_def: Gear) -> None:
    world.ending = "good"
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id}'s ears went straight up and he nodded his big head, which is how "
        f"burros say yes."
    )
    world.say(
        f"They {gear_def.tail}, and soon {hero.id} was {activity.gerund} while his "
        f"{prize.label} stayed clean and {MAGIC_TINT}-bright."
    )
    world.say(
        f"{giver.id} laughed and gave him an extra carrot for being such a clever little burro."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Pedro", giver_name: str = "Mr. Magenta",
         giver_type: str = "mister", ending: str = "bad",
         hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather
    world.ending = ending

    hero = world.add(Entity(
        id=hero_name, kind="character", type="burro",
        traits=["little"] + (hero_traits or ["stubborn", "curious"]),
        label="the little burro",
    ))
    giver = world.add(Entity(
        id=giver_name, kind="character", type=giver_type,
        label=f"Mr. Magenta",
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=giver.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1
    introduce(world, hero)
    loves_activity(world, hero, activity)
    gets_hat(world, giver, hero, prize)
    loves_hat(world, hero, prize)

    # Act 2
    world.para()
    arrive(world, hero, giver, activity)
    wants(world, hero, activity)
    warn(world, giver, hero, activity, prize)
    defies(world, hero, activity)
    grab(world, giver, hero)

    # Act 3
    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, giver, hero, activity, prize)

    if ending == "bad" or gear_def is None:
        bad_ending(world, hero, giver, activity, prize)
    else:
        good_ending(world, hero, giver, activity, prize, gear_def)

    world.facts.update(hero=hero, giver=giver, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None and ending == "good",
                       ending=ending)
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "farm": Setting(place="the farm", indoor=False, affords={"puddles", "rain", "mud", "hay"}),
    "meadow": Setting(place="the meadow", indoor=False, affords={"puddles", "rain", "berries", "hay"}),
    "barn": Setting(place="the barn", indoor=True, affords={"hay", "paint"}),
    "orchard": Setting(place="the orchard", indoor=False, affords={"berries", "rain", "puddles"}),
    "riverbank": Setting(place="the riverbank", indoor=False, affords={"puddles", "mud", "berries"}),
}

ACTIVITIES = {
    "puddles": Activity(
        id="puddles",
        verb="splash in the puddles",
        gerund="splash in the puddles",
        rush="gallop straight into the biggest puddle",
        mess="wet",
        soil="soaking wet",
        zone={"feet", "legs", "head"},
        weather="rainy",
        risk="the splash goes up past his ears",
        keyword="puddles",
        tags={"puddle", "wet"},
    ),
    "rain": Activity(
        id="rain",
        verb="dance in the rain",
        gerund="dancing in the rain",
        rush="run out into the rain",
        mess="wet",
        soil="soaking wet",
        zone={"head", "back", "ears"},
        weather="rainy",
        risk="the rain lands right on top of his hat",
        keyword="rain",
        tags={"rain", "wet"},
    ),
    "mud": Activity(
        id="mud",
        verb="roll in the mud",
        gerund="rolling in the mud",
        rush="drop down into the muddiest spot",
        mess="muddy",
        soil="covered in mud",
        zone={"legs", "back", "head"},
        weather="rainy",
        risk="the mud splashes up to his brand-new hat",
        keyword="mud",
        tags={"mud", "dirty"},
    ),
    "paint": Activity(
        id="paint",
        verb="paint a fence",
        gerund="painting a fence",
        rush="grab the brush and run to the fence",
        mess="painted",
        soil="covered in paint",
        zone={"head", "ears"},
        weather="",
        risk="the pink paint drips right onto his hat",
        keyword="paint",
        tags={"paint", "dirty"},
    ),
    "berries": Activity(
        id="berries",
        verb="pick berries",
        gerund="picking berries",
        rush="trot over to the berry bushes",
        mess="stained",
        soil="stained with berry juice",
        zone={"head", "ears"},
        weather="sunny",
        risk="the berry juice drips onto his hat",
        keyword="berries",
        tags={"berries", "dirty"},
    ),
    "hay": Activity(
        id="hay",
        verb="burrow in the hay",
        gerund="burrowing in the hay",
        rush="jump straight into the hay pile",
        mess="strawy",
        soil="covered in straw",
        zone={"head", "back", "ears"},
        weather="",
        risk="the hay sticks out of his hat like a silly crown",
        keyword="hay",
        tags={"hay", "dirty"},
    ),
}

GEAR = [
    Gear(
        id="hatcover",
        label="a little hat cover",
        covers={"head"},
        guards={"wet", "muddy", "painted", "stained", "strawy"},
        prep="put a little hat cover on your hat",
        tail="tied the little hat cover over his new hat",
    ),
    Gear(
        id="oldhat",
        label="an old hat",
        covers={"head", "ears"},
        guards={"wet", "muddy", "painted", "stained", "strawy"},
        prep="wear the old hat instead of the new one",
        tail="swapped the old hat on and put the new one away",
    ),
    Gear(
        id="rainhood",
        label="a tiny rainhood",
        covers={"head", "ears", "back"},
        guards={"wet"},
        prep="pull the tiny rainhood right over your hat",
        tail="tugged the tiny rainhood on over his hat",
    ),
]

PRIZES = {
    "magenta_hat": Prize(
        label="magenta hat",
        phrase="a shiny magenta hat with a little tassel",
        type="hat",
        region="head",
        plural=False,
        gendered=False,
        genders={"boy", "girl", "man", "woman", "burro"},
    ),
    "magenta_bandana": Prize(
        label="magenta bandana",
        phrase="a soft magenta bandana with polka dots",
        type="bandana",
        region="head",
        plural=False,
        gendered=False,
        genders={"boy", "girl", "man", "woman", "burro"},
    ),
    "magenta_feather": Prize(
        label="magenta feather",
        phrase="a tall magenta feather on a thin band",
        type="feather",
        region="head",
        plural=False,
        gendered=False,
        genders={"boy", "girl", "man", "woman", "burro"},
    ),
}

DONKEY_NAMES = ["Pedro", "Burrito", "Bean", "Cisco", "Nopal", "Tuco", "Olmo", "Solecito", "Milo", "Tito"]
TRAITS = ["stubborn", "curious", "cheerful", "playful", "spirited", "lively"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


# ---------------------------------------------------------------------------
# Per-story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    giver: str
    ending: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "puddle": [("What is a puddle?",
                "A puddle is a small pool of water on the ground, usually left "
                "behind after it rains.")],
    "rain": [("Where does rain come from?",
              "Rain is water that falls from clouds in the sky when the clouds "
              "get too full of tiny water drops.")],
    "mud": [("What is mud?",
             "Mud is soft, wet dirt. It sticks to hooves and clothes and makes "
             "them dirty.")],
    "paint": [("Why can paint be messy?",
               "Paint is a colored liquid, so it can drip and smear onto clothes "
               "and hats, and it is hard to wash out.")],
    "berries": [("Why do berries stain?",
                 "Berry juice has strong colour in it, and when it drips on cloth "
                 "it leaves a mark that is hard to wash out.")],
    "hay": [("Why does hay stick to everything?",
              "Hay is dry and scratchy, and the long pieces catch on cloth and "
              "fur like tiny hooks.")],
    "burro": [("What is a burro?",
               "A burro is a small donkey with long ears. They are sturdy, "
               "patient, and very good at carrying things.")],
    "magenta": [("What colour is magenta?",
                 "Magenta is a bright pinkish-purple colour, like a flower "
                 "and a crayon mixed together.")],
    "bad_ending": [("What is a 'bad ending' in a story?",
                    "A bad ending is one where the hero's plan does not work "
                    "out, but the reader still learns something funny or useful.")],
    "hat": [("Why do people wear hats on a burro?",
             "Hats keep sun and rain off a burro's head, and they make the burro "
             "look very dapper for the day.")],
}
KNOWLEDGE_ORDER = ["burro", "magenta", "hat", "puddle", "rain", "mud", "paint",
                   "berries", "hay", "bad_ending"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, giver, act, prize = f["hero"], f["giver"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short comedy story for a 3-to-5-year-old on the theme "a '
        f'stubborn little burro, a new hat, and a very funny bad day" that '
        f'includes the word "{act.keyword}".',
        f"Tell a gentle, funny story where a little burro named {hero.id} "
        f"wants to {act.verb}, but {giver.id} worries about {prize.phrase}, "
        f"and the day ends in a bad-but-sweet way.",
        f'Write a simple story that uses the noun "{MAGIC_TINT}" and ends '
        f"with a silly, lesson-filled bad ending for a stubborn little burro.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, giver, prize, act = f["hero"], f["giver"], f["prize"], f["activity"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    day = {"rainy": "rainy day", "sunny": "sunny day"}.get(world.weather, "play day")
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} goes to {place} to "
                f"{act.verb} in his new {prize.label}?"
            ),
            answer=(
                f"It is about a little {trait} burro named {hero.id} and his "
                f"friend {giver.id}. They go to {place} on a {day}, and "
                f"{hero.id} is wearing {pos} {prize.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love to do before {giver.id} "
                f"worried about his {prize.label}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} loved {act.gerund}. That wish "
                f"became tricky because {pos} {prize.label} was brand new and "
                f"the {act.keyword} could splash right on it."
            ),
        ),
        QAItem(
            question=(
                f"What new {prize.label} did {giver.id} give {hero.id} before "
                f"the {act.keyword} day at {place}?"
            ),
            answer=(
                f"{giver.id} gave {obj} {prize.phrase}. {hero.id} loved "
                f"{prize.it()} and wore {prize.it()} on his head."
            ),
        ),
    ]
    if f.get("conflict"):
        soil = f.get("predicted_soil", "messy")
        work = f.get("predicted_workload", 0)
        why = (f"{giver.id} was worried because if {hero.id} went to "
               f"{act.verb}, {pos} {prize.label} would get {soil}")
        why += f", and then {giver.id} would have to clean {prize.it()}. " if work >= THRESHOLD else ". "
        why += (f"When {hero.id} tried to {act.rush.rstrip(', ')}, {giver.id} "
                f"caught his halter and reminded him there was a safer way.")
        qa.append(QAItem(
            question=(
                f"Why did {giver.id} worry about {hero.id}'s {prize.label} "
                f"when he wanted to {act.verb} at {place}?"
            ),
            answer=why,
        ))

    # Ending questions -- central to the "bad ending" feature.
    if f["ending"] == "bad":
        qa.append(QAItem(
            question=(
                f"What went wrong with {hero.id}'s {prize.label} on the "
                f"{act.keyword} day at {place}?"
            ),
            answer=(
                f"{hero.id} would not wait for the safer plan, so he went to "
                f"{act.verb} anyway. The {act.keyword} splashed all over his "
                f"{prize.label}, and it ended up the brightest {MAGIC_TINT} "
                f"anyone in the valley had ever seen."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What lesson did little {hero.id} learn from the bad day "
                f"with his {prize.label} at {place}?"
            ),
            answer=(
                f"He learned that grown-ups sometimes ask you to wait for a "
                f"reason, and that a brand-new hat plus a {act.keyword} day "
                f"is a recipe for a very loud, very {MAGIC_TINT} mess."
            ),
        ))
    else:
        gear = f["gear"]
        qa.append(QAItem(
            question=(
                f"How did {gear.label} help {hero.id} {act.verb} at {place} "
                f"without ruining his {prize.label}?"
            ),
            answer=(
                f"They agreed to use {gear.label} first, so {hero.id} could "
                f"{act.verb} at {place} without ruining {pos} {prize.label}. "
                f"The plan let {obj} play and kept the {MAGIC_TINT} bright."
            ),
        ))

    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    tags.add("burro")
    tags.add("magenta")
    tags.add("hat")
    if f["ending"] == "bad":
        tags.add("bad_ending")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
# Trace dump
# ---------------------------------------------------------------------------
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  ending: {world.ending}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set (used by --all)
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="farm",
        activity="puddles",
        prize="magenta_hat",
        name="Pedro",
        giver="Mr. Magenta",
        ending="bad",
        trait="stubborn",
    ),
    StoryParams(
        place="orchard",
        activity="berries",
        prize="magenta_bandana",
        name="Burrito",
        giver="Mr. Magenta",
        ending="bad",
        trait="curious",
    ),
    StoryParams(
        place="riverbank",
        activity="mud",
        prize="magenta_feather",
        name="Bean",
        giver="Mr. Magenta",
        ending="bad",
        trait="spirited",
    ),
    StoryParams(
        place="barn",
        activity="paint",
        prize="magenta_hat",
        name="Cisco",
        giver="Mr. Magenta",
        ending="good",
        trait="cheerful",
    ),
    StoryParams(
        place="meadow",
        activity="rain",
        prize="magenta_bandana",
        name="Nopal",
        giver="Mr. Magenta",
        ending="good",
        trait="lively",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, "
                f"but {noun} {verb} on the {prize.region} -- it wouldn't get "
                f"{activity.mess}, so the giver has no honest warning. "
                f"Try a prize worn on {sorted(activity.zone)}.)")
    return (f"(No story: nothing in the gear catalog protects {noun} "
            f"({prize.region}) from {activity.gerund}. The compromise must actually "
            f"cover the at-risk item, so this argument is rejected.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk when the activity splashes the region it is worn on.
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

% Gear is a compatible fix only when it both neutralises the mess kind AND
% covers the at-risk region.
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).

% Both endings are ASP-reasonable; the *style* of ending is a separate choice.
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Ending) :- valid(Place, A, P),
                                     ending_kind(Ending).
bad_valid(Place, A, P) :- valid(Place, A, P), bad_allowed.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    lines.append(asp.fact("ending_kind", "bad"))
    lines.append(asp.fact("ending_kind", "good"))
    lines.append(asp.fact("bad_allowed"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_bad_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show bad_valid/3."))
    return sorted(set(asp.atoms(model, "bad_valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    bad_set = set(asp_bad_combos())
    if clingo_set == python_set and bad_set <= python_set:
        print(f"OK: clingo gate matches valid_combos() "
              f"({len(clingo_set)} combos, {len(bad_set)} bad-ending-eligible).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if bad_set - python_set:
        print("  bad combos outside valid:", sorted(bad_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a stubborn little burro, Mr. Magenta, a "
                    "magenta hat, and a comedic bad ending. Unspecified "
                    "choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--ending", choices=["bad", "good"], default="bad",
                    help="story outcome: a comedic bad ending (default) or a good one")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(DONKEY_NAMES)
    ending = args.ending or "bad"
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        giver="Mr. Magenta",
        ending=ending,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.giver,
                 "mister", params.ending, [params.trait, "curious"])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        triples = asp_valid_combos()
        bad = asp_bad_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos "
              f"({len(bad)} bad-ending-eligible):\n")
        for place, act, prize in triples:
            tag = "bad" if (place, act, prize) in bad else "good"
            print(f"  {place:10} {act:8} {prize:16}  [{tag}]")
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
            header = (f"### {p.name} + {p.giver}: {p.activity} at {p.place} "
                      f"(prize: {p.prize}, ending: {p.ending})")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
