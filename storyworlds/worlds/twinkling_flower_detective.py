#!/usr/bin/env python3
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
GENDERS = ("girl", "boy")


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    gender: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    zone: Optional[str] = None
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    used_on: Optional[str] = None
    caretaker: Optional[str] = None
    protective: bool = False

    def pronoun(self, case: str) -> str:
        table = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "mother": {"subject": "she", "object": "her", "possessive": "her"},
            "father": {"subject": "he", "object": "him", "possessive": "his"},
            "gardener": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return table.get(self.gender or self.kind, table["girl"])[case]


@dataclass(frozen=True)
class Setting:
    id: str
    label: str
    line: str
    affords: set[str]
    mystery_line: str


@dataclass(frozen=True)
class Search:
    id: str
    label: str
    gerund: str
    urge: str
    risk: str
    zones: set[str]
    warning: str
    tags: set[str]


@dataclass(frozen=True)
class Flower:
    id: str
    label: str
    full_label: str
    zone: str
    vulnerable: set[str]
    clue_line: str
    tags: set[str]


@dataclass(frozen=True)
class Tool:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    advice: str
    action: str
    reveal: str
    tags: set[str]


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.fired_names: list[str] = []
        self.facts: dict[str, object] = {}
        self.active_search: Optional[str] = None

    def copy(self) -> "World":
        return copy.deepcopy(self)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def break_para(self) -> None:
        if self.paragraphs and self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def tools_for(self, flower: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.protective and e.used_on == flower.id]

    def protected(self, flower: Entity, risk: str) -> bool:
        return any(flower.zone in tool.covers and risk in tool.guards for tool in self.tools_for(flower))


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


def _r_damage_flower(world: World, narrate: bool) -> bool:
    search_id = world.active_search
    if not search_id:
        return False
    search = SEARCHES[search_id]
    changed = False
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters[search.risk] < THRESHOLD:
            continue
        for flower in [e for e in world.entities.values() if e.kind == "flower"]:
            if flower.zone not in search.zones or search.risk not in flower.guards:
                continue
            if world.protected(flower, search.risk):
                continue
            if not _mark(world, "flower_damage", actor.id, flower.id, search.risk):
                continue
            flower.meters["hurt"] += 1
            flower.meters["clue_lost"] += 1
            changed = True
            if narrate:
                world.say(f"The {flower.label} drooped, and the clue began to disappear.")
    return changed


def _r_case_worry(world: World, narrate: bool) -> bool:
    flower_id = world.facts.get("flower")
    helper_id = world.facts.get("helper")
    if not isinstance(flower_id, str) or not isinstance(helper_id, str):
        return False
    flower = world.get(flower_id)
    helper = world.get(helper_id)
    if flower.meters["clue_lost"] < THRESHOLD:
        return False
    if not _mark(world, "case_worry", flower.id, helper.id):
        return False
    helper.memes["worry"] += 1
    if narrate:
        world.say(f"{helper.label} would not know the surprise answer if the clue vanished.")
    return True


def _r_conflict(world: World, narrate: bool) -> bool:
    hero_id = world.facts.get("hero")
    elder_id = world.facts.get("elder")
    if not isinstance(hero_id, str) or not isinstance(elder_id, str):
        return False
    hero = world.get(hero_id)
    elder = world.get(elder_id)
    if hero.memes["certainty"] < THRESHOLD or hero.meters["stopped"] < THRESHOLD:
        return False
    if not _mark(world, "conflict", hero.id, elder.id):
        return False
    hero.memes["conflict"] += 1
    elder.memes["concern"] += 1
    if narrate:
        world.say(f"For a moment, {hero.label}'s detective hurry argued with {elder.label}'s care.")
    return True


CAUSAL_RULES = [
    Rule("flower_damage", _r_damage_flower),
    Rule("case_worry", _r_case_worry),
    Rule("conflict", _r_conflict),
]


def propagate(world: World, *, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world, narrate):
                changed = True


