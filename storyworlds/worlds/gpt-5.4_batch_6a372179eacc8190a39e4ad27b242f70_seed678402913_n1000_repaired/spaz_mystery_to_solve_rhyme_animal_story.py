#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/spaz_mystery_to_solve_rhyme_animal_story.py
======================================================================

A tiny animal-story world about a small mystery: one forest animal's treasured
thing is missing, another animal moved it for a good reason, and a pair of
rhyming clues leads to the answer.

The seed asked for:
- the word "spaz"
- a mystery to solve
- rhyme
- an animal-story feel

This world treats the mystery as a calm, child-facing puzzle. The missing item
is never stolen; it is moved to keep it safe from a simple threat like rain,
wind, ants, or mud. The detective follows concrete signs in the world model:
pawprints, leaf bits, mud specks, and the rhyme clues themselves. The story
always resolves with an ending image that proves what changed.

Run it
------
python storyworlds/worlds/gpt-5.4/spaz_mystery_to_solve_rhyme_animal_story.py
python storyworlds/worlds/gpt-5.4/spaz_mystery_to_solve_rhyme_animal_story.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/spaz_mystery_to_solve_rhyme_animal_story.py --all --qa
python storyworlds/worlds/gpt-5.4/spaz_mystery_to_solve_rhyme_animal_story.py --trace --seed 777
python storyworlds/worlds/gpt-5.4/spaz_mystery_to_solve_rhyme_animal_story.py --json
python storyworlds/worlds/gpt-5.4/spaz_mystery_to_solve_rhyme_animal_story.py --verify
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

