#!/usr/bin/env python3
"""
A small pirate-tale storyworld with a cautionary bad ending and a key
misunderstanding involving a heel and a sausage.

The world is intentionally compact:
- a child pirate,
- a hungry deck-side mess,
- a warning that gets misunderstood,
- and an ending that proves the mistake had consequences.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = ""


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    zone: set[str] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


class StoryReasoningError(StoryError):
    pass


SETTINGS = {
    "deck": Setting(place="the ship deck", affords={"sausage"}),
    "galley": Setting(place="the galley", affords={"sausage"}),
}

ACTIVITIES = {
    "sausage": Activity(
        id="sausage",
        verb="eat the sausage",
        gerund="eating sausages",
        rush="lunge for the sausage",
        mess="greasy",
        soil="greasy and slippery",
        zone={"feet", "heel"},
        keyword="sausage",
    )
}

PRIZES = {
    "sausage": Prize(
        label="sausage",
        phrase="a hot sausage wrapped in paper",
        type="sausage",
        region="heel",
        plural=False,
    )
}

GIRL_NAMES = ["Mina", "Nell", "Tessa"]
BOY_NAMES = ["Finn", "Pip", "Jory"]
TRAITS = ["bold", "curious", "cheery", "stubborn"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not endanger a {prize.label} here, "
        f"so there is no honest warning and no cautionary turn.)"
    )


class _NullRule:
    pass


def propagate(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("greasy", 0.0) >= THRESHOLD:
            for item in world.worn_items(actor):
                if item.region in world.zone and ("soak", item.id) not in world.fired:
                    world.fired.add(("soak", item.id))
                    item.meters["greasy"] = item.meters.get("greasy", 0.0) + 1
                    out.append(f"{actor.id}'s {item.label} got greasy.")
    for item in world.entities.values():
        if item.meters.get("greasy", 0.0) >= THRESHOLD and item.caretaker and ("work", item.id) not in world.fired:
            world.fired.add(("work", item.id))
            carer = world.get(item.caretaker)
            carer.meters["workload"] = carer.meters.get("workload", 0.0) + 1
            out.append(f"That meant more work for {carer.label}.")
    return out


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    act = ACTIVITIES[params.activity]
    prize = PRIZES[params.prize]
    world = World(setting=setting)

    hero = world.add(Entity(
        id=params.name, kind="character", type=params.gender, label=params.name,
        meters={}, memes={}
    ))
    parent = world.add(Entity(
        id="Captain", kind="character", type="man" if params.parent == "father" else "woman",
        label="the captain", meters={}, memes={}
    ))
    item = world.add(Entity(
        id="sausage", type="sausage", label="sausage", phrase=prize.phrase,
        owner=hero.id, caretaker=parent.id, worn_by=hero.id, region=prize.region
    ))

    # Act 1: setup.
    world.say(
        f"{hero.id} was a {params.trait} little pirate who loved {act.gerund} on {setting.place}."
    )
    world.say(
        f"One gray morning, {parent.label} brought out {prize.phrase}, and {hero.id} held {item.it()} tight."
    )

    # Act 2: warning and misunderstanding.
    world.para()
    world.say(
        f"{hero.id} wanted to {act.verb}, but {parent.label} looked at {item.label} on the heel and frowned."
    )
    world.say(
        f'"If you dash about now, that sausage grease will hit your heel and make the deck slick," {parent.label} said.'
    )
    hero.memes["confusion"] = hero.memes.get("confusion", 0.0) + 1
    world.say(
        f"{hero.id} misunderstood the warning and thought {parent.label} meant the sausage should be kept by the heel."
    )
    world.say(
        f"So {hero.id} tucked the sausage near the boot heel and tried to {act.rush} anyway."
    )

    # Act 3: bad ending.
    world.para()
    hero.meters["greasy"] = hero.meters.get("greasy", 0.0) + 1
    world.zone = set(act.zone)
    propagate(world)
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(
        f"The sausage slipped loose, the heel turned slick, and {hero.id} skidded hard across the deck."
    )
    world.say(
        f"The sausage flew into the sea, and {parent.label} had to scrub the greasy boards while {hero.id} sat with a sore heel and a sinking face."
    )
    world.say(
        f"After that, {hero.id} learned that on a pirate ship, a warning should be listened to, not guessed at."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=item,
        activity=act,
        setting=setting,
        resolved=False,
        misunderstood=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    act = f["activity"]
    return [
        f'Write a short pirate story for a small child about a {hero.type} named {hero.id}, a sausage, and a heel.',
        f"Tell a cautionary tale where {hero.id} misunderstands {parent.label}'s warning and makes the deck slippery.",
        f'Write a simple pirate story that includes the words "{act.keyword}", "heel", and "sausage".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    act = f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do on the ship?",
            answer=f"{hero.id} wanted to {act.verb} on the ship deck.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the sausage?",
            answer=f"{parent.label} worried that sausage grease would hit the heel and make the deck slick.",
        ),
        QAItem(
            question=f"What did {hero.id} misunderstand?",
            answer=(
                f"{hero.id} misunderstood the warning and thought the sausage should be kept by the heel, "
                f"which led to the slip."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                "The story ended badly: the sausage was lost overboard, the deck got greasy, and the child learned a careful lesson."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a heel?",
            answer="A heel is the back part of a shoe or boot that touches the ground.",
        ),
        QAItem(
            question="What is a sausage?",
            answer="A sausage is a food made from seasoned meat, often cooked in a long casing.",
        ),
        QAItem(
            question="Why can grease be dangerous on a floor or deck?",
            answer="Grease can make a surface slippery, so people can slide or fall.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and python valid_combos().")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary pirate tale about a heel and a sausage.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr)):
            raise StoryError(explain_rejection(act, pr))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for place, act, prize in triples:
            print(f"  {place:8} {act:8} {prize:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in [
            StoryParams(place="deck", activity="sausage", prize="sausage", name="Finn", gender="boy", parent="father", trait="bold"),
            StoryParams(place="galley", activity="sausage", prize="sausage", name="Mina", gender="girl", parent="mother", trait="curious"),
        ]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
