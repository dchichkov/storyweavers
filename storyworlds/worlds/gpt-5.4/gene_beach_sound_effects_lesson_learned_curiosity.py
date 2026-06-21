#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gene_beach_sound_effects_lesson_learned_curiosity.py
================================================================================

A standalone story world for a heartwarming beach tale about **Gene**, curiosity,
tiny sounds, and a gentle lesson: when you are curious about a living thing,
quiet watching is kinder than grabbing.

The domain is intentionally small and concrete:

- A child at the beach hears a tiny sound -- "plip", "scritch", or "tap-tap".
- The sound comes from a shy beach creature in a small place: a tide pool, a shell,
  or a burrow in damp sand.
- The child first wants to act quickly (poke, grab, or scoop), because curiosity
  pulls hard.
- A caring grown-up suggests a gentle method instead (wait quietly, crouch and
  watch, or listen with a shell still in place).
- If the child follows the gentle method, the creature feels safe enough to appear.
  The ending image proves that curiosity has become careful wonder.
- If the child startles the creature first, it hides; the grown-up still helps the
  child slow down, and the story ends with a quieter, wiser second try.

The world uses simple typed entities with physical meters and emotional memes,
a small forward-chaining rule set, a reasonableness gate, and an inline ASP twin.
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/ itself.
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
    kind: str = "thing"            # "character" | "creature" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    living: bool = False
    shy: bool = False
    # physical and emotional dimensions
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    description: str
    sound_line: str
    wet: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class CreatureCfg:
    id: str
    label: str
    phrase: str
    home: str
    sound: str
    move_line: str
    lesson: str
    living: bool = True
    shy: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Impulse:
    id: str
    verb: str
    fast_line: str
    force: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class GentleMethod:
    id: str
    offer: str
    action_line: str
    helps_sound: bool
    power: int
    sense: int
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GrownupStyle:
    id: str
    type: str
    opening: str
    comfort: str


PLACES = {
    "tide_pool": Place(
        "tide_pool",
        "the tide pool",
        "where a ring of stones held a little bowl of sea water",
        'The waves went whoosh on the shore, and now and then the pool said, "plip."',
        tags={"beach", "water", "tide_pool"},
    ),
    "shell_patch": Place(
        "shell_patch",
        "the shell patch",
        "where wet shells shone like little moons in the sand",
        'The waves whispered whoosh, and from the shells came a tiny "tap-tap."',
        tags={"beach", "shell", "sound"},
    ),
    "sand_burrow": Place(
        "sand_burrow",
        "the damp sand by a burrow",
        "where the tide had left dark, smooth sand with one neat round hole",
        'The sea said whoosh, and the hole answered with a tiny "scritch."',
        tags={"beach", "sand", "burrow"},
    ),
}

CREATURES = {
    "hermit_crab": CreatureCfg(
        "hermit_crab",
        "hermit crab",
        "a little hermit crab",
        "inside a borrowed shell",
        "tap-tap",
        "At last a tiny claw peeked out, then the whole hermit crab came walking sideways into the sun.",
        "small beach creatures feel safer when people look gently instead of grabbing",
        tags={"hermit_crab", "living_thing", "shell"},
    ),
    "sand_crab": CreatureCfg(
        "sand_crab",
        "sand crab",
        "a pale sand crab",
        "under the damp sand",
        "scritch",
        "Soon the damp sand wiggled, and a pale sand crab popped up and hurried sideways like a wind-up toy.",
        "small beach creatures feel safer when people move slowly and keep gentle hands",
        tags={"sand_crab", "living_thing", "sand"},
    ),
    "snail": CreatureCfg(
        "snail",
        "sea snail",
        "a little sea snail",
        "clinging near a wet stone",
        "plip",
        "After a quiet moment, a little sea snail stretched out and began to glide along the shiny rock.",
        "quiet watching helps shy beach animals come out when they feel safe",
        tags={"snail", "living_thing", "tide_pool"},
    ),
}

