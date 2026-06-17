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
    caretaker: Optional[str] = None
    protective: bool = False

    def pronoun(self, case: str) -> str:
        table = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "mother": {"subject": "she", "object": "her", "possessive": "her"},
            "father": {"subject": "he", "object": "him", "possessive": "his"},
            "neighbor": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return table.get(self.gender or self.kind, table["girl"])[case]


@dataclass(frozen=True)
class Setting:
    id: str
    label: str
    line: str
    affords: set[str]
    everyday_detail: str


@dataclass(frozen=True)
class Search:
    id: str
    label: str
    gerund: str
    urge: str
    risk: str
    zones: set[str]
    warning: str
    false_guess: str
    tags: set[str]


@dataclass(frozen=True)
class HiddenThing:
    id: str
    label: str
    full_label: str
    zone: str
    vulnerable: set[str]
    twist: str
    tags: set[str]


@dataclass(frozen=True)
class Method:
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

    def methods_for(self, thing: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.protective and e.used_on == thing.id]

    def protected(self, thing: Entity, risk: str) -> bool:
        return any(thing.zone in method.covers and risk in method.guards for method in self.methods_for(thing))


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


def _r_damage_hidden(world: World, narrate: bool) -> bool:
    search_id = world.active_search
    if not search_id:
        return False
    search = SEARCHES[search_id]
    changed = False
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters[search.risk] < THRESHOLD:
            continue
        for thing in [e for e in world.entities.values() if e.kind == "hidden"]:
            if thing.zone not in search.zones or search.risk not in thing.guards:
                continue
            if world.protected(thing, search.risk):
                continue
            if not _mark(world, "damage_hidden", actor.id, thing.id, search.risk):
                continue
            thing.meters["damaged"] += 1
            thing.meters["misunderstood"] += 1
            changed = True
            if narrate:
                world.say(f"The {thing.label} was disturbed before anyone understood it.")
    return changed


def _r_caretaker_worry(world: World, narrate: bool) -> bool:
    thing_id = world.facts.get("hidden")
    caretaker_id = world.facts.get("caretaker")
    if not isinstance(thing_id, str) or not isinstance(caretaker_id, str):
        return False
    thing = world.get(thing_id)
    caretaker = world.get(caretaker_id)
    if thing.meters["damaged"] < THRESHOLD:
        return False
    if not _mark(world, "caretaker_worry", thing.id, caretaker.id):
        return False
    caretaker.memes["worry"] += 1
    if narrate:
        world.say(f"{caretaker.label} would have to fix the misunderstanding.")
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
        world.say(f"{hero.label} paused, still sure the misty bush meant trouble.")
    return True


CAUSAL_RULES = [
    Rule("damage_hidden", _r_damage_hidden),
    Rule("caretaker_worry", _r_caretaker_worry),
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
    "back_step": Setting(
        "back_step",
        "the back step",
        "the back step after breakfast",
        {"poke_bush", "shake_branch"},
        "The tea kettle clicked in the kitchen, and the morning fog still sat low.",
    ),
    "laundry_path": Setting(
        "laundry_path",
        "the laundry path",
        "the narrow path beside the clothesline",
        {"grab_shape", "shake_branch"},
        "Damp socks swung on the line like tiny flags.",
    ),
    "garden_gate": Setting(
        "garden_gate",
        "the garden gate",
        "the gate where the garden met the sidewalk",
        {"poke_bush", "grab_shape"},
        "A delivery bell had rung, but no one was at the gate.",
    ),
}


SEARCHES = {
    "poke_bush": Search(
        "poke_bush",
        "poke the misty bush with a broom",
        "poking the misty bush with a broom",
        "wanted to poke the misty bush and chase out the strange lump",
        "scratch",
        {"leaves", "ground"},
        "scratch the real hidden thing before seeing what it is",
        "a stray cat",
        {"misty_bush", "problem_solving", "misunderstanding"},
    ),
    "shake_branch": Search(
        "shake_branch",
        "shake the branch to make the shape fall",
        "shaking the branch to make the shape fall",
        "wanted to shake the branch until the shadow dropped",
        "scatter",
        {"leaves"},
        "scatter the clue before the twist can be understood",
        "a torn paper bag",
        {"misty_bush", "twist", "leaves"},
    ),
    "grab_shape": Search(
        "grab_shape",
        "grab the shape from under the bush",
        "grabbing the shape from under the bush",
        "wanted to grab the shape and solve the problem at once",
        "tear",
        {"ground"},
        "tear the hidden thing while trying to help",
        "a muddy glove",
        {"misty_bush", "problem_solving", "care"},
    ),
}


