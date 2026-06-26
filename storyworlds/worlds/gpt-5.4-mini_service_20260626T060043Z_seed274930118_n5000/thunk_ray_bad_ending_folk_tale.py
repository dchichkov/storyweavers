#!/usr/bin/env python3
"""
storyworlds/worlds/thunk_ray_bad_ending_folk_tale.py
=====================================================

A small folk-tale story world with a bad ending: a curious child hears a thunk,
follows a ray of light, and loses the thing they were warned to keep safe.

Seed tale, distilled:
---
A poor child walked through the old woods with a loaf tied in a cloth.
At a dark stump, they heard a thunk from under the roots and saw one bright
ray on the moss. They lifted the root, found a hidden hollow, and reached in.
A sly forest spirit snapped the cloth away, and the child came home hungry,
with only the memory of the light.

World model:
---
    desire / curiosity         -> child moves toward the hidden place
    warning ignored            -> child defiance += 1
    hidden hollow opened       -> prize exposed
    spirit steals prize        -> prize.lost += 1, hero.memes["loss"] += 1
    ending bad                 -> hero returns empty-handed, cold, and sorry

Narrative instruments:
---
    thunk   -> a sound cue from the hollow under the roots
    ray     -> the single beam of light that tempts the child
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"lost": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "defiance": 0.0, "fear": 0.0, "loss": 0.0, "hunger": 0.0}

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
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    label: str
    phrase: str
    type: str
    risk: str
    gender: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class StoryParams:
    place: str
    prize: str
    name: str
    gender: str
    guardian: str
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_hunger(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    prize = world.get("prize")
    if prize.meters["lost"] >= THRESHOLD and ("hunger", prize.id) not in world.fired:
        world.fired.add(("hunger", prize.id))
        hero.memes["hunger"] += 1
        hero.memes["loss"] += 1
        out.append("The child felt the empty stomach grow louder.")
    return out


def _r_bad_end(world: World) -> list[str]:
    hero = world.get("hero")
    prize = world.get("prize")
    if prize.meters["lost"] >= THRESHOLD and ("bad_end", hero.id) not in world.fired:
        world.fired.add(("bad_end", hero.id))
        hero.memes["fear"] += 1
        return ["__bad_end__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_hunger, _r_bad_end):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__bad_end__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "forest": Setting(place="the old woods", mood="dim", affords={"search"}),
    "cottage": Setting(place="the border cottage", mood="warm", affords={"search"}),
    "hill": Setting(place="the windy hill", mood="bright", affords={"search"}),
}

PRIZES = {
    "loaf": Item(label="loaf", phrase="a warm loaf of bread", type="loaf", risk="hungry"),
    "bundle": Item(label="bundle", phrase="a cloth bundle of apples", type="bundle", risk="hungry", gender={"girl", "boy"}),
    "cake": Item(label="cake", phrase="a sweet honey cake", type="cake", risk="hungry"),
}

GIRL_NAMES = ["Mara", "Tess", "Nia", "Lena", "Anya", "Bela"]
BOY_NAMES = ["Pavel", "Niko", "Joren", "Tarin", "Milo", "Rurik"]
GUARDIANS = ["grandmother", "mother", "father", "uncle"]

CURATED = [
    StoryParams(place="forest", prize="loaf", name="Mara", gender="girl", guardian="grandmother"),
    StoryParams(place="cottage", prize="bundle", name="Pavel", gender="boy", guardian="mother"),
    StoryParams(place="hill", prize="cake", name="Tess", gender="girl", guardian="father"),
]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for prize_id, prize in PRIZES.items():
            combos.append((place, prize_id))
    return combos


def explain_rejection(place: str, prize: str) -> str:
    return f"(No story: the old tale needs a place and a prize that can be searched for; {place!r} with {prize!r} does not fit.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale world with a thunk, a ray, and a bad ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=GUARDIANS)
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
    if args.place and args.prize:
        if (args.place, args.prize) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.prize is None or c[1] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender not in prize.gender:
        gender = rng.choice(sorted(prize.gender))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(GUARDIANS)
    return StoryParams(place=place, prize=prize_id, name=name, gender=gender, guardian=guardian)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    prize_cfg = PRIZES[params.prize]
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name))
    guardian = world.add(Entity(id="guardian", kind="character", type=params.guardian, label=params.guardian))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=guardian.id))
    spirit = world.add(Entity(id="spirit", kind="character", type="spirit", label="forest spirit"))

    hero.memes["curiosity"] += 1
    world.say(f"Once, in {setting.place}, there lived a little {params.gender} named {params.name}.")
    world.say(f"{params.name} carried {params.name.lower()}'s {prize_cfg.phrase} in a cloth, because {params.guardian} had said it must be kept safe.")
    world.para()
    world.say(f"When {params.name} came to a hollow stump, there was a sudden thunk from under the roots.")
    world.say("A thin ray of light slipped through a crack and shone right on the moss.")
    world.say(f"{params.name} bent close, and the ray looked almost like a little road into the dark.")
    world.say(f"{params.name} wanted to see what made the thunk, even though the warning was still warm in {params.name.lower()}'s ears.")
    hero.memes["curiosity"] += 1
    hero.memes["defiance"] += 1
    world.para()
    world.say(f"So {params.name} lifted the root and peered into the hollow.")
    world.say(f"Inside, {params.name} reached for the shining thing, but the forest spirit was waiting.")
    prize.meters["lost"] += 1
    hero.memes["loss"] += 1
    propagate(world, narrate=False)
    world.say(f"With one sly tug, the spirit snatched the cloth away and vanished like smoke.")
    world.say(f"{params.name} stood in the leaves with empty hands and a sinking heart.")
    world.para()
    world.say(f"By the time {params.name} walked home, the woods had gone gray and the ray was gone.")
    world.say(f"{params.name} came back hungry, sorry, and poorer than before, while {params.guardian} found only an empty cloth.")
    world.facts.update(hero=hero, guardian=guardian, prize=prize, spirit=spirit, setting=setting, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write a short folk tale for a young child that includes the words "thunk" and "ray".',
        f"Tell a gentle but eerie story about {p.name}, who goes into {world.setting.place} with a {f['prize'].label}, hears a thunk, follows a ray, and loses the prize.",
        f"Write a folk-tale style story where curiosity wins for a moment and then ends badly, with an empty-handed return home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    prize = f["prize"]
    hero = f["hero"]
    guardian = f["guardian"]
    return [
        QAItem(
            question=f"Who was the little child in the story?",
            answer=f"The child was {p.name}, who went into {world.setting.place} with {prize.phrase}.",
        ),
        QAItem(
            question=f"What two things first made {p.name} curious at the stump?",
            answer=f"{p.name} heard a thunk from under the roots and saw a bright ray of light on the moss.",
        ),
        QAItem(
            question=f"What happened when {p.name} reached into the hollow?",
            answer=f"The forest spirit stole the cloth away, and {p.name} came home with empty hands.",
        ),
        QAItem(
            question=f"Why was {p.name} sad at the end?",
            answer=f"{p.name} was sad because the prize was lost, the walk home was lonely, and the story ended badly instead of with a happy rescue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ray of light?",
            answer="A ray of light is a narrow beam of light that comes from the sun, a lamp, or another bright thing.",
        ),
        QAItem(
            question="What does thunk sound like?",
            answer="Thunk is a dull, heavy sound, like something knocking against wood or dropping onto the ground.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(forest). place(cottage). place(hill).
prize(loaf). prize(bundle). prize(cake).
valid(P, R) :- place(P), prize(R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


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


def generate(params: StoryParams) -> StorySample:
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, prize in combos:
            print(f"  {place:8} {prize:8}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.prize} in {p.place}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
