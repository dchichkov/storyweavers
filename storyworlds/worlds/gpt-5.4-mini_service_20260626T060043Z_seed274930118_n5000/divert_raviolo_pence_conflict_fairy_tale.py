#!/usr/bin/env python3
"""
Standalone storyworld: a small fairy-tale conflict about a child of the court,
a diverted errand, raviolo, and pence.

The seed words suggest a compact old-world tale:
- divert: a journey is interrupted and then redrawn toward a safer choice
- raviolo: a treasured round dumpling-like pastry/meal at the castle table
- pence: the small coins used for a purchase or toll
- Conflict: the core emotional turn
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "princess", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "prince", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    diversion: str
    risk: str
    consequence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    cost: int
    kind: str = "thing"
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    role: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


PLACES = {
    "market": Place("market", "the market", {"buy", "pay"}),
    "bridge": Place("bridge", "the old bridge", {"cross", "pay"}),
    "kitchen": Place("kitchen", "the castle kitchen", {"cook", "buy"}),
    "lane": Place("lane", "the narrow lane", {"buy", "cross"}),
}

QUESTS = {
    "buy_raviolo": Quest(
        "buy_raviolo",
        verb="buy a raviolo",
        gerund="buying a raviolo",
        diversion="take the long way around the fountain",
        risk="the stall may close",
        consequence="the raviolo might be lost to hunger",
        tags={"raviolo", "buy", "market"},
    ),
    "deliver_raviolo": Quest(
        "deliver_raviolo",
        verb="deliver the raviolo",
        gerund="delivering the raviolo",
        diversion="stop to help a traveler",
        risk="the food may grow cold",
        consequence="the raviolo might not be fit for the table",
        tags={"raviolo", "deliver"},
    ),
    "pay_pence": Quest(
        "pay_pence",
        verb="pay the pence",
        gerund="counting pence",
        diversion="let a child peek into the purse",
        risk="the coins may spill",
        consequence="the purse may be short by a penny or two",
        tags={"pence", "pay"},
    ),
}

PRIZES = {
    "raviolo": Prize("raviolo", "raviolo", "a hot raviolo wrapped in a soft cloth", 3),
    "pence": Prize("pence", "pence", "a small purse of pence", 5, plural=True),
}

NAMES = ["Alia", "Bram", "Celia", "Doran", "Elin", "Fenn", "Gilda", "Hugo"]
ROLES = ["girl", "boy"]
HELPERS = ["mother", "father", "baker", "stablehand", "wizard"]


def reasonableness_gate(place: str, quest: str, prize: str) -> None:
    p = PLACES[place]
    q = QUESTS[quest]
    pr = PRIZES[prize]
    if prize not in q.tags:
        raise StoryError("This quest does not honestly involve that prize.")
    if quest == "pay_pence" and place == "kitchen":
        raise StoryError("Pence do not belong in the kitchen scene for this tale.")
    if quest in {"buy_raviolo", "deliver_raviolo"} and "raviolo" != prize:
        raise StoryError("A raviolo tale needs the raviolo prize.")
    if "buy" not in p.affords and quest == "buy_raviolo":
        raise StoryError("That place cannot host a proper buying scene.")
    if "pay" not in p.affords and quest == "pay_pence":
        raise StoryError("That place cannot host a proper paying scene.")


def predict(world: World, hero: Entity, quest: Quest, prize: Prize) -> dict:
    sim = world.copy()
    hero2 = sim.get(hero.id)
    if quest.id == "buy_raviolo":
        hero2.memes["want"] = hero2.memes.get("want", 0) + 1
        hero2.meters["delay"] = hero2.meters.get("delay", 0) + 1
    elif quest.id == "deliver_raviolo":
        hero2.meters["cold"] = hero2.meters.get("cold", 0) + 1
    elif quest.id == "pay_pence":
        hero2.meters["spill"] = hero2.meters.get("spill", 0) + 1
    return {
        "risk": True,
        "lost": prize.id == "pence" and hero2.meters.get("spill", 0) > 0,
    }


def setup(world: World, hero: Entity, helper: Entity, prize: Entity, quest: Quest) -> None:
    world.say(
        f"Long ago, in {world.place.label}, there lived {hero.pronoun('possessive')} "
        f"{helper.type} helper, who knew every turn of the path and every small coin in a purse."
    )
    world.say(
        f"{hero.id} loved {quest.gerund}, and one shining day {hero.pronoun('possessive')} "
        f"thoughts were fixed on {prize.phrase}."
    )
    prize.carried_by = helper.id


def conflict(world: World, hero: Entity, helper: Entity, prize: Entity, quest: Quest) -> None:
    world.para()
    world.say(
        f"At first, all was well, until a little trouble came along the road: "
        f"{quest.diversion}."
    )
    pred = predict(world, hero, quest, prize)
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    if quest.id == "buy_raviolo":
        world.say(
            f"{hero.id} frowned, because {quest.risk}, and then {prize.label} would be gone."
        )
    elif quest.id == "deliver_raviolo":
        world.say(
            f"{helper.id} warned that {quest.risk}, and the soft raviolo would no longer be warm."
        )
    else:
        world.say(
            f"The purse felt heavy, but the little diversion made the {prize.label} feel shakier."
        )
    if pred["lost"]:
        world.say(f"{quest.consequence.capitalize()}.")


def resolution(world: World, hero: Entity, helper: Entity, prize: Prize, quest: Quest) -> None:
    world.para()
    if quest.id == "buy_raviolo":
        world.say(
            f"Then {helper.id} smiled and said, \"Let us divert to the side lane, where the baker has one more {prize.label}.\""
        )
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        hero.memes["conflict"] = 0
        world.say(
            f"They went the safer way, paid the pence, and came home with the warm raviolo held tight against the chill."
        )
    elif quest.id == "deliver_raviolo":
        world.say(
            f"{helper.id} wrapped the raviolo in a fresh cloth and said, \"We shall divert by the hearth, so it stays warm.\""
        )
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        hero.memes["conflict"] = 0
        world.say(
            f"By the time they arrived, the raviolo was still tender, and the table was glad."
        )
    else:
        world.say(
            f"{helper.id} held the purse open and said, \"Count the pence slowly, and divert your hands from any rushing.\""
        )
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        hero.memes["conflict"] = 0
        world.say(
            f"{hero.id} counted carefully, no coin spilled, and the purse stayed full enough for supper."
        )


def tell(place: Place, quest: Quest, prize: Prize, name: str, role: str, helper_role: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=role))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_role))
    prize_ent = world.add(Entity(id=prize.id, type=prize.kind, label=prize.label, phrase=prize.phrase, plural=prize.plural))
    setup(world, hero, helper, prize_ent, quest)
    conflict(world, hero, helper, prize_ent, quest)
    resolution(world, hero, helper, prize, quest)
    world.facts = {
        "hero": hero,
        "helper": helper,
        "prize": prize_ent,
        "quest": quest,
        "place": place,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    prize = f["prize"]
    return [
        f'Write a short fairy tale about {hero.id} and a sudden diversion involving {prize.label}.',
        f"Tell a gentle story where {hero.id} tries to {quest.verb} but must manage a conflict at {world.place.label}.",
        f'Create a child-friendly tale using the words "divert", "{prize.label}", and "pence".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    quest = f["quest"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the story?",
            answer=f"{hero.id} wanted to {quest.verb}, and {prize.phrase} was the thing that mattered most.",
        ),
        QAItem(
            question=f"Why did the story turn into a conflict?",
            answer=f"The story turned into a conflict because {quest.diversion} got in the way, and that could have spoiled the plan.",
        ),
        QAItem(
            question=f"How did {helper.id} help at the end?",
            answer=f"{helper.id} helped by suggesting a safer way to continue, so the tale could end well instead of in loss.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are pence?",
            answer="Pence are small coins used to pay for things in old-money stories.",
        ),
        QAItem(
            question="What is a raviolo?",
            answer="A raviolo is a stuffed piece of pasta, often round like a little pocket.",
        ),
        QAItem(
            question="What does divert mean?",
            answer="To divert means to turn aside or change the path for a moment.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    out.append(f"paragraphs={len([p for p in world.paragraphs if p])}")
    return "\n".join(out)


ASP_RULES = r"""
place(market). place(bridge). place(kitchen). place(lane).
quest(buy_raviolo). quest(deliver_raviolo). quest(pay_pence).
prize(raviolo). prize(pence).

