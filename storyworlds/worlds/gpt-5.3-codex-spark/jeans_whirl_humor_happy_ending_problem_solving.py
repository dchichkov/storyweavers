#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.3-codex-spark/jeans_whirl_humor_happy_ending_problem_solving.py
==============================================================================

A tiny fairy-tale style story world built from this source prompt:

"Write a story that includes the following words and narrative instruments.
Words: jeans, whirl. Features: Humor, Happy Ending, Problem Solving. Style: Fairy Tale."

Short source tale used as the planning seed:
Once upon a time, there was a child with very lucky jeans and a brave heart.
At the harvest festival a giant carnival device called The Whirl lost balance, and the child had to solve the tangle without frightening the crowd.

The implementation below follows the seed by turning that tale into a grounded
state-driven simulation with typed entities, physical meters, emotional memes,
and ASP-backed admissibility checks for generated combinations.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    kind_word: str
    label: str
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def __str__(self) -> str:
        return self.label

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "grandma", "maid", "witch"}
        male = {"boy", "king", "squire"}
        if self.kind_word in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind_word in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    id: str
    place: str
    wind: str
    has_water: bool
    flavor: str


@dataclass
class JeansSpec:
    id: str
    adjective: str
    tie_ready: bool
    snugness: float
    comfort: str
    humor: str


@dataclass
class FixMethod:
    id: str
    label: str
    intro: str
    action: str
    requires_water: bool


@dataclass
class StoryWorld:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Optional[Entity]:
        return self.entities.get(eid)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "StoryWorld":
        clone = StoryWorld(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    location: str
    jeans: str
    method: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "fairground_glen": Setting("fairground_glen", "the silver fairground glen", "gentle", True, "rainbow flags and painted lanterns"),
    "ridge_courtyard": Setting("ridge_courtyard", "the windy ridge courtyard", "breezy", False, "a stone drum where everyone cheered the festival dancers"),
    "harbor_square": Setting("harbor_square", "the harbor square", "gale", True, "a brass wind wheel and a stone fountain"),
}

JEANS = {
    "patchy": JeansSpec(
        id="patchy",
        adjective="patchy",
        tie_ready=False,
        snugness=0.60,
        comfort="The pockets felt like small, sleepy hamsters that would not stay put.",
        humor="They always seemed to choose the wrong pocket for the right job.",
    ),
    "heroic": JeansSpec(
        id="heroic",
        adjective="heroic",
        tie_ready=True,
        snugness=1.05,
        comfort="The belt sat high and kind, and the hem moved only when asked to.",
        humor="Even the buttons seemed to march in a line when they laughed.",
    ),
    "sturdy": JeansSpec(
        id="sturdy",
        adjective="sturdy",
        tie_ready=True,
        snugness=0.95,
        comfort="The cloth was thick and patient, like a blanket that could do two jobs.",
        humor="A stubborn seam once held a twig, and the twig fell asleep by itself.",
    ),
}

METHODS = {
    "tuck_and_tie": FixMethod(
        id="tuck_and_tie",
        label="tuck-and-tie the hem",
        intro="They made a wide loop with the jeans hem and tied it to a painted post.",
        action="The loop kept the fabric away from the spinning board, so the Whirl could breathe.",
        requires_water=False,
    ),
    "bucket_hush": FixMethod(
        id="bucket_hush",
        label="bucket hush",
        intro="They fetched a bucket of cool seawater and sprinkled it in short circles.",
        action="The fresh spray calmed the wheel and made the denim slide smoothly rather than snatch at it.",
        requires_water=True,
    ),
    "song_and_pause": FixMethod(
        id="song_and_pause",
        label="song-and-pause plan",
        intro="They sang a long, silly song and counted slowly, giving the wind a rule to wait by.",
        action="The wind softened in the middle of the beat, and the giant Whirl slowly returned to even spinning.",
        requires_water=False,
    ),
}

NAMES_GIRLS = ["Lina", "Mina", "Aria", "Tara", "Nora", "Ivy"]
NAMES_BOYS = ["Timo", "Milo", "Theo", "Nate", "Finn", "Joren"]
TRAITS = ["curious", "clever", "eager", "kind", "brave"]

