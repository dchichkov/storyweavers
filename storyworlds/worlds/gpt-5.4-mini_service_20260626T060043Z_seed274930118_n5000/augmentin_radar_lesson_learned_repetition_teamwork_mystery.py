#!/usr/bin/env python3
"""
storyworlds/worlds/augmentin_radar_lesson_learned_repetition_teamwork_mystery.py
=================================================================================

A small storyworld about a child, a missing thing, a clue-hunt, and a tidy
lesson learned. The seed words are woven into the premise: augmentin and radar.

Premise:
- A child needs their augmentin.
- The bottle goes missing in a small home setting.
- Someone uses a radar toy or a radar app to search for it.
- The search repeats a few times, but teamwork turns the mystery into a solved
  little story.
- The ending leaves the lesson learned: keep medicine in one place.

This world is intentionally narrow. It does not try to be broad; it tries to be
plausible, clear, and story-shaped.
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
# World constants
# ---------------------------------------------------------------------------

LOCATIONS = {
    "kitchen": "the kitchen",
    "bedroom": "the bedroom",
    "hall": "the hall",
    "living_room": "the living room",
    "bathroom": "the bathroom",
}

HELPERS = ["mother", "father", "grandparent", "older sibling"]

NAMES = {
    "girl": ["Mia", "Nora", "Zoe", "Lily", "Ava", "Elsa", "Ruby"],
    "boy": ["Leo", "Finn", "Max", "Owen", "Noah", "Theo", "Jack"],
}

TARGET_ITEMS = [
    "bottle of augmentin",
    "medicine bottle",
    "pink medicine bottle",
    "small white bottle of augmentin",
]

RADAR_TOOLS = [
    "a toy radar",
    "a phone radar app",
    "a little radar screen",
]

CLUES = [
    "a beep near the couch",
    "a soft glow under the table",
    "a tiny ping by the chair",
    "a green blip near the sink",
]

LESSONS = [
    "keep medicine in one safe spot",
    "put medicine back after using it",
    "ask for help right away when something important is missing",
]

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden_in: str = ""
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "sister", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "brother", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    cozy: bool = True
    hiding_spots: tuple[str, ...] = ("couch", "table", "chair", "sink", "basket")


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    helper_type: str
    target_item: str
    radar_tool: str
    clue_count: int
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.search_rounds: int = 0

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


# ---------------------------------------------------------------------------
# Narrative rules
# ---------------------------------------------------------------------------

def _r_search_progress(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    item = world.get("target")
    helper = world.get("helper")
    if item.found:
        return out
    if child.memes.get("searching", 0.0) < THRESHOLD:
        return out
    world.search_rounds += 1
    sig = ("search", world.search_rounds)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["distance"] = max(0.0, item.meters.get("distance", 1.0) - 0.4)
    out.append(f"They heard the radar beep again, and the clue pointed them a little closer.")
    if world.search_rounds >= 2:
        helper.memes["hope"] = helper.memes.get("hope", 0.0) + 1
        out.append(f"{helper.label.capitalize()} and the child kept going together.")
    return out


def _r_found_item(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("target")
    if item.found:
        return out
    if item.meters.get("distance", 1.0) > 0.0:
        return out
    sig = ("found", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.found = True
    out.append("__found__")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("target")
    child = world.get("child")
    helper = world.get("helper")
    if not item.found:
        return out
    sig = ("lesson", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1
    out.append("Lesson learned: important medicine should stay in one safe spot.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_search_progress, _r_found_item, _r_lesson):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__found__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Core world actions
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    setting = Setting(place=LOCATIONS[params.setting])
    world = World(setting)

    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_gender,
        label=params.child_name,
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_type,
        label=f"the {params.helper_type}",
    ))
    item = world.add(Entity(
        id="target",
        kind="thing",
        type="medicine",
        label="augmentin",
        phrase=params.target_item,
        hidden_in=random.choice(setting.hiding_spots),
        found=False,
    ))
    tool = world.add(Entity(
        id="radar",
        kind="thing",
        type="tool",
        label="radar",
        phrase=params.radar_tool,
    ))

    world.facts.update(
        child=child,
        helper=helper,
        item=item,
        tool=tool,
        clue_count=params.clue_count,
        setting=setting,
    )
    return world


def open_story(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    item = world.get("target")
    tool = world.get("radar")

    world.say(
        f"{child.label} was a little {child.type} who needed augmentin after getting sick."
    )
    world.say(
        f"One day, the medicine went missing, and {helper.label} noticed the room had turned into a mystery."
    )
    world.para()
    world.say(
        f"They picked up {tool.phrase} and began to search {world.setting.place} together."
    )
    world.say(
        f"{child.label} listened closely, because the radar made a tiny beep that sounded like a clue."
    )
    child.memes["searching"] = 1.0
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0.0) + 1
    item.meters["distance"] = 1.0


def repeat_search(world: World, clue_count: int) -> None:
    child = world.get("child")
    helper = world.get("helper")
    item = world.get("target")

    world.para()
    for i in range(clue_count):
        if item.found:
            break
        world.say(
            f"They checked {CLUES[i % len(CLUES)]}, then listened for the radar beep again."
        )
        child.memes["patience"] = child.memes.get("patience", 0.0) + 1
        helper.memes["teamwork"] = helper.memes.get("teamwork", 0.0) + 1
        child.memes["searching"] = 1.0
        propagate(world, narrate=True)


def resolve_story(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    item = world.get("target")

    if not item.found:
        item.meters["distance"] = 0.0
        propagate(world, narrate=True)

    world.para()
    if item.found:
        world.say(
            f"At last, they found the augmentin tucked away in {item.hidden_in}."
        )
        world.say(
            f"{child.label} smiled, and {helper.label} smiled too, because teamwork had solved the mystery."
        )
        world.say(
            f"After that, they put the medicine in one safe spot, and the radar went back on the shelf."
        )
        child.memes["joy"] = child.memes.get("joy", 0.0) + 1
        helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    else:
        world.say("The mystery stayed unsolved, which should not happen in this storyworld.")


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    open_story(world)
    repeat_search(world, params.clue_count)
    resolve_story(world)
    return world


# ---------------------------------------------------------------------------
# Registries and validation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting in LOCATIONS:
        for gender in ("girl", "boy"):
            for target in TARGET_ITEMS:
                combos.append((setting, gender, target))
    return combos


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    return [
        "Write a short mystery story for a small child about a missing medicine bottle and a helpful radar.",
        f"Tell a gentle mystery where {child.label} and {helper.label} use teamwork and repeat their search until the clue is solved.",
        "Write a child-friendly story that includes the words augmentin and radar, and ends with a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item = f["item"]
    tool = f["tool"]
    qa = [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"The missing thing was {item.phrase}, which was the child's augmentin.",
        ),
        QAItem(
            question=f"What did {child.label} and {helper.label} use to search?",
            answer=f"They used {tool.phrase} to help solve the mystery.",
        ),
        QAItem(
            question=f"What helped them keep going when the search took more than one try?",
            answer="Repetition and teamwork helped them keep checking clues until they found the medicine.",
        ),
    ]
    qa.append(
        QAItem(
            question="What lesson did they learn at the end?",
            answer="They learned to keep medicine in one safe spot so it would be easy to find later.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is augmentin?",
            answer="Augmentin is a medicine that doctors may give to help treat certain infections.",
        ),
        QAItem(
            question="What is a radar?",
            answer="A radar is a tool that helps notice where something is by sending out signals and showing a return signal.",
        ),
        QAItem(
            question="Why can teamwork help solve a mystery?",
            answer="Teamwork helps because different people can look, listen, and think together to find clues faster.",
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
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid(setting, gender, target) :- setting_fact(setting), gender_fact(gender), target_fact(target).
needs_teamwork(child, helper) :- child_fact(child), helper_fact(helper).
mystery_story(setting, gender, target) :- valid(setting, gender, target).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in LOCATIONS:
        lines.append(asp.fact("setting_fact", s))
    for g in ("girl", "boy"):
        lines.append(asp.fact("gender_fact", g))
    for t in TARGET_ITEMS:
        lines.append(asp.fact("target_fact", t))
    for h in HELPERS:
        lines.append(asp.fact("helper_fact", h))
    lines.append(asp.fact("child_fact", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly mystery world about augmentin and radar.")
    ap.add_argument("--setting", choices=LOCATIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", dest="helper_type", choices=HELPERS)
    ap.add_argument("--target", choices=TARGET_ITEMS)
    ap.add_argument("--radar", choices=RADAR_TOOLS)
    ap.add_argument("--clues", type=int, default=3)
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
    setting = args.setting or rng.choice(list(LOCATIONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(HELPERS)
    target_item = args.target or rng.choice(TARGET_ITEMS)
    radar_tool = args.radar or rng.choice(RADAR_TOOLS)
    clue_count = args.clues if args.clues > 0 else 3
    if clue_count < 1:
        raise StoryError("The mystery needs at least one clue.")
    name = args.name or rng.choice(NAMES[gender])
    return StoryParams(
        setting=setting,
        child_name=name,
        child_gender=gender,
        helper_type=helper_type,
        target_item=target_item,
        radar_tool=radar_tool,
        clue_count=clue_count,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.found:
            bits.append("found=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  search rounds: {world.search_rounds}")
    lines.append(f"  fired rules: {sorted({n for (n, *_) in world.fired})}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for setting in LOCATIONS:
            for gender in ("girl", "boy"):
                params = StoryParams(
                    setting=setting,
                    child_name=NAMES[gender][0],
                    child_gender=gender,
                    helper_type=HELPERS[0],
                    target_item=TARGET_ITEMS[0],
                    radar_tool=RADAR_TOOLS[0],
                    clue_count=3,
                )
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
