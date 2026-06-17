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
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    used_on: Optional[str] = None
    protective: bool = False

    def pronoun(self, case: str) -> str:
        table = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "mother": {"subject": "she", "object": "her", "possessive": "her"},
            "father": {"subject": "he", "object": "him", "possessive": "his"},
            "vendor": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return table.get(self.gender or self.kind, table["girl"])[case]


@dataclass(frozen=True)
class Setting:
    id: str
    label: str
    line: str
    affords: set[str]
    street_line: str


@dataclass(frozen=True)
class Search:
    id: str
    label: str
    gerund: str
    urge: str
    risk: str
    zones: set[str]
    warning: str
    suspicion: str
    tags: set[str]


@dataclass(frozen=True)
class Clue:
    id: str
    label: str
    full_label: str
    zone: str
    vulnerable: set[str]
    reveal: str
    tags: set[str]


@dataclass(frozen=True)
class Tool:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    advice: str
    action: str
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

    def tools_for(self, clue: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.protective and e.used_on == clue.id]

    def protected(self, clue: Entity, risk: str) -> bool:
        return any(clue.zone in tool.covers and risk in tool.guards for tool in self.tools_for(clue))


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


def _r_damage_clue(world: World, narrate: bool) -> bool:
    search_id = world.active_search
    if not search_id:
        return False
    search = SEARCHES[search_id]
    changed = False
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters[search.risk] < THRESHOLD:
            continue
        for clue in [e for e in world.entities.values() if e.kind == "clue"]:
            if clue.zone not in search.zones or search.risk not in clue.guards:
                continue
            if world.protected(clue, search.risk):
                continue
            if not _mark(world, "damage_clue", actor.id, clue.id, search.risk):
                continue
            clue.meters["damaged"] += 1
            clue.meters["case_confused"] += 1
            changed = True
            if narrate:
                world.say(f"The {clue.label} was damaged, and the case became less kind.")
    return changed


def _r_friend_worry(world: World, narrate: bool) -> bool:
    clue_id = world.facts.get("clue")
    friend_id = world.facts.get("friend")
    if not isinstance(clue_id, str) or not isinstance(friend_id, str):
        return False
    clue = world.get(clue_id)
    friend = world.get(friend_id)
    if clue.meters["case_confused"] < THRESHOLD:
        return False
    if not _mark(world, "friend_worry", clue.id, friend.id):
        return False
    friend.memes["worry"] += 1
    if narrate:
        world.say(f"{friend.label} would stay upset if the clue could not explain the mix-up.")
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
        world.say(f"{hero.label} stopped, but the loud street still made the case feel urgent.")
    return True


CAUSAL_RULES = [
    Rule("damage_clue", _r_damage_clue),
    Rule("friend_worry", _r_friend_worry),
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
    "market_corner": Setting(
        "market_corner",
        "the market corner",
        "the loud street by the morning market",
        {"lift_cushion", "crawl_under"},
        "Wheels rattled, bells rang, and a pigeon-shaped weather vane squeaked overhead.",
    ),
    "bus_stop": Setting(
        "bus_stop",
        "the bus stop",
        "the loud street beside the bus stop",
        {"crawl_under", "tap_slats"},
        "Every bus sighed like it had just heard disappointing news.",
    ),
    "bakery_front": Setting(
        "bakery_front",
        "the bakery front",
        "the loud street in front of the bakery",
        {"lift_cushion", "tap_slats"},
        "The bakery door jingled so often that silence had no place to sit.",
    ),
}