SETTINGS = {
    "moon_garden": Setting(
        "moon_garden",
        "the moon garden",
        "a moon garden where every path was dusted with pale light",
        {"pluck_clue", "shake_pollen"},
        "Someone had left tiny boot prints beside the watering can.",
    ),
    "greenhouse": Setting(
        "greenhouse",
        "the glass greenhouse",
        "a glass greenhouse warm enough to fog a detective's notebook",
        {"shine_lamp", "shake_pollen"},
        "The missing ribbon had vanished between two rows of pots.",
    ),
    "fountain_bed": Setting(
        "fountain_bed",
        "the fountain flower bed",
        "a fountain flower bed where water clicked like a clock",
        {"pluck_clue", "shine_lamp"},
        "A trail of glitter stopped exactly at one flower.",
    ),
}


SEARCHES = {
    "pluck_clue": Search(
        "pluck_clue",
        "pluck the flower to inspect it",
        "plucking the flower to inspect it",
        "wanted to pluck the flower and look under every petal",
        "bruise",
        {"stem", "petal"},
        "bruise the stem before the clue could be read",
        {"flower", "detective", "clue"},
    ),
    "shake_pollen": Search(
        "shake_pollen",
        "shake the pollen onto the notebook",
        "shaking the pollen onto the notebook",
        "wanted to shake the pollen loose and see what pattern fell",
        "scatter",
        {"pollen"},
        "scatter the pollen clue into a useless golden cloud",
        {"pollen", "surprise", "clue"},
    ),
    "shine_lamp": Search(
        "shine_lamp",
        "shine a bright lamp on the flower",
        "shining a bright lamp on the flower",
        "wanted to shine a bright lamp until the clue showed itself",
        "fade",
        {"petal", "pollen"},
        "fade the twinkling marks before anyone could copy them",
        {"twinkling", "flower", "light"},
    ),
}


FLOWERS = {
    "twinkling_flower": Flower(
        "twinkling_flower",
        "twinkling flower",
        "twinkling flower",
        "petal",
        {"bruise", "fade"},
        "Its petals blinked once when a question was near.",
        {"twinkling", "flower", "petal"},
    ),
    "wondrous_flower": Flower(
        "wondrous_flower",
        "wondrous flower",
        "wondrous flower",
        "pollen",
        {"scatter", "fade"},
        "Its pollen arranged itself like secret handwriting.",
        {"wondrous", "flower", "pollen"},
    ),
    "silver_stem": Flower(
        "silver_stem",
        "silver-stem flower",
        "silver-stem wondrous flower",
        "stem",
        {"bruise"},
        "Its silver stem bent toward hidden things.",
        {"wondrous", "flower", "stem"},
    ),
}


TOOLS = {
    "mirror_card": Tool(
        "mirror_card",
        "mirror card",
        {"petal"},
        {"bruise", "fade"},
        "hold the mirror card beside the petals instead",
        "held the mirror card beside the petals",
        "The reflected twinkle made a tiny arrow on the card.",
        {"mirror", "light"},
    ),
    "pollen_ring": Tool(
        "pollen_ring",
        "pollen ring",
        {"pollen"},
        {"scatter", "fade"},
        "place the pollen ring around the flower first",
        "placed the pollen ring around the flower",
        "The pollen settled into a neat question mark.",
        {"pollen", "tool"},
    ),
    "stem_cradle": Tool(
        "stem_cradle",
        "stem cradle",
        {"stem"},
        {"bruise"},
        "support the stem in the cradle and look closely",
        "slipped the stem cradle under the flower",
        "The silver stem pointed toward the hidden ribbon.",
        {"stem", "tool"},
    ),
}


NAMES = {"girl": ["Ada", "Mina", "Nell", "Vera"], "boy": ["Theo", "Eli", "Jon", "Miles"]}
HELPERS = ["Pip", "Rae", "Lulu", "Ben"]
ELDERS = ["mother", "father", "gardener"]
TRAITS = ["curious", "careful", "bold", "patient"]


