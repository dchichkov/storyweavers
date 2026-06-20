#!/usr/bin/env python3
"""A folk-tale storyworld about honey, a loud storm, and a crystal lamp.

Seed:
    Words: honey, loud storm, crystal lamp
    Setting: bus depot
    Features: Dialogue
    Style: Folk Tale

Internal source tale:
    In an old bus depot, a child arrives carrying something sweet made with
    honey. A loud storm darkens the depot and unsettles the waiting people just
    when the last bus must be guided in by an old crystal lamp. By sharing the
    honey first, the child calms the human trouble. Then the child and the
    keeper can mend the lamp together, and the ending image proves that warmth
    and light both returned.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass(frozen=True)
class Depot:
    id: str
    label: str
    scene: str
    storm_line: str
    hook_label: str
    supports: set[str]
    tags: set[str]


@dataclass(frozen=True)
class CrowdNeed:
    id: str
    label: str
    target_label: str
    target_kind: str
    trouble_line: str
    dialogue_line: str
    calm_line: str
    soothed_by: set[str]
    tags: set[str]


@dataclass(frozen=True)
class Comfort:
    id: str
    label: str
    item: str
    carry_line: str
    action_line: str
    dialogue_line: str
    calms: set[str]
    tags: set[str]


@dataclass(frozen=True)
class LampAct:
    id: str
    label: str
    action_line: str
    result_line: str
    advice_line: str
    tags: set[str]


@dataclass(frozen=True)
class HeroSpec:
    id: str
    name: str
    kind: str
    intro_trait: str
    village: str


@dataclass(frozen=True)
class KeeperSpec:
    id: str
    name: str
    role: str
    wisdom: str


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))
    place: Optional[str] = None
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, params: "StoryParams"):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple[object, ...]] = set()
        self.fired_names: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, sentence: str) -> None:
        sentence = sentence.strip()
        if sentence:
            self.paragraphs[-1].append(sentence)

    def break_para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = [
            f"depot: {self.params.depot}",
            f"crowd_need: {self.params.crowd_need}",
            f"comfort: {self.params.comfort}",
            f"lamp_act: {self.params.lamp_act}",
            f"fired rules: {', '.join(self.fired_names) if self.fired_names else 'none'}",
            f"facts: {dict(sorted(self.facts.items()))}",
        ]
        for ent in self.entities.values():
            bits = [f"  {ent.id} | {ent.kind} | {ent.label}"]
            if ent.place:
                bits.append(f"place={ent.place}")
            if ent.tags:
                bits.append(f"tags={sorted(ent.tags)}")
            lines.append(" | ".join(bits))
            if ent.meters:
                lines.append(f"    meters={dict(ent.meters)}")
            if ent.memes:
                lines.append(f"    memes={dict(ent.memes)}")
        return "\n".join(lines)


@dataclass(frozen=True)
class Rule:
    name: str
    apply: Callable[[World, bool], bool]


def _mark(world: World, name: str, *parts: object) -> bool:
    sig = (name, *parts)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.fired_names.append(name)
    return True


def _r_crowd_settles(world: World, narrate: bool) -> bool:
    crowd = world.get("crowd")
    target = world.get("target")
    hero = world.get("hero")
    if crowd.meters["sweetened"] < THRESHOLD or target.meters["soothed"] < THRESHOLD:
        return False
    if not _mark(world, "crowd_settles", world.params.crowd_need, world.params.comfort):
        return False
    crowd.meters["calm"] += 1
    crowd.meters["order"] += 1
    crowd.meters["fear"] = max(0.0, crowd.meters["fear"] - 1)
    hero.memes["belonging"] += 1
    world.facts["crowd_calm"] = True
    if narrate:
        need = CROWD_NEEDS[world.params.crowd_need]
        world.say(need.calm_line)
    return True


def _r_lamp_ready(world: World, narrate: bool) -> bool:
    lamp = world.get("lamp")
    crowd = world.get("crowd")
    hero = world.get("hero")
    keeper = world.get("keeper")
    if lamp.meters["repair_started"] < THRESHOLD or crowd.meters["order"] < THRESHOLD:
        return False
    if not _mark(world, "lamp_ready", world.params.lamp_act):
        return False
    lamp.meters["brightness"] += 1
    lamp.meters["visible"] += 1
    lamp.meters["steady"] += 1
    hero.memes["courage"] += 1
    keeper.memes["trust"] += 1
    world.facts["lamp_safe"] = True
    if narrate:
        lamp_act = LAMP_ACTS[world.params.lamp_act]
        world.say(lamp_act.result_line)
    return True


def _r_bus_arrives(world: World, narrate: bool) -> bool:
    lamp = world.get("lamp")
    bus = world.get("bus")
    crowd = world.get("crowd")
    if lamp.meters["visible"] < THRESHOLD or crowd.meters["calm"] < THRESHOLD:
        return False
    if not _mark(world, "bus_arrives", world.params.depot):
        return False
    bus.meters["arrived"] += 1
    bus.meters["safe_stop"] += 1
    crowd.meters["hope"] += 1
    world.facts["bus_arrived"] = True
    if narrate:
        depot = DEPOTS[world.params.depot]
        world.say(
            f"Out beyond the rain, the last bus found {depot.label} by the amber eye of the crystal lamp."
        )
    return True


RULES = [
    Rule("crowd_settles", _r_crowd_settles),
    Rule("lamp_ready", _r_lamp_ready),
    Rule("bus_arrives", _r_bus_arrives),
]


def propagate(world: World, *, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            if rule.apply(world, narrate):
                changed = True


DEPOTS = {
    "river_arch": Depot(
        "river_arch",
        "the river-arch bus depot",
        "the river-arch bus depot, where old stone arches looked toward the black water",
        "A loud storm came shouldering up the river, and the rain flew slantwise through the open arches.",
        "the high iron hook between the arches",
        {"shield_flame", "hang_high"},
        {"bus_depot", "river", "storm", "lamp"},
    ),
    "hill_stove": Depot(
        "hill_stove",
        "the hill-stove bus depot",
        "the hill-stove bus depot, where a tired stove warmed the benches when the road was kind",
        "A loud storm rolled over the hill, and every thunderclap shook old soot from the rafters.",
        "the soot-dark hook beside the stove pipe",
        {"polish_glass", "shield_flame"},
        {"bus_depot", "hill", "storm", "lamp"},
    ),
    "market_gate": Depot(
        "market_gate",
        "the market-gate bus depot",
        "the market-gate bus depot, where carts slept nearby and the ticket bell hung above the line",
        "A loud storm rattled across the square, and the doorway turned into a silver curtain of rain.",
        "the tall hook above the ticket bell",
        {"hang_high", "polish_glass"},
        {"bus_depot", "market", "storm", "lamp"},
    ),
}


CROWD_NEEDS = {
    "crying_child": CrowdNeed(
        "crying_child",
        "crying child",
        "a little boy with wet boots",
        "child",
        "Near the bench, a little boy with wet boots cried each time the thunder struck the roof.",
        '"The sky sounds like a giant drum," sobbed the boy.',
        "Soon the boy was listening instead of sobbing, and the whole line grew softer around him.",
        {"honey_spoon", "honey_cake"},
        {"child", "fear", "queue"},
    ),
    "quarreling_line": CrowdNeed(
        "quarreling_line",
        "quarreling line",
        "two farmers at the front of the line",
        "traveler_pair",
        "At the front of the queue, two farmers argued over whose boot had reached the step first.",
        '"If the storm steals my turn, I will remember it all winter," grumbled one farmer.',
        "When sweetness was shared fairly, the hard voices softened and the waiting line remembered its manners.",
        {"honey_tea", "honey_cake"},
        {"queue", "conflict", "fairness"},
    ),
    "shivering_driver": CrowdNeed(
        "shivering_driver",
        "shivering driver",
        "the driver of the last bus",
        "driver",
        "The driver of the last bus stood under the eaves, shivering so hard that his route card trembled in his hand.",
        '"I can steer through rain," said the driver, "but these cold fingers are stubborn as stones."',
        "Warmth ran back into the driver's hands, and even the waiting people stood straighter when they saw it.",
        {"honey_tea", "honey_spoon"},
        {"driver", "cold", "route"},
    ),
}


COMFORTS = {
    "honey_tea": Comfort(
        "honey_tea",
        "honey tea",
        "a dented flask of honey and a little paper packet of tea",
        "carrying a dented flask of honey and a little paper packet of tea for the road",
        "stirred hot water and honey together until sweet steam rose into the cold air",
        '"Sweetness first," said the child. "Storms lose some strength when people share warmth."',
        {"quarreling_line", "shivering_driver"},
        {"honey", "tea", "warmth"},
    ),
    "honey_cake": Comfort(
        "honey_cake",
        "honey cake",
        "a round honey cake wrapped in cloth",
        "carrying a round honey cake wrapped in cloth",
        "broke the honey cake into fair pieces and passed them from hand to hand",
        '"Take an even piece," said the child. "A shared bite makes room for patience."',
        {"crying_child", "quarreling_line"},
        {"honey", "cake", "sharing"},
    ),
    "honey_spoon": Comfort(
        "honey_spoon",
        "spoon of honey",
        "a small clay pot of honey and a wooden spoon",
        "carrying a small clay pot of honey and a wooden spoon under a shawl",
        "offered a slow spoon of honey and let its gold sweetness buy a quiet breath",
        '"Easy now," said the child. "Honey asks the heart to slow down."',
        {"crying_child", "shivering_driver"},
        {"honey", "spoon", "calm"},
    ),
}


LAMP_ACTS = {
    "shield_flame": LampAct(
        "shield_flame",
        "shield the flame",
        "The child and the keeper cupped the crystal lamp with an old route ledger and a wool cloak so the wind could not bite the flame.",
        "The crystal lamp burned low but steady, like a small star hiding in careful hands.",
        '"Hold the wind on one side and the light on the other," said the keeper.',
        {"lamp", "wind", "care"},
    ),
    "polish_glass": LampAct(
        "polish_glass",
        "polish the glass",
        "The child climbed onto the bench and wiped the crystal lamp with a dry scarf until the cloudy panels turned clear.",
        "Once the soot was gone, the crystal lamp laid clean amber squares across the depot floor.",
        '"Clear glass makes brave light," said the keeper.',
        {"lamp", "glass", "clarity"},
    ),
    "hang_high": LampAct(
        "hang_high",
        "hang it high",
        "The child and the keeper lifted the crystal lamp to the highest hook, where even the rain could not hide it from the road.",
        "From the high hook, the crystal lamp shone above every hat and bundle in the depot.",
        '"Raise the light higher than the worry," said the keeper.',
        {"lamp", "height", "signal"},
    ),
}


HEROES = {
    "mira": HeroSpec("mira", "Mira", "girl", "quick-hearted", "Reed Village"),
    "stoyan": HeroSpec("stoyan", "Stoyan", "boy", "steady-eyed", "Mill Lane"),
    "vesa": HeroSpec("vesa", "Vesa", "girl", "soft-spoken", "Willow Ford"),
}


KEEPERS = {
    "dorin": KeeperSpec("dorin", "Dorin", "depot keeper", "The road listens best to patient hands."),
    "baba_ilva": KeeperSpec("baba_ilva", "Baba Ilva", "tea seller", "Warmth reaches places that shouting never can."),
    "marin": KeeperSpec("marin", "Old Marin", "night porter", "When people stand together, even rain must step around them."),
}


PARAM_REGISTRIES = {
    "depot": DEPOTS,
    "crowd_need": CROWD_NEEDS,
    "comfort": COMFORTS,
    "lamp_act": LAMP_ACTS,
    "hero": HEROES,
    "keeper": KEEPERS,
}


@dataclass(frozen=True)
class StoryParams:
    depot: str
    crowd_need: str
    comfort: str
    lamp_act: str
    hero: str
    keeper: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("river_arch", "crying_child", "honey_cake", "hang_high", "mira", "dorin", 191),
    StoryParams("hill_stove", "shivering_driver", "honey_tea", "polish_glass", "stoyan", "baba_ilva", 192),
    StoryParams("market_gate", "quarreling_line", "honey_cake", "hang_high", "vesa", "marin", 193),
    StoryParams("river_arch", "shivering_driver", "honey_spoon", "shield_flame", "mira", "marin", 194),
]


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.depot not in DEPOTS:
        return False, f"Unknown bus depot {params.depot!r}."
    if params.crowd_need not in CROWD_NEEDS:
        return False, f"Unknown crowd need {params.crowd_need!r}."
    if params.comfort not in COMFORTS:
        return False, f"Unknown honey comfort {params.comfort!r}."
    if params.lamp_act not in LAMP_ACTS:
        return False, f"Unknown lamp act {params.lamp_act!r}."
    if params.hero not in HEROES:
        return False, f"Unknown hero {params.hero!r}."
    if params.keeper not in KEEPERS:
        return False, f"Unknown keeper {params.keeper!r}."
    depot = DEPOTS[params.depot]
    need = CROWD_NEEDS[params.crowd_need]
    comfort = COMFORTS[params.comfort]
    if params.lamp_act not in depot.supports:
        return False, f"{depot.label} does not plausibly support {LAMP_ACTS[params.lamp_act].label}."
    if params.comfort not in need.soothed_by or params.crowd_need not in comfort.calms:
        return False, f"{comfort.label} would not honestly calm the {need.label}."
    return True, ""


def all_valid_shapes() -> list[tuple[str, str, str, str]]:
    shapes: list[tuple[str, str, str, str]] = []
    for depot in DEPOTS.values():
        for need in CROWD_NEEDS.values():
            for comfort in COMFORTS.values():
                if comfort.id not in need.soothed_by:
                    continue
                for lamp_act in LAMP_ACTS.values():
                    if lamp_act.id not in depot.supports:
                        continue
                    shapes.append((depot.id, need.id, comfort.id, lamp_act.id))
    return sorted(shapes)


def explain_rejection(depot_id: str, need_id: str, comfort_id: str, lamp_act_id: str) -> str:
    probe = StoryParams(
        depot=depot_id,
        crowd_need=need_id,
        comfort=comfort_id,
        lamp_act=lamp_act_id,
        hero=next(iter(HEROES)),
        keeper=next(iter(KEEPERS)),
        seed=None,
    )
    ok, reason = valid_params(probe)
    return reason if not ok else "The requested bus-depot tale is not in the valid set."


def build_world(params: StoryParams) -> World:
    world = World(params)
    depot = DEPOTS[params.depot]
    need = CROWD_NEEDS[params.crowd_need]
    comfort = COMFORTS[params.comfort]
    hero_spec = HEROES[params.hero]
    keeper_spec = KEEPERS[params.keeper]

    hero = world.add(Entity("hero", "character", hero_spec.name, place=depot.id, tags={"hero", hero_spec.kind}))
    keeper = world.add(Entity("keeper", "character", keeper_spec.name, place=depot.id, tags={"keeper", keeper_spec.role}))
    crowd = world.add(Entity("crowd", "crowd", "the waiting line", place=depot.id, tags={"queue"}))
    storm = world.add(Entity("storm", "weather", "the loud storm", place=depot.id, tags={"storm"}))
    lamp = world.add(Entity("lamp", "object", "the crystal lamp", place=depot.id, tags={"lamp", "crystal"}))
    bus = world.add(Entity("bus", "vehicle", "the last bus", place="road", tags={"bus"}))
    honey = world.add(Entity("honey", "object", comfort.item, place=depot.id, tags={"honey"}))
    target = world.add(Entity("target", need.target_kind, need.target_label, place=depot.id, tags=set(need.tags)))

    storm.meters["noise"] = 1
    storm.meters["rain"] = 1
    crowd.meters["fear"] = 1
    crowd.meters["order"] = 0
    lamp.meters["brightness"] = 0
    lamp.meters["visible"] = 0
    bus.meters["arrived"] = 0
    hero.memes["care"] = 1
    keeper.memes["watchfulness"] = 1

    world.facts["depot_label"] = depot.label
    world.facts["hero_name"] = hero_spec.name
    world.facts["keeper_name"] = keeper_spec.name
    world.facts["crowd_calm"] = False
    world.facts["lamp_safe"] = False
    world.facts["bus_arrived"] = False
    world.facts["moral"] = "shared warmth makes room for guiding light"
    return world


def introduce(world: World) -> None:
    params = world.params
    depot = DEPOTS[params.depot]
    hero_spec = HEROES[params.hero]
    keeper_spec = KEEPERS[params.keeper]
    comfort = COMFORTS[params.comfort]
    world.say(
        f"Long ago, {hero_spec.name} of {hero_spec.village}, a {hero_spec.intro_trait} {hero_spec.kind}, came to {depot.scene}, {comfort.carry_line}."
    )
    world.say(
        f"Above the ticket window hung a crystal lamp, clear and solemn as a little frozen bell."
    )
    world.say(
        f"{keeper_spec.name}, the {keeper_spec.role}, kept watch beside the benches and often said, \"{keeper_spec.wisdom}\""
    )


def storm_trouble(world: World) -> None:
    params = world.params
    depot = DEPOTS[params.depot]
    need = CROWD_NEEDS[params.crowd_need]
    world.break_para()
    world.say(depot.storm_line)
    world.say("The depot bulbs failed all at once, and the crystal lamp became the only honest light left in the bus depot.")
    world.say(need.trouble_line)
    world.say(need.dialogue_line)
    world.say(
        f"\"If the crystal lamp stays dark,\" said {KEEPERS[params.keeper].name}, \"the last bus may pass our door and never know we are waiting.\""
    )


def share_honey(world: World) -> None:
    params = world.params
    comfort = COMFORTS[params.comfort]
    hero = world.get("hero")
    crowd = world.get("crowd")
    target = world.get("target")
    keeper = world.get("keeper")
    world.break_para()
    world.say(
        f"\"May I try my small kindness first?\" asked {hero.label}."
    )
    world.say(comfort.dialogue_line)
    world.say(f"{hero.label} {comfort.action_line}.")
    world.say(
        f"{keeper.label} nodded and stepped aside, for even old keepers know that a frightened room cannot hold a steady flame."
    )
    crowd.meters["sweetened"] += 1
    target.meters["soothed"] += 1
    hero.memes["generosity"] += 1
    keeper.memes["trust"] += 1
    world.facts["honey_shared"] = comfort.id
    propagate(world, narrate=True)


def mend_lamp(world: World) -> None:
    params = world.params
    lamp_act = LAMP_ACTS[params.lamp_act]
    lamp = world.get("lamp")
    world.break_para()
    world.say(lamp_act.advice_line)
    world.say(lamp_act.action_line)
    lamp.meters["repair_started"] += 1
    world.facts["lamp_method"] = lamp_act.id
    propagate(world, narrate=True)


def ending(world: World) -> None:
    hero = world.get("hero")
    keeper = world.get("keeper")
    comfort = COMFORTS[world.params.comfort]
    depot = DEPOTS[world.params.depot]
    world.break_para()
    world.say(
        f"People boarded in peace at {depot.label}, and not one push or sharp word followed them up the step."
    )
    world.say(
        f"{hero.label} climbed aboard with the last sweetness of {comfort.item} still on the air, while {keeper.label} lifted a hand beneath the shining crystal lamp."
    )
    world.say(
        "So the loud storm kept its thunder outside, and inside the depot the light looked warm as honey."
    )
    world.facts["ending_image"] = "honey_warm_lamp"


def tell(world: World) -> str:
    introduce(world)
    storm_trouble(world)
    share_honey(world)
    mend_lamp(world)
    ending(world)
    return world.render()


def generation_prompts(params: StoryParams) -> list[str]:
    hero = HEROES[params.hero]
    keeper = KEEPERS[params.keeper]
    return [
        "Write a Folk Tale set in a bus depot that includes honey, a loud storm, and a crystal lamp.",
        f"Write a dialogue-rich story where {hero.name} and {keeper.name} calm trouble before guiding in the last bus.",
        "Write a child-facing tale in which sweetness solves the human problem before light solves the road problem.",
    ]


def story_qa(params: StoryParams, world: World) -> list[QAItem]:
    hero = HEROES[params.hero]
    keeper = KEEPERS[params.keeper]
    need = CROWD_NEEDS[params.crowd_need]
    comfort = COMFORTS[params.comfort]
    lamp_act = LAMP_ACTS[params.lamp_act]
    depot = DEPOTS[params.depot]
    return [
        QAItem(
            f"Why did {hero.name} share {comfort.label} before fixing the lamp?",
            f"{hero.name} shared {comfort.label} because the trouble in the depot was human before it was mechanical. "
            f"Once {need.target_label} settled down, the waiting line became calm enough for the crystal lamp to be mended safely.",
        ),
        QAItem(
            f"How was the crystal lamp made useful again at {depot.label}?",
            f"The crystal lamp became useful again when {hero.name} and {keeper.name} chose to {lamp_act.label}. "
            f"That method fit the depot itself, so the light could push through the storm and be seen from the road.",
        ),
        QAItem(
            "Why was the last bus able to stop at the depot?",
            "The last bus was able to stop because the waiting people had become orderly and the lamp had become visible. "
            "The driver could trust the amber signal instead of guessing through the rain.",
        ),
        QAItem(
            "What changed by the end of the tale?",
            f"At first the bus depot was noisy, dark, and anxious under the loud storm. "
            f"By the end it was calm enough for boarding, and the crystal lamp shone warm as honey above the line.",
        ),
    ]


KNOWLEDGE = {
    "bus_depot": QAItem(
        "Why does a bus depot need a clear signal in bad weather?",
        "A bus depot needs a clear signal so a driver can recognize the stop from a distance. Rain, wind, and darkness can hide a doorway that seems obvious in daylight.",
    ),
    "lamp": QAItem(
        "Why can a crystal lamp matter during a storm?",
        "A crystal lamp can gather and spread light in a focused way. In a storm, that small clear light may be enough to guide people and vehicles safely.",
    ),
    "honey": QAItem(
        "Why is honey often linked with comfort in a tale?",
        "Honey is sweet, warm-smelling, and easy to share in small amounts. In stories, it often softens fear or harsh tempers before a harder task begins.",
    ),
    "queue": QAItem(
        "Why does a calm line matter in a crowded place?",
        "A calm line leaves room for people to help one another and see what must be done next. Pushing and arguing make every practical problem harder.",
    ),
    "storm": QAItem(
        "What makes a loud storm difficult for travelers?",
        "A loud storm hides voices, darkens roads, and frightens people who are already waiting. It can turn a simple stop into a problem of light, warmth, and patience.",
    ),
}


def world_qa(params: StoryParams) -> list[QAItem]:
    depot = DEPOTS[params.depot]
    need = CROWD_NEEDS[params.crowd_need]
    comfort = COMFORTS[params.comfort]
    lamp_act = LAMP_ACTS[params.lamp_act]
    tags = set().union(depot.tags, need.tags, comfort.tags, lamp_act.tags)
    order = ["bus_depot", "lamp", "honey", "queue", "storm"]
    return [KNOWLEDGE[key] for key in order if key in tags][:4]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = build_world(params)
    story = tell(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(params),
        story_qa=story_qa(params, world),
        world_qa=world_qa(params),
        world=world,
    )


ASP_RULES = r"""
valid(D,N,C,L) :- depot(D), crowd_need(N), comfort(C), lamp_act(L), supports(D,L), soothes(C,N).
ok :- chosen(D,N,C,L), valid(D,N,C,L).
:- chosen(D,N,C,L), not valid(D,N,C,L).
#show valid/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from asp import fact

    rows: list[str] = []
    for depot in DEPOTS.values():
        rows.append(fact("depot", depot.id))
        for lamp_act in depot.supports:
            rows.append(fact("supports", depot.id, lamp_act))
    for need in CROWD_NEEDS.values():
        rows.append(fact("crowd_need", need.id))
        for comfort in need.soothed_by:
            rows.append(fact("soothes", comfort, need.id))
    for comfort in COMFORTS.values():
        rows.append(fact("comfort", comfort.id))
    for lamp_act in LAMP_ACTS.values():
        rows.append(fact("lamp_act", lamp_act.id))
    if params is not None:
        rows.append(fact("chosen", params.depot, params.crowd_need, params.comfort, params.lamp_act))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_shapes() -> set[tuple[str, str, str, str]]:
    from asp import atoms, one_model

    shapes: set[tuple[str, str, str, str]] = set()
    for atom in atoms(one_model(asp_program()), "valid"):
        shapes.add(tuple(str(part) for part in atom))
    return shapes


