#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cashew_yankee_swiss_flashback_rhyme_detective_story.py
======================================================================================

A standalone storyworld for a tiny Detective Story domain with a playful
mystery: a child detective follows clues involving a cashew, a yankee, and a
swiss cheese, then uses a flashback and a rhyme to solve the case.

The model keeps the action small and concrete:
- a missing snack is investigated,
- a clue points to a visitor from a baseball game,
- a flashback reveals who hid the snack,
- a rhyme helps the detective remember the hiding place,
- the ending proves what changed by showing the snack returned and the case
  closed.

The world is intentionally narrow and constraint-checked so the prose stays
clear, causal, and child-facing.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/cashew_yankee_swiss_flashback_rhyme_detective_story.py
    python storyworlds/worlds/gpt-5.4-mini/cashew_yankee_swiss_flashback_rhyme_detective_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/cashew_yankee_swiss_flashback_rhyme_detective_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/cashew_yankee_swiss_flashback_rhyme_detective_story.py --verify
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class ItemSpec:
    id: str
    label: str
    phrase: str
    kind: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class ClueSpec:
    id: str
    label: str
    phrase: str
    reveals: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class ResponseSpec:
    id: str
    sense: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_nervous(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["missing"] < THRESHOLD:
            continue
        sig = ("nervous", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__narrate_missing__")
    return out


def _r_flashback(world: World) -> list[str]:
    out = []
    if world.facts.get("flashback_done"):
        return out
    if world.entities["Snack"].meters["missing"] < THRESHOLD:
        return out
    world.facts["flashback_done"] = True
    detective = world.get("Detective")
    detective.memes["memory"] += 1
    out.append("__flashback__")
    return out


CAUSAL_RULES = [Rule("nervous", _r_nervous), Rule("flashback", _r_flashback)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(p for p in produced if not p.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def have_missing(world: World) -> None:
    world.get("Snack").meters["missing"] += 1
    world.get("Snack").meters["hidden"] += 1
    propagate(world, narrate=False)


def predict_conflict(world: World) -> bool:
    sim = world.copy()
    have_missing(sim)
    return sim.get("Detective").memes["worry"] >= THRESHOLD


def setup(world: World, detective: Entity, friend: Entity, owner: Entity) -> None:
    detective.memes["curious"] += 1
    friend.memes["kind"] += 1
    owner.memes["busy"] += 1
    world.say(
        f"On a bright afternoon, {detective.id} was helping {friend.id} solve a small mystery "
        f"in the kitchen. The case involved a cashew, a yankee, and a swiss cheese sandwich."
    )
    world.say(
        f"{owner.label_word.capitalize()} had left a snack on the table, but by the time "
        f"{detective.id} looked back, it was gone."
    )


def clue_scene(world: World, detective: Entity, clue: ClueSpec) -> None:
    world.say(
        f"{detective.id} spotted {clue.phrase} near the door and wrote it down in {detective.pronoun('possessive')} little notebook."
    )
    world.say(
        f'"That clue might reveal who moved the snack," {detective.id} whispered.'
    )


def warn(world: World, detective: Entity, friend: Entity) -> None:
    if predict_conflict(world):
        world.say(
            f'{friend.id} bit {friend.pronoun("possessive")} lip. "If the snack is really missing, '
            f'we should look carefully instead of guessing," {friend.pronoun()} said.'
        )


def flashback(world: World, detective: Entity, owner: Entity) -> None:
    world.say(
        f"Then {detective.id} had a flashback. Yesterday, {owner.id} had heard a cheerful rhyme "
        f"about a cashew in a shoe, a yankee by the sink, and swiss on a dish."
    )
    world.say(
        f"{detective.id} remembered {owner.id} laughing and saying the rhyme would help them remember where to hide a treat."
    )


def solve(world: World, detective: Entity, owner: Entity, snack: ItemSpec) -> None:
    world.get("Snack").meters["missing"] = 0.0
    world.get("Snack").meters["found"] += 1
    detective.memes["pride"] += 1
    world.say(
        f'{detective.id} followed the rhyme to the blue shoe by the bench, and there was the {snack.label}.'
    )
    world.say(
        f"{owner.label_word.capitalize()} smiled and thanked {detective.id} for solving the case so gently."
    )
    world.say(
        f'In the end, the {snack.label} was back on the table, the notebook was closed, and the mystery was done.'
    )


def tell() -> World:
    world = World()
    detective = world.add(Entity("Detective", kind="character", type="girl", role="detective"))
    friend = world.add(Entity("Friend", kind="character", type="boy", role="helper"))
    owner = world.add(Entity("Mom", kind="character", type="mother", role="owner", label="the mom"))
    snack = world.add(Entity("Snack", kind="thing", type="thing", label="cashew snack"))

    clue = ClueSpec("shoe", "blue shoe", "a blue shoe by the bench", "hidden place", {"shoe", "blue"})
    item = ItemSpec("cashew", "cashew snack", "a small cashew snack", "snack", {"cashew", "snack"})
    world.facts["clue"] = clue
    world.facts["item"] = item
    world.facts["owner"] = owner
    world.facts["detective"] = detective
    world.facts["friend"] = friend

    setup(world, detective, friend, owner)
    world.para()
    have_missing(world)
    clue_scene(world, detective, clue)
    warn(world, detective, friend)
    world.para()
    flashback(world, detective, owner)
    solve(world, detective, owner, item)
    world.facts["outcome"] = "solved"
    return world


THEME_NOTES = {
    "cashew": "A tiny snack with a hard shell.",
    "yankee": "A word for a baseball fan or player from the northeast.",
    "swiss": "A kind of cheese with holes in it.",
    "flashback": "A story moment that jumps back to an earlier time.",
    "rhyme": "Words that sound alike at the end.",
    "detective": "Someone who looks for clues and solves mysteries.",
}

KNOWLEDGE_ORDER = ["detective", "flashback", "rhyme", "cashew", "yankee", "swiss"]


@dataclass
@dataclass
class StoryParams:
    seed: Optional[int] = None
    detective_name: str = "Mina"
    helper_name: str = "Ben"
    owner_name: str = "Mom"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str]]:
    return [("detective",)]


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("topic", "cashew"),
        asp.fact("topic", "yankee"),
        asp.fact("topic", "swiss"),
        asp.fact("feature", "flashback"),
        asp.fact("feature", "rhyme"),
        asp.fact("style", "detective"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(detective) :- topic(cashew), topic(yankee), topic(swiss),
                          feature(flashback), feature(rhyme), style(detective).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH:", sorted(py ^ cl))
    try:
        sample = generate(StoryParams())
        assert sample.story
        print("OK: generate() smoke test produced a story.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short detective story for a young child that includes the words cashew, yankee, and swiss.",
        "Tell a mystery with a flashback clue and a rhyme that helps solve where the missing snack was hidden.",
        "Write a gentle detective story where a child finds a cashew snack by remembering a rhyme from the past.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What was missing?",
         "A cashew snack was missing from the table, so the detective had to look for clues."),
        ("What helped solve the mystery?",
         "A flashback helped the detective remember a rhyme from yesterday. The rhyme led straight to the hiding place."),
        ("How did the story end?",
         "The snack was found and put back on the table, and the mystery was solved calmly."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [(f"What is {k}?", v) for k, v in THEME_NOTES.items()]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [StoryParams()]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with cashew, yankee, swiss, flashback, and rhyme.")
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
    return StoryParams(seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell()
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid combos:", asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
