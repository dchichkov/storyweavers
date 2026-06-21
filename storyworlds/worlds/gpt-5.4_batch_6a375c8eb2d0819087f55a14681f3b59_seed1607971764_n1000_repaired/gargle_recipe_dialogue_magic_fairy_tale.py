#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gargle_recipe_dialogue_magic_fairy_tale.py
=====================================================================

A standalone story world for a tiny fairy-tale domain: a young fairy must speak
or sing a little bit of magic, but a croaky voice gets in the way. A helper
finds a recipe for a sparkling gargle, and the world decides whether the remedy
fully restores the voice or whether the magic must be finished together.

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- eager import of shared result containers from storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- typed entities with physical meters and emotional memes
- a Python reasonableness gate plus an inline ASP twin
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify,
  and --show-asp
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy_girl", "woman", "grandmother"}
        male = {"boy", "fairy_boy", "man", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    water: str
    ingredients: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Problem:
    id: str
    cause: str
    symptom: str
    severity: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Recipe:
    id: str
    label: str
    ingredient: str
    bowl_text: str
    chant: str
    strength: int
    cures: set[str] = field(default_factory=set)
    sense: int = 3
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Event:
    id: str
    need: str
    opening_line: str
    solo_success: str
    shared_success: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class HelperCfg:
    id: str
    name: str
    type: str
    title: str
    entrance: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "gargled": False,
            "supporting": False,
            "event_pending": True,
            "event_done": False,
            "outcome": "",
        }

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_croaky(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["croak"] >= THRESHOLD and ("croaky",) not in world.fired:
        world.fired.add(("croaky",))
        hero.meters["voice_dim"] += 1
        hero.memes["worry"] += 1
        out.append("__croaky__")
    return out


def _r_gargle_restore(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    recipe: Recipe = world.facts["recipe_cfg"]
    problem: Problem = world.facts["problem_cfg"]
    if not world.facts["gargled"]:
        return out
    if ("restore", recipe.id, problem.id) in world.fired:
        return out
    world.fired.add(("restore", recipe.id, problem.id))
    if problem.id in recipe.cures:
        hero.meters["croak"] = max(0.0, hero.meters["croak"] - recipe.strength)
        hero.memes["hope"] += 1
        hero.meters["magic_warmth"] += 1
        if hero.meters["croak"] < THRESHOLD:
            hero.meters["voice_clear"] = 1.0
        else:
            hero.meters["voice_clear"] = 0.5
        out.append("__restore__")
    return out


def _r_event_result(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if not world.facts["event_pending"] or world.facts["event_done"]:
        return out
    if hero.meters["voice_clear"] >= THRESHOLD and ("solo_done",) not in world.fired:
        world.fired.add(("solo_done",))
        world.facts["event_done"] = True
        world.facts["outcome"] = "solo"
        hero.memes["relief"] += 1
        hero.memes["joy"] += 1
        out.append("__solo__")
    elif world.facts["supporting"] and hero.meters["croak"] >= THRESHOLD and ("shared_done",) not in world.fired:
        world.fired.add(("shared_done",))
        world.facts["event_done"] = True
        world.facts["outcome"] = "shared"
        hero.memes["relief"] += 1
        hero.memes["gratitude"] += 1
        out.append("__shared__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="croaky", tag="physical", apply=_r_croaky),
    Rule(name="gargle_restore", tag="magic", apply=_r_gargle_restore),
    Rule(name="event_result", tag="social", apply=_r_event_result),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def recipe_possible(setting: Setting, recipe: Recipe) -> bool:
    return recipe.ingredient in setting.ingredients


def recipe_helps(problem: Problem, recipe: Recipe) -> bool:
    return problem.id in recipe.cures


def sensible_recipes() -> list[Recipe]:
    return [r for r in RECIPES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for problem_id, problem in PROBLEMS.items():
            for recipe_id, recipe in RECIPES.items():
                if recipe_possible(setting, recipe) and recipe_helps(problem, recipe) and recipe.sense >= SENSE_MIN:
                    combos.append((setting_id, problem_id, recipe_id))
    return combos


def explain_setting_recipe(setting: Setting, recipe: Recipe) -> str:
    return (
        f"(No story: {setting.place} does not have {recipe.ingredient}, so the "
        f"{recipe.label} recipe cannot be mixed there. Pick a setting whose pantry "
        f"or garden actually holds that ingredient.)"
    )


def explain_recipe_problem(problem: Problem, recipe: Recipe) -> str:
    return (
        f"(No story: the {recipe.label} recipe does not soothe {problem.symptom}. "
        f"The gargle has to match the trouble, or the fairy-tale fix would feel false.)"
    )


def explain_recipe_sense(recipe: Recipe) -> str:
    return (
        f"(Refusing recipe '{recipe.id}': it scores too low on common sense "
        f"(sense={recipe.sense} < {SENSE_MIN}). This world prefers recipes that "
        f"a careful helper would honestly choose.)"
    )


def outcome_of(params: "StoryParams") -> str:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.recipe not in RECIPES:
        raise StoryError("(Unknown setting, problem, or recipe in params.)")
    problem = PROBLEMS[params.problem]
    recipe = RECIPES[params.recipe]
    return "solo" if recipe.strength >= problem.severity else "shared"


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, event: Event) -> None:
    world.say(f"Once, in {world.setting.place}, {hero.id} had a shining duty. {event.opening_line}")


def opening_world(world: World) -> None:
    world.say(world.setting.opening)


def trouble_begins(world: World, hero: Entity, problem: Problem, event: Event) -> None:
    hero.meters["croak"] = float(problem.severity)
    hero.meters["sparkle"] = 1.0
    world.say(problem.cause)
    world.say(
        f"When {hero.id} tried to practice for {event.need}, {hero.pronoun('possessive')} "
        f"voice came out {problem.symptom} instead of bright and clear."
    )
    propagate(world, narrate=False)


def worry_line(world: World, hero: Entity, event: Event) -> None:
    world.say(
        f'"Oh dear," said {hero.id}. "How can I manage {event.need} if my words sound like that?"'
    )


def helper_arrives(world: World, helper: Entity, helper_cfg: HelperCfg) -> None:
    helper.memes["care"] += 1
    world.say(helper_cfg.entrance)


def suggest_recipe(world: World, helper: Entity, hero: Entity, recipe: Recipe) -> None:
    hero.memes["hope"] += 1
    world.say(
        f'"Do not fret," said {helper.id}. "The old recipe book keeps a {recipe.label} recipe for voices in a tangle."'
    )
    world.say(
        f'{helper.id} opened the silver-edged book and traced a line with one finger. '
        f'"{recipe.bowl_text}," {helper.pronoun()} read.'
    )


def mix_gargle(world: World, hero: Entity, helper: Entity, recipe: Recipe) -> None:
    world.say(
        f'Together they stirred {recipe.ingredient} into {world.setting.water} until the bowl shone softly. '
        f'"{recipe.chant}," whispered {hero.id}.'
    )


def gargle_spell(world: World, hero: Entity, recipe: Recipe) -> None:
    world.facts["gargled"] = True
    world.say(
        f"{hero.id} took a careful sip, tipped back {hero.pronoun('possessive')} head, "
        f"and began to gargle. The little sound bubbled like moonlit water, and pale sparks "
        f"danced around the rim of the bowl."
    )
    propagate(world, narrate=False)
    if hero.meters["voice_clear"] >= THRESHOLD:
        world.say(
            f"When the magic settled, {hero.id}'s throat felt warm and easy, as if a tiny bell had been polished inside."
        )
    else:
        world.say(
            f"The gargle softened the roughness, but a small croak still clung to the end of each word."
        )


def face_event(world: World, hero: Entity, helper: Entity, event: Event) -> None:
    world.para()
    world.say(f"Soon it was time for {event.need}.")
    if hero.meters["voice_clear"] >= THRESHOLD:
        propagate(world, narrate=False)
        world.say(event.solo_success.replace("{hero}", hero.id))
    else:
        world.facts["supporting"] = True
        helper.memes["care"] += 1
        world.say(
            f'"Stand beside me," said {helper.id}. "If your voice is still tender, mine will hold the spell with yours."'
        )
        propagate(world, narrate=False)
        world.say(event.shared_success.replace("{hero}", hero.id).replace("{helper}", helper.id))


def ending_image(world: World, hero: Entity, helper: Entity) -> None:
    if world.facts["outcome"] == "solo":
        world.say(
            f"After that, {hero.id} tucked the recipe into memory. Whenever a hard moment came, {hero.pronoun()} remembered that patient magic could be stronger than a hurried wish."
        )
    else:
        world.say(
            f"After that, {hero.id} kept the recipe book close and never forgot the kindness of shared magic. A voice may wobble for a while, but help can still carry the song to the end."
        )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    problem: Problem,
    recipe: Recipe,
    event: Event,
    helper_cfg: HelperCfg,
    hero_name: str = "Lina",
    hero_type: str = "fairy_girl",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_cfg.type,
            label=helper_cfg.name,
            role="helper",
            attrs={"title": helper_cfg.title},
        )
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        setting_cfg=setting,
        problem_cfg=problem,
        recipe_cfg=recipe,
        event_cfg=event,
        helper_cfg=helper_cfg,
        hero_name=hero_name,
    )

    introduce(world, hero, event)
    opening_world(world)

    world.para()
    trouble_begins(world, hero, problem, event)
    worry_line(world, hero, event)

    world.para()
    helper_arrives(world, helper, helper_cfg)
    suggest_recipe(world, helper, hero, recipe)
    mix_gargle(world, hero, helper, recipe)
    gargle_spell(world, hero, recipe)

    face_event(world, hero, helper, event)

    world.para()
    ending_image(world, hero, helper)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "dew_hollow": Setting(
        id="dew_hollow",
        place="Dew Hollow, where foxgloves leaned over a clear spring",
        opening="Every fern in the hollow seemed to listen when the fairies practiced their tiny spells at dusk.",
        water="clear spring water",
        ingredients={"moonmint", "honeyblossom"},
        tags={"spring", "garden"},
    ),
    "amber_tower": Setting(
        id="amber_tower",
        place="Amber Tower, above the clouds and beside a copper kettle room",
        opening="The windows glowed gold there, and even the spoons rang softly when evening magic was near.",
        water="warm cloud-water",
        ingredients={"silver_salt", "moonmint"},
        tags={"tower", "kitchen"},
    ),
    "thistledown_cottage": Setting(
        id="thistledown_cottage",
        place="Thistledown Cottage at the edge of the whispering marsh",
        opening="Bundles of herbs hung from the rafters, and an old lamp painted star-shapes on the floorboards.",
        water="dew from a blue glass jug",
        ingredients={"dew_pearl", "honeyblossom"},
        tags={"cottage", "herbs"},
    ),
}

PROBLEMS = {
    "frost_nibble": Problem(
        id="frost_nibble",
        cause="That afternoon, {hero} had nibbled a frost-plum too quickly, and the chilly bite left the back of the throat prickly."
              .replace("{hero}", "the young fairy"),
        symptom="scratchy and thin",
        severity=1,
        tags={"cold_throat", "scratchy"},
    ),
    "chimney_whiff": Problem(
        id="chimney_whiff",
        cause="A mischievous chimney puff had curled across the path and filled the air with smoky dust before anyone could clap it away.",
        symptom="rough and sooty",
        severity=2,
        tags={"smoke", "rough_voice"},
    ),
    "toadlet_hex": Problem(
        id="toadlet_hex",
        cause="At the marsh gate, a sleepy toadlet had sneezed a tiny hex, and ever since then each brave word wanted to hop into a croak.",
        symptom="croaky and bouncy",
        severity=3,
        tags={"curse", "croak"},
    ),
}

RECIPES = {
    "moonmint_gargle": Recipe(
        id="moonmint_gargle",
        label="moonmint gargle",
        ingredient="moonmint",
        bowl_text="Steep moonmint in warm water, blow across the bowl three times, and let the silver smell rise",
        chant="Mint be mild and moon be bright, smooth this little voice tonight",
        strength=2,
        cures={"frost_nibble", "chimney_whiff"},
        sense=3,
        tags={"gargle", "mint", "magic_recipe"},
    ),
    "honeyblossom_gargle": Recipe(
        id="honeyblossom_gargle",
        label="honeyblossom gargle",
        ingredient="honeyblossom",
        bowl_text="Stir honeyblossom petals into clear water until the bowl catches a sleepy golden gleam",
        chant="Petal sweet and petal slow, help the tender singing grow",
        strength=1,
        cures={"frost_nibble", "toadlet_hex"},
        sense=3,
        tags={"gargle", "flower", "magic_recipe"},
    ),
    "pearl_rinse": Recipe(
        id="pearl_rinse",
        label="dew-pearl gargle",
        ingredient="dew_pearl",
        bowl_text="Drop one dew pearl into the water and wait for seven rings to shimmer across the top",
        chant="Pearl of dawn and pearl of rain, untie the croak and clear the strain",
        strength=3,
        cures={"toadlet_hex"},
        sense=3,
        tags={"gargle", "pearl", "magic_recipe"},
    ),
    "silver_salt_gargle": Recipe(
        id="silver_salt_gargle",
        label="silver-salt gargle",
        ingredient="silver_salt",
        bowl_text="Pinch in silver salt and swirl until the water flashes like a tiny star",
        chant="Salt of shine and kitchen light, chase the soot from song tonight",
        strength=2,
        cures={"chimney_whiff"},
        sense=3,
        tags={"gargle", "salt", "magic_recipe"},
    ),
    "sugar_spark_sip": Recipe(
        id="sugar_spark_sip",
        label="sugar-spark sip",
        ingredient="sugar_spark",
        bowl_text="Scatter sugar sparks and hope for the best",
        chant="Sweet and quick, do the trick",
        strength=0,
        cures=set(),
        sense=1,
        tags={"sweet"},
    ),
}

EVENTS = {
    "moon_gate": Event(
        id="moon_gate",
        need="the moon-gate opening song",
        opening_line="At moonrise, she was meant to sing the silver gate awake so the night moths could flutter through.",
        solo_success="{hero} lifted a clear voice, and the moon-gate bloomed open like a lily made of light.",
        shared_success="{hero} began the song and {helper} braided a second voice through it, so the moon-gate opened with a gentle shining sigh.",
        tags={"song", "moon"},
    ),
    "lantern_blessing": Event(
        id="lantern_blessing",
        need="the lantern blessing",
        opening_line="Before the village lanterns floated into the evening sky, she had to whisper the blessing that taught them where to shine.",
        solo_success="{hero} spoke the blessing in one smooth ribbon of sound, and every lantern bobbed upward, warm and brave.",
        shared_success="{hero} whispered the first part and {helper} carried the rest, and soon the lanterns rose together like a flock of golden birds.",
        tags={"lantern", "spell"},
    ),
    "brook_lullaby": Event(
        id="brook_lullaby",
        need="the brook lullaby",
        opening_line="At twilight, she was to sing to the brook so the water would settle into a soft bedtime murmur for the sleeping reeds.",
        solo_success="{hero} sang, and the brook slowed into a shining hush, as if the whole waterway had tucked itself in.",
        shared_success="{hero} sang what she could and {helper} hummed beside her, and together they settled the brook into a soft silver murmur.",
        tags={"brook", "song"},
    ),
}

HELPERS = {
    "fern_grandma": HelperCfg(
        id="fern_grandma",
        name="Grandma Fern",
        type="grandmother",
        title="grandmother",
        entrance="Just then Grandma Fern came in with her basket of evening herbs and a smile that knew many old remedies.",
        tags={"elder", "kind"},
    ),
    "kettle_sprite": HelperCfg(
        id="kettle_sprite",
        name="Pip the Kettle Sprite",
        type="sprite",
        title="sprite",
        entrance="From the warm shelf above the stove hopped Pip the Kettle Sprite, shaking steam from a bright copper cap.",
        tags={"sprite", "kitchen"},
    ),
    "reed_wizard": HelperCfg(
        id="reed_wizard",
        name="Reed the Marsh Wizard",
        type="wizard",
        title="wizard",
        entrance="A tap of willow wood sounded at the door, and in stepped Reed the Marsh Wizard with his mossy cloak smelling of rain.",
        tags={"wizard", "guide"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tansy", "Wren", "Elsie", "Poppy", "Nia", "Faye"]
BOY_NAMES = ["Rowan", "Finn", "Tobin", "Alder", "Jory", "Milo", "Ash", "Ren"]
HERO_TYPES = ["fairy_girl", "fairy_boy"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str = ""
    problem: str = ""
    recipe: str = ""
    event: str = ""
    helper: str = ""
    hero_name: str = ""
    hero_type: str = ""
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "gargle": [
        (
            "What does it mean to gargle?",
            "To gargle means to hold liquid in the back of your mouth and throat and make it bubble with your breath. People do it to soothe a sore throat or help clean their mouth."
        )
    ],
    "magic_recipe": [
        (
            "What is a recipe?",
            "A recipe is a set of steps that tells you how to make something. In a fairy tale, a recipe can guide a magical remedy just as it guides ordinary cooking."
        )
    ],
    "mint": [
        (
            "Why might mint help a throat feel better?",
            "Mint can feel cool and soothing. That gentle feeling can make a scratchy throat seem calmer."
        )
    ],
    "flower": [
        (
            "Why are flowers often used in fairy-tale remedies?",
            "Fairy tales like flowers because they are gentle, fragrant, and easy to imagine as holding a little magic. Their sweetness helps a remedy feel caring instead of harsh."
        )
    ],
    "pearl": [
        (
            "Why is a pearl magical in fairy tales?",
            "A pearl feels special because it is small, bright, and rare. Fairy tales often treat pearls as things that can hold calm light or old magic."
        )
    ],
    "salt": [
        (
            "What can salt do in a simple remedy?",
            "Salt can help rinse and clean. In stories, sparkling salt is often imagined as something that chases away soot or other clingy trouble."
        )
    ],
    "song": [
        (
            "Why do songs matter in fairy tales?",
            "Songs can carry feelings, promises, and magic all at once. A song makes a spell feel alive and memorable."
        )
    ],
    "spell": [
        (
            "What is a spell in a fairy tale?",
            "A spell is a special set of words, sounds, or actions that brings about magic. Fairy tales often show that the spell works best when spoken carefully."
        )
    ],
    "elder": [
        (
            "Why do fairy tales often have a wise elder helper?",
            "A wise elder has seen more seasons and knows old remedies or stories. That makes the helper a calm guide when the young hero feels worried."
        )
    ],
    "kind": [
        (
            "Why does kindness help in a hard moment?",
            "Kindness can make fear feel smaller. When someone helps gently, it becomes easier to be brave and try again."
        )
    ],
}
KNOWLEDGE_ORDER = ["gargle", "magic_recipe", "mint", "flower", "pearl", "salt", "song", "spell", "elder", "kind"]


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    event: Event = world.facts["event_cfg"]
    problem: Problem = world.facts["problem_cfg"]
    recipe: Recipe = world.facts["recipe_cfg"]
    helper: HelperCfg = world.facts["helper_cfg"]
    outcome = world.facts["outcome"] or ("solo" if recipe.strength >= problem.severity else "shared")
    if outcome == "solo":
        return [
            'Write a short fairy tale for a 3-to-5-year-old that includes the words "gargle" and "recipe".',
            f"Tell a fairy tale where a young fairy's voice turns {problem.symptom}, {helper.name} finds a magical {recipe.label} recipe, and the child can finish {event.need} alone in the end.",
            f"Write a gentle story with dialogue and magic in which {hero.label} learns that patient care can restore a voice before an important enchanted duty."
        ]
    return [
        'Write a short fairy tale for a 3-to-5-year-old that includes the words "gargle" and "recipe".',
        f"Tell a fairy tale where a young fairy tries a magical {recipe.label} recipe, but the voice is still a little weak, so {helper.name} helps finish {event.need}.",
        f"Write a child-friendly magical story with dialogue showing that when one voice wobbles, help and kindness can still carry the spell to its ending."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    problem: Problem = world.facts["problem_cfg"]
    recipe: Recipe = world.facts["recipe_cfg"]
    event: Event = world.facts["event_cfg"]
    setting: Setting = world.facts["setting_cfg"]
    outcome = world.facts["outcome"] or ("solo" if recipe.strength >= problem.severity else "shared")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a young fairy, and {helper.label}, who comes to help. They are in {setting.place}, where magic is part of ordinary evening life."
        ),
        (
            f"Why was {hero.label} worried?",
            f"{hero.label} was worried because {hero.pronoun('possessive')} voice had turned {problem.symptom} before {event.need}. That mattered because the magic depended on speaking or singing clearly."
        ),
        (
            f"What recipe did {helper.label} choose?",
            f"{helper.label} chose the {recipe.label} recipe from the old book. The helper picked it because it matched the kind of voice trouble in this story."
        ),
        (
            f"What happened when {hero.label} began to gargle?",
            f"The bowl shimmered and the gargle made little magical bubbles. The remedy changed how {hero.label}'s throat felt, so the next part of the story turned on whether the voice cleared fully or only partly."
        ),
    ]
    if outcome == "solo":
        qa.append(
            (
                f"How did the problem get solved?",
                f"The gargle worked well enough to clear {hero.label}'s voice before {event.need}. Because the recipe's magic was strong for this trouble, {hero.pronoun()} could do the enchanted task alone."
            )
        )
        qa.append(
            (
                f"How did the story end?",
                f"It ended with {hero.label} using a clear voice and finishing {event.need}. The ending image shows that patient magic and careful help changed fear into confidence."
            )
        )
    else:
        qa.append(
            (
                f"Did the gargle fix everything right away?",
                f"No. The gargle helped, but a little croak was still left in {hero.label}'s voice. That is why {helper.label} stood beside {hero.pronoun('object')} and helped carry the magic through."
            )
        )
        qa.append(
            (
                f"How did the story end?",
                f"It ended with {hero.label} and {helper.label} completing {event.need} together. The change is not that the trouble vanished all at once, but that kindness turned a shaky moment into a shared success."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"gargle", "magic_recipe"}
    event: Event = world.facts["event_cfg"]
    recipe: Recipe = world.facts["recipe_cfg"]
    helper_cfg: HelperCfg = world.facts["helper_cfg"]
    tags |= set(event.tags)
    tags |= set(recipe.tags)
    tags |= set(helper_cfg.tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = [f"{ent.id:8} ({ent.type:12}) label={ent.label!r}"]
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append("  " + " ".join(parts))
    lines.append(f"  facts: outcome={world.facts.get('outcome')!r} gargled={world.facts.get('gargled')} supporting={world.facts.get('supporting')}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CURATED
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="dew_hollow",
        problem="frost_nibble",
        recipe="moonmint_gargle",
        event="moon_gate",
        helper="fern_grandma",
        hero_name="Lina",
        hero_type="fairy_girl",
    ),
    StoryParams(
        setting="amber_tower",
        problem="chimney_whiff",
        recipe="silver_salt_gargle",
        event="lantern_blessing",
        helper="kettle_sprite",
        hero_name="Rowan",
        hero_type="fairy_boy",
    ),
    StoryParams(
        setting="thistledown_cottage",
        problem="toadlet_hex",
        recipe="honeyblossom_gargle",
        event="brook_lullaby",
        helper="reed_wizard",
        hero_name="Tansy",
        hero_type="fairy_girl",
    ),
    StoryParams(
        setting="thistledown_cottage",
        problem="toadlet_hex",
        recipe="pearl_rinse",
        event="moon_gate",
        helper="fern_grandma",
        hero_name="Mira",
        hero_type="fairy_girl",
    ),
    StoryParams(
        setting="amber_tower",
        problem="chimney_whiff",
        recipe="moonmint_gargle",
        event="brook_lullaby",
        helper="kettle_sprite",
        hero_name="Finn",
        hero_type="fairy_boy",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(S,P,R) :- setting(S), problem(P), recipe(R),
                has_ingredient(S,R), cures(R,P), sensible(R).

outcome(P,R,solo)   :- problem(P), recipe(R), severity(P,SV), strength(R,ST), ST >= SV.
outcome(P,R,shared) :- problem(P), recipe(R), severity(P,SV), strength(R,ST), ST < SV.

#show valid/3.
#show outcome/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for ingredient in sorted(setting.ingredients):
            lines.append(asp.fact("available", setting_id, ingredient))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("severity", problem_id, problem.severity))
    for recipe_id, recipe in RECIPES.items():
        lines.append(asp.fact("recipe", recipe_id))
        lines.append(asp.fact("needs", recipe_id, recipe.ingredient))
        lines.append(asp.fact("strength", recipe_id, recipe.strength))
        lines.append(asp.fact("sense", recipe_id, recipe.sense))
        if recipe.sense >= SENSE_MIN:
            lines.append(asp.fact("sensible", recipe_id))
        for problem_id in sorted(recipe.cures):
            lines.append(asp.fact("cures", recipe_id, problem_id))
    lines.append("has_ingredient(S,R) :- available(S,I), needs(R,I).")
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(problem_id: str, recipe_id: str) -> str:
    import asp
    model = asp.one_model(asp_program())
    atoms = asp.atoms(model, "outcome")
    for p, r, out in atoms:
        if p == problem_id and r == recipe_id:
            return out
    return "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: ASP gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue

    mismatches = []
    for params in cases:
        py_out = outcome_of(params)
        asp_out = asp_outcome(params.problem, params.recipe)
        if py_out != asp_out:
            mismatches.append((params.problem, params.recipe, py_out, asp_out))
    if not mismatches:
        print(f"OK: ASP outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print("MISMATCH in outcomes:")
        for item in mismatches[:10]:
            print(" ", item)

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story in smoke test")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a croaky voice, a magical recipe, and a shining gargle."
    )
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--recipe", choices=sorted(RECIPES))
    ap.add_argument("--event", choices=sorted(EVENTS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=sorted(HERO_TYPES))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and QA")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (setting, problem, recipe) combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_hero_name(rng: random.Random, hero_type: str) -> str:
    if hero_type == "fairy_girl":
        return rng.choice(GIRL_NAMES)
    return rng.choice(BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.recipe:
        recipe = RECIPES[args.recipe]
        if recipe.sense < SENSE_MIN:
            raise StoryError(explain_recipe_sense(recipe))

    if args.setting and args.recipe:
        setting = SETTINGS[args.setting]
        recipe = RECIPES[args.recipe]
        if not recipe_possible(setting, recipe):
            raise StoryError(explain_setting_recipe(setting, recipe))

    if args.problem and args.recipe:
        problem = PROBLEMS[args.problem]
        recipe = RECIPES[args.recipe]
        if not recipe_helps(problem, recipe):
            raise StoryError(explain_recipe_problem(problem, recipe))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.problem is None or combo[1] == args.problem)
        and (args.recipe is None or combo[2] == args.recipe)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, problem_id, recipe_id = rng.choice(sorted(combos))
    event_id = args.event or rng.choice(sorted(EVENTS))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    hero_type = args.hero_type or rng.choice(sorted(HERO_TYPES))
    hero_name = args.hero_name or _pick_hero_name(rng, hero_type)

    return StoryParams(
        setting=setting_id,
        problem=problem_id,
        recipe=recipe_id,
        event=event_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_type=hero_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.recipe not in RECIPES:
        raise StoryError(f"(Unknown recipe: {params.recipe})")
    if params.event not in EVENTS:
        raise StoryError(f"(Unknown event: {params.event})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.hero_type not in HERO_TYPES:
        raise StoryError(f"(Unknown hero type: {params.hero_type})")
    if not params.hero_name:
        raise StoryError("(Hero name may not be empty.)")

    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    recipe = RECIPES[params.recipe]
    if recipe.sense < SENSE_MIN:
        raise StoryError(explain_recipe_sense(recipe))
    if not recipe_possible(setting, recipe):
        raise StoryError(explain_setting_recipe(setting, recipe))
    if not recipe_helps(problem, recipe):
        raise StoryError(explain_recipe_problem(problem, recipe))

    world = tell(
        setting=setting,
        problem=problem,
        recipe=recipe,
        event=EVENTS[params.event],
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
    )
    story_text = world.render().replace("hero", params.hero_name).replace("helper", HELPERS[params.helper].name)
    story_text = story_text.replace("  ", " ")
    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, problem, recipe) combos:\n")
        for setting_id, problem_id, recipe_id in combos:
            print(f"  {setting_id:19} {problem_id:15} {recipe_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.problem} with {p.recipe} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
