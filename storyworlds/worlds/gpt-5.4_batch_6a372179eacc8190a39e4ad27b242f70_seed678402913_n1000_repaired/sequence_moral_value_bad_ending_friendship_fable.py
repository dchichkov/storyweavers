#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sequence_moral_value_bad_ending_friendship_fable.py
===============================================================================

A standalone storyworld for a small fable about friendship, patience, and a safe
sequence of shared actions. Two animal friends agree on an order for crossing an
obstacle with food. One breaks the sequence out of selfish hurry, the food is
lost, and the friendship is tested. Some variants mend the friendship; others
end badly, with the friends walking home apart.

The world is intentionally narrow. It prefers a few plausible fable-like
variants over weak coverage. The key reasonableness gate is this:

* the obstacle, cargo, and crossing method must fit together;
* the chosen combination must also be vulnerable to a rushed shortcut, so the
  broken sequence can honestly cause trouble.

Run it
------
    python storyworlds/worlds/gpt-5.4/sequence_moral_value_bad_ending_friendship_fable.py
    python storyworlds/worlds/gpt-5.4/sequence_moral_value_bad_ending_friendship_fable.py --all
    python storyworlds/worlds/gpt-5.4/sequence_moral_value_bad_ending_friendship_fable.py --qa
    python storyworlds/worlds/gpt-5.4/sequence_moral_value_bad_ending_friendship_fable.py --trace
    python storyworlds/worlds/gpt-5.4/sequence_moral_value_bad_ending_friendship_fable.py --asp
    python storyworlds/worlds/gpt-5.4/sequence_moral_value_bad_ending_friendship_fable.py --verify
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
        table = {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }
        return table[case]


@dataclass
class PathCfg:
    id: str
    label: str
    phrase: str
    place_line: str
    kind: str
    shaky: bool = False
    sequence_hint: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class CargoCfg:
    id: str
    label: str
    phrase: str
    food_word: str
    fragile: bool = False
    weight: int = 1
    sink_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class MethodCfg:
    id: str
    label: str
    phrase: str
    strength: int = 1
    kinds: set[str] = field(default_factory=set)
    first_step: str = ""
    second_step: str = ""
    third_step: str = ""
    calm_line: str = ""
    rush_fail: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class AftermathCfg:
    id: str
    label: str
    action_line: str
    repair: bool = False
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