SEARCHES = {
    "lift_cushion": Search(
        "lift_cushion",
        "lift the cozy bench cushion",
        "lifting the cozy bench cushion",
        "wanted to lift the cozy bench cushion and prove who took the note",
        "tear",
        {"cushion", "bench"},
        "tear the hidden clue before it can explain the argument",
        "the baker's helper",
        {"cozy_bench", "detective", "kindness"},
    ),
    "crawl_under": Search(
        "crawl_under",
        "crawl under the cozy bench",
        "crawling under the cozy bench",
        "wanted to crawl under the cozy bench and grab the shiny shape",
        "smudge",
        {"under", "bench"},
        "smudge the clue before both friends can read it",
        "a rolling coin thief",
        {"cozy_bench", "loud_street", "clue"},
    ),
    "tap_slats": Search(
        "tap_slats",
        "tap the bench slats for a secret compartment",
        "tapping the bench slats for a secret compartment",
        "wanted to tap every slat until the bench confessed",
        "scatter",
        {"slats"},
        "scatter the tiny evidence into the street noise",
        "a spy bench",
        {"bench", "detective", "reconciliation"},
    ),
}


CLUES = {
    "apology_note": Clue(
        "apology_note",
        "apology note",
        "folded apology note",
        "cushion",
        {"tear"},
        "The note said, I borrowed your ribbon and meant to bring it back.",
        {"note", "reconciliation", "paper"},
    ),
    "chalk_heart": Clue(
        "chalk_heart",
        "chalk heart",
        "tiny chalk heart",
        "under",
        {"smudge"},
        "The chalk heart matched both friends' drawings, so neither one had been mean.",
        {"chalk", "kindness", "reconciliation"},
    ),
    "crumb_trail": Clue(
        "crumb_trail",
        "crumb trail",
        "line of sesame crumbs",
        "slats",
        {"scatter"},
        "The crumbs led to a shared cookie, not a stolen one.",
        {"crumbs", "reconciliation", "street"},
    ),
}


TOOLS = {
    "flat_card": Tool(
        "flat_card",
        "flat card",
        {"cushion"},
        {"tear"},
        "slide the flat card under the cushion first",
        "slid the flat card under the cushion",
        {"paper", "tool"},
    ),
    "soft_cloth": Tool(
        "soft cloth",
        "soft cloth",
        {"under", "bench"},
        {"smudge"},
        "use the soft cloth to lift the clue",
        "used the soft cloth to lift the clue",
        {"cloth", "kindness"},
    ),
    "crumb_tray": Tool(
        "crumb_tray",
        "crumb tray",
        {"slats"},
        {"scatter"},
        "place the crumb tray below the slats",
        "placed the crumb tray below the slats",
        {"crumbs", "tool"},
    ),
}


NAMES = {"girl": ["Ada", "Nell", "Rosa", "Tess"], "boy": ["Ben", "Eli", "Milo", "Theo"]}
FRIENDS = ["Pip", "Rae", "June", "Max"]
ELDERS = ["mother", "father", "vendor"]
TRAITS = ["kind", "curious", "careful", "quick"]


def at_risk(search: Search, clue: Clue) -> bool:
    return clue.zone in search.zones and search.risk in clue.vulnerable


def select_tool(search: Search, clue: Clue) -> Optional[Tool]:
    for tool in TOOLS.values():
        if clue.zone in tool.covers and search.risk in tool.guards:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place, setting in SETTINGS.items():
        for search_id in setting.affords:
            search = SEARCHES[search_id]
            for clue_id, clue in CLUES.items():
                if at_risk(search, clue) and select_tool(search, clue) is not None:
                    for gender in GENDERS:
                        out.append((place, search_id, clue_id, gender))
    return sorted(out)


def explain_rejection(place: str, search_id: str, clue_id: str, gender: str) -> str:
    setting = SETTINGS.get(place)
    search = SEARCHES.get(search_id)
    clue = CLUES.get(clue_id)
    if setting is None:
        return f"Unknown place: {place}."
    if search is None:
        return f"Unknown search: {search_id}."
    if clue is None:
        return f"Unknown clue: {clue_id}."
    if gender not in GENDERS:
        return f"Unknown gender: {gender}."
    if search_id not in setting.affords:
        return f"{setting.label} does not support {search.label}."
    if not at_risk(search, clue):
        return f"The {search.label} would not honestly threaten the {clue.label}."
    if select_tool(search, clue) is None:
        return f"No detective tool protects the {clue.label} from that search."
    return "The requested options are reasonable."


