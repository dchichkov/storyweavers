#!/usr/bin/env python3
"""
Standalone storyworld: glorious epee exclusion magic repetition moral value.

A small Adventure-style world in which a young hero wants to join a blade
ceremony, gets excluded at first, and must solve the problem through repeated
practice, a little magic, and a moral choice about sharing the glory.
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

@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    excluded: bool = False
    has_epee: bool = False
    enchanted: bool = False
    practiced_times: int = 0
    allies: list[str] = field(default_factory=list)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def setm(self, key: str, value: float) -> None:
        self.meters[key] = value

    def mem(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def setmem(self, key: str, value: float) -> None:
        self.memes[key] = value


@dataclass
class World:
    place: str
    hero: Person
    mentor: Person
    rival: Person
    epee_name: str
    magic_word: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    name: str
    seed: Optional[int] = None


PLACES = {
    "castle_yard": "the castle yard",
    "river_port": "the river port",
    "moon_gate": "the moon gate",
    "orchard_fort": "the orchard fort",
}

HERO_NAMES = ["Lina", "Milo", "Nia", "Tarin", "Elio", "Sera", "Jori", "Pia"]
MENTOR_NAMES = ["Master Vale", "Captain Brin", "Aunt Sol", "Old Rook"]
RIVAL_NAMES = ["Rook", "Bram", "Cira", "Dune"]

EPEE_NAMES = [
    "the glorious epee",
    "the silver epee",
    "the bright epee",
    "the star epee",
]

MAGIC_WORDS = [
    "lumen",
    "harbor",
    "soar",
    "ward",
]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_places() -> list[str]:
    return list(PLACES)


def is_reasonable(place: str) -> bool:
    return place in PLACES


def explain_invalid(place: str) -> str:
    return f"(No story: the place {place!r} is not a valid adventure setting for this world.)"


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def intro(world: World) -> None:
    world.say(
        f"{world.hero.name} lived near {world.place}, where banners snapped in the wind and old stone felt ready for a quest."
    )
    world.say(
        f"Every day, {world.hero.name} watched fighters in bright cloaks polish {world.epee_name} until it shone like a star."
    )
    world.facts["glorious"] = True


def exclusion(world: World) -> None:
    world.para()
    world.hero.excluded = True
    world.hero.setmem("hurt", 1.0)
    world.hero.setmem("want", 1.0)
    world.say(
        f"When the blade-keepers lined up the training ring, {world.hero.name} stepped forward, but the rival shook their head and said, 'Not today.'"
    )
    world.say(
        f"{world.hero.name} was left outside the ring, staring at {world.epee_name}, feeling small beside the loud cheers."
    )
    world.facts["excluded"] = True


def first_try(world: World) -> None:
    world.para()
    world.hero.practiced_times += 1
    world.hero.setmem("resolve", world.hero.mem("resolve") + 1.0)
    world.say(
        f"Still, {world.hero.name} did not run away. Instead, {world.hero.name} practiced a careful step, then another, repeating the motion again and again."
    )
    world.say(
        f"Each repetition made the stance steadier, but the gate still stayed shut."
    )


def magic_turn(world: World) -> None:
    world.para()
    world.hero.setmem("hope", world.hero.mem("hope") + 1.0)
    world.hero.setmem("skill", world.hero.m("skill") + 1.0)
    world.hero.enchanted = True
    world.say(
        f"Then {world.mentor.name} came close and whispered the magic word '{world.magic_word}'."
    )
    world.say(
        f"The air hummed, and a silver spark danced around {world.epee_name}, making the blade lighter in {world.hero.name}'s hands."
    )


def more_repetition(world: World) -> None:
    world.para()
    for _ in range(2):
        world.hero.practiced_times += 1
        world.hero.setmem("skill", world.hero.m("skill") + 1.0)
    world.say(
        f"{world.hero.name} practiced the same safe salute, the same footwork, and the same breath until the moves felt like a song."
    )
    world.say(
        f"That repetition turned clumsy hope into real skill."
    )


def moral_choice(world: World) -> None:
    world.para()
    world.hero.setmem("moral_value", world.hero.m("moral_value") + 1.0)
    world.hero.excluded = False
    world.hero.has_epee = True
    world.hero.allies.append(world.rival.name)
    world.rival.allies.append(world.hero.name)
    world.say(
        f"At last, {world.hero.name} reached the ring, but instead of boasting, {world.hero.name} offered to show the waiting children the easy steps first."
    )
    world.say(
        f"The rival frowned, then saw the good in that choice and lifted the rope so everyone could enter together."
    )
    world.say(
        f"{world.hero.name} took up {world.epee_name} at last, but the brightest part of the day was not the blade. It was the way the whole ring opened to the others."
    )
    world.facts["moral_value"] = True


def tell_story(params: StoryParams) -> World:
    hero = Person(name=params.name, role="young adventurer")
    mentor = Person(name=random.choice(MENTOR_NAMES), role="mentor")
    rival = Person(name=random.choice(RIVAL_NAMES), role="gatekeeper")
    world = World(
        place=PLACES[params.place],
        hero=hero,
        mentor=mentor,
        rival=rival,
        epee_name=random.choice(EPEE_NAMES),
        magic_word=random.choice(MAGIC_WORDS),
    )
    world.facts.update(place=params.place, name=params.name)
    intro(world)
    exclusion(world)
    first_try(world)
    magic_turn(world)
    more_repetition(world)
    moral_choice(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        f'Write an Adventure-style story about a child named {world.hero.name} and {world.epee_name}, using the word "exclusion".',
        f"Tell a short tale where {world.hero.name} is left out at {world.place}, but repeated practice and magic help {world.hero.name} grow wiser.",
        f'Create a child-friendly adventure with a glowing sword, a kind mentor, and a moral choice about who gets to enter the ring.',
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"Why did {world.hero.name} feel sad at first?",
            answer=f"{world.hero.name} felt sad because the rival excluded {world.hero.name} from the training ring and the glorious epee was being used without {world.hero.name}.",
        ),
        QAItem(
            question=f"What helped {world.hero.name} get better?",
            answer=f"Repeated practice helped {world.hero.name} get better, and then {world.mentor.name} used the magic word '{world.magic_word}' to give the epee a shining boost.",
        ),
        QAItem(
            question=f"What was the moral choice in the end?",
            answer=f"{world.hero.name} chose to share the steps and welcome the waiting children instead of keeping the glory alone, which showed kindness and fairness.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an epee?",
            answer="An epee is a kind of fencing sword with a slender blade, often used in careful, skillful duels or training.",
        ),
        QAItem(
            question="What does repetition help with?",
            answer="Repetition helps a person learn because doing the same safe action again and again makes it easier to remember and do well.",
        ),
        QAItem(
            question="What does moral value mean?",
            answer="Moral value means choosing what is fair, kind, and honest, especially when it would be easier to be selfish.",
        ),
        QAItem(
            question="What is exclusion?",
            answer="Exclusion is when someone is left out and not allowed to join a group or activity.",
        ),
        QAItem(
            question="What does magic mean in stories?",
            answer="Magic in stories is a wondrous force that can change how things feel, move, or shine in ways ordinary life cannot.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for p in [world.hero, world.mentor, world.rival]:
        lines.append(
            f"{p.name}: meters={dict(p.meters)} memes={dict(p.memes)} excluded={p.excluded} has_epee={p.has_epee} enchanted={p.enchanted} practiced={p.practiced_times} allies={p.allies}"
        )
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(castle_yard).
place(river_port).
place(moon_gate).
place(orchard_fort).

glorious_epee(epee).
feature(magic).
feature(repetition).
feature(moral_value).

valid_story(P) :- place(P).

% A story is reasonable if it includes:
% 1) a glorious epee
% 2) an exclusion beat
% 3) magic
% 4) repetition
% 5) a moral-value resolution
contains_glorious_epee(valid).
contains_exclusion(valid).
contains_magic(valid).
contains_repetition(valid).
contains_moral_value(valid).

good(valid) :- valid_story(_),
               contains_glorious_epee(valid),
               contains_exclusion(valid),
               contains_magic(valid),
               contains_repetition(valid),
               contains_moral_value(valid).

#show good/1.
#show valid_story/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        lines.append(asp.fact("valid_story", p))
    lines.append(asp.fact("glorious_epee", "epee"))
    lines.append(asp.fact("feature", "magic"))
    lines.append(asp.fact("feature", "repetition"))
    lines.append(asp.fact("feature", "moral_value"))
    lines.append(asp.fact("contains_glorious_epee", "valid"))
    lines.append(asp.fact("contains_exclusion", "valid"))
    lines.append(asp.fact("contains_magic", "valid"))
    lines.append(asp.fact("contains_repetition", "valid"))
    lines.append(asp.fact("contains_moral_value", "valid"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/1.\n#show good/1.")
    model = asp.one_model(program)
    valids = set(asp.atoms(model, "valid_story"))
    goods = set(asp.atoms(model, "good"))
    python_valids = {(p,) for p in valid_places()}
    if valids != python_valids:
        print("MISMATCH: ASP valid_story set does not match Python registry.")
        print("ASP:", sorted(valids))
        print("PY :", sorted(python_valids))
        return 1
    if goods != {("valid",)}:
        print("MISMATCH: ASP good/1 missing.")
        print("ASP:", sorted(goods))
        return 1
    sample = generate(StoryParams(place=valid_places()[0], name="Test", seed=1))
    if not sample.story or "exclusion" not in sample.story.lower():
        print("MISMATCH: generated story failed basic content check.")
        return 1
    print(f"OK: ASP parity verified for {len(valids)} places; story generation exercised.")
    return 0


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(valid_places())
    if not is_reasonable(place):
        raise StoryError(explain_invalid(place))
    name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(place=place, name=name)


def generate(params: StoryParams) -> StorySample:
    if not is_reasonable(params.place):
        raise StoryError(explain_invalid(params.place))
    seed = params.seed if params.seed is not None else 0
    rng = random.Random(seed)
    world = tell_story(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="castle_yard", name="Lina"),
    StoryParams(place="river_port", name="Milo"),
    StoryParams(place="moon_gate", name="Nia"),
    StoryParams(place="orchard_fort", name="Tarin"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with glorious epee, exclusion, magic, repetition, and moral value.")
    ap.add_argument("--place", choices=valid_places())
    ap.add_argument("--name", choices=HERO_NAMES)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1.\n#show good/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1.\n#show good/1."))
        print(f"{len(set(asp.atoms(model, 'valid_story')))} valid places")
        for t in sorted(set(asp.atoms(model, "valid_story"))):
            print(" ", t[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, p in enumerate(CURATED):
            p.seed = base_seed + i
            samples.append(generate(p))
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
