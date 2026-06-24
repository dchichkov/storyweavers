#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074326Z_seed779406221_n50/shark_inner_monologue_cautionary_foreshadowing_nursery_rhyme.py
=========================================================================================================================================

A small storyworld in a nursery-rhyme voice: a child on a seaside outing, a shark
lurking nearby, an inner monologue that notices clues, cautionary hesitation, a
foreshadowing beat, and a safe turn toward shore.

The world is modeled as typed entities with physical meters and emotional memes.
A simple causal engine updates danger and feelings from the simulated actions.
An inline ASP twin mirrors the reasonableness gate and the ending outcome.
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
SAFE_THRESHOLD = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    role: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    water: str
    home: str
    sound: str
    rhyme: str


@dataclass
class Shark:
    id: str
    name: str
    fin: str
    shadow: str
    warning: str
    foreshadow: str
    dangerous: bool = True


@dataclass
class Choice:
    id: str
    action: str
    safe: bool
    ending: str
    qa: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple[str, str]] = set()
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "beach": Setting("beach", "the bright beach", "the blue sea", "the little sandcastle home", "the hush of waves", "splashy, dashy, shh"),
    "bay": Setting("bay", "the quiet bay", "the green water", "the shell-bright shore hut", "the lap of tide", "tip-toe, toe-toe, sway"),
}

SHARKS = {
    "shark": Shark("shark", "shark", "silver fin", "dark shadow", "Stay close to shore.", "A silver fin will soon appear."),
    "reef_shark": Shark("reef_shark", "reef shark", "striped fin", "striped shadow", "Do not go past the marker.", "A striped shadow circles deep."),
}

CHOICES = {
    "shore": Choice("shore", "stayed where the water was shallow", True, "They sang and splashed near the shore.", "stayed near the shore"),
    "call_grownup": Choice("call_grownup", "called a grown-up right away", True, "A grown-up came and kept watch.", "called a grown-up"),
    "chase": Choice("chase", "went chasing the glittering fin", False, "The child chased the shark and splashed into danger.", "chased the shark"),
    "ignore": Choice("ignore", "ignored the whisper in the mind", False, "The child ignored the warning and drifted too far.", "ignored the warning"),
}

