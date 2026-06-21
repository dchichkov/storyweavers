#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/guppy_nudge_gunk_dim_transformation_conflict_nursery.py
==================================================================================

A standalone storyworld for a nursery-rhyme-flavored tiny domain:

    a little guppy gets all gunk-dim,
    a friend gives a nudge,
    they quarrel for a moment,
    then the guppy is washed bright again.

The world model treats dimming and brightening as simulated state, not as simple
word swaps. A muddy place makes scales dull; a fitting rinse place can clear the
gunk. The conflict beat depends on how stubborn the guppy feels and how firmly
the helper nudges.

Run it
------
    python storyworlds/worlds/gpt-5.4/guppy_nudge_gunk_dim_transformation_conflict_nursery.py
    python storyworlds/worlds/gpt-5.4/guppy_nudge_gunk_dim_transformation_conflict_nursery.py --setting lily_pond --muck mudbank --rinse spring_runnel
    python storyworlds/worlds/gpt-5.4/guppy_nudge_gunk_dim_transformation_conflict_nursery.py --setting moon_pool --muck duck_slosh
    python storyworlds/worlds/gpt-5.4/guppy_nudge_gunk_dim_transformation_conflict_nursery.py --all --qa
    python storyworlds/worlds/gpt-5.4/guppy_nudge_gunk_dim_transformation_conflict_nursery.py --verify
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

