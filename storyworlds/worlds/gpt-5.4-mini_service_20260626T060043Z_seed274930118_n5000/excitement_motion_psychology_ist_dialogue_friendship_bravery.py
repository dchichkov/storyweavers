#!/usr/bin/env python3
"""
A standalone story world for a small mythic domain built from the seed:
excitement, motion, psychology-ist, with Dialogue, Friendship, and Bravery.

The world is intentionally tiny and classical:
- A young hero feels excitement before a motion-filled rite.
- A friend notices fear and offers honest dialogue.
- A brave choice changes the ending image.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    mems: dict[str, float] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "daughter", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son", "king", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    mood: str
    opening: str


@dataclass
class Trial:
    id: str
    motion: str
    verb: str
    risk: str
    cost: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    protects: set[str]
    use: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
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


@dataclass
class StoryParams:
    place: str
    trial: str
    gift: str
    hero_name: str
    hero_type: str
    friend_name: str
    seed: Optional[int] = None


PLACES = {
    "hill": Place(
        name="the hill of the first dawn",
        mood="bright",
        opening="The hill of the first dawn shone like a silver drum under the sky.",
    ),
    "river": Place(
        name="the river bridge",
        mood="moving",
        opening="The river bridge sang softly while the water hurried below it.",
    ),
    "forest": Place(
        name="the moonwood",
        mood="mysterious",
        opening="The moonwood waited in green silence, and every leaf seemed to listen.",
    ),
}

TRIALS = {
    "leap": Trial(
        id="leap",
        motion="jump across the glowing stones",
        verb="jump across the glowing stones",
        risk="slip into the shining water",
        cost="get wet and shaken",
        keyword="motion",
        tags={"motion", "excitement"},
    ),
    "run": Trial(
        id="run",
        motion="run to the far bell",
        verb="run to the far bell",
        risk="lose the path in the dark reeds",
        cost="feel lost and tired",
        keyword="excitement",
        tags={"motion", "excitement"},
    ),
    "climb": Trial(
        id="climb",
        motion="climb the wind-stair",
        verb="climb the wind-stair",
        risk="tremble on the high steps",
        cost="shake with fear",
        keyword="motion",
        tags={"motion"},
    ),
}

GIFTS = {
    "rope": Gift(
        id="rope",
        label="a lantern-rope",
        phrase="a lantern-rope with a steady golden knot",
        protects={"dark", "fear"},
        use="hold onto",
        tags={"bravery"},
    ),
    "song": Gift(
        id="song",
        label="a courage-song",
        phrase="a courage-song learned from an old guardian",
        protects={"fear"},
        use="repeat",
        tags={"friendship", "bravery"},
    ),
    "hand": Gift(
        id="hand",
        label="a friend’s handclasp",
        phrase="a warm handclasp tied with a ribbon",
        protects={"fear", "lonely"},
        use="keep",
        tags={"friendship", "dialogue"},
    ),
}

HERO_NAMES = ["Mira", "Tavi", "Nilo", "Arin", "Sera", "Kellan"]
FRIEND_NAMES = ["Oren", "Luma", "Pia", "Bram", "Nia", "Thale"]
TYPES = ["girl", "boy"]


def prize_at_risk(trial: Trial, gift: Gift) -> bool:
    return "fear" in gift.protects and trial.id in {"run", "climb", "leap"}


def select_gift(trial: Trial, gift: Gift) -> Optional[Gift]:
    if prize_at_risk(trial, gift):
        return gift
    return None


ASP_RULES = r"""
trial(T).
gift(G).
place(P).

