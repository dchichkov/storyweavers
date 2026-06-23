#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T035527Z_seed1855084837_n10/occupy_tennis_friendship_happy_ending_fable.py
=============================================================================================================

A small fable-style storyworld about friends, a tennis court, and the choice to
occupy space kindly instead of selfishly. The world keeps typed entities with
meters and memes, simulates a simple turn, and ends with a happy ending image
that proves what changed.

Seed tale:
---
At the edge of a sunny village, two friends found an empty tennis court.
A boastful peacock wanted to occupy the whole court and keep the shiny balls
for himself, but a patient turtle reminded him that friendship grows when space
is shared.
The peacock tried to block the court, yet the turtle rolled a spare ball back,
and soon the two were playing together, laughing under the fence.
In the end, the peacock moved aside, the court stayed open, and the friends
promised to share it every afternoon.

The world model tracks:
- physical meters: court_occupied, blocked, balls, play, openness
- emotional memes: pride, patience, warmth, friendship, joy, peace

The moral:
- A big space becomes a happy place when friends share it.
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
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str | None = None
    caretaker: str | None = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id


@dataclass
class StoryParams:
    setting: str
    court: str
    intruder: str
    friend: str
    ball: str
    seed: int | None = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, str]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.history = copy.deepcopy(self.history)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "village_green": {"place": "the village green", "time": "afternoon"},
    "orchard_clearing": {"place": "the orchard clearing", "time": "morning"},
    "sunlit_court": {"place": "the sunlit court", "time": "afternoon"},
}

COURTS = {
    "tennis_court": {
        "label": "tennis court",
        "phrase": "an empty tennis court",
        "surface": "smooth white lines",
        "open_image": "The net stood straight, the chalk lines shone, and the court was open for both friends.",
    }
}

FRIENDS = {
    "peacock": {
        "type": "bird",
        "label": "peacock",
        "phrase": "a proud peacock",
        "trait": "showy",
        "color": "blue-green",
    },
    "turtle": {
        "type": "turtle",
        "label": "turtle",
        "phrase": "a patient turtle",
        "trait": "calm",
        "color": "olive",
    },
}

BALLS = {
    "green_ball": {
        "label": "tennis ball",
        "phrase": "a bright tennis ball",
        "color": "yellow-green",
    }
}

MORAL = "Friendship grows best when everyone gets a turn."


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for court in COURTS:
            for intruder in FRIENDS:
                for friend in FRIENDS:
                    if friend == intruder:
                        continue
                    for ball in BALLS:
                        combos.append((setting, court, intruder, friend, ball))
    return combos


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this fable needs two different friends and a tennis court.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about friends, tennis, and sharing space kindly.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--court", choices=COURTS)
    ap.add_argument("--intruder", choices=FRIENDS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--ball", choices=BALLS)
    ap.add_argument("-n", "--n", type=int, default=1)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.court is None or c[1] == args.court)
              and (args.intruder is None or c[2] == args.intruder)
              and (args.friend is None or c[3] == args.friend)
              and (args.ball is None or c[4] == args.ball)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, court, intruder, friend, ball = rng.choice(sorted(combos))
    return StoryParams(setting=setting, court=court, intruder=intruder, friend=friend, ball=ball)


