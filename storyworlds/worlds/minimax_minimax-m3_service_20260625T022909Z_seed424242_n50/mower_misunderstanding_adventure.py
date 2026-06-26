#!/usr/bin/env python3
"""
storyworlds/worlds/mower_misunderstanding_adventure.py
=====================================================

A standalone story-world sketch in the "mower misunderstanding adventure" mode.

Initial story (used to build the world model):
---
Once upon a time there was a little cheerful girl named Ada who loved helping
her dad out in the garden. One bright morning her dad pulled out the old push
mower and showed her how it worked. "Stay well back," he said. "It cuts, and
it does not know you are there."

Ada watched the mower chug along the lawn and thought it sounded lonely. She
walked up behind it and waved. The mower roared on. She waved harder and
called, "Hello, mower!" The mower did not turn its head, because mowers do
not have heads.

Ada thought the mower was being rude. She folded her arms. "Why won't you
answer me?" she asked. Her dad laughed and knelt beside her. "It isn't being
unkind," he said. "It cannot hear you. It only knows grass." He showed her
the spinning blade hidden safely under the guard. "That is why I told you
to stay back -- the bit that cuts cannot tell a blade of grass from a
shoe."

Ada's eyes went wide. She remembered the rule and stepped well back. Then
her dad let her push the mower along a gentle strip, with him holding the
handle beside her. The mower hummed happily, the lawn grew neat, and Ada
decided she had a new job. From then on she asked her friends the
important question: would the lawn please stand still? The mower, of
course, never answered.

Causal state updates:
---
    actor approaches mower    -> actor.mess.exposure += 1 (close-range meter)
    blade spinning + actor close -> actor.memes.danger += 1
                                       actor.memes.brave_pretend += 1
    misunderstanding resolved  -> actor.memes.clarity += 1 ; actor.memes.shame = 0
    child pushed the mower    -> actor.memes.pride += 1 ; parent.memes.pride += 1
    parent knelt to explain   -> parent.memes.tenderness += 1

Adventure instruments:
    the quest    : "figure out what the mower is doing and why"
    the mystery  : "why does it ignore me?"
    the reveal   : "the spinning blade under the guard is what is loud, not a mind"
    the sidekick : the dad, who kneels and teaches
    the rule     : "stay well back from the cutting bit"
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

# The bit of the mower that actually does harm. Two regions sit on the body:
#   handle   - where the pusher stands (always safe)
#   blade    - where the spinning cutter lives (the danger zone)
REGIONS = {"handle", "blade"}

# What kinds of mess the activity can spread onto a body region.
MESS_KINDS = {"noise", "dust", "wet"}

# An actor is "exposed" when their body region is the blade zone AND they are
# close. "Brave pretending" is when the kid walks up to investigate alone.
DANGER_ZONE = "blade"
SAFE_ZONE = "handle"


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, mother, father, mower ...
    label: str = ""                # short reference, e.g. "mower", "dad"
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""               # body region of the actor / location on the mower
    protective: bool = False       # gear that doesn't get ruined
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the garden"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    """A mower-using adventure in the lawn (or another mower-friendly place)."""
    id: str
    verb: str            # after "wanted to ..."             : "push the mower"
    gerund: str          # after "loved ... and ..."        : "watching the mower chug"
    rush: str            # after "tried to ..."             : "walk up to the mower"
    mess: str            # one of MESS_KINDS                : "noise"
    soil: str            # how it bothers people nearby     : "so loud it covers your voice"
    zone: set[str]       # body regions the activity affects: {"handle", "blade"}
    weather: str         # "sunny" | "rainy" | ""
    keyword: str = ""    # generation prompt word           : "mower"
    tags: set[str] = field(default_factory=set)


@dataclass
class RuleArtifact:
    """The parent's safety rule -- the resolution of the misunderstanding."""
    id: str
    label: str
    covers: set[str]     # regions the rule shields (handle = safe to push)
    guards: set[str]     # danger kinds the rule neutralizes
    prep: str            # body of the offer: "stay well back from the cutting bit"
    tail: str            # closing clause: "stepped well back from the cutting bit"
    plural: bool = False


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def mower(self) -> Optional[Entity]:
        for e in self.entities.values():
            if e.type == "mower":
                return e
        return None

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
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_close_to_blade(world: World) -> list[str]:
    """If the actor is close to the mower and the blade is exposed, raise the
    danger meter (and a 'brave pretending' mem) so the parent can warn."""
    out: list[str] = []
    for actor in world.characters():
        sig = ("close_blade", actor.id)
        if sig in world.fired:
            continue
        if actor.meters.get("exposure", 0.0) < THRESHOLD:
            continue
        if not (actor.meters.get("noise", 0.0) >= THRESHOLD
                or actor.memes.get("lonely_mower", 0.0) >= THRESHOLD):
            continue
        world.fired.add(sig)
        actor.memes["danger"] += 1
        actor.memes["brave_pretend"] += 1
        out.append(
            f"{actor.pronoun().capitalize()} did not know that the spinning blade "
            f"hidden under the guard cannot tell grass from a shoe."
        )
    return out


