#!/usr/bin/env python3
"""
Standalone storyworld: a nursery-rhyme style tale about a small controversy,
someone taking something without asking, a gentle arrest, a twist, and a happy
ending.

Premise:
- In a bright little meadow village, a child or tiny animal wants a prized item.
- Another character thinks the taking was unfair, causing a controversy.
- A soft "arrest" happens in the nursery-rhyme sense: a harmless hold-and-walk-
  along by the village watcher or toy constable.
- The twist reveals the taken thing was not stolen at all, but borrowed for a
  surprise.
- The ending returns everyone to joy, with the item shared and the tension
  cleared.

The script models physical meters and emotional memes, emits prose from state,
and includes a Python reasonableness gate plus an inline ASP twin.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def poss(self) -> str:
        return self.pronoun("possessive")

    def obj(self) -> str:
        return self.pronoun("object")


@dataclass
class Setting:
    place: str
    outdoors: bool = True
    mood: str = "bright"


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    value: str
    care: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Cause:
    id: str
    verb: str
    noun: str
    reach: str
    risk: str
    twist: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _meters(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _memes(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _bump_meter(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = _meters(e, key) + amount


def _bump_meme(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = _memes(e, key) + amount


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "meadow": Setting("the meadow", True, "bright"),
    "lantern_lane": Setting("Lantern Lane", True, "golden"),
    "garden": Setting("the garden path", True, "green"),
}

CAUSES = {
    "cake": Cause(
        id="cake",
        verb="take the cake",
        noun="cake",
        reach="the table",
        risk="gone too soon",
        twist="it was being saved for a surprise",
        tags={"sweet", "sharing", "cake", "take"},
    ),
    "bells": Cause(
        id="bells",
        verb="take the bells",
        noun="bells",
        reach="the hook",
        risk="missing from the rung",
        twist="they were being borrowed for a song",
        tags={"music", "bells", "take"},
    ),
    "paint": Cause(
        id="paint",
        verb="take the paint",
        noun="paint",
        reach="the bench",
        risk="spilled before the show",
        twist="it was for a bright sign",
        tags={"art", "paint", "take"},
    ),
}

PRIZES = {
    "basket": Prize("basket", "a little basket", "a little basket of treats", "treats", "sharing"),
    "ribbon": Prize("ribbon", "a blue ribbon", "a blue ribbon", "ribbon", "care"),
    "crown": Prize("crown", "a shiny crown", "a shiny crown", "crown", "care"),
}

GIRL_NAMES = ["Mia", "Nell", "Ruby", "Pip", "Luna"]
BOY_NAMES = ["Tom", "Ben", "Finn", "Ollie", "Sam"]
TRAITS = ["merry", "tiny", "curious", "cheery", "brave"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A cause is at risk when its taking creates a controversy around the prize.
controversy(C, P) :- cause(C), prize(P), sparks(C, P).

% An arrest is reasonable when the watcher can safely hold the actor
% and the controversy is real.
arrestable(C, P) :- controversy(C, P), watcher(W), can_hold(W, C).

% A happy ending requires that the twist is revealed and the prize is returned.
happy_end(C, P) :- controversy(C, P), twist_reveals(C), returned(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.outdoors:
            lines.append(asp.fact("outdoors", sid))
        lines.append(asp.fact("mood", sid, s.mood))
    for cid, c in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
        lines.append(asp.fact("sparks", cid, "basket" if cid == "cake" else "ribbon" if cid == "bells" else "crown"))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    lines.append(asp.fact("watcher", "tally"))
    lines.append(asp.fact("can_hold", "tally", "cake"))
    lines.append(asp.fact("can_hold", "tally", "bells"))
    lines.append(asp.fact("can_hold", "tally", "paint"))
    lines.append(asp.fact("twist_reveals", "cake"))
    lines.append(asp.fact("twist_reveals", "bells"))
    lines.append(asp.fact("twist_reveals", "paint"))
    lines.append(asp.fact("returned", "basket"))
    lines.append(asp.fact("returned", "ribbon"))
    lines.append(asp.fact("returned", "crown"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show happy_end/2."))
    return sorted(set(asp.atoms(model, "happy_end")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for cause in CAUSES:
            for prize in PRIZES:
                if reasonableness_gate(cause, prize):
                    combos.append((place, cause, prize))
    return combos


def reasonableness_gate(cause_id: str, prize_id: str) -> bool:
    return (cause_id, prize_id) in {
        ("cake", "basket"),
        ("bells", "ribbon"),
        ("paint", "crown"),
    }


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    cause: str
    prize: str
    name: str
    gender: str
    watcher: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about a small controversy, a gentle arrest, a twist, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--watcher", choices=["tally"])
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
    if args.cause and args.prize and not reasonableness_gate(args.cause, args.prize):
        raise StoryError("That taking-prize pair does not make a fair nursery-rhyme controversy.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.cause is None or c[1] == args.cause)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    place, cause, prize = rng.choice(sorted(combos))
    pr = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(pr.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    watcher = args.watcher or "tally"
    return StoryParams(place=place, cause=cause, prize=prize, name=name, gender=gender, watcher=watcher, trait=rng.choice(TRAITS))


def _story_subject(e: Entity) -> str:
    return e.id


def _act(world: World, child: Entity, cause: Cause, prize: Entity) -> None:
    _bump_meme(child, "want")
    _bump_meter(prize, "at_risk")
    child.meters["reach"] = 1.0
    world.say(f"{child.id} went to the {world.setting.place} with a merry little hop, and {child.pronoun()} wanted to {cause.verb}.")
    world.say(f"But the village watched the {prize.label} and whispered about a tiny controversy, for {prize.label} might go {cause.risk}.")


def _warn(world: World, watcher: Entity, child: Entity, prize: Entity) -> None:
    _bump_meme(child, "worry")
    _bump_meme(watcher, "care")
    world.say(f"{watcher.id} shook a finger and said, \"Now, now, little one, don't take what is not your own.\"")


def _arrest(world: World, watcher: Entity, child: Entity) -> None:
    _bump_meme(child, "startle")
    _bump_meme(watcher, "resolve")
    child.memes["held"] = 1.0
    world.say(f"So {watcher.id} gave {child.id} a gentle arrest, not with irons and not with dread, but with a soft hand and a steady tread.")


def _twist(world: World, child: Entity, prize: Entity, cause: Cause) -> None:
    _bump_meme(child, "surprise")
    prize.meters["returned"] = 1.0
    world.say(f"Then came the twist, as neat as lace: {cause.twist}.")
    world.say(f"The {prize.label} had never been stolen at all; it was only borrowed for a bright surprise in place.")


def _happy_end(world: World, child: Entity, watcher: Entity, prize: Entity) -> None:
    child.memes["joy"] = 1.0
    watcher.memes["joy"] = 1.0
    child.memes["worry"] = 0.0
    world.say(f"{child.id} laughed, the watcher smiled, and the whole green lane grew mild.")
    world.say(f"In the end the {prize.label} was shared with care, and everyone waved in the nursery air.")


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    watcher = world.add(Entity(id=params.watcher, kind="character", type="child", label="Tally the watchful one"))
    prize = world.add(Entity(id=params.prize, kind="thing", type="thing", label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner="village", caretaker=watcher.id))
    cause = CAUSES[params.cause]

    _act(world, child, cause, prize)
    world.para()
    _warn(world, watcher, child, prize)
    _arrest(world, watcher, child)
    world.para()
    _twist(world, child, prize, cause)
    _happy_end(world, child, watcher, prize)

    world.facts.update(child=child, watcher=watcher, prize=prize, cause=cause, params=params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    c = world.facts["cause"]
    pr = world.facts["prize"]
    return [
        f"Write a nursery-rhyme story about {p.name} who wants to {c.verb} and a little controversy over {pr.label}.",
        f"Tell a gentle story where a watchful helper gives a soft arrest, then reveal the twist and happy ending.",
        f"Compose a simple rhyme about taking, a misunderstanding, and a surprise that makes everything right again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    c = world.facts["cause"]
    pr = world.facts["prize"]
    child: Entity = world.facts["child"]
    watcher: Entity = world.facts["watcher"]
    return [
        QAItem(
            question=f"What did {child.id} want to do?",
            answer=f"{child.id} wanted to {c.verb}. That desire started the little controversy near the {world.setting.place}.",
        ),
        QAItem(
            question=f"Why was there a controversy about the {pr.label}?",
            answer=f"There was a controversy because people thought the {pr.label} had been taken too soon, before they knew it was part of a surprise.",
        ),
        QAItem(
            question=f"Who gave {child.id} a gentle arrest?",
            answer=f"{watcher.id} gave {child.id} a gentle arrest, holding the moment still until the truth could come out.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {c.twist}. The {pr.label} was borrowed for kindness, not taken in trouble.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily: the misunderstanding cleared up, the {pr.label} was shared, and everyone smiled together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a controversy?",
            answer="A controversy is a disagreement or fuss when people feel unsure about what happened.",
        ),
        QAItem(
            question="What does arrest mean in this story?",
            answer="Here, arrest means a gentle stopping and holding-together by the watcher, not a scary punishment.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise turn that changes what you thought was true.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if n:
            bits.append(f"memes={n}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("meadow", "cake", "basket", "Mia", "girl", "tally", "merry"),
    StoryParams("lantern_lane", "bells", "ribbon", "Tom", "boy", "tally", "curious"),
    StoryParams("garden", "paint", "crown", "Nell", "girl", "tally", "cheery"),
]


def asp_verify() -> int:
    clingo_set = set(asp_valid())
    py_set = set((c, p) for _, c, p in valid_combos())
    if clingo_set == py_set:
        print(f"OK: ASP matches Python gate ({len(clingo_set)} cases).")
        return 0
    print("Mismatch between ASP and Python gates.")
    print("ASP only:", sorted(clingo_set - py_set))
    print("Python only:", sorted(py_set - clingo_set))
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show happy_end/2."))
    return sorted(set(asp.atoms(model, "happy_end")))


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
        print(asp_program("#show happy_end/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show happy_end/2."))
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

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.cause is None or c[1] == args.cause)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("No valid nursery-rhyme story fits those choices.")
    place, cause, prize = rng.choice(sorted(combos))
    pr = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(pr.genders))
    if args.gender and args.gender not in pr.genders:
        raise StoryError("That prize is not a typical match for the chosen gender in this world.")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    watcher = args.watcher or "tally"
    return StoryParams(place=place, cause=cause, prize=prize, name=name, gender=gender, watcher=watcher, trait=rng.choice(TRAITS))


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (place, cause, prize)
        for place in SETTINGS
        for cause in CAUSES
        for prize in PRIZES
        if reasonableness_gate(cause, prize)
    ]


if __name__ == "__main__":
    main()
