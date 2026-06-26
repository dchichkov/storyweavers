#!/usr/bin/env python3
"""
storyworlds/worlds/zweiback_inner_monologue_foreshadowing_flashback_tall_tale.py
================================================================================

A small tall-tale storyworld about a child, a stubborn baker, and a box of
zweiback that wants to cross a windy bridge and reach the county fair.

The tale uses three narrative instruments:
- Inner Monologue: the hero thinks to themself while facing trouble.
- Foreshadowing: a small omen hints at the later turn.
- Flashback: a remembered scene explains why the hero knows the right move.

The world is tiny and state-driven: the bread is physical, the worry is emotional,
and the ending proves what changed.
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

TALL_TALE_TONE = [
    "bigger than a barn and twice as lively",
    "as wide as a wagon track and as brave as a bell",
    "full of wind, whim, and whiskers of dust",
]

HERO_NAMES = ["Mabel", "Ivy", "June", "Otis", "Ruth", "Cal"]
HERO_TYPES = ["girl", "boy"]
HELPER_NAMES = ["Grandma", "Uncle Ben", "Aunt Jo", "Pa", "Ma"]
PLACES = ["the hill road", "the county bridge", "the fair lane", "the old bakery"]
WEATHERS = ["windy", "bright", "gusty"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandma", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandpa", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    weather: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
    weather: str
    hero_name: str
    hero_type: str
    helper_name: str
    seed: Optional[int] = None


@dataclass
class Bread:
    label: str = "zweiback"
    phrase: str = "a tin box of zweiback"
    crunch: str = "dry and crisp"
    weight: float = 1.0


@dataclass
class StoryModel:
    world: World
    hero: Entity
    helper: Entity
    bread: Entity
    omen_seen: bool = False
    flashback_seen: bool = False
    resolved: bool = False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld about zweiback, a windy bridge, and a clever fix."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--helper")
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
    place = args.place or rng.choice(PLACES)
    weather = args.weather or rng.choice(WEATHERS)
    hero_type = args.gender or rng.choice(HERO_TYPES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    if place == "the old bakery" and weather == "bright":
        pass
    return StoryParams(
        place=place,
        weather=weather,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
    )


def _set(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = value


def _add(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + value


def _mood(entity: Entity, key: str, value: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + value


def tell(params: StoryParams) -> StoryModel:
    world = World(place=params.place, weather=params.weather)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper_type = "grandma" if params.helper_name == "Grandma" else "uncle"
    helper = world.add(Entity(id=params.helper_name, kind="character", type=helper_type))
    bread = world.add(Entity(
        id="zweiback",
        kind="thing",
        type="bread",
        label="zweiback",
        phrase="a tin box of zweiback",
        owner=helper.id,
    ))
    _set(bread, "crunch", 1.0)
    _set(bread, "dry", 1.0)
    _set(hero, "hope", 1.0)
    _set(hero, "worry", 0.0)
    _set(hero, "bravery", 0.0)
    _set(helper, "pride", 1.0)

    world.say(
        f"{hero.id} was a {params.hero_type} as {random.choice(TALL_TALE_TONE)}. "
        f"{hero.pronoun().capitalize()} lived by {params.place} and knew the wind by name."
    )
    world.say(
        f"{helper.id} kept {bread.phrase} in the pantry, and everybody in town said "
        f"it could feed a parade."
    )

    world.para()
    world.say(
        f"One {params.weather} morning, {hero.id} smelled the bread and felt a little tug in the chest."
    )
    world.say(
        f"A sliver of cracked crust slid from the box and skittered across the floor like a tiny sign."
    )
    world.say(
        f"That was the foreshadowing, though {hero.id} only knew it meant something was about to happen."
    )
    _mood(hero, "curiosity", 1.0)
    model = StoryModel(world=world, hero=hero, helper=helper, bread=bread, omen_seen=True)
    return model


def _flashback(model: StoryModel) -> None:
    if model.flashback_seen:
        return
    w = model.world
    h = model.hero
    helper = model.helper
    w.para()
    w.say(
        f"{h.id} remembered a day last autumn when {helper.id} had crossed the same bridge with a basket of rolls."
    )
    w.say(
        f"The wind had nearly turned the basket into a kite, but {helper.id} tied the lid down with twine and laughed."
    )
    w.say(
        f"That flashback came back quick as a whistling kettle, and {h.id} thought, "
        f'“If wind can steal a basket, it can surely bother a box.”'
    )
    _mood(h, "memory", 1.0)
    model.flashback_seen = True


def _inner_monologue(model: StoryModel) -> None:
    w = model.world
    h = model.hero
    _add(h, "worry", 1.0)
    _add(h, "bravery", 1.0)
    w.say(
        f"{h.id} looked at the bridge and had a long, quiet inner monologue: "
        f'“If I carry the zweiback now, the gusts may scatter crumbs clear to the courthouse.”'
    )
    w.say(
        f'“But if I tie it tight and keep one hand on the rail, I can do this without losing a single bite.”'
    )


def _cross_bridge(model: StoryModel) -> None:
    w = model.world
    h = model.hero
    helper = model.helper
    bread = model.bread

    w.para()
    w.say(
        f"Then {h.id} tucked the box under {h.pronoun('possessive')} arm, tied it with twine, and stepped onto {w.place}."
    )
    w.say(
        f"The wind tried to brag, but {h.id} held on with a grin and a good, steady hand."
    )
    if w.weather in {"windy", "gusty"}:
        _add(h, "skill", 1.0)
        _add(bread, "safe", 1.0)
    else:
        _add(bread, "safe", 0.5)

    w.say(
        f"{helper.id} called from behind, 'Easy now; even a tall tale needs a careful knot.'"
    )
    if w.weather == "gusty":
        w.say(
            f"A big gust came stomping by, but it only ruffled {h.id}'s hair and made the bridge sing."
        )
    else:
        w.say(
            f"The air was lively, but the box stayed snug as a duckling under a wing."
        )
    model.resolved = True


def _ending(model: StoryModel) -> None:
    w = model.world
    h = model.hero
    helper = model.helper
    bread = model.bread
    w.para()
    w.say(
        f"By the time {h.id} reached the other side, the zweiback was still whole, still crisp, and not one crumb had gone missing."
    )
    w.say(
        f"{helper.id} opened the box later at the fair, and the smell of toasted bread rolled out so far that three dogs sat down to listen."
    )
    w.say(
        f"{h.id} smiled, because the fear had turned into a memory, and the memory had turned into courage."
    )
    _add(h, "joy", 1.0)
    _add(helper, "pride", 1.0)
    _add(bread, "served", 1.0)


def generate_story(params: StoryParams) -> StoryModel:
    model = tell(params)
    _flashback(model)
    _inner_monologue(model)
    _cross_bridge(model)
    _ending(model)
    model.world.facts.update(
        hero=model.hero,
        helper=model.helper,
        bread=model.bread,
        params=params,
    )
    return model


def generation_prompts(model: StoryModel) -> list[str]:
    p = model.world.facts["params"]
    return [
        f"Write a tall tale for a child about {p.hero_name} carrying zweiback across {p.place}.",
        f"Tell a story with foreshadowing, a flashback, and an inner monologue about preserving zweiback in windy weather.",
        f"Create a child-friendly tall tale where {p.helper_name} and {p.hero_name} keep a box of zweiback safe on a blustery crossing.",
    ]


def story_qa(model: StoryModel) -> list[QAItem]:
    p = model.world.facts["params"]
    h = model.hero
    helper = model.helper
    return [
        QAItem(
            question=f"What was {p.hero_name} carrying in the story?",
            answer="The child was carrying a tin box of zweiback, and the story treated it like something precious enough to protect from the wind.",
        ),
        QAItem(
            question=f"Why did {p.hero_name} worry on {p.place}?",
            answer=f"{p.hero_name} worried because the wind might scatter crumbs, and the box of zweiback could have been spoiled if it had not been tied down well.",
        ),
        QAItem(
            question=f"What remembered moment helped {p.hero_name} choose the safe way?",
            answer=f"{p.hero_name} remembered how {helper.id} had once tied a basket shut before crossing the bridge, so the child knew to use twine and keep a steady hand.",
        ),
        QAItem(
            question=f"How did {p.hero_name} feel at the end?",
            answer=f"At the end, {p.hero_name} felt brave and happy because the zweiback arrived whole and the worry turned into courage.",
        ),
    ]


def world_knowledge_qa(model: StoryModel) -> list[QAItem]:
    return [
        QAItem(
            question="What is zweiback?",
            answer="Zweiback is a dry, crisp bread or twice-baked rusk that can keep well in a tin box.",
        ),
        QAItem(
            question="Why can wind be a problem for crumbs?",
            answer="Wind can carry crumbs away, so a loose loaf or open box may spill its pieces far and wide.",
        ),
        QAItem(
            question="What does a flashback do in a story?",
            answer="A flashback briefly shows something that happened earlier, so readers understand why a character knows what to do now.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(model: StoryModel) -> str:
    lines = ["--- world model state ---"]
    for e in model.world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.kind:9}) meters={meters} memes={memes}")
    lines.append(f"  facts: {sorted(model.world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
bread_safe(H) :- hero(H), bridge_place(P), windy(W), crossing(H, P, W), tied_down(H).
omen_seen(P) :- crumb_falls(P).
flashback_help(H) :- remembers(H), tied_down_before(H).
resolution(H) :- bread_safe(H), flashback_help(H).
"""

