#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/set_trinket_wag_flashback_misunderstanding_pirate_tale.py
=================================================================================================

A small pirate-tale storyworld about a crew, a treasured trinket, a wagging parrot,
and a misunderstanding that gets untangled by a flashback.

Premise:
- A young deckhand wants to keep a shiny trinket safe during a seaside errand.
- The crew misreads the wagging parrot's signals and thinks the trinket is stolen.
- A flashback reveals where the trinket really came from.
- The misunderstanding resolves when the crew returns the trinket to its proper place.

The story is grounded in a tiny simulated world:
- physical meters: who holds what, where items are set, and whether the trinket is safe
- emotional memes: trust, worry, confusion, relief, and pride
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dock"
    weather: str = "breezy"


@dataclass
class Trinket:
    label: str
    phrase: str
    kind: str = "trinket"
    safe_place: str = "neck pouch"
    shiny: bool = True


@dataclass
class CrewRole:
    id: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    name: str = "Mira"
    gender: str = "girl"
    captain: str = "Captain Rook"
    companion: str = "Nell"
    parrot: str = "Skipper"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "dock": Setting(place="the dock", weather="breezy"),
    "cove": Setting(place="the cove", weather="salt-sprayed"),
    "ship": Setting(place="the little ship", weather="rocking"),
}

TRINKETS = {
    "set": Trinket(
        label="set",
        phrase="a small brass set of ship bells",
        safe_place="a padded chest",
    ),
    "trinket": Trinket(
        label="trinket",
        phrase="a tiny pearl trinket on a blue string",
        safe_place="a neck pouch",
    ),
    "wag": Trinket(
        label="wag",
        phrase="a bright wooden wag charm",
        safe_place="a belt loop",
    ),
}

# The seed words are kept as valid identifiers and story vocabulary.
TRINKET_ORDER = ["set", "trinket", "wag"]

GENDER_TYPES = {
    "girl": "girl",
    "boy": "boy",
}

TALES = {
    "set": {
        "want": "set the little bells in a safe place",
        "flashback": "she had found the bells in a storm-tossed chest the day before",
        "misread": "the crew thought the bells had gone missing",
        "resolve": "the bells were set back where they belonged",
        "ending": "their soft clink sounded like a happy tune",
    },
    "trinket": {
        "want": "keep the trinket safe from the sea spray",
        "flashback": "she had been given the trinket by her grandmother before the voyage",
        "misread": "the crew thought someone had snatched the trinket",
        "resolve": "the trinket was tucked back into its neck pouch",
        "ending": "it gleamed safely against her shirt",
    },
    "wag": {
        "want": "show the wag charm to the crew",
        "flashback": "the wag charm had been tied to the parrot's perch as a lucky sign",
        "misread": "the crew thought the wagging parrot was warning them of trouble",
        "resolve": "the wag charm was tied to the rail again",
        "ending": "the parrot wagged happily instead of warning anyone",
    },
}


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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

        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Entity, Entity]:
    setting = SETTINGS["dock"]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    captain = world.add(Entity(id=params.captain, kind="character", type="captain", label=params.captain))
    companion = world.add(Entity(id=params.companion, kind="character", type="mate", label=params.companion))
    parrot = world.add(Entity(id=params.parrot, kind="character", type="parrot", label=params.parrot))

    trinket_key = "trinket"
    trinket_cfg = TRINKETS[trinket_key]
    trinket = world.add(Entity(
        id="trinket",
        type="thing",
        label=trinket_cfg.label,
        phrase=trinket_cfg.phrase,
        owner=hero.id,
        held_by=hero.id,
        location=trinket_cfg.safe_place,
        meters={"safe": 1.0, "seen": 1.0},
    ))

    parrot.meters["wagging"] = 1.0
    parrot.location = "the rail"
    hero.memes.update({"hope": 1.0, "trust": 1.0})
    captain.memes.update({"worry": 0.0, "trust": 1.0})
    companion.memes.update({"curious": 1.0})
    world.facts.update(trinket_key=trinket_key)
    return world, hero, captain, companion, parrot, trinket


def flashback_line(trinket_key: str) -> str:
    return TALES[trinket_key]["flashback"]