def _r_parent_tenderness(world: World) -> list[str]:
    """The parent kneeling to explain accumulates tenderness."""
    for parent in world.characters():
        if parent.type not in {"mother", "father"}:
            continue
        sig = ("tender", parent.id)
        if sig in world.fired:
            continue
        if world.facts.get("knelt") and parent.memes["tenderness"] < THRESHOLD:
            world.fired.add(sig)
            parent.memes["tenderness"] += 1
    return []


def _r_resolution_clarity(world: World) -> list[str]:
    """Once the rule is named and the kid steps back, the confusion clears."""
    for actor in world.characters():
        if actor.memes.get("clarity", 0.0) >= THRESHOLD:
            continue
        sig = ("clarity", actor.id)
        if sig in world.fired:
            continue
        if (actor.memes.get("danger", 0.0) >= THRESHOLD
                and world.facts.get("rule_offered")
                and actor.memes.get("stepped_back", 0.0) >= THRESHOLD):
            world.fired.add(sig)
            actor.memes["clarity"] += 1
            actor.memes["shame"] = 0.0
    return []


def _r_child_pushed(world: World) -> list[str]:
    """If the child got to push the mower (with the parent holding on), bump
    pride on the child and the parent."""
    if not world.facts.get("child_pushed"):
        return []
    out: list[str] = []
    for actor in world.characters():
        if actor.type not in {"mother", "father", "girl", "boy"}:
            continue
        sig = ("pride", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["pride"] += 1
        out.append(
            f"{actor.pronoun().capitalize()} felt proud of the new job."
        )
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="close_to_blade", tag="physical", apply=_r_close_to_blade),
    Rule(name="parent_tenderness", tag="social", apply=_r_parent_tenderness),
    Rule(name="resolution_clarity", tag="social", apply=_r_resolution_clarity),
    Rule(name="child_pushed", tag="social", apply=_r_child_pushed),
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
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness gates (the constraint the inline ASP gate mirrors).
# ---------------------------------------------------------------------------
def activity_at_zone(activity: Activity, region: str) -> bool:
    """Would this activity actually reach this body region of the actor?"""
    return region in activity.zone


def select_rule(activity: Activity, region: str) -> Optional[RuleArtifact]:
    """The compatible safety rule -- the one whose guards neutralise the
    activity's mess and whose covers shield the at-risk region."""
    for rule in RULES:
        if activity.mess in rule.guards and region in rule.covers:
            return rule
    return None


