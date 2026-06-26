#!/usr/bin/env python3
"""
Standalone storyworld: a snazzy superhero, a pagan festival, and a conflict
that turns into a careful rescue.

This world is a compact, classical simulation. A young hero loves a flashy
costume and wants to use powers at a city pagan festival, but a mentor worries
that a careless blast could ruin sacred decorations or scare the crowd. The
story's turn is a conflict over that choice, and the resolution is a better
method that protects the celebration.
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
# World constants
# ---------------------------------------------------------------------------

SETTING_NAME = "the lantern square"
FEATURE_WORDS = {"snazzy", "pagan", "conflict"}
HERO_NAMES = ["Nova", "Jules", "Rin", "Mika", "Pip", "Tala", "Ezra", "Aria"]
MENTOR_NAMES = ["Aunt Comet", "Uncle Beacon", "Captain Wren", "Ms. Halo"]
VILLAIN_NAMES = ["Moth Mask", "Grim Glint", "Hush Hex", "Night Kite"]
TRUTHS = ["brave", "curious", "bold", "cheerful", "sparkly", "steady"]


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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Hero:
    name: str
    trait: str
    gender: str
    costume: str
    power: str
    place: str = SETTING_NAME
    seed: Optional[int] = None


@dataclass
class StoryParams:
    name: str
    trait: str
    gender: str
    mentor: str
    villain: str
    seed: Optional[int] = None


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self) -> None:
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

    def copy(self) -> "World":
        import copy as _copy

        clone = World()
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


GEAR = [
    Gear(
        id="shield",
        label="a bright shield",
        covers={"torso"},
        guards={"glare"},
        prep="hold a bright shield up first",
        tail="used the bright shield",
    ),
    Gear(
        id="muffler",
        label="soft ear-muffs",
        covers={"head"},
        guards={"boom"},
        prep="put on soft ear-muffs",
        tail="put on the soft ear-muffs",
        plural=True,
    ),
    Gear(
        id="gloves",
        label="careful gloves",
        covers={"hands"},
        guards={"spark"},
        prep="slip on careful gloves",
        tail="slipped on the careful gloves",
        plural=True,
    ),
]

ACTIVITIES = {
    "flare": {
        "verb": "fire a flare",
        "gerund": "firing flares",
        "rush": "blast a flare into the air",
        "mess": "glare",
        "soil": "too bright",
        "zone": {"torso", "hands"},
        "keyword": "snazzy",
        "tags": {"snazzy", "light"},
    },
    "drum": {
        "verb": "bang the giant drum",
        "gerund": "beating the drum",
        "rush": "slam the drum with power",
        "mess": "boom",
        "soil": "too loud",
        "zone": {"head", "torso"},
        "keyword": "pagan",
        "tags": {"pagan", "sound"},
    },
    "spark": {
        "verb": "spin a spark ring",
        "gerund": "spinning spark rings",
        "rush": "whirl the sparks around",
        "mess": "spark",
        "soil": "full of sparks",
        "zone": {"hands", "torso"},
        "keyword": "conflict",
        "tags": {"fire", "light"},
    },
}

PLACES = {
    "square": {
        "name": SETTING_NAME,
        "affords": {"flare", "drum", "spark"},
        "pagan": True,
    }
}


def _gesture(world: World, hero: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1


def predict_problem(world: World, hero: Entity, activity: str, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(hero.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"damaged": bool(prize.meters.get("dirty", 0) >= 1), "tension": hero.memes.get("conflict", 0)}


def do_activity(world: World, hero: Entity, activity: str, narrate: bool = True) -> None:
    hero.meters[ACTIVITIES[activity]["mess"]] = hero.meters.get(ACTIVITIES[activity]["mess"], 0) + 1
    _apply_rules(world, narrate=narrate)


def _apply_rules(world: World, narrate: bool = True) -> None:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("conflict", 0) >= 1 and actor.memes.get("softened", 0) >= 1:
            sig = ("resolve", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.memes["conflict"] = 0
                out.append("__resolve__")
    if narrate:
        for s in out:
            if s != "__resolve__":
                world.say(s)


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.memes if t), 'hero')}"
    )


def tell(hero_name: str, trait: str, gender: str, mentor_name: str, villain_name: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, meters={}, memes={"joy": 0, "conflict": 0}))
    mentor = world.add(Entity(id=mentor_name, kind="character", type="woman" if gender == "girl" else "man"))
    villain = world.add(Entity(id=villain_name, kind="character", type="thing"))
    banner = world.add(Entity(
        id="banner",
        type="banner",
        label="a snazzy festival banner",
        phrase="a snazzy festival banner",
        owner="festival",
    ))
    lantern = world.add(Entity(
        id="lantern",
        type="lantern",
        label="a pagan lantern",
        phrase="a pagan lantern",
        caretaker=mentor.id,
    ))

    world.say(
        f"{hero.id} was a {trait} little superhero who loved a {hero.pronoun('possessive')} snazzy costume."
    )
    world.say(
        f"Every evening at {SETTING_NAME}, the pagan festival lights shone like tiny stars."
    )
    world.say(
        f"{hero.id} wanted to show off {hero.pronoun('possessive')} power and keep the crowd smiling."
    )
    world.para()

    world.say(
        f"Then {hero.id} saw {villain.id} sneaking toward {lantern.label} near the banner."
    )
    world.say(
        f"{mentor.id} noticed the trouble too, but said, \"Wait—{hero.id}, do not blast first.\""
    )
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    world.say(
        f"{hero.id} felt torn. {hero.pronoun().capitalize()} wanted to stop the sneaky villain fast."
    )
    world.para()

    world.say(
        f"{hero.id} lifted {hero.pronoun('possessive')} hands, then chose a careful plan instead."
    )
    hero.memes["softened"] = 1
    world.say(
        f"Together, they used a snazzy shield of bright light to guide {villain.id} away."
    )
    world.say(
        f"The pagan lantern stayed safe, the banner stayed pretty, and {hero.id} smiled in the glow."
    )

    world.facts.update(
        hero=hero,
        mentor=mentor,
        villain=villain,
        banner=banner,
        lantern=lantern,
        activity="flare",
        setting=SETTING_NAME,
        feature_words=FEATURE_WORDS,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    return [
        f'Write a short superhero story that uses the word "snazzy" and includes a pagan festival.',
        f"Tell a child-friendly story where {hero.id} wants to solve a conflict fast, but {mentor.id} asks for a careful plan.",
        f"Write a story about a snazzy hero, a pagan celebration, and a conflict that ends with a gentle rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    villain = f["villain"]
    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"The story was mainly about {hero.id}, a little superhero with a snazzy costume.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel conflicted near the festival?",
            answer=(
                f"{hero.id} wanted to stop {villain.id} quickly, but {mentor.id} warned that a big blast could hurt the pagan lanterns and the banner."
            ),
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=(
                f"{hero.id} chose a careful rescue instead of a reckless one, so the festival stayed safe and the conflict was calmed."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does snazzy mean?",
            answer="Snazzy means bright, stylish, or showy in a fun way.",
        ),
        QAItem(
            question="What is a pagan festival in this story?",
            answer="It is a public celebration with special lights, banners, and traditions.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a problem or disagreement that makes people unsure what to do next.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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


ASP_RULES = r"""
hero(H) :- hero_name(H).
mentor(M) :- mentor_name(M).
villain(V) :- villain_name(V).

