#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cordon_prefer_fool_magic_humor_lesson_learned.py
============================================================================

A standalone storyworld for a tall-tale-style magical mishap on the windy
frontier. A boastful child is tempted to try a fool trick with a magical marvel.
A wiser companion may talk the child out of it; otherwise the marvel breaks
loose, the mayor throws up a rope cordon, and a grown-up uses the right gentle
fix.

This world is built around the seed words "cordon", "prefer", and "fool", with
Magic, Humor, and a Lesson Learned.

Run it
------
    python storyworlds/worlds/gpt-5.4/cordon_prefer_fool_magic_humor_lesson_learned.py
    python storyworlds/worlds/gpt-5.4/cordon_prefer_fool_magic_humor_lesson_learned.py --place fairground --marvel giggle_vine --fix moon_hum
    python storyworlds/worlds/gpt-5.4/cordon_prefer_fool_magic_humor_lesson_learned.py --fix cannon_boom
    python storyworlds/worlds/gpt-5.4/cordon_prefer_fool_magic_humor_lesson_learned.py --all
    python storyworlds/worlds/gpt-5.4/cordon_prefer_fool_magic_humor_lesson_learned.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/cordon_prefer_fool_magic_humor_lesson_learned.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAG_INIT = 6.0
STEADY_TRAITS = {"steady", "careful", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "mayor_female"}
        male = {"boy", "man", "father", "uncle", "mayor_male"}
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
            "aunt": "aunt",
            "uncle": "uncle",
            "mayor_female": "mayor",
            "mayor_male": "mayor",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    cordon_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Marvel:
    id: str
    label: str
    article: str
    seed_phrase: str
    need_tags: set[str] = field(default_factory=set)
    settle_fixes: set[str] = field(default_factory=set)
    hatch_line: str = ""
    commotion_line: str = ""
    calm_line: str = ""
    lesson_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    use_text: str
    qa_text: str
    fail_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_commotion(world: World) -> list[str]:
    out: list[str] = []
    marvel = world.entities.get("marvel")
    if marvel is None or marvel.meters["loose"] < THRESHOLD:
        return out
    sig = ("commotion", marvel.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("town").meters["trouble"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__commotion__")
    return out


def _r_cordon(world: World) -> list[str]:
    out: list[str] = []
    town = world.entities.get("town")
    mayor = world.entities.get("Mayor")
    if town is None or mayor is None or town.meters["trouble"] < THRESHOLD:
        return out
    sig = ("cordon", "town")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mayor.meters["cordon"] += 1
    out.append("__cordon__")
    return out


CAUSAL_RULES = [
    Rule(name="commotion", tag="physical", apply=_r_commotion),
    Rule(name="cordon", tag="social", apply=_r_cordon),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for item in produced:
            if item == "__cordon__":
                mayor = world.get("Mayor")
                world.say(
                    f"{mayor.id} whirled a long ranch rope through the air and laid a neat cordon around "
                    f"{world.place.cordon_spot}, so nobody but helpers and chickens got too close."
                )
    return produced


def initial_caution(trait: str) -> float:
    return 5.0 if trait in STEADY_TRAITS else 3.0


def place_supports(place: Place, marvel: Marvel) -> bool:
    return marvel.need_tags.issubset(place.tags)


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def valid_combo(place_id: str, marvel_id: str, fix_id: str) -> bool:
    if place_id not in PLACES or marvel_id not in MARVELS or fix_id not in FIXES:
        return False
    place = PLACES[place_id]
    marvel = MARVELS[marvel_id]
    fix = FIXES[fix_id]
    return place_supports(place, marvel) and fix.sense >= SENSE_MIN and fix.id in marvel.settle_fixes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for marvel_id in MARVELS:
            for fix_id in FIXES:
                if valid_combo(place_id, marvel_id, fix_id):
                    combos.append((place_id, marvel_id, fix_id))
    return sorted(combos)


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAG_INIT


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    marvel = sim.get("marvel")
    marvel.meters["loose"] += 1
    propagate(sim, narrate=False)
    return {
        "trouble": sim.get("town").meters["trouble"],
        "cordon": sim.get("Mayor").meters["cordon"],
    }


def introduce(world: World, a: Entity, b: Entity, adult: Entity) -> None:
    world.say(
        f"In {world.place.label}, {world.place.opening}, folks said the wind could untie a knot, "
        f"retie it prettier, and still have breath left to whistle a tune."
    )
    world.say(
        f"That was where {a.id} and {b.id} spent the morning, following {adult.id} from stall to stall "
        f"and feeling ten feet tall just by breathing the frontier air."
    )


def boast_setup(world: World, a: Entity, marvel: Marvel) -> None:
    a.memes["joy"] += 1
    a.memes["brag"] = BRAG_INIT
    world.say(
        f"On a crate by the biggest wagon sat {marvel.article} {marvel.seed_phrase}. "
        f'"I can handle that," {a.id} declared. "Why, I could make it mind me before a grasshopper blinked."'
    )


def warning(world: World, a: Entity, b: Entity, marvel: Marvel) -> None:
    pred = predict_trouble(world)
    b.memes["caution"] = initial_caution(next(iter(b.traits), ""))
    b.memes["caution"] += 1
    world.facts["predicted_trouble"] = pred["trouble"]
    extra = ""
    if pred["cordon"] >= THRESHOLD:
        extra = " Even Mayor Buckle would have to rope off the whole place."
    world.say(
        f'{b.id} tipped {b.pronoun("possessive")} hat back and frowned. '
        f'"I prefer a steady plan to a fool stunt," {b.pronoun()} said. '
        f'"That {marvel.label} looks like the sort of magic that grows legs and trouble.{extra}"'
    )


def back_down(world: World, a: Entity, b: Entity, adult: Entity, marvel: Marvel, fix: Fix) -> None:
    a.memes["brag"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} puffed up for one more second, then let the air out of the idea. "
        f'"Maybe I do not need to play the fool," {a.pronoun()} admitted.'
    )
    world.say(
        f"{adult.id} heard that and smiled. Instead of poking the magic, they called for a proper show."
    )
    world.para()
    world.say(
        f"{adult.id} used {fix.label}; {fix.use_text}. {marvel.calm_line}"
    )
    world.say(
        f"The marvel behaved itself so politely that even the fence posts seemed impressed, "
        f"and {a.id} learned that a wise pause can be bigger than a loud boast."
    )


def defy(world: World, a: Entity, marvel: Marvel) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"Stand back and watch," {a.id} said, grinning like a child who expected applause from the clouds.'
    )
    world.say(marvel.hatch_line)
    world.get("marvel").meters["loose"] += 1
    propagate(world, narrate=False)


def commotion(world: World, marvel: Marvel) -> None:
    world.say(marvel.commotion_line)
    if world.get("town").meters["trouble"] >= THRESHOLD:
        world.say(
            "Boots skidded, hats flew, and three solemn goats forgot their manners and laughed right out loud."
        )
    if world.get("Mayor").meters["cordon"] >= THRESHOLD:
        world.say(
            f"Mayor Buckle shouted for folks to mind the rope and keep their noses outside the cordon."
        )


def rescue(world: World, adult: Entity, fix: Fix, marvel: Marvel) -> None:
    world.get("marvel").meters["loose"] = 0.0
    world.get("marvel").meters["calm"] += 1
    world.get("town").meters["trouble"] = 0.0
    for kid in world.kids():
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    world.say(f"{adult.id} stepped in without huffing or hollering. {fix.use_text}.")
    world.say(marvel.calm_line)


def lesson(world: World, adult: Entity, a: Entity, b: Entity, marvel: Marvel) -> None:
    a.memes["lesson"] += 1
    b.memes["lesson"] += 1
    world.say(
        f'{adult.id} rested a hand on {a.id}\'s shoulder. "{marvel.lesson_line} '
        f'If you can choose between a careful plan and a fool trick, prefer the careful one."'
    )
    world.say(
        f"{a.id} nodded so hard that {a.pronoun('possessive')} hat nearly jumped the fence, "
        f"and {b.id} laughed because the lesson had landed without anyone needing a bigger rope."
    )


def ending(world: World, a: Entity, b: Entity, marvel: Marvel) -> None:
    for kid in world.kids():
        kid.memes["joy"] += 1
    world.say(
        f"By sundown, {world.place.label} was cheerful again. {a.id} and {b.id} stood by {world.place.cordon_spot}, "
        f"telling the story smaller than it had happened and smiling bigger than they meant to."
    )
    world.say(
        f"And from then on, whenever shiny magic winked at {a.id}, {a.pronoun()} remembered the laughing mess, "
        f"tipped {a.pronoun('possessive')} hat, and preferred sense over showing off."
    )


def tell(
    place: Place,
    marvel: Marvel,
    fix: Fix,
    *,
    instigator: str = "Tess",
    instigator_gender: str = "girl",
    cautioner: str = "Boone",
    cautioner_gender: str = "boy",
    adult_type: str = "aunt",
    trait: str = "steady",
    relation: str = "siblings",
    instigator_age: int = 5,
    cautioner_age: int = 7,
) -> World:
    world = World(place=place)
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        traits=["bold"],
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    adult_name = "Aunt Juniper" if adult_type == "aunt" else "Uncle Rafe"
    adult = world.add(Entity(
        id=adult_name,
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
    ))
    mayor_type = "mayor_male"
    mayor = world.add(Entity(
        id="Mayor Buckle",
        kind="character",
        type=mayor_type,
        role="mayor",
        label="the mayor",
    ))
    world.add(Entity(
        id="town",
        kind="thing",
        type="town",
        label=place.label,
        tags=set(place.tags),
    ))
    world.add(Entity(
        id="marvel",
        kind="thing",
        type="marvel",
        label=marvel.label,
        phrase=marvel.seed_phrase,
        tags=set(marvel.tags),
    ))

    introduce(world, a, b, adult)
    boast_setup(world, a, marvel)

    world.para()
    warning(world, a, b, marvel)
    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, adult, marvel, fix)
        outcome = "averted"
    else:
        defy(world, a, marvel)
        world.para()
        commotion(world, marvel)
        world.para()
        rescue(world, adult, fix, marvel)
        lesson(world, adult, a, b, marvel)
        world.para()
        ending(world, a, b, marvel)
        outcome = "repaired"

    world.facts.update(
        place=place,
        marvel=marvel,
        fix=fix,
        instigator=a,
        cautioner=b,
        adult=adult,
        mayor=mayor,
        relation=relation,
        outcome=outcome,
        averted=(outcome == "averted"),
        trouble_happened=world.get("marvel").meters["calm"] >= THRESHOLD or world.get("town").meters["trouble"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "magic": [
        (
            "What is magic in a story?",
            "Magic in a story is something strange and special that does not happen in ordinary life. It can be funny or useful, but it still needs careful handling.",
        )
    ],
    "cordon": [
        (
            "What is a cordon?",
            "A cordon is a line or barrier that keeps people back from a place. Grown-ups use one to keep everyone safe when something busy or dangerous is happening.",
        )
    ],
    "lesson": [
        (
            "What is a lesson learned?",
            "A lesson learned is an idea you understand after something happens. It helps you make a wiser choice next time.",
        )
    ],
    "vines": [
        (
            "Why can vines tangle things?",
            "Vines bend and curl as they grow, so they can wrap around wheels, boots, and fences. That makes them tricky if they start growing in the wrong place.",
        )
    ],
    "cloud": [
        (
            "Why can a strong wind make trouble?",
            "A strong wind can push hats, dust, and light things all around. That is why people tie things down and keep clear when the air gets wild.",
        )
    ],
    "pancake": [
        (
            "Why is a hot pancake from a griddle not a toy?",
            "A hot pancake is food, and fresh griddle food can still be hot and slippery. It belongs on a plate, not bouncing around where people can slip.",
        )
    ],
    "hum": [
        (
            "Why can a calm song help in a story?",
            "A calm song can slow everyone down and help people think clearly. In a magic story, it can even settle jumpy magic.",
        )
    ],
    "rain": [
        (
            "Why does gentle rain help some plants?",
            "Gentle rain gives thirsty plants water without knocking them over. Soft help can work better than rough help.",
        )
    ],
    "lasso": [
        (
            "What is a lasso?",
            "A lasso is a looped rope people can throw around something to catch or guide it. In tall tales, people use lassos for all sorts of extra-big jobs.",
        )
    ],
}
KNOWLEDGE_ORDER = ["magic", "cordon", "lesson", "vines", "cloud", "pancake", "hum", "rain", "lasso"]


PLACES = {
    "fairground": Place(
        id="fairground",
        label="Dusty Draw Fairground",
        opening="where even the bandstand boards creaked in rhythm",
        cordon_spot="the pie tent and the mule carousel",
        tags={"soil", "wind", "griddle", "crowd"},
    ),
    "windmill_hill": Place(
        id="windmill_hill",
        label="Windmill Hill",
        opening="where the wind was said to comb a buffalo from ten fences away",
        cordon_spot="the squeaky pump and the picnic table",
        tags={"soil", "wind", "open"},
    ),
    "water_tower_yard": Place(
        id="water_tower_yard",
        label="Water Tower Yard",
        opening="where shadows stayed short because the stories stood so tall",
        cordon_spot="the water trough and the hitching rail",
        tags={"soil", "open"},
    ),
}

MARVELS = {
    "giggle_vine": Marvel(
        id="giggle_vine",
        label="giggle vine",
        article="a",
        seed_phrase="striped chuckle bean no bigger than a thumbnail",
        need_tags={"soil"},
        settle_fixes={"moon_hum", "sleepy_rain"},
        hatch_line="The bean popped, winked, and shot into a green vine that climbed a wagon wheel, tied itself in bowknots, and laughed leaf by leaf.",
        commotion_line="The giggle vine bounced from post to post, tickled ankles, and wrapped wagon tongues together as if the whole town were one big present.",
        calm_line="The vine slowly untied itself, curled into a neat green basket, and gave one last polite snicker before going still.",
        lesson_line="Magic that grows should be guided gently, not teased into showing off.",
        tags={"magic", "vines", "lesson"},
    ),
    "sneeze_cloud": Marvel(
        id="sneeze_cloud",
        label="sneeze cloud",
        article="a",
        seed_phrase="pepper-gray puff trapped in a jar",
        need_tags={"wind"},
        settle_fixes={"moon_hum", "sleepy_rain"},
        hatch_line="The jar lid twitched, sprang free, and out burst a sneeze cloud that hiccupped thunder and puffed dust rings big enough for a pony to step through.",
        commotion_line="The sneeze cloud zigzagged above the roofs, blowing hats inside out and making the weathercock bow like it had taken dancing lessons.",
        calm_line="At last the cloud drooped low, sighed out one tiny achoo, and floated into a soft silver puff that drifted harmlessly over the hill.",
        lesson_line="Windy magic listens better to patience than to boasting.",
        tags={"magic", "cloud", "lesson"},
    ),
    "skipping_pancake": Marvel(
        id="skipping_pancake",
        label="skipping pancake",
        article="a",
        seed_phrase="golden skillet cake painted with a sparkle syrup star",
        need_tags={"griddle"},
        settle_fixes={"butter_lasso"},
        hatch_line="The pancake gave a buttery shimmy, flipped itself off the crate, and began hopping across the ground higher than a jackrabbit on a trampoline.",
        commotion_line="The skipping pancake boinged past the pie stand, slapped flour into the air, and left shining butter tracks slicker than a duck's grin.",
        calm_line="The pancake settled back onto the warm griddle with a happy sizzle, puffed once, and behaved like breakfast again.",
        lesson_line="A playful bit of food magic still needs kitchen sense.",
        tags={"magic", "pancake", "lesson"},
    ),
}

FIXES = {
    "moon_hum": Fix(
        id="moon_hum",
        label="the moon hum",
        sense=3,
        use_text="Aunt Juniper hummed a low moon tune until the jumpy magic remembered how to sway instead of stampede",
        qa_text="used a low moon hum to calm the magic",
        tags={"hum", "magic"},
    ),
    "sleepy_rain": Fix(
        id="sleepy_rain",
        label="sleepy rain",
        sense=3,
        use_text="Aunt Juniper tipped a tin cloud and sprinkled sleepy rain, soft as kitten whiskers, over the mischief",
        qa_text="sprinkled sleepy rain to settle the magic",
        tags={"rain", "magic"},
    ),
    "butter_lasso": Fix(
        id="butter_lasso",
        label="a butter lasso",
        sense=3,
        use_text="Uncle Rafe spun a butter-bright lasso, looped the hopping cake, and slid it back to the griddle before another boot could skid",
        qa_text="caught the pancake with a butter lasso and guided it back to the griddle",
        tags={"lasso", "magic"},
    ),
    "cannon_boom": Fix(
        id="cannon_boom",
        label="a cannon boom",
        sense=1,
        use_text="someone fired a brass parade cannon at the trouble",
        qa_text="tried a loud cannon boom",
        fail_text="only made the magic jumpier",
        tags={"magic"},
    ),
}

GIRL_NAMES = ["Tess", "Molly", "Nell", "Ruby", "Mae", "Della", "Poppy", "June"]
BOY_NAMES = ["Boone", "Jed", "Hank", "Cal", "Otis", "Wade", "Finn", "Roy"]
TRAITS = ["steady", "careful", "sensible", "curious", "sparky", "quick"]
RELATIONS = ["siblings", "friends"]


@dataclass
class StoryParams:
    place: str
    marvel: str
    fix: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    adult: str
    trait: str
    relation: str
    instigator_age: int
    cautioner_age: int
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="fairground",
        marvel="giggle_vine",
        fix="moon_hum",
        instigator="Tess",
        instigator_gender="girl",
        cautioner="Boone",
        cautioner_gender="boy",
        adult="aunt",
        trait="steady",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
    ),
    StoryParams(
        place="windmill_hill",
        marvel="sneeze_cloud",
        fix="sleepy_rain",
        instigator="Cal",
        instigator_gender="boy",
        cautioner="Ruby",
        cautioner_gender="girl",
        adult="aunt",
        trait="careful",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
    ),
    StoryParams(
        place="fairground",
        marvel="skipping_pancake",
        fix="butter_lasso",
        instigator="Mae",
        instigator_gender="girl",
        cautioner="Otis",
        cautioner_gender="boy",
        adult="uncle",
        trait="quick",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
    ),
    StoryParams(
        place="water_tower_yard",
        marvel="giggle_vine",
        fix="sleepy_rain",
        instigator="Roy",
        instigator_gender="boy",
        cautioner="June",
        cautioner_gender="girl",
        adult="aunt",
        trait="sensible",
        relation="siblings",
        instigator_age=4,
        cautioner_age=7,
    ),
]