def do_setup(world: World, hero: Entity, trinket: Entity, trinket_key: str) -> None:
    world.say(f"{hero.id} was a young deckhand who liked the salty wind and the creak of ropes.")
    world.say(f"{hero.id} carried {hero.pronoun('possessive')} {trinket.label} because it felt lucky.")
    world.say(f"The little pirate crew had a bright day ahead of them near {world.setting.place}.")
    world.say(f"It was the kind of day that made even small treasures feel important.")


def do_misunderstanding(world: World, hero: Entity, captain: Entity, companion: Entity, parrot: Entity, trinket: Entity, trinket_key: str) -> None:
    world.para()
    world.say(f"At the dock, {parrot.id} began to wag on the rail while the breeze pushed its feathers side to side.")
    world.say(f"{companion.id} pointed and said the wagging looked like a warning.")
    world.say(f"{captain.id} frowned and thought someone must have taken {hero.pronoun('possessive')} {trinket.label}.")
    captain.memes["worry"] = 1.0
    captain.memes["misunderstanding"] = 1.0
    hero.memes["confusion"] = 1.0
    hero.memes["hurt"] = 0.5
    trinket.meters["safe"] = 0.0
    trinket.location = "in plain view"
    world.say(f"{hero.id} looked startled, because {hero.pronoun('possessive')} {trinket.label} had only been set down while tying a knot.")


def do_flashback(world: World, hero: Entity, captain: Entity, companion: Entity, parrot: Entity, trinket: Entity, trinket_key: str) -> None:
    world.para()
    world.say("Then the story flashed back to the morning before the sail.")
    world.say(flashback_line(trinket_key))
    world.say(f"That memory showed {hero.id} setting the {trinket.label} carefully beside {hero.pronoun('possessive')} gear before the trip.")
    world.say(f"It was never stolen; it had simply been moved and then forgotten in the rush of work.")
    hero.memes["confidence"] = 1.0
    captain.memes["worry"] = 0.2
    captain.memes["misunderstanding"] = 0.0


def resolve(world: World, hero: Entity, captain: Entity, companion: Entity, parrot: Entity, trinket: Entity, trinket_key: str) -> None:
    world.para()
    world.say(f"{hero.id} reached for the {trinket.label} and showed everyone where it had been left.")
    world.say(f"{captain.id} blinked, then laughed at the mistake.")
    world.say(f"{companion.id} gave a sheepish grin, and even {parrot.id} wagged as if it knew the truth all along.")
    trinket.held_by = hero.id
    trinket.location = TRINKETS[trinket_key].safe_place
    trinket.meters["safe"] = 1.0
    hero.memes["relief"] = 1.0
    hero.memes["pride"] = 1.0
    captain.memes["trust"] = 1.0
    companion.memes["relief"] = 1.0
    world.say(f"By the end, the {trinket.label} was tucked back where it belonged, and the crew felt better for the honest mistake.")
    world.say(TALES[trinket_key]["ending"] + ".")


def tell(params: StoryParams) -> World:
    world, hero, captain, companion, parrot, trinket = setup_world(params)
    trinket_key = world.facts["trinket_key"]
    do_setup(world, hero, trinket, trinket_key)
    do_misunderstanding(world, hero, captain, companion, parrot, trinket, trinket_key)
    do_flashback(world, hero, captain, companion, parrot, trinket, trinket_key)
    resolve(world, hero, captain, companion, parrot, trinket, trinket_key)
    world.facts.update(hero=hero, captain=captain, companion=companion, parrot=parrot, trinket=trinket)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
has_trinket(T) :- trinket(T).
wagging(P) :- parrot(P).

misunderstanding(H, C, P, T) :- hero(H), captain(C), wagging(P), has_trinket(T).
flashback_reveals(T) :- trinket(T).
resolved(T) :- flashback_reveals(T), has_trinket(T).