IMPULSES = {
    "poke": Impulse(
        "poke",
        "poke at it",
        'Gene reached out quickly. "Maybe if I poke it, I can see it better," he said.',
        force=2,
        sense=1,
        tags={"poke", "startle"},
    ),
    "grab": Impulse(
        "grab",
        "grab the shell",
        'Gene bent down fast. "Maybe I can grab the shell and look inside," he said.',
        force=3,
        sense=1,
        tags={"grab", "startle"},
    ),
    "scoop": Impulse(
        "scoop",
        "scoop the sand away",
        'Gene cupped both hands. "Maybe if I scoop the sand away, I can find it," he said.',
        force=2,
        sense=1,
        tags={"scoop", "startle"},
    ),
}

METHODS = {
    "wait_quietly": GentleMethod(
        "wait_quietly",
        "kneel down and wait very quietly",
        "So Gene knelt down, tucked his hands into his lap, and waited while the water made its tiny sounds.",
        helps_sound=True,
        power=3,
        sense=3,
        qa_text="waited very quietly until the creature felt safe enough to come out",
        tags={"wait", "patience"},
    ),
    "watch_from_still": GentleMethod(
        "watch_from_still",
        "crouch still and watch without touching",
        "Gene crouched still as a shell on the sand and watched without touching anything.",
        helps_sound=True,
        power=3,
        sense=3,
        qa_text="crouched still and watched without touching, which helped the creature stay calm",
        tags={"watch", "patience"},
    ),
    "listen_gently": GentleMethod(
        "listen_gently",
        "put an ear close and listen gently while leaving everything in place",
        "Gene leaned close enough to listen, but he left the shell and the wet sand exactly where they were.",
        helps_sound=True,
        power=2,
        sense=2,
        qa_text="listened gently and left the little home in place",
        tags={"listen", "gentle"},
    ),
}

GROWNUPS = {
    "mother": GrownupStyle(
        "mother",
        "mother",
        '"Let us use quiet eyes and quiet hands," Mom said.',
        "Mom gave Gene a warm side hug.",
    ),
    "father": GrownupStyle(
        "father",
        "father",
        '"Let us try the gentle way first," Dad said.',
        "Dad rested a warm hand on Gene's shoulder.",
    ),
}

