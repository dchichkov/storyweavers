#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/stationery_magic_transformation_humor_mystery.py
================================================================================

A standalone story world about stationery, a little magic, a transformation, and
a silly mystery that gets solved by noticing the clues in the desk.

The premise is simple:
a child finds a strange stationery item, a small magical change happens, the
change causes a funny mystery, and then the mystery is explained with a gentle
ending image that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/stationery_magic_transformation_humor_mystery.py
    python storyworlds/worlds/gpt-5.4-mini/stationery_magic_transformation_humor_mystery.py --all
    python storyworlds/worlds/gpt-5.4-mini/stationery_magic_transformation_humor_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/stationery_magic_transformation_humor_mystery.py --verify
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
MYSTERY_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    magic: bool = False
    transformable: bool = False
    clue: bool = False

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"shimmer": 0.0, "oddity": 0.0, "transformed": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "delight": 0.0, "worry": 0.0}

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
        return self.label or self.type


@dataclass
class DeskSetting:
    id: str
    place: str
    detail: str


@dataclass
class StationeryItem:
    id: str
    label: str
    phrase: str
    magic_word: str
    transformed_label: str
    clue: str
    safe: bool = True
    magic: bool = False
    transformable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicEffect:
    id: str
    sense: int
    power: int
    start_text: str
    transform_text: str
    fix_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: DeskSetting) -> None:
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
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    setting: str
    item: str
    effect: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "desk": DeskSetting(id="desk", place="the school desk", detail="Under the desk sat a neat row of folders and pencils."),
    "library": DeskSetting(id="library", place="the library table", detail="The table had quiet lamps, stacks of books, and one lonely pencil cup."),
    "study": DeskSetting(id="study", place="the study table", detail="The study table was covered with papers, ruler marks, and a warm lamp."),
}

STATIONERY = {
    "pencil": StationeryItem(
        id="pencil",
        label="pencil",
        phrase="a striped pencil",
        magic_word="whisper",
        transformed_label="tiny paintbrush",
        clue="a curl of purple graphite dust",
        tags={"stationery", "pencil", "magic"},
    ),
    "eraser": StationeryItem(
        id="eraser",
        label="eraser",
        phrase="a pink eraser",
        magic_word="rub",
        transformed_label="little cloud",
        clue="pink crumbs shaped like stars",
        tags={"stationery", "eraser", "magic"},
    ),
    "notebook": StationeryItem(
        id="notebook",
        label="notebook",
        phrase="a blue notebook",
        magic_word="open",
        transformed_label="pop-up map",
        clue="a page that kept flipping by itself",
        tags={"stationery", "notebook", "magic"},
    ),
    "stapler": StationeryItem(
        id="stapler",
        label="stapler",
        phrase="a tiny stapler",
        magic_word="tap",
        transformed_label="silver beetle",
        clue="one lonely staple on the floor",
        tags={"stationery", "stapler", "magic"},
    ),
}

