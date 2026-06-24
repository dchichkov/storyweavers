#!/usr/bin/env python3
"""
storyworlds/worlds/fellow_ship_paw_rosemary_happy_ending_humor.py
==================================================================

A small pirate-tale storyworld about a fellow-ship crew, a hungry paw, and a
sprig of rosemary that saves the supper with a funny, happy ending.

Premise:
- A child pirate and a grown-up friend sail a tiny boat called the Fellow-Ship.
- A cheeky paw keeps reaching for the captain's rosemary bun.
- The crew first worries the paw is trouble, then discovers it is only a
  hungry little helper from the harbor cat.
- The fix is to offer a rosemary twig and a safe snack, turning the chase into
  a laugh and a shared meal.

This world uses typed entities with meters and memes, a forward-chained state
update, a reasonableness gate, and an inline ASP twin.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "sailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Harbor:
    name: str = "the little harbor"
    place: str = "the dock"
    affords: set[str] = field(default_factory=lambda: {"sail", "snack", "trade"})


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    tastes: str
    plural: bool = False


@dataclass
class CrewMove:
    id: str
    verb: str
    gerund: str
    at_risk: str
    risk: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.harbor)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_hungry_paw(world: World) -> list[str]:
    out: list[str] = []
    paw = world.entities.get("paw")
    if not paw:
        return out
    if paw.meters.get("hungry", 0.0) < THRESHOLD:
        return out
    sig = ("hungry_paw", paw.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    paw.meters["sneaky"] = paw.meters.get("sneaky", 0.0) + 1
    out.append("A hungry paw kept patting the table like a tiny drum.")
    return out


def _r_spill_rosemary(world: World) -> list[str]:
    out: list[str] = []
    paw = world.entities.get("paw")
    bun = world.entities.get("bun")
    if not paw or not bun:
        return out
    if paw.meters.get("snatched", 0.0) < THRESHOLD:
        return out
    sig = ("snatch", bun.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bun.meters["crumbled"] = bun.meters.get("crumbled", 0.0) + 1
    bun.meters["touched"] = bun.meters.get("touched", 0.0) + 1
    out.append("The rosemary bun went tumble-tap and spilled a trail of crumbs.")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    cat = world.entities.get("cat")
    paw = world.entities.get("paw")
    if not cat or not paw:
        return out
    if paw.meters.get("fed", 0.0) < THRESHOLD:
        return out
    sig = ("laugh", cat.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cat.memes["joy"] = cat.memes.get("joy", 0.0) + 1
    out.append("The harbor cat blinked, then looked so pleased that everyone laughed.")
    return out


CAUSAL_RULES = [
    _r_hungry_paw,
    _r_spill_rosemary,
    _r_laugh,
]


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


def paw_at_risk(move: CrewMove, prize: Prize) -> bool:
    return prize.region in move.at_risk


def compatible_fix(move: CrewMove, prize: Prize) -> bool:
    return move.fix == "feed_and_share" and prize.tastes == "rosemary"


@dataclass
class StoryParams:
    move: str
    prize: str
    treat: str
    name: str
    helper: str
    seed: Optional[int] = None


MOVES = {
    "snack_theft": CrewMove(
        id="snack_theft",
        verb="grab the snack",
        gerund="grabbing the snack",
        at_risk="table",
        risk="crumbly",
        fix="feed_and_share",
        tags={"snack", "paw", "rosemary"},
    ),
    "map_mess": CrewMove(
        id="map_mess",
        verb="paw at the map",
        gerund="pawing at the map",
        at_risk="table",
        risk="inky",
        fix="feed_and_share",
        tags={"paw"},
    ),
}

PRIZES = {
    "bun": Prize(label="bun", phrase="a warm rosemary bun", region="table", tastes="rosemary"),
    "crackers": Prize(label="crackers", phrase="a tin of crackers", region="table", tastes="salty"),
}

TREATS = {
    "fish": Treat(id="fish", label="little fish snack", phrase="a little fish snack", tags={"fish"}),
    "cheese": Treat(id="cheese", label="cheese cube", phrase="a cheese cube", tags={"cheese"}),
    "rosemary": Treat(id="rosemary", label="rosemary twig", phrase="a fresh rosemary twig", tags={"rosemary"}),
}

NAMES = ["Mina", "Pip", "Jude", "Nell", "Bram", "Tessa"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for m in MOVES:
        for p in PRIZES:
            if paw_at_risk(MOVES[m], PRIZES[p]) and compatible_fix(MOVES[m], PRIZES[p]):
                out.append((m, p, "rosemary"))
    return out


def tell(params: StoryParams) -> World:
    world = World(Harbor())
    captain = world.add(Entity(id=params.name, kind="character", type="captain", label=params.name))
    helper = world.add(Entity(id=params.helper, kind="character", type="sailor", label=params.helper))
    paw = world.add(Entity(id="paw", kind="character", type="cat", label="a cheeky paw"))
    cat = world.add(Entity(id="cat", kind="character", type="cat", label="the harbor cat"))
    bun = world.add(Entity(id="bun", kind="thing", type="bun", label="rosemary bun"))
    treat = world.add(Entity(id="treat", kind="thing", type="treat", label=TREATS[params.treat].label))

    paw.meters["hungry"] = 1.0
    captain.memes["worry"] = 1.0
    helper.memes["humor"] = 1.0

    world.say(
        f"On the fellow-ship, {captain.id} and {helper.id} sailed past {world.harbor.name}, "
        f"with a rosemary bun waiting by the mast."
    )
    world.say(
        f"Then a cheeky paw peeked up from the dock, as if it had a secret joke and a very empty tummy."
    )
    world.para()
    world.say(
        f'{captain.id} pointed at the bun. "{paw.label} is after supper!"'
    )
    world.say(
        f'{helper.id} chuckled. "Maybe the paw wants a share, not a squabble."'
    )

    move = MOVES[params.move]
    prize = PRIZES[params.prize]
    treat_cfg = TREATS[params.treat]

    if not paw_at_risk(move, prize):
        raise StoryError("This story needs a prize that the paw can actually reach.")

    paw.meters["snatched"] = 1.0
    propagate(world)

    world.para()
    world.say(
        f"The paw went tap-tap and knocked the rosemary bun sideways, but {helper.id} did not scold."
    )
    world.say(
        f'Instead, {helper.id} held up {treat_cfg.phrase} and said, "Little paws need little snacks."'
    )
    paw.meters["fed"] = 1.0
    world.say(
        f"The paw settled down at once, because a full paw is a polite paw."
    )
    propagate(world)

    world.para()
    world.say(
        f'{captain.id} laughed so hard that the fellow-ship rocked. "That paw has better manners now than the pirates!"'
    )
    world.say(
        f"With the rosemary twig and the snack shared out, the crew ate the bun, the cat purred, and the dock stayed merry."
    )

    world.facts.update(
        captain=captain,
        helper=helper,
        paw=paw,
        cat=cat,
        bun=bun,
        treat=treat,
        move=move,
        prize=prize,
        treat_cfg=treat_cfg,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate-style story for a little child about the fellow-ship, a hungry paw, and rosemary.',
        f"Tell a funny happy-ending story where {f['captain'].id} and {f['helper'].id} meet a cheeky paw near a rosemary bun.",
        f"Write a child-friendly pirate tale with a joke, a hungry paw, and a rosemary treat that ends in shared supper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cap, hel, paw, bun = f["captain"], f["helper"], f["paw"], f["bun"]
    treat = f["treat_cfg"]
    return [
        QAItem(
            question=f"Who was the story about on the fellow-ship?",
            answer=(
                f"It was about {cap.id}, {hel.id}, and a cheeky paw. They were all caught up in the rosemary bun business, but the ending stayed cheerful."
            ),
        ),
        QAItem(
            question=f"What did the paw want near the bun?",
            answer=(
                f"The paw wanted the rosemary bun at first, because it was hungry and the smell was tempting. That is why the bun got knocked sideways."
            ),
        ),
        QAItem(
            question=f"How did {hel.id} solve the problem?",
            answer=(
                f"{hel.id} offered a little snack and a rosemary twig, so the paw calmed down and stopped snatching. That turned the trouble into a joke instead of a mess."
            ),
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=(
                f"Everyone shared the bun, the cat purred, and the crew laughed together on the dock. It ended as a happy supper with no one upset."
            ),
        ),
        QAItem(
            question=f"Why was rosemary important?",
            answer=(
                f"Rosemary made the bun smell special, and a rosemary twig also helped calm the hungry paw. In this tale, rosemary was part of both the treat and the fix."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a paw?",
            answer="A paw is an animal foot, like the soft foot a cat uses for walking and tapping things.",
        ),
        QAItem(
            question="What is rosemary?",
            answer="Rosemary is a herb with a fresh smell. People use it to flavor food, and it can make a bun or roast smell nice.",
        ),
        QAItem(
            question="Why do cats like snacks?",
            answer="Cats like snacks because food smells good and makes them feel full. A hungry cat may follow a tasty smell.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        parts.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(parts)


ASP_RULES = r"""
paw_risk(M,P) :- move(M), prize(P), at_risk_region(M,R), prize_region(P,R).
good_fix(M,P) :- move(M), prize(P), paw_risk(M,P), fix(M,feed_and_share), tastes(P,rosemary).
valid(M,P,T) :- paw_risk(M,P), good_fix(M,P), treat(T), tags(T,rosemary).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("at_risk_region", mid, m.at_risk))
        lines.append(asp.fact("fix", mid, m.fix))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
        lines.append(asp.fact("tastes", pid, p.tastes))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        for tag in t.tags:
            lines.append(asp.fact("tags", tid, tag))
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
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("py-only:", sorted(py - cl))
    print("cl-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale about a fellow-ship, a paw, and rosemary.")
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    combos = valid_combos()
    if args.move and args.prize and (args.move, args.prize, "rosemary") not in combos:
        raise StoryError("That combination is too weak for this paw-and-rosemary story.")
    move, prize, treat = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != name])
    return StoryParams(move=move, prize=prize, treat=args.treat or treat, name=name, helper=helper)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(move="snack_theft", prize="bun", treat="rosemary", name="Mina", helper="Pip"),
    StoryParams(move="map_mess", prize="bun", treat="fish", name="Jude", helper="Tessa"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(rng_base + i))
            samples.append(generate(p))

    if args.json:
        print(json.dumps([s.to_dict() for s in samples] if len(samples) > 1 else samples[0].to_dict(), indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
