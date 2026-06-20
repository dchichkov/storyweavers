#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mallard_wick_injection_teamwork_kindness_twist_superhero.py
===========================================================================================

A tiny standalone storyworld for a superhero-flavored rescue tale with a twist:
a small team of kid heroes helps an injured mallard, protects a dangerous wick,
and uses a careful injection as part of the fix. The story is built from a
simulated world state, with physical meters and emotional memes driving the prose.

The world models a simple premise:
- A child superhero squad notices a mallard in trouble near a flickering wick.
- One hero is tempted to act too fast, but teamwork and kindness steer the plan.
- A careful injection is used as medicine, not as a weapon.
- The ending twist proves the heroes were helping a duck, not chasing a villain.

This script follows the shared storyworld contract:
- StoryParams, build_parser, resolve_params, generate, emit, main
- StoryError / QAItem / StorySample from storyworlds.results
- --qa, --json, --trace, --all, --seed, --asp, --verify, --show-asp
- Python validity checks plus an inline ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
TEAM_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    injured: bool = False
    safe: bool = False
    wet: bool = False
    has_wick: bool = False
    has_injection: bool = False

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"risk": 0.0, "care": 0.0, "teamwork": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "fear": 0.0, "kindness": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    kind: str
    has_water: bool = False
    has_light: bool = True
    risky_wick: bool = False
    warmth: str = ""

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class TeamMove:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_team(world: World) -> list[str]:
    out: list[str] = []
    squad = [e for e in list(world.entities.values()) if e.role in {"hero1", "hero2"}]
    if len(squad) < 2:
        return out
    if all(e.meters["teamwork"] >= TEAM_MIN for e in squad):
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__team__")
    return out


