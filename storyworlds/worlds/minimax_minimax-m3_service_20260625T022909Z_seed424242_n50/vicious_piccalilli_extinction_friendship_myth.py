#!/usr/bin/env python3
"""
storyworlds/worlds/vicious_piccalilli_extinction_friendship_myth.py
===================================================================

A standalone *story world* sketch in a TinyStories-friendly style, mixing
mythic register with a small, named domain.  Three seed words anchor the
world: ``vicious`` (a biting wind and the sharp, jagged cliff that
shelters none), ``piccalilli`` (a bright yellow relish traded at the
market, the prized good the two friends must keep safe), and
``extinction`` (the long-forgotten path of the great tusked things whose
traces are still felt).

Theme
-----
Friendship in a small, mythic village at the edge of a jagged cliff.
The wind is vicious, the tusked beasts of legend are gone, and only
the smell of the new piccalilli keeps the winter market alive.  Two
children must save a jar from a coming storm by working together.

Causal state updates
--------------------
    wind rises (vicious)        -> cliff.echo++, actor.cold++
    do carry                    -> actor.care++
    jar fragile + wind          -> jar.crack++                    only if no
                                                                     cover
    cover held over the jar     -> jar.crack=0 ; actor.care++
    final shared song           -> bond ++, tension 0

Scripted emotional beats
------------------------
    warning heard               -> actor.caution ++
    warning ignored             -> actor.defiance ++
    hand clasped                -> bond.friendship ++
    shared work done            -> bond.myth ++                  (the ending)
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

# Make the shared result containers importable when this script is run
# directly: add the parent package directory to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# The cliff is jagged; the wind hits faces, hands, and jars.
ZONES = {"face", "hands", "jar"}
# The kinds of harm the world tracks; "vicious" is the wind's biting cold.
HARM_KINDS = {"vicious", "smashed"}


# ---------------------------------------------------------------------------
# Entities: characters, places, and prized objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"           # "character" | "place" | "thing"
    type: str = "thing"           # friend, elder, jar, cliff, market ...
    label: str = ""               # short reference, e.g. "the jar", "the cliff"
    phrase: str = ""              # full noun phrase used in prose
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    held_by: Optional[str] = None         # who is currently holding/covering it
    region: str = ""                      # where on the body / landscape it sits
    protective: bool = False              # covers another thing from harm
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "elder", "mother", "woman"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "elder": "the elder",
                "uncle": "uncle"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    name: str                          # "the village of Cragpenny"
    place_phrase: str                  # the phrase used in prose
    affords: set[str]                  # which activities this place supports
    extinct_thing: str                 # the vanished creature/people
    extinct_whisper: str               # the mythic phrase said about them


@dataclass
class Activity:
    id: str
    verb: str                          # after "wanted to ..."            "carry the jar to market"
    gerund: str                        # after "loved ..."                 "carrying the bright jar"
    rush: str                          # after "tried to ..."              "run toward the cliff road"
    mess: str                          # harm key, one of HARM_KINDS       "vicious"
    zone: set[str]                     # body / jar regions the activity harms
    weather: str                       # "windy" | "still" | ""
    keyword: str = ""                  # "piccalilli", "cliff", "extinction"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str                          # "jar", "satchel", "parcel"
    region: str                        # face | hands | jar
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Cover:
    """Protective gear / object that shields the prize from the named harm."""
    id: str
    label: str
    covers: set[str]                   # regions it shields
    guards: set[str]                   # harm kinds it neutralises
    prep: str                          # body of the offer
    tail: str                          # closing clause after the plan is made
    plural: bool = False


@dataclass
class Bond:
    """Friendship between the two characters; the theme and the ending."""
    id: str
    phrase: str                        # full noun phrase for the bond
    short: str                         # short reference, e.g. "their bond"
    shared_song: str                   # the song that resolves the tale
    shared_phrase: str                 # the line that proves what changed


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

    def carried(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

    def covered(self, prize: Entity, region: str) -> bool:
        """Is `prize` (in `region`) shielded by some held cover?"""
        for e in self.entities.values():
            if e.protective and region in e.covers and e.held_by is not None:
                return True
        return False

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


def _r_bite(world: World) -> list[str]:
    """vicious wind + uncovered prize in zone -> prize.crack and prize.smashed."""
    out: list[str] = []
    for prize in [e for e in world.entities.values()
                  if e.kind == "thing" and e.region in ZONES]:
        if prize.meters["vicious"] < THRESHOLD:
            continue
        for region in ZONES:
            if region not in world.zone:
                continue
            if world.covered(prize, region):
                continue
            sig = ("bite", prize.id, region)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            prize.meters["crack"] += 1
            prize.meters["smashed"] += 1
            out.append(
                f"the {prize.label} cracked from the vicious wind on the {region}."
            )
    return out


def _r_cold(world: World) -> list[str]:
    """vicious wind on the cliff -> every character is colder."""
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["vicious"] < THRESHOLD:
            continue
        sig = ("cold", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["cold"] += 1
    return out


def _r_grab_friendship(world: World) -> list[str]:
    """A warning + a hand clasped + a shared duty -> bond.friendship."""
    bond = world.entities.get("bond")
    if not bond:
        return []
    for actor in world.characters():
        if (actor.memes["caution"] < THRESHOLD
                or actor.memes["clasped"] < THRESHOLD):
            continue
        sig = ("friendship", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        bond.memes["friendship"] += 1
    return []


def _r_song_myth(world: World) -> list[str]:
    """Bond high + jar still intact -> the tale enters the mythic register."""
    bond = world.entities.get("bond")
    prize = world.entities.get("prize")
    if not (bond and prize):
        return []
    if bond.memes["friendship"] < THRESHOLD or prize.meters["crack"] >= THRESHOLD:
        return []
    sig = ("myth", "shared_song")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bond.memes["myth"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="bite", tag="physical", apply=_r_bite),
    Rule(name="cold", tag="physical", apply=_r_cold),
    Rule(name="friendship", tag="social", apply=_r_grab_friendship),
    Rule(name="myth", tag="mythic", apply=_r_song_myth),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires (forward chaining to fixpoint)."""
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers: when is this a *reasonable* story?
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    """Would this activity actually harm this prize (right region)?"""
    return prize.region in activity.zone


