#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/carbon_temple_putt_humor_whodunit.py
===============================================================================================================

A compact whodunit-style storyworld about a carbon clue in a temple and a putt
that solves the mystery with a laugh.

The domain premise:
- A little detective notices a strange carbon mark in a quiet temple.
- Someone claims a tiny golf putt must be the culprit.
- The detective follows physical clues, not guesses.
- The truth turns out funny: the "mystery" is a harmless temple game, and the
  carbon mark came from a charcoal rubbing used to mark the target.
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

TEMPLE_PLACES = [
    "the old temple",
    "the river temple",
    "the quiet temple",
    "the little hill temple",
]

HERO_NAMES = ["Nia", "Milo", "Pia", "Ravi", "Lena", "Timo", "Sana", "Jori"]
SIDEKICK_NAMES = ["Bert", "Mina", "Owen", "Zuri", "Ari", "Dina"]
ROLES = ["detective", "caretaker", "guide", "monk", "visitor"]
MOODS = ["curious", "cheerful", "serious", "quick-thinking", "gentle"]
TEMPLE_OBJECTS = ["lantern", "bell", "bowl", "stone tile", "offering tray"]
TOOLS = ["magnifying glass", "notebook", "small brush", "chalk", "soft cloth"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    material: str
    found_at: str
    truth: str
    noise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspicion:
    id: str
    claim: str
    why: str
    false_if: str


@dataclass
class StoryParams:
    place: str
    clue: str
    suspicion: str
    name: str
    sidekick: str
    mood: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.trace_notes = list(self.trace_notes)
        return clone


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def add_meter(ent: Entity, key: str, amt: float) -> None:
    ent.meters[key] = _meter(ent, key) + amt


def add_meme(ent: Entity, key: str, amt: float) -> None:
    ent.memes[key] = _meme(ent, key) + amt


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for ent in world.entities.values():
            if _meter(ent, "carbon") >= 1 and ("carbon_smudge", ent.id) not in world.fired:
                world.fired.add(("carbon_smudge", ent.id))
                add_meme(ent, "suspicion", 1)
                sent = f"A dark carbon smudge made the clue look important."
                out.append(sent)
                changed = True
            if _meme(ent, "suspicion") >= 1 and ("smile", ent.id) not in world.fired:
                # humor beat: suspicious things can still be silly
                world.fired.add(("smile", ent.id))
                add_meme(ent, "amusement", 1)
                out.append("The detective noticed the clue was almost too dramatic to be serious.")
                changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def trace_world(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def tell(setting: Setting, clue: Clue, suspicion: Suspicion, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type="detective", label="the detective"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="helper", label="the sidekick"))
    suspect = world.add(Entity(id="Caretaker", kind="character", type="caretaker", label="the caretaker"))
    artifact = world.add(Entity(id="artifact", kind="thing", type="temple-object", label=clue.label, phrase=clue.truth))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label="magnifying glass", phrase="a tiny magnifying glass"))

    hero.memes["curiosity"] = 2
    hero.memes["humor"] = 1
    sidekick.memes["humor"] = 1

    world.say(f"{hero.id} was a {params.mood} little detective who liked quiet rooms and tiny clues.")
    world.say(f"One afternoon, {hero.id} and {sidekick.id} walked into {setting.place} with a {tool.label}.")
    world.say(f"There, on a stone near {clue.found_at}, they found {clue.label}.")

    world.para()
    world.say(f"{hero.id} frowned. \"That {clue.noise} looks suspicious,\" {hero.pronoun()} said.")
    world.say(f"{sidekick.id} whispered, \"Very suspicious. It is doing its best to look guilty.\"")
    add_meter(artifact, "carbon", 1)
    propagate(world)

    world.para()
    hero.memes["attention"] = 1
    world.say(f"{hero.id} knelt down and brushed the mark with a soft cloth.")
    world.say(f"The dark line was not soot from a fire. It was charcoal from a temple game.")
    world.say(f"{suspicion.claim} turned out to be wrong, because {suspicion.false_if}.")

    world.para()
    add_meme(hero, "relief", 1)
    add_meme(sidekick, "amusement", 1)
    world.say(f"At last, {hero.id} found the real answer: someone had used charcoal to mark a tiny putting spot.")
    world.say(f"{clue.truth.capitalize()}, and the best proof was a little putt that rolled straight to the mark.")
    world.say(f"{sidekick.id} laughed. \"The only thing stolen here was everyone's seriousness.\"")
    world.say(f"{hero.id} smiled, closed the notebook, and solved the mystery without making a fuss.")
    world.say(f"By sunset, {setting.place} was peaceful again, and the chalky little putt mark looked almost proud of itself.")

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        suspect=suspect,
        clue=clue,
        suspicion=suspicion,
        artifact=artifact,
        tool=tool,
        params=params,
        setting=setting,
    )
    return world


SETTINGS = {
    "temple": Setting(place="the old temple", affords={"putt", "investigate"}),
    "river": Setting(place="the river temple", affords={"putt", "investigate"}),
    "quiet": Setting(place="the quiet temple", affords={"putt", "investigate"}),
    "hill": Setting(place="the little hill temple", affords={"putt", "investigate"}),
}