BOY_NAMES = ["Gene", "Ben", "Max", "Theo", "Sam", "Eli", "Noah", "Finn"]
GIRL_NAMES = ["Gene", "Lily", "Mia", "Zoe", "Ava", "Nora", "Lucy", "Rose"]
TRAITS = ["curious", "gentle", "bright-eyed", "eager", "thoughtful", "patient"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_startle_hides(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    child = world.get("child")
    if creature.meters["startled"] >= THRESHOLD and creature.meters["hidden"] < THRESHOLD:
        sig = ("hide", creature.id)
        if sig not in world.fired:
            world.fired.add(sig)
            creature.meters["hidden"] = 1.0
            child.memes["disappointment"] += 1
            out.append("__hide__")
    return out


def _r_quiet_restores(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    child = world.get("child")
    if child.memes["patience"] >= THRESHOLD and child.memes["care"] >= THRESHOLD:
        sig = ("calm", creature.id)
        if sig not in world.fired:
            world.fired.add(sig)
            creature.meters["safe"] += 1
            creature.meters["startled"] = 0.0
            out.append("__calm__")
    return out


def _r_safe_reveals(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    child = world.get("child")
    if creature.meters["safe"] >= THRESHOLD and child.memes["patience"] >= THRESHOLD:
        sig = ("reveal", creature.id)
        if sig not in world.fired:
            world.fired.add(sig)
            creature.meters["visible"] = 1.0
            creature.meters["hidden"] = 0.0
            child.memes["wonder"] += 1
            out.append("__reveal__")
    return out


CAUSAL_RULES = [
    Rule("startle_hides", "physical", _r_startle_hides),
    Rule("quiet_restores", "social", _r_quiet_restores),
    Rule("safe_reveals", "physical", _r_safe_reveals),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraints and prediction
# ---------------------------------------------------------------------------
def combo_valid(place: Place, creature: CreatureCfg, impulse: Impulse, method: GentleMethod) -> bool:
    if method.sense < SENSE_MIN:
        return False
    if impulse.force > 0 and not creature.shy:
        return False
    place_ok = {
        "hermit_crab": {"shell_patch", "tide_pool"},
        "sand_crab": {"sand_burrow"},
        "snail": {"tide_pool", "shell_patch"},
    }
    impulse_ok = {
        "hermit_crab": {"grab", "poke"},
        "sand_crab": {"scoop", "poke"},
        "snail": {"poke", "grab"},
    }
    if place.id not in place_ok[creature.id]:
        return False
    if impulse.id not in impulse_ok[creature.id]:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for creature_id, creature in CREATURES.items():
            for impulse_id, impulse in IMPULSES.items():
                for method_id, method in METHODS.items():
                    if combo_valid(place, creature, impulse, method):
                        combos.append((place_id, creature_id, impulse_id, method_id))
    return combos


def predict_impulse(world: World, impulse: Impulse) -> dict:
    sim = world.copy()
    creature = sim.get("creature")
    child = sim.get("child")
    creature.meters["startled"] += 1
    child.memes["rush"] += 1
    propagate(sim, narrate=False)
    return {
        "hidden": creature.meters["hidden"] >= THRESHOLD,
        "visible": creature.meters["visible"] >= THRESHOLD,
    }


def explain_rejection(place: Place, creature: CreatureCfg, impulse: Impulse, method: GentleMethod) -> str:
    place_ok = {
        "hermit_crab": {"shell_patch", "tide_pool"},
        "sand_crab": {"sand_burrow"},
        "snail": {"tide_pool", "shell_patch"},
    }
    impulse_ok = {
        "hermit_crab": {"grab", "poke"},
        "sand_crab": {"scoop", "poke"},
        "snail": {"poke", "grab"},
    }
    if place.id not in place_ok[creature.id]:
        return (
            f"(No story: {creature.phrase} does not plausibly live at {place.label} in this world. "
            f"Choose a place that matches its little home.)"
        )
    if impulse.id not in impulse_ok[creature.id]:
        return (
            f"(No story: wanting to {impulse.verb} is not a natural first move for a {creature.label} here. "
            f"Pick an impulse that fits what the child can actually reach.)"
        )
    if method.sense < SENSE_MIN:
        return (
            f"(No story: method '{method.id}' scores too low on gentle common sense.)"
        )
    return "(No story: this combination is not reasonable in this beach world.)"


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, grownup: Entity, place: Place) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"One soft morning at the beach, {child.id} walked beside {child.pronoun('possessive')} "
        f"{grownup.label_word} until they reached {place.label}, {place.description}."
    )
    world.say(place.sound_line)
    world.say(
        f"{child.id} stopped so fast that the wet sand squished under his toes. "
        f'"What was that sound?" he whispered.'
    )


def wonder(world: World, child: Entity, creature: CreatureCfg) -> None:
    world.say(
        f"{child.id} leaned closer, curious and bright-eyed. Maybe there was "
        f"{creature.phrase} hiding {creature.home}."
    )


def urge(world: World, child: Entity, impulse: Impulse) -> None:
    child.memes["rush"] += 1
    world.say(impulse.fast_line)


def warn(world: World, child: Entity, grownup: Entity, creature: CreatureCfg) -> None:
    pred = predict_impulse(world, IMPULSES[world.facts["impulse"].id])
    world.facts["pred_hidden"] = pred["hidden"]
    world.say(GROWNUPS[grownup.type].opening)
    if pred["hidden"]:
        world.say(
            f'"If you move too fast, the little {creature.label} may hide," '
            f"{grownup.label_word} said. "
            f'"Tiny beach animals do better when we let them feel safe."'
        )


def defy(world: World, child: Entity, creature_ent: Entity, impulse: Impulse) -> None:
    child.memes["defiance"] += 1
    creature_ent.meters["startled"] += 1
    propagate(world, narrate=False)
    if creature_ent.meters["hidden"] >= THRESHOLD:
        world.say(
            f"But curiosity tugged hard. {child.id} moved too quickly, and at once "
            f"everything went still. The tiny sound stopped."
        )
    else:
        world.say(
            f"But curiosity tugged hard, and {child.id} moved too quickly for a moment."
        )


def disappointment(world: World, child: Entity) -> None:
    if child.memes["disappointment"] >= THRESHOLD:
        world.say(
            f'{child.id} blinked and drew back. "Oh," he said softly. "I think I scared it."'
        )


def comfort(world: World, grownup: Entity, child: Entity) -> None:
    world.say(GROWNUPS[grownup.type].comfort)
    world.say(
        f'"It is all right to be curious," {grownup.label_word} said. '
        f'"The kind part is learning how to be curious gently."'
    )


def offer_method(world: World, grownup: Entity, method: GentleMethod) -> None:
    world.say(
        f'"Let us {method.offer}," {grownup.label_word} said. '
        f'"We can watch and listen, and then the beach can tell us its secret."'
    )


def accept(world: World, child: Entity, method: GentleMethod) -> None:
    child.memes["care"] += 1
    child.memes["patience"] += 1
    child.memes["curiosity"] += 1
    world.say(method.action_line)
    propagate(world, narrate=False)


def reveal(world: World, child: Entity, creature_cfg: CreatureCfg) -> None:
    if world.get("creature").meters["visible"] >= THRESHOLD:
        world.say(creature_cfg.move_line)
        world.say(
            f'{child.id} smiled so wide that his whole face seemed to shine. '
            f'"There you are," he whispered.'
        )


def lesson(world: World, child: Entity, grownup: Entity, creature_cfg: CreatureCfg) -> None:
    child.memes["lesson"] += 1
    world.say(
        f'"Now you know," {grownup.label_word} said. '
        f'"When we slow down, we see more."'
    )
    world.say(
        f"{child.id} nodded. He had learned that {creature_cfg.lesson}."
    )


def ending(world: World, child: Entity, grownup: Entity, place: Place, creature_cfg: CreatureCfg) -> None:
    world.say(
        f"They stayed by {place.label} a little longer, listening to the waves go whoosh "
        f"and the small brave sound go {creature_cfg.sound}."
    )
    world.say(
        f"When they finally walked on, {child.id} held {grownup.label_word}'s hand more gently than before, "
        f"as if he had learned how to carry a secret without squeezing it."
    )


# ---------------------------------------------------------------------------
# Full tale
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    creature_cfg: CreatureCfg,
    impulse: Impulse,
    method: GentleMethod,
    name: str = "Gene",
    gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "curious",
    first_try: str = "startle",
) -> World:
    world = World()
    child = world.add(Entity(id=name, kind="character", type=gender, role="child", traits=[trait]))
    grownup = world.add(Entity(id="Parent", kind="character", type=parent_type, role="grownup", label="the parent"))
    creature = world.add(Entity(
        id="creature",
        kind="creature",
        type=creature_cfg.id,
        label=creature_cfg.label,
        role="creature",
        living=True,
        shy=creature_cfg.shy,
    ))
    place_ent = world.add(Entity(id="place", kind="place", type="beach_place", label=place.label))

    world.facts.update(
        place=place,
        creature_cfg=creature_cfg,
        impulse=impulse,
        method=method,
        child=child,
        grownup=grownup,
        creature=creature,
        first_try=first_try,
        used_name_gene=(name == "Gene"),
    )

    introduce(world, child, grownup, place)
    wonder(world, child, creature_cfg)

    world.para()
    urge(world, child, impulse)
    warn(world, child, grownup, creature_cfg)

    if first_try == "startle":
        defy(world, child, creature, impulse)
        disappointment(world, child)
        comfort(world, grownup, child)
    else:
        world.say(
            f"{child.id} held still, even though curiosity was bouncing inside him like a little drum."
        )

    world.para()
    offer_method(world, grownup, method)
    accept(world, child, method)
    reveal(world, child, creature_cfg)
    lesson(world, child, grownup, creature_cfg)

    world.para()
    ending(world, child, grownup, place, creature_cfg)

    world.facts.update(
        revealed=creature.meters["visible"] >= THRESHOLD,
        hid_first=child.memes["disappointment"] >= THRESHOLD,
        learned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    creature: str
    impulse: str
    method: str
    name: str
    gender: str
    parent: str
    trait: str
    first_try: str = "startle"   # "startle" | "listen_first"
    seed: Optional[int] = None


CURATED = [
    StoryParams("tide_pool", "snail", "poke", "wait_quietly", "Gene", "boy", "mother", "curious", "startle"),
    StoryParams("shell_patch", "hermit_crab", "grab", "watch_from_still", "Gene", "boy", "father", "bright-eyed", "startle"),
    StoryParams("sand_burrow", "sand_crab", "scoop", "wait_quietly", "Gene", "boy", "mother", "eager", "listen_first"),
    StoryParams("tide_pool", "hermit_crab", "poke", "listen_gently", "Gene", "boy", "father", "thoughtful", "startle"),
]


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "beach": [(
        "Why do you hear so many sounds at the beach?",
        "You can hear many sounds at the beach because waves, wind, shells, and little animals all move in different ways. Together they make a busy, gentle kind of music."
    )],
    "tide_pool": [(
        "What is a tide pool?",
        "A tide pool is a little pool of sea water left behind among rocks when the tide goes out. Small beach creatures often rest or hide there."
    )],
    "shell": [(
        "Why do some beach animals hide in shells?",
        "Some small animals use shells like tiny homes because hard shells help protect their soft bodies. If they feel scared, they can pull inside."
    )],
    "sand": [(
        "Why do small crabs hide in sand?",
        "Small crabs hide in sand because the sand helps keep them safe from bigger animals and from drying out. They can disappear very quickly when they feel a shake or a shadow."
    )],
    "living_thing": [(
        "How should you look at a small living thing?",
        "You should look gently, with quiet hands and patient eyes. Living things can feel unsafe when people grab or poke them."
    )],
    "wait": [(
        "Why does waiting quietly help you see shy animals?",
        "Waiting quietly helps because shy animals notice sudden movement and hide from it. When everything stays calm, they often feel safe enough to come out again."
    )],
    "listen": [(
        "Why is listening a gentle way to learn?",
        "Listening is gentle because you can notice what is happening without moving or grabbing. It lets you learn while leaving the small place undisturbed."
    )],
}
KNOWLEDGE_ORDER = ["beach", "tide_pool", "shell", "sand", "living_thing", "wait", "listen"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, creature_cfg, impulse, method = f["place"], f["creature_cfg"], f["impulse"], f["method"]
    return [
        'Write a heartwarming beach story for a 3-to-5-year-old that includes the word "Gene", tiny sound effects, and a gentle lesson about curiosity.',
        f"Tell a story where Gene hears a tiny {creature_cfg.sound} at {place.label}, wants to {impulse.verb}, and learns to {method.offer} instead.",
        f"Write a simple beach story with wonder, sound words like whoosh and {creature_cfg.sound}, and an ending where curiosity becomes kindness."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    creature_cfg = f["creature_cfg"]
    place = f["place"]
    impulse = f["impulse"]
    method = f["method"]
    pw = grownup.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious child at the beach, and {pw} who helps him slow down. It is also about a tiny {creature_cfg.label} hidden near {place.label}."
        ),
        (
            "What made Gene curious?",
            f"Gene heard a tiny {creature_cfg.sound} near {place.label}, and he wanted to know what was making it. The small sound felt like a secret waiting to be discovered."
        ),
        (
            f"What did Gene want to do first?",
            f"He wanted to {impulse.verb} so he could find the sound quickly. That first idea came from excitement, not from being gentle."
        ),
    ]
    if f["hid_first"]:
        qa.append((
            "Why did the little creature hide?",
            f"It hid because Gene moved too fast and startled it. Shy little beach animals often disappear when they do not feel safe."
        ))
    else:
        qa.append((
            "Did Gene scare the creature first?",
            f"No. He kept himself still even though he was excited. That helped the tiny creature feel safer from the start."
        ))
    qa.append((
        f"How did {pw} help Gene?",
        f"{pw.capitalize()} helped Gene choose a gentler way: {method.qa_text}. The grown-up turned Gene's curiosity into patient watching instead of quick grabbing."
    ))
    qa.append((
        "What lesson did Gene learn?",
        f"Gene learned that {creature_cfg.lesson}. He also learned that slowing down can help him notice more, not less."
    ))
    qa.append((
        "How did the story end?",
        f"It ended with Gene and {pw} listening to the beach together while the tiny sound returned. The last image is calm and warm, showing that Gene had become gentler with his curiosity."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"beach", "living_thing"}
    tags |= set(world.facts["place"].tags)
    tags |= set(world.facts["creature_cfg"].tags)
    tags |= set(world.facts["method"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.living:
            bits.append("living=True")
        if e.shy:
            bits.append("shy=True")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Reasonable world combinations.
valid(P, C, I, M) :- place(P), creature(C), impulse(I), method(M),
                     place_ok(C, P), impulse_ok(C, I), sensible(M),
                     not forceful_nonshy(C, I).

sensible(M) :- method(M), method_sense(M, S), sense_min(Min), S >= Min.
forceful_nonshy(C, I) :- creature(C), impulse(I), impulse_force(I, F), F > 0, not shy(C).

% Outcome model: a first fast move startles a shy creature; patience and care
% restore safety; safe + patience reveals the creature.
hidden_first :- first_try(startle), chosen_creature(C), shy(C).
revealed     :- chosen_method(M), method_power(M, P), P >= 2.
lesson       :- revealed.

#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        if creature.shy:
            lines.append(asp.fact("shy", cid))
    for iid, impulse in IMPULSES.items():
        lines.append(asp.fact("impulse", iid))
        lines.append(asp.fact("impulse_force", iid, impulse.force))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("method_sense", mid, method.sense))
        lines.append(asp.fact("method_power", mid, method.power))
    place_ok = {
        "hermit_crab": {"shell_patch", "tide_pool"},
        "sand_crab": {"sand_burrow"},
        "snail": {"tide_pool", "shell_patch"},
    }
    impulse_ok = {
        "hermit_crab": {"grab", "poke"},
        "sand_crab": {"scoop", "poke"},
        "snail": {"poke", "grab"},
    }
    for cid, places in place_ok.items():
        for pid in sorted(places):
            lines.append(asp.fact("place_ok", cid, pid))
    for cid, impulses in impulse_ok.items():
        for iid in sorted(impulses):
            lines.append(asp.fact("impulse_ok", cid, iid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


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
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming beach storyworld: Gene hears a tiny sound and learns gentle curiosity."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--impulse", choices=IMPULSES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--first-try", dest="first_try", choices=["startle", "listen_first"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.creature and args.impulse and args.method:
        place = PLACES[args.place]
        creature = CREATURES[args.creature]
        impulse = IMPULSES[args.impulse]
        method = METHODS[args.method]
        if not combo_valid(place, creature, impulse, method):
            raise StoryError(explain_rejection(place, creature, impulse, method))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.creature is None or c[1] == args.creature)
        and (args.impulse is None or c[2] == args.impulse)
        and (args.method is None or c[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, creature, impulse, method = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl"])
    default_names = BOY_NAMES if gender == "boy" else GIRL_NAMES
    name = args.name or rng.choice(default_names)
    # Ensure the seed word appears often in this world.
    if args.name is None and rng.random() < 0.7:
        name = "Gene"
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    first_try = args.first_try or rng.choice(["startle", "listen_first", "startle"])
    return StoryParams(place, creature, impulse, method, name, gender, parent, trait, first_try)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        CREATURES[params.creature],
        IMPULSES[params.impulse],
        METHODS[params.method],
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
        trait=params.trait,
        first_try=params.first_try,
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, creature, impulse, method) combos:\n")
        for place, creature, impulse, method in combos:
            print(f"  {place:12} {creature:12} {impulse:8} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
                f"### {p.name}: {p.creature} at {p.place} "
                f"({p.impulse} -> {p.method}, {p.first_try})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
