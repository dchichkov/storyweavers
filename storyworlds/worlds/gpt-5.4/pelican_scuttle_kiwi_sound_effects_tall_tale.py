#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pelican_scuttle_kiwi_sound_effects_tall_tale.py
============================================================================

A standalone storyworld for a tall-tale style story with a pelican, a scuttling
kiwi, and lots of sound effects.

Premise
-------
A boastful pelican offers to move an absurdly large kiwi fruit for a little kiwi
bird. The route is troubled by one exaggerated obstacle, and the pair must find
a transport method that fits both the fruit and the hazard. Sometimes the
pelican's first plan is mighty enough; sometimes it wobbles until the kiwi's
small, quick scuttle turns the rescue into teamwork.

The world enforces common-sense constraints:
- a method must fit the route hazard,
- a method must support the fruit's transport need,
- low-sense methods are refused,
- if the chosen method is weaker than the hazard, the story turns into a
  teamwork ending instead of a smooth solo boast.

Run it
------
    python storyworlds/worlds/gpt-5.4/pelican_scuttle_kiwi_sound_effects_tall_tale.py
    python storyworlds/worlds/gpt-5.4/pelican_scuttle_kiwi_sound_effects_tall_tale.py --cargo golden_kiwi --hazard gust
    python storyworlds/worlds/gpt-5.4/pelican_scuttle_kiwi_sound_effects_tall_tale.py --method hop_bump
    python storyworlds/worlds/gpt-5.4/pelican_scuttle_kiwi_sound_effects_tall_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/pelican_scuttle_kiwi_sound_effects_tall_tale.py --verify
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
        male = {"boy", "man", "pelican"}
        female = {"girl", "woman", "kiwi"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    finish: str
    route_word: str
    echo: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    boast: str
    need: str
    size: int
    sound: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    route: str
    threat: str
    sound: str
    guards: set[str] = field(default_factory=set)
    severity: int = 2
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    power: int
    guards: set[str] = field(default_factory=set)
    supports: set[str] = field(default_factory=set)
    start_text: str = ""
    success_text: str = ""
    wobble_text: str = ""
    qa_text: str = ""
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


def _r_wobble_alarm(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.entities.get("cargo")
    if cargo is None or cargo.meters["wobble"] < THRESHOLD:
        return out
    sig = ("wobble_alarm", cargo.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("pelican", "kiwi"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    out.append("__wobble__")
    return out


def _r_progress_joy(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.entities.get("cargo")
    if cargo is None or cargo.meters["progress"] < 2 * THRESHOLD:
        return out
    sig = ("progress_joy", cargo.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("pelican", "kiwi"):
        if eid in world.entities:
            world.get(eid).memes["joy"] += 1
    return out


CAUSAL_RULES = [
    Rule("wobble_alarm", "physical", _r_wobble_alarm),
    Rule("progress_joy", "emotional", _r_progress_joy),
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


SETTINGS = {
    "clamor_beach": Setting(
        "clamor_beach",
        "Clamor Beach",
        "where every shell liked to brag louder than the wave beside it",
        "the windy picnic rock",
        "shore path",
        "boom-boom and shushhh",
        tags={"beach"},
    ),
    "pebble_marsh": Setting(
        "pebble_marsh",
        "Pebble Marsh",
        "where the reeds bent low and the stones clicked like toy drums",
        "the tall berry hill",
        "reed path",
        "clack-clack and swishhh",
        tags={"marsh"},
    ),
    "thunder_dunes": Setting(
        "thunder_dunes",
        "Thunder Dunes",
        "where the sand hummed under every footstep as if it had a secret song",
        "the moon-view mound",
        "dune track",
        "whooom and hissss",
        tags={"dunes"},
    ),
}

CARGOES = {
    "golden_kiwi": Cargo(
        "golden_kiwi",
        "golden kiwi",
        "a kiwi fruit so big it made a wheelbarrow look like a teacup",
        "I can carry that shining thing with one wing half asleep!",
        "steady",
        2,
        "plonk",
        "The giant golden kiwi sat at the feast like a round green moon with freckles.",
        tags={"fruit", "kiwi_fruit"},
    ),
    "striped_kiwi": Cargo(
        "striped_kiwi",
        "striped kiwi",
        "a striped kiwi fruit as wide as a washtub and twice as proud",
        "Why, I have hauled fish longer than trains and fruit fatter than clouds!",
        "dry",
        2,
        "bonk",
        "The striped kiwi gleamed in the sunset while everyone stared with soup-spoon eyes.",
        tags={"fruit", "kiwi_fruit"},
    ),
    "singing_kiwi": Cargo(
        "singing_kiwi",
        "singing kiwi",
        "a kiwi fruit so ripe it whistled through its own stem",
        "That fruity fellow belongs in my pouch, and quick about it too!",
        "light",
        1,
        "toot",
        "The singing kiwi rested on the hill and gave one last tiny toot before supper.",
        tags={"fruit", "kiwi_fruit"},
    ),
}

HAZARDS = {
    "gust": Hazard(
        "gust",
        "gusty wind",
        "a wind that ran sideways and tried to steal hats, maps, and good ideas",
        "It could tip a load unless someone kept it steady.",
        "WHOOOOSH!",
        guards={"air", "steady"},
        severity=3,
        tags={"wind"},
    ),
    "foam": Hazard(
        "foam",
        "tide foam",
        "a lace of bubbling sea-foam that slapped over the path in silly white socks",
        "It could soak the fruit unless the method kept it dry.",
        "splish-splosh!",
        guards={"water", "dry"},
        severity=2,
        tags={"water"},
    ),
    "pebbles": Hazard(
        "pebbles",
        "rattling pebbles",
        "a rolling patch of round pebbles that danced out from under any heavy load",
        "It could bounce a cargo unless the method handled bumps lightly.",
        "clitter-clatter!",
        guards={"ground", "light"},
        severity=2,
        tags={"ground"},
    ),
}

METHODS = {
    "pouch_lift": Method(
        "pouch_lift",
        "pelican pouch lift",
        sense=3,
        power=3,
        guards={"air", "dry"},
        supports={"steady", "dry", "light"},
        start_text="The pelican dipped low and scooped the load into his deep pouch. FWOOMP!",
        success_text="He marched along the route with his bill held level as a bridge, and not a wobble escaped.",
        wobble_text="He rose grandly, but the load swayed inside his pouch like a bell in a storm.",
        qa_text="used his deep pouch to carry the fruit above the trouble",
        tags={"pouch"},
    ),
    "reed_sled": Method(
        "reed_sled",
        "reed sled",
        sense=3,
        power=2,
        guards={"ground", "steady"},
        supports={"steady", "light"},
        start_text="Together they tied reeds into a sled, slid the fruit on top, and gave it a mighty tug. SCRRRP!",
        success_text="The sled skimmed over the path so neatly that even the pebbles sounded polite.",
        wobble_text="The sled started well, then jittered and skipped when the trouble grew rougher than expected.",
        qa_text="made a sled from reeds and pulled the fruit carefully",
        tags={"sled", "reeds"},
    ),
    "shell_raft": Method(
        "shell_raft",
        "shell raft",
        sense=2,
        power=2,
        guards={"water", "dry"},
        supports={"dry", "steady"},
        start_text="They lashed driftwood and broad shells into a tiny raft and nudged the fruit aboard. PLOP-ploop!",
        success_text="The raft bobbed over the wet places while the fruit stayed high and dry.",
        wobble_text="The raft floated, but each slap of water made the cargo spin like a dinner plate.",
        qa_text="floated the fruit over the wet path on a little raft",
        tags={"raft", "shell"},
    ),
    "hop_bump": Method(
        "hop_bump",
        "bump-and-hop",
        sense=1,
        power=1,
        guards={"ground"},
        supports={"light"},
        start_text="The pelican announced that a few heroic hops would do the job. BOING! BONK!",
        success_text="By pure luck, the fruit bounced the right way.",
        wobble_text="The fruit bumped every which way and behaved like a runaway drum.",
        qa_text="tried to move the fruit with big hops",
        tags={"hopping"},
    ),
}

PELICAN_NAMES = ["Captain Bill", "Mighty Beak", "Long-Bill Lou", "Pelican Pete", "Harbor Hank"]
KIWI_NAMES = ["Kiri", "Pip", "Momo", "Tui", "Nell"]

KNOWLEDGE = {
    "pelican": [
        ("What is a pelican?",
         "A pelican is a large water bird with a long bill and a stretchy pouch. It can scoop fish and carry things in that big bill pouch.")
    ],
    "kiwi_bird": [
        ("What is a kiwi bird?",
         "A kiwi is a small bird from New Zealand with a long beak and strong little legs. It does not fly, so it often moves by running and scuttling.")
    ],
    "kiwi_fruit": [
        ("What is a kiwi fruit?",
         "A kiwi fruit is a small brown fruit with green or golden flesh inside. It tastes sweet and tart.")
    ],
    "wind": [
        ("What can a strong gust of wind do?",
         "A strong gust can push light things sideways and make loads wobble. That is why people hold onto hats, kites, and carts on windy days.")
    ],
    "water": [
        ("Why do people keep fruit dry?",
         "Keeping fruit dry helps it stay clean and pleasant to eat. Too much water can make a load slippery too.")
    ],
    "ground": [
        ("Why are round pebbles hard to walk on?",
         "Round pebbles roll under your feet, so they can feel slippery and bumpy. A heavy thing can wobble on them.")
    ],
    "pouch": [
        ("Why is a pelican's pouch useful?",
         "A pelican's pouch can hold fish and other things for a short time. It makes the bird good at scooping and carrying.")
    ],
    "sled": [
        ("What does a sled do?",
         "A sled helps you pull something along the ground instead of lifting all of it. That can make a heavy load easier to move.")
    ],
    "raft": [
        ("What is a raft?",
         "A raft is a flat thing that floats on water. People can use one to carry objects across shallow water.")
    ],
}
KNOWLEDGE_ORDER = [
    "pelican", "kiwi_bird", "kiwi_fruit", "wind", "water", "ground", "pouch", "sled", "raft"
]


def supports_hazard(method: Method, hazard: Hazard) -> bool:
    return bool(method.guards & hazard.guards)


def supports_cargo(method: Method, cargo: Cargo) -> bool:
    return cargo.need in method.supports


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid in SETTINGS:
        for cid, cargo in CARGOES.items():
            for hid, hazard in HAZARDS.items():
                for mid, method in METHODS.items():
                    if method.sense >= SENSE_MIN and supports_hazard(method, hazard) and supports_cargo(method, cargo):
                        combos.append((sid, cid, hid, mid))
    return combos


def predicted_outcome(cargo: Cargo, hazard: Hazard, method: Method) -> str:
    return "smooth" if method.power >= hazard.severity else "teamwork"


def explain_rejection(cargo: Cargo, hazard: Hazard, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (f"(Refusing method '{method.id}': it scores too low on common sense "
                f"(sense={method.sense} < {SENSE_MIN}). Pick a steadier plan such as "
                f"{', '.join(sorted(m.id for m in sensible_methods()))}.)")
    if not supports_hazard(method, hazard):
        return (f"(No story: {method.label} does not really answer {hazard.label}. "
                f"The route needs a method that guards {sorted(hazard.guards)}.)")
    if not supports_cargo(method, cargo):
        return (f"(No story: {cargo.label} needs a '{cargo.need}' kind of ride, but "
                f"{method.label} supports {sorted(method.supports)}.)")
    return "(No story: this combination does not fit the world's constraints.)"


def predict_trip(world: World, cargo_cfg: Cargo, hazard: Hazard, method: Method) -> dict:
    sim = world.copy()
    cargo = sim.get("cargo")
    cargo.meters["progress"] += 1
    if method.power < hazard.severity:
        cargo.meters["wobble"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": cargo.meters["wobble"] >= THRESHOLD,
        "progress": cargo.meters["progress"],
    }


def introduce(world: World, pelican: Entity, kiwi: Entity, setting: Setting, cargo: Cargo) -> None:
    pelican.memes["pride"] += 1
    kiwi.memes["hope"] += 1
    world.say(
        f"In {setting.place}, {setting.opening}, there lived a pelican named {pelican.id} "
        f"whose pouch was said to be so roomy it could shade a whole fishing boat at noon."
    )
    world.say(
        f"One bright morning, a kiwi named {kiwi.id} found {cargo.phrase}. "
        f"It landed beside her with a giant {cargo.sound}! and made three sleepy crabs blink."
    )


def need_help(world: World, kiwi: Entity, setting: Setting, cargo: Cargo, hazard: Hazard) -> None:
    world.say(
        f'"If only this {cargo.label} could reach {setting.finish}," said {kiwi.id}. '
        f'She gave it a hopeful shove, but it barely rolled an eyebrow.'
    )
    world.say(
        f"Between the fruit and the finish lay {hazard.route}. {hazard.sound} went the trouble, "
        f"as if the path itself were showing off."
    )


def boast(world: World, pelican: Entity, cargo: Cargo) -> None:
    world.say(
        f"{pelican.id} puffed his chest until the breeze had to walk around him. "
        f'"{cargo.boast}"'
    )


def warning(world: World, kiwi: Entity, cargo: Cargo, hazard: Hazard, method: Method) -> None:
    pred = predict_trip(world, cargo, hazard, method)
    kiwi.memes["caution"] += 1
    world.facts["predicted_wobble"] = pred["wobble"]
    world.say(
        f'{kiwi.id} gave a quick scuttle in a worried little circle. '
        f'"Mind {hazard.label}," she said. "{hazard.threat}"'
    )


def start_method(world: World, pelican: Entity, kiwi: Entity, method: Method) -> None:
    pelican.meters["reach"] += 1
    kiwi.meters["steps"] += 1
    world.say(method.start_text)


def smooth_crossing(world: World, pelican: Entity, kiwi: Entity, cargo: Entity,
                    setting: Setting, hazard: Hazard, method: Method) -> None:
    cargo.meters["progress"] += 2
    pelican.memes["joy"] += 1
    kiwi.memes["trust"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{method.success_text} {hazard.sound} cried the hazard, but it could not catch them."
    )
    world.say(
        f"{kiwi.id} scampered beside the load on her quick little feet, whispering "
        f'"scuttle-scuttle, easy now," as they reached {setting.finish}.'
    )


def wobble_crossing(world: World, pelican: Entity, kiwi: Entity, cargo: Entity,
                    setting: Setting, hazard: Hazard, method: Method) -> None:
    cargo.meters["progress"] += 1
    cargo.meters["wobble"] += 1
    pelican.memes["pride"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{method.wobble_text} {hazard.sound} shouted the route, and over went the fruit -- not far, "
        f"but far enough to make {pelican.id}'s knees knock: klak-klak!"
    )


def kiwi_turn(world: World, pelican: Entity, kiwi: Entity, cargo: Entity,
              setting: Setting, hazard: Hazard) -> None:
    kiwi.memes["bravery"] += 1
    pelican.memes["humility"] += 1
    cargo.meters["progress"] += 1
    cargo.meters["wobble"] = 0.0
    world.say(
        f"Then {kiwi.id} did what kiwis do best. She began to scuttle -- scritch-scritch, scuttle-scuttle -- "
        f"in a neat rhythm around the fruit, nudging one side, then the other."
    )
    world.say(
        f'"Match my steps," she called. {pelican.id} lowered his grand bill, listened for the beat, '
        f"and together they moved the load in little steady shoves until the boast became true the honest way."
    )
    propagate(world, narrate=False)
    world.say(
        f"Past the {hazard.label} they went at last, not fast, but right, all the way to {setting.finish}."
    )


def ending(world: World, pelican: Entity, kiwi: Entity, cargo_cfg: Cargo, outcome: str) -> None:
    pelican.memes["joy"] += 1
    kiwi.memes["joy"] += 1
    if outcome == "smooth":
        world.say(
            f"From that day on, folks said {pelican.id} could carry anything from a teacup to a thundercloud, "
            f"and perhaps he let them say it."
        )
    else:
        world.say(
            f"From that day on, folks still praised {pelican.id}'s mighty pouch, but they also praised "
            f"{kiwi.id}'s quick brain and quicker scuttle."
        )
    world.say(cargo_cfg.ending_image)


def tell(setting: Setting, cargo_cfg: Cargo, hazard: Hazard, method: Method,
         pelican_name: str = "Captain Bill", kiwi_name: str = "Kiri") -> World:
    world = World()
    pelican = world.add(Entity(pelican_name, kind="character", type="pelican", role="helper"))
    kiwi = world.add(Entity(kiwi_name, kind="character", type="kiwi", role="finder"))
    cargo = world.add(Entity("cargo", type="fruit", label=cargo_cfg.label))

    introduce(world, pelican, kiwi, setting, cargo_cfg)
    need_help(world, kiwi, setting, cargo_cfg, hazard)

    world.para()
    boast(world, pelican, cargo_cfg)
    warning(world, kiwi, cargo_cfg, hazard, method)
    start_method(world, pelican, kiwi, method)

    outcome = predicted_outcome(cargo_cfg, hazard, method)
    world.para()
    if outcome == "smooth":
        smooth_crossing(world, pelican, kiwi, cargo, setting, hazard, method)
    else:
        wobble_crossing(world, pelican, kiwi, cargo, setting, hazard, method)
        kiwi_turn(world, pelican, kiwi, cargo, setting, hazard)

    world.para()
    ending(world, pelican, kiwi, cargo_cfg, outcome)

    world.facts.update(
        pelican=pelican,
        kiwi=kiwi,
        cargo_cfg=cargo_cfg,
        cargo=cargo,
        setting=setting,
        hazard=hazard,
        method=method,
        outcome=outcome,
        delivered=cargo.meters["progress"] >= 2 * THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    cargo: str
    hazard: str
    method: str
    pelican_name: str
    kiwi_name: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting, cargo, hazard, method = f["setting"], f["cargo_cfg"], f["hazard"], f["method"]
    outcome = f["outcome"]
    base = (
        f'Write a short tall tale for a 3-to-5-year-old that includes a pelican, a kiwi, '
        f'and sound effects. The pelican helps move a giant {cargo.label} across {setting.place}.'
    )
    if outcome == "smooth":
        return [
            base,
            f"Tell a boastful story where a pelican uses {method.label} to beat {hazard.label}, "
            f'and let the kiwi scuttle beside the load saying "scuttle-scuttle."',
            f'Write a gentle tall tale with funny sounds like "{hazard.sound}" and an ending where the huge fruit reaches {setting.finish}.',
        ]
    return [
        base,
        f"Tell a tall tale where the pelican's first big plan wobbles against {hazard.label}, "
        f"but the kiwi's quick scuttle rhythm saves the day.",
        f'Write a sound-filled story with a proud pelican, a clever kiwi, and a turn where teamwork works better than bragging.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    pelican, kiwi = f["pelican"], f["kiwi"]
    setting, cargo, hazard, method = f["setting"], f["cargo_cfg"], f["hazard"], f["method"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a pelican named {pelican.id} and a kiwi named {kiwi.id}. They try to move a giant {cargo.label} across {setting.place}."
        ),
        (
            f"What problem did {kiwi.id} have?",
            f"{kiwi.id} found {cargo.phrase}, but it was too enormous to move alone. The path to {setting.finish} was troubled by {hazard.label}, so the trip needed a careful plan."
        ),
        (
            f"What did {pelican.id} say he could do?",
            f"{pelican.id} bragged that he could carry the giant fruit with ease. His big promise is what started the attempt to move it."
        ),
        (
            f"Why was {hazard.label} a problem?",
            f"{hazard.threat} That mattered because the fruit was so large that even a small wobble could spoil the trip."
        ),
    ]
    if outcome == "smooth":
        qa.append((
            f"How did they get the fruit across safely?",
            f"{pelican.id} {method.qa_text}. {kiwi.id} scuttled beside him and helped keep the trip calm, so the trouble never knocked the load off course."
        ))
        qa.append((
            "How did the story end?",
            f"They reached {setting.finish}, and the giant {cargo.label} was delivered safely. The ending proves the boast worked this time because the fruit arrived just as planned."
        ))
    else:
        qa.append((
            f"What went wrong with {pelican.id}'s first plan?",
            f"The first try was not strong enough for {hazard.label}, so the fruit began to wobble. That shaky moment frightened {pelican.id} and opened the door for a better idea."
        ))
        qa.append((
            f"How did {kiwi.id} help save the day?",
            f"{kiwi.id} began to scuttle in a steady rhythm around the fruit and told {pelican.id} to match her steps. Together they turned a wobbly boast into real teamwork and got the fruit to {setting.finish}."
        ))
        qa.append((
            "What changed by the end of the story?",
            f"At first {pelican.id} wanted to solve everything with bragging, but by the end he listened to {kiwi.id}. The giant {cargo.label} still arrived, and now both of them are remembered for the victory."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"pelican", "kiwi_bird"} | set(f["cargo_cfg"].tags)
    hazard = f["hazard"]
    method = f["method"]
    if "wind" in hazard.tags:
        tags.add("wind")
    if "water" in hazard.tags:
        tags.add("water")
    if "ground" in hazard.tags:
        tags.add("ground")
    if "pouch" in method.tags:
        tags.add("pouch")
    if "sled" in method.tags or "reeds" in method.tags:
        tags.add("sled")
    if "raft" in method.tags or "shell" in method.tags:
        tags.add("raft")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("clamor_beach", "golden_kiwi", "gust", "pouch_lift", "Captain Bill", "Kiri"),
    StoryParams("pebble_marsh", "singing_kiwi", "pebbles", "reed_sled", "Mighty Beak", "Pip"),
    StoryParams("thunder_dunes", "striped_kiwi", "foam", "shell_raft", "Long-Bill Lou", "Momo"),
    StoryParams("clamor_beach", "golden_kiwi", "gust", "reed_sled", "Pelican Pete", "Tui"),
]


ASP_RULES = r"""
supports_hazard(M, H) :- method(M), hazard(H), guards_method(M, G), guards_hazard(H, G).
supports_cargo(M, C)  :- method(M), cargo(C), cargo_need(C, N), supports_need(M, N).
sensible(M)           :- method(M), sense(M, S), sense_min(Min), S >= Min.

valid(S, C, H, M) :- setting(S), cargo(C), hazard(H), method(M),
                     sensible(M), supports_hazard(M, H), supports_cargo(M, C).

smooth(C, H, M)   :- cargo(C), hazard(H), method(M), power(M, P), severity(H, V), P >= V.
teamwork(C, H, M) :- valid(_, C, H, M), not smooth(C, H, M).

outcome(smooth)   :- chosen_cargo(C), chosen_hazard(H), chosen_method(M), smooth(C, H, M).
outcome(teamwork) :- chosen_cargo(C), chosen_hazard(H), chosen_method(M), valid(_, C, H, M),
                     not smooth(C, H, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, cargo in CARGOES.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("cargo_need", cid, cargo.need))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("severity", hid, hazard.severity))
        for g in sorted(hazard.guards):
            lines.append(asp.fact("guards_hazard", hid, g))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("power", mid, method.power))
        for g in sorted(method.guards):
            lines.append(asp.fact("guards_method", mid, g))
        for s in sorted(method.supports):
            lines.append(asp.fact("supports_need", mid, s))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_cargo", params.cargo),
        asp.fact("chosen_hazard", params.hazard),
        asp.fact("chosen_method", params.method),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    csens = set(asp_sensible())
    psens = {m.id for m in sensible_methods()}
    if csens == psens:
        print(f"OK: sensible methods match ({sorted(csens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(csens)} python={sorted(psens)}")

    cases = list(CURATED)
    for sid, cid, hid, mid in sorted(valid_combos())[:20]:
        cases.append(StoryParams(sid, cid, hid, mid, PELICAN_NAMES[0], KIWI_NAMES[0]))
    bad = 0
    for p in cases:
        py = predicted_outcome(CARGOES[p.cargo], HAZARDS[p.hazard], METHODS[p.method])
        cl = asp_outcome(p)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a pelican, a scuttling kiwi, and a giant kiwi fruit."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--pelican-name")
    ap.add_argument("--kiwi-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo and args.hazard and args.method:
        cargo = CARGOES[args.cargo]
        hazard = HAZARDS[args.hazard]
        method = METHODS[args.method]
        if not (method.sense >= SENSE_MIN and supports_hazard(method, hazard) and supports_cargo(method, cargo)):
            raise StoryError(explain_rejection(cargo, hazard, method))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.cargo is None or c[1] == args.cargo)
              and (args.hazard is None or c[2] == args.hazard)
              and (args.method is None or c[3] == args.method)]
    if not combos:
        if args.cargo and args.hazard and args.method:
            raise StoryError(explain_rejection(CARGOES[args.cargo], HAZARDS[args.hazard], METHODS[args.method]))
        raise StoryError("(No valid combination matches the given options.)")

    setting, cargo, hazard, method = rng.choice(sorted(combos))
    pelican_name = args.pelican_name or rng.choice(PELICAN_NAMES)
    kiwi_name = args.kiwi_name or rng.choice(KIWI_NAMES)
    if pelican_name == kiwi_name:
        kiwi_name = next(name for name in KIWI_NAMES if name != pelican_name)
    return StoryParams(setting, cargo, hazard, method, pelican_name, kiwi_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CARGOES[params.cargo],
        HAZARDS[params.hazard],
        METHODS[params.method],
        pelican_name=params.pelican_name,
        kiwi_name=params.kiwi_name,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, cargo, hazard, method) combos:\n")
        for setting, cargo, hazard, method in combos:
            print(f"  {setting:13} {cargo:13} {hazard:8} {method}")
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
            header = (
                f"### {p.pelican_name} & {p.kiwi_name}: {p.cargo} with {p.method} "
                f"through {p.hazard} at {p.setting} ({predicted_outcome(CARGOES[p.cargo], HAZARDS[p.hazard], METHODS[p.method])})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