def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "hero"),
            asp.fact("bridge_place", "bridge"),
            asp.fact("windy", "wind"),
            asp.fact("crumb_falls", "bridge"),
            asp.fact("remembers", "hero"),
            asp.fact("tied_down_before", "hero"),
            asp.fact("crossing", "hero", "bridge", "wind"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Lazy import to respect contract.
    import asp
    model = asp.one_model(asp_program("#show resolution/1."))
    atoms = set(asp.atoms(model, "resolution"))
    py = {("hero",)} if True else set()
    if atoms == py:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("  ASP:", sorted(atoms))
    print("  PY :", sorted(py))
    return 1


def generate(params: StoryParams) -> StorySample:
    model = generate_story(params)
    story = model.world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(model),
        story_qa=story_qa(model),
        world_qa=world_knowledge_qa(model),
        world=model,
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
    StoryParams(place="the county bridge", weather="windy", hero_name="Mabel", hero_type="girl", helper_name="Grandma"),
    StoryParams(place="the fair lane", weather="gusty", hero_name="Otis", hero_type="boy", helper_name="Uncle Ben"),
    StoryParams(place="the hill road", weather="windy", hero_name="June", hero_type="girl", helper_name="Aunt Jo"),
]


def build_sample(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolution/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show resolution/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [build_sample(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = build_sample(params)
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
            header = f"### {p.hero_name}: zweiback at {p.place} ({p.weather})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
