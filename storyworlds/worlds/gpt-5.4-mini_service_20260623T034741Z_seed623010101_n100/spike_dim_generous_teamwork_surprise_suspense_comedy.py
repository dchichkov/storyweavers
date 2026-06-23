#!/usr/bin/env python3
"""
storyworlds/worlds/spike_dim_generous_teamwork_surprise_suspense_comedy.py
==========================================================================
A small comedy storyworld about a tiny team solving a surprise problem in a
spike-dim room using generous teamwork.

Seed tale:
---
In a spike-dim room, two kids tried to build a wobble-prone snack tower for a
surprise party. The room was so low and cramped that every tall box bumped the
ceiling. They were getting nervous because the final cookie jar had to cross a
tiny bridge of chairs without toppling.

One kid grabbed the ribbon, the other held the tray, and their very generous
cat "helped" by batting at the paper stars. With teamwork, they found a silly
way to sneak the tower under the low shelf. The surprise stayed secret, the
suspense became giggles, and everyone ended up sharing the snacks.

World model:
- Physical meters: balance, height, distance, tidiness, snack_level.
- Emotional memes: teamwork, surprise, suspense, joy, worry, pride, generosity.
- The story is driven by the tower's stability, the room's spike-dim ceiling,
  the generosity of sharing, and the comic surprise of a helpful cat.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    helper_for: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"balance": 0.0, "height": 0.0, "distance": 0.0, "tidiness": 0.0, "snack_level": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"teamwork": 0.0, "surprise": 0.0, "suspense": 0.0, "joy": 0.0, "worry": 0.0, "pride": 0.0, "generosity": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str
    spike_dim: bool = True
    ceiling_low: bool = True
    shelf_low: bool = True
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    room: str = "kitchen"
    hero1: str = "Mina"
    hero2: str = "Toby"
    hero1_type: str = "girl"
    hero2_type: str = "boy"
    helper: str = "cat"
    helper_name: str = "Pickles"
    prize: str = "cookie tower"
    surprise: str = "party"
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room):
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(copy.deepcopy(self.room))
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


def _r_spike_dim(world: World) -> list[str]:
    out = []
    room = world.room
    if not room.spike_dim:
        return out
    for e in world.characters():
        if e.meters["height"] < THRESHOLD:
            continue
        sig = ("bump", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        e.meters["balance"] -= 1
        out.append("__bump__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out = []
    a, b = world.get("hero1"), world.get("hero2")
    if a.memes["teamwork"] < THRESHOLD or b.memes["teamwork"] < THRESHOLD:
        return out
    sig = ("team",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["pride"] += 1
    b.memes["pride"] += 1
    out.append("They found a silly way to work together.")
    return out


def _r_generous_share(world: World) -> list[str]:
    out = []
    tower = world.get("tower")
    if tower.meters["snack_level"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in world.characters():
        e.memes["generosity"] += 1
        e.memes["joy"] += 1
    out.append("The snacks got shared at the end.")
    return out


CAUSAL_RULES = [_r_spike_dim, _r_teamwork, _r_generous_share]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class Activity:
    id: str
    verb: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    height: float
    fragile: bool = True
    plural: bool = False


ACTIONS = {
    "build": Activity("build", "build a snack tower", "wobble", {"teamwork", "surprise"}),
    "carry": Activity("carry", "carry the tower", "wobble", {"teamwork", "suspense"}),
    "hide": Activity("hide", "hide the surprise", "secret", {"surprise", "suspense"}),
}

PRIZES = {
    "tower": Prize("tower", "cookie tower", 3.0),
    "jar": Prize("jar", "cookie jar", 2.5),
}

ROOMS = {
    "kitchen": Room("the kitchen", spike_dim=True, ceiling_low=True, shelf_low=True),
    "hall": Room("the hall", spike_dim=True, ceiling_low=False, shelf_low=False),
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Toby", "Eli", "Finn", "Owen", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for act in ACTIONS:
            for prize in PRIZES:
                if room == "kitchen" and act == "hide":
                    combos.append((room, act, prize))
                if room == "kitchen" and act in {"build", "carry"}:
                    combos.append((room, act, prize))
                if room == "hall":
                    combos.append((room, act, prize))
    return combos


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: spike-dim teamwork, surprise, suspense, generosity.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--helper-name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              if (args.room is None or c[0] == args.room)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, action, prize = rng.choice(sorted(combos))
    g1, g2 = rng.choice([("girl", "boy"), ("boy", "girl"), ("girl", "girl"), ("boy", "boy")])
    name1 = args.name1 or choose_name(rng, g1)
    name2 = args.name2 or choose_name(rng, g2 if g2 else "boy")
    helper_name = args.helper_name or "Pickles"
    return StoryParams(room=room, hero1=name1, hero2=name2, hero1_type=g1, hero2_type=g2,
                       helper="cat", helper_name=helper_name, prize=prize, surprise="party")


def _build_world(params: StoryParams) -> World:
    if params.room not in ROOMS or params.prize not in PRIZES or params.room not in ROOMS:
        raise StoryError("Invalid story parameters.")
    world = World(copy.deepcopy(ROOMS[params.room]))
    hero1 = world.add(Entity("hero1", kind="character", type=params.hero1_type, label=params.hero1))
    hero2 = world.add(Entity("hero2", kind="character", type=params.hero2_type, label=params.hero2))
    helper = world.add(Entity("helper", kind="character", type="cat", label=params.helper_name, plural=False))
    tower = world.add(Entity("tower", label=PRIZES[params.prize].label))
    world.facts["action"] = ACTIONS["build"]
    hero1.meters["height"] = PRIZES[params.prize].height
    hero2.meters["height"] = PRIZES[params.prize].height
    tower.meters["snack_level"] = 1.0
    hero1.memes["teamwork"] = 1.0
    hero2.memes["teamwork"] = 1.0
    hero1.memes["surprise"] = 1.0
    hero2.memes["suspense"] = 1.0
    helper.memes["generosity"] = 1.0
    return world


def tell(params: StoryParams) -> World:
    world = _build_world(params)
    h1, h2, helper, tower = world.get("hero1"), world.get("hero2"), world.get("helper"), world.get("tower")

    world.say(f"In {world.room.name}, {h1.label} and {h2.label} tried to {ACTIONS['build'].verb} for a surprise {params.surprise}.")
    world.say(f"The room was {('spike-dim' if world.room.spike_dim else 'wide-open')}, so every tall box bonked the ceiling like a clown shoe.")
    world.para()
    h1.memes["suspense"] += 1
    h2.memes["suspense"] += 1
    world.say(f"{h1.label} held the tray while {h2.label} guarded the ribbon.")
    world.say(f"Then {helper.label} made a very generous leap onto the table and batted at the paper stars.")
    propagate(world, narrate=False)
    world.say(f"That surprise nearly ruined the plan, but it also made everybody laugh.")
    world.para()
    h1.memes["teamwork"] += 1
    h2.memes["teamwork"] += 1
    world.say(f"They worked together to slide the {tower.label} under the low shelf without bumping the ceiling.")
    propagate(world, narrate=False)
    world.say(f"When the secret was ready, they opened the door, and the surprise {params.surprise} became a giggle storm.")
    world.say(f"At the end, they shared the snacks, and even {helper.label} got a crumb-sized prize.")
    world.facts.update(hero1=h1, hero2=h2, helper=helper, tower=tower, room=world.room, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a funny story that uses the words "spike-dim" and "generous" in a scene with {p.hero1} and {p.hero2}.',
        f"Tell a child-friendly comedy about teamwork, surprise, and suspense in a {p.room} with a {p.prize}.",
        f"Write a short story where two kids solve a tricky room problem and a generous helper causes a comic surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    h1, h2, helper, tower = world.get("hero1"), world.get("hero2"), world.get("helper"), world.get("tower")
    return [
        QAItem(
            question=f"Why did {h1.label} and {h2.label} need teamwork in the {p.room}?",
            answer=f"They needed teamwork because the room was spike-dim and the tower was easy to bump. Working together let them move the snacks safely without knocking the ceiling.",
        ),
        QAItem(
            question=f"What surprise made the story funny?",
            answer=f"The helper cat jumped in and batted the paper stars around at the worst possible moment. It turned a suspenseful job into a silly surprise instead of a disaster.",
        ),
        QAItem(
            question=f"How did the children finish the cookie tower plan?",
            answer=f"They slid the {tower.label} under the low shelf and then shared the snacks with everybody. The ending proves they solved the problem together and ended in a happy, generous mood.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does generous mean?",
            answer="Generous means happy to share or give help to other people. A generous person does not keep all the good things for themselves.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other to do one job. The job goes better because everyone does a part.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the nervous wondering about what will happen next. It can feel exciting when the outcome is still hidden.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={ {k:v for k,v in e.meters.items() if v} } memes={ {k:v for k,v in e.memes.items() if v} }")
    return "\n".join(out)


ASP_RULES = r"""
ok(Room,Action,Prize) :- room(Room), action(Action), prize(Prize).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for r in ROOMS:
        lines.append(asp.fact("room", r))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show ok/3."))
    return sorted(set(asp.atoms(model, "ok")))


CURATED = [
    StoryParams(room="kitchen", hero1="Mina", hero2="Toby", hero1_type="girl", hero2_type="boy", helper="cat", helper_name="Pickles", prize="tower", surprise="party"),
    StoryParams(room="hall", hero1="Lia", hero2="Owen", hero1_type="girl", hero2_type="boy", helper="cat", helper_name="Nibbles", prize="jar", surprise="party"),
]


def valid_story(params: StoryParams) -> bool:
    return params.room in ROOMS and params.prize in PRIZES


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("Invalid params.")
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


def asp_verify() -> int:
    try:
        import asp
        py = set((r, a, p) for r, a, p in valid_combos())
        cl = set(asp_valid_combos())
        if py != cl:
            print("MISMATCH in ASP parity")
            print("python-only:", sorted(py - cl))
            print("asp-only:", sorted(cl - py))
            return 1
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("Smoke test failed: empty story")
            return 1
        print("OK: ASP parity and smoke test passed.")
        return 0
    except Exception as e:
        print(f"VERIFY FAILED: {e}")
        return 1


def build_sample_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
