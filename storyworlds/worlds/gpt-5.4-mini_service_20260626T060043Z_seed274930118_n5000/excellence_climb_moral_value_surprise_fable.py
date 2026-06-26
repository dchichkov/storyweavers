#!/usr/bin/env python3
"""
A fable-style storyworld about a small creature striving for excellence,
climbing a hill, learning humility, and meeting a surprise turn that changes
the ending.
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
        if self.type in {"fox", "wolf", "goat", "rabbit", "crow", "mouse"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    risk: str
    zone: str
    surprise: str
    keyword: str = "excellence"


@dataclass
class Prize:
    label: str
    phrase: str
    region: str


@dataclass
class Guidance:
    label: str
    prep: str
    tail: str
    covers: set[str]
    fixes: set[str]


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _r_excess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character":
            continue
        if actor.meters.get("effort", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("pride", 0.0) < THRESHOLD:
            continue
        sig = ("excess", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["strain"] = actor.memes.get("strain", 0.0) + 1
        out.append(f"{actor.label} tried too hard and began to strain.")
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    mentor = next((e for e in world.entities.values() if e.kind == "character" and e.type == "owl"), None)
    hero = next((e for e in world.entities.values() if e.kind == "character" and e.type in {"fox", "goat", "mouse", "rabbit"}), None)
    if not mentor or not hero:
        return out
    if hero.memes.get("humility", 0.0) < THRESHOLD:
        return out
    sig = ("help", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["wisdom"] = hero.memes.get("wisdom", 0.0) + 1
    out.append(f"{mentor.label} noticed the change and offered one kind word.")
    return out


CAUSAL_RULES = [
    _r_excess,
    _r_help,
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


def predict(world: World, actor: Entity, challenge: Challenge) -> dict:
    sim = world.copy()
    do_climb(sim, sim.get(actor.id), challenge, narrate=False)
    hero = sim.get(actor.id)
    return {
        "stumbled": hero.meters.get("stumble", 0.0) >= THRESHOLD,
        "surprised": hero.memes.get("surprise", 0.0) >= THRESHOLD,
    }


def do_climb(world: World, actor: Entity, challenge: Challenge, narrate: bool = True) -> None:
    if challenge.id not in world.setting.afford:
        raise StoryError("This place cannot host that climb.")
    actor.meters["effort"] = actor.meters.get("effort", 0.0) + 1
    actor.meters["height"] = actor.meters.get("height", 0.0) + 1
    actor.memes["pride"] = actor.memes.get("pride", 0.0) + 1
    if challenge.zone == "steep":
        actor.meters["stumble"] = actor.meters.get("stumble", 0.0) + 1
    if narrate:
        propagate(world, narrate=True)


def setting_line(setting: Setting) -> str:
    return {
        "hill": "The hill rose green and quiet above the meadow.",
        "tree": "The tree stood tall, with bark that looked like a ladder of brown lines.",
        "stone": "The stone path curled upward like a sleepy ribbon.",
    }.get(setting.place, "The path waited under a bright sky.")


def intro(world: World, hero: Entity, mentor: Entity, prize: Entity, challenge: Challenge) -> None:
    world.say(
        f"Once in a small field, {hero.label} the {hero.type} loved the word excellence, "
        f"because it sounded like the best kind of trying."
    )
    world.say(
        f"{hero.label} wanted to {challenge.verb}, and {mentor.label} the wise owl "
        f"watched from a branch near the {prize.label}."
    )


def warn(world: World, mentor: Entity, hero: Entity, prize: Entity, challenge: Challenge) -> bool:
    pred = predict(world, hero, challenge)
    if not pred["stumbled"]:
        return False
    world.facts["surprise"] = challenge.surprise
    world.say(
        f'"If you keep rushing," {mentor.label} said, "you may miss the {challenge.surprise}."'
    )
    return True


def struggle(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.memes["impatience"] = hero.memes.get("impatience", 0.0) + 1
    world.say(
        f"{hero.label} climbed faster and faster, but the steep parts made tiny paws slip."
    )


def surprise_turn(world: World, hero: Entity, prize: Entity, challenge: Challenge) -> None:
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
    world.say(
        f"Near the top, {hero.label} found the {challenge.surprise}: the {prize.label} had not been lost at all."
    )


def accept(world: World, hero: Entity, mentor: Entity, prize: Entity) -> None:
    hero.memes["humility"] = hero.memes.get("humility", 0.0) + 1
    hero.memes["pride"] = 0.0
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
    world.say(
        f"{hero.label} smiled, thanked {mentor.label}, and climbed the last steps more carefully."
    )
    world.say(
        f"At the top, {hero.label} sat beside the {prize.label}, and the little field felt brighter than before."
    )


def tell(setting: Setting, challenge: Challenge, prize_cfg: Prize, hero_name: str = "Robin", hero_type: str = "fox") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    mentor = world.add(Entity(id="Mentor", kind="character", type="owl", label="Aunt Owl"))
    prize = world.add(Entity(id="Prize", type="thing", label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    intro(world, hero, mentor, prize, challenge)
    world.para()
    world.say(setting_line(setting))
    warn(world, mentor, hero, prize, challenge)
    struggle(world, hero, challenge)
    do_climb(world, hero, challenge, narrate=True)
    world.para()
    surprise_turn(world, hero, prize, challenge)
    accept(world, hero, mentor, prize)
    world.facts.update(hero=hero, mentor=mentor, prize=prize, challenge=challenge, setting=setting)
    return world


SETTINGS = {
    "hill": Setting(place="hill", afford={"climb"}),
    "tree": Setting(place="tree", afford={"climb"}),
    "stone": Setting(place="stone", afford={"climb"}),
}

CHALLENGES = {
    "climb": Challenge(
        id="climb",
        verb="climb to the top",
        gerund="climbing upward",
        risk="stumble",
        zone="steep",
        surprise="a missing prize was waiting on the ledge",
        keyword="excellence",
    ),
}

PRIZES = {
    "star": Prize(label="star ribbon", phrase="a bright star ribbon", region="top"),
    "bell": Prize(label="bell", phrase="a tiny brass bell", region="top"),
}

GUIDANCE = [
    Guidance(
        label="careful steps",
        prep="pause and take careful steps",
        tail="walked the rest of the way with careful steps",
        covers={"top"},
        fixes={"stumble"},
    ),
]


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about excellence, climbing, and a surprise moral turn.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, c, r) for p in SETTINGS for c in CHALLENGES for r in PRIZES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, challenge, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Robin", "Milo", "Pip", "Nia", "Tess"])
    return StoryParams(place=place, challenge=challenge, prize=prize, name=name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for children about excellence and a {f["challenge"].verb} story with a surprise ending.',
        f"Tell a gentle story about {f['hero'].label} the {f['hero'].type} climbing the {f['setting'].place} and learning a moral value.",
        f'Write a fable that uses the word "excellence" and ends with a surprise at the top of a climb.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mentor, prize, challenge = f["hero"], f["mentor"], f["prize"], f["challenge"]
    return [
        QAItem(
            question=f"Who learned about excellence in the story?",
            answer=f"{hero.label} the {hero.type} learned that excellence is not only about speed; it is also about patience and careful trying.",
        ),
        QAItem(
            question=f"What was {hero.label} trying to do?",
            answer=f"{hero.label} was trying to {challenge.verb}, which made the climb feel exciting and hard.",
        ),
        QAItem(
            question=f"Who gave the warning before the climb became tricky?",
            answer=f"{mentor.label} the owl gave the warning because {mentor.label} could see that rushing might lead to a stumble.",
        ),
        QAItem(
            question=f"What surprise appeared near the end?",
            answer=f"The surprise was that the {prize.label} was already waiting on the ledge, so the climb ended with a happy discovery instead of a loss.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is excellence?",
            answer="Excellence means doing something very well, with care, practice, and attention.",
        ),
        QAItem(
            question="What is a moral value in a fable?",
            answer="A moral value is the lesson a fable teaches, like kindness, patience, or honesty.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is a sudden change or discovery that the reader did not expect.",
        ),
        QAItem(
            question="Why do fables often use animals?",
            answer="Fables often use animals so they can act like people and teach a lesson in a simple, memorable way.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill", challenge="climb", prize="star", name="Robin"),
    StoryParams(place="tree", challenge="climb", prize="bell", name="Milo"),
]


ASP_RULES = r"""
#show valid/3.
valid(P,C,R) :- place(P), challenge(C), prize(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c in CHALLENGES:
        lines.append(asp.fact("challenge", c))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CHALLENGES[params.challenge], PRIZES[params.prize], params.name)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
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
            header = f"### {p.name}: {p.challenge} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