conflict(H) :- wants_help(H), warns_against_blast(M,H), mentor(M).

safe_choice(H) :- conflict(H), careful_plan(H).
resolved(H) :- safe_choice(H), conflict(H).

#show conflict/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("hero_name", "Nova"),
        asp.fact("mentor_name", "Captain Wren"),
        asp.fact("villain_name", "Moth Mask"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show conflict/1.\n#show resolved/1."))
    atoms = {(s.name, tuple(a.name if a.type == a.type.SymbolType.Function else getattr(a, 'name', None) for a in s.arguments)) for s in model}
    # We only need parity on the reasonableness gate; here it is deterministic.
    if any(sym.name == "conflict" for sym in model) and not any(sym.name == "resolved" for sym in model):
        print("OK: ASP gate can represent conflict without immediate resolution.")
        return 0
    print("MISMATCH: ASP twin did not behave as expected.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A snazzy superhero storyworld with a pagan festival conflict.")
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--trait", choices=TRUTHS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=MENTOR_NAMES)
    ap.add_argument("--villain", choices=VILLAIN_NAMES)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRUTHS)
    mentor = args.mentor or rng.choice(MENTOR_NAMES)
    villain = args.villain or rng.choice(VILLAIN_NAMES)
    return StoryParams(name=name, trait=trait, gender=gender, mentor=mentor, villain=villain)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.trait, params.gender, params.mentor, params.villain)
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
        print(asp_program("#show conflict/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples.append(generate(StoryParams("Nova", "brave", "girl", "Captain Wren", "Moth Mask")))
        samples.append(generate(StoryParams("Jules", "curious", "boy", "Aunt Comet", "Night Kite")))
        samples.append(generate(StoryParams("Aria", "sparkly", "girl", "Ms. Halo", "Hush Hex")))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
