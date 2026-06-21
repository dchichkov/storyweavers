#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/defeat_bronco_mixture_mystery_to_solve_slice.py
============================================================================

A standalone story world for a small slice-of-life "mystery to solve" tale:
a child and a grown-up prepare a mixture for a school event with a bronco
mascot, notice that something is wrong, and calmly solve the kitchen mystery.

The world model tracks:
- physical meters on bowls, trays, jars, and people
- emotional memes like worry, relief, pride, and trust
- a tiny causal engine that turns a wrong ingredient into a spoiled mixture
  and a spoiled mixture into event risk

The reasonableness gate is about kitchen common sense:
- only recipes that actually use the mixed-up ingredient are allowed
- clues must genuinely fit the kind of mix-up
- only sensible fixes are allowed
- visible mistakes may be picked out or remade; dissolved mistakes must be remade

Run it
------
    python storyworlds/worlds/gpt-5.4/defeat_bronco_mixture_mystery_to_solve_slice.py
    python storyworlds/worlds/gpt-5.4/defeat_bronco_mixture_mystery_to_solve_slice.py --recipe muffins --mixup salt_for_sugar
    python storyworlds/worlds/gpt-5.4/defeat_bronco_mixture_mystery_to_solve_slice.py --fix stir_more
    python storyworlds/worlds/gpt-5.4/defeat_bronco_mixture_mystery_to_solve_slice.py --all
    python storyworlds/worlds/gpt-5.4/defeat_bronco_mixture_mystery_to_solve_slice.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/defeat_bronco_mixture_mystery_to_solve_slice.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }
        return mapping.get(self.type, self.type)
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
class Occasion:
    id: str
    label: str
    place: str
    reason: str
    flyer_text: str
    ending_image: str
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
    mixture_name: str
    bowl_phrase: str
    result_name: str
    result_phrase: str
    action: str
    serve_text: str
    needed_words: set[str] = field(default_factory=set)
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
class Mixup:
    id: str
    expected: str
    wrong: str
    kind: str
    symptom: str
    source_text: str
    cause_text: str
    observations: dict[str, str] = field(default_factory=dict)
    recipe_ids: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    investigation_text: str
    qa_text: str
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
class Fix:
    id: str
    label: str
    sense: int
    handles: set[str] = field(default_factory=set)
    action_text: str = ""
    result_text: str = ""
    qa_text: str = ""
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "predicted_risk": False,
            "mystery_solved": False,
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


