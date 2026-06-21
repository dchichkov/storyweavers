#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chy_dust_reconciliation_mystery_to_solve_transformation.py
======================================================================================

A standalone storyworld for a tall-tale mystery about **chy dust**:
a boast-sized wind, a missing keepsake, a giant transformed creature, and
two children who must stop blaming each other long enough to solve the puzzle.

The world enforces a small common-sense gate:
- the transformed creature must plausibly want the missing keepsake
- the place must provide the kind of water needed for the de-dusting fix

That keeps the mystery tight: a clue trail, a real culprit, a reversible
transformation, and a reconciliation that grows out of the solved mystery.

Run it
------
    python storyworlds/worlds/gpt-5.4/chy_dust_reconciliation_mystery_to_solve_transformation.py
    python storyworlds/worlds/gpt-5.4/chy_dust_reconciliation_mystery_to_solve_transformation.py --place prairie --keepsake silver_bell --creature magpie
    python storyworlds/worlds/gpt-5.4/chy_dust_reconciliation_mystery_to_solve_transformation.py --place canyon --reversal barrel_bath
    python storyworlds/worlds/gpt-5.4/chy_dust_reconciliation_mystery_to_solve_transformation.py --all
    python storyworlds/worlds/gpt-5.4/chy_dust_reconciliation_mystery_to_solve_transformation.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/chy_dust_reconciliation_mystery_to_solve_transformation.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    owner: str = ""
    # physical + emotional state
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
    boast: str
    clue_path: str
    sources: set[str] = field(default_factory=set)
    home: str = ""
    ending: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    tag: str
    sparkle: str
    use_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CreatureCfg:
    id: str
    label: str
    phrase: str
    likes: set[str] = field(default_factory=set)
    lair: str = ""
    print_name: str = ""
    coat: str = ""
    carry: int = 1
    hiding_line: str = ""
    calm_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Reversal:
    id: str
    label: str
    source: str
    act: str
    closing: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    keepsake: str
    creature: str
    reversal: str
    accuser: str
    accuser_gender: str
    accused: str
    accused_gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


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
        return [e for e in self.entities.values() if e.role in {"accuser", "accused"}]

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