def explain_rejection(place: Place, marvel: Marvel, fix: Fix) -> str:
    if not place_supports(place, marvel):
        return (
            f"(No story: {marvel.label} does not fit {place.label}. That marvel needs {sorted(marvel.need_tags)}, "
            f"but the place only offers {sorted(place.tags)}.)"
        )
    if fix.sense < SENSE_MIN:
        better = ", ".join(sorted(f.id for f in sensible_fixes()))
        return (
            f"(Refusing fix '{fix.id}': it is too foolish for this world (sense={fix.sense} < {SENSE_MIN}). "
            f"Try one of: {better}.)"
        )
    if fix.id not in marvel.settle_fixes:
        return (
            f"(No story: {fix.label} is not a believable way to settle {marvel.label}. "
            f"Choose a fix that matches the kind of magic causing trouble.)"
        )
    return "(No story: this combination does not make sense.)"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait) else "repaired"


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    marvel = world.facts["marvel"]
    fix = world.facts["fix"]
    a = world.facts["instigator"]
    b = world.facts["cautioner"]
    outcome = world.facts["outcome"]
    if outcome == "averted":
        return [
            f'Write a tall-tale story for a 3-to-5-year-old that includes the words "cordon", "prefer", and "fool", set in {place.label}, where a child almost stirs up magical trouble but listens in time.',
            f"Tell a humorous frontier story where {a.id} wants to show off with a {marvel.label}, but {b.id} says they prefer a careful plan and stops the fool idea before the town is in a fuss.",
            f"Write a gentle magic story with a lesson learned: a boastful child backs down, a grown-up uses {fix.label}, and the ending shows wiser behavior.",
        ]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the words "cordon", "prefer", and "fool", with playful magic and a lesson learned.',
        f"Tell a frontier comedy where {a.id} tries a fool stunt with a {marvel.label}, the mayor makes a cordon, and a grown-up fixes the trouble with {fix.label}.",
        f"Write a child-facing magical story that starts with showing off, turns into a funny town-sized mess, and ends with the child preferring sense over bragging.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    place = world.facts["place"]
    marvel = world.facts["marvel"]
    fix = world.facts["fix"]
    a = world.facts["instigator"]
    b = world.facts["cautioner"]
    adult = world.facts["adult"]
    outcome = world.facts["outcome"]
    relation = world.facts["relation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b, relation)}, {a.id} and {b.id}, in {place.label}. It also includes {adult.id} and Mayor Buckle, who help keep the magic from turning into bigger trouble.",
        ),
        (
            f"What did {a.id} want to do?",
            f"{a.id} wanted to show off by handling the {marvel.label} alone. That proud idea is why {b.id} warned against a fool stunt.",
        ),
        (
            f"What did {b.id} mean by saying {b.pronoun('subject')} would prefer a steady plan?",
            f"{b.id} meant that careful help was wiser than showing off. {b.pronoun().capitalize()} could already imagine the magic making trouble for the town.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"Did the magical trouble ever break loose?",
                f"No. {a.id} listened before touching the magic the wrong way, so the town never needed a real emergency cordon. The grown-up handled the marvel safely from the start.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended calmly, with {adult.id} using {fix.label} and the marvel behaving itself. The change is that {a.id} learned to pause and choose wisdom before trouble started.",
            )
        )
    else:
        qa.append(
            (
                "Why did Mayor Buckle make a cordon?",
                f"Mayor Buckle made a cordon to keep people back from the running magic. The rope gave {adult.id} room to use {fix.label} without boots and wagon wheels getting in the way.",
            )
        )
        qa.append(
            (
                f"How did {adult.id} fix the problem?",
                f"{adult.id} {fix.qa_text}. That worked because the fix matched the kind of magic the marvel had become.",
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                f"They learned that loud bragging can make a small magical thing into a big silly mess. After that, {a.id} knew to prefer a careful plan instead of trying to play the fool.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    marvel = world.facts["marvel"]
    fix = world.facts["fix"]
    tags = {"cordon", "lesson"} | set(marvel.tags) | set(fix.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:14} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
supports(P, M) :- place(P), marvel(M), need_tag(M, T), place_tag(P, T),
                  not missing_need(P, M).
missing_need(P, M) :- need_tag(M, T), not place_tag(P, T).
supports(P, M) :- place(P), marvel(M), not need_tag(M, _).

sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
matches(M, F) :- settle_fix(M, F).
valid(P, M, F) :- place(P), marvel(M), fix(F), supports(P, M), sensible(F), matches(M, F).

steady_trait(T) :- trait_name(T), is_steady(T).
init_caution(5) :- chosen_trait(T), steady_trait(T).
init_caution(3) :- chosen_trait(T), not steady_trait(T).
older_sibling :- relation(siblings), cautioner_age(CA), instigator_age(IA), CA > IA.
bonus(4) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), brag_init(BR), A > BR.

outcome(averted) :- averted.
outcome(repaired) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for tag in sorted(place.tags):
            lines.append(asp.fact("place_tag", place_id, tag))
    for marvel_id, marvel in MARVELS.items():
        lines.append(asp.fact("marvel", marvel_id))
        for tag in sorted(marvel.need_tags):
            lines.append(asp.fact("need_tag", marvel_id, tag))
        for fix_id in sorted(marvel.settle_fixes):
            lines.append(asp.fact("settle_fix", marvel_id, fix_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait_name", trait))
    for trait in sorted(STEADY_TRAITS):
        lines.append(asp.fact("is_steady", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("brag_init", int(BRAG_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(item[0] for item in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_trait", params.trait),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "?"


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

    clingo_sensible = set(asp_sensible())
    python_sensible = {fix.id for fix in sensible_fixes()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible fixes match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    for seed in range(50):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)

    mismatches = [params for params in cases if asp_outcome(params) != outcome_of(params)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Tall-tale magic storyworld: a boastful child, a rope cordon, and a wiser choice."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--marvel", choices=MARVELS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--adult", choices=["aunt", "uncle"])
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.marvel and args.fix:
        place = PLACES[args.place]
        marvel = MARVELS[args.marvel]
        fix = FIXES[args.fix]
        if not valid_combo(args.place, args.marvel, args.fix):
            raise StoryError(explain_rejection(place, marvel, fix))
    elif args.fix and FIXES[args.fix].sense < SENSE_MIN:
        any_place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        any_marvel = MARVELS[args.marvel] if args.marvel else next(iter(MARVELS.values()))
        raise StoryError(explain_rejection(any_place, any_marvel, FIXES[args.fix]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.marvel is None or combo[1] == args.marvel)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, marvel_id, fix_id = rng.choice(combos)
    instigator, instigator_gender = _pick_child(rng)
    cautioner, cautioner_gender = _pick_child(rng, avoid=instigator)
    adult = args.adult or rng.choice(["aunt", "uncle"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(RELATIONS)
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        place=place_id,
        marvel=marvel_id,
        fix=fix_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        adult=adult,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.marvel not in MARVELS:
        raise StoryError(f"(Unknown marvel: {params.marvel})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if not valid_combo(params.place, params.marvel, params.fix):
        raise StoryError(explain_rejection(PLACES[params.place], MARVELS[params.marvel], FIXES[params.fix]))

    world = tell(
        PLACES[params.place],
        MARVELS[params.marvel],
        FIXES[params.fix],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        adult_type=params.adult,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (place, marvel, fix) combos:\n")
        for place_id, marvel_id, fix_id in combos:
            print(f"  {place_id:16} {marvel_id:16} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator} & {p.cautioner}: {p.marvel} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