CLUES = {
    "carbon": Clue(
        id="carbon",
        label="a carbon mark",
        material="charcoal",
        found_at="the temple step",
        truth="the mark came from charcoal used to aim a toy putt",
        noise="carbon",
        tags={"carbon", "charcoal", "putt"},
    ),
    "putt": Clue(
        id="putt",
        label="a tiny putt mark",
        material="chalk",
        found_at="the floor by the bell",
        truth="the putt was only a harmless game",
        noise="putt",
        tags={"putt", "game"},
    ),
}

SUSPICIONS = {
    "swipe": Suspicion(
        id="swipe",
        claim="It looked like someone had swiped the clue",
        why="the mark was dark and lonely",
        false_if="the clue was only charcoal from a game",
    ),
    "prank": Suspicion(
        id="prank",
        claim="It looked like a prank",
        why="it was near the stepping stones",
        false_if="the temple had a practice spot for little putts",
    ),
}

ASP_RULES = r"""
% A carbon clue is suspicious when it appears near the temple floor.
suspicious(C) :- clue(C), has_carbon(C), at_temple(C).

% A putt can explain the carbon mark if the mark is from charcoal and the temple
% has a game spot.
explained(C) :- clue(C), has_carbon(C), putt_game(C).

% A valid whodunit story needs a clue, an apparent suspicion, and an explanation.
valid_story(P, C, S) :- place(P), clue(C), suspicion(S), suspicious(C), explained(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for k, s in SETTINGS.items():
        lines.append(asp.fact("place", k))
        lines.append(asp.fact("place_name", k, s.place))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", k, a))
    for k, c in CLUES.items():
        lines.append(asp.fact("clue", k))
        if "carbon" in c.tags:
            lines.append(asp.fact("has_carbon", k))
        if "putt" in c.tags:
            lines.append(asp.fact("putt_game", k))
        lines.append(asp.fact("at_temple", k))
    for k, s in SUSPICIONS.items():
        lines.append(asp.fact("suspicion", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def explain_rejection(place: str, clue: Clue, suspicion: Suspicion) -> str:
    return (
        f"(No story: this combination cannot make a fair whodunit. "
        f"The clue '{clue.label}' and suspicion '{suspicion.claim}' do not lead to a "
        f"clear, funny explanation in {SETTINGS[place].place}.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for clue in CLUES:
            for suspicion in SUSPICIONS:
                combos.append((place, clue, suspicion))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous temple whodunit with a carbon clue and a tiny putt.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspicion", choices=SUSPICIONS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICK_NAMES)
    ap.add_argument("--mood", choices=MOODS)
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
    place = args.place or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    suspicion = args.suspicion or rng.choice(list(SUSPICIONS))
    return StoryParams(
        place=place,
        clue=clue,
        suspicion=suspicion,
        name=args.name or rng.choice(HERO_NAMES),
        sidekick=args.sidekick or rng.choice(SIDEKICK_NAMES),
        mood=args.mood or rng.choice(MOODS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short humorous whodunit for a young child with a carbon clue, a temple, and a tiny putt.',
        f"Tell a funny mystery story where {f['hero'].id} investigates {f['clue'].label} in {f['setting'].place}.",
        f"Write a simple detective story that ends with a harmless putt explaining the carbon mark.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    clue = f["clue"]
    suspicion = f["suspicion"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who solved the mystery in {setting.place}?",
            answer=f"{hero.id} solved the mystery by looking closely at {clue.label} and not trusting the first guess.",
        ),
        QAItem(
            question=f"Why did {sidekick.id} laugh at the end?",
            answer="The mystery was funny because the scary-looking clue was only charcoal from a harmless temple game.",
        ),
        QAItem(
            question=f"What made the clue seem suspicious at first?",
            answer=f"It was dark, lonely, and looked like {suspicion.claim.lower()}, so it seemed guilty until the detective checked it carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is carbon in this story?",
            answer="Carbon is part of charcoal, which can leave a dark mark on stone or paper.",
        ),
        QAItem(
            question="What is a temple?",
            answer="A temple is a quiet building or place for prayer, care, or special visits.",
        ),
        QAItem(
            question="What is a putt?",
            answer="A putt is a gentle roll of a golf ball toward a target.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CLUES[params.clue], SUSPICIONS[params.suspicion], params)
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
        print(trace_world(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid())
    # This world uses a very small ASP twin; compare only on the shape we encode.
    expected = set((p, c, s) for p, c, s in py)
    got = set((p, c, s) for p, c, s in cl)
    if expected == got:
        print(f"OK: clingo gate matches python gate ({len(got)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(got - expected))
    print("  only in python:", sorted(expected - got))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in [
            StoryParams("temple", "carbon", "swipe", "Nia", "Bert", "serious"),
            StoryParams("river", "putt", "prank", "Milo", "Mina", "curious"),
            StoryParams("quiet", "carbon", "prank", "Pia", "Owen", "cheerful"),
            StoryParams("hill", "putt", "swipe", "Ravi", "Zuri", "gentle"),
        ]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
