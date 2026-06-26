#!/usr/bin/env python3
"""
storyworlds/worlds/born_ninety_repetition_cautionary_superhero_story.py
=======================================================================

A small superhero story world about a young hero, a repeated stunt, and a
careful grown-up warning that keeps everybody safe.

Seed image:
---
A kid superhero keeps trying the same flashy leap over and over because it
feels amazing. The more the stunt is repeated, the more the cape strains and
the rooftop gets risky. A mentor notices the pattern, warns about the danger,
and offers a safer practice way so the hero can still feel brave.

World model:
---
- Physical meters track flight charge, cape strain, and rooftop risk.
- Emotional memes track excitement, worry, and relief.
- Repetition is the core tension: the hero wants to do the same move again.
- The cautionary turn is a mentor who predicts the harm before it happens.
- Resolution is a safer training setup that lets the hero keep practicing
  without damaging the cape or endangering the city.

This file follows the storyworld contract:
- self-contained stdlib script
- typed entities with meters and memes
- generate/emit/main interface
- lazy ASP import via helper functions
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["charge", "strain", "risk", "safe_space", "boost"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "trust", "pride", "relief", "impatience"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_plural(self) -> bool:
        return self.plural


@dataclass
class City:
    place: str = "the bright city rooftop"
    loop_safe: bool = False
    windy: bool = True


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.history: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.repetition_count = 0
        self.training_setup = False

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
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        clone = World(self.city)
        clone.entities = copy.deepcopy(self.entities)
        clone.history = list(self.history)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.repetition_count = self.repetition_count
        clone.training_setup = self.training_setup
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
@dataclass
class HeroProfile:
    name: str
    gender: str
    trait: str
    born_note: str


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    makes_safe: bool = False


@dataclass
class Move:
    id: str
    verb: str
    gerund: str
    risk: str
    repeat_effect: str
    safe_practice: str
    tags: set[str] = field(default_factory=set)


CITY = City(place="the bright city rooftop", loop_safe=False, windy=True)

HEROES = [
    HeroProfile("Nova", "girl", "brave", "born with a tiny gold star stitched into her cape"),
    HeroProfile("Jet", "boy", "curious", "born on a stormy night with shiny boots"),
    HeroProfile("Sky", "girl", "spirited", "born to chase the tallest clouds"),
]

MOVES = {
    "roof-loop": Move(
        id="roof-loop",
        verb="leap off the roof and swoop back in a shining loop",
        gerund="looping through the air",
        risk="the cape can tug hard and twist in the wind",
        repeat_effect="the more times it is repeated, the more the cape strains",
        safe_practice="practice the same jump over soft mats instead of the roof edge",
        tags={"repetition", "cautionary", "superhero"},
    ),
    "beam-zoom": Move(
        id="beam-zoom",
        verb="zoom across the training beam",
        gerund="zooming across the beam",
        risk="the beam is narrow, so a hurried repeat can send a hero wobbling",
        repeat_effect="every extra lap makes the feet less steady",
        safe_practice="try the beam again with a safety line and a helper below",
        tags={"repetition", "cautionary", "superhero"},
    ),
}

GEAR = {
    "mat": Gear(
        id="mat",
        label="soft training mats",
        phrase="a stack of soft training mats",
        protects={"landing"},
        makes_safe=True,
    ),
    "line": Gear(
        id="line",
        label="a safety line",
        phrase="a safety line tied to the beam",
        protects={"balance"},
        makes_safe=True,
    ),
    "cape-clip": Gear(
        id="cape-clip",
        label="a cape clip",
        phrase="a snug cape clip",
        protects={"cape"},
        makes_safe=True,
    ),
}

TRAITS = ["brave", "curious", "spirited", "quick", "bright"]


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def choose_hero(rng: random.Random) -> HeroProfile:
    return rng.choice(HEROES)


def choose_move(rng: random.Random) -> Move:
    return rng.choice(list(MOVES.values()))


def choose_name(hero: HeroProfile, rng: random.Random) -> str:
    if hero.name:
        return hero.name
    return rng.choice(["Nova", "Jet", "Sky"])


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def story_pronoun(hero: Entity, case: str = "subject") -> str:
    return hero.pronoun(case)


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def warn_if_repeated(world: World, hero: Entity, move: Move) -> bool:
    if world.repetition_count < 2:
        return False
    if ("warn", move.id) in world.fired:
        return True
    world.fired.add(("warn", move.id))
    hero.memes["worry"] += 1
    hero.memes["trust"] += 1
    world.say(
        f"{hero.id}'s mentor watched the same stunt happen again and frowned. "
        f'"If you keep repeating it, {move.risk}," the mentor warned.'
    )
    return True


def do_move(world: World, hero: Entity, move: Move, safe: bool = False) -> None:
    world.repetition_count += 1
    hero.memes["joy"] += 1
    hero.meters["charge"] -= 1
    if safe:
        hero.meters["strain"] = max(0.0, hero.meters["strain"] - 0.5)
        hero.memes["relief"] += 1
        world.say(
            f"With the safety setup in place, {hero.id} tried it again and smiled. "
            f"{hero.pronoun().capitalize()} could practice {move.gerund} without the rooftop edge."
        )
        return

    hero.meters["strain"] += 1
    if world.repetition_count >= 2:
        hero.memes["impatience"] += 1
        world.say(
            f"{hero.id} did it once more, because the flash of the move felt too good to stop."
        )
    else:
        world.say(f"{hero.id} took a running start and did {move.verb}.")

    if hero.meters["strain"] >= 2 and ("strain", move.id) not in world.fired:
        world.fired.add(("strain", move.id))
        world.say(
            f"The cape tugged tight, and the wind gave it a rough shake."
        )


def set_scene(world: World, hero: Entity, move: Move) -> None:
    world.say(
        f"{hero.id} was {hero.facts['born_note'] if 'born_note' in hero.facts else 'born to be a hero'}."
    )


def build_setup(world: World, hero: Entity, move: Move) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} loved {move.gerund} above the city."
    )
    world.say(
        f"Every time {hero.id} landed, the rooftops below looked tiny and the clouds looked friendly."
    )


def offer_caution(world: World, mentor: Entity, hero: Entity, move: Move) -> None:
    hero.memes["worry"] += 1
    mentor.memes["trust"] += 1
    world.say(
        f"{mentor.id} pointed at the cape and said, "
        f'"That trick is exciting, but repeating it over and over is not safe."'
    )


def resolve_with_setup(world: World, hero: Entity, mentor: Entity, move: Move) -> None:
    world.training_setup = True
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"Then {mentor.id} brought out soft mats and a safety line."
    )
    world.say(
        f'{mentor.id} said, "You can still practice {move.gerund}, just do it the careful way."'
    )
    do_move(world, hero, move, safe=True)
    world.say(
        f"By the end, {hero.id} was grinning, the cape was steady, and the city below stayed safe."
    )


def tell_story(hero_prof: HeroProfile, move: Move) -> World:
    world = World(CITY)
    hero = world.add(Entity(id=hero_prof.name, kind="character", type=hero_prof.gender))
    mentor = world.add(Entity(id="Mentor", kind="character", type="woman", label="the mentor"))
    cape = world.add(Entity(
        id="cape",
        type="cape",
        label="cape",
        phrase="a bright red cape",
        owner=hero.id,
        caretaker=mentor.id,
    ))
    hero.facts = {"born_note": hero_prof.born_note}

    world.say(f"{hero.id} was {hero_prof.born_note}.")
    world.say(
        f"{hero.id} wore {article(cape.phrase)} {cape.phrase} and felt ready to save the day."
    )
    world.say(
        f"{hero.id} loved {move.gerund} because it made {hero.pronoun('possessive')} heart feel huge."
    )

    world.para()
    world.say(f"One windy afternoon, {hero.id} stood on {world.city.place} and looked at the open sky.")
    do_move(world, hero, move, safe=False)
    do_move(world, hero, move, safe=False)
    warn_if_repeated(world, hero, move)
    do_move(world, hero, move, safe=False)
    offer_caution(world, mentor, hero, move)

    world.para()
    resolve_with_setup(world, hero, mentor, move)

    world.facts.update(
        hero=hero,
        mentor=mentor,
        cape=cape,
        move=move,
        repetition_count=world.repetition_count,
        training_setup=world.training_setup,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    move = f["move"]
    return [
        f'Write a superhero story for a young child about {hero.id}, who keeps repeating one risky stunt and learns to choose the careful way.',
        f"Tell a cautionary superhero tale where {hero.id} wants to keep {move.gerund} but a mentor worries about the cape and offers a safer practice setup.",
        f'Write a simple heroic story that includes the word "born" and the number word "ninety" in a child-friendly way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mentor: Entity = f["mentor"]
    move: Move = f["move"]

    return [
        QAItem(
            question=f"Who is the superhero story about?",
            answer=f"It is about {hero.id}, a young superhero who loves {move.gerund} above the city.",
        ),
        QAItem(
            question=f"Why did {mentor.id} warn {hero.id}?",
            answer=(
                f"{mentor.id} warned {hero.id} because repeating the same stunt over and over could strain the cape and make the rooftop unsafe."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} learn to do instead?",
            answer=(
                f"{hero.id} learned to practice the same move with soft mats and a safety line, so the hero could keep training without danger."
            ),
        ),
        QAItem(
            question=f"How did the story show repetition?",
            answer=(
                f"{hero.id} tried the stunt several times in a row, and each repeat made the warning more important."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with {hero.id} smiling in a safer training setup, with the cape steady and the city still safe."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a safety line do?",
            answer="A safety line helps a person stay secure if they slip or wobble while practicing something tricky.",
        ),
        QAItem(
            question="What are soft training mats for?",
            answer="Soft training mats help make landings gentler during practice.",
        ),
        QAItem(
            question="What does the word ninety mean?",
            answer="Ninety is the number after eighty-nine and before ninety-one.",
        ),
        QAItem(
            question="What does born mean?",
            answer="Born means a baby has come into the world.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  repetition_count={world.repetition_count}")
    lines.append(f"  training_setup={world.training_setup}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A stunt becomes risky when it is repeated enough times.
repeated(stunt) :- repeat_count(N), N >= 2.

caution_needed(stunt) :- repeated(stunt), cape_strain(high).

safe_plan(stunt) :- safety(mat), safety(line).

story_ok(stunt) :- caution_needed(stunt), safe_plan(stunt).
"""