HIDDEN = {
    "thank_you_note": HiddenThing(
        "thank_you_note",
        "thank-you note",
        "folded thank-you note",
        "leaves",
        {"scatter", "scratch"},
        "It was a thank-you note from the neighbor, held in place by a clothespin.",
        {"note", "twist", "paper"},
    ),
    "picnic_cloth": HiddenThing(
        "picnic_cloth",
        "picnic cloth",
        "small picnic cloth",
        "ground",
        {"scratch", "tear"},
        "It was covering a surprise snack for later, not hiding anything scary.",
        {"cloth", "surprise", "twist"},
    ),
    "seed_packet": HiddenThing(
        "seed_packet",
        "seed packet",
        "paper seed packet",
        "ground",
        {"tear"},
        "It was a seed packet the neighbor had left for planting.",
        {"seed", "paper", "garden"},
    ),
}


METHODS = {
    "wait_for_mist": Method(
        "wait_for_mist",
        "patient waiting",
        {"leaves", "ground"},
        {"scratch", "scatter", "tear"},
        "wait three breaths for the mist to lift",
        "waited three breaths for the mist to lift",
        {"mist", "patience"},
    ),
    "soft_tongs": Method(
        "soft_tongs",
        "soft tongs",
        {"ground"},
        {"tear", "scratch"},
        "lift it with the soft tongs instead",
        "lifted the shape with the soft tongs",
        {"tool", "care"},
    ),
    "clothespin_check": Method(
        "clothespin_check",
        "clothespin check",
        {"leaves"},
        {"scatter", "scratch"},
        "check for a clothespin before shaking anything",
        "found the clothespin and opened it gently",
        {"clothespin", "paper"},
    ),
}


NAMES = {"girl": ["Iris", "Maya", "Nell", "Tara"], "boy": ["Ben", "Leo", "Noah", "Sam"]}
CARETAKERS = ["Mrs. Vale", "Mr. Lin", "Aunt Jo", "Nina"]
ELDERS = ["mother", "father", "neighbor"]
TRAITS = ["helpful", "quick", "curious", "careful"]


def at_risk(search: Search, thing: HiddenThing) -> bool:
    return thing.zone in search.zones and search.risk in thing.vulnerable


def select_method(search: Search, thing: HiddenThing) -> Optional[Method]:
    for method in METHODS.values():
        if thing.zone in method.covers and search.risk in method.guards:
            return method
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place, setting in SETTINGS.items():
        for search_id in setting.affords:
            search = SEARCHES[search_id]
            for thing_id, thing in HIDDEN.items():
                if at_risk(search, thing) and select_method(search, thing) is not None:
                    for gender in GENDERS:
                        out.append((place, search_id, thing_id, gender))
    return sorted(out)


def explain_rejection(place: str, search_id: str, thing_id: str, gender: str) -> str:
    setting = SETTINGS.get(place)
    search = SEARCHES.get(search_id)
    thing = HIDDEN.get(thing_id)
    if setting is None:
        return f"Unknown place: {place}."
    if search is None:
        return f"Unknown search: {search_id}."
    if thing is None:
        return f"Unknown hidden thing: {thing_id}."
    if gender not in GENDERS:
        return f"Unknown gender: {gender}."
    if search_id not in setting.affords:
        return f"{setting.label} does not support {search.label}."
    if not at_risk(search, thing):
        return f"The {search.label} would not honestly threaten the {thing.label}."
    if select_method(search, thing) is None:
        return f"No gentle method protects the {thing.label} from that search."
    return "The requested options are reasonable."


