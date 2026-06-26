#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/catastrophe_dig_gyp_misunderstanding_sound_effects_adventure.py
=============================================================================================================================

A standalone *story world* sketch for a tiny domain inspired by the seed
"catastrophe / dig / gyp" with the narrative instruments *Misunderstanding*
and *Sound Effects*, written in an Adventure style for a young reader.

Source tale (imagination of the seed)
------------------------------------
Mira, a curious girl, signed up for a summer *dinosaur dig* in the rocky hills
beyond the creek.  The dig site is run by a friendly ranger called Dale, who
warns the kids to never chip at the bones themselves -- "One bad whack and a
tiny tooth can crumble like old chalk."  Mira misunderstands "dinosaur dig"
as "a treasure dig," the kind grown-ups do in movies, so when a thunderstorm
rolls in and the tarp snaps loose, she imagines the worst: the storm is a
catastrophe that has buried the dinosaur, and the ranger has been
shortchanged by a "gyp" -- a sly dealer who swapped the bones overnight.

Dale pulls Mira into the field tent, where the *sound effects* of the storm --
the BOOM of thunder, the TICK of rain on canvas, the CRACK of a branch --
turn into a kind of map.  Mira finally understands: there is no catastrophe
and no gyp, only a real dinosaur skeleton that was already buried by mud
millions of years ago, and a ranger who is just as soaked and worried as she
is.  They laugh, mop the tarp, and Mira gets to brush dust off a single,
perfectly preserved tooth -- the smallest, oldest sound the dig has ever
made.

Causal state updates
--------------------
    do activity (dig)            -> actor.dig_meter += 1 ; actor.excitement += 1
    surprise weather             -> actor.worry += 1 ; tension += 1
    misunderstanding fired        -> actor.meme["misunderstanding"] += 1
    reveal truth                 -> actor.meme["misunderstanding"] -> 0 ;
                                    actor.meme["relief"] += 1 ;
                                    actor.meme["joy"] += 1

