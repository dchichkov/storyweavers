#!/usr/bin/env python3
"""
storyworlds/worlds/gooey_bedroom_repetition_flashback_slice_of_life.py
=======================================================================

A small slice-of-life storyworld set in a bedroom, built from the seed word
"gooey" and shaped around repetition plus flashback.

Premise:
- A child is in a cozy bedroom after a sticky snack or craft mishap.
- The child keeps trying the same simple fix again and again.
- A flashback explains where the goo came from.
- The story ends with the bedroom calm again and the child satisfied.

The world is intentionally small and constraint-checked:
- only bedroom scenes
- only a few plausible goo sources and fixes
- explicit invalid combinations raise StoryError
- prose is driven by simulated state, not a frozen template swap
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
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Bedroom:
    place: str = "the bedroom"
    affordances: set[str] = field(default_factory=lambda: {"snack", "jam", "paint", "marker"})


@dataclass
class GooSource:
    id: str
    label: str
    verb: str
    mess_kind: str
    goo_word: str
    flashback_line: str
    cleanup_tool: str
    cleanup_action: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ComfortObject:
    id: str
    label: str
    phrase: str
    region: str
    care_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    source: str
    comfort: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Bedroom) -> None:
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


GOO_SOURCES = {
    "jam": GooSource(
        id="jam",
        label="jam",
        verb="spread jam on a toast",
        mess_kind="sticky",
        goo_word="gooey jam",
        flashback_line="Yesterday, the toast slipped, and jam smudged onto the blanket.",
        cleanup_tool="a damp cloth",
        cleanup_action="wipe the sticky spots",
        tags={"gooey", "sticky", "food"},
    ),
    "pudding": GooSource(
        id="pudding",
        label="pudding",
        verb="spill pudding by the bed",
        mess_kind="sticky",
        goo_word="gooey pudding",
        flashback_line="At snack time, a spoon tipped, and pudding dotted the sheet.",
        cleanup_tool="a soft towel",
        cleanup_action="pat the sticky puddle dry",
        tags={"gooey", "sticky", "food"},
    ),
    "paint": GooSource(
        id="paint",
        label="paint",
        verb="tap open a paint cup",
        mess_kind="smudgy",
        goo_word="gooey paint",
        flashback_line="Earlier, a brush flicked, and paint freckles landed on the rug.",
        cleanup_tool="a little wipe",
        cleanup_action="wipe the colorful smears",
        tags={"gooey", "art", "color"},
    ),
}

COMFORTS = {
    "bunny": ComfortObject(
        id="bunny",
        label="stuffed bunny",
        phrase="a soft stuffed bunny",
        region="arms",
        care_kind="washable",
        tags={"soft", "sleep", "gooey"},
    ),
    "blanket": ComfortObject(
        id="blanket",
        label="blanket",
        phrase="a cozy blue blanket",
        region="lap",
        care_kind="washable",
        tags={"soft", "sleep"},
    ),
    "book": ComfortObject(
        id="book",
        label="picture book",
        phrase="a little picture book",
        region="hands",
        care_kind="wipeable",
        tags={"quiet", "read"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Nora", "Ella", "Ava", "Ruby", "Ivy"]
BOY_NAMES = ["Leo", "Sam", "Finn", "Max", "Theo", "Ben", "Noah", "Jude"]
TRAITS = ["gentle", "curious", "quiet", "thoughtful", "cheerful", "restless"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, source in GOO_SOURCES.items():
        for cid, comfort in COMFORTS.items():
            if source.id == "paint" and comfort.id == "book":
                continue
            combos.append((sid, cid))
    return combos


def explain_rejection(source: GooSource, comfort: ComfortObject) -> str:
    return (
        f"(No story: {source.label} in the bedroom doesn't reasonably pair with "
        f"{comfort.label}. Try a softer comfort item, or a different goo source.)"
    )


def reasonableness_gate(source: GooSource, comfort: ComfortObject) -> bool:
    if source.id == "paint" and comfort.id == "book":
        return False
    return True


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life bedroom story with gooey repetition and flashback."
    )
    ap.add_argument("--source", choices=GOO_SOURCES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.source and args.comfort:
        src, cfm = GOO_SOURCES[args.source], COMFORTS[args.comfort]
        if not reasonableness_gate(src, cfm):
            raise StoryError(explain_rejection(src, cfm))
    combos = [c for c in valid_combos()
              if (args.source is None or c[0] == args.source)
              and (args.comfort is None or c[1] == args.comfort)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    source_id, comfort_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(source=source_id, comfort=comfort_id, name=name, gender=gender, parent=parent, trait=trait)


def _mess_sentence(source: GooSource, hero: Entity, comfort: Entity) -> str:
    return (
        f"{hero.pronoun().capitalize()} tried again, and again, and the bedroom got more {source.mess_kind}."
    )


def tell(params: StoryParams) -> World:
    world = World(Bedroom())
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    source = GOO_SOURCES[params.source]
    comfort = COMFORTS[params.comfort]
    goo = world.add(Entity(id="goo", type="thing", label=source.label, owner=hero.id))
    soft = world.add(Entity(id="comfort", type="thing", label=comfort.label, phrase=comfort.phrase, owner=hero.id))

    # Beginning
    world.say(f"{hero.id} was in {world.setting.place}, where the day felt quiet and small.")
    world.say(f"{hero.pronoun().capitalize()} liked {source.goo_word} because it made ordinary moments feel a little silly.")
    world.say(f"Near {hero.pronoun('possessive')} pillow sat {soft.phrase}, waiting for a calm afternoon.")
    world.para()

    # Middle with repetition
    world.say(f"At first, {hero.id} tried to {source.verb}.")
    world.say(f"{_mess_sentence(source, hero, soft)}")
    world.say(f"So {hero.id} fetched {source.cleanup_tool} and tried to {source.cleanup_action}.")
    world.say(f"But the goo stayed on the blanket, so {hero.id} tried once more.")
    world.say(f"{hero.pronoun().capitalize()} kept making the same careful wipe, hoping the spot would disappear.")
    world.para()

    # Flashback turn
    world.say(f"That made {hero.id} pause and remember.")
    world.say(source.flashback_line)
    world.say(f"Now the bedroom felt different, because the mess had a clear beginning instead of a mysterious one.")
    world.say(f"{hero.id} nodded, took a slower breath, and cleaned the place the simple way.")
    world.say(f"After a few steady wipes, the {source.mess_kind} patch was gone.")
    world.para()

    # Resolution
    world.say(f"When {hero.pronoun('possessive')} {parent.label} came in, the room was tidy again.")
    world.say(f"{hero.id} smiled at {soft.label} and set it neatly back by the bed.")
    world.say(f"By the end, the bedroom was calm, the goo was gone, and {hero.id} was ready for a quieter game.")
    world.facts.update(hero=hero, parent=parent, source=source, comfort=comfort, goo=goo, soft=soft)
    return world


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, source, comfort = f["hero"], f["source"], f["comfort"]
    return [
        f"Write a short slice-of-life story in a bedroom about {hero.id} and {source.goo_word}.",
        f"Tell a gentle story where {hero.id} keeps trying to clean a gooey mess and remembers how it started.",
        f"Write a child-friendly story that uses the word 'gooey' and includes repetition and a flashback.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, source, comfort = f["hero"], f["parent"], f["source"], f["comfort"]
    return [
        QAItem(
            question=f"Where does {hero.id}'s story happen?",
            answer=f"It happens in the bedroom, where {hero.id} tries to clean up a {source.label} mess.",
        ),
        QAItem(
            question=f"What did {hero.id} keep doing again and again?",
            answer=f"{hero.id} kept wiping at the gooey spot again and again, hoping it would disappear.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=source.flashback_line,
        ),
        QAItem(
            question=f"What helped the bedroom feel calm at the end?",
            answer=f"Careful cleaning helped, and then {hero.id} put {comfort.label} back by the bed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does gooey mean?",
            answer="Gooey means sticky, soft, and a little wet, so it can cling to hands or cloth.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that remembers something from before the main moment.",
        ),
        QAItem(
            question="Why can repetition be useful?",
            answer="Repetition can show that someone is trying hard, practicing, or thinking the same thought more than once.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
source(S) :- source_fact(S).
comfort(C) :- comfort_fact(C).
valid(S,C) :- source(S), comfort(C), not invalid(S,C).
invalid("paint","book").
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in GOO_SOURCES:
        lines.append(asp.fact("source_fact", sid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort_fact", cid))
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


def explain_gender(gender: str) -> str:
    return f"(No story: this tiny bedroom world can use either girl or boy, but got {gender!r}.)"


CURATED = [
    StoryParams(source="jam", comfort="bunny", name="Mia", gender="girl", parent="mother", trait="gentle"),
    StoryParams(source="pudding", comfort="blanket", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(source="paint", comfort="book", name="Ava", gender="girl", parent="mother", trait="thoughtful"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError(explain_gender(args.gender))
    if args.source and args.comfort:
        if not reasonableness_gate(GOO_SOURCES[args.source], COMFORTS[args.comfort]):
            raise StoryError(explain_rejection(GOO_SOURCES[args.source], COMFORTS[args.comfort]))
    combos = [c for c in valid_combos()
              if (args.source is None or c[0] == args.source)
              and (args.comfort is None or c[1] == args.comfort)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    source, comfort = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(source=source, comfort=comfort, name=name, gender=gender, parent=parent, trait=trait)


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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid source/comfort combos:")
        for s, c in combos:
            print(f"  {s:8} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.source} + {p.comfort}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