def do_search(world: World, hero: Entity, search: Search, *, narrate: bool) -> None:
    world.active_search = search.id
    hero.meters[search.risk] += 1
    if narrate:
        world.say(f"{hero.label} started {search.gerund}.")
    propagate(world, narrate=narrate)


def predict_damage(world: World, hero: Entity, search: Search, thing: Entity) -> dict[str, object]:
    sim = world.copy()
    sim.paragraphs = [[]]
    do_search(sim, sim.get(hero.id), search, narrate=False)
    sim_thing = sim.get(thing.id)
    caretaker = sim.get(str(sim.facts["caretaker"]))
    return {
        "damaged": sim_thing.meters["damaged"] >= THRESHOLD,
        "misunderstood": sim_thing.meters["misunderstood"] >= THRESHOLD,
        "caretaker_worry": caretaker.memes["worry"] >= THRESHOLD,
        "warning": search.warning,
    }


def introduce(world: World, hero: Entity, caretaker: Entity, elder: Entity, trait: str) -> None:
    world.say(
        f"Once upon a time, there was a {trait} child named {hero.label} who stood by {world.setting.line}."
    )
    world.say(f"{world.setting.everyday_detail} A misty bush beside the path seemed to wiggle.")
    world.say(
        f"{hero.label} thought, \"If there is a problem, I should solve it before {caretaker.label} worries.\""
    )
    hero.memes["helpfulness"] += 1
    caretaker.memes["trust"] += 1
    elder.memes["care"] += 1


def place_hidden(world: World, thing_cfg: HiddenThing) -> Entity:
    thing = world.add(
        Entity(
            thing_cfg.id,
            "hidden",
            thing_cfg.label,
            zone=thing_cfg.zone,
            guards=set(thing_cfg.vulnerable),
            caretaker=str(world.facts["caretaker"]),
        )
    )
    world.say(f"Under the mist was a shape that was really a {thing_cfg.full_label}, though nobody could tell yet.")
    world.facts["hidden"] = thing.id
    return thing


def misunderstand(world: World, hero: Entity, search: Search) -> None:
    world.break_para()
    world.say(f"{hero.label} guessed it was {search.false_guess} and {search.urge}.")
    world.say(f"Inside, {hero.pronoun('subject')} thought, \"Fast problem solving is still problem solving.\"")
    hero.memes["certainty"] += 1


def warn(world: World, hero: Entity, elder: Entity, search: Search, thing: Entity) -> None:
    prediction = predict_damage(world, hero, search, thing)
    world.facts["prediction"] = prediction
    world.say(
        f'"Wait," said {elder.label}. "If you {search.label}, you may {prediction["warning"]}. '
        f'The problem might not be what it looks like."'
    )
    elder.memes["caution"] += 1


def pause_conflict(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} frowned at the misty bush, still trying to be useful.")
    world.say(f'"But I saw it move," {hero.pronoun("subject")} said.')
    hero.meters["stopped"] += 1
    propagate(world, narrate=True)


def choose_method(world: World, hero: Entity, caretaker: Entity, search: Search, thing_cfg: HiddenThing) -> Method:
    method = select_method(search, thing_cfg)
    if method is None:
        raise StoryError("No gentle method can make this misty-bush story reasonable.")
    thing = world.get(str(world.facts["hidden"]))
    world.break_para()
    world.add(
        Entity(
            method.id,
            "method",
            method.label,
            covers=set(method.covers),
            guards=set(method.guards),
            used_on=thing.id,
            protective=True,
        )
    )
    world.say(f"{caretaker.label} came down the path and offered a calmer plan.")
    world.say(f'"Let us {method.advice}," {caretaker.label} said.')
    world.say(f"So {hero.label} {method.action}.")
    hero.memes["patience"] += 1
    caretaker.memes["gratitude"] += 1
    world.facts["method"] = method.id
    return method


