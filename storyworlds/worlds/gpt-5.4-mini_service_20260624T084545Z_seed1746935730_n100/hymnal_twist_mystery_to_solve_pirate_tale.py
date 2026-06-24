#!/usr/bin/env python3
"""
storyworlds/worlds/hymnal_twist_mystery_to_solve_pirate_tale.py
===============================================================

A small pirate tale storyworld with a hymnal, a mystery to solve, and a twist.

Premise:
- A child pirate on a ship or at a harbor loves singing from a hymnal.
- Something puzzling happens: the ship's bell, lantern, or map clue goes missing.
- The crew investigates by following a song hidden in the hymnal.
- Twist: the "mystery" is solved by discovering the hymnal itself contains a sea-shanty clue, not by a thief.

The world model tracks physical meters and emotional memes:
- meters: clue_bits, tide, lantern_oil, stash, wet, wear, ink
- memes: curiosity, worry, bravery, delight, suspicion, trust

The prose is driven by changes in the simulated state, not a frozen template.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str = "the Bright Gull"
    place: str = "the ship"
    harbor: str = "the harbor"
    hold: str = "the cargo hold"
    weather: str = "foggy"
    tide: str = "low"


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    details: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    thing: str
    missing_from: str
    clue_kind: str
    risk_kind: str
    twist_kind: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hymnal:
    id: str
    label: str
    phrase: str
    is_old: bool = True
    pages: int = 12
    sings: set[str] = field(default_factory=set)
    hides: set[str] = field(default_factory=set)


SETTINGS = {
    "harbor": Setting(
        place="the harbor",
        details="The harbor had creaky docks, rope coils, and gulls that cried overhead.",
        affords={"search", "sing", "row"},
    ),
    "deck": Setting(
        place="the deck",
        details="The deck smelled of tar, salt, and wet wood, with a lantern hanging by the mast.",
        affords={"search", "sing", "row"},
    ),
    "cabin": Setting(
        place="the cabin",
        details="The cabin was snug and dim, with a table, a map chest, and a little lamp.",
        affords={"search", "sing"},
    ),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        thing="ship's bell",
        missing_from="the mast",
        clue_kind="ringing",
        risk_kind="silent",
        twist_kind="hymn",
        reveal="the bell was never stolen; the hymn page described where it was moved during cleaning",
        tags={"bell", "sound"},
    ),
    "map": Mystery(
        id="map",
        thing="treasure map",
        missing_from="the cabin table",
        clue_kind="ink",
        risk_kind="lost",
        twist_kind="chorus",
        reveal="the map had been tucked into the hymnal as a bookmark",
        tags={"map", "ink"},
    ),
    "lantern": Mystery(
        id="lantern",
        thing="lantern",
        missing_from="the rail",
        clue_kind="light",
        risk_kind="dark",
        twist_kind="verse",
        reveal="the lantern was lit and carried below deck to follow the song's clue",
        tags={"lantern", "light"},
    ),
}

HYMNALES = {
    "sea_hymn": Hymnal(
        id="sea_hymn",
        label="hymnal",
        phrase="an old hymnal with a blue cover and salt-stained pages",
        sings={"hymn", "chorus", "verse"},
        hides={"map", "ink", "bell"},
    ),
    "shore_book": Hymnal(
        id="shore_book",
        label="hymnal",
        phrase="a small hymnal tied with twine",
        sings={"hymn", "verse"},
        hides={"lantern", "light"},
    ),
}

GIRL_NAMES = ["Mara", "Nina", "Tess", "Ava", "Lina", "Pia"]
BOY_NAMES = ["Finn", "Owen", "Rafe", "Jory", "Ned", "Tobin"]
TRAITS = ["brave", "curious", "quick", "cheery", "bold"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    mystery: str
    hymnal: str
    name: str
    gender: str
    shipmate: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting: Setting, mystery: Mystery, hymnal: Hymnal) -> bool:
    if mystery.id == "bell" and setting.place == "the cabin":
        return False
    if mystery.id == "lantern" and setting.place == "the harbor":
        return False
    if mystery.id == "map" and "map" not in hymnal.hides:
        return False
    if mystery.id == "bell" and "bell" not in hymnal.hides:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, s in SETTINGS.items():
        for m_id, m in MYSTERIES.items():
            for h_id, h in HYMNALES.items():
                if valid_combo(s, m, h):
                    combos.append((s_id, m_id, h_id))
    return combos


def explain_rejection(setting: Setting, mystery: Mystery, hymnal: Hymnal) -> str:
    return (
        f"(No story: {mystery.thing} and {hymnal.label} do not fit a clear pirate mystery "
        f"at {setting.place}. Try another combination where the songbook can hide a clue.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    ship = Ship(place=SETTINGS[params.setting].place)
    world = World(ship)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"wet": 0.0, "wear": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "bravery": 1.0, "delight": 0.0, "suspicion": 0.0, "trust": 1.0},
    ))
    mate = world.add(Entity(
        id="Mate",
        kind="character",
        type="pirate",
        label=params.shipmate,
        meters={"wet": 0.0, "wear": 0.0},
        memes={"curiosity": 0.5, "worry": 0.0, "bravery": 1.0, "delight": 0.0, "suspicion": 0.0, "trust": 1.0},
    ))
    hymnal = world.add(Entity(
        id="Hymnal",
        type="thing",
        label="hymnal",
        phrase=HYMNALES[params.hymnal].phrase,
        owner=hero.id,
        meters={"ink": 0.0, "pages": float(HYMNALES[params.hymnal].pages)},
        memes={"mystery": 1.0},
    ))
    mystery = world.add(Entity(
        id="Mystery",
        type="thing",
        label=MYSTERIES[params.mystery].thing,
        phrase=MYSTERIES[params.mystery].thing,
        owner=None,
        meters={"missing": 1.0},
        memes={"mystery": 1.0},
    ))

    world.facts.update(
        hero=hero,
        mate=mate,
        hymnal=hymnal,
        mystery=mystery,
        setting=SETTINGS[params.setting],
        mystery_def=MYSTERIES[params.mystery],
        hymnal_def=HYMNALES[params.hymnal],
    )

    # Act 1
    world.say(
        f"{hero.id} was a little {params.trait} pirate who loved the sea and a good song."
    )
    world.say(
        f"{hero.id} carried {hymnal.phrase} wherever {hero.pronoun('subject')} went, "
        f"because the old songs made {hero.pronoun('object')} feel bold."
    )
    world.say(SETTINGS[params.setting].details)

    world.para()

    # Act 2
    mystery_def = MYSTERIES[params.mystery]
    world.say(
        f"One day, the crew found that {mystery_def.thing} was gone from {mystery_def.missing_from}."
    )
    hero.memes["worry"] += 1.0
    mate.memes["suspicion"] += 1.0
    world.say(
        f"{hero.id} squinted at the empty spot and felt a puzzle tug at {hero.pronoun('possessive')} chest."
    )
    world.say(
        f"{params.shipmate} muttered that a thief might be close by, but the tiny clue did not fit a sneaky thief."
    )

    if params.mystery == "map":
        hymnal.meters["ink"] += 1.0
        world.say(
            f"When {hero.id} opened the hymnal, a folded scrap slipped out from between the pages."
        )
    elif params.mystery == "bell":
        hymnal.memes["mystery"] += 1.0
        world.say(
            f"{hero.id} thumbed through the hymnal and noticed a verse about bells, brushing the page with care."
        )
    else:
        hymnal.memes["mystery"] += 1.0
        world.say(
            f"A salt-stiff page in the hymnal hinted that someone had lit the lantern for a reason."
        )

    world.para()

    # Act 3: twist and solve
    hero.memes["curiosity"] += 1.0
    mate.memes["trust"] += 1.0

    if params.mystery == "map":
        world.say(
            f"The twist was that the treasure map had been used as a bookmark in the hymnal all along."
        )
        world.say(
            f"{hero.id} found the map tucked safely inside, and the crew laughed at the clever hiding place."
        )
    elif params.mystery == "bell":
        world.say(
            f"The twist was that the hymn's chorus told the deckhands where the bell had been moved during cleaning."
        )
        world.say(
            f"The bell was not stolen at all; it was hanging below, waiting to be put back in the right place."
        )
    else:
        world.say(
            f"The twist was that the lantern belonged with the song, because the verses guided the crew below deck."
        )
        world.say(
            f"With the lantern lit, {hero.id} and {params.shipmate} followed the hymn to the hidden corner and solved the mystery."
        )

    world.say(
        f"In the end, {hero.id} smiled, the crew felt brave again, and the old hymnal was still safe in {hero.pronoun('possessive')} hands."
    )

    return world


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery_def"]
    hymnal = f["hymnal_def"]
    setting = f["setting"]
    return [
        f'Write a pirate tale for a small child about a {hero.type} who loves a {hymnal.label} and must solve a mystery at {setting.place}.',
        f'Tell a short story where {hero.id} follows a song clue in an old {hymnal.label} to find {mystery.thing}.',
        f'Write a gentle pirate adventure with a twist: the missing {mystery.thing} is explained by a clue hidden in a {hymnal.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    mystery = f["mystery_def"]
    hymnal = f["hymnal_def"]
    setting = f["setting"]

    return [
        QAItem(
            question=f"What did {hero.id} love to carry on the pirate adventure?",
            answer=f"{hero.id} loved carrying {hymnal.phrase} because the old songs made {hero.pronoun('object')} feel bold.",
        ),
        QAItem(
            question=f"What was missing from {mystery.missing_from} at {setting.place}?",
            answer=f"{mystery.thing} was missing from {mystery.missing_from}.",
        ),
        QAItem(
            question=f"Who thought a thief might be nearby?",
            answer=f"{mate.label} thought a thief might be nearby, but the clue turned out to be hiding in the hymnal.",
        ),
        QAItem(
            question=f"What solved the mystery in the end?",
            answer=f"The mystery was solved by following the song clue in the hymnal and discovering the hidden truth.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hymnal?",
            answer="A hymnal is a book of songs, often used for singing hymns together.",
        ),
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat that sails the sea and carries a pirate crew.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people try to figure out.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A setting can host a mystery when it affords searching.
can_search(S) :- affords(S, search).

% A hymnal can hide clues when it stores the matching clue type.
can_hide(H, M) :- hymnal(H), mystery(M), hides(H, T), clue_kind(M, T).

% A story is valid when the setting supports search and the hymnal can hide
% the mystery's clue kind.
valid_story(S, M, H) :- can_search(S), can_hide(H, M).

% Twist: the clue is embedded in the hymnal rather than stolen.
twist(H, M) :- valid_story(_, M, H).

#show valid_story/3.
#show twist/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_kind", mid, m.clue_kind))
        lines.append(asp.fact("twist_kind", mid, m.twist_kind))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    for hid, h in HYMNALES.items():
        lines.append(asp.fact("hymnal", hid))
        for t in sorted(h.sings):
            lines.append(asp.fact("sings", hid, t))
        for t in sorted(h.hides):
            lines.append(asp.fact("hides", hid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - ap:
        print("  only in python:", sorted(py - ap))
    if ap - py:
        print("  only in clingo:", sorted(ap - py))
    return 1


# ---------------------------------------------------------------------------
# Param handling
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate mystery tale with a hymnal twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hymnal", choices=HYMNALES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--shipmate")
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if args.hymnal:
        combos = [c for c in combos if c[2] == args.hymnal]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, hymnal = rng.choice(sorted(combos))

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    shipmate = args.shipmate or rng.choice(["Captain Reef", "Old Sal", "Nell Tide", "Rook"])
    trait = args.trait or rng.choice(TRAITS)

    if args.gender and args.name is None:
        # allow either gender; no extra restriction needed here
        pass

    return StoryParams(
        setting=setting,
        mystery=mystery,
        hymnal=hymnal,
        name=name,
        gender=gender,
        shipmate=shipmate,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=story_text(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def explain_options(args: argparse.Namespace) -> None:
    if args.setting and args.mystery and args.hymnal:
        s, m, h = SETTINGS[args.setting], MYSTERIES[args.mystery], HYMNALES[args.hymnal]
        if not valid_combo(s, m, h):
            raise StoryError(explain_rejection(s, m, h))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3.\n#show twist/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3.\n#show twist/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:\n")
        for s, m, h in combos:
            print(f"  {s:8} {m:10} {h:10}")
        return

    explain_options(args)
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for s, m, h in sorted(valid_combos()):
            params = StoryParams(
                setting=s,
                mystery=m,
                hymnal=h,
                name="Mara",
                gender="girl",
                shipmate="Captain Reef",
                trait="curious",
                seed=None,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
            header = f"### {p.name}: {p.mystery} at {p.setting} with {p.hymnal}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
