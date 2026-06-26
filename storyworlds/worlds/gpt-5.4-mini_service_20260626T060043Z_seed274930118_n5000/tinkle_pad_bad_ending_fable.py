#!/usr/bin/env python3
"""
A small fable-style storyworld about a careful helper, a ringing tinkle, and a
slippery pad that leads to a bad ending.

This world models a tiny classical tale:
- a small animal wants to do a useful task,
- a tempting sound or path invites risk,
- a warning is ignored,
- the choice causes loss,
- the ending proves the loss by changing the world state.

The domain is intentionally narrow so the turn and ending stay clear.
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
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rabbit", "squirrel", "fox"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"mother", "father", "woman", "man"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little lane"
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Choice:
    id: str
    verb: str
    gerund: str
    warn: str
    risk: str
    result: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("risk", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.worn_by != actor.id:
                continue
            sig = ("spill", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["damp"] = item.meters.get("damp", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} grew damp.")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("damp", 0.0) < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("loss", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["trouble"] = carer.memes.get("trouble", 0.0) + 1
        out.append(f"That caused trouble for {carer.label}.")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("loss", _r_loss)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "lane": Setting(place="the little lane", outdoors=True, affords={"tinkle", "pad"}),
    "mill": Setting(place="the old mill yard", outdoors=True, affords={"tinkle", "pad"}),
    "garden": Setting(place="the garden path", outdoors=True, affords={"tinkle", "pad"}),
}

CHOICES = {
    "tinkle": Choice(
        id="tinkle",
        verb="follow the tinkle",
        gerund="following the tinkle",
        warn="The sound may lead you away from home",
        risk="the path may hide a trap",
        result="the sound led to a snare",
        keyword="tinkle",
        tags={"sound", "bell"},
    ),
    "pad": Choice(
        id="pad",
        verb="pad along the soft pad",
        gerund="padding along the soft pad",
        warn="Soft pads can hide a slick spot",
        risk="the pad may slip underfoot",
        result="the soft pad gave way",
        keyword="pad",
        tags={"soft", "slip"},
    ),
}

PRIZES = {
    "cheese": Prize(id="cheese", label="cheese", phrase="a little round cheese", region="mouth"),
    "ink": Prize(id="ink", label="ink jar", phrase="a tiny jar of ink", region="paws"),
}

CHAR_NAMES = ["Milo", "Pip", "Nia", "Tess", "Bram", "Moss"]


@dataclass
class StoryParams:
    place: str
    choice: str
    prize: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def can_story(choice: Choice, prize: Prize) -> bool:
    return True


def tell(setting: Setting, choice: Choice, prize_cfg: Prize, name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="mouse", label=name, phrase=f"little {name}"))
    elder = world.add(Entity(id="elder", kind="character", type="mouse", label="the old mouse", phrase="old mouse"))
    prize = world.add(
        Entity(
            id=prize_cfg.id,
            type="thing",
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            caretaker=elder.id,
            plural=prize_cfg.plural,
        )
    )

    world.say(f"{hero.label} was a small mouse who loved the quiet work of the barn.")
    world.say(f"{hero.label} also loved the {choice.keyword} that sounded near the stones.")
    world.say(f"One day, {elder.label} had kept {prize.phrase} safe for the winter.")

    world.para()
    world.say(f"{hero.label} went out to {setting.place}.")
    world.say(f"The old mouse warned, “{choice.warn}.”")
    world.say(f"But {hero.label} wanted to {choice.verb}.")
    hero.meters["risk"] = hero.meters.get("risk", 0.0) + 1
    world.say(f"So {hero.label} kept going because {choice.risk}.")

    propagate(world, narrate=True)

    world.para()
    # Bad ending: no rescue, no fix, only loss.
    if prize.meters.get("damp", 0.0) >= THRESHOLD:
        world.say(
            f"At last, {choice.result}, and the little prize was no longer fit for the winter shelf."
        )
        world.say(
            f"{elder.label} shook its head and hid the spoiled {prize.label} away."
        )
        world.say(
            f"{hero.label} sat very still beside the empty shelf, and the lane felt colder than before."
        )
    else:
        world.say(
            f"Nothing could save the day, and the small hope of a clean prize was lost anyway."
        )

    world.facts.update(
        hero=hero,
        elder=elder,
        prize=prize,
        choice=choice,
        setting=setting,
        bad_ending=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    choice = f["choice"]
    prize = f["prize"]
    return [
        f'Write a short fable for a young child about {hero.label}, a {choice.keyword}, and a mistake that ends badly.',
        f"Tell a simple story where {hero.label} ignores a warning, follows a {choice.keyword}, and loses {prize.label}.",
        f'Write a fable-style tale that includes the words "{choice.keyword}" and "pad" and ends in sadness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    prize = f["prize"]
    choice = f["choice"]
    return [
        QAItem(
            question=f"What did {hero.label} want to do when the warning was given?",
            answer=f"{hero.label} wanted to {choice.verb}.",
        ),
        QAItem(
            question=f"Who warned {hero.label} about the danger?",
            answer=f"{elder.label} warned {hero.label} that {choice.warn.lower()}.",
        ),
        QAItem(
            question=f"What was lost in the end?",
            answer=f"The story ended badly because {prize.phrase} was spoiled and could not be kept for winter.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that uses animals or simple characters to teach a lesson.",
        ),
        QAItem(
            question="Why is a warning sometimes important?",
            answer="A warning is important because it can help someone avoid a bad choice and a bad result.",
        ),
        QAItem(
            question="What does a little path mean in a story like this?",
            answer="A little path can mean a small route or choice that seems safe but may hide danger.",
        ),
    ]


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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
choice(choice_tinkle).
choice(choice_pad).

risk(choice_tinkle, sound).
risk(choice_pad, slip).

bad_end(C) :- choice(C), risk(C, _).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.outdoors:
            lines.append(asp.fact("outdoors", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, choice in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("keyword", cid, choice.keyword))
        for tag in sorted(choice.tags):
            lines.append(asp.fact("tag", cid, tag))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, prize.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_bad_choices() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show bad_end/1."))
    return sorted(set(asp.atoms(model, "bad_end")))


def asp_verify() -> int:
    py = {(cid,) for cid in CHOICES}
    clingo = set(asp_bad_choices())
    if py == clingo:
        print(f"OK: clingo gate matches Python choices ({len(py)} choices).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in clingo:", sorted(clingo - py))
    print("  only in python:", sorted(py - clingo))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable storyworld with a bad ending.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--choice", choices=CHOICES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
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
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.choice and args.choice not in CHOICES:
        raise StoryError("Unknown choice.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")

    place = args.place or rng.choice(list(SETTINGS))
    choice = args.choice or rng.choice(list(CHOICES))
    prize = args.prize or rng.choice(list(PRIZES))
    name = args.name or rng.choice(CHAR_NAMES)
    return StoryParams(place=place, choice=choice, prize=prize, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CHOICES[params.choice], PRIZES[params.prize], params.name)
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
    StoryParams(place="lane", choice="tinkle", prize="cheese", name="Milo"),
    StoryParams(place="garden", choice="pad", prize="ink", name="Pip"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show bad_end/1."))
        print(sorted(set(asp.atoms(model, "bad_end"))))
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
