#!/usr/bin/env python3
"""
storyworlds/worlds/deadly_cash_pursue_suspense_transformation_reconciliation_bedtime.py
======================================================================================

A tiny bedtime-story world with suspense, transformation, and reconciliation.

Premise:
- A child notices a small cash tin is missing at bedtime.
- The room feels strangely, "deadly" quiet.
- The child wants to pursue the sound of a tiny clink.
- The clue turns out to be harmless: a shadow transforms into an ordinary object.
- The story ends with a gentle reconciliation before sleep.

This world is intentionally small and constraint-checked. It models a few typed
entities with physical meters and emotional memes, then renders child-facing
prose from the simulated state.
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
# World vocabulary
# ---------------------------------------------------------------------------

SUSPENSE_LEVEL = 1.0
MAX_STORY_VARIANTS = 32


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    bedtime_detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    reveals: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    clue: str
    hero_name: str
    hero_type: str
    parent_type: str
    sibling_name: str
    sibling_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.sounds: list[str] = []

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.sounds = list(self.sounds)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "nursery": Setting(
        place="the nursery",
        bedtime_detail="A moon-shaped nightlight glowed on the wall.",
        affords={"listen", "look", "search"},
    ),
    "hall": Setting(
        place="the hall",
        bedtime_detail="The hall was narrow and sleepy, with soft shadows on the rug.",
        affords={"listen", "look", "search"},
    ),
    "attic_room": Setting(
        place="the attic room",
        bedtime_detail="The attic room held an old trunk and a window with silver moonlight.",
        affords={"listen", "look", "search"},
    ),
}

CLUES = {
    "bell": Clue(
        id="bell",
        label="little bell",
        phrase="a little silver bell",
        kind="bell",
        reveals="the bell on a toy rabbit",
        sound="tiny clink",
        tags={"sound", "silver"},
    ),
    "tin": Clue(
        id="tin",
        label="cash tin",
        phrase="a small cash tin with a shiny lid",
        kind="tin",
        reveals="the cash tin tucked beside a book",
        sound="soft clink",
        tags={"cash", "metal"},
    ),
    "spoon": Clue(
        id="spoon",
        label="teaspoon",
        phrase="a spoon with a bright handle",
        kind="spoon",
        reveals="the teaspoon beside a bowl",
        sound="gentle clink",
        tags={"metal", "kitchen"},
    ),
}

GENTLE_GLOSSES = {
    "cash": "Cash is money people keep in coins or bills to pay for things.",
    "suspense": "Suspense is the feeling of wondering what will happen next.",
    "transformation": "A transformation is when something seems to change into something else.",
    "reconciliation": "Reconciliation is when people make peace after a misunderstanding.",
    "bedtime": "Bedtime is the time to get ready for sleep with calm routines and soft lights.",
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ella", "Zoe"]
BOY_NAMES = ["Noah", "Finn", "Theo", "Leo", "Milo"]
SIBLING_NAMES = ["Pip", "Rae", "June", "Max", "Iris"]
TRAITS = ["curious", "sleepy", "careful", "brave", "gentle"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is reasonable when a clue can be pursued at bedtime and the ending
% supports both transformation and reconciliation.
reasonable(P, C) :- place(P), clue(C), affords(P, search), bedside(C).
has_suspense(P, C) :- reasonable(P, C), clues_from_sound(C).
has_transformation(C) :- clue(C), reveals_change(C).
has_reconciliation(P) :- place(P), bedtime(P), peace_possible(P).
valid_story(P, C) :- has_suspense(P, C), has_transformation(C), has_reconciliation(P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("bedtime", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("bedside", cid))
        lines.append(asp.fact("clues_from_sound", cid))
        lines.append(asp.fact("reveals_change", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(asp_set - py))
    print("  only in python:", sorted(py - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place, setting in SETTINGS.items():
        if "search" not in setting.affords:
            continue
        for clue_id in CLUES:
            combos.append((place, clue_id))
    return combos


def explain_rejection(place: str, clue_id: str) -> str:
    return (
        f"(No story: {place} and {clue_id} do not make a strong bedtime mystery "
        f"with a real clue, suspense, transformation, and reconciliation.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def bed_time_lantern(setting: Setting) -> str:
    return setting.bedtime_detail


def _suspense(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.id} heard a {clue.sound} in the quiet room, and the silence felt "
        f"deadly still."
    )
    world.say(
        f"{hero.id} wanted to pursue the sound, because bedtime was near and the "
        f"little clink felt important."
    )


def _transformation(world: World, hero: Entity, sibling: Entity, clue: Clue) -> None:
    sibling.memes["surprise"] = sibling.memes.get("surprise", 0.0) + 1
    world.say(
        f"Near the pillow, {hero.id} found {clue.phrase}, but the silver shape "
        f"looked almost like something else in the moonlight."
    )
    world.say(
        f"When {hero.id} lifted it, the scary-looking shadow transformed into "
        f"the ordinary {clue.reveals}."
    )


def _reconciliation(world: World, hero: Entity, sibling: Entity, parent: Entity, clue: Clue) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    sibling.memes["guilt"] = sibling.memes.get("guilt", 0.0) + 1
    sibling.memes["calm"] = sibling.memes.get("calm", 0.0) + 1
    world.say(
        f"{sibling.id} admitted that {sibling.pronoun('subject')} had moved the "
        f"{clue.label} and forgotten to say so."
    )
    world.say(
        f"{hero.id} smiled, and the two children made peace again while "
        f"{parent.id} tucked the blanket more snugly around them."
    )
    world.say(
        f"In the end, the cash tin was safe, the mystery was solved, and the room "
        f"felt soft enough for sleep."
    )


def tell(world: World, params: StoryParams) -> World:
    setting = world.setting
    clue = CLUES[params.clue]

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"sleep": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "calm": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label="the parent",
        meters={"sleep": 0.0},
        memes={"calm": 1.0},
    ))
    sibling = world.add(Entity(
        id=params.sibling_name,
        kind="character",
        type=params.sibling_type,
        label=params.sibling_name,
        meters={"sleep": 0.0},
        memes={"surprise": 0.0, "guilt": 0.0, "calm": 0.0},
    ))
    object_box = world.add(Entity(
        id="cash_tin",
        kind="thing",
        type="tin",
        label="cash tin",
        phrase="a small cash tin",
        owner=parent.id,
    ))
    clue_obj = world.add(Entity(
        id=clue.id,
        kind="thing",
        type=clue.kind,
        label=clue.label,
        phrase=clue.phrase,
        owner=parent.id,
        caretaker=parent.id,
    ))

    world.facts.update(
        hero=hero,
        parent=parent,
        sibling=sibling,
        object_box=object_box,
        clue=clue_obj,
        setting=setting,
        clue_cfg=clue,
    )

    world.say(f"{hero.id} was a little {params.hero_type} who loved bedtime stories.")
    world.say(f"{bed_time_lantern(setting)}")
    world.say(
        f"On the nightstand sat {object_box.phrase}, and {hero.id} knew it was important."
    )

    world.para()
    world.say(
        f"One quiet night in {setting.place}, {hero.id} heard a sound and sat up."
    )
    _suspense(world, hero, clue)

    world.para()
    world.say(setting.bedtime_detail)
    _transformation(world, hero, sibling, clue)

    world.para()
    _reconciliation(world, hero, sibling, parent, clue)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue_cfg"]
    setting = f["setting"]
    return [
        f'Write a short bedtime story with suspense, transformation, and reconciliation in {setting.place}.',
        f"Tell a gentle story where {hero.id} hears a {clue.sound}, pursues the clue, and learns a safe truth.",
        f'Write a child-friendly story that includes the words "deadly", "cash", and "pursue" without real danger.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sibling: Entity = f["sibling"]
    parent: Entity = f["parent"]
    clue: Clue = f["clue_cfg"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"Why did {hero.id} stay awake in {setting.place}?",
            answer=(
                f"{hero.id} heard a {clue.sound} in the quiet room and wanted to "
                f"pursue it before falling asleep."
            ),
        ),
        QAItem(
            question=f"What looked strange before the clue was understood?",
            answer=(
                f"The clue's silver shape looked spooky in the moonlight, but it "
                f"transformed into an ordinary {clue.reveals}."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} and {sibling.id} finish the story?",
            answer=(
                f"They made peace again after {sibling.id} admitted the mistake, "
                f"and {parent.label} tucked them in for sleep."
            ),
        ),
        QAItem(
            question=f"What was the important object in the room?",
            answer=(
                f"It was a cash tin, and the story used it as part of the bedtime mystery."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["suspense", "transformation", "reconciliation", "cash", "bedtime"]:
        q = {"suspense": "What is suspense?",
             "transformation": "What is a transformation?",
             "reconciliation": "What is reconciliation?",
             "cash": "What is cash?",
             "bedtime": "What is bedtime?"}[key]
        out.append(QAItem(question=q, answer=GENTLE_GLOSSES[key]))
    return out


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


# ---------------------------------------------------------------------------
# Serialization / trace
# ---------------------------------------------------------------------------

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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(
        place="nursery",
        clue="tin",
        hero_name="Mia",
        hero_type="girl",
        parent_type="mother",
        sibling_name="Pip",
        sibling_type="boy",
    ),
    StoryParams(
        place="hall",
        clue="bell",
        hero_name="Noah",
        hero_type="boy",
        parent_type="father",
        sibling_name="Rae",
        sibling_type="girl",
    ),
    StoryParams(
        place="attic_room",
        clue="spoon",
        hero_name="Ella",
        hero_type="girl",
        parent_type="mother",
        sibling_name="June",
        sibling_type="girl",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime suspense storyworld with a gentle turn.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--sibling")
    ap.add_argument("--sibling-gender", choices=["girl", "boy"])
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
    if args.place and args.clue:
        if (args.place, args.clue) not in combos:
            raise StoryError(explain_rejection(args.place, args.clue))

    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.clue is None or c[1] == args.clue)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")

    place, clue = rng.choice(sorted(filtered))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    sibling_gender = args.sibling_gender or ("girl" if hero_gender == "boy" else "boy")
    sibling_name = args.sibling or rng.choice(SIBLING_NAMES)

    return StoryParams(
        place=place,
        clue=clue,
        hero_name=hero_name,
        hero_type=hero_gender,
        parent_type=parent_type,
        sibling_name=sibling_name,
        sibling_type=sibling_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    world = tell(world, params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def asp_valid_story_pairs() -> list[tuple[str, str]]:
    return asp_valid_combos()


def asp_program_full(show: str) -> str:
    return asp_program(show)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_full("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_story_pairs()
        print(f"{len(pairs)} compatible (place, clue) combos:\n")
        for place, clue in pairs:
            print(f"  {place:12} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < MAX_STORY_VARIANTS * max(args.n, 1):
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
            header = f"### {p.hero_name}: {p.clue} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
