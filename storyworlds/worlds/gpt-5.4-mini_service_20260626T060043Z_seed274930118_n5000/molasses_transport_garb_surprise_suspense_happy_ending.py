#!/usr/bin/env python3
"""
A small mystery-flavored storyworld about a careful transport, a sticky spill,
and a surprising hidden piece of garb that changes the ending.

The premise:
- A child or helper is transporting a jar or crate of molasses.
- The path is uncertain, so the story builds suspense.
- A surprise is discovered in the garb or cargo.
- The ending is happy because the mystery is solved without ruining the cargo.

This script follows the Storyweavers contract: it defines a simulated world,
a reasonableness gate, an inline ASP twin, and the standard CLI/QA interface.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    contains: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False
    has_path: bool = True
    has_stairs: bool = False
    has_hidey_place: bool = False


@dataclass
class Cargo:
    label: str
    phrase: str
    spill: str
    scent: str
    weight: int = 1


@dataclass
class Garb:
    id: str
    label: str
    phrase: str
    cover: str
    surprise_hide: bool = False
    protective: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path_hazard: float = 0.0
        self.hidden_note_found: bool = False

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
        clone.path_hazard = self.path_hazard
        clone.hidden_note_found = self.hidden_note_found
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    courier = world.get("courier")
    cargo = world.get("cargo")
    if courier.memes.get("jostle", 0.0) < THRESHOLD:
        return out
    if cargo.meters.get("secure", 0.0) >= THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.meters["sticky"] = 1.0
    cargo.meters["risk"] = 1.0
    out.append("The jar trembled, and the molasses threatened to leak.")
    return out


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    if world.path_hazard < THRESHOLD:
        return out
    if ("suspense",) in world.fired:
        return out
    world.fired.add(("suspense",))
    out.append("The narrow path made every step feel like a clue waiting to be found.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    courier = world.get("courier")
    cargo = world.get("cargo")
    garb = world.get("garb")
    if cargo.meters.get("sticky", 0.0) < THRESHOLD:
        return out
    if garb.meters.get("open", 0.0) < THRESHOLD:
        return out
    if ("surprise",) in world.fired:
        return out
    world.fired.add(("surprise",))
    world.hidden_note_found = True
    courier.memes["surprise"] = courier.memes.get("surprise", 0.0) + 1.0
    out.append("Inside the garb, a little note explained the secret route.")
    return out


def _r_happy(world: World) -> list[str]:
    out: list[str] = []
    courier = world.get("courier")
    cargo = world.get("cargo")
    if cargo.meters.get("sticky", 0.0) < THRESHOLD:
        return out
    if world.hidden_note_found and ("happy",) not in world.fired:
        world.fired.add(("happy",))
        courier.memes["relief"] = courier.memes.get("relief", 0.0) + 1.0
        cargo.meters["delivered"] = 1.0
        out.append("They followed the hidden note and delivered the molasses safely at last.")
    return out


RULES = [
    _r_suspense,
    _r_spill,
    _r_surprise,
    _r_happy,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_spill(world: World) -> bool:
    sim = world.copy()
    courier = sim.get("courier")
    courier.memes["jostle"] = 1.0
    propagate(sim, narrate=False)
    return sim.get("cargo").meters.get("sticky", 0.0) >= THRESHOLD


def build_garb() -> Garb:
    return Garb(
        id="garb",
        label="wrapped garb",
        phrase="a folded bundle of old garb",
        cover="cargo",
        surprise_hide=True,
        protective=True,
    )


def build_cargo() -> Cargo:
    return Cargo(
        label="molasses",
        phrase="a heavy jar of molasses",
        spill="sticky",
        scent="sweet",
        weight=2,
    )


def build_setting(place: str) -> Setting:
    settings = {
        "lane": Setting(place="the lamp-lit lane", indoor=False, has_path=True, has_stairs=False, has_hidey_place=True),
        "stairs": Setting(place="the old stairway", indoor=False, has_path=True, has_stairs=True, has_hidey_place=False),
        "attic": Setting(place="the dusty attic", indoor=True, has_path=False, has_stairs=True, has_hidey_place=True),
    }
    return settings[place]


@dataclass
class StoryParams:
    place: str
    name: str
    role: str
    seed: Optional[int] = None


SETTINGS = {
    "lane": build_setting("lane"),
    "stairs": build_setting("stairs"),
    "attic": build_setting("attic"),
}

ROLES = {
    "girl": "girl",
    "boy": "boy",
}

NAMES = {
    "girl": ["Mina", "Lena", "Ivy", "Nora", "June"],
    "boy": ["Toby", "Finn", "Eli", "Milo", "Theo"],
}

CURATED = [
    StoryParams(place="lane", name="Mina", role="girl"),
    StoryParams(place="stairs", name="Toby", role="boy"),
    StoryParams(place="attic", name="Ivy", role="girl"),
]


def reasonableness_gate(params: StoryParams) -> None:
    setting = SETTINGS[params.place]
    if not setting.has_path and setting.place != "the dusty attic":
        raise StoryError("This story needs a route for the molasses transport.")
    if params.role not in ROLES:
        raise StoryError("Unknown role.")
    if setting.has_hidey_place is False and setting.indoor is False and setting.has_stairs is False:
        raise StoryError("This world needs either a hiding place or a risky path.")


ASP_RULES = r"""
cargo_risk(C) :- cargo(C), jostled(C), not secured(C).
suspense :- path(P), narrow(P).
surprise :- cargo_risk(cargo), garb(G), hidden_note(G).
happy :- surprise, followed_note.
#show cargo_risk/1.
#show suspense/0.
#show surprise/0.
#show happy/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        if s.has_path:
            lines.append(asp.fact("path", sid))
        if s.has_stairs:
            lines.append(asp.fact("stairs", sid))
        if s.has_hidey_place:
            lines.append(asp.fact("hidey", sid))
    lines.append(asp.fact("cargo", "cargo"))
    lines.append(asp.fact("garb", "garb"))
    lines.append(asp.fact("hidden_note", "garb"))
    lines.append(asp.fact("narrow", "lane"))
    lines.append(asp.fact("narrow", "stairs"))
    lines.append(asp.fact("jostled", "cargo"))
    lines.append(asp.fact("secured", "cargo"))
    lines.append(asp.fact("followed_note"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show cargo_risk/1.\n#show suspense/0.\n#show surprise/0.\n#show happy/0."))
    atoms = set((sym.name, len(sym.arguments), tuple(a.name if a.type == a.type.Function else (a.string if a.type == a.type.String else a.number) for a in sym.arguments)) for sym in model)
    # Minimal parity check on the intended atoms.
    expected = {("cargo_risk", 1, ("cargo",)), ("suspense", 0, ()), ("surprise", 0, ()), ("happy", 0, ())}
    if atoms == expected:
        print("OK: ASP rules produce the expected story-state markers.")
        return 0
    print("MISMATCH between ASP and expected markers.")
    print("got:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    world.path_hazard = 1.0 if setting.has_path else 0.0

    courier = world.add(Entity(
        id="courier",
        kind="character",
        type=params.role,
        label=params.name,
        meters={"steps": 0.0},
        memes={"care": 1.0},
    ))
    cargo = world.add(Entity(
        id="cargo",
        type="cargo",
        label="molasses",
        phrase="a heavy jar of molasses",
        caretaker="courier",
        meters={"secure": 0.0, "sticky": 0.0, "delivered": 0.0},
        memes={"value": 1.0},
    ))
    garb = world.add(Entity(
        id="garb",
        type="garb",
        label="garb",
        phrase="a wrapped bundle of old garb",
        meters={"open": 0.0},
        memes={"secret": 1.0},
    ))

    world.say(
        f"{params.name} was carrying a heavy jar of molasses through {setting.place}."
    )
    world.say(
        "The night felt quiet, but the silence made the transport seem more and more suspicious."
    )
    world.para()

    courier.memes["jostle"] = 1.0
    if setting.has_stairs:
        world.say("Each stair looked like a clue that might make the jar slip.")
    else:
        world.say("The lane bent near a dark corner, and every shadow felt like a clue.")

    propagate(world, narrate=True)

    world.para()
    world.say(
        "Then the garb shifted, and the mystery turned into a surprise."
    )
    garb.meters["open"] = 1.0
    propagate(world, narrate=True)

    world.para()
    if world.hidden_note_found:
        world.say(
            f"{params.name} followed the tiny note, found the safe route, and brought the molasses home without a spill."
        )
    else:
        world.say(
            f"{params.name} still protected the molasses, and the careful transport ended safely."
        )
    world.say(
        f"In the end, the garb held a secret, the molasses stayed safe, and the whole mystery ended happily."
    )

    world.facts.update(
        courier=courier,
        cargo=cargo,
        garb=garb,
        setting=setting,
        hidden_note=world.hidden_note_found,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    courier: Entity = f["courier"]
    cargo: Entity = f["cargo"]
    garb: Entity = f["garb"]
    setting: Setting = f["setting"]
    qa = [
        QAItem(
            question=f"What was {courier.label} carrying?",
            answer=f"{courier.label} was carrying a heavy jar of molasses through {setting.place}.",
        ),
        QAItem(
            question="Why did the trip feel suspenseful?",
            answer=(
                "It felt suspenseful because the route was quiet and uncertain, "
                "so every step seemed like it might make the molasses spill."
            ),
        ),
        QAItem(
            question="What surprising thing was found in the garb?",
            answer=(
                "A tiny note was hidden in the garb, and it showed the safe route."
            ),
        ),
    ]
    if f.get("hidden_note"):
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=(
                    f"{courier.label} followed the note, delivered the molasses safely, "
                    "and the mystery ended happily."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is molasses?",
            answer=(
                "Molasses is a thick, dark, sweet syrup. It pours slowly and can be sticky."
            ),
        ),
        QAItem(
            question="What does transport mean?",
            answer=(
                "Transport means moving something from one place to another."
            ),
        ),
        QAItem(
            question="What is garb?",
            answer=(
                "Garb means clothing or a set of clothes, often in a formal or old-fashioned way."
            ),
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    courier: Entity = f["courier"]
    setting: Setting = f["setting"]
    return [
        f'Write a short mystery story for a young child about {courier.label} transporting molasses through {setting.place}.',
        "Tell a suspenseful but gentle story where a hidden piece of garb reveals a surprise and leads to a happy ending.",
        "Write a small story with molasses, transport, and garb that feels like a mystery but ends safely.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n[0] for n in world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld about molasses transport and a garb surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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
    place = args.place or rng.choice(list(SETTINGS))
    role = args.role or rng.choice(list(ROLES))
    setting = SETTINGS[place]
    if not setting.has_path and not setting.has_stairs:
        raise StoryError("This story needs a route for the transport.")
    name = args.name or rng.choice(NAMES[role])
    return StoryParams(place=place, name=name, role=role)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
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


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show cargo_risk/1.\n#show suspense/0.\n#show surprise/0.\n#show happy/0."))
    return sorted((sym.name, len(sym.arguments), tuple(a.name if a.type == a.type.Function else (a.string if a.type == a.type.String else a.number) for a in sym.arguments)) for sym in model)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show cargo_risk/1.\n#show suspense/0.\n#show surprise/0.\n#show happy/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP markers:", asp_valid())
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
