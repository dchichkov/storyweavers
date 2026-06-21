#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/haybine_furnish_extinguish_icy_sidewalk_flashback_reconciliation.py
================================================================================================

A standalone storyworld for a small winter whodunit on an icy sidewalk.

Seed requirements rebuilt as simulation:
- required words: haybine, furnish, extinguish
- setting: icy sidewalk
- features: Flashback, Reconciliation
- style: Whodunit

Premise
-------
Two children help furnish an icy sidewalk with winter lights. Then one small
lantern is suddenly extinguished. The detective-minded child jumps to the wrong
conclusion, studies the clues, has a flashback that explains what really
happened, and then makes peace with the accused friend or sibling. The ending
proves the change by showing a safer, steadier kind of light glowing on the same
icy sidewalk where the argument began.

Reasonableness constraint
-------------------------
Not every lantern and cause make sense together, and not every fix genuinely
solves the problem.

- A strong wind can extinguish an open paper lantern, but not a shielded jar
  lantern.
- A slip on ice or a puppy tugging a ribbon can upset any lantern.
- A repair is only valid when it specifically guards against the real cause:
  glass helps against wind, an electric candle helps against wind or pet bumps,
  and a wall-mounted porch lamp solves all three by moving the light out of the
  danger zone.

The world model itself enforces those choices, and the inline ASP twin mirrors
the same gate.

Run it
------
    python storyworlds/worlds/gpt-5.4/haybine_furnish_extinguish_icy_sidewalk_flashback_reconciliation.py
    python storyworlds/worlds/gpt-5.4/haybine_furnish_extinguish_icy_sidewalk_flashback_reconciliation.py --cause wind --prop paper_lantern
    python storyworlds/worlds/gpt-5.4/haybine_furnish_extinguish_icy_sidewalk_flashback_reconciliation.py --prop jar_lantern --cause wind
    python storyworlds/worlds/gpt-5.4/haybine_furnish_extinguish_icy_sidewalk_flashback_reconciliation.py --all --qa
    python storyworlds/worlds/gpt-5.4/haybine_furnish_extinguish_icy_sidewalk_flashback_reconciliation.py --verify
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

# Make the shared result containers importable when this script is run directly
# from its nested directory under storyworlds/worlds/gpt-5.4/.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class MysteryProp:
    id: str
    label: str
    phrase: str
    flame_word: str
    shielded: bool = False
    steady: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    actor: str
    clue: str
    track: str
    flashback: str
    accusation_hint: str
    affects_shielded: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    protects_from: set[str] = field(default_factory=set)
    furnish_line: str = ""
    ending_line: str = ""
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


