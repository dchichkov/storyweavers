#!/usr/bin/env python3
"""
A tiny Tall Tale storyworld about a boast, a symbolic dimple, and a conflict
that turns into a gentler ending.

Seed words: ouch, symbolic, dimple
Style: Tall Tale
"""

from __future__ import annotations

import argparse
import copy
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wear": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "conflict": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "giant", "father", "dad"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the windy hill"
    detail: str = "A stone path curled up the hill like a ribbon."


@dataclass
class TaleObject:
    id: str
    label: str
    phrase: str
    location: str
    symbol: bool = False
    worn: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.objects: dict[str, TaleObject] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_object(self, obj: TaleObject) -> TaleObject:
        self.objects[obj.id] = obj
        return obj

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.objects = copy.deepcopy(self.objects)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str = "hill"
    hero: str = "Hank"
    rival: str = "Mabel"
    seed: Optional[int] = None


SETTINGS = {
    "hill": Setting(
        place="the windy hill",
        detail="A stone path curled up the hill like a ribbon, and the clouds marched overhead.",
    ),
    "plain": Setting(
        place="the open plain",
        detail="The open plain stretched far and wide, with grass leaning like listeners in a story.",
    ),
    "canyon": Setting(
        place="the red canyon",
        detail="The red canyon stood tall and hollow, and every call came back with a grin.",
    ),
}

HEROES = ["Hank", "Bess", "Otto", "Mina", "Jeb", "Lula"]
RIVALS = ["Mabel", "Gus", "Nell", "Rufus", "Tilda", "Clem"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall Tale world: ouch, symbolic, dimple, and conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--rival")
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
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.name or rng.choice(HEROES)
    rival = args.rival or rng.choice([r for r in RIVALS if r != hero])
    return StoryParams(place=place, hero=hero, rival=rival)


def _say_boast(world: World, hero: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} was a tall-talking giant who said {hero.pronoun('subject')} could out-stomp any thundercloud."
    )
    world.say(
        f"Everybody on {world.setting.place} knew {hero.id} for {hero.pronoun('possessive')} booming laugh and big boots."
    )


def _set_symbolic_dimple(world: World) -> TaleObject:
    dimple = world.add_object(TaleObject(
        id="dimple",
        label="dimple",
        phrase="a tiny symbolic dimple carved into a pebble",
        location=world.setting.place,
        symbol=True,
    ))
    return dimple


def _conflict(world: World, hero: Entity, rival: Entity, dimple: TaleObject) -> None:
    hero.memes["conflict"] += 1
    rival.memes["conflict"] += 1
    world.say(
        f"Then {rival.id} pointed at a little pebble with a symbolic dimple and said it was a sign {hero.id} would stub {hero.pronoun('possessive')} toe."
    )
    world.say(
        f"That made {hero.id} snort. {hero.pronoun().capitalize()} planted one huge boot down, and ouch! the rock bit back like a grumpy squirrel."
    )
    hero.meters["wear"] += 1
    dimple.worn = False
    world.facts["ouch"] = True
    world.facts["conflict"] = True


def _turn(world: World, hero: Entity, rival: Entity, dimple: TaleObject) -> None:
    hero.memes["conflict"] += 1
    world.say(
        f"Still, the wind rolled around them, and {hero.id} noticed the symbolic dimple had marked the exact place where the path was slickest."
    )
    world.say(
        f"{hero.id} rubbed {hero.pronoun('possessive')} toe, laughed at {hero.pronoun('object')}self, and said, 'Well, that ouch taught me something.'"
    )
    world.say(
        f"'{rival.id}, let's use the dimple as a warning mark,' {hero.pronoun('subject')} said, 'and step around the slippery spot instead of trying to squash it.'"
    )
    world.facts["symbolic"] = True


def _resolution(world: World, hero: Entity, rival: Entity, dimple: TaleObject) -> None:
    hero.memes["conflict"] = 0.0
    hero.memes["relief"] += 1
    rival.memes["conflict"] = 0.0
    world.say(
        f"So the two of them walked on with the pebble beside the path, its tiny symbolic dimple shining like a lesson."
    )
    world.say(
        f"{hero.id} did not brag so hard after that. {hero.pronoun().capitalize()} stepped lighter, and no more ouch came from the hill."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type="giant"))
    rival = world.add(Entity(id=params.rival, kind="character", type="girl"))
    dimple = _set_symbolic_dimple(world)

    world.say(f"On {world.setting.place}, the air felt large enough to carry a giant's brag clear to the next town.")
    world.say(world.setting.detail)
    _say_boast(world, hero)

    world.para()
    _conflict(world, hero, rival, dimple)
    _turn(world, hero, rival, dimple)
    _resolution(world, hero, rival, dimple)

    world.facts.update(hero=hero, rival=rival, dimple=dimple, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    rival: Entity = f["rival"]
    return [
        "Write a tall-tale about a boast, a symbolic dimple, and an ouch that teaches a lesson.",
        f"Tell a big-hearted story where {hero.id} and {rival.id} argue on a windy hill, then solve the conflict kindly.",
        "Write a child-friendly tall tale that starts with pride, includes ouch, and ends with a wiser walk.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    rival: Entity = f["rival"]
    return [
        QAItem(
            question=f"Who was the tall-talking giant in the story?",
            answer=f"The tall-talking giant was {hero.id}. {hero.pronoun().capitalize()} bragged big, then learned to step more carefully.",
        ),
        QAItem(
            question=f"What did {rival.id} point to on the path?",
            answer="The rival pointed to a little pebble with a symbolic dimple, which became a warning sign about the slippery path.",
        ),
        QAItem(
            question="What happened after the giant said ouch?",
            answer=f"After the ouch, {hero.id} stopped boasting so hard, used the dimple as a warning, and walked more carefully with {rival.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dimple?",
            answer="A dimple is a small hollow or dent. In this story, the symbolic dimple helped stand for a warning.",
        ),
        QAItem(
            question="What does symbolic mean?",
            answer="Symbolic means something stands for a bigger idea. Here, the dimple stood for caution and good sense.",
        ),
        QAItem(
            question="Why do people say ouch?",
            answer="People say ouch when something hurts or surprises them in a painful way.",
        ),
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a problem or disagreement that makes the characters struggle before they find a way forward.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:8} ({e.type:7}) meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    for o in world.objects.values():
        lines.append(f"  {o.id:8} (object ) symbol={o.symbol} location={o.location}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
rival(R) :- rival_name(R).
symbolic_dimple(D) :- dimple(D), symbol(D).
conflict(H,R) :- hero(H), rival(R), big_brag(H), point_to_dimple(R).
ouch(H) :- conflict(H,_).
resolved(H,R) :- conflict(H,R), lesson_learned(H).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("hero_name", h) for h in HEROES]
    lines += [asp.fact("rival_name", r) for r in RIVALS]
    lines.append(asp.fact("dimple", "dimple"))
    lines.append(asp.fact("symbol", "dimple"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show symbolic_dimple/1."))
    asp_set = set(asp.atoms(model, "symbolic_dimple"))
    py_set = {("dimple",)}
    if asp_set == py_set:
        print("OK: ASP and Python agree on the symbolic dimple fact.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("  asp:", sorted(asp_set))
    print("  py :", sorted(py_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="hill", hero="Hank", rival="Mabel"),
    StoryParams(place="plain", hero="Bess", rival="Gus"),
    StoryParams(place="canyon", hero="Otto", rival="Tilda"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show symbolic_dimple/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show symbolic_dimple/1."))
        print(sorted(set(asp.atoms(model, "symbolic_dimple"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.rival} on the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
