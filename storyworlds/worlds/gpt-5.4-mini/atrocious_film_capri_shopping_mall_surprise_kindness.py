#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/atrocious_film_capri_shopping_mall_surprise_kindness.py
========================================================================================

A standalone story world for a small adventure tale set in a shopping mall.

Seed inspiration:
- words: atrocious, film, capri
- features: Surprise, Kindness, Twist
- style: Adventure

Premise:
A child goes to a shopping mall for a film outing, faces an atrocious mishap
with a snapped capri outfit and a surprising detour, then kindness from a helper
turns the trip into a brighter adventure.

This script follows the Storyweavers contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, --show-asp
- includes Python reasonableness gate and inline ASP twin
- generates story-grounded QA from simulated state, not by parsing rendered text
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"tired": 0.0, "worry": 0.0, "kindness": 0.0, "surprise": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "hope": 0.0, "joy": 0.0, "stunned": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    scene: str
    inside: bool = True
    has_film_shop: bool = True
    has_cafe: bool = True
    has_hallway: bool = True

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
class Goal:
    id: str
    phrase: str
    need: str
    tags: set[str] = field(default_factory=set)

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
class Surprise:
    id: str
    twist: str
    reveal: str
    gift: str
    tags: set[str] = field(default_factory=set)

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
class Kindness:
    id: str
    action: str
    help_text: str
    tags: set[str] = field(default_factory=set)

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
class Twist:
    id: str
    turn: str
    fix: str
    tags: set[str] = field(default_factory=set)

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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


def _r_cheer(world: World) -> list[str]:
    out = []
    kid = world.get("child")
    if kid.memes["hope"] >= THRESHOLD and ("cheer", "child") not in world.fired:
        world.fired.add(("cheer", "child"))
        kid.meters["worry"] = max(0.0, kid.meters["worry"] - 1)
        kid.memes["joy"] += 1
        out.append("__cheer__")
    return out


def _r_kindness(world: World) -> list[str]:
    out = []
    helper = world.get("helper")
    if helper.meters["kindness"] >= THRESHOLD and ("kindness", "helper") not in world.fired:
        world.fired.add(("kindness", "helper"))
        world.get("child").memes["hope"] += 1
        out.append("__kindness__")
    return out