def at_risk(search: Search, flower: Flower) -> bool:
    return flower.zone in search.zones and search.risk in flower.vulnerable


def select_tool(search: Search, flower: Flower) -> Optional[Tool]:
    for tool in TOOLS.values():
        if flower.zone in tool.covers and search.risk in tool.guards:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place, setting in SETTINGS.items():
        for search_id in setting.affords:
            search = SEARCHES[search_id]
            for flower_id, flower in FLOWERS.items():
                if at_risk(search, flower) and select_tool(search, flower) is not None:
                    for gender in GENDERS:
                        out.append((place, search_id, flower_id, gender))
    return sorted(out)


def explain_rejection(place: str, search_id: str, flower_id: str, gender: str) -> str:
    setting = SETTINGS.get(place)
    search = SEARCHES.get(search_id)
    flower = FLOWERS.get(flower_id)
    if setting is None:
        return f"Unknown place: {place}."
    if search is None:
        return f"Unknown search: {search_id}."
    if flower is None:
        return f"Unknown flower: {flower_id}."
    if gender not in GENDERS:
        return f"Unknown gender: {gender}."
    if search_id not in setting.affords:
        return f"{setting.label} does not support {search.label}."
    if not at_risk(search, flower):
        return f"The {search.label} would not honestly threaten the {flower.label}."
    if select_tool(search, flower) is None:
        return f"No detective tool protects the {flower.label} from that search."
    return "The requested options are reasonable."


def do_search(world: World, hero: Entity, search: Search, *, narrate: bool) -> None:
    world.active_search = search.id
    hero.meters[search.risk] += 1
    if narrate:
        world.say(f"{hero.label} began {search.gerund}.")
    propagate(world, narrate=narrate)


def predict_damage(world: World, hero: Entity, search: Search, flower: Entity) -> dict[str, object]:
    sim = world.copy()
    sim.paragraphs = [[]]
    do_search(sim, sim.get(hero.id), search, narrate=False)
    sim_flower = sim.get(flower.id)
    helper = sim.get(str(sim.facts["helper"]))
    return {
        "hurt": sim_flower.meters["hurt"] >= THRESHOLD,
        "clue_lost": sim_flower.meters["clue_lost"] >= THRESHOLD,
        "helper_worry": helper.memes["worry"] >= THRESHOLD,
        "warning": search.warning,
    }


def introduce(world: World, hero: Entity, helper: Entity, elder: Entity, trait: str) -> None:
    world.say(
        f"Once upon a time, there was a {trait} child detective named {hero.label} "
        f"who carried a notebook through {world.setting.line}."
    )
    world.say(f"{world.setting.mystery_line} {hero.label} thought, \"Every surprise leaves a clue if I look kindly.\"")
    world.say(f"{helper.label} followed with a tiny envelope marked SECRET.")
    hero.memes["curiosity"] += 1
    helper.memes["trust"] += 1
    elder.memes["care"] += 1


def place_flower(world: World, flower_cfg: Flower) -> Entity:
    flower = world.add(
        Entity(
            flower_cfg.id,
            "flower",
            flower_cfg.label,
            zone=flower_cfg.zone,
            guards=set(flower_cfg.vulnerable),
        )
    )
    world.say(
        f"Some children called any clue plant a twinkling flower; the gardener called it a wondrous flower. "
        f"In the middle grew a {flower_cfg.full_label}. {flower_cfg.clue_line}"
    )
    world.facts["flower"] = flower.id
    return flower


def want_clue(world: World, hero: Entity, search: Search) -> None:
    world.break_para()
    world.say(f"{hero.label} {search.urge}.")
    world.say(f"Inside, {hero.pronoun('subject')} thought, \"A real detective solves the surprise before anyone else blinks.\"")
    hero.memes["certainty"] += 1


