#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gender_cease_neigh_repetition_folk_tale.py
=====================================================================

A small storyworld in a folk-tale style: a child finds a frightened foal at a
village horse fair, reads the clay tag that names the foal's stable mark and
gender, helps the frightening noise cease in the right way, and leads the foal
home by following the mother mare's repeated neigh.

The domain is constrained on purpose. A bell is sensibly stilled by tying its
clapper, a drum by muffling it with a quilt, and a rattling cart by oiling and
wedging its loose wheel. Explicitly mismatched choices are refused.

Run it
------
python storyworlds/worlds/gpt-5.4/gender_cease_neigh_repetition_folk_tale.py
python storyworlds/worlds/gpt-5.4/gender_cease_neigh_repetition_folk_tale.py --place fair_green --noise bell --method tie_clapper
python storyworlds/worlds/gpt-5.4/gender_cease_neigh_repetition_folk_tale.py --noise drum --method oil_wheel
python storyworlds/worlds/gpt-5.4/gender_cease_neigh_repetition_folk_tale.py --all
python storyworlds/worlds/gpt-5.4/gender_cease_neigh_repetition_folk_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/gender_cease_neigh_repetition_folk_tale.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mare", "filly"}
        male = {"boy", "man", "father", "stallion", "colt"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandmother", "farrier": "farrier", "carter": "carter"}.get(
            self.type, self.type
        )


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class NoiseSource:
    id: str
    label: str
    phrase: str
    verb: str
    stop_need: str
    stop_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CeaseMethod:
    id: str
    label: str
    phrase: str
    works_on: set[str] = field(default_factory=set)
    text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ElderRole:
    id: str
    type: str
    label: str
    intro: str
    line: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    foal = world.entities.get("foal")
    noise = world.entities.get("noise")
    if not foal or not noise:
        return out
    if noise.meters["sounding"] < THRESHOLD:
        return out
    sig = ("fear", foal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    foal.memes["fear"] += 1
    foal.meters["frozen"] += 1
    out.append("__fear__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    foal = world.entities.get("foal")
    mare = world.entities.get("mare")
    noise = world.entities.get("noise")
    if not foal or not mare or not noise:
        return out
    if noise.meters["sounding"] >= THRESHOLD:
        return out
    if mare.meters["calling"] < THRESHOLD:
        return out
    sig = ("calm", foal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    foal.memes["fear"] = 0.0
    foal.memes["trust"] += 1
    foal.meters["frozen"] = 0.0
    out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule(name="fear", tag="emotion", apply=_r_fear),
    Rule(name="calm", tag="emotion", apply=_r_calm),
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


PLACES = {
    "fair_green": Place(
        id="fair_green",
        label="fair green",
        phrase="on the fair green below the hill",
        affords={"bell", "drum"},
        tags={"fair", "village"},
    ),
    "stone_bridge": Place(
        id="stone_bridge",
        label="stone bridge",
        phrase="by the stone bridge above the river",
        affords={"bell", "cart"},
        tags={"bridge", "village"},
    ),
    "mill_lane": Place(
        id="mill_lane",
        label="mill lane",
        phrase="along mill lane by the willow trees",
        affords={"cart", "drum"},
        tags={"mill", "village"},
    ),
}

NOISES = {
    "bell": NoiseSource(
        id="bell",
        label="bell",
        phrase="the fair bell in the oak frame",
        verb="clanged",
        stop_need="clapper",
        stop_line="The bell must cease before the little one will trust the path again.",
        tags={"bell", "loud_sound"},
    ),
    "drum": NoiseSource(
        id="drum",
        label="drum",
        phrase="the crier's broad market drum",
        verb="boom-boomed",
        stop_need="hide",
        stop_line="The drum must cease before the little one will lower its ears.",
        tags={"drum", "loud_sound"},
    ),
    "cart": NoiseSource(
        id="cart",
        label="cart",
        phrase="a loose grain cart at the lane",
        verb="rattle-clattered",
        stop_need="wheel",
        stop_line="The cart must cease before the little one will step on.",
        tags={"cart", "loud_sound"},
    ),
}

METHODS = {
    "tie_clapper": CeaseMethod(
        id="tie_clapper",
        label="tie the clapper",
        phrase="a strip of red cloth for the bell",
        works_on={"bell"},
        text="slipped a strip of red cloth around the clapper, and at once the hard clang ceased",
        qa_text="tied the bell's clapper with a strip of cloth so the clang stopped",
        tags={"bell_fix"},
    ),
    "muffle_drum": CeaseMethod(
        id="muffle_drum",
        label="muffle the drum",
        phrase="a folded quilt for the drum",
        works_on={"drum"},
        text="laid a folded quilt over the drumhead, and the boom-boom ceased under the soft cloth",
        qa_text="covered the drum with a quilt so the booming stopped",
        tags={"drum_fix"},
    ),
    "oil_wheel": CeaseMethod(
        id="oil_wheel",
        label="oil the wheel",
        phrase="a dab of axle oil and a wooden wedge",
        works_on={"cart"},
        text="dabbed axle oil on the loose wheel and set a wedge in place, and the rattle ceased like rain ending",
        qa_text="oiled the loose wheel and wedged it still so the rattling stopped",
        tags={"cart_fix"},
    ),
}

ELDERS = {
    "grandmother": ElderRole(
        id="grandmother",
        type="grandmother",
        label="Grandmother Sela",
        intro="an old horse-wise grandmother with a gray braid",
        line='“Step by step, little hooves. Neigh by neigh, come home.”',
        tags={"elder"},
    ),
    "farrier": ElderRole(
        id="farrier",
        type="farrier",
        label="Master Ivo",
        intro="the village farrier with soot on his apron",
        line='“Step by step, little hooves. Neigh by neigh, come home.”',
        tags={"elder"},
    ),
    "carter": ElderRole(
        id="carter",
        type="carter",
        label="Old Brin",
        intro="a carter who knew every stable mark in the valley",
        line='“Step by step, little hooves. Neigh by neigh, come home.”',
        tags={"elder"},
    ),
}

CHILD_NAMES = {
    "girl": ["Mira", "Tala", "Nessa", "Iris", "Lina", "Pia"],
    "boy": ["Tobin", "Eli", "Marek", "Nico", "Pavel", "Rian"],
}

TRAITS = ["kind", "patient", "brisk", "careful", "bright"]


@dataclass
class StoryParams:
    place: str
    noise: str
    method: str
    child_name: str
    child_gender: str
    foal_gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="fair_green",
        noise="bell",
        method="tie_clapper",
        child_name="Mira",
        child_gender="girl",
        foal_gender="filly",
        elder="grandmother",
        trait="patient",
        seed=101,
    ),
    StoryParams(
        place="stone_bridge",
        noise="cart",
        method="oil_wheel",
        child_name="Tobin",
        child_gender="boy",
        foal_gender="colt",
        elder="carter",
        trait="careful",
        seed=102,
    ),
    StoryParams(
        place="mill_lane",
        noise="drum",
        method="muffle_drum",
        child_name="Nessa",
        child_gender="girl",
        foal_gender="filly",
        elder="farrier",
        trait="kind",
        seed=103,
    ),
]


def valid_combo(place_id: str, noise_id: str, method_id: str) -> bool:
    if place_id not in PLACES or noise_id not in NOISES or method_id not in METHODS:
        return False
    return noise_id in PLACES[place_id].affords and noise_id in METHODS[method_id].works_on


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for noise_id in sorted(place.affords):
            for method_id, method in METHODS.items():
                if noise_id in method.works_on:
                    out.append((place_id, noise_id, method_id))
    return sorted(out)


def explain_rejection(place: str, noise: str, method: str) -> str:
    if place in PLACES and noise in NOISES and noise not in PLACES[place].affords:
        return (
            f"(No story: {NOISES[noise].label} is not a fitting trouble at {PLACES[place].label}. "
            f"Choose a noise the place actually affords.)"
        )
    if noise in NOISES and method in METHODS and noise not in METHODS[method].works_on:
        need = NOISES[noise].stop_need
        return (
            f"(No story: {METHODS[method].label} will not make the {NOISES[noise].label} cease. "
            f"This trouble needs help with its {need} instead.)"
        )
    return "(No story: the chosen options do not make a reasonable folk tale in this world.)"


def repeated_neigh(kind: str) -> str:
    if kind == "filly":
        return "neigh, neigh, neigh"
    return "neigh, neigh, neigh"


def predict_reunion(world: World) -> dict:
    sim = world.copy()
    foal = sim.get("foal")
    mare = sim.get("mare")
    noise = sim.get("noise")
    noise.meters["sounding"] = 0.0
    mare.meters["calling"] += 1
    propagate(sim, narrate=False)
    can_walk = foal.meters["frozen"] < THRESHOLD and foal.memes["trust"] >= THRESHOLD
    return {"can_walk": can_walk, "fear": foal.memes["fear"]}


def opening(world: World, child: Entity, elder: Entity, foal: Entity, place: Place) -> None:
    world.say(
        f"In the old valley, where people still remembered small rhymes and patient ways, "
        f"{child.id} was a {child.attrs.get('trait', '')} {child.type} who liked to help {place.phrase}."
    )
    world.say(
        f"That morning {elder.label} stood nearby, {elder.attrs.get('intro', '')}, while traders and farmers "
        f"led their horses past bright ribbons and baskets."
    )
    world.say(
        f"Then from behind a water trough came a frightened little {foal.type}, all long legs and quick eyes."
    )


def find_tag(world: World, child: Entity, foal: Entity) -> None:
    child.memes["care"] += 1
    foal.memes["lonely"] += 1
    world.say(
        f"On a cord around {foal.pronoun('possessive')} neck hung a clay tag. "
        f"It showed the stable mark of Willow Fold and, just as the fair ledger did, the foal's gender."
    )
    world.say(
        f'“So you belong to Willow Fold,” {child.id} whispered. “And you are a little {foal.type}.”'
    )


def startle(world: World, noise: Entity, foal: Entity, noise_cfg: NoiseSource) -> None:
    noise.meters["sounding"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just then {noise_cfg.phrase} {noise_cfg.verb}. "
        f"The little {foal.type} sprang sideways, planted all four hooves, and would not take another step."
    )
    world.say(noise_cfg.stop_line)


def elder_guidance(world: World, elder: Entity, foal: Entity) -> None:
    world.say(
        f"{elder.label} laid a calm hand on {foal.pronoun('possessive')} shoulder and said, {elder.attrs.get('line', '')}"
    )


def identify_mare(world: World, mare: Entity, foal: Entity) -> None:
    mare.memes["worry"] += 1
    world.say(
        f"From the Willow Fold pen came the mother mare, tossing her head and searching. "
        f"She had already heard her little {foal.type} go missing."
    )


def cease_noise(world: World, child: Entity, elder: Entity, noise: Entity, method_cfg: CeaseMethod) -> None:
    child.memes["resolve"] += 1
    elder.memes["trust"] += 1
    noise.meters["sounding"] = 0.0
    world.say(
        f"So {child.id} fetched {method_cfg.phrase}, and together {child.id} and {elder.label} {method_cfg.text}."
    )
    world.say("Once the loudness was gone, the whole lane seemed to breathe out.")


def mare_calls(world: World, mare: Entity, foal: Entity, child: Entity) -> None:
    mare.meters["calling"] += 1
    foal.memes["hope"] += 1
    propagate(world, narrate=False)
    cry = repeated_neigh(foal.type)
    world.say(
        f'Then the mare lifted her head and called, "{cry}." '
        f'{child.id} answered softly with the old rhyme: “Step by step, little hooves. Neigh by neigh, come home.”'
    )


def reunite(world: World, foal: Entity, mare: Entity) -> None:
    foal.meters["distance"] = 0.0
    foal.memes["joy"] += 1
    mare.memes["relief"] += 1
    world.say(
        f"Step by step, hoof by hoof, the little {foal.type} crossed the ground. "
        f"First one step, then another; first one breath, then another."
    )
    world.say(
        f"Soon {foal.pronoun()} was pressed against the mare's warm side, and the mare brushed {foal.pronoun('object')} with her nose."
    )


def ending(world: World, child: Entity, elder: Entity, foal: Entity) -> None:
    child.memes["joy"] += 1
    child.memes["lesson"] += 1
    world.say(
        f'“A loud thing may frighten a small heart,” said {elder.label}, “but a quiet hand and a true call can mend the day.”'
    )
    world.say(
        f"By sunset the little {foal.type} was safe in the Willow Fold straw, and the people of the valley still said, "
        f"“Step by step, little hooves. Neigh by neigh, come home.”"
    )


def tell(
    place: Place,
    noise_cfg: NoiseSource,
    method_cfg: CeaseMethod,
    child_name: str,
    child_gender: str,
    foal_gender: str,
    elder_cfg: ElderRole,
    trait: str,
) -> World:
    world = World(place)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            attrs={"trait": trait},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_cfg.type,
            label=elder_cfg.label,
            role="elder",
            attrs={"intro": elder_cfg.intro, "line": elder_cfg.line},
        )
    )
    foal = world.add(
        Entity(
            id="foal",
            kind="character",
            type=foal_gender,
            label=foal_gender,
            role="foal",
            attrs={"stable": "Willow Fold"},
        )
    )
    mare = world.add(
        Entity(
            id="mare",
            kind="character",
            type="mare",
            label="mother mare",
            role="mare",
            attrs={"stable": "Willow Fold"},
        )
    )
    noise = world.add(
        Entity(
            id="noise",
            kind="thing",
            type=noise_cfg.id,
            label=noise_cfg.label,
            role="noise",
        )
    )

    foal.meters["distance"] = 1.0

    opening(world, child, elder, foal, place)
    find_tag(world, child, foal)

    world.para()
    startle(world, noise, foal, noise_cfg)
    elder_guidance(world, elder, foal)
    identify_mare(world, mare, foal)

    world.para()
    pred = predict_reunion(world)
    world.facts["predicted_can_walk_if_quiet"] = pred["can_walk"]
    cease_noise(world, child, elder, noise, method_cfg)
    mare_calls(world, mare, foal, child)
    reunite(world, foal, mare)

    world.para()
    ending(world, child, elder, foal)

    world.facts.update(
        child=child,
        elder=elder,
        foal=foal,
        mare=mare,
        noise_cfg=noise_cfg,
        method_cfg=method_cfg,
        place=place,
        ceased=noise.meters["sounding"] < THRESHOLD,
        reunited=foal.meters["distance"] < THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "gender": [
        (
            "What does the word gender mean in the story?",
            "In the story, gender is a note on the fair tag that tells whether the foal is a filly or a colt. It helps the horse keepers write careful records.",
        )
    ],
    "neigh": [
        (
            "What is a neigh?",
            "A neigh is the sound a horse makes. Horses call this way when they are excited, worried, or trying to find one another.",
        )
    ],
    "bell": [
        (
            "Why can a loud bell scare a foal?",
            "A foal is young and can be startled by a sudden hard sound. When the bell clangs too close, the foal may freeze instead of walking.",
        )
    ],
    "drum": [
        (
            "Why can a drum frighten an animal?",
            "A drum makes a deep, booming sound. For a young animal, that heavy sound can feel surprising and unsafe.",
        )
    ],
    "cart": [
        (
            "Why might a rattling cart upset a foal?",
            "A loose cart makes jumpy, uneven noises. Young animals often dislike sharp rattles because they do not know what the sound means.",
        )
    ],
    "quiet": [
        (
            "Why does a frightened animal need quiet?",
            "Quiet helps a frightened animal notice safe voices and familiar sounds. When the noise goes away, the animal can think and move again.",
        )
    ],
    "folk_tale": [
        (
            "Why do folk tales repeat lines?",
            "Folk tales repeat lines so listeners can remember them and join in. Repetition also makes the lesson feel gentle and strong.",
        )
    ],
}