def select_cover(activity: Activity, prize: Prize) -> Optional[Cover]:
    """A cover that guards the harm AND covers the at-risk region."""
    for cover in COVERS:
        if activity.mess in cover.guards and prize.region in cover.covers:
            return cover
    return None


# ---------------------------------------------------------------------------
# Prediction: forward-simulate to see whether the prize would survive the
# activity without a cover.  Used by the elder's warning beat.
# ---------------------------------------------------------------------------
def predict_harm(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "cracked": bool(prize and prize.meters["crack"] >= THRESHOLD),
        "cold": bool(actor.meters["cold"] >= THRESHOLD),
    }


# ---------------------------------------------------------------------------
# Beats (verbs): each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def setting_detail(setting: Setting, activity: Activity) -> str:
    if activity.weather == "windy":
        return (f"Along the {setting.name}, the wind came in vicious gusts "
                f"off the high cliff, and small stones went clicking.")
    return f"{setting.name.capitalize()} was quiet, and the long cliff stood in shadow."


def extinct_phrase(setting: Setting) -> str:
    return (f"They say the {setting.extinct_thing} once walked this very path, "
            f"and that is why the wind still {setting.extinct_whisper}.")


def prize_was_safe(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed whole and bright"


def _do_activity(world: World, actor: Entity, activity: Activity,
                 narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["care"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who liked the path that ran along the cliff.")


def knows_legend(world: World, hero: Entity, setting: Setting) -> None:
    world.say(extinct_phrase(setting))
    world.say(
        f"{hero.id} listened for the wind's whisper, and thought of the "
        f"{setting.extinct_thing} who had walked there long before."
    )


def knows_prize(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"The prized {prize.label} of the village was {prize.phrase}, and "
        f"the market would only be kind if it was carried home unbroken."
    )


def the_prize_is_set(world: World, hero: Entity, prize: Entity) -> None:
    prize.carried_by = hero.id
    world.say(
        f"That week, the village chose {hero.id} to carry the {prize.label} "
        f"back to the market, and the bright colour shone like a small sun."
    )


def arrive(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    day = {"windy": "On a windy morning, "}.get(world.weather, "On a clear morning, ")
    world.say(
        f"{day}{hero.id} and {friend.id} set out along the cliff path, "
        f"and the {hero.pronoun('possessive')} {prize_label_for(world)} was in "
        f"{hero.pronoun('possessive')} arms."
    )
    world.say(setting_detail(world.setting, activity))


def prize_label_for(world: World) -> str:
    p = world.entities.get("prize")
    return p.label if p else "jar"


def elder_warns(world: World, hero: Entity, activity: Activity, prize: Entity) -> bool:
    """The elder foresees the harm via the world model and warns about it."""
    pred = predict_harm(world, hero, activity, prize.id)
    if not (pred["cracked"] or pred["cold"]):
        return False
    world.facts["predicted_crack"] = pred["cracked"]
    world.facts["predicted_cold"] = pred["cold"]
    bit = (f"that vicious gusts would crack the {prize.label}"
           if pred["cracked"] else
           f"that the cold would bite {hero.pronoun('object')}")
    world.say(
        f'The village elder called after them, "Mind the cliff, children -- '
        f'{bit}."'
    )
    return True


def defies_warning(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    hero.memes["caution"] += 1
    world.say(
        f"{hero.id} heard the warning, but the path was bright and the wind "
        f"had been quiet all morning."
    )


def wind_rises(world: World, activity: Activity) -> None:
    world.weather = "windy"
    world.say(
        "But the wind was not quiet for long, and the gusts came vicious and "
        "loud, throwing grit at small faces."
    )


def tries_to_run(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["caution"] += 1
    world.say(
        f"{hero.id} tried to {activity.rush}, but the wind was stronger than "
        f"{hero.pronoun('object')}, and {hero.pronoun('possessive')} arms were "
        f"heavy with the {prize_label_for(world)}."
    )


def friend_appears(world: World, hero: Entity, friend: Entity) -> None:
    friend.memes["caution"] += 1
    world.say(
        f"{friend.id} ran up beside {hero.id} and called out, "
        f'"Wait -- let me help with the cover, and we will hold it together."'
    )


def clasp_hands(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["clasped"] += 1
    friend.memes["clasped"] += 1
    hero.memes["defiance"] = 0.0
    world.say(
        f"{hero.id} clasped {friend.id}'s hand, and the two of them stood "
        f"shoulder to shoulder against the cliff."
    )


def cover_offer(world: World, hero: Entity, friend: Entity, activity: Activity,
                prize: Entity) -> Optional[Cover]:
    cover_def = select_cover(activity, prize)
    if cover_def is None:
        return None
    cover = world.add(Entity(
        id=cover_def.id, type="cover", label=cover_def.label,
        owner=hero.id, protective=True, covers=set(cover_def.covers),
        plural=cover_def.plural,
    ))
    cover.held_by = friend.id
    if predict_harm(world, hero, activity, prize.id)["cracked"]:
        cover.held_by = None
        del world.entities[cover.id]
        return None
    world.say(
        f'"{cover_def.prep.capitalize() if not cover_def.prep[0].isupper() else cover_def.prep}, '
        f'and I will hold the cover over the {prize.label}," {friend.id} said.'
    )
    return cover_def


def carry_together(world: World, hero: Entity, friend: Entity,
                   activity: Activity, prize: Entity, cover_def: Cover) -> None:
    hero.memes["care"] += 1
    friend.memes["care"] += 1
    world.say(
        f"They {cover_def.tail}, and soon {hero.id} and {friend.id} were "
        f"{activity.gerund} side by side, the cover held high."
    )


def shared_song(world: World, hero: Entity, friend: Entity, prize: Entity,
                bond: Bond) -> None:
    world.say(
        f"When the path finally opened to the market, the {prize.label} was "
        f"{prize_was_safe(hero, prize)} in {hero.pronoun('possessive')} arms, "
        f"and {friend.pronoun('subject')} was laughing at {hero.pronoun('object')}."
    )
    world.say(
        f"They sang {bond.shared_song}, and the market folk said the wind "
        f"never sounded so tame."
    )
    world.say(
        f"From that day on, the children of {world.setting.name} told the "
        f"story as a myth, and the verse the two friends had sung became a "
        f"line for the next travellers along the cliff."
    )


# ---------------------------------------------------------------------------
# The screenplay: three-act shape, driven by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         bond: Bond, cover_default: Cover,
         hero_name: str = "Wren", friend_name: str = "Theo",
         hero_type: str = "girl", friend_type: str = "boy",
         hero_traits: Optional[list[str]] = None,
         friend_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["brave", "stubborn"]),
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_type,
        traits=["little"] + (friend_traits or ["quick", "kind"]),
    ))
    elder = world.add(Entity(
        id="Elder", kind="character", type="elder", label="the village elder",
    ))
    prize = world.add(Entity(
        id="prize", kind="thing", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    world.add(Entity(
        id="bond", kind="thing", type="bond", label=bond.short,
        phrase=bond.phrase,
    ))

    # Act 1 -- setup: the village, the legend, the prized piccalilli.
    introduce(world, hero)
    knows_legend(world, hero, setting)
    knows_prize(world, hero, prize)
    the_prize_is_set(world, hero, prize)

    # Act 2 -- conflict: warning, defiance, vicious wind, a friend at the cliff.
    world.para()
    arrive(world, hero, friend, activity)
    elder_warns(world, hero, activity, prize)
    defies_warning(world, hero)
    wind_rises(world, activity)
    _do_activity(world, hero, activity, narrate=True)
    tries_to_run(world, hero, activity)

    # Act 3 -- resolution: cover, shared work, the shared song (myth).
    world.para()
    friend_appears(world, hero, friend)
    clasp_hands(world, hero, friend)
    cover_def = cover_offer(world, hero, friend, activity, prize)
    if cover_def is None:
        cover_def = cover_default
    carry_together(world, hero, friend, activity, prize, cover_def)
    shared_song(world, hero, friend, prize, bond)

    # World facts read by the Q&A generators.
    world.facts.update(
        hero=hero, friend=friend, elder=elder, prize=prize, prize_cfg=prize_cfg,
        activity=activity, setting=setting, cover=cover_def, bond=bond,
        conflict=hero.memes["defiance"] >= THRESHOLD or hero.meters["cold"] >= THRESHOLD,
        resolved=cover_def is not None,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "cragpenny": Setting(
        id="cragpenny",
        name="the village of Cragpenny",
        place_phrase="along the cliff path above Cragpenny",
        affords={"carry"},
        extinct_thing="tusked ones",
        extinct_whisper="remembers their slow footfall",
    ),
    "hollowmere": Setting(
        id="hollowmere",
        name="the village of Hollowmere",
        place_phrase="around the dark lake at Hollowmere",
        affords={"carry"},
        extinct_thing="bright-scaled eels",
        extinct_whisper="hums under the ice",
    ),
}

ACTIVITIES = {
    "carry": Activity(
        id="carry",
        verb="carry the piccalilli to market",
        gerund="carrying the bright jar",
        rush="run ahead of the wind",
        mess="vicious",
        zone={"face", "hands", "jar"},
        weather="windy",
        keyword="piccalilli",
        tags={"piccalilli", "vicious", "extinction", "friendship"},
    ),
}

# Order matters: more specific cover first.
COVERS = [
    Cover(
        id="cloth",
        label="a strong cloth",
        covers={"jar"},
        guards={"vicious"},
        prep="take this strong cloth",
        tail="held the strong cloth high between them",
    ),
    Cover(
        id="basket",
        label="a woven basket",
        covers={"jar", "hands"},
        guards={"vicious"},
        prep="set the jar in the woven basket",
        tail="tucked the jar into the woven basket and held it between them",
    ),
    Cover(
        id="satchel",
        label="a sturdy satchel",
        covers={"jar", "face", "hands"},
        guards={"vicious"},
        prep="zip the jar into the sturdy satchel",
        tail="zipped the jar into the sturdy satchel and walked close together",
    ),
]

PRIZES = {
    "jar": Prize(
        label="jar of piccalilli",
        phrase="a small jar of bright piccalilli, the colour of warm hay",
        type="jar",
        region="jar",
    ),
    "satchel": Prize(
        label="satchel of piccalilli",
        phrase="a leather satchel full of fresh piccalilli, sealed with wax",
        type="satchel",
        region="jar",
    ),
    "parcel": Prize(
        label="parcel of piccalilli",
        phrase="a brown paper parcel of piccalilli, tied with string",
        type="parcel",
        region="jar",
    ),
}

BONDS = {
    "clasp": Bond(
        id="clasp",
        phrase="a hand-clasp bound in old rhyme",
        short="the hand-clasp",
        shared_song=("a small rhyme that went, \"Wind may bite and wind may "
                     "call, two held hands will not let fall.\""),
        shared_phrase="Two held hands will not let fall.",
    ),
    "promise": Bond(
        id="promise",
        phrase="a whispered promise the cliff keeps",
        short="the whispered promise",
        shared_song=("a quiet verse, \"Hills may sleep and stars may turn, "
                     "kindness keeps the fire that burn.\""),
        shared_phrase="Kindness keeps the fire that burns.",
    ),
    "name": Bond(
        id="name",
        phrase="a name each one had earned on the cliff",
        short="the cliff name",
        shared_song=("a soft call, \"Call the name, call the name, "
                     "echo brings the climber home.\""),
        shared_phrase="Echo brings the climber home.",
    ),
}

GIRL_NAMES = ["Wren", "Mara", "Aila", "Nell", "Sora", "Pip", "Iris", "Juniper"]
BOY_NAMES = ["Theo", "Bram", "Oren", "Wynn", "Faelan", "Kit", "Cobb", "Lin"]
TRAITS = ["brave", "curious", "stubborn", "cheerful", "spirited", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(setting, activity, prize) triples that pass the reasonableness gate."""
    combos = []
    for sid, s in SETTINGS.items():
        for aid in s.affords:
            act = ACTIVITIES[aid]
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_cover(act, prize):
                    combos.append((sid, aid, pid))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    setting: str
    activity: str
    prize: str
    bond: str
    name: str
    friend: str
    gender: str
    friend_gender: str
    trait: str
    friend_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "piccalilli": [("What is piccalilli?",
                    "Piccalilli is a bright yellow relish made from chopped "
                    "vegetables and mustard, often eaten with bread or cheese.")],
    "vicious": [("What does a vicious wind feel like?",
                 "A vicious wind is a strong, biting wind that stings your face "
                 "and makes small things shake in your hands.")],
    "extinction": [("What does it mean when a kind of animal has gone extinct?",
                    "When a kind of animal has gone extinct, it means no more of "
                    "that animal are alive, and the world has them only in "
                    "old stories and bones.")],
    "friendship": [("What is friendship?",
                    "Friendship is the warm feeling between people who like "
                    "each other and choose to help and stand by one another.")],
    "cliff": [("Why is a cliff path dangerous in wind?",
               "A cliff path is dangerous in wind because the gusts can push "
               "small bodies sideways and make it hard to keep hold of "
               "things you are carrying.")],
    "cloth": [("What does a strong cloth do in the wind?",
               "A strong cloth held up high can block the wind, so the wind "
               "does not hit whatever is under it so hard.")],
    "basket": [("Why carry something fragile in a basket?",
                "A basket holds the fragile thing steady and keeps it from "
                "sliding, so it is less likely to crack on the way.")],
    "satchel": [("What is a satchel for?",
                 "A satchel is a soft bag with a strap, used to carry small "
                 "things safely against the body.")],
    "market": [("What happens at a village market?",
                "A village market is a place where people bring goods to "
                "trade, and neighbours meet to share news and food.")],
}
KNOWLEDGE_ORDER = ["piccalilli", "vicious", "extinction", "friendship", "cliff",
                   "cloth", "basket", "satchel", "market"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, act, prize, bond = (f["hero"], f["friend"], f["activity"],
                                      f["prize_cfg"], f["bond"])
    return [
        f'Write a short, gentle mythic story that includes the words '
        f'"{act.keyword}", "{SETTINGS[f["setting"].id if False else world.setting.id].extinct_thing}", '
        f'and ends with a line about friendship.',
        f'Tell a story where {hero.id} and {friend.id} must carry {prize.phrase} '
        f'past a vicious wind on a cliff, and a small verse they sing at the end '
        f'becomes a myth the village will remember.',
        f'Use a mythic register and a TinyStories-friendly tone to write about '
        f'friendship, extinction, and a jar of piccalilli carried to market.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, act, bond = (f["hero"], f["friend"], f["prize"],
                                      f["activity"], f["bond"])
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    fsub, fobj, fpos = (friend.pronoun("subject"), friend.pronoun("object"),
                        friend.pronoun("possessive"))
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    ftrait = next((t for t in friend.traits if t != "little"), friend.type)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who sets out from {world.setting.name} to carry {prize.phrase} "
                f"to the market along the cliff path?"
            ),
            answer=(
                f"A little {trait} {hero.type} named {hero.id} and a {ftrait} "
                f"{friend.type} named {friend.id} set out together to carry "
                f"{prize.phrase} to the village market."
            ),
        ),
        QAItem(
            question=(
                f"What did the village elder warn {hero.id} about on the cliff path?"
            ),
            answer=(
                f"The village elder warned {hero.id} that the wind was vicious "
                f"and could crack the {prize.label} or bite at small hands if "
                f"they did not keep it covered."
            ),
        ),
        QAItem(
            question=(
                f"Why did {hero.id} listen to the warning after the wind rose "
                f"along the cliff?"
            ),
            answer=(
                f"{hero.id} had tried to keep going alone, but the vicious wind "
                f"was stronger than {pos} arms. {friend.id} ran up and called "
                f"{obj} to wait, and {hero.id} clasped {friend.id}'s hand so "
                f"they could hold a cover over the {prize.label} together."
            ),
        ),
    ]
    if f.get("resolved"):
        cover = f["cover"]
        qa.append(QAItem(
            question=(
                f"How did {cover.label} help {hero.id} and {friend.id} carry the "
                f"{prize.label} safely along the cliff?"
            ),
            answer=(
                f"{friend.id} held {cover.label} over the {prize.label} while "
                f"they walked close together, so the vicious wind could not "
                f"crack the jar. The plan let {obj} carry {prize.phrase} all "
                f"the way to the market without harm."
            ),
        ))
    qa.append(QAItem(
        question=(
            f"What verse did {hero.id} and {friend.id} sing at the market to "
            f"mark their friendship?"
        ),
        answer=(
            f"They sang {bond.shared_song}, and the market folk said the wind "
            f"never sounded so tame. The verse became a small myth the village "
            f"told after that day."
        ),
    ))
    qa.append(QAItem(
        question=(
            f"What did the wind whisper about the {world.setting.extinct_thing} "
            f"on the cliff above {world.setting.name}?"
        ),
        answer=(
            f"They say the {world.setting.extinct_thing} once walked the cliff "
            f"path, and that is why the wind still {world.setting.extinct_whisper}. "
            f"{hero.id} listened for that whisper on the way to the market."
        ),
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    tags.add(f["prize"].type)
    if f.get("cover"):
        tags.add(f["cover"].id)
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
# CLI / trace helpers.
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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set used by --all.
CURATED = [
    StoryParams(
        setting="cragpenny",
        activity="carry",
        prize="jar",
        bond="clasp",
        name="Wren",
        friend="Theo",
        gender="girl",
        friend_gender="boy",
        trait="brave",
        friend_trait="quick",
    ),
    StoryParams(
        setting="hollowmere",
        activity="carry",
        prize="satchel",
        bond="promise",
        name="Mara",
        friend="Bram",
        gender="girl",
        friend_gender="boy",
        trait="curious",
        friend_trait="kind",
    ),
    StoryParams(
        setting="cragpenny",
        activity="carry",
        prize="parcel",
        bond="name",
        name="Aila",
        friend="Oren",
        gender="girl",
        friend_gender="boy",
        trait="spirited",
        friend_trait="lively",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return (f"(No story: the {activity.gerund} threatens {sorted(activity.zone)}, "
                f"but a {prize.label} sits on the {prize.region} -- it would not "
                f"be harmed, so the elder has no honest warning. "
                f"Try a prize on {sorted(activity.zone)}.)")
    return (f"(No story: nothing in the cover catalog protects a {prize.label} "
            f"({prize.region}) from the {activity.gerund}. The cover must actually "
            f"shield the at-risk region, so this argument is rejected.)")


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return (f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s "
            f"item here; try --gender {ok}.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (prize_at_risk / select_cover / valid_combos).  Inline rules below; facts
# are generated from the registries above so the two can never drift.  Uses
# the shared `asp` helper + clingo, imported lazily so the prose engine runs
# without them.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk when the activity harms the region it sits on.
prize_at_risk(A, P) :- harms(A, R), worn_on(P, R).

% A cover is a compatible fix when it both neutralises the harm AND covers
% the at-risk region (a strong cloth guards vicious wind but only covers
% the jar, not the face).
protects(C, A, P) :- cover(C), prize_at_risk(A, P),
                     harm_of(A, M), guards(C, M),
                     covers(C, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).

valid(Setting, A, P) :- affords(Setting, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Setting, A, P) :- valid(Setting, A, P).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
        lines.append(asp.fact("extinct", sid, s.extinct_thing))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("harm_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("harms", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for c in COVERS:
        lines.append(asp.fact("cover", c.id))
        for m in sorted(c.guards):
            lines.append(asp.fact("guards", c.id, m))
        for r in sorted(c.covers):
            lines.append(asp.fact("covers", c.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (setting, activity, prize) triples."""
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
    clingo_set = {tuple(sorted(t)) for t in asp_valid_combos()}
    python_set = {tuple(sorted(t)) for t in valid_combos()}
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
        description="Mythic story world: two children, a jar of piccalilli, "
                    "a vicious wind, and a friendship that ends in song.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--bond", choices=BONDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"],
                    help="kept for CLI symmetry; the elder is the speaker.")
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
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
    """Fill in unspecified choices at random, keeping the combo reasonable."""
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_cover(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, activity_id, prize_id = rng.choice(sorted(combos))
    bond_id = args.bond or rng.choice(sorted(BONDS))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    friend_trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id, activity=activity_id, prize=prize_id, bond=bond_id,
        name=name, friend=friend, gender=gender, friend_gender=friend_gender,
        trait=trait, friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity],
                 PRIZES[params.prize], BONDS[params.bond], COVERS[0],
                 params.name, params.friend, params.gender, params.friend_gender,
                 [params.trait, "stubborn"], [params.friend_trait, "kind"])
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, activity, prize) combos:\n")
        for setting, act, prize in triples:
            print(f"  {setting:11} {act:6} {prize:9}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2,
                             ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (f"### {p.name} & {p.friend}: carrying the {p.prize} "
                      f"from {p.setting} ({p.bond} bond)")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