# ---------------------------------------------------------------------------
# Prediction: the parent runs the world model forward to foresee danger.
# ---------------------------------------------------------------------------
def predict_danger(world: World, actor: Entity, activity: Activity,
                   region: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    a = sim.entities[actor.id]
    return {
        "danger": a.memes.get("danger", 0.0) >= THRESHOLD,
        "exposure": a.meters.get("exposure", 0.0) >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def activity_detail(activity: Activity) -> str:
    return {
        "mower": "the mower chugged along the lawn and made the grass lay down neat",
        "trimmer": "the trimmer whined close to the hedge and made the edges look tidy",
        "blower": "the blower whooshed the leaves into a tidy pile by the wall",
    }.get(activity.id, "the machine made its small busy sound")


def mower_sound_detail(mower: Entity) -> str:
    if mower.memes.get("sounds_busy", 0.0) >= THRESHOLD:
        return f"The {mower.type} sounded busy and full of purpose."
    return f"The {mower.type} made its small busy sound."


def setting_detail(setting: Setting) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was quiet, and a poster of a garden waited nearby."
    if setting.place == "the garden":
        return "The garden was bright, and the lawn looked ready for a tidy trim."
    if setting.place == "the park":
        return "The park was wide and sunny, and a long stretch of grass waited beside the path."
    if setting.place == "the backyard":
        return "The backyard was small but tidy, and a patch of grass waited in the middle."
    return f"{setting.place.capitalize()} was bright, and the lawn looked ready for a tidy trim."


def _do_activity(world: World, actor: Entity, activity: Activity,
                 narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.meters["exposure"] += 1
    actor.memes["desire"] += 1
    if narrate:
        world.say(activity_detail(activity))


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who liked helping out with grown-up jobs.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_help"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved watching {hero.pronoun('possessive')} "
        f"dad work, and the {activity.gerund} made the day feel like a tiny adventure."
    )


def dad_brings_mower(world: World, parent: Entity, hero: Entity,
                     activity: Activity) -> Entity:
    mower = world.add(Entity(
        id="mower", kind="thing", type="mower",
        label="mower", phrase="an old push mower with a tidy green paint",
        region=DANGER_ZONE, caretaker=parent.id,
    ))
    mower.memes["sounds_busy"] += 1
    world.say(
        f"One bright morning {hero.id}'s {parent.label_word} pulled out "
        f"{mower.phrase} and showed {hero.pronoun('object')} how it worked."
    )
    return mower


def dad_warns(world: World, parent: Entity, hero: Entity,
              mower: Entity) -> None:
    world.say(
        f'"{mower.label_word.capitalize() if mower.label_word else "It"} cuts, '
        f'and it does not know you are there," {hero.pronoun("possessive")} '
        f'{parent.label_word} said. "Stay well back."'
    )


def watch_mower(world: World, hero: Entity, activity: Activity,
                mower: Entity) -> None:
    world.say(mower_sound_detail(mower))
    hero.memes["lonely_mower"] += 1
    world.say(
        f"{hero.id} thought the {activity.gerund} made the {mower.label} sound lonely."
    )


def approaches(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["exposure"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} walked up behind the {activity.keyword} and waved."
    )


def greets_mower(world: World, hero: Entity, activity: Activity,
                 mower: Entity) -> None:
    hero.memes["attempt"] += 1
    world.say(
        f'The {mower.label} roared on. {hero.pronoun().capitalize()} waved '
        f'harder and called, "Hello, {mower.label}!"'
    )
    world.say(f"The {mower.label} did not turn its head, because {mower.label}s do not have heads.")


def misinterprets(world: World, hero: Entity, mower: Entity) -> None:
    hero.memes["misread"] += 1
    world.say(
        f"{hero.id} thought the {mower.label} was being rude, and "
        f"{hero.pronoun()} folded {hero.pronoun('possessive')} arms."
    )
    world.say(
        f'"Why won\'t you answer me?" {hero.pronoun()} asked.'
    )


def dad_kneels(world: World, parent: Entity, hero: Entity,
               mower: Entity) -> None:
    world.facts["knelt"] = True
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label_word} "
        f"laughed and knelt beside {hero.pronoun('object')}."
    )


def dad_explains(world: World, parent: Entity, hero: Entity,
                 activity: Activity, mower: Entity,
                 region: str) -> Optional[RuleArtifact]:
    """Offer the safety rule -- but only if it actually guards the at-risk
    region. If no rule exists for this activity+region, refuse."""
    rule_def = select_rule(activity, region)
    if rule_def is None:
        return None
    world.say(
        f'"It isn\'t being unkind," {hero.pronoun("possessive")} '
        f'{parent.label_word} said. "It cannot hear you. It only knows grass."'
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label_word} "
        f"showed {hero.pronoun('object')} the spinning blade hidden safely "
        f"under the guard."
    )
    world.say(
        f'"That is why I told you to {rule_def.prep} -- the bit that cuts '
        f'cannot tell a blade of grass from a shoe."'
    )
    return rule_def


def step_back(world: World, hero: Entity, rule_def: RuleArtifact) -> None:
    hero.memes["stepped_back"] += 1
    world.say(
        f"{hero.id} remembered the rule and {rule_def.tail}."
    )


