#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cheapo_bridge_flap_foreshadowing_magic_slice_of.py
==============================================================================

A standalone story world for a small slice-of-life tale with a magical bridge,
a cheapo container with a loose flap, and an ordinary errand that turns into a
gentle lesson about noticing little warnings.

Seed constraints
----------------
Words: cheapo, bridge, flap
Features: Foreshadowing, Magic
Style: Slice of Life

World premise
-------------
A child carries something small in a cheapo holder with a loose flap. Before the
walk, a grown-up notices that the flap keeps lifting. That warning matters when
the child steps onto a breezy bridge. If the child is watchful enough, the
problem is averted. If not, the item slips out. Then the bridge's mild magic may
help recover it -- or, if the item is too heavy for that bridge's magic, the
grown-up later makes things right and fixes the holder for next time.

The simulation keeps track of:
- physical meters: breeze, risk, slipping, lost, repaired
- emotional memes: worry, relief, awe, care, embarrassment, joy

The story text is rendered from state transitions, not from one frozen template.
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
WATCHFUL_TRAITS = {"careful", "patient", "tidy"}
FIX_MIN = 1


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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class BridgeCfg:
    id: str
    label: str
    phrase: str
    place: str
    wind: int
    magic: int
    shimmer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ContainerCfg:
    id: str
    label: str
    phrase: str
    flap_word: str
    flap_strength: int
    holds: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    item_type: str
    weight: int
    purpose: str
    if_lost: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FixCfg:
    id: str
    label: str
    phrase: str
    sense: int
    works_for: set[str] = field(default_factory=set)
    action: str = ""
    ending: str = ""
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


