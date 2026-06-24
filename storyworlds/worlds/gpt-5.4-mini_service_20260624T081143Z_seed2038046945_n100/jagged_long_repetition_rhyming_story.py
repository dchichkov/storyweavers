#!/usr/bin/env python3
"""
storyworlds/worlds/jagged_long_repetition_rhyming_story.py
==========================================================

A small standalone storyworld built from the seed idea of a jagged, long,
repetitive rhyming tale.

Premise:
- A child wants to walk a long, jagged trail and bring home a prize.
- The trail is rough and the wrong shoes or tools will get scratched or stuck.
- A parent notices the risk, offers a safer match, and the child gets to go.

The prose is written in a simple rhyming-story cadence with deliberate
repetition, so the narration feels sung and memorable rather than like a log.
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
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protects: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"scratched": 0.0, "muddy": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "tug": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    surface: str
    rhyme: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Path:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict = {}
        self.zone: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "meadow": Setting("the meadow", "grass", "glow", {"trail"}),
    "shore": Setting("the shore", "shells", "flow", {"trail"}),
    "hill": Setting("the hill", "stones", "hill", {"trail"}),
}

PATHS = {
    "trail": Path(
        id="trail",
        verb="follow the long jagged trail",
        gerund="following the long jagged trail",
        rush="dash down the jagged path",
        risk="scratched and sore",
        zone={"feet", "hands"},
        keyword="jagged",
        tags={"jagged", "long"},
    ),
}

PRIZES = {
    "stone": Prize("stone", "stone", "a shiny stone", "hands"),
    "shell": Prize("shell", "shell", "a bright shell", "hands"),
    "flower": Prize("flower", "flower", "a small flower", "hands"),
}

GEAR = [
    Gear("boots", "sturdy boots", {"feet"}, {"scratched"}, "put on sturdy boots", "went back for the sturdy boots"),
    Gear("gloves", "soft gloves", {"hands"}, {"scratched"}, "put on soft gloves", "went back for the soft gloves"),
    Gear("boots_and_gloves", "sturdy boots and soft gloves", {"feet", "hands"}, {"scratched"}, "put on sturdy boots and soft gloves", "went back for the sturdy boots and soft gloves", True),
]

NAMES = ["Mia", "Leo", "Nora", "Eli", "Ava", "Ben"]
TYPES = {"girl": ["mother", "woman"], "boy": ["father", "man"]}


def has_at_risk(path: Path, prize: Prize) -> bool:
    return prize.region in path.zone


def select_gear(path: Path, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and "scratched" in gear.guards:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for pid in setting.affords:
            path = PATHS[pid]
            for prize_id, prize in PRIZES.items():
                if has_at_risk(path, prize) and select_gear(path, prize):
                    out.append((place, pid, prize_id))
    return out


def explain_rejection(path: Path, prize: Prize) -> str:
    return f"(No story: the {path.keyword} trail would not honestly threaten a {prize.label}.)"


def build_world(params) -> World:
    setting = SETTINGS[params.place]
    path = PATHS[params.path]
    prize = PRIZES[params.prize]
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label="the parent"))
    prize_e = world.add(Entity(id="prize", label=prize.label, phrase=prize.phrase, plural=prize.plural, owner=child.id, caretaker=parent.id))
    gear_def = select_gear(path, prize)
    gear = world.add(Entity(id=gear_def.id, label=gear_def.label, plural=gear_def.plural, owner=child.id, protects=set(gear_def.covers))) if gear_def else None
    if gear:
        gear.worn_by = child.id

    child.memes["tug"] += 1
    child.memes["joy"] += 1
    world.say(f"{child.id} was a little {params.trait} {params.gender} who loved to sing and sway.")
    world.say(f"{child.id} loved {path.gerund}, day after day, with a la-la-lay.")
    world.say(f"{parent.label_word if hasattr(parent, 'label_word') else 'parent'} bought {child.pronoun('object')} {prize.phrase}.")
    world.say(f"{child.id} loved {prize_e.label} and carried {prize_e.it()} on the way.")

    world.say(f"One day by {setting.place}, with a soft little spray, {child.id} wanted to {path.verb}.")
    world.say(f"{child.id} said it again: '{path.keyword}, {path.keyword}, hooray, hooray!'")
    world.say(f"But {parent.label or 'the parent'} frowned. 'That path is long and jagged,' {parent.pronoun('subject') if False else 'they'} said.")
    world.say(f"'It can leave you {path.risk} if you run and play.'")

    child.memes["worry"] += 1
    if gear:
        world.say(f"Then {parent.label or 'the parent'} smiled a small safe smile and said, 'Let's {gear_def.prep} first today.'")
        world.say(f"{child.id} nodded and nodded, with a da-da-dae, and they {gear_def.tail}.")
        world.say(f"Now {child.id} could {path.gerund}, and {prize_e.label} stayed bright and gay.")
        child.memes["joy"] += 1
        child.memes["pride"] += 1
        prize_e.meters["scratched"] += 0
    world.facts = {"child": child, "parent": parent, "prize": prize_e, "gear": gear, "path": path, "setting": setting}
    return world


@dataclass
class StoryParams:
    place: str
    path: str
    prize: str
    name: str
    gender: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming storyworld with jagged, long repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", dest="parent_type", choices=["mother", "father"])
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
    if args.path and args.prize:
        if not (has_at_risk(PATHS[args.path], PRIZES[args.prize]) and select_gear(PATHS[args.path], PRIZES[args.prize])):
            raise StoryError(explain_rejection(PATHS[args.path], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.path is None or c[1] == args.path)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, path, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent_type = args.parent_type or ("mother" if gender == "girl" else "father")
    trait = rng.choice(["cheery", "brave", "spry", "kind"])
    return StoryParams(place, path, prize, name, gender, parent_type, trait)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, prize, path = f["child"], f["parent"], f["prize"], f["path"]
    return [
        QAItem(question=f"What did {child.id} want to do?", answer=f"{child.id} wanted to {path.verb}, again and again, along the long jagged way."),
        QAItem(question=f"Why did {parent.label if parent.label else 'the parent'} worry?", answer=f"The trail was long and jagged, so it could leave {child.id} scratched and sore."),
        QAItem(question=f"What helped {child.id} go safely?", answer=f"{f['gear'].label} helped {child.id} travel safely while keeping the prize bright."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does jagged mean?", answer="Jagged means rough and sharp, with uneven edges."),
        QAItem(question="What does repetition do in a story?", answer="Repetition repeats words or lines so a story feels catchy, steady, and easy to remember."),
        QAItem(question="What is a long trail?", answer="A long trail stretches far and takes many steps to follow."),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short rhyming story with jagged repetition and a long trail.',
        f"Tell a child-friendly rhyme where {world.facts['child'].id} wants to follow a jagged path but a parent worries.",
        "Make the ending gentle, safe, and sing-song.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
at_risk(P) :- prize(P), worn_on(P,R), path_zone(R).
has_fix(P) :- at_risk(P), gear(G), covers(G,R), worn_on(P,R), guards(G,scratched).
valid(Place,Path,Prize) :- setting(Place), affords(Place,Path), path(Path), prize(Prize), at_risk(Prize), has_fix(Prize).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", sid, p))
    for pid, p in PATHS.items():
        lines.append(asp.fact("path", pid))
        for z in sorted(p.zone):
            lines.append(asp.fact("path_zone", z))
    for prid, pr in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("worn_on", prid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid/3."))
    asp_set = set(asp.atoms(model, "valid"))
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python:", sorted(py))
    print("asp:", sorted(asp_set))
    return 1


CURATED = [
    StoryParams("meadow", "trail", "stone", "Mia", "girl", "mother", "cheery"),
    StoryParams("shore", "trail", "shell", "Leo", "boy", "father", "brave"),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    if trace and sample.world:
        print("--- trace ---")
        for k, v in sample.world.facts.items():
            if k in {"child", "parent", "prize", "gear", "path", "setting"}:
                continue
            print(k, v)
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
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(asp.atoms(model, "valid")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
