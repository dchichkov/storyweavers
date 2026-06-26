#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/teller_remainder_margarita_quest_animal_story.py
=================================================================================================

A small, self-contained storyworld in the Animal Story style.

Seed tale:
- A teller, a remainder, and a margarita are part of a quest.
- The world is animal-centered, concrete, and child-facing.
- The story turns on a simple problem: the quest item is incomplete, so the
  animal heroes must decide how to finish the errand and who should carry what.

The world model tracks both physical meters and emotional memes:
- meters: distance, weight, completeness, tidiness, shine
- memes: worry, courage, trust, joy, relief

The domain's core premise is that a small animal team receives a quest from a
teller. They find a remainder of something important, and a character named
Margarita helps them finish the errand in a satisfying way.
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

SETTING_NAME = "the little river market"


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "animal" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0, "completeness": 0.0, "tidiness": 0.0, "shine": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0, "courage": 0.0, "trust": 0.0, "joy": 0.0, "relief": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "she", "cat", "rabbit", "mouse", "duck"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "he", "fox", "bear", "dog", "goat", "turtle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = SETTING_NAME


@dataclass
class StoryParams:
    teller: str
    remainder: str
    margarita: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace_log: list[str] = []
        self.done: set[str] = set()

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

    def log(self, text: str) -> None:
        self.trace_log.append(text)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story: a teller, a remainder, and a margarita on a quest.")
    ap.add_argument("--teller")
    ap.add_argument("--remainder")
    ap.add_argument("--margarita")
    ap.add_argument("--name")
    ap.add_argument("--type")
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-type")
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
    teller = args.teller or rng.choice(["Teller", "Old Teller", "River Teller"])
    remainder = args.remainder or rng.choice(["remainder", "little remainder", "lost remainder"])
    margarita = args.margarita or rng.choice(["Margarita", "Captain Margarita", "Margarita the Mouse"])
    hero_name = args.name or rng.choice(["Nina", "Pip", "Milo", "Lulu", "Toby"])
    hero_type = args.type or rng.choice(["rabbit", "fox", "duck", "mouse", "bear"])
    sidekick_name = args.sidekick or rng.choice(["Mina", "Dot", "Bibi", "Sunny", "Momo"])
    sidekick_type = args.sidekick_type or rng.choice(["mouse", "duck", "cat", "goat", "turtle"])
    return StoryParams(teller=teller, remainder=remainder, margarita=margarita, hero_name=hero_name, hero_type=hero_type, sidekick_name=sidekick_name, sidekick_type=sidekick_type)


def _maybe_article(text: str) -> str:
    return text if text.lower().startswith(("a ", "an ", "the ")) else f"the {text}"


