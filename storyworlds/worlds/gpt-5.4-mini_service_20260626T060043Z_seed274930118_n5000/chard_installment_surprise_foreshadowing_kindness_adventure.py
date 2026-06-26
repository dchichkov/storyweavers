#!/usr/bin/env python3
"""
storyworlds/worlds/chard_installment_surprise_foreshadowing_kindness_adventure.py
=================================================================================

A small storyworld for an adventure-flavored tale about a child, a garden, a
surprising discovery, and a kind choice that changes how the trip ends.

Premise:
- A child and a grown-up are on a small errand to deliver an installment of
  garden goods to a market stall.
- The prized crop is chard.
- The route includes foreshadowing clues that something unusual is hidden in the
  leaves.
- The surprise is that the chard shelters something fragile.
- The resolution is a kindness that turns the trip from a simple delivery into
  an adventure with a gentler ending.

This file follows the Storyworld contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- StoryParams, registries, parser, resolution, generation, emit, main
- inline ASP twin with a Python reasonableness gate
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Journey:
    id: str
    verb: str
    gerund: str
    rush: str
    surprise: str
    foreshadow: str
    kindness: str
    route: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False
    fragile: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    effect: str
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        return c


SETTINGS = {
    "garden_path": Setting(place="the garden path", affords={"forage", "deliver"}),
    "market_lane": Setting(place="the market lane", affords={"deliver"}),
    "greenhouse": Setting(place="the greenhouse", outdoor=False, affords={"forage"}),
}

JOURNEYS = {
    "deliver_chard": Journey(
        id="deliver_chard",
        verb="deliver the chard installment",
        gerund="delivering the chard installment",
        rush="hurry along the path",
        surprise="a tiny nest tucked under the broad leaves",
        foreshadow="thin nibble marks and a wobbling stem",
        kindness="leave the nest in place and carry the chard more carefully",
        route=["garden_path", "market_lane"],
        tags={"chard", "installment", "surprise", "foreshadowing", "kindness", "adventure"},
    ),
    "forage_chard": Journey(
        id="forage_chard",
        verb="harvest the chard for supper",
        gerund="harvesting the chard",
        rush="dash between the rows",
        surprise="a baby snail hiding on the back of a leaf",
        foreshadow="silver slime and chewed edges",
        kindness="pick around the little snail and keep it safe",
        route=["greenhouse", "garden_path"],
        tags={"chard", "surprise", "foreshadowing", "kindness", "adventure"},
    ),
}

PRIZES = {
    "bundle": Prize(
        label="bundle of chard",
        phrase="a fresh bundle of chard",
        type="chard",
        fragile=True,
        tags={"chard"},
    ),
    "crate": Prize(
        label="crate of chard",
        phrase="a crate of chard for the market",
        type="chard",
        plural=False,
        fragile=True,
        tags={"chard"},
    ),
}

AIDS = {
    "basket": Aid(
        id="basket",
        label="a woven basket",
        effect="kept the leaves from crushing each other",
        prep="put the chard into a woven basket first",
        tail="walked on with the basket held close",
    ),
    "cloth": Aid(
        id="cloth",
        label="a soft cloth wrap",
        effect="protected the tender stems from bumps",
        prep="wrap the chard in a soft cloth",
        tail="moved on with the wrapped bundle",
    ),
    "gloves": Aid(
        id="gloves",
        label="garden gloves",
        effect="kept careful fingers from scratching the stems",
        prep="pull on garden gloves",
        tail="set off again with careful hands",
    ),
}

NAMES_GIRL = ["Mina", "Lila", "June", "Ava", "Nora", "Ivy"]
NAMES_BOY = ["Owen", "Theo", "Ben", "Finn", "Leo", "Milo"]
TRAITS = ["curious", "brave", "kind", "lively", "patient"]


@dataclass
class StoryParams:
    setting: str
    journey: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def prize_at_risk(j: Journey, p: Prize) -> bool:
    return "chard" in p.tags and "deliver" in j.id or p.fragile


def select_aid(j: Journey, p: Prize) -> Optional[Aid]:
    if not prize_at_risk(j, p):
        return None
    return AIDS["basket"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for jid, j in JOURNEYS.items():
            if sid not in j.route and sid != j.route[0]:
                continue
            for pid, p in PRIZES.items():
                if prize_at_risk(j, p) and select_aid(j, p):
                    combos.append((sid, jid, pid))
    return combos


def explain_rejection(j: Journey, p: Prize) -> str:
    return f"(No story: {j.verb} does not have a reasonable aid for {p.label}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: {PRIZES[prize_id].label} is not a typical {gender}'s job in this tiny world.)"


def _act_move(world: World, hero: Entity, j: Journey) -> None:
    hero.meters["travel"] = hero.meters.get("travel", 0.0) + 1
    hero.memes["adventure"] = hero.memes.get("adventure", 0.0) + 1


def _act_foreshadow(world: World, hero: Entity, j: Journey, prize: Entity) -> None:
    if world.fired and ("foreshadow", hero.id) in world.fired:
        return
    world.fired.add(("foreshadow", hero.id))
    world.say(
        f"Along the path, {hero.id} noticed {j.foreshadow} on the chard."
    )


def _act_surprise(world: World, hero: Entity, j: Journey, prize: Entity) -> None:
    if ("surprise", hero.id) in world.fired:
        return
    world.fired.add(("surprise", hero.id))
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
    world.say(f"Then came the surprise: {j.surprise}.")


def _act_kindness(world: World, hero: Entity, helper: Entity, j: Journey, prize: Entity) -> None:
    if ("kindness", hero.id) in world.fired:
        return
    world.fired.add(("kindness", hero.id))
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    world.say(
        f"{hero.id} chose kindness, because {j.kindness}."
    )


def tell(setting: Setting, journey: Journey, prize_cfg: Prize,
         hero_name: str, hero_type: str, parent_type: str, traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=traits or []))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the grown-up"))
    prize = world.add(Entity(id="chard", type="chard", label=prize_cfg.label, phrase=prize_cfg.phrase))
    aid_def = select_aid(journey, prize_cfg)
    aid = world.add(Entity(id=aid_def.id, type="aid", label=aid_def.label)) if aid_def else None

    world.say(
        f"{hero.id} was a {hero.traits[0] if hero.traits else 'brave'} {hero.type} who loved little adventures."
    )
    world.say(
        f"That morning, {hero.id} and {parent.label} were sent to {setting.place} to make the chard installment."
    )
    world.say(
        f"{hero.id} carried {prize_cfg.phrase} carefully, and the basket felt like a small ship on a big journey."
    )
    world.para()
    world.say(
        f"At {setting.place}, they {journey.verb}."
    )
    _act_move(world, hero, journey)
    _act_foreshadow(world, hero, journey, prize)

    world.say(
        f"{hero.id} peeked under the leaves and saw {journey.surprise}."
    )
    _act_surprise(world, hero, journey, prize)

    world.say(
        f"{parent.label.capitalize()} worried the bundle might get jostled, so they paused together."
    )
    world.para()
    if aid and aid_def:
        world.say(f"Then they used {aid_def.label}, which {aid_def.effect}.")
        world.say(
            f"{hero.id} did as asked: {aid_def.prep}, and {aid_def.tail}."
        )

    _act_kindness(world, hero, parent, journey, prize)

    world.say(
        f"Instead of stripping the nest away, {hero.id} left it safe in the chard and carried the rest to the stall."
    )
    world.say(
        f"By the end, the market keeper had the chard installment, the tiny nest stayed snug, and {hero.id} felt proud of the kinder path."
    )

    world.facts.update(hero=hero, parent=parent, prize=prize, aid=aid, journey=journey, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    journey = f["journey"]
    prize = f["prize"]
    return [
        f'Write a short adventure story for a young child about {hero.id}, a {prize.label}, and a surprising discovery.',
        f"Tell a gentle adventure where {hero.id} goes to {f['setting'].place} to {journey.verb} and chooses kindness.",
        f'Write a story that includes the words "chard" and "installment" and ends with a kind choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    journey = f["journey"]
    prize = f["prize"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do at {f['setting'].place}?",
            answer=f"{hero.id} was trying to {journey.verb}, and the trip felt like a little adventure.",
        ),
        QAItem(
            question=f"What surprise did {hero.id} find in the chard?",
            answer=f"{hero.id} found {journey.surprise}. The leaves were hiding something small and fragile.",
        ),
        QAItem(
            question=f"Why did the grown-up pause the journey?",
            answer=f"The grown-up paused because the chard might have been damaged, and they wanted to choose a careful plan.",
        ),
        QAItem(
            question=f"How did {hero.id} help keep the chard safe?",
            answer=f"{hero.id} used {aid.label if aid else 'careful hands'} so the bundle would not get crushed on the way.",
        ),
        QAItem(
            question=f"What was kind about the ending?",
            answer=f"{hero.id} left the fragile surprise safe inside the chard and still delivered the installment to the stall.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is chard?",
            answer="Chard is a leafy green vegetable with wide leaves and colorful stems.",
        ),
        QAItem(
            question="What does installment mean?",
            answer="An installment is one part of something that is delivered or paid in steps instead of all at once.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue before something important happens.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing to help, protect, or care about someone or something else.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that changes what the characters do next.",
        ),
    ]
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="garden_path", journey="deliver_chard", prize="bundle", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="market_lane", journey="deliver_chard", prize="crate", name="Owen", gender="boy", parent="father", trait="brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: chard, installment, surprise, foreshadowing, kindness, adventure.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--journey", choices=JOURNEYS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.journey and args.prize:
        j, p = JOURNEYS[args.journey], PRIZES[args.prize]
        if not (prize_at_risk(j, p) and select_aid(j, p)):
            raise StoryError(explain_rejection(j, p))
    if args.gender and args.prize and args.gender not in {"girl", "boy"}:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.journey is None or c[1] == args.journey)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, journey, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, journey=journey, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], JOURNEYS[params.journey], PRIZES[params.prize],
                 params.name, params.gender, params.parent, [params.trait, "gentle"])
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


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


ASP_RULES = r"""
prize_at_risk(J,P) :- journey(J), prize(P), fragile(P).
has_aid(J,P) :- prize_at_risk(J,P), aid(A), helpful(A).
valid(S,J,P) :- setting(S), journey(J), prize(P), prize_at_risk(J,P), has_aid(J,P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.outdoor:
            lines.append(asp.fact("outdoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for jid, j in JOURNEYS.items():
        lines.append(asp.fact("journey", jid))
        for r in j.route:
            lines.append(asp.fact("route", jid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.fragile:
            lines.append(asp.fact("fragile", pid))
    for aid in AIDS.values():
        lines.append(asp.fact("aid", aid.id))
        lines.append(asp.fact("helpful", aid.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_story_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - asp_set:
        print("  only python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only asp:", sorted(asp_set - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(str(x) for x in asp_valid_combos()))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