The "gyp" beat is intentionally a *misunderstanding* in the model -- it is
never actually present, but the hero believes it long enough to motivate the
adventure-style middle turn.
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
# directly: add the package dir (storyworlds/) to the path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities: characters, gear, and discovered artifacts share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    region: str = ""               # for gear: head | torso | hands | none
    gear: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    # the recovered specimen -- a fossil, in this domain
    specimen: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "ranger", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "ranger": "ranger"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the dig site"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    """The adventure action the hero signs up for."""
    id: str
    verb: str            # "dig for bones"
    gerund: str          # "digging for bones"
    rush: str            # "run toward the dig pit"
    mess: str            # "dusty"
    noise: str           # the sound effect that closes the loop: "tink"
    weather: str         # "stormy" | "sunny" | ""
    keyword: str = ""    # for generation prompts: "dig"
    tags: set[str] = field(default_factory=set)


@dataclass
class CrewMember:
    """The grown-up at the dig: their tone shapes how the misunderstanding lands."""
    id: str
    type: str            # "ranger" | "guide" | "professor"
    label: str
    phrase: str
    warn_about: str      # the danger they actually warn about


@dataclass
class Specimen:
    """The fragile thing the dig protects -- a fossil the kid finally sees."""
    label: str
    phrase: str
    tiny: bool = True
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
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules (forward chained to a fixpoint).
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_misunderstanding(world: World) -> list[str]:
    """When the surprise weather fires while the hero is mid-dig and the ranger
    has not yet spoken, the misunderstanding lights up -- but only once."""
    out: list[str] = []
    for actor in world.characters():
        if not actor.id.startswith(("Mira", "Finn", "Lily", "Tim", "Ben", "Zoe", "Sam", "Mia", "Max", "Noah")):
            continue
        if (actor.memes["misunderstanding"] >= THRESHOLD
                or actor.memes["relief"] >= THRESHOLD):
            continue
        if actor.meters["dig_meter"] < THRESHOLD:
            continue
        if actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("misunderstanding", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["misunderstanding"] += 1
        out.append("__misunderstanding__")
    return out


def _r_truth_clears(world: World) -> list[str]:
    """Once the truth is told, the misunderstanding resolves and relief fires."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["truth_told"] < THRESHOLD:
            continue
        if actor.memes["relief"] >= THRESHOLD:
            continue
        sig = ("relief", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["misunderstanding"] = 0.0
        actor.memes["relief"] += 1
        actor.memes["joy"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="misunderstanding", tag="social", apply=_r_misunderstanding),
    Rule(name="truth_clears", tag="social", apply=_r_truth_clears),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what makes a *reasonable* misunderstanding/fix.
# ---------------------------------------------------------------------------
def specimen_exists(activity: Activity, specimen: Specimen) -> bool:
    """Every supported activity here yields some small fossil the ranger
    would actually protect -- this is the 'real' constraint."""
    return True


def supports_misunderstanding(activity: Activity, crew: CrewMember) -> bool:
    """A dig with a ranger/guide/professor and stormy weather supports the
    'catastrophe / gyp' misunderstanding; sunny beach 'digs' do not."""
    return activity.id in {"bones", "fossil", "finds"} and crew.id in {
        "ranger", "guide", "professor"
    } and activity.weather == "stormy"


def select_gear(activity: Activity) -> Optional[str]:
    """One simple piece of gear is needed for the dig: a brush.  The gear
    catalog is tiny on purpose -- it is the brush that does the resolution."""
    return "brush"


# ---------------------------------------------------------------------------
# Prediction helper -- the ranger runs the world model forward to *prove* the
# misunderstanding is wrong before saying so.  (Cheap but useful for --trace.)
# ---------------------------------------------------------------------------
def predict_truth(world: World, actor: Entity) -> dict:
    sim = world.copy()
    sim.get("crew").memes["truth_told"] += 1
    propagate(sim, narrate=False)
    return {
        "relief": sim.entities[actor.id].memes["relief"] >= THRESHOLD,
        "misunderstanding": sim.entities[actor.id].memes["misunderstanding"],
    }


# ---------------------------------------------------------------------------
# Verbs -- each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def delight_clause(activity: Activity) -> str:
    return {
        "bones": "every chip of rock felt like opening a tiny locked door",
        "fossil": "the dust smelled old and kind, like a library made of stone",
        "finds": "each sweep of the brush felt like writing a quiet letter",
    }.get(activity.id, "the work felt big and small at the same time")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if activity.weather == "stormy":
        return (f"{setting.place.capitalize()} sat under a low, gray sky, "
                f"and the dig pit was covered with a flapping tarp.")
    return f"{setting.place.capitalize()} was bright, and the dig pit waited like a small stage."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who had been waiting for "
        f"summer to begin for what felt like a hundred mornings."
    )


def signs_up(world: World, hero: Entity, crew: Entity, activity: Activity) -> None:
    world.say(
        f"This year, {hero.id} was going on a real dinosaur dig with "
        f"{crew.label}, and {hero.pronoun()} could barely eat breakfast that morning."
    )


def arrival(world: World, hero: Entity, crew: Entity, activity: Activity,
            setting: Setting) -> None:
    world.say(
        f"When {hero.id} arrived at {setting.place}, the wind smelled like rain, "
        f"and {crew.label} was already unloading buckets and brushes."
    )
    world.say(setting_detail(setting, activity))


