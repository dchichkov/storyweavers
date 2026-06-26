#!/usr/bin/env python3
"""
storyworlds/worlds/knot_mystery_to_solve_friendship_foreshadowing_tall.py
========================================================================

A small storyworld about a stubborn knot, two friends, and a mystery that
unravels with a tall-tale smile.

Seed tale:
---
On a windy afternoon, two friends found a knot in a long rope stretched across
a little bridge. The knot blocked their way and looked as stubborn as a mule.
They noticed clues: a bright feather, a scrap of blue twine, and muddy little
prints. The clues led them to the barn cat, who had not tied the knot at all.
Instead, the cat had been chasing a fluttering ribbon, and the rope had caught
on a post by itself. The friends laughed, untied the knot together, and the
bridge was open again.

World model:
---
A knot has physical tightness and emotional stubbornness; clues increase
certainty; friendship increases shared resolve; solving the mystery clears
confusion and opens the blocked path.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    tied_to: Optional[str] = None
    blocked: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    id: str
    name: str
    place_line: str
    blocked_route: str
    clue_line: str


@dataclass
class Mystery:
    id: str
    source: str
    reason: str
    clue: str
    reveal: str
    place: str
    target: str
    twist: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    friend_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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


SETTINGS = {
    "bridge": Setting(
        id="bridge",
        name="the old rope bridge",
        place_line="the old rope bridge swayed over the creek like a tired yellow horse",
        blocked_route="the bridge",
        clue_line="A bright feather lay on the planks, and a scrap of blue twine clung to the rail.",
    ),
    "barn": Setting(
        id="barn",
        name="the red barn loft",
        place_line="the red barn loft stood above the hay like a storybook castle",
        blocked_route="the loft door",
        clue_line="A dusting of straw and a little milk smear lay beside the rope.",
    ),
    "orchard": Setting(
        id="orchard",
        name="the apple orchard gate",
        place_line="the orchard gate stood under the apple trees like a missing tooth in a grin",
        blocked_route="the gate",
        clue_line="A red apple peel and a muddy pawprint sat right by the knot.",
    ),
}

MYSTERIES = {
    "kite": Mystery(
        id="kite",
        source="kite string",
        reason="a gust twisted the string around the post",
        clue="blue twine",
        reveal="a fluttering kite had snagged the rope and tied the knot by accident",
        place="the sky above the bridge",
        target="kite",
        twist="the wind was the real trickster",
    ),
    "cat": Mystery(
        id="cat",
        source="barn cat",
        reason="the cat chased a ribbon and pulled the rope sideways",
        clue="milk smear",
        reveal="the barn cat had chased a ribbon, and the rope caught on a nail all by itself",
        place="the barn loft",
        target="cat",
        twist="the cat only looked guilty",
    ),
    "goat": Mystery(
        id="goat",
        source="goat's lead",
        reason="the goat rubbed against the gate and tightened the loop",
        clue="muddy pawprint",
        reveal="a curious goat had brushed the rope, and the loop cinched tight on its own",
        place="the orchard lane",
        target="goat",
        twist="the goat was innocent of the whole blame",
    ),
}

NAMES = ["Mabel", "Junie", "Benny", "Tessa", "Hank", "Rosie", "Walt", "Nell"]
FRIENDS = ["Pip", "Milo", "Dot", "Bea", "Ike", "Lark", "Nora", "Cleo"]


class KnotWorld(World):
    pass


def build_world(params: StoryParams) -> KnotWorld:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = KnotWorld(setting)
    hero = world.add(Entity(id=params.name, kind="character", type="child", meters={"resolve": 0.0}, memes={"curiosity": 0.0, "joy": 0.0}))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="child", meters={"resolve": 0.0}, memes={"curiosity": 0.0, "joy": 0.0}))
    knot = world.add(Entity(id="knot", type="knot", label="knot", phrase="a stubborn knot", meters={"tightness": 1.0}, memes={"mystery": 1.0}))
    route = world.add(Entity(id="route", type="route", label=setting.blocked_route, blocked=True))
    clue = world.add(Entity(id="clue", type="clue", label=mystery.clue, phrase=mystery.clue, meters={"notice": 0.0}))
    source = world.add(Entity(id="source", type=mystery.target, label=mystery.target, phrase=mystery.target))

    world.facts.update(
        hero=hero,
        friend=friend,
        knot=knot,
        route=route,
        clue=clue,
        source=source,
        mystery=mystery,
        setting=setting,
    )

    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    hero.meters["resolve"] += 1
    friend.meters["resolve"] += 1
    knot.meters["tightness"] += 1
    knot.memes["stubborn"] = 1.0
    return world


def _search_clues(world: KnotWorld) -> None:
    clue = world.get("clue")
    knot = world.get("knot")
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]

    clue.meters["notice"] += 1
    knot.memes["mystery"] += 1
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"{hero.id} and {friend.id} stared at {world.setting.name}, where {knot.phrase} blocked the way like a bull in a teacup."
    )
    world.say(
        f"They found a clue: {world.setting.clue_line} That little sign felt like a whisper from the mystery itself."
    )
    world.say(
        f'{hero.id} said, "This knot did not grow here. Something from {mystery.place} must have tugged it tight."'
    )


def _solve_mystery(world: KnotWorld) -> None:
    knot = world.get("knot")
    route = world.get("route")
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]

    hero.meters["resolve"] += 1
    friend.meters["resolve"] += 1
    knot.meters["tightness"] = 0.0
    knot.memes["mystery"] = 0.0
    route.blocked = False
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{friend.id} grinned and used a finger like a tiny crowbar. Together they worked the rope loose, slow as molasses in January."
    )
    world.say(
        f"They solved it at last: {mystery.reveal}. {mystery.twist.capitalize()}, and the knot was only an accident in a hurry."
    )
    world.say(
        f"Then {world.setting.blocked_route} swung open, and {hero.id} and {friend.id} skipped through side by side, laughing at their own tall-tale luck."
    )


def tell_story(world: KnotWorld) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]

    world.say(
        f"Once upon a wind-whipped afternoon, {hero.id} and {friend.id} set out to visit {world.setting.name}."
    )
    world.say(
        f"Everybody in those parts knew the place could keep a secret longer than a June day is bright, and today it had one."
    )
    world.para()
    _search_clues(world)
    world.say(
        f"The clue pointed to {mystery.target}, and that was the sort of hint that made both friends stand taller."
    )
    world.para()
    _solve_mystery(world)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            combos.append((sid, mid))
    return combos


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("source", mid, m.target))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M) :- setting(S), mystery(M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def generation_prompts(world: KnotWorld) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    return [
        f'Write a short tall-tale style story about {hero.id} and {friend.id} finding a knot and solving a mystery.',
        f"Tell a child-friendly friendship story where {hero.id} and {friend.id} notice clues and explain why the knot was there.",
        f'Write a mystery-to-solve story that uses the word "knot" and ends with two friends together again.',
    ]


def story_qa(world: KnotWorld) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who found the knot at {setting.name}?",
            answer=f"{hero.id} and {friend.id} found it together, and they treated the mystery like a big story waiting to be read.",
        ),
        QAItem(
            question=f"What clue helped the friends think about who made the knot?",
            answer=f"They noticed {mystery.clue}, which pointed them toward {mystery.target} and helped them keep solving.",
        ),
        QAItem(
            question=f"What was the mystery's answer in the end?",
            answer=f"The answer was that {mystery.reveal}. The knot was an accident, not a mean trick.",
        ),
        QAItem(
            question=f"How did the story end for the two friends?",
            answer=f"They opened {setting.blocked_route} and went on together, laughing and feeling braver because they solved it side by side.",
        ),
    ]


def world_knowledge_qa(world: KnotWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a knot?",
            answer="A knot is a tied-up place in a rope, string, or ribbon that can make it hard to pull apart until someone loosens it.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle where you do not know the answer yet, so you look for clues and think carefully.",
        ),
        QAItem(
            question="Why are clues helpful?",
            answer="Clues are helpful because they give little bits of information that can lead you toward the answer.",
        ),
        QAItem(
            question="Why is friendship important in a hard job?",
            answer="Friendship helps because friends can share ideas, share work, and cheer each other on when something is tricky.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: KnotWorld) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.blocked:
            bits.append("blocked=True")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="bridge", mystery="kite", name="Mabel", friend_name="Pip"),
    StoryParams(setting="barn", mystery="cat", name="Junie", friend_name="Bea"),
    StoryParams(setting="orchard", mystery="goat", name="Benny", friend_name="Nora"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIENDS if n != name])
    return StoryParams(setting=setting, mystery=mystery, name=name, friend_name=friend_name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale mystery storyworld about a knot, friendship, and clues."
    )
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend-name", choices=FRIENDS)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/mystery combos:\n")
        for s, m in combos:
            print(f"  {s:8} {m}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} and {p.friend_name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