SIZE_ORDER = {"tiny": 1, "small": 2, "medium": 3}
FOCUS_MIN = 2
KIND_TO_SPECIES = {
    "rabbit": "rabbit",
    "squirrel": "squirrel",
    "mouse": "mouse",
    "fox": "fox",
    "otter": "otter",
    "frog": "frog",
    "duck": "duck",
    "hedgehog": "hedgehog",
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def species(self) -> str:
        return KIND_TO_SPECIES.get(self.type, self.type)


@dataclass
class AnimalSpec:
    id: str
    species: str
    clue_mark: str
    move_style: str
    coat: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    size: str
    material: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Threat:
    id: str
    sign: str
    risk_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    fits_up_to: str
    protects: set[str] = field(default_factory=set)
    clue_thing: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ClueStyle:
    id: str
    line1_template: str
    line2_template: str
    follow_text: str
    focus: int
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    owner = world.get("owner")
    item = world.get("treasure")
    if item.attrs.get("location") == "missing":
        sig = ("worry", owner.id)
        if sig not in world.fired:
            world.fired.add(sig)
            owner.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_calm_search(world: World) -> list[str]:
    out: list[str] = []
    sleuth = world.get("sleuth")
    owner = world.get("owner")
    if sleuth.memes["focus"] >= THRESHOLD and owner.memes["worry"] >= THRESHOLD:
        sig = ("calm", owner.id)
        if sig not in world.fired:
            world.fired.add(sig)
            owner.memes["calm"] += 1
            owner.memes["worry"] = max(0.0, owner.memes["worry"] - 1.0)
            out.append("__calm__")
    return out


def _r_found_relief(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("treasure")
    owner = world.get("owner")
    mover = world.get("mover")
    if item.attrs.get("location") == "found":
        sig = ("relief", owner.id)
        if sig not in world.fired:
            world.fired.add(sig)
            owner.memes["relief"] += 1
            mover.memes["relief"] += 1
            owner.memes["joy"] += 1
            mover.memes["joy"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="worry", tag="emotion", apply=_r_worry),
    Rule(name="calm_search", tag="emotion", apply=_r_calm_search),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
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
    return [s for s in produced if not s.startswith("__")]


def fits(place: HidingPlace, treasure: Treasure) -> bool:
    return SIZE_ORDER[treasure.size] <= SIZE_ORDER[place.fits_up_to]


def protects(place: HidingPlace, threat: Threat) -> bool:
    return threat.id in place.protects


def clue_works(style: ClueStyle) -> bool:
    return style.focus >= FOCUS_MIN


def valid_combo(treasure: Treasure, threat: Threat, place: HidingPlace, style: ClueStyle) -> bool:
    return fits(place, treasure) and protects(place, threat) and clue_works(style)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for treasure_id, treasure in TREASURES.items():
        for threat_id, threat in THREATS.items():
            for place_id, place in HIDING_PLACES.items():
                for style_id, style in CLUE_STYLES.items():
                    if valid_combo(treasure, threat, place, style):
                        combos.append((treasure_id, threat_id, place_id, style_id))
    return sorted(combos)


def explain_combo_rejection(treasure: Treasure, threat: Threat, place: HidingPlace, style: ClueStyle) -> str:
    if not fits(place, treasure):
        return (
            f"(No story: {treasure.phrase} is too big for {place.phrase}. "
            f"The hiding place must be able to hold the missing item.)"
        )
    if not protects(place, threat):
        return (
            f"(No story: {place.phrase} would not keep the treasure safe from {threat.risk_text}. "
            f"The helper needs a sensible hiding place that actually fixes the problem.)"
        )
    if not clue_works(style):
        return (
            f"(No story: clue style '{style.id}' is too muddled for a fair mystery. "
            f"Pick a clue style with clear rhyming directions.)"
        )
    return "(No story: that combination does not make a reasonable mystery.)"


def predict_search(world: World, place_id: str, style_id: str) -> dict:
    sim = world.copy()
    sleuth = sim.get("sleuth")
    item = sim.get("treasure")
    style = CLUE_STYLES[style_id]
    if style.focus >= FOCUS_MIN:
        sleuth.memes["focus"] += 1
    if sim.facts.get("trace_mark") and sim.facts.get("trace_thing"):
        sleuth.meters["noticed_clues"] += 1
    if sim.facts.get("final_place") == place_id:
        item.attrs["location"] = "found"
        sleuth.meters["solved"] += 1
    propagate(sim, narrate=False)
    return {
        "solved": item.attrs.get("location") == "found",
        "focus": sleuth.memes["focus"],
    }


def line_text(template: str, world: World) -> str:
    f = world.facts
    return template.format(
        owner=f["owner"].id,
        sleuth=f["sleuth"].id,
        mover=f["mover"].id,
        treasure=f["treasure_cfg"].label,
        treasure_phrase=f["treasure_cfg"].phrase,
        place=f["place_cfg"].label,
        place_phrase=f["place_cfg"].phrase,
        clue_thing=f["place_cfg"].clue_thing,
        threat=f["threat_cfg"].id,
        threat_sign=f["threat_cfg"].sign,
        mark=f["trace_mark"],
        trace_thing=f["trace_thing"],
    )


def introduce(world: World) -> None:
    owner = world.get("owner")
    sleuth = world.get("sleuth")
    treasure = world.get("treasure")
    mover = world.get("mover")
    threat = world.facts["threat_cfg"]
    world.say(
        f"In the little green woods, {owner.id} the {owner.species} loved "
        f"{treasure.phrase}. {owner.pronoun('possessive').capitalize()} friend "
        f"{sleuth.id} the {sleuth.species} loved puzzles, while {mover.id} the "
        f"{mover.species} noticed every flutter and splatter in the weather."
    )
    world.say(
        f"That morning, the air felt busy with {threat.risk_text}, and the forest "
        f"smelled like moss, bark, and breakfast berries."
    )


def treasure_goes_missing(world: World) -> None:
    owner = world.get("owner")
    treasure = world.get("treasure")
    treasure.attrs["location"] = "missing"
    propagate(world, narrate=False)
    world.say(
        f"When {owner.id} came back to the stump table, {owner.pronoun('possessive')} "
        f"{treasure.label} was gone."
    )
    world.say(
        f'"My {treasure.label}!" cried {owner.id}. "{owner.pronoun("possessive").capitalize()} '
        f'favorite {treasure.use} has vanished!"'
    )


def calm_the_panic(world: World) -> None:
    owner = world.get("owner")
    sleuth = world.get("sleuth")
    sleuth.memes["focus"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{sleuth.id} touched {owner.id}\'s paw gently and said, '
        f'"Do not spaz. Use your eyes, be wise, and look for a clue or two."'
    )


def discover_first_clue(world: World) -> None:
    sleuth = world.get("sleuth")
    style = world.facts["style_cfg"]
    line1 = line_text(style.line1_template, world)
    line2 = line_text(style.line2_template, world)
    world.facts["clue_lines"] = (line1, line2)
    sleuth.meters["noticed_clues"] += 1
    world.say(
        f"On the stump lay a curled leaf with a tiny rhyme written in berry juice:"
    )
    world.say(f'"{line1}"')
    world.say(f'"{line2}"')


def follow_signs(world: World) -> None:
    sleuth = world.get("sleuth")
    owner = world.get("owner")
    style = world.facts["style_cfg"]
    trace_mark = world.facts["trace_mark"]
    trace_thing = world.facts["trace_thing"]
    sleuth.meters["tracking"] += 1
    world.say(
        f"{sleuth.id} read the rhyme again and looked around. Soon {sleuth.pronoun()} "
        f"saw {trace_mark} beside {trace_thing}."
    )
    world.say(style.follow_text.format(
        sleuth=sleuth.id,
        owner=owner.id,
        trace_mark=trace_mark,
        trace_thing=trace_thing,
    ))


def solve_mystery(world: World) -> None:
    item = world.get("treasure")
    place = world.facts["place_cfg"]
    mover = world.get("mover")
    owner = world.get("owner")
    threat = world.facts["threat_cfg"]
    item.attrs["location"] = "found"
    item.attrs["place"] = place.id
    world.facts["solved"] = True
    propagate(world, narrate=False)
    world.say(
        f"Behind {place.phrase}, they found the {item.label}, tucked snug and dry."
    )
    world.say(
        f"Just then {mover.id} scampered out and blinked. "
        f'"I moved it," {mover.pronoun()} admitted. "I saw {threat.sign}, and I did '
        f'not want {owner.id}\'s {item.label} to be spoiled."'
    )


def explain_kindness(world: World) -> None:
    owner = world.get("owner")
    mover = world.get("mover")
    place = world.facts["place_cfg"]
    threat = world.facts["threat_cfg"]
    treasure = world.get("treasure")
    mover.memes["care"] += 1
    world.say(
        f'{mover.id} pointed to {place.phrase}. "{place.label.capitalize()} keeps things safe '
        f'from {threat.id}, so I hid it there and left a rhyme to guide you."'
    )
    world.say(
        f"{owner.id}'s worried whiskers softened. {owner.pronoun('possessive').capitalize()} "
        f"{treasure.label} had not been stolen at all. It had been protected."
    )


def resolve(world: World) -> None:
    owner = world.get("owner")
    sleuth = world.get("sleuth")
    treasure = world.get("treasure")
    world.say(
        f'"You solved the mystery," said {owner.id}, hugging {sleuth.id}. '
        f'"And you kept my {treasure.label} safe," {owner.pronoun()} told {world.get("mover").id}.'
    )
    world.say(
        f"Soon the three friends sat together while {owner.id} used the {treasure.label}, "
        f"and the little rhyme note rested on the stump like a proud, red clue."
    )


def tell(
    *,
    owner_name: str,
    owner_species: str,
    sleuth_name: str,
    sleuth_species: str,
    mover_name: str,
    mover_species: str,
    treasure_id: str,
    threat_id: str,
    place_id: str,
    clue_style_id: str,
) -> World:
    world = World()
    treasure_cfg = TREASURES[treasure_id]
    threat_cfg = THREATS[threat_id]
    place_cfg = HIDING_PLACES[place_id]
    style_cfg = CLUE_STYLES[clue_style_id]
    owner_spec = ANIMAL_SPECS[owner_species]
    sleuth_spec = ANIMAL_SPECS[sleuth_species]
    mover_spec = ANIMAL_SPECS[mover_species]

    owner = world.add(Entity(
        id=owner_name,
        kind="character",
        type=owner_species,
        role="owner",
        traits=["fond", owner_spec.coat],
        tags=set(owner_spec.tags),
    ))
    sleuth = world.add(Entity(
        id=sleuth_name,
        kind="character",
        type=sleuth_species,
        role="sleuth",
        traits=["calm", "curious", sleuth_spec.coat],
        tags=set(sleuth_spec.tags),
    ))
    mover = world.add(Entity(
        id=mover_name,
        kind="character",
        type=mover_species,
        role="mover",
        traits=["helpful", mover_spec.coat],
        tags=set(mover_spec.tags),
    ))
    treasure = world.add(Entity(
        id="treasure",
        type="treasure",
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        attrs={"location": "stump"},
        tags=set(treasure_cfg.tags),
    ))

    world.facts.update(
        owner=owner,
        sleuth=sleuth,
        mover=mover,
        treasure_cfg=treasure_cfg,
        threat_cfg=threat_cfg,
        place_cfg=place_cfg,
        style_cfg=style_cfg,
        trace_mark=mover_spec.clue_mark,
        trace_thing=place_cfg.clue_thing,
        final_place=place_id,
        solved=False,
    )

    introduce(world)
    world.para()
    treasure_goes_missing(world)
    calm_the_panic(world)
    world.para()
    discover_first_clue(world)
    follow_signs(world)
    world.para()
    solve_mystery(world)
    explain_kindness(world)
    world.para()
    resolve(world)
    return world


ANIMAL_SPECS = {
    "rabbit": AnimalSpec(
        id="rabbit",
        species="rabbit",
        clue_mark="soft hop-marks",
        move_style="hopped",
        coat="velvet-eared",
        tags={"rabbit"},
    ),
    "squirrel": AnimalSpec(
        id="squirrel",
        species="squirrel",
        clue_mark="tiny claw-lines",
        move_style="scampered",
        coat="bushy-tailed",
        tags={"squirrel"},
    ),
    "mouse": AnimalSpec(
        id="mouse",
        species="mouse",
        clue_mark="pin-dot prints",
        move_style="scurried",
        coat="whiskery",
        tags={"mouse"},
    ),
    "fox": AnimalSpec(
        id="fox",
        species="fox",
        clue_mark="neat pawprints",
        move_style="padded",
        coat="copper-furred",
        tags={"fox"},
    ),
    "otter": AnimalSpec(
        id="otter",
        species="otter",
        clue_mark="damp slide-marks",
        move_style="slid",
        coat="slick-furred",
        tags={"otter"},
    ),
    "frog": AnimalSpec(
        id="frog",
        species="frog",
        clue_mark="little splash-dots",
        move_style="sprang",
        coat="bright-eyed",
        tags={"frog"},
    ),
    "duck": AnimalSpec(
        id="duck",
        species="duck",
        clue_mark="webbed prints",
        move_style="waddled",
        coat="feather-bright",
        tags={"duck"},
    ),
    "hedgehog": AnimalSpec(
        id="hedgehog",
        species="hedgehog",
        clue_mark="prickly shuffle-marks",
        move_style="trundled",
        coat="spiky",
        tags={"hedgehog"},
    ),
}

TREASURES = {
    "teacup": Treasure(
        id="teacup",
        label="acorn teacup",
        phrase="a painted acorn teacup",
        size="tiny",
        material="shell",
        use="tea-cup",
        tags={"cup"},
    ),
    "ribbon": Treasure(
        id="ribbon",
        label="red ribbon",
        phrase="a bright red ribbon",
        size="small",
        material="cloth",
        use="ribbon",
        tags={"ribbon"},
    ),
    "map": Treasure(
        id="map",
        label="berry map",
        phrase="a folded berry map",
        size="small",
        material="paper",
        use="map",
        tags={"map"},
    ),
    "drum": Treasure(
        id="drum",
        label="seed drum",
        phrase="a little seed drum",
        size="medium",
        material="wood",
        use="drum",
        tags={"drum"},
    ),
}

THREATS = {
    "rain": Threat(
        id="rain",
        sign="fat rain drops gathering on the leaves",
        risk_text="coming rain",
        tags={"rain", "weather"},
    ),
    "wind": Threat(
        id="wind",
        sign="a gusty wind teasing the grass",
        risk_text="gusty wind",
        tags={"wind", "weather"},
    ),
    "ants": Threat(
        id="ants",
        sign="a line of hungry ants near the stump",
        risk_text="hungry ants",
        tags={"ants"},
    ),
    "mud": Threat(
        id="mud",
        sign="slippery mud creeping around the roots",
        risk_text="slippery mud",
        tags={"mud"},
    ),
}

HIDING_PLACES = {
    "log": HidingPlace(
        id="log",
        label="hollow log",
        phrase="a dry hollow log",
        fits_up_to="medium",
        protects={"rain", "wind"},
        clue_thing="the mossy path",
        tags={"log"},
    ),
    "fern_basket": HidingPlace(
        id="fern_basket",
        label="fern basket",
        phrase="a woven fern basket under a broad leaf",
        fits_up_to="small",
        protects={"rain", "ants", "mud"},
        clue_thing="the fern patch",
        tags={"basket"},
    ),
    "reed_nest": HidingPlace(
        id="reed_nest",
        label="reed nest",
        phrase="a tucked reed nest by the pond",
        fits_up_to="tiny",
        protects={"wind", "ants"},
        clue_thing="the pond edge",
        tags={"nest"},
    ),
    "stone_nook": HidingPlace(
        id="stone_nook",
        label="stone nook",
        phrase="a stone nook beneath a root",
        fits_up_to="medium",
        protects={"rain", "wind", "ants", "mud"},
        clue_thing="the root arch",
        tags={"stone"},
    ),
}

CLUE_STYLES = {
    "moss": ClueStyle(
        id="moss",
        line1_template="If you seek the missing thing, do not stomp or toss;",
        line2_template="follow {mark} past {trace_thing}, and look beneath the moss.",
        follow_text="{sleuth} whispered the rhyme and led {owner} along the path, slowly and carefully.",
        focus=3,
        tags={"rhyme"},
    ),
    "pond": ClueStyle(
        id="pond",
        line1_template="If your heart feels hot and cross, pause and count to two;",
        line2_template="search where {trace_thing} mirrors sky, and the hidden thing waits for you.",
        follow_text="{sleuth} watched the ground and the waterline until the clue made sense.",
        focus=3,
        tags={"rhyme"},
    ),
    "root": ClueStyle(
        id="root",
        line1_template="Tiny signs are easy to miss when worry makes you scoot;",
        line2_template="follow {mark} by {trace_thing}, and peek beside the root.",
        follow_text="{sleuth} stayed calm, and that calm helped {owner} notice the little signs too.",
        focus=2,
        tags={"rhyme"},
    ),
    "muddle": ClueStyle(
        id="muddle",
        line1_template="Round and round the clovers go, maybe high and maybe low;",
        line2_template="guess a place and guess again, perhaps by leaf or stone.",
        follow_text="{sleuth} frowned because the rhyme was too muddled to guide anybody fairly.",
        focus=1,
        tags={"rhyme"},
    ),
}

OWNER_NAMES = ["Pip", "Mimi", "Tansy", "Nibbles", "Poppy", "Bramble"]
SLEUTH_NAMES = ["Nell", "Clover", "Moss", "Juniper", "Tad", "Hazel"]
MOVER_NAMES = ["Rill", "Pebble", "Thimble", "Reed", "Burr", "Puddle"]


@dataclass
class StoryParams:
    treasure: str
    threat: str
    place: str
    clue_style: str
    owner_name: str
    owner_species: str
    sleuth_name: str
    sleuth_species: str
    mover_name: str
    mover_species: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "rain": [(
        "Why do animals hide things from rain?",
        "Rain can soak paper, cloth, and small treasures. A dry place keeps them from getting soggy or spoiled."
    )],
    "wind": [(
        "Why can wind be a problem for light things?",
        "Wind can blow light things away or tumble them into dirty places. That is why a tucked nook can be safer."
    )],
    "ants": [(
        "Why would ants bother a forest treasure?",
        "Ants like crumbs and sweet smells, and they can swarm around a little object left out. A covered place keeps the item harder to reach."
    )],
    "mud": [(
        "Why is mud bad for a treasure?",
        "Mud can smear and stain things, and it can make them hard to use again. A dry hiding place keeps the treasure clean."
    )],
    "rhyme": [(
        "What is a rhyme?",
        "A rhyme uses words that sound alike, like moss and toss or root and scoot. Rhymes can help clues feel fun and easy to remember."
    )],
    "mystery": [(
        "What is a mystery?",
        "A mystery is a problem you solve by noticing clues and asking what happened. Good clues help you think instead of only guessing."
    )],
    "rabbit": [(
        "What is special about rabbits in stories?",
        "Story rabbits are often quick, gentle, and good at noticing little sounds in the grass. Their long ears make them feel alert and lively."
    )],
    "squirrel": [(
        "Why do squirrels make good hide-and-seek characters?",
        "Squirrels are small, nimble climbers who dart from place to place. That makes it believable when they tuck something somewhere safe."
    )],
    "mouse": [(
        "Why are mice often shown as careful?",
        "Mice are tiny, so story mice often survive by being quiet and noticing details. That makes them good clue-followers."
    )],
    "fox": [(
        "Why do foxes fit mystery stories?",
        "Foxes are often pictured as observant and clever in stories. A careful fox can spot tracks and signs others miss."
    )],
}

KNOWLEDGE_ORDER = [
    "mystery",
    "rhyme",
    "rain",
    "wind",
    "ants",
    "mud",
    "rabbit",
    "squirrel",
    "mouse",
    "fox",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner = f["owner"]
    sleuth = f["sleuth"]
    mover = f["mover"]
    treasure = f["treasure_cfg"]
    threat = f["threat_cfg"]
    return [
        (
            f'Write a short animal story for a 3-to-5-year-old that includes the word '
            f'"spaz", contains a small mystery, and uses a rhyming clue. The missing '
            f'object should be {treasure.phrase}.'
        ),
        (
            f"Tell a gentle forest mystery where {owner.id} loses {treasure.phrase}, "
            f"{sleuth.id} follows clues, and {mover.id} turns out to have hidden it to "
            f"protect it from {threat.id}."
        ),
        (
            f"Write a child-facing rhyme mystery in which worried {owner.species}s calm "
            f"down, notice tracks, and end with friendship stronger than before."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    owner = f["owner"]
    sleuth = f["sleuth"]
    mover = f["mover"]
    treasure = f["treasure_cfg"]
    threat = f["threat_cfg"]
    place = f["place_cfg"]
    line1, line2 = f.get("clue_lines", ("", ""))
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {owner.id} the {owner.species}, {sleuth.id} the {sleuth.species}, "
            f"and {mover.id} the {mover.species}. They are forest friends trying to solve a small mystery."
        ),
        (
            f"What went missing?",
            f"{owner.id}'s {treasure.label} went missing from the stump table. That made {owner.pronoun('object')} worry because it was {owner.pronoun('possessive')} favorite {treasure.use}."
        ),
        (
            f"Why did {sleuth.id} tell {owner.id}, 'Do not spaz'?",
            f"{sleuth.id} wanted {owner.id} to stop panicking and look carefully instead. Calm thinking helped them notice the clue and solve the mystery."
        ),
        (
            "What was the rhyming clue?",
            f'The note said, "{line1}" and "{line2}" It pointed them toward the right path instead of making them guess wildly.'
        ),
        (
            f"How was the mystery solved?",
            f"{sleuth.id} followed {f['trace_mark']} near {f['trace_thing']} and found the {treasure.label} behind {place.phrase}. The clue worked because the signs in the world matched the rhyme."
        ),
        (
            f"Why had {mover.id} moved the {treasure.label}?",
            f"{mover.id} saw {threat.sign} and wanted to protect it from {threat.id}. So the treasure was hidden for safety, not taken out of meanness."
        ),
        (
            "How did the story end?",
            f"It ended happily with the treasure safe, the mystery solved, and the friends sitting together again. The ending image shows that worry turned into relief and trust."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"mystery", "rhyme", f["threat_cfg"].id, f["owner"].species, f["sleuth"].species}
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        treasure="map",
        threat="rain",
        place="stone_nook",
        clue_style="moss",
        owner_name="Pip",
        owner_species="rabbit",
        sleuth_name="Hazel",
        sleuth_species="fox",
        mover_name="Reed",
        mover_species="squirrel",
        seed=1,
    ),
    StoryParams(
        treasure="ribbon",
        threat="wind",
        place="log",
        clue_style="root",
        owner_name="Mimi",
        owner_species="mouse",
        sleuth_name="Clover",
        sleuth_species="rabbit",
        mover_name="Pebble",
        mover_species="hedgehog",
        seed=2,
    ),
    StoryParams(
        treasure="teacup",
        threat="ants",
        place="reed_nest",
        clue_style="pond",
        owner_name="Tansy",
        owner_species="duck",
        sleuth_name="Nell",
        sleuth_species="mouse",
        mover_name="Burr",
        mover_species="frog",
        seed=3,
    ),
    StoryParams(
        treasure="drum",
        threat="mud",
        place="stone_nook",
        clue_style="moss",
        owner_name="Bramble",
        owner_species="otter",
        sleuth_name="Juniper",
        sleuth_species="fox",
        mover_name="Thimble",
        mover_species="hedgehog",
        seed=4,
    ),
]


ASP_RULES = r"""
fits(P, T) :- hiding_place(P), treasure(T), fits_up_to(P, PS), size(T, TS), size_rank(PS, PR), size_rank(TS, TR), TR <= PR.
protected(P, H) :- protects(P, H).
clear_clue(C) :- clue_style(C), focus(C, F), focus_min(M), F >= M.
valid(T, H, P, C) :- treasure(T), threat(H), hiding_place(P), clue_style(C), fits(P, T), protected(P, H), clear_clue(C).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for label, rank in sorted(SIZE_ORDER.items(), key=lambda x: x[1]):
        lines.append(asp.fact("size_rank", label, rank))
    lines.append(asp.fact("focus_min", FOCUS_MIN))
    for treasure_id, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", treasure_id))
        lines.append(asp.fact("size", treasure_id, treasure.size))
    for threat_id in THREATS:
        lines.append(asp.fact("threat", threat_id))
    for place_id, place in HIDING_PLACES.items():
        lines.append(asp.fact("hiding_place", place_id))
        lines.append(asp.fact("fits_up_to", place_id, place.fits_up_to))
        for threat_id in sorted(place.protects):
            lines.append(asp.fact("protects", place_id, threat_id))
    for clue_id, clue in CLUE_STYLES.items():
        lines.append(asp.fact("clue_style", clue_id))
        lines.append(asp.fact("focus", clue_id, clue.focus))
    return "\n".join(lines)


def asp_program(extra_show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra_show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between Python and ASP valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in asp:", sorted(clingo_set - python_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "spaz" not in sample.story:
            raise StoryError("smoke test failed: story missing text or required seed word")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story:
            raise StoryError("resolved sample rendered empty story")
        print("OK: default resolve/generate succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal-story mystery world with rhyming clues. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--treasure", choices=sorted(TREASURES))
    ap.add_argument("--threat", choices=sorted(THREATS))
    ap.add_argument("--place", choices=sorted(HIDING_PLACES))
    ap.add_argument("--clue-style", dest="clue_style", choices=sorted(CLUE_STYLES))
    ap.add_argument("--owner-species", choices=sorted(ANIMAL_SPECS))
    ap.add_argument("--sleuth-species", choices=sorted(ANIMAL_SPECS))
    ap.add_argument("--mover-species", choices=sorted(ANIMAL_SPECS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_distinct(rng: random.Random, pool: list[str], used: set[str]) -> str:
    choices = [name for name in pool if name not in used]
    if not choices:
        raise StoryError("(No story: ran out of distinct names for characters.)")
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treasure and args.threat and args.place and args.clue_style:
        treasure = TREASURES[args.treasure]
        threat = THREATS[args.threat]
        place = HIDING_PLACES[args.place]
        style = CLUE_STYLES[args.clue_style]
        if not valid_combo(treasure, threat, place, style):
            raise StoryError(explain_combo_rejection(treasure, threat, place, style))

    combos = [
        combo for combo in valid_combos()
        if (args.treasure is None or combo[0] == args.treasure)
        and (args.threat is None or combo[1] == args.threat)
        and (args.place is None or combo[2] == args.place)
        and (args.clue_style is None or combo[3] == args.clue_style)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    treasure_id, threat_id, place_id, clue_style_id = rng.choice(combos)

    owner_species = args.owner_species or rng.choice(sorted(ANIMAL_SPECS))
    sleuth_species = args.sleuth_species or rng.choice(sorted(ANIMAL_SPECS))
    mover_species = args.mover_species or rng.choice(sorted(ANIMAL_SPECS))

    used: set[str] = set()
    owner_name = _pick_distinct(rng, OWNER_NAMES, used)
    used.add(owner_name)
    sleuth_name = _pick_distinct(rng, SLEUTH_NAMES, used)
    used.add(sleuth_name)
    mover_name = _pick_distinct(rng, MOVER_NAMES, used)

    return StoryParams(
        treasure=treasure_id,
        threat=threat_id,
        place=place_id,
        clue_style=clue_style_id,
        owner_name=owner_name,
        owner_species=owner_species,
        sleuth_name=sleuth_name,
        sleuth_species=sleuth_species,
        mover_name=mover_name,
        mover_species=mover_species,
    )


def generate(params: StoryParams) -> StorySample:
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.threat not in THREATS:
        raise StoryError(f"(Unknown threat: {params.threat})")
    if params.place not in HIDING_PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.clue_style not in CLUE_STYLES:
        raise StoryError(f"(Unknown clue style: {params.clue_style})")
    if params.owner_species not in ANIMAL_SPECS:
        raise StoryError(f"(Unknown owner species: {params.owner_species})")
    if params.sleuth_species not in ANIMAL_SPECS:
        raise StoryError(f"(Unknown sleuth species: {params.sleuth_species})")
    if params.mover_species not in ANIMAL_SPECS:
        raise StoryError(f"(Unknown mover species: {params.mover_species})")

    treasure = TREASURES[params.treasure]
    threat = THREATS[params.threat]
    place = HIDING_PLACES[params.place]
    style = CLUE_STYLES[params.clue_style]
    if not valid_combo(treasure, threat, place, style):
        raise StoryError(explain_combo_rejection(treasure, threat, place, style))

    world = tell(
        owner_name=params.owner_name,
        owner_species=params.owner_species,
        sleuth_name=params.sleuth_name,
        sleuth_species=params.sleuth_species,
        mover_name=params.mover_name,
        mover_species=params.mover_species,
        treasure_id=params.treasure,
        threat_id=params.threat,
        place_id=params.place,
        clue_style_id=params.clue_style,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (treasure, threat, place, clue_style) combos:\n")
        for treasure, threat, place, clue_style in combos:
            print(f"  {treasure:8} {threat:5} {place:11} {clue_style}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        limit = max(args.n * 50, 50)
        while len(samples) < args.n and i < limit:
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
            header = (
                f"### {p.owner_name}, {p.sleuth_name}, and {p.mover_name}: "
                f"{p.treasure} / {p.threat} / {p.place}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
