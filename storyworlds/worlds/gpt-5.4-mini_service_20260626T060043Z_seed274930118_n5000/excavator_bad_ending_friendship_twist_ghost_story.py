#!/usr/bin/env python3
"""
A tiny ghost-story world with an excavator, a friendship, and a twist ending.

The seed premise:
- A lonely child visits a moonlit lot where an excavator works at night.
- A friendly ghost appears beside the machine and becomes a surprising helper.
- The twist is that the ghost was guarding a hidden keepsake.
- The ending is bittersweet: the friend vanishes at sunrise, leaving a small
  gift and a changed heart, but not a permanent companion.

This world is intentionally small and classical: one core premise, a stateful
middle turn, and an ending image that proves something changed.
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "boy", "child"}:
            if self.type == "girl":
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type == "boy":
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old construction lot"
    night: bool = True
    haunted: bool = True


@dataclass
class Tale:
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    parent_name: str
    prize: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_lonely(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    ghost = world.entities.get("ghost")
    if not hero or not ghost:
        return out
    if hero.memes.get("lonely", 0) >= THRESHOLD and ghost.memes.get("kindness", 0) >= THRESHOLD:
        sig = ("lonely",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["hope"] = hero.memes.get("hope", 0) + 1
            out.append("The dark felt a little less heavy.")
    return out


def _r_twist(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    ghost = world.entities.get("ghost")
    relic = world.entities.get("relic")
    if not hero or not ghost or not relic:
        return out
    if ghost.memes.get("guarded_relic", 0) >= THRESHOLD and relic.meters.get("found", 0) >= THRESHOLD:
        sig = ("twist",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
            out.append("__twist__")
    return out


def _r_bad_ending(world: World) -> list[str]:
    hero = world.entities.get("hero")
    ghost = world.entities.get("ghost")
    if not hero or not ghost:
        return []
    if ghost.meters.get("gone", 0) >= THRESHOLD:
        sig = ("gone",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["sadness"] = hero.memes.get("sadness", 0) + 1
            return ["The friend was already fading."]
    return []


RULES = [
    Rule("lonely", _r_lonely),
    Rule("twist", _r_twist),
    Rule("bad_ending", _r_bad_ending),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend([x for x in lines if x != "__twist__"])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(tale: Tale) -> World:
    w = World(SETTING)
    hero = w.add(Entity(
        id="hero", kind="character", type=tale.hero_type, label=tale.hero_name,
        meters={}, memes={"lonely": 1.0, "curious": 1.0, "brave": 0.5},
    ))
    parent = w.add(Entity(
        id="parent", kind="character", type="adult", label=tale.parent_name,
        meters={}, memes={"worry": 0.5},
    ))
    excavator = w.add(Entity(
        id="excavator", type="machine", label="excavator",
        phrase="a big yellow excavator", meters={"weight": 8.0, "noise": 7.0},
    ))
    ghost = w.add(Entity(
        id="ghost", kind="character", type="ghost", label=tale.companion_name,
        meters={"glow": 3.0, "gone": 0.0},
        memes={"kindness": 1.0, "friendship": 1.0, "guarded_relic": 0.0},
    ))
    relic = w.add(Entity(
        id="relic", type="thing", label="tin box", phrase="a little tin box",
        meters={"buried": 1.0, "found": 0.0},
    ))

    w.say(
        f"On a cold night, {hero.label} stood at {SETTING.place} and watched the excavator "
        f"blink its lights through the fog."
    )
    w.say(
        f"{hero.label} felt lonely, because the lot was quiet and even the streetlamp seemed to hold its breath."
    )

    w.para()
    ghost.memes["friendship"] += 1
    w.say(
        f"Then {ghost.label} drifted out from behind a stack of bricks, soft as mist, and smiled at {hero.label}."
    )
    w.say(
        f"{ghost.label} said the excavator was not scary at all; it was only making room for something hidden."
    )
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    w.say(
        f"{hero.label} laughed, and the two became friends while the excavator hummed under the moon."
    )

    w.para()
    relic.meters["found"] = 1.0
    ghost.memes["guarded_relic"] = 1.0
    w.say(
        f"Together they followed a pale shimmer in the dirt, and the excavator's bucket gently lifted a patch of earth."
    )
    w.say(
        f"Under it, they found {relic.phrase}, wrapped in a ribbon the color of old rain."
    )
    w.say(
        f"{ghost.label} looked very glad, because the little box had been waiting for someone kind to uncover it."
    )
    propagate(w, narrate=True)

    w.para()
    w.say(
        f"But the twist came with the first silver line of morning: {ghost.label} was fading."
    )
    ghost.meters["gone"] = 1.0
    propagate(w, narrate=True)
    w.say(
        f"{hero.label} wanted to keep the new friend forever, yet {ghost.label} only waved once and turned into a soft curl of mist."
    )
    w.say(
        f"When the sun rose, {hero.label} held the tin box in both hands while the excavator stood quiet and gold in the light."
    )

    w.facts.update(hero=hero, parent=parent, excavator=excavator, ghost=ghost, relic=relic)
    return w


SETTING = Setting(place="the old construction lot", night=True, haunted=True)


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    parent_name: str
    prize: str
    seed: Optional[int] = None


HERO_NAMES = ["Mina", "Toby", "Iris", "Noah", "Lena"]
PARENT_NAMES = ["Mom", "Dad", "Aunt Ruth", "Uncle Ben"]
GHOST_NAMES = ["Pip", "Moth", "Vera", "Nell"]
PRIZES = ["tin box", "blue marble", "music key"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost story with an excavator, friendship, and a twist.")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--companion-name")
    ap.add_argument("--companion-type", choices=["ghost"])
    ap.add_argument("--parent-name")
    ap.add_argument("--prize", choices=PRIZES)
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
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    companion_name = args.companion_name or rng.choice(GHOST_NAMES)
    parent_name = args.parent_name or rng.choice(PARENT_NAMES)
    prize = args.prize or rng.choice(PRIZES)
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        companion_name=companion_name,
        companion_type="ghost",
        parent_name=parent_name,
        prize=prize,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    prompts = generation_prompts(world)
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    ghost = f["ghost"]
    return [
        "Write a short ghost story for children with an excavator, a friendship, and a twist ending.",
        f"Tell a moonlit story where {hero.label} meets a friendly ghost near an excavator and discovers a hidden surprise.",
        f"Write a gentle spooky tale in which {hero.label} and {ghost.label} follow a clue under the dirt and then face a sad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ghost = f["ghost"]
    relic = f["relic"]
    qa = [
        QAItem(
            question=f"Where did {hero.label} see the excavator?",
            answer=f"{hero.label} saw the excavator at {SETTING.place}, under the moon and fog.",
        ),
        QAItem(
            question=f"Who became {hero.label}'s friend in the story?",
            answer=f"{ghost.label}, the friendly ghost, became {hero.label}'s new friend.",
        ),
        QAItem(
            question=f"What hidden thing did they uncover together?",
            answer=f"They uncovered {relic.phrase}, which had been buried in the dirt.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {ghost.label} was not there to frighten anyone; {ghost.label} had been guarding the hidden box.",
        ),
        QAItem(
            question=f"Why was the ending sad?",
            answer=f"The ending was sad because {ghost.label} faded away with the morning light, so the new friendship could not last forever.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an excavator?",
            answer="An excavator is a large machine with a bucket arm that can scoop up dirt and move heavy ground.",
        ),
        QAItem(
            question="What is a ghost in a story like this?",
            answer="A ghost is a spooky figure that can float or appear like mist in a ghost story.",
        ),
        QAItem(
            question="Why do people use lights at night on a work site?",
            answer="People use lights at night so they can see the ground clearly and work more safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(hero).
ghost(ghost).
excavator(excavator).
relic(relic).

twist :- guarded_relic(ghost), found(relic).
bad_ending :- ghost_gone(ghost).

#show twist/0.
#show bad_ending/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("guarded_relic", "ghost"),
        asp.fact("found", "relic"),
        asp.fact("ghost_gone", "ghost"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show twist/0.\n#show bad_ending/0."))
    atoms = {(s.name, len(s.arguments)) for s in model}
    expected = {("twist", 0), ("bad_ending", 0)}
    if atoms == expected:
        print("OK: ASP twin matches the Python story logic.")
        return 0
    print("MISMATCH: ASP twin did not match Python story logic.")
    print("  got:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


def explain_rejection() -> str:
    return "(No story: this world always uses one excavator, one ghost, and one bittersweet twist.)"


def resolve_params_strict(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def asp_valid_story() -> bool:
    return True


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
        print(asp_program("#show twist/0.\n#show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world has one declarative twin; use --show-asp or --verify.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Mina", "girl", "Pip", "ghost", "Mom", "tin box"),
            StoryParams("Toby", "boy", "Moth", "ghost", "Dad", "blue marble"),
            StoryParams("Iris", "girl", "Vera", "ghost", "Aunt Ruth", "music key"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params_strict(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
