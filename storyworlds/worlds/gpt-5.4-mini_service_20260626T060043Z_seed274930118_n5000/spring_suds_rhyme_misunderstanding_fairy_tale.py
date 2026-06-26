#!/usr/bin/env python3
"""
A small fairy-tale storyworld about spring, suds, a rhyme, and a misunderstanding.

A seed tale:
- In a village by the woods, a young mouse loved to sing little rhymes.
- On a spring morning, the mouse found a bucket of suds outside a cottage.
- The mouse heard a rhyme and misunderstood it, thinking the suds were meant for a spell.
- A kindly washerwoman explained the joke, and together they used the suds to wash a muddy ribbon and brighten the day.

This script builds a compact simulation with typed entities, physical meters, and
emotional memes. The story is driven by state changes, not by fixed paragraph
swapping. It also includes a reasonableness gate and an inline ASP twin.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "boy", "prince"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "princess", "maid"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    stir: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    offer: str
    tail: str
    guards: set[str]
    covers: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.lines = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _mget(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _gget(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _addm(e: Entity, key: str, val: float) -> None:
    e.meters[key] = _mget(e, key) + val


def _addg(e: Entity, key: str, val: float) -> None:
    e.memes[key] = _gget(e, key) + val


def _soak(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if _mget(actor, "suds") < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.worn_by != actor.id:
                continue
            if item.region not in world.zone:
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            _addm(item, "suds", 1)
            _addm(item, "dirty", 1)
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} turned sudsy and spotted.")
    return out


def _helper(world: World) -> list[str]:
    out = []
    for item in world.entities.values():
        if _mget(item, "dirty") < THRESHOLD or not item.caretaker:
            continue
        sig = ("helper", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        _addg(carer, "worry", -0.5)
        out.append(f"That meant more work for {carer.label}.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_soak, _helper):
            got = fn(world)
            if got:
                changed = True
                produced.extend(got)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell_rhyme(world: World, singer: Entity) -> None:
    _addg(singer, "delight", 1)
    world.say(
        f"In the spring by the green old well, {singer.id} sang a rhyme with a tinkling bell."
    )
    world.say(
        f"The little verse went round the lane, and every word came back like rain."
    )


def misunderstanding(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    _addg(hero, "confusion", 1)
    _addg(hero, "fear", 1)
    _addg(helper, "worry", 1)
    world.say(
        f"{hero.id} peered at the bucket of suds and heard the rhyme the wrong way."
    )
    world.say(
        f"{hero.pronoun().capitalize()} thought the suds were a spell that would swallow {hero.pronoun('possessive')} {prize.label}."
    )


def explain(world: World, helper: Entity, hero: Entity, prize: Entity) -> None:
    _addg(hero, "relief", 1)
    _addg(hero, "joy", 1)
    hero.memes["confusion"] = 0.0
    world.say(
        f"But {helper.label} laughed softly and said, 'No, dear one, the rhyme only meant the suds would help the wash go right.'"
    )
    world.say(
        f"{hero.id}'s ears grew warm, and {hero.pronoun()} saw the joke at last."
    )


def wash_and_finish(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    _addm(prize, "clean", 1)
    _addm(hero, "suds", 0)
    world.say(
        f"Together they lifted the bucket, and the spring suds foamed bright as snow."
    )
    world.say(
        f"They washed the muddy {prize.label}, and soon {prize.phrase} gleamed again."
    )
    world.say(
        f"By evening, {hero.id} was smiling, {helper.label} was humming, and the little lane felt blessed."
    )


SETTINGS = {
    "cottage_lane": Setting(place="the cottage lane", afford={"wash"}),
    "wellyard": Setting(place="the wellyard", afford={"wash"}),
    "meadow": Setting(place="the meadow", afford={"wash"}),
}

ACTIVITIES = {
    "wash": Activity(
        id="wash",
        verb="wash the ribbon",
        gerund="washing the ribbon",
        stir="stir the suds",
        mess="suds",
        soil="sudsy and muddy",
        zone={"hands", "torso"},
        keyword="suds",
        tags={"spring", "suds", "rhyme", "misunderstanding"},
    )
}

PRIZES = {
    "ribbon": Prize(
        label="ribbon",
        phrase="a bright blue ribbon",
        type="ribbon",
        region="hands",
    ),
}

HELPERS = {
    "washerwoman": Helper(
        id="washerwoman",
        label="the washerwoman",
        offer="let's use the suds for washing instead of worrying",
        tail="the suds did their gentle work",
        guards={"suds"},
        covers={"hands", "torso"},
    )
}

NAMES = ["Milo", "Lina", "Pip", "Elin", "Toby", "Mira"]
TRAITS = ["curious", "gentle", "brave", "bright", "dreamy"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p, setting in SETTINGS.items():
        for a in setting.afford:
            for pr in PRIZES:
                out.append((p, a, pr))
    return out


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    act = ACTIVITIES[params.activity]
    prize_cfg = PRIZES[params.prize]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="mouse",
        label="little mouse",
        meters={"suds": 0.0},
        memes={"confusion": 0.0, "fear": 0.0, "joy": 0.0, "relief": 0.0, "worry": 0.0},
    ))
    helper = world.add(Entity(
        id=HELPERS["washerwoman"].id,
        kind="character",
        type="woman",
        label=HELPERS["washerwoman"].label,
        meters={},
        memes={"worry": 0.0, "kindness": 1.0},
    ))
    prize = world.add(Entity(
        id="ribbon",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        region=prize_cfg.region,
        caretaker=helper.id,
    ))
    hero.owner = hero.id
    prize.owner = hero.id

    world.say(f"{hero.id} was a {params.trait} little mouse who loved rhymes and morning light.")
    world.say(f"Every spring, {hero.id} listened for songs in the grass and wished for a small adventure.")
    world.say(f"One day, {hero.id} found {prize.phrase} beside a bucket of suds near {setting.place}.")
    world.say(f"{hero.id} loved {prize.it()} and wore {prize.it()} as if the ribbon were a tiny flag of luck.")

    world.para()
    world.say(f"At {setting.place}, {hero.id} wanted to {act.verb}.")
    tell_rhyme(world, hero)
    world.zone = set(act.zone)
    _addm(hero, "suds", 1)
    misunderstanding(world, hero, helper, prize)
    propagate(world)

    world.para()
    explain(world, helper, hero, prize)
    wash_and_finish(world, hero, helper, prize)

    world.facts.update(hero=hero, helper=helper, prize=prize, activity=act, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a fairy-tale story about {hero.id}, spring, and suds that includes a rhyme and a misunderstanding.',
        f'Tell a gentle story in which a little mouse hears a rhyme wrong, then learns what the suds are for.',
        f'Write a short child-friendly fairy tale where springtime suds turn from a scare into a happy wash.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, act = f["hero"], f["helper"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about a little mouse named {hero.id}, who loved rhymes and spring mornings.",
        ),
        QAItem(
            question=f"What did {hero.id} first misunderstand about the suds?",
            answer=f"{hero.id} thought the suds were a spell that would swallow {hero.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question=f"How did {the:=helper.label} help in the end?",
            answer=f"{helper.label} explained the rhyme, and then they used the suds to wash {prize.phrase}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The fear faded, the ribbon got clean, and {hero.id} ended the day smiling in the spring light.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are suds?",
            answer="Suds are bubbly foam made by soap and water when something is being washed.",
        ),
        QAItem(
            question="What is spring?",
            answer="Spring is the season when flowers open, birds sing, and the days grow warm and bright again.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little song or saying where words sound alike at the ends.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone hears or thinks something the wrong way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for m in sorted(h.guards):
            lines.append(asp.fact("guards", hid, m))
        for c in sorted(h.covers):
            lines.append(asp.fact("covers", hid, c))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
needs_help(A,P) :- prize_at_risk(A,P), mess_of(A,M), helper(H), guards(H,M), covers(H,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize(P), prize_at_risk(A,P), needs_help(A,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about spring, suds, rhyme, and misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    place, activity, prize = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, trait=trait)


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


CURATED = [
    StoryParams(place="cottage_lane", activity="wash", prize="ribbon", name="Milo", trait="curious"),
    StoryParams(place="wellyard", activity="wash", prize="ribbon", name="Lina", trait="gentle"),
    StoryParams(place="meadow", activity="wash", prize="ribbon", name="Pip", trait="bright"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