NAMES = ["Mia", "Nora", "Toby", "Luca", "Pip", "Zoe", "Finn", "Milo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Shark nursery-rhyme storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--shark", choices=SHARKS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--name")
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


@dataclass
class StoryParams:
    setting: str
    shark: str
    choice: str
    name: str
    seed: Optional[int] = None


def reasonableness_gate(params: StoryParams) -> None:
    if params.choice == "chase":
        raise StoryError("A nursery-rhyme shark story should avoid chasing the shark; choose a safer ending.")
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.shark not in SHARKS:
        raise StoryError("Unknown shark.")
    if params.choice not in CHOICES:
        raise StoryError("Unknown choice.")


def _danger_from_shark(world: World) -> None:
    child = world.get("child")
    shark = world.get("shark")
    if child.meters.get("near_water", 0) >= THRESHOLD and not child.meters.get("safe", 0):
        child.memes["worry"] = child.memes.get("worry", 0) + 1
        world.get("sea").meters["danger"] = world.get("sea").meters.get("danger", 0) + 1
        world.say(f"The water went hush-hush; the {shark.shadow} made the child feel a tiny shiver.")


def tell_story(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    shark = SHARKS[params.shark]
    choice = CHOICES[params.choice]

    child = world.add(Entity("child", kind="character", label=params.name, type="girl"))
    sea = world.add(Entity("sea", kind="thing", label=setting.water, meters={"danger": 0.0}))
    world.add(Entity("shark", kind="animal", label=shark.name, meters={"nearby": 1.0}))
    world.add(Entity("shore", kind="thing", label=setting.place))
    world.facts.update(setting=setting, shark=shark, choice=choice, child=child)

    child.meters["near_water"] = 1.0
    child.memes["joy"] = 1.0
    world.say(f"Near {setting.place}, little {params.name} played with a bucket and a shell, tra-la-la.")
    world.say(f"{setting.sound} went the water, and the child thought, {shark.foreshadow}")
    child.memes["caution"] = 1.0
    world.say(f"Inside the heart came a little voice: \"{shark.warning}\"")
    if choice.id == "shore":
        child.meters["safe"] = 1.0
        child.meters["near_water"] = 0.0
        child.memes["relief"] = 1.0
        world.say(f"{params.name} took a tiny step back and stayed by the sand.")
        world.say(f"That was the wise thing to do, and the fin passed far away.")
        world.say(choice.ending)
    elif choice.id == "call_grownup":
        child.meters["safe"] = 1.0
        child.meters["near_water"] = 0.0
        child.memes["relief"] = 1.0
        world.say(f"{params.name} called a grown-up with a bright, brave shout.")
        world.say("The grown-up came quick as a kite and kept the child on the shore.")
        world.say(choice.ending)
    elif choice.id == "ignore":
        child.memes["worry"] = 2.0
        world.say(f"But {params.name} tried to hush the little voice and drifted too close.")
        world.say(f"The {shark.name} only flashed by, yet the child learned to listen next time.")
        world.say(choice.ending)
    _danger_from_shark(world)
    world.facts["outcome"] = "safe" if child.meters.get("safe", 0) else "risky"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s: Setting = f["setting"]
    sh: Shark = f["shark"]
    c: Choice = f["choice"]
    name = f["child"].label
    return [
        f"Write a nursery-rhyme style shark story where {name} hears a warning near {s.place} and chooses to stay safe.",
        f"Tell a child-sized seaside tale with foreshadowing: {sh.foreshadow} and then {name} listens to the cautionary voice.",
        f"Make a gentle rhyme about a shark near the water, an inner monologue that says \"{sh.warning}\", and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    s: Setting = f["setting"]
    sh: Shark = f["shark"]
    c: Choice = f["choice"]
    name = f["child"].label
    return [
        QAItem(question=f"What did {name} do after hearing the warning?", answer=f"{name} {c.qa} and stayed out of danger."),
        QAItem(question=f"What clue foreshadowed the shark?", answer=f"The story said: \"{sh.foreshadow}\" before the shark was close."),
        QAItem(question="What was the little inner voice saying?", answer=f"It said, \"{sh.warning}\" so the child would stay safe."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="Why should a child stay close to shore when a shark is nearby?", answer="Because the open water is risky, and staying close to shore helps keep the child safe."),
        QAItem(question="What is foreshadowing?", answer="Foreshadowing is a little clue that hints that something important may happen soon."),
        QAItem(question="What does a cautionary warning do in a story?", answer="It helps the character notice danger and choose the safer path."),
        QAItem(question="What is inner monologue?", answer="Inner monologue is the character's private thinking voice inside their head."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid in SHARKS:
        lines.append(asp.fact("shark", sid))
    for cid in CHOICES:
        lines.append(asp.fact("choice", cid))
    lines.append(asp.fact("safe_choice", "shore"))
    lines.append(asp.fact("safe_choice", "call_grownup"))
    return "\n".join(lines)


ASP_RULES = r"""
safe(shore).
safe(call_grownup).
risky(chase).
risky(ignore).
outcome(safe) :- choice(shore).
outcome(safe) :- choice(call_grownup).
outcome(risky) :- choice(chase).
outcome(risky) :- choice(ignore).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_choices() -> list[str]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show safe/1.\n"))
    return sorted({x[0] for x in asp.atoms(model, "safe")})


def asp_outcome(params: StoryParams) -> str:
    import storyworlds.asp as asp
    program = asp_program(asp.fact("choice", params.choice), "#show outcome/1.")
    model = asp.one_model(program)
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    ok = 0
    py = {"shore", "call_grownup"}
    cl = set(asp_valid_choices())
    if cl == py:
        print("OK: ASP safe choices match Python gate.")
    else:
        ok = 1
        print("MISMATCH: ASP safe choices differ.")
    for choice in ["shore", "call_grownup", "ignore"]:
        p = StoryParams("beach", "shark", choice, "Mia")
        if choice in py and asp_outcome(p) != "safe":
            ok = 1
        if choice not in py and asp_outcome(p) != "risky":
            ok = 1
    print("OK: ASP outcome checked." if ok == 0 else "MISMATCH: ASP outcome checked.")
    return ok


CURATED = [
    StoryParams("beach", "shark", "shore", "Mia"),
    StoryParams("bay", "reef_shark", "call_grownup", "Toby"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    shark = args.shark or rng.choice(list(SHARKS))
    choice = args.choice or rng.choice(["shore", "call_grownup"])
    name = args.name or rng.choice(NAMES)
    params = StoryParams(setting=setting, shark=shark, choice=choice, name=name, seed=args.seed)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"{e.id}: {' '.join(bits)}")
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
    ap = build_parser()
    args = ap.parse_args()
    if args.show_asp:
        print(asp_program("", "#show safe/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("", "#show safe/1."))
        print("safe choices:", ", ".join(sorted(x[0] for x in asp.atoms(model, "safe"))))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            seed = (args.seed or 0) + i
            local = random.Random(seed)
            try:
                params = resolve_params(args, local)
            except StoryError as e:
                print(e)
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
        hdr = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=hdr)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
