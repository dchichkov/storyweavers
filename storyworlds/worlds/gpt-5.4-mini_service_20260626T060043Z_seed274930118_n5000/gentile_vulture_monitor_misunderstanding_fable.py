#!/usr/bin/env python3
"""
gentile_vulture_monitor_misunderstanding_fable.py
==================================================

A small fable-style story world about a gentile, a vulture, and a monitor,
built around a misunderstanding that is resolved by patient explanation.

Seed premise:
- A gentile traveler is carrying food through a hot plain.
- A vulture is watching from above.
- A monitor lizard is on a stone wall, looking stern and still.
- The traveler mistakes the vulture's circling and the monitor's silence for
  danger or blame, while the animals misunderstand the gentile too.
- The misunderstanding is resolved when the gentile shares the food and learns
  that the vulture was only waiting for scraps and the monitor was only trying
  to warm itself and keep watch.

The world uses physical meters and emotional memes:
- meters: distance, hunger, thirst, heat, satiety, shade
- memes: fear, trust, pride, worry, calm, shame, gratitude

The prose should read like a short fable with a clear turn and a simple moral.
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
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""
    visible: bool = True

    def __post_init__(self) -> None:
        for k in ["distance", "hunger", "thirst", "heat", "satiety", "shade"]:
            self.meters.setdefault(k, 0.0)
        for k in ["fear", "trust", "pride", "worry", "calm", "shame", "gratitude"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"gentile", "traveler", "person"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"vulture"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"monitor", "monitor lizard"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the warm plain"
    shade: str = "a low acacia tree"
    water: str = "a small spring"
    wall: str = "a sun-baked stone wall"


@dataclass
class StoryParams:
    setting: str = "plain"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clamp(x: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, x))


def moral_from_world(world: World) -> str:
    if world.get("gentile").memes["gratitude"] > 0:
        return "The fable taught that a gentle question can save a fearful heart."
    return "The fable taught that not every watchful eye is a threat."


def intro_line(hero: Entity, setting: Setting) -> str:
    return (
        f"Once in {setting.place}, a gentile traveler named {hero.label} walked "
        f"slowly beside {setting.shade} and looked for {setting.water}."
    )


def describe_fear(world: World) -> None:
    g = world.get("gentile")
    v = world.get("vulture")
    m = world.get("monitor")
    world.say(
        f"{g.label} noticed a vulture circling overhead and a monitor lizard "
        f"holding still on {world.setting.wall}."
    )
    world.say(
        f"{g.label} worried that the vulture meant harm, and {g.pronoun('subject')} "
        f"did not trust the monitor's sharp stare."
    )
    world.say(
        f"From above, the vulture thought the gentile was guarding food, and the "
        f"monitor thought the traveler looked proud and unwilling to share."
    )
    g.memes["fear"] += 2
    g.memes["worry"] += 1
    v.memes["worry"] += 1
    m.memes["worry"] += 1


def escalate(world: World) -> None:
    g = world.get("gentile")
    v = world.get("vulture")
    m = world.get("monitor")
    g.meters["heat"] += 2
    g.meters["thirst"] += 2
    v.meters["hunger"] += 2
    m.meters["heat"] += 1
    g.memes["pride"] += 1
    world.say(
        f"The day grew hotter, and the gentile hugged the food closer, because "
        f"the vulture's shadow made {g.pronoun('object')} nervous."
    )
    world.say(
        f"The vulture stayed near, not to attack, but because the smell of food "
        f"made {v.pronoun('subject')} hopeful."
    )
    world.say(
        f"The monitor remained on the wall, still and watchful, which made the "
        f"gentile fear a warning where there was only silence."
    )


def resolve(world: World) -> None:
    g = world.get("gentile")
    v = world.get("vulture")
    m = world.get("monitor")

    g.memes["calm"] += 2
    g.memes["trust"] += 2
    g.memes["fear"] = 0
    v.memes["calm"] += 1
    v.memes["trust"] += 1
    m.memes["calm"] += 1
    m.memes["trust"] += 1

    g.meters["satiety"] += 2
    v.meters["hunger"] = clamp(v.meters["hunger"] - 1)
    m.meters["shade"] += 1

    world.say(
        f"At last, {g.label} set the food down under {world.setting.shade} and "
        f"spoke kindly to the two watchers."
    )
    world.say(
        f"Then the misunderstanding came clear: the vulture had only wanted the "
        f"crumbs, and the monitor had only wanted the warmth of the wall."
    )
    world.say(
        f"{g.label} shared a small meal, the vulture took the scraps, and the "
        f"monitor slipped closer to the shade."
    )
    world.say(
        f"The three were no longer enemies in a cloud of guesses; they were "
        f"simply creatures sharing one hot day."
    )
    world.say(f"Moral: {moral_from_world(world)}")


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    setting = Setting()
    world = World(setting)

    gentile = world.add(Entity(
        id="gentile",
        kind="character",
        label="a gentile traveler",
        type="gentile",
        traits=["gentle", "careful", "kind"],
        meters={"distance": 4.0, "hunger": 3.0, "thirst": 2.0, "heat": 2.0, "satiety": 0.0, "shade": 0.0},
        memes={"fear": 0.0, "trust": 1.0, "pride": 0.0, "worry": 0.0, "calm": 1.0, "shame": 0.0, "gratitude": 0.0},
    ))
    vulture = world.add(Entity(
        id="vulture",
        kind="character",
        label="a vulture",
        type="vulture",
        traits=["watchful", "patient"],
        meters={"distance": 7.0, "hunger": 4.0, "thirst": 1.0, "heat": 1.0, "satiety": 0.0, "shade": 0.0},
        memes={"fear": 0.0, "trust": 0.0, "pride": 0.0, "worry": 1.0, "calm": 0.0, "shame": 0.0, "gratitude": 0.0},
    ))
    monitor = world.add(Entity(
        id="monitor",
        kind="character",
        label="a monitor lizard",
        type="monitor",
        traits=["still", "stern-looking"],
        meters={"distance": 2.0, "hunger": 1.0, "thirst": 0.5, "heat": 2.0, "satiety": 0.0, "shade": 1.0},
        memes={"fear": 0.0, "trust": 0.0, "pride": 0.0, "worry": 1.0, "calm": 0.5, "shame": 0.0, "gratitude": 0.0},
    ))

    world.say(intro_line(gentile, setting))
    world.say(
        f"{gentile.label.capitalize()} carried a little bundle of bread and dates, "
        f"hoping to reach {setting.water} before the sun grew harsher."
    )
    world.para()

    describe_fear(world)
    escalate(world)
    world.para()
    resolve(world)

    world.facts = {
        "gentile": gentile,
        "vulture": vulture,
        "monitor": monitor,
        "setting": setting,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short fable about a gentile, a vulture, and a monitor who first misunderstand one another and then learn the truth.',
        'Tell a child-friendly story where a gentile traveler fears a vulture and a monitor, but the misunderstanding turns into sharing.',
        'Write a brief fable with the seed words "gentile", "vulture", and "monitor" that ends with a simple moral.',
    ]


def story_qa(world: World) -> list[QAItem]:
    g = world.get("gentile")
    v = world.get("vulture")
    m = world.get("monitor")
    setting = world.setting
    return [
        QAItem(
            question="Who is the story mainly about?",
            answer=f"The story is about a gentile traveler named {g.label}, who is trying to cross {setting.place}.",
        ),
        QAItem(
            question="Why did the gentile feel afraid?",
            answer="The gentile misunderstood the vulture's circling and the monitor's stillness, so those signs felt like danger.",
        ),
        QAItem(
            question="What did the vulture really want?",
            answer="The vulture was not trying to attack; it was waiting hopefully for scraps of food.",
        ),
        QAItem(
            question="What did the monitor really want?",
            answer="The monitor was only trying to keep watch and enjoy the warmth of the wall, not to scare anyone.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The gentile shared the food, the fear faded, and all three creatures became calm on the hot day.",
        ),
        QAItem(
            question="What moral does the fable give?",
            answer=moral_from_world(world),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vulture?",
            answer="A vulture is a large bird that often soars high and looks for food or scraps.",
        ),
        QAItem(
            question="What is a monitor lizard?",
            answer="A monitor lizard is a large lizard that can stay very still and watch what is happening around it.",
        ),
        QAItem(
            question="What does gentile mean in this story?",
            answer="Here, gentile means kind and gentle, describing a traveler who tries to act with care.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A gentile, a vulture, and a monitor can be in a misunderstanding when the
% gentile fears the watchers and the watchers are merely observing or waiting.
misunderstood(gentile) :- sees(gentile, vulture), fears(gentile, vulture).
misunderstood(gentile) :- sees(gentile, monitor), fears(gentile, monitor).
misunderstood(vulture) :- sees(vulture, gentile), assumes(vulture, gentile).
misunderstood(monitor) :- sees(monitor, gentile), assumes(monitor, gentile).

% Resolution happens when the gentile shares food and fear drops.
resolved :- shares(gentile, food), not fears(gentile, vulture), not fears(gentile, monitor).

#show misunderstood/1.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("sees", "gentile", "vulture"),
        asp.fact("sees", "gentile", "monitor"),
        asp.fact("sees", "vulture", "gentile"),
        asp.fact("sees", "monitor", "gentile"),
        asp.fact("fears", "gentile", "vulture"),
        asp.fact("fears", "gentile", "monitor"),
        asp.fact("assumes", "vulture", "gentile"),
        asp.fact("assumes", "monitor", "gentile"),
        asp.fact("shares", "gentile", "food"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    got = set(asp.atoms(model, "misunderstood"))
    resolved = bool(asp.atoms(model, "resolved"))
    want = {("gentile",), ("vulture",), ("monitor",)}
    if got == want and resolved:
        print("OK: ASP model matches the fable's misunderstanding and resolution.")
        return 0
    print("MISMATCH in ASP model.")
    print("got misunderstood:", sorted(got))
    print("resolved:", resolved)
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable about misunderstanding among a gentile, a vulture, and a monitor.")
    ap.add_argument("--setting", choices=["plain"], default=None)
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
    if args.setting and args.setting != "plain":
        raise StoryError("Only one setting is supported in this fable world: plain.")
    return StoryParams(setting="plain", seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("misunderstood:", sorted(asp.atoms(model, "misunderstood")))
        print("resolved:", bool(asp.atoms(model, "resolved")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples.append(generate(StoryParams(setting="plain", seed=base_seed)))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