def reveal_twist(world: World, hero: Entity, caretaker: Entity, elder: Entity, search: Search, thing: Entity) -> None:
    thing_cfg = HIDDEN[str(world.facts["hidden"])]
    do_search(world, hero, search, narrate=False)
    if thing.meters["damaged"] < THRESHOLD:
        world.say(thing_cfg.twist)
    hero.memes["conflict"] = 0
    hero.memes["surprise"] += 1
    caretaker.memes["relief"] += 1
    elder.memes["relief"] += 1
    world.say(f"{hero.label} laughed softly and thought, \"A misunderstanding can wear a very misty coat.\"")
    world.say(f"The real solution was not being faster; it was looking longer.")
    world.facts["resolved"] = True


def tell(params: "StoryParams") -> World:
    setting = SETTINGS[params.place]
    search = SEARCHES[params.search]
    thing_cfg = HIDDEN[params.hidden]
    world = World(setting)
    hero = world.add(Entity("hero", "character", params.name, gender=params.gender))
    caretaker = world.add(Entity("caretaker", "character", params.caretaker, gender="neighbor"))
    elder = world.add(Entity("elder", "character", params.elder.title(), gender=params.elder))
    world.facts.update(
        {"hero": hero.id, "caretaker": caretaker.id, "elder": elder.id, "search": search.id, "place": setting.id}
    )
    introduce(world, hero, caretaker, elder, params.trait)
    thing = place_hidden(world, thing_cfg)
    misunderstand(world, hero, search)
    warn(world, hero, elder, search, thing)
    pause_conflict(world, hero)
    choose_method(world, hero, caretaker, search, thing_cfg)
    reveal_twist(world, hero, caretaker, elder, search, thing)
    return world


@dataclass
class StoryParams:
    place: str
    search: str
    hidden: str
    name: str
    gender: str
    caretaker: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("back_step", "poke_bush", "picnic_cloth", "Iris", "girl", "Mrs. Vale", "mother", "helpful", 51),
    StoryParams("laundry_path", "shake_branch", "thank_you_note", "Leo", "boy", "Mr. Lin", "father", "quick", 52),
    StoryParams("garden_gate", "grab_shape", "seed_packet", "Maya", "girl", "Aunt Jo", "neighbor", "curious", 53),
    StoryParams("back_step", "poke_bush", "thank_you_note", "Sam", "boy", "Nina", "mother", "careful", 54),
]


