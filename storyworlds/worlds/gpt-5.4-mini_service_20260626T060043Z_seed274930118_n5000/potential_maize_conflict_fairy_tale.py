#!/usr/bin/env python3
"""
storyworlds/worlds/potential_maize_conflict_fairy_tale.py
==========================================================

A small fairy-tale story world about maize, promise, and conflict.

Premise:
- A child or helper tends a young maize patch in a tiny kingdom.
- The patch has "potential" to become tall, gold, and full of kernels.
- A conflict arises when someone tries to rush harvest or take the best ears too soon.
- A careful compromise or act of protection lets the maize reach its promise.

The world is intentionally small and constraint-checked: the story only
generates when the chosen conflict can be resolved in a believable way.

The prose engine is fully stdlib; clingo is only imported if ASP modes are used.
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
    kind: str = "thing"  # "character" | "thing"
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
        female = {"girl", "queen", "fairy", "witch", "mother", "mom"}
        male = {"boy", "king", "wizard", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the castle garden"
    affords: set[str] = field(default_factory=set)


@dataclass
class Crop:
    id: str
    label: str
    phrase: str
    growth: str
    promise: str
    risk: str
    ripened: str
    season: str
    keyword: str = "maize"


@dataclass
class ConflictTool:
    id: str
    label: str
    verb: str
    effect: str
    good_end: str
    bad_end: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "garden": Setting(place="the castle garden", affords={"watch", "water", "harvest"}),
    "field": Setting(place="the golden field", affords={"watch", "water", "harvest"}),
    "courtyard": Setting(place="the sunny courtyard", affords={"watch", "water"}),
}

CROPS = {
    "maize": Crop(
        id="maize",
        label="maize",
        phrase="a small row of maize",
        growth="growing taller each day",
        promise="full of potential",
        risk="too early to harvest",
        ripened="golden and sweet",
        season="late summer",
        keyword="maize",
    ),
}

CONFLICTS = {
    "crow": ConflictTool(
        id="crow",
        label="a crow",
        verb="peck at the young ears",
        effect="stole the sweet kernels before they were ready",
        good_end="a shiny ribbon and a scarecrow",
        bad_end="a ruined row of stalks",
    ),
    "prince": ConflictTool(
        id="prince",
        label="a prince",
        verb="pick the best ears early",
        effect="wanted to carry off the harvest before the maize had ripened",
        good_end="a shared basket and a patient promise",
        bad_end="crumbled kernels and a sad garden",
    ),
    "storm": ConflictTool(
        id="storm",
        label="a storm wind",
        verb="flatten the tall stalks",
        effect="bent the stems and scared the leaves",
        good_end="a careful tying of the stalks",
        bad_end="broken leaves and muddy roots",
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Elin", "Sage", "Tessa", "Nora"]
BOY_NAMES = ["Robin", "Pip", "Theo", "Finn", "Owen", "Ari"]
HELPER_NAMES = ["Nell", "Penny", "Bram", "Ivo", "June", "Wren"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    conflict: str
    name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helper text
# ---------------------------------------------------------------------------

def _hero_phrase(hero: Entity) -> str:
    article = "a" if hero.type[0] not in "aeiou" else "an"
    return f"{article} little {hero.type}"


def _season_line(crop: Crop) -> str:
    return f"It was {crop.season}, the sort of time when {crop.label} could dream of becoming {crop.ripened}."


def _resolve_conflict(tool: ConflictTool) -> str:
    if tool.id == "crow":
        return "They tied up a bright ribbon and set a small scarecrow by the row."
    if tool.id == "prince":
        return "They filled a basket with ripe apples instead and promised to wait for the maize."
    return "They tied the stalks with soft twine and waited for the wind to pass."
   

# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def tell(setting: Setting, crop: Crop, conflict: ConflictTool, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type))
    maize = world.add(Entity(
        id="maize",
        type="maize",
        label="maize",
        phrase=crop.phrase,
        caretaker=hero.id,
    ))

    maize.meters["growth"] = 1.0
    maize.meters["potential"] = 1.0
    hero.memes["hope"] = 1.0
    hero.memes["care"] = 1.0

    world.say(f"{hero.id} lived beside {setting.place} and loved the little maize there.")
    world.say(f"{hero.pronoun().capitalize()} said the maize had great potential, even while it was still small.")
    world.say(f"{_season_line(crop)}")

    world.para()
    world.say(f"Each morning, {hero.id} and {helper.id} went to {setting.place} to water the rows and pull up weeds.")
    world.say(f"The maize kept {crop.growth}, and its leaves grew brighter and steadier in the sun.")

    world.para()
    if conflict.id == "crow":
        world.say("Then one morning, a crow hopped onto the fence and eyed the tender ears.")
        world.say(f"It tried to {conflict.verb}, which meant it could {conflict.effect}.")
    elif conflict.id == "prince":
        world.say("Then one morning, a prince came striding into the garden with a gold glove and a greedy smile.")
        world.say(f"He wanted to {conflict.verb}, which meant he {conflict.effect}.")
    else:
        world.say("Then the sky grew dark, and a storm wind rushed over the garden.")
        world.say(f"It wanted to {conflict.verb}, which meant it might {conflict.effect}.")

    world.say(f"{hero.id} felt a tight little conflict in {hero.pronoun('possessive')} chest.")
    world.say("The maize was not ready yet, and hurrying it now would spoil the fairy tale ending.")

    world.para()
    world.say(f"{helper.id} came close and said, 'Not yet. Let the maize keep its promise.'")
    world.say(_resolve_conflict(conflict))
    world.say(f"Together they stayed with the row until the trouble passed.")

    world.para()
    maize.meters["growth"] = 2.0
    maize.meters["ripe"] = 1.0
    hero.memes["hope"] += 1.0
    hero.memes["peace"] = 1.0
    world.say(f"In time, the maize became {crop.ripened}, and the whole row stood straight and proud.")
    world.say(f"{hero.id} smiled because the maize had reached its full potential without being rushed.")
    world.say(f"By the end, {setting.place} looked like a tiny kingdom keeping a very patient treasure.")

    world.facts.update(
        hero=hero,
        helper=helper,
        maize=maize,
        crop=crop,
        conflict=conflict,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    return [(place, conflict_id) for place in SETTINGS for conflict_id in CONFLICTS]


def explain_rejection(place: str, conflict: str) -> str:
    return f"(No story: the requested tale about {place} and {conflict} does not fit this fairy-tale maize world.)"


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    conflict = f["conflict"]
    crop = f["crop"]
    return [
        f'Write a short fairy tale about a child named {hero.id} who tends maize with great potential.',
        f"Tell a gentle story where {hero.id} protects young maize from {conflict.label} and the harvest can ripen.",
        f'Write a child-friendly fairy tale that uses the word "{crop.keyword}" and ends with a patient reward.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    conflict = f["conflict"]
    crop = f["crop"]
    setting = f["setting"]

    return [
        QAItem(
            question=f"What did {hero.id} love about the maize near {setting.place}?",
            answer=f"{hero.id} loved that the maize had great potential and could grow into something golden and sweet.",
        ),
        QAItem(
            question=f"Who helped {hero.id} keep watch when {conflict.label} caused trouble?",
            answer=f"{helper.id} helped {hero.id} stay calm and protect the young maize row.",
        ),
        QAItem(
            question=f"Why was it a problem to rush the maize?",
            answer=f"It was a problem because the maize was still too young and had not reached its ripened, ready state yet.",
        ),
        QAItem(
            question=f"How did the conflict end?",
            answer=f"They solved it by protecting the maize and waiting patiently until it could become {crop.ripened}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is maize?",
            answer="Maize is a grain plant that grows on tall stalks and makes ears with kernels.",
        ),
        QAItem(
            question="Why do plants need patience while they grow?",
            answer="Plants need time for roots, leaves, and fruit to grow strong before they are ready to harvest.",
        ),
        QAItem(
            question="What does potential mean?",
            answer="Potential means something can grow, become, or do more in the future.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(garden).
place(field).
place(courtyard).

conflict(crow).
conflict(prince).
conflict(storm).

valid(Place, Conflict) :- place(Place), conflict(Conflict).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c in CONFLICTS:
        lines.append(asp.fact("conflict", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in Python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Rendering and trace
# ---------------------------------------------------------------------------

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale world: potential, maize, and conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"], dest="hero_type")
    ap.add_argument("--helper-type", choices=["girl", "boy"], dest="helper_type")
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
    if args.place and args.conflict:
        if args.place not in SETTINGS or args.conflict not in CONFLICTS:
            raise StoryError("(No valid combination matches the given options.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.conflict is None or c[1] == args.conflict)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, conflict = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    return StoryParams(place=place, conflict=conflict, name=name, hero_type=hero_type, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CROPS["maize"],
        CONFLICTS[params.conflict],
        params.name,
        params.hero_type,
        params.helper_type,
    )
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible place/conflict combos:\n")
        for place, conflict in combos:
            print(f"  {place:10} {conflict}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place, conflict in sorted(valid_combos()):
            params = StoryParams(
                place=place,
                conflict=conflict,
                name="Lina",
                hero_type="girl",
                helper_type="boy",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