def _r_giant(world: World) -> list[str]:
    out: list[str] = []
    creature = world.entities.get("creature")
    if creature is None:
        return out
    if creature.meters["chy_dust"] < THRESHOLD:
        return out
    sig = ("giant", creature.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.meters["giant"] += 1
    for kid in world.kids():
        kid.memes["awe"] += 1
    out.append("__giant__")
    return out


def _r_missing_hurts(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("keepsake")
    accused = next((e for e in world.kids() if e.role == "accused"), None)
    accuser = next((e for e in world.kids() if e.role == "accuser"), None)
    if item is None or accused is None or accuser is None:
        return out
    if item.meters["missing"] < THRESHOLD or accuser.memes["blame"] < THRESHOLD:
        return out
    sig = ("hurt", accused.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    accused.memes["hurt"] += 1
    accused.memes["distance"] += 1
    accuser.memes["distance"] += 1
    out.append("__hurt__")
    return out


def _r_apology_repairs(world: World) -> list[str]:
    out: list[str] = []
    accused = next((e for e in world.kids() if e.role == "accused"), None)
    accuser = next((e for e in world.kids() if e.role == "accuser"), None)
    if accused is None or accuser is None:
        return out
    if accuser.memes["sorry"] < THRESHOLD:
        return out
    sig = ("repair", accuser.id, accused.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    accuser.memes["trust"] += 1
    accused.memes["trust"] += 1
    accuser.memes["distance"] = 0.0
    accused.memes["distance"] = 0.0
    accused.memes["hurt"] = 0.0
    accused.memes["forgive"] += 1
    out.append("__repair__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="giant", tag="physical", apply=_r_giant),
    Rule(name="missing_hurts", tag="social", apply=_r_missing_hurts),
    Rule(name="apology_repairs", tag="social", apply=_r_apology_repairs),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "prairie": Place(
        id="prairie",
        label="the long prairie outside Dusty Draw",
        boast="Out there the grass was so wide it looked as if the earth had forgotten where to fold up.",
        clue_path="past a leaning fence, around a windmill, and up to a hay hill that looked as tall as Tuesday",
        sources={"barrel", "pump"},
        home="the windmill yard",
        ending="the evening wind hummed like a fiddle string",
        tags={"prairie", "barrel", "pump"},
    ),
    "canyon": Place(
        id="canyon",
        label="the red canyon by Rumble Creek",
        boast="The canyon walls were so high they could have hidden a second sunset behind them.",
        clue_path="along the red stones, across a narrow log, and down to the creek bend",
        sources={"creek"},
        home="the creek bend",
        ending="the red rocks glowed warm as apple peels",
        tags={"canyon", "creek"},
    ),
    "fairground": Place(
        id="fairground",
        label="the old fairground on the edge of town",
        boast="Its empty rides still looked ready to spin the moon if somebody gave them one good shove.",
        clue_path="between the silent booths, under the giant arch, and behind the big striped tent",
        sources={"pump", "barrel"},
        home="behind the striped tent",
        ending="the quiet ferris wheel held the last pink light",
        tags={"fairground", "pump", "barrel"},
    ),
}

KEEPSAKES = {
    "silver_bell": Keepsake(
        id="silver_bell",
        label="silver bell",
        phrase="a silver bell no bigger than a plum and twice as bright",
        tag="shiny",
        sparkle="caught every bit of sun and tossed it back laughing",
        use_line="They liked to ring the bell to start their make-believe cattle drive.",
        ending_line="Its little clear ring skipped across the evening air.",
        tags={"bell", "shiny"},
    ),
    "kite_spool": Keepsake(
        id="kite_spool",
        label="kite spool",
        phrase="a kite spool wound with blue string as long as a lazy river",
        tag="stringy",
        sparkle="glimmered with blue thread from end to end",
        use_line="With it they could let their tall-tale kite climb almost nose to nose with the clouds.",
        ending_line="The blue string rose into the sky in one smooth humming line.",
        tags={"kite", "string"},
    ),
    "red_scarf": Keepsake(
        id="red_scarf",
        label="red scarf",
        phrase="a red scarf light enough to flutter before the wind had even made up its mind",
        tag="fluttery",
        sparkle="flickered in the breeze like a tiny flag of fire",
        use_line="They liked to tie the scarf to a stick and parade like heroes home from impossible journeys.",
        ending_line="The scarf danced from a stick like a brave red flame that did not burn.",
        tags={"scarf", "cloth"},
    ),
}

CREATURES = {
    "magpie": CreatureCfg(
        id="magpie",
        label="magpie",
        phrase="a magpie with black feathers glossy as boot polish",
        likes={"shiny", "stringy"},
        lair="a nest jammed into the windmill braces",
        print_name="three-toed prints",
        coat="feathers",
        carry=1,
        hiding_line="The keepsake was tucked into the nest as neatly as treasure in a pirate box.",
        calm_line="The bird only hopped sideways and blinked, as if it had never meant to start a quarrel bigger than itself.",
        tags={"magpie", "bird"},
    ),
    "goat": CreatureCfg(
        id="goat",
        label="goat",
        phrase="a goat with a beard like a gray paintbrush",
        likes={"stringy", "fluttery"},
        lair="the hay hill",
        print_name="split hoofprints",
        coat="fur",
        carry=2,
        hiding_line="The keepsake was looped around one horn, where the goat seemed to think it was the finest decoration in three counties.",
        calm_line="The goat stamped once, sneezed out a puff of dust, and looked more puzzled than mean.",
        tags={"goat", "farm_animal"},
    ),
    "calf": CreatureCfg(
        id="calf",
        label="calf",
        phrase="a calf with soft ears and eyes the color of wet chestnuts",
        likes={"shiny", "fluttery"},
        lair="the trough beside the fence",
        print_name="round hoofprints",
        coat="hide",
        carry=2,
        hiding_line="The keepsake had slid beside the trough, where the calf had nosed it close just to admire it.",
        calm_line="The calf gave a surprised moo, the kind that sounded more sorry than scary.",
        tags={"calf", "farm_animal"},
    ),
}

REVERSALS = {
    "barrel_bath": Reversal(
        id="barrel_bath",
        label="rain-barrel bath",
        source="barrel",
        act="tilted a rain barrel and sluiced cool water over the creature until the chy dust ran away in glittering streams",
        closing="When the last bright streak washed off, the creature shrank back to its everyday size.",
        qa_text="They washed the chy dust off with rain-barrel water",
        tags={"barrel", "water"},
    ),
    "creek_rinse": Reversal(
        id="creek_rinse",
        label="creek rinse",
        source="creek",
        act="led the creature to the creek and splashed water over it until the shy magic gave up and slid downstream",
        closing="The giant shape melted down to ordinary size, leaving only wet whiskers and blinking eyes behind.",
        qa_text="They rinsed the chy dust away in the creek",
        tags={"creek", "water"},
    ),
    "pump_spray": Reversal(
        id="pump_spray",
        label="pump spray",
        source="pump",
        act="worked the old hand pump until a silver stream splashed over the creature and knocked the chy dust loose",
        closing="Soon the creature was small again, dripping and harmless and looking almost embarrassed.",
        qa_text="They sprayed the chy dust off with water from the old hand pump",
        tags={"pump", "water"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Tom", "Max", "Sam", "Eli", "Finn", "Noah", "Theo"]
TRAITS = ["quick", "careful", "bold", "stubborn", "clever", "sunny"]


def wants_keepsake(creature: CreatureCfg, keepsake: Keepsake) -> bool:
    return keepsake.tag in creature.likes and creature.carry >= 1


def place_supports(place: Place, reversal: Reversal) -> bool:
    return reversal.source in place.sources


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for keepsake_id, keepsake in KEEPSAKES.items():
            for creature_id, creature in CREATURES.items():
                if not wants_keepsake(creature, keepsake):
                    continue
                for reversal_id, reversal in REVERSALS.items():
                    if place_supports(place, reversal):
                        combos.append((place_id, keepsake_id, creature_id, reversal_id))
    return combos


def explain_rejection(place: Place, keepsake: Keepsake, creature: CreatureCfg, reversal: Reversal) -> str:
    if not wants_keepsake(creature, keepsake):
        return (
            f"(No story: a {creature.label} in this world would not plausibly carry off a "
            f"{keepsake.label}. The mystery needs a creature that actually likes something "
            f"{keepsake.tag}.)"
        )
    if not place_supports(place, reversal):
        return (
            f"(No story: {place.label} has no {reversal.source} water source, so "
            f"'{reversal.id}' cannot wash off the chy dust there.)"
        )
    return "(No story: that combination does not make a tight mystery.)"


def _do_dusting(world: World, creature: Entity, narrate: bool = True) -> None:
    creature.meters["chy_dust"] += 1
    propagate(world, narrate=narrate)


def _do_take(world: World, creature: Entity, item: Entity, narrate: bool = True) -> None:
    item.meters["missing"] += 1
    item.owner = creature.id
    propagate(world, narrate=narrate)


def _do_wash(world: World, creature: Entity, reversal: Reversal, narrate: bool = True) -> None:
    creature.meters["chy_dust"] = 0.0
    creature.meters["giant"] = 0.0
    creature.meters["washed"] += 1
    if narrate:
        world.say(reversal.closing)


def predict_mystery(world: World, keepsake: Keepsake, creature_cfg: CreatureCfg) -> dict:
    sim = world.copy()
    creature = sim.get("creature")
    item = sim.get("keepsake")
    _do_dusting(sim, creature, narrate=False)
    if wants_keepsake(creature_cfg, keepsake):
        _do_take(sim, creature, item, narrate=False)
    return {
        "giant": creature.meters["giant"] >= THRESHOLD,
        "missing": item.meters["missing"] >= THRESHOLD,
    }


def setup_play(world: World, a: Entity, b: Entity, keepsake: Keepsake) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["trust"] += 1
    world.say(
        f"{a.id} and {b.id} were the kind of partners who could turn one open afternoon into six impossible adventures. "
        f"They lived near {world.place.label}, and {world.place.boast}"
    )
    world.say(
        f"They had {keepsake.phrase} that {keepsake.sparkle}. {keepsake.use_line}"
    )


def dust_night(world: World) -> None:
    world.say(
        "That night a wind came bowling through town with more swagger than manners. "
        "It left a gold-gray sprinkling of chy dust on fences, boots, and windowsills."
    )


def missing_and_blame(world: World, accuser: Entity, accused: Entity, item: Entity, elder: Entity) -> None:
    item.meters["missing"] += 1
    accuser.memes["alarm"] += 1
    accuser.memes["blame"] += 1
    propagate(world, narrate=False)
    world.say(
        f"By morning the {item.label} was gone. {accuser.id} looked at the empty spot and blurted, "
        f'"{accused.id}, did you take it?"'
    )
    world.say(
        f"{accused.id}'s face fell. "
        f'"No," {accused.pronoun()} said. "I wanted to find it with you."'
    )
    world.say(
        f"{elder.label_word.capitalize()} did not scold. {elder.pronoun().capitalize()} only pointed at the step, "
        f"where something stranger than a plain loss had begun to show."
    )


def clue_scene(world: World, keepsake: Keepsake, creature_cfg: CreatureCfg) -> None:
    pred = predict_mystery(world, keepsake, creature_cfg)
    world.facts["predicted_giant"] = pred["giant"]
    world.facts["predicted_missing"] = pred["missing"]
    world.say(
        f"There in the dirt lay {creature_cfg.print_name} big enough to use for soup bowls, "
        f"and between them ran a glittering trail of chy dust."
    )
    world.say(
        f"The trail wound {world.place.clue_path}. That made the missing keepsake feel less like stealing and more like a mystery begging to be solved."
    )


def follow_trail(world: World, a: Entity, b: Entity) -> None:
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f"So the two children went after the clues together, though there was still a sore little space between {a.id} and {b.id} where the blaming had landed."
    )


def discover_creature(world: World, creature: Entity, creature_cfg: CreatureCfg, item: Entity) -> None:
    _do_dusting(world, creature)
    _do_take(world, creature, item, narrate=False)
    world.say(
        f"They found the answer at {creature_cfg.lair}: {creature_cfg.phrase}, only now it was grown so large it could have looked in a second-story window without standing on tiptoe."
    )
    world.say(creature_cfg.hiding_line)
    world.say(creature_cfg.calm_line)


def realize(world: World, accuser: Entity, accused: Entity, creature_cfg: CreatureCfg) -> None:
    accuser.memes["shame"] += 1
    accuser.memes["blame"] = 0.0
    world.say(
        f"{accuser.id} stared, then turned red clear to the ears. "
        f'"It was not {accused.id} at all," {accuser.pronoun()} whispered. '
        f'"The chy dust changed the {creature_cfg.label} and sent us chasing the wrong idea."'
    )


def calm_and_fix(world: World, a: Entity, b: Entity, creature: Entity, reversal: Reversal, place: Place) -> None:
    for kid in (a, b):
        kid.memes["bravery"] += 1
    world.say(
        f"{a.id} and {b.id} moved closer together again. Working side by side, they {reversal.act}."
    )
    _do_wash(world, creature, reversal)
    world.say(
        f"The creature blinked in surprise, gave one ordinary little sound, and stood in the wet grass as gentle as any yard animal near {place.home}."
    )


def recover_item(world: World, item: Entity, a: Entity, b: Entity) -> None:
    item.meters["missing"] = 0.0
    item.owner = ""
    item.meters["recovered"] += 1
    world.say(
        f"{b.id} picked up the {item.label}, and {a.id} brushed the last sparkly dust from it. Nothing was broken after all, just misplaced in a very big way."
    )


def apologize(world: World, accuser: Entity, accused: Entity) -> None:
    accuser.memes["sorry"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{accuser.id} swallowed hard. "I am sorry I blamed you," {accuser.pronoun()} said. '
        f'"I was scared about the missing keepsake, and I spoke before I knew the truth."'
    )
    world.say(
        f'{accused.id} nodded. "I was hurt," {accused.pronoun()} said, "but I know you were worried. We solved it better together."'
    )


def ending(world: World, a: Entity, b: Entity, keepsake: Keepsake) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"Before sundown they used the {keepsake.label} together again. {keepsake.ending_line} "
        f"And because the mystery had been solved honestly, the friendship sounded bright again too."
    )
    world.say(
        f"From then on, whenever chy dust shimmered on the ground, {a.id} and {b.id} checked the clues first and their tempers second. "
        f"That is how they stayed friends in a country where even the wind could tell a tall tale."
    )


def tell(
    place: Place,
    keepsake: Keepsake,
    creature_cfg: CreatureCfg,
    reversal: Reversal,
    accuser_name: str = "Ben",
    accuser_gender: str = "boy",
    accused_name: str = "Lily",
    accused_gender: str = "girl",
    elder_type: str = "mother",
    trait: str = "quick",
) -> World:
    world = World(place)
    accuser = world.add(Entity(
        id=accuser_name,
        kind="character",
        type=accuser_gender,
        role="accuser",
        traits=[trait],
        label=accuser_name,
    ))
    accused = world.add(Entity(
        id=accused_name,
        kind="character",
        type=accused_gender,
        role="accused",
        traits=["steady"],
        label=accused_name,
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
    ))
    creature = world.add(Entity(
        id="creature",
        type=creature_cfg.label,
        label=creature_cfg.label,
        phrase=creature_cfg.phrase,
        tags=set(creature_cfg.tags),
    ))
    item = world.add(Entity(
        id="keepsake",
        type="keepsake",
        label=keepsake.label,
        phrase=keepsake.phrase,
        tags=set(keepsake.tags),
    ))

    setup_play(world, accuser, accused, keepsake)
    world.para()
    dust_night(world)
    missing_and_blame(world, accuser, accused, item, elder)
    clue_scene(world, keepsake, creature_cfg)
    follow_trail(world, accuser, accused)
    world.para()
    discover_creature(world, creature, creature_cfg, item)
    realize(world, accuser, accused, creature_cfg)
    world.para()
    calm_and_fix(world, accuser, accused, creature, reversal, place)
    recover_item(world, item, accuser, accused)
    apologize(world, accuser, accused)
    world.para()
    ending(world, accuser, accused, keepsake)

    world.facts.update(
        place=place,
        keepsake_cfg=keepsake,
        creature_cfg=creature_cfg,
        reversal=reversal,
        accuser=accuser,
        accused=accused,
        elder=elder,
        creature=creature,
        keepsake=item,
        mystery_solved=item.meters["recovered"] >= THRESHOLD,
        transformed=creature.meters["washed"] >= THRESHOLD,
        reconciled=accused.memes["forgive"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "apology": [
        (
            "Why does saying sorry help after blaming someone unfairly?",
            "Saying sorry shows that you know you hurt someone and want to make it right. A real apology can help trust start growing again."
        )
    ],
    "mystery": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you figure out what happened. Footprints, dust, and missing things can all be clues."
        )
    ],
    "transformation": [
        (
            "What does transformation mean in a story?",
            "Transformation means something changes into a different state or shape. In this story world, chy dust can make an animal grow giant until the dust is washed away."
        )
    ],
    "magpie": [
        (
            "Why might a magpie pick up a shiny thing?",
            "Some birds notice sparkling objects and carry them off because they catch the eye. A bright bell can look like treasure to a curious magpie."
        )
    ],
    "goat": [
        (
            "Why do goats get tangled in cloth or string sometimes?",
            "Goats are curious and like to nibble or nose interesting things. A scarf or string can catch on a horn while the goat is poking at it."
        )
    ],
    "calf": [
        (
            "Why would a calf nose a bright scarf or bell?",
            "A calf explores with its nose and is curious about new things. A bright keepsake can seem interesting even if the calf does not mean any harm."
        )
    ],
    "barrel": [
        (
            "What is a rain barrel?",
            "A rain barrel is a big container that saves rainwater. People can use that water for cleaning or watering plants."
        )
    ],
    "pump": [
        (
            "What does a hand pump do?",
            "A hand pump pulls water up when someone works the handle. It can send out a strong splash of water."
        )
    ],
    "creek": [
        (
            "What is a creek?",
            "A creek is a small stream of moving water. It can rinse mud or dust away."
        )
    ],
    "bell": [
        (
            "What is a bell used for?",
            "A bell makes a clear ringing sound when it is shaken or tapped. People use bells to call, signal, or celebrate."
        )
    ],
    "kite": [
        (
            "Why does a kite need string?",
            "The string lets you hold the kite while the wind lifts it. Without string, the kite would just fly away."
        )
    ],
    "scarf": [
        (
            "What is a scarf?",
            "A scarf is a long piece of cloth people can wear or wave. It flutters easily in the wind."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "mystery",
    "transformation",
    "apology",
    "magpie",
    "goat",
    "calf",
    "barrel",
    "pump",
    "creek",
    "bell",
    "kite",
    "scarf",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["accuser"]
    b = f["accused"]
    keepsake = f["keepsake_cfg"]
    creature = f["creature_cfg"]
    place = f["place"]
    return [
        (
            f'Write a tall-tale story for a 3-to-5-year-old that includes the words "chy" and "dust", '
            f'and uses a missing {keepsake.label}, a clue trail, and a reconciliation.'
        ),
        (
            f"Tell a gentle mystery where {a.id} wrongly blames {b.id} when a {keepsake.label} disappears near {place.label}, "
            f"but the real culprit is a dust-transformed {creature.label}."
        ),
        (
            f"Write a child-facing tall tale in which huge clues lead two friends to solve a mystery, wash off magical chy dust, "
            f"and make up after an unfair accusation."
        ),
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two friends"
    if a.type == "girl" and b.type == "girl":
        return "two friends"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["accuser"]
    b = f["accused"]
    elder = f["elder"]
    keepsake = f["keepsake_cfg"]
    creature = f["creature_cfg"]
    reversal = f["reversal"]
    place = f["place"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, who lose a shared {keepsake.label} and have to solve a mystery together."
        ),
        (
            f"What was missing?",
            f"The missing thing was their {keepsake.label}. It mattered because they used it in their game and both cared about it."
        ),
        (
            f"Why did {a.id} hurt {b.id}'s feelings?",
            f"{a.id} saw the keepsake was gone and blamed {b.id} before knowing the truth. That unfair guess made {b.id} feel hurt and pushed the friends apart for a while."
        ),
        (
            "What clues showed this was a mystery to solve?",
            f"They found huge {creature.print_name} and a sparkling trail of chy dust. Those clues showed that something strange had happened, not an ordinary stealing."
        ),
        (
            f"What had really happened to the {creature.label}?",
            f"The {creature.label} had been changed by chy dust and grown giant. In that transformed state, it carried off the {keepsake.label} because it liked something {keepsake.tag}."
        ),
        (
            f"How did the children fix the transformation?",
            f"They worked together and used the {reversal.label}. {reversal.qa_text}, and that made the creature small and gentle again."
        ),
        (
            f"How did {a.id} and {b.id} reconcile?",
            f"{a.id} apologized for blaming {b.id} unfairly, and {b.id} answered honestly about being hurt. They came back together by solving the mystery side by side and speaking kindly at the end."
        ),
        (
            "How did the story end?",
            f"It ended with the keepsake safe again and the friendship mended. Near {place.label}, they used it together and knew to follow clues before blaming anyone."
        ),
    ]
    if elder is not None:
        qa.append((
            f"What did the {elder.label_word} do when the keepsake went missing?",
            f"The {elder.label_word} stayed calm and pointed the children toward the strange clues instead of the quarrel. That helped turn a fight into a mystery they could solve."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"mystery", "transformation", "apology"}
    creature = f["creature_cfg"]
    place = f["place"]
    keepsake = f["keepsake_cfg"]
    if creature.id in KNOWLEDGE:
        tags.add(creature.id)
    if keepsake.id == "silver_bell":
        tags.add("bell")
    elif keepsake.id == "kite_spool":
        tags.add("kite")
    elif keepsake.id == "red_scarf":
        tags.add("scarf")
    for tag in place.tags | f["reversal"].tags:
        if tag in KNOWLEDGE:
            tags.add(tag)

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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
wants(C, K) :- creature(C), keepsake(K), likes(C, T), keep_tag(K, T).
can_reverse(P, R) :- place(P), reversal(R), has_source(P, S), needs_source(R, S).

valid(P, K, C, R) :- place(P), keepsake(K), creature(C), reversal(R),
                     wants(C, K), can_reverse(P, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for source in sorted(place.sources):
            lines.append(asp.fact("has_source", pid, source))
    for kid, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", kid))
        lines.append(asp.fact("keep_tag", kid, keepsake.tag))
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        for tag in sorted(creature.likes):
            lines.append(asp.fact("likes", cid, tag))
    for rid, reversal in REVERSALS.items():
        lines.append(asp.fact("reversal", rid))
        lines.append(asp.fact("needs_source", rid, reversal.source))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(
        place="prairie",
        keepsake="silver_bell",
        creature="magpie",
        reversal="pump_spray",
        accuser="Ben",
        accuser_gender="boy",
        accused="Lily",
        accused_gender="girl",
        elder="mother",
        trait="quick",
    ),
    StoryParams(
        place="canyon",
        keepsake="red_scarf",
        creature="calf",
        reversal="creek_rinse",
        accuser="Zoe",
        accuser_gender="girl",
        accused="Max",
        accused_gender="boy",
        elder="father",
        trait="bold",
    ),
    StoryParams(
        place="fairground",
        keepsake="kite_spool",
        creature="goat",
        reversal="barrel_bath",
        accuser="Sam",
        accuser_gender="boy",
        accused="Mia",
        accused_gender="girl",
        elder="mother",
        trait="stubborn",
    ),
    StoryParams(
        place="prairie",
        keepsake="red_scarf",
        creature="goat",
        reversal="barrel_bath",
        accuser="Ella",
        accuser_gender="girl",
        accused="Nora",
        accused_gender="girl",
        elder="father",
        trait="careful",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale mystery storyworld: chy dust, a missing keepsake, a transformation, and reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--reversal", choices=REVERSALS)
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place is not None and args.reversal is not None:
        place = PLACES[args.place]
        reversal = REVERSALS[args.reversal]
        if not place_supports(place, reversal):
            keepsake = KEEPSAKES[args.keepsake] if args.keepsake else next(iter(KEEPSAKES.values()))
            creature = CREATURES[args.creature] if args.creature else next(iter(CREATURES.values()))
            raise StoryError(explain_rejection(place, keepsake, creature, reversal))
    if args.keepsake is not None and args.creature is not None:
        keepsake = KEEPSAKES[args.keepsake]
        creature = CREATURES[args.creature]
        place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        reversal = REVERSALS[args.reversal] if args.reversal else next(iter(REVERSALS.values()))
        if not wants_keepsake(creature, keepsake):
            raise StoryError(explain_rejection(place, keepsake, creature, reversal))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.keepsake is None or c[1] == args.keepsake)
        and (args.creature is None or c[2] == args.creature)
        and (args.reversal is None or c[3] == args.reversal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, keepsake_id, creature_id, reversal_id = rng.choice(sorted(combos))
    accuser, accuser_gender = _pick_kid(rng)
    accused, accused_gender = _pick_kid(rng, avoid=accuser)
    elder = args.elder or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        keepsake=keepsake_id,
        creature=creature_id,
        reversal=reversal_id,
        accuser=accuser,
        accuser_gender=accuser_gender,
        accused=accused,
        accused_gender=accused_gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Unknown keepsake: {params.keepsake})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.reversal not in REVERSALS:
        raise StoryError(f"(Unknown reversal: {params.reversal})")

    place = PLACES[params.place]
    keepsake = KEEPSAKES[params.keepsake]
    creature = CREATURES[params.creature]
    reversal = REVERSALS[params.reversal]
    if not wants_keepsake(creature, keepsake) or not place_supports(place, reversal):
        raise StoryError(explain_rejection(place, keepsake, creature, reversal))

    world = tell(
        place=place,
        keepsake=keepsake,
        creature_cfg=creature,
        reversal=reversal,
        accuser_name=params.accuser,
        accuser_gender=params.accuser_gender,
        accused_name=params.accused,
        accused_gender=params.accused_gender,
        elder_type=params.elder,
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


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    smoke_cases = list(CURATED)
    try:
        args = build_parser().parse_args([])
        auto = resolve_params(args, random.Random(123))
        auto.seed = 123
        smoke_cases.append(auto)
    except StoryError as err:
        rc = 1
        print(f"SMOKE FAIL: resolve_params raised {err}")

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            if sample.world is None:
                raise StoryError("missing world model on sample")
            if "chy dust" not in sample.story:
                raise StoryError("story omitted required words")
            print(f"OK: smoke story {i} generated.")
        except Exception as err:
            rc = 1
            print(f"SMOKE FAIL on case {i}: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, keepsake, creature, reversal) combos:\n")
        for place, keepsake, creature, reversal in combos:
            print(f"  {place:10} {keepsake:12} {creature:8} {reversal}")
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
            header = f"### {p.accuser} and {p.accused}: {p.keepsake} / {p.creature} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