def loves_dig(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["excitement"] += 1
    hero.meters["dig_meter"] += 1
    world.say(
        f"{hero.id} loved {activity.gerund}; {delight_clause(activity)}."
    )


def ranger_warns(world: World, hero: Entity, crew: Entity, specimen: Specimen) -> None:
    world.say(
        f'"{specimen.label.capitalize()} like these can crumble like old chalk," '
        f'{crew.label} said, holding up a tiny {specimen.label}. '
        f'"Always brush, never pry."'
    )


def storm_hits(world: World, hero: Entity, crew: Entity, activity: Activity) -> None:
    hero.memes["worry"] += 1
    hero.meters["dig_meter"] += 1
    world.say(
        f"Suddenly the wind snapped the tarp, and the sky went BOOM like a drum "
        f"the size of a hill."
    )
    world.say(
        f'Rain TICKED on the canvas, a branch CRACKED somewhere in the trees, '
        f"and {hero.id}'s heart went thump-thump-thump."
    )


def misunderstanding_blooms(world: World, hero: Entity, activity: Activity) -> None:
    """The 'gyp' beat: the kid imagines a sly dealer swapped the bones.
    This is purely a meme inside the hero's head -- it never escapes to the
    world; the ranger never hears it.  That is what makes it a misunderstanding."""
    propagate(world, narrate=False)
    world.say(
        f"Inside {hero.pronoun('possessive')} head, the sounds turned into a story: "
        f"a sly dealer had crept in during the night, swapped the bones for fakes, "
        f"and the storm was just his getaway."
    )
    world.say(
        f'{hero.id} thought, "It is a catastrophe! We have been gypped of the '
        f'real dig, and {hero.pronoun("object")} do not even know it."'
    )


def ranger_invites_in(world: World, hero: Entity, crew: Entity) -> None:
    world.say(
        f'{crew.label} waved {hero.id} into the field tent, where the canvas '
        f"thumped and the lantern swung."
    )


def sounds_as_map(world: World, hero: Entity, activity: Activity) -> None:
    """The 'sound effects' instrument: the kid turns the storm into a map."""
    world.say(
        f"They listened together: BOOM meant the storm was past the far ridge. "
        f"TICK meant the bones were safe under the tarp. CRACK meant a branch, "
        f"not a bone."
    )
    world.say(
        f"One by one, the scary sounds became a small map of the dig site, "
        f"and {hero.id} could almost point to where each one was happening."
    )


def truth_told(world: World, hero: Entity, crew: Entity, specimen: Specimen,
               activity: Activity) -> None:
    hero.memes["truth_told"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"{specimen.label.capitalize()} like these are already buried under a '
        f'million years of mud," {crew.label} said kindly. '
        f'"No storm can swap them, and no dealer can carry them off. They are '
        f'too heavy with time."'
    )
    world.say(
        f'{hero.id} looked at the {specimen.label}, then at the tarp, then at '
        f'{crew.label}, and the inside-the-head story quietly broke apart.'
    )


def mop_tarp(world: World, hero: Entity, crew: Entity) -> None:
    world.say(
        f"They pulled the tarp back over the dig pit together, and the rain "
        f"sounded softer now, just pat-pat-pat on the canvas."
    )


def reveal_specimen(world: World, hero: Entity, crew: Entity,
                    specimen: Specimen) -> None:
    """The ending image: one tiny fossil, brushed clean, with its own tiny sound."""
    world.say(
        f"When the cloud thinned, {crew.label} lifted a single {specimen.label} "
        f"from the pit and handed {hero.id} a soft brush."
    )
    world.say(
        f"{hero.id} brushed dust from the {specimen.label}, and there it was: "
        f"the smallest, oldest {activity.noise.upper()} a dig has ever made."
    )


# ---------------------------------------------------------------------------
# The screenplay: three-act adventure, driven by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, crew_cfg: CrewMember,
         specimen_cfg: Specimen, hero_name: str = "Mira",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None,
         crew_name: str = "Dale") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "stubborn"]),
    ))
    crew = world.add(Entity(
        id="crew", kind="character", type=crew_cfg.type,
        label=crew_name, phrase=crew_cfg.phrase,
    ))
    specimen = world.add(Entity(
        id="specimen", type="fossil", label=specimen_cfg.label,
        phrase=specimen_cfg.phrase, specimen=True,
        plural=specimen_cfg.plural,
    ))

    # Act 1 -- setup.
    introduce(world, hero)
    signs_up(world, hero, crew, activity)
    arrival(world, hero, crew, activity, setting)
    loves_dig(world, hero, activity)
    ranger_warns(world, hero, crew, specimen)

    # Act 2 -- conflict (the misunderstanding): storm + imagined catastrophe/gyp.
    world.para()
    storm_hits(world, hero, crew, activity)
    misunderstanding_blooms(world, hero, activity)
    ranger_invites_in(world, hero, crew)
    sounds_as_map(world, hero, activity)

    # Act 3 -- resolution: truth told, gear (the brush) reveals the fossil.
    world.para()
    truth_told(world, hero, crew, specimen, activity)
    mop_tarp(world, hero, crew)
    reveal_specimen(world, hero, crew, specimen)

    world.facts.update(
        hero=hero, crew=crew, activity=activity, setting=setting,
        specimen=specimen, crew_cfg=crew_cfg, specimen_cfg=specimen_cfg,
        misunderstanding=hero.memes["misunderstanding"] >= THRESHOLD,
        resolved=hero.memes["relief"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "creek": Setting(place="the dig site by the creek", indoor=False,
                     affords={"bones", "fossil", "finds"}),
    "ridge": Setting(place="the dig site on the ridge", indoor=False,
                     affords={"bones", "fossil", "finds"}),
    "badlands": Setting(place="the badlands dig site", indoor=False,
                        affords={"bones", "fossil", "finds"}),
}

ACTIVITIES = {
    "bones": Activity(
        id="bones",
        verb="dig for bones",
        gerund="digging for bones",
        rush="run toward the dig pit",
        mess="dusty",
        noise="tink",
        weather="stormy",
        keyword="dig",
        tags={"dig", "fossil", "storm"},
    ),
    "fossil": Activity(
        id="fossil",
        verb="dig for fossils",
        gerund="digging for fossils",
        rush="race to the fossil pit",
        mess="dusty",
        noise="click",
        weather="stormy",
        keyword="fossil",
        tags={"dig", "fossil", "storm"},
    ),
    "finds": Activity(
        id="finds",
        verb="search for small finds",
        gerund="searching for small finds",
        rush="scramble to the find spot",
        mess="dusty",
        noise="tock",
        weather="stormy",
        keyword="find",
        tags={"dig", "fossil", "storm"},
    ),
}

CREW = {
    "ranger": CrewMember(
        id="ranger", type="ranger", label="Ranger Dale",
        phrase="a friendly park ranger in a wide-brimmed hat",
        warn_about="chipping at the bones",
    ),
    "guide": CrewMember(
        id="guide", type="guide", label="Guide Rosa",
        phrase="a dig guide with a clipboard and kind eyes",
        warn_about="rushing the brush",
    ),
    "professor": CrewMember(
        id="professor", type="professor", label="Professor Hale",
        phrase="a university professor who brought her own field kit",
        warn_about="poking the fossil",
    ),
}

SPECIMENS = {
    "tooth": Specimen(label="tooth", phrase="a tiny dinosaur tooth"),
    "claw": Specimen(label="claw", phrase="a curved dinosaur claw"),
    "vertebra": Specimen(label="vertebra", phrase="a small, knobby vertebra"),
}

GIRL_NAMES = ["Mira", "Lily", "Zoe", "Mia", "Ava", "Ella", "Nora", "Rose"]
BOY_NAMES = ["Finn", "Tim", "Ben", "Max", "Sam", "Jack", "Noah", "Eli"]
TRAITS = ["curious", "brave", "stubborn", "cheerful", "spirited", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(place, activity, crew) triples that pass the reasonableness constraint."""
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for crew_id, crew in CREW.items():
                if supports_misunderstanding(act, crew):
                    out.append((place, act_id, crew_id))
    return out


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    crew: str
    specimen: str
    name: str
    gender: str
    crew_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three separate sets.
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, crew, act = f["hero"], f["crew"], f["activity"]
    kw = act.keyword or "dig"
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a sound '
        f'map that solves a fear" that uses the word "{kw}".',
        f"Tell a gentle adventure where a {hero.type} named {hero.id} goes on "
        f"a {act.keyword} with {crew.label}, hears a scary storm, and turns "
        f"the sounds into a small map.",
        f'Write a simple adventure story that uses the noun "{kw}" and ends '
        f"with a grown-up showing a real fossil to the child.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, crew, act, specimen = (
        f["hero"], f["crew"], f["activity"], f["specimen_cfg"]
    )
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    place = world.setting.place
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who took {trait} {hero.id} to the dinosaur {act.keyword} at "
                f"{place} before the storm came in?"
            ),
            answer=(
                f"{crew.label}, {crew.phrase}, ran the dig. {hero.id} signed "
                f"up for the summer and arrived early in the morning, ready to "
                f"{act.verb}."
            ),
        ),
        QAItem(
            question=(
                f"What was {trait} {hero.id} doing when the storm broke over "
                f"the dig pit at {place}?"
            ),
            answer=(
                f"{hero.id} was {act.gerund}, and the wind snapped the tarp. "
                f"The sky went BOOM, the rain went TICK, and a branch went "
                f"CRACK, which made {pos} heart go thump-thump-thump."
            ),
        ),
    ]
    if f.get("misunderstanding"):
        qa.append(QAItem(
            question=(
                f"What did {trait} {hero.id} think was happening at {place} "
                f"when the storm hit during the {act.keyword}?"
            ),
            answer=(
                f"{hero.id} imagined a sly dealer had swapped the bones for "
                f"fakes and was escaping in the storm. Inside {pos} head, it "
                f"felt like a real catastrophe and a real gyp, even though "
                f"nothing like that was happening."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did the BOOM, TICK, and CRACK sounds help {trait} {hero.id} "
                f"stop believing the catastrophe story at {place}?"
            ),
            answer=(
                f"{crew.label} invited {obj} into the field tent, and they "
                f"listened together. BOOM was past the far ridge, TICK was "
                f"the tarp holding, and CRACK was just a branch. The sounds "
                f"became a small map of the dig, and the imagined gyp quietly "
                f"broke apart."
            ),
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            question=(
                f"What did {crew.label} show {trait} {hero.id} at the end of "
                f"the {act.keyword} at {place}?"
            ),
            answer=(
                f"{crew.label} lifted a single {specimen.label} from the pit "
                f"and handed {obj} a soft brush. When {hero.id} brushed the "
                f"dust away, the {specimen.label} made the smallest, oldest "
                f"{act.noise.upper()} a dig has ever made."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} feel after the catastrophe story "
                f"broke apart at the {act.keyword}?"
            ),
            answer=(
                f"{hero.id} felt relief and joy. {sub.capitalize()} helped "
                f"{crew.label} pull the tarp back over the pit, and the rain "
                f"sounded soft again, just pat-pat-pat on the canvas."
            ),
        ))
    return qa


# (3) Child-level world knowledge, keyed by topic.
KNOWLEDGE = {
    "dig": [("What is a dig?",
             "A dig is a careful place where people brush away dirt and rock, "
             "little by little, to find old bones or other buried things.")],
    "fossil": [("What is a fossil?",
                "A fossil is the shape of a plant or animal that has been "
                "kept in rock for a very, very long time.")],
    "storm": [("Why does thunder boom?",
               "Thunder booms because lightning heats the air so fast that "
               "the air pops, and that pop is the big sound we call thunder.")],
    "sound": [("Why do loud sounds feel scary at first?",
               "Loud sounds feel scary because we do not yet know what made "
               "them, and our body gets ready to run or hide until we find out.")],
    "map": [("What is a sound map?",
             "A sound map is when you match each sound you hear to the place "
             "it came from, so the noise becomes a small picture in your head.")],
    "brush": [("Why do diggers use a soft brush?",
               "Diggers use a soft brush because old bones crumble like chalk, "
               "and a brush cleans them without breaking them.")],
    "gyp": [("What does \"gypped\" mean?",
             '"Gypped" means tricked or shortchanged -- when someone takes '
             "something from you that should be yours.")],
    "catastrophe": [("What is a catastrophe?",
                     "A catastrophe is a sudden, very bad event that changes "
                     "things fast, like a flood or a fire.")],
}
KNOWLEDGE_ORDER = ["dig", "fossil", "storm", "sound", "map", "brush",
                   "catastrophe", "gyp"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags) | {"sound", "map", "brush"}
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
        if e.specimen:
            bits.append("specimen")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="creek", activity="bones", crew="ranger", specimen="tooth",
        name="Mira", gender="girl", crew_name="Dale", trait="curious",
    ),
    StoryParams(
        place="ridge", activity="fossil", crew="guide", specimen="claw",
        name="Finn", gender="boy", crew_name="Rosa", trait="brave",
    ),
    StoryParams(
        place="badlands", activity="finds", crew="professor", specimen="vertebra",
        name="Lily", gender="girl", crew_name="Hale", trait="spirited",
    ),
]


def explain_rejection(activity: Activity, crew: CrewMember) -> str:
    return (
        f"(No story: a '{activity.id}' dig with a '{crew.id}' leader does "
        f"not support the catastrophe/gyp misunderstanding in this world. "
        f"Stormy weather plus ranger/guide/professor is required.)"
    )


def explain_specimen(crew_id: str, specimen_id: str) -> str:
    return f"(No story: '{specimen_id}' is not in the specimen catalog for '{crew_id}'.)"


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- declarative twin of supports_misunderstanding().
# Inline rules; facts generated from the registries above.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A dig at a setting with stormy weather plus a ranger/guide/professor
% supports the catastrophe/gyp misunderstanding.
dig_supports(S, A, C) :- setting(S), affords(S, A), stormy(A),
                        crew_kind(C, K), crew_supports(K).

% A story is valid when the chosen place, activity, and crew all line up
% with the support predicate.
valid_story(S, A, C) :- dig_supports(S, A, C).
"""


def asp_facts() -> str:
    """Import the asp helper lazily and emit the registries as base facts."""
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        if a.weather == "stormy":
            lines.append(asp.fact("stormy", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for cid, c in CREW.items():
        lines.append(asp.fact("crew", cid))
        lines.append(asp.fact("crew_kind", cid, c.type))
        if c.type in {"ranger", "guide", "professor"}:
            lines.append(asp.fact("crew_supports", c.type))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_stories()), set(valid_combos())
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
        description="Story world sketch: a dinosaur dig, a storm, a misunderstanding "
                    "solved by sound effects. Unspecified choices are picked at random.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--crew", choices=CREW)
    ap.add_argument("--specimen", choices=SPECIMENS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.activity and args.crew:
        act, crew = ACTIVITIES[args.activity], CREW[args.crew]
        if not supports_misunderstanding(act, crew):
            raise StoryError(explain_rejection(act, crew))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.crew is None or c[2] == args.crew)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, crew_id = rng.choice(sorted(combos))
    crew = CREW[crew_id]
    specimen_id = args.specimen or rng.choice(sorted(SPECIMENS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, activity=activity, crew=crew_id, specimen=specimen_id,
        name=name, gender=gender,
        crew_name={"ranger": "Dale", "guide": "Rosa",
                   "professor": "Hale"}[crew_id],
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 CREW[params.crew], SPECIMENS[params.specimen],
                 params.name, params.gender, [params.trait, "stubborn"],
                 params.crew_name)
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
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, crew) combos:\n")
        for place, act, crew in triples:
            print(f"  {place:10} {act:8} {crew:10}")
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
            header = f"### {p.name}: {p.activity} at {p.place} (crew: {p.crew})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
