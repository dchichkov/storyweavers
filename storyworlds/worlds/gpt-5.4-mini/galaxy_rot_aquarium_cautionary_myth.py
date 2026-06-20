#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/galaxy_rot_aquarium_cautionary_myth.py
======================================================================

A small standalone storyworld for a cautionary myth set in an aquarium.

Premise:
- In an aquarium, a child or keeper notices a strange "galaxy" shimmer in a
  shell or glass ornament.
- The shimmer tempts them to ignore warning signs: water smells wrong, food is
  left too long, and rot spreads in the tank.
- A sensible helper acts early, removes the source, cleans the tank, and saves
  the fish.
- The ending proves the change: the aquarium becomes clear again, and the
  caution becomes a myth-like lesson remembered by all.

This file follows the shared storyworld contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports -n, --all, --seed, --trace, --qa, --json, --asp, --verify,
  --show-asp
- includes Python reasonableness checks and an inline ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    details: str


@dataclass
class MythFigure:
    id: str
    name: str
    type: str
    role: str
    title: str
    courage: str


@dataclass
class RotSource:
    id: str
    label: str
    scent: str
    spreads: int = 2
    rots: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class GalaxyCharm:
    id: str
    label: str
    glow: str
    lure: str
    harmless: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    name: str
    power: int
    method: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_rot(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["rot"] < THRESHOLD:
            continue
        sig = ("rot", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "tank" in world.entities:
            world.get("tank").meters["stink"] += 1
            world.get("tank").meters["cloud"] += 1
        for kid in world.entities.values():
            if kid.role in {"seer", "guardian"}:
                kid.memes["alarm"] += 1
        out.append("__rot__")
    return out


def _r_decay(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["cloud"] < THRESHOLD:
            continue
        sig = ("decay", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "fish" in world.entities:
            world.get("fish").memes["unease"] += 1
        out.append("__decay__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("rot", "physical", _r_rot),
    Rule("decay", "social", _r_decay),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def hazard_at_risk(charm: GalaxyCharm, rot: RotSource) -> bool:
    return not charm.harmless and rot.rots


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.power >= 2]


def chosen_remedy() -> Remedy:
    return max(REMEDIES.values(), key=lambda r: r.power)


def disaster_level(rot: RotSource, delay: int) -> int:
    return rot.spreads + delay


def can_prevent(remedy: Remedy, rot: RotSource, delay: int) -> bool:
    return remedy.power >= disaster_level(rot, delay)


def advise_against(world: World, guardian: Entity, seer: Entity, charm: GalaxyCharm, rot: RotSource) -> None:
    world.say(
        f'{guardian.id} sniffed the water and frowned. "That bright {charm.label} '
        f"does not make a safe light for fish. It only hides the rot smell.""
    )
    world.say(
        f'"If we leave the {rot.label} in the tank, the whole place can turn wrong," '
        f"{guardian.id} warned."
    )


def tempt(world: World, seer: Entity, charm: GalaxyCharm) -> None:
    seer.memes["wonder"] += 1
    world.say(
        f"{seer.id} pointed at the shining {charm.label}. It glimmered like a "
        f"little galaxy trapped under glass, and the sparkle felt magical."
    )
    world.say(f'"{charm.lure}," {seer.id} whispered.')


def make_mistake(world: World, seer: Entity, rot: RotSource) -> None:
    seer.memes["defiance"] += 1
    world.say(
        f"{seer.id} left the {rot.label} where it was, thinking the fish would "
        f"be fine for one more day."
    )


def spoil(world: World, rot: RotSource) -> None:
    rot_ent = world.get("rot_source")
    rot_ent.meters["rot"] += 1
    rot_ent.meters["mold"] += 1
    propagate(world, narrate=False)
    world.say(
        f"By dawn, the water had gone cloudy. The sweet little smell turned sour, "
        f"and the tank began to rot like old bread forgotten in the sun."
    )


def rescue(world: World, guardian: Entity, remedy: Remedy, rot: RotSource) -> None:
    world.get("rot_source").meters["rot"] = 0.0
    world.get("tank").meters["cloud"] = 0.0
    world.get("tank").meters["stink"] = 0.0
    body = remedy.method.replace("{rot}", rot.label)
    world.say(
        f"{guardian.label_word.capitalize()} came at once and {body}."
    )
    world.say(
        f"The {remedy.result} worked, and the water cleared until the fish could "
        f"see through it again."
    )


def lesson(world: World, guardian: Entity, seer: Entity, charm: GalaxyCharm) -> None:
    seer.memes["relief"] += 1
    seer.memes["lesson"] += 1
    guardian.memes["peace"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {guardian.label_word.capitalize()} knelt beside the glass and said, "
        f'"A pretty shine is not always a kind thing. A real guardian looks for '
        f'what is hidden, not only what sparkles."'
    )
    world.say(
        f"{seer.id} promised to listen next time the aquarium looked wrong."
    )


def ending(world: World, seer: Entity) -> None:
    world.say(
        f"In the end, the aquarium shone clear again, and the little {seer.id} "
        f"remembered the myth of the galaxy that could not save rotten water."
    )


def tell(setting: Setting, figure: MythFigure, charm: GalaxyCharm, rot: RotSource,
         remedy: Remedy, delay: int = 0) -> World:
    world = World()
    guardian = world.add(Entity(id="Keeper", kind="character", type="mother", role="guardian", label="the keeper"))
    seer = world.add(Entity(id=figure.name, kind="character", type=figure.type, role="seer", label=figure.name))
    tank = world.add(Entity(id="tank", type="thing", label="the tank"))
    rot_ent = world.add(Entity(id="rot_source", type="thing", label=rot.label))
    fish = world.add(Entity(id="fish", type="thing", label="the fish"))

    seer.memes["wonder"] = 1.0
    guardian.memes["duty"] = 1.0
    world.facts["setting"] = setting
    world.facts["figure"] = figure
    world.facts["charm"] = charm
    world.facts["rot"] = rot
    world.facts["remedy"] = remedy
    world.facts["delay"] = delay

    world.say(
        f"Long ago, in {setting.place}, there lived a keeper and a child who loved "
        f"stories about the sea."
    )
    world.say(
        f"The aquarium was calm and bright, {setting.details}, and the glass held a "
        f"small world like a temple bowl."
    )
    world.say(
        f"{seer.id} saw a {charm.label} shining in the water, and it gleamed like a "
        f"tiny galaxy."
    )
    world.para()
    tempt(world, seer, charm)
    advise_against(world, guardian, seer, charm, rot)

    if not hazard_at_risk(charm, rot):
        raise StoryError("This myth needs a dangerous charm and a rot source.")

    if delay > 0:
        world.say(
            f"But the warning came late, and the smell had already settled over the glass."
        )

    if delay > 0 and not can_prevent(remedy, rot, delay):
        seer.memes["fear"] += 1
        world.say(
            f"The rot spread too far for a small fix. The keeper still acted fast, "
            f"but the damage had already taken hold."
        )
        spoil(world, rot)
        world.say(
            "The fish were moved to clean water, and the old tank was scrubbed "
            "until it could begin again."
        )
        ending(world, seer)
        outcome = "bad"
    else:
        make_mistake(world, seer, rot)
        spoil(world, rot)
        world.para()
        rescue(world, guardian, remedy, rot)
        lesson(world, guardian, seer, charm)
        ending(world, seer)
        outcome = "good"

    world.facts.update(
        guardian=guardian,
        seer=seer,
        tank=tank,
        rot_ent=rot_ent,
        fish=fish,
        outcome=outcome,
        prevented=(outcome == "good"),
    )
    return world


SETTINGS = {
    "aquarium": Setting(
        id="aquarium",
        place="the aquarium",
        mood="quiet and blue",
        details="blue lamps glowed over the water and little bubbles rose like beads",
    ),
}

FIGURES = {
    "mira": MythFigure("mira", "Mira", "girl", "seer", "a small seer", "brave"),
    "orin": MythFigure("orin", "Orin", "boy", "seer", "a young watcher", "careful"),
}

CHARS = {
    "galaxy_shell": GalaxyCharm(
        "galaxy_shell",
        "galaxy shell",
        "blue-white glow",
        "a treasure for the eye, not for the fish",
        False,
        {"galaxy"},
    ),
    "star_glass": GalaxyCharm(
        "star_glass",
        "star glass",
        "silver glow",
        "a miracle of light, but not a cure",
        False,
        {"galaxy"},
    ),
}

ROTS = {
    "food": RotSource("food", "old fish food", "sour crumbs", 3, True, {"rot"}),
    "plant": RotSource("plant", "rotting plant", "wet decay", 2, True, {"rot"}),
}

REMEDIES = {
    "cleanout": Remedy(
        "cleanout", "cleanout", 4,
        "scooped out the rotten bits, changed the water, and rinsed the stones",
        "cleansing",
        {"clean", "water"},
    ),
    "filter": Remedy(
        "filter", "filter change", 2,
        "replaced the filter and pulled the foul water through fresh cloth",
        "filtering",
        {"clean", "water"},
    ),
    "bucket": Remedy(
        "bucket", "bucket change", 1,
        "poured in a bucket of water and hoped for the best",
        "hurrying",
        {"water"},
    ),
}

TRAITS = ["brave", "careful", "curious", "gentle", "watchful"]
NAMES = ["Mira", "Orin", "Lina", "Tavi", "Nia", "Ivo"]


@dataclass
class StoryParams:
    setting: str
    figure: str
    charm: str
    rot: str
    remedy: str
    delay: int = 0
    name: str = "Mira"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for fid in FIGURES:
            for cid in CHARS:
                for rid in ROTS:
                    if hazard_at_risk(CHARS[cid], ROTS[rid]):
                        combos.append((sid, fid, cid, rid))
    return combos


def explain_rejection(charm: GalaxyCharm, rot: RotSource) -> str:
    return (
        f"(No story: {charm.label} can make a galaxy-like shine, but this world "
        f"also needs real rot to threaten the aquarium. Pick a rot source that can "
        f"actually spread.)"
    )


def explain_remedy(rid: str) -> str:
    r = REMEDIES[rid]
    good = ", ".join(sorted(x.id for x in sensible_remedies()))
    return (
        f"(Refusing remedy '{rid}': it is too weak for a clear cautionary myth. "
        f"Try one of: {good}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "good" if can_prevent(REMEDIES[params.remedy], ROTS[params.rot], params.delay) else "bad"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary myth in an aquarium.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--figure", choices=FIGURES)
    ap.add_argument("--charm", choices=CHARS)
    ap.add_argument("--rot", choices=ROTS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
    ap.add_argument("--name", choices=NAMES)
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
    if args.charm and args.rot and not hazard_at_risk(CHARS[args.charm], ROTS[args.rot]):
        raise StoryError(explain_rejection(CHARS[args.charm], ROTS[args.rot]))
    if args.remedy and REMEDIES[args.remedy].power < 2:
        raise StoryError(explain_remedy(args.remedy))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.figure is None or c[1] == args.figure)
              and (args.charm is None or c[2] == args.charm)
              and (args.rot is None or c[3] == args.rot)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, figure, charm, rot = rng.choice(sorted(combos))
    remedy = args.remedy or rng.choice(sorted(r.id for r in sensible_remedies()))
    delay = args.delay
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting, figure, charm, rot, remedy, delay, name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary myth set in {f["setting"].place} that includes the words "galaxy" and "rot".',
        f"Tell a myth-like aquarium story where {f['seer'].id} sees a galaxy shine but learns that rot in the tank is the real danger.",
        f"Write a short child-facing warning tale in an aquarium where a beautiful glow tempts a child, but a keeper saves the fish from rot.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seer = f["seer"]
    charm = f["charm"]
    rot = f["rot"]
    remedy = f["remedy"]
    qa = [
        QAItem(
            question="What did the shining thing look like?",
            answer=f"It looked like a tiny galaxy trapped under glass. The shimmer was beautiful, but it was only a lure, not a cure."
        ),
        QAItem(
            question="Why was the aquarium in danger?",
            answer=f"The {rot.label} was starting to rot and make the water sour. Rot spreads if nobody cleans it out quickly."
        ),
        QAItem(
            question="How did the keeper fix the problem?",
            answer=f"The keeper used a {remedy.name} and cleaned the tank carefully. That stopped the rot and made the water clear again."
        ),
    ]
    if f["outcome"] == "good":
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended safely, with the fish back in clear water and {seer.id} wiser than before. The galaxy shimmer was remembered as a warning, not a treasure."
        ))
    else:
        qa.append(QAItem(
            question="How did the story end?",
            answer="It ended sadly and cautiously: the rot had spread too far, so the fish had to be moved while the old tank was cleaned and started over."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    topics = set(f["charm"].tags) | set(f["rot"].tags) | set(f["remedy"].tags)
    out = []
    if "galaxy" in topics:
        out.append(QAItem(
            question="What does the word galaxy usually make people think of?",
            answer="A galaxy makes people think of stars, space, and a wide sparkling sky. In the story, that idea was used for a pretty glow."
        ))
    if "rot" in topics:
        out.append(QAItem(
            question="What is rot?",
            answer="Rot is what happens when something old or wet starts to break down and smell bad. It can make water dirty and unsafe."
        ))
    if "water" in topics:
        out.append(QAItem(
            question="Why does an aquarium need clean water?",
            answer="Fish need clean water to breathe and stay healthy. Dirty water can make them weak and unhappy."
        ))
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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("aquarium", "mira", "galaxy_shell", "food", "cleanout", 0, "Mira"),
    StoryParams("aquarium", "orin", "star_glass", "plant", "filter", 0, "Orin"),
    StoryParams("aquarium", "mira", "galaxy_shell", "food", "bucket", 1, "Mira"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid in FIGURES:
        lines.append(asp.fact("figure", fid))
    for cid, c in CHARS.items():
        lines.append(asp.fact("charm", cid))
        if c.harmless:
            lines.append(asp.fact("harmless", cid))
    for rid, r in ROTS.items():
        lines.append(asp.fact("rot", rid))
        if r.rots:
            lines.append(asp.fact("rots", rid))
        lines.append(asp.fact("spreads", rid, r.spreads))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("threshold", THRESHOLD))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(C,R) :- charm(C), rot(R), not harmless(C), rots(R).
good_remedy(M) :- remedy(M), power(M,P), threshold(T), P >= 2, T = 1.0.
valid(S,F,C,R) :- setting(S), figure(F), charm(C), rot(R), hazard(C,R).
contained(M,R,D) :- power(M,P), spreads(R,Sp), delay(D), P >= Sp + D.
outcome(good) :- chosen_remedy(M), chosen_rot(R), delay(D), contained(M,R,D).
outcome(bad) :- chosen_remedy(M), chosen_rot(R), delay(D), not contained(M,R,D).
#show valid/4.
#show outcome/1.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_remedy", params.remedy),
        asp.fact("chosen_rot", params.rot),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        print("  only in python:", sorted(py - cl))
        print("  only in clingo:", sorted(cl - py))
    sample = generate(resolve_params(argparse.Namespace(
        setting=None, figure=None, charm=None, rot=None, remedy=None,
        delay=0, name=None, n=1, seed=None, all=False, trace=False, qa=False,
        json=False, asp=False, verify=False, show_asp=False
    ), random.Random(777)))
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: generate() produced empty story.")
    try:
        _ = tell(SETTINGS["aquarium"], FIGURES["mira"], CHARS["galaxy_shell"], ROTS["food"], REMEDIES["cleanout"], 0)
        print("OK: smoke test generation completed.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: smoke test failed: {exc}")
    for p in CURATED:
        if asp_outcome(p) != outcome_of(p):
            rc = 1
            print(f"MISMATCH outcome for {p}")
    if rc == 0:
        print("OK: ASP/Python parity and generation smoke test passed.")
    return rc


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for fid in FIGURES:
            for cid in CHARS:
                for rid in ROTS:
                    if hazard_at_risk(CHARS[cid], ROTS[rid]):
                        combos.append((sid, fid, cid, rid))
    return combos


def sensible_choice_ids() -> list[str]:
    return [r.id for r in sensible_remedies()]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], FIGURES[params.figure], CHARS[params.charm], ROTS[params.rot], REMEDIES[params.remedy], params.delay)
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.charm} / {p.rot} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