#show misunderstanding/4.
#show flashback_reveals/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("hero_name", "Mira"))
    lines.append(asp.fact("hero_name", "Jory"))
    lines.append(asp.fact("captain", "Captain Rook"))
    lines.append(asp.fact("parrot", "Skipper"))
    for key in TRINKETS:
        lines.append(asp.fact("trinket", key))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    mis = set(asp.atoms(model, "misunderstanding"))
    flash = set(asp.atoms(model, "flashback_reveals"))
    resolved = set(asp.atoms(model, "resolved"))

    expected_mis = {
        ("Mira", "Captain Rook", "Skipper", "set"),
        ("Mira", "Captain Rook", "Skipper", "trinket"),
        ("Mira", "Captain Rook", "Skipper", "wag"),
        ("Jory", "Captain Rook", "Skipper", "set"),
        ("Jory", "Captain Rook", "Skipper", "trinket"),
        ("Jory", "Captain Rook", "Skipper", "wag"),
    }
    expected_flash = {("set",), ("trinket",), ("wag",)}
    expected_resolved = {("set",), ("trinket",), ("wag",)}

    if mis == expected_mis and flash == expected_flash and resolved == expected_resolved:
        print("OK: ASP parity verified.")
        return 0
    print("ASP mismatch")
    print("mis:", sorted(mis))
    print("flash:", sorted(flash))
    print("resolved:", sorted(resolved))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    trinket_key = world.facts["trinket_key"]
    t = TRINKETS[trinket_key]
    hero = world.facts["hero"]
    return [
        f"Write a short pirate tale for a child named {hero.id} and the {t.label} on a breezy dock.",
        f"Tell a story where a wagging parrot causes a misunderstanding, but a flashback clears it up.",
        f"Write a gentle pirate story about a lost-looking {t.label} that was only set aside, not stolen.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    captain: Entity = world.facts["captain"]
    parrot: Entity = world.facts["parrot"]
    trinket: Entity = world.facts["trinket"]
    trinket_key = world.facts["trinket_key"]

    return [
        QAItem(
            question=f"Why did {captain.id} think there was trouble when {parrot.id} wagged on the rail?",
            answer=f"{captain.id} had a misunderstanding and thought someone had taken the {trinket.label}, because the wagging looked like a warning to the crew.",
        ),
        QAItem(
            question=f"What did the flashback show about the {trinket.label}?",
            answer=f"The flashback showed that {hero.id} had set the {trinket.label} aside earlier, so it was not stolen at all.",
        ),
        QAItem(
            question=f"What happened to the {trinket.label} at the end?",
            answer=f"The {trinket.label} was tucked back where it belonged, and the crew felt relieved and embarrassed about the mistake.",
        ),
        QAItem(
            question=f"How did the wagging parrot help solve the misunderstanding?",
            answer=f"The wagging parrot made everyone look closely, and that helped {hero.id} remember the truth about where the {trinket.label} had been set.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a trinket?",
            answer="A trinket is a small special object, often kept because it is lucky, pretty, or meaningful.",
        ),
        QAItem(
            question="What does it mean to set something down?",
            answer="To set something down means to place it carefully somewhere for a moment.",
        ),
        QAItem(
            question="Why can a misunderstanding happen?",
            answer="A misunderstanding can happen when people see the same thing but think it means something different.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a trinket, a wagging parrot, a flashback, and a misunderstanding.")
    ap.add_argument("--name", choices=["Mira", "Jory", "Pip", "Sana"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain")
    ap.add_argument("--companion")
    ap.add_argument("--parrot")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(["Mira", "Jory", "Pip", "Sana"]) if gender == "girl" else rng.choice(["Jory", "Pip", "Sana", "Mira"])
    return StoryParams(
        name=name,
        gender=gender,
        captain=args.captain or "Captain Rook",
        companion=args.companion or "Nell",
        parrot=args.parrot or "Skipper",
        seed=args.seed,
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
        if e.location:
            bits.append(f"location={e.location}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print(asp.atoms(model, "misunderstanding"))
        print(asp.atoms(model, "flashback_reveals"))
        print(asp.atoms(model, "resolved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()

    if args.all:
        params = [
            StoryParams(name="Mira", gender="girl"),
            StoryParams(name="Jory", gender="boy"),
            StoryParams(name="Pip", gender="boy"),
        ]
        for p in params:
            samples.append(generate(p))
    else:
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
