#!/usr/bin/env python3
"""
A standalone storyworld: a tiny nursery-rhyme tale about a child who inherits a
little piece of magic, learns that surprises can be gentle, and hears the sound
effects of wonder in a small shared home.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    keeper: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    magic: bool = False
    sound: bool = False
    surprise: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Home:
    place: str = "the little cottage"
    indoors: bool = True
    has_fireplace: bool = True
    has_window: bool = True
    setting_detail: str = "a warm room with a round rug and a bright lamp"


@dataclass
class StoryParams:
    name: str
    gender: str
    guardian: str
    heirloom: str
    setting: str = "the little cottage"
    seed: Optional[int] = None


class World:
    def __init__(self, home: Home):
        self.home = home
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.home)
        w.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

HOME = Home()

HEIRLOOMS = {
    "bell": {
        "label": "bell",
        "phrase": "a small silver bell with a blue ribbon",
        "sound": "jingle-jingle",
        "magic": "sparkle",
        "surprise": "surprise",
        "kind": "bell",
        "plural": False,
    },
    "lantern": {
        "label": "lantern",
        "phrase": "a tiny lantern with star cutouts",
        "sound": "twinkle-twinkle",
        "magic": "glow",
        "surprise": "surprise",
        "kind": "lantern",
        "plural": False,
    },
    "book": {
        "label": "book",
        "phrase": "a little storybook with a moon on the cover",
        "sound": "flip-flip",
        "magic": "shine",
        "surprise": "surprise",
        "kind": "book",
        "plural": False,
    },
}

GIVEN_NAMES = {
    "girl": ["Mia", "Luna", "Nora", "Ada", "Ivy"],
    "boy": ["Noah", "Eli", "Finn", "Owen", "Leo"],
}

GUARDIANS = {
    "mother": "mother",
    "father": "father",
    "grandma": "grandma",
    "grandpa": "grandpa",
}

TRAITS = ["small", "gentle", "curious", "bright", "cheery"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(params: StoryParams) -> bool:
    if params.gender not in GIVEN_NAMES:
        return False
    if params.guardian not in GUARDIANS:
        return False
    if params.heirloom not in HEIRLOOMS:
        return False
    return True


def explain_invalid(params: StoryParams) -> str:
    return "That story choice does not fit this tiny home of magic and surprise."


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def nursery_rhyme_opening(name: str, trait: str, guardian: str, setting: str) -> list[str]:
    return [
        f"In {setting}, {name} was {trait} and small,",
        f"with {guardian} nearby in the warm little hall.",
    ]


def teach_inherit(world: World, child: Entity, guardian: Entity, heirloom: Entity) -> None:
    world.say(
        f'{guardian.id} smiled and said, "This {heirloom.label} is yours to inherit, '
        f'{child.id}."'
    )
    world.say(
        f"The word inherit felt like a soft song: a gift from old hands to new."
    )


def wake_magic(world: World, heirloom: Entity) -> None:
    heirloom.meters["magic"] = 1.0
    heirloom.memes["wonder"] = 1.0
    world.say(
        f'At once the {heirloom.label} went "{HEIRLOOMS[heirloom.type]["sound"]}!" '
        f'and gave a little {HEIRLOOMS[heirloom.type]["magic"]}.'
    )


def surprise(world: World, child: Entity, guardian: Entity, heirloom: Entity) -> None:
    child.memes["surprise"] = 1.0
    world.say(
        f"{child.id} blinked in surprise, then giggled with delight."
    )
    world.say(
        f'Nobody expected the "{HEIRLOOMS[heirloom.type]["sound"]}" to sound so bright.'
    )


def share_sound(world: World, child: Entity, guardian: Entity, heirloom: Entity) -> None:
    child.memes["joy"] = 1.0
    guardian.memes["warmth"] = 1.0
    world.say(
        f"{child.id} shook the little {heirloom.label}, and {HEIRLOOMS[heirloom.type]['sound']} went the tune."
    )
    world.say(
        f"{guardian.id} clapped along, and the room felt merry as June."
    )


def closing(world: World, child: Entity, guardian: Entity, heirloom: Entity) -> None:
    world.say(
        f"So {child.id} kept the {heirloom.label}, inherited with care,"
    )
    world.say(
        f"and the magic, the surprise, and the music stayed there."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    if not valid_combo(params):
        raise StoryError(explain_invalid(params))

    home = Home(place=params.setting)
    world = World(home)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        traits=["small", "gentle"],
    ))
    guardian = world.add(Entity(
        id=params.guardian,
        kind="character",
        type=params.guardian,
        label=params.guardian,
        traits=["kind", "careful"],
    ))
    heir_def = HEIRLOOMS[params.heirloom]
    heirloom = world.add(Entity(
        id=params.heirloom,
        kind="thing",
        type=params.heirloom,
        label=heir_def["label"],
        phrase=heir_def["phrase"],
        owner=child.id,
        keeper=guardian.id,
        plural=heir_def["plural"],
        magic=True,
        sound=True,
        surprise=True,
    ))

    world.say(nursery_rhyme_opening(child.id, "gentle", guardian.label, world.home.place)[0])
    world.say(nursery_rhyme_opening(child.id, "gentle", guardian.label, world.home.place)[1])
    world.para()
    world.say(
        f"In a drawer by the lamp, {guardian.id} found {heirloom.phrase}."
    )
    world.say(
        f'"One day," {guardian.id} said, "you will inherit this little treasure."'
    )
    teach_inherit(world, child, guardian, heirloom)
    world.para()
    wake_magic(world, heirloom)
    surprise(world, child, guardian, heirloom)
    share_sound(world, child, guardian, heirloom)
    world.para()
    closing(world, child, guardian, heirloom)

    world.facts.update(
        child=child,
        guardian=guardian,
        heirloom=heirloom,
        heirloom_def=heir_def,
        setting=home,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    guardian: Entity = f["guardian"]
    heir_def = f["heirloom_def"]
    return [
        f"Write a nursery-rhyme style story about {child.id} who inherits {heir_def['phrase']} from {guardian.label}.",
        f"Tell a short magical story where the word inherit matters and a little {heirloom_noun(heir_def)} makes a surprise sound.",
        f"Make a gentle rhyme about family, magic, and the sound '{heir_def['sound']}' in a cozy home.",
    ]


def heirloom_noun(heir_def: dict) -> str:
    return heir_def["label"]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    guardian: Entity = f["guardian"]
    heirloom: Entity = f["heirloom"]
    heir_def = f["heirloom_def"]
    return [
        QAItem(
            question=f"What did {child.id} inherit?",
            answer=f"{child.id} inherited {heirloom.phrase} from {guardian.label}.",
        ),
        QAItem(
            question=f"Why was the moment a surprise?",
            answer=f"It was a surprise because the {heirloom.label} suddenly made {heir_def['sound']} and showed its little magic.",
        ),
        QAItem(
            question=f"What sound did the {heirloom.label} make?",
            answer=f"The {heirloom.label} went {heir_def['sound']}.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt happy and delighted, because the inherited {heirloom.label} was a family treasure with magic in it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does inherit mean?",
            answer="To inherit means to receive something from a family member or someone who gives it to you to keep.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes someone blink, smile, or laugh.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that help readers hear a noise in their imagination, like jingles, pops, or taps.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something special and impossible-looking that can make ordinary things shine, glow, or change in a wonder-filled way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
story(X) :- child(X), heirloom(H), inherits(X,H), magic(H), surprise(H), sound(H).
valid(G, H) :- child_gender(G), heirloom(H), family_heirloom(H), compatible(H).
compatible(bell).
compatible(lantern).
compatible(book).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for gender, names in GIVEN_NAMES.items():
        lines.append(asp.fact("child_gender", gender))
        for n in names:
            lines.append(asp.fact("child_name", n))
    for g in GUARDIANS:
        lines.append(asp.fact("guardian_kind", g))
    for h, d in HEIRLOOMS.items():
        lines.append(asp.fact("heirloom", h))
        lines.append(asp.fact("family_heirloom", h))
        if d["magic"]:
            lines.append(asp.fact("magic", h))
        if d["surprise"]:
            lines.append(asp.fact("surprise", h))
        if d["sound"]:
            lines.append(asp.fact("sound", h))
        lines.append(asp.fact("inherits", "x", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = {(g, h) for g in GIVEN_NAMES for h in HEIRLOOMS}
    if asp_set == py_set:
        print(f"OK: ASP and Python agree on {len(py_set)} compatible pairs.")
        return 0
    print("MISMATCH between ASP and Python:")
    if asp_set - py_set:
        print("  only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny nursery-rhyme story world about inherit, magic, surprise, and sound effects.")
    ap.add_argument("--name", choices=sorted({n for ns in GIVEN_NAMES.values() for n in ns}))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=sorted(GUARDIANS))
    ap.add_argument("--heirloom", choices=sorted(HEIRLOOMS))
    ap.add_argument("--setting", default="the little cottage")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gender and args.name is None:
        name = rng.choice(GIVEN_NAMES[args.gender])
    elif args.name is not None:
        name = args.name
    else:
        gender = args.gender or rng.choice(["girl", "boy"])
        name = rng.choice(GIVEN_NAMES[gender])
    gender = args.gender or ("girl" if name in GIVEN_NAMES["girl"] else "boy")
    guardian = args.guardian or rng.choice(list(GUARDIANS))
    heirloom = args.heirloom or rng.choice(list(HEIRLOOMS))
    params = StoryParams(
        name=name,
        gender=gender,
        guardian=guardian,
        heirloom=heirloom,
        setting=args.setting,
    )
    if not valid_combo(params):
        raise StoryError(explain_invalid(params))
    return params


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.magic:
            bits.append("magic")
        if e.sound:
            bits.append("sound")
        if e.surprise:
            bits.append("surprise")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.keeper:
            bits.append(f"keeper={e.keeper}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) " + " ".join(bits))
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


CURATED = [
    StoryParams(name="Mia", gender="girl", guardian="mother", heirloom="bell"),
    StoryParams(name="Noah", gender="boy", guardian="grandma", heirloom="lantern"),
    StoryParams(name="Luna", gender="girl", guardian="father", heirloom="book"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid pairs:")
        for g, h in vals:
            print(f"  {g} {h}")
        return

    rng_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = rng_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, s in enumerate(samples):
        header = ""
        if args.all:
            p = s.params
            header = f"### {p.name}: {p.heirloom} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if idx + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
