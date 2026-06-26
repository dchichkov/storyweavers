#!/usr/bin/env python3
"""
A standalone storyworld for a tiny nursery-rhyme-like tale about greed and
sharing.

Seed idea:
- A little character sees a small pile of treats.
- Greed makes them scoop up too much.
- A friend or parent suggests sharing.
- Sharing turns the scene warm again, and everyone gets a sweet ending image.

This script keeps the world model small, state-driven, and child-facing.
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
# Core entities and world state
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
    plural: bool = False
    shared: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    taste: str
    shareable: bool = True
    plural: bool = False


@dataclass
class Compromise:
    id: str
    label: str
    action: str
    ending: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "nursery": Setting(place="the nursery", indoors=True, affords={"treats"}),
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"treats"}),
    "garden": Setting(place="the garden", indoors=False, affords={"treats"}),
}

TASTES = {
    "honey": Treat(id="honey", label="honey cake", phrase="a little honey cake", taste="sweet", shareable=True),
    "berry": Treat(id="berry", label="berry bun", phrase="a round berry bun", taste="bright and sweet", shareable=True),
    "cookie": Treat(id="cookie", label="cookie", phrase="a warm cookie", taste="crumbly and sweet", shareable=True, plural=False),
    "apple": Treat(id="apple", label="apple slices", phrase="some apple slices", taste="fresh and crisp", shareable=True, plural=True),
}

COMPROMISES = {
    "share": Compromise(
        id="share",
        label="sharing",
        action="share the treat with everyone",
        ending="shared the treat, and the table felt kind and happy",
    )
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ruby", "Ada", "Ella"]
BOY_NAMES = ["Ben", "Theo", "Finn", "Leo", "Max", "Sam"]
TRAITS = ["tiny", "cheery", "busy", "playful", "lively", "curious"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    treat: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def is_greedy(hero: Entity) -> bool:
    return hero.memes.get("greed", 0.0) >= THRESHOLD


def is_sad(hero: Entity) -> bool:
    return hero.memes.get("sadness", 0.0) >= THRESHOLD


def is_shared(treat: Entity) -> bool:
    return treat.shared


def resolve_greed(world: World, hero: Entity, parent: Entity, treat: Entity) -> None:
    if not is_greedy(hero):
        return
    world.say(
        f"{hero.pronoun('subject').capitalize()} grabbed the treat close, and "
        f"{hero.pronoun('possessive')} cheeks looked puffed with greed."
    )
    hero.memes["greed"] = 0.0
    hero.memes["softness"] = hero.memes.get("softness", 0.0) + 1.0
    parent.memes["warmth"] = parent.memes.get("warmth", 0.0) + 1.0
    treat.shared = True
    world.say(
        f"Then {parent.label} smiled and said, "
        f'"Let us share the {treat.label}, one for you and one for me."'
    )
    world.say(
        f"{hero.id} looked at the little pieces, and {hero.id} shared at once. "
        f"The greedy feeling grew small, and the room felt bright."
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"hunger": 0.0},
        memes={"greed": 0.0, "joy": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        memes={"warmth": 0.0},
    ))
    treat_cfg = TASTES[params.treat]
    treat = world.add(Entity(
        id="Treat",
        kind="thing",
        type=treat_cfg.id,
        label=treat_cfg.label,
        phrase=treat_cfg.phrase,
        plural=treat_cfg.plural,
        owner=hero.id,
        shared=False,
    ))

    # Act 1: introduce the rhyme world.
    world.say(
        f"Little {hero.id} was a {params.trait} {params.gender} who loved a sweet little song."
    )
    world.say(
        f"In {setting.place}, there sat {treat_cfg.phrase}, and it smelled {treat_cfg.taste}."
    )
    world.say(
        f"{hero.id} liked {treat.label} so much that {hero.pronoun('subject')} wanted it all."
    )

    # Act 2: greed rises, then creates a problem.
    world.para()
    hero.memes["greed"] += 1.0
    hero.meters["wanting"] = hero.meters.get("wanting", 0.0) + 1.0
    world.say(
        f"{hero.id} tucked {treat.it()} close, and {hero.pronoun('subject')} would not pass it around."
    )
    if is_greedy(hero):
        world.say(
            f"The treat looked small in {hero.pronoun('possessive')} hands, but {hero.id}'s greed looked big."
        )

    # Act 3: a gentle turn toward sharing.
    world.para()
    world.say(
        f"Then the {params.parent} came near and sang, "
        f'"A share now is sweeter than a snatch and a stare."'
    )
    resolve_greed(world, hero, parent, treat)
    hero.memes["joy"] += 1.0
    hero.memes["greed"] = 0.0
    world.say(
        f"After that, {hero.id} took a small bite, {parent.label} took a small bite, "
        f"and the last crumbs were gone with a happy sigh."
    )

    world.para()
    world.say(
        f"At the end, {hero.id} and {parent.label} sat close and smiled at the empty plate. "
        f"The little room felt warm, and sharing made the day sing."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        treat=treat,
        treat_cfg=treat_cfg,
        place=params.place,
        setting=setting,
        shared=treat.shared,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin and facts
# ---------------------------------------------------------------------------
ASP_RULES = r"""
greedy(H) :- greed(H).
sharing_fix(H) :- greedy(H), shareable(T), wants(H,T).
resolved(H) :- greedy(H), sharing_fix(H).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, treat in TASTES.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("shareable", tid))
        lines.append(asp.fact("wants", "hero", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show greedy/1.\n#show resolved/1."))
    atoms = set((sym.name, tuple(str(a) for a in sym.arguments)) for sym in model)
    expected = {("greedy", ("hero",)), ("resolved", ("hero",))}
    if atoms == expected:
        print("OK: ASP gate matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  asp:", sorted(atoms))
    print("  py :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    treat = f["treat_cfg"]
    return [
        f'Write a short nursery-rhyme-style story about greed and sharing in {world.setting.place}.',
        f"Tell a gentle story where little {hero.id} wants {treat.phrase} all to {hero.pronoun('possessive')} self, but learns to share.",
        f'Create a child-friendly rhyme with the words "greed" and "sharing" and a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    treat = f["treat"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {hero.id} want at {place}?",
            answer=f"{hero.id} wanted {treat.phrase}, and at first {hero.pronoun('subject')} wanted it all for {hero.pronoun('possessive')} self.",
        ),
        QAItem(
            question=f"Why was {hero.id} acting greedy?",
            answer=f"{hero.id} was acting greedy because {hero.pronoun('subject')} tried to keep {treat.label} close instead of passing it around.",
        ),
        QAItem(
            question=f"How did the {parent.type} help {hero.id}?",
            answer=f"The {parent.type} helped by inviting {hero.id} to share the treat, which turned the greedy moment into a kind one.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} had shared the treat, and the greedy feeling was gone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    treat = f["treat_cfg"]
    return [
        QAItem(
            question="What is greed?",
            answer="Greed is the feeling of wanting too much for yourself, even when other people want some too.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people have some too, so everyone can enjoy the thing together.",
        ),
        QAItem(
            question=f"Why are {treat.label} and other treats fun to share?",
            answer="Treats are fun to share because little pieces can make more than one person smile.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Story generation / emission
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about greed and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treat", choices=TASTES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str]]:
    return sorted((place, treat) for place in SETTINGS for treat in TASTES if SETTINGS[place].affords)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        (place, treat)
        for place in SETTINGS
        for treat in TASTES
        if SETTINGS[place].affords
        and (args.place is None or args.place == place)
        and (args.treat is None or args.treat == treat)
    ]
    if not combos:
        raise StoryError("No valid setting/treat combination matches those options.")
    place, treat = rng.choice(combos)
    treat_cfg = TASTES[treat]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, treat=treat, name=name, gender=gender, parent=parent, trait=trait)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.shared:
            bits.append("shared=True")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
    return "\n".join(lines)


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
        print(asp_program("#show greedy/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show greedy/1.\n#show resolved/1."))
        print("\n".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    seen: set[str] = set()
    if args.all:
        for place in SETTINGS:
            for treat in TASTES:
                params = StoryParams(
                    place=place,
                    treat=treat,
                    name="Mia",
                    gender="girl",
                    parent="mother",
                    trait="cheery",
                )
                samples.append(generate(params))
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
