#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/kidney_eyed_misunderstanding_suspense_dialogue_superhero_story.py
=================================================================================================

A small, self-contained storyworld for a superhero-style misunderstanding tale
with suspense and dialogue.

Seed tale used to shape the domain:
---
A young hero spots a strange clue in a stormy city and thinks a helper is lying.
The clue is really a warning about a hidden danger. After tense chasing and
shouted questions, the hero realizes the helper was trying to save everyone.
The misunderstanding clears, the danger is stopped, and the city feels safe
again.
---

This world models:
- a hero, helper, and suspect with physical meters and emotional memes
- a suspicious object whose appearance invites a misunderstanding
- suspense from delayed information and hidden danger
- dialogue that can escalate tension or resolve it
- a reasonableness gate: only plausible story premises are generated

The required seed words "kidney" and "eyed" are woven into the prose via the
clue and character descriptions.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wear": 0.0, "risk": 0.0, "pursuit": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "trust": 0.0, "confusion": 0.0, "courage": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass(frozen=True)
class Setting:
    place: str
    weather: str
    suspense: str
    affords: set[str]


@dataclass(frozen=True)
class Clue:
    id: str
    label: str
    phrase: str
    risk: str
    concealment: str
    tags: set[str]


@dataclass(frozen=True)
class Threat:
    id: str
    label: str
    method: str
    danger: str
    reveal: str
    tags: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        return c


SETTINGS = {
    "alley": Setting(place="the rain-slick alley", weather="stormy", suspense="a shuttered lamp flickered", affords={"chase", "hide", "inspect"}),
    "museum": Setting(place="the moonlit museum", weather="windy", suspense="glass cases glinted like secrets", affords={"chase", "hide", "inspect"}),
    "rooftop": Setting(place="the high rooftop", weather="windy", suspense="the skyline held its breath", affords={"chase", "hide", "inspect"}),
}

HEROES = [
    ("Captain Comet", "boy", ["brave", "bright-eyed"]),
    ("Skyline Star", "girl", ["quick", "wide-eyed"]),
    ("Thunder Kid", "boy", ["bold", "sharp-eyed"]),
]

HELPERS = [
    ("Nova", "girl", ["steady", "kind"]),
    ("Pip", "boy", ["small", "quick"]),
    ("Mira", "girl", ["calm", "clever"]),
]

SUSPECTS = [
    ("Shadow Vice", "man", ["silent", "gloved"]),
    ("Velvet Fox", "woman", ["slippery", "smiling"]),
    ("Dr. Veil", "man", ["careful", "hooded"]),
]

CLUES = {
    "kidney": Clue(
        id="kidney",
        label="kidney-shaped charm",
        phrase="a small kidney-shaped charm",
        risk="could be a secret signal",
        concealment="was tucked where only a careful eye would notice it",
        tags={"kidney", "signal"},
    ),
    "eyed": Clue(
        id="eyed",
        label="wide-eyed sketch",
        phrase="a wide-eyed sketch on folded paper",
        risk="could make someone look guilty by mistake",
        concealment="was half-hidden under a loose brick",
        tags={"eyed", "misunderstanding"},
    ),
    "battery": Clue(
        id="battery",
        label="spark battery",
        phrase="a spark battery with a blinking blue light",
        risk="could power the dangerous device",
        concealment="was wrapped in a red scarf",
        tags={"signal", "danger"},
    ),
}

THREATS = {
    "flood": Threat(id="flood", label="the flood pump", method="overload", danger="could flood the street", reveal="would shut the pump before midnight", tags={"danger"}),
    "drone": Threat(id="drone", label="the drone jammer", method="jam", danger="could knock out the city's alarms", reveal="would stop the jammer before it went live", tags={"signal", "danger"}),
    "vault": Threat(id="vault", label="the vault lock", method="seal", danger="could trap the helper inside", reveal="would keep the vault from sealing shut", tags={"misunderstanding"}),
}


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    suspect: str
    clue: str
    threat: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for clue_id, clue in CLUES.items():
            for threat_id, threat in THREATS.items():
                if "signal" in clue.tags and "signal" in threat.tags:
                    out.append((place, clue_id, threat_id))
                elif "misunderstanding" in clue.tags and threat_id == "vault":
                    out.append((place, clue_id, threat_id))
    return out


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: misunderstanding, suspense, and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--suspect")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.threat is None or c[2] == args.threat)]
    if not combos:
        raise StoryError("No reasonable superhero mystery matches the given options.")
    place, clue_id, threat_id = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HEROES)[0]
    helper = args.helper or rng.choice(HELPERS)[0]
    suspect = args.suspect or rng.choice(SUSPECTS)[0]
    return StoryParams(place=place, hero=hero, helper=helper, suspect=suspect, clue=clue_id, threat=threat_id)