def _r_spoil(world: World) -> list[str]:
    bowl = world.entities.get("bowl")
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if bowl is None or hero is None or helper is None:
        return []
    if bowl.meters["wrong_added"] < THRESHOLD:
        return []
    if bowl.attrs.get("fixed"):
        return []
    sig = ("spoil", bowl.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bowl.meters["spoiled"] += 1
    hero.memes["worry"] += 1
    helper.memes["concern"] += 1
    return ["__spoil__"]


def _r_event_risk(world: World) -> list[str]:
    bowl = world.entities.get("bowl")
    event = world.entities.get("event")
    if bowl is None or event is None:
        return []
    if bowl.meters["spoiled"] < THRESHOLD:
        return []
    sig = ("risk", bowl.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    event.meters["risk"] += 1
    world.facts["predicted_risk"] = True
    return ["__risk__"]


def _r_relief(world: World) -> list[str]:
    bowl = world.entities.get("bowl")
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    event = world.entities.get("event")
    if bowl is None or hero is None or helper is None or event is None:
        return []
    if bowl.attrs.get("fixed") is not True:
        return []
    sig = ("relief", bowl.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    helper.memes["relief"] += 1
    helper.memes["trust"] += 1
    event.meters["ready"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="spoil", tag="physical", apply=_r_spoil),
    Rule(name="event_risk", tag="physical", apply=_r_event_risk),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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


def recipe_supports_mixup(recipe: Recipe, mixup: Mixup) -> bool:
    return recipe.id in mixup.recipe_ids


def clue_matches(mixup: Mixup, clue: Clue) -> bool:
    return clue.id in mixup.observations


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def can_fix(mixup: Mixup, fix: Fix) -> bool:
    return mixup.kind in fix.handles


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for recipe_id, recipe in RECIPES.items():
        for mixup_id, mixup in MIXUPS.items():
            if not recipe_supports_mixup(recipe, mixup):
                continue
            for clue_id, clue in CLUES.items():
                if not clue_matches(mixup, clue):
                    continue
                for fix in sensible_fixes():
                    if can_fix(mixup, fix):
                        combos.append((recipe_id, mixup_id, clue_id, fix.id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    mixup = MIXUPS[params.mixup]
    if FIXES[params.fix].id == "pick_out" and mixup.kind == "visible":
        return "saved"
    return "remade"


def predict_serving(world: World) -> dict:
    sim = world.copy()
    bowl = sim.get("bowl")
    bowl.attrs["fixed"] = False
    bowl.meters["wrong_added"] = max(bowl.meters["wrong_added"], 1.0)
    propagate(sim, narrate=False)
    return {
        "risky": sim.get("event").meters["risk"] >= THRESHOLD,
        "spoiled": sim.get("bowl").meters["spoiled"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, helper: Entity, occasion: Occasion, recipe: Recipe) -> None:
    hero.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f"After school, {hero.id} stood on a chair at the kitchen table while "
        f"{hero.pronoun('possessive')} {helper.label_word} set out {recipe.bowl_phrase}."
    )
    world.say(
        f"Tomorrow was {occasion.label} at {occasion.place}, and they were making "
        f"{recipe.mixture_name} for {occasion.reason}."
    )
    world.say(occasion.flyer_text)


def start_mixing(world: World, hero: Entity, recipe: Recipe, mixup: Mixup) -> None:
    bowl = world.get("bowl")
    hero.memes["focus"] += 1
    bowl.meters["mixed"] += 1
    world.say(
        f"{hero.id} measured oats and other small ingredients into the bowl and "
        f"stirred until the {recipe.mixture_name} looked almost ready."
    )
    bowl.attrs["wrong_word"] = mixup.wrong
    bowl.attrs["expected_word"] = mixup.expected
    bowl.attrs["kind"] = mixup.kind
    bowl.meters["wrong_added"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when the last spoonful went in, something changed. {mixup.symptom}"
    )


def investigate(world: World, hero: Entity, helper: Entity, clue: Clue, mixup: Mixup, occasion: Occasion) -> None:
    world.say(
        f'"Wait," said {helper.label_word.capitalize()}. "Let\'s solve the mystery before we '
        f'carry anything to {occasion.place}."'
    )
    pred = predict_serving(world)
    world.facts["predicted_risk"] = pred["risky"]
    if pred["risky"]:
        world.say(
            f"{helper.label_word.capitalize()} knew that if they ignored the problem, the "
            f"{mixup.symptom.lower()} would follow the bowl right to the school table."
        )
    world.say(clue.investigation_text)
    world.say(mixup.observations[clue.id])
    hero.memes["curiosity"] += 1
    world.facts["clue_line"] = mixup.observations[clue.id]


def reveal(world: World, hero: Entity, helper: Entity, mixup: Mixup) -> None:
    world.say(
        f"Together they checked the jars and boxes on the counter. {mixup.source_text}"
    )
    world.say(mixup.cause_text)
    hero.memes["understanding"] += 1
    world.facts["mystery_solved"] = True


def apply_fix(world: World, hero: Entity, helper: Entity, recipe: Recipe, fix: Fix, mixup: Mixup) -> None:
    bowl = world.get("bowl")
    event = world.get("event")
    world.say(fix.action_text)
    bowl.attrs["fixed"] = True
    bowl.attrs["fix_id"] = fix.id
    bowl.meters["spoiled"] = 0.0
    bowl.meters["wrong_added"] = 0.0
    event.meters["risk"] = 0.0
    if fix.id == "pick_out":
        bowl.meters["saved"] += 1
    else:
        bowl.meters["remade"] += 1
        bowl.meters["mixed"] += 1
    propagate(world, narrate=False)
    world.say(fix.result_text.format(result=recipe.result_name))
    hero.memes["worry"] = 0.0
    helper.memes["concern"] = 0.0


def ending(world: World, hero: Entity, helper: Entity, occasion: Occasion, recipe: Recipe, fix: Fix) -> None:
    outcome = "saved" if fix.id == "pick_out" else "remade"
    if outcome == "saved":
        world.say(
            f"Soon the {recipe.result_phrase} sat cooling by the window, and the kitchen felt calm again."
        )
    else:
        world.say(
            f"The second bowl came together smoothly, and before long the kitchen smelled just right."
        )
    world.say(
        f"When {hero.id} packed the tray, {hero.pronoun()} smiled at the little bronco on the flyer. "
        f"{hero.pronoun().capitalize()} had helped defeat a tiny mystery with patient eyes and a careful mind."
    )
    world.say(occasion.ending_image)


def tell(
    occasion: Occasion,
    recipe: Recipe,
    mixup: Mixup,
    clue: Clue,
    fix: Fix,
    hero_name: str = "Nora",
    hero_gender: str = "girl",
    helper_type: str = "father",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    helper = world.add(
        Entity(id="helper", kind="character", type=helper_type, label=helper_type, role="helper")
    )
    event = world.add(Entity(id="event", type="event", label=occasion.label))
    bowl = world.add(
        Entity(
            id="bowl",
            type="bowl",
            label="mixing bowl",
            attrs={"fixed": False, "wrong_word": "", "expected_word": "", "kind": ""},
        )
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        occasion=occasion,
        recipe=recipe,
        mixup=mixup,
        clue=clue,
        fix=fix,
        outcome="",
    )

    introduce(world, hero, helper, occasion, recipe)
    world.para()
    start_mixing(world, hero, recipe, mixup)
    investigate(world, hero, helper, clue, mixup, occasion)
    world.para()
    reveal(world, hero, helper, mixup)
    apply_fix(world, hero, helper, recipe, fix, mixup)
    ending(world, hero, helper, occasion, recipe, fix)

    world.facts["outcome"] = "saved" if fix.id == "pick_out" else "remade"
    return world


OCCASIONS = {
    "breakfast": Occasion(
        id="breakfast",
        label="Bronco Breakfast",
        place="Maple Street School",
        reason="the early family table in the gym",
        flyer_text='A bright blue flyer with a smiling bronco mascot leaned against the flour tin.',
        ending_image="The next morning, the tray waited on the long gym table under a paper sign that said BRONCO BREAKFAST.",
        tags={"bronco", "school"},
    ),
    "book_fair": Occasion(
        id="book_fair",
        label="Bronco Book Fair",
        place="Maple Street School",
        reason="the parent snack table by the library doors",
        flyer_text='On the fridge, a book fair note showed a bronco wearing glasses and waving from a stack of books.',
        ending_image="At the fair, children shuffled past the library doors, and the snack tray looked neat and welcoming beside the bronco sign.",
        tags={"bronco", "school", "books"},
    ),
    "game_night": Occasion(
        id="game_night",
        label="Bronco Game Night",
        place="Maple Street School",
        reason="the family refreshment table near the folding chairs",
        flyer_text='A hand-drawn bronco from the school office rested beside the recipe card with a row of little stars.',
        ending_image="That evening, the lights in the multipurpose room glowed warm, and their tray sat ready under the bronco banner.",
        tags={"bronco", "school", "community"},
    ),
}

RECIPES = {
    "muffins": Recipe(
        id="muffins",
        mixture_name="apple-oat muffin mixture",
        bowl_phrase="a big yellow bowl and a muffin tin",
        result_name="muffins",
        result_phrase="muffins",
        action="spooning batter into the tin",
        serve_text="a tray of warm muffins",
        needed_words={"sugar", "cinnamon", "chips"},
        tags={"baking", "muffins"},
    ),
    "cocoa": Recipe(
        id="cocoa",
        mixture_name="hot cocoa mixture",
        bowl_phrase="a bowl, a whisk, and the tin for cocoa packets",
        result_name="cocoa packets",
        result_phrase="little cocoa packets",
        action="whisking the dry mix smooth",
        serve_text="a basket of cocoa packets",
        needed_words={"sugar", "cinnamon"},
        tags={"cocoa", "drink"},
    ),
    "snack_mix": Recipe(
        id="snack_mix",
        mixture_name="after-school snack mixture",
        bowl_phrase="a steel bowl and a clean paper tray",
        result_name="snack cups",
        result_phrase="paper snack cups",
        action="filling paper cups",
        serve_text="a row of snack cups",
        needed_words={"chips"},
        tags={"snack", "mixture"},
    ),
}

MIXUPS = {
    "salt_for_sugar": Mixup(
        id="salt_for_sugar",
        expected="sugar",
        wrong="salt",
        kind="dissolved",
        symptom="The mixture looked fine, but one tiny taste made the sweetness disappear.",
        source_text="The sugar label had been taped onto the salt jar after a rushed breakfast cleanup.",
        cause_text="Someone had moved the jars while wiping the counter, and the plain white canisters had traded places.",
        observations={
            "taste": "Nora touched a bit to her tongue and blinked. It was salty instead of sweet.",
            "label": "A thin trail of white crystals led to two matching jars, and the wrong label was wrapped around the salt jar.",
        },
        recipe_ids={"muffins", "cocoa"},
        tags={"salt", "labels"},
    ),
    "cumin_for_cinnamon": Mixup(
        id="cumin_for_cinnamon",
        expected="cinnamon",
        wrong="cumin",
        kind="dissolved",
        symptom="The bowl gave off a warm smell, but it was not the cozy smell they expected.",
        source_text="The cinnamon lid had landed on the cumin jar, and the two little spice bottles looked almost like twins.",
        cause_text="Grandma had washed the spice lids the night before, and two brown bottles had been set back in the wrong order.",
        observations={
            "smell": "When she leaned close, the bowl smelled savory and dinner-like, not sweet and soft.",
            "label": "Near the rack, two brown spice bottles sat side by side, and the cinnamon lid was on the cumin bottle.",
        },
        recipe_ids={"muffins", "cocoa"},
        tags={"spices", "labels"},
    ),
    "raisins_for_chips": Mixup(
        id="raisins_for_chips",
        expected="chocolate chips",
        wrong="raisins",
        kind="visible",
        symptom="The bowl looked cheerful at first, until the dark bits turned out to be the wrong shape.",
        source_text="The raisin box had been set in front of the chocolate chips, and both boxes wore nearly the same brown paper sleeve.",
        cause_text="A grocery bag had been unpacked in a hurry, and two snack boxes with matching tops ended up together.",
        observations={
            "look": "Nora stared into the bowl. The dark pieces were wrinkled raisins, not shiny little chocolate chips.",
            "label": "Two brown boxes sat shoulder to shoulder by the toaster, and the front one was raisins, not chips.",
        },
        recipe_ids={"muffins", "snack_mix"},
        tags={"snack", "look"},
    ),
}

CLUES = {
    "taste": Clue(
        id="taste",
        label="taste",
        investigation_text="They paused before adding anything else. A careful clue would tell them more than guessing.",
        qa_text="They used a tiny taste as a clue.",
        tags={"taste"},
    ),
    "smell": Clue(
        id="smell",
        label="smell",
        investigation_text="Instead of hurrying, they bent over the bowl and let the smell speak first.",
        qa_text="They used the smell as a clue.",
        tags={"smell"},
    ),
    "look": Clue(
        id="look",
        label="look",
        investigation_text="They held the bowl under the window and looked slowly instead of stirring faster.",
        qa_text="They used what they could see as a clue.",
        tags={"look"},
    ),
    "label": Clue(
        id="label",
        label="label",
        investigation_text="They followed the mystery away from the bowl and toward the jars and boxes on the counter.",
        qa_text="They checked the labels on the containers.",
        tags={"labels"},
    ),
}

FIXES = {
    "remake": Fix(
        id="remake",
        label="remake the batch",
        sense=3,
        handles={"dissolved", "visible"},
        action_text="So they tipped the mistaken mixture into the compost pail, washed the bowl, and started again with the right jar open beside them.",
        result_text="Soon a fresh batch of {result} was ready, and this time the mixture matched the recipe card perfectly.",
        qa_text="They remade the batch from the beginning.",
        tags={"kitchen", "careful"},
    ),
    "pick_out": Fix(
        id="pick_out",
        label="pick the pieces out",
        sense=3,
        handles={"visible"},
        action_text="Because the mistake was easy to see, they sat side by side and picked the wrong pieces out one by one, laughing quietly when the last raisin was gone.",
        result_text="When they finished, the {result} were ready to pack, and nothing in the bowl looked out of place anymore.",
        qa_text="They picked out the visible wrong pieces and saved the batch.",
        tags={"kitchen", "careful"},
    ),
    "stir_more": Fix(
        id="stir_more",
        label="stir more and hope",
        sense=1,
        handles=set(),
        action_text="They stirred harder and hoped the problem would disappear.",
        result_text="But hoping is not a real fix for a wrong ingredient.",
        qa_text="They just stirred more.",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Ella", "Zoe", "Lucy", "Anna"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Eli", "Noah", "Jack", "Finn"]


@dataclass
class StoryParams:
    occasion: str
    recipe: str
    mixup: str
    clue: str
    fix: str
    hero_name: str
    hero_gender: str
    helper_type: str
    seed: Optional[int] = None
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
    "bronco": [
        (
            "What is a bronco mascot?",
            "A bronco mascot is a team symbol based on a lively horse. Schools use mascots on signs, shirts, and event posters so everyone knows they belong together.",
        )
    ],
    "mixture": [
        (
            "What is a mixture?",
            "A mixture is made when different things are stirred or put together in one bowl or cup. In cooking, a mixture can become food only if the ingredients are the right ones.",
        )
    ],
    "salt": [
        (
            "Why is salt different from sugar?",
            "Salt and sugar can look alike, but they taste very different. If you mix them up in a recipe, the food can taste wrong right away.",
        )
    ],
    "spices": [
        (
            "Why do cooks smell spices?",
            "Spices have strong smells that help you tell them apart. Smelling them can be a good clue when two jars look almost the same.",
        )
    ],
    "labels": [
        (
            "Why are labels helpful in a kitchen?",
            "Labels tell you what is inside a jar or box. Clear labels help people avoid mix-ups when two containers look alike.",
        )
    ],
    "taste": [
        (
            "When is a tiny taste useful while cooking?",
            "A careful tiny taste can help a grown-up check whether a mixture seems right. It can reveal a problem before the food is packed or baked.",
        )
    ],
    "look": [
        (
            "How can looking closely solve a food mystery?",
            "Looking closely helps you notice shapes, colors, and textures. That can show whether the pieces in a bowl are the ones the recipe meant to use.",
        )
    ],
    "remake": [
        (
            "Why is remaking food sometimes the best choice?",
            "If the wrong ingredient has already mixed all the way in, you often cannot pull it back out. Starting over can be the safest and kindest fix.",
        )
    ],
    "save_batch": [
        (
            "When can you save a batch instead of starting over?",
            "You can sometimes save a batch when the mistake is still easy to see and remove. That works better with big visible pieces than with powders that dissolve.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "bronco",
    "mixture",
    "salt",
    "spices",
    "labels",
    "taste",
    "look",
    "remake",
    "save_batch",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    recipe = f["recipe"]
    occasion = f["occasion"]
    mixup = f["mixup"]
    fix = f["fix"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old about a child making a {recipe.mixture_name} for {occasion.label}. Include the words "defeat", "bronco", and "mixture".',
        f"Tell a gentle Mystery to Solve story where a child notices that {mixup.wrong} went into a school snack by mistake and works with a grown-up to fix it before the {occasion.label} table.",
        f"Write a home-and-school story with a small kitchen mystery, a calm helper, and a happy ending where they {fix.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    occasion = f["occasion"]
    recipe = f["recipe"]
    mixup = f["mixup"]
    clue = f["clue"]
    fix = f["fix"]
    helper_word = helper.label_word
    hero_name = hero.label
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name} and {hero.pronoun('possessive')} {helper_word} making food for {occasion.label}. They are working together at home for a school event with a bronco mascot.",
        ),
        (
            "What were they making?",
            f"They were making {recipe.mixture_name}. The bowl was meant for {occasion.reason}, so the mixture had to be right before they packed it.",
        ),
        (
            "What was the mystery?",
            f"The mystery was that the bowl did not seem right after the last ingredient went in. Something had been mixed up, and they needed to figure out which ingredient was wrong before serving it.",
        ),
        (
            f"How did they know something was wrong?",
            f"They noticed a clue: {clue.qa_text} {world.facts.get('clue_line', '')} That clue pointed them toward the real problem instead of letting them guess wildly.",
        ),
        (
            "What had been mixed up?",
            f"They meant to use {mixup.expected}, but {mixup.wrong} went in instead. The jars or boxes looked too similar, which is why the mistake happened.",
        ),
    ]
    if f.get("predicted_risk"):
        qa.append(
            (
                "Why did they stop and investigate instead of hurrying?",
                f"They knew the mixture could spoil the tray for {occasion.label} if they ignored the problem. Stopping early gave them time to solve the mystery before anyone tasted the wrong batch.",
            )
        )
    if f.get("outcome") == "saved":
        qa.append(
            (
                "How did they solve the problem?",
                f"They saved the batch by removing the visible mistake. That worked because the wrong pieces had not dissolved into the rest of the mixture.",
            )
        )
    else:
        qa.append(
            (
                "How did they solve the problem?",
                f"They remade the batch from the beginning. That was the sensible fix because once the wrong ingredient had mixed all the way in, they could not simply pull it back out.",
            )
        )
    qa.append(
        (
            f"How did {hero_name} feel at the end?",
            f"{hero_name} felt relieved and proud. {hero.pronoun().capitalize()} had helped defeat a small mystery by paying attention and staying calm with {helper.pronoun('object')}.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mixup = f["mixup"]
    clue = f["clue"]
    fix = f["fix"]
    tags: set[str] = {"bronco", "mixture"}
    if "salt" in mixup.tags:
        tags.add("salt")
    if "spices" in mixup.tags:
        tags.add("spices")
    if "labels" in mixup.tags or "labels" in clue.tags:
        tags.add("labels")
    if "taste" in clue.tags:
        tags.add("taste")
    if "look" in clue.tags:
        tags.add("look")
    if fix.id == "remake":
        tags.add("remake")
    if fix.id == "pick_out":
        tags.add("save_batch")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", False, None)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        occasion="breakfast",
        recipe="muffins",
        mixup="salt_for_sugar",
        clue="taste",
        fix="remake",
        hero_name="Nora",
        hero_gender="girl",
        helper_type="father",
    ),
    StoryParams(
        occasion="book_fair",
        recipe="cocoa",
        mixup="cumin_for_cinnamon",
        clue="smell",
        fix="remake",
        hero_name="Ben",
        hero_gender="boy",
        helper_type="grandmother",
    ),
    StoryParams(
        occasion="game_night",
        recipe="snack_mix",
        mixup="raisins_for_chips",
        clue="look",
        fix="pick_out",
        hero_name="Mia",
        hero_gender="girl",
        helper_type="mother",
    ),
    StoryParams(
        occasion="breakfast",
        recipe="muffins",
        mixup="raisins_for_chips",
        clue="label",
        fix="pick_out",
        hero_name="Leo",
        hero_gender="boy",
        helper_type="grandfather",
    ),
    StoryParams(
        occasion="book_fair",
        recipe="cocoa",
        mixup="salt_for_sugar",
        clue="label",
        fix="remake",
        hero_name="Ella",
        hero_gender="girl",
        helper_type="mother",
    ),
]


def explain_recipe_mixup(recipe: Recipe, mixup: Mixup) -> str:
    return (
        f"(No story: {recipe.mixture_name} is not a good fit for the mix-up "
        f"'{mixup.id}'. This recipe would not normally be using {mixup.expected} "
        f"in the spot that got confused.)"
    )


def explain_clue(mixup: Mixup, clue: Clue) -> str:
    return (
        f"(No story: the clue '{clue.id}' would not honestly reveal the mix-up "
        f"'{mixup.id}'. Pick a clue that fits what the child could really notice.)"
    )


def explain_fix(fix: Fix) -> str:
    return (
        f"(Refusing fix '{fix.id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). A storyworld should prefer a real, sensible kitchen fix.)"
    )


def explain_incompatible_fix(mixup: Mixup, fix: Fix) -> str:
    if mixup.kind == "dissolved":
        return (
            f"(No story: {mixup.wrong} dissolves into the mixture, so '{fix.id}' cannot really undo it. "
            f"A remade batch is the sensible fix.)"
        )
    return (
        f"(No story: '{fix.id}' does not fit the kind of mistake described here.)"
    )


ASP_RULES = r"""
sensible_fix(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(R, M, C, F) :- recipe(R), mixup(M), clue(C), fix(F),
                     recipe_match(R, M), clue_match(M, C),
                     sensible_fix(F), kind(M, K), handles(F, K).

outcome(saved)  :- chosen_mixup(M), kind(M, visible), chosen_fix(pick_out).
outcome(remade) :- not outcome(saved).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for occasion_id in OCCASIONS:
        lines.append(asp.fact("occasion", occasion_id))
    for recipe_id in RECIPES:
        lines.append(asp.fact("recipe", recipe_id))
    for mixup_id, mixup in MIXUPS.items():
        lines.append(asp.fact("mixup", mixup_id))
        lines.append(asp.fact("kind", mixup_id, mixup.kind))
        for recipe_id in sorted(mixup.recipe_ids):
            lines.append(asp.fact("recipe_match", recipe_id, mixup_id))
        for clue_id in sorted(mixup.observations):
            lines.append(asp.fact("clue_match", mixup_id, clue_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        for kind in sorted(fix.handles):
            lines.append(asp.fact("handles", fix_id, kind))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_mixup", params.mixup),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_params.seed = 123
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
            rendered = buf.getvalue()
        if "smoke" not in rendered or len(rendered.strip()) < 40:
            raise StoryError("Emit smoke test produced suspiciously little output.")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child and grown-up solve a small kitchen mystery before a Bronco school event."
    )
    ap.add_argument("--occasion", choices=OCCASIONS)
    ap.add_argument("--recipe", choices=RECIPES)
    ap.add_argument("--mixup", choices=MIXUPS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(FIXES[args.fix]))
    if args.recipe and args.mixup:
        recipe = RECIPES[args.recipe]
        mixup = MIXUPS[args.mixup]
        if not recipe_supports_mixup(recipe, mixup):
            raise StoryError(explain_recipe_mixup(recipe, mixup))
    if args.mixup and args.clue:
        mixup = MIXUPS[args.mixup]
        clue = CLUES[args.clue]
        if not clue_matches(mixup, clue):
            raise StoryError(explain_clue(mixup, clue))
    if args.mixup and args.fix:
        mixup = MIXUPS[args.mixup]
        fix = FIXES[args.fix]
        if fix.sense >= SENSE_MIN and not can_fix(mixup, fix):
            raise StoryError(explain_incompatible_fix(mixup, fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.recipe is None or combo[0] == args.recipe)
        and (args.mixup is None or combo[1] == args.mixup)
        and (args.clue is None or combo[2] == args.clue)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    recipe_id, mixup_id, clue_id, fix_id = rng.choice(sorted(combos))
    occasion_id = args.occasion or rng.choice(sorted(OCCASIONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        hero_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])

    return StoryParams(
        occasion=occasion_id,
        recipe=recipe_id,
        mixup=mixup_id,
        clue=clue_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_gender=gender,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.occasion not in OCCASIONS:
        raise StoryError(f"(Unknown occasion: {params.occasion})")
    if params.recipe not in RECIPES:
        raise StoryError(f"(Unknown recipe: {params.recipe})")
    if params.mixup not in MIXUPS:
        raise StoryError(f"(Unknown mixup: {params.mixup})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    recipe = RECIPES[params.recipe]
    mixup = MIXUPS[params.mixup]
    clue = CLUES[params.clue]
    fix = FIXES[params.fix]

    if not recipe_supports_mixup(recipe, mixup):
        raise StoryError(explain_recipe_mixup(recipe, mixup))
    if not clue_matches(mixup, clue):
        raise StoryError(explain_clue(mixup, clue))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(fix))
    if not can_fix(mixup, fix):
        raise StoryError(explain_incompatible_fix(mixup, fix))

    world = tell(
        occasion=OCCASIONS[params.occasion],
        recipe=recipe,
        mixup=mixup,
        clue=clue,
        fix=fix,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_type=params.helper_type,
    )
    world.get("hero").label = params.hero_name

    story = world.render().replace("hero", params.hero_name)
    sample = StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )
    sample.story = sample.story.replace("hero", params.hero_name)
    return sample


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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (recipe, mixup, clue, fix) combos:\n")
        for recipe_id, mixup_id, clue_id, fix_id in combos:
            print(f"  {recipe_id:10} {mixup_id:18} {clue_id:8} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name}: {p.recipe} / {p.mixup} / {p.clue} / {p.fix} "
                f"({p.occasion}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
