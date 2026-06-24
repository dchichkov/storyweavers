#!/usr/bin/env python3
"""
A standalone storyworld for a small pirate-tale domain with blue magic, a twist,
and a bad ending. The world is state-driven: treasure, tide, magic, trust, and
the final outcome all arise from simulated changes in meters and memes.
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


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    color: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "captain":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "mate":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    weather: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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
    hero_kind: str
    hero_name: str
    mate_name: str
    prize: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Prize:
    id: str
    label: str
    phrase: str
    risk: str
    holds_magic: bool = False
    blue_sensitive: bool = False


@dataclass(frozen=True)
class Setting:
    id: str
    label: str
    weather: str
    tide: str


@dataclass(frozen=True)
class Twist:
    id: str
    reveal: str
    consequence: str


SETTINGS = {
    "harbor": Setting("harbor", "the harbor", "windy", "high"),
    "reef": Setting("reef", "the reef", "misty", "low"),
    "cove": Setting("cove", "the cove", "calm", "rising"),
}

PRIZES = {
    "map": Prize("map", "map", "a folded map", "water", blue_sensitive=True),
    "key": Prize("key", "key", "a tiny brass key", "salt", holds_magic=True),
    "shell": Prize("shell", "shell", "a pearly shell", "magic", blue_sensitive=True),
}

TWISTS = {
    "blue_spell": Twist("blue_spell", "the blue glow was not a lamp at all", "it was a spell waking up"),
    "false_bottle": Twist("false_bottle", "the bottle was blue, but it held a trick note", "the note led them wrong"),
    "sleeping_wave": Twist("sleeping_wave", "the blue wave was sleeping magic", "it would not help the crew"),
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- harbor(S).
setting(S) :- reef(S).
setting(S) :- cove(S).

risk(P, water) :- prize(P), needs_water(P).
risk(P, salt) :- prize(P), needs_salt(P).
risk(P, magic) :- prize(P), blue_sensitive(P).

bad_ending(P, T) :- risk(P, _), twist(T), false_help(T).
blue_magic(P) :- prize(P), blue_sensitive(P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS.values():
        lines.append(asp.fact("setting", s.id))
        lines.append(asp.fact(s.id, s.id))
    for p in PRIZES.values():
        lines.append(asp.fact("prize", p.id))
        if p.holds_magic:
            lines.append(asp.fact("needs_magic", p.id))
        if p.blue_sensitive:
            lines.append(asp.fact("blue_sensitive", p.id))
        if p.risk == "water":
            lines.append(asp.fact("needs_water", p.id))
        elif p.risk == "salt":
            lines.append(asp.fact("needs_salt", p.id))
        elif p.risk == "magic":
            lines.append(asp.fact("needs_magic", p.id))
    for t in TWISTS.values():
        lines.append(asp.fact("twist", t.id))
        if t.id in {"false_bottle", "sleeping_wave"}:
            lines.append(asp.fact("false_help", t.id))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/2.\n#show blue_magic/1."))
    bad = set(asp.atoms(model, "bad_ending"))
    blue = set(asp.atoms(model, "blue_magic"))
    py_bad = {(p.id, t.id) for p in PRIZES.values() for t in TWISTS.values() if p.blue_sensitive and t.id in {"false_bottle", "sleeping_wave"}}
    py_blue = {(p.id,) for p in PRIZES.values() if p.blue_sensitive}
    if bad == py_bad and blue == py_blue:
        print(f"OK: ASP parity for {len(py_bad)} bad endings and {len(py_blue)} blue magic prizes.")
        return 0
    print("MISMATCH")
    print("bad only in asp:", sorted(bad - py_bad))
    print("bad only in py:", sorted(py_bad - bad))
    print("blue only in asp:", sorted(blue - py_blue))
    print("blue only in py:", sorted(py_blue - blue))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def reasonableness_gate(place: str, prize: Prize, twist: Twist) -> None:
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    if prize.blue_sensitive and twist.id == "false_bottle":
        return
    if prize.risk == "water" and place == "reef":
        return


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    prize = PRIZES[params.prize]
    twist = next(t for t in TWISTS.values() if t.id == params.prize_tie())
    world = World(place=setting.label, weather=setting.weather)
    captain = world.add(Entity(params.hero_name, kind="captain", label=params.hero_name, traits=["brave", "blue-eyed"]))
    mate = world.add(Entity(params.mate_name, kind="mate", label=params.mate_name, traits=["quick", "small"]))
    trinket = world.add(Entity("treasure", kind="thing", label=prize.label, phrase=prize.phrase, color="blue" if prize.blue_sensitive else "", owner=captain.id))
    magic = world.add(Entity("magic", kind="thing", label="blue magic", phrase="a blue shimmer", color="blue"))

    captain.add_meme("hope", 1)
    captain.add_meme("greed", 1)
    mate.add_meme("trust", 1)
    trinket.add_meter("safe", 1)
    magic.add_meter("glow", 1)
    if prize.blue_sensitive:
        magic.add_meme("temptation", 1)

    world.say(f"{captain.label} was a little pirate who loved the blue sea and bright treasure.")
    world.say(f"{captain.pronoun().capitalize()} kept {trinket.phrase} in a cloth bag and promised to share it with {mate.label}.")
    world.para()

    world.say(f"At {world.place}, the tide was {setting.tide}, and the air smelled like salt and rope.")
    world.say(f"{captain.label} wanted to use a bit of blue magic to make the treasure shine.")
    captain.add_meme("desire", 1)

    # magic helps at first
    if prize.blue_sensitive:
        trinket.add_meter("shine", 2)
        world.say("The blue glow curled around the treasure like a ribbon.")
    else:
        trinket.add_meter("shine", 1)
        world.say("The blue glow made the deck look kind and strange.")

    world.para()
    world.say(f"Then the twist came: {twist.reveal}, and {twist.consequence}.")
    captain.add_meme("shock", 1)
    mate.add_meme("worry", 1)

    # bad ending path
    if prize.blue_sensitive:
        trinket.add_meter("loss", 2)
        captain.add_meme("sorrow", 2)
        mate.add_meme("fear", 1)
        world.say(f"The glow slipped into the prize, and the {trinket.label} turned cold and dull.")
        world.say(f"{mate.label} reached out, but the magic had already washed the bright hope away.")
        world.say(f"In the end, the crew watched the blue light fade, and the treasure was not saved.")
    elif prize.risk == "water":
        trinket.add_meter("soak", 2)
        captain.add_meme("sorrow", 1)
        world.say(f"A wave slapped the {trinket.label} clean out of the bag, and the map grew soggy.")
        world.say("The crew tried to catch it, but the sea took the chance away.")
        world.say("By the last line, the map was ruined, and the pirate plan ended badly.")
    else:
        trinket.add_meter("fade", 1)
        world.say(f"The spell fizzled, and the little prize lost its spark.")
        world.say("Nobody found a clever fix before the dark clouds rolled in.")

    world.facts.update(
        captain=captain, mate=mate, prize=trinket, prize_def=prize, twist=twist,
        setting=setting, bad=True, blue=(prize.blue_sensitive)
    )
    return world

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

def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short pirate tale with blue magic, a twist, and a bad ending.',
        f'Write a child-friendly story about {world.facts["captain"].label}, a pirate at {world.place}, and a {world.facts["prize_def"].label} that goes wrong.',
        'Tell a small pirate story where blue magic seems helpful first, then turns into a mistake.',
    ]

def story_qa(world: World) -> list[QAItem]:
    c = world.facts["captain"]
    m = world.facts["mate"]
    p = world.facts["prize"]
    t = world.facts["twist"]
    qas = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {c.label}, a little pirate, and {m.label}, who sails with {c.label}.",
        ),
        QAItem(
            question=f"What did the blue magic do at first?",
            answer=f"The blue magic made {p.label} shine for a moment and look special.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {t.reveal}, so the magic did not help the crew in the end.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended badly: the treasure was lost or ruined, and the crew could not save it.",
        ),
    ]
    return qas

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate?",
            answer="A pirate is a person who sails on the sea and looks for treasure.",
        ),
        QAItem(
            question="Why can magic be tricky?",
            answer="Magic can be tricky because it may work in a surprising way and cause trouble instead of helping.",
        ),
        QAItem(
            question="What does blue usually make people think of?",
            answer="Blue usually makes people think of the sky, the sea, and things that feel cool and calm.",
        ),
    ]


# ---------------------------------------------------------------------------
# Parameter helpers and CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate-tale storyworld with blue magic and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
    ap.add_argument("--mate-name")
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
    place = args.place or rng.choice(list(SETTINGS))
    prize = args.prize or rng.choice(list(PRIZES))
    if place == "reef" and prize == "map":
        pass
    elif place == "harbor" and prize == "key":
        pass
    elif place == "cove" and prize == "shell":
        pass
    name = args.name or rng.choice(["Finn", "Mara", "Jett", "Nia"])
    mate_name = args.mate_name or rng.choice(["Bo", "Luna", "Tess", "Pip"])
    return StoryParams(place=place, hero_kind="captain", hero_name=name, mate_name=mate_name, prize=prize)

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))

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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)

CURATED = [
    StoryParams(place="harbor", hero_kind="captain", hero_name="Finn", mate_name="Bo", prize="map"),
    StoryParams(place="reef", hero_kind="captain", hero_name="Mara", mate_name="Pip", prize="shell"),
    StoryParams(place="cove", hero_kind="captain", hero_name="Jett", mate_name="Luna", prize="key"),
]

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show bad_ending/2.\n#show blue_magic/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show bad_ending/2.\n#show blue_magic/1."))
        print(asp.atoms(model, "bad_ending"))
        print(asp.atoms(model, "blue_magic"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
