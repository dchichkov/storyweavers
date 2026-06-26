#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/personify_favorite_heed_problem_solving_dialogue_kindness.py
===============================================================================================================================

A small pirate-tale story world about a shipmate's favorite treasure, a warning
to heed, and a problem solved through dialogue and kindness.
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
    wears: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captainess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "captain"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "it"


@dataclass
class Harbor:
    place: str = "the harbor"
    docks: bool = True
    affords: set[str] = field(default_factory=lambda: {"storm", "lost_map", "bent_compass"})


@dataclass
class Trouble:
    id: str
    name: str
    danger: str
    verb: str
    result: str
    signs: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    kind: str
    risk: str
    holders: set[str] = field(default_factory=lambda: {"pirate", "captain", "crew"})


@dataclass
class Aid:
    id: str
    label: str
    verb: str
    tail: str
    helps: set[str]
    covers: set[str]


class World:
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
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
        import copy
        c = World(self.harbor)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _warned(world: World, actor: Entity) -> bool:
    return actor.memes.get("warned", 0.0) >= THRESHOLD


def _troubled(world: World, actor: Entity) -> bool:
    return actor.meters.get("trouble", 0.0) >= THRESHOLD


def _r_spread(world: World) -> list[str]:
    out = []
    crew = world.get("Crew")
    trouble = world.facts["trouble"]
    prize = world.facts["prize"]
    if crew.meters.get(trouble.id, 0.0) < THRESHOLD:
        return out
    if prize.meters.get("safe", 0.0) >= THRESHOLD:
        return out
    sig = ("spread", trouble.id, prize.id)
    if sig not in world.facts.setdefault("fired", set()):
        world.facts["fired"].add(sig)
        prize.meters["risk"] = 1.0
        out.append(f"The {trouble.name} nipped at {prize.label}.")
    return out


def _r_kindest(world: World) -> list[str]:
    out = []
    if world.facts.get("kindness_done"):
        return out
    crew = world.get("Crew")
    mate = world.facts["hero"]
    if crew.memes.get("kindness", 0.0) >= THRESHOLD and crew.memes.get("dialogue", 0.0) >= THRESHOLD:
        world.facts["kindness_done"] = True
        mate.meters["safe"] = 1.0
        out.append("The kind words settled the worry like a calm wind.")
    return out