def push_mower(world: World, hero: Entity, parent: Entity,
               mower: Entity, activity: Activity) -> None:
    world.facts["child_pushed"] = True
    world.facts["rule_offered"] = True
    world.say(
        f"Then {hero.pronoun('possessive')} {parent.label_word} let "
        f"{hero.pronoun('object')} push the {mower.label} along a gentle strip, "
        f"with {parent.pronoun('object')} holding the handle beside {hero.pronoun('object')}."
    )
    world.say(
        f"The {mower.label} hummed happily, the lawn grew neat, and "
        f"{hero.id} decided {hero.pronoun()} had a new job."
    )


def resolve(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["clarity"] += 1
    world.say(
        f"From then on {hero.id} asked the important question: would the lawn "
        f"please stand still? The {activity.keyword}, of course, never answered."
    )


# ---------------------------------------------------------------------------
# The screenplay.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity,
         hero_name: str = "Ada", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None,
         parent_type: str = "father",
         region: str = DANGER_ZONE) -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "cheerful"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type,
                              label="the parent"))

    # Act 1 -- setup.
    introduce(world, hero)
    loves_activity(world, hero, activity)
    mower = dad_brings_mower(world, parent, hero, activity)
    dad_warns(world, parent, hero, mower)

    # Act 2 -- the misunderstanding.
    world.para()
    watch_mower(world, hero, activity, mower)
    approaches(world, hero, activity)
    greets_mower(world, hero, activity, mower)
    misinterprets(world, hero, mower)
    _do_activity(world, hero, activity, narrate=False)   # silence; rule fires next
    propagate(world, narrate=False)                      # close_to_blade etc.

    # Act 3 -- the reveal + the rule.
    world.para()
    dad_kneels(world, parent, hero, mower)
    rule_def = dad_explains(world, parent, hero, activity, mower, region)
    if rule_def is None:
        raise StoryError(
            f"(No rule in the catalog guards {activity.gerund} at the "
            f"{region} of the mower. The reveal must actually cover the "
            f"at-risk region.)"
        )
    step_back(world, hero, rule_def)
    propagate(world, narrate=False)                      # resolution_clarity fires
    push_mower(world, hero, parent, mower, activity)
    resolve(world, hero, activity)

    world.facts.update(
        hero=hero, parent=parent, activity=activity, mower=mower,
        rule=rule_def, setting=setting, region=region,
        misunderstanding=True,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"mower", "trimmer"}),
    "park": Setting(place="the park", indoor=False, affords={"mower", "blower"}),
    "backyard": Setting(place="the backyard", indoor=False, affords={"mower", "trimmer"}),
}

ACTIVITIES = {
    # The classic push mower: blade zone is the cutter, handle is where the
    # pusher stands. The kid's "danger" comes from walking into the blade zone.
    "mower": Activity(
        id="mower",
        verb="push the mower",
        gerund="the mower chug",
        rush="walk up to the mower",
        mess="noise",
        soil="so loud it covers your voice",
        zone={"handle", "blade"},
        weather="sunny",
        keyword="mower",
        tags={"mower", "noise", "garden"},
    ),
    "trimmer": Activity(
        id="trimmer",
        verb="trim the hedge",
        gerund="the trimmer whined close to the hedge",
        rush="walk up to the trimmer",
        mess="noise",
        soil="so loud it covers your voice",
        zone={"blade"},
        weather="sunny",
        keyword="trimmer",
        tags={"trimmer", "noise", "garden"},
    ),
    "blower": Activity(
        id="blower",
        verb="blow the leaves",
        gerund="the blower whooshed",
        rush="walk up to the blower",
        mess="dust",
        soil="a cloud of dust in the air",
        zone={"handle"},
        weather="sunny",
        keyword="blower",
        tags={"blower", "dust", "garden"},
    ),
}

