#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/daisy_energetic_transformation_foreshadowing_tall_tale.py
====================================================================================

A standalone storyworld for a tall-tale flavored transformation story built from
the seed words "daisy" and "energetic".

Premise
-------
An energetic child notices a daisy in a windy place. A gentle bit of
foreshadowing hints that the day may grow too wild. The child tries to make the
daisy grow in an exaggerated tall-tale way, causing a magical transformation:
the daisy grows enormous and starts carrying things with its giant stem and
petals. A calm helper guides the child toward a better use of that impossible
change, and the ending proves what changed.

Reasonableness constraint
-------------------------
Not every combination makes a sensible tall tale. This world only tells stories
when the chosen place naturally affords strong wind, the chosen boast method can
plausibly trigger magical overgrowth, and the chosen use matches the flower's
new size. The Python gate and the inline ASP twin enforce the same compatibility.

Run it
------
python storyworlds/worlds/gpt-5.4/daisy_energetic_transformation_foreshadowing_tall_tale.py
python storyworlds/worlds/gpt-5.4/daisy_energetic_transformation_foreshadowing_tall_tale.py --place hill --method singing --use shade
python storyworlds/worlds/gpt-5.4/daisy_energetic_transformation_foreshadowing_tall_tale.py --place cellar
python storyworlds/worlds/gpt-5.4/daisy_energetic_transformation_foreshadowing_tall_tale.py --all --qa
python storyworlds/worlds/gpt-5.4/daisy_energetic_transformation_foreshadowing_tall_tale.py --verify
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
WIND_MIN = 2
ENERGY_START = 3.0


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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    wind: int
    afford_tall_tale: bool
    omen: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    action: str
    boast: str
    growth: int
    works_in_wind: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class GiantUse:
    id: str
    label: str
    need_size: int
    solve_text: str
    ending_image: str
    qa_text: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_giant_daisy(world: World) -> list[str]:
    flower = world.get("daisy")
    if flower.meters["growth"] < THRESHOLD:
        return []
    sig = ("giant", "daisy")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    flower.meters["giant"] += 1
    world.get("place").meters["surprise"] += 1
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["wonder"] += 1
    helper.memes["wonder"] += 1
    return ["__giant__"]


def _r_stem_sways(world: World) -> list[str]:
    flower = world.get("daisy")
    place = world.get("place")
    if flower.meters["giant"] < THRESHOLD or place.meters["wind"] < THRESHOLD:
        return []
    sig = ("sway", "daisy")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    flower.meters["swaying"] += 1
    world.get("hero").memes["alarm"] += 1
    return ["__sway__"]


