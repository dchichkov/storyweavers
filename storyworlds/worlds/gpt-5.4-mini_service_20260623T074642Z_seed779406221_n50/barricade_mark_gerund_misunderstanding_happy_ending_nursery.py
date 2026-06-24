#!/usr/bin/env python3
"""
storyworlds/worlds/barricade_mark_gerund_misunderstanding_happy_ending_nursery.py
=================================================================================

A small nursery-rhyme storyworld about a child, a barricade, a mysterious mark,
and a misunderstanding that becomes a happy ending.

Seed tale:
- A little child finds a barricade with a mark on it.
- The child misunderstands the mark and thinks the barricade is a mean or scary
  sign.
- A grown-up explains that the mark is just a kind note, a game mark, or a path
  mark depending on the setting.
- The child helps with the barricade and the story ends with relief and delight.

This world keeps the prose concrete and state-driven:
- physical meters track things like dust, wobble, and blocked_path
- emotional memes track worry, curiosity, relief, and joy
- a misunderstanding is only narrated when the child's fear and the mark's
  ambiguity actually rise enough in the world state
- a happy ending is only narrated when the clue is explained and the barricade
  becomes useful rather than scary

Style goal: nursery rhyme cadence, short sentences, gentle repetition.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class Setting:
    place: str
    indoor: bool = False
    weather: str = ""
    theme: str = "lane"


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    meaning: str
    kind: str
    makes: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Barrier:
    id: str
    label: str
    phrase: str
    purpose: str
    supports: set[str] = field(default_factory=set)
    can_be_moved_by_child: bool = False


@dataclass
class StoryParams:
    setting: str
    clue: str
    barrier: str
    name: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.mark_seen = False
        self.misunderstanding = False
        self.happy_ending = False

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        c.mark_seen = self.mark_seen
        c.misunderstanding = self.misunderstanding
        c.happy_ending = self.happy_ending
        return c


def _pronoun_type(kind: str, case: str = "subject") -> str:
    if kind in {"girl", "mother", "woman"}:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if kind in {"boy", "father", "man"}:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "it", "object": "it", "possessive": "its"}[case]


def _r_mark(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    clue = world.get("clue")
    if child.meme("curious") < THRESHOLD:
        return out
    if clue.meter("notice") < THRESHOLD:
        return out
    sig = ("mark_seen",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.mark_seen = True
    child.memes["worry"] = child.meme("worry") + 1
    out.append(f"The child saw the mark and wondered what it meant.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    child = world.get("child")
    clue = world.get("clue")
    if child.meme("worry") < THRESHOLD or clue.meter("notice") < THRESHOLD:
        return []
    sig = ("misunderstanding",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.misunderstanding = True
    child.memes["fear"] = child.meme("fear") + 1
    return ["__misunderstanding__"]


def _r_reassure(world: World) -> list[str]:
    child = world.get("child")
    grown = world.get("parent")
    clue = world.get("clue")
    barrier = world.get("barrier")
    if not world.misunderstanding:
        return []
    sig = ("reassure",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] = max(0.0, child.meme("fear") - 1)
    child.memes["relief"] = child.meme("relief") + 1
    world.happy_ending = True
    return [f"{grown.label} smiled and explained the mark on the {barrier.label}."]


RULES = [_r_mark, _r_misunderstanding, _r_reassure]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                out.extend([s for s in lines if s != "__misunderstanding__"])
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_world(setting: Setting, clue: Clue, barrier: Barrier, name: str, parent: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id="child",
        kind="character",
        type="girl" if name in GIRL_NAMES else "boy",
        label=name,
        meters={"tiny": 1},
        memes={"curious": 1, "joy": 1},
    ))
    parent_e = world.add(Entity(
        id="parent",
        kind="character",
        type=parent,
        label=parent,
        memes={"calm": 1, "love": 1},
    ))
    clue_e = world.add(Entity(
        id="clue",
        type=clue.kind,
        label=clue.label,
        phrase=clue.phrase,
        owner="child",
        meters={"notice": 1, clue.makes: 1},
        memes={"mystery": 1},
    ))
    barrier_e = world.add(Entity(
        id="barrier",
        type="barricade",
        label=barrier.label,
        phrase=barrier.phrase,
        owner="parent",
        meters={"wobble": 1, "blocked_path": 1},
        memes={"importance": 1},
    ))

    world.say(f"Little {name} went out one day, in {setting.place} bright and gay.")
    world.say(f"There stood {barrier.phrase}, and there was {clue.phrase}.")
    world.say(f"{name} looked, and blinked, and thought the mark might mean a scary thing.")
    world.para()
    clue_e.meters["notice"] += 1
    propagate(world, narrate=True)
    world.say(f"{name} asked, “What is this mark upon the barricade?”")
    world.say(f"{parent} answered, “It is only a guide, a helpful sign, not a frown to make you hide.”")
    world.para()
    world.say(f"So {name} helped with the barricade, with tiny hands and careful cheer.")
    barrier_e.meters["wobble"] = 0
    barrier_e.meters["fixed"] = 1
    child.memes["joy"] += 1
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1)
    child.memes["relief"] = child.meme("relief") + 1
    world.happy_ending = True
    world.say(f"The mark was friendly after all, and the path was safe and clear.")
    world.say(f"{name} skipped home in the evening light, and everyone felt light.")
    world.facts.update(
        child=child,
        parent=parent_e,
        clue=clue_e,
        barrier=barrier_e,
        setting=setting,
        clue_def=clue,
        barrier_def=barrier,
    )
    return world


SETTINGS = {
    "lane": Setting(place="the little lane", indoor=False, weather="soft", theme="lane"),
    "yard": Setting(place="the sunny yard", indoor=False, weather="warm", theme="yard"),
    "bridge": Setting(place="the narrow bridge", indoor=False, weather="breezy", theme="bridge"),
}

CLUES = {
    "tape_mark": Clue(
        id="tape_mark",
        label="tape mark",
        phrase="a bright tape mark on the barricade",
        meaning="a careful guide",
        kind="mark",
        makes="sticky",
        tags={"mark", "guide"},
    ),
    "chalk_mark": Clue(
        id="chalk_mark",
        label="chalk mark",
        phrase="a chalk mark on the barricade",
        meaning="a path note",
        kind="mark",
        makes="dusty",
        tags={"mark", "path"},
    ),
    "flower_mark": Clue(
        id="flower_mark",
        label="flower mark",
        phrase="a flower-shaped mark on the barricade",
        meaning="a friendly sign",
        kind="mark",
        makes="pretty",
        tags={"mark", "friendly"},
    ),
}

BARRIERS = {
    "barricade": Barrier(
        id="barricade",
        label="barricade",
        phrase="a little barricade",
        purpose="to keep the path safe",
        supports={"mark", "guide", "path"},
        can_be_moved_by_child=False,
    ),
    "gate": Barrier(
        id="gate",
        label="gate",
        phrase="a tiny gate",
        purpose="to keep the garden neat",
        supports={"mark", "guide", "friendly"},
        can_be_moved_by_child=True,
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ruby", "Ada"]
BOY_NAMES = ["Tom", "Finn", "Ben", "Leo", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, b) for s in SETTINGS for c in CLUES for b in BARRIERS]


@dataclass
class StoryParams:
    setting: str
    clue: str
    barrier: str
    name: str
    parent: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme style story about {f["child"].label} and a {f["barrier_def"].label} with a {f["clue_def"].label}.',
        f"Tell a gentle story in which a child misunderstands a mark on a barricade, then learns it is friendly.",
        f"Write a happy ending story for a child in {f['setting'].place} where a marked barricade turns out to be helpful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    clue = f["clue"]
    barrier = f["barrier"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who found the {clue.label} near the {barrier.label}?",
            answer=f"{child.label} found it in {setting.place}.",
        ),
        QAItem(
            question=f"What did {child.label} think the mark meant at first?",
            answer=f"{child.label} thought it might mean something scary or unfriendly, which was a misunderstanding.",
        ),
        QAItem(
            question=f"Who explained the mark on the {barrier.label}?",
            answer=f"{parent.label} explained that the mark was only a helpful sign.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The misunderstanding faded, the barricade became useful, and the ending was happy and calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a barricade?", answer="A barricade is a barrier that helps keep a path or place safe."),
        QAItem(question="What is a mark?", answer="A mark is a sign, spot, or line that can show a message or guide someone."),
        QAItem(question="What is a misunderstanding?", answer="A misunderstanding happens when someone thinks something means one thing, but it really means another."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for bid in BARRIERS:
        lines.append(asp.fact("barrier", bid))
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("has_place", sid, s.place))
    for cid, c in CLUES.items():
        lines.append(asp.fact("meaning", cid, c.meaning))
        lines.append(asp.fact("mark_kind", cid, c.kind))
    for bid, b in BARRIERS.items():
        lines.append(asp.fact("supports", bid, "mark"))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S,C,B) :- setting(S), clue(C), barrier(B).
misunderstanding(C) :- clue(C), mark_kind(C, mark).
happy_ending(S,C,B) :- compatible(S,C,B), misunderstanding(C), supports(B, mark).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery rhyme storyworld: a barricade, a mark, a misunderstanding, a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--barrier", choices=BARRIERS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father", "grown-up"])
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
    choice = rng.choice(combos)
    setting = args.setting or choice[0]
    clue = args.clue or choice[1]
    barrier = args.barrier or choice[2]
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father", "grown-up"])
    return StoryParams(setting=setting, clue=clue, barrier=barrier, name=name, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(SETTINGS[params.setting], CLUES[params.clue], BARRIERS[params.barrier], params.name, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"misunderstanding={world.misunderstanding} happy_ending={world.happy_ending}")
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


CURATED = [
    StoryParams(setting="lane", clue="tape_mark", barrier="barricade", name="Mia", parent="mother"),
    StoryParams(setting="yard", clue="chalk_mark", barrier="gate", name="Leo", parent="father"),
    StoryParams(setting="bridge", clue="flower_mark", barrier="barricade", name="Nora", parent="grown-up"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/3."))
        vals = sorted(set(asp.atoms(model, "compatible")))
        for t in vals:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
