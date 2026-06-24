#!/usr/bin/env python3
"""
storyworlds/worlds/tread_brad_cautionary_happy_ending_whodunit.py
==================================================================

A small whodunit story world: a child detective follows a tread clue, suspects
Brad, and learns a cautionary lesson before the story ends happily.

Premise:
- A special pie vanishes from the kitchen table.
- Fresh tread marks lead the detective through a tiny mystery.
- Brad looks suspicious, but the clues point to a kinder truth.

Tension:
- The detective notices a useful clue and jumps to a conclusion.
- Emotional pressure rises: worry, suspicion, and a little shame.

Turn:
- The tread is matched to a garden cart, not Brad's shoes.
- Brad was only helping carry the pie back after it slipped.

Resolution:
- The pie is rescued, Brad is cleared, and everyone shares the treat.
- The ending is cautionary: don't accuse too fast; check the clues first.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

TREAD_DEPTH = 1.0
SUSPICION_DEPTH = 1.0


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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    detail: str = "The kitchen smelled like warm sugar and butter."


@dataclass
class Clue:
    id: str
    label: str
    source: str
    prints: str
    fit: str


@dataclass
class Case:
    id: str
    verb: str
    danger: str
    consequence: str
    clue: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    clue = world.facts["clue"]
    if detective.meters.get("suspicion", 0) < TREAD_DEPTH:
        return out
    sig = ("suspect", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["anxiety"] = detective.memes.get("anxiety", 0) + 1
    out.append(f"The clue made the room feel smaller.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts["clue"]
    cart = world.get("cart")
    detective = world.get("detective")
    if cart.meters.get("used", 0) < TREAD_DEPTH:
        return out
    sig = ("reveal", cart.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["relief"] = detective.memes.get("relief", 0) + 1
    out.append("The answer was hiding in plain sight.")
    return out


CAUSAL_RULES = [_r_suspicion, _r_reveal]


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


def track_fresh_tread(world: World, detective: Entity) -> None:
    detective.meters["suspicion"] = detective.meters.get("suspicion", 0) + 1
    world.say(
        f"{detective.id} noticed a fresh tread by the table and felt certain it mattered."
    )


def accuse(world: World, detective: Entity, brad: Entity) -> None:
    detective.memes["suspicion"] = detective.memes.get("suspicion", 0) + 1
    brad.memes["hurt"] = brad.memes.get("hurt", 0) + 1
    world.say(
        f'{detective.id} looked at Brad and said, "You took the pie, didn\'t you?"'
    )


def inspect(world: World, detective: Entity) -> None:
    world.say(
        f"{detective.id} bent low and studied the tread again, looking for a better answer."
    )


def reveal_truth(world: World, brad: Entity, cart: Entity, pie: Entity) -> None:
    cart.meters["used"] = cart.meters.get("used", 0) + 1
    world.say(
        f'Brad pointed to the garden cart and said, "I used this to carry the pie when it slipped."'
    )
    world.say(
        f"The tread came from the cart wheel, not from Brad's shoes."
    )
    pie.meters["found"] = pie.meters.get("found", 0) + 1
    brad.memes["calm"] = brad.memes.get("calm", 0) + 1


def happy_ending(world: World, detective: Entity, brad: Entity, pie: Entity) -> None:
    detective.memes["shame"] = detective.memes.get("shame", 0) + 1
    detective.memes["relief"] = detective.memes.get("relief", 0) + 1
    world.say(
        f"{detective.id} apologized, and Brad smiled because the pie was safe at last."
    )
    world.say(
        f"They shared the pie together, and the kitchen felt warm and bright again."
    )


SETTINGS = {
    "kitchen": Setting(
        place="the kitchen",
        detail="The kitchen smelled like warm sugar and butter.",
    )
}

CASES = {
    "pie": Case(
        id="pie",
        verb="vanish",
        danger="went missing",
        consequence="someone might be blamed unfairly",
        clue="tread",
        tags={"tread", "pie", "cart"},
    )
}

CLUES = {
    "tread": Clue(
        id="tread",
        label="fresh tread marks",
        source="garden cart wheel",
        prints="round and narrow",
        fit="the cart wheel",
    )
}

GIRL_NAMES = ["Maya", "Nora", "Lina", "Eve", "Ada"]
BOY_NAMES = ["Finn", "Owen", "Jude", "Noah", "Leo"]
TRAITS = ["careful", "curious", "bright", "thoughtful", "quick"]


@dataclass
class StoryParams:
    place: str
    case: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_cases() -> list[tuple[str, str]]:
    return [("kitchen", "pie")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary happy-ending whodunit.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.place and args.place != "kitchen":
        raise StoryError("This mystery only works in the kitchen.")
    if args.case and args.case != "pie":
        raise StoryError("This mystery only works with the missing pie.")
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("Unsupported gender.")
    name = args.name or rng.choice(GIRL_NAMES if (args.gender or "girl") == "girl" else BOY_NAMES)
    gender = args.gender or ("girl" if name in GIRL_NAMES else "boy")
    trait = rng.choice(TRAITS)
    return StoryParams(place="kitchen", case="pie", name=name, gender=gender, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    detective = world.add(Entity(id="detective", kind="character", type=params.gender, label=params.name))
    brad = world.add(Entity(id="brad", kind="character", type="boy", label="Brad"))
    pie = world.add(Entity(id="pie", type="thing", label="pie", phrase="a berry pie", caretaker="detective"))
    cart = world.add(Entity(id="cart", type="thing", label="garden cart", phrase="a small garden cart"))
    clue = CLUES["tread"]

    world.facts.update(detective=detective, brad=brad, pie=pie, cart=cart, clue=clue, params=params)

    world.say(f"{params.name} was a {params.trait} little detective who loved neat clues.")
    world.say(f"One morning, a berry pie vanished from {world.setting.place}.")
    world.say(world.setting.detail)
    world.para()
    track_fresh_tread(world, detective)
    world.say(f"The tread was {clue.prints}, and it seemed to fit {clue.fit}.")
    accuse(world, detective, brad)
    propagate(world)
    world.para()
    inspect(world, detective)
    reveal_truth(world, brad, cart, pie)
    propagate(world)
    world.para()
    happy_ending(world, detective, brad, pie)
    world.facts["resolved"] = True
    world.facts["cautionary"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        'Write a short whodunit for a child that includes the word "tread".',
        f"Tell a cautionary mystery where {p.name} suspects Brad too quickly, then learns the truth.",
        "Write a happy-ending detective story about a missing pie, a cart wheel, and a fresh clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    detective = world.facts["detective"]
    brad = world.facts["brad"]
    return [
        QAItem(
            question="What clue did the detective notice first?",
            answer="The detective noticed fresh tread marks by the table.",
        ),
        QAItem(
            question="Why did the detective suspect Brad?",
            answer="Because the tread looked suspicious, and Brad was the first person nearby, so the detective jumped to a quick conclusion.",
        ),
        QAItem(
            question="What was the real source of the tread?",
            answer="The tread came from the garden cart wheel, not from Brad's shoes.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The detective apologized, the pie was found safe, and everyone shared it happily.",
        ),
        QAItem(
            question=f"Who is the story about?",
            answer=f"It follows {p.name}, a {p.trait} little detective, and Brad in a kitchen mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tread?",
            answer="Tread is the pattern or marks that a shoe or wheel leaves behind on a surface.",
        ),
        QAItem(
            question="What is a cart wheel for?",
            answer="A cart wheel helps a cart roll and carry things from one place to another.",
        ),
        QAItem(
            question="Why should you check clues before accusing someone?",
            answer="Because clues can have more than one meaning, and checking first helps you avoid blaming the wrong person.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:9} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
clue(tread).
character(detective).
character(brad).
thing(pie).
thing(cart).

suspect(detective, brad) :- clue(tread).
wrongly_accused(detective, brad) :- suspect(detective, brad).
reveal(cart) :- clue(tread).
happy_ending :- reveal(cart).
cautionary :- wrongly_accused(detective, brad).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("clue", "tread"),
        asp.fact("character", "detective"),
        asp.fact("character", "brad"),
        asp.fact("thing", "pie"),
        asp.fact("thing", "cart"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/0. #show cautionary/0. #show wrongly_accused/2."))
    atoms = set((a.name, len(a.arguments)) for a in model)
    expected = {("happy_ending", 0), ("cautionary", 0), ("wrongly_accused", 2)}
    if atoms == expected:
        print("OK: ASP twin matches the Python story shape.")
        return 0
    print("MISMATCH in ASP verification.")
    return 1


def asp_valid_combos() -> list[tuple[str, str]]:
    return valid_cases()


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
    StoryParams(place="kitchen", case="pie", name="Maya", gender="girl", trait="careful"),
    StoryParams(place="kitchen", case="pie", name="Noah", gender="boy", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/0. #show cautionary/0. #show wrongly_accused/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern: kitchen / pie")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
