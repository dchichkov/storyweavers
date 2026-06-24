#!/usr/bin/env python3
"""
Storyworld: Pirate Tale with Reconciliation and a Lesson Learned

A small, self-contained story simulator about a young pirate crew, a tempting win,
a quarrel on deck, and a reconciliation that teaches the lesson.

The seed premise:
- A pirate wants to win a challenge.
- A mistake causes conflict with a crewmate or captain.
- The characters reconcile and learn a lesson about sharing, patience, or honesty.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "daughter", "captainess", "pirate-girl"}
        male = {"boy", "man", "father", "son", "captain", "pirate-boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    sea: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    goal: str
    attempt: str
    hazard: str
    turn: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "harbor": Setting(place="the harbor", sea="the blue sea", affords={"race", "search"}),
    "island": Setting(place="a small island", sea="the bright sea", affords={"search", "race"}),
    "cove": Setting(place="a hidden cove", sea="the dark sea", affords={"search"}),
}

CHALLENGES = {
    "race": Challenge(
        id="race",
        goal="win the race to the cove",
        attempt="sail as fast as they could",
        hazard="a sudden snag in the sail line",
        turn="slow down and ask for help",
        lesson="winning is sweeter when the crew works together",
        tags={"win", "simulator", "ship"},
    ),
    "search": Challenge(
        id="search",
        goal="find the missing lantern",
        attempt="follow the glittering clues",
        hazard="a false clue that could cause a quarrel",
        turn="tell the truth before the guess grew worse",
        lesson="honesty keeps the crew from drifting apart",
        tags={"lesson", "reconciliation", "map"},
    ),
}

PRIZES = {
    "flag": Prize(label="flag", phrase="a bright victory flag", region="mast"),
    "lantern": Prize(label="lantern", phrase="a little brass lantern", region="deck"),
    "shell": Prize(label="shell", phrase="a shiny pearl shell", region="hand"),
}

HERO_NAMES = ["Milo", "Jory", "Nina", "Pip", "Tessa", "Rafe", "Luna", "Sailor Jo"]
CREWMATE_NAMES = ["Captain Brine", "Mara", "Old Hook", "Bell", "Fin", "Wren"]
TRAITS = ["brave", "restless", "curious", "quick", "stubborn", "cheerful"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
challenge(C) :- goal(C,_).
setting(S) :- place(S,_).
prize(P) :- label(P,_).

wants_win(C) :- tag(C,win).
needs_reconciliation(C) :- tag(C,reconciliation).
learns_lesson(C) :- tag(C,lesson).

valid_story(S, C, P) :- setting(S), challenge(C), prize(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_id", sid))
        lines.append(asp.fact("place", sid, s.place))
        lines.append(asp.fact("sea", sid, s.sea))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("goal", cid, c.goal))
        lines.append(asp.fact("attempt", cid, c.attempt))
        lines.append(asp.fact("hazard", cid, c.hazard))
        lines.append(asp.fact("turn", cid, c.turn))
        lines.append(asp.fact("lesson", cid, c.lesson))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("label", pid, p.label))
        lines.append(asp.fact("region", pid, p.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, challenge in CHALLENGES.items():
            if cid not in setting.affords:
                continue
            for pid in PRIZES:
                combos.append((sid, cid, pid))
    return combos


def explain_rejection(setting: str, challenge: str, prize: str) -> str:
    return (
        f"(No story: {challenge} is not supported at {setting} with prize {prize}. "
        f"Try a combination listed by the simulator.)"
    )


# ---------------------------------------------------------------------------
# Story synthesis
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    challenge: str
    prize: str
    hero: str
    hero_type: str
    mate: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story simulator with reconciliation and lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"], dest="hero_type")
    ap.add_argument("--mate")
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.challenge is None or c[1] == args.challenge)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, challenge, prize = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    hero = args.hero or rng.choice(HERO_NAMES)
    mate = args.mate or rng.choice(CREWMATE_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, challenge=challenge, prize=prize, hero=hero, hero_type=hero_type, mate=mate, trait=trait)


def _intro(world: World, hero: Entity, mate: Entity, prize: Entity, challenge: Challenge) -> None:
    world.say(
        f"On {world.setting.place}, {hero.id} was a {hero.trait_desc()} pirate who loved a good {challenge.id}."
    )
    world.say(
        f"{hero.id} kept {prize.pronoun('possessive')} {prize.label} close and dreamed about a win."
    )
    world.say(
        f"Beside {hero.pronoun('object')}, {mate.id} watched the deck and listened for the sea breeze."
    )


def _problem(world: World, hero: Entity, mate: Entity, challenge: Challenge, prize: Entity) -> None:
    hero.memes["want_win"] = 1
    world.para()
    world.say(
        f"One day, {hero.id} tried to {challenge.attempt}, but {challenge.hazard} made the plan wobble."
    )
    world.say(
        f"{hero.id} wanted to fix it alone, and that made {mate.id} feel left out."
    )
    mate.memes["hurt"] = 1
    hero.memes["rush"] = 1
    world.say(
        f"When {hero.id} blamed the delay on {mate.id}, the two pirates fell into a sharp argument."
    )


def _turn(world: World, hero: Entity, mate: Entity, challenge: Challenge, prize: Entity) -> None:
    world.para()
    hero.memes["guilt"] = 1
    mate.memes["distance"] = 1
    world.say(
        f"Then {hero.id} looked at the {prize.label} and noticed how lonely the deck felt."
    )
    world.say(
        f"{hero.id} lowered {hero.pronoun('possessive')} voice and said sorry to {mate.id}."
    )
    mate.memes["soften"] = 1
    world.say(
        f"{mate.id} nodded, and the two pirates worked out a calmer way to handle the {challenge.id}."
    )
    world.say(
        f"They chose to {challenge.turn}, because a true crew sails better together."
    )


def _resolution(world: World, hero: Entity, mate: Entity, challenge: Challenge, prize: Entity) -> None:
    world.para()
    hero.memes["joy"] = 1
    mate.memes["joy"] = 1
    hero.memes["reconciled"] = 1
    mate.memes["reconciled"] = 1
    world.say(
        f"With both pirates pulling together, the ship moved steady, and the challenge turned into a win."
    )
    world.say(
        f"{hero.id} and {mate.id} shared a grin, because the best prize was not just the {prize.label}, but their peace again."
    )
    world.say(
        f"By sunset, {world.setting.place} glowed gold, and {challenge.lesson}."
    )


def _do_story(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, traits=[params.trait], label=params.hero))
    hero.trait_desc = lambda h=hero: f"{h.traits[0]} and bright-eyed"
    mate = world.add(Entity(id=params.mate, kind="character", type="pirate", traits=["steadfast"], label=params.mate))
    prize_cfg = PRIZES[params.prize]
    prize = world.add(Entity(id="prize", kind="thing", type=prize_cfg.label, label=prize_cfg.label, phrase=prize_cfg.phrase))
    challenge = CHALLENGES[params.challenge]

    _intro(world, hero, mate, prize, challenge)
    _problem(world, hero, mate, challenge, prize)
    _turn(world, hero, mate, challenge, prize)
    _resolution(world, hero, mate, challenge, prize)

    world.facts.update(hero=hero, mate=mate, prize=prize, challenge=challenge, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short pirate story where {f['hero'].id} tries to {f['challenge'].attempt} and learns a lesson.",
        f"Tell a child-friendly tale about a pirate win, a quarrel, and a reconciliation at {f['setting'].place}.",
        f"Write a simple story that includes a ship, a mistake, and friends making up again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    prize = f["prize"]
    challenge = f["challenge"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who wanted to win the {challenge.id} on the pirate ship?",
            answer=f"{hero.id} wanted to win, even before the quarrel started.",
        ),
        QAItem(
            question=f"What caused trouble when {hero.id} tried to handle the {challenge.id} alone?",
            answer=f"{challenge.hazard.capitalize()} caused trouble and made the plan wobble.",
        ),
        QAItem(
            question=f"How did {hero.id} and {mate.id} fix their argument?",
            answer="They apologized, talked it out, and chose a calmer way to work together.",
        ),
        QAItem(
            question=f"What was the lesson learned at {setting.place}?",
            answer=f"The lesson was that {challenge.lesson}.",
        ),
        QAItem(
            question=f"What did the pirates care about besides the {prize.label}?",
            answer="They cared about staying friends and keeping the crew together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat used by pirates to sail the sea and carry their crew.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making up after an argument and becoming friendly again.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a good idea that someone understands after what happened.",
        ),
        QAItem(
            question="What does it mean to win?",
            answer="To win means to do well in a contest or challenge and come out ahead.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _do_story(params)
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
    StoryParams(setting="harbor", challenge="race", prize="flag", hero="Milo", hero_type="boy", mate="Captain Brine", trait="brave"),
    StoryParams(setting="island", challenge="search", prize="lantern", hero="Nina", hero_type="girl", mate="Mara", trait="curious"),
    StoryParams(setting="cove", challenge="search", prize="shell", hero="Pip", hero_type="boy", mate="Old Hook", trait="stubborn"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
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
            header = f"### {p.hero}: {p.challenge} at {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