def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("repeat_count", 3),
        asp.fact("cape_strain", "high"),
        asp.fact("safety", "mat"),
        asp.fact("safety", "line"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        raise StoryError(f"ASP verification requested but clingo is unavailable: {exc}")

    model = asp.one_model(asp_program("#show story_ok/1."))
    atoms = asp.atoms(model, "story_ok")
    ok = any(a[0] == "stunt" for a in atoms)
    if ok:
        print("OK: ASP twin finds the story reasonable.")
        return 0
    print("MISMATCH: ASP twin did not confirm the story.")
    return 1


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    name: str
    gender: str
    trait: str
    move: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero storyworld about repetition, caution, and a safer way to practice."
    )
    ap.add_argument("--name", choices=[h.name for h in HEROES])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--move", choices=list(MOVES))
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
    hero = None
    if args.name:
        hero = next((h for h in HEROES if h.name == args.name), None)
        if hero is None:
            raise StoryError("Unknown hero name.")
    else:
        hero = choose_hero(rng)

    gender = args.gender or hero.gender
    trait = args.trait or rng.choice(TRAITS)
    move = args.move or choose_move(rng).id
    return StoryParams(name=hero.name, gender=gender, trait=trait, move=move)


def generate(params: StoryParams) -> StorySample:
    hero_prof = next(h for h in HEROES if h.name == params.name)
    move = MOVES[params.move]
    world = tell_story(hero_prof, move)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


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
        print(asp_program("#show story_ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show story_ok/1."))
        print("ASP story_ok atoms:", asp.atoms(model, "story_ok"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for hero in HEROES:
            for move_id in MOVES:
                params = StoryParams(name=hero.name, gender=hero.gender, trait=hero.trait, move=move_id)
                samples.append(generate(params))
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
            header = f"### {p.name}: {p.move}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
