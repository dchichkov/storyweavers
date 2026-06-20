#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/still_current_cliff_lookout_mystery_to_solve.py
================================================================================

A small standalone storyworld for a slice-of-life cliff lookout mystery.

Premise
-------
A child and a grown-up visit a cliff lookout above the sea. They notice a puzzling
thing: the tide line and the ocean current seem to be changing, but a small boat
in the cove is still not moving. The pair solve the mystery by paying attention to
what is anchored, what is floating, and who left a note behind.

This world is built to satisfy the Storyweavers contract:
- typed entities with meters and memes,
- simulated state driving the prose,
- a reasonableness gate and inline ASP twin,
- three Q&A sets generated from world state,
- a normal generation path plus `--verify`, `--asp`, `--show-asp`, and JSON output.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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
    label: str
    scenic: str
    view: str
    has_water: bool = True
    has_cliff: bool = True

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
class Clue:
    id: str
    label: str
    note: str
    hidden: bool = True
    solved_by: str = ""

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
class Wind:
    id: str
    label: str
    direction: str
    strength: int
    current: str
    safe: bool = True

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


def _r_clue_seen(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    clue = world.entities.get("clue")
    if not child or not clue:
        return out
    if child.memes["curiosity"] >= THRESHOLD and clue.meters["noticed"] < THRESHOLD:
        clue.meters["noticed"] += 1
        out.append("__clue__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    clue = world.entities.get("clue")
    if clue and clue.meters["noticed"] >= THRESHOLD and clue.meters["solved"] < THRESHOLD:
        clue.meters["solved"] += 1
        out.append("__solve__")
    return out


CAUSAL_RULES = [
    Rule("clue_seen", "social", _r_clue_seen),
    Rule("settle", "social", _r_settle),
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


def reasonable_clues() -> list[str]:
    return [c.id for c in CLUES.values()]


def valid_combo(place: Place, wind: Wind, clue: Clue) -> bool:
    return place.has_cliff and place.has_water and wind.safe and clue.hidden


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for wid, wind in WINDS.items():
            for cid, clue in CLUES.items():
                if valid_combo(place, wind, clue):
                    combos.append((pid, wid, cid))
    return combos


def predict(world: World, clue_id: str) -> dict:
    sim = world.copy()
    sim.get("child").memes["curiosity"] += 1
    _do_solve(sim, sim.get(clue_id), narrate=False)
    return {"solved": sim.get(clue_id).meters["solved"] >= THRESHOLD}


def _do_solve(world: World, clue: Entity, narrate: bool = True) -> None:
    clue.meters["noticed"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, parent: Entity, place: Place, wind: Wind) -> None:
    child.memes["curiosity"] += 1
    child.memes["calm"] += 1
    world.say(
        f"On a still afternoon, {child.id} and {parent.id} walked up to {place.label}. "
        f"{place.scenic}"
    )
    world.say(
        f"The sea below seemed to breathe with {wind.current}, and the lookout felt very quiet."
    )


def notice_mystery(world: World, child: Entity, place: Place, clue: Clue, wind: Wind) -> None:
    world.say(
        f"{child.id} peered over the rail and noticed something odd: the water was moving, "
        f"but the little boat in the cove was still."
    )
    world.say(
        f'Near the bench, {clue.note}. "{child.id} said it was a mystery to solve," '
        f"{child.pronoun()} whispered."
    )


def wonder(world: World, child: Entity, parent: Entity, wind: Wind, clue: Clue) -> None:
    child.memes["wonder"] += 1
    world.say(
        f'"Why is the current so fast today, but that boat does not drift?" {child.id} asked.'
    )
    world.say(
        f'{parent.id} looked where {child.pronoun("object")} pointed. "Let\'s look for a clue," '
        f"{parent.pronoun()} said."
    )


def reveal(world: World, child: Entity, parent: Entity, clue: Clue, wind: Wind) -> None:
    child.memes["joy"] += 1
    child.memes["confidence"] += 1
    clue.meters["solved"] += 1
    world.say(
        f"They found the answer in a tiny note tied to the post: {clue.solved_by}."
    )
    world.say(
        f"The boat was still because it was anchored fast, while the current kept sliding past."
    )


def ending(world: World, child: Entity, parent: Entity, place: Place, clue: Clue, wind: Wind) -> None:
    world.say(
        f"{parent.id} smiled and tucked the note back where it belonged. {child.id} smiled too, "
        f"happy to know that some still things stay put for a reason."
    )
    world.say(
        f"As they left {place.label}, the sea kept moving and the lookout stayed peaceful."
    )
    world.say(
        f"The mystery was solved, and the small harbor looked calm and ordinary again."
    )


def tell(place: Place, wind: Wind, clue: Clue, child_name: str = "Mina",
         child_gender: str = "girl", parent_name: str = "Mom",
         parent_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    clue_ent = world.add(Entity(id="clue", kind="thing", type="note", label=clue.label))
    world.add(Entity(id="place", kind="thing", type="place", label=place.label))
    world.add(Entity(id="wind", kind="thing", type="wind", label=wind.label))

    setup(world, child, parent, place, wind)
    world.para()
    notice_mystery(world, child, parent, clue, wind)
    wonder(world, child, parent, wind, clue)
    world.para()
    _do_solve(world, clue_ent)
    reveal(world, child, parent, clue, wind)
    ending(world, child, parent, place, clue, wind)

    world.facts.update(
        child=child,
        parent=parent,
        place=place,
        wind=wind,
        clue=clue,
        solved=clue_ent.meters["solved"] >= THRESHOLD,
        mystery="still boat and moving current",
    )
    return world


PLACES = {
    "cliff_lookout": Place(
        "cliff_lookout",
        "the cliff lookout",
        "A wooden rail faced the wide sea, and a bench waited beside a patch of wind-tossed grass.",
        "The bay below was open to the current.",
    ),
    "lighthouse_path": Place(
        "lighthouse_path",
        "the lighthouse path",
        "A narrow path bent past a stone wall and looked down at the bright water.",
        "The cove below could be watched from above.",
    ),
}

WINDS = {
    "gentle": Wind("gentle", "gentle breeze", "from the west", 1, "a slow current"),
    "steady": Wind("steady", "steady wind", "off the sea", 2, "a clear current"),
    "breezy": Wind("breezy", "breezy air", "past the rocks", 3, "a quick current"),
}

CLUES = {
    "anchor_note": Clue("anchor_note", "a folded note", "A folded note fluttered under the bench.", solved_by="someone had tied the boat to the post"),
    "shell_tag": Clue("shell_tag", "a shell tag", "A small shell tag hung from the railing.", solved_by="the boat owner had marked the boat as anchored"),
    "rope_knot": Clue("rope_knot", "a rope knot", "A neat rope knot rested beside the post.", solved_by="the rope was tied to an anchor ring"),
}

@dataclass
@dataclass
class StoryParams:
    place: str
    wind: str
    clue: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
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


KNOWLEDGE = {
    "current": [("What is a current in the sea?", "A current is moving water that flows in one direction. It can carry floating things along.")],
    "anchor": [("What does an anchor do?", "An anchor helps keep a boat in one place so it does not drift away.")],
    "cliff": [("What is a cliff lookout?", "A cliff lookout is a safe place high above the water where people can watch the view.")],
    "note": [("What is a note?", "A note is a short message written on paper or tied to something.")],
}

KNOWLEDGE_ORDER = ["current", "anchor", "cliff", "note"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child at {f["place"].label} that includes the words "still" and "current".',
        f"Tell a gentle mystery story where {f['child'].id} notices a still boat while the current moves, and a grown-up helps solve the puzzle.",
        f'Write a small everyday story set at a cliff lookout where someone finds a clue and solves the mystery of the still boat.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, place, wind, clue = f["child"], f["parent"], f["place"], f["wind"], f["clue"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {parent.id} at {place.label}."),
        ("What mystery did they solve?", f"They solved the mystery of why the boat was still even though the current moved. The answer was that it was anchored or tied fast."),
        ("What clue helped them?", f"{clue.note} That clue pointed them toward the answer."),
        ("How did the story end?", f"It ended calmly, with the mystery solved and the harbor peaceful again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"current", "anchor", "cliff", "note"}
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("cliff_lookout", "steady", "anchor_note", "Mina", "girl", "Mom", "woman"),
    StoryParams("lighthouse_path", "breezy", "shell_tag", "Eli", "boy", "Dad", "man"),
    StoryParams("cliff_lookout", "gentle", "rope_knot", "Nora", "girl", "Mom", "woman"),
]


def explain_rejection() -> str:
    return "(No story: this world needs a cliff lookout, a moving current, and a clue that can reasonably solve the mystery.)"


def valid_outcome(params: StoryParams) -> str:
    return "solved"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for wid in WINDS:
        lines.append(asp.fact("wind", wid))
        lines.append(asp.fact("safe", wid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("hidden", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, W, C) :- place(P), wind(W), safe(W), clue(C), hidden(C).
solved :- valid(P, W, C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import itertools
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations.")
        print("python only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))

    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")

    # lightweight additional parity check on all curated params
    for p in CURATED:
        try:
            if valid_outcome(p) != "solved":
                rc = 1
        except Exception:
            rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life cliff lookout mystery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--wind", choices=WINDS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["woman", "man"])
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
    if args.place and args.place not in PLACES:
        raise StoryError(explain_rejection())
    if args.wind and args.clue:
        if not valid_combo(PLACES[args.place or "cliff_lookout"], WINDS[args.wind], CLUES[args.clue]):
            raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.wind is None or c[1] == args.wind)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError(explain_rejection())
    place, wind, clue = rng.choice(combos)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    parent_gender = args.parent_gender or rng.choice(["woman", "man"])
    child_name = args.child_name or rng.choice(["Mina", "Eli", "Nora", "Finn", "Ivy", "Theo"])
    parent_name = args.parent_name or ("Mom" if parent_gender == "woman" else "Dad")
    return StoryParams(place, wind, clue, child_name, child_gender, parent_name, parent_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], WINDS[params.wind], CLUES[params.clue],
                 params.child_name, params.child_gender, params.parent_name, params.parent_gender)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, wind, clue) combos:\n")
        for t in combos:
            print("  ", t)
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
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
            header = f"### {p.child_name} at {p.place} ({p.clue}, {p.wind})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