# Make the shared result containers importable when this script is run directly:
# .../storyworlds/worlds/gpt-5.4/<file>.py  -> add storyworlds/ to sys.path.
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    label: str
    opening: str
    ring: str
    affords_muck: set[str] = field(default_factory=set)
    affords_rinse: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Muck:
    id: str
    label: str
    phrase: str
    severity: int
    splash: str
    blame: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rinse:
    id: str
    label: str
    phrase: str
    power: int
    shimmer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    label: str
    call: str
    motion: str
    firmness: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_gunk_dim(world: World) -> list[str]:
    out: list[str] = []
    guppy = world.get("guppy")
    if guppy.meters["gunk"] < THRESHOLD:
        return out
    sig = ("gunk_dim", int(guppy.meters["gunk"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guppy.meters["dim"] += 1
    guppy.memes["embarrassed"] += 1
    world.get("water").meters["murk"] += 1
    out.append("__dim__")
    return out


def _r_rinse_bright(world: World) -> list[str]:
    out: list[str] = []
    guppy = world.get("guppy")
    if guppy.meters["rinsed"] < THRESHOLD:
        return out
    sig = ("rinse_bright", int(guppy.meters["rinsed"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guppy.meters["gunk"] = 0.0
    guppy.meters["dim"] = 0.0
    guppy.meters["bright"] += 1
    guppy.memes["embarrassed"] = 0.0
    guppy.memes["relief"] += 1
    guppy.memes["joy"] += 1
    world.get("water").meters["murk"] = 0.0
    out.append("__bright__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="gunk_dim", tag="physical", apply=_r_gunk_dim),
    Rule(name="rinse_bright", tag="physical", apply=_r_rinse_bright),
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


def valid_combo(setting_id: str, muck_id: str, rinse_id: str) -> bool:
    if setting_id not in SETTINGS or muck_id not in MUCKS or rinse_id not in RINSES:
        return False
    setting = SETTINGS[setting_id]
    muck = MUCKS[muck_id]
    rinse = RINSES[rinse_id]
    return (
        muck_id in setting.affords_muck
        and rinse_id in setting.affords_rinse
        and rinse.power >= muck.severity
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for muck_id in MUCKS:
            for rinse_id in RINSES:
                if valid_combo(setting_id, muck_id, rinse_id):
                    combos.append((setting_id, muck_id, rinse_id))
    return combos


def predict_transformation(world: World, muck: Muck, rinse: Rinse) -> dict:
    sim = world.copy()
    guppy = sim.get("guppy")
    guppy.meters["gunk"] += muck.severity
    propagate(sim, narrate=False)
    before_dim = guppy.meters["dim"]
    guppy.meters["rinsed"] += rinse.power
    propagate(sim, narrate=False)
    return {
        "will_dim": before_dim >= THRESHOLD,
        "will_brighten": guppy.meters["bright"] >= THRESHOLD,
    }


def accepts_first_nudge(stubbornness: int, helper_firmness: int) -> bool:
    return helper_firmness + 1 >= stubbornness


def outcome_of(params: "StoryParams") -> str:
    if not valid_combo(params.setting, params.muck, params.rinse):
        return "invalid"
    helper = HELPERS[params.helper]
    if accepts_first_nudge(params.stubbornness, helper.firmness):
        return "easy_turn"
    return "stubborn_turn"


def opening(world: World, guppy: Entity, helper: Entity) -> None:
    setting = world.setting
    guppy.memes["joy"] += 1
    helper.memes["care"] += 1
    world.say(
        f"In {setting.label}, where {setting.ring}, swam {guppy.id}, a little guppy with a silver grin."
    )
    world.say(
        f"{setting.opening} Near {guppy.pronoun('object')} bobbed {helper.id} the {helper.label}, humming a tiny water tune."
    )
    world.say(
        f'"Swish, little fish, swish in a ring; shimmer your tail and shine while you sing," crooned the water.'
    )


def muck_misstep(world: World, guppy: Entity, muck: Muck) -> None:
    guppy.meters["gunk"] += muck.severity
    guppy.memes["pride"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {guppy.id} darted too close to {muck.phrase}. Up came a blur of brown and green; it dabbed {guppy.pronoun("possessive")} cheeks, it dusted {guppy.pronoun("possessive")} tail, and soon the bright little fish looked all gunk-dim."
    )
    world.say(
        f'The water gave a hush and a swirl. "{muck.splash}," it seemed to sigh.'
    )


def quarrel(world: World, guppy: Entity, helper: Entity, muck: Muck, rinse: Rinse, first_accept: bool) -> None:
    pred = predict_transformation(world, muck, rinse)
    world.facts["predicted_brighten"] = pred["will_brighten"]
    helper.memes["care"] += 1
    guppy.memes["cross"] += 1
    world.say(
        f'{helper.id} gave a little nudge with {helper.attrs["motion"]}. "{helper.attrs["call"]}, {guppy.id}, do not pout. {rinse.phrase} can wash that smudge right out."'
    )
    if first_accept:
        guppy.memes["trust"] += 1
        world.say(
            f'But {guppy.id} only blinked at the dim little face in the water and whispered, "Am I still me under this muddy trim?"'
        )
    else:
        guppy.memes["defiance"] += 1
        world.say(
            f'"No, no, no," cried {guppy.id}. "It was {muck.blame}, not me. I will not budge for a bathy spree."'
        )
        world.say(
            f'{helper.id} floated beside {guppy.pronoun("object")} and would not snap back. Instead, {helper.pronoun()} sang, "Nudge by nudge and fin by fin, we can rinse the gunk and find your grin."'
        )
        guppy.memes["reflection"] += 1
        world.say(
            f'{guppy.id} peeped into a still patch of water and saw that the sparkle on {guppy.pronoun("possessive")} tail had gone meek and thin. That sight made the quarrel feel smaller.'
        )


def rinse_scene(world: World, guppy: Entity, helper: Entity, rinse: Rinse) -> None:
    guppy.meters["rinsed"] += rinse.power
    propagate(world, narrate=False)
    world.say(
        f'So off they went to {rinse.phrase}, with a wiggle, a giggle, and one last careful nudge.'
    )
    world.say(
        f'The clear water slipped over {guppy.pronoun("possessive")} head and under {guppy.pronoun("possessive")} fins. {rinse.shimmer}, and the brownish blur came floating away.'
    )
    world.say(
        f'{guppy.id} was not gunk-dim now. {guppy.pronoun().capitalize()} flashed bright as a bead again, and even the ripples seemed to clap.'
    )
    helper.memes["joy"] += 1
    guppy.memes["love"] += 1


def closing(world: World, guppy: Entity, helper: Entity) -> None:
    world.say(
        f'"Swish, little fish, swish in a ring; after the muddle, more brightly sing," laughed {helper.id}.'
    )
    world.say(
        f'And {guppy.id} the guppy spun through the clean small waves, bright-eyed, soft-finned, and ready to mind a kind nudge next time.'
    )


def tell(
    setting: Setting,
    muck: Muck,
    rinse: Rinse,
    helper_cfg: HelperKind,
    guppy_name: str = "Pip",
    helper_name: str = "Tup",
    stubbornness: int = 2,
) -> World:
    world = World(setting)
    guppy = world.add(
        Entity(
            id=guppy_name,
            kind="character",
            type="guppy",
            label="guppy",
            phrase="a little guppy",
            role="hero",
            traits=["little", "quick"],
            attrs={"stubbornness": stubbornness},
            tags={"guppy"},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type="fish",
            label=helper_cfg.label,
            phrase=f"a {helper_cfg.label}",
            role="helper",
            attrs={"call": helper_cfg.call, "motion": helper_cfg.motion, "firmness": helper_cfg.firmness},
            tags=set(helper_cfg.tags),
        )
    )
    world.add(Entity(id="water", kind="thing", type="water", label="water", phrase="the pond water"))

    opening(world, guppy, helper)
    world.para()
    muck_misstep(world, guppy, muck)
    world.para()
    first_accept = accepts_first_nudge(stubbornness, helper_cfg.firmness)
    quarrel(world, guppy, helper, muck, rinse, first_accept)
    world.para()
    rinse_scene(world, guppy, helper, rinse)
    closing(world, guppy, helper)

    world.facts.update(
        guppy=guppy,
        helper=helper,
        setting=setting,
        muck=muck,
        rinse=rinse,
        helper_cfg=helper_cfg,
        stubbornness=stubbornness,
        outcome="easy_turn" if first_accept else "stubborn_turn",
        transformed=guppy.meters["bright"] >= THRESHOLD,
        conflict=guppy.memes["cross"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "lily_pond": Setting(
        id="lily_pond",
        label="the lily pond",
        opening="Round leaves rocked like green little boats, and reed shadows made striped roads on the water.",
        ring="the lily pads made a green ring",
        affords_muck={"mudbank", "silt_swirl"},
        affords_rinse={"bubble_ring", "spring_runnel"},
        tags={"pond", "lily"},
    ),
    "moon_pool": Setting(
        id="moon_pool",
        label="the moon pool",
        opening="A pale shine lay on the water, and the pebbles below looked like tiny moons.",
        ring="the pale light made a silver ring",
        affords_muck={"duck_slosh", "mudbank"},
        affords_rinse={"moonfall", "bubble_ring"},
        tags={"pool", "moon"},
    ),
    "brook_nursery": Setting(
        id="brook_nursery",
        label="the brook nursery",
        opening="Small stones clicked together, and fern tips bowed at the busy little stream.",
        ring="the water curled in a bright ring around the stones",
        affords_muck={"silt_swirl", "leaf_mash"},
        affords_rinse={"spring_runnel", "pebble_chute"},
        tags={"brook"},
    ),
}

MUCKS = {
    "mudbank": Muck(
        id="mudbank",
        label="mudbank",
        phrase="the soft mudbank",
        severity=2,
        splash="Muck on the nose and smudge on the fin",
        blame="that bossy bank",
        tags={"mud"},
    ),
    "silt_swirl": Muck(
        id="silt_swirl",
        label="silt swirl",
        phrase="a sleepy silt swirl",
        severity=1,
        splash="Dust in the ripple and dim on the chin",
        blame="that silly swirl",
        tags={"silt"},
    ),
    "leaf_mash": Muck(
        id="leaf_mash",
        label="leaf mash",
        phrase="the leaf mash under the reeds",
        severity=1,
        splash="Mash on the cheek and fleck on the fin",
        blame="that mushy mash",
        tags={"leaf"},
    ),
    "duck_slosh": Muck(
        id="duck_slosh",
        label="duck slosh",
        phrase="the duck-made slosh by the bank",
        severity=2,
        splash="Slop in the water and smear on the skin",
        blame="that flappy duck water",
        tags={"duck", "mud"},
    ),
}

RINSES = {
    "bubble_ring": Rinse(
        id="bubble_ring",
        label="bubble ring",
        phrase="the bubble ring by the reeds",
        power=1,
        shimmer="A string of bubbles popped like tiny bells",
        tags={"bubbles"},
    ),
    "spring_runnel": Rinse(
        id="spring_runnel",
        label="spring runnel",
        phrase="the spring runnel where the water ran clear",
        power=2,
        shimmer="The cool thread of water sang over every scale",
        tags={"spring"},
    ),
    "moonfall": Rinse(
        id="moonfall",
        label="moonfall",
        phrase="the moonfall trickle under the stone lip",
        power=2,
        shimmer="Silver-bright drops pattered down like a soft song",
        tags={"moon", "spring"},
    ),
    "pebble_chute": Rinse(
        id="pebble_chute",
        label="pebble chute",
        phrase="the pebble chute where the stream skipped fast",
        power=1,
        shimmer="The skipping water tickled every fin-tip",
        tags={"pebbles"},
    ),
}

HELPERS = {
    "minnow": HelperKind(
        id="minnow",
        label="minnow",
        call="come now",
        motion="a neat bright nose",
        firmness=1,
        tags={"minnow", "friend"},
    ),
    "snail": HelperKind(
        id="snail",
        label="snail",
        call="hush now",
        motion="a patient shell-edge",
        firmness=2,
        tags={"snail", "friend"},
    ),
    "froglet": HelperKind(
        id="froglet",
        label="froglet",
        call="hop to it",
        motion="a springy little toe",
        firmness=3,
        tags={"frog", "friend"},
    ),
}

GUPPY_NAMES = ["Pip", "Pib", "Mip", "Nim", "Dot", "Bibi", "Tib", "Lulu"]
HELPER_NAMES = ["Tup", "Moss", "Peep", "Nib", "Plink", "Roo"]

KNOWLEDGE = {
    "guppy": [
        (
            "What is a guppy?",
            "A guppy is a very small fish with a tail that can look bright and fluttery in the water."
        )
    ],
    "mud": [
        (
            "Why does mud make things look dull?",
            "Mud is made of wet dirt, and when it sticks to something bright it covers the shine and makes the color look dull."
        )
    ],
    "silt": [
        (
            "What is silt?",
            "Silt is very fine dirt in water. It can swirl up in a cloud and settle on fish or stones."
        )
    ],
    "bubbles": [
        (
            "What are bubbles in water?",
            "Bubbles are little pockets of air in the water. They pop quickly and can dance upward in shiny strings."
        )
    ],
    "spring": [
        (
            "Why is clear spring water good for rinsing?",
            "Clear running water keeps moving, so it can wash dirt away instead of letting it stick."
        )
    ],
    "frog": [
        (
            "What is a froglet?",
            "A froglet is a young frog. It is small, lively, and almost grown."
        )
    ],
    "snail": [
        (
            "Why might a snail seem patient?",
            "A snail moves slowly and steadily, so people often use snails in stories to show patience."
        )
    ],
    "friend": [
        (
            "What is a kind nudge?",
            "A kind nudge is a gentle push or reminder that helps someone move the right way without being mean."
        )
    ],
}
KNOWLEDGE_ORDER = ["guppy", "mud", "silt", "bubbles", "spring", "frog", "snail", "friend"]


@dataclass
class StoryParams:
    setting: str
    muck: str
    rinse: str
    helper: str
    guppy_name: str
    helper_name: str
    stubbornness: int
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="lily_pond",
        muck="silt_swirl",
        rinse="bubble_ring",
        helper="minnow",
        guppy_name="Pip",
        helper_name="Tup",
        stubbornness=1,
    ),
    StoryParams(
        setting="lily_pond",
        muck="mudbank",
        rinse="spring_runnel",
        helper="snail",
        guppy_name="Nim",
        helper_name="Moss",
        stubbornness=3,
    ),
    StoryParams(
        setting="moon_pool",
        muck="duck_slosh",
        rinse="moonfall",
        helper="froglet",
        guppy_name="Dot",
        helper_name="Roo",
        stubbornness=3,
    ),
    StoryParams(
        setting="brook_nursery",
        muck="leaf_mash",
        rinse="pebble_chute",
        helper="snail",
        guppy_name="Bibi",
        helper_name="Peep",
        stubbornness=2,
    ),
    StoryParams(
        setting="brook_nursery",
        muck="silt_swirl",
        rinse="spring_runnel",
        helper="minnow",
        guppy_name="Lulu",
        helper_name="Nib",
        stubbornness=2,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    guppy = f["guppy"]
    helper = f["helper"]
    setting = f["setting"]
    muck = f["muck"]
    rinse = f["rinse"]
    return [
        'Write a short nursery-rhyme-style story for a 3-to-5-year-old that includes the words "guppy", "nudge", and "gunk-dim".',
        f"Tell a gentle Transformation and Conflict story where a little guppy in {setting.label} gets muddy in {muck.phrase}, quarrels for a moment, and is helped toward {rinse.phrase}.",
        f"Write a rhyming story where {helper.id} the {helper.label} gives {guppy.id} a kind nudge, and the ending image proves that the little fish has changed from dull to bright.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    guppy = f["guppy"]
    helper = f["helper"]
    setting = f["setting"]
    muck = f["muck"]
    rinse = f["rinse"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {guppy.id}, a little guppy in {setting.label}, and {helper.id} the {helper.label}, who tried to help. Their story is about getting messy, feeling cross, and becoming bright again."
        ),
        (
            f"Why did {guppy.id} become gunk-dim?",
            f"{guppy.id} swam too close to {muck.phrase}, and the muck smeared over {guppy.pronoun('possessive')} face and tail. That dirt covered the shine on the little fish, so {guppy.pronoun()} looked dull instead of bright."
        ),
        (
            f"What was the conflict in the story?",
            f'The conflict was that {helper.id} wanted to help, but {guppy.id} felt cross and did not want to be told what to do. The kind nudge turned into a small quarrel before {guppy.id} was ready to change.'
        ),
    ]
    if outcome == "easy_turn":
        qa.append(
            (
                f"How did {helper.id} help {guppy.id}?",
                f"{helper.id} gave {guppy.id} a gentle nudge toward {rinse.phrase}. {guppy.id} listened quickly, and the clear water washed the gunk away."
            )
        )
    else:
        qa.append(
            (
                f"Why did {guppy.id} stop arguing?",
                f"{guppy.id} first argued and blamed {muck.blame}, but then saw a dim reflection in the still water. That sight made the quarrel feel smaller, so {guppy.pronoun()} agreed to go rinse off."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {guppy.id} shining bright again after the rinse. The final image shows the little guppy swimming through clean water and remembering that a kind nudge can help."
        )
    )
    return qa


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"guppy", "friend"} | set(f["muck"].tags) | set(f["rinse"].tags) | set(f["helper_cfg"].tags)
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
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting_id: str, muck_id: str, rinse_id: str) -> str:
    if setting_id not in SETTINGS:
        return f"(No story: unknown setting '{setting_id}'.)"
    if muck_id not in MUCKS:
        return f"(No story: unknown muck '{muck_id}'.)"
    if rinse_id not in RINSES:
        return f"(No story: unknown rinse '{rinse_id}'.)"
    setting = SETTINGS[setting_id]
    muck = MUCKS[muck_id]
    rinse = RINSES[rinse_id]
    if muck_id not in setting.affords_muck:
        return f"(No story: {setting.label} does not have {muck.phrase}, so the guppy has no honest way to get gunk-dim there.)"
    if rinse_id not in setting.affords_rinse:
        return f"(No story: {setting.label} does not have {rinse.phrase}, so the needed brightening turn cannot happen there.)"
    if rinse.power < muck.severity:
        return f"(No story: {rinse.phrase} is too weak to wash off {muck.phrase}. Pick a stronger rinse so the transformation is believable.)"
    return "(No story: that combination does not fit this world.)"


ASP_RULES = r"""
valid(S, M, R) :- setting(S), muck(M), rinse(R),
                  affords_muck(S, M), affords_rinse(S, R),
                  severity(M, Sev), power(R, Pow), Pow >= Sev.

easy_turn :- chosen_helper(H), firmness(H, F),
             chosen_stubbornness(S), F + 1 >= S.
stubborn_turn :- chosen_helper(H), firmness(H, F),
                 chosen_stubbornness(S), F + 1 < S.

outcome(easy_turn) :- easy_turn.
outcome(stubborn_turn) :- stubborn_turn.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for muck_id in sorted(setting.affords_muck):
            lines.append(asp.fact("affords_muck", setting_id, muck_id))
        for rinse_id in sorted(setting.affords_rinse):
            lines.append(asp.fact("affords_rinse", setting_id, rinse_id))
    for muck_id, muck in MUCKS.items():
        lines.append(asp.fact("muck", muck_id))
        lines.append(asp.fact("severity", muck_id, muck.severity))
    for rinse_id, rinse in RINSES.items():
        lines.append(asp.fact("rinse", rinse_id))
        lines.append(asp.fact("power", rinse_id, rinse.power))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("firmness", helper_id, helper.firmness))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_stubbornness", params.stubbornness),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
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

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        if not smoke.prompts or not smoke.story_qa or not smoke.world_qa:
            raise StoryError("missing prompts or QA")
        print("OK: smoke test generate() produced story, prompts, and QA.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a guppy goes gunk-dim, resists a nudge, and turns bright again."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--muck", choices=MUCKS)
    ap.add_argument("--rinse", choices=RINSES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--guppy-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--stubbornness", type=int, choices=[1, 2, 3], help="1 = easy to guide, 3 = very stubborn")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.muck and args.rinse and not valid_combo(args.setting, args.muck, args.rinse):
        raise StoryError(explain_rejection(args.setting, args.muck, args.rinse))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.muck is None or combo[1] == args.muck)
        and (args.rinse is None or combo[2] == args.rinse)
    ]
    if not combos:
        if args.setting and args.muck and args.rinse:
            raise StoryError(explain_rejection(args.setting, args.muck, args.rinse))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, muck_id, rinse_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    guppy_name = args.guppy_name or rng.choice(GUPPY_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != guppy_name] or HELPER_NAMES)
    stubbornness = args.stubbornness if args.stubbornness is not None else rng.choice([1, 2, 3])

    return StoryParams(
        setting=setting_id,
        muck=muck_id,
        rinse=rinse_id,
        helper=helper_id,
        guppy_name=guppy_name,
        helper_name=helper_name,
        stubbornness=stubbornness,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.muck not in MUCKS:
        raise StoryError(f"(No story: unknown muck '{params.muck}'.)")
    if params.rinse not in RINSES:
        raise StoryError(f"(No story: unknown rinse '{params.rinse}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if not valid_combo(params.setting, params.muck, params.rinse):
        raise StoryError(explain_rejection(params.setting, params.muck, params.rinse))

    world = tell(
        setting=SETTINGS[params.setting],
        muck=MUCKS[params.muck],
        rinse=RINSES[params.rinse],
        helper_cfg=HELPERS[params.helper],
        guppy_name=params.guppy_name,
        helper_name=params.helper_name,
        stubbornness=params.stubbornness,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_items(world)],
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, muck, rinse) combos:\n")
        for setting_id, muck_id, rinse_id in combos:
            print(f"  {setting_id:14} {muck_id:11} {rinse_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.guppy_name}: {p.muck} -> {p.rinse} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