def _mk_world(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    court = COURTS[params.court]
    intr = FRIENDS[params.intruder]
    fr = FRIENDS[params.friend]
    ball = BALLS[params.ball]

    court_ent = world.add(Entity(
        id="court", kind="place", type="place", label=court["label"], phrase=court["phrase"],
        tags={"tennis", "court"},
    ))
    a = world.add(Entity(
        id="intruder", kind="character", type=intr["type"], label=intr["label"], phrase=intr["phrase"],
        traits=[intr["trait"]], role="intruder", tags={"friendship", "tennis"}, attrs={"color": intr["color"]},
    ))
    b = world.add(Entity(
        id="friend", kind="character", type=fr["type"], label=fr["label"], phrase=fr["phrase"],
        traits=[fr["trait"]], role="friend", tags={"friendship", "tennis"}, attrs={"color": fr["color"]},
    ))
    ball_ent = world.add(Entity(
        id="ball", kind="thing", type="ball", label=ball["label"], phrase=ball["phrase"],
        tags={"tennis"},
    ))
    world.facts.update(setting=setting, court=court_ent, intruder=a, friend=b, ball=ball_ent)
    return world


def _propagate(world: World) -> None:
    court = world.get("court")
    a = world.get("intruder")
    b = world.get("friend")
    ball = world.get("ball")
    if a.meters.get("blocking", 0) >= 1 and ("block", a.id) not in world.fired:
        world.fired.add(("block", a.id))
        court.meters["blocked"] += 1
        a.memes["pride"] += 1
        world.event("block", actor=a.id)
    if b.meters.get("sharing", 0) >= 1 and ("share", b.id) not in world.fired:
        world.fired.add(("share", b.id))
        court.meters["open"] += 1
        a.memes["friendship"] += 1
        b.memes["friendship"] += 1
        b.memes["patience"] += 1
        ball.meters["play"] += 1
        world.event("share", actor=b.id)


def tell(params: StoryParams) -> World:
    world = _mk_world(params)
    court = world.get("court")
    a = world.get("intruder")
    b = world.get("friend")
    ball = world.get("ball")
    setting = SETTINGS[params.setting]
    court_text = court.ref()
    world.say(f"At {setting['place']}, {a.ref()} and {b.ref()} found {court.ref()} waiting in the sun.")
    world.say(f"It was a fine place for tennis, and the bright ball lay there like a small round promise.")

    world.para()
    world.say(f"{a.ref().capitalize()} wanted to occupy the whole court and keep the tennis ball close.")
    a.meters["blocking"] += 1
    a.memes["pride"] += 1
    _propagate(world)
    world.say(f"{b.ref().capitalize()} did not scold, but said that friendship grows when space is shared.")

    world.para()
    world.say(f"{b.ref().capitalize()} rolled the tennis ball back across the white line.")
    b.meters["sharing"] += 1
    _propagate(world)
    world.say(f"{a.ref().capitalize()} saw the ball return and felt the heat of pride cool into kindness.")
    a.memes["pride"] = 0
    a.memes["friendship"] += 1
    a.meters["blocking"] = 0
    court.meters["blocked"] = 0
    court.meters["open"] = 1

    world.para()
    world.say(f"Then the two friends played together, one bounce at a time, and even the court seemed to smile.")
    world.say(f"{court.open_image} {MORAL}")
    world.facts.update(outcome="happy", court_open=True, ball_play=ball.meters["play"] >= 1)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fable for a young child about {f['intruder'].label} and {f['friend'].label} sharing {f['court'].label} with a tennis ball.",
        f"Tell a happy-ending story that includes the words occupy and tennis, and teaches why friends should share a court.",
        f"Write a short fable in which one friend tries to occupy the tennis court, but another friend turns it into a shared game.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["intruder"]
    b = world.facts["friend"]
    court = world.facts["court"]
    ball = world.facts["ball"]
    return [
        QAItem(
            question=f"Who tried to occupy the tennis court?",
            answer=f"{a.ref().capitalize()} tried to occupy the whole court. That was the selfish choice at the start of the fable.",
        ),
        QAItem(
            question=f"What did {b.ref()} do instead of arguing?",
            answer=f"{b.ref().capitalize()} rolled the tennis ball back and shared the space. That gentle move changed the mood and brought the friends together.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The court stayed open, the ball was being played, and the two friends were happy together. The ending shows that sharing made the whole place better.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tennis?",
            answer="Tennis is a game played with a ball and a racket on a court. Friends can take turns and keep the game fair.",
        ),
        QAItem(
            question="Why is friendship important in a fable?",
            answer="Friendship matters because kind choices help everyone feel welcome. In a fable, that lesson is usually shown with simple actions and a happy ending.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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


def generate(params: StoryParams) -> StorySample:
    if params.intruder == params.friend:
        raise StoryError("(No story: the two friends must be different.)")
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
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
same_court(C) :- court(C).
valid(S,C,I,F,B) :- setting(S), court(C), intruder(I), friend(F), ball(B), I != F.
share_wins(C) :- blocked(C,0), open(C,1).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in COURTS:
        lines.append(asp.fact("court", cid))
    for fid in FRIENDS:
        lines.append(asp.fact("intruder", fid))
        lines.append(asp.fact("friend", fid))
    for bid in BALLS:
        lines.append(asp.fact("ball", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH")
    else:
        print(f"OK: {len(py)} combos")
    # smoke test ordinary generation
    sample = generate(StoryParams(setting="village_green", court="tennis_court", intruder="peacock", friend="turtle", ball="green_ball"))
    if "tennis" not in sample.story.lower():
        rc = 1
        print("SMOKE FAILED")
    else:
        print("OK: generate smoke test")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.asp:
        print("\n".join(map(str, asp_valid_combos())))
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(setting=s, court="tennis_court", intruder="peacock", friend="turtle", ball="green_ball")) for s in SETTINGS]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
