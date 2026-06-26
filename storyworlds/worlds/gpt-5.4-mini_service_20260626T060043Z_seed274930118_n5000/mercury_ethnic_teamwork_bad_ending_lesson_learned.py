#!/usr/bin/env python3
"""
storyworlds/worlds/mercury_ethnic_teamwork_bad_ending_lesson_learned.py
=======================================================================

A small ghost-story world with teamwork, a bad ending, and a learned lesson.

Seed tale:
---
During an ethnic heritage night at the old river hall, a child named Mina
noticed a silver gleam under the stairs. It was mercury from a cracked old
thermometer, and beside it came a whispery ghost that nobody else could see at
first. Mina called two friends, and together they tried to clean up the spill
and calm the ghost down.

They worked as a team: one friend fetched gloves, one held a lantern, and Mina
spoke softly to the ghost. But the ghost only grew colder and the silver
mercury rolled into a crack beneath the floorboards. The hall lights blinked
out. The friends escaped, shaken, and learned that some old places need more
than brave hands; they need permission, patience, and adults who know the
story.

World model summary:
---
- Physical meters: mercury, cold, dark, broken, opened, cleaned, hidden
- Emotional memes: fear, courage, trust, teamwork, worry, lesson, regret
- Teamwork can reduce risk if the group coordinates correctly.
- A bad ending happens when the ghost remains hidden and the spill is not fully
  contained.
- The lesson learned is narrated when the children realize they should not
  touch strange old things alone.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    roles: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("mercury", "cold", "dark", "broken", "opened", "cleaned", "hidden"):
            self.meters.setdefault(k, 0.0)
        for k in ("fear", "courage", "trust", "teamwork", "worry", "lesson", "regret"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    vibe: str
    has_stairs: bool
    is_old: bool = True


@dataclass
class StoryParams:
    place: str
    ghost_kind: str
    group_size: int
    name: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _m(world: World, eid: str, key: str, amt: float = 1.0) -> None:
    world.get(eid).meters[key] += amt


def _e(world: World, eid: str, key: str, amt: float = 1.0) -> None:
    world.get(eid).memes[key] += amt


def _rule_spill_spreads(world: World) -> list[str]:
    out = []
    hall = world.get("hall")
    if hall.meters["opened"] >= THRESHOLD and hall.meters["mercury"] >= THRESHOLD:
        sig = ("spill_spreads",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hall.meters["hidden"] += 1
        hall.meters["cold"] += 1
        out.append("The silver spill slid deeper into the cracks, and the hall felt colder.")
    return out


def _rule_ghost_grows(world: World) -> list[str]:
    out = []
    ghost = world.get("ghost")
    hall = world.get("hall")
    if hall.meters["hidden"] >= THRESHOLD and ghost.meters["opened"] >= THRESHOLD:
        sig = ("ghost_grows",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        ghost.meters["dark"] += 1
        ghost.memes["worry"] += 1
        out.append("The ghost did not fade. It only turned quieter and darker.")
    return out


def _rule_teamwork_help(world: World) -> list[str]:
    out = []
    kids = [c for c in world.characters() if "child" in c.roles]
    if len(kids) < 2:
        return out
    if sum(k.memes["teamwork"] for k in kids) >= 2 and world.get("hall").meters["opened"] >= THRESHOLD:
        sig = ("teamwork_help",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        for kid in kids:
            kid.memes["courage"] += 1
        out.append("They worked together, but the old place still felt bigger than their small hands.")
    return out


CAUSAL_RULES = [_rule_spill_spreads, _rule_ghost_grows, _rule_teamwork_help]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hall = world.add(Entity(
        id="hall", type="place", label=place.name, kind="thing"
    ))
    ghost = world.add(Entity(
        id="ghost", type=params.ghost_kind, kind="thing",
        label="ghost", phrase=f"a whispery {params.ghost_kind} ghost"
    ))

    children = []
    names = NAMES[:params.group_size]
    for i, name in enumerate(names):
        kid = world.add(Entity(
            id=name,
            kind="character",
            type="child",
            label=name,
            roles={"child", "team"},
        ))
        kid.memes["teamwork"] = 1.0 if i > 0 else 0.0
        children.append(kid)

    world.facts["children"] = children
    world.facts["ghost"] = ghost
    world.facts["hall"] = hall
    world.facts["place"] = place
    world.facts["params"] = params

    # Act 1: setup.
    world.say(
        f"On ethnic heritage night, {children[0].id} walked into {place.name}, "
        f"where old songs floated under the ceiling."
    )
    world.say(
        f"{children[0].id} noticed a silver shine near the stairs, like a coin that had melted."
    )
    _m(world, "hall", "opened", 1)
    _m(world, "hall", "mercury", 1)
    _e(world, children[0].id, "worry", 1)

    # Act 2: teamwork and fear.
    world.para()
    if len(children) > 1:
        world.say(
            f"{children[0].id} called {children[1].id}, and soon the children formed a little team."
        )
    if len(children) > 2:
        world.say(
            f"{children[2].id} brought a lantern, {children[1].id} held open a window, and {children[0].id} reached for a broom."
        )
    else:
        world.say(
            f"One child carried the lantern while the other kept the door open."
        )
    for kid in children:
        kid.memes["teamwork"] += 1
        kid.memes["fear"] += 1
    ghost.meters["opened"] += 1
    ghost.memes["worry"] += 1
    world.say(
        f"Then a thin ghost rose by the stair rail, pale as chalk in moonlight."
    )
    world.say(
        f"The children tried to help each other, and their teamwork made them a little braver."
    )
    propagate(world, narrate=True)

    # Act 3: bad ending and lesson learned.
    world.para()
    world.say(
        f"But the mercury slipped deeper under the floorboards, and the ghost grew colder instead of kinder."
    )
    _m(world, "hall", "hidden", 1)
    _m(world, "hall", "cold", 1)
    _e(world, "ghost", "dark", 1)
    for kid in children:
        kid.memes["regret"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"The lights blinked out, and the children backed away, their hearts thumping hard."
    )
    world.say(
        f"They learned a hard lesson: strange old things are not for children to fix alone."
    )
    world.say(
        f"By the time they reached the front door, the ghost was still inside the hall, and the silver mercury was still hiding in the cracks."
    )

    world.facts["bad_ending"] = True
    world.facts["lesson_learned"] = True
    world.facts["teamwork"] = True
    return world


PLACES = {
    "old river hall": Place(
        name="the old river hall",
        vibe="echoing",
        has_stairs=True,
    ),
    "ethnic museum": Place(
        name="the ethnic museum",
        vibe="quiet",
        has_stairs=True,
    ),
    "community center": Place(
        name="the community center",
        vibe="bright",
        has_stairs=False,
    ),
}

GHOST_TYPES = {
    "mirror": "mirror",
    "lantern": "lantern",
    "bell": "bell",
}

NAMES = ["Mina", "Ira", "Noor", "Tari", "Lea", "Sami"]

CURATED = [
    StoryParams(place="old river hall", ghost_kind="mirror", group_size=3, name="Mina"),
    StoryParams(place="ethnic museum", ghost_kind="lantern", group_size=2, name="Ira"),
    StoryParams(place="community center", ghost_kind="bell", group_size=3, name="Noor"),
]


def valid_combos() -> list[tuple[str, str, int]]:
    out = []
    for place in PLACES:
        for ghost in GHOST_TYPES:
            for n in (2, 3):
                if place != "community center" or n >= 2:
                    out.append((place, ghost, n))
    return out


def explain_rejection(place: str, ghost_kind: str, group_size: int) -> str:
    if place == "community center" and group_size < 2:
        return "(No story: a ghost story needs at least two children to show teamwork.)"
    return "(No story: this combination does not make a strong ghost-story turn.)"


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    place = world.facts["place"].name
    return [
        f"Write a spooky child-friendly ghost story about {p.name} and friends at {place}.",
        "Tell a short story where teamwork helps children face a strange ghost, but the ending stays bad and leaves a lesson learned.",
        "Write a ghost story that includes mercury and an old place with a whispery spirit.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    place = world.facts["place"].name
    kids = world.facts["children"]
    first = kids[0].id
    qa = [
        QAItem(
            question=f"Where did {first} see the silver spill?",
            answer=f"{first} saw the silver spill at {place}, near the stairs and the old floorboards.",
        ),
        QAItem(
            question="What did the children try to do together?",
            answer="They tried to help as a team: one watched with a lantern, one stayed near the door, and one tried to clean the spill.",
        ),
        QAItem(
            question="Why was the ending bad?",
            answer="The ending was bad because the mercury slipped deeper into the cracks, the ghost stayed inside, and the children had to leave afraid.",
        ),
        QAItem(
            question="What lesson did they learn?",
            answer="They learned that strange old things should not be handled alone, and that adults should help with scary surprises.",
        ),
    ]
    if len(kids) >= 2:
        qa.append(
            QAItem(
                question=f"How did {kids[0].id} and {kids[1].id} show teamwork?",
                answer=f"They worked together by sharing jobs and staying close, which made their team a little braver even though the problem did not get fixed.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mercury?",
            answer="Mercury is a shiny metal that can look like silver beads, but it is dangerous and should only be handled by grown-ups with care.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and share jobs so they can do something together.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a spooky tale about something mysterious, like a spirit, a whisper, or a strange noise in an old place.",
        ),
        QAItem(
            question="What does a lesson learned mean?",
            answer="A lesson learned is a useful idea someone remembers after making a mistake or seeing what went wrong.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        out.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
teamwork_help(C) :- child(C), teamwork(C), courage(C).
bad_ending :- mercury_spill, ghost_present, hidden_spill.
lesson_learned(C) :- child(C), regret(C), teamwork(C).
valid_story(P,G,N) :- place(P), ghost(G), children(N), N >= 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for g in GHOST_TYPES:
        lines.append(asp.fact("ghost", g))
    for n in (2, 3):
        lines.append(asp.fact("children", n))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with teamwork and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ghost-kind", choices=GHOST_TYPES)
    ap.add_argument("--group-size", type=int, choices=[2, 3])
    ap.add_argument("--name")
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
    if args.ghost_kind:
        combos = [c for c in combos if c[1] == args.ghost_kind]
    if args.group_size:
        combos = [c for c in combos if c[2] == args.group_size]
    if not combos:
        raise StoryError(explain_rejection(args.place or "", args.ghost_kind or "", args.group_size or 0))
    place, ghost_kind, group_size = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, ghost_kind=ghost_kind, group_size=group_size, name=name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(f"{len(combos)} compatible stories:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