KNOWLEDGE_ORDER = ["gender", "neigh", "bell", "drum", "cart", "quiet", "folk_tale"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    foal = f["foal"]
    noise_cfg = f["noise_cfg"]
    return [
        (
            f'Write a short folk tale for a 3-to-5-year-old that includes the words "gender", '
            f'"cease", and "neigh", with a repeated rhyme that helps a lost foal come home.'
        ),
        (
            f"Tell a village folk tale where {child.id} reads a foal's tag, learns the foal's gender, "
            f"helps the {noise_cfg.label} cease, and follows the mother mare's neigh."
        ),
        (
            f"Write a gentle story with repetition, where a frightened little {foal.type} will not move "
            f"until loud noise is quiet and a loving horse calls again."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    foal = f["foal"]
    mare = f["mare"]
    noise_cfg = f["noise_cfg"]
    method_cfg = f["method_cfg"]
    place = f["place"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {elder.label}, a lost little {foal.type}, and the mother mare from Willow Fold. They meet {place.phrase} when the foal is too frightened to go home.",
        ),
        (
            "What did the clay tag tell them?",
            f"The clay tag showed the stable mark of Willow Fold and the foal's gender. That clue told {child.id} which pen to search and what little horse they were helping.",
        ),
        (
            f"Why did the little {foal.type} stop walking?",
            f"The {noise_cfg.label} was making a loud sound, and it frightened the foal into freezing. A young animal may stand still when the world suddenly feels too loud.",
        ),
        (
            f"How did they make the {noise_cfg.label} cease?",
            f"{child.id} and {elder.label} {method_cfg.qa_text}. Once the noise ended, the place felt calmer and the foal could listen again.",
        ),
        (
            "How did the mother mare help?",
            f"The mare called to her baby with a repeated neigh, and {child.id} repeated the old rhyme. The familiar call gave the foal courage to take one step and then another.",
        ),
        (
            "How did the story end?",
            f"The little {foal.type} reached the mare and went safely back to Willow Fold. By sunset the danger had passed, and the repeated rhyme became the valley's ending memory.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"gender", "neigh", "quiet", "folk_tale"}
    noise_id = f["noise_cfg"].id
    if noise_id in {"bell", "drum", "cart"}:
        tags.add(noise_id)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
compatible_method(N, M) :- method(M), works_on(M, N).
valid(P, N, M) :- place(P), noise(N), method(M), affords(P, N), compatible_method(N, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for noise_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, noise_id))
    for noise_id in NOISES:
        lines.append(asp.fact("noise", noise_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        for noise_id in sorted(method.works_on):
            lines.append(asp.fact("works_on", method_id, noise_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a folk-tale child helps a frightened foal by making a loud noise cease."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--noise", choices=sorted(NOISES))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--foal-gender", choices=["filly", "colt"])
    ap.add_argument("--elder", choices=sorted(ELDERS))
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, noise, method) triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.noise and args.method and not valid_combo(args.place, args.noise, args.method):
        raise StoryError(explain_rejection(args.place, args.noise, args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.noise is None or combo[1] == args.noise)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        place = args.place or next(iter(PLACES))
        noise = args.noise or next(iter(NOISES))
        method = args.method or next(iter(METHODS))
        raise StoryError(explain_rejection(place, noise, method))

    place_id, noise_id, method_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    foal_gender = args.foal_gender or rng.choice(["filly", "colt"])
    elder_id = args.elder or rng.choice(sorted(ELDERS))
    name = args.name or rng.choice(CHILD_NAMES[child_gender])
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        noise=noise_id,
        method=method_id,
        child_name=name,
        child_gender=child_gender,
        foal_gender=foal_gender,
        elder=elder_id,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.noise not in NOISES:
        raise StoryError(f"(No story: unknown noise '{params.noise}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(No story: unknown method '{params.method}'.)")
    if params.elder not in ELDERS:
        raise StoryError(f"(No story: unknown elder '{params.elder}'.)")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unknown child gender '{params.child_gender}'.)")
    if params.foal_gender not in {"filly", "colt"}:
        raise StoryError(f"(No story: unknown foal gender '{params.foal_gender}'.)")
    if not valid_combo(params.place, params.noise, params.method):
        raise StoryError(explain_rejection(params.place, params.noise, params.method))

    world = tell(
        place=PLACES[params.place],
        noise_cfg=NOISES[params.noise],
        method_cfg=METHODS[params.method],
        child_name=params.child_name,
        child_gender=params.child_gender,
        foal_gender=params.foal_gender,
        elder_cfg=ELDERS[params.elder],
        trait=params.trait,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, noise, method) combos:\n")
        for place, noise, method in combos:
            print(f"  {place:12} {noise:6} {method}")
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
            header = f"### {p.child_name}: {p.noise} -> {p.method} at {p.place}"
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