def _r_dark_worry(world: World) -> list[str]:
    lamp = world.entities.get("lamp")
    if lamp is None or lamp.meters["extinguished"] < THRESHOLD:
        return []
    sig = ("dark_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if "sidewalk" in world.entities:
        world.get("sidewalk").meters["darkness"] += 1
        world.get("sidewalk").meters["mystery"] += 1
    for ent in world.entities.values():
        if ent.role in {"detective", "suspect"}:
            ent.memes["worry"] += 1
    return ["__dark__"]


def _r_accusation_hurts(world: World) -> list[str]:
    detective = next((e for e in world.entities.values() if e.role == "detective"), None)
    suspect = next((e for e in world.entities.values() if e.role == "suspect"), None)
    if detective is None or suspect is None:
        return []
    if detective.memes["accusing"] < THRESHOLD:
        return []
    sig = ("accusation_hurts",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["hurt"] += 1
    detective.memes["certainty"] += 1
    return ["__hurt__"]


def _r_truth_relieves(world: World) -> list[str]:
    detective = next((e for e in world.entities.values() if e.role == "detective"), None)
    suspect = next((e for e in world.entities.values() if e.role == "suspect"), None)
    if detective is None or suspect is None:
        return []
    if detective.memes["truth"] < THRESHOLD or detective.memes["apology"] < THRESHOLD:
        return []
    sig = ("truth_relieves",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["hurt"] = 0.0
    suspect.memes["relief"] += 1
    detective.memes["relief"] += 1
    detective.memes["trust"] += 1
    suspect.memes["trust"] += 1
    return ["__reconcile__"]


CAUSAL_RULES = [
    Rule(name="dark_worry", tag="mystery", apply=_r_dark_worry),
    Rule(name="accusation_hurts", tag="social", apply=_r_accusation_hurts),
    Rule(name="truth_relieves", tag="social", apply=_r_truth_relieves),
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
        for sent in produced:
            world.say(sent)
    return produced


def hazard_at_risk(prop: MysteryProp, cause: Cause) -> bool:
    if prop.shielded and not cause.affects_shielded:
        return False
    return True


def compatible_fix(cause: Cause, fix: Fix) -> bool:
    return cause.id in fix.protects_from


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for prop_id, prop in PROPS.items():
        for cause_id, cause in CAUSES.items():
            if not hazard_at_risk(prop, cause):
                continue
            for fix_id, fix in FIXES.items():
                if compatible_fix(cause, fix):
                    combos.append((prop_id, cause_id, fix_id))
    return sorted(combos)


def predict_disturbance(world: World, prop: MysteryProp, cause: Cause) -> dict:
    sim = world.copy()
    lamp = sim.get("lamp")
    if hazard_at_risk(prop, cause):
        lamp.meters["extinguished"] += 1
        propagate(sim, narrate=False)
    return {
        "extinguished": lamp.meters["extinguished"] >= THRESHOLD,
        "darkness": sim.get("sidewalk").meters["darkness"],
    }


def introduce(world: World, detective: Entity, suspect: Entity, parent: Entity,
              prop: MysteryProp) -> None:
    world.say(
        f"By late afternoon, {detective.id} and {suspect.id} were out on the icy sidewalk "
        f"with {detective.pronoun('possessive')} {parent.label_word}, trying to furnish the "
        f"front walk with winter light."
    )
    world.say(
        f"They set down {prop.phrase} beside the snowbank, and its {prop.flame_word} made a "
        f"small warm dot against all the blue ice."
    )
    world.say(
        f"{detective.id} loved mysteries, so {detective.pronoun()} whispered that the walk "
        f"looked like the beginning of a very fine case."
    )


def mystery_strikes(world: World, detective: Entity, suspect: Entity, prop: MysteryProp,
                    cause: Cause) -> None:
    pred = predict_disturbance(world, prop, cause)
    world.facts["predicted_darkness"] = pred["darkness"]
    lamp = world.get("lamp")
    lamp.meters["extinguished"] += 1
    lamp.meters["disturbed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then, without any warning, the little light gave a shiver and went out. "
        f"Someone -- or something -- had managed to extinguish it."
    )
    world.say(
        f"On the icy sidewalk, {detective.id} spotted {cause.accusation_hint} near the lantern "
        f"and narrowed {detective.pronoun('possessive')} eyes."
    )
    detective.memes["accusing"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Aha," {detective.pronoun()} said. "That looks suspicious."'
    )
    world.say(
        f"{suspect.id} blinked in surprise. {cause.clue}"
    )


def accuse(world: World, detective: Entity, suspect: Entity) -> None:
    world.say(
        f'"Did you do it?" {detective.id} asked. It was a soft question, but it still landed '
        f"hard."
    )
    if suspect.memes["hurt"] >= THRESHOLD:
        world.say(
            f'{suspect.id} drew back and shook {suspect.pronoun("possessive")} head. '
            f'"No. I was helping."'
        )


def inspect(world: World, detective: Entity, cause: Cause) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"But good detectives do not stop at the first guess. {detective.id} crouched low and "
        f"studied the ice."
    )
    world.say(
        f"{detective.pronoun().capitalize()} saw {cause.track}."
    )
    world.say(
        "The mark curled in a funny hook instead of pointing straight at the lantern."
    )


def flashback(world: World, detective: Entity, cause: Cause) -> None:
    detective.memes["memory"] += 1
    detective.memes["truth"] += 1
    world.say(
        f"Then a flashback flickered through {detective.pronoun('possessive')} mind."
    )
    world.say(
        f"Earlier that week, Grandpa had pointed to a rusty haybine resting by the shed and "
        f"shown {detective.pronoun('object')} one bent tooth on its wheel. The scratch on the "
        f"ice had the same hooked shape."
    )
    world.say(cause.flashback)
    world.say(
        f"All at once, the case changed shape. This was not a mean trick at all."
    )


def reveal(world: World, detective: Entity, suspect: Entity, cause: Cause, parent: Entity) -> None:
    world.say(
        f'"Wait," {detective.id} said. "{cause.label.capitalize()} did it."'
    )
    if cause.actor == "weather":
        world.say(
            f"{parent.label_word.capitalize()} looked at the drifting snow and nodded. "
            f'"The wind caught it," {parent.pronoun()} said.'
        )
    elif cause.actor == "pet":
        world.say(
            f"{parent.label_word.capitalize()} followed the tiny prints and smiled at the puppy "
            f"at the end of the ribbon. \"There is our culprit,\" {parent.pronoun()} said."
        )
    else:
        world.say(
            f"{parent.label_word.capitalize()} touched the long scrape with a glove. "
            f'"That was a slip, not a shove," {parent.pronoun()} said.'
        )
    world.facts["truth_cause"] = cause.id
    if suspect.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{suspect.id} let out the breath {suspect.pronoun()} had been holding."
        )


def apologize(world: World, detective: Entity, suspect: Entity) -> None:
    detective.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I am sorry I blamed you," {detective.id} said. "I hurried past the clues."'
    )
    world.say(
        f'{suspect.id} rubbed {suspect.pronoun("possessive")} mitten on the coat and nodded. '
        f'"I was upset," {suspect.pronoun()} admitted, "but I am glad you kept looking."'
    )


def repair(world: World, detective: Entity, suspect: Entity, parent: Entity,
           fix: Fix) -> None:
    lamp = world.get("lamp")
    lamp.meters["extinguished"] = 0.0
    lamp.meters["steady"] += 1
    world.get("sidewalk").meters["darkness"] = 0.0
    world.say(
        f"Together they chose {fix.phrase}. {fix.furnish_line}"
    )
    world.say(
        f"Soon the light stood steady again, and the icy sidewalk no longer felt like a place "
        f"full of blame."
    )
    world.say(
        fix.ending_line
    )


def tell(prop: MysteryProp, cause: Cause, fix: Fix,
         detective_name: str = "Nora", detective_gender: str = "girl",
         suspect_name: str = "Ben", suspect_gender: str = "boy",
         parent_type: str = "mother", relation: str = "siblings",
         pet_name: str = "Pip") -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        traits=["observant"],
        attrs={"relation": relation},
    ))
    suspect = world.add(Entity(
        id=suspect_name,
        kind="character",
        type=suspect_gender,
        role="suspect",
        traits=["helpful"],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(id="sidewalk", type="place", label="icy sidewalk"))
    lamp = world.add(Entity(
        id="lamp",
        type="lantern",
        label=prop.label,
        phrase=prop.phrase,
        tags=set(prop.tags),
    ))
    if cause.actor == "pet":
        world.add(Entity(
            id="pet",
            kind="character",
            type="animal",
            label=pet_name,
            phrase=pet_name,
            role="pet",
        ))
    world.facts["pet_name"] = pet_name
    world.facts["relation"] = relation

    introduce(world, detective, suspect, parent, prop)
    world.para()
    mystery_strikes(world, detective, suspect, prop, cause)
    accuse(world, detective, suspect)
    world.para()
    inspect(world, detective, cause)
    flashback(world, detective, cause)
    reveal(world, detective, suspect, cause, parent)
    world.para()
    apologize(world, detective, suspect)
    repair(world, detective, suspect, parent, fix)

    world.facts.update(
        detective=detective,
        suspect=suspect,
        parent=parent,
        prop=prop,
        cause=cause,
        fix=fix,
        lantern=lamp,
        mystery=lamp.meters["disturbed"] >= THRESHOLD,
        reconciled=detective.memes["apology"] >= THRESHOLD and detective.memes["truth"] >= THRESHOLD,
    )
    return world


PROPS = {
    "paper_lantern": MysteryProp(
        id="paper_lantern",
        label="paper lantern",
        phrase="a paper lantern with a tiny candle inside",
        flame_word="little flame",
        shielded=False,
        steady=False,
        tags={"lantern", "candle"},
    ),
    "tin_lantern": MysteryProp(
        id="tin_lantern",
        label="tin lantern",
        phrase="a punched-tin lantern with star holes",
        flame_word="pinprick glow",
        shielded=False,
        steady=True,
        tags={"lantern", "candle"},
    ),
    "jar_lantern": MysteryProp(
        id="jar_lantern",
        label="jar lantern",
        phrase="a jar lantern with the flame tucked behind glass",
        flame_word="gold bead of light",
        shielded=True,
        steady=True,
        tags={"lantern", "glass"},
    ),
}

CAUSES = {
    "wind": Cause(
        id="wind",
        label="the wind",
        actor="weather",
        clue="The snow beside it was fanned into a tiny silver swirl.",
        track="a feathered sweep in the frost and a soft curve of blown snow",
        flashback="In the flashback, the same sharp gust came rushing around the corner of the house, lifting a loose scarf end and making every porch ribbon jump. If it could toss ribbons, it could certainly snuff a small flame.",
        accusation_hint="a messy swirl of snow",
        affects_shielded=False,
        tags={"wind", "weather"},
    ),
    "slip": Cause(
        id="slip",
        label="a slippery stumble",
        actor="child",
        clue="There was a long heel scrape beside the base and one gray mitten thread caught in the handle.",
        track="one sliding boot line, then a stop, as if someone had tried very hard not to fall",
        flashback="In the flashback, Ben had hurried over with more ribbon, his boot skidding on the ice. He had windmilled his arms, bumped the lantern by accident, and then caught himself before he dropped the spool.",
        accusation_hint="a boot scrape and a mitten thread",
        affects_shielded=True,
        tags={"ice", "slip"},
    ),
    "puppy": Cause(
        id="puppy",
        label="the puppy's leap",
        actor="pet",
        clue="Tiny pawprints danced around the lantern, and a ribbon end had been nibbled into a wet curl.",
        track="pawprints, pawprints, then a quick hop mark beside the light",
        flashback="In the flashback, little Pip had bounded after the fluttering ribbon, landed with both front paws near the lantern, and thumped it sideways with a happy wagging body.",
        accusation_hint="pawprints and a chewed ribbon",
        affects_shielded=True,
        tags={"pet", "puppy"},
    ),
}

FIXES = {
    "glass_cover": Fix(
        id="glass_cover",
        label="a glass wind cover",
        phrase="a glass wind cover around the light",
        protects_from={"wind"},
        furnish_line="Parent set it around the lantern, and the flame sat still instead of shivering.",
        ending_line="The children watched the protected glow shine on the ice, and the case ended with everyone shoulder to shoulder.",
        tags={"glass", "lantern"},
    ),
    "electric_candle": Fix(
        id="electric_candle",
        label="an electric candle",
        phrase="an electric candle inside the lantern",
        protects_from={"wind", "puppy"},
        furnish_line="When Parent clicked it on, the light came back without any little flame to blow out or knock away.",
        ending_line="Its safe glow painted a yellow oval on the icy sidewalk while the puppy sneezed at the cold and settled down at last.",
        tags={"electric_light", "battery"},
    ),
    "porch_lamp": Fix(
        id="porch_lamp",
        label="the porch lamp",
        phrase="the bright porch lamp and a high hook for the ribbon",
        protects_from={"wind", "slip", "puppy"},
        furnish_line="They moved the important light up by the door, where no sliding boot or wagging tail could reach it.",
        ending_line="Then the whole icy sidewalk shone from above, and the children walked under it with their feelings mended too.",
        tags={"porch_light", "safe_light"},
    ),
}


@dataclass
class StoryParams:
    prop: str
    cause: str
    fix: str
    detective: str
    detective_gender: str
    suspect: str
    suspect_gender: str
    parent: str
    relation: str
    pet_name: str = "Pip"
    seed: Optional[int] = None


GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ava", "Ella", "June", "Clara"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Finn", "Theo", "Jack", "Eli"]


