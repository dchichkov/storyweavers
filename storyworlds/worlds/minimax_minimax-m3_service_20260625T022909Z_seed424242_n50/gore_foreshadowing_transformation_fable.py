#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/gore_foreshadowing_transformation_fable.py
==============================================================================================================

A standalone *story world* for a tiny TinyStories-style domain: a Fable about
a small animal who finds a sharp bone in the forest, is warned by an elder
about the danger of the cut it carries, and learns that the very splinter
that hurt becomes the carved whistle that saves the flock from a hidden hawk.

The seed word is **gore**. We use it carefully: there is no graphic violence
in the prose; instead we narrate the *consequences* -- a paw that bleeds, a
feather that is torn, a wound that is cleaned and bandaged. The fable voice
keeps it child-facing by speaking of "drops of red" rather than vivid injury.

Narrative instruments:
  * **Foreshadowing** -- the elder's warning (about the sharp thing in the
    grass) and the "small sound that saved them" planted before the storm.
  * **Transformation** -- the painful splinter becomes the carved whistle,
    and the bleeding paw becomes the paw that whistles the warning.
  * **Fable style** -- named animal characters, a short moral at the end,
    a gentle talking-animal voice, a clear three-act shape.

Causal state updates:
  -- find_splinter  -> hero.wound += 1, hero.bleeds += 1, scene.bone += 1
  -- wound ignored  -> hero.pain += 1, hero.weary += 1
  -- elder warned   -> elder.wisdom_used += 1 (only after a find_splinter)
  -- elder cleans   -> hero.wound -> 0, hero.bleeds -> 0, elder.care += 1
  -- carver shapes  -> splinter.shaped += 1, hero.hope += 1
  -- whistle blown  -> flock.saved += 1, hero.role += "sentinel"
  -- hawk struck    -> feather.broken += 1, flock.fear -> 0

Scripted social/emotional beats:
  -- warning ignored          -> hero.defiance += 1
  -- elder speaks gentle      -> elder.kindness += 1
  -- hero shares the lesson   -> hero.kindness += 1, hero.role -> "elder-seed"
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
# directly (``python .../gore_foreshadowing_transformation_fable.py``).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Body regions used by the gear/coverage constraints (the elder's cloth, etc.).
REGIONS = {"paw", "leg", "wing", "beak", "tail"}

# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # rabbit, mouse, deer, owl, elder, bone ...
    label: str = ""                # short reference, e.g. "elder"
    phrase: str = ""               # full noun phrase, e.g. "a small grey rabbit"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""              # where the thing sits on the body
    protective: bool = False      # gear / covering that shields something
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    # Two numeric dimensions: physical (meters) and emotional (memes).
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"doe", "vixen", "hen", "she-wolf", "owl-mother"}
        male = {"buck", "ram", "fox", "cock", "owl-father", "stag"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"owl-mother": "owl-mother", "owl-father": "owl-father",
                "she-wolf": "she-wolf"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this small fable domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the forest path"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    """The dangerous thing the hero finds in the grass.

    The seed word 'gore' lives here: hazards carry a 'soil' word that is the
    child-facing consequence of being cut ("drops of red", "a small red mark").
    """
    id: str
    label: str             # "splinter", "thorn", "sharp bone", "broken glass"
    phrase: str            # "a sharp splinter of bone"
    verb: str              # the moment of finding: "found a sharp splinter"
    rush: str              # the hero reaching for it: "reach for the sharp splinter"
    soil: str              # the consequence shown: "a small red mark"
    zone: set[str]         # body regions the hazard reaches: {"paw"}
    foreshadow: str        # a line the elder says *before* the hero finds it
    after_sound: str       # the sound the carved whistle makes
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    """The small helpful thing the elder offers -- bandage, leaf, salve."""
    label: str
    phrase: str
    type: str              # "bandage", "leaf-wrap", "moss-poultice"
    region: str            # paws | wing | tail
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"rabbit", "mouse", "fox"})


@dataclass
class Helper:
    """The elder's tool -- the thing that helps the hero clean up or shape."""
    id: str
    label: str             # "small wooden bowl", "smooth river stone", "carving knife"
    verb: str              # "used the smooth river stone to press the moss"
    tail: str              # "the elder pressed the moss with a smooth river stone"


@dataclass
class Adversary:
    """The hawk / fox / weasel who threatens the flock at the end."""
    id: str
    label: str             # "the silent hawk"
    noun: str              # "hawk"
    rush: str              # "drove down from the pine"
    sound: str             # "a sharp shadow over the path"
    prey: str              # what it wanted: "the smallest rabbit"
    foil: str              # what beats it: "the whistle, blown sharp and clear"


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


def _r_wound(world: World) -> list[str]:
    """hero found a sharp thing -> wound + bleeds; elder's foresight tracks it."""
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["bone"] < THRESHOLD:
            continue
        for hazard_label in world.facts.get("hazards_taken", []):
            sig = ("wound", actor.id, hazard_label)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.meters["wound"] += 1
            actor.meters["bleeds"] += 1
            out.append(
                f"{actor.pronoun('possessive').capitalize()} paw came away with "
                f"a small red mark from the {hazard_label}."
            )
    return out


def _r_pain_ignored(world: World) -> list[str]:
    """wound + (no elder cleansing yet) -> pain + weary."""
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wound"] < THRESHOLD or actor.meters["bleeds"] < THRESHOLD:
            continue
        if actor.memes["cleansed"] >= THRESHOLD:
            continue
        sig = ("pain", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["pain"] += 1
        actor.meters["weary"] += 1
        out.append(
            f"The small cut kept stinging; {actor.id} grew quiet and tired."
        )
    return out


def _r_cleansed(world: World) -> list[str]:
    """elder cleans the wound -> wound clears; elder care += 1."""
    out: list[str] = []
    for elder in world.characters():
        if elder.meters["care_given"] < THRESHOLD:
            continue
        for actor in world.characters():
            if actor.id == elder.id:
                continue
            if actor.meters["wound"] < THRESHOLD:
                continue
            sig = ("cleansed", actor.id, elder.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.meters["wound"] = 0.0
            actor.meters["bleeds"] = 0.0
            actor.meters["pain"] = 0.0
            actor.memes["cleansed"] += 1
            elder.memes["care"] += 1
            out.append(
                f"The elder pressed the soft moss against the paw and held it "
                f"until the small red mark faded."
            )
    return out


def _r_carved(world: World) -> list[str]:
    """splinter shaped -> splinter.shaped += 1, hero.hope += 1."""
    out: list[str] = []
    for shard in world.entities.values():
        if shard.type != "shard" or shard.meters["shaped"] < THRESHOLD:
            continue
        sig = ("carved", shard.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for hero in world.characters():
            if hero.memes["love_play"] >= THRESHOLD:
                hero.memes["hope"] += 1
        out.append(
            f"With patient strokes, the elder shaped the {shard.label} into a "
            f"small whistle."
        )
    return out


def _r_saved(world: World) -> list[str]:
    """whistle blown -> flock.saved += 1; hero.role -> sentinel."""
    out: list[str] = []
    if world.facts.get("whistle_blown") is not True:
        return out
    sig = ("saved", "flock")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for hero in world.characters():
        if hero.memes["hope"] >= THRESHOLD:
            hero.memes["role"] = 1.0
    out.append(
        "The flock heard the small sharp whistle and ran for the low brush; "
        "the hawk turned away on empty wings."
    )
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wound", tag="physical", apply=_r_wound),
    Rule(name="pain_ignored", tag="physical", apply=_r_pain_ignored),
    Rule(name="cleansed", tag="social", apply=_r_cleansed),
    Rule(name="carved", tag="physical", apply=_r_carved),
    Rule(name="saved", tag="social", apply=_r_saved),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Forward-chain to fixpoint."""
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
# Constraint helpers -- what is a *reasonable* hazard and a *reasonable* fix.
# ---------------------------------------------------------------------------
def hazard_at_paw(hazard: Hazard, prize: Prize) -> bool:
    """Would this hazard actually reach a region the prize protects?"""
    return prize.region in hazard.zone


def select_helper(hazard: Hazard, prize: Prize) -> Optional[Helper]:
    """The compatible elder-tool: a helper who can press / bind / carve.

    For our tiny domain any helper works once a prize shields the at-risk
    region; we keep the gate for symmetry with the other worlds.
    """
    if hazard_at_paw(hazard, prize):
        return HELPERS[0]
    return None


# ---------------------------------------------------------------------------
# Prediction: the elder runs the world model forward to foresee the cut.
# ---------------------------------------------------------------------------
def predict_wound(world: World, actor: Entity, hazard: Hazard) -> dict:
    sim = world.copy()
    _do_find(sim, sim.get(actor.id), hazard, narrate=False)
    return {
        "wounded": sim.entities[actor.id].meters["wound"] >= THRESHOLD,
        "bleeds": sim.entities[actor.id].meters["bleeds"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def setting_detail(setting: Setting, hazard: Hazard) -> str:
    if setting.indoor:
        return f"{setting.place.capitalize()} was quiet, and the floor was swept clean."
    return (f"{setting.place.capitalize()} was bright and dewy, and small tracks "
            f"crossed the soft ground.")


def hazard_detail(hazard: Hazard) -> str:
    return {
        "splinter": "it lay in the grass, pale and sliver-thin, with a faint red smear",
        "thorn": "it curled from a low bush, sharp and curved, with a drop of red at its tip",
        "bone": "it was a small cracked bone, white and sharp, with a thread of red still on it",
        "glass": "it was a sliver of broken glass, bright and cruel, with a streak of red along its edge",
    }.get(hazard.id, f"it lay in the grass, a sharp {hazard.label}")


def _do_find(world: World, actor: Entity, hazard: Hazard, narrate: bool = True) -> None:
    if hazard.id not in world.setting.affords:
        return
    world.zone = set(hazard.zone)
    actor.meters["bone"] += 1
    actor.memes["curious"] += 1
    world.facts.setdefault("hazards_taken", []).append(hazard.label)
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved to wander where the light came through the trees.")


def loves_wander(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.memes["love_play"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved wandering under the leaves and "
        f"peering at every curious thing on the path; today {hero.pronoun()} had "
        f"come looking for a {hazard.label}."
    )


def elder_warns(world: World, elder: Entity, hero: Entity, hazard: Hazard) -> bool:
    """The elder foresees the cut via the world model and warns about it."""
    pred = predict_wound(world, hero, hazard)
    if not pred["wounded"]:
        return False
    elder.meters["wisdom_used"] += 1
    world.facts["predicted_soil"] = hazard.soil
    world.facts["predicted_wound"] = True
    world.say(
        f'"{hazard.foreshadow}," the {elder.label_word} said gently, '
        f'stopping {hero.id} before the next step. '
        f'"A sharp thing waits in the grass, and a paw cut on it will carry '
        f'its {hazard.soil} for the rest of the day."'
    )
    return True


def defies(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} heard the warning, but the wish to see was still tugging."
    )
    world.say(f"{hero.pronoun().capitalize()} tried to {hazard.rush},")


def elder_blocks(world: World, elder: Entity, hero: Entity, hazard: Hazard) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"but the {elder.label_word} stepped lightly in front and held up a "
        f"soft paw. \"You can still want to see, and we can still choose the "
        f"safe way,\" the {elder.label_word} said."
    )


def finds(world: World, hero: Entity, hazard: Hazard) -> None:
    _do_find(world, hero, hazard, narrate=True)
    world.say(
        f"the {hazard.label} {hazard_detail(hazard)}. {hero.pronoun('possessive').capitalize()} "
        f"paw came away with {hazard.soil}."
    )


def elder_cleans(world: World, elder: Entity, hero: Entity, prize: Entity,
                 helper: Helper) -> None:
    elder.meters["care_given"] += 1
    world.say(
        f"The {elder.label_word} set {hero.id} down on a flat stone and "
        f"{helper.verb}."
    )
    propagate(world, narrate=True)


def elder_carves(world: World, elder: Entity, hero: Entity, hazard: Hazard) -> None:
    """The transformation beat: the splinter becomes a whistle."""
    shard = world.add(Entity(
        id="shard", type="shard", label=hazard.label, owner=hero.id,
        caretaker=elder.id, plural=False,
    ))
    shard.meters["shaped"] += 1
    world.say(
        f"The {elder.label_word} did not throw the {hazard.label} away. "
        f"Instead, {elder.pronoun('subject')} sat by the fire and, with patient "
        f"small strokes, carved it down into a tiny whistle."
    )
    propagate(world, narrate=True)
    world.facts["whistle"] = shard
    world.facts["after_sound"] = hazard.after_sound


def shares(world: World, hero: Entity, elder: Entity) -> None:
    """Hero shares the lesson; kindness + role -> elder-seed."""
    hero.memes["kindness"] += 1
    if hero.memes.get("role", 0.0) >= THRESHOLD:
        hero.memes["role"] = 2.0        # promote to "elder-seed" via the moral
    world.say(
        f"That night, {hero.id} told the smaller ones about the day the "
        f"sharp thing became a kind thing, and how the smallest sound had "
        f"saved them all."
    )


def hawk_strikes(world: World, adversary: Adversary, flock: list[Entity]) -> None:
    world.say(
        f"Suddenly there was {adversary.sound}. {adversary.label} "
        f"{adversary.rush}, eyes fixed on {adversary.prey}."
    )
    for f in flock:
        f.meters["fear"] += 1


def hero_whistles(world: World, hero: Entity, shard: Entity) -> None:
    hero.memes["hope"] += 1
    world.facts["whistle_blown"] = True
    world.say(
        f"{hero.id} lifted the carved whistle to {hero.pronoun('possessive')} "
        f"lips and blew."
    )
    world.say(
        f"The whistle made {shard_after_sound(shard)}."
    )
    propagate(world, narrate=True)


def shard_after_sound(shard: Entity) -> str:
    # The after_sound is recorded on the facts dict by elder_carves().
    return WORLD_FACTS_REF["after_sound"]


def moral(world: World, hero: Entity, elder: Entity) -> None:
    world.say(
        f"And so the small rabbit learned the lesson the {elder.label_word} "
        f"had planted long before: what cuts us can be cleaned, what hurts "
        f"us can be shaped, and the small sound we make can keep the flock "
        f"safe."
    )
    world.say(
        "So it is, and so the forest remembers."
    )


# ---------------------------------------------------------------------------
# Reference used so the narration function (shard_after_sound) can read
# facts that elder_carves() just stored, without a free global.
# ---------------------------------------------------------------------------
WORLD_FACTS_REF: dict = {"after_sound": "a single clear note"}


# ---------------------------------------------------------------------------
# The screenplay: coarse three-act shape, driven by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, hazard: Hazard, prize_cfg: Prize, helper: Helper,
         adversary: Adversary, hero_name: str = "Pip", hero_type: str = "rabbit",
         hero_traits: Optional[list[str]] = None,
         elder_type: str = "owl-mother",
         flock_names: Optional[list[str]] = None) -> World:
    world = World(setting)
    world.weather = "early morning"

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "quick"]),
    ))
    elder = world.add(Entity(
        id="Elder", kind="character", type=elder_type,
        label="elder", traits=["patient", "old", "soft-eyed"],
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=elder.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))
    shard = world.add(Entity(
        id="hazard", type="hazard-label", label=hazard.label,
        phrase=hazard.phrase, owner=None, caretaker=elder.id,
    ))

    flock_names = flock_names or ["Nibs", "Mop", "Tup"]
    flock = [
        world.add(Entity(id=n, kind="character", type="rabbit",
                          traits=["little", "soft"], label=n))
        for n in flock_names
    ]

    # ---- Act 1: setup, foreshadowing, and the warning ignored ----
    introduce(world, hero)
    loves_wander(world, hero, hazard)
    world.say(
        f"That morning, the {elder.label_word} had spoken quietly of a sharp "
        f"thing in the grass. \"Be gentle with small paws,\" {elder.pronoun('subject')} said."
    )
    world.para()
    world.say(setting_detail(world.setting, hazard))
    elder_warns(world, elder, hero, hazard)
    defies(world, hero, hazard)
    elder_blocks(world, elder, hero, hazard)

    # ---- Act 2: the cut, the cleansing, the transformation ----
    world.para()
    finds(world, hero, hazard)
    elder_cleans(world, elder, hero, prize, helper)
    elder_carves(world, elder, hero, hazard)

    # ---- Act 3: the hawk, the whistle, and the moral ----
    world.para()
    hawk_strikes(world, adversary, flock)
    hero_whistles(world, hero, shard)
    shares(world, hero, elder)
    moral(world, hero, elder)

    world.facts.update(hero=hero, elder=elder, prize=prize, prize_cfg=prize_cfg,
                       hazard=hazard, helper=helper, adversary=adversary,
                       flock=flock, conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=True)
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "path": Setting(place="the forest path", indoor=False,
                    affords={"splinter", "thorn", "bone", "glass"}),
    "glade": Setting(place="the mossy glade", indoor=False,
                     affords={"splinter", "thorn", "bone"}),
    "riverbank": Setting(place="the riverbank", indoor=False,
                         affords={"splinter", "thorn", "bone", "glass"}),
    "old_nest": Setting(place="the old nest", indoor=True,
                        affords={"bone"}),
}

HAZARDS = {
    "splinter": Hazard(
        id="splinter", label="splinter", phrase="a sharp splinter of bone",
        verb="found a sharp splinter", rush="reach for the sharp splinter",
        soil="drops of red", zone={"paw"},
        foreshadow="the wind has carried something sharp down from the oaks",
        after_sound="a single clear note, like a bell the size of a heart",
        tags={"splinter", "bone"},
    ),
    "thorn": Hazard(
        id="thorn", label="thorn", phrase="a hooked thorn",
        verb="found a hooked thorn", rush="sniff the hooked thorn",
        soil="a small red mark", zone={"paw", "leg"},
        foreshadow="the low bushes have grown their hooks overnight",
        after_sound="a high thin note, like a raindrop on a leaf",
        tags={"thorn"},
    ),
    "bone": Hazard(
        id="bone", label="bone", phrase="a small cracked bone",
        verb="found a small cracked bone", rush="lift the small cracked bone",
        soil="a thread of red", zone={"paw"},
        foreshadow="an older creature left something behind in the leaves",
        after_sound="a low warm note, like a hug made of sound",
        tags={"bone"},
    ),
    "glass": Hazard(
        id="glass", label="glass", phrase="a sliver of broken glass",
        verb="found a sliver of glass", rush="bat at the bright sliver",
        soil="a streak of red", zone={"paw"},
        foreshadow="something bright has fallen out of the human path",
        after_sound="a bright sharp note, like a star struck small",
        tags={"glass"},
    ),
}

HELPERS = [
    Helper(id="moss", label="soft moss", verb="pressed the soft moss against the paw",
           tail="the elder pressed the soft moss with a small flat stone"),
    Helper(id="leaf", label="broad leaf", verb="wrapped the broad leaf over the paw",
           tail="the elder wrapped the broad leaf and tied it with a thin grass"),
    Helper(id="cloth", label="small cloth", verb="laid the small cloth over the paw",
           tail="the elder laid the small cloth and held it with both paws"),
]

PRIZES = {
    "moss-poultice": Prize(
        label="moss-poultice", phrase="a small poultice of soft moss",
        type="poultice", region="paw", plural=False,
        genders={"rabbit", "mouse", "fox"},
    ),
    "leaf-wrap": Prize(
        label="leaf-wrap", phrase="a wrap of broad cool leaf",
        type="wrap", region="paw", plural=False,
        genders={"rabbit", "mouse"},
    ),
    "cloth-band": Prize(
        label="cloth-band", phrase="a small cloth band",
        type="band", region="paw", plural=False,
        genders={"rabbit", "mouse", "fox"},
    ),
}

ADVERSARIES = [
    Adversary(id="hawk", label="the silent hawk", noun="hawk",
              rush="drove down from the pine",
              sound="a sharp shadow over the path",
              prey="the smallest rabbit",
              foil="the whistle, blown sharp and clear"),
    Adversary(id="weasel", label="the long weasel", noun="weasel",
              rush="slipped from under the log",
              sound="a thin smell of something hungry",
              prey="the slowest mouse",
              foil="the whistle, blown quick and bright"),
    Adversary(id="fox", label="the soft-footed fox", noun="fox",
              rush="trotted from the bramble",
              sound="a low rustle of leaves in a place with no wind",
              prey="any one of the flock",
              foil="the whistle, blown steady and long"),
]

RABBIT_NAMES = ["Pip", "Nibs", "Mop", "Tup", "Clover", "Wisp", "Fennel", "Thistle"]
MOUSE_NAMES = ["Tin", "Pip", "Midge", "Quill", "Ash", "Bramble"]
FOX_NAMES = ["Rowan", "Ash", "Vixen", "Bramble"]
OWL_MOTHER_NAMES = ["Halla", "Sova", "Mira", "Luma"]
OWL_FATHER_NAMES = ["Bran", "Holm", "Elder"]
SHE_WOLF_NAMES = ["Lirien", "Asha"]
ELDER_TYPES = ["owl-mother", "owl-father", "she-wolf"]
HERO_KIND_BY_TYPE = {"rabbit": ("rabbit", RABBIT_NAMES),
                     "mouse": ("mouse", MOUSE_NAMES),
                     "fox": ("fox", FOX_NAMES)}
TRAITS = ["curious", "quick", "stubborn", "lively", "soft-eyed", "small-pawed"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(place, hazard, prize) triples that pass the reasonableness constraint."""
    combos = []
    for place, setting in SETTINGS.items():
        for h_id in setting.affords:
            hz = HAZARDS[h_id]
            for prize_id, prize in PRIZES.items():
                if hazard_at_paw(hz, prize) and select_helper(hz, prize):
                    combos.append((place, h_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    hazard: str
    prize: str
    name: str
    hero_type: str
    elder_type: str
    adversary: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "splinter": [
        ("What is a splinter?",
         "A splinter is a tiny sharp piece of wood or bone that can stick into "
         "a paw or a finger and make a small wound that needs to be cleaned."),
        ("Why does a splinter hurt?",
         "A splinter hurts because it has a sharp tip that presses into the "
         "skin and makes a tiny tear that the body has to heal."),
    ],
    "thorn": [
        ("What is a thorn?",
         "A thorn is a sharp curved point that grows on a bush or rose, made "
         "by the plant to keep small animals from eating it."),
        ("Why are thorns sharp?",
         "Thorns are sharp so that animals learn not to bite the plant, and "
         "the plant can keep its leaves safe."),
    ],
    "bone": [
        ("What is a bone?",
         "A bone is the hard white part inside an animal's body that holds it "
         "up and lets it move; old bones can crack into sharp pieces."),
        ("Why can a cracked bone be sharp?",
         "A cracked bone is sharp because the break leaves small pointed "
         "edges that can cut a paw that touches them."),
    ],
    "glass": [
        ("What is broken glass?",
         "Broken glass is what is left when a glass cup or bottle falls and "
         "shatters; its edges are very sharp and can cut."),
        ("Why is broken glass dangerous?",
         "Broken glass is dangerous because its thin sharp edges can cut skin "
         "easily, and the cuts can be hard to see."),
    ],
    "wound": [
        ("What is a wound?",
         "A wound is a place on the body where the skin has been cut or hurt; "
         "it usually needs cleaning so it can heal."),
        ("Why do wounds need cleaning?",
         "Wounds need cleaning so the dirt and small bits do not stay inside, "
         "and the body can heal the skin the right way."),
    ],
    "bleed": [
        ("Why does a small cut bleed?",
         "A small cut bleeds because there are tiny tubes of blood under the "
         "skin, and when the skin is broken the blood comes out."),
    ],
    "moss": [
        ("What is moss?",
         "Moss is a soft green plant that grows on stones and trees; it can "
         "be pressed onto a small cut to help it feel cool and clean."),
    ],
    "leaf": [
        ("Why can a leaf help a cut?",
         "A clean broad leaf can cover a small cut and keep the dirt out "
         "while the skin heals underneath."),
    ],
    "cloth": [
        ("Why can cloth help a wound?",
         "A small piece of clean cloth can hold against a wound to keep it "
         "pressed, to slow the bleeding and keep it clean while it heals."),
    ],
    "whistle": [
        ("What is a whistle?",
         "A whistle is a small object shaped so that blowing into it makes a "
         "clear loud sound; animals and people use whistles to call to each "
         "other from far away."),
        ("Why is a whistle useful for animals?",
         "A whistle is useful for animals because its sound travels farther "
         "than a call, and it can warn friends of danger they cannot yet see."),
    ],
    "hawk": [
        ("Why are hawks dangerous to small animals?",
         "Hawks are dangerous to small animals because they fly quickly and "
         "silently, and they hunt from above where the animals cannot see "
         "them coming."),
        ("How do small animals stay safe from a hawk?",
         "Small animals stay safe from a hawk by listening for warning sounds "
         "and running to a low bush or a burrow where the hawk cannot follow."),
    ],
    "weasel": [
        ("Why are weasels dangerous to small animals?",
         "Weasels are dangerous because they are quick and can slip into small "
         "holes; they hunt rabbits and mice for food."),
    ],
    "fox": [
        ("Why are foxes dangerous to small animals?",
         "Foxes are dangerous because they hunt quietly at dusk and dawn, "
         "and they are quick enough to catch a small rabbit if it is not "
         "warned."),
    ],
    "elder": [
        ("Who is an elder in a fable?",
         "An elder in a fable is the oldest, kindest animal in the forest, "
         "who has seen many seasons and knows what is safe and what is not."),
    ],
    "flock": [
        ("What is a flock?",
         "A flock is a small group of animals that stay together so they can "
         "warn each other and look after the smallest among them."),
    ],
}
KNOWLEDGE_ORDER = ["splinter", "thorn", "bone", "glass", "wound", "bleed",
                   "moss", "leaf", "cloth", "whistle",
                   "hawk", "weasel", "fox",
                   "elder", "flock"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, elder, hz = f["hero"], f["elder"], f["hazard"]
    kw = hz.label
    return [
        f'Write a short fable for a 4-to-6-year-old on the theme "a small '
        f'wound becomes a kind tool" that includes the word "{kw}".',
        f"Tell a gentle fable where a {hero.type} named {hero.id} finds a "
        f"{hz.label}, is warned by an {elder.label_word}, and the very "
        f"{hz.label} becomes a whistle that saves the flock.",
        f'Write a short fable that uses the noun "{kw}", ends with a clear '
        f"moral, and shows how a small painful thing can be cleaned and shaped.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, elder, prize, hz, adv = f["hero"], f["elder"], f["prize"], f["hazard"], f["adversary"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    pw = elder.label_word
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} walks {place} and "
                f"finds the {hz.label}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"the kind {pw} of the forest. {hero.id} had wandered to {place} "
                f"on a bright morning, and the {pw} had warned {obj} about "
                f"something sharp in the grass."
            ),
        ),
        QAItem(
            question=(
                f"What did the {pw} warn {trait} {hero.id} about before the "
                f"{hero.type} found the {hz.label} at {place}?"
            ),
            answer=(
                f'The {pw} had said, "{hz.foreshadow}," and told {hero.id} that '
                f"a paw cut on it would carry its {hz.soil} for the rest of "
                f"the day. It was a gentle warning, planted before the cut."
            ),
        ),
        QAItem(
            question=(
                f"What happened to {pos} paw after {trait} {hero.id} reached "
                f"for the {hz.label}?"
            ),
            answer=(
                f"{pos.capitalize()} paw came away with {hz.soil}. The small "
                f"cut kept stinging, and {hero.id} grew quiet and tired."
            ),
        ),
    ]
    if f.get("conflict"):
        why = (f"The {pw} was upset because if {hero.id} reached for the "
               f"{hz.label}, the paw would come away with {hz.soil}. When "
               f"{hero.id} tried to {hz.rush}, the {pw} stepped lightly in "
               f"front and held up a soft paw to remind {obj} that there was "
               f"a safer way.")
        qa.append(QAItem(
            question=(
                f"Why did the {pw} try to stop {trait} {hero.id} from reaching "
                f"for the {hz.label} at {place}?"
            ),
            answer=why,
        ))
    qa.append(QAItem(
        question=(
            f"How did the {pw} clean the small red mark on {trait} {hero.id}'s "
            f"paw at {place}?"
        ),
        answer=(
            f"The {pw} set {hero.id} down on a flat stone and pressed a soft "
            f"{prize.label} against the paw until the small red mark faded. "
            f"It was a gentle cleaning, and {hero.id} felt calm again."
        ),
    ))
    qa.append(QAItem(
        question=(
            f"How did the {hz.label} become a whistle for {trait} {hero.id} "
            f"at {place}?"
        ),
        answer=(
            f"The {pw} did not throw the {hz.label} away. {elder.pronoun('subject').capitalize()} "
            f"sat by the fire and carved it down, with patient small strokes, "
            f"until it was a tiny whistle that made {hz.after_sound}."
        ),
    ))
    qa.append(QAItem(
        question=(
            f"How did the whistle help {trait} {hero.id} when {adv.label} "
            f"drove down at {place}?"
        ),
        answer=(
            f"When {adv.label} {adv.rush}, eyes on {adv.prey}, {hero.id} "
            f"lifted the carved whistle and blew. The flock heard the small "
            f"clear note and ran for the low brush, and the hawk turned away "
            f"on empty wings. The whistle had saved them."
        ),
    ))
    qa.append(QAItem(
        question=(
            f"What is the moral of the fable about {trait} {hero.id} and the "
            f"{hz.label} at {place}?"
        ),
        answer=(
            "What cuts us can be cleaned, what hurts us can be shaped, and "
            "the small sound we make can keep the flock safe. That is the "
            "lesson the forest remembers."
        ),
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic child-level questions about the world's elements."""
    f = world.facts
    tags = set(f["hazard"].tags)
    tags.add("wound")
    tags.add("bleed")
    tags.add("whistle")
    tags.add(f["prize"].type.split("-")[0] if "-" in f["prize"].type else f["prize"].type)
    tags.add(f["adversary"].id)
    tags.add("elder")
    tags.add("flock")
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
# CLI / trace
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  hazards_taken: {world.facts.get('hazards_taken', [])}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="path", hazard="splinter", prize="moss-poultice",
        name="Pip", hero_type="rabbit", elder_type="owl-mother",
        adversary="hawk", trait="curious",
    ),
    StoryParams(
        place="glade", hazard="bone", prize="leaf-wrap",
        name="Tin", hero_type="mouse", elder_type="owl-father",
        adversary="weasel", trait="quick",
    ),
    StoryParams(
        place="riverbank", hazard="thorn", prize="cloth-band",
        name="Rowan", hero_type="fox", elder_type="she-wolf",
        adversary="fox", trait="lively",
    ),
    StoryParams(
        place="path", hazard="glass", prize="moss-poultice",
        name="Mop", hero_type="rabbit", elder_type="owl-mother",
        adversary="hawk", trait="stubborn",
    ),
    StoryParams(
        place="old_nest", hazard="bone", prize="cloth-band",
        name="Nibs", hero_type="rabbit", elder_type="owl-mother",
        adversary="hawk", trait="soft-eyed",
    ),
]


def explain_rejection(hazard: Hazard, prize: Prize) -> str:
    if not hazard_at_paw(hazard, prize):
        return (f"(No story: {hazard.label} reaches {sorted(hazard.zone)}, but a "
                f"{prize.label} sits on the {prize.region} -- it wouldn't help "
                f"with this cut. Try a prize worn on {sorted(hazard.zone)}.)")
    return (f"(No story: nothing in the helper catalog can clean a "
            f"{prize.label} cut from a {hazard.label}. The fix must actually "
            f"cover the at-risk region, so this argument is rejected.)")


def explain_kind(hero_type: str) -> str:
    if hero_type not in {"rabbit", "mouse", "fox"}:
        return (f"(No story: hero_type must be one of rabbit / mouse / fox.)")
    return ""


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (hazard_at_paw / select_helper / valid_combos).  Inline rules below; facts
# emitted from the registries so the two cannot drift.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is useful when the hazard reaches the region it covers.
prize_helps(H, P) :- reaches(H, R), covers_region(P, R).

% A helper is compatible when the prize helps the hazard's region and the
% helper can press / wrap the prize onto the paw.
has_fix(H, P) :- prize_helps(H, P).

% A story is valid only when the place affords the hazard, and the prize fits.
valid(Place, H, P) :- affords(Place, H), prize_helps(H, P), has_fix(H, P).
valid_story(Place, H, P, Kind) :- valid(Place, H, P), hero_kind(Place, Kind).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for h in sorted(s.affords):
            lines.append(asp.fact("affords", pid, h))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        for r in sorted(h.zone):
            lines.append(asp.fact("reaches", hid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("covers_region", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for k in sorted(pr.genders):
            lines.append(asp.fact("wears", k, pid))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
    for a in ADVERSARIES:
        lines.append(asp.fact("adversary", a.id))
    for kind in ("rabbit", "mouse", "fox"):
        lines.append(asp.fact("hero_kind", kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
        description="Fable story world: a small animal finds a sharp thing, "
                    "is warned by an elder, and the very splinter becomes a "
                    "whistle that saves the flock. Unspecified choices are "
                    "picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-type", choices=["rabbit", "mouse", "fox"])
    ap.add_argument("--elder-type", choices=ELDER_TYPES)
    ap.add_argument("--adversary", choices=[a.id for a in ADVERSARIES])
    ap.add_argument("--name")
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
    """Fill in any unspecified choices at random, keeping the combo reasonable.

    Raises StoryError if explicit options describe an invalid story."""
    if args.hazard and args.prize:
        hz, pr = HAZARDS[args.hazard], PRIZES[args.prize]
        if not (hazard_at_paw(hz, pr) and select_helper(hz, pr)):
            raise StoryError(explain_rejection(hz, pr))
    if args.hero_type and args.prize and args.hero_type not in PRIZES[args.prize].genders:
        raise StoryError(
            f"(No story: a {PRIZES[args.prize].label} isn't a typical "
            f"{args.hero_type}'s item here; try --hero-type "
            f"{' / '.join(sorted(PRIZES[args.prize].genders))}.)"
        )
    if args.hero_type and args.hero_type not in {"rabbit", "mouse", "fox"}:
        raise StoryError(explain_kind(args.hero_type or ""))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.prize is None or c[2] == args.prize)
              and (args.hero_type is None
                   or args.hero_type in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, hazard_id, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    hero_type = args.hero_type or rng.choice(sorted(prize.genders))
    _, name_pool = HERO_KIND_BY_TYPE[hero_type]
    name = args.name or rng.choice(name_pool)
    elder_type = args.elder_type or rng.choice(ELDER_TYPES)
    adversary = args.adversary or rng.choice([a.id for a in ADVERSARIES])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, hazard=hazard_id, prize=prize_id,
        name=name, hero_type=hero_type, elder_type=elder_type,
        adversary=adversary, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    helper = HELPERS[0]               # the only helper in this minimal domain
    adversary = next(a for a in ADVERSARIES if a.id == params.adversary)
    WORLD_FACTS_REF["after_sound"] = HAZARDS[params.hazard].after_sound
    world = tell(SETTINGS[params.place], HAZARDS[params.hazard],
                 PRIZES[params.prize], helper, adversary,
                 params.name, params.hero_type,
                 [params.trait, "stubborn"], params.elder_type)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, hazard, prize) combos "
              f"({len(stories)} with hero_kind):\n")
        for place, hz, prize in triples:
            kinds = sorted(k for (pl, h, pr, k) in stories
                           if (pl, h, pr) == (place, hz, prize))
            print(f"  {place:11} {hz:9} {prize:14}  [{', '.join(kinds)}]")
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
            header = (f"### {p.name} the {p.hero_type}: "
                      f"{p.hazard} at {p.place} (vs. {p.adversary})")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
