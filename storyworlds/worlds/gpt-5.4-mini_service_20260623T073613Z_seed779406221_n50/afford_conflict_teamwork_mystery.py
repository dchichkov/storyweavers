#!/usr/bin/env python3
"""
storyworlds/worlds/afford_conflict_teamwork_mystery.py
======================================================

A small storyworld about a missing thing, a tense clue hunt, and a teamwork
resolution. The setting is mystery-like: the children notice an odd absence,
argue about what the clues mean, then work together to discover what the room
affords and where the missing object ended up.

The world uses typed entities with physical meters and emotional memes, a tiny
forward-causal model, a Python reasonableness gate, and an inline ASP twin for
parity checks.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = ""
    hidden_in: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    afford: set[str] = field(default_factory=set)
    hiding_spots: list[str] = field(default_factory=list)
    clue_words: list[str] = field(default_factory=list)
    mood: str = ""


@dataclass
class MissingThing:
    id: str
    label: str
    phrase: str
    find_word: str
    size: str
    can_hide_in: set[str] = field(default_factory=set)
    needed_for: set[str] = field(default_factory=set)


@dataclass
class TeamTool:
    id: str
    label: str
    phrase: str
    use_word: str
    reveals: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


@dataclass
class StoryParams:
    place: str
    missing: str
    tool: str
    name_a: str
    name_b: str
    gender_a: str
    gender_b: str
    role_a: str
    role_b: str
    seed: Optional[int] = None


PLACES = {
    "library": Place(
        id="library",
        label="the little library",
        afford={"search", "whisper", "sort"},
        hiding_spots=["the reading nook", "the tall shelves", "the card table"],
        clue_words=["quiet", "paper", "dust"],
        mood="quiet",
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="the greenhouse",
        afford={"search", "listen", "peek"},
        hiding_spots=["the potting bench", "the watering shelf", "the fern corner"],
        clue_words=["leaf", "drop", "glass"],
        mood="glassy",
    ),
    "workshop": Place(
        id="workshop",
        label="the workshop",
        afford={"search", "lift", "tap"},
        hiding_spots=["the tool shelf", "the workbench", "the wooden crate"],
        clue_words=["wood", "dust", "tin"],
        mood="busy",
    ),
}

MISSING = {
    "stamp": MissingThing(
        id="stamp",
        label="rubber stamp",
        phrase="a red rubber stamp",
        find_word="stamp",
        size="small",
        can_hide_in={"reading nook", "card table", "tool shelf"},
        needed_for={"marking notes"},
    ),
    "key": MissingThing(
        id="key",
        label="brass key",
        phrase="a tiny brass key",
        find_word="key",
        size="small",
        can_hide_in={"card table", "fern corner", "wooden crate"},
        needed_for={"opening the little box"},
    ),
    "note": MissingThing(
        id="note",
        label="note",
        phrase="a folded note",
        find_word="note",
        size="small",
        can_hide_in={"reading nook", "workbench", "watering shelf"},
        needed_for={"solving the puzzle"},
    ),
}

TOOLS = {
    "lamp": TeamTool(
        id="lamp",
        label="desk lamp",
        phrase="a desk lamp",
        use_word="shine",
        reveals={"quiet", "paper", "dust"},
    ),
    "magnifier": TeamTool(
        id="magnifier",
        label="magnifier",
        phrase="a magnifier",
        use_word="inspect",
        reveals={"tiny marks", "scratches", "glue"},
    ),
    "stepstool": TeamTool(
        id="stepstool",
        label="step stool",
        phrase="a step stool",
        use_word="reach",
        reveals={"top shelf", "high ledge", "box lid"},
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Theo", "Zoe", "Max"]
ROLES = ["curious", "careful", "bold", "patient", "clever", "watchful"]


class State:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.clue_found = False
        self.teamwork = False
        self.misread = False

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "State":
        clone = State(self.place)
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.clue_found = self.clue_found
        clone.teamwork = self.teamwork
        clone.misread = self.misread
        clone.paragraphs = [[]]
        return clone


def clue_state(place: Place, missing: MissingThing) -> bool:
    return any(h in missing.can_hide_in for h in place.hiding_spots)


def select_tool(place: Place, missing: MissingThing) -> Optional[TeamTool]:
    for tool in TOOLS.values():
        if place.afford & tool.reveals:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for missing_id, missing in MISSING.items():
            if not clue_state(place, missing):
                continue
            for tool_id in TOOLS:
                if select_tool(place, missing) is not None:
                    out.append((place_id, missing_id, tool_id))
    return out


def _rule_conflict(state: State) -> list[str]:
    a = state.get("A")
    b = state.get("B")
    if a.memes.get("certainty", 0) >= THRESHOLD and b.memes.get("certainty", 0) >= THRESHOLD:
        sig = ("conflict",)
        if sig in state.fired:
            return []
        state.fired.add(sig)
        a.memes["conflict"] = a.memes.get("conflict", 0) + 1
        b.memes["conflict"] = b.memes.get("conflict", 0) + 1
        return ["__conflict__"]
    return []


def _rule_teamwork(state: State) -> list[str]:
    a = state.get("A")
    b = state.get("B")
    if state.clue_found and not state.teamwork and a.memes.get("conflict", 0) >= THRESHOLD:
        state.teamwork = True
        a.memes["conflict"] = 0
        b.memes["conflict"] = 0
        a.memes["trust"] = a.memes.get("trust", 0) + 1
        b.memes["trust"] = b.memes.get("trust", 0) + 1
        return ["__teamwork__"]
    return []


CAUSAL_RULES = [
    _rule_conflict,
    _rule_teamwork,
]


def propagate(state: State, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule(state)
            if got:
                changed = True
                out.extend([g for g in got if not g.startswith("__")])
    if narrate:
        for s in out:
            state.say(s)
    return out


def tell(place: Place, missing: MissingThing, tool: TeamTool,
         name_a: str = "Mia", gender_a: str = "girl",
         name_b: str = "Leo", gender_b: str = "boy",
         role_a: str = "curious", role_b: str = "careful") -> State:
    state = State(place)
    a = state.add(Entity(id="A", kind="character", type=gender_a, label=name_a, traits=[role_a]))
    b = state.add(Entity(id="B", kind="character", type=gender_b, label=name_b, traits=[role_b]))
    item = state.add(Entity(id="missing", type=missing.id, label=missing.label, owner=name_a, hidden_in=""))
    state.facts.update(place=place, missing=missing, tool=tool, a=a, b=b, item=item)

    a.memes["certainty"] = 1
    b.memes["certainty"] = 1
    a.memes["curiosity"] = 1
    b.memes["curiosity"] = 1

    state.say(f"{name_a} and {name_b} were in {place.label}, where the rooms seemed to afford quiet clues.")
    state.say(f"They noticed that {missing.phrase} was gone.")
    state.para()
    state.say(f"{name_a} thought the answer was near {place.hiding_spots[0]}, but {name_b} thought it was somewhere else.")
    state.say(f"Their voices got sharp, because each one was sure the other had missed an important clue.")
    propagate(state, narrate=False)
    state.para()
    state.say(f"Then they picked a plan: {tool.phrase} for the search.")
    state.say(f"{name_a} used the {tool.label} while {name_b} checked the hiding spots one by one.")
    state.clue_found = True
    propagate(state, narrate=False)
    state.say(f"At last, {name_b} spotted the missing {missing.label} tucked in {missing.can_hide_in and sorted(missing.can_hide_in)[0] or 'a small place'}.")
    state.say(f"{name_a} smiled, and together they put everything back where it belonged.")
    state.say(f"The little room felt calm again, as if it had been waiting to afford exactly that kind of teamwork.")
    state.facts.update(conflict=state.get("A").memes.get("conflict", 0) >= THRESHOLD, teamwork=state.teamwork)
    return state


def generation_prompts(world: State) -> list[str]:
    f = world.facts
    p = f["place"].label
    m = f["missing"].label
    t = f["tool"].label
    a = f["a"].label
    b = f["b"].label
    return [
        f'Write a short mystery for a 3-to-5-year-old set in {p} about a missing {m} and two children who disagree before teaming up.',
        f"Tell a gentle conflict-and-teamwork story where {a} and {b} search {p} for a missing {m} using {t}.",
        f'Write a child-friendly mystery that uses the word "afford" and ends with two children working together to solve the clue.',
    ]


def story_qa(world: State) -> list[QAItem]:
    f = world.facts
    p = f["place"]
    m = f["missing"]
    t = f["tool"]
    a = f["a"]
    b = f["b"]
    return [
        QAItem(
            question=f"What kind of story is this with {a.label} and {b.label} in {p.label}?",
            answer=f"It is a small mystery. {a.label} and {b.label} try to find the missing {m.label}, and their disagreement turns into teamwork.",
        ),
        QAItem(
            question=f"Why did {a.label} and {b.label} argue at first?",
            answer="They each thought a different clue was the best one to follow. That made the search tense until they stopped and listened to each other.",
        ),
        QAItem(
            question=f"What helped {a.label} and {b.label} solve the mystery?",
            answer=f"They used {t.phrase} and shared the search. Once they worked together, the clue became easy to spot.",
        ),
        QAItem(
            question=f"Where was the missing {m.label} found?",
            answer=f"It was found in a small hiding spot in {p.label}. The clue matched a place the room could afford for hiding, so the answer made sense.",
        ),
    ]


def world_knowledge_qa(world: State) -> list[QAItem]:
    out: list[QAItem] = []
    out.append(QAItem(
        question="What does afford mean?",
        answer="In this storyworld, afford means what a place or tool makes possible. A quiet room can afford whispering, and a magnifier can afford closer looking.",
    ))
    out.append(QAItem(
        question="What is a mystery?",
        answer="A mystery is a story with a missing answer or a hidden thing. The characters use clues to figure it out.",
    ))
    out.append(QAItem(
        question="What is teamwork?",
        answer="Teamwork is when people help each other and combine their ideas. The problem gets easier when everyone works together.",
    ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: State) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: {e.label} meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    lines.append(f"teamwork={world.teamwork} clue_found={world.clue_found}")
    return "\n".join(lines)


ASP_RULES = r"""
conflict(A,B) :- certainty(A,1), certainty(B,1), A != B.
teamwork :- clue_found, conflict(A,B).
valid(P,M,T) :- place(P), missing(M), tool(T), clue_place(P,M), tool_helpful(P,T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for h in p.hiding_spots:
            lines.append(asp.fact("hide_spot", pid, h))
        for a in p.afford:
            lines.append(asp.fact("afford", pid, a))
    for mid, m in MISSING.items():
        lines.append(asp.fact("missing", mid))
        for spot in m.can_hide_in:
            lines.append(asp.fact("clue_place", "library" if spot in {"reading nook", "card table"} else "workshop" if spot in {"tool shelf", "wooden crate"} else "greenhouse", mid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for r in t.reveals:
            lines.append(asp.fact("tool_helpful", "library", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    return 0 if set(asp_valid_combos()) == set(valid_combos()) else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Storyworld: conflict, teamwork, mystery, and afford.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
    ap.add_argument("--role-a", choices=ROLES)
    ap.add_argument("--role-b", choices=ROLES)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.missing:
        combos = [c for c in combos if c[1] == args.missing]
    if args.tool:
        combos = [c for c in combos if c[2] == args.tool]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, missing, tool = rng.choice(sorted(combos))
    pa = args.name_a or rng.choice(NAMES)
    pb = args.name_b or rng.choice([n for n in NAMES if n != pa])
    ga = args.gender_a or rng.choice(["girl", "boy"])
    gb = args.gender_b or rng.choice(["girl", "boy"])
    ra = args.role_a or rng.choice(ROLES)
    rb = args.role_b or rng.choice([r for r in ROLES if r != ra])
    return StoryParams(place=place, missing=missing, tool=tool, name_a=pa, name_b=pb, gender_a=ga, gender_b=gb, role_a=ra, role_b=rb)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MISSING[params.missing], TOOLS[params.tool],
                 params.name_a, params.gender_a, params.name_b, params.gender_b,
                 params.role_a, params.role_b)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("library", "stamp", "magnifier", "Mia", "Leo", "girl", "boy", "curious", "careful"),
    StoryParams("greenhouse", "note", "stepstool", "Nora", "Ben", "girl", "boy", "watchful", "patient"),
    StoryParams("workshop", "key", "lamp", "Ava", "Theo", "girl", "boy", "bold", "clever"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place} / {p.missing} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
