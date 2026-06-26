#!/usr/bin/env python3
"""
storyworlds/worlds/wealth_frill_bad_ending_magic_mystery_to.py
===============================================================

A small slice-of-life storyworld about a wealthy household, one cherished
frilled thing, and a tiny mystery that a bit of magic can solve—though not
always in a happy way.

Premise:
- A child in a comfortable home loves a decorative frill.
- A small household mystery appears: something important has gone missing.
- A gentle bit of magic helps uncover what really happened.
- The ending is intentionally bittersweet: the mystery is solved, but the
  frill or the moment is not saved in perfect condition.

The story stays grounded in everyday domestic detail: a room, a snack, a
drawer, a ribbon, a lamp, a careful search, and the feeling of learning that
not every nice thing can be kept pristine.

The world model uses meters (physical state) and memes (emotional state), and
the narrated story is driven by those state changes.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bright townhouse"
    indoors: bool = True
    wealth: str = "comfortable"


@dataclass
class Mystery:
    id: str
    missing: str
    hidden_in: str
    clue: str
    solved_by_magic: bool = True


@dataclass
class FrillItem:
    id: str
    label: str
    phrase: str
    kind: str
    damage: str
    region: str
    owner_kind: str = "girl"


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    reveals: str
    cost: str
    side_effect: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.magic_used: bool = False
        self.mystery_solved: bool = False

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


HERO_NAMES = ["Mina", "Clara", "Lena", "Mira", "Nora", "Pia"]
PARENT_NAMES = ["Mother", "Aunt", "Grandmother"]
TRAITS = ["careful", "curious", "gentle", "tidy", "quiet"]


SETTINGS = {
    "parlor": Setting(place="the parlor", indoors=True, wealth="comfortable"),
    "sunroom": Setting(place="the sunroom", indoors=True, wealth="rich"),
    "hall": Setting(place="the front hall", indoors=True, wealth="comfortable"),
}

FRILLS = {
    "dress_frill": FrillItem(
        id="dress_frill",
        label="frilled dress",
        phrase="a cream dress with a wide frill",
        kind="dress",
        damage="creased and tea-spotted",
        region="torso",
        owner_kind="girl",
    ),
    "curtain_frill": FrillItem(
        id="curtain_frill",
        label="frilled curtain",
        phrase="a lace curtain with a soft frill",
        kind="curtain",
        damage="pulled loose",
        region="window",
        owner_kind="girl",
    ),
    "pillow_frill": FrillItem(
        id="pillow_frill",
        label="frilled pillow",
        phrase="a velvet pillow with a neat frill",
        kind="pillow",
        damage="slightly bent",
        region="lap",
        owner_kind="girl",
    ),
}

MYSTERIES = {
    "missing_brooch": Mystery(
        id="missing_brooch",
        missing="a little gold brooch",
        hidden_in="the candy bowl",
        clue="a sugar sparkle on the table",
        solved_by_magic=True,
    ),
    "missing_key": Mystery(
        id="missing_key",
        missing="the music-box key",
        hidden_in="the sewing basket",
        clue="a thread caught on the drawer",
        solved_by_magic=True,
    ),
    "missing_note": Mystery(
        id="missing_note",
        missing="a folded note",
        hidden_in="the book with the blue ribbon",
        clue="a ribbon mark on the page",
        solved_by_magic=True,
    ),
}

MAGIC = {
    "glow_lamp": MagicTool(
        id="glow_lamp",
        label="a little glow lamp",
        phrase="a little glow lamp with a warm gold bulb",
        reveals="soft gold lines in the room",
        cost="a small pocketful of dust",
        side_effect="left a faint shimmer on the frill",
    ),
    "moon_spoon": MagicTool(
        id="moon_spoon",
        label="a moon spoon",
        phrase="a tiny silver spoon that caught moonlight",
        reveals="reflections in shiny places",
        cost="a quiet wish",
        side_effect="made every shine look a little brighter",
    ),
}

ASP_RULES = r"""
mystery_valid(M, F, G) :- mystery(M), frill(F), magic(G), clue_points_to(M, F), magic_can_reveal(G, M).
bad_ending(M, F) :- mystery_valid(M, F, _), frill_can_damage(F), damage_happens(F).
solved(M) :- mystery_valid(M, _, G), magic_can_reveal(G, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid, f in FRILLS.items():
        lines.append(asp.fact("frill", fid))
        lines.append(asp.fact("frill_can_damage", fid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_points_to", mid, mid))
    for gid, g in MAGIC.items():
        lines.append(asp.fact("magic", gid))
        lines.append(asp.fact("magic_can_reveal", gid, "missing_brooch"))
        lines.append(asp.fact("magic_can_reveal", gid, "missing_key"))
        lines.append(asp.fact("magic_can_reveal", gid, "missing_note"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show mystery_valid/3.\n#show bad_ending/2.\n#show solved/1."))
    atoms = set((s.name, len(s.arguments)) for s in model)
    if ("solved", 1) in atoms:
        print("OK: ASP program produces a solved mystery.")
        return 0
    print("MISMATCH: ASP program did not produce the expected model.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life wealth/frill mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--frill", choices=FRILLS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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


@dataclass
class StoryParams:
    setting: str
    frill: str
    mystery: str
    magic: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combo(setting: str, frill: str, mystery: str, magic: str) -> bool:
    return setting in SETTINGS and frill in FRILLS and mystery in MYSTERIES and magic in MAGIC


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    frill = args.frill or rng.choice(list(FRILLS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    magic = args.magic or rng.choice(list(MAGIC))
    if not valid_combo(setting, frill, mystery, magic):
        raise StoryError("No valid combination matches the given options.")
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, frill=frill, mystery=mystery, magic=magic, name=name, parent=parent, trait=trait)


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id="hero", kind="character", type="girl", label=params.name, owner=params.parent))
    parent = world.add(Entity(id="parent", kind="character", type="mother", label=params.parent))
    frill_cfg = FRILLS[params.frill]
    mystery_cfg = MYSTERIES[params.mystery]
    magic_cfg = MAGIC[params.magic]
    frill = world.add(Entity(
        id="frill", type=frill_cfg.kind, label=frill_cfg.label, phrase=frill_cfg.phrase,
        owner=hero.id, caretaker=parent.id
    ))
    clue = world.add(Entity(id="clue", type="thing", label="clue"))
    tool = world.add(Entity(id="magic", type="thing", label=magic_cfg.label, phrase=magic_cfg.phrase))
    world.facts.update(hero=hero, parent=parent, frill=frill, mystery=mystery_cfg, magic=magic_cfg, clue=clue)
    return world


def tell(world: World, params: StoryParams) -> None:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    frill_cfg: FrillItem = FRILLS[params.frill]
    mystery_cfg: Mystery = world.facts["mystery"]
    magic_cfg: MagicTool = world.facts["magic"]

    hero.memes["curiosity"] = 1.0
    hero.memes["comfort"] = 1.0
    world.say(
        f"{hero.label} lived in {world.setting.place}, a house that always seemed to have enough everything."
        f" Even the rooms felt soft with wealth: polished tables, neat curtains, and little silver details."
    )
    world.say(
        f"Still, {hero.label} liked one humble thing best: {frill_cfg.phrase}."
        f" {hero.pronoun('possessive').capitalize()} {frill_cfg.label} made ordinary afternoons feel fancy."
    )

    world.para()
    world.say(
        f"One quiet afternoon, {hero.label} noticed something odd."
        f" {mystery_cfg.missing.capitalize()} was gone, and everyone had begun looking in drawers, bowls, and baskets."
    )
    world.say(
        f"{parent.label} frowned and said the missing thing had to be somewhere nearby, because the clue was simple:"
        f" {mystery_cfg.clue}."
    )
    hero.memes["worry"] = 1.0
    hero.memes["curiosity"] = 2.0

    world.para()
    world.say(
        f"{hero.label} fetched {magic_cfg.phrase} from a side table and held it over the room."
        f" The little light showed {magic_cfg.reveals}, and the bright edges made the search feel like a game."
    )
    world.magic_used = True
    if params.mystery == "missing_brooch":
        hidden = "the candy bowl"
        result = "the brooch glittered at the bottom of the bowl, tucked under a sticky lemon drop"
    elif params.mystery == "missing_key":
        hidden = "the sewing basket"
        result = "the key had slid under a spool of thread and flashed once in the lamp light"
    else:
        hidden = "the book with the blue ribbon"
        result = "the note was pressed flat inside the book, right where the ribbon had marked the page"

    world.say(f"The mystery was solved at last: {result}.")
    world.mystery_solved = True
    hero.memes["relief"] = 1.0

    world.para()
    frill = world.facts["frill"]
    frill.meters["damaged"] = 1.0
    frill.meters["creased"] = 1.0
    hero.memes["disappointment"] = 1.0
    world.say(
        f"But the story did not end perfectly."
        f" While everyone had been searching, {hero.label}'s {frill.label} had caught on a drawer handle and come away {frill_cfg.damage}."
    )
    world.say(
        f"{parent.label} touched the frill gently and said it could be mended, but not before tea."
        f" {hero.label} looked at the solved mystery, then at the damaged frill, and learned that a tidy home can still have an untidy moment."
    )
    world.say(
        f"By evening, the missing thing was found, the lamp was put away, and the frill hung over a chair instead of being worn."
        f" The room stayed warm and calm, but a little less shiny than before."
    )

    world.facts["hidden"] = hidden


def story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    magic: MagicTool = f["magic"]
    return [
        f"Write a slice-of-life story about {hero.label} in a wealthy home, a frilled thing, and a small mystery that magic helps solve.",
        f"Tell a gentle story where a child uses {magic.label} to find {mystery.missing}, but the ending is a little sad.",
        "Write a short domestic story with polished rooms, a decorative frill, a hidden object, and a bittersweet ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    mystery: Mystery = f["mystery"]
    frill_cfg: FrillItem = FRILLS[world.params.frill]
    magic_cfg: MagicTool = f["magic"]
    return [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"The story was mostly about {hero.label}, a curious child living in {world.setting.place}.",
        ),
        QAItem(
            question=f"What pretty thing did {hero.label} love most?",
            answer=f"{hero.label} loved {frill_cfg.phrase}, because it made ordinary afternoons feel special.",
        ),
        QAItem(
            question=f"What went missing in the story?",
            answer=f"{mystery.missing} went missing, and that was the mystery everyone searched for.",
        ),
        QAItem(
            question=f"How did {hero.label} help solve the mystery?",
            answer=f"{hero.label} used {magic_cfg.label} to look carefully around the room until the hidden thing was found.",
        ),
        QAItem(
            question=f"Why was the ending sad?",
            answer=f"The mystery was solved, but {hero.label}'s {frill_cfg.label} was damaged while everyone searched, so the day ended in a bittersweet way.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is wealth?",
            answer="Wealth means having a lot of money or valuable things, so a home can have nice rooms, polished furniture, and special keepsakes.",
        ),
        QAItem(
            question="What is a frill?",
            answer="A frill is a decorative ruffle or edge on clothing or cloth, and it can make something look fancy.",
        ),
        QAItem(
            question="What does magic do in a mystery story?",
            answer="Magic can help reveal clues, show hidden places, or make a search feel unusual and exciting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"  magic_used={world.magic_used}")
    lines.append(f"  mystery_solved={world.mystery_solved}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    world.params = params
    tell(world, params)
    return StorySample(
        params=params,
        story=story_text(world),
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


CURATED = [
    StoryParams(setting="sunroom", frill="dress_frill", mystery="missing_brooch", magic="glow_lamp", name="Mina", parent="Mother", trait="curious"),
    StoryParams(setting="parlor", frill="pillow_frill", mystery="missing_key", magic="moon_spoon", name="Clara", parent="Grandmother", trait="careful"),
    StoryParams(setting="hall", frill="curtain_frill", mystery="missing_note", magic="glow_lamp", name="Lena", parent="Aunt", trait="gentle"),
]


def asp_stories() -> list[tuple]:
    try:
        import asp
    except Exception:
        return []
    model = asp.one_model(asp_program("#show mystery_valid/3.\n#show bad_ending/2.\n#show solved/1."))
    out = []
    for sym in model:
        out.append((sym.name, len(sym.arguments)))
    return out


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show mystery_valid/3.\n#show bad_ending/2.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for the inline reasonableness gate.")
        print("Model atoms:", asp_stories())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.frill}, {p.mystery}, {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
