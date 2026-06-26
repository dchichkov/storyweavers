#!/usr/bin/env python3
"""
Space-adventure storyworld: a small crew, a shared mission, a warm bowl of consomme,
and the moment one tiny worry turns into a brave choice.

This world is built to produce child-facing stories with:
- Inner Monologue
- Repetition
- Flashback

Premise seed:
A young space traveler is on a ship or station, carrying a special bowl of consomme.
Something in the ship's routine creates tension: a spill, a missing spoon, a nervous
landing, or a lonely feeling. The traveler remembers a prior lesson, repeats a brave
phrase to themself, and finds a helpful action that resolves the problem.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass(frozen=True)
class Location:
    id: str
    label: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Challenge:
    id: str
    verb: str
    danger: str
    turn: str
    keyword: str
    mess: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Comfort:
    id: str
    label: str
    phrase: str
    fix: str
    covers: set[str]
    guards: set[str]
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    challenge: str
    comfort: str
    name: str
    role: str
    seed: Optional[int] = None


LOCATIONS = {
    "cabin": Location("cabin", "the ship's cabin", "soft and bright", {"spill", "drift"}),
    "galley": Location("galley", "the tiny galley", "warm and busy", {"spill"}),
    "dock": Location("dock", "the station dock", "wide and echoing", {"drift", "repair"}),
    "window": Location("window", "the starglass window", "quiet and silver", {"drift"}),
}

CHALLENGES = {
    "spill": Challenge(
        "spill",
        verb="eat the consomme while the ship was rocking",
        danger="the bowl could wobble and splash",
        turn="the soup wavered in the bowl",
        keyword="consomme",
        mess="broth",
        zone="hands",
        tags={"food", "soup", "spill", "consomme"},
    ),
    "drift": Challenge(
        "drift",
        verb="watch the stars from the open hatch",
        danger="a gust might tug the spoon away",
        turn="the spoon slid toward the floor",
        keyword="space",
        mess="scratch",
        zone="hands",
        tags={"space", "stars", "drift"},
    ),
    "repair": Challenge(
        "repair",
        verb="help fix the humming panel",
        danger="tiny sparks could frighten the crew",
        turn="the panel blinked and beeped",
        keyword="repair",
        mess="dust",
        zone="hands",
        tags={"repair", "tools", "ship"},
    ),
}

COMFORTS = {
    "bowl": Comfort(
        "bowl",
        label="a snug bowl lid",
        phrase="a snug bowl lid for the consomme",
        fix="cover the bowl so it would not slosh",
        covers={"hands"},
        guards={"broth"},
    ),
    "gloves": Comfort(
        "gloves",
        label="soft repair gloves",
        phrase="soft repair gloves",
        fix="hold the parts safely",
        covers={"hands"},
        guards={"dust", "scratch"},
    ),
    "strap": Comfort(
        "strap",
        label="a shoulder strap",
        phrase="a shoulder strap for the soup tray",
        fix="steady the tray against the rocking",
        covers={"hands"},
        guards={"broth"},
    ),
}

NAMES = ["Ari", "Mina", "Tess", "Niko", "Luna", "Kai", "Rin", "Sora"]
ROLES = ["cadet", "pilot", "helper", "messenger", "engineer"]


class World:
    def __init__(self, place: Location):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.state: dict[str, float] = {
            "fear": 0.0,
            "brave": 0.0,
            "relief": 0.0,
            "memory": 0.0,
            "repeat": 0.0,
        }

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def reasonableness_gate(challenge: Challenge, comfort: Comfort) -> bool:
    return challenge.mess in comfort.guards and challenge.zone in comfort.covers


def select_pair(rng: random.Random, args: argparse.Namespace) -> tuple[Location, Challenge, Comfort]:
    if args.challenge and args.comfort:
        ch = CHALLENGES[args.challenge]
        cf = COMFORTS[args.comfort]
        if not reasonableness_gate(ch, cf):
            raise StoryError("That comfort would not genuinely help with that space problem.")
    valid = []
    for place in LOCATIONS.values():
        for ch in CHALLENGES.values():
            if ch.id not in place.affords:
                continue
            for cf in COMFORTS.values():
                if reasonableness_gate(ch, cf):
                    valid.append((place, ch, cf))
    if args.place:
        valid = [t for t in valid if t[0].id == args.place]
    if args.challenge:
        valid = [t for t in valid if t[1].id == args.challenge]
    if args.comfort:
        valid = [t for t in valid if t[2].id == args.comfort]
    if not valid:
        raise StoryError("No valid story matches the given options.")
    return rng.choice(valid)


def flashback_line(hero: Entity) -> str:
    return (
        f"{hero.pronoun('subject').capitalize()} remembered a smaller day when "
        f"{hero.id} had been scared of a dark tunnel, and the captain had said, "
        f'"One step, then the next."'
    )


def inner_monologue(hero: Entity, phrase: str) -> str:
    return (
        f'"I can do this," {hero.id} thought. '
        f'"I can do this. I can do this," {hero.id} thought again.'
    )


def tell_story(place: Location, challenge: Challenge, comfort: Comfort, name: str, role: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type="child", label=role, meters={}, memes={}))
    captain = world.add(Entity(id="Captain", kind="character", type="adult", label="the captain"))
    bowl = world.add(Entity(id="consomme", type="food", label="consomme", phrase="a warm bowl of consomme"))
    bowl.owner = hero.id

    world.say(
        f"{hero.id} was a {role} on {place.label}. "
        f"{hero.pronoun('subject').capitalize()} loved the warm smell of consomme from the galley."
    )
    world.say(
        f"That evening, {hero.id} carried {hero.pronoun('possessive')} bowl and looked out at the stars. "
        f"{hero.pronoun('subject').capitalize()} wanted to {challenge.verb}, but {challenge.danger}."
    )

    world.state["fear"] += 1
    world.say(flashback_line(hero))
    world.state["memory"] += 1

    world.say(inner_monologue(hero, challenge.keyword))
    world.state["repeat"] += 2

    world.say(
        f"Then the ship lurched. {challenge.turn.capitalize()}, and the broth trembled near the rim."
    )
    world.state["fear"] += 1

    world.say(
        f"{hero.id} whispered the brave words again: 'Slow and steady, slow and steady.'"
    )
    world.state["repeat"] += 1
    world.state["brave"] += 1

    if comfort.id == "bowl":
        world.say(
            f"The captain smiled and handed over {comfort.phrase}. "
            f"It could {comfort.fix}, so the consomme stayed safe."
        )
    elif comfort.id == "strap":
        world.say(
            f"The captain clipped on {comfort.phrase}. It could {comfort.fix}, "
            f"so the bowl stayed steady as the stars bobbed by."
        )
    else:
        world.say(
            f"The captain gave {hero.id} {comfort.phrase}. It could {comfort.fix}, "
            f"and the tiny sparks no longer felt scary."
        )

    world.state["fear"] = 0
    world.state["relief"] += 2

    if challenge.id == "spill":
        world.say(
            f"At last, {hero.id} took a careful sip. The consomme stayed warm, and the ship felt calm again."
        )
    elif challenge.id == "drift":
        world.say(
            f"At last, {hero.id} watched the stars without losing the spoon. The quiet window seemed friendly now."
        )
    else:
        world.say(
            f"At last, {hero.id} helped finish the repair. The panel hummed softly, like a sleepy tune."
        )

    world.facts.update(
        hero=hero,
        captain=captain,
        bowl=bowl,
        place=place,
        challenge=challenge,
        comfort=comfort,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a young child that includes the word "consomme".',
        f"Tell a gentle story where {f['hero'].id} feels worried on {f['place'].label} but uses an inner thought and a repeated phrase to stay brave.",
        f"Write a story with a flashback, a repeated line, and a happy ending involving {f['challenge'].verb} and {f['comfort'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ch = f["challenge"]
    cf = f["comfort"]
    return [
        QAItem(
            question=f"Where was {hero.id} when the story began?",
            answer=f"{hero.id} was on {f['place'].label}, aboard a small ship or station with a warm galley nearby.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before feeling nervous?",
            answer=f"{hero.id} wanted to {ch.verb}. That sounded exciting, but it also felt a little risky.",
        ),
        QAItem(
            question=f"What did {hero.id} think to themself when the problem got hard?",
            answer=f"{hero.id} thought, 'I can do this,' and then repeated it again to feel braver.",
        ),
        QAItem(
            question="What old memory helped the hero stay calm?",
            answer="The hero remembered a smaller day when the captain had helped with a scary tunnel and said, 'One step, then the next.'",
        ),
        QAItem(
            question=f"How did {cf.label} help the hero?",
            answer=f"It helped by letting the hero {cf.fix}, which kept the consomme safe and the worry small.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is consomme?",
            answer="Consomme is a clear, tasty soup that people sip carefully, often served warm.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="Why do people repeat a brave phrase to themselves?",
            answer="People sometimes repeat a brave phrase to help their mind feel steady and calm.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the voice of a character's private thoughts inside their head.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for p in sample.prompts:
        parts.append(p)
    parts.append("")
    parts.append("== Story Q&A ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("")
    parts.append("== World Q&A ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"place={world.place.id}")
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} owner={e.owner}")
    lines.append(f"state={world.state}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with consomme, flashback, repetition, and inner monologue.")
    ap.add_argument("--place", choices=LOCATIONS.keys())
    ap.add_argument("--challenge", choices=CHALLENGES.keys())
    ap.add_argument("--comfort", choices=COMFORTS.keys())
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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
    place, ch, cf = select_pair(rng, args)
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    return StoryParams(place=place.id, challenge=ch.id, comfort=cf.id, name=name, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(LOCATIONS[params.place], CHALLENGES[params.challenge], COMFORTS[params.comfort], params.name, params.role)
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
    StoryParams(place="cabin", challenge="spill", comfort="bowl", name="Ari", role="cadet"),
    StoryParams(place="dock", challenge="repair", comfort="gloves", name="Mina", role="engineer"),
    StoryParams(place="window", challenge="drift", comfort="strap", name="Kai", role="pilot"),
]


ASP_RULES = r"""
place(P) :- setting(P).
challenge(C) :- problem(C).
comfort(F) :- aid(F).

valid(P,C,F) :- place(P), challenge(C), comfort(F), affords(P,C), helps(F,C), covers_zone(F,hands).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, p in LOCATIONS.items():
        lines.append(asp.fact("setting", pid))
        for c in sorted(p.affords):
            lines.append(asp.fact("affords", pid, c))
    for cid in CHALLENGES:
        lines.append(asp.fact("problem", cid))
    for fid, f in COMFORTS.items():
        lines.append(asp.fact("aid", fid))
        for m in sorted(f.guards):
            lines.append(asp.fact("helps", fid, m))
        for z in sorted(f.covers):
            lines.append(asp.fact("covers_zone", fid, z))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    got = sorted(set(asp.atoms(model, "valid")))
    py = sorted({
        (p.id, c.id, f.id)
        for p in LOCATIONS.values()
        for c in CHALLENGES.values()
        if c.id in p.affords
        for f in COMFORTS.values()
        if reasonableness_gate(c, f)
    })
    if got == py:
        print(f"OK: ASP gate matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP:", got)
    print("PY:", py)
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