def do_search(world: World, hero: Entity, search: Search, *, narrate: bool) -> None:
    world.active_search = search.id
    hero.meters[search.risk] += 1
    if narrate:
        world.say(f"{hero.label} started {search.gerund}.")
    propagate(world, narrate=narrate)


def predict_damage(world: World, hero: Entity, search: Search, clue: Entity) -> dict[str, object]:
    sim = world.copy()
    sim.paragraphs = [[]]
    do_search(sim, sim.get(hero.id), search, narrate=False)
    sim_clue = sim.get(clue.id)
    friend = sim.get(str(sim.facts["friend"]))
    return {
        "damaged": sim_clue.meters["damaged"] >= THRESHOLD,
        "case_confused": sim_clue.meters["case_confused"] >= THRESHOLD,
        "friend_worry": friend.memes["worry"] >= THRESHOLD,
        "warning": search.warning,
    }


def introduce(world: World, hero: Entity, friend: Entity, elder: Entity, trait: str) -> None:
    world.say(
        f"Once upon a time, there was a {trait} child detective named {hero.label} "
        f"who watched {world.setting.line} from a cozy bench."
    )
    world.say(f"{world.setting.street_line} {friend.label} sat at the other end, not speaking to a friend yet.")
    world.say(f"{hero.label} thought, \"Kind detectives solve cases so people can talk again.\"")
    hero.memes["kindness"] += 1
    friend.memes["sadness"] += 1
    elder.memes["care"] += 1


def place_clue(world: World, clue_cfg: Clue) -> Entity:
    clue = world.add(
        Entity(
            clue_cfg.id,
            "clue",
            clue_cfg.label,
            zone=clue_cfg.zone,
            guards=set(clue_cfg.vulnerable),
        )
    )
    world.say(f"A {clue_cfg.full_label} waited near the bench, small enough to be missed in the noise.")
    world.facts["clue"] = clue.id
    return clue


def accuse_too_fast(world: World, hero: Entity, search: Search) -> None:
    world.break_para()
    world.say(f"{hero.label} suspected {search.suspicion} and {search.urge}.")
    world.say(f"Inside, {hero.pronoun('subject')} thought, \"If I hurry, the friends can stop being mad sooner.\"")
    hero.memes["certainty"] += 1


def warn(world: World, hero: Entity, elder: Entity, search: Search, clue: Entity) -> None:
    prediction = predict_damage(world, hero, search, clue)
    world.facts["prediction"] = prediction
    world.say(
        f'"Wait," said {elder.label}. "If you {search.label}, you may {prediction["warning"]}. '
        f'A kind detective protects the clue."'
    )
    elder.memes["caution"] += 1


def pause_conflict(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} glanced from the loud street to the cozy bench and tried not to argue.")
    world.say(f'"I was solving kindly, just quickly," {hero.pronoun("subject")} said.')
    hero.meters["stopped"] += 1
    propagate(world, narrate=True)


def choose_tool(world: World, hero: Entity, friend: Entity, search: Search, clue_cfg: Clue) -> Tool:
    tool = select_tool(search, clue_cfg)
    if tool is None:
        raise StoryError("No tool can make this bench detective story reasonable.")
    clue = world.get(str(world.facts["clue"]))
    world.break_para()
    world.add(
        Entity(
            tool.id,
            "tool",
            tool.label,
            covers=set(tool.covers),
            guards=set(tool.guards),
            used_on=clue.id,
            protective=True,
        )
    )
    world.say(f"{friend.label} slid closer on the bench and offered a gentler detective tool.")
    world.say(f'"Try this: {tool.advice}," {friend.label} said.')
    world.say(f"So {hero.label} {tool.action}.")
    hero.memes["patience"] += 1
    friend.memes["hope"] += 1
    world.facts["tool"] = tool.id
    return tool