def _build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero_info = next(x for x in HEROES if x[0] == params.hero)
    helper_info = next(x for x in HELPERS if x[0] == params.helper)
    suspect_info = next(x for x in SUSPECTS if x[0] == params.suspect)
    clue = CLUES[params.clue]
    threat = THREATS[params.threat]

    hero = world.add(Entity(id=_normalize_name(params.hero), kind="character", type=hero_info[1], label=params.hero, traits=hero_info[2]))
    helper = world.add(Entity(id=_normalize_name(params.helper), kind="character", type=helper_info[1], label=params.helper, traits=helper_info[2]))
    suspect = world.add(Entity(id=_normalize_name(params.suspect), kind="character", type=suspect_info[1], label=params.suspect, traits=suspect_info[2]))
    clue_ent = world.add(Entity(id=clue.id, kind="thing", type="clue", label=clue.label, phrase=clue.phrase, owner=suspect.id))
    danger = world.add(Entity(id=threat.id, kind="thing", type="threat", label=threat.label, phrase=threat.danger))

    world.facts.update(hero=hero, helper=helper, suspect=suspect, clue=clue_ent, threat=danger, clue_cfg=clue, threat_cfg=threat)
    return world


def _start(world: World) -> None:
    h = world.facts["hero"]
    helper = world.facts["helper"]
    world.say(f"{h.label} was a little superhero who noticed every flicker in {world.setting.place}.")
    world.say(f"{helper.label} stayed close, because {world.setting.suspense}.")
    world.say(f"That night, they were looking for {world.facts['clue_cfg'].phrase}, and {helper.label} kept saying, \"Stay calm and listen.\"")


def _misunderstanding(world: World) -> None:
    h = world.facts["hero"]
    suspect = world.facts["suspect"]
    clue = world.facts["clue_cfg"]
    threat = world.facts["threat_cfg"]
    world.para()
    world.say(f"At the end of a dark corridor, {h.label} saw {suspect.label} near the clue.")
    if clue.id == "kidney":
        world.say(f"The tiny kidney-shaped charm gleamed once in the dark, and {h.label} thought it was proof of trouble.")
    elif clue.id == "eyed":
        world.say(f"The wide-eyed sketch looked like a sneaky warning, and {h.label} feared {suspect.label} had done something awful.")
    else:
        world.say(f"The blinking battery made the hallway feel even more dangerous.")
    h.memes["confusion"] += 1
    h.memes["fear"] += 1
    suspect.meters["risk"] += 1
    world.say(f'"You took it!" {h.label} shouted. "No," {suspect.label} snapped back, "I hid it so nobody would get hurt."')
    world.say(f"The answer did not fit yet, and that made the shadows feel longer.")
    if threat.id == "vault":
        world.say(f"Somewhere ahead, the vault lock clicked, and everyone froze.")


def _suspense(world: World) -> None:
    h = world.facts["hero"]
    helper = world.facts["helper"]
    suspect = world.facts["suspect"]
    threat = world.facts["threat_cfg"]
    h.meters["pursuit"] += 1
    helper.memes["trust"] += 1
    world.para()
    world.say(f"{helper.label} whispered, \"Don't rush. Look for the real danger.\"")
    world.say(f"They followed the clue deeper into {world.setting.place}, where {world.setting.suspense}.")
    world.say(f"{suspect.label} ran ahead, but not away; {suspect.pronoun()} kept checking the ceiling and the floor.")
    world.say(f"Then a red light blinked on. The hidden {threat.label} was almost ready.")
    world.say(f"{h.label} swallowed hard. The chase was not about a stolen clue at all; it was about stopping {threat.danger}.")


def _reveal(world: World) -> None:
    h = world.facts["hero"]
    helper = world.facts["helper"]
    suspect = world.facts["suspect"]
    threat = world.facts["threat_cfg"]
    clue = world.facts["clue_cfg"]
    world.para()
    world.say(f'"I thought you were the wrong one," {h.label} said, panting.')
    world.say(f'"I thought you would never ask," {suspect.label} replied. "{clue.concealment.capitalize()}, and I needed you to find it."')
    world.say(f"{helper.label} nodded. \"That was the warning. The clue pointed to the {threat.label}.\"")
    world.say(f"{h.label} looked from the clue to the blinking machine and felt the truth settle into place.")
    h.memes["confusion"] = 0.0
    h.memes["courage"] += 1
    h.memes["relief"] += 1
    helper.memes["trust"] += 1
    suspect.memes["relief"] = 1.0
    world.say(f"With one quick move, {h.label} used a burst of power to stop the {threat.method}.")
    world.say(f"The danger went quiet, and the city could breathe again.")