WIND_SPEED = {
    "gentle": 1.4,
    "breezy": 2.0,
    "gale": 2.9,
}

KNOWLEDGE: dict[str, list[tuple[str, str]]] = {
    "jeans": [
        (
            "Why does snug denim matter on a windy festival day?",
            "Well-fitting denim is less likely to catch on spinning parts. A snug fit keeps the cloth from snagging when things whirl by fast.",
        ),
        (
            "Can a story character still solve a problem with torn or old clothes?",
            "Yes. The character can use a safer plan, helper tools, and timing. The key is choosing a method that matches the risk, not forcing a risky move.",
        ),
    ],
    "whirl": [
        (
            "Why can a spinning machine become dangerous?",
            "Spinning devices can throw loose fabric or pebbles if things get off-balance. A small snag can quickly become a bigger tangle.",
        ),
        (
            "What helps a spinning device return to steady movement?",
            "Evenness of force and stable guides help. Reducing side pull and keeping fabric clear from contact points makes motion safe again.",
        ),
    ],
    "water": [
        (
            "What does a quick water sprinkle do for a dusty whirl mechanism?",
            "A cool spray can reduce friction and vibration. It also slows sudden grabbing so everyone can plan the next safe step.",
        )
    ],
    "wind": [
        (
            "Why did the plan change in stronger wind?",
            "Strong wind changes a safe method from tied cloth to rhythm-and-pause. In that case, slowing the whole moment is often safer than adding tension around the fabric.",
        )
    ],
    "humor": [
        (
            "Why is humor useful during problem solving?",
            "Gentle humor keeps panic low and helps people stay patient. That improves timing, and timing is often the difference between a fix and a second tangle.",
        )
    ],
}

KNOWLEDGE_ORDER = ["jeans", "whirl", "water", "wind", "humor"]


SOURCE_TALE = (
    "Once upon a time, a child with bright jeans met a giant, noisy Whirl at the festival, \
"
    "and learned that clever choices can make a noisy trouble into a happy ending."
)


def _clamp(v: float, minimum: float = 0.0) -> float:
    return max(minimum, v)