# Order matters: more specific rules first.
RULES = [
    RuleArtifact(
        id="stay_back_blade",
        label="stay well back from the cutting bit",
        covers={"blade"},
        guards={"noise", "dust"},
        prep="stay well back from the cutting bit",
        tail="stepped well back from the cutting bit",
    ),
    RuleArtifact(
        id="wear_ear_cover",
        label="wear an ear cover",
        covers={"blade"},
        guards={"noise"},
        prep="put on your ear cover first",
        tail="stepped back and put on the ear cover",
    ),
    RuleArtifact(
        id="hold_handle",
        label="hold the handle and stand behind it",
        covers={"handle"},
        guards={"noise", "dust"},
        prep="hold the handle and stand behind it",
        tail="stood behind the handle with two hands",
    ),
]

GIRL_NAMES = ["Ada", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Nora", "Rose", "Ivy"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "playful", "cheerful", "spirited", "lively", "brave", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(place, activity, region) triples that pass the reasonableness gate."""
    out: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for region in REGIONS:
                if activity_at_zone(act, region) and select_rule(act, region):
                    out.append((place, act_id, region))
    return out


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    region: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation.
# ---------------------------------------------------------------------------
# (3) Child-level world knowledge, keyed by topic.
KNOWLEDGE = {
    "mower": [
        ("What is a push mower?",
         "A push mower is a small wheeled machine with a spinning blade under "
         "a guard. A person walks behind it and pushes it forward to cut grass."),
        ("Why is a mower loud?",
         "A mower is loud because the spinning blade pushes the air very fast, "
         "and a small engine helps turn the blade. That fast motion makes the "
         "sound we hear."),
        ("Why do people stay back from a mower?",
         "People stay back from a mower because the spinning blade under the "
         "guard cannot tell grass from a shoe. Standing back keeps fingers and "
         "toes far from the cutting bit."),
    ],
    "trimmer": [
        ("What is a trimmer?",
         "A trimmer is a long-handled machine with a fast-spinning line or "
         "blade at the bottom. It tidies edges where a mower cannot reach."),
        ("Why is a trimmer loud?",
         "A trimmer is loud because the spinning line or blade pushes the air "
         "very fast, which makes the high whine we hear."),
    ],
    "blower": [
        ("What is a blower?",
         "A blower is a machine that pushes a strong stream of air. It is used "
         "to gather leaves into a tidy pile."),
        ("Why does a blower raise dust?",
         "A blower raises dust because the strong stream of air lifts tiny "
         "bits of dry soil and leaf powder into the air as it moves them."),
    ],
    "noise": [
        ("Why can a loud machine make it hard to hear a friend?",
         "A loud machine makes it hard to hear a friend because its sound is "
         "bigger than a voice, so the voice gets lost underneath it."),
    ],
    "dust": [
        ("Why do we try not to breathe in dust?",
         "We try not to breathe in dust because tiny bits of dirt and leaf "
         "powder can tickle the nose and throat and make us cough or sneeze."),
    ],
    "garden": [
        ("What does it mean to tidy the garden?",
         "Tidying the garden means cutting the grass, trimming the edges, and "
         "blowing the leaves into a pile so the garden looks neat and cared for."),
    ],
}
KNOWLEDGE_ORDER = ["mower", "trimmer", "blower", "noise", "dust", "garden"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, mower = f["hero"], f["parent"], f["activity"], f["mower"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old on the theme '
        f'"a misunderstanding, a grown-up who explains, a safer way" that '
        f'includes the word "{act.keyword}".',
        f"Tell a gentle adventure where a {hero.type} named {hero.id} misreads "
        f"the {mower.label} and thinks it is being rude, but a {parent.label_word} "
        f"kneels down and shows {hero.pronoun('object')} why the {mower.label} "
        f"only knows grass.",
        f'Write a simple story that uses the noun "{act.keyword}" and ends with '
        f"a child remembering a rule about staying back from a spinning blade.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, mower, rule = (
        f["hero"], f["parent"], f["activity"], f["mower"], f["rule"])
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    pw = parent.label_word
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the adventure about when {hero.id} meets the "
                f"{mower.label} at {place} on a sunny morning?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"{pos} {pw}. {pw.capitalize()} brought out an old push "
                f"{mower.label} to tidy the lawn, and {hero.id} came to watch."
            ),
        ),
        QAItem(
            question=(
                f"Why did {trait} {hero.id} think the {mower.label} was being "
                f"rude in the {place}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} waved at the {mower.label} and "
                f"called hello, but the {mower.label} did not turn its head, "
                f"because {mower.label}s do not have heads. So {hero.id} "
                f"thought it was being unkind."
            ),
        ),
        QAItem(
            question=(
                f"What did {hero.id}'s {pw} do when {trait} {hero.id} folded "
                f"{pos} arms at the {mower.label}?"
            ),
            answer=(
                f"{pos.capitalize()} {pw} laughed and knelt beside {obj}, then "
                f"showed {obj} the spinning blade hidden under the guard. "
                f"{pw.capitalize()} said the {mower.label} cannot hear and only "
                f"knows grass."
            ),
        ),
    ]
    if f.get("misunderstanding"):
        qa.append(QAItem(
            question=(
                f"What was the real reason the {mower.label} ignored "
                f"{trait} {hero.id} at {place}?"
            ),
            answer=(
                f"The {mower.label} did not ignore {obj}. It has no head and "
                f"no ears, so it cannot hear a wave or a hello. The loud sound "
                f"is just the spinning blade pushing the air fast, not a mind."
            ),
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            question=(
                f"What rule did {pw} share with {trait} {hero.id} about the "
                f"{mower.label} at {place}?"
            ),
            answer=(
                f"{pw.capitalize()} said the rule was: {rule.label}. The bit "
                f"that cuts cannot tell a blade of grass from a shoe, so "
                f"{hero.id} {rule.tail.rstrip('.')}."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} feel at the end of the {mower.label} "
                f"adventure at {place}?"
            ),
            answer=(
                f"{hero.id} felt proud and clear about the rule. {sub.capitalize()} "
                f"got to push the {mower.label} with {pw} beside {obj}, the lawn "
                f"grew neat, and {sub} decided {sub} had a new job."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
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
# CLI / trace.
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden", activity="mower", region="blade",
        name="Ada", gender="girl", parent="father", trait="curious",
    ),
    StoryParams(
        place="park", activity="mower", region="blade",
        name="Tim", gender="boy", parent="mother", trait="brave",
    ),
    StoryParams(
        place="garden", activity="trimmer", region="blade",
        name="Mia", gender="girl", parent="father", trait="cheerful",
    ),
    StoryParams(
        place="backyard", activity="blower", region="handle",
        name="Ben", gender="boy", parent="mother", trait="playful",
    ),
    StoryParams(
        place="garden", activity="mower", region="blade",
        name="Zoe", gender="girl", parent="father", trait="spirited",
    ),
]