def warn(world: World, hero: Entity, elder: Entity, search: Search, flower: Entity) -> None:
    prediction = predict_damage(world, hero, search, flower)
    world.facts["prediction"] = prediction
    world.say(
        f'"Wait," said {elder.label}. "If you {search.label}, you may {prediction["warning"]}. '
        f'Then the surprise clue will be gone."'
    )
    elder.memes["caution"] += 1


def resist(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} tapped the notebook and felt the case tug at {hero.pronoun('possessive')} sleeve.")
    world.say(f'"But I am so close," {hero.pronoun("subject")} said.')
    hero.meters["stopped"] += 1
    propagate(world, narrate=True)


def compromise(world: World, hero: Entity, helper: Entity, search: Search, flower_cfg: Flower) -> Tool:
    tool = select_tool(search, flower_cfg)
    if tool is None:
        raise StoryError("No tool can make this flower detective story reasonable.")
    flower = world.get(str(world.facts["flower"]))
    world.break_para()
    world.add(
        Entity(
            tool.id,
            "tool",
            tool.label,
            covers=set(tool.covers),
            guards=set(tool.guards),
            used_on=flower.id,
            protective=True,
        )
    )
    world.say(f"{helper.label} opened the secret envelope and revealed a detective tool.")
    world.say(f'"Try this: {tool.advice}," {helper.label} said.')
    world.say(f"So {hero.label} {tool.action}.")
    hero.memes["patience"] += 1
    helper.memes["helpfulness"] += 1
    world.facts["tool"] = tool.id
    return tool


def solve_case(world: World, hero: Entity, helper: Entity, elder: Entity, search: Search, flower: Entity) -> None:
    tool = TOOLS[str(world.facts["tool"])]
    do_search(world, hero, search, narrate=False)
    if flower.meters["hurt"] < THRESHOLD:
        world.say(tool.reveal)
    hero.memes["conflict"] = 0
    hero.memes["surprise"] += 1
    helper.memes["joy"] += 1
    elder.memes["relief"] += 1
    world.say(f"The surprise was that {helper.label} had hidden a thank-you note for {hero.label}.")
    world.say(f"{hero.label} wrote, \"Best clue: solve gently,\" and closed the case.")
    world.facts["resolved"] = True
    world.facts["surprise"] = "thank-you note"


def tell(params: "StoryParams") -> World:
    setting = SETTINGS[params.place]
    search = SEARCHES[params.search]
    flower_cfg = FLOWERS[params.flower]
    world = World(setting)
    hero = world.add(Entity("hero", "character", params.name, gender=params.gender))
    helper = world.add(Entity("helper", "character", params.helper, gender="girl"))
    elder = world.add(Entity("elder", "character", params.elder.title(), gender=params.elder))
    world.facts.update({"hero": hero.id, "helper": helper.id, "elder": elder.id, "search": search.id, "place": setting.id})
    introduce(world, hero, helper, elder, params.trait)
    flower = place_flower(world, flower_cfg)
    want_clue(world, hero, search)
    warn(world, hero, elder, search, flower)
    resist(world, hero)
    compromise(world, hero, helper, search, flower_cfg)
    solve_case(world, hero, helper, elder, search, flower)
    return world


@dataclass
class StoryParams:
    place: str
    search: str
    flower: str
    name: str
    gender: str
    helper: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("moon_garden", "pluck_clue", "twinkling_flower", "Ada", "girl", "Pip", "mother", "curious", 41),
    StoryParams("greenhouse", "shake_pollen", "wondrous_flower", "Theo", "boy", "Rae", "father", "careful", 42),
    StoryParams("fountain_bed", "shine_lamp", "twinkling_flower", "Mina", "girl", "Lulu", "gardener", "patient", 43),
    StoryParams("moon_garden", "pluck_clue", "silver_stem", "Eli", "boy", "Ben", "gardener", "bold", 44),
]


