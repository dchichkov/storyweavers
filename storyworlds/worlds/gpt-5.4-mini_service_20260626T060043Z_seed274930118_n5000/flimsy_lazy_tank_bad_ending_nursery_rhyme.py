#!/usr/bin/env python3
"""
A small Storyweavers world: a nursery-rhyme style tale about a flimsy bridge,
a lazy tank, and a bad ending.

Premise:
- A little tank wants to roll to a ribbon.
- A flimsy bridge is the only path.
- The tank is lazy, so it tries a risky shortcut instead of waiting.

Turn:
- The shortcut weakens the bridge and traps the tank.

Resolution:
- There is no happy fix; the tank ends in a worse spot, which makes this a
  deliberate bad-ending world.
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

WORD_FLIMSY = "flimsy"
WORD_LAZY = "lazy"
WORD_TANK = "tank"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    setting_line: str
    path_line: str
    hazard_line: str
    end_line: str


@dataclass
class StoryParams:
    place: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


PLACES = {
    "muddy_lane": Place(
        name="the muddy lane",
        setting_line="Down by the lane, the daisies nodded in a row.",
        path_line="A flimsy little bridge lay over the ditch.",
        hazard_line="Its boards were thin and old, and they creaked like a spoon in a bowl.",
        end_line="The lane looked sad when the bridge gave way.",
    ),
    "apple_yard": Place(
        name="the apple yard",
        setting_line="In the apple yard, the bees hummed low and slow.",
        path_line="A flimsy plank crossed a sleepy stream.",
        hazard_line="The plank was light as paper and bowed at every toe.",
        end_line="The yard grew quiet when the plank broke loose.",
    ),
}

PLACE_ORDER = ["muddy_lane", "apple_yard"]


@dataclass
class EventState:
    tank_motion: float = 0.0
    bridge_strength: float = 2.0
    trapped: bool = False
    broken: bool = False


def nursery_opening(place: Place) -> str:
    return f"{place.setting_line} {place.path_line} {place.hazard_line}"


def state_storybeat(world: World) -> None:
    tank = world.get("tank")
    bridge = world.get("bridge")
    place = world.place
    world.say(nursery_opening(place))
    world.say(
        f"On that lane there lived a {WORD_LAZY} little {WORD_TANK}, all shiny and round."
    )
    world.say(
        f"{tank.id.capitalize()} loved to roll along, but most days {tank.pronoun()} would nap in the grass."
    )
    world.say(
        f"The little {WORD_TANK} kept eyeing a red ribbon at the far side of the bridge."
    )
    world.facts["opening_bridge_strength"] = bridge.meters["strength"]
    world.facts["opening_lazy"] = tank.memes["lazy"]


def want_and_warning(world: World) -> None:
    tank = world.get("tank")
    bridge = world.get("bridge")
    world.say(
        f"One bright day, {tank.id.capitalize()} wanted the ribbon right away, but the way was {WORD_FLIMSY} and small."
    )
    world.say(
        f"The bridge whispered a warning in its wooden squeak: 'Go slow, go slow, or I may fall.'"
    )
    tank.memes["want"] += 1
    tank.memes["lazy"] += 1
    bridge.meters["stress"] += 0.5


def try_shortcut(world: World) -> None:
    tank = world.get("tank")
    bridge = world.get("bridge")
    world.say(
        f"But the {WORD_LAZY} little {WORD_TANK} did not wait."
    )
    world.say(
        f"{tank.id.capitalize()} rolled too fast onto the {WORD_FLIMSY} bridge, and the boards began to shiver."
    )
    tank.meters["speed"] += 1.0
    tank.meters["weight"] += 1.0
    bridge.meters["stress"] += 2.0
    bridge.meters["strength"] -= 1.5
    if bridge.meters["strength"] <= 0:
        bridge.meters["broken"] = 1
        tank.memes["trouble"] += 1


def fall_and_bad_end(world: World) -> None:
    tank = world.get("tank")
    bridge = world.get("bridge")
    world.say(
        f"Then the bridge cracked with a snap and a clack, and down went the little track."
    )
    world.say(
        f"The {WORD_TANK} tipped in the mud, and the ribbon bobbed away in the reeds."
    )
    bridge.meters["broken"] = 1
    tank.meters["stuck"] = 1
    tank.memes["sad"] += 2
    tank.memes["regret"] += 1
    world.facts["bad_ending"] = True


def tell(place: Place) -> World:
    world = World(place)
    tank = world.add(Entity(
        id="tank",
        kind="character",
        type="tank",
        label="tank",
        phrase=f"a {WORD_LAZY} little tank",
        meters={"speed": 0.0, "weight": 1.0, "stuck": 0.0},
        memes={"lazy": 1.0, "want": 0.0, "sad": 0.0, "regret": 0.0, "trouble": 0.0},
    ))
    bridge = world.add(Entity(
        id="bridge",
        kind="thing",
        type="bridge",
        label="bridge",
        phrase=f"a {WORD_FLIMSY} bridge",
        meters={"strength": 2.0, "stress": 0.0, "broken": 0.0},
    ))
    world.facts.update(tank=tank, bridge=bridge, place=place)

    state_storybeat(world)
    world.para()
    want_and_warning(world)
    world.para()
    try_shortcut(world)
    fall_and_bad_end(world)
    world.para()
    world.say(
        f"So the little {WORD_TANK} stayed in the mud, and the ribbon fluttered on without it."
    )
    world.say(
        f"That was the end: no cheer, no prize, only the quiet lane and a broken bridge."
    )
    return world


def story_prompts() -> list[str]:
    return [
        f"Write a short nursery rhyme story about a {WORD_LAZY} {WORD_TANK} and a {WORD_FLIMSY} bridge, ending badly.",
        f"Tell a child-friendly rhyme where a little {WORD_TANK} ignores a warning and meets a bad ending.",
        f"Make a simple story with the words {WORD_FLIMSY}, {WORD_LAZY}, and {WORD_TANK}, with a sad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    place: Place = world.facts["place"]  # type: ignore[assignment]
    tank: Entity = world.facts["tank"]  # type: ignore[assignment]
    bridge: Entity = world.facts["bridge"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Who wanted the red ribbon?",
            answer="The little tank wanted the red ribbon.",
        ),
        QAItem(
            question="What was the bridge like?",
            answer="The bridge was flimsy, thin, and old, so it could not hold up well.",
        ),
        QAItem(
            question="Why did the bridge break?",
            answer="It broke because the lazy tank rolled onto it too fast and made the bridge take too much stress.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly: the tank got stuck in the mud and the ribbon stayed out of reach.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened at {place.name}.",
        ),
    ]


def world_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does flimsy mean?",
            answer="Flimsy means weak, thin, or easy to break.",
        ),
        QAItem(
            question="What does lazy mean?",
            answer="Lazy means not wanting to work, move, or try very hard.",
        ),
        QAItem(
            question="What is a tank?",
            answer="A tank is a heavy vehicle with strong wheels or tracks that can roll over rough ground.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return story_prompts()


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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
flimsy_bridge(B) :- bridge(B), strength(B,S), S < 1.
lazy_tank(T) :- tank(T), lazy(T).
bad_ending :- flimsy_bridge(_), lazy_tank(_), broken(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("bridge", "bridge"))
    lines.append(asp.fact("tank", "tank"))
    lines.append(asp.fact("lazy", "tank"))
    lines.append(asp.fact("strength", "bridge", 2))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/0."))
    has = any(sym.name == "bad_ending" for sym in model)
    if has:
        print("OK: ASP reasoner can derive the bad ending.")
        return 0
    print("MISMATCH: ASP reasoner did not derive the bad ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: flimsy bridge, lazy tank, bad ending."
    )
    ap.add_argument("--place", choices=PLACES)
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
    place = args.place or rng.choice(sorted(PLACES))
    return StoryParams(place=place)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    world = tell(place)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def valid_places() -> list[str]:
    return sorted(PLACES)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern: the flimsy bridge, the lazy tank, and the bad ending.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in valid_places():
            params = StoryParams(place=place, seed=base_seed)
            samples.append(generate(params))
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
