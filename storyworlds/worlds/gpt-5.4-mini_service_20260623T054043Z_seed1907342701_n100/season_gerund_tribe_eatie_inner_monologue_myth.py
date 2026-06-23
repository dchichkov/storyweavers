#!/usr/bin/env python3
"""
storyworlds/worlds/season_gerund_tribe_eatie_inner_monologue_myth.py
====================================================================

A small mythic storyworld about a tribe, a sacred seasonal task, and an eatie
that changes the tribe's evening. The stories use inner monologue as a narrative
instrument: the protagonist thinks in short, clear thoughts while the world
moves from worry to action to a visible ending image.

Seed tale shape:
- A tribe gathers for a season-gerund rite.
- An eatie is in trouble: hungry, lost, or unable to finish the rite.
- The protagonist thinks through the problem, chooses a fitting helper or tool,
  and the tribe's state changes in a concrete, myth-flavored ending.

The world is deliberately tiny and constraint-checked. Each valid story requires
a problem that genuinely calls for the chosen help, so the tale has a real turn
rather than a swapped-noun template.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    moon: str
    wind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Rite:
    id: str
    name: str
    chant: str
    sign: str
    need: str
    outcome: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    sign: str
    risk: str
    meter: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    action: str
    final_image: str
    fix: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


SETTINGS = {
    "stone_hall": Setting("stone_hall", "the stone hall", "a pale moon", "a cool wind", {"feast", "sing"}),
    "river_bend": Setting("river_bend", "the river bend", "a silver moon", "a wet wind", {"fish", "feast"}),
    "hill_ring": Setting("hill_ring", "the hill ring", "a bright moon", "a singing wind", {"dance", "feast"}),
    "pine_camp": Setting("pine_camp", "the pine camp", "a low moon", "a pine-scented wind", {"feast", "rest"}),
}

RITES = {
    "season_gerund": Rite(
        id="season_gerund",
        name="season-gerund",
        chant="season-gerund",
        sign="the tribe must keep the season-gerund alive",
        need="a finished rite",
        outcome="the rite can be finished",
        tags={"season-gerund", "rite"},
    ),
    "moon_feast": Rite(
        id="moon_feast",
        name="moon-feast",
        chant="moon-feast",
        sign="the tribe must share warm food",
        need="a full bowl",
        outcome="the bowl can be shared",
        tags={"feast", "food"},
    ),
    "song_bridge": Rite(
        id="song_bridge",
        name="song-bridge",
        chant="song-bridge",
        sign="the tribe must sing across the water",
        need="a strong voice",
        outcome="the singing can cross",
        tags={"sing", "song"},
    ),
    "pine_watch": Rite(
        id="pine_watch",
        name="pine-watch",
        chant="pine-watch",
        sign="the tribe must guard the fire through the dark",
        need="steady warmth",
        outcome="the fire can stay small and safe",
        tags={"rest", "fire"},
    ),
}

PROBLEMS = {
    "hunger": Problem(
        id="hunger",
        label="hunger",
        sign="the eatie's belly is empty",
        risk="the eatie will wander and spoil the rite",
        meter="hunger",
        tags={"food", "feast", "eatie"},
    ),
    "fear": Problem(
        id="fear",
        label="fear",
        sign="the eatie is too shy to come near",
        risk="the eatie will hide before the chant",
        meter="fear",
        tags={"song", "eatie"},
    ),
    "cold": Problem(
        id="cold",
        label="cold",
        sign="the eatie is shivering by the stones",
        risk="the eatie will not stand through the rite",
        meter="cold",
        tags={"rest", "eatie"},
    ),
    "mud": Problem(
        id="mud",
        label="mud",
        sign="the eatie is stuck at the bank",
        risk="the eatie cannot reach the tribe",
        meter="mud",
        tags={"river", "eatie"},
    ),
}

HELPERS = {
    "bowl": Helper("bowl", "warm bowl", "set down a warm bowl of grain", "the eatie eats, and the tribe sees the moonlit bowl", "feed the eatie well", {"food", "feast"}),
    "song": Helper("song", "low song", "sing a low song beside the stones", "the eatie lifts its ears and follows the song", "quiet the eatie with song", {"song", "fear"}),
    "blanket": Helper("blanket", "wool blanket", "wrap the eatie in a wool blanket", "the eatie stands warm and still beside the fire", "warm the eatie against the cold", {"rest", "cold"}),
    "bridge": Helper("bridge", "reed bridge", "lay down a reed bridge over the mud", "the eatie crosses the mud on the reed bridge", "carry the eatie safely over the mud", {"river", "mud"}),
}

GUESTS = ["Aru", "Mina", "Tavi", "Sela", "Noa", "Piri", "Kora", "Luno"]
TRIBES = ["the ash tribe", "the reed tribe", "the hill tribe", "the pine tribe"]
TRAITS = ["quiet", "brave", "wise", "gentle", "watchful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for rid, rite in RITES.items():
            if rite.id not in setting.affords and rite.id not in {"season_gerund"}:
                continue
            for pid, problem in PROBLEMS.items():
                for hid, helper in HELPERS.items():
                    if problem.tags & helper.tags:
                        combos.append((sid, rid, pid, hid))
    return combos


@dataclass
class StoryParams:
    setting: str = "stone_hall"
    rite: str = "season_gerund"
    problem: str = "hunger"
    helper: str = "bowl"
    name: str = "Aru"
    tribe: str = "the ash tribe"
    trait: str = "wise"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld with inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--tribe", choices=TRIBES)
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


def _pick_name(rng: random.Random) -> str:
    return rng.choice(GUESTS)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.rite is None or c[1] == args.rite)
              and (args.problem is None or c[2] == args.problem)
              and (args.helper is None or c[3] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, rite, problem, helper = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        rite=rite,
        problem=problem,
        helper=helper,
        name=args.name or _pick_name(rng),
        tribe=args.tribe or rng.choice(TRIBES),
        trait=args.trait or rng.choice(TRAITS),
    )


def _build_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Entity, Entity]:
    setting = SETTINGS[params.setting]
    rite = RITES[params.rite]
    problem = PROBLEMS[params.problem]
    helper = HELPERS[params.helper]
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type="child", label=params.name, traits=[params.trait], meters={}, memes={"hope": 0.0, "worry": 0.0}, attrs={"tribe": params.tribe}))
    elder = world.add(Entity(id="elder", kind="character", type="elder", label="the elder", meters={}, memes={"calm": 0.0}, attrs={"tribe": params.tribe}))
    eatie = world.add(Entity(id="eatie", kind="character", type="eatie", label="the eatie", meters={"hunger": 0.0, "fear": 0.0, "cold": 0.0, "mud": 0.0}, memes={"trust": 0.0}, attrs={"tribe": params.tribe}))
    world.add(Entity(id="ritual", type="ritual", label=rite.name, meters={"done": 0.0}, memes={}))
    world.add(Entity(id="helper", type="helper", label=helper.label, meters={}, memes={}))
    world.facts.update(params=params, setting=setting, rite=rite, problem=problem, helper=helper, hero=hero, elder=elder, eatie=eatie)
    return world, hero, elder, eatie, setting, rite


def predict(world: World, problem: Problem, helper: Helper) -> bool:
    sim = world.copy()
    eatie = sim.get("eatie")
    eatie.meters[problem.meter] += 1.0
    return problem.tags & helper.tags != set()


def narrate_problem(world: World, hero: Entity, eatie: Entity, rite: Rite, problem: Problem) -> None:
    world.say(f"In {world.setting.place}, {hero.label} of {world.facts['params'].tribe} lifted {their := 'their'} eyes to {world.setting.moon}.")
    world.say(f'The tribe began the {rite.name}, and the air seemed to wait for the old chant, "{rite.chant}."')
    world.say(f"{hero.label} thought, {hero.pronoun('possessive').capitalize()} inner voice said, 'I can feel it—{problem.sign}.'")
    hero.memes["worry"] += 1.0
    eatie.meters[problem.meter] += 1.0
    eatie.memes["trust"] += 0.5


def apply_helper(world: World, hero: Entity, eatie: Entity, helper: Helper, problem: Problem) -> None:
    world.say(f"{hero.label} chose to {helper.action}.")
    if problem.id == "hunger":
        eatie.meters["hunger"] = 0.0
        eatie.meters["food"] = 1.0
    elif problem.id == "fear":
        eatie.meters["fear"] = 0.0
    elif problem.id == "cold":
        eatie.meters["cold"] = 0.0
    elif problem.id == "mud":
        eatie.meters["mud"] = 0.0
    hero.memes["hope"] += 1.0
    eatie.memes["trust"] += 1.0
    world.say(helper.final_image + ".")


def tell(params: StoryParams) -> World:
    world, hero, elder, eatie, setting, rite = _build_world(params)
    problem = PROBLEMS[params.problem]
    helper = HELPERS[params.helper]
    world.say(f"{params.tribe} gathered in {setting.place} under {setting.moon}, and the {rite.name} began.")
    world.say(f"{hero.label} stood among the stones and thought, 'If the rite fails, the whole night will feel empty.'")
    world.para()
    narrate_problem(world, hero, eatie, rite, problem)
    world.say(f"The elder looked from the {rite.need} to the eatie and nodded once, as if the answer were already in the earth.")
    world.para()
    apply_helper(world, hero, eatie, helper, problem)
    eatie.meters["seen"] = 1.0
    world.say(f"At the end, the tribe could keep the {rite.name}, and the eatie stood close by, no longer lost in the dark.")
    world.facts.update(resolved=True, ending_image=helper.final_image)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a mythic story for a young child about {p.tribe}, the word "season-gerund", and an eatie that needs help.',
        f"Tell a gentle legend where {p.name} hears an inner voice, notices a problem with the eatie, and saves the {p.rite.replace('_', '-')} rite.",
        f'Write a short myth with inner monologue, the word "tribe", and a final image where the eatie is safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    rite = world.facts["rite"]
    problem = world.facts["problem"]
    helper = world.facts["helper"]
    hero = world.facts["hero"]
    eatie = world.facts["eatie"]
    return [
        QAItem(
            question=f"What was {p.name} listening for while the tribe began the {rite.name} rite?",
            answer=f"{p.name} was listening to a small inner voice that noticed {problem.sign}. The thought helped {p.name} choose a careful answer instead of rushing past the eatie.",
        ),
        QAItem(
            question=f"Why did the eatie need {helper.label}?",
            answer=f"The eatie needed {helper.label} because {problem.risk}. {helper.fix.capitalize()}, so the rite could keep going safely.",
        ),
        QAItem(
            question=f"What changed for the tribe after {p.name} helped the eatie?",
            answer=f"The tribe could finish the {rite.name}, and the eatie was no longer stuck or afraid. The ending image proves it: {world.facts['ending_image']}.",
        ),
        QAItem(
            question=f"Who was the story about besides the eatie?",
            answer=f"It was about {p.name}, a careful member of {p.tribe}, and the elder who watched over the rite. Together they kept the night steady and helped the eatie.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a tribe?", "A tribe is a group of people who belong together and share work, stories, and ways of living."),
        QAItem("What is inner monologue?", "Inner monologue is the quiet voice inside a character's mind. It lets the story show what the character thinks before acting."),
        QAItem("What is a rite?", "A rite is a special ceremony or act that people do in a set way because it matters to them."),
        QAItem("What kind of thing is an eatie?", "In this storyworld, an eatie is a small creature that can be hungry, shy, cold, or stuck and needs gentle help."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("\n== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("\n== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} label={e.label} meters={e.meters} memes={e.memes} attrs={e.attrs}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="stone_hall", rite="season_gerund", problem="hunger", helper="bowl", name="Aru", tribe="the ash tribe", trait="wise"),
    StoryParams(setting="river_bend", rite="moon_feast", problem="fear", helper="song", name="Mina", tribe="the reed tribe", trait="gentle"),
    StoryParams(setting="hill_ring", rite="song_bridge", problem="mud", helper="bridge", name="Tavi", tribe="the hill tribe", trait="watchful"),
    StoryParams(setting="pine_camp", rite="pine_watch", problem="cold", helper="blanket", name="Sela", tribe="the pine tribe", trait="brave"),
]


ASP_RULES = r"""
valid(S,R,P,H) :- setting(S), rite(R), problem(P), helper(H), compatible(R,P,H).
compatible(_, hunger, bowl).
compatible(_, fear, song).
compatible(_, cold, blanket).
compatible(_, mud, bridge).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid in RITES:
        lines.append(asp.fact("rite", rid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP matches Python, and generation smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.rite not in RITES or params.problem not in PROBLEMS or params.helper not in HELPERS:
        raise StoryError("Invalid story parameters.")
    if (params.setting, params.rite, params.problem, params.helper) not in valid_combos():
        raise StoryError("That combination does not make a reasonable story.")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        for row in asp_valid_combos():
            print(row)
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = [generate(resolve_params(args, random.Random((args.seed or 0) + i))) for i in range(args.n)] if not args.all else [generate(p) for p in CURATED]
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
