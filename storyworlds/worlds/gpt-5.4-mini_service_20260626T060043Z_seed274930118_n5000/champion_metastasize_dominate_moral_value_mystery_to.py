#!/usr/bin/env python3
"""
A pirate-tale story world about a young champion, a mysterious map, and the
choice to share the treasure instead of trying to dominate the crew.

The simulated premise:
- A child aboard a small pirate ship is praised as a champion for being brave.
- The crew finds a strange clue that may solve a mystery.
- A selfish urge can metastasize into greedy behavior if the child starts
  ordering everyone around.
- The moral value is whether the child uses courage to help the crew or uses it
  to dominate them.
- A bad ending is possible when the child chooses greed over fairness.

The generated stories are state-driven and can end in either a warm resolution
or a bad ending, depending on the sampled parameters.
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


@dataclass
class Crewmate:
    id: str
    kind: str = "character"
    role: str = "crew"
    name: str = ""
    brave: float = 0.0
    greedy: float = 0.0
    kindness: float = 0.0
    dominance: float = 0.0
    wonder: float = 0.0
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Clue:
    id: str
    label: str
    place: str
    reveals: str
    risky: bool = False


@dataclass
class Setting:
    ship: str
    sea: str
    dock: str


@dataclass
class StoryParams:
    ship: str
    clue: str
    turn: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Crewmate] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Crewmate) -> Crewmate:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Crewmate:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


THRESHOLD = 1.0


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class Rule:
    name: str
    apply: callable


def _r_misrule_spreads(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes.get("dominance", 0.0) < THRESHOLD:
        return out
    if hero.memes.get("greed", 0.0) < THRESHOLD:
        return out
    sig = ("misrule",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["bad_ending"] = True
    out.append("The more the child barked orders, the more the crew frowned and the good mood sank.")
    return out


def _r_moral_value(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if world.facts.get("shared") and world.facts.get("mystery_solved") and ("moral",) not in world.fired:
        world.fired.add(("moral",))
        hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
        out.append("That choice showed the crew that a champion can be fair as well as brave.")
    return out


RULES = [
    Rule("misrule_spreads", _r_misrule_spreads),
    Rule("moral_value", _r_moral_value),
]


SETTINGS = {
    "sloop": Setting(ship="the Lucky Sloop", sea="the blue sea", dock="a windy dock"),
    "brig": Setting(ship="the Little Brig", sea="the green sea", dock="a busy dock"),
    "cutter": Setting(ship="the Moon Cutter", sea="the silver sea", dock="a quiet dock"),
}

CLUES = {
    "shell": Clue(id="shell", label="a silver shell", place="the deck", reveals="the tide points to a hidden cove"),
    "lantern": Clue(id="lantern", label="a cracked lantern", place="the mast", reveals="someone searched at night"),
    "rope": Clue(id="rope", label="a frayed rope", place="the rail", reveals="the boat brushed a secret rock"),
}

TURN_TYPES = ["share", "dominate"]

NAMES = ["Mina", "Kai", "Jules", "Pip", "Ari", "Nia", "Finn", "Tess"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world: a champion, a mystery, and a moral choice.")
    ap.add_argument("--ship", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--turn", choices=TURN_TYPES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    ship = args.ship or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    turn = args.turn or rng.choice(TURN_TYPES)
    name = args.name or rng.choice(NAMES)
    return StoryParams(ship=ship, clue=clue, turn=turn, name=name)


def _make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.ship]
    world = World(setting)
    hero = world.add(Crewmate(id="hero", role="champion", name=params.name))
    captain = world.add(Crewmate(id="captain", role="captain", name="Captain Reef"))
    clue = CLUES[params.clue]
    world.facts.update(hero=hero, captain=captain, clue=clue, params=params)

    hero.memes["brave"] = 1
    hero.meters["pride"] = 1

    world.say(f"On {setting.ship}, {params.name} was the crew's little champion, quick with a grin and brave with a lantern.")
    world.say(f"One morning, the crew found {clue.label} on {clue.place}, and everyone wondered what it meant.")
    world.say(f"It looked like the start of a mystery to solve, because {clue.reveals}.")
    world.para()

    hero.memes["wonder"] = 1
    world.say(f"{params.name} leaned close to the clue and said, 'I can solve this!'")
    if params.turn == "dominate":
        hero.memes["dominance"] = 1
        hero.memes["greed"] = 1
        world.say(f"But soon {params.name} began to dominate the crew, pointing with a tiny finger and ordering the sailors about.")
        world.say("The selfish feeling seemed to metastasize, growing bigger each time the child demanded more praise and more treasure.")
        world.facts["shared"] = False
        propagate(world)
        world.para()
        world.say(f"At sunset, the mystery was solved, but the answer led only to a hidden chest that {params.name} tried to keep.")
        world.say("The crew turned away. Their cheers were gone, and the champion's big pride left a bad ending in the salt air.")
        world.facts["mystery_solved"] = True
        world.facts["bad_ending"] = True
    else:
        hero.memes["kindness"] = 1
        world.say(f"Instead of trying to dominate anyone, {params.name} asked the crew to search together.")
        world.say("The clue helped them find the missing chart, and the mystery to solve became a team game.")
        world.facts["shared"] = True
        world.facts["mystery_solved"] = True
        propagate(world)
        world.para()
        world.say(f"By nightfall, {params.name} shared the shiny find with everyone, and the champion's brave heart stayed gentle.")
        world.say("The sea kept glittering, and the crew sailed on with a moral value they would remember.")

    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    clue = world.facts["clue"]
    return [
        f"Write a short pirate tale for a child named {p.name} who is a champion and finds {clue.label}.",
        f"Tell a story where a mystery to solve leads a young pirate to choose between sharing and trying to dominate the crew.",
        f"Write a gentle pirate story with the words champion, metastasize, and dominate, ending in a moral choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    clue = world.facts["clue"]
    hero = world.facts["hero"]
    qa = [
        QAItem(
            question=f"Who was the champion in the story?",
            answer=f"The champion was {p.name}, the child sailor on {world.setting.ship}.",
        ),
        QAItem(
            question=f"What was the mystery to solve?",
            answer=f"The crew needed to understand {clue.label}, which pointed toward {clue.reveals}.",
        ),
        QAItem(
            question=f"Did {p.name} try to share with the crew or dominate them?",
            answer="They chose to share with the crew." if world.facts.get("shared") else "They tried to dominate the crew.",
        ),
    ]
    if world.facts.get("bad_ending"):
        qa.append(
            QAItem(
                question="Why did the story end badly?",
                answer="It ended badly because the child let greed and dominance grow bigger than kindness, so the crew stopped trusting them.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="What moral value did the story show?",
                answer="It showed that real courage also means being fair, listening, and sharing the credit.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a champion?",
            answer="A champion is someone who wins, helps, or stands out as the best at something brave or skillful.",
        ),
        QAItem(
            question="What does metastasize mean?",
            answer="Metastasize means to spread and grow into a bigger problem, like trouble that keeps getting worse.",
        ),
        QAItem(
            question="What does it mean to dominate?",
            answer="To dominate means to control others too much and not let them take part fairly.",
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
        lines.append(f"  {e.id:8} ({e.role:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for (n,) in world.fired)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("ship", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for t in TURN_TYPES:
        lines.append(asp.fact("turn", t))
    lines.append(asp.fact("word", "champion"))
    lines.append(asp.fact("word", "metastasize"))
    lines.append(asp.fact("word", "dominate"))
    return "\n".join(lines)


ASP_RULES = r"""
{ choose_turn(share); choose_turn(dominate) } = 1.
story_ok(S,C,share) :- ship(S), clue(C), choose_turn(share).
story_ok(S,C,dominate) :- ship(S), clue(C), choose_turn(dominate).
#show story_ok/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_story_set() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    py = {(s, c, t) for s in SETTINGS for c in CLUES for t in TURN_TYPES}
    cl = set(asp_story_set())
    if cl != py:
        print("MISMATCH between ASP and Python story-space gates.")
        print("only in ASP:", sorted(cl - py))
        print("only in Python:", sorted(py - cl))
        return 1
    print(f"OK: ASP matches Python over {len(py)} story combinations.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
    StoryParams(ship="sloop", clue="shell", turn="share", name="Mina"),
    StoryParams(ship="brig", clue="lantern", turn="dominate", name="Kai"),
    StoryParams(ship="cutter", clue="rope", turn="share", name="Pip"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/3."))
        print(f"{len(set(asp.atoms(model, 'story_ok')))} compatible story combinations.")
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
            header = f"### {p.name}: {p.ship} / {p.clue} / {p.turn}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
