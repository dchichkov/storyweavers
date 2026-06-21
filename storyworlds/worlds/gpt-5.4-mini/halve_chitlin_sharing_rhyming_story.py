#!/usr/bin/env python3
"""Standalone storyworld: sharing a single treat by halving it.

This world rebuilds a tiny rhyming-style sharing tale from a seed with the words
"halve" and "chitlin". A child wants to share a snack, first makes a clumsy or
sensible choice about how to divide it, and then learns a warm lesson about
sharing.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    role: str = ""
    owner: str = ""
    portable: bool = True
    shareable: bool = False
    divisible: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    rhyme: str
    sweet: bool = True
    shareable: bool = True
    divisible: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class ShareMove:
    id: str
    sense: int
    parts: int
    text: str
    fail: str
    qa_text: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_shared(world: World) -> list[str]:
    out: list[str] = []
    snack = world.get("snack")
    if snack.meters["cut"] < THRESHOLD:
        return out
    sig = ("shared",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for name in ("kid1", "kid2"):
        world.get(name).memes["happy"] += 1
    world.get("house").memes["peace"] += 1
    out.append("__shared__")
    return out


CAUSAL_RULES = [Rule("shared", "social", _r_shared)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(snack: Snack, move: ShareMove) -> bool:
    return snack.shareable and snack.divisible and move.parts == 2


def safe_moves() -> list[ShareMove]:
    return [m for m in MOVES.values() if m.sense >= 2]


def best_move() -> ShareMove:
    return max(MOVES.values(), key=lambda m: m.sense)


def split_success(move: ShareMove, snack: Snack) -> bool:
    return move.parts == 2 and snack.divisible


def _do_cut(world: World, snack: Entity, move: ShareMove, narrate: bool = True) -> None:
    snack.meters["cut"] += 1
    snack.meters["shared_parts"] += move.parts
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, friend: Entity, snack: Snack, scene: str) -> None:
    world.say(
        f"On a bright little day, {child.id} and {friend.id} had a tune in their feet, "
        f"for sharing can make a sweet day sweeter than sweet."
    )
    world.say(
        f"They sat in {scene}, with a {snack.phrase} to spare, and a tiny wish whispered, "
        f'"Let\'s split it and share."'
    )


def want_share(world: World, child: Entity, snack: Snack) -> None:
    child.memes["want_share"] += 1
    world.say(
        f"{child.id} smiled at the {snack.label} with a merry little glow, "
        f"for one treat can taste better when two hearts say so."
    )


def clumsy_plan(world: World, child: Entity, snack: Snack) -> None:
    child.memes["eager"] += 1
    world.say(
        f'"I can {snack.rhyme} it! I can make it right neat," said {child.id}, '
        f'"I\'ll try to halve it and hand you a treat."'
    )


def warn(world: World, friend: Entity, child: Entity, snack: Snack, parent: Entity) -> None:
    friend.memes["care"] += 1
    world.say(
        f'{friend.id} shook {friend.pronoun("possessive")} head with a kind little sigh. '
        f'"{parent.label_word.capitalize()} said share with care; don\'t make it fly."'
    )


def choose_move(world: World, move: ShareMove, snack: Snack, child: Entity, friend: Entity) -> None:
    if move.id == "gentle_halve":
        world.say(
            f"So {child.id} took a small knife and cut straight and slow, "
            f"making two even halves in one careful row."
        )
    elif move.id == "crumbly_break":
        world.say(
            f"But {child.id} pinched it and broke it apart with a snap, "
            f"and crumbs sprinkled down in a bumpy little trap."
        )
    else:
        world.say(
            f"{child.id} tried a quick twist and a hurried little shove, "
            f"but the pieces did not fit like two hands in a glove."
        )


def share_result(world: World, child: Entity, friend: Entity, snack: Snack, move: ShareMove) -> None:
    if split_success(move, snack):
        _do_cut(world, world.get("snack"), move)
        world.say(
            f"Then one half went to {child.id} and one half went to {friend.id}, "
            f"and the room filled with giggles from end to end."
        )
    else:
        _do_cut(world, world.get("snack"), move)
        world.say(
            f"The snack turned lumpy and lopsided, and nobody felt glad; "
            f"it was hard to share tidy when the cut went bad."
        )


def lesson(world: World, parent: Entity, child: Entity, friend: Entity, snack: Snack) -> None:
    child.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f"Then {parent.label_word.capitalize()} came in with a warm, happy grin, "
        f'"Sharing is kinder when everyone wins."'
    )
    world.say(
        f"{child.id} nodded, {friend.id} cheered, and the little bright snack "
        f"felt twice as nice once the sharing came back."
    )


def ending_image(world: World, child: Entity, friend: Entity, snack: Snack) -> None:
    world.say(
        f"By the end, the plate held two neat little bits, and {child.id} and {friend.id} "
        f"sat side by side, with crumbs and with smiles and with full grateful hearts."
    )


SNACKS = {
    "chitlin": Snack(
        id="chitlin",
        label="chitlin",
        phrase="one hot chitlin",
        rhyme="halve",
        sweet=False,
        shareable=True,
        divisible=True,
    ),
    "cookie": Snack(
        id="cookie",
        label="cookie",
        phrase="one big cookie",
        rhyme="halve",
        sweet=True,
        shareable=True,
        divisible=True,
    ),
    "pie": Snack(
        id="pie",
        label="pie",
        phrase="one warm pie",
        rhyme="halve",
        sweet=True,
        shareable=True,
        divisible=True,
    ),
}

MOVES = {
    "gentle_halve": ShareMove(
        id="gentle_halve",
        sense=3,
        parts=2,
        text="cut the snack into two neat halves",
        fail="tried to cut the snack, but it stayed messy",
        qa_text="cut the snack into two neat halves",
    ),
    "crumbly_break": ShareMove(
        id="crumbly_break",
        sense=2,
        parts=2,
        text="broke the snack into two pieces",
        fail="broke the snack into uneven bits",
        qa_text="broke the snack into two pieces",
    ),
    "divide_three": ShareMove(
        id="divide_three",
        sense=1,
        parts=3,
        text="tried to make three pieces",
        fail="made too many pieces to share well",
        qa_text="tried to make three pieces",
    ),
}

SCENES = ["the kitchen table", "the sunny porch", "a tiny picnic blanket"]
CHILDREN = ["Mia", "Lily", "Noah", "Ben", "Ava", "Theo"]


@dataclass
@dataclass
class StoryParams:
    snack: str
    move: str
    child: str
    friend: str
    parent: str
    scene: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for snack_id, snack in SNACKS.items():
        for move_id, move in MOVES.items():
            if reasonableness_gate(snack, move):
                combos.append((snack_id, move_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld about sharing a snack.")
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--child")
    ap.add_argument("--friend")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--scene", choices=SCENES)
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
    if args.snack and args.move:
        if not reasonableness_gate(SNACKS[args.snack], MOVES[args.move]):
            raise StoryError("(No story: this snack-and-move pair does not make a clean sharing tale.)")
    combos = [c for c in valid_combos()
              if (args.snack is None or c[0] == args.snack)
              and (args.move is None or c[1] == args.move)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    snack, move = rng.choice(sorted(combos))
    child = args.child or rng.choice(CHILDREN)
    friend_choices = [n for n in CHILDREN if n != child]
    friend = args.friend or rng.choice(friend_choices)
    parent = args.parent or rng.choice(["mother", "father"])
    scene = args.scene or rng.choice(SCENES)
    return StoryParams(snack, move, child, friend, parent, scene)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type="child", role="child"))
    friend = world.add(Entity(id=params.friend, kind="character", type="child", role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    snack_cfg = SNACKS[params.snack]
    snack = world.add(Entity(id="snack", kind="thing", type="snack", label=snack_cfg.label, phrase=snack_cfg.phrase, shareable=True, divisible=True))
    move = MOVES[params.move]

    intro(world, child, friend, snack_cfg, params.scene)
    world.para()
    want_share(world, child, snack_cfg)
    clumsy_plan(world, child, snack_cfg)
    warn(world, friend, child, snack_cfg, parent)
    world.para()
    choose_move(world, move, snack_cfg, child, friend)
    share_result(world, child, friend, snack_cfg, move)
    lesson(world, parent, child, friend, snack_cfg)
    ending_image(world, child, friend, snack_cfg)

    world.facts.update(child=child, friend=friend, parent=parent, snack=snack, snack_cfg=snack_cfg, move=move)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    snack = f["snack_cfg"]
    return [
        f'Write a rhyming story for a little child that includes the word "halve" and the word "{snack.id}".',
        f"Tell a sharing story where {f['child'].id} wants to split a {snack.label} with {f['friend'].id}, and they learn to share kindly.",
        f'Write a gentle rhyming story about sharing one {snack.label} by trying to halve it.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    parent = f["parent"]
    snack = f["snack_cfg"]
    move = f["move"]
    return [
        QAItem(
            question="What were the children trying to do?",
            answer=f"They were trying to share one {snack.label}. {child.id} wanted to halve it so both children could have some."),
        QAItem(
            question=f"What did {child.id} do with the snack?",
            answer=f"{child.id} used a careful move and {move.qa_text}. That made it easier for {child.id} and {friend.id} to share."),
        QAItem(
            question="Why did the ending feel happy?",
            answer=f"The snack was split into two parts, so both children got a piece. Their parent liked that everyone ended up smiling and included."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to halve something?",
            answer="To halve something means to divide it into two equal parts. That way, two people can each get the same amount."),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or have part of what you have. It is a kind way to play and eat together."),
        QAItem(
            question="Why is sharing nice?",
            answer="Sharing is nice because it helps people feel included and cared for. A shared treat can make the whole moment feel warmer."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("chitlin", "gentle_halve", "Mia", "Noah", "mother", "the kitchen table"),
    StoryParams("cookie", "crumbly_break", "Lily", "Ben", "father", "a tiny picnic blanket"),
    StoryParams("pie", "gentle_halve", "Ava", "Theo", "mother", "the sunny porch"),
]


ASP_RULES = r"""
valid(Snack, Move) :- snack(Snack), move(Move), shareable(Snack), divisible(Snack), parts(Move, 2).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if s.shareable:
            lines.append(asp.fact("shareable", sid))
        if s.divisible:
            lines.append(asp.fact("divisible", sid))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("parts", mid, m.parts))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    c = set(asp_valid_combos())
    p = set(valid_combos())
    if c == p:
        print(f"OK: clingo gate matches valid_combos() ({len(c)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if c - p:
        print("  only in clingo:", sorted(c - p))
    if p - c:
        print("  only in python:", sorted(p - c))
    return 1


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (snack, move) combos:\n")
        for snack, move in asp_valid_combos():
            print(f"  {snack:10} {move}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        if args.all:
            p = sample.params
            header = f"### {p.child} and {p.friend}: {p.snack} with {p.move}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