RULES = [
    _r_spread,
    _r_kindest,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


HARBOURS = {
    "harbor": Harbor(place="the harbor", docks=True),
    "deck": Harbor(place="the deck", docks=True),
    "cove": Harbor(place="the cove", docks=False),
}

TROUBLES = {
    "storm": Trouble(
        id="storm",
        name="storm",
        danger="rough",
        verb="blow in",
        result="splashing the deck",
        signs={"wind", "waves"},
        tags={"storm", "weather"},
    ),
    "lost_map": Trouble(
        id="lost_map",
        name="lost map",
        danger="torn",
        verb="go missing",
        result="leaving the crew adrift",
        signs={"paper", "ink"},
        tags={"map", "problem"},
    ),
    "bent_compass": Trouble(
        id="bent_compass",
        name="bent compass",
        danger="crooked",
        verb="point wrong",
        result="sending the ship the wrong way",
        signs={"needle", "spin"},
        tags={"compass", "problem"},
    ),
}

PRIZES = {
    "lantern": Prize(
        id="lantern",
        label="lantern",
        phrase="a little brass lantern",
        kind="lantern",
        risk="go dark",
    ),
    "shell": Prize(
        id="shell",
        label="shell",
        phrase="a shiny sea shell",
        kind="shell",
        risk="get lost",
    ),
    "flag": Prize(
        id="flag",
        label="flag",
        phrase="a bright red flag",
        kind="flag",
        risk="blow away",
    ),
}

AIDS = {
    "parrot": Aid(
        id="parrot",
        label="a parrot friend",
        verb="repeat the plan",
        tail="and the parrot cried the plan again",
        helps={"storm", "lost_map", "bent_compass"},
        covers={"dialogue"},
    ),
    "rope": Aid(
        id="rope",
        label="a strong rope",
        verb="tie things down",
        tail="and the rope kept the prize snug and safe",
        helps={"storm", "flag"},
        covers={"kindness"},
    ),
    "chart": Aid(
        id="chart",
        label="a clean chart",
        verb="draw a new path",
        tail="and the new chart showed a gentler way",
        helps={"lost_map", "bent_compass"},
        covers={"problem_solving"},
    ),
}

NAMES = ["Mara", "Finn", "Ivy", "Jory", "Pip", "Tess", "Nell", "Bo"]
PIRATE_TYPES = ["pirate", "captain", "mate", "deckhand"]
TRAITS = ["brave", "cheerful", "clever", "spry", "steady"]


@dataclass
class StoryParams:
    harbor: str
    trouble: str
    prize: str
    name: str
    role: str
    trait: str
    seed: Optional[int] = None


def choose_aid(trouble: Trouble, prize: Prize) -> Optional[Aid]:
    for aid in AIDS.values():
        if trouble.id in aid.helps:
            return aid
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for h in HARBOURS:
        for t in TROUBLES.values():
            for p in PRIZES.values():
                if choose_aid(t, p):
                    combos.append((h, t.id, p.id))
    return combos


def tell(harbor: Harbor, trouble: Trouble, prize: Prize, name: str, role: str, trait: str) -> World:
    world = World(harbor)
    hero = world.add(Entity(id=name, kind="character", type=role, label=name))
    crew = world.add(Entity(id="Crew", kind="character", type="crew", label="the crew"))
    prize_ent = world.add(Entity(id="Prize", kind="thing", type=prize.kind, label=prize.label, phrase=prize.phrase, owner=hero.id))
    trouble_ent = world.add(Entity(id="Trouble", kind="thing", type=trouble.id, label=trouble.name))

    world.facts.update(hero=hero, crew=crew, prize=prize_ent, trouble=trouble_ent, trouble_cfg=trouble, prize_cfg=prize, aid=None)

    world.say(f"{hero.id} was a {trait} little {role} who could almost hear the sea telling stories.")
    world.say(f"{hero.pronoun().capitalize()} loved {prize.phrase} and kept it close as a favorite treasure.")
    world.say(f"One day at {harbor.place}, a {trouble.name} came along and tried to {trouble.verb}.")

    world.para()
    world.say(f"{hero.id} saw the trouble and tried to heed the warning before the ship got hurt.")
    crew.meters[trouble.id] = 1.0
    crew.memes["warned"] = 1.0
    prize_ent.meters["safe"] = 0.0

    world.say(f'"We need to fix this," {hero.id} said, and the crew gathered round to talk.')
    crew.memes["dialogue"] = 1.0
    crew.memes["kindness"] = 1.0
    world.say(f"{hero.id} spoke kindly, and the others listened instead of grumbling.")

    world.para()
    aid = choose_aid(trouble, prize)
    world.facts["aid"] = aid
    if aid is None:
        raise StoryError("No reasonable aid exists for this trouble and prize.")
    world.say(f"They chose {aid.label} to {aid.verb}.")
    if aid.id == "parrot":
        world.say(f"The parrot friend squawked the plan back so everyone could follow it.")
    elif aid.id == "rope":
        world.say(f"The rope was tied fast, so the wind could not snatch the treasure away.")
    elif aid.id == "chart":
        world.say(f"They spread the clean chart flat and drew a safer course with careful paws and fingers.")
    world.say(f"At last, {aid.tail}, and the {trouble.name} did not win the day.")

    prize_ent.meters["safe"] = 1.0
    propagate(world, narrate=True)
    world.say(f"By sunset, {hero.id} smiled beside the {prize.label}, safe again and shining like a story worth telling.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child about a favorite {f["prize_cfg"].label} and a warning that must be heeded.',
        f"Tell a gentle shipboard story where {f['hero'].id} solves a {f['trouble_cfg'].name} with dialogue and kindness.",
        f'Write a short story with the words "personify", "favorite", and "heed" in a pirate setting.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    trouble = f["trouble_cfg"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"What was {hero.id}'s favorite thing in the story?",
            answer=f"{hero.id}'s favorite thing was {prize.label}, described as {prize.phrase}.",
        ),
        QAItem(
            question=f"What warning did {hero.id} try to heed?",
            answer=f"{hero.id} tried to heed the warning that the {trouble.name} could cause trouble if no one acted in time.",
        ),
        QAItem(
            question=f"How did the crew solve the problem?",
            answer=f"They solved it by talking kindly, listening to one another, and using {aid.label} to fix the problem together.",
        ),
        QAItem(
            question=f"Why did the ending feel happy?",
            answer=f"It felt happy because the trouble was handled, the favorite {prize.label} stayed safe, and everyone worked together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to heed a warning?",
            answer="To heed a warning means to listen carefully and act on it before something gets worse.",
        ),
        QAItem(
            question="What is a favorite thing?",
            answer="A favorite thing is something a person likes the most or likes very much.",
        ),
        QAItem(
            question="What is a kind way to solve a problem?",
            answer="A kind way to solve a problem is to talk calmly, listen, and help instead of fighting.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(harbor="harbor", trouble="storm", prize="flag", name="Mara", role="captain", trait="brave"),
    StoryParams(harbor="deck", trouble="lost_map", prize="lantern", name="Finn", role="pirate", trait="clever"),
    StoryParams(harbor="cove", trouble="bent_compass", prize="shell", name="Tess", role="mate", trait="cheerful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with favorite things, heeding warnings, and kind problem solving.")
    ap.add_argument("--harbor", choices=HARBOURS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=PIRATE_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.harbor is None or c[0] == args.harbor)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid pirate tale matches the given options.)")
    h, t, p = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(PIRATE_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(harbor=h, trouble=t, prize=p, name=name, role=role, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(HARBOURS[params.harbor], TROUBLES[params.trouble], PRIZES[params.prize], params.name, params.role, params.trait)
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
prize_at_risk(T, P) :- trouble(T), prize(P), needs_fix(T, P).
compatible(T, P, A) :- trouble(T), prize(P), aid(A), helps(A, T).
valid_story(H, T, P) :- harbor(H), trouble(T), prize(P), prize_at_risk(T, P), compatible(T, P, _).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for h in HARBOURS:
        lines.append(asp.fact("harbor", h))
    for t in TROUBLES.values():
        lines.append(asp.fact("trouble", t.id))
        lines.append(asp.fact("needs_fix", t.id, "x"))
    for p in PRIZES.values():
        lines.append(asp.fact("prize", p.id))
    for a in AIDS.values():
        lines.append(asp.fact("aid", a.id))
        for x in sorted(a.helps):
            lines.append(asp.fact("helps", a.id, x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
            header = f"### {p.name}: {p.trouble} at {p.harbor} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