def reconcile(world: World, hero: Entity, friend: Entity, elder: Entity, search: Search, clue: Entity) -> None:
    clue_cfg = CLUES[str(world.facts["clue"])]
    do_search(world, hero, search, narrate=False)
    if clue.meters["damaged"] < THRESHOLD:
        world.say(clue_cfg.reveal)
    hero.memes["conflict"] = 0
    hero.memes["relief"] += 1
    friend.memes["joy"] += 1
    elder.memes["relief"] += 1
    world.say(f"{friend.label} smiled and went to make peace before the street got any louder.")
    world.say(f"{hero.label} closed the case: kindness had found the clue without bruising it.")
    world.facts["resolved"] = True


def tell(params: "StoryParams") -> World:
    setting = SETTINGS[params.place]
    search = SEARCHES[params.search]
    clue_cfg = CLUES[params.clue]
    world = World(setting)
    hero = world.add(Entity("hero", "character", params.name, gender=params.gender))
    friend = world.add(Entity("friend", "character", params.friend, gender="girl"))
    elder = world.add(Entity("elder", "character", params.elder.title(), gender=params.elder))
    world.facts.update({"hero": hero.id, "friend": friend.id, "elder": elder.id, "search": search.id, "place": setting.id})
    introduce(world, hero, friend, elder, params.trait)
    clue = place_clue(world, clue_cfg)
    accuse_too_fast(world, hero, search)
    warn(world, hero, elder, search, clue)
    pause_conflict(world, hero)
    choose_tool(world, hero, friend, search, clue_cfg)
    reconcile(world, hero, friend, elder, search, clue)
    return world


@dataclass
class StoryParams:
    place: str
    search: str
    clue: str
    name: str
    gender: str
    friend: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("market_corner", "lift_cushion", "apology_note", "Ada", "girl", "Pip", "mother", "kind", 71),
    StoryParams("bus_stop", "crawl_under", "chalk_heart", "Milo", "boy", "Rae", "father", "curious", 72),
    StoryParams("bakery_front", "tap_slats", "crumb_trail", "Nell", "girl", "June", "vendor", "careful", 73),
    StoryParams("market_corner", "crawl_under", "chalk_heart", "Theo", "boy", "Max", "vendor", "quick", 74),
]


