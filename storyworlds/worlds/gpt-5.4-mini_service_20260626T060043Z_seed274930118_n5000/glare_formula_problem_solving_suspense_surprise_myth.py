#!/usr/bin/env python3
"""
A small mythic storyworld about a blinding glare, a missing formula, and a
problem-solution journey with suspense and surprise.

The source tale imagined here:
- A young apprentice in a sunlit shrine loses an old formula tablet.
- A glare from the river mirror makes the symbols impossible to read.
- The apprentice searches the temple rooms, solves the puzzle of the missing
  line, and discovers the formula was hiding in a reflection.
- The ending turns on a mythic surprise: the glare itself reveals the answer.
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
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Shrine:
    place: str
    name: str
    glare_source: str
    rooms: list[str]


@dataclass
class Relic:
    label: str
    phrase: str
    region: str
    plural: bool = False
    sacred: bool = True


@dataclass
class Formula:
    label: str
    phrase: str
    hidden_in: str
    needs_glare: bool = False


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    mentor_type: str
    relic: str
    formula: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, shrine: Shrine) -> None:
        self.shrine = shrine
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SHRINES = {
    "river_shrine": Shrine(
        place="the river shrine",
        name="the river shrine",
        glare_source="the bright water",
        rooms=["courtyard", "archive", "sanctum"],
    ),
    "sun_temple": Shrine(
        place="the sun temple",
        name="the sun temple",
        glare_source="the polished golden doors",
        rooms=["courtyard", "lattice room", "inner hall"],
    ),
    "cliff_cave": Shrine(
        place="the cliff cave",
        name="the cliff cave",
        glare_source="the sea-glass pool",
        rooms=["mouth", "shadow hall", "hidden chamber"],
    ),
}

RELICS = {
    "torch": Relic(label="torch", phrase="a bronze torch", region="hand"),
    "seal": Relic(label="seal", phrase="a carved stone seal", region="hand"),
    "cup": Relic(label="cup", phrase="a silver cup", region="hand"),
}

FORMULAS = {
    "light_formula": Formula(
        label="formula",
        phrase="an ancient formula for safe light",
        hidden_in="reflection",
        needs_glare=True,
    ),
    "rain_formula": Formula(
        label="formula",
        phrase="a wet-season formula for calm waters",
        hidden_in="tablet groove",
        needs_glare=False,
    ),
    "hearth_formula": Formula(
        label="formula",
        phrase="a hearth formula for steady flame",
        hidden_in="ash box",
        needs_glare=False,
    ),
}

HERO_NAMES = ["Ari", "Mira", "Niko", "Lina", "Sorin", "Tala"]
TRAITS = ["brave", "curious", "patient", "earnest", "gentle", "clever"]


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------
def build_story(params: StoryParams) -> StorySample:
    shrine = SHRINES[params.place]
    world = World(shrine)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    mentor = world.add(Entity(id="mentor", kind="character", type=params.mentor_type, label="the elder"))
    relic_cfg = RELICS[params.relic]
    formula_cfg = FORMULAS[params.formula]

    relic = world.add(Entity(
        id="relic",
        type="relic",
        label=relic_cfg.label,
        phrase=relic_cfg.phrase,
        owner=hero.id,
        caretaker=mentor.id,
    ))
    formula = world.add(Entity(
        id="formula",
        type="formula",
        label=formula_cfg.label,
        phrase=formula_cfg.phrase,
        owner=mentor.id,
        caretaker=mentor.id,
    ))

    world.facts.update(hero=hero, mentor=mentor, relic=relic, formula=formula, shrine=shrine)

    # Act I
    trait = params.hero_type
    world.say(f"Long ago, {hero.id} was a {random.choice(TRAITS)} {trait} at {shrine.name}.")
    world.say(f"{hero.id} guarded {hero.pronoun('possessive')} {relic.label} and listened when the elder spoke of {formula.phrase}.")
    world.say(f"The old teachers said the {formula.label} could only be read when the signs were clear and true.")

    # Act II
    world.para()
    world.say(f"One morning, {hero.id} carried the relic into the shrine, but a fierce glare fell across the stones from {shrine.glare_source}.")
    world.say(f"The light made the carvings flash and vanish again, and the {formula.label} could not be seen.")
    world.say(f"{hero.id} grew worried, because the path to the answer was now hidden in bright sight.")

    world.say(f"The elder sent {hero.id} through the courtyard, the archive, and the {shrine.rooms[-1]}, one room at a time.")
    world.say(f"In each place, {hero.id} solved a small puzzle: a moved bowl, a turned mirror, a tilted shield.")
    world.say(f"Every clue said the same thing in a different way: look where the glare lands, not where it hurts.")

    # Act III surprise resolution
    world.para()
    world.say(f"At last {hero.id} lifted the relic and caught the glare in its polished side.")
    if formula_cfg.needs_glare:
        world.say(f"Then, surprise: the reflected light drew the missing letters of the {formula.label} onto the wall, and the answer was there all along.")
    else:
        world.say(f"Then, surprise: the glare revealed a hidden mark that pointed straight to the {formula.label}, tucked where no one thought to look.")

    world.say(f"{hero.id} copied the {formula.label} with steady hands, and the shrine grew calm again.")
    world.say(f"That night the elder smiled, for the problem was solved, the suspense had ended, and the bright glare had become a helper instead of a threat.")

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    shrine = f["shrine"]
    formula = f["formula"]
    return [
        f"Write a mythic short story about {hero.id} at {shrine.name} where a glaring light hides a {formula.label}.",
        f"Tell a child-friendly legend in which a brave seeker solves a temple puzzle and finds a missing formula.",
        f"Write a story with suspense and surprise about a bright glare, an old shrine, and a secret formula.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    relic = f["relic"]
    formula = f["formula"]
    shrine = f["shrine"]

    return [
        QAItem(
            question=f"Who was the story about at {shrine.name}?",
            answer=f"The story was about {hero.id}, a {hero.type} who lived and learned at {shrine.name}.",
        ),
        QAItem(
            question=f"What problem made it hard to read the {formula.label}?",
            answer=f"A fierce glare from {shrine.glare_source} flashed across the stones and hid the symbols.",
        ),
        QAItem(
            question=f"What did {hero.id} carry while searching for the answer?",
            answer=f"{hero.id} carried {hero.pronoun('possessive')} {relic.label} and kept looking for the hidden clue.",
        ),
        QAItem(
            question=f"Who helped guide {hero.id}?",
            answer=f"The elder, {mentor.id}, gave hints and taught {hero.id} to look for the light in a new way.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{hero.id} found the formula by using the glare as a clue, solved the problem, and brought calm back to the shrine.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is glare?",
            answer="Glare is a very bright shine that can make it hard to see things clearly.",
        ),
        QAItem(
            question="What is a formula?",
            answer="A formula is a special set of words or signs that helps someone do something the right way.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next before the answer is revealed.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is an unexpected moment that changes what the reader thought would happen.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A shrine story is valid when it includes a glare source, a missing formula,
% and a resolution that uses the glare as part of the solution.
valid_story(Place, Relic, Formula) :-
    shrine(Place), relic(Relic), formula(Formula),
    has_glare(Place), formula_uses_glare(Formula).

problem(Place, Formula) :-
    valid_story(Place, _, Formula).

suspense(Place) :- problem(Place, _).
surprise(Formula) :- formula_uses_glare(Formula).

#show valid_story/3.
#show problem/2.
#show suspense/1.
#show surprise/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, shrine in SHRINES.items():
        lines.append(asp.fact("shrine", sid))
        lines.append(asp.fact("has_glare", sid))
    for rid in RELICS:
        lines.append(asp.fact("relic", rid))
    for fid, form in FORMULAS.items():
        lines.append(asp.fact("formula", fid))
        if form.needs_glare:
            lines.append(asp.fact("formula_uses_glare", fid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set((s.name, tuple(str(a) for a in s.arguments)) for s in model)
    needed = {
        ("valid_story", ("river_shrine", "torch", "light_formula")) or None
    }
    if any(a[0] == "valid_story" for a in atoms):
        print("OK: ASP produced a valid story model.")
        return 0
    print("MISMATCH: ASP did not produce the expected valid_story atoms.")
    return 1


# ---------------------------------------------------------------------------
# Parameter handling
# ---------------------------------------------------------------------------
@dataclass
class StoryChoice:
    place: str
    hero_name: str
    hero_type: str
    mentor_type: str
    relic: str
    formula: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld of glare and formula.")
    ap.add_argument("--place", choices=sorted(SHRINES))
    ap.add_argument("--relic", choices=sorted(RELICS))
    ap.add_argument("--formula", choices=sorted(FORMULAS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["apprentice", "priestess", "scribe", "child"])
    ap.add_argument("--mentor-type", choices=["elder", "priest", "wise woman", "oracle"])
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
    place = args.place or rng.choice(list(SHRINES))
    relic = args.relic or rng.choice(list(RELICS))
    formula = args.formula or "light_formula"

    if formula == "light_formula" and place not in {"river_shrine", "sun_temple", "cliff_cave"}:
        raise StoryError("The light formula needs a place where glare can reveal hidden writing.")

    hero_type = args.hero_type or rng.choice(["apprentice", "priestess", "scribe", "child"])
    mentor_type = args.mentor_type or rng.choice(["elder", "priest", "wise woman", "oracle"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)

    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        mentor_type=mentor_type,
        relic=relic,
        formula=formula,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def validate_combo(params: StoryParams) -> None:
    if params.formula == "light_formula" and params.place not in {"river_shrine", "sun_temple", "cliff_cave"}:
        raise StoryError("No mythic glare path exists for that place and formula.")
    if params.relic not in RELICS or params.formula not in FORMULAS:
        raise StoryError("Unknown relic or formula.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("\n".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = []
        for place in SHRINES:
            for relic in RELICS:
                params = StoryParams(
                    place=place,
                    hero_name=HERO_NAMES[0],
                    hero_type="apprentice",
                    mentor_type="elder",
                    relic=relic,
                    formula="light_formula",
                    seed=base_seed,
                )
                validate_combo(params)
                samples.append(generate(params))
    else:
        samples = []
        for i in range(max(1, args.n)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            validate_combo(params)
            samples.append(generate(params))

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
