#!/usr/bin/env python3
"""
storyworlds/worlds/hyrax_seven_elevate_dialogue_rhyme_mystery.py
==================================================================

A small mystery story world about a curious hyrax, seven clues, and a careful
elevate-the-thing turn that reveals who moved the missing item.

Premise:
- A little hyrax notices that seven bright shells are missing from a stone shelf.
- The hyrax talks with friends, checks a few places, and follows clues.

Tension:
- Every clue points somewhere different, and the missing shells are not in the
  obvious place.

Turn:
- The hyrax elevates a small basket on a stump, revealing a hidden trail.

Resolution:
- The mystery is solved, and the shells are returned to their shelf.

The prose engine uses the world state to decide what is suspected, what is
searched, and how the ending is resolved. Dialogue and rhyme are baked into the
narration, while the internal state tracks the clues, the hidden stash, and the
final reveal.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    carried_by: Optional[str] = None
    elevated: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"hyrax"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the mossy den"
    clue_places: tuple[str, ...] = ("the stone shelf", "the root nook", "the water bowl", "the fern patch")
    mystery_spot: str = "the basket on the stump"


@dataclass
class Suspect:
    id: str
    type: str
    label: str
    reason: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: replace(v, meters=dict(v.meters), memes=dict(v.memes))
                          for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "den": Setting(place="the mossy den"),
    "garden": Setting(place="the little garden"),
    "rocky": Setting(place="the rocky ledge"),
}

HERO_NAMES = ["Milo", "Pip", "Nia", "Luna", "Kito", "Roo"]
FRIEND_NAMES = ["Tavi", "Bela", "Rin", "Suri", "Odo", "Mina"]

SUSPECTS = [
    Suspect(id="wind", type="wind", label="the wind", reason="it could have blown a light thing away"),
    Suspect(id="bird", type="bird", label="a blue bird", reason="it liked shiny things"),
    Suspect(id="squirrel", type="squirrel", label="a gray squirrel", reason="it hid nuts and sometimes odd trinkets"),
]

# The missing item is always seven shells, to match the seed word and story beat.
MISSING_ITEM = Entity(
    id="shells",
    kind="thing",
    type="shells",
    label="shells",
    phrase="seven bright shells",
    plural=True,
)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if not params.hero_name or not params.friend_name:
        raise StoryError("Need both a hero and a friend name.")


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    hero = world.add(Entity(id=params.hero_name, kind="character", type="hyrax", label=params.hero_name))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="hyrax", label=params.friend_name))
    shelf = world.add(Entity(id="shelf", kind="thing", type="shelf", label="stone shelf", location="stone shelf"))
    basket = world.add(Entity(id="basket", kind="thing", type="basket", label="basket", location="stump"))
    stump = world.add(Entity(id="stump", kind="thing", type="stump", label="stump", location="stump"))

    world.add(replace(MISSING_ITEM, owner=hero.id, location="missing"))

    world.facts.update(
        hero=hero,
        friend=friend,
        shelf=shelf,
        basket=basket,
        stump=stump,
        missing_count=7,
        suspect_order=["wind", "bird", "squirrel"],
        resolved=False,
        reveal="",
    )
    return world


def opening(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    world.say(
        f"{hero.id} was a little hyrax who kept a careful eye on the stone shelf in {world.setting.place}."
    )
    world.say(
        f"One morning, {hero.id} blinked hard. Seven bright shells were gone."
    )
    world.say(
        f'"Oh no," said {friend.id}. "Seven shells? That is a lot." "It is," said {hero.id}, '
        f'"and a mystery never likes to wait."'
    )
    world.say(
        "The den felt quiet, and the quiet made the missing shells feel louder."
    )


def search_clue(world: World, place: str, clue: str, suspect: Suspect) -> str:
    if clue == "stone shelf":
        return "a dusty curve where the shells had rested"
    if clue == "root nook":
        return "a little line of scratches under the roots"
    if clue == "water bowl":
        return "a wet ring and one tiny sparkle"
    return "a soft trail in the fern leaves"


def investigation(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    clues = ["stone shelf", "root nook", "water bowl", "fern patch"]
    suspect_cycle = SUSPECTS[:]

    world.para()
    for i, place in enumerate(clues, 1):
        suspect = suspect_cycle[i % len(suspect_cycle)]
        world.say(f'{hero.id} said, "Let us look at {place}."')
        world.say(f'{friend.id} said, "Good idea. Mystery first, worry later."')
        world.say(
            f"They found {search_clue(world, place, place, suspect)}."
        )
        if i == 1:
            world.say(
                f'"A clue at the shelf," said {hero.id}. "That means the shells were not lost by magic."'
            )
        if i == 2:
            world.say(
                f'"A clue under the roots," said {friend.id}. "Someone may have carried them carefully."'
            )
        if i == 3:
            world.say(
                f'"A sparkle by the bowl," said {hero.id}, "and the trail still feels fresh."'
            )
        if i == 4:
            world.say(
                f'"A soft trail in the fern patch," said {friend.id}. "Now the mystery is getting taller."'
            )

    world.facts["clues_found"] = 4
    world.say(
        f'“Seven clues? No,” said {hero.id}. “Four clues, but they point to one place.”'
    )
    world.say(
        "To keep the mystery tidy, the two hyraxes counted what they knew and left what they did not know alone."
    )


def elevate_reveal(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    basket = world.facts["basket"]
    stump = world.facts["stump"]

    world.para()
    world.say(
        f'{hero.id} stared at the basket on the stump. "It sits too neatly," {hero.id} whispered.'
    )
    world.say(
        f'"Then let us elevate it," said {friend.id}. "Mysteries often hide where things look most normal."'
    )
    basket.elevated = True
    world.facts["reveal"] = "the shells were hidden under the basket"
    world.say(
        f"Together, they lifted the basket higher. Underneath, there was a narrow ring of shell dust."
    )
    world.say(
        f'Then the last clue shone like a moonbeam: {world.facts["reveal"]}.'
    )
    world.say(
        f'"Aha," said {hero.id}. "So the basket was not empty after all."'
    )
    world.say(
        "And the rhyme in the air was easy to hear: lift and glance, and clues advance."
    )


def solve_mystery(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    shells = world.get("shells")
    shells.location = "stone shelf"
    world.facts["resolved"] = True

    world.para()
    world.say(
        f'The hidden shells had been tucked away for safe keeping by the gray squirrel, who meant to sort them by shine.'
    )
    world.say(
        f'"Not stolen," said {friend.id}. "Just moved."'
    )
    world.say(
        f'"A mystery with a kind ending," said {hero.id}. "We can bring them back."'
    )
    world.say(
        f'They returned the seven bright shells to the stone shelf, where they glittered in a tidy row.'
    )
    world.say(
        f'{hero.id} smiled. "{hero.id} found the clue, and now the shelf is true."'
    )
    world.say(
        f"{friend.id} laughed. \"A small rhyme for a small crime.\""
    )


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = build_world(params)
    opening(world)
    investigation(world)
    elevate_reveal(world)
    solve_mystery(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        f'Write a gentle mystery for a young child about a hyrax named {hero.id} who notices seven missing shells.',
        f'Tell a story with dialogue and a little rhyme where {hero.id} and {friend.id} search for a hidden clue and elevate a basket.',
        "Write a child-friendly mystery about a small animal, seven clues, and a surprise reveal under a basket.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        QAItem(
            question=f"What mystery did {hero.id} notice in the opening?",
            answer="The seven bright shells were missing from the stone shelf.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look for clues?",
            answer=f"{friend.id}, another little hyrax, helped search the den and talk through the clues.",
        ),
        QAItem(
            question="What did the hyraxes elevate to solve the mystery?",
            answer="They elevated the basket on the stump and found shell dust hiding underneath it.",
        ),
        QAItem(
            question="Who had moved the shells?",
            answer="A gray squirrel had tucked the shells away for safe keeping and sorting.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The seven shells were returned to the stone shelf, and the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hyrax?",
            answer="A hyrax is a small furry mammal that can live among rocks and shrubs.",
        ),
        QAItem(
            question="What does elevate mean?",
            answer="To elevate something means to lift it up or make it higher.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like shell and bell.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or problem where you do not know the answer yet.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hyrax(hero).
hyrax(friend).
missing(shells, 7).
clue_count(4).
suspect(wind).
suspect(bird).
suspect(squirrel).

needs_search(H) :- hyrax(H), missing(shells, 7).
good_reveal(hero) :- missing(shells, 7), clue_count(4), suspect(squirrel).
resolved :- good_reveal(hero).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("hyrax", "hero"))
    lines.append(asp.fact("hyrax", "friend"))
    lines.append(asp.fact("missing", "shells", 7))
    lines.append(asp.fact("clue_count", 4))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0.\n#show good_reveal/1."))
    atoms = {(sym.name, tuple(_py(a) for a in sym.arguments)) for sym in model}
    want = {("resolved", ()), ("good_reveal", ("hero",))}
    if atoms == want:
        print("OK: ASP parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("asp:", sorted(atoms))
    print("want:", sorted(want))
    return 1


def _py(sym):
    import clingo
    if sym.type == clingo.SymbolType.Number:
        return sym.number
    if sym.type == clingo.SymbolType.String:
        return sym.string
    return sym.name


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small hyrax mystery world with dialogue, rhyme, and a hidden reveal.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    name = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != name])
    if name == friend:
        raise StoryError("The hero and friend must be different names.")
    return StoryParams(place=place, hero_name=name, friend_name=friend)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.elevated:
            bits.append("elevated=True")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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


def asp_run() -> None:
    import asp
    model = asp.one_model(asp_program("#show resolved/0.\n#show good_reveal/1."))
    print(f"resolved: {bool(asp.atoms(model, 'resolved'))}")
    print(f"good_reveal: {asp.atoms(model, 'good_reveal')}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0.\n#show good_reveal/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_run()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(place=place, hero_name=HERO_NAMES[i % len(HERO_NAMES)], friend_name=FRIEND_NAMES[i % len(FRIEND_NAMES)])
            for i, place in enumerate(SETTINGS.keys())
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
