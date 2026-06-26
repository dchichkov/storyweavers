#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/nation_slap_lotto_grandparent_s_house_kindness.py
=================================================================================

A standalone story world for a small Animal Story-style domain set in a
grandparent's house, with kindness and teamwork as the turn and resolution.

Seed-tale sketch:
---
A little animal from a far nation visits Grandparent's house with a shiny lotto
board. A pushy slap knocks the pieces aside, and everyone feels the tension.
Then the family slows down, uses kindness and teamwork, and finishes the game
together.

World premise:
- "nation" is the origin-word of the little traveler.
- "slap" is the disruptive action that scatters the lotto pieces.
- "lotto" is the prized game everyone wants to play.
- Kindness and Teamwork are the emotional tools that resolve the story.

This script follows the Storyweavers world contract:
- self-contained stdlib script
- imports results eagerly, asp lazily
- exposes StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "grandparent's house"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    tag: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    kind: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("slap", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.worn_by != actor.id:
                continue
            sig = ("spill", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["scattered"] = item.meters.get("scattered", 0.0) + 1
            item.meters["messy"] = item.meters.get("messy", 0.0) + 1
            out.append(f"Their {item.label} scattered across the table.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("messy", 0.0) < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append(f"That made {carer.label} worry about the tidy house.")
    return out


def _r_kind(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("kindness", 0.0) < THRESHOLD:
            continue
        sig = ("kind", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = max(0.0, actor.memes.get("worry", 0.0) - 1)
        actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
        out.append(f"{actor.label} spoke softly and helped everyone calm down.")
    return out


def _r_team(world: World) -> list[str]:
    out: list[str] = []
    team = sum(1 for c in world.characters() if c.memes.get("teamwork", 0.0) >= THRESHOLD)
    if team < 2:
        return out
    sig = ("team", team)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for item in world.entities.values():
        if item.meters.get("messy", 0.0) >= THRESHOLD:
            item.meters["messy"] = 0.0
            item.meters["sorted"] = item.meters.get("sorted", 0.0) + 1
    out.append("Together, they picked up every piece and put the lotto board back in place.")
    return out


CAUSAL_RULES = [
    Rule("spill", _r_spill),
    Rule("worry", _r_worry),
    Rule("kind", _r_kind),
    Rule("team", _r_team),
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
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting(place="grandparent's house", indoors=True, affords={"lotto"})

ACTIVITIES = {
    "lotto": Activity(
        id="lotto",
        verb="play lotto",
        gerund="playing lotto",
        rush="reach for the lotto cards",
        mess="slap",
        soil="scattered all over",
        tag="lotto",
    )
}

PRIZES = {
    "lotto": Prize(
        label="lotto board",
        phrase="a bright lotto board with little animal pictures",
        type="lotto_board",
        location="table",
    )
}

AIDS = {
    "kindness": Aid(
        id="kindness",
        label="kindness",
        prep="speak kindly and help tidy up",
        tail="smiled and took turns",
        kind="kindness",
    ),
    "teamwork": Aid(
        id="teamwork",
        label="teamwork",
        prep="work together to sort the cards",
        tail="worked side by side",
        kind="teamwork",
    ),
}

NAMES = {
    "fox": ["Fia", "Finn", "Fawn"],
    "rabbit": ["Rumi", "Rae", "Ro"],
    "bear": ["Bibi", "Bram", "Bo"],
}

TYPES = ["fox", "rabbit", "bear"]
NATIONS = ["Sun Nation", "River Nation", "Hill Nation"]

TRAITS = ["curious", "gentle", "brave", "playful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    animal: str
    nation: str
    grandparent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def validate_combo(activity: Activity, prize: Prize) -> bool:
    return activity.id == "lotto" and prize.type == "lotto_board"


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: this world only supports the lotto game in grandparent's house, "
        f"and the chosen prize must be the lotto board.)"
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.animal,
        label=params.name,
        meters={},
        memes={"kindness": 0.0, "teamwork": 0.0, "joy": 0.0, "worry": 0.0},
    ))
    grandparent = world.add(Entity(
        id="Grandparent",
        kind="character",
        type=params.grandparent,
        label="Grandparent",
        memes={"worry": 0.0, "joy": 0.0},
    ))
    prize = world.add(Entity(
        id="LottoBoard",
        type="lotto_board",
        label="lotto board",
        phrase="a bright lotto board with little animal pictures",
        owner=hero.id,
        caretaker=grandparent.id,
        worn_by=hero.id,
        meters={"messy": 0.0, "sorted": 0.0, "scattered": 0.0},
    ))

    world.facts.update(hero=hero, grandparent=grandparent, prize=prize, params=params)
    return world


def intro(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    params: StoryParams = f["params"]
    world.say(
        f"{hero.label} was a little {params.animal} from the {params.nation}, and "
        f"{hero.pronoun('possessive')} favorite place was {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved {ACTIVITIES['lotto'].gerund} with the shiny lotto board."
    )
    world.say(
        f"At {world.setting.place}, {params.grandparent} kept the board safe and ready on the table."
    )


def conflict(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    gp: Entity = f["grandparent"]
    prize: Entity = f["prize"]
    act = ACTIVITIES["lotto"]

    world.para()
    world.say(
        f"One afternoon, {hero.label} wanted to {act.verb} right away."
    )
    world.say(
        f"Then a quick {act.mess} came with a sharp {act.mess} on the table, and the cards flew apart."
    )
    hero.meters["slap"] = hero.meters.get("slap", 0.0) + 1
    propagate(world)
    world.say(
        f"{gp.label} frowned a little because the {prize.label} was no longer neat."
    )


def resolve(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    gp: Entity = f["grandparent"]
    prize: Entity = f["prize"]

    world.para()
    hero.memes["kindness"] = 1.0
    hero.memes["teamwork"] = 1.0
    gp.memes["teamwork"] = 1.0
    propagate(world)
    world.say(
        f"{hero.label} said sorry and used kindness to gather the cards."
    )
    world.say(
        f"{hero.label} and {gp.label} used teamwork to sort every piece, and soon the lotto board was tidy again."
    )
    world.say(
        f"After that, they played lotto together at {world.setting.place}, and the room felt warm and happy."
    )
    world.say(
        f"The {prize.label} stayed safe on the table, and the little {f['params'].animal} smiled like the best day had just begun."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    intro(world)
    conflict(world)
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    return [
        f"Write an Animal Story about a little {params.animal} from the {params.nation} visiting grandparent's house to play lotto.",
        f"Tell a short story where a {params.trait} {params.animal} makes a slap mistake with a lotto board, then kindness and teamwork fix it.",
        f"Write a child-friendly story set in grandparent's house that includes the words nation, slap, and lotto.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    gp: Entity = f["grandparent"]
    params: StoryParams = f["params"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, a little {params.animal} from the {params.nation} who visited grandparent's house.",
        ),
        QAItem(
            question=f"What game did {hero.label} want to play?",
            answer="They wanted to play lotto with the shiny lotto board.",
        ),
        QAItem(
            question=f"What went wrong when the game started?",
            answer="A quick slap scattered the lotto pieces across the table.",
        ),
        QAItem(
            question=f"How did {hero.label} and Grandparent fix the problem?",
            answer="They used kindness and teamwork to pick up every piece and make the lotto board tidy again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward others.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together to do a job better and faster.",
        ),
        QAItem(
            question="Why do people tidy up scattered game pieces?",
            answer="People tidy up game pieces so the game stays organized and everyone can keep playing safely.",
        ),
    ]


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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(Place, Activity, Prize) :- setting(Place), affords(Place, Activity), prize(Prize), activity(Activity), at_risk(Activity, Prize), has_fix(Activity, Prize).

at_risk(lotto, lotto_board).

has_fix(lotto, lotto_board).

valid_story(Place, Activity, Prize, Animal) :- valid(Place, Activity, Prize), wears(Animal, Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "grandparent_house"))
    lines.append(asp.fact("affords", "grandparent_house", "lotto"))
    lines.append(asp.fact("activity", "lotto"))
    lines.append(asp.fact("prize", "lotto_board"))
    for animal in TYPES:
        lines.append(asp.fact("wears", animal, "lotto_board"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    return [("grandparent's house", "lotto", "lotto")]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    cl = {("grandparent's house", a, p) for (_, a, p) in cl} if cl else set()
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world: nation, slap, lotto, kindness, teamwork.")
    ap.add_argument("--place", choices=["grandparent's house"], default=None)
    ap.add_argument("--activity", choices=sorted(ACTIVITIES), default=None)
    ap.add_argument("--prize", choices=sorted(PRIZES), default=None)
    ap.add_argument("--name")
    ap.add_argument("--animal", choices=TYPES)
    ap.add_argument("--nation", choices=NATIONS)
    ap.add_argument("--grandparent", choices=["grandmother", "grandfather"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        if not validate_combo(ACTIVITIES[args.activity], PRIZES[args.prize]):
            raise StoryError(explain_rejection(ACTIVITIES[args.activity], PRIZES[args.prize]))
    combos = valid_combos()
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(combos)
    animal = args.animal or rng.choice(TYPES)
    nation = args.nation or rng.choice(NATIONS)
    grandparent = args.grandparent or rng.choice(["grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(NAMES[animal])
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=name,
        animal=animal,
        nation=nation,
        grandparent=grandparent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(combos)} compatible combos ({len(stories)} with animal):")
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            place="grandparent's house",
            activity="lotto",
            prize="lotto",
            name="Fia",
            animal="fox",
            nation="Sun Nation",
            grandparent="grandmother",
            trait="kind",
        )
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