def generation_prompts(world: World) -> list[str]:
    hero = world.get(str(world.facts["hero"]))
    search = SEARCHES[str(world.facts["search"])]
    clue = CLUES[str(world.facts["clue"])]
    return [
        'Write a detective story that includes "loud street" and "cozy bench".',
        f"Write a kind reconciliation story where {hero.label} investigates a {clue.label}.",
        f"Write a story where {search.gerund} would damage the clue, so the detective uses a gentler method.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.get(str(world.facts["hero"]))
    friend = world.get(str(world.facts["friend"]))
    elder = world.get(str(world.facts["elder"]))
    search = SEARCHES[str(world.facts["search"])]
    clue = world.get(str(world.facts["clue"]))
    tool = TOOLS[str(world.facts["tool"])]
    prediction = dict(world.facts["prediction"])
    return [
        (
            f"Why did {elder.label} stop {hero.label}?",
            f"{elder.label} stopped {hero.label} because {search.gerund} could {prediction['warning']}. "
            f"The warning was predicted before the {clue.label} was damaged.",
        ),
        (
            f"How did {friend.label} help?",
            f"{friend.label} offered the {tool.label}, which let {hero.label} examine the clue gently. "
            f"That helped the case move toward reconciliation instead of another argument.",
        ),
        (
            "What made the ending kind?",
            f"The clue showed that the conflict was fixable, so {friend.label} could make peace. "
            f"{hero.label} solved the case without harming the evidence.",
        ),
    ]


KNOWLEDGE = {
    "cozy_bench": (
        "Why might a bench be important in a detective story?",
        "A bench is a place where people sit, wait, and leave small things behind. It can hold clues under cushions, slats, or seats.",
    ),
    "loud_street": (
        "Why is a loud street hard for solving a mystery?",
        "Noise can distract people and make small clues easy to miss. A detective has to slow down and observe carefully.",
    ),
    "detective": (
        "What does a detective do?",
        "A detective protects clues, asks questions, and checks guesses. Good detective work avoids damaging evidence.",
    ),
    "kindness": (
        "How can kindness help solve a disagreement?",
        "Kindness keeps people from blaming too quickly. It gives everyone room to explain what really happened.",
    ),
    "reconciliation": (
        "What does reconciliation mean?",
        "Reconciliation means making peace after a disagreement. It often happens when people understand each other better.",
    ),
    "paper": (
        "Why should a paper clue be handled carefully?",
        "Paper can tear, wrinkle, or smear. Gentle handling keeps the words readable.",
    ),
    "chalk": (
        "Why can chalk clues smudge?",
        "Chalk is powdery and can rub away easily. A cloth or careful lift can protect the mark.",
    ),
    "crumbs": (
        "Why are crumbs fragile clues?",
        "Crumbs are tiny and can scatter with a tap or breeze. A tray can catch them before they disappear.",
    ),
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    search = SEARCHES[str(world.facts["search"])]
    clue = CLUES[str(world.facts["clue"])]
    tool = TOOLS[str(world.facts["tool"])]
    tags = set(search.tags) | set(clue.tags) | set(tool.tags)
    return [KNOWLEDGE[tag] for tag in sorted(tags) if tag in KNOWLEDGE][:4]


ASP_RULES = r"""
at_risk(Search,Clue) :- search_zone(Search,Zone), clue_zone(Clue,Zone), risk_of(Search,Risk), vulnerable(Clue,Risk).
effective(Search,Clue,Tool) :- at_risk(Search,Clue), clue_zone(Clue,Zone), covers(Tool,Zone), risk_of(Search,Risk), guards(Tool,Risk).
valid(Place,Search,Clue,Gender) :- setting(Place), affords(Place,Search), clue(Clue), gender(Gender), effective(Search,Clue,_).
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
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_zone", clue_id, clue.zone))
        for risk in clue.vulnerable:
            lines.append(asp.fact("vulnerable", clue_id, risk))
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
        print(f"OK: Python and ASP agree on {len(py)} valid loud-street stories.")
        return 0
    print("Mismatch between Python and ASP valid story sets.")
    print("Only Python:", sorted(py - lp))
    print("Only ASP:", sorted(lp - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the loud-street bench detective storyworld.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--search", choices=sorted(SEARCHES))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--gender", choices=list(GENDERS))
    parser.add_argument("--name")
    parser.add_argument("--friend", choices=FRIENDS)
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
    if args.clue:
        combos = [c for c in combos if c[2] == args.clue]
    if args.gender:
        combos = [c for c in combos if c[3] == args.gender]
    if not combos:
        place = args.place or next(iter(SETTINGS))
        search = args.search or next(iter(SEARCHES))
        clue = args.clue or next(iter(CLUES))
        gender = args.gender or GENDERS[0]
        raise StoryError(explain_rejection(place, search, clue, gender))
    place, search, clue, gender = rng.choice(combos)
    name = args.name or rng.choice(NAMES[gender])
    friend = args.friend or rng.choice([f for f in FRIENDS if f != name])
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, search, clue, name, gender, friend, elder, trait, args.seed)


def generate(params: StoryParams) -> StorySample:
    if (params.place, params.search, params.clue, params.gender) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.search, params.clue, params.gender))
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
        header = f"=== loud_street_bench_detective #{i} seed={sample.params.seed} ===" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