def _r_calm_risk(world: World) -> list[str]:
    out: list[str] = []
    wick = world.entities.get("wick")
    if wick and wick.has_wick and wick.meters["risk"] >= THRESHOLD:
        sig = ("risk",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__risk__")
    return out


CAUSAL_RULES = [
    Rule("team", "social", _r_team),
    Rule("risk", "physical", _r_calm_risk),
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


def _use_wick(world: World, narrate: bool = True) -> None:
    wick = world.get("wick")
    wick.meters["risk"] += 1
    propagate(world, narrate=narrate)


def predict_injection(world: World, move: TeamMove) -> dict:
    sim = world.copy()
    _use_wick(sim, narrate=False)
    doc = sim.get("duck")
    return {
        "risk": sim.get("wick").meters["risk"],
        "duck_safe": doc.safe,
        "can_help": move.power >= 1,
    }


def build_scene(world: World, hero1: Entity, hero2: Entity, duck: Entity, place: Place) -> None:
    world.say(
        f"On a bright afternoon, {hero1.id} and {hero2.id} watched over {place.label}. "
        f"That was when they noticed a small mallard by the water, shivering under a low wick."
    )
    world.say(
        f'The mallard blinked its tiny eyes, and {hero2.id} whispered, '
        f'"That duck needs help, not a chase."'
    )


def twist_hint(world: World, hero1: Entity, hero2: Entity) -> None:
    hero1.memes["pride"] += 1
    hero2.memes["kindness"] += 1
    world.say(
        f'{hero1.id} lifted a fist. "I can grab the wick!" {hero1.pronoun()} said. '
        f'But {hero2.id} shook {hero2.pronoun("possessive")} head. "Wait. Let us think like a team."'
    )


def team_up(world: World, hero1: Entity, hero2: Entity) -> None:
    hero1.meters["teamwork"] += 1
    hero2.meters["teamwork"] += 1
    hero1.memes["hope"] += 1
    hero2.memes["hope"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they made a plan. One hero blocked the breeze with a jacket, "
        f"and the other kept the duck calm with a soft voice."
    )


def kindness_move(world: World, hero1: Entity, hero2: Entity, duck: Entity) -> None:
    hero1.memes["kindness"] += 1
    hero2.memes["kindness"] += 1
    duck.meters["care"] += 1
    duck.memes["fear"] = max(0.0, duck.memes["fear"] - 1)
    world.say(
        f"{hero2.id} knelt down and offered water in a shallow cap. "
        f"The mallard stopped trembling and nibbled once, as if it knew the heroes meant well."
    )


def injection_move(world: World, hero1: Entity, hero2: Entity, duck: Entity, move: TeamMove) -> None:
    duck.has_injection = True
    duck.safe = True
    duck.injured = False
    duck.meters["care"] += 2
    duck.memes["hope"] += 2
    world.say(
        f"Then {hero1.id} held still while {hero2.id} gave the duck a careful injection "
        f"to help it heal. It was medicine, not a trick, and the mallard rested easier at once."
    )


def wick_result(world: World, place: Place, duck: Entity) -> None:
    wick = world.get("wick")
    if wick.meters["risk"] >= THRESHOLD:
        world.say(
            f"The wick flickered once, but the heroes had already moved the duck to safety. "
            f"No spark reached the feathers, and the little light went out harmlessly."
        )
    if duck.safe:
        world.say(
            f"At last the mallard paddled back toward the water, calmer and cleaner, "
            f"with both heroes smiling beside it."
        )


def ending_twist(world: World, hero1: Entity, hero2: Entity, duck: Entity) -> None:
    world.say(
        f'Then came the twist: the "mystery mission" was never about a villain at all. '
        f'It was about protecting a lost mallard, and their teamwork had been the real superpower.'
    )
    world.say(
        f"{hero1.id} laughed, {hero2.id} smiled, and the duck gave one proud quack as the day turned gentle again."
    )


def tell(place: Place, move: TeamMove, hero1_name: str = "Mia", hero2_name: str = "Ravi") -> World:
    world = World()
    hero1 = world.add(Entity(id=hero1_name, kind="character", type="girl", role="hero1"))
    hero2 = world.add(Entity(id=hero2_name, kind="character", type="boy", role="hero2"))
    duck = world.add(Entity(id="duck", kind="character", type="duck", label="mallard", injured=True))
    wick = world.add(Entity(id="wick", kind="thing", type="thing", label="wick", has_wick=True))
    world.facts["place"] = place
    world.facts["move"] = move
    world.facts["hero1"] = hero1
    world.facts["hero2"] = hero2
    world.facts["duck"] = duck
    world.facts["wick"] = wick

    build_scene(world, hero1, hero2, duck, place)
    world.para()
    twist_hint(world, hero1, hero2)

    world.para()
    team_up(world, hero1, hero2)
    kindness_move(world, hero1, hero2, duck)
    injection_move(world, hero1, hero2, duck, move)

    world.para()
    wick_result(world, place, duck)
    ending_twist(world, hero1, hero2, duck)

    world.facts.update(outcome="rescued", duck_safe=duck.safe, teamwork=True, kindness=True, twist=True)
    return world


PLACES = {
    "pond": Place("pond", "the pond", "outdoor", has_water=True, has_light=True, risky_wick=True, warmth="sunlit"),
    "harbor": Place("harbor", "the harbor", "outdoor", has_water=True, has_light=True, risky_wick=True, warmth="windy"),
    "roof": Place("roof", "the rooftop garden", "outdoor", has_water=False, has_light=True, risky_wick=True, warmth="breezy"),
}

MOVES = {
    "careful_injection": TeamMove(
        "careful_injection", 3, 3,
        "gave the duck a careful injection to help it heal",
        "tried to help, but the plan was too rushed and the duck stayed frightened",
        "gave the duck a careful injection to help it heal",
    ),
    "gentle_injection": TeamMove(
        "gentle_injection", 3, 2,
        "gave the duck a gentle injection and then covered it with a towel",
        "tried to help, but the duck needed a steadier hand",
        "gave the duck a gentle injection and then covered it with a towel",
    ),
}

NAMES_GIRL = ["Mia", "Nina", "Lina", "Ivy", "Zara", "Pia"]
NAMES_BOY = ["Ravi", "Owen", "Noah", "Eli", "Taro", "Milo"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for mid in MOVES:
            if place.risky_wick:
                combos.append((pid, mid))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    move: str
    hero1: str
    hero2: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: teamwork, kindness, twist, and a mallard.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--hero1")
    ap.add_argument("--hero2")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.move is None or c[1] == args.move)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, move = rng.choice(sorted(combos))
    hero1 = args.hero1 or rng.choice(NAMES_GIRL)
    hero2 = args.hero2 or rng.choice([n for n in NAMES_BOY if n != hero1])
    return StoryParams(place, move, hero1, hero2)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story for a small child that includes the words mallard, wick, and injection, and shows teamwork and kindness.",
        f"Tell a twisty rescue story where {f['hero1'].id} and {f['hero2'].id} help a mallard near a wick and use an injection as medicine.",
        f"Write a gentle superhero tale in which two heroes work together, stay kind, and the ending reveals the duck was the real mission.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero1, hero2, duck, place = f["hero1"], f["hero2"], f["duck"], f["place"]
    return [
        ("Who are the story heroes?",
         f"The story is about {hero1.id} and {hero2.id}. They worked as a team and stayed kind while helping the mallard."),
        ("What needed help?",
         f"The mallard needed help near the wick. The duck was frightened at first, so the heroes moved slowly and gently."),
        ("What did they use the injection for?",
         f"They used the injection as medicine to help the duck heal. It was part of a careful rescue, not something scary."),
        ("How did the story end?",
         f"It ended with the mallard safe and calm. The twist was that the heroes were protecting a duck, not fighting a villain."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a mallard?",
         "A mallard is a kind of duck. Ducks usually live near water and paddle with their feet."),
        ("What is a wick?",
         "A wick is the part of a candle or lamp that can carry flame. It must be handled carefully because it can help make fire."),
        ("What is an injection?",
         "An injection is a way grown-ups or doctors give medicine with a needle. It can help an animal or person heal."),
        ("What does teamwork mean?",
         "Teamwork means people help each other and do a job together. When a team shares the work, the problem is often easier to solve."),
        ("What does kindness mean?",
         "Kindness means being gentle, caring, and helpful. Kind people try to make someone else feel safe."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.type:7}) meters={e.meters} memes={e.memes} flags={[k for k in ['injured','safe','wet','has_wick','has_injection'] if getattr(e, k)]}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pond", "careful_injection", "Mia", "Ravi"),
    StoryParams("harbor", "gentle_injection", "Nina", "Owen"),
]


def explain_rejection() -> str:
    return "(No story: this combination cannot support the rescue twist.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MOVES:
        lines.append(asp.fact("move", mid))
    lines.append(asp.fact("sense_min", 3))
    lines.append(asp.fact("has_wick_scene", "yes"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, M) :- place(P), move(M), has_wick_scene(yes).
outcome(rescued) :- valid(P, M).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches Python valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP does not match Python valid_combos().")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generate() failed: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MOVES[params.move], params.hero1, params.hero2)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{p} {m}" for p, m in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