def tell(params: StoryParams) -> World:
    w = World(Setting())
    hero = w.add(Entity(id=params.hero_name, kind="animal", type=params.hero_type, label=params.hero_name))
    sidekick = w.add(Entity(id=params.sidekick_name, kind="animal", type=params.sidekick_type, label=params.sidekick_name))
    teller = w.add(Entity(id="teller", kind="animal", type="turtle", label=params.teller))
    remainder = w.add(Entity(id="remainder", kind="thing", type="thing", label=params.remainder, phrase=f"the {params.remainder}", owner=teller.id))
    margarita = w.add(Entity(id="margarita", kind="animal", type="goat", label=params.margarita))
    quest = w.add(Entity(id="quest", kind="thing", type="thing", label="quest", phrase="the quest", plural=False))

    w.facts.update(hero=hero, sidekick=sidekick, teller=teller, remainder=remainder, margarita=margarita, quest=quest)

    hero.memes["joy"] += 1
    sidekick.memes["trust"] += 1

    w.say(
        f"At {w.setting.place}, {hero.label} the {hero.type} and {sidekick.label} the {sidekick.type} listened to {teller.label}, "
        f"who had a small quest with a missing piece."
    )
    w.say(
        f"{teller.label} explained that the story would not be finished until the {remainder.label} was brought back."
    )
    w.para()

    hero.memes["worry"] += 1
    w.say(
        f"{hero.label} looked at the half-finished map and felt a little worry, because a quest is hard when it is not whole."
    )
    w.say(
        f"Then {margarita.label} arrived with bright eyes and a brave step, ready to help find the rest."
    )
    w.para()

    remainder.meters["distance"] = 1.0
    hero.memes["courage"] += 1
    sidekick.memes["courage"] += 1
    w.say(
        f"The three friends followed a narrow path by the water, searched under reeds, and peeked behind a stack of clean crates."
    )
    w.say(
        f"At last, {sidekick.label} found the {remainder.label} tucked beside a lantern, safe and dry."
    )
    w.para()

    remainder.meters["completeness"] = 1.0
    remainder.meters["tidiness"] = 1.0
    margarita.memes["joy"] += 1
    teller.memes["relief"] += 1
    hero.memes["joy"] += 1
    w.say(
        f"{margarita.label} carried the {remainder.label} back carefully, and {teller.label} joined it to the waiting page."
    )
    w.say(
        f"The quest was whole again, and the little market felt warm and bright."
    )
    w.para()

    w.say(
        f"{hero.label} smiled at {margarita.label} and {sidekick.label}, because a good quest ends with help, not hurry."
    )
    w.say(
        f"{teller.label} waved goodbye while the finished {remainder.label} shone in the lantern light."
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    sidekick: Entity = f["sidekick"]  # type: ignore[assignment]
    teller: Entity = f["teller"]  # type: ignore[assignment]
    remainder: Entity = f["remainder"]  # type: ignore[assignment]
    margarita: Entity = f["margarita"]  # type: ignore[assignment]
    return [
        f'Write a short Animal Story about {hero.label} and {sidekick.label} on a quest at {SETTING_NAME}.',
        f"Tell a child-friendly story where {teller.label} needs the {remainder.label} found, and {margarita.label} helps bring it back.",
        f'Write a gentle animal quest story that includes the words "{teller.label}", "{remainder.label}", and "{margarita.label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    sidekick: Entity = f["sidekick"]  # type: ignore[assignment]
    teller: Entity = f["teller"]  # type: ignore[assignment]
    remainder: Entity = f["remainder"]  # type: ignore[assignment]
    margarita: Entity = f["margarita"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who went on the quest at {world.setting.place}?",
            answer=f"{hero.label} the {hero.type} and {sidekick.label} the {sidekick.type} went on the quest, with {margarita.label} helping them.",
        ),
        QAItem(
            question=f"What did {teller.label} need for the story to be finished?",
            answer=f"{teller.label} needed the {remainder.label} to come back so the quest could be complete.",
        ),
        QAItem(
            question=f"How did {margarita.label} help?",
            answer=f"{margarita.label} helped carry the {remainder.label} back safely, which made the whole quest work out well.",
        ),
        QAItem(
            question=f"How did {hero.label} feel at the end?",
            answer=f"{hero.label} felt happy and brave after the quest was finished and the {remainder.label} was back where it belonged.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or errand where someone goes out to find, deliver, or fix something important.",
        ),
        QAItem(
            question="What is a remainder?",
            answer="A remainder is what is left after something is used, split, or taken apart; it can also mean the missing part that is still left to find.",
        ),
        QAItem(
            question="What does a teller do?",
            answer="A teller is a person or helper who gives information, keeps track of things, or helps at a counter or desk.",
        ),
        QAItem(
            question="What is a margarita?",
            answer="A margarita can be a name for a character, and in stories a named character can help the others in the quest.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        parts = [f"type={e.type}"]
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{e.id}: " + ", ".join(parts))
    return "\n".join(lines)


ASP_RULES = r"""
entity(hero).
entity(sidekick).
entity(teller).
entity(remainder).
entity(margarita).

quest_complete :- found(remainder), returned(remainder), helped(margarita).
happy_end :- quest_complete.
#show quest_complete/0.
#show happy_end/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("found", "remainder"),
            asp.fact("returned", "remainder"),
            asp.fact("helped", "margarita"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show quest_complete/0. #show happy_end/0."))
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    expected = {"quest_complete/0", "happy_end/0"}
    if atoms == expected:
        print("OK: ASP parity check passed.")
        return 0
    print(f"MISMATCH: {sorted(atoms)} != {sorted(expected)}")
    return 1


def generate(params: StoryParams) -> StorySample:
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(teller="Teller", remainder="remainder", margarita="Margarita", hero_name="Nina", hero_type="rabbit", sidekick_name="Momo", sidekick_type="mouse"),
    StoryParams(teller="River Teller", remainder="little remainder", margarita="Captain Margarita", hero_name="Pip", hero_type="fox", sidekick_name="Dot", sidekick_type="duck"),
    StoryParams(teller="Old Teller", remainder="lost remainder", margarita="Margarita the Goat", hero_name="Lulu", hero_type="bear", sidekick_name="Bibi", sidekick_type="cat"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_complete/0. #show happy_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show quest_complete/0. #show happy_end/0."))
        print("ASP model:", " ".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
