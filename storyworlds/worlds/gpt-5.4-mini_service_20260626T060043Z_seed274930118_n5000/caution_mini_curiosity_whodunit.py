#!/usr/bin/env python3
"""
storyworlds/worlds/caution_mini_curiosity_whodunit.py
======================================================

A tiny whodunit storyworld built around caution, a mini mystery, and Curiosity.

Premise:
- Curiosity is a careful little detective.
- Something small goes missing in a miniature setting.
- The story turns on noticing clues instead of rushing.

The domain is intentionally small and constraint-driven:
- a single investigator with emotional state
- a handful of suspects, each with a motive and a clue trail
- a reasonableness gate that only allows cases with a solvable, non-magical answer

The style aims at a child-facing whodunit: concrete clues, a cautious search,
a clear reveal, and an ending image proving what changed.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"placed": 0.0, "missing": 0.0, "found": 0.0}
        if not self.memes:
            self.memes = {"caution": 0.0, "curiosity": 0.0, "worry": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    description: str
    hides: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing_item: str
    item_phrase: str
    item_location: str
    culprit: str
    culprit_reason: str
    clue: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str = "Curiosity"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "mini_library": Setting(
        place="the mini library",
        description="tiny shelves lined the walls, and every book had a careful place",
        hides={"dust", "behind-book", "under-rug"},
    ),
    "mini_workshop": Setting(
        place="the mini workshop",
        description="small jars, small screws, and small tools sat in tidy rows",
        hides={"under-bench", "inside-box", "behind-board"},
    ),
    "mini_garden": Setting(
        place="the mini garden",
        description="little pots, pebbles, and a narrow path made a neat little maze",
        hides={"under-pot", "behind-pot", "under-leaf"},
    ),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        missing_item="bell",
        item_phrase="a tiny brass bell",
        item_location="on the hook by the door",
        culprit="mouse",
        culprit_reason="it wanted the shiny bell for its nest",
        clue="a trail of soft crumbs",
        reveal="the mouse had moved the bell into a nest of paper bits and ribbon",
        tags={"small", "shiny", "crumbs"},
    ),
    "spoon": Mystery(
        id="spoon",
        missing_item="spoon",
        item_phrase="a little silver spoon",
        item_location="beside the tea set",
        culprit="squirrel",
        culprit_reason="it was using the spoon to scoop seeds",
        clue="tiny seed shells under a chair",
        reveal="the squirrel had carried the spoon to a seed jar and left it there",
        tags={"silver", "seeds"},
    ),
    "key": Mystery(
        id="key",
        missing_item="key",
        item_phrase="a small gold key",
        item_location="on the blue ribbon",
        culprit="bird",
        culprit_reason="it liked shiny things and tucked the key into a nest",
        clue="one blue feather on the windowsill",
        reveal="the bird had hidden the key in a nest made from ribbon and straw",
        tags={"gold", "feather", "ribbon"},
    ),
}

GHOST_WORDS = ["caution", "mini", "Curiosity"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s_name, setting in SETTINGS.items():
        for m_name, mystery in MYSTERIES.items():
            if s_name == "mini_library" and mystery.id == "key":
                combos.append((s_name, m_name))
            elif s_name == "mini_workshop" and mystery.id in {"bell", "key"}:
                combos.append((s_name, m_name))
            elif s_name == "mini_garden" and mystery.id in {"bell", "spoon"}:
                combos.append((s_name, m_name))
    return combos


ASP_RULES = r"""
% A mystery is reasonable when the setting can hide the item and the culprit has
% a plausible reason to move it.
possible(Setting, Mystery) :- setting(Setting), mystery(Mystery),
                              fits(Setting, Mystery), has_reason(Mystery).

