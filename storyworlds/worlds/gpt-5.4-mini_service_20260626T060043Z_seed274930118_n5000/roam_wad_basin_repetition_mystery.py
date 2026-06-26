#!/usr/bin/env python3
"""
A tiny mystery storyworld: a child roams, notices a wad near a basin, and
solves a small puzzle through repetition and careful looking.

The premise is close to a children's mystery: something is out of place, the
hero keeps circling the same places, and the repeated details reveal the answer.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoors: bool
    rooms: list[str]
    has_basin: bool = False
    has_roam_paths: bool = True


@dataclass
class Clue:
    id: str
    label: str
    place: str
    kind: str
    significance: str


@dataclass
class StoryParams:
    setting: str
    clue: str
    hero_name: str
    hero_type: str
    witness_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Place):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "location": v.location,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_repeat_notice(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    clue = world.entities.get("clue")
    if not hero or not clue:
        return out
    if hero.meters.get("roam", 0) >= 2 and clue.meters.get("noticed", 0) >= 1:
        sig = ("repeat_notice",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
        out.append("The same small detail kept coming back to mind.")
    return out


def _r_solve(world: World) -> list[str]:
    hero = world.entities.get("hero")
    clue = world.entities.get("clue")
    if not hero or not clue:
        return []
    if hero.meters.get("roam", 0) >= 2 and clue.meters.get("noticed", 0) >= 2:
        sig = ("solve",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        hero.memes["relief"] = hero.memes.get("relief", 0) + 1
        return ["__solve__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_repeat_notice, _r_solve):
            got = fn(world)
            if got:
                changed = True
                out.extend(x for x in got if x != "__solve__")
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTINGS = {
    "house": Place(name="the house", indoors=True, rooms=["hall", "kitchen", "bathroom"], has_basin=True),
    "garden": Place(name="the garden", indoors=False, rooms=["path", "shed"], has_basin=False),
    "school": Place(name="the school", indoors=True, rooms=["cloakroom", "office", "washroom"], has_basin=True),
}

CLUES = {
    "wad": Clue(id="wad", label="wad", place="basin", kind="paper", significance="it had been used to block a drip"),
    "note": Clue(id="note", label="note", place="desk", kind="paper", significance="it hinted at a hidden key"),
    "spoon": Clue(id="spoon", label="spoon", place="sink", kind="metal", significance="it pointed to a missing kitchen item"),
}

NAMES = ["Milo", "Nia", "Tara", "Eli", "June", "Owen", "Iris", "Finn"]
WITNESSES = ["Mom", "Dad", "the teacher", "the neighbor"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s_name, setting in SETTINGS.items():
        for c_name, clue in CLUES.items():
            if clue.place == "basin" and not setting.has_basin:
                continue
            combos.append((s_name, c_name))
    return combos


@dataclass
class Rule:
    name: str
    apply: object


CAUSAL_RULES = [
    Rule("repeat_notice", _r_repeat_notice),
    Rule("solve", _r_solve),
]


def roam(world: World, hero: Entity, setting: Place) -> None:
    hero.meters["roam"] = hero.meters.get("roam", 0) + 1
    hero.memes["unease"] = hero.memes.get("unease", 0) + 1
    world.say(f"{hero.id} roamed from room to room, listening for anything odd.")
    if setting.indoors:
        world.say(f"{hero.pronoun().capitalize()} passed the same doors again and again.")
    else:
        world.say(f"{hero.pronoun().capitalize()} circled the path twice, looking for a sign.")


def notice_wad(world: World, hero: Entity, clue: Entity) -> None:
    clue.meters["noticed"] = clue.meters.get("noticed", 0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(f"Then {hero.id} found a small wad near the basin.")
    world.say(f"It looked ordinary at first, but the wad did not belong there.")


def repeat_look(world: World, hero: Entity, clue: Entity) -> None:
    clue.meters["noticed"] = clue.meters.get("noticed", 0) + 1
    hero.meters["roam"] = hero.meters.get("roam", 0) + 1
    world.say(f"{hero.id} looked again, and the same wad was still there.")
    world.say(f"This time {hero.id} noticed where the wet mark led.")


def reveal(world: World, hero: Entity, witness: Entity, clue: Entity) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.say(
        f"{hero.id} told {witness.id} the answer: the wad had been stuck by the basin "
        f"to stop a drip, and the repeated visits had made the clue impossible to miss."
    )
    world.say(
        f"With the mystery solved, the basin looked ordinary again, and the small room "
        f"felt calm instead of puzzling."
    )


def tell(setting: Place, clue_cfg: Clue, hero_name: str, hero_type: str, witness_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    clue = world.add(Entity(id="clue", type=clue_cfg.kind, label=clue_cfg.label, location=clue_cfg.place))
    witness = world.add(Entity(id="witness", kind="character", type="adult", label=witness_name))

    world.say(f"{hero_name} was a small {hero_type} who loved a mystery.")
    world.say(f"One quiet day, {hero_name} went roaming through {setting.name}.")
    world.say(f"Something felt off near the basin, where a tiny {clue_cfg.label} waited.")

    world.para()
    roam(world, hero, setting)
    notice_wad(world, hero, clue)
    world.say(f"The clue seemed ordinary, but its place made it strange.")

    world.para()
    repeat_look(world, hero, clue)
    propagate(world, narrate=True)
    reveal(world, hero, witness, clue)

    world.facts.update(
        hero=hero,
        clue=clue,
        witness=witness,
        setting=setting,
        clue_cfg=clue_cfg,
        repeated=hero.meters.get("roam", 0) >= 2,
        solved=hero.memes.get("relief", 0) >= 1,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a small child that includes "roam", "wad", and "basin".',
        f"Tell a gentle mystery where {f['hero'].label} keeps roaming and notices the same clue twice.",
        f"Write a child-friendly story about a tiny mystery in {f['setting'].name} that is solved by repeating the search.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    witness = f["witness"]
    clue = f["clue"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What did {hero.label} keep doing in {setting.name}?",
            answer=f"{hero.label} kept roaming from place to place because something felt strange.",
        ),
        QAItem(
            question=f"What did {hero.label} find near the basin?",
            answer=f"{hero.label} found a small {clue.label} near the basin, and that was the strange clue.",
        ),
        QAItem(
            question=f"Why did the clue matter?",
            answer=f"It mattered because the same {clue.label} kept showing up in the same spot, which meant it was not random.",
        ),
        QAItem(
            question=f"Who heard the answer to the mystery?",
            answer=f"{hero.label} told {witness.label} how the {clue.label} by the basin solved the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to roam?",
            answer="To roam means to move around from one place to another without staying in just one spot.",
        ),
        QAItem(
            question="What is a wad?",
            answer="A wad is a small bunch of something soft or crumpled, like paper or cloth.",
        ),
        QAItem(
            question="What is a basin?",
            answer="A basin is a bowl-like container or sink that holds water.",
        ),
        QAItem(
            question="Why can repetition help in a mystery?",
            answer="Repetition can help because seeing the same clue again and again makes it easier to notice what it means.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== story prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
clue(C) :- clue_fact(C).
basin_setting(S) :- has_basin(S).

valid(S, C) :- setting_fact(S), clue_fact(C), clue_place(C, basin), basin_setting(S).
valid(S, C) :- setting_fact(S), clue_fact(C), clue_place(C, P), P != basin.
repeated(S) :- valid(S, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        if s.has_basin:
            lines.append(asp.fact("has_basin", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue_fact", cid))
        lines.append(asp.fact("clue_place", cid, c.place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny mystery storyworld with roam, wad, basin, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--witness")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
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
    if args.setting or args.clue:
        combos = [c for c in combos if (args.setting is None or c[0] == args.setting) and (args.clue is None or c[1] == args.clue)]
    if not combos:
        raise StoryError("(No valid story matches the given options.)")
    setting, clue = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(NAMES)
    witness = args.witness or rng.choice(WITNESSES)
    return StoryParams(setting=setting, clue=clue, hero_name=hero_name, hero_type=hero_type, witness_name=witness)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], params.hero_name, params.hero_type, params.witness_name)
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


CURATED = [
    StoryParams(setting="house", clue="wad", hero_name="Milo", hero_type="boy", witness_name="Mom"),
    StoryParams(setting="school", clue="wad", hero_name="Iris", hero_type="girl", witness_name="the teacher"),
    StoryParams(setting="house", clue="note", hero_name="Nia", hero_type="girl", witness_name="Dad"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, c in combos:
            print(f"  {s:8} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero_name}: {p.setting} / {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