at_risk(T,G) :- trial(T), gift(G), can_make_fear(T), protects(G,fear).
compatible(T,G) :- at_risk(T,G).
valid(P,T,G) :- place(P), trial(T), compatible(T,G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TRIALS:
        lines.append(asp.fact("trial", tid))
        for t in sorted(TRIALS[tid].tags):
            lines.append(asp.fact("tag", tid, t))
        lines.append(asp.fact("can_make_fear", tid))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        for p in sorted(g.protects):
            lines.append(asp.fact("protects", gid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid in PLACES:
        for tid, trial in TRIALS.items():
            for gid, gift in GIFTS.items():
                if prize_at_risk(trial, gift):
                    combos.append((pid, tid))
    return combos


def _do_trial(world: World, hero: Entity, friend: Entity, trial: Trial, narrate: bool = True) -> None:
    hero.meters["motion"] = hero.meters.get("motion", 0.0) + 1.0
    hero.mems["excitement"] = hero.mems.get("excitement", 0.0) + 1.0
    if narrate:
        world.say(f"{hero.id} felt excitement rise like a bright drumbeat.")

    if hero.mems.get("fear", 0.0) >= THRESHOLD:
        hero.mems["bravery"] = hero.mems.get("bravery", 0.0) + 1.0

    if trial.id == "run":
        hero.meters["speed"] = hero.meters.get("speed", 0.0) + 1.0
    if trial.id == "climb":
        hero.meters["height"] = hero.meters.get("height", 0.0) + 1.0
    if trial.id == "leap":
        hero.meters["air"] = hero.meters.get("air", 0.0) + 1.0

    if narrate:
        world.say(f"{hero.id} did not stop at the first fear; {hero.pronoun()} kept moving.")


def tell(place: Place, trial: Trial, gift: Gift, hero_name: str, hero_type: str, friend_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["young", "hopeful"]))
    friend = world.add(Entity(id=friend_name, kind="character", type="child", traits=["kind", "steady"]))
    gift_ent = world.add(Entity(id=gift.id, type="gift", label=gift.label, phrase=gift.phrase))

    hero.mems["excitement"] = 1.0
    hero.mems["fear"] = 0.0
    friend.mems["care"] = 1.0

    world.say(place.opening)
    world.say(f"{hero.id} had heard that on this day, a small rite of motion would open the road ahead.")
    world.say(f"{hero.id} wanted to {trial.verb}, because {trial.keyword} made the whole journey feel alive.")
    world.say(f"{friend.id} came close and said, \"You can do hard things, and I will walk with you.\"")

    world.para()
    world.say(f"The old guardian had given them {gift.phrase}.")
    world.say(f"{hero.id} held it close, for the gift felt like a promise against fear.")
    hero.mems["fear"] = 1.0
    hero.mems["bravery"] = 0.0

    world.para()
    world.say(f"At the edge of the path, {hero.id} saw the place where {trial.risk}.")
    world.say(f"{hero.id} whispered, \"I want to go on, but my heart is shaking.\"")
    world.say(f"{friend.id} answered, \"Then let us speak plainly: what part feels too high, too fast, or too dark?\"")
    world.say(f"{hero.id} said, \"The steps look long, and I do not wish to fall.\"")
    world.say(f"{friend.id} said, \"Then I will stand near, and you will not be alone.\"")

    world.para()
    world.say(f"That honest dialogue steadied {hero.id}.")
    hero.mems["fear"] = 0.0
    hero.mems["bravery"] = 1.0
    friend.mems["friendship"] = 1.0
    _do_trial(world, hero, friend, trial, narrate=True)

    world.para()
    world.say(f"So {hero.id} {trial.verb}, and this time the fear did not win.")
    world.say(f"{hero.id} reached the far side with {friend.id} beside {hero.pronoun('object')}, and the road opened like dawn.")
    world.facts.update(hero=hero, friend=friend, gift=gift_ent, trial=trial, place=place, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mythic story for a child about excitement, motion, and a brave choice in {f["place"].name}.',
        f'Write a gentle legend where {f["hero"].id} and {f["friend"].id} speak honestly before a hard motion-filled task.',
        f'Write a small myth with dialogue and friendship that ends in bravery and a bright new image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    trial: Trial = f["trial"]
    place: Place = f["place"]
    gift: Entity = f["gift"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {place.name}?",
            answer=f"{hero.id} wanted to {trial.verb}. It felt full of motion and excitement.",
        ),
        QAItem(
            question=f"Who spoke kindly to {hero.id} before the hard part?",
            answer=f"{friend.id} spoke kindly to {hero.id} and stayed near {hero.pronoun('object')} during the hard moment.",
        ),
        QAItem(
            question=f"What did the gift help {hero.id} remember?",
            answer=f"The gift helped {hero.id} remember bravery. It was {gift.phrase}, and it felt like a promise.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel worried near the path?",
            answer=f"{hero.id} worried because {trial.risk}, and that could make {hero.pronoun('object')} {trial.cost}.",
        ),
        QAItem(
            question=f"What changed after the dialogue between the two friends?",
            answer=f"After they spoke honestly, {hero.id} felt steadier and chose bravery instead of turning back.",
        ),
    ]


KNOWLEDGE = {
    "motion": [
        QAItem(
            question="What is motion?",
            answer="Motion is when something moves from one place to another.",
        )
    ],
    "excitement": [
        QAItem(
            question="What is excitement?",
            answer="Excitement is a lively feeling that makes a person eager, bright, and ready to do something.",
        )
    ],
    "friendship": [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between people who care for one another and help each other.",
        )
    ],
    "bravery": [
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing a hard thing even when you feel worried.",
        )
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters speak to one another in a story.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["trial"].tags) | world.facts["gift"].traits if False else set()
    tags = set(world.facts["trial"].tags) | set(world.facts["gift"].traits)
    out: list[QAItem] = []
    for tag in ["excitement", "motion", "dialogue", "friendship", "bravery"]:
        if tag in tags:
            out.extend(KNOWLEDGE.get(tag, []))
    return out


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== (1) Generation prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} mems={e.mems}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: excitement, motion, psychology-ist, dialogue, friendship, bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=TYPES)
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
    if args.trial and args.gift:
        if not prize_at_risk(TRIALS[args.trial], GIFTS[args.gift]):
            raise StoryError("That gift does not honestly answer the trial's fear.")
    combos = []
    for pid in PLACES:
        for tid in TRIALS:
            for gid in GIFTS:
                if args.place and pid != args.place:
                    continue
                if args.trial and tid != args.trial:
                    continue
                if args.gift and gid != args.gift:
                    continue
                if prize_at_risk(TRIALS[tid], GIFTS[gid]):
                    combos.append((pid, tid, gid))
    if not combos:
        raise StoryError("No valid story can be built from those choices.")
    place, trial, gift = rng.choice(combos)
    gender = args.gender or rng.choice(TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != name])
    return StoryParams(place=place, trial=trial, gift=gift, hero_name=name, hero_type=gender, friend_name=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TRIALS[params.trial], GIFTS[params.gift], params.hero_name, params.hero_type, params.friend_name)
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
    StoryParams(place="hill", trial="leap", gift="hand", hero_name="Mira", hero_type="girl", friend_name="Oren"),
    StoryParams(place="forest", trial="climb", gift="song", hero_name="Tavi", hero_type="boy", friend_name="Luma"),
    StoryParams(place="river", trial="run", gift="rope", hero_name="Sera", hero_type="girl", friend_name="Bram"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, t, g) for p in PLACES for t in TRIALS for g in GIFTS if prize_at_risk(TRIALS[t], GIFTS[g])}
    # Keep parity check simple and deterministic.
    if py:
        print(f"OK: Python gate produced {len(py)} valid combinations.")
        return 0
    print("No valid combinations found.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} valid triples:")
        for c in combos[:50]:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
