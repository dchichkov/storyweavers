#!/usr/bin/env python3
"""
storyworlds/worlds/plankton_acrobatics_friendship_dialogue_twist_mystery.py
===========================================================================

A tiny mystery storyworld about underwater friends, suspicious glowing plankton,
and a careful acrobatics solution that reveals the truth.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fish", "girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Reef:
    place: str = "the coral reef"
    dark: bool = True
    current: str = "gentle"


@dataclass
class Suspect:
    id: str
    label: str
    clue: str
    harmless: bool
    rumor: str


@dataclass
class Tool:
    id: str
    label: str
    action: str
    helps: str
    reveal: str
    safe: bool = True


class World:
    def __init__(self, reef: Reef) -> None:
        self.reef = reef
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
    friend: str
    hero_name: str
    suspect: str
    tool: str
    seed: Optional[int] = None


REEF = Reef()

HEROES = ["Mina", "Nori", "Cora", "Pip", "Luma", "Tia"]
FRIENDS = ["Bree", "Kiko", "Mara", "Toto", "Suri", "Jae"]

SUSPECTS = {
    "glow_plankton": Suspect(
        id="glow_plankton",
        label="glowing plankton",
        clue="tiny blue sparks",
        harmless=True,
        rumor="a strange little light was hiding in the water",
    ),
    "drift_shell": Suspect(
        id="drift_shell",
        label="a drifting shell",
        clue="a pale curve in the dark",
        harmless=True,
        rumor="something white kept sliding past the rocks",
    ),
    "shadow_knot": Suspect(
        id="shadow_knot",
        label="a shadowy knot of seaweed",
        clue="a wiggly dark shape",
        harmless=True,
        rumor="a dark shape was twisting near the reef",
    ),
}

TOOLS = {
    "spin": Tool(
        id="spin",
        label="a spinning loop",
        action="flip and spin through the water",
        helps="turns the eyes to every corner",
        reveal="circle of light",
    ),
    "flip": Tool(
        id="flip",
        label="a quick flip",
        action="do a quick flip above the coral",
        helps="moves the body over the hiding place",
        reveal="sparkling trail",
    ),
    "dive": Tool(
        id="dive",
        label="a careful dive",
        action="dive down between the rocks",
        helps="brings the friends close to the clue",
        reveal="hidden nook",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery storyworld: plankton, acrobatics, friendship, and a twist."
    )
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--hero-name", choices=HEROES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--tool", choices=TOOLS)
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
    combos = []
    for sus in SUSPECTS:
        for tool in TOOLS:
            combos.append((sus, tool))
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    tool = args.tool or rng.choice(sorted(TOOLS))
    hero_name = args.hero_name or rng.choice(HEROES)
    friend = args.friend or rng.choice(FRIENDS)
    return StoryParams(friend=friend, hero_name=hero_name, suspect=suspect, tool=tool)


def generate(params: StoryParams) -> StorySample:
    world = World(REEF)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="fish"))
    friend = world.add(Entity(id=params.friend, kind="character", type="fish"))
    suspect = SUSPECTS[params.suspect]
    tool = TOOLS[params.tool]

    hero.memes["curiosity"] = 1
    hero.memes["worry"] = 0
    friend.memes["trust"] = 1
    friend.memes["friendship"] = 1

    world.say(
        f"{hero.id} and {friend.id} were best friends at {world.reef.place}, where the water was dark and quiet."
    )
    world.say(
        f"One night, {hero.id} noticed {suspect.rumor}."
    )
    world.para()
    world.say(
        f'"Do you see that?" {hero.id} whispered. "It looks like {suspect.label}."'
    )
    world.say(
        f'"Maybe," {friend.id} said, "but let us look together before we guess."'
    )

    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1
    friend.memes["trust"] += 1
    world.para()
    world.say(
        f"To search the reef, {hero.id} used {tool.label} and chose to {tool.action}."
    )
    world.say(
        f"The move was a little acrobatic, but it {tool.helps}."
    )

    if suspect.id == "glow_plankton":
        world.facts["twist"] = "glow_plankton"
        world.say(
            f"Then the mystery turned: the blue glow was not a monster at all."
        )
        world.say(
            f"It was a swirl of {suspect.label}, shining like tiny stars."
        )
        world.say(
            f'{friend.id} laughed softly. "We worried for nothing."'
        )
        world.say(
            f'{hero.id} smiled back. "No, we found a bright surprise together."'
        )
    elif suspect.id == "drift_shell":
        world.facts["twist"] = "drift_shell"
        world.say(
            f"The twist came when {hero.id} flipped above the coral and saw a small shell turning in the current."
        )
        world.say(
            f'{friend.id} said, "That is only {suspect.label}."'
        )
        world.say(
            f"{they_together(hero, friend)} watched it drift by, safe and quiet."
        )
    else:
        world.facts["twist"] = "shadow_knot"
        world.say(
            f"When they dove closer, the shadow broke apart into a harmless tangle of seaweed."
        )
        world.say(
            f'"It was only {suspect.label}," {friend.id} said, and both friends grinned in relief.'
        )

    world.para()
    world.say(
        f"In the end, the reef felt friendly again, and the friends swam home side by side."
    )
    world.say(
        f"The little mystery had become a happy story about trust, teamwork, and a bright underwater surprise."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        suspect=suspect,
        tool=tool,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def they_together(hero: Entity, friend: Entity) -> str:
    return f"{hero.id} and {friend.id}"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for young children about {f["hero"].id} and {f["friend"].id} looking for {f["suspect"].label}.',
        f'Include dialogue, friendship, and a small acrobatic move that helps solve the mystery of the glowing water.',
        f'Write a child-friendly underwater story that uses the word "plankton" and ends with a twist.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    suspect: Suspect = f["suspect"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The story was about {hero.id} and {friend.id}, who were best friends at the reef.",
        ),
        QAItem(
            question=f"What did {hero.id} think the strange light might be?",
            answer=f"{hero.id} thought it might be {suspect.label}.",
        ),
        QAItem(
            question=f"What acrobatic move helped the friends look more closely?",
            answer=f"They used {tool.label}, which let {hero.id} {tool.action}.",
        ),
        QAItem(
            question=f"What was the twist in the mystery?",
            answer=f"The twist was that the strange light was actually {suspect.label}, not something scary.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is plankton?",
            answer="Plankton are tiny living things that float in the water and can glow or drift in big groups.",
        ),
        QAItem(
            question="What are acrobatics?",
            answer="Acrobatics are strong, careful moves like flips, spins, and turns that need balance and practice.",
        ),
        QAItem(
            question="Why do friends talk to each other when something seems strange?",
            answer="Friends talk so they can share clues, calm worries, and solve problems together.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle where something seems hidden or odd, and you look for clues to learn the truth.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
kind(character).
kind(thing).

twist(glow_plankton).
twist(drift_shell).
twist(shadow_knot).

mystery(T) :- twist(T).
friendship(hero, friend).
dialogue(hero, friend).
acrobatic(spin).
acrobatic(flip).
acrobatic(dive).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in sorted(SUSPECTS):
        lines.append(asp.fact("suspect", s))
    for t in sorted(TOOLS):
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show mystery/1."))
    if asp.atoms(model, "mystery"):
        print("OK: ASP twin emits mystery facts.")
        return 0
    print("MISMATCH: no mystery facts from ASP.")
    return 1


CURATED = [
    StoryParams(friend="Bree", hero_name="Mina", suspect="glow_plankton", tool="spin"),
    StoryParams(friend="Kiko", hero_name="Nori", suspect="drift_shell", tool="flip"),
    StoryParams(friend="Mara", hero_name="Cora", suspect="shadow_knot", tool="dive"),
]


def resolve_restrictions(args: argparse.Namespace) -> None:
    if args.suspect and args.tool and args.suspect == "shadow_knot" and args.tool == "spin":
        raise StoryError("That combination is too weak for the mystery twist; try a different acrobatic move.")


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
        print(asp_program("#show mystery/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show twist/1."))
        print("\n".join(str(a) for a in model))
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
            resolve_restrictions(args)
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