affords(market,buy). affords(market,pay).
affords(bridge,cross). affords(bridge,pay).
affords(kitchen,cook). affords(kitchen,buy).
affords(lane,buy). affords(lane,cross).

tags(buy_raviolo,raviolo). tags(buy_raviolo,buy).
tags(deliver_raviolo,raviolo). tags(deliver_raviolo,deliver).
tags(pay_pence,pence). tags(pay_pence,pay).

valid(P,Q,Pr) :- place(P), quest(Q), prize(Pr), tags(Q,Pr), tags(Q,buy), affords(P,buy).
valid(P,Q,Pr) :- place(P), quest(Q), prize(Pr), tags(Q,Pr), tags(Q,pay), affords(P,pay).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for t in sorted(q.tags):
            lines.append(asp.fact("tags", qid, t))
    for prid in PRIZES:
        lines.append(asp.fact("prize", prid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    out = []
    for pid in PLACES:
        for qid, q in QUESTS.items():
            for prid in PRIZES:
                try:
                    reasonableness_gate(pid, qid, prid)
                except StoryError:
                    continue
                out.append((pid, qid, prid))
    return sorted(set(out))


def asp_verify() -> int:
    a = set(asp_valid())
    p = set(python_valid())
    if a == p:
        print(f"OK: ASP and Python agree on {len(a)} valid combos.")
        return 0
    print("MISMATCH:")
    if a - p:
        print("only in ASP:", sorted(a - p))
    if p - a:
        print("only in Python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fairy-tale storyworld of conflict, raviolo, and pence.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(list(PLACES))
    quest = args.quest or rng.choice(list(QUESTS))
    prize = args.prize or ("raviolo" if quest != "pay_pence" else "pence")
    reasonableness_gate(place, quest, prize)
    role = args.role or rng.choice(ROLES)
    helper = args.helper or rng.choice(HELPERS)
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, quest=quest, prize=prize, name=name, role=role, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], PRIZES[params.prize], params.name, params.role, params.helper)
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
    StoryParams(place="market", quest="buy_raviolo", prize="raviolo", name="Alia", role="girl", helper="mother"),
    StoryParams(place="bridge", quest="pay_pence", prize="pence", name="Bram", role="boy", helper="father"),
    StoryParams(place="lane", quest="deliver_raviolo", prize="raviolo", name="Celia", role="girl", helper="baker"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid combinations:")
        for row in vals:
            print(" ", row)
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
