#!/usr/bin/env python3
"""
storyworlds/worlds/lead_sharing_bravery_pirate_tale.py
======================================================

A standalone story world for a small Pirate Tale domain about sharing and
bravery.

Premise:
- A young pirate finds a special lead token or lead-lined chest key.
- The crew needs to cross a risky place and share a single useful item.
- Brave sharing helps them finish the trip together.

The world is intentionally small and constraint-checked:
- The risk must be real.
- The fix must be a plausible sharing/bravery turn.
- Invalid setups raise StoryError with a clear reason.

The story engine keeps both physical meters and emotional memes.
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
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    sea: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    danger: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    risk: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.challenge: Optional[Challenge] = None
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


SETTINGS = {
    "deck": Setting(place="the deck", sea=True, affords={"storm", "reef"}),
    "cove": Setting(place="the cove", sea=True, affords={"reef"}),
    "harbor": Setting(place="the harbor", sea=True, affords={"storm", "reef"}),
    "island": Setting(place="the island shore", sea=True, affords={"reef"}),
}

CHALLENGES = {
    "storm": Challenge(
        id="storm",
        verb="sail through the storm",
        gerund="sailing through the storm",
        rush="race into the waves",
        mess="soaked",
        soil="soaked through",
        danger="rough water",
        keyword="storm",
        tags={"water", "wind"},
    ),
    "reef": Challenge(
        id="reef",
        verb="cross the reef",
        gerund="squeezing past the reef",
        rush="dash toward the rocks",
        mess="scratched",
        soil="scratched and scraped",
        danger="sharp rocks",
        keyword="reef",
        tags={"rocks", "sea"},
    ),
}

PRIZES = {
    "map": Prize(
        label="map",
        phrase="a small paper map",
        type="map",
        risk="torn",
        genders={"girl", "boy"},
    ),
    "flag": Prize(
        label="flag",
        phrase="a bright ship flag",
        type="flag",
        risk="frayed",
    ),
    "satchel": Prize(
        label="satchel",
        phrase="a sturdy little satchel",
        type="satchel",
        risk="splashed",
    ),
    "lamp": Prize(
        label="lamp",
        phrase="a brass lamp",
        type="lamp",
        risk="dented",
    ),
}

GEAR = [
    Gear(
        id="oilcloth",
        label="an oilcloth wrap",
        prep="wrap the map in oilcloth first",
        tail="wrapped the map in oilcloth and kept it dry",
        guards={"storm"},
        covers=set(),
    ),
    Gear(
        id="rope",
        label="a rope handline",
        prep="share the rope and clip it to the rail",
        tail="held the rope together and moved step by step",
        guards={"storm", "reef"},
        covers=set(),
    ),
    Gear(
        id="crate",
        label="a small crate",
        prep="put the lamp in a small crate",
        tail="kept the lamp tucked in the crate",
        guards={"reef"},
        covers=set(),
    ),
    Gear(
        id="cloak",
        label="a rain cloak",
        prep="share the rain cloak between them",
        tail="shared the rain cloak and stayed dry enough",
        guards={"storm"},
        covers=set(),
    ),
]

NAMES = ["Mira", "Finn", "Pip", "Nell", "Jory", "Bram", "Ada", "Tess", "Kian", "Luna"]
TITLES = ["young pirate", "brave deckhand", "little captain", "quick sailor"]


def prize_at_risk(challenge: Challenge, prize: Prize) -> bool:
    return (challenge.id, prize.label) in {
        ("storm", "map"),
        ("storm", "flag"),
        ("storm", "satchel"),
        ("reef", "map"),
        ("reef", "satchel"),
        ("reef", "lamp"),
    }


def select_gear(challenge: Challenge, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if challenge.id in gear.guards:
            if prize.label == "flag" and gear.id not in {"rope", "cloak"}:
                continue
            if prize.label == "lamp" and gear.id not in {"crate", "rope"}:
                continue
            if prize.label == "map" and gear.id not in {"oilcloth", "rope", "cloak"}:
                continue
            if prize.label == "satchel" and gear.id not in {"rope", "cloak"}:
                continue
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for ch_id in setting.affords:
            ch = CHALLENGES[ch_id]
            for pr_id, prize in PRIZES.items():
                if prize_at_risk(ch, prize) and select_gear(ch, prize):
                    combos.append((place, ch_id, pr_id))
    return combos


def explain_rejection(challenge: Challenge, prize: Prize) -> str:
    if not prize_at_risk(challenge, prize):
        return f"(No story: {challenge.gerund} does not honestly risk {prize.label}.)"
    return f"(No story: no shared gear can plausibly protect {prize.label} from {challenge.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: {PRIZES[prize_id].label} is not usually a {gender}'s treasure here; try {ok}.)"


def activity_detail(challenge: Challenge) -> str:
    return {
        "storm": "The sea kept thumping the hull, and the wind tugged at every sleeve.",
        "reef": "The water flashed pale around the rocks, and every splash looked sharp.",
    }[challenge.id]


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {hero.label} who loved to watch the sea and keep a steady heart.")


def love_treasure(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    prize.carried_by = hero.id
    world.say(f"{hero.id} treasured {prize.phrase} and kept {prize.it()} close like a lucky charm.")


def arrive(world: World, hero: Entity, mate: Entity, challenge: Challenge) -> None:
    world.say(f"One day, {hero.id} and {mate.id} went to {world.setting.place}.")
    world.say(activity_detail(challenge))


def want(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(f"{hero.id} wanted to {challenge.verb}, even though the water looked wild.")


def warn(world: World, mate: Entity, hero: Entity, challenge: Challenge, prize: Entity) -> bool:
    if not prize_at_risk(challenge, prize):
        return False
    world.facts["predicted_soil"] = challenge.soil
    world.say(f'"If you do that, your {prize.label} will get {challenge.soil}," {mate.id} said.')
    return True


def brave_share(world: World, hero: Entity, mate: Entity, challenge: Challenge) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    mate.memes["trust"] = mate.memes.get("trust", 0) + 1
    world.say(f"{hero.id} took a brave breath instead of rushing ahead alone.")


def choose_gear(world: World, hero: Entity, mate: Entity, challenge: Challenge, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(challenge, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, plural=gear_def.plural))
    gear.carried_by = hero.id
    world.say(f"{mate.id} pointed to {gear_def.label} and said, \"We can share this.\"")
    world.say(f"{hero.id} nodded and {gear_def.prep}.")
    return gear_def


def accept(world: World, hero: Entity, mate: Entity, challenge: Challenge, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    hero.memes["sharing"] = hero.memes.get("sharing", 0) + 1
    world.say(f"Then they went on together, {gear_def.tail}.")
    world.say(
        f"In the end, {hero.id} was still {challenge.gerund}, and the {prize.label} stayed safe."
    )


def tell(setting: Setting, challenge: Challenge, prize_cfg: Prize, hero_name: str, mate_name: str) -> World:
    world = World(setting)
    world.challenge = challenge
    hero = world.add(Entity(id=hero_name, kind="character", type="pirate", label="brave pirate"))
    mate = world.add(Entity(id=mate_name, kind="character", type="pirate", label="crew mate"))
    prize = world.add(Entity(id="prize", label=prize_cfg.label, phrase=prize_cfg.phrase, type=prize_cfg.type))
    introduce(world, hero)
    love_treasure(world, hero, prize)
    world.para()
    arrive(world, hero, mate, challenge)
    want(world, hero, challenge)
    warn(world, mate, hero, challenge, prize)
    brave_share(world, hero, mate, challenge)
    gear_def = choose_gear(world, hero, mate, challenge, prize)
    world.para()
    if gear_def is not None:
        accept(world, hero, mate, challenge, prize, gear_def)
    world.facts.update(hero=hero, mate=mate, prize=prize, challenge=challenge, gear=gear_def, setting=setting)
    return world


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    name: str
    mate: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mate, prize, ch = f["hero"], f["mate"], f["prize"], f["challenge"]
    return [
        f'Write a short pirate tale for a child about "{ch.keyword}" and a brave choice to share.',
        f"Tell a story where {hero.id} and {mate.id} must {ch.verb} without ruining {prize.phrase}.",
        f"Write a pirate story that includes sharing, bravery, and the word \"lead\" in a child-friendly way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, prize, ch = f["hero"], f["mate"], f["prize"], f["challenge"]
    return [
        QAItem(
            question=f"Who wanted to {ch.verb}?",
            answer=f"{hero.id} wanted to {ch.verb}, even though the sea looked risky.",
        ),
        QAItem(
            question=f"Why did {mate.id} warn {hero.id} about the {prize.label}?",
            answer=f"{mate.id} warned {hero.id} because the {prize.label} would get {ch.soil} if they rushed ahead.",
        ),
        QAItem(
            question="What did they do instead of going alone?",
            answer=f"They shared the helpful gear and stayed together, which showed bravery and sharing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["challenge"].tags)
    tags.add("lead")
    out: list[QAItem] = []
    if "water" in tags:
        out.append(QAItem(question="What is a storm at sea?", answer="A storm at sea is rough weather with strong wind, waves, and rain that can make sailing hard."))
    if "rocks" in tags:
        out.append(QAItem(question="What is a reef?", answer="A reef is a line of rocks or coral in the water, and ships need to steer carefully around it."))
    out.append(QAItem(question="What does it mean to share?", answer="To share means to let other people use part of what you have, or to use something together."))
    out.append(QAItem(question="What is bravery?", answer="Bravery means doing something hard or scary while staying steady and trying your best."))
    out.append(QAItem(question="What is lead?", answer="Lead is a heavy metal. It can be used to make things weighty or sturdy, though children should not play with it."))
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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.plural:
            bits.append("plural=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_name() -> str:
    return random.choice(NAMES)


CURATED = [
    StoryParams(place="deck", challenge="storm", prize="map", name="Mira", mate="Finn"),
    StoryParams(place="harbor", challenge="reef", prize="lamp", name="Pip", mate="Nell"),
    StoryParams(place="cove", challenge="reef", prize="satchel", name="Jory", mate="Ada"),
]


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    name: str
    mate: str
    seed: Optional[int] = None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.challenge and args.prize:
        ch, pr = CHALLENGES[args.challenge], PRIZES[args.prize]
        if not (prize_at_risk(ch, pr) and select_gear(ch, pr)):
            raise StoryError(explain_rejection(ch, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    mate = getattr(args, "mate", None) or rng.choice([n for n in NAMES if n != name])
    return StoryParams(place=place, challenge=challenge, prize=prize, name=name, mate=mate)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CHALLENGES[params.challenge], PRIZES[params.prize], params.name, params.mate)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale world: sharing and bravery around a risky voyage.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--mate")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


ASP_RULES = r"""
prize_at_risk(C,P) :- challenge(C), prize(P), risk_pair(C,P).
has_fix(C,P) :- prize_at_risk(C,P), gear(G), guards(G,C), fits(G,P).
valid(Place,C,P) :- setting(Place), affords(Place,C), prize_at_risk(C,P), has_fix(C,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
        for ch in sorted(SETTINGS[pid].affords):
            lines.append(asp.fact("affords", pid, ch))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for pr_id, pr in PRIZES.items():
            if prize_at_risk(ch, pr):
                lines.append(asp.fact("risk_pair", cid, pr_id))
    for gid, g in [(x.id, x) for x in GEAR]:
        lines.append(asp.fact("gear", gid))
        for c in sorted(g.guards):
            lines.append(asp.fact("guards", gid, c))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.challenge} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