def generation_prompts(world: World) -> list[str]:
    hero = world.get(str(world.facts["hero"]))
    search = SEARCHES[str(world.facts["search"])]
    flower = FLOWERS[str(world.facts["flower"])]
    return [
        'Write a detective story that includes "twinkling flower" and "wondrous flower".',
        f"Write a surprise mystery about {hero.label} and {search.gerund} without hurting a {flower.label}.",
        "Write a story where the solution comes from preserving evidence instead of grabbing it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.get(str(world.facts["hero"]))
    helper = world.get(str(world.facts["helper"]))
    elder = world.get(str(world.facts["elder"]))
    search = SEARCHES[str(world.facts["search"])]
    flower = world.get(str(world.facts["flower"]))
    tool = TOOLS[str(world.facts["tool"])]
    prediction = dict(world.facts["prediction"])
    return [
        (
            f"Why did {elder.label} stop {hero.label}?",
            f"{elder.label} stopped {hero.label} because {search.gerund} could {prediction['warning']}. "
            f"The danger was predicted before the {flower.label} was actually harmed.",
        ),
        (
            f"How did {helper.label} help solve the case?",
            f"{helper.label} provided the {tool.label}, which let {hero.label} read the clue safely. "
            f"The help mattered because the clue depended on the flower staying intact.",
        ),
        (
            "What was the surprise?",
            f"The surprise was a thank-you note hidden by {helper.label}. "
            f"{hero.label} found it by using patience instead of damaging the evidence.",
        ),
    ]


KNOWLEDGE = {
    "flower": (
        "Why are flowers easy to damage?",
        "Many flowers have soft petals, stems, or pollen. Rough handling can bruise them or scatter the parts that carry clues in a story.",
    ),
    "twinkling": (
        "What does twinkling mean?",
        "Twinkling means shining with small, quick flashes of light. A twinkling clue can be easier to see with a mirror or gentle light.",
    ),
    "wondrous": (
        "What does wondrous mean?",
        "Wondrous means amazing or full of wonder. In a story, a wondrous flower can make an ordinary mystery feel magical.",
    ),
    "pollen": (
        "What is pollen?",
        "Pollen is a fine powder made by flowers. In real life it helps plants reproduce, and in a story it can show patterns or tracks.",
    ),
    "detective": (
        "What does a detective do?",
        "A detective looks for clues and asks careful questions. Good detectives protect evidence so the answer stays trustworthy.",
    ),
    "clue": (
        "Why should evidence be preserved?",
        "Evidence should be preserved because damaged evidence can point to the wrong answer. Careful observation keeps the mystery fair.",
    ),
    "mirror": (
        "How can a mirror help observation?",
        "A mirror can show light from another angle. It lets someone inspect a delicate thing without touching it directly.",
    ),
    "stem": (
        "Why is a flower stem important?",
        "The stem supports the flower and carries water through the plant. If it is bruised, the flower may droop.",
    ),
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    search = SEARCHES[str(world.facts["search"])]
    flower = FLOWERS[str(world.facts["flower"])]
    tool = TOOLS[str(world.facts["tool"])]
    tags = set(search.tags) | set(flower.tags) | set(tool.tags)
    return [KNOWLEDGE[tag] for tag in sorted(tags) if tag in KNOWLEDGE][:4]


ASP_RULES = r"""
at_risk(Search,Flower) :- search_zone(Search,Zone), flower_zone(Flower,Zone), risk_of(Search,Risk), vulnerable(Flower,Risk).
effective(Search,Flower,Tool) :- at_risk(Search,Flower), flower_zone(Flower,Zone), covers(Tool,Zone), risk_of(Search,Risk), guards(Tool,Risk).
valid(Place,Search,Flower,Gender) :- setting(Place), affords(Place,Search), flower(Flower), gender(Gender), effective(Search,Flower,_).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gender in GENDERS:
        lines.append(asp.fact("gender", gender))
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for search in setting.affords:
            lines.append(asp.fact("affords", place, search))
    for search_id, search in SEARCHES.items():
        lines.append(asp.fact("search", search_id))
        lines.append(asp.fact("risk_of", search_id, search.risk))
        for zone in search.zones:
            lines.append(asp.fact("search_zone", search_id, zone))
    for flower_id, flower in FLOWERS.items():
        lines.append(asp.fact("flower", flower_id))
        lines.append(asp.fact("flower_zone", flower_id, flower.zone))
        for risk in flower.vulnerable:
            lines.append(asp.fact("vulnerable", flower_id, risk))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for zone in tool.covers:
            lines.append(asp.fact("covers", tool_id, zone))
        for risk in tool.guards:
            lines.append(asp.fact("guards", tool_id, risk))
    return "\n".join(lines) + "\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    model = asp.one_model(asp_facts() + ASP_RULES)
    return sorted(asp.atoms(model, "valid"))


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
    if py == lp:
        print(f"OK: Python and ASP agree on {len(py)} valid twinkling-flower stories.")
        return 0
    print("Mismatch between Python and ASP valid story sets.")
    print("Only Python:", sorted(py - lp))
    print("Only ASP:", sorted(lp - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the twinkling-flower detective storyworld.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--search", choices=sorted(SEARCHES))
    parser.add_argument("--flower", choices=sorted(FLOWERS))
    parser.add_argument("--gender", choices=list(GENDERS))
    parser.add_argument("--name")
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--elder", choices=ELDERS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.search:
        combos = [c for c in combos if c[1] == args.search]
    if args.flower:
        combos = [c for c in combos if c[2] == args.flower]
    if args.gender:
        combos = [c for c in combos if c[3] == args.gender]
    if not combos:
        place = args.place or next(iter(SETTINGS))
        search = args.search or next(iter(SEARCHES))
        flower = args.flower or next(iter(FLOWERS))
        gender = args.gender or GENDERS[0]
        raise StoryError(explain_rejection(place, search, flower, gender))
    place, search, flower, gender = rng.choice(combos)
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice([h for h in HELPERS if h != name])
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, search, flower, name, gender, helper, elder, trait, args.seed)


def generate(params: StoryParams) -> StorySample:
    if (params.place, params.search, params.flower, params.gender) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.search, params.flower, params.gender))
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def dump_trace(world: World) -> None:
    print("\nTRACE")
    print(f"setting: {world.setting.id}")
    print("fired rules:", ", ".join(world.fired_names) or "(none)")
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        parts = [entity.id, entity.kind, entity.label]
        if entity.zone:
            parts.append(f"zone={entity.zone}")
        if entity.covers:
            parts.append(f"covers={sorted(entity.covers)}")
        if entity.guards:
            parts.append(f"guards={sorted(entity.guards)}")
        if entity.used_on:
            parts.append(f"used_on={entity.used_on}")
        print("  " + " | ".join(parts))
        if meters:
            print(f"    meters={meters}")
        if memes:
            print(f"    memes={memes}")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print("\nPROMPTS")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print("\nSTORY QA")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\nWORLD KNOWLEDGE QA")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
    if trace and sample.world is not None:
        dump_trace(sample.world)


def _samples_from_args(args) -> list[StorySample]:
    if args.all:
        return [generate(params) for params in CURATED]
    base_seed = args.seed if args.seed is not None else random.randrange(1, 10_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    attempts = 0
    while len(samples) < args.n and attempts < max(20, args.n * 20):
        seed = base_seed + attempts
        rng = random.Random(seed)
        local_args = copy.copy(args)
        local_args.seed = seed
        params = resolve_params(local_args, rng)
        params.seed = seed
        sample = generate(params)
        if sample.story not in seen:
            samples.append(sample)
            seen.add(sample.story)
        attempts += 1
    if len(samples) < args.n:
        raise StoryError(f"Only generated {len(samples)} distinct stories after {attempts} attempts.")
    return samples


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.show_asp:
        print(asp_facts() + ASP_RULES)
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return 0
    try:
        samples = _samples_from_args(args)
    except StoryError as exc:
        parser.error(str(exc))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return 0
    for i, sample in enumerate(samples, 1):
        header = f"=== twinkling_flower_detective #{i} seed={sample.params.seed} ===" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