EFFECTS = {
    "hum": MagicEffect(
        id="hum",
        sense=3,
        power=3,
        start_text="gave a soft hum and a sparkly wink",
        transform_text="changed the {item} into {new}",
        fix_text="the spell settled down with a happy fizz",
        tags={"magic", "transformation", "humor"},
    ),
    "giggle": MagicEffect(
        id="giggle",
        sense=4,
        power=4,
        start_text="gave a silly giggle and a blue puff",
        transform_text="turned the {item} into {new}",
        fix_text="the magic laughed itself back into place",
        tags={"magic", "transformation", "humor"},
    ),
    "blink": MagicEffect(
        id="blink",
        sense=2,
        power=2,
        start_text="blinked once like a sleepy star",
        transform_text="swapped the {item} for {new}",
        fix_text="the last sparkle drifted away",
        tags={"magic", "transformation", "humor"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Theo", "Ben", "Leo", "Max", "Noah", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for iid in STATIONERY:
            for eid in EFFECTS:
                out.append((sid, iid, eid))
    return out


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in STATIONERY.items():
        lines.append(asp.fact("item", iid))
        if item.magic:
            lines.append(asp.fact("magic_item", iid))
        if item.transformable:
            lines.append(asp.fact("transformable", iid))
    for eid, eff in EFFECTS.items():
        lines.append(asp.fact("effect", eid))
        lines.append(asp.fact("sense", eid, eff.sense))
        lines.append(asp.fact("power", eid, eff.power))
    lines.append(asp.fact("sense_min", MYSTERY_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S,I,E) :- setting(S), item(I), effect(E).
reasonable(E) :- effect(E), sense(E, X), sense_min(M), X >= M.
"""

def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_reasonable() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show reasonable/1."))
    return sorted(x for (x,) in asp.atoms(model, "reasonable"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny stationery magic mystery world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=STATIONERY)
    ap.add_argument("--effect", choices=EFFECTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.effect and EFFECTS[args.effect].sense < MYSTERY_MIN:
        raise StoryError(f"(Refusing effect '{args.effect}': too flimsy for a mystery.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.effect is None or c[2] == args.effect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, effect = rng.choice(sorted(combos))
    gender = rng.choice(["girl", "boy"])
    helper_gender = "girl" if gender == "boy" else "boy"
    return StoryParams(
        setting=setting,
        item=item,
        effect=effect,
        child=args.name or _pick_name(rng, gender),
        child_gender=gender,
        helper=args.helper or _pick_name(rng, helper_gender),
        helper_gender=helper_gender,
    )


def _story_state(world: World, child: Entity, helper: Entity, item: Entity, effect: MagicEffect) -> None:
    child.memes["curiosity"] += 2
    helper.memes["worry"] += 1
    world.say(
        f"At {world.setting.place}, {child.id} noticed {item.label} tucked beside a stack of stationery."
    )
    world.say(
        f'{child.id} leaned close. "{item.phrase}?" {child.pronoun()} whispered, because it looked ordinary and odd at the same time.'
    )
    world.para()
    world.say(
        f"Then the {item.label} {effect.start_text}. "
        f"It felt like the desk had decided to tell a joke."
    )
    item.meters["shimmer"] += 1
    item.meters["oddity"] += 1
    item.meters["transformed"] += 1
    world.get("clue").meters["oddity"] += 1


def tell_story(world: World, child: Entity, helper: Entity, item_cfg: StationeryItem, effect: MagicEffect) -> None:
    item = world.add(Entity(id="item", kind="thing", type="stationery", label=item_cfg.label,
                            traits=["ordinary"], attrs={"phrase": item_cfg.phrase},
                            magic=item_cfg.magic, transformable=item_cfg.transformable))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=item_cfg.clue, clue=True))
    world.add(Entity(id="desk", kind="thing", type="place", label=world.setting.place))
    world.facts["clue"] = clue.label
    _story_state(world, child, helper, item, effect)
    world.para()
    world.say(
        f"{helper.id} peered under the lamp. \"It isn't missing,\" {helper.pronoun()} said. "
        f"\"It is just trying to be {item_cfg.transformed_label}.\""
    )
    helper.memes["delight"] += 1
    if effect.id == "giggle":
        world.say(
            f"{child.id} giggled too, because the {item.label} now looked like it had borrowed a new job."
        )
    elif effect.id == "hum":
        world.say(
            f"{child.id} tapped the desk, and the magic answered with another tiny hum."
        )
    else:
        world.say(
            f"{child.id} blinked twice. The change was so neat it almost seemed like a trick."
        )
    world.para()
    world.say(
        f"They checked the clue -- {item_cfg.clue} -- and found that it matched the transformed shape."
    )
    world.say(
        f"At last, the mystery was solved: the {item.label} had become {item_cfg.transformed_label},"
        f" but it was still the same little bit of stationery underneath."
    )
    world.say(
        f"By the end, {child.id} set the transformed thing beside the pencils, and the desk looked ready for another funny secret."
    )
    world.facts.update(
        child=child, helper=helper, item=item, item_cfg=item_cfg, effect=effect,
        transformed=item_cfg.transformed_label, solved=True
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.item not in STATIONERY:
        raise StoryError(f"Unknown stationery item: {params.item}")
    if params.effect not in EFFECTS:
        raise StoryError(f"Unknown effect: {params.effect}")
    setting = SETTINGS[params.setting]
    world = World(setting)
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    tell_story(world, child, helper, STATIONERY[params.item], EFFECTS[params.effect])
    prompts = [
        f'Write a short mystery story for a child that includes the word "stationery" and a magical transformation.',
        f"Tell a humorous mystery about {child.id}, {params.helper}, and a piece of stationery that changes into something else.",
        f'Write a gentle story where magic, transformation, and humor solve a tiny mystery at {setting.place}.',
    ]
    story_qa = [
        QAItem(question=f"What did {child.id} find?", answer=f"{child.id} found {STATIONERY[params.item].phrase} in the middle of the stationery pile. It changed magically, so everyone had to figure out what it became."),
        QAItem(question="How was the mystery solved?", answer=f"They noticed the clue and matched it to the new shape. That told them the strange item was still the same stationery, only transformed into {STATIONERY[params.item].transformed_label}."),
        QAItem(question="Was the story scary?", answer="No. It was more funny than scary, because the magic acted playful and the surprise ended with a silly explanation."),
    ]
    world_qa = [
        QAItem(question="What is stationery?", answer="Stationery is paper things and writing things, like pencils, notebooks, erasers, and staplers. People use stationery to write, draw, and keep notes."),
        QAItem(question="What is magic in a story?", answer="Magic is when something impossible happens, like a thing changing shape or doing something surprising without a normal reason."),
        QAItem(question="What is a transformation?", answer="A transformation is a change from one thing into another. In stories, it can be funny, strange, or wonderful."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.clue:
            bits.append("clue=True")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(setting="desk", item="pencil", effect="hum", child="Mia", child_gender="girl", helper="Theo", helper_gender="boy"),
    StoryParams(setting="library", item="eraser", effect="giggle", child="Leo", child_gender="boy", helper="Nora", helper_gender="girl"),
    StoryParams(setting="study", item="notebook", effect="blink", child="Ava", child_gender="girl", helper="Max", helper_gender="boy"),
]


def valid_story(params: StoryParams) -> bool:
    return params.effect in EFFECTS and EFFECTS[params.effect].sense >= MYSTERY_MIN


def asp_verify() -> int:
    import asp
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    rc = 0
    if python_set == clingo_set:
        print(f"OK: ASP compatible set matches valid_combos() ({len(python_set)} combos).")
    else:
        print("MISMATCH in compatible combos:")
        rc = 1
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    python_reasonable = {e.id for e in EFFECTS.values() if e.sense >= MYSTERY_MIN}
    clingo_reasonable = set(asp_reasonable())
    if python_reasonable == clingo_reasonable:
        print("OK: ASP reasonableness matches.")
    else:
        print("MISMATCH in reasonableness:")
        rc = 1
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test produced a story.")
    except Exception as err:  # noqa: BLE001
        print(f"FAIL: generate() smoke test crashed: {err}")
        return 1
    return rc


def generate_story_sample(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program(show="#show compatible/3.\n#show reasonable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        reasonable = asp_reasonable()
        print(f"{len(combos)} compatible combos.")
        print(f"Reasonable magic effects: {', '.join(reasonable)}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.child} with {p.item} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
