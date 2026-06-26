#!/usr/bin/env python3
"""
storyworlds/worlds/quirk_instance_insert_foreshadowing_mystery.py
==================================================================

A small mystery storyworld built from the seed words "quirk", "instance", and
"insert", with foreshadowing as the guiding narrative instrument.

Premise:
- A curious child and a careful grown-up explore a quiet place where one small
  oddity hints that something important is hidden.
- The mystery is not violent; it is a gentle puzzle with clues that matter.

Causal shape:
- A strange quirk in the room creates foreshadowing.
- An instance of the clue appears again in a later place.
- The child inserts the missing piece to reveal the answer.

The simulated state tracks:
- physical meters: clue strength, hiddenness, openness, tidiness
- emotional memes: curiosity, worry, relief, pride, trust

This script follows the Storyweavers contract:
- standalone stdlib script
- shared results containers imported eagerly
- ASP helper imported lazily
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify,
  and --show-asp supported
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
    keeper: Optional[str] = None
    hidden: bool = False
    usable: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    title: str
    quirk: str
    foreshadow: str
    instance: str
    reveal: str
    action: str
    insert_verb: str
    clue_kind: str
    hidden_kind: str
    clue_place: str
    reveal_place: str
    resolution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class KeyItem:
    id: str
    label: str
    phrase: str
    fits: str
    plural: bool = False


@dataclass
class StoryParams:
    setting: str
    mystery: str
    key_item: str
    name: str
    gender: str
    helper: str
    trait: str
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
        other = World(self.setting)
        import copy

        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _clue_matches(world: World) -> list[str]:
    out: list[str] = []
    mystery: Mystery = world.facts["mystery"]
    clue = world.get("clue")
    searcher = world.get("child")
    if searcher.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    sig = ("clue",)
    if sig in world.fired:
        return out
    if clue.hidden:
        return out
    world.fired.add(sig)
    clue.meters["hint"] = clue.meters.get("hint", 0.0) + 1
    searcher.memes["hope"] = searcher.memes.get("hope", 0.0) + 0.5
    out.append(f"It felt like the room was pointing toward a clue.")
    return out


def _open_secret(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    hidden = world.get("hidden")
    if clue.meters.get("inserted", 0.0) < THRESHOLD:
        return out
    sig = ("open_secret",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hidden.hidden = False
    hidden.meters["open"] = 1.0
    out.append(f"With a small click, the secret place opened.")
    return out


CAUSAL_RULES = [
    _clue_matches,
    _open_secret,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def foreshadow(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    child.memes["worry"] = child.memes.get("worry", 0.0) + 0.2
    world.say(
        f"{child.id} noticed a quirk: {mystery.quirk}. "
        f"It felt like foreshadowing, as if the room was keeping a secret."
    )


def first_instance(world: World, child: Entity, mystery: Mystery) -> None:
    world.say(
        f"Later, an instance of the same odd thing showed up again: {mystery.instance}."
    )


def search(world: World, child: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"{child.id} and {helper.label} searched {world.setting.place} carefully, "
        f"following each tiny hint."
    )


def insert_piece(world: World, child: Entity, key: Entity, mystery: Mystery) -> None:
    key.meters["inserted"] = key.meters.get("inserted", 0.0) + 1
    world.say(
        f"{child.id} decided to {mystery.insert_verb} {key.phrase} into the hidden opening."
    )
    propagate(world, narrate=True)


def reveal(world: World, child: Entity, helper: Entity, mystery: Mystery) -> None:
    hidden = world.get("hidden")
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    child.memes["pride"] = child.memes.get("pride", 0.0) + 0.5
    helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1
    world.say(
        f"Inside, they found {mystery.reveal}. {mystery.resolution} "
        f"{child.id} smiled, because the mystery finally made sense."
    )


SETTING_REGISTRY = {
    "library": Setting(
        place="the old library",
        detail="Dusty shelves leaned close together, and a narrow desk sat by the window.",
        affords={"quiet"},
    ),
    "attic": Setting(
        place="the attic",
        detail="Boxes, blankets, and a tilted lamp made the room feel like a puzzle.",
        affords={"search"},
    ),
    "garden_shed": Setting(
        place="the garden shed",
        detail="A row of hooks, a wooden bench, and a little lockbox waited in the corner.",
        affords={"search"},
    ),
}

MYSTERY_REGISTRY = {
    "clock_note": Mystery(
        id="clock_note",
        title="The Clock That Winked Twice",
        quirk="the clock ticked once, then skipped a beat",
        foreshadow="the second skip happened every time someone walked past the desk",
        instance="the same skipped beat echoed from the hallway clock",
        reveal="a folded note with one line about a hidden drawer",
        action="solve the mystery",
        insert_verb="insert",
        clue_kind="note",
        hidden_kind="drawer",
        clue_place="under the desk",
        reveal_place="inside the drawer",
        resolution="That was why the clock kept acting strange: it was warning them where to look.",
        tags={"clock", "note", "drawer", "foreshadowing"},
    ),
    "painted_key": Mystery(
        id="painted_key",
        title="The Painted Key Hint",
        quirk="a blue paint smudge shaped like a tiny arrow appeared on one shelf",
        foreshadow="the same blue smudge showed up again near the back wall",
        instance="an instance of that blue arrow was on the floor by a loose board",
        reveal="a brass key and a map folded into a neat square",
        action="solve the mystery",
        insert_verb="insert",
        clue_kind="key",
        hidden_kind="board",
        clue_place="near the shelf",
        reveal_place="behind the loose board",
        resolution="The blue marks were clues, quietly leading them to the secret spot.",
        tags={"key", "paint", "board", "foreshadowing"},
    ),
    "bell_box": Mystery(
        id="bell_box",
        title="The Bell in the Box",
        quirk="a tiny bell rang once whenever the lamp shadow moved",
        foreshadow="the bell rang again from the same corner after the room went still",
        instance="another instance of that bell sound came from a small box",
        reveal="a picture card, a ribbon, and a message that said 'look below'",
        action="solve the mystery",
        insert_verb="insert",
        clue_kind="card",
        hidden_kind="box",
        clue_place="near the lamp",
        reveal_place="inside the box",
        resolution="The repeating bell sound had been a clue all along.",
        tags={"bell", "box", "shadow", "foreshadowing"},
    ),
}

KEY_REGISTRY = {
    "brass_key": KeyItem(
        id="brass_key",
        label="brass key",
        phrase="the brass key",
        fits="hidden opening",
    ),
    "card_piece": KeyItem(
        id="card_piece",
        label="card piece",
        phrase="the card piece",
        fits="hidden opening",
    ),
    "tiny_tool": KeyItem(
        id="tiny_tool",
        label="tiny tool",
        phrase="the tiny tool",
        fits="hidden opening",
    ),
}

GIRL_NAMES = ["Mina", "Ivy", "Lina", "Nora", "Tia", "Ruby"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Finn", "Theo", "Ben"]
HELPERS = ["aunt", "father", "mother", "uncle"]
TRAITS = ["curious", "quiet", "bold", "patient", "bright"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle mystery world with foreshadowing and small clues.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--mystery", choices=MYSTERY_REGISTRY)
    ap.add_argument("--key-item", choices=KEY_REGISTRY)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    mystery = args.mystery or rng.choice(list(MYSTERY_REGISTRY))
    key_item = args.key_item or rng.choice(list(KEY_REGISTRY))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, key_item=key_item, name=name, gender=gender, helper=helper, trait=trait)


def tell(params: StoryParams) -> World:
    setting = SETTING_REGISTRY[params.setting]
    mystery = MYSTERY_REGISTRY[params.mystery]
    key_def = KEY_REGISTRY[params.key_item]

    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    clue = world.add(Entity(id="clue", type="thing", label=mystery.clue_kind, hidden=False, usable=False))
    hidden = world.add(Entity(id="hidden", type="thing", label=mystery.hidden_kind, hidden=True, usable=True))
    key = world.add(Entity(id="key", type="thing", label=key_def.label, phrase=key_def.phrase, usable=True))

    world.facts.update(
        child=child,
        helper=helper,
        clue=clue,
        hidden=hidden,
        key=key,
        mystery=mystery,
        key_def=key_def,
    )

    world.say(
        f"{child.id} was a {params.trait} {params.gender} named {params.name}, and {child.pronoun('possessive')} {params.helper} "
        f"was helping at {setting.place}."
    )
    world.say(setting.detail)

    world.para()
    foreshadow(world, child, mystery)
    search(world, child, helper, mystery)
    first_instance(world, child, mystery)

    world.para()
    world.say(f"They found that the clue was real: {mystery.foreshadow}.")
    world.say(f"The odd pattern made {child.id} even more curious.")
    insert_piece(world, child, key, mystery)

    world.para()
    reveal(world, child, helper, mystery)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    mystery = f["mystery"]
    return [
        f"Write a short mystery for a young child that uses the word 'quirk' and shows foreshadowing.",
        f"Tell a gentle story about {child.label} trying to {mystery.action} in {world.setting.place}.",
        f"Write a small detective story where an instance of a clue leads to a reveal after someone uses an insert motion.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    mystery = f["mystery"]
    key = f["key"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.label}, who explored {world.setting.place} with {helper.label}.",
        ),
        QAItem(
            question=f"What was the first quirk that hinted at the answer?",
            answer=f"The first quirk was that {mystery.quirk}. That was foreshadowing, because it hinted that something hidden mattered.",
        ),
        QAItem(
            question=f"What was the later instance of the clue?",
            answer=f"The later instance was that {mystery.instance}. It matched the first odd hint and helped solve the mystery.",
        ),
        QAItem(
            question=f"What did {child.label} insert to open the hidden place?",
            answer=f"{child.label} inserted {key.phrase}. After that, the hidden place opened and the secret was revealed.",
        ),
        QAItem(
            question=f"What did they find at the end?",
            answer=f"They found {mystery.reveal}. That answer explained why the strange clue had been there all along.",
        ),
    ]
    return qa


WORLD_KNOWLEDGE = {
    "foreshadowing": [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small hint early on so the reader can guess that something important will happen later.",
        )
    ],
    "quirk": [
        QAItem(
            question="What is a quirk?",
            answer="A quirk is a small unusual thing about a person, place, or object.",
        )
    ],
    "insert": [
        QAItem(
            question="What does it mean to insert something?",
            answer="To insert something means to put it into a place where it fits, like putting a key into a lock.",
        )
    ],
    "mystery": [
        QAItem(
            question="What is a mystery story?",
            answer="A mystery story is a story where a problem or secret is slowly solved by following clues.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery"].tags) | {"mystery", "quirk", "insert", "foreshadowing"}
    out: list[QAItem] = []
    for tag in ["mystery", "quirk", "insert", "foreshadowing"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        if e.usable:
            bits.append("usable=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A clue is important when it is visible and the searcher is curious.
important(clue) :- clue_visible, curious(searcher).

% An inserted key opens the hidden place.
opened(hidden) :- inserted(key), hidden_place(hidden).

% The mystery is solved when the hidden place is opened and the reveal is available.
solved :- opened(hidden), reveal_available.

% Foreshadowing is represented by repeated hints.
foreshadowing :- quirk_hint, later_instance.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTING_REGISTRY.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERY_REGISTRY.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("quirk_hint", mid))
        lines.append(asp.fact("later_instance", mid))
        lines.append(asp.fact("hidden_place", m.hidden_kind))
        lines.append(asp.fact("reveal_available", mid))
    for kid, k in KEY_REGISTRY.items():
        lines.append(asp.fact("key_item", kid))
        lines.append(asp.fact("fits", kid, k.fits))
    lines.append(asp.fact("inserted", "key"))
    lines.append(asp.fact("clue_visible"))
    lines.append(asp.fact("searcher", "child"))
    lines.append(asp.fact("curious", "searcher"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show solved/0. #show foreshadowing/0."))
    atoms = {str(a) for a in model}
    if "solved" in atoms and "foreshadowing" in atoms:
        print("OK: ASP twin reports the mystery can be solved with foreshadowing.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected result.")
    return 1


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show solved/0. #show foreshadowing/0."))
    return [(str(a),) for a in model]


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


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(setting="library", mystery="clock_note", key_item="brass_key", name="Mina", gender="girl", helper="aunt", trait="curious"),
        StoryParams(setting="attic", mystery="painted_key", key_item="tiny_tool", name="Owen", gender="boy", helper="mother", trait="quiet"),
        StoryParams(setting="garden_shed", mystery="bell_box", key_item="card_piece", name="Ivy", gender="girl", helper="father", trait="bright"),
    ]


CURATED = build_curated()


def resolve_random_choice(options: list[str], rng: random.Random) -> str:
    return rng.choice(sorted(options))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        setting=args.setting or resolve_random_choice(list(SETTING_REGISTRY), rng),
        mystery=args.mystery or resolve_random_choice(list(MYSTERY_REGISTRY), rng),
        key_item=args.key_item or resolve_random_choice(list(KEY_REGISTRY), rng),
        name=args.name or rng.choice(GIRL_NAMES if (args.gender or rng.choice(["girl", "boy"])) == "girl" else BOY_NAMES),
        gender=args.gender or rng.choice(["girl", "boy"]),
        helper=args.helper or rng.choice(HELPERS),
        trait=args.trait or rng.choice(TRAITS),
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/0. #show foreshadowing/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        atoms = asp_list()
        for a in atoms:
            print(" ".join(a))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