def explain_rejection(activity: Activity, region: str) -> str:
    return (f"(No story: {activity.gerund} reaches {sorted(activity.zone)}, "
            f"but you asked for the {region}. The rule must actually shield the "
            f"at-risk region, so this argument is rejected.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% The activity reaches a region if the region is in the activity's zone.
reaches(A, R) :- activity(A), splashes(A, R).

% A rule is a compatible safety rule only when it guards the activity's mess
% AND covers the at-risk region (the spinning bit, or the handle).
is_compatible(Rule, A, Region) :- rule(Rule), reaches(A, Region),
                                  mess_of(A, M), guards(Rule, M),
                                  covers(Rule, Region).
has_rule(A, Region) :- is_compatible(_, A, Region).

valid(Place, A, Region) :- affords(Place, A), reaches(A, Region), has_rule(A, Region).
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
    for r in RULES:
        lines.append(asp.fact("rule", r.id))
        for m in sorted(r.guards):
            lines.append(asp.fact("guards", r.id, m))
        for c in sorted(r.covers):
            lines.append(asp.fact("covers", r.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mower misunderstanding adventure. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--region", choices=sorted(REGIONS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.region:
        act = ACTIVITIES[args.activity]
        if not (activity_at_zone(act, args.region)
                and select_rule(act, args.region)):
            raise StoryError(explain_rejection(act, args.region))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.region is None or c[2] == args.region)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, region = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, activity=activity, region=region,
        name=name, gender=gender, parent=parent, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 params.name, params.gender, [params.trait, "curious"],
                 params.parent, region=params.region)
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
        print(f"{len(triples)} compatible (place, activity, region) combos:\n")
        for place, act, region in triples:
            print(f"  {place:9} {act:8} {region:6}")
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
            header = f"### {p.name}: {p.activity} at {p.place} (region: {p.region})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
