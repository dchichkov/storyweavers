#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/coffee_gopher_upset_bad_ending_fairy_tale.py
================================================================================================

A tiny fairy-tale story world about a coffee-carrying gopher, a rising upset,
and a bad ending.

Premise source:
- A little gopher wants coffee in a fairy-tale place.
- The coffee is precious and difficult to carry.
- A spill or loss makes someone upset.
- There is no neat fix: the tale ends in a sad image.

This world is intentionally small and constraint-checked. It produces complete
stories with a beginning, a turn, and a bad ending image, while keeping the
tone close to a fairy tale.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "gopher":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    name: str
    mood: str
    supports: set[str] = field(default_factory=set)


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    spill_kind: str
    fragile: bool = False


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    danger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    action: str
    object: str
    gopher_name: str
    witness_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "castle_kitchen": Place(
        id="castle_kitchen",
        name="the castle kitchen",
        mood="warm and bright",
        supports={"carry", "serve", "sip"},
    ),
    "moonlit_garden": Place(
        id="moonlit_garden",
        name="the moonlit garden",
        mood="quiet and silver",
        supports={"carry", "sip"},
    ),
    "old_pantry": Place(
        id="old_pantry",
        name="the old pantry",
        mood="dusty and small",
        supports={"carry", "serve"},
    ),
}

ACTIONS = {
    "carry": Action(
        id="carry",
        verb="carry the coffee",
        gerund="carrying coffee",
        rush="hurry with the cup",
        mess="spilled",
        danger="slipped",
        tags={"coffee", "spill"},
    ),
    "serve": Action(
        id="serve",
        verb="bring the coffee to the table",
        gerund="bringing coffee to the table",
        rush="dash to the table",
        mess="spilled",
        danger="jolted",
        tags={"coffee", "serve"},
    ),
    "sip": Action(
        id="sip",
        verb="sip the coffee",
        gerund="sipping coffee",
        rush="reach for the cup",
        mess="cold",
        danger="slipped",
        tags={"coffee", "sip"},
    ),
}

OBJECTS = {
    "coffee": ObjectThing(
        id="coffee",
        label="coffee",
        phrase="a small cup of coffee",
        spill_kind="spilled",
        fragile=True,
    ),
    "mug": ObjectThing(
        id="mug",
        label="mug",
        phrase="a blue mug of coffee",
        spill_kind="spilled",
        fragile=True,
    ),
    "pot": ObjectThing(
        id="pot",
        label="coffee pot",
        phrase="a shiny coffee pot",
        spill_kind="spilled",
        fragile=True,
    ),
}