valid_story(Setting, Mystery) :- possible(Setting, Mystery).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for h in sorted(s.hides):
            lines.append(asp.fact("hides", sid, h))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("item", mid, m.missing_item))
        lines.append(asp.fact("culprit", mid, m.culprit))
        lines.append(asp.fact("reason", mid))
    for sid, mid in valid_combos():
        lines.append(asp.fact("fits", sid, mid))
        lines.append(asp.fact("has_reason", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A mini whodunit storyworld featuring caution and Curiosity."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name", default="Curiosity")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(sorted(combos))
    return StoryParams(setting=setting, mystery=mystery, name=args.name)


def reasonableness_gate(setting: str, mystery: str) -> None:
    if (setting, mystery) not in valid_combos():
        raise StoryError(
            f"(No story: the mini mystery '{mystery}' does not fit {SETTINGSNICE(setting)}.)"
        )


def SETTINGSNICE(setting: str) -> str:
    return SETTINGS[setting].place


def predict_reveal(world: World, mystery: Mystery) -> dict:
    sim = world.copy()
    item = sim.get("missing")
    item.meters["found"] = 1.0
    return {"found": bool(item.meters["found"] >= THRESHOLD), "culprit": mystery.culprit}


def tell(setting: Setting, mystery: Mystery, name: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=name, kind="character", type="girl", label=name))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type=mystery.missing_item,
        label=mystery.missing_item,
        phrase=mystery.item_phrase,
        location=mystery.item_location,
    ))
    culprit = world.add(Entity(id=mystery.culprit, kind="character", type=mystery.culprit, label=mystery.culprit))

    world.say(
        f"At {setting.place}, {name} was a small detective with a big habit of looking twice."
    )
    world.say(
        f"{name} kept {name.lower()}'s voice calm and careful, because a good mystery needed caution, not rush."
    )
    world.say(
        f"Then the {mystery.missing_item} went missing. One minute it was {mystery.item_location}, and the next minute it was gone."
    )

    world.para()
    detective.memes["curiosity"] += 1
    detective.memes["caution"] += 1
    detective.memes["worry"] += 1
    missing.meters["missing"] = 1.0
    world.say(
        f"{name} looked under the little things first and followed {mystery.clue}, one tiny clue at a time."
    )
    world.say(
        f"That clue led past the quiet corners of the {setting.place}, where somebody had been busy in a very sneaky-looking way."
    )

    world.para()
    detective.memes["curiosity"] += 1
    world.say(
        f"At last, {name} found out what was going on: {mystery.reveal}."
    )
    world.say(
        f"The {mystery.culprit} had not meant to cause trouble; it had only wanted {mystery.culprit_reason}."
    )
    world.say(
        f"So {name} used a gentle voice, and the little helper put the {mystery.missing_item} back where it belonged."
    )

    world.para()
    detective.memes["relief"] += 1
    detective.meters["found"] = 1.0
    missing.meters["missing"] = 0.0
    missing.meters["found"] = 1.0
    world.say(
        f"In the end, the {mystery.missing_item} was safe again, and {name} smiled at the neat little answer."
    )
    world.say(
        f"The whole {setting.place} felt calmer after the secret was solved, and Curiosity kept the clue in memory like a shiny pebble."
    )

    world.facts.update(
        detective=detective,
        missing=missing,
        culprit=culprit,
        mystery=mystery,
        setting=setting,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]
    detective: Entity = f["detective"]
    return [
        f'Write a short whodunit for a child about {detective.label}, caution, and a missing {mystery.missing_item} in {setting.place}.',
        f"Tell a mini mystery where Curiosity notices clues instead of rushing, and the missing {mystery.missing_item} is found.",
        f'Write a gentle detective story that includes the word "{mystery.missing_item}" and ends with the item put back in its place.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    detective: Entity = f["detective"]
    setting: Setting = f["setting"]
    culprit: Entity = f["culprit"]
    return [
        QAItem(
            question=f"Who solved the mini mystery at {setting.place}?",
            answer=f"{detective.label} solved it by being careful and following the clues.",
        ),
        QAItem(
            question=f"What went missing in the story?",
            answer=f"{mystery.item_phrase.capitalize()} went missing from {mystery.item_location}.",
        ),
        QAItem(
            question=f"Who moved the {mystery.missing_item}?",
            answer=f"The {culprit.label} moved it, but not to be mean. It had {mystery.culprit_reason}.",
        ),
        QAItem(
            question="How did Curiosity find the answer?",
            answer=f"Curiosity looked slowly, followed {mystery.clue}, and used caution instead of guessing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is caution?",
            answer="Caution means moving carefully and thinking before you act so you do not make a mistake.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the desire to ask questions and find out how things work or what happened.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a mystery.",
        ),
    ]


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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = tell(setting, mystery, params.name)
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


CURATED = [
    StoryParams(setting="mini_library", mystery="key", name="Curiosity"),
    StoryParams(setting="mini_workshop", mystery="bell", name="Curiosity"),
    StoryParams(setting="mini_garden", mystery="spoon", name="Curiosity"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mystery) combos:\n")
        for setting, mystery in combos:
            print(f"  {setting:14} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