def _r_breeze_risk(world: World) -> list[str]:
    bridge = world.get("bridge")
    holder = world.get("holder")
    child = world.get("child")
    if bridge.meters["crossing"] < THRESHOLD:
        return []
    sig = ("breeze_risk",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    risk = max(0.0, bridge.meters["wind"] - holder.meters["flap_strength"])
    if risk > 0:
        holder.meters["risk"] += risk
        child.memes["worry"] += 1
        return ["__risk__"]
    return []


def _r_slip(world: World) -> list[str]:
    bridge = world.get("bridge")
    holder = world.get("holder")
    item = world.get("item")
    child = world.get("child")
    if holder.meters["risk"] < THRESHOLD:
        return []
    if child.meters["holding_flap"] >= THRESHOLD:
        return []
    sig = ("slip",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["slipping"] += 1
    child.memes["alarm"] += 1
    return ["__slip__"]


def _r_magic(world: World) -> list[str]:
    bridge = world.get("bridge")
    item = world.get("item")
    child = world.get("child")
    if item.meters["slipping"] < THRESHOLD:
        return []
    sig = ("magic",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if bridge.meters["magic_strength"] >= item.meters["weight"]:
        item.meters["recovered"] += 1
        child.memes["awe"] += 1
        child.memes["relief"] += 1
        return ["__recovered__"]
    item.meters["lost"] += 1
    child.memes["sadness"] += 1
    return ["__lost__"]


CAUSAL_RULES = [
    Rule(name="breeze_risk", tag="physical", apply=_r_breeze_risk),
    Rule(name="slip", tag="physical", apply=_r_slip),
    Rule(name="magic", tag="magical", apply=_r_magic),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


def item_fits(container: ContainerCfg, item: ItemCfg) -> bool:
    return item.item_type in container.holds


def fix_compatible(container: ContainerCfg, fix: FixCfg) -> bool:
    return container.id in fix.works_for and fix.sense >= FIX_MIN


def story_risk(bridge: BridgeCfg, container: ContainerCfg) -> int:
    return max(0, bridge.wind - container.flap_strength)


def watchful(trait: str) -> bool:
    return trait in WATCHFUL_TRAITS


def would_avoid(bridge: BridgeCfg, container: ContainerCfg, trait: str) -> bool:
    risk = story_risk(bridge, container)
    if risk <= 0:
        return True
    if watchful(trait) and risk <= 1:
        return True
    return False


def outcome_of(params: "StoryParams") -> str:
    bridge = BRIDGES[params.bridge]
    container = CONTAINERS[params.container]
    item = ITEMS[params.item]
    if would_avoid(bridge, container, params.trait):
        return "averted"
    if bridge.magic >= item.weight:
        return "recovered"
    return "lost"


def predict_bridge(world: World) -> dict:
    sim = world.copy()
    sim.get("bridge").meters["crossing"] += 1
    if would_avoid(
        BRIDGES[sim.facts["bridge_cfg"].id],
        CONTAINERS[sim.facts["container_cfg"].id],
        sim.facts["child"].attrs["trait"],
    ):
        sim.get("child").meters["holding_flap"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("holder").meters["risk"],
        "slipping": sim.get("item").meters["slipping"],
        "recovered": sim.get("item").meters["recovered"],
        "lost": sim.get("item").meters["lost"],
    }


def introduce(world: World, child: Entity, caregiver: Entity, item: ItemCfg, container: ContainerCfg) -> None:
    world.say(
        f"After school, {child.id} had one small job to do. "
        f"{caregiver.label_word.capitalize()} asked {child.pronoun('object')} to carry {item.phrase} in {container.phrase}."
    )
    world.say(
        f"It was a cheapo little thing, and its {container.flap_word} never liked to stay flat for long."
    )


def foreshadow(world: World, child: Entity, caregiver: Entity, bridge: BridgeCfg, container: ContainerCfg) -> None:
    pred = predict_bridge(world)
    world.facts["predicted_risk"] = pred["risk"]
    hint = "kept lifting" if pred["risk"] >= THRESHOLD else "hardly moved at all"
    world.say(
        f'At the door, {caregiver.label_word} touched the {container.flap_word} and said, '
        f'"That little flap {hint}. Hold it tight when you get to {bridge.phrase}."'
    )
    world.say(
        f"{child.id} nodded. Far off, the bridge gave one soft gleam in the afternoon light, as if it had heard."
    )


def set_out(world: World, child: Entity, bridge: BridgeCfg, item: ItemCfg) -> None:
    child.memes["duty"] += 1
    world.say(
        f"{child.id} walked down {bridge.place} with {item.label} tucked away and the ordinary sounds of the neighborhood all around."
    )


def onto_bridge(world: World, child: Entity, bridge: Entity, bridge_cfg: BridgeCfg) -> None:
    bridge.meters["crossing"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"When {child.id} stepped onto {bridge_cfg.phrase}, the breeze came skipping over the water."
    )
    world.say(
        f"The loose flap gave a quick little flap of its own, just the way {caregiver_name(world)} had warned."
    )
    propagate(world, narrate=False)


def caregiver_name(world: World) -> str:
    return world.get("caregiver").label_word


def hold_tight(world: World, child: Entity, holder: Entity, container: ContainerCfg) -> None:
    child.meters["holding_flap"] += 1
    child.memes["care"] += 1
    world.say(
        f"{child.id} remembered the warning, pinched the {container.flap_word} closed, and held the cheapo {holder.label} against {child.pronoun('possessive')} sweater."
    )


def slip_out(world: World, child: Entity, item: Entity, item_cfg: ItemCfg) -> None:
    world.say(
        f"But one playful gust lifted the flap wide, and {item_cfg.phrase} slipped out before {child.id} could grab it."
    )


def magic_recover(world: World, child: Entity, bridge_cfg: BridgeCfg, item_cfg: ItemCfg) -> None:
    world.say(
        f"For a blink, {bridge_cfg.shimmer} ran along the rails. Then the air curled under {item_cfg.label} and nudged it back toward {child.id}'s hands."
    )
    world.say(
        f"{child.id} caught it against {child.pronoun('possessive')} chest and stood very still, half laughing and half staring."
    )


def lose_item(world: World, child: Entity, bridge_cfg: BridgeCfg, item_cfg: ItemCfg) -> None:
    world.say(
        f"{bridge_cfg.shimmer.capitalize()} stirred over the water, but {item_cfg.label} was too heavy for the little magic there."
    )
    world.say(
        f"{child.id} watched it go with a hot, embarrassed face and hurried home across the bridge with the empty holder in {child.pronoun('possessive')} hand."
    )


def return_home(world: World, child: Entity, caregiver: Entity, item_cfg: ItemCfg) -> None:
    world.say(
        f"Back in the kitchen, {child.id} told {caregiver.label_word} exactly what had happened."
    )
    world.say(
        f"{caregiver.label_word.capitalize()} listened first and only then looked at the loose flap."
    )


def mend(world: World, child: Entity, caregiver: Entity, holder: Entity, fix: FixCfg, item_cfg: ItemCfg, outcome: str) -> None:
    holder.meters["repaired"] += 1
    child.memes["relief"] += 1
    child.memes["love"] += 1
    if outcome == "lost":
        world.say(
            f'"We can fix two things at once," {caregiver.label_word} said softly. "{item_cfg.if_lost}"'
        )
    else:
        world.say(
            f'"Let\'s make this easier for tomorrow," {caregiver.label_word} said.'
        )
    world.say(
        f"At the table, {caregiver.label_word} used {fix.phrase} and {fix.action}."
    )
    world.say(fix.ending)
    if outcome == "recovered":
        world.say(
            f"{child.id} tucked {item_cfg.label} back inside and pressed the flap down with new respect."
        )
    elif outcome == "averted":
        world.say(
            f"{child.id} smiled at the quiet holder. The bridge had not needed to help today."
        )
    else:
        world.say(
            f"{child.id} touched the neat flap and felt better. Next time, the walk to the bridge would begin a little wiser."
        )


def tell(
    bridge_cfg: BridgeCfg,
    container_cfg: ContainerCfg,
    item_cfg: ItemCfg,
    fix_cfg: FixCfg,
    *,
    child_name: str = "Mira",
    child_gender: str = "girl",
    caregiver_type: str = "mother",
    trait: str = "careful",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, attrs={"trait": trait}))
    caregiver = world.add(Entity(id="caregiver", kind="character", type=caregiver_type, label="the parent"))
    bridge = world.add(Entity(id="bridge", kind="thing", type="bridge", label=bridge_cfg.label, phrase=bridge_cfg.phrase))
    holder = world.add(Entity(id="holder", kind="thing", type="holder", label=container_cfg.label, phrase=container_cfg.phrase))
    item = world.add(Entity(id="item", kind="thing", type=item_cfg.item_type, label=item_cfg.label, phrase=item_cfg.phrase))

    child.id = child_name
    bridge.meters["wind"] = float(bridge_cfg.wind)
    bridge.meters["magic_strength"] = float(bridge_cfg.magic)
    holder.meters["flap_strength"] = float(container_cfg.flap_strength)
    item.meters["weight"] = float(item_cfg.weight)

    world.facts.update(
        bridge_cfg=bridge_cfg,
        container_cfg=container_cfg,
        item_cfg=item_cfg,
        fix_cfg=fix_cfg,
        child=child,
        caregiver=caregiver,
        bridge=bridge,
        holder=holder,
        item=item,
    )

    introduce(world, child, caregiver, item_cfg, container_cfg)
    foreshadow(world, child, caregiver, bridge_cfg, container_cfg)

    world.para()
    set_out(world, child, bridge_cfg, item_cfg)
    onto_bridge(world, child, bridge, bridge_cfg)

    if would_avoid(bridge_cfg, container_cfg, trait):
        hold_tight(world, child, holder, container_cfg)
        outcome = "averted"
    else:
        propagate(world, narrate=False)
        if item.meters["slipping"] >= THRESHOLD:
            slip_out(world, child, item, item_cfg)
        if item.meters["recovered"] >= THRESHOLD:
            magic_recover(world, child, bridge_cfg, item_cfg)
            outcome = "recovered"
        else:
            lose_item(world, child, bridge_cfg, item_cfg)
            outcome = "lost"

    world.para()
    return_home(world, child, caregiver, item_cfg)
    mend(world, child, caregiver, holder, fix_cfg, item_cfg, outcome)

    world.facts.update(
        outcome=outcome,
        held_tight=child.meters["holding_flap"] >= THRESHOLD,
        slipped=item.meters["slipping"] >= THRESHOLD,
        recovered=item.meters["recovered"] >= THRESHOLD,
        lost=item.meters["lost"] >= THRESHOLD,
        repaired=holder.meters["repaired"] >= THRESHOLD,
    )
    return world


BRIDGES = {
    "stone": BridgeCfg(
        id="stone",
        label="stone bridge",
        phrase="the old stone bridge",
        place="Maple Lane",
        wind=1,
        magic=2,
        shimmer="a pale silver shimmer",
        tags={"bridge", "magic", "wind"},
    ),
    "wooden": BridgeCfg(
        id="wooden",
        label="wooden bridge",
        phrase="the wooden bridge by the canal",
        place="Willow Street",
        wind=2,
        magic=2,
        shimmer="golden ripples of light",
        tags={"bridge", "magic", "wind"},
    ),
    "red": BridgeCfg(
        id="red",
        label="red footbridge",
        phrase="the little red footbridge",
        place="Cherry Path",
        wind=2,
        magic=1,
        shimmer="a tiny rosy gleam",
        tags={"bridge", "magic", "wind"},
    ),
}

CONTAINERS = {
    "envelope": ContainerCfg(
        id="envelope",
        label="envelope",
        phrase="a cheapo paper envelope",
        flap_word="paper flap",
        flap_strength=0,
        holds={"flat"},
        tags={"cheapo", "flap", "paper"},
    ),
    "folder": ContainerCfg(
        id="folder",
        label="folder",
        phrase="a cheapo homework folder",
        flap_word="cardboard flap",
        flap_strength=0,
        holds={"flat"},
        tags={"cheapo", "flap", "paper"},
    ),
    "purse": ContainerCfg(
        id="purse",
        label="coin purse",
        phrase="a cheapo vinyl coin purse",
        flap_word="snappy flap",
        flap_strength=1,
        holds={"coin", "card"},
        tags={"cheapo", "flap", "purse"},
    ),
}

ITEMS = {
    "library_card": ItemCfg(
        id="library_card",
        label="the library card",
        phrase="the library card",
        item_type="card",
        weight=1,
        purpose="so a book could be checked out before dinner",
        if_lost="We'll stop by the library together and ask for a new card.",
        tags={"library", "card"},
    ),
    "seed_packet": ItemCfg(
        id="seed_packet",
        label="the seed packet",
        phrase="a seed packet for the window box",
        item_type="flat",
        weight=1,
        purpose="so the windowsill could have something green by spring",
        if_lost="We'll buy another seed packet, and next time we'll carry it better.",
        tags={"seeds", "garden"},
    ),
    "drawing": ItemCfg(
        id="drawing",
        label="the drawing",
        phrase="a folded drawing for Aunt June",
        item_type="flat",
        weight=1,
        purpose="so Aunt June could hang it on her fridge",
        if_lost="We'll make a fresh drawing together after supper.",
        tags={"drawing", "gift"},
    ),
    "cookie_coin": ItemCfg(
        id="cookie_coin",
        label="the cookie coin",
        phrase="one shiny coin for the bakery",
        item_type="coin",
        weight=2,
        purpose="so a sesame bun could come home warm in a paper bag",
        if_lost="I have one more coin in the blue jar, and we'll start again.",
        tags={"coin", "bakery"},
    ),
}

FIXES = {
    "star_sticker": FixCfg(
        id="star_sticker",
        label="star sticker",
        phrase="a silver star sticker",
        sense=2,
        works_for={"envelope", "folder"},
        action="sealed the flap neatly shut",
        ending="The cheapo holder looked plain no more. The tiny star winked each time it caught the light.",
        tags={"sticker", "repair"},
    ),
    "paper_clip": FixCfg(
        id="paper_clip",
        label="paper clip",
        phrase="a striped paper clip",
        sense=2,
        works_for={"envelope", "folder"},
        action="clipped the flap snug without tearing the paper",
        ending="The flap sat still at last, as if it had learned some manners.",
        tags={"clip", "repair"},
    ),
    "snap_patch": FixCfg(
        id="snap_patch",
        label="snap patch",
        phrase="a little snap patch",
        sense=2,
        works_for={"purse"},
        action="pressed a firmer snap onto the flap",
        ending="After that, the cheapo purse gave one tidy click instead of a wobbly flap.",
        tags={"snap", "repair"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Tess", "Ivy", "June", "Ella", "Maya"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Ben", "Eli", "Finn", "Noah", "Sam"]
TRAITS = ["careful", "patient", "tidy", "dreamy", "hurried", "chatty"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for bridge_id, bridge in BRIDGES.items():
        for container_id, container in CONTAINERS.items():
            if story_risk(bridge, container) <= 0:
                continue
            for item_id, item in ITEMS.items():
                if not item_fits(container, item):
                    continue
                for fix_id, fix in FIXES.items():
                    if fix_compatible(container, fix):
                        combos.append((bridge_id, container_id, item_id, fix_id))
    return combos


@dataclass
class StoryParams:
    bridge: str
    container: str
    item: str
    fix: str
    child_name: str
    child_gender: str
    caregiver: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "bridge": [
        (
            "What is a bridge?",
            "A bridge is something built to help people cross over water, a road, or another gap without going through it."
        )
    ],
    "wind": [
        (
            "Why can wind bother loose paper or a flap?",
            "Wind pushes on light things very easily. If a flap is loose, the wind can lift it and let the thing inside slip out."
        )
    ],
    "magic": [
        (
            "What is magic in a story like this?",
            "Magic is something surprising that cannot happen in ordinary life, like a bridge giving a lost paper a gentle push home. In stories, magic often helps people notice what matters."
        )
    ],
    "library": [
        (
            "What is a library card for?",
            "A library card helps you borrow books from the library. It shows that the books belong to you for a little while and then should be brought back."
        )
    ],
    "seeds": [
        (
            "What is a seed packet?",
            "A seed packet holds tiny seeds that can grow into plants. People keep the packet dry so the seeds stay safe until planting time."
        )
    ],
    "drawing": [
        (
            "Why do people give drawings as gifts?",
            "A drawing can be a gift because someone made it with time and care. Even simple paper can feel special when it comes from a person you love."
        )
    ],
    "coin": [
        (
            "What is a coin?",
            "A coin is a small round piece of money. It is heavier than a piece of paper, so wind cannot carry it the same way."
        )
    ],
    "repair": [
        (
            "Why fix a loose flap instead of only hoping for the best?",
            "Fixing the flap changes the real problem, so the same trouble is less likely next time. Hope feels nice, but a repair helps in a practical way."
        )
    ],
}
KNOWLEDGE_ORDER = ["bridge", "wind", "magic", "library", "seeds", "drawing", "coin", "repair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item_cfg = f["item_cfg"]
    bridge_cfg = f["bridge_cfg"]
    container_cfg = f["container_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a gentle slice-of-life story for a 3-to-5-year-old that includes the words "cheapo", "bridge", and "flap", with a tiny touch of magic.',
            f"Tell a story about {child.label if child.label else child.id} carrying {item_cfg.phrase} in {container_cfg.phrase}, remembering a warning on {bridge_cfg.phrase}, and preventing trouble before it starts.",
            "Write a foreshadowing story where an ordinary warning about a loose flap matters later, and the ending feels calm and homely.",
        ]
    if outcome == "recovered":
        return [
            'Write a slice-of-life story for a young child that includes the words "cheapo", "bridge", and "flap", plus one magical moment.',
            f"Tell a story where a child crossing {bridge_cfg.phrase} almost loses {item_cfg.phrase}, but the bridge itself seems to help.",
            "Write a gentle foreshadowing story in which a small warning at the door blooms into a magical rescue on a breezy walk.",
        ]
    return [
        'Write a soft, child-facing story that includes the words "cheapo", "bridge", and "flap", with a mild magical touch and a warm ending at home.',
        f"Tell a story where a child loses {item_cfg.phrase} on {bridge_cfg.phrase}, then goes home and is helped kindly instead of scolded.",
        "Write a slice-of-life story where foreshadowing comes from a grown-up noticing a loose flap before the walk.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    bridge_cfg = f["bridge_cfg"]
    container_cfg = f["container_cfg"]
    item_cfg = f["item_cfg"]
    fix_cfg = f["fix_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was trusted with {item_cfg.phrase}, and {caregiver.label_word} who noticed the problem with the cheapo holder."
        ),
        (
            "What warning came at the beginning of the story?",
            f"{caregiver.label_word.capitalize()} noticed that the {container_cfg.flap_word} kept lifting and told {child.id} to hold it tight on the bridge. That warning mattered because the bridge was breezy."
        ),
        (
            f"Why was the bridge important in this story?",
            f"The bridge was where the breeze made the loose flap dangerous. It was also the place where the story's little bit of magic showed itself."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"How did {child.id} stop the problem before anything was lost?",
                f"{child.id} remembered the warning and pinched the flap closed before the breeze could pull it open. Because {child.pronoun()} acted in time, the item stayed safe and the bridge's magic did not need to step in."
            )
        )
    elif outcome == "recovered":
        qa.append(
            (
                f"What happened when {item_cfg.label} slipped out?",
                f"It began to slip away on the bridge, but the bridge's magic nudged it back toward {child.id}. The earlier warning explains why the trouble started, and the magical push explains how it was solved."
            )
        )
    else:
        qa.append(
            (
                f"Why was {item_cfg.label} lost even though there was some magic on the bridge?",
                f"The bridge had only a little magic, and {item_cfg.label} was too heavy for it to lift back. So the item was lost, but the grown-up still helped kindly afterward."
            )
        )
    qa.append(
        (
            "How was the ending different from the beginning?",
            f"At the start, the cheapo holder had a loose flap that could not be trusted. By the end, {caregiver.label_word} had used {fix_cfg.label} to mend it, so the last image shows a small real change in everyday life."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["bridge_cfg"].tags) | set(f["item_cfg"].tags) | set(f["fix_cfg"].tags)
    out: list[tuple[str, str]] = []
    if "bridge" in tags:
        out.extend(KNOWLEDGE["bridge"])
    if "wind" in tags:
        out.extend(KNOWLEDGE["wind"])
    if "magic" in tags:
        out.extend(KNOWLEDGE["magic"])
    for tag in ["library", "seeds", "drawing", "coin"]:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    out.extend(KNOWLEDGE["repair"])
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    lines.append(f"  outcome: {world.facts.get('outcome')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        bridge="stone",
        container="envelope",
        item="seed_packet",
        fix="star_sticker",
        child_name="Mira",
        child_gender="girl",
        caregiver="mother",
        trait="careful",
    ),
    StoryParams(
        bridge="wooden",
        container="folder",
        item="drawing",
        fix="paper_clip",
        child_name="Owen",
        child_gender="boy",
        caregiver="father",
        trait="dreamy",
    ),
    StoryParams(
        bridge="red",
        container="purse",
        item="cookie_coin",
        fix="snap_patch",
        child_name="Lina",
        child_gender="girl",
        caregiver="mother",
        trait="chatty",
    ),
]


def explain_rejection(bridge_id: str, container_id: str, item_id: str, fix_id: str) -> str:
    bridge = BRIDGES.get(bridge_id)
    container = CONTAINERS.get(container_id)
    item = ITEMS.get(item_id)
    fix = FIXES.get(fix_id)
    if bridge and container and story_risk(bridge, container) <= 0:
        return (
            f"(No story: {container.phrase} would stay shut well enough on {bridge.phrase}, "
            f"so there is no real bridge-flap problem to tell.)"
        )
    if container and item and not item_fits(container, item):
        return (
            f"(No story: {item.phrase} does not sensibly belong in {container.phrase}. "
            f"Pick an item the holder can actually carry.)"
        )
    if container and fix and not fix_compatible(container, fix):
        return (
            f"(No story: {fix.label} is not a sensible repair for {container.phrase}. "
            f"Use a fix that really works for that holder.)"
        )
    return "(No story: this combination is not part of the world model.)"


ASP_RULES = r"""
risky(B, C) :- bridge(B), container(C), wind(B, W), flap_strength(C, F), W > F.
valid(B, C, I, Fx) :- bridge(B), container(C), item(I), fix(Fx),
                      risky(B, C), holds(C, T), item_type(I, T), works_for(Fx, C).

watchful(T) :- trait(T), watchful_trait(T).
avoid(B, C, T) :- risky(B, C), watchful(T), wind(B, W), flap_strength(C, F), W - F <= 1.

outcome(averted) :- chosen_bridge(B), chosen_container(C), trait(T), avoid(B, C, T).
outcome(recovered) :- chosen_bridge(B), chosen_container(C), chosen_item(I),
                      not avoid(B, C, T), trait(T),
                      magic(B, M), weight(I, W), M >= W.
outcome(lost) :- chosen_bridge(B), chosen_container(C), chosen_item(I),
                 not avoid(B, C, T), trait(T),
                 magic(B, M), weight(I, W), M < W.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for bridge_id, bridge in BRIDGES.items():
        lines.append(asp.fact("bridge", bridge_id))
        lines.append(asp.fact("wind", bridge_id, bridge.wind))
        lines.append(asp.fact("magic", bridge_id, bridge.magic))
    for container_id, container in CONTAINERS.items():
        lines.append(asp.fact("container", container_id))
        lines.append(asp.fact("flap_strength", container_id, container.flap_strength))
        for hold in sorted(container.holds):
            lines.append(asp.fact("holds", container_id, hold))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_type", item_id, item.item_type))
        lines.append(asp.fact("weight", item_id, item.weight))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for works in sorted(fix.works_for):
            lines.append(asp.fact("works_for", fix_id, works))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait", trait))
    for trait in sorted(WATCHFUL_TRAITS):
        lines.append(asp.fact("watchful_trait", trait))
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
            asp.fact("chosen_bridge", params.bridge),
            asp.fact("chosen_container", params.container),
            asp.fact("chosen_item", params.item),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print("resolve_params failed during verify.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A slice-of-life story world about a cheapo holder, a loose flap, and a magical bridge."
    )
    ap.add_argument("--bridge", choices=sorted(BRIDGES))
    ap.add_argument("--container", choices=sorted(CONTAINERS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.bridge and args.container and story_risk(BRIDGES[args.bridge], CONTAINERS[args.container]) <= 0:
        item_id = args.item or next(iter(ITEMS))
        fix_id = args.fix or next(iter(FIXES))
        raise StoryError(explain_rejection(args.bridge, args.container, item_id, fix_id))
    if args.container and args.item and not item_fits(CONTAINERS[args.container], ITEMS[args.item]):
        bridge_id = args.bridge or next(iter(BRIDGES))
        fix_id = args.fix or next(iter(FIXES))
        raise StoryError(explain_rejection(bridge_id, args.container, args.item, fix_id))
    if args.container and args.fix and not fix_compatible(CONTAINERS[args.container], FIXES[args.fix]):
        bridge_id = args.bridge or next(iter(BRIDGES))
        item_id = args.item or next(iter(ITEMS))
        raise StoryError(explain_rejection(bridge_id, args.container, item_id, args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.bridge is None or combo[0] == args.bridge)
        and (args.container is None or combo[1] == args.container)
        and (args.item is None or combo[2] == args.item)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    bridge_id, container_id, item_id, fix_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        bridge=bridge_id,
        container=container_id,
        item=item_id,
        fix=fix_id,
        child_name=name,
        child_gender=gender,
        caregiver=caregiver,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.bridge not in BRIDGES:
        raise StoryError(f"(Unknown bridge: {params.bridge})")
    if params.container not in CONTAINERS:
        raise StoryError(f"(Unknown container: {params.container})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if not item_fits(CONTAINERS[params.container], ITEMS[params.item]):
        raise StoryError(explain_rejection(params.bridge, params.container, params.item, params.fix))
    if not fix_compatible(CONTAINERS[params.container], FIXES[params.fix]):
        raise StoryError(explain_rejection(params.bridge, params.container, params.item, params.fix))
    if story_risk(BRIDGES[params.bridge], CONTAINERS[params.container]) <= 0:
        raise StoryError(explain_rejection(params.bridge, params.container, params.item, params.fix))

    world = tell(
        BRIDGES[params.bridge],
        CONTAINERS[params.container],
        ITEMS[params.item],
        FIXES[params.fix],
        child_name=params.child_name,
        child_gender=params.child_gender,
        caregiver_type=params.caregiver,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (bridge, container, item, fix) combos:\n")
        for bridge_id, container_id, item_id, fix_id in combos:
            print(f"  {bridge_id:7} {container_id:9} {item_id:12} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.container} over {p.bridge} with {p.item} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
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
