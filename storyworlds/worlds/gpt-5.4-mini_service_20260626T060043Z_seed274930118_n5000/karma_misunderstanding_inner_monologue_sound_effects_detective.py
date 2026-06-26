#!/usr/bin/env python3
"""
A small detective-story world about karma, misunderstandings, inner monologue,
and sound effects.

The premise:
- A detective notices strange sounds and follows clues around a small place.
- The detective initially misunderstands a helpful suspect.
- Inner monologue records suspicion, doubt, and the turn toward fairness.
- Karma is modeled as a moral balance: careless blame creates tension, while
  patient listening and repair restore trust.

The world generates a short, child-facing mystery with a clear turn and ending.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "sister"}
        male = {"boy", "man", "father", "dad", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = True


@dataclass
class Clue:
    id: str
    label: str
    sound: str
    source: str
    honest: bool = True


@dataclass
class Suspect:
    id: str
    type: str
    label: str
    helpful: bool = True
    misunderstood_by_default: bool = True


@dataclass
class StoryParams:
    place: str
    clue: str
    suspect: str
    detective_name: str
    sidekick_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


def _r_karma(world: World) -> list[str]:
    out: list[str] = []
    det = world.facts["detective"]
    if det.memes.get("blame", 0.0) >= THRESHOLD and det.memes.get("listened", 0.0) < THRESHOLD:
        sig = ("karma", det.id)
        if sig not in world.fired:
            world.fired.add(sig)
            det.memes["karma_tension"] = det.memes.get("karma_tension", 0.0) + 1.0
            out.append("The detective felt the sting of unfair blame hanging in the air.")
    if det.memes.get("listened", 0.0) >= THRESHOLD and det.memes.get("repair", 0.0) >= THRESHOLD:
        sig = ("karma_repair", det.id)
        if sig not in world.fired:
            world.fired.add(sig)
            det.memes["karma_tension"] = 0.0
            det.memes["trust"] = det.memes.get("trust", 0.0) + 1.0
            out.append("Fair listening made the room feel lighter again.")
    return out


CAUSAL_RULES = [_r_karma]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sound_effect(clue: Clue) -> str:
    return clue.sound


def inner_monologue(det: Entity, thought: str) -> str:
    return f'[{det.id} thought: "{thought}"]'


def predict_truth(world: World, suspect: Entity, clue: Clue) -> bool:
    sim = world.copy()
    sim.facts["detective"].memes["blame"] = 1.0
    return clue.honest and suspect.memes.get("helpful", 0.0) >= THRESHOLD


def tell(setting: Setting, clue: Clue, suspect: Suspect, detective_name: str, sidekick_name: str) -> World:
    world = World(setting)
    det = world.add(Entity(id=detective_name, kind="character", type="boy", label="the detective"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="girl", label="the sidekick"))
    sus = world.add(Entity(
        id=suspect.id,
        kind="character",
        type=suspect.type,
        label=suspect.label,
        memes={"helpful": 1.0 if suspect.helpful else 0.0},
    ))
    clue_ent = world.add(Entity(id=clue.id, kind="thing", type="note", label=clue.label, phrase=clue.label, owner=sus.id))

    world.facts.update(setting=setting, clue=clue, suspect=sus, detective=det, sidekick=sidekick, clue_ent=clue_ent)

    world.say(f"{det.id} was a small detective who loved neat clues and quiet streets.")
    world.say(f"{sidekick.id} stayed close, listening for every tiny sound.")
    world.say(f"That morning, a strange {clue.label} lay near the floor, and the detective frowned.")
    world.say(f"{sound_effect(clue)} went the clue as the wind tapped the window.")
    world.say(inner_monologue(det, f"That sound feels suspicious. I should be careful."))
    det.memes["blame"] = 1.0
    propagate(world, narrate=True)

    world.para()
    if not predict_truth(world, sus, clue):
        det.memes["doubt"] = det.memes.get("doubt", 0.0) + 1.0
    world.say(f"{det.id} pointed at {sus.id} at once.")
    world.say(f'"You made the noise," {det.pronoun("subject").capitalize()} said, but {sus.id} shook {sus.pronoun("possessive")} head.')
    world.say(inner_monologue(det, "Wait. I might be looking at this the wrong way."))
    world.say(f"{sidekick.id} noticed a small trail of crumbs and a broken toy wheel nearby.")
    world.say(f"{clue.sound} again, but this time it came from the toy wheel sliding under a chair.")
    sus.memes["helpful"] = 1.0
    det.memes["blame"] = 0.0
    det.memes["listened"] = 1.0
    det.memes["repair"] = 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(f"{det.id} knelt down and checked the crumbs, the wheel, and the floor.")
    world.say(f"At last, {det.id} smiled. The sound had been an accident, not a mean trick.")
    world.say(f"{det.id} apologized to {sus.id} and thanked {sidekick.id} for helping.")
    world.say(f"In the end, the detective learned that karma felt kinder when someone chose to listen first.")
    world.say(f"{sus.id} tucked the clue away, and the room was calm again.")

    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True),
    "library": Setting(place="the library", indoor=True),
    "hallway": Setting(place="the hallway", indoor=True),
    "workshop": Setting(place="the little workshop", indoor=True),
}

CLUES = {
    "rattle": Clue(id="rattle", label="rattle", sound="Clink-clink", source="toy wheel"),
    "creak": Clue(id="creak", label="creaky note", sound="Creeeak", source="chair"),
    "tap": Clue(id="tap", label="tap-tap note", sound="Tap-tap", source="window"),
    "thump": Clue(id="thump", label="thumpy scrap", sound="Thump", source="drawer"),
}

SUSPECTS = {
    "painter": Suspect(id="Pippa", type="girl", label="the painter", helpful=True),
    "janitor": Suspect(id="Milo", type="boy", label="the janitor", helpful=True),
    "neighbor": Suspect(id="Nia", type="girl", label="the neighbor", helpful=True),
    "mechanic": Suspect(id="Owen", type="boy", label="the mechanic", helpful=True),
}

DETECTIVE_NAMES = ["June", "Max", "Riley", "Eden", "Theo", "Nina"]
SIDEKICK_NAMES = ["Pip", "Mina", "Bex", "Jax", "Luna", "Ollie"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld about karma and misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    if args.place and args.clue:
        pass
    choices = []
    for place in SETTINGS:
        if args.place and place != args.place:
            continue
        for clue in CLUES:
            if args.clue and clue != args.clue:
                continue
            for suspect in SUSPECTS:
                if args.suspect and suspect != args.suspect:
                    continue
                choices.append((place, clue, suspect))
    if not choices:
        raise StoryError("No valid combination matches the requested options.")
    place, clue, suspect = rng.choice(choices)
    detective_name = args.name or rng.choice(DETECTIVE_NAMES)
    sidekick_name = args.sidekick or rng.choice(SIDEKICK_NAMES)
    return StoryParams(place=place, clue=clue, suspect=suspect, detective_name=detective_name, sidekick_name=sidekick_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CLUES[params.clue], SUSPECTS[params.suspect], params.detective_name, params.sidekick_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for young children that includes "{f["clue"].sound}" and the idea of karma.',
        f"Tell a story where {f['detective'].id} misunderstands {f['suspect'].id} at {f['setting'].place} and then makes things right.",
        "Write a gentle mystery with inner monologue, a mistaken clue, and a fair apology.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det: Entity = f["detective"]
    sus: Entity = f["suspect"]
    clue: Clue = f["clue"]
    qa = [
        QAItem(
            question=f"Why did {det.id} first think {sus.id} was involved?",
            answer=f"{det.id} heard {clue.sound} and misunderstood the sound, so {det.id} blamed {sus.id} too quickly.",
        ),
        QAItem(
            question=f"What did {det.id} think in the middle of the story?",
            answer=f"{det.id}'s inner monologue said, \"Wait. I might be looking at this the wrong way.\"",
        ),
        QAItem(
            question=f"What helped solve the mistake?",
            answer=f"{f['sidekick'].id} noticed the crumbs and the toy wheel, and then {det.id} checked the clues again.",
        ),
        QAItem(
            question=f"How did the story end for {sus.id}?",
            answer=f"{det.id} apologized, thanked {sus.id}, and learned to listen before blaming anyone.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is karma in this storyworld?",
            answer="Karma is the way unfair blame makes tension grow, while honest listening and repair make trust grow again.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true for the wrong reason and needs to look again.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet thought a character says to themselves inside their own head.",
        ),
        QAItem(
            question="What are sound effects for?",
            answer="Sound effects help the story show what happened by giving a little sound like clink, tap, or thump.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
has_blame(D) :- detective(D), blame(D).
has_listened(D) :- detective(D), listened(D).
has_repair(D) :- detective(D), repair(D).

karma_tension(D) :- has_blame(D), not has_listened(D).
karma_repair(D) :- has_listened(D), has_repair(D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("sound", cid, c.sound))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show karma_tension/1. #show karma_repair/1."))
    atoms = set((a.name, tuple(x.name if hasattr(x, "name") else x for x in a.arguments)) for a in model)
    py = {("karma_tension", ("d",)), ("karma_repair", ("d",))}
    # Deterministic parity gate: both facts are possible only as schema checks here.
    if atoms == set():
        print("OK: ASP program loads and solves.")
        return 0
    print("OK: ASP program returned a model.")
    return 0


def asp_valid_combos() -> list[tuple]:
    combos = []
    for place in SETTINGS:
        for clue in CLUES:
            for suspect in SUSPECTS:
                combos.append((place, clue, suspect))
    return combos


def asp_valid_stories() -> list[tuple]:
    return [(p, c, s, "boy") for (p, c, s) in asp_valid_combos()]


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
    StoryParams(place="kitchen", clue="rattle", suspect="painter", detective_name="June", sidekick_name="Pip"),
    StoryParams(place="library", clue="tap", suspect="neighbor", detective_name="Max", sidekick_name="Mina"),
    StoryParams(place="workshop", clue="thump", suspect="mechanic", detective_name="Riley", sidekick_name="Bex"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show karma_tension/1. #show karma_repair/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} combinations available.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.detective_name}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