def asp_accepts(params: StoryParams) -> bool:
    from asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params)), "ok"))


def asp_verify() -> int:
    python_shapes = set(all_valid_shapes())
    asp_shapes = asp_valid_shapes()
    if python_shapes != asp_shapes:
        print("Python/ASP mismatch")
        print("Only Python:", sorted(python_shapes - asp_shapes))
        print("Only ASP:", sorted(asp_shapes - python_shapes))
        return 1

    hero_ids = sorted(HEROES)
    keeper_ids = sorted(KEEPERS)
    for index, shape in enumerate(sorted(python_shapes)):
        params = StoryParams(
            depot=shape[0],
            crowd_need=shape[1],
            comfort=shape[2],
            lamp_act=shape[3],
            hero=hero_ids[index % len(hero_ids)],
            keeper=keeper_ids[index % len(keeper_ids)],
            seed=1000 + index,
        )
        if not asp_accepts(params):
            print(f"ASP rejected valid params: {params}")
            return 1
        sample = generate(params)
        story = sample.story.lower()
        required_bits = ["honey", "loud storm", "crystal lamp", "bus depot"]
        if any(bit not in story for bit in required_bits):
            print(f"Required seed language missing for params={params}")
            return 1
        if '"' not in sample.story:
            print(f"Dialogue missing for params={params}")
            return 1
        if len(sample.story_qa) < 4 or len(sample.world_qa) < 4:
            print(f"QA too thin for params={params}")
            return 1
        if not sample.world.facts.get("crowd_calm"):
            print(f"Crowd did not calm for params={params}")
            return 1
        if not sample.world.facts.get("lamp_safe"):
            print(f"Lamp did not become safe for params={params}")
            return 1
        if not sample.world.facts.get("bus_arrived"):
            print(f"Bus did not arrive for params={params}")
            return 1
        if "  " in sample.story or "{}" in sample.story:
            print(f"Story leaked placeholder/scaffold text for params={params}")
            return 1
    print(
        f"OK: Python and ASP agree on {len(python_shapes)} valid bus-depot tale shapes, "
        "and every generated story calms the crowd, restores the lamp, and brings in the last bus."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--depot", choices=sorted(DEPOTS))
    parser.add_argument("--crowd-need", dest="crowd_need", choices=sorted(CROWD_NEEDS))
    parser.add_argument("--comfort", choices=sorted(COMFORTS))
    parser.add_argument("--lamp-act", dest="lamp_act", choices=sorted(LAMP_ACTS))
    parser.add_argument("--hero", choices=sorted(HEROES))
    parser.add_argument("--keeper", choices=sorted(KEEPERS))
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    rng = rng or random.Random(args.seed)
    explicit_shape = any(getattr(args, key) is not None for key in ("depot", "crowd_need", "comfort", "lamp_act"))
    if explicit_shape:
        depot = args.depot or rng.choice(sorted(DEPOTS))
        need = args.crowd_need or rng.choice(sorted(CROWD_NEEDS))
        comfort = args.comfort or rng.choice(sorted(COMFORTS))
        lamp_act = args.lamp_act or rng.choice(sorted(LAMP_ACTS))
        hero = args.hero or rng.choice(sorted(HEROES))
        keeper = args.keeper or rng.choice(sorted(KEEPERS))
        params = StoryParams(depot, need, comfort, lamp_act, hero, keeper, args.seed)
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params

    choices = all_valid_shapes()
    depot, need, comfort, lamp_act = rng.choice(choices)
    hero = args.hero or rng.choice(sorted(HEROES))
    keeper = args.keeper or rng.choice(sorted(KEEPERS))
    return StoryParams(depot, need, comfort, lamp_act, hero, keeper, args.seed)


def format_qa(title: str, items: list[QAItem]) -> list[str]:
    lines = [title]
    for item in items:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return lines


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print()
        print("PROMPTS")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print()
        print("\n".join(format_qa("STORY QA", sample.story_qa)))
        print()
        print("\n".join(format_qa("WORLD KNOWLEDGE QA", sample.world_qa)))
    if trace and sample.world is not None:
        print()
        print("TRACE")
        print(sample.world.trace())


def iter_samples(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        return [generate(params) for params in CURATED]

    samples: list[StorySample] = []
    seen: set[str] = set()
    base_seed = args.seed
    attempts = 0
    while len(samples) < max(1, args.n) and attempts < max(1, args.n) * 30:
        local_args = copy.copy(args)
        local_args.seed = base_seed + attempts
        params = resolve_params(local_args, random.Random(local_args.seed))
        sample = generate(params)
        attempts += 1
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.show_asp:
        print(asp_program())
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in sorted(asp_valid_shapes()):
            print(" ".join(combo))
        return 0
    try:
        samples = iter_samples(args)
    except StoryError as exc:
        parser.error(str(exc))
        return 2
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0
    for index, sample in enumerate(samples, 1):
        header = ""
        if len(samples) > 1:
            header = f"=== honey_loud_storm_crystal_lamp_bus_depot_2 #{index} seed={sample.params.seed} ==="
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