def _ending(world: World) -> None:
    h = world.facts["hero"]
    helper = world.facts["helper"]
    suspect = world.facts["suspect"]
    world.para()
    world.say(f'{helper.label} smiled. "{h.label}, next time ask before you accuse."')
    world.say(f'{h.label} grinned back. "Next time, I will. And you can still call me bright-eyed if I forget."')
    world.say(f"{suspect.label} laughed, and the three of them walked out together under the safe, quiet sky.")
    world.say(f"In the end, the kidney-shaped clue was not a bad sign after all, and the wide-eyed worry had turned into trust.")


def _tell(world: World) -> None:
    _start(world)
    _misunderstanding(world)
    _suspense(world)
    _reveal(world)
    _ending(world)


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    _tell(world)
    prompts = [
        f'Write a superhero story with a misunderstanding, suspense, and dialogue in {SETTINGS[params.place].place}.',
        f"Tell a child-friendly story where {params.hero} thinks {params.suspect} is hiding something, but the truth is kinder than it seems.",
        f'Write a short superhero tale that includes the words "kidney" and "eyed" and ends with relief.',
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


def _story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    suspect = f["suspect"]
    clue = f["clue_cfg"]
    threat = f["threat_cfg"]
    return [
        QAItem(
            question=f"Why did {hero.label} first get upset in the story?",
            answer=f"{hero.label} saw {suspect.label} near {clue.label} and thought {suspect.pronoun()} had taken something important, so the scene felt like a bad secret at first.",
        ),
        QAItem(
            question=f"What was the real reason {suspect.label} acted suspicious?",
            answer=f"{suspect.label} was hiding the clue to warn everyone about {threat.danger}, not to cause the problem.",
        ),
        QAItem(
            question=f"How did {helper.label} help clear up the misunderstanding?",
            answer=f"{helper.label} told {hero.label} to slow down, look closely, and listen, which helped everyone see that the clue was a warning.",
        ),
        QAItem(
            question=f"What happened when the truth was finally revealed?",
            answer=f"{hero.label} understood the mistake, stopped the {threat.method}, and the city became safe and quiet again.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a situation means one thing, but it really means something else.",
        ),
        QAItem(
            question="What does suspense do in a story?",
            answer="Suspense makes you wait and wonder what will happen next, which can make a story feel exciting.",
        ),
        QAItem(
            question="Why is dialogue useful in a superhero story?",
            answer="Dialogue lets the characters ask questions, warn each other, and explain the truth with their own voices.",
        ),
    ]
    if world.facts["clue_cfg"].id == "kidney":
        out.append(QAItem(
            question="What does kidney mean in this story?",
            answer="Here, kidney is part of the clue's shape, because the charm looks like a little kidney-shaped object.",
        ))
    if world.facts["clue_cfg"].id == "eyed":
        out.append(QAItem(
            question="What does eyed mean in this story?",
            answer="Here, eyed appears in the clue description to show a wide-eyed sketch, which helps create a worried, watchful feeling.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.label or e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
% A clue is suspicious when it is a kidney-shaped charm, a wide-eyed sketch, or a blinking battery.
suspicious(C) :- clue(C), clue_kind(C,kidney).
suspicious(C) :- clue(C), clue_kind(C,eyed).
suspicious(C) :- clue(C), clue_kind(C,battery).

% The hero begins confused if a suspect is near a suspicious clue.
misunderstanding(H) :- hero(H), nearby_suspect(H,S), suspicious(C), seen_together(H,S,C).

% Suspense exists if the setting has a tense atmosphere and the threat is not yet revealed.
suspense(P) :- place(P), tense(P), not revealed(P).

% The truth is resolved when the hero and helper learn the real threat.
resolved(P) :- place(P), hero_learns_truth(P), helper_explains(P).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.weather:
            lines.append(asp.fact("tense", pid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_kind", cid, clue.id))
    for tid in THREATS:
        lines.append(asp.fact("threat", tid))
    for place in SETTINGS:
        for clue in CLUES:
            for threat in THREATS:
                if (place, clue, threat) in valid_combos():
                    lines.append(asp.fact("valid", place, clue, threat))
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
    print("MISMATCH between clingo and python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="alley", hero="Captain Comet", helper="Nova", suspect="Shadow Vice", clue="kidney", threat="drone"),
    StoryParams(place="museum", hero="Skyline Star", helper="Mira", suspect="Velvet Fox", clue="eyed", threat="vault"),
    StoryParams(place="rooftop", hero="Thunder Kid", helper="Pip", suspect="Dr. Veil", clue="battery", threat="flood"),
]


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
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print("  ", c)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} at {p.place} with {p.clue} / {p.threat}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
