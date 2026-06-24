#!/usr/bin/env python3
"""
storyworlds/worlds/cell_magic_fairy_tale.py
==========================================

A small fairy-tale storyworld about a castle cell, a locked door, and a little
bit of magic used wisely. The model keeps track of physical meters and emotional
memes, and the prose is driven by state changes rather than fixed text.

The seed premise is close to a fairy tale:
- a child or fairy is trapped in a cell,
- a helper discovers a magical way to open it,
- the story turns on a choice between a spell and a safer, gentler spell,
- the ending shows freedom and a changed mood.

This file follows the Storyweavers storyworld contract.
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

CELL_THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"locked": 0.0, "open": 0.0, "glow": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "hope": 0.0, "joy": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy", "queen", "witch", "woman"}
        male = {"boy", "knight", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Magic:
    id: str
    label: str
    phrase: str
    effect: str
    sense: int
    power: int
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    helper: str
    helper_type: str
    prisoner: str
    prisoner_type: str
    keeper: str
    keeper_type: str
    magic: str
    cell: str
    setting: str = "an old stone castle"
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.parts: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.parts[-1].append(text)

    def para(self) -> None:
        if self.parts[-1]:
            self.parts.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.parts if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        return w


def _safe_pronoun(name: str, typ: str) -> str:
    return Entity(id=name, type=typ).pronoun()


THEMES = ["castle", "forest", "moonlit tower"]
CELLS = {
    "cell": {"label": "cell", "place": "the cell", "stone": "cold stone", "bars": "iron bars"},
    "dungeon": {"label": "dungeon cell", "place": "the dungeon cell", "stone": "gray stone", "bars": "black bars"},
}
MAGICS = {
    "keyspell": Magic(
        id="keyspell",
        label="key spell",
        phrase="tapped the air and whispered a key spell",
        effect="opened the lock with a golden click",
        sense=3,
        power=3,
        safe=True,
        tags={"magic", "key", "open"},
    ),
    "mothlight": Magic(
        id="mothlight",
        label="moth-light charm",
        phrase="spread her hands and called a moth-light charm",
        effect="filled the lock with soft blue light until it loosened",
        sense=3,
        power=2,
        safe=True,
        tags={"magic", "light", "open"},
    ),
    "wildspark": Magic(
        id="wildspark",
        label="wild spark",
        phrase="cracked her fingers and tried a wild spark",
        effect="made the bars rattle and glow too hot to touch",
        sense=1,
        power=1,
        safe=False,
        tags={"magic", "spark"},
    ),
}
KEEPERS = {
    "witch": {"type": "witch", "label": "the witch"},
    "giant": {"type": "giant", "label": "the giant"},
    "queen": {"type": "queen", "label": "the queen"},
}
HELPERS = ["Rose", "Mina", "Elin", "Tilda", "Luna", "Ivy", "Sera", "Nora"]
PRISONERS = ["Pip", "Lark", "Bea", "Finn", "Milo", "Aster", "Drew", "Wren"]


def sensible_magics() -> list[Magic]:
    return [m for m in MAGICS.values() if m.sense >= SENSE_MIN]


def best_magic() -> Magic:
    return max(MAGICS.values(), key=lambda m: m.sense)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a cell and a little magic.")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--prisoner", choices=PRISONERS)
    ap.add_argument("--keeper", choices=KEEPERS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--cell", choices=CELLS)
    ap.add_argument("--theme", choices=THEMES)
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
    if args.magic and MAGICS[args.magic].sense < SENSE_MIN:
        raise StoryError("That magic is too wild for a gentle fairy tale; choose a wiser spell.")
    magic = args.magic or rng.choice(sorted(m.id for m in sensible_magics()))
    cell = args.cell or rng.choice(sorted(CELLS))
    helper = args.helper or rng.choice(HELPERS)
    prisoner = args.prisoner or rng.choice(PRISONERS)
    keeper = args.keeper or rng.choice(sorted(KEEPERS))
    theme = args.theme or rng.choice(THEMES)
    return StoryParams(
        helper=helper,
        helper_type="fairy",
        prisoner=prisoner,
        prisoner_type="child",
        keeper=keeper,
        keeper_type=KEEPERS[keeper]["type"],
        magic=magic,
        cell=cell,
        setting=theme,
    )


def valid_combos() -> list[tuple[str, str, str]]:
    return [(t, m, c) for t in THEMES for m in MAGICS if MAGICS[m].sense >= SENSE_MIN for c in CELLS]


def _make_world(params: StoryParams) -> World:
    world = World()
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper"))
    prisoner = world.add(Entity(id=params.prisoner, kind="character", type=params.prisoner_type, role="prisoner"))
    keeper = world.add(Entity(id="Keeper", kind="character", type=params.keeper_type, role="keeper", label=KEEPERS[params.keeper]["label"]))
    cell_cfg = CELLS[params.cell]
    cell = world.add(Entity(id="cell", kind="place", type="cell", label=cell_cfg["label"]))
    lock = world.add(Entity(id="lock", kind="thing", type="lock", label="lock"))
    prisoner.meters["locked"] = 1.0
    cell.meters["locked"] = 1.0
    prisoner.memes["fear"] = 2.0
    prisoner.memes["hope"] = 1.0
    helper.memes["hope"] = 2.0
    world.facts.update(params=params, helper=helper, prisoner=prisoner, keeper=keeper, cell=cell, lock=lock)
    return world


def narrate_setup(world: World, params: StoryParams) -> None:
    helper = world.facts["helper"]
    prisoner = world.facts["prisoner"]
    cell_cfg = CELLS[params.cell]
    world.say(
        f"In {params.setting}, {prisoner.id} sat in {cell_cfg['place']}, behind {cell_cfg['bars']} and {cell_cfg['stone']}."
    )
    world.say(
        f"{helper.id} came softly to the door and saw that the little room was shut tight."
    )
    helper.memes["hope"] += 1
    prisoner.memes["fear"] += 0.5


def narrate_choice(world: World, params: StoryParams) -> None:
    helper = world.facts["helper"]
    prisoner = world.facts["prisoner"]
    magic = MAGICS[params.magic]
    world.para()
    world.say(
        f'{helper.id} smiled. "{magic.label.capitalize()}," {helper.pronoun()} whispered, and {magic.phrase}.'
    )
    if magic.safe:
        helper.memes["hope"] += 1
    else:
        helper.memes["boldness"] = helper.memes.get("boldness", 0.0) + 1


def apply_magic(world: World, params: StoryParams) -> bool:
    magic = MAGICS[params.magic]
    cell = world.facts["cell"]
    lock = world.facts["lock"]
    if magic.safe:
        lock.meters["open"] += magic.power
        cell.meters["open"] += magic.power
        cell.meters["locked"] = 0.0
        world.facts["opened"] = True
        return True
    lock.meters["glow"] += 1.0
    cell.memes["fear"] = cell.memes.get("fear", 0.0) + 1.0
    world.facts["opened"] = False
    return False


def narrate_end(world: World, params: StoryParams, opened: bool) -> None:
    helper = world.facts["helper"]
    prisoner = world.facts["prisoner"]
    keeper = world.facts["keeper"]
    magic = MAGICS[params.magic]
    world.para()
    if opened:
        helper.memes["joy"] += 1
        prisoner.memes["relief"] += 2
        prisoner.memes["fear"] = 0.0
        world.say(
            f"The {magic.label} worked at once. The lock gave a soft click, the door swung wide, and {prisoner.id} stepped into the light."
        )
        world.say(
            f"{keeper.label} was not pleased, yet the magic had been gentle, and nobody was hurt."
        )
        world.say(
            f"At last, {helper.id} and {prisoner.id} walked away together, with the cell left empty and quiet behind them."
        )
    else:
        helper.memes["fear"] += 1
        prisoner.memes["fear"] += 1
        world.say(
            f"The wild spell only made the bars tremble. {keeper.label} heard the noise and came near, so {helper.id} had to stop at once."
        )
        world.say(
            f"Then {helper.id} remembered the kinder magic, and the story ended with a wiser wish and a safer plan."
        )


def tell(params: StoryParams) -> World:
    world = _make_world(params)
    narrate_setup(world, params)
    narrate_choice(world, params)
    opened = apply_magic(world, params)
    narrate_end(world, params, opened)
    world.facts["outcome"] = "opened" if opened else "stopped"
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a fairy-tale story where {p.helper} uses magic to open a cell and free {p.prisoner}.",
        f"Tell a gentle castle story about {p.helper}, {p.prisoner}, and a locked cell that changes because of magic.",
        f"Write a child-facing fairy tale with a cell, a little spell, and a happy ending after a careful rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    magic = MAGICS[p.magic]
    opened = world.facts["outcome"] == "opened"
    return [
        QAItem(
            question=f"Who was trapped in the cell?",
            answer=f"{p.prisoner} was trapped in the cell until the helper found a way to open it.",
        ),
        QAItem(
            question=f"What did {p.helper} use to change the locked cell?",
            answer=f"{p.helper} used {magic.label}, a little bit of magic that helped the lock open.",
        ),
        QAItem(
            question=f"Did the magic feel safe or wild?",
            answer="It felt safe and gentle." if opened else "It started wild, but the story stopped before it could do harm.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cell in a fairy tale castle?",
            answer="A cell is a small locked room where someone might be kept until a door or lock is opened.",
        ),
        QAItem(
            question="What should a gentle magic spell do in this storyworld?",
            answer="It should help without hurting anyone, like opening a lock or bringing light.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} role={e.role} type={e.type}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
sense_min(2).
sensible(M) :- magic(M), magic_sense(M,S), sense_min(N), S >= N.
valid(T,M,C) :- theme(T), sensible(M), cell(C).
opened :- chosen_magic(M), magic_sense(M,S), S >= 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for cid in CELLS:
        lines.append(asp.fact("cell", cid))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("magic_sense", mid, m.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    program = asp_program(
        "\n".join([asp.fact("chosen_magic", params.magic)]),
        "#show opened/0.",
    )
    model = asp.one_model(program)
    return "opened" if asp.atoms(model, "opened") else "stopped"


def asp_verify() -> int:
    rc = 0
    if set(asp_sensible()) == {m.id for m in sensible_magics()}:
        print("OK: sensible magic matches.")
    else:
        rc = 1
        print("MISMATCH: sensible magic differs.")
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: valid combos match.")
    else:
        rc = 1
        print("MISMATCH: valid combos differ.")
    params = resolve_params(build_parser().parse_args([]), random.Random(1))
    if asp_outcome(params) == ("opened" if MAGICS[params.magic].sense >= SENSE_MIN else "stopped"):
        print("OK: outcome matches.")
    else:
        rc = 1
        print("MISMATCH: outcome differs.")
    return rc


CURATED = [
    StoryParams(helper="Luna", helper_type="fairy", prisoner="Pip", prisoner_type="child", keeper="witch", keeper_type="witch", magic="keyspell", cell="cell", setting="an old stone castle"),
    StoryParams(helper="Ivy", helper_type="fairy", prisoner="Wren", prisoner_type="child", keeper="queen", keeper_type="queen", magic="mothlight", cell="dungeon", setting="a moonlit tower"),
]


def explain_rejection() -> str:
    return "No story: the chosen magic is too wild for a gentle fairy tale."


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.magic and MAGICS[args.magic].sense < SENSE_MIN:
        raise StoryError(explain_rejection())
    return StoryParams(
        helper=args.helper or rng.choice(HELPERS),
        helper_type="fairy",
        prisoner=args.prisoner or rng.choice(PRISONERS),
        prisoner_type="child",
        keeper=args.keeper or rng.choice(sorted(KEEPERS)),
        keeper_type=KEEPERS[args.keeper or rng.choice(sorted(KEEPERS))]["type"] if args.keeper else KEEPERS[rng.choice(sorted(KEEPERS))]["type"],
        magic=args.magic or rng.choice(sorted(m.id for m in sensible_magics())),
        cell=args.cell or rng.choice(sorted(CELLS)),
        setting=args.theme or rng.choice(THEMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    ap = build_parser()
    args = ap.parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show opened/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible magic:", ", ".join(asp_sensible()))
        print("valid combos:", len(asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