CURATED = [
    StoryParams(
        prop="paper_lantern",
        cause="wind",
        fix="glass_cover",
        detective="Nora",
        detective_gender="girl",
        suspect="Ben",
        suspect_gender="boy",
        parent="mother",
        relation="siblings",
        pet_name="Pip",
    ),
    StoryParams(
        prop="tin_lantern",
        cause="slip",
        fix="porch_lamp",
        detective="June",
        detective_gender="girl",
        suspect="Max",
        suspect_gender="boy",
        parent="father",
        relation="friends",
        pet_name="Pip",
    ),
    StoryParams(
        prop="paper_lantern",
        cause="puppy",
        fix="electric_candle",
        detective="Theo",
        detective_gender="boy",
        suspect="Mia",
        suspect_gender="girl",
        parent="mother",
        relation="siblings",
        pet_name="Pip",
    ),
    StoryParams(
        prop="jar_lantern",
        cause="slip",
        fix="porch_lamp",
        detective="Ella",
        detective_gender="girl",
        suspect="Leo",
        suspect_gender="boy",
        parent="father",
        relation="friends",
        pet_name="Pip",
    ),
]


KNOWLEDGE = {
    "ice": [
        (
            "Why is an icy sidewalk slippery?",
            "Ice is smooth and hard, so shoes cannot grip it very well. That makes it easy for feet to slide."
        )
    ],
    "wind": [
        (
            "How can wind put out a candle?",
            "A candle flame needs a steady bit of hot air around it. A strong gust can blow that heat away and make the flame go out."
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light with some kind of cover or frame around it. People use lanterns outdoors when they want a small light they can carry or set down."
        )
    ],
    "glass": [
        (
            "Why does glass help protect a flame?",
            "Glass lets the light shine through while blocking moving air. That helps stop wind from reaching the flame."
        )
    ],
    "electric_light": [
        (
            "Why is an electric candle safer outside for children?",
            "An electric candle glows without a real flame. That means wind cannot blow it out the same way, and it does not make hot fire."
        )
    ],
    "porch_light": [
        (
            "Why is a porch lamp steadier than a little sidewalk light?",
            "A porch lamp is fixed high up and does not sit where boots, paws, or wind swirls around the ground. That makes it harder to bump or blow out."
        )
    ],
    "pet": [
        (
            "Why do puppies bump things by accident?",
            "Puppies are curious and quick, and they do not always know where their paws and tails are going. They can knock things over while they play."
        )
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means people make peace again after hurt feelings or an argument. They tell the truth, apologize, and choose to be close again."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "ice",
    "wind",
    "lantern",
    "glass",
    "electric_light",
    "porch_light",
    "pet",
    "reconciliation",
]


def pair_noun(detective: Entity, suspect: Entity, relation: str) -> str:
    if relation == "siblings":
        if detective.type == "girl" and suspect.type == "girl":
            return "two sisters"
        if detective.type == "boy" and suspect.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    suspect = f["suspect"]
    cause = f["cause"]
    prop = f["prop"]
    fix = f["fix"]
    return [
        f'Write a short child-facing whodunit on an icy sidewalk that includes the words "haybine", "furnish", and "extinguish".',
        f"Tell a winter mystery where {detective.id} thinks {suspect.id} put out a {prop.label}, but a flashback shows that {cause.label} was really to blame and the children reconcile.",
        f"Write a gentle detective story where an argument begins over a lantern on the ice and ends with an apology and {fix.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    suspect = f["suspect"]
    parent = f["parent"]
    prop = f["prop"]
    cause = f["cause"]
    fix = f["fix"]
    pair = pair_noun(detective, suspect, f.get("relation", "friends"))
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {detective.id} and {suspect.id}, and {detective.id}'s {parent.label_word}. They were trying to make the icy sidewalk look bright and welcoming."
        ),
        (
            "What was the mystery?",
            f"A light inside the {prop.label} suddenly went out on the icy sidewalk. That made {detective.id} think someone nearby had caused it."
        ),
        (
            f"Why did {detective.id} suspect {suspect.id} at first?",
            f"{detective.id} saw {cause.accusation_hint} near the lantern and made a quick guess. The clue looked suspicious before {detective.id} studied it more carefully."
        ),
        (
            "What did the flashback help explain?",
            f"The flashback showed what had happened just before the lantern went out. It helped {detective.id} understand that {cause.label}, not meanness, was the real cause."
        ),
        (
            "Why is the haybine mentioned in the story?",
            f"The curved mark on the ice reminded {detective.id} of a bent part on Grandpa's old haybine. That memory helped {detective.pronoun('object')} notice the shape of the true clue."
        ),
        (
            "How did the children reconcile?",
            f"{detective.id} apologized for blaming {suspect.id} too fast, and {suspect.id} told the truth about being hurt. They made peace by fixing the light together instead of arguing."
        ),
        (
            "How did the story end?",
            f"They chose {fix.phrase}, and the sidewalk glowed steadily again. The new light showed that both the mystery and the hurt feelings had been settled."
        ),
    ]
    if cause.id == "wind":
        qa.append(
            (
                "Was anybody secretly mean?",
                f"No. The wind was the culprit. The story feels like a whodunit, but the real answer is that nature made the trouble."
            )
        )
    elif cause.id == "slip":
        qa.append(
            (
                f"Did {suspect.id} mean to put the light out?",
                f"No. {suspect.id} slipped on the icy sidewalk and bumped the lantern by accident. The scrape on the ice showed it was a stumble, not a shove."
            )
        )
    else:
        qa.append(
            (
                "Who really disturbed the lantern?",
                f"The puppy did when it leaped after the ribbon. The pawprints and the flashback together solved the case."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"lantern", "ice", "reconciliation"}
    cause = world.facts["cause"]
    fix = world.facts["fix"]
    tags |= set(cause.tags)
    tags |= set(fix.tags)
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
    for ent in world.entities.values():
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
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(prop: MysteryProp, cause: Cause, fix: Optional[Fix] = None) -> str:
    if not hazard_at_risk(prop, cause):
        return (
            f"(No story: {cause.label} would not reasonably extinguish the {prop.label}. "
            f"A shielded jar lantern is protected from that kind of trouble.)"
        )
    if fix is not None and not compatible_fix(cause, fix):
        return (
            f"(No story: {fix.label} does not solve the problem caused by {cause.label}. "
            f"Pick a repair that truly guards against the real cause.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


ASP_RULES = r"""
hazard(P, C) :- prop(P), cause(C), not shielded(P).
hazard(P, C) :- prop(P), cause(C), shielded(P), affects_shielded(C).

compatible(C, F) :- fix(F), protects(F, C).
valid(P, C, F) :- hazard(P, C), compatible(C, F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if prop.shielded:
            lines.append(asp.fact("shielded", pid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        if cause.affects_shielded:
            lines.append(asp.fact("affects_shielded", cid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for c in sorted(fix.protects_from):
            lines.append(asp.fact("protects", fid, c))
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
            raise StoryError("empty story")
        if "haybine" not in sample.story or "furnish" not in sample.story or "extinguish" not in sample.story:
            raise StoryError("required seed words missing from smoke-test story")
        print("OK: generate() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        text = format_qa(sample)
        if not text.strip():
            raise StoryError("empty QA")
        print("OK: QA formatting smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"QA SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Winter whodunit storyworld: a light goes out on an icy sidewalk, a flashback solves the case, and the children reconcile."
    )
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (prop, cause, fix) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prop and args.cause:
        prop = PROPS[args.prop]
        cause = CAUSES[args.cause]
        if not hazard_at_risk(prop, cause):
            raise StoryError(explain_rejection(prop, cause))
    if args.prop and args.cause and args.fix:
        prop = PROPS[args.prop]
        cause = CAUSES[args.cause]
        fix = FIXES[args.fix]
        if not hazard_at_risk(prop, cause) or not compatible_fix(cause, fix):
            raise StoryError(explain_rejection(prop, cause, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.prop is None or combo[0] == args.prop)
        and (args.cause is None or combo[1] == args.cause)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    prop_id, cause_id, fix_id = rng.choice(combos)
    detective, dg = pick_child(rng)
    suspect, sg = pick_child(rng, avoid=detective)
    parent = args.parent or rng.choice(["mother", "father"])
    relation = args.relation or rng.choice(["siblings", "friends"])
    pet_name = "Pip"
    return StoryParams(
        prop=prop_id,
        cause=cause_id,
        fix=fix_id,
        detective=detective,
        detective_gender=dg,
        suspect=suspect,
        suspect_gender=sg,
        parent=parent,
        relation=relation,
        pet_name=pet_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.prop not in PROPS:
        raise StoryError(f"(Invalid prop: {params.prop})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Invalid cause: {params.cause})")
    if params.fix not in FIXES:
        raise StoryError(f"(Invalid fix: {params.fix})")

    prop = PROPS[params.prop]
    cause = CAUSES[params.cause]
    fix = FIXES[params.fix]
    if not hazard_at_risk(prop, cause):
        raise StoryError(explain_rejection(prop, cause))
    if not compatible_fix(cause, fix):
        raise StoryError(explain_rejection(prop, cause, fix))

    world = tell(
        prop=prop,
        cause=cause,
        fix=fix,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        suspect_name=params.suspect,
        suspect_gender=params.suspect_gender,
        parent_type=params.parent,
        relation=params.relation,
        pet_name=params.pet_name,
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
        print(f"{len(combos)} compatible (prop, cause, fix) combos:\n")
        for prop, cause, fix in combos:
            print(f"  {prop:14} {cause:8} {fix}")
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
            header = f"### {p.detective} investigates {p.cause} with {p.prop} ({p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