def generation_prompts(world: World) -> list[str]:
    hero = world.get(str(world.facts["hero"]))
    search = SEARCHES[str(world.facts["search"])]
    hidden = HIDDEN[str(world.facts["hidden"])]
    return [
        'Write a slice-of-life story that includes the phrase "misty bush".',
        f"Write a problem-solving story where {hero.label} misunderstands a {hidden.label} near a bush.",
        f"Write a story with a twist where {search.gerund} would be the wrong solution.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.get(str(world.facts["hero"]))
    caretaker = world.get(str(world.facts["caretaker"]))
    elder = world.get(str(world.facts["elder"]))
    search = SEARCHES[str(world.facts["search"])]
    hidden = world.get(str(world.facts["hidden"]))
    method = METHODS[str(world.facts["method"])]
    prediction = dict(world.facts["prediction"])
    return [
        (
            f"Why did {elder.label} stop {hero.label}?",
            f"{elder.label} stopped {hero.label} because {search.gerund} could {prediction['warning']}. "
            f"The warning came from a predicted outcome before the {hidden.label} was damaged.",
        ),
        (
            "What was the misunderstanding?",
            f"{hero.label} thought the shape in the misty bush was {search.false_guess}. "
            f"It was really the {hidden.label}, so rushing would have solved the wrong problem.",
        ),
        (
            f"How did {caretaker.label} help?",
            f"{caretaker.label} suggested {method.label}, which let everyone inspect the bush gently. "
            f"That preserved the hidden thing and revealed the twist.",
        ),
    ]


KNOWLEDGE = {
    "misty_bush": (
        "Why can mist make a bush confusing to look at?",
        "Mist softens edges and hides details. A normal object can look like a strange shape until the air clears.",
    ),
    "problem_solving": (
        "Why is pausing useful in problem solving?",
        "Pausing gives a person time to check the real problem. A fast answer can be wrong if the situation was misunderstood.",
    ),
    "misunderstanding": (
        "What is a misunderstanding?",
        "A misunderstanding happens when someone reads a situation incorrectly. More information can turn the same event into a different story.",
    ),
    "twist": (
        "What is a twist in a story?",
        "A twist is a surprising change in what the reader understands. It works best when the new answer still fits the earlier clues.",
    ),
    "paper": (
        "Why can paper be damaged near bushes?",
        "Paper can tear, crumple, or get damp outside. Gentle handling keeps notes and packets readable.",
    ),
    "cloth": (
        "Why can cloth look strange in mist?",
        "Cloth can fold into odd shapes. Mist hides its color and edges, so it may look like something else.",
    ),
    "patience": (
        "How can patience solve a small everyday problem?",
        "Patience lets people observe before acting. In everyday problems, that can prevent extra mess or hurt feelings.",
    ),
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    search = SEARCHES[str(world.facts["search"])]
    hidden = HIDDEN[str(world.facts["hidden"])]
    method = METHODS[str(world.facts["method"])]
    tags = set(search.tags) | set(hidden.tags) | set(method.tags)
    return [KNOWLEDGE[tag] for tag in sorted(tags) if tag in KNOWLEDGE][:4]


ASP_RULES = r"""
at_risk(Search,Hidden) :- search_zone(Search,Zone), hidden_zone(Hidden,Zone), risk_of(Search,Risk), vulnerable(Hidden,Risk).
effective(Search,Hidden,Method) :- at_risk(Search,Hidden), hidden_zone(Hidden,Zone), covers(Method,Zone), risk_of(Search,Risk), guards(Method,Risk).
valid(Place,Search,Hidden,Gender) :- setting(Place), affords(Place,Search), hidden(Hidden), gender(Gender), effective(Search,Hidden,_).
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
    for hidden_id, hidden in HIDDEN.items():
        lines.append(asp.fact("hidden", hidden_id))
        lines.append(asp.fact("hidden_zone", hidden_id, hidden.zone))
        for risk in hidden.vulnerable:
            lines.append(asp.fact("vulnerable", hidden_id, risk))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        for zone in method.covers:
            lines.append(asp.fact("covers", method_id, zone))
        for risk in method.guards:
            lines.append(asp.fact("guards", method_id, risk))
    return "\n".join(lines) + "\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    model = asp.one_model(asp_facts() + ASP_RULES)
    return sorted(asp.atoms(model, "valid"))


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
    if py == lp:
        print(f"OK: Python and ASP agree on {len(py)} valid misty-bush stories.")
        return 0
    print("Mismatch between Python and ASP valid story sets.")
    print("Only Python:", sorted(py - lp))
    print("Only ASP:", sorted(lp - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the misty-bush misunderstanding storyworld.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--search", choices=sorted(SEARCHES))
    parser.add_argument("--hidden", choices=sorted(HIDDEN))
    parser.add_argument("--gender", choices=list(GENDERS))
    parser.add_argument("--name")
    parser.add_argument("--caretaker", choices=CARETAKERS)
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
    if args.hidden:
        combos = [c for c in combos if c[2] == args.hidden]
    if args.gender:
        combos = [c for c in combos if c[3] == args.gender]
    if not combos:
        place = args.place or next(iter(SETTINGS))
        search = args.search or next(iter(SEARCHES))
        hidden = args.hidden or next(iter(HIDDEN))
        gender = args.gender or GENDERS[0]
        raise StoryError(explain_rejection(place, search, hidden, gender))
    place, search, hidden, gender = rng.choice(combos)
    name = args.name or rng.choice(NAMES[gender])
    caretaker = args.caretaker or rng.choice(CARETAKERS)
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, search, hidden, name, gender, caretaker, elder, trait, args.seed)


def generate(params: StoryParams) -> StorySample:
    if (params.place, params.search, params.hidden, params.gender) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.search, params.hidden, params.gender))
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
        header = f"=== misty_bush_misunderstanding #{i} seed={sample.params.seed} ===" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