CAUSAL_RULES = [
    _r_kindness,
    _r_cheer,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend([s for s in sents if not s.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(place: Place, goal: Goal, surprise: Surprise, kindness: Kindness, twist: Twist) -> bool:
    return place.inside and place.has_film_shop and goal.id == "film" and "shopping_mall" in place.id and all((surprise.id, kindness.id, twist.id))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for goal_id, goal in GOALS.items():
            for surprise_id, surprise in SURPRISES.items():
                for kindness_id, kindness in KINDNESSES.items():
                    for twist_id, twist in TWISTS.items():
                        if reasonableness_gate(place, goal, surprise, kindness, twist):
                            combos.append((place_id, goal_id, surprise_id))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.inside:
            lines.append(asp.fact("inside", pid))
        if p.has_film_shop:
            lines.append(asp.fact("film_shop", pid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    for kid in KINDNESSES:
        lines.append(asp.fact("kindness", kid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, G, S) :- place(P), goal(G), surprise(S), inside(P), film_shop(P), G = film.
"""


@dataclass
@dataclass
class StoryParams:
    place: str
    goal: str
    surprise: str
    kindness: str
    twist: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
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


PLACES = {
    "shopping_mall": Place("shopping_mall", "a bright shopping mall with glass rails, shiny floors, and a busy film shop", inside=True, has_film_shop=True),
    "mall_atrium": Place("mall_atrium", "the wide atrium of a shopping mall, full of echoing footsteps and store lights", inside=True, has_film_shop=True),
}

GOALS = {
    "film": Goal("film", "to see a new film", "tickets, popcorn, and a good seat", tags={"film"}),
}

SURPRISES = {
    "capri_snap": Surprise("capri_snap", "a capri hem snagged on a door handle", "the snap made an atrocious rip", "a spare ribbon and a calmer path", tags={"capri", "surprise"}),
    "wrong_ticket": Surprise("wrong_ticket", "the ticket scanner blinked red", "the showtime had been changed", "a quick swap at the counter", tags={"surprise"}),
}

KINDNESSES = {
    "helper_ribbon": Kindness("helper_ribbon", "offered a ribbon", "carefully tied the torn capri hem", tags={"kindness", "capri"}),
    "helper_popcorn": Kindness("helper_popcorn", "shared popcorn", "made the child feel brave again", tags={"kindness"}),
}

TWISTS = {
    "lost_lobby": Twist("lost_lobby", "the child took a wrong turn near the arcade", "the mall suddenly felt enormous", "a map from the kiosk", tags={"twist"}),
    "secret_shortcut": Twist("secret_shortcut", "a hidden hallway led behind the film shop", "the route was faster than expected", "a staff member pointing the way", tags={"twist"}),
}

CHILD_NAMES = ["Mia", "Noah", "Lena", "Owen", "Zoe", "Eli", "Ava", "Theo"]
HELPER_NAMES = ["Sam", "Nora", "Iris", "Ben", "Maya", "June", "Leo", "Tess"]


def valid_goal(goal_id: str) -> bool:
    return goal_id in GOALS


def explain_rejection() -> str:
    return "(No story: this world needs a shopping-mall film adventure with a real surprise, a kind help, and a twist that still fits the mall.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.goal and not valid_goal(args.goal):
        raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.goal is None or c[1] == args.goal)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError(explain_rejection())
    place, goal, surprise = rng.choice(sorted(combos))
    kindness = args.kindness or rng.choice(sorted(KINDNESSES))
    twist = args.twist or rng.choice(sorted(TWISTS))
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != child])
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    return StoryParams(place, goal, surprise, kindness, twist, child, child_gender, helper, helper_gender)


def intro(world: World, child: Entity, helper: Entity, place: Place, goal: Goal) -> None:
    world.say(f"{child.id} and {helper.id} arrived at {place.scene}. {child.id} had come for {goal.phrase}, and the mall buzzed like an adventure waiting to start.")
    world.say(f"{child.id} carried a small bag and wore capri pants, ready for a fun day under the bright mall lights.")


def surprise_beat(world: World, child: Entity, surprise: Surprise) -> None:
    child.memes["stunned"] += 1
    child.meters["worry"] += 1
    world.say(f"Then came a surprise: {surprise.twist}. It was atrocious for the capri outfit, and {surprise.reveal}.")


def twist_beat(world: World, child: Entity, twist: Twist) -> None:
    child.memes["curiosity"] += 1
    world.say(f"Before they could fix the problem, {twist.turn}. That twist made the shopping mall feel huge and mysterious all at once.")


def kindness_beat(world: World, helper: Entity, kindness: Kindness) -> None:
    helper.meters["kindness"] += 1
    world.say(f"{helper.id} smiled and {kindness.action}. {kindness.help_text}, and the child began to feel brave again.")


def resolve_story(world: World, child: Entity, helper: Entity, kindness: Kindness, twist: Twist) -> None:
    child.memes["hope"] += 1
    child.memes["joy"] += 1
    propagate(world, narrate=False)
    world.say(f"With kindness and a quick twist of luck, they kept going. The capri trouble was handled, the film shop was found, and the day turned into a small adventure instead of a disaster.")
    world.say(f"By the end, {child.id} was smiling beside {helper.id}, both of them walking toward the film with the shopping mall lights sparkling all around them.")


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    goal = GOALS[params.goal]
    surprise = SURPRISES[params.surprise]
    kindness = KINDNESSES[params.kindness]
    twist = TWISTS[params.twist]
    child = world.add(Entity("child", kind="character", type=params.child_gender, label=params.child, role="hero"))
    helper = world.add(Entity("helper", kind="character", type=params.helper_gender, label=params.helper, role="helper"))
    world.add(Entity("mall", type="place", label=place.id))
    intro(world, child, helper, place, goal)
    world.para()
    surprise_beat(world, child, surprise)
    twist_beat(world, child, twist)
    kindness_beat(world, helper, kindness)
    world.para()
    resolve_story(world, child, helper, kindness, twist)
    world.facts.update(place=place, goal=goal, surprise=surprise, kindness=kindness, twist=twist, child=child, helper=helper)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an adventure story set in a shopping mall that includes the words atrocious, film, and capri.",
        f"Tell a child-friendly mall adventure where {f['child'].id} wants to see a film, faces an atrocious capri mishap, and kindness helps the day recover.",
        f"Write a story with a surprise, a kind helper, and a twist in a shopping mall, ending with a child still reaching the film.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    surprise = f["surprise"]
    kindness = f["kindness"]
    twist = f["twist"]
    return [
        QAItem(question=f"What was {child.id} doing at the shopping mall?", answer=f"{child.id} was there to see a film, and the mall trip was meant to be a fun adventure."),
        QAItem(question=f"What went wrong with the capri outfit?", answer=f"{surprise.reveal}. That made the capri trouble feel atrocious, because it turned a happy trip into a sudden mess."),
        QAItem(question=f"How did {helper.id} help?", answer=f"{helper.id} {kindness.action} and stayed calm. That kindness gave {child.id} hope and helped turn the trip back toward the film."),
        QAItem(question=f"What was the twist in the story?", answer=f"{twist.turn}. It changed the route through the mall and made the adventure feel bigger before things got better again."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a shopping mall?", answer="A shopping mall is a large building with many stores, hallways, and places where people can walk, shop, or eat indoors."),
        QAItem(question="What is a film?", answer="A film is a movie that people watch on a screen, usually while sitting in a theater with other people."),
        QAItem(question="What are capri pants?", answer="Capri pants are trousers that are shorter than long pants and end partway down the leg."),
        QAItem(question="What does kindness mean?", answer="Kindness means helping someone gently, sharing, or making them feel better when something goes wrong."),
        QAItem(question="What is a surprise?", answer="A surprise is something unexpected that happens all of a sudden."),
        QAItem(question="What is a twist in a story?", answer="A twist is a turn in the story that changes what is happening and makes the adventure feel different."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(f"{asp_facts()}\n{ASP_RULES}\n#show valid/3.\n")
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    clingo = set(asp_valid_combos())
    python = set(valid_combos())
    rc = 0
    if clingo == python:
        print(f"OK: ASP matches valid_combos() ({len(clingo)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combo parity.")
        print("only in asp:", sorted(clingo - python))
        print("only in python:", sorted(python - clingo))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, goal=None, surprise=None, kindness=None, twist=None, child=None, child_gender=None, helper=None, helper_gender=None), random.Random(777)))
        _ = sample.story
        print("OK: smoke-test generate() succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world for a shopping mall surprise, kindness, and twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def resolve_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError(explain_rejection())
    place, goal, surprise = rng.choice(combos)
    kindness = args.kindness or rng.choice(sorted(KINDNESSES))
    twist = args.twist or rng.choice(sorted(TWISTS))
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != child])
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    return StoryParams(place, goal, surprise, kindness, twist, child, child_gender, helper, helper_gender)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(f"{asp_facts()}\n{ASP_RULES}")
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for t in asp_valid_combos():
            print(" ", t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in [
            StoryParams("shopping_mall", "film", "capri_snap", "Mia", "girl", "Nora", "helper_ribbon", "lost_lobby"),
            StoryParams("mall_atrium", "film", "wrong_ticket", "Noah", "boy", "Sam", "helper_popcorn", "secret_shortcut"),
        ]:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_args(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
