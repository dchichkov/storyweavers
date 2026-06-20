#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/minister_escort_friendship_twist_animal_story.py
=================================================================================

A small animal-story world about a kind minister, an escort, a friendship, and a
gentle twist.

Seed premise:
- Animal Story style.
- Include the words "minister" and "escort".
- Features: Friendship, Twist.

World shape:
- An animal character wants to visit a minister.
- A careful escort offers to guide the animal through a tricky place.
- Friendship changes the plan.
- A twist reveals the escort is not a stranger at all, but a helper with a
  connection to the animal.
- The ending proves what changed with a concrete image.

This is a standalone storyworld script following the shared StorySample/QAItem
contract.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "cow", "duck"}
        male = {"boy", "father", "dad", "man", "rooster", "ram", "dog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



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
    risky: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class EscortPlan:
    id: str
    label: str
    route: str
    help_phrase: str
    twist_phrase: str
    safe_end: str
    risk: int
    support: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        self.places: dict[str, Place] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        if isinstance(ent, Place):
            self.places[ent.id] = ent
        else:
            self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def place(self, pid: str) -> Place:
        return self.places[pid]

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
        clone.places = copy.deepcopy(self.places)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.place("road").meters["quiet"] += 1
        out.append("__worry__")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["friendship"] < THRESHOLD:
            continue
        sig = ("friendship", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["brave"] += 1
        out.append("__friendship__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("friendship", "social", _r_friendship)]


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


def reasonable_combo(place: Place, plan: EscortPlan) -> bool:
    return place.risky and plan.support >= 2 and plan.risk <= 3


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for plid, plan in PLANS.items():
            if reasonable_combo(place, plan):
                combos.append((pid, plid))
    return combos


def predict_twist(world: World, child: Entity, escort: Entity, plan: EscortPlan) -> dict:
    sim = world.copy()
    _go_route(sim, sim.get(child.id), sim.get(escort.id), plan, narrate=False)
    return {
        "friendship": sim.get(child.id).memes["friendship"],
        "worry": sim.get(child.id).memes["worry"],
        "twist": sim.facts.get("twist", ""),
    }


def _go_route(world: World, child: Entity, escort: Entity, plan: EscortPlan, narrate: bool = True) -> None:
    child.meters["travel"] += 1
    escort.meters["travel"] += 1
    child.memes["trust"] += 1
    escort.memes["care"] += 1
    world.place("road").meters["used"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, minister: Entity, place: Place) -> None:
    child.memes["hope"] += 1
    world.say(
        f"On a warm morning, {child.id} the {child.type} wanted to visit the minister at the {place.label}."
    )
    world.say(
        f"{child.id} carried a small basket of seeds and a bright feather, because {child.pronoun()} wanted the minister to bless the little garden."
    )


def meet_escort(world: World, child: Entity, escort: Entity, plan: EscortPlan) -> None:
    child.memes["worry"] += 1
    escort.memes["worry"] += 1
    world.say(
        f"At the edge of the road, {escort.id} offered to escort {child.id} along the windy path."
    )
    world.say(
        f'"The path is tricky," {escort.id} said. "{plan.help_phrase}."'
    )


def warn_turn(world: World, child: Entity, escort: Entity, plan: EscortPlan, place: Place) -> None:
    pred = predict_twist(world, child, escort, plan)
    world.facts["predicted_worry"] = pred["worry"]
    world.facts["predicted_friendship"] = pred["friendship"]
    world.say(
        f"{child.id} looked at the dark bend in the road and felt unsure. The wind tugged at the basket."
    )
    world.say(
        f'But {escort.id} smiled and said, "{plan.twist_phrase}"'
    )


def twist_reveal(world: World, child: Entity, escort: Entity, minister: Entity, plan: EscortPlan) -> None:
    escort.memes["friendship"] += 1
    child.memes["friendship"] += 1
    world.facts["twist"] = "escort was a cousin of the minister and a friend from the pond"
    world.say(
        f"Then came the twist: {escort.id} was not a stranger after all. {escort.id} was the minister's cousin, and {child.id} had once shared pond bread with {escort.id}."
    )
    world.say(
        f"{child.id} blinked, then smiled, because the escort was really an old friend in a new hat."
    )


def arrive(world: World, child: Entity, minister: Entity, plan: EscortPlan, place: Place) -> None:
    child.memes["joy"] += 1
    minister.memes["joy"] += 1
    world.say(
        f"Together they followed {plan.route} and reached the minister at the {place.label}."
    )
    world.say(
        f"{minister.id} tied the feather to the seed basket and thanked {child.id} for the gift."
    )


def ending(world: World, child: Entity, escort: Entity, minister: Entity, plan: EscortPlan) -> None:
    child.memes["calm"] += 1
    child.meters["offered"] += 1
    world.say(
        f"By the end, {child.id} walked beside {escort.id} without fear, and the basket stayed steady in {child.pronoun('possessive')} hands."
    )
    world.say(
        f"The little group left the minister's gate with a new friendship, and the feather still tucked safely beside the seeds."
    )


def tell(place: Place, plan: EscortPlan, child_name: str = "Milo", child_type: str = "rabbit",
         escort_name: str = "Tess", escort_type: str = "fox", minister_name: str = "Minister Reed",
         minister_type: str = "goat") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="visitor"))
    escort = world.add(Entity(id=escort_name, kind="character", type=escort_type, role="escort"))
    minister = world.add(Entity(id=minister_name, kind="character", type=minister_type, role="minister", label="the minister"))
    world.add(Place(id="road", label="the road", kind="route", risky=False))
    world.add(place)

    child.memes["hope"] = 1
    escort.memes["care"] = 1
    minister.memes["friendship"] = 1

    opening(world, child, minister, place)
    world.para()
    meet_escort(world, child, escort, plan)
    warn_turn(world, child, escort, plan, place)
    twist_reveal(world, child, escort, minister, plan)
    world.para()
    _go_route(world, child, escort, plan)
    arrive(world, child, minister, plan, place)
    ending(world, child, escort, minister, plan)

    world.facts.update(
        child=child,
        escort=escort,
        minister=minister,
        place=place,
        plan=plan,
        outcome="twist_friendship",
        twist=world.facts.get("twist", ""),
    )
    return world


PLACES = {
    "hill": Place("hill", "the hill path", "path", risky=True),
    "woods": Place("woods", "the woods trail", "trail", risky=True),
    "river": Place("river", "the river bridge", "bridge", risky=True),
    "meadow": Place("meadow", "the meadow lane", "lane", risky=True),
    "garden": Place("garden", "the garden gate", "gate", risky=False),
}

PLANS = {
    "lantern": EscortPlan(
        "lantern", "a lantern escort", "the lantern-lit lane",
        "kept close and watched every stone", "the escort knew the minister had sent them",
        "They reached the minister in good time.", risk=2, support=3,
        tags={"light", "guide"},
    ),
    "rope": EscortPlan(
        "rope", "a rope guide", "the rope-marked path",
        "kept one end of the rope in sight", "the escort wore the minister's blue ribbon",
        "They came through together, step by step.", risk=3, support=2,
        tags={"guide", "rope"},
    ),
    "map": EscortPlan(
        "map", "a map escort", "the map-straight road",
        "held up the map and pointed at each turn", "the escort carried the minister's signet",
        "They arrived with only a little wobble in their steps.", risk=1, support=2,
        tags={"map", "guide"},
    ),
}

GIRL_NAMES = ["Mina", "Ruby", "Luna", "Pip", "Tia"]
BOY_NAMES = ["Nico", "Otis", "Bean", "Toby", "Milo"]
ANIMAL_TYPES = ["rabbit", "fox", "goat", "duck", "mouse", "hedgehog"]


@dataclass
@dataclass
class StoryParams:
    place: str
    plan: str
    child_name: str
    child_type: str
    escort_name: str
    escort_type: str
    minister_name: str
    minister_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


KNOWLEDGE = {
    "minister": [("What is a minister?", "A minister is a grown-up who leads a church or helps a community with kind words and ceremonies.")],
    "escort": [("What does escort mean?", "To escort someone means to walk with them or guide them safely to a place.")],
    "friendship": [("What is friendship?", "Friendship is when two beings care about each other, help each other, and enjoy being together.")],
    "twist": [("What is a twist in a story?", "A twist is a surprising change that makes the story turn in a new way.")],
    "rabbit": [("What do rabbits like to eat?", "Rabbits like to eat grasses, hay, and leafy greens.")],
    "fox": [("What is a fox?", "A fox is a clever wild animal with a bushy tail and sharp ears.")],
    "goat": [("What is a goat?", "A goat is an animal that likes to climb and nibble on leaves.")],
    "duck": [("What do ducks use their feet for?", "Ducks use their feet to paddle in water and walk on soft ground.")],
    "mouse": [("Why are mice careful?", "Mice are small, so they move carefully and hide where it is safe.")],
    "hedgehog": [("What is a hedgehog?", "A hedgehog is a small animal with spines that curls into a ball when scared.")],
}
KNOWLEDGE_ORDER = ["minister", "escort", "friendship", "twist", "rabbit", "fox", "goat", "duck", "mouse", "hedgehog"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a young child that includes the words "minister" and "escort" and ends with a friendly surprise.',
        f"Tell a gentle story about {f['child'].id} asking an escort to help reach a minister, with a twist that changes what the escort means to them.",
        f"Write a friendship story in animal-story style where a minister appears and the escort turns out to be someone important to the child.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    escort: Entity = f["escort"]
    minister: Entity = f["minister"]
    place: Place = f["place"]
    plan: EscortPlan = f["plan"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {escort.id}, and {minister.id}. The story follows how a visit to the minister becomes a friendship story."),
        ("Why did {0} need an escort?".format(child.id),
         f"{child.id} needed help because the path to {place.label} was tricky. The escort stayed close so the child could walk safely and not lose the basket."),
        ("What was the twist?",
         f"The twist was that {escort.id} was not a stranger. {escort.id} was connected to the minister and already knew {child.id} from an old friendship."),
        ("How did the story end?",
         f"It ended with the child reaching the minister safely and with a new friendship growing. The basket of seeds stayed steady, which proves the escort really helped."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {world.facts["child"].type, world.facts["escort"].type, world.facts["minister"].type, "friendship", "twist"}
    tags |= world.facts["plan"].tags
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hill", "lantern", "Milo", "rabbit", "Tess", "fox", "Minister Reed", "goat"),
    StoryParams("woods", "rope", "Ruby", "mouse", "Otis", "hedgehog", "Minister Green", "goat"),
    StoryParams("river", "map", "Nico", "duck", "Luna", "fox", "Minister Bell", "goat"),
    StoryParams("meadow", "lantern", "Bean", "rabbit", "Tia", "mouse", "Minister Ash", "goat"),
]


def explain_rejection(place: Place, plan: EscortPlan) -> str:
    if not reasonable_combo(place, plan):
        return f"(No story: {plan.label} does not fit the path at {place.label}, so there is no honest escort story here.)"
    return "(No story: invalid combination.)"


def valid_for_place(place: str, plan: str) -> bool:
    return reasonable_combo(PLACES[place], PLANS[plan])


ASP_RULES = r"""
valid(P, Pl) :- place(P), plan(Pl), risky(P), support(Pl, S), S >= 2, risk(Pl, R), R <= 3.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.risky:
            lines.append(asp.fact("risky", pid))
    for plid, pl in PLANS.items():
        lines.append(asp.fact("plan", plid))
        lines.append(asp.fact("support", plid, pl.support))
        lines.append(asp.fact("risk", plid, pl.risk))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    ok = True
    if clingo_set != python_set:
        ok = False
        print("MISMATCH in valid combos")
        if clingo_set - python_set:
            print("only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("only in python:", sorted(python_set - clingo_set))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    print("OK: ASP parity passed." if ok else "VERIFY FAILED.")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with minister, escort, friendship, and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=ANIMAL_TYPES)
    ap.add_argument("--escort-name")
    ap.add_argument("--escort-type", choices=ANIMAL_TYPES)
    ap.add_argument("--minister-name")
    ap.add_argument("--minister-type", choices=ANIMAL_TYPES)
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
              and (args.plan is None or c[1] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, plan = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(ANIMAL_TYPES)
    escort_type = args.escort_type or rng.choice([t for t in ANIMAL_TYPES if t != child_type])
    minister_type = args.minister_type or "goat"
    child_name = args.child_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    escort_name = args.escort_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != child_name])
    minister_name = args.minister_name or rng.choice(["Minister Reed", "Minister Green", "Minister Bell", "Minister Ash"])
    return StoryParams(place, plan, child_name, child_type, escort_name, escort_type, minister_name, minister_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PLANS[params.plan], params.child_name, params.child_type,
                 params.escort_name, params.escort_type, params.minister_name, params.minister_type)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for p, pl in asp_valid_combos():
            print(p, pl)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