GOPHER_NAMES = ["Pip", "Milo", "Nib", "Tilo", "Bram", "Soot"]
WITNESS_NAMES = ["Queen Rowan", "Old Finch", "Lady Ivy", "Baker Moss"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal logic
# ---------------------------------------------------------------------------
def _spill(world: World) -> list[str]:
    out: list[str] = []
    gopher = next((e for e in world.entities.values() if e.type == "gopher"), None)
    coffee = world.entities.get("coffee")
    if not gopher or not coffee:
        return out
    if gopher.memes.get("clumsy", 0) < 1:
        return out
    if coffee.meters.get("carried", 0) < 1:
        return out
    if "spill" in world.fired:
        return out
    world.fired.add("spill")
    coffee.meters["spilled"] = coffee.meters.get("spilled", 0) + 1
    witness = next((e for e in world.entities.values() if e.kind == "character" and e.type != "gopher"), None)
    if witness:
        witness.memes["upset"] = witness.memes.get("upset", 0) + 1
    gopher.memes["sad"] = gopher.memes.get("sad", 0) + 1
    out.append("The cup slipped, and the coffee spilled across the stone floor.")
    return out


def _cold(world: World) -> list[str]:
    out: list[str] = []
    coffee = world.entities.get("coffee")
    if not coffee or coffee.meters.get("spilled", 0) < 1:
        return out
    if "cold" in world.fired:
        return out
    world.fired.add("cold")
    coffee.meters["gone"] = coffee.meters.get("gone", 0) + 1
    out.append("Soon the sweet smell faded, and there was no coffee left to save.")
    return out


CAUSAL_RULES = [_spill, _cold]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def location_opening(place: Place) -> str:
    return f"Once upon a time, in {place.name}, everything felt {place.mood}."


def introduce_gopher(name: str) -> str:
    return f"There lived a little gopher named {name}, and {name} loved tiny warm sips more than anything."


def witness_line(witness: str) -> str:
    return f"{witness} kept the kitchen tidy and did not like surprises on the floor."


def why_coffee_matters(obj: ObjectThing) -> str:
    return f"The {obj.label} was special, because it was the only bright coffee in the room."


def predict_spill(world: World, gopher: Entity, coffee: Entity) -> bool:
    sim = world.copy()
    sim.get(gopher.id).memes["clumsy"] = 1
    sim.get(coffee.id).meters["carried"] = 1
    propagate(sim, narrate=False)
    return bool(sim.get(coffee.id).meters.get("spilled", 0) >= 1)


def act_one(world: World, gopher: Entity, witness: Entity, coffee: Entity, action: Action) -> None:
    world.say(location_opening(world.place))
    world.say(introduce_gopher(gopher.id))
    world.say(witness_line(witness.id))
    world.say(why_coffee_matters(coffee))
    world.say(f"One morning, {gopher.id} wanted to {action.verb}.")


def act_two(world: World, gopher: Entity, witness: Entity, coffee: Entity, action: Action) -> None:
    world.para()
    world.say(
        f"{gopher.id} {action.rush} through {world.place.name}, and {gopher.pronoun('possessive')} little paws shook."
    )
    if predict_spill(world, gopher, coffee):
        world.say(
            f'"Careful," said {witness.id}, for the cup looked ready to tip.'
        )
    gopher.memes["clumsy"] = 1
    coffee.meters["carried"] = 1
    propagate(world, narrate=True)


def act_three_bad(world: World, gopher: Entity, witness: Entity, coffee: Entity, action: Action) -> None:
    world.para()
    if coffee.meters.get("spilled", 0) >= 1:
        world.say(
            f"{gopher.id} stared at the wet stone and felt very upset."
        )
        world.say(
            f"{witness.id} frowned at the mess, and there was no second cup, no warm fix, and no happy trick."
        )
        world.say(
            f"So {gopher.id} sat by the empty saucer while the moon climbed high, and the castle kitchen stayed quiet and cold."
        )
    else:
        world.say(
            f"Nothing spilled, but the story had already grown too still, and even the coffee tasted sad."
        )


def tell(place: Place, action: Action, obj: ObjectThing, gopher_name: str, witness_name: str) -> World:
    world = World(place)
    gopher = world.add(Entity(id=gopher_name, kind="character", type="gopher"))
    witness = world.add(Entity(id=witness_name, kind="character", type="witness"))
    coffee = world.add(Entity(
        id="coffee",
        kind="thing",
        type="coffee",
        label=obj.label,
        phrase=obj.phrase,
        fragile=obj.fragile,
    ))

    world.facts.update(gopher=gopher, witness=witness, coffee=coffee, action=action, object=obj)

    act_one(world, gopher, witness, coffee, action)
    act_two(world, gopher, witness, coffee, action)
    act_three_bad(world, gopher, witness, coffee, action)
    return world


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_combo(place: Place, action: Action, obj: ObjectThing) -> bool:
    if "coffee" not in action.tags:
        return False
    if "carry" not in place.supports and action.id in {"carry", "serve"}:
        return False
    if obj.label != "coffee" and action.id == "sip":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for aid, action in ACTIONS.items():
            for oid, obj in OBJECTS.items():
                if valid_combo(place, action, obj):
                    combos.append((pid, aid, oid))
    return combos


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale about a gopher named {f["gopher"].id} and a cup of coffee.',
        f'Tell a gentle bad-ending story where {f["gopher"].id} wants to {f["action"].verb} in {world.place.name}.',
        f'Write a fairy tale with coffee, a gopher, and an upset ending in {world.place.name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    gopher, witness, coffee, action = f["gopher"], f["witness"], f["coffee"], f["action"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about a little gopher named {gopher.id} who wanted {coffee.phrase} in {world.place.name}.",
        ),
        QAItem(
            question=f"Why did {witness.id} become upset?",
            answer=f"{witness.id} became upset because {gopher.id} tried to {action.verb} and the coffee spilled on the stone floor.",
        ),
        QAItem(
            question=f"What was the ending like?",
            answer=f"The ending was sad: the coffee was gone, {gopher.id} felt upset, and the kitchen stayed quiet and cold.",
        ),
    ]
    if coffee.meters.get("spilled", 0) >= 1:
        qa.append(QAItem(
            question=f"What happened to the coffee?",
            answer="The cup tipped over, the coffee spilled, and then there was no warm coffee left to save.",
        ))
    return qa


WORLD_KNOWLEDGE = {
    "coffee": [
        QAItem(
            question="What is coffee?",
            answer="Coffee is a warm, dark drink made from roasted beans, and grown-ups often sip it in the morning.",
        )
    ],
    "gopher": [
        QAItem(
            question="What is a gopher?",
            answer="A gopher is a small animal that digs tunnels and lives under the ground.",
        )
    ],
    "upset": [
        QAItem(
            question="What does upset mean?",
            answer="Upset means feeling sad, worried, or bothered when something goes wrong.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [WORLD_KNOWLEDGE["coffee"][0], WORLD_KNOWLEDGE["gopher"][0], WORLD_KNOWLEDGE["upset"][0]]
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
act(A) :- action(A).
obj(O) :- object(O).

can_story(P,A,O) :- place(P), act(A), obj(O), supports(P, carry), coffee_action(A).

spills(A,O) :- coffee_action(A), fragile(O).
upset_after_spill(P,A,O) :- can_story(P,A,O), spills(A,O).
valid_story(P,A,O) :- upset_after_spill(P,A,O).
#show valid_story/3.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for s in sorted(p.supports):
            lines.append(asp.fact("supports", pid, s))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        if "coffee" in a.tags:
            lines.append(asp.fact("coffee_action", aid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.fragile:
            lines.append(asp.fact("fragile", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
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
# Storyworld contract interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale coffee gopher story world with a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name", dest="gopher_name")
    ap.add_argument("--witness")
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
              and (args.action is None or c[1] == args.action)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, obj = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        action=action,
        object=obj,
        gopher_name=args.gopher_name or rng.choice(GOPHER_NAMES),
        witness_name=args.witness or rng.choice(WITNESS_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ACTIONS[params.action], OBJECTS[params.object],
                 params.gopher_name, params.witness_name)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, action, object) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("castle_kitchen", "carry", "coffee", "Pip", "Queen Rowan"),
            StoryParams("moonlit_garden", "sip", "mug", "Milo", "Lady Ivy"),
            StoryParams("old_pantry", "serve", "pot", "Bram", "Old Finch"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if args.all:
            p = sample.params
            header = f"### {p.gopher_name}: {p.action} in {p.place} (object: {p.object})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
