#!/usr/bin/env python3
"""
storyworlds/worlds/prime_oyster_nooney.py
==========================================

A standalone *story world* sketch for "Prime, the Oyster, and the Nooney Cakes" 
and close, *constraint-checked* variations of it.  The domain is built from the 
seed words "prime", "oyster", and "nooney" with a lesson-learned, bad-ending arc 
told in a heartwarming style.

Initial story (used to build a world model):
---
Once upon a time, there was a cheerful little girl named Prime. She loved
collecting shiny oyster shells at the seaside and sniffing the warm nooney
cakes that Gran baked every afternoon.  Gran always saved two nooney cakes
for Prime after her beach walks.

One sunny morning, Gran bought Prime a beautiful new apron with a deep pocket
for shells.  Prime adored the apron and wore it everywhere.  "Come back in 
time for nooney cakes," Gran said as Prime ran to the cove.

Prime searched and searched.  At last she found the most perfect oyster – the
prime oyster – all smooth and pearly.  She was so excited that she ignored 
Gran's call.  She stayed to dig for more, and the apron got soaked and torn 
on a sharp rock.  The prime oyster fell out of the torn pocket and rolled 
into the waves.  Prime cried.

Gran came down, hugged her, and said, "The prime oyster is lost, but you
learned to listen.  Nooney cakes will still be there."  Prime learned that
day that rules keep you – and the things you love – safe.

Causal state updates:
---
    do activity                 -> actor.<mess> += 1  (sandy / wet)
    actor messy + worn item     -> item.<mess>++, item.dirty++   if same region
    worn item dirty             -> item.caretaker.workload += 1
    defiance (ignore call)      -> actor.defiance++ ; then reward lost
    parent comforts             -> actor.joy = 0.5, actor.lesson++ ; conflict cleared
    gear worn                   -> item protected ; no mess transferred

Scripted social/emotional beats:
---
    warning given but ignored   -> actor.defiance++
    prize ruined                -> actor.sadness++, parent.workload++
    parent comforts             -> actor.sadness -> 0 ; actor.lesson++ ; heartwarming close
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
# (``python storyworlds/worlds/prime_oyster_nooney.py``): add the package dir (storyworlds/)
# to the path so ``results`` resolves regardless of the current directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Physical meter keys that count as a "mess" the activity spreads onto worn items.
MESS_KINDS = {"wet", "sandy", "torn"}

# Body regions, used for the gear-coverage constraint.
REGIONS = {"torso", "legs", "feet"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, gran, apron, bucket, gear ...
    label: str = ""                # short reference, e.g. "apron", "bucket"
    phrase: str = ""               # full noun phrase, e.g. "a beautiful new apron"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None   # who has to clean up after this object
    worn_by: Optional[str] = None
    region: str = ""                  # where a worn item sits: torso | legs | feet
    protective: bool = False          # gear that doesn't get ruined
    covers: set[str] = field(default_factory=set)   # regions the gear shields
    plural: bool = False              # "shoes" -> them, "apron" -> it
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model):
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "gran", "woman"}
        male = {"boy", "grandpa", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"gran": "Gran"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the cove"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)   # which activities this place supports


@dataclass
class Activity:
    """A messy thing the hero loves to do."""
    id: str
    verb: str            # after "wanted to ..."             : "search for the prime oyster"
    gerund: str          # after "loved ... and ..."         : "searching for oyster shells"
    rush: str            # after "tried to ..."              : "keep digging in the sand"
    mess: str            # mess kind key, one of MESS_KINDS  : "wet" or "sandy"
    soil: str            # how the prize gets ruined         : "soaked and torn"
    zone: set[str]       # body regions the activity splashes: {"torso"}
    weather: str         # "sunny" | "breezy" | ""
    keyword: str = ""    # topic word for generation prompts : "oyster"
    tags: set[str] = field(default_factory=set)   # world-knowledge topics it touches


@dataclass
class Prize:
    """The thing the hero loves and wears, that the messy activity would ruin."""
    label: str
    phrase: str
    type: str
    region: str          # torso | legs | feet  -- where it sits on the body
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})  # who plausibly wears it


@dataclass
class Gear:
    """Protective clothing offered as the compromise (but here often refused)."""
    id: str
    label: str
    covers: set[str]     # regions it shields
    guards: set[str]     # mess kinds it neutralizes
    prep: str            # body of the offer: "put on your waterproof apron cover"
    tail: str            # closing clause: "went to get the apron cover"
    plural: bool = False


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()          # splash zone of the activity in play
        self.weather: str = ""
        # Facts recorded during the screenplay, read back by the Q&A generators.
        self.facts: dict = {}

    # -- entity helpers -----------------------------------------------------
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
        """Is `region` shielded by some protective gear the actor is wearing?"""
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    # -- narration helpers --------------------------------------------------
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
        """Throwaway clone used for forward-simulation (prediction)."""
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]            # predictions are silent
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soak(world: World) -> list[str]:
    """actor messy + worn item in the splash zone & uncovered -> mess + dirty."""
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soak", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"got {mess} and dirty."
                )
    return out


def _r_workload(world: World) -> list[str]:
    """worn item dirty -> its caretaker has more work."""
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
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_grab_conflict(world: World) -> list[str]:
    """Gran called while child is defiant -> child conflict (ignored call)."""
    for actor in world.characters():
        if actor.memes["called_by"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]          # marker; narrated by the screenplay beat
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="grab_conflict", tag="social", apply=_r_grab_conflict),
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
# Constraint helpers -- what is a *reasonable* concern and a *reasonable* fix.
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    """Would this activity actually mess up this prize (right body region)?"""
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    """The compatible compromise: gear that guards the mess AND covers the
    at-risk region.  Returns None when no reasonable gear exists."""
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


# ---------------------------------------------------------------------------
# Prediction: the parent runs the world model forward on a copy to foresee the
# mess before deciding what to say.
# ---------------------------------------------------------------------------
def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    """Simulate the activity silently and report whether the prize is ruined."""
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "oyster": "the shiny shells felt like little treasures in the sand",
        "shell": "the smooth edges made a soft clinking sound in her pocket",
    }.get(activity.id, "the cove felt full of hidden wonders")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was quiet, and the play table waited nearby."
    if activity.weather == "sunny":
        return f"The sun sparkled on the water, and the sand was warm underfoot."
    return f"{setting.place.capitalize()} looked inviting in the morning light."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed clean"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return                                  # this place can't host the activity
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved exploring the seaside.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    where = "inside" if world.setting.indoor else "outside"
    world.say(
        f"{hero.pronoun().capitalize()} loved playing {where} and {activity.gerund}; "
        f"{activity_delight(activity)}."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"That morning, {hero.id}'s {parent.label_word} bought "
        f"{hero.pronoun('object')} {prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and "
        f"wore {prize.it()} with a proud smile."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"sunny": "One sunny morning, ", "breezy": "One breezy afternoon, "}.get(world.weather, "One day, ")
    go = "were in" if world.setting.indoor else "went to"
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} {go} {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but "
        f"{hero.pronoun('possessive')} {parent.label_word} called gently."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    """The parent foresees the mess via the world model and warns about it."""
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"Be careful with your {prize.label} or it will get {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += ", and I will have to wash it"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. "Come back soon!"')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the shiny shells were too tempting.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["called_by"] += 1
    propagate(world, narrate=False)             # fires the grab->conflict rule
    # Instead of grabbing, the parent calls again – the child ignores.
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} called again, "
        f'"I have nooney cakes waiting! Please come soon!"'
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:     # only narrate embedded conflict
        world.say(
            f'{hero.id} pouted and shook {hero.pronoun("possessive")} head. '
            f'"Just one more shell!" {hero.pronoun()} called back.'
        )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    """Offer gear -- but here the child refuses and the prize gets ruined."""
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:   # gear didn't actually help
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} held up a '
        f'{gear_def.label}. "Wear this to keep your {prize.label} safe, then you can play longer."'
    )
    return gear_def


def acceptance_fails(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity,
                     gear_def: Gear) -> None:
    """The child refuses the gear and the prize gets ruined (bad ending)."""
    hero.memes["defiance"] += 1
    hero.memes["sadness"] += 1
    prize.meters["dirty"] = 2.0  # fully ruined
    prize.meters["torn"] = 1.0
    world.say(
        f'{hero.id} shook {hero.pronoun("possessive")} head. "No, I can be careful!" '
        f'{hero.pronoun().capitalize()} kept digging, and soon the {prize.label} '
        f'got {activity.soil}. The prime oyster slipped out of the torn pocket and was lost.'
    )


def comfort_after_loss(world: World, parent: Entity, hero: Entity, prize: Entity,
                       gear_def: Optional[Gear]) -> None:
    """Parent comforts and the lesson is learned (heartwarming resolution)."""
    hero.memes["sadness"] = 0.0
    hero.memes["lesson"] += 1
    world.say(
        f'{hero.id} cried. {hero.pronoun("possessive").capitalize()} {parent.label_word} '
        f'came down, knelt, and hugged {hero.pronoun("object")} tightly. '
        f'"The prime oyster is gone," she said softly, "but the nooney cakes are still warm. '
        f'Next time you will listen to my warning, won\'t you?"'
    )
    world.say(f"{hero.id} nodded, still sniffling. The lesson was learned, and the nooney cakes "
              f"tasted sweeter than ever.")


# ---------------------------------------------------------------------------
# The screenplay: coarse three-act shape, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Prime", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "gran") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "determined"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="Gran"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1 -- setup: who, what they love, the prize they wear.
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2 -- conflict: desire vs. the predicted mess, defiance.
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    # Act 3 -- resolution: the child refuses gear, prize is ruined, comfort and lesson.
    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        acceptance_fails(world, parent, hero, activity, prize, gear_def)
    else:
        # No gear exists; the prize simply gets ruined.
        world.say(
            f"{hero.id} dug deeper. The {prize.label} got {activity.soil} and "
            f"the prime oyster was lost forever."
        )
    comfort_after_loss(world, parent, hero, prize, gear_def)

    # Record facts for the Q&A generators (grounded in the simulated world).
    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["called_by"] >= THRESHOLD,
                       resolved=False, lesson=True)
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "cove": Setting(place="the cove", indoor=False, affords={"oyster", "shell"}),
    "beach": Setting(place="the beach", indoor=False, affords={"oyster", "shell"}),
    "seaside": Setting(place="the seaside", indoor=False, affords={"oyster"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"shell"}),   # for variety
}

ACTIVITIES = {
    "oyster": Activity(
        id="oyster",
        verb="search for the prime oyster",
        gerund="searching for oyster shells",
        rush="keep digging in the sand",
        mess="sandy",
        soil="soaked and torn",
        zone={"torso", "legs"},
        weather="sunny",
        keyword="oyster",
        tags={"oyster", "shell", "beach"},
    ),
    "shell": Activity(
        id="shell",
        verb="collect shiny shells",
        gerund="collecting shiny shells",
        rush="reach for more shells",
        mess="sandy",
        soil="scratched and dirty",
        zone={"torso"},
        weather="sunny",
        keyword="shell",
        tags={"shell", "beach"},
    ),
}

GEAR = [
    Gear(
        id="aproncover",
        label="a waterproof apron cover",
        covers={"torso", "legs"},
        guards={"sandy", "wet"},
        prep="put on the waterproof apron cover",
        tail="grabbed the waterproof apron cover",
    ),
    Gear(
        id="bucket",
        label="a big bucket",
        covers={"torso"},
        guards={"sandy"},
        prep="carry your shells in the bucket",
        tail="picked up the big bucket",
        plural=True,
    ),
]

PRIZES = {
    "apron": Prize(
        label="apron",
        phrase="a beautiful new apron with a deep pocket",
        type="apron",
        region="torso",
    ),
    "shirt": Prize(
        label="shirt",
        phrase="a crisp new shirt with a shell print",
        type="shirt",
        region="torso",
    ),
    "shorts": Prize(
        label="shorts",
        phrase="light blue shorts with stretchy pockets",
        type="shorts",
        region="legs",
        plural=True,
    ),
}

GIRL_NAMES = ["Prime", "Maya", "Luna", "Nina", "Rosa"]
BOY_NAMES = ["Finn", "Arlo", "Kai", "Jude", "Otis"]
TRAITS = ["curious", "determined", "stubborn", "cheerful", "spirited"]


def valid_combos() -> list[tuple]:
    """(place, activity, prize) triples that pass the reasonableness constraint."""
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
# (3) Child-level world knowledge, keyed by topic.
KNOWLEDGE = {
    "oyster": [("What is an oyster?",
                "An oyster is a sea animal that lives inside a hard, bumpy shell. "
                "Sometimes you can find a shiny pearl inside an oyster.")],
    "shell": [("Why are seashells shiny?",
               "Seashells are shiny because the animal that lived inside made a "
               "smooth layer to protect itself. The sun makes them sparkle.")],
    "beach": [("What is the beach like?",
               "The beach is a sandy place next to the ocean. You can build "
               "sandcastles, find shells, and feel the salty breeze.")],
    "apron": [("What is an apron for?",
               "An apron is a cloth you wear over your clothes to keep them clean "
               "when you are cooking or doing something messy.")],
    "nooney": [("What are nooney cakes?",
                "Nooney cakes are sweet, warm cakes baked by Gran. They smell like "
                "honey and cinnamon, and they are a special treat after playing.")],
}
KNOWLEDGE_ORDER = ["oyster", "shell", "beach", "apron", "nooney"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a child, '
        f'an oyster, and a lesson learned" that includes the words "{kw}" and "nooney".',
        f"Tell a gentle story where a {hero.type} named {hero.id} ignores "
        f"{hero.pronoun('possessive')} {parent.label_word}'s warning about "
        f"{prize.phrase}, loses the prime oyster, and learns a lesson.",
        f'Write a simple story that uses the word "{kw}" and ends with a parent '
        f"comforting a child who has lost something precious.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    where = "inside" if world.setting.indoor else "outside"
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    day = {"sunny": "sunny morning", "breezy": "breezy afternoon"}.get(world.weather, "day")
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} visits {place} to "
                f"{act.verb} in {pos} {prize.label}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"{pos} {pw}. On a {day} they go to {place}, and {hero.id} is "
                f"wearing {pos} {prize.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love to do {where} before "
                f"{pw} called {obj} back for nooney cakes?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} loved {act.gerund} at {place}. "
                f"That love made {obj} stay too long, even when {pw} warned about "
                f"the {prize.label}."
            ),
        ),
        QAItem(
            question=(
                f"What new item did {hero.id}'s {pw} give {obj} "
                f"before the trip to {place}?"
            ),
            answer=(
                f"{pos.capitalize()} {pw} gave {obj} {prize.phrase}. "
                f"{hero.id} wore {prize.it()} proudly."
            ),
        ),
    ]
    # Lesson and loss
    qa.append(QAItem(
        question=(
            f"Why did {trait} {hero.id} lose the prime oyster at {place}?"
        ),
        answer=(
            f"{hero.id} did not listen when {pw} warned about keeping the "
            f"{prize.label} safe. {hero.pronoun('possessive').capitalize()} "
            f"{prize.label} got {act.soil}, the pocket tore, and the prime "
            f"oyster fell into the water."
        ),
    ))
    qa.append(QAItem(
        question=(
            f"How did {pw} comfort {trait} {hero.id} after the loss?"
        ),
        answer=(
            f"{pw.capitalize()} hugged {obj} and said the prime oyster was "
            f"gone, but the nooney cakes were still warm. {pw} told {obj} "
            f"that next time {sub} would listen. {hero.id} learned the lesson."
        ),
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
    # Always include "nooney" because it's central
    tags.add("nooney")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="cove",
        activity="oyster",
        prize="apron",
        name="Prime",
        gender="girl",
        parent="gran",
        trait="curious",
    ),
    StoryParams(
        place="beach",
        activity="shell",
        prize="shirt",
        name="Kai",
        gender="boy",
        parent="gran",
        trait="determined",
    ),
    StoryParams(
        place="playroom",
        activity="shell",
        prize="shorts",
        name="Maya",
        gender="girl",
        parent="gran",
        trait="stubborn",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, "
                f"but {noun} {verb} on the {prize.region} -- it wouldn't get "
                f"{activity.mess}, so the parent has no honest warning. "
                f"Try a prize worn on {sorted(activity.zone)}.)")
    return (f"(No story: nothing in the gear catalog protects {noun} "
            f"({prize.region}) from {activity.gerund}. The compromise must actually "
            f"cover the at-risk item, so this argument is rejected.)")


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return (f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s "
            f"item here; try --gender {ok}.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate.
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

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
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
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (place, activity, prize) triples."""
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    """(place, activity, prize, gender) -- gender-aware compatible stories."""
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
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
# Standard storyworld interface (see storyworlds/AGENTS.md):
#   build_parser() -> ArgumentParser
#   resolve_params(args, rng) -> StoryParams        (random where unspecified)
#   generate(params) -> StorySample                  (the core; world -> story+QA)
#   emit(sample, ...) -> None                        (human-readable output)
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, an oyster, a nooney cake, and "
                    "a lesson learned the hard way. "
                    "Unspecified choices are picked at random (seeded).")
    # A small, debuggable set of pins; any omitted choice is randomized.
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["gran", "grandpa"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    # Clingo (ASP) modes -- the inline declarative reasoner (needs clingo).
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random, keeping the combo reasonable.

    Raises StoryError if the *explicit* options describe an invalid story."""
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["gran", "grandpa"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "stubborn"], params.parent)
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
        print(f"{len(triples)} compatible (place, activity, prize) combos "
              f"({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories
                             if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