def _r_spill_loss(world: World) -> list[str]:
    cargo = world.entities.get("cargo")
    if cargo is None or cargo.meters["spilled"] < THRESHOLD:
        return []
    sig = ("spill_loss", cargo.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["lost"] += 1
    for ent in list(world.entities.values()):
        if ent.role in {"impatient", "friend"}:
            ent.meters["hungry"] += 1
            ent.memes["sad"] += 1
    return []


def _r_broken_sequence(world: World) -> list[str]:
    imp = world.entities.get("imp")
    pal = world.entities.get("pal")
    if imp is None or pal is None or imp.memes["broke_sequence"] < THRESHOLD:
        return []
    sig = ("broken_sequence", imp.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pal.memes["hurt"] += 1
    imp.memes["guilt_seed"] += 1
    return []


def _r_blame_frays(world: World) -> list[str]:
    imp = world.entities.get("imp")
    pal = world.entities.get("pal")
    if imp is None or pal is None:
        return []
    if imp.memes["blame"] < THRESHOLD or pal.memes["hurt"] < THRESHOLD:
        return []
    sig = ("blame_frays", imp.id, pal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    imp.memes["friendship_frayed"] += 1
    pal.memes["friendship_frayed"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="spill_loss", tag="physical", apply=_r_spill_loss),
    Rule(name="broken_sequence", tag="social", apply=_r_broken_sequence),
    Rule(name="blame_frays", tag="social", apply=_r_blame_frays),
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
        for sent in produced:
            world.say(sent)
    return produced


PATHS = {
    "brook_log": PathCfg(
        id="brook_log",
        label="brook",
        phrase="a narrow log across a brook",
        place_line="At the edge of the wood, a brook ran quick and clear under a narrow log.",
        kind="log",
        shaky=True,
        sequence_hint="one friend had to steady the log while the other crossed",
        tags={"water", "brook", "log"},
    ),
    "reed_bridge": PathCfg(
        id="reed_bridge",
        label="reed bridge",
        phrase="a thin bridge of woven reeds",
        place_line="Beyond the rushes stood a thin bridge of woven reeds over a marshy channel.",
        kind="bridge",
        shaky=True,
        sequence_hint="light feet and a careful order kept the bridge from wobbling",
        tags={"marsh", "bridge"},
    ),
    "stone_crossing": PathCfg(
        id="stone_crossing",
        label="stepping stones",
        phrase="a line of stepping stones across the stream",
        place_line="Farther on, flat stones made a path across the stream.",
        kind="stones",
        shaky=False,
        sequence_hint="the basket had to be passed paw to paw before the last hop",
        tags={"stream", "stones"},
    ),
}

CARGOES = {
    "berry_basket": CargoCfg(
        id="berry_basket",
        label="berry basket",
        phrase="a willow basket full of blackberries",
        food_word="blackberries",
        fragile=True,
        weight=1,
        sink_line="The berries splashed into the water and spun away like little purple boats.",
        tags={"berries", "basket", "fragile_food"},
    ),
    "honey_pot": CargoCfg(
        id="honey_pot",
        label="honey pot",
        phrase="a clay pot of honey",
        food_word="honey",
        fragile=True,
        weight=2,
        sink_line="The pot cracked on a stone, and golden honey ran into the mud.",
        tags={"honey", "pot", "fragile_food"},
    ),
    "nut_bundle": CargoCfg(
        id="nut_bundle",
        label="nut bundle",
        phrase="a bundle of hazelnuts tied in leaves",
        food_word="hazelnuts",
        fragile=False,
        weight=2,
        sink_line="The leaves burst apart, and the hazelnuts bounced into the reeds where no small paw could find them all.",
        tags={"nuts", "bundle"},
    ),
}

METHODS = {
    "steady_then_pass": MethodCfg(
        id="steady_then_pass",
        label="steady then pass",
        phrase="steady the way first and pass the food second",
        strength=2,
        kinds={"log", "bridge"},
        first_step="First one friend would brace the crossing with both feet.",
        second_step="Next the other would pass the food across with slow, careful paws.",
        third_step="Last they would cross in turn.",
        calm_line="When they kept to that order, the crossing stayed quiet under them.",
        rush_fail="The sudden lunge made the crossing twist before anyone was ready.",
        tags={"sequence", "careful_order"},
    ),
    "paw_to_paw": MethodCfg(
        id="paw_to_paw",
        label="paw to paw",
        phrase="pass the food paw to paw before hopping after it",
        strength=1,
        kinds={"stones"},
        first_step="First the friend in front would find a firm stone.",
        second_step="Next the food would travel paw to paw across the gap.",
        third_step="Last the second friend would hop after it.",
        calm_line="That order kept both paws and supper balanced.",
        rush_fail="A hurried leap came before the food was settled.",
        tags={"sequence", "passing"},
    ),
    "tail_rope": MethodCfg(
        id="tail_rope",
        label="tail rope",
        phrase="loop a vine like a tail rope and guide the load across",
        strength=2,
        kinds={"log", "stones"},
        first_step="First they would loop a vine around the load.",
        second_step="Next one friend would guide the vine while the other crossed lightly.",
        third_step="Last they would pull the food over and follow together.",
        calm_line="Used gently, the vine kept the load from slipping.",
        rush_fail="The vine jerked hard, and the load swung the wrong way.",
        tags={"vine", "sequence"},
    ),
}

AFTERMATHS = {
    "blame": AftermathCfg(
        id="blame",
        label="blame",
        action_line='Instead of saying sorry, the impatient friend snapped, "If you had moved faster, nothing would have fallen."',
        repair=False,
        tags={"blame", "bad_ending"},
    ),
    "sulk": AftermathCfg(
        id="sulk",
        label="sulk",
        action_line="Instead of helping, the impatient friend turned away and sat with a hard face under a dock leaf.",
        repair=False,
        tags={"sulk", "bad_ending"},
    ),
    "apology": AftermathCfg(
        id="apology",
        label="apology",
        action_line='The impatient friend bowed a low head and said, "I broke our plan. I was wrong, and I am sorry."',
        repair=True,
        tags={"apology", "repair"},
    ),
}

ANIMALS = [
    ("Pip", "squirrel"),
    ("Moss", "turtle"),
    ("Lark", "mouse"),
    ("Fern", "rabbit"),
    ("Wren", "hedgehog"),
    ("Ash", "fox"),
    ("Clover", "otter"),
    ("Juniper", "badger"),
]


def method_fits(path: PathCfg, cargo: CargoCfg, method: MethodCfg) -> bool:
    return path.kind in method.kinds and method.strength >= cargo.weight


def rush_is_risky(path: PathCfg, cargo: CargoCfg) -> bool:
    return path.shaky or cargo.fragile


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for path_id, path in PATHS.items():
        for cargo_id, cargo in CARGOES.items():
            for method_id, method in METHODS.items():
                if method_fits(path, cargo, method) and rush_is_risky(path, cargo):
                    combos.append((path_id, cargo_id, method_id))
    return sorted(combos)


@dataclass
class StoryParams:
    path: str
    cargo: str
    method: str
    aftermath: str
    impatient_name: str
    impatient_kind: str
    friend_name: str
    friend_kind: str
    moral_tone: str = "plain"
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        path="brook_log",
        cargo="berry_basket",
        method="steady_then_pass",
        aftermath="blame",
        impatient_name="Pip",
        impatient_kind="squirrel",
        friend_name="Moss",
        friend_kind="turtle",
        moral_tone="plain",
    ),
    StoryParams(
        path="reed_bridge",
        cargo="honey_pot",
        method="steady_then_pass",
        aftermath="sulk",
        impatient_name="Ash",
        impatient_kind="fox",
        friend_name="Fern",
        friend_kind="rabbit",
        moral_tone="stern",
    ),
    StoryParams(
        path="stone_crossing",
        cargo="berry_basket",
        method="paw_to_paw",
        aftermath="blame",
        impatient_name="Clover",
        impatient_kind="otter",
        friend_name="Lark",
        friend_kind="mouse",
        moral_tone="plain",
    ),
    StoryParams(
        path="brook_log",
        cargo="nut_bundle",
        method="tail_rope",
        aftermath="sulk",
        impatient_name="Juniper",
        impatient_kind="badger",
        friend_name="Wren",
        friend_kind="hedgehog",
        moral_tone="plain",
    ),
    StoryParams(
        path="stone_crossing",
        cargo="berry_basket",
        method="tail_rope",
        aftermath="apology",
        impatient_name="Fern",
        impatient_kind="rabbit",
        friend_name="Pip",
        friend_kind="squirrel",
        moral_tone="gentle",
    ),
]


def explain_rejection(path: PathCfg, cargo: CargoCfg, method: MethodCfg) -> str:
    if path.kind not in method.kinds:
        return (
            f"(No story: {method.label} does not suit {path.phrase}. "
            f"Pick a crossing method that actually fits that kind of path.)"
        )
    if method.strength < cargo.weight:
        return (
            f"(No story: {cargo.phrase} is too heavy for {method.label}. "
            f"The method must be strong enough to carry the load.)"
        )
    if not rush_is_risky(path, cargo):
        return (
            f"(No story: rushing with {cargo.label} across {path.label} would not "
            f"plausibly cause trouble here, so the broken sequence would feel weak.)"
        )
    return "(No story: this combination does not make a good fable.)"


def outcome_of(params: StoryParams) -> str:
    aftermath = AFTERMATHS[params.aftermath]
    return "mended" if aftermath.repair else "parted"


def predict_spill(world: World, path: PathCfg, cargo: CargoCfg, method: MethodCfg) -> bool:
    sim = world.copy()
    imp = sim.get("imp")
    do_rush(sim, imp, path, cargo, method, narrate=False)
    return sim.get("cargo").meters["spilled"] >= THRESHOLD


def introduce(world: World, imp: Entity, pal: Entity) -> None:
    world.say(
        f"In a green wood lived {imp.id} the {imp.type} and {pal.id} the {pal.type}. "
        f"They were friends, and each liked best a meal shared with the other."
    )


def find_food(world: World, cargo: CargoCfg, path: PathCfg) -> None:
    world.say(
        f"One afternoon they found {cargo.phrase} on the far side of {path.phrase}. "
        f"{path.place_line}"
    )


def make_plan(world: World, imp: Entity, pal: Entity, path: PathCfg, method: MethodCfg) -> None:
    imp.memes["trust"] += 1
    pal.memes["trust"] += 1
    imp.memes["hope"] += 1
    pal.memes["hope"] += 1
    world.say(
        f'Together they chose a careful plan: {method.phrase}. "{method.first_step} '
        f'{method.second_step} {method.third_step}"'
    )
    world.say(
        f"It was a simple sequence, and {pal.id} said that good friends honor the agreed order. "
        f"{method.calm_line}"
    )
    world.facts["sequence_text"] = f"{method.first_step} {method.second_step} {method.third_step}"


def temptation(world: World, imp: Entity, cargo: CargoCfg) -> None:
    imp.memes["greed"] += 1
    world.say(
        f"But the smell of {cargo.food_word} rose sweet into the air, and {imp.id}'s thoughts ran ahead of {imp.pronoun('object')}."
    )
    world.say(
        f'{imp.id} glanced at the food and said, "Why wait for all that? I can be there first."'
    )


def warning(world: World, pal: Entity, imp: Entity, path: PathCfg, cargo: CargoCfg, method: MethodCfg) -> None:
    risky = predict_spill(world, path, cargo, method)
    world.facts["predicted_spill"] = risky
    if risky:
        pal.memes["care"] += 1
        world.say(
            f'{pal.id} shook {pal.pronoun("possessive")} head. "Do not break the sequence," {pal.pronoun()} said. '
            f'"When friends rush ahead of each other, they may lose more than supper."'
        )


def do_rush(world: World, imp: Entity, path: PathCfg, cargo: CargoCfg, method: MethodCfg, narrate: bool = True) -> None:
    cargo_ent = world.get("cargo")
    imp.memes["broke_sequence"] += 1
    cargo_ent.meters["rushed"] += 1
    cargo_ent.meters["spilled"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"Yet {imp.id} sprang forward with the {cargo.label} before the first step had been finished. "
            f"{method.rush_fail}"
        )


def spill_scene(world: World, cargo: CargoCfg) -> None:
    world.say(cargo.sink_line)
    world.say(
        "In one breath the shared feast was gone, and the hungry quiet after it felt larger than the path itself."
    )


def aftermath_scene(world: World, imp: Entity, pal: Entity, aftermath: AftermathCfg) -> None:
    if aftermath.repair:
        imp.memes["apology"] += 1
        pal.memes["forgiveness"] += 1
        imp.memes["friendship_mended"] += 1
        pal.memes["friendship_mended"] += 1
    else:
        imp.memes["blame"] += 1
        propagate(world, narrate=False)
    world.say(aftermath.action_line)
    if aftermath.repair:
        world.say(
            f"{pal.id} was still sad, but {pal.pronoun()} heard the truth in the words and stayed beside {imp.id}."
        )
    else:
        world.say(
            f"{pal.id} lowered {pal.pronoun('possessive')} eyes. The empty place where the food had been hurt less than the broken kindness."
        )


def ending_bad(world: World, imp: Entity, pal: Entity, path: PathCfg, tone: str) -> None:
    world.say(
        f"So the two friends went home by different ways, with empty bellies and heavier hearts than when they had come to {path.label}."
    )
    if tone == "stern":
        world.say(
            f"That night no lamp shone in a shared window, and no one spoke the old cheerful call across the grass."
        )
    else:
        world.say(
            f"Evening found {imp.id} alone on one side of the wood and {pal.id} alone on the other, and friendship was thinner than the supper they had lost."
        )
    world.say(
        "Thus the wood remembered: a selfish hurry can break both a meal and a friend."
    )


def ending_mended(world: World, imp: Entity, pal: Entity, tone: str) -> None:
    world.say(
        f"They did not get the feast they had hoped for, but they gathered a few dry acorns and ate them together under an elder bush."
    )
    if tone == "gentle":
        world.say(
            f"The meal was small, yet it tasted better than rich food eaten alone, because truth had sat down beside them."
        )
    else:
        world.say(
            f"It was a plain supper, but the two friends kept each other company, and that was better than sulking apart."
        )
    world.say(
        "Thus the wood remembered: friends may stumble, but honest sorrow can still lead them back to one another."
    )


def tell(
    path: PathCfg,
    cargo: CargoCfg,
    method: MethodCfg,
    aftermath: AftermathCfg,
    impatient_name: str,
    impatient_kind: str,
    friend_name: str,
    friend_kind: str,
    moral_tone: str,
) -> World:
    world = World()
    imp = world.add(Entity(id="imp", kind="character", type=impatient_kind, label=impatient_name, role="impatient"))
    pal = world.add(Entity(id="pal", kind="character", type=friend_kind, label=friend_name, role="friend"))
    cargo_ent = world.add(Entity(id="cargo", kind="thing", type="food", label=cargo.label, phrase=cargo.phrase))
    imp.id = impatient_name
    pal.id = friend_name
    world.entities["imp"] = imp
    world.entities["pal"] = pal
    world.entities["cargo"] = cargo_ent

    introduce(world, imp, pal)
    find_food(world, cargo, path)
    world.para()
    make_plan(world, imp, pal, path, method)
    temptation(world, imp, cargo)
    warning(world, pal, imp, path, cargo, method)
    world.para()
    do_rush(world, imp, path, cargo, method, narrate=True)
    spill_scene(world, cargo)
    world.para()
    aftermath_scene(world, imp, pal, aftermath)
    world.para()
    if aftermath.repair:
        ending_mended(world, imp, pal, moral_tone)
    else:
        ending_bad(world, imp, pal, path, moral_tone)

    world.facts.update(
        path=path,
        cargo_cfg=cargo,
        method=method,
        aftermath=aftermath,
        impatient=imp,
        friend=pal,
        cargo=cargo_ent,
        outcome="mended" if aftermath.repair else "parted",
        moral_tone=moral_tone,
        food_lost=cargo_ent.meters["lost"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "sequence": [
        (
            "What is a sequence?",
            "A sequence is an order of steps, like first, next, and last. Following the order can help friends do a hard job safely.",
        )
    ],
    "friendship": [
        (
            "Why does friendship need patience?",
            "Friendship needs patience because friends must make room for each other. If one friend always rushes or grabs first, trust gets hurt.",
        )
    ],
    "brook": [
        (
            "Why can a log over a brook be dangerous?",
            "A narrow log can wobble or roll if someone hurries on it. That makes it easy to drop what you are carrying.",
        )
    ],
    "bridge": [
        (
            "Why should you cross a thin bridge carefully?",
            "A thin bridge can sway under quick, heavy steps. Slow steps help keep your body and your load balanced.",
        )
    ],
    "stones": [
        (
            "Why do stepping stones need careful feet?",
            "Stepping stones can be slippery or uneven. Careful feet help you keep your balance from one stone to the next.",
        )
    ],
    "berries": [
        (
            "Why are berries easy to lose?",
            "Berries are small and roll away fast once they spill. Water or mud can carry them off before you can gather them again.",
        )
    ],
    "honey": [
        (
            "Why is a clay honey pot fragile?",
            "Clay can crack if it hits a hard stone. Once the pot breaks, the honey runs out and is hard to save.",
        )
    ],
    "nuts": [
        (
            "Why can a nut bundle still be lost if it is not fragile?",
            "The nuts may not break, but they can scatter in many directions. Then a small animal may not be able to find them all again.",
        )
    ],
    "apology": [
        (
            "What makes an apology honest?",
            "An honest apology admits the wrong thing clearly and does not blame someone else. It tries to mend the hurt it caused.",
        )
    ],
    "blame": [
        (
            "Why is blame bad for friendship?",
            "Blame pushes the hurt onto someone else instead of telling the truth. That makes the wound in a friendship grow deeper.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "sequence",
    "friendship",
    "brook",
    "bridge",
    "stones",
    "berries",
    "honey",
    "nuts",
    "apology",
    "blame",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    imp = f["impatient"]
    pal = f["friend"]
    cargo = f["cargo_cfg"]
    path = f["path"]
    outcome = f["outcome"]
    if outcome == "parted":
        return [
            'Write a short fable for a 3-to-5-year-old that includes the word "sequence" and teaches that selfish hurry can spoil friendship.',
            f"Tell a woodland fable where {imp.id} and {pal.id} are friends with a careful crossing plan for {cargo.phrase}, but {imp.id} breaks the sequence and the ending is sad.",
            f"Write a moral tale about two animal friends at {path.phrase} whose shared meal is lost because one of them will not wait for the agreed order.",
        ]
    return [
        'Write a short fable for a 3-to-5-year-old that includes the word "sequence" and teaches that honest apology can help friendship heal.',
        f"Tell a woodland fable where {imp.id} breaks a careful plan for carrying {cargo.phrase}, then speaks the truth and begins to mend the friendship.",
        f"Write a moral story about two animal friends at {path.phrase} who lose their feast when one rushes ahead, but end by staying together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    imp = f["impatient"]
    pal = f["friend"]
    cargo = f["cargo_cfg"]
    path = f["path"]
    method = f["method"]
    aftermath = f["aftermath"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {imp.id} the {imp.type} and {pal.id} the {pal.type}, two friends trying to carry {cargo.phrase} across {path.phrase}. Their friendship matters as much as the food.",
        ),
        (
            "What plan did the friends make?",
            f"They made a careful sequence for crossing: {world.facts.get('sequence_text', method.first_step)} Because the path and the food needed balance, the order itself was part of staying safe.",
        ),
        (
            f"Why did {pal.id} tell {imp.id} not to rush?",
            f"{pal.id} could see that breaking the sequence would make the crossing unsafe. The trouble came from hurrying before the careful steps had been finished.",
        ),
        (
            f"What happened when {imp.id} rushed ahead?",
            f"The food spilled and the shared meal was lost. That physical loss also hurt the friendship, because {imp.id} broke the plan both friends had trusted.",
        ),
    ]
    if outcome == "parted":
        qa.append(
            (
                f"Why did the ending become a bad ending for the friends?",
                f"The ending turned bad because {imp.id} did not stop at losing the food; {imp.pronoun()} also {aftermath.label}d the friendship instead of caring for it. After the accident, unkindness made the two friends walk home apart.",
            )
        )
        qa.append(
            (
                "What is the moral of the story?",
                "The moral is that selfish hurry and blame can break more than a basket or a pot. They can also break trust between friends.",
            )
        )
    else:
        qa.append(
            (
                f"How did the friends begin to mend the problem?",
                f"{imp.id} admitted the wrong and apologized instead of blaming {pal.id}. The food was still gone, but truthful sorrow kept the friendship from being lost too.",
            )
        )
        qa.append(
            (
                "What is the moral of the story?",
                "The moral is that rushing ahead hurts friendship, but an honest apology can begin to mend the hurt. Good friends need truth as much as they need food.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"sequence", "friendship"}
    path = f["path"]
    cargo = f["cargo_cfg"]
    aftermath = f["aftermath"]
    if "brook" in path.tags:
        tags.add("brook")
    if "bridge" in path.tags:
        tags.add("bridge")
    if "stones" in path.tags:
        tags.add("stones")
    if "berries" in cargo.tags:
        tags.add("berries")
    if "honey" in cargo.tags:
        tags.add("honey")
    if "nuts" in cargo.tags:
        tags.add("nuts")
    if aftermath.repair:
        tags.add("apology")
    else:
        tags.add("blame")
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
    for key, ent in world.entities.items():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = [f"name={ent.id}", f"type={ent.type}"]
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {key:8} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(P, C, M) :- path(P), cargo(C), method(M),
                 kind(P, K), supports_kind(M, K),
                 weight(C, W), strength(M, S), S >= W.

risky(P, C) :- path(P), cargo(C), shaky(P).
risky(P, C) :- path(P), cargo(C), fragile(C).

valid(P, C, M) :- fits(P, C, M), risky(P, C).

outcome(mended) :- chosen_aftermath(A), repair(A).
outcome(parted) :- chosen_aftermath(A), not repair(A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, path in PATHS.items():
        lines.append(asp.fact("path", pid))
        lines.append(asp.fact("kind", pid, path.kind))
        if path.shaky:
            lines.append(asp.fact("shaky", pid))
    for cid, cargo in CARGOES.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("weight", cid, cargo.weight))
        if cargo.fragile:
            lines.append(asp.fact("fragile", cid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("strength", mid, method.strength))
        for kind in sorted(method.kinds):
            lines.append(asp.fact("supports_kind", mid, kind))
    for aid, aftermath in AFTERMATHS.items():
        lines.append(asp.fact("aftermath", aid))
        if aftermath.repair:
            lines.append(asp.fact("repair", aid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_aftermath", params.aftermath)
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
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcome differences.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a fable about friendship, sequence, and selfish hurry."
    )
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--aftermath", choices=AFTERMATHS)
    ap.add_argument("--tone", choices=["plain", "gentle", "stern"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def pick_animals(rng: random.Random) -> tuple[tuple[str, str], tuple[str, str]]:
    first = rng.choice(ANIMALS)
    second_choices = [a for a in ANIMALS if a != first]
    second = rng.choice(second_choices)
    return first, second


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.path and args.cargo and args.method:
        path = PATHS[args.path]
        cargo = CARGOES[args.cargo]
        method = METHODS[args.method]
        if not (method_fits(path, cargo, method) and rush_is_risky(path, cargo)):
            raise StoryError(explain_rejection(path, cargo, method))

    combos = [
        combo for combo in valid_combos()
        if (args.path is None or combo[0] == args.path)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    path_id, cargo_id, method_id = rng.choice(combos)
    tone = args.tone or rng.choice(["plain", "plain", "stern", "gentle"])
    aftermath_id = args.aftermath or rng.choice(["blame", "blame", "sulk", "apology"])
    first, second = pick_animals(rng)
    return StoryParams(
        path=path_id,
        cargo=cargo_id,
        method=method_id,
        aftermath=aftermath_id,
        impatient_name=first[0],
        impatient_kind=first[1],
        friend_name=second[0],
        friend_kind=second[1],
        moral_tone=tone,
    )


def generate(params: StoryParams) -> StorySample:
    if params.path not in PATHS:
        raise StoryError(f"(Unknown path: {params.path})")
    if params.cargo not in CARGOES:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.aftermath not in AFTERMATHS:
        raise StoryError(f"(Unknown aftermath: {params.aftermath})")

    path = PATHS[params.path]
    cargo = CARGOES[params.cargo]
    method = METHODS[params.method]
    aftermath = AFTERMATHS[params.aftermath]
    if not (method_fits(path, cargo, method) and rush_is_risky(path, cargo)):
        raise StoryError(explain_rejection(path, cargo, method))

    world = tell(
        path=path,
        cargo=cargo,
        method=method,
        aftermath=aftermath,
        impatient_name=params.impatient_name,
        impatient_kind=params.impatient_kind,
        friend_name=params.friend_name,
        friend_kind=params.friend_kind,
        moral_tone=params.moral_tone,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (path, cargo, method) combos:\n")
        for path_id, cargo_id, method_id in combos:
            print(f"  {path_id:14} {cargo_id:13} {method_id}")
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.impatient_name} and {p.friend_name}: {p.cargo} at {p.path} ({outcome_of(p)})"
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