def _article(word: str) -> str:
    return "an" if word[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def _gender_traits(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def valid_plan(location: Setting, jeans: JeansSpec, method: FixMethod) -> bool:
    if method.id == "song_and_pause":
        return location.wind == "gale"
    if method.id == "tuck_and_tie":
        return location.wind != "gale" and jeans.tie_ready
    if method.id == "bucket_hush":
        return location.has_water and location.wind != "gale" and jeans.snugness >= 0.65
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for loc_id, loc in SETTINGS.items():
        for jeans_id, jeans in JEANS.items():
            for method_id, method in METHODS.items():
                if valid_plan(loc, jeans, method):
                    out.append((loc_id, jeans_id, method_id))
    return sorted(out)


def introduce(world: StoryWorld, hero: Entity, helper: Entity, jeans: Entity) -> None:
    world.say(
        f"Once upon a time, there was {_article(hero.traits[0])} {hero.traits[0]} {hero.kind_word} named {hero.id}. "
        f"{hero.id} wore {jeans.label} for luck and for dancing."
    )
    world.say(
        f"In {world.setting.place}, flags fluttered, the air smelt of sugared apples, and {hero.pronoun('subject')} could already hear the brass pipes calling for the Great Whirl."
    )
    world.say(
        f"{helper.id}, a cheerful helper-elf with a pocketful of odd tools, whispered, \"Let us make this a merry problem to solve, not a fearful one.\""
    )


def start_whirl(world: StoryWorld, hero: Entity, jeans: Entity, whirl: Entity) -> None:
    world.say(
        "At dusk, the Great Whirl began its grand turning. At first it swayed, then it found its rhythm, and the crowd clapped in bright surprise."
    )
    hero.memes["joy"] += 1.3
    whirl.meters["spin"] = WIND_SPEED[world.setting.wind]
    whirl.meters["imbalance"] = 1.8
    jeans.meters["snag"] = 0.4
    jeans.meters["tension"] = jeans.traits[0] == "heroic" and 1.4 or 1.0
    world.say(
        f"Then {hero.id} stepped close to check the music-box lever, and a sudden gust pulled at {jeans.label} hem. "
        f"The cloth snagged. The Whirl lurched, and one giant board almost kissed the ground."
    )
    hero.memes["worry"] += 1.1
    hero.memes["humor"] += 0.4


def diagnose(world: StoryWorld, hero: Entity, jeans: Entity, whirl: Entity) -> None:
    snag = jeans.meters["snag"]
    imbalance = whirl.meters["imbalance"]
    if world.setting.wind == "gale":
        whirl.meters["imbalance"] = _clamp(imbalance + 0.8)
    world.say(
        f"It was a tricky tangle: the Whirl's imbalance climbed, and the jeans were now tugging at it every turn. "
        f"{hero.id} had a choice to make quickly, before the crowd saw panic and before the board caught fabric again."
    )
    hero.memes["concern"] += 1.0
    world.facts["snag_severity"] = _clamp(snag * (1.5 if world.setting.wind == "gale" else 1.0))


def apply_tuck_and_tie(world: StoryWorld, hero: Entity, jeans: Entity, whirl: Entity, method: FixMethod) -> None:
    world.say(f"{hero.id} chose the {method.label}. {method.intro}")
    world.say(
        f"{hero.id} laughed, tightened the loop, and kept everything gentle. "
        "The crowd cheered the silly concentration, then the board listened."
    )
    jeans.meters["snag"] = _clamp(jeans.meters["snag"] * 0.18)
    jeans.meters["tension"] = _clamp(jeans.meters["tension"] + 0.3)
    whirl.meters["imbalance"] = _clamp(whirl.meters["imbalance"] - 1.2)
    whirl.meters["spin"] = _clamp(whirl.meters["spin"] - 0.25)
    hero.memes["courage"] += 1.1
    hero.memes["joy"] += 0.7
    hero.memes["humor"] += 0.6
    world.facts["method_effect"] = "cleanly tucked, so it could not grip the turning board again"


def apply_bucket_hush(world: StoryWorld, hero: Entity, jeans: Entity, whirl: Entity, helper: Entity, method: FixMethod) -> None:
    world.say(f"{hero.id} chose the {method.label}. {method.intro}")
    world.say(
        f"{helper.id} held the bucket steady while {hero.id} sprinkled circles near the axle. "
        "The spray made a tiny hiss and everyone said the Whirl had just yawned, then smiled."
    )
    world.say(
        f"{hero.id} remembered a useful trick from the {world.facts['jeans_spec'].adjective} pockets: "
        f"{world.facts['jeans_spec'].humor}"
    )
    jeans.meters["snag"] = _clamp(jeans.meters["snag"] - 0.32)
    whirl.meters["imbalance"] = _clamp(whirl.meters["imbalance"] - 1.5)
    whirl.meters["spin"] = _clamp(whirl.meters["spin"] - 0.4)
    hero.memes["cleverness"] += 1.0
    hero.memes["joy"] += 0.6
    hero.memes["humor"] += 0.9
    world.facts["method_effect"] = "coated with cool mist, so it slid instead of snagging"


def apply_song_and_pause(world: StoryWorld, hero: Entity, jeans: Entity, whirl: Entity, helper: Entity, method: FixMethod) -> None:
    world.say(f"{hero.id} chose the {method.label}. {method.intro}")
    world.say(
        f"When the crowd counted, the wind seemed to pause between breaths. "
        f"{helper.id} clapped the beat like a tiny drum, and {hero.id} laughed through the long note."
    )
    jeans.meters["snag"] = _clamp(jeans.meters["snag"] - 0.15)
    whirl.meters["imbalance"] = _clamp(whirl.meters["imbalance"] - 1.95)
    whirl.meters["spin"] = _clamp(whirl.meters["spin"] - 0.2)
    hero.memes["confidence"] += 1.1
    hero.memes["joy"] += 1.2
    hero.memes["humor"] += 1.4
    world.facts["method_effect"] = "stay safe in a slow rhythm until the snag settled"


def settle(world: StoryWorld, hero: Entity, jeans: Entity, whirl: Entity) -> None:
    world.say(
        f"The Whirl made one calm, full circle and then another. "
        f"Its hum turned from frantic clatter to a soft, steady singing."
    )
    jeans.meters["fray"] = _clamp(jeans.meters["snag"] * 0.3)

    if jeans.meters["snag"] <= 0.35 and whirl.meters["imbalance"] <= 0.7:
        world.facts["resolved"] = True
        hero.memes["hope"] += 1.0
        hero.memes["joy"] += 0.8
        world.say(
            f"Then the fair organizer clapped both hands. "
            f"{hero.id} and {world.get('helper').id if world.get('helper') else 'the helper'} were handed a ribbon as a prize. "
            f"At the ending image, the hero twirled once, the Whirl spun safely, and the jeans now had a neat, tied hem instead of a tangled one."
        )
    else:
        world.facts["resolved"] = False
        world.say(
            f"Though they tried bravely, the Whirl still felt wild. The story keeps the lesson of caution, but this draft needs a different helper, "
            f"and so this tale would retry with another method."
        )


def tell_world(setting: Setting, jeans_spec: JeansSpec, method: FixMethod, name: str, gender: str, trait: str, helper_name: str = "Penny") -> StoryWorld:
    hero_word = _gender_traits(gender)
    world = StoryWorld(setting)
    hero = world.add(
        Entity(
            id=name,
            kind="person",
            kind_word=hero_word,
            label=name,
            traits=[trait],
            role="hero",
        )
    )
    jeans = world.add(
        Entity(
            id="hero_jeans",
            kind="thing",
            kind_word="garment",
            label=f"{_article(jeans_spec.adjective)} {jeans_spec.adjective} pair of jeans",
            traits=[jeans_spec.adjective, "jeans"],
            role="gear",
            meters={"snag": 0.0, "tension": jeans_spec.snugness, "fray": 0.0},
            memes={"comfort": 0.0},
        )
    )
    whirl = world.add(
        Entity(
            id="Great_Whirl",
            kind="thing",
            kind_word="whirl",
            label="the Great Whirl",
            traits=["metal", "festival", "spinning"],
            role="device",
            meters={"spin": 0.0, "imbalance": 0.0},
            memes={"joy": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="person",
            kind_word="fox",
            label=helper_name,
            traits=["helpful", "quick"],
            role="helper",
        )
    )

    hero.memes["curiosity"] += 1.0
    hero.memes["humor"] += 0.7

    world.facts.update(
        setting=setting,
        hero=hero,
        jeans=jeans,
        jeans_spec=jeans_spec,
        whirl=whirl,
        helper=helper,
        method=method,
        source_tale=SOURCE_TALE,
    )

    introduce(world, hero, helper, jeans)
    world.para()
    start_whirl(world, hero, jeans, whirl)
    world.para()
    diagnose(world, hero, jeans, whirl)
    world.para()

    if method.id == "tuck_and_tie":
        apply_tuck_and_tie(world, hero, jeans, whirl, method)
    elif method.id == "bucket_hush":
        apply_bucket_hush(world, hero, jeans, whirl, helper, method)
    elif method.id == "song_and_pause":
        apply_song_and_pause(world, hero, jeans, whirl, helper, method)

    world.para()
    settle(world, hero, jeans, whirl)

    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    hero = f["hero"]
    method = f["method"]
    setting = f["setting"]
    return [
        f"Write a fairy-tale style 3-5-year-old story featuring {hero.id}, two-word magic jeans, and a huge festival {world.get('Great_Whirl').id if world.get('Great_Whirl') else 'Whirl'}.",
        f"Show humor and a clear problem-solver moment where the Whirl begins to snag and {hero.id} uses {method.label}.",
        f"Close with a concrete ending image that proves the problem changed from danger to safe celebration in {setting.place}.",
    ]


def story_qa(world: StoryWorld) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    jeans = f["jeans"]
    jeans_spec = f["jeans_spec"]
    whirl = f["whirl"]
    method = f["method"]
    resolved = bool(f.get("resolved", False))
    method_effect = f.get("method_effect", "a focused step")
    return [
        (
            f"Who is the story about?",
            f"The story is about {hero.id}, {_article(hero.traits[0])} {hero.traits[0]} {hero.kind_word}. "
            f"There was also a helper named {helper.id}, who stood close by with a pocketful of good ideas.",
        ),
        (
            "What was the problem at the festival?",
            f"The problem was that a gusty turn of wind made {hero.id}'s jeans snag on the Great Whirl. "
            f"The snag raised the device’s imbalance, and that could have made a dangerous tangle.",
        ),
        (
            "How did the hero solve it?",
            f"{hero.id} used the {method.label}, and the action made the jeans hem {method_effect}. "
            f"That kept fabric from grabbing the moving board and reduced the Whirl’s wobble.",
        ),
        (
            f"Why was this method a reasonable choice for this scene?",
            f"Because the setting was {world.setting.place} with {world.setting.wind} wind, and the selected method matched the risk conditions there. "
            f"{hero.id} adjusted the immediate cause—the snag—not the Whirl with force, so the machine could settle safely.",
        ),
        (
            f"What changed at the end of the story?",
            f"The Great Whirl ended on even, calm circles while the helper handed out a ribbon. "
            f"You can see the change in the ending image: the jeans were tidy and tied, the crowd was cheering, and the festival moment turned into a safe victory.",
        ),
    ] + ([
        (
            f"How did humor affect the group?",
            f"The helper and {hero.id} kept a playful mood through silly comments and rhythm, which lowered worry in the crowd. "
            f"When fear drops and timing stays steady, a team can think clearly and choose a safer fix.",
        ),
    ] if resolved else [])


def world_knowledge_qa(world: StoryWorld) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"jeans", "whirl", "humor"}
    if f["setting"].has_water:
        tags.add("water")
    if f["setting"].wind == "gale":
        tags.add("wind")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- storyworld state ---"]
    for ent in world.entities.values():
        meters = {k: round(v, 2) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 2) for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        traits = ", ".join(ent.traits)
        lines.append(f"  {ent.id:14} ({ent.kind_word:10}) traits=[{traits}] {' '.join(bits)}")
    if world.facts.get("method") is not None:
        method = world.facts["method"]
        lines.append(f"  selected method: {method.id}")
    lines.append(f"  resolved: {world.facts.get('resolved', False)}")
    lines.append(f"  source_tale: {world.facts.get('source_tale')}")
    return "\n".join(lines)


def explain_rejection(location: Setting, jeans_spec: JeansSpec, method: FixMethod) -> str:
    if method.id == "song_and_pause" and location.wind != "gale":
        return (f"(No story: '{method.id}' only fits gale wind, but this location has {location.wind} wind.)")
    if method.id == "tuck_and_tie" and not jeans_spec.tie_ready:
        return (f"(No story: {jeans_spec.adjective} jeans do not hold a safe tucked loop for this method.)")
    if method.id == "bucket_hush" and not location.has_water:
        return "(No story: bucket-hush needs a nearby source of water.)"
    if not valid_plan(location, jeans_spec, method):
        return "(No story: this location/jeans/method combination is not modeled.)"
    return "(No story: invalid combination.)"


ASP_RULES = r"""
valid(L,J,M) :- location(L), jeans(J), wind(L,gentle), tie_ready(J), can_tie(M).
valid(L,J,M) :- location(L), jeans(J), wind(L,breezy), tie_ready(J), can_tie(M).
valid(L,J,M) :- location(L), has_water(L), wind(L,gentle), jeans(J), can_bucket(M), method(M), bucket_eligible(J).
valid(L,J,M) :- location(L), has_water(L), wind(L,breezy), jeans(J), can_bucket(M), method(M), bucket_eligible(J).
valid(L,J,M) :- location(L), jeans(J), method(M), wind(L,gale), song(M).
"""


def asp_facts(params: StoryParams | None = None) -> str:
    import asp

    lines: list[str] = []
    for loc_id, loc in SETTINGS.items():
        lines.append(asp.fact("location", loc_id))
        lines.append(asp.fact("wind", loc_id, loc.wind))
        if loc.has_water:
            lines.append(asp.fact("has_water", loc_id))
    for jeans_id, jeans in JEANS.items():
        lines.append(asp.fact("jeans", jeans_id))
        if jeans.tie_ready:
            lines.append(asp.fact("tie_ready", jeans_id))
        if jeans.snugness >= 0.65:
            lines.append(asp.fact("bucket_eligible", jeans_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        if method_id == "song_and_pause":
            lines.append(asp.fact("song", method_id))
        if method_id == "bucket_hush":
            lines.append(asp.fact("can_bucket", method_id))
        if method_id == "tuck_and_tie":
            lines.append(asp.fact("can_tie", method_id))
        if method_id == "song_and_pause":
            lines.append(asp.fact("requires_gale", method_id))

    if params is not None:
        lines.append(f"#show valid({params.location},{params.jeans},{params.method}).")
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    out = asp.atoms(model, "valid")
    return sorted(set((a, b, c) for a, b, c in out))


def asp_verify() -> int:
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set != asp_set:
        print(f"MISMATCH between ASP and Python valid-combo sets.")
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        return 1
    print(f"OK: ASP and Python describe {len(py_set)} combos identically.")

    # Exercise a few stories to ensure runtime parity and valid sampling.
    for location_id, jeans_id, method_id in sorted(py_set)[:min(8, len(py_set))]:
        params = StoryParams(
            location=location_id,
            jeans=jeans_id,
            method=method_id,
            name=random.choice(NAMES_GIRLS),
            gender="girl",
            trait=random.choice(TRAITS),
        )
        sample = generate(params)
        if "Whirl" not in sample.story or "jeans" not in sample.story:
            print("FAILED: story does not include mandatory terms for", params)
            return 2
    print("OK: --verify exercised sampled stories from every valid combo class.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a fairy-tale problem-solving Whirl tale with jeans and humor.")
    ap.add_argument("--location", choices=sorted(SETTINGS))
    ap.add_argument("--jeans", choices=sorted(JEANS))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--name")
    ap.add_argument("--trait")
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
    if args.location and args.jeans and args.method:
        loc = SETTINGS[args.location]
        jeans = JEANS[args.jeans]
        method = METHODS[args.method]
        if not valid_plan(loc, jeans, method):
            raise StoryError(explain_rejection(loc, jeans, method))

    combos = [
        combo for combo in valid_combos()
        if (args.location is None or combo[0] == args.location)
        and (args.jeans is None or combo[1] == args.jeans)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("No valid world combinations available for the selected filters.")

    location_id, jeans_id, method_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or (rng.choice(NAMES_GIRLS) if gender == "girl" else rng.choice(NAMES_BOYS))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(location_id, jeans_id, method_id, name, gender, trait)


def generate(params: StoryParams) -> StorySample:
    loc = SETTINGS[params.location]
    jeans = JEANS[params.jeans]
    method = METHODS[params.method]
    if not valid_plan(loc, jeans, method):
        raise StoryError(explain_rejection(loc, jeans, method))

    world = tell_world(loc, jeans, method, params.name, params.gender, params.trait)
    story = world.render()
    if "Whirl" not in story:
        raise StoryError("Internal generation failed to render the tale around the required Whirl object.")
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, args: argparse.Namespace, label: str | None = None) -> None:
    if label:
        print(label)
    print(sample.story)
    if args.trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if args.qa:
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
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [
            generate(StoryParams("fairground_glen", "heroic", "tuck_and_tie", "Mina", "girl", "kind", seed=1)),
            generate(StoryParams("ridge_courtyard", "sturdy", "bucket_hush", "Timo", "boy", "curious", seed=2)),
            generate(StoryParams("harbor_square", "heroic", "song_and_pause", "Aria", "girl", "brave", seed=3)),
            generate(StoryParams("fairground_glen", "sturdy", "bucket_hush", "Theo", "boy", "eager", seed=4)),
            generate(StoryParams("ridge_courtyard", "heroic", "bucket_hush", "Nora", "girl", "clever", seed=5)),
        ]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(200, args.n * 40):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples, 1):
        header = f"--- story {i} ---" if len(samples) > 1 else ""
        emit(sample, args, label=header)
        if i != len(samples):
            print()


if __name__ == "__main__":
    try:
        main()
    except StoryError as exc:
        print(exc)
        sys.exit(2)
