#!/usr/bin/env python3
"""
A small mythic storyworld about a brave monger, an alcove, and a pavilion.

The world is built from a simple seed-tale idea:
a monger hears a warning, enters an alcove beside a pavilion, acts bravely,
and the choice leads to a bad ending that still feels like a full myth.

This script keeps a tiny state model with physical meters and emotional memes,
renders story prose from the evolving world, and provides grounded QA plus
an ASP twin for reasonableness checks.
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
# Story state
# ---------------------------------------------------------------------------
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
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"woman", "girl", "mother", "queen", "priestess"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"man", "boy", "father", "king", "priest"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    has_pavilion: bool = True
    has_alcove: bool = True


@dataclass
class Hazard:
    id: str
    name: str
    sign: str
    ruin: str
    meter: str
    pressure: str


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    fragile: bool = False


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Ilan"
    hero_type: str = "monger"
    keeper_name: str = "Vela"
    setting: str = "shore-temple"
    hazard: str = "storm"
    relic: str = "oil-lamp"
    tone: str = "mythic"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.trace_facts: dict[str, object] = {}
        self.hazard_active: bool = False

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


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _bump_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _bump_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "shore-temple": Setting(place="the shore-temple", mood="salt-bright"),
    "hill-pavilion": Setting(place="the hill pavilion", mood="windy"),
    "river-pavilion": Setting(place="the river pavilion", mood="misty"),
}

HAZARDS = {
    "storm": Hazard(
        id="storm",
        name="storm",
        sign="the sky went black and the water began to slam the stones",
        ruin="the roof would shake loose",
        meter="break",
        pressure="a storm can split old wood",
    ),
    "fire": Hazard(
        id="fire",
        name="fire",
        sign="sparks climbed the dry grass like little red snakes",
        ruin="the beams would crack and smoke",
        meter="burn",
        pressure="fire can chew through dry cloth and wood",
    ),
}

RELICS = {
    "oil-lamp": Relic(
        id="oil-lamp",
        label="oil lamp",
        phrase="a small oil lamp with a brass handle",
        protects={"dark"},
        fragile=True,
    ),
    "song-charm": Relic(
        id="song-charm",
        label="song charm",
        phrase="a carved charm that held an old hymn",
        protects={"fear"},
    ),
    "bundle-of-salt": Relic(
        id="bundle-of-salt",
        label="bundle of salt",
        phrase="a paper-wrapped bundle of white salt",
        protects={"storm"},
    ),
}

# ---------------------------------------------------------------------------
# Narrative world rules
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, keeper: Entity, relic: Entity) -> None:
    world.say(
        f"In {world.setting.place}, there was a {hero.type} named {hero.id}, "
        f"and people said {hero.pronoun('subject')} could walk into trouble with a steady face."
    )
    world.say(
        f"{keeper.id}, the keeper of the old paths, had placed {keeper.pronoun('possessive')} trust in "
        f"{hero.pronoun('object')} and had given {hero.pronoun('object')} {relic.phrase}."
    )
    _bump_meme(hero, "bravery", 1.0)
    _bump_meme(hero, "duty", 1.0)


def omen(world: World, hazard: Hazard) -> None:
    world.hazard_active = True
    world.say(
        f"Then the sign of {hazard.name} came: {hazard.sign}."
    )


def approach(world: World, hero: Entity, alcove: Entity, pavilion: Entity, hazard: Hazard) -> None:
    _bump_meme(hero, "fear", 1.0)
    _bump_meme(hero, "bravery", 1.0)
    world.say(
        f"{hero.id} went at once to the alcove beside the pavilion, because {hero.pronoun('subject')} would not "
        f"turn away from a hard road."
    )
    world.say(
        f"The alcove was narrow and shadowed, while the pavilion stood open to the wind."
    )
    world.trace_facts["alcove"] = alcove.id
    world.trace_facts["pavilion"] = pavilion.id
    world.trace_facts["hazard"] = hazard.id


def test_bravery(world: World, hero: Entity, relic: Entity, hazard: Hazard) -> None:
    _bump_meter(hero, hazard.meter, 1.0)
    _bump_meme(hero, "resolve", 1.0)
    world.say(
        f"{hero.id} lifted {hero.pronoun('possessive')} chin and set {relic.label} on the stone shelf inside the alcove."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} hands did not shake, though {hazard.pressure}."
    )


def bad_turn(world: World, hero: Entity, pavilion: Entity, hazard: Hazard, relic: Entity) -> None:
    if _meter(hero, hazard.meter) < THRESHOLD or not world.hazard_active:
        raise StoryError("The myth needs a real danger before the ending can turn bad.")

    if hazard.id == "storm":
        _bump_meter(pavilion, "break", 1.0)
        _bump_meter(relic, "soaked", 1.0)
        _bump_meme(hero, "grief", 1.0)
        world.say(
            f"At last the storm rushed in, and the pavilion groaned as if an old beast were waking."
        )
        world.say(
            f"The roof boards split, rain poured through the rafters, and {relic.label} went dark with water."
        )
    else:
        _bump_meter(pavilion, "burn", 1.0)
        _bump_meter(relic, "blackened", 1.0)
        _bump_meme(hero, "grief", 1.0)
        world.say(
            f"At last the fire leapt up, and the pavilion shivered like dry grass."
        )
        world.say(
            f"Smoke curled through the rafters, and {relic.label} came away blackened in {hero.pronoun('possessive')} hand."
        )


def ending_image(world: World, hero: Entity, keeper: Entity, pavilion: Entity, relic: Entity) -> None:
    _bump_meme(hero, "acceptance", 1.0)
    world.say(
        f"When the wind at last quieted, {hero.id} stood in the alcove with {keeper.id}, looking at the ruined pavilion."
    )
    world.say(
        f"{hero.id} still held {relic.label}, but the old shelter had lost its proud roof, and the night sky showed through."
    )
    world.say(
        f"That was the price of {hero.pronoun('possessive')} bravery: {hero.pronoun('subject')} had gone forward, and the story ended in ash and rain."
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    hazard = HAZARDS[params.hazard]
    relic_cfg = RELICS[params.relic]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"break": 0.0, "burn": 0.0},
        memes={"bravery": 0.0, "fear": 0.0, "duty": 0.0},
    ))
    keeper = world.add(Entity(
        id=params.keeper_name,
        kind="character",
        type="keeper",
        meters={},
        memes={"worry": 1.0},
    ))
    alcove = world.add(Entity(
        id="Alcove",
        kind="thing",
        type="alcove",
        label="alcove",
        phrase="a cool stone alcove",
    ))
    pavilion = world.add(Entity(
        id="Pavilion",
        kind="thing",
        type="pavilion",
        label="pavilion",
        phrase="an old pavilion with a high roof",
        meters={"break": 0.0, "burn": 0.0},
    ))
    relic = world.add(Entity(
        id=relic_cfg.id,
        kind="thing",
        type=relic_cfg.label,
        label=relic_cfg.label,
        phrase=relic_cfg.phrase,
        owner=hero.id,
        caretaker=keeper.id,
        meters={},
    ))

    world.trace_facts.update(
        hero=hero.id,
        keeper=keeper.id,
        alcove=alcove.id,
        pavilion=pavilion.id,
        relic=relic.id,
        hazard=hazard.id,
    )

    introduce(world, hero, keeper, relic)
    world.para()
    omen(world, hazard)
    approach(world, hero, alcove, pavilion, hazard)
    test_bravery(world, hero, relic, hazard)
    world.para()
    bad_turn(world, hero, pavilion, hazard, relic)
    ending_image(world, hero, keeper, pavilion, relic)
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate and registries
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for h in HAZARDS:
            for r in RELICS:
                if h == "storm" and r in {"oil-lamp", "bundle-of-salt", "song-charm"}:
                    combos.append((s, h, r))
                if h == "fire" and r == "song-charm":
                    combos.append((s, h, r))
    return combos


def explain_rejection(setting: str, hazard: str, relic: str) -> str:
    return (
        f"(No story: the chosen relic '{relic}' does not make a strong mythic "
        f"match for '{hazard}' in '{setting}'. Pick one that can matter in the bad ending.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A combination is valid when the hazard and relic form a meaningful mythic tension.
valid(S,H,R) :- setting(S), hazard(H), relic(R), matches(H,R).

% Storm pairs with fragile or protective relics that can be harmed or tested.
matches(storm, oil_lamp).
matches(storm, bundle_of_salt).
matches(storm, song_charm).

% Fire pairs with song charm because the myth can lose the song to smoke.
matches(fire, song_charm).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for h in HAZARDS:
        lines.append(asp.fact("hazard", h))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
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


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.trace_facts
    return [
        f'Write a short myth about a {f["hero"]} who enters an alcove near a pavilion during a {f["hazard"]}.',
        f"Tell a child-facing legend where the monger faces danger in the alcove and the pavilion suffers a bad ending.",
        f'Write a small mythic story that includes the words "monger", "alcove", and "pavilion".',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get(world.trace_facts["hero"])
    keeper = world.get(world.trace_facts["keeper"])
    pavilion = world.get(world.trace_facts["pavilion"])
    relic = world.get(world.trace_facts["relic"])
    hazard = HAZARDS[world.trace_facts["hazard"]]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {hero.type} with a brave heart, and {keeper.id}, who kept watch over the old paths.",
        ),
        QAItem(
            question=f"What place did {hero.id} walk into?",
            answer=f"{hero.id} walked into the alcove beside the pavilion.",
        ),
        QAItem(
            question=f"What happened to the pavilion in the end?",
            answer=f"The pavilion was damaged in the bad ending: {hazard.name} made the roof split and left it standing ruined.",
        ),
        QAItem(
            question=f"What did {hero.id} carry that mattered in the myth?",
            answer=f"{hero.id} carried {relic.phrase}, and it was part of the choice the story followed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pavilion?",
            answer="A pavilion is a roofed shelter or open-sided building used for resting, gathering, or ceremony.",
        ),
        QAItem(
            question="What is an alcove?",
            answer="An alcove is a small recessed space built into a wall or a larger room.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means acting even when something feels scary or risky.",
        ),
        QAItem(
            question="What is a bad ending in a myth?",
            answer="A bad ending is when the danger does not get fixed and the story closes with loss or ruin.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld of a brave monger, an alcove, and a pavilion.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--keeper")
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
    if args.setting and args.hazard and args.relic:
        if (args.setting, args.hazard, args.relic) not in valid_combos():
            raise StoryError(explain_rejection(args.setting, args.hazard, args.relic))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.relic is None or c[2] == args.relic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hazard, relic = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Ilan", "Mira", "Tavi", "Sera", "Niko"])
    keeper = args.keeper or rng.choice(["Vela", "Orin", "Mara", "Daren"])
    return StoryParams(
        seed=None,
        hero_name=name,
        keeper_name=keeper,
        setting=setting,
        hazard=hazard,
        relic=relic,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid myth combos:")
        for c in combos:
            print(*c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(hero_name="Ilan", keeper_name="Vela", setting="shore-temple", hazard="storm", relic="oil-lamp"),
            StoryParams(hero_name="Mira", keeper_name="Orin", setting="hill-pavilion", hazard="storm", relic="bundle-of-salt"),
            StoryParams(hero_name="Tavi", keeper_name="Mara", setting="river-pavilion", hazard="fire", relic="song-charm"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
            header = f"### {p.hero_name} / {p.setting} / {p.hazard} / {p.relic}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