CAUSAL_RULES = [
    Rule(name="giant_daisy", tag="physical", apply=_r_giant_daisy),
    Rule(name="stem_sways", tag="physical", apply=_r_stem_sways),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(place: Place, method: Method, use: GiantUse) -> bool:
    return place.afford_tall_tale and place.wind >= WIND_MIN and method.works_in_wind and method.growth >= use.need_size


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for method_id, method in METHODS.items():
            for use_id, use in USES.items():
                if valid_combo(place, method, use):
                    out.append((place_id, method_id, use_id))
    return out


def explain_rejection(place: Place, method: Method, use: GiantUse) -> str:
    if not place.afford_tall_tale:
        return f"(No story: {place.label} is too shut-in for this windy tall tale. Pick a breezier place where a daisy could feel larger than life.)"
    if place.wind < WIND_MIN:
        return f"(No story: {place.label} is not windy enough to support the foreshadowed gusty day that drives this tale.)"
    if not method.works_in_wind:
        return f"(No story: {method.label} does not make sense as a gusty, boastful way to wake the daisy's magic here.)"
    if method.growth < use.need_size:
        return f"(No story: {method.label} would not grow the daisy large enough to {use.label}. Choose a smaller use or a bolder method.)"
    return "(No story: this combination is not reasonable in this world.)"


def predict_growth(world: World, method: Method) -> dict:
    sim = world.copy()
    flower = sim.get("daisy")
    hero = sim.get("hero")
    flower.meters["growth"] += float(method.growth)
    hero.memes["boast"] += 1
    propagate(sim, narrate=False)
    return {
        "giant": flower.meters["giant"] >= THRESHOLD,
        "growth": flower.meters["growth"],
        "swaying": flower.meters["swaying"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    hero.memes["energy"] = ENERGY_START
    world.say(
        f"In {place.phrase}, there lived an energetic child named {hero.id} who could never cross the ground in ordinary little steps."
    )
    world.say(
        f"{hero.pronoun().capitalize()} bounced, skipped, and twirled so fast that even the grass seemed to lean aside to make room."
    )
    world.say(
        f"{helper.id}, {hero.pronoun('possessive')} {helper.attrs['relation']}, often laughed and said the day had to run hard just to keep up."
    )


def discover_daisy(world: World, hero: Entity, place: Place) -> None:
    flower = world.get("daisy")
    world.say(
        f"One morning {hero.id} spotted a daisy standing alone in {place.label}, white as a star and brave as a lantern."
    )
    flower.memes["noticed"] += 1
    world.say(
        f"It was only a small flower, but it held its yellow face so high that it looked as if it expected something grand."
    )


def foreshadow(world: World, helper: Entity, place: Place) -> None:
    place_ent = world.get("place")
    place_ent.meters["wind"] = float(place.wind)
    helper.memes["caution"] += 1
    world.say(
        f"{place.omen} {helper.id} narrowed {helper.pronoun('possessive')} eyes and said, \"That breeze is practicing for mischief.\""
    )
    world.say(
        "It was the kind of warning that sounds silly at first and clever later."
    )


def boast(world: World, hero: Entity, method: Method) -> None:
    hero.memes["boast"] += 1
    world.say(
        f"That only made {hero.id} grin wider. \"Then I will outdo the wind,\" {hero.pronoun()} declared. \"I can {method.boast}.\""
    )
    world.say(
        f"So {hero.pronoun()} began {method.action} around the daisy with the confidence of ten brass bands and a parade besides."
    )


def transform(world: World, hero: Entity, method: Method) -> None:
    flower = world.get("daisy")
    flower.meters["growth"] += float(method.growth)
    propagate(world, narrate=False)
    flower.memes["magic"] += 1
    world.say(
        "At first nothing happened but a whirl of dust and a shiver in the stem."
    )
    if flower.meters["giant"] >= THRESHOLD:
        world.say(
            "Then the daisy stretched. It stretched past the fence, past the weather vane, and past the idea of good sense."
        )
        world.say(
            f"In a blink it was no garden flower at all, but a towering daisy with petals broad as porch roofs and a stem thick as a wagon post."
        )
    else:
        world.say(
            "The daisy gave one polite nod, but it did not truly become the giant wonder this tale requires."
        )


def wobble(world: World, hero: Entity, helper: Entity) -> None:
    flower = world.get("daisy")
    place_ent = world.get("place")
    if flower.meters["giant"] >= THRESHOLD and place_ent.meters["wind"] >= THRESHOLD:
        propagate(world, narrate=False)
        world.say(
            "Just then the practicing breeze came back as a full-grown gust, and the giant blossom began to sway over the whole place."
        )
        world.say(
            f"{hero.id}'s grin slid sideways. Even an energetic heart can thump once when a miracle starts leaning."
        )
        helper.memes["steady"] += 1


def guide(world: World, helper: Entity, use: GiantUse) -> None:
    helper.memes["care"] += 1
    world.say(
        f'But {helper.id} did not shout. "{use.solve_text}," {helper.pronoun()} said, as calm as if giant daisies happened every Tuesday.'
    )


def resolve_use(world: World, hero: Entity, helper: Entity, use: GiantUse) -> None:
    flower = world.get("daisy")
    hero.memes["wisdom"] += 1
    hero.memes["joy"] += 1
    helper.memes["relief"] += 1
    flower.attrs["used_for"] = use.id
    world.say(
        f"{hero.id} stopped showing off and started helping. Together they turned the impossible flower toward a kinder purpose."
    )
    world.say(use.ending_image)
    world.say(
        f"After that, whenever {hero.id} felt a wild idea rattling around inside, {hero.pronoun()} remembered that big changes shine brightest when they help somebody."
    )


def tell(place: Place, method: Method, use: GiantUse,
         hero_name: str = "Daisy", hero_gender: str = "girl",
         helper_name: str = "Uncle Ash", helper_type: str = "man") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    relation = "uncle" if helper_type == "man" else "aunt"
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="helper",
        attrs={"relation": relation},
    ))
    world.add(Entity(
        id="place",
        type="place",
        label=place.label,
        phrase=place.phrase,
        tags=set(place.tags),
    ))
    world.add(Entity(
        id="daisy",
        type="flower",
        label="daisy",
        phrase="a brave little daisy",
        tags={"daisy", "flower"},
    ))

    introduce(world, hero, helper, place)
    discover_daisy(world, hero, place)
    world.para()
    foreshadow(world, helper, place)
    boast(world, hero, method)
    world.para()
    transform(world, hero, method)
    wobble(world, hero, helper)
    guide(world, helper, use)
    world.para()
    resolve_use(world, hero, helper, use)

    world.facts.update(
        place=place,
        method=method,
        use=use,
        hero=hero,
        helper=helper,
        daisy=world.get("daisy"),
        giant=world.get("daisy").meters["giant"] >= THRESHOLD,
        swaying=world.get("daisy").meters["swaying"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    method: str
    use: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


PLACES = {
    "hill": Place(
        id="hill",
        label="the windy hill",
        phrase="the windy hill above the town",
        wind=3,
        afford_tall_tale=True,
        omen="The buttercups bowed flat, and the clouds lined up like oxen before a race.",
        tags={"wind", "hill"},
    ),
    "meadow": Place(
        id="meadow",
        label="the broad meadow",
        phrase="the broad meadow past the creek",
        wind=2,
        afford_tall_tale=True,
        omen="The long grass hissed in one direction, then another, as if the air could not sit still.",
        tags={"wind", "meadow"},
    ),
    "orchard": Place(
        id="orchard",
        label="the old orchard edge",
        phrase="the old orchard edge where the rows broke open to the sky",
        wind=2,
        afford_tall_tale=True,
        omen="The apples knocked softly together though nobody had touched a branch.",
        tags={"wind", "orchard"},
    ),
    "cellar": Place(
        id="cellar",
        label="the stone cellar",
        phrase="the stone cellar under the house",
        wind=0,
        afford_tall_tale=False,
        omen="No leaf stirred there at all.",
        tags={"indoors"},
    ),
}

METHODS = {
    "singing": Method(
        id="singing",
        label="singing",
        action="singing in circles",
        boast="sing louder than a kettle train",
        growth=3,
        works_in_wind=True,
        tags={"song", "boast"},
    ),
    "stomping": Method(
        id="stomping",
        label="stomping",
        action="stomping a ring into the earth",
        boast="stamp enough thunder into the ground to wake roots a mile away",
        growth=2,
        works_in_wind=True,
        tags={"stomp", "boast"},
    ),
    "whistling": Method(
        id="whistling",
        label="whistling",
        action="whistling at the gusts",
        boast="whistle a tune the wind itself will have to follow",
        growth=1,
        works_in_wind=True,
        tags={"whistle", "boast"},
    ),
    "watering_can": Method(
        id="watering_can",
        label="watering with a can",
        action="pouring a neat trickle of water",
        boast="pour enough to make a polite flower feel refreshed",
        growth=1,
        works_in_wind=False,
        tags={"water"},
    ),
}

USES = {
    "shade": GiantUse(
        id="shade",
        label="make shade for the tired workers",
        need_size=2,
        solve_text="If it is going to be that big, turn its petals toward the road and let the tired melon pickers rest in the cool shadow",
        ending_image="By noon a whole row of melon pickers sat under the daisy's giant white petals, eating bread in a patch of flower shade as soft as a porch roof.",
        qa_text="They used the giant petals as shade for tired workers on the road.",
        tags={"shade", "helping"},
    ),
    "bridge": GiantUse(
        id="bridge",
        label="lay a bridge over the ditch",
        need_size=3,
        solve_text="If it is going to wave around up there, bend the stem across the ditch so the geese and children can cross dry-footed",
        ending_image="Soon the thick green stem arched over the ditch like a springy bridge, and children crossed laughing while the geese marched underneath in solemn white lines.",
        qa_text="They bent the stem into a bridge over the ditch.",
        tags={"bridge", "helping"},
    ),
    "weathervane": GiantUse(
        id="weathervane",
        label="point out the weather",
        need_size=1,
        solve_text="If it insists on dancing with the gusts, tie bright ribbons to the petals and let everyone read the weather from its turning head",
        ending_image="Before evening the giant blossom stood above the roofs with ribbons streaming from its petals, and every baker and washerwoman could tell the wind's mood at a glance.",
        qa_text="They turned the giant daisy into a weather sign for the town.",
        tags={"weather", "helping"},
    ),
}

GIRL_NAMES = ["Daisy", "Mara", "June", "Nell", "Poppy", "Ruth"]
BOY_NAMES = ["Jasper", "Eli", "Tate", "Milo", "Ben", "Otis"]
HELPERS = [
    {"name": "Uncle Ash", "type": "man"},
    {"name": "Aunt Fern", "type": "woman"},
    {"name": "Grandpa Reed", "type": "man"},
]

CURATED = [
    StoryParams(
        place="hill",
        method="singing",
        use="bridge",
        hero_name="Daisy",
        hero_gender="girl",
        helper_name="Uncle Ash",
        helper_type="man",
    ),
    StoryParams(
        place="meadow",
        method="stomping",
        use="shade",
        hero_name="June",
        hero_gender="girl",
        helper_name="Aunt Fern",
        helper_type="woman",
    ),
    StoryParams(
        place="orchard",
        method="whistling",
        use="weathervane",
        hero_name="Jasper",
        hero_gender="boy",
        helper_name="Grandpa Reed",
        helper_type="man",
    ),
]


KNOWLEDGE = {
    "daisy": [
        (
            "What is a daisy?",
            "A daisy is a small flower with white petals around a yellow middle. Many daisies grow low to the ground in grass or fields."
        )
    ],
    "wind": [
        (
            "What does wind do to flowers?",
            "Wind can make flowers sway and bend. A strong wind can also scatter seeds or shake petals."
        )
    ],
    "bridge": [
        (
            "What is a bridge for?",
            "A bridge helps people or animals cross over water, a ditch, or another gap without climbing down into it."
        )
    ],
    "shade": [
        (
            "Why is shade helpful on a hot day?",
            "Shade blocks some of the sun's heat and bright light. That can help people rest and cool down."
        )
    ],
    "weather": [
        (
            "How can people tell which way the wind is blowing?",
            "They can watch ribbons, flags, leaves, or weather vanes. Those things move in the wind and show its direction."
        )
    ],
    "transformation": [
        (
            "What is a transformation in a story?",
            "A transformation is when something changes into a very different form. In stories, that change often causes the big middle surprise."
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing?",
            "Foreshadowing is a small clue that hints at something important that will happen later. It helps the story feel like the ending was prepared for."
        )
    ],
}
KNOWLEDGE_ORDER = ["daisy", "wind", "bridge", "shade", "weather", "transformation", "foreshadowing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    method = f["method"]
    use = f["use"]
    return [
        'Write a tall-tale story for a 3-to-5-year-old that includes the words "daisy" and "energetic".',
        f"Tell a playful tall tale about an energetic child named {hero.id} who finds a daisy at {place.label}, boasts wildly, and accidentally causes a magical transformation.",
        f"Write a story with clear foreshadowing from the wind, then let the giant daisy become useful when the child and helper choose to {use.label} after all the showing off from {method.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    method = f["method"]
    use = f["use"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, an energetic child, a daisy that grows huge, and {helper.id}, the calm {helper.attrs['relation']} who helps at the turning point."
        ),
        (
            f"Where did {hero.id} find the daisy?",
            f"{hero.id} found it at {place.label}. The open, windy place matters because the breeze is part of the story's foreshadowing."
        ),
        (
            "What was the foreshadowing clue?",
            f"The strange wind signs and {helper.id}'s warning were the clue. They hinted that the day was getting ready for trouble before the daisy changed."
        ),
        (
            f"How did the daisy transform?",
            f"{hero.id} began {method.action} and bragging far too boldly, and then the flower stretched into a giant daisy. The transformation turns a tiny flower into something big enough to change the whole place."
        ),
    ]
    if f["swaying"]:
        qa.append(
            (
                "Why did the middle of the story feel a little dangerous?",
                "Once the daisy was enormous, the wind made it sway over everything. That turned the magical surprise into a problem that needed a wiser idea."
            )
        )
    qa.append(
        (
            f"How did {hero.id} and {helper.id} solve the problem?",
            f"They stopped using the giant daisy for showing off and used it to help people instead. {use.qa_text} That choice changed the ending from wild trouble into a useful wonder."
        )
    )
    qa.append(
        (
            f"What did {hero.id} learn?",
            f"{hero.id} learned that big energy can make a big mess if it is only for bragging. {hero.pronoun('subject').capitalize()} also learned that a grand change is best when it helps others."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"daisy", "wind", "transformation", "foreshadowing"}
    use = world.facts["use"]
    if "bridge" in use.tags:
        tags.add("bridge")
    if "shade" in use.tags:
        tags.add("shade")
    if "weather" in use.tags:
        tags.add("weather")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
windy(P) :- place(P), wind(P, W), wind_min(M), W >= M.
valid(P, M, U) :- place(P), method(M), use(U),
                  affords_tall_tale(P), windy(P), works_in_wind(M),
                  growth(M, G), need_size(U, N), G >= N.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("wind", place_id, place.wind))
        if place.afford_tall_tale:
            lines.append(asp.fact("affords_tall_tale", place_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("growth", method_id, method.growth))
        if method.works_in_wind:
            lines.append(asp.fact("works_in_wind", method_id))
    for use_id, use in USES.items():
        lines.append(asp.fact("use", use_id))
        lines.append(asp.fact("need_size", use_id, use.need_size))
    lines.append(asp.fact("wind_min", WIND_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def _validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.use not in USES:
        raise StoryError(f"(Unknown use: {params.use})")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown hero gender: {params.hero_gender})")
    if params.helper_type not in {"man", "woman"}:
        raise StoryError(f"(Unknown helper type: {params.helper_type})")
    place = PLACES[params.place]
    method = METHODS[params.method]
    use = USES[params.use]
    if not valid_combo(place, method, use):
        raise StoryError(explain_rejection(place, method, use))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: an energetic child, a daisy, a windy clue, and a giant transformation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--use", choices=USES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["man", "woman"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.method and args.use:
        place = PLACES[args.place]
        method = METHODS[args.method]
        use = USES[args.use]
        if not valid_combo(place, method, use):
            raise StoryError(explain_rejection(place, method, use))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.method is None or combo[1] == args.method)
        and (args.use is None or combo[2] == args.use)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, method_id, use_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_pick = rng.choice(HELPERS)
    helper_name = args.helper_name or helper_pick["name"]
    helper_type = args.helper_type or helper_pick["type"]
    return StoryParams(
        place=place_id,
        method=method_id,
        use=use_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        place=PLACES[params.place],
        method=METHODS[params.method],
        use=USES[params.use],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
    )
    prediction = predict_growth(world, METHODS[params.method])
    world.facts["predicted_giant"] = prediction["giant"]
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, method, use) combos:\n")
        for place_id, method_id, use_id in combos:
            print(f"  {place_id:8} {method_id:12} {use_id}")
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
            header = f"### {p.hero_name}: {p.method} at {p.place} -> {p.use}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
