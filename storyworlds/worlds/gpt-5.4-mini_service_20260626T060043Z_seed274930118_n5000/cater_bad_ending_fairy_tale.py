#!/usr/bin/env python3
"""
storyworlds/worlds/cater_bad_ending_fairy_tale.py
==================================================

A small classical storyworld in a fairy-tale register, built from the seed
idea "cater" and ending in a bad outcome.

Premise:
- A tiny caterpillar helper wants to cater a royal feast.
- The tale begins with warmth, promise, and shiny food.
- The middle turns when the helper ignores a warning and rushes ahead.
- The ending is bad: the feast is spoiled, the hall goes quiet, and no one
  gets the celebration they hoped for.

The world is intentionally small and constraint-checked:
- The featured helper must be able to ruin the feast with the chosen action.
- The warning must be reasonable in-world.
- The story ends without a rescue or compromise, proving the change through
  the final state.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "woman", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "man", "prince"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old castle"
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
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    role: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        for item in [e for e in world.entities.values() if e.worn_by == actor.id]:
            if item.region not in world.zone:
                continue
            sig = ("spill", item.id)
            if sig in world.fired:
                continue
            if actor.meters["mess"] < THRESHOLD:
                continue
            world.fired.add(sig)
            item.meters["mess"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} was spoiled.")
    return out


CAUSAL_RULES = [_r_spill]


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


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("That place cannot host this fairy-tale task.")
    world.zone = set(activity.zone)
    actor.meters["mess"] += 1
    actor.memes["rush"] += 1
    propagate(world, narrate=narrate)


SETTINGS = {
    "castle": Setting(place="the old castle", affords={"cater", "carry"}),
    "kitchen": Setting(place="the castle kitchen", affords={"cater", "carry"}),
    "garden": Setting(place="the rose garden", affords={"carry"}),
}

ACTIVITIES = {
    "cater": Activity(
        id="cater",
        verb="cater the feast",
        gerund="catering the feast",
        rush="dash down the corridor with the supper tray",
        mess="spilled",
        soil="spilled and ruined",
        zone={"torso", "hands"},
        keyword="cater",
        tags={"feast", "food", "spill"},
    ),
    "carry": Activity(
        id="carry",
        verb="carry the cakes",
        gerund="carrying the cakes",
        rush="hurry down the corridor with the cake plate",
        mess="spilled",
        soil="spilled and broken",
        zone={"hands"},
        keyword="carry",
        tags={"cakes", "food", "spill"},
    ),
}

PRIZES = {
    "cakes": Prize(
        label="cakes",
        phrase="a silver tray of honey cakes",
        type="cakes",
        region="hands",
        plural=True,
    ),
    "soup": Prize(
        label="soup",
        phrase="a warm tureen of carrot soup",
        type="soup",
        region="hands",
        plural=False,
    ),
    "bread": Prize(
        label="bread",
        phrase="a basket of sweet bread rolls",
        type="bread",
        region="hands",
        plural=True,
    ),
}

TRAITS = ["tiny", "kind", "eager", "brave", "busy"]

CURATED = [
    StoryParams(place="castle", activity="cater", prize="cakes", name="Pip", role="caterpillar"),
    StoryParams(place="kitchen", activity="carry", prize="bread", name="Miri", role="mouse"),
]


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize_cfg"]
    return [
        f'Write a short fairy tale for a child about a {hero.type} named {hero.id} who wants to {act.verb}.',
        f"Tell a simple castle story where {hero.id} carries {prize.phrase} and learns too late to slow down.",
        f'Write a gentle fairy tale using the word "{act.keyword}" and ending in a sad, quiet way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["guardian"]
    prize = f["prize"]
    act = f["activity"]
    place = world.setting.place
    qa = [
        QAItem(
            question=f"Who is the story about in {place}?",
            answer=f"It is about {hero.id}, a little {hero.type}, and {parent.label}, who watched the feast with concern.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the food?",
            answer=f"{hero.id} wanted to {act.verb} and bring the feast to the hall before the lanterns burned low.",
        ),
        QAItem(
            question=f"What was the important thing that could be ruined?",
            answer=f"The important thing was {prize.phrase}. It was meant for the royal feast, and it had to stay clean.",
        ),
        QAItem(
            question=f"Why did the guardian warn {hero.id}?",
            answer=f"{parent.label} warned {hero.id} because rushing through the castle could make {prize.label} {act.soil}.",
        ),
        QAItem(
            question=f"What happened by the end of the tale?",
            answer=f"{hero.id} rushed ahead anyway, the {prize.label} was {act.soil}, and the feast ended in silence instead of joy.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    act = f["activity"]
    out = [
        QAItem(
            question="What does it mean to cater a feast?",
            answer="To cater a feast means to prepare and bring food for a meal or celebration.",
        ),
        QAItem(
            question="Why can a feast be ruined by spilling food?",
            answer="A feast can be ruined by spilling food because the guests may have nothing neat and tasty to eat.",
        ),
    ]
    if "spill" in act.tags:
        out.append(QAItem(
            question="Why should a helper slow down when carrying a tray?",
            answer="A helper should slow down so the tray stays steady and the food does not tumble onto the floor.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_role))
    guardian = world.add(Entity(id="Guardian", kind="character", type="queen", label="the queen"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=guardian.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        worn_by=hero.id,
    ))

    world.say(f"Once in {setting.place}, there was {hero.id}, a little {hero_role} who loved to help.")
    world.say(f"{hero.id} longed to {activity.verb}, because the royal hall glittered like a dream.")
    world.say(f"The queen had placed {prize.phrase} in {hero.id}'s care for the evening feast.")

    world.para()
    world.say(f"At dusk, {hero.id} slipped into the corridor with the trays.")
    world.say(f"{hero.id} wanted to {activity.verb}, but the long hall was dim and the stones were slick.")
    world.say(f'"Go slowly," the queen said. "If you rush, {prize.label} may be {activity.soil}."')
    hero.memes["fear"] += 1
    hero.memes["defiance"] += 1
    world.say(f"But {hero.id} was too eager to listen, and {hero.id} tried to {activity.rush}.")
    _do_activity(world, hero, activity, narrate=False)

    # Bad ending: the mistake is not repaired.
    world.para()
    if prize.meters["dirty"] >= THRESHOLD:
        world.say(f"The tray tipped. {prize.phrase} became {activity.soil} on the cold floor.")
        world.say(f"The lanterns kept burning, but no warm supper reached the table.")
        world.say(f"The queen looked at the mess, and the hall grew quiet as a shut drawer.")
        world.say(f"At last, {hero.id} sat beside the crumbs while the feast went cold and the guests went home hungry.")
    else:
        world.say(f"Still, the hour passed too fast, and the feast was late and sad.")
        world.say(f"No one sang when the plates were empty.")

    world.facts.update(
        hero=hero,
        guardian=guardian,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
    )
    return world


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} only endangers things carried in the hands, "
        f"but {prize.label} would not be at risk here.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not prize_at_risk(act, pr):
            raise StoryError(explain_rejection(act, pr))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid fairy-tale combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Pip", "Milo", "Lina", "Bram", "Nell"])
    role = args.role or "caterpillar"
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.role)
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


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld with a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--role")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
