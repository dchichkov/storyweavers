#!/usr/bin/env python3
"""
A tiny detective-story world about a missing quarter, a surprise clue, and a
kind act that leads to reconciliation.

Premise:
A child detective notices that a small toy raptor is worth only a quarter,
but the quarter has gone missing. The search turns into a gentle mystery with a
surprising clue, a helpful act, and a soft ending where everyone makes peace.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    discovered: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the small museum lobby"
    afford_surprise: bool = True
    afford_search: bool = True


@dataclass
class StoryParams:
    setting: str = "lobby"
    raptor_name: str = "Rex"
    detective_name: str = "Mina"
    helper_name: str = "Toby"
    seed: Optional[int] = None


SETTINGS = {
    "lobby": Setting(place="the small museum lobby"),
    "desk": Setting(place="the front desk"),
    "shed": Setting(place="the quiet storage shed"),
    "hall": Setting(place="the narrow hall"),
}

DETECTIVE_NAMES = ["Mina", "Ivy", "Nina", "Piper", "Lena"]
HELPER_NAMES = ["Toby", "Owen", "Jules", "Eli", "Noah"]
RAPTOR_NAMES = ["Rex", "Ruby", "Rolo", "Rina", "Riff"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


def _setup_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    world = World(SETTINGS[params.setting])
    detective = world.add(Entity(id="detective", kind="character", type="girl", label=params.detective_name))
    helper = world.add(Entity(id="helper", kind="character", type="boy", label=params.helper_name))
    raptor = world.add(Entity(id="raptor", kind="thing", type="raptor", label=params.raptor_name))
    quarter = world.add(Entity(id="quarter", kind="thing", type="coin", label="quarter", owner="raptor"))
    return world


def _introduce(world: World) -> None:
    det = world.get("detective")
    rap = world.get("raptor")
    world.say(
        f"{det.label} was a little detective who noticed every tiny detail in {world.setting.place}."
    )
    world.say(
        f"On the counter sat {rap.label}, a small toy raptor that was worth a quarter."
    )


def _mystery(world: World) -> None:
    det = world.get("detective")
    rap = world.get("raptor")
    q = world.get("quarter")
    det.memes["curious"] = 1
    rap.memes["hopeful"] = 1
    world.para()
    world.say(
        f"Then {q.label} disappeared, and {det.label} frowned at the empty spot where it had been."
    )
    world.say(
        f"{det.label} said the missing coin made {rap.label} look lonely and unfinished."
    )


def _search(world: World) -> None:
    det = world.get("detective")
    helper = world.get("helper")
    q = world.get("quarter")
    world.para()
    det.memes["worry"] = 1
    world.say(
        f"{det.label} looked under a paper cup, beside a basket, and behind the sign."
    )
    world.say(
        f"{helper.label} joined in and helped with a careful search, because kindness makes hard jobs lighter."
    )
    q.discovered = True
    q.meters["found"] = 1
    world.say(
        f"At last, they found the quarter tucked inside a folded map, like a surprise clue waiting to be seen."
    )


def _reconcile(world: World) -> None:
    det = world.get("detective")
    helper = world.get("helper")
    rap = world.get("raptor")
    q = world.get("quarter")
    det.memes["relief"] = 1
    det.memes["joy"] = 1
    helper.memes["kindness"] = 1
    rap.memes["reconciled"] = 1
    world.para()
    world.say(
        f"{det.label} smiled, put the quarter back beside {rap.label}, and thanked {helper.label} for the kindness."
    )
    world.say(
        f"The little raptor looked bright again, and everyone felt reconciled when the mystery was solved."
    )
    world.say(
        f"In the end, the quarter was only worth a little money, but the helpful surprise and the kind ending were worth much more."
    )


def generate_story(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    _introduce(world)
    _mystery(world)
    _search(world)
    _reconcile(world)
    world.facts.update(
        detective=world.get("detective"),
        helper=world.get("helper"),
        raptor=world.get("raptor"),
        quarter=world.get("quarter"),
    )
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    det = world.get("detective")
    return [
        "Write a short detective story for a young child about a missing quarter and a toy raptor.",
        f"Tell a gentle mystery where {det.label} finds a surprise clue and a kind helper makes things better.",
        "Write a story that ends with reconciliation after the missing coin is found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    det = world.get("detective")
    helper = world.get("helper")
    rap = world.get("raptor")
    return [
        QAItem(
            question="Who was the detective in the story?",
            answer=f"The detective was {det.label}, who kept noticing little clues in {world.setting.place}.",
        ),
        QAItem(
            question="What was the surprise clue?",
            answer="The surprise clue was the quarter hidden inside a folded map.",
        ),
        QAItem(
            question="Who helped with kindness?",
            answer=f"{helper.label} helped with kindness by searching carefully until the quarter was found.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"{rap.label} got its quarter back, and everyone ended the story feeling reconciled and happy.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quarter?",
            answer="A quarter is a small coin worth twenty-five cents.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping, caring, and using gentle actions toward others.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and make peace again.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.discovered:
            bits.append("discovered=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
missing_quarter :- quarter, not found_quarter.
found_quarter :- found_quarter_fact.
kind_help :- helper_kind.
happy_end :- missing_quarter, found_quarter, kind_help.
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("quarter"),
        asp.fact("helper_kind"),
        asp.fact("found_quarter_fact"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_end/0."))
    ok = any(sym.name == "happy_end" for sym in model)
    if ok:
        print("OK: ASP model confirms the happy ending.")
        return 0
    print("MISMATCH: ASP model did not confirm the happy ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world about a missing quarter, a toy raptor, and a kind reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    return StoryParams(
        setting=setting,
        raptor_name=rng.choice(RAPTOR_NAMES),
        detective_name=rng.choice(DETECTIVE_NAMES),
        helper_name=rng.choice(HELPER_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    return generate_story(params)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
    StoryParams(setting="lobby", raptor_name="Rex", detective_name="Mina", helper_name="Toby"),
    StoryParams(setting="desk", raptor_name="Ruby", detective_name="Ivy", helper_name="Jules"),
    StoryParams(setting="shed", raptor_name="Rolo", detective_name="Nina", helper_name="Owen"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_end/0."))
        print("ASP atoms:", [str(s) for s in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.detective_name}: {p.setting}, raptor={p.raptor_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
