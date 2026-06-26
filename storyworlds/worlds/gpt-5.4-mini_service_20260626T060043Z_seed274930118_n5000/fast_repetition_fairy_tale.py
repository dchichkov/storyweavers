#!/usr/bin/env python3
"""
A small fairy-tale storyworld about speed, repetition, and a helpful turn.

Premise:
- A swift little fox or hare must deliver a message before dusk.
- The path is blocked by three repeating obstacles.
- Each try teaches something, and the final try succeeds because the hero
  changes method, not because the world freezes.

The world model tracks physical meters and emotional memes:
- meters: distance, speed, tiredness, progress, blocked, gathered, opened
- memes: worry, hope, pride, patience, kindness, gratitude

The story is narrated as a gentle fairy tale with repeated beats:
- "fast" is central to the hero's identity and the solution.
- Repetition is structural: three tries, each slightly different.
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
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "rabbit", "hare", "bird", "mouse"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "fairy", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    trail: str
    hazard: str
    gate: str
    weather: str = "soft"


@dataclass
class StoryParams:
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    setting: str
    prize: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "forest": Setting(
        place="the deep forest",
        trail="a narrow winding trail",
        hazard="a thorny bramble",
        gate="an old gate of roots",
    ),
    "hill": Setting(
        place="the green hill",
        trail="a steep windy path",
        hazard="a rolling stone patch",
        gate="a gate of wicker reeds",
    ),
    "river": Setting(
        place="the silver riverbank",
        trail="a sandy riverside path",
        hazard="a quick brook",
        gate="a little bridge of sticks",
    ),
}

HEROES = [
    ("Pip", "fox"),
    ("Milo", "hare"),
    ("Nina", "rabbit"),
    ("Tavi", "mouse"),
]

HELPERS = [
    ("Brim", "bird"),
    ("Wren", "bird"),
    ("Mira", "fairy"),
    ("Oren", "fox"),
]

PRIZES = {
    "letter": "a sealed letter for the kind king",
    "crownleaf": "a silver leaf crown for the spring feast",
    "berry": "a basket of star berries for the village",
}

TRAITS = ["brave", "curious", "gentle", "quick", "bright", "steady"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld of fast repetition and a happy turn.")
    ap.add_argument("--hero", choices=[h[0] for h in HEROES])
    ap.add_argument("--hero-type", choices=sorted({h[1] for h in HEROES}))
    ap.add_argument("--helper", choices=[h[0] for h in HELPERS])
    ap.add_argument("--helper-type", choices=sorted({h[1] for h in HELPERS}))
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
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


def choose(rng: random.Random, seq):
    return rng.choice(list(seq))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_name, hero_type = choose(rng, HEROES)
    helper_name, helper_type = choose(rng, HELPERS)
    setting = choose(rng, list(SETTINGS))
    prize = choose(rng, list(PRIZES))
    if args.hero:
        hero_name = args.hero
        if args.hero_type is None:
            hero_type = next(t for n, t in HEROES if n == hero_name)
    if args.hero_type:
        hero_type = args.hero_type
    if args.helper:
        helper_name = args.helper
        if args.helper_type is None:
            helper_type = next(t for n, t in HELPERS if n == helper_name)
    if args.helper_type:
        helper_type = args.helper_type
    if args.setting:
        setting = args.setting
    if args.prize:
        prize = args.prize
    return StoryParams(
        hero=hero_name,
        hero_type=hero_type,
        helper=helper_name,
        helper_type=helper_type,
        setting=setting,
        prize=prize,
    )


def _meter(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _meme(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def act_run(world: World, hero: Entity) -> None:
    _meter(hero, "speed", 1.0)
    _meter(hero, "progress", 1.0)
    _meter(hero, "tiredness", 0.2)
    _meme(hero, "hope", 0.4)


def act_block(world: World, hero: Entity) -> bool:
    if world.facts["attempt"] == 1:
        _meme(hero, "worry", 0.5)
        world.say(f"But at the {world.setting.trail}, a {world.setting.hazard} blocked the way.")
        return True
    if world.facts["attempt"] == 2:
        _meme(hero, "patience", 0.6)
        world.say(f"Again the {world.setting.hazard} blocked the way, and the little feet had to stop.")
        return True
    return False


def tell(world: World) -> World:
    hero = world.get("hero")
    helper = world.get("helper")
    prize = world.get("prize")

    world.say(f"Once in {world.setting.place}, there lived a {world.facts['hero_trait']} little {hero.type} named {hero.id}.")
    world.say(f"{hero.id} was so fast that the wind seemed to chase {hero.pronoun('object')}.")

    world.say(f"One morning, {helper.id} brought {hero.pronoun('object')} {prize.phrase}.")
    world.say(f'"Please carry it to the king before dusk," said {helper.id}, and {hero.id} promised to go at once.')

    world.para()
    world.say(f"{hero.id} hurried down {world.setting.trail}.")
    for attempt in (1, 2, 3):
        world.facts["attempt"] = attempt
        act_run(world, hero)
        blocked = act_block(world, hero)
        if blocked and attempt < 3:
            if attempt == 1:
                world.say(f"{hero.id} ran back, then ran again, faster than before.")
            else:
                world.say(f"{hero.id} looked and looked, and then paused to think, still breathing fast.")
            continue
        if attempt == 3:
            world.say(f"Then {helper.id} fluttered down and pointed to a small side path beside the roots.")
            _meme(helper, "kindness", 0.8)
            _meme(hero, "grace", 0.7)
            _meter(hero, "progress", 2.0)
            world.say(
                f"{hero.id} dashed along the side path, slipped through the {world.setting.gate}, "
                f"and reached the castle just in time."
            )
            _meme(hero, "pride", 0.7)
            _meme(helper, "gratitude", 0.8)
            break

    world.para()
    world.say(f"The king took the prize with a smile, and the whole hall grew bright.")
    world.say(f"{hero.id} was still fast, but now {hero.id} was also wise enough to listen and try a new way.")
    world.say(f"And because the little journey was repeated three times, the last one felt like a true fairy-tale victory.")

    world.facts.update(hero=hero, helper=helper, prize=prize)
    return world


def generate_story_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type))
    prize = world.add(Entity(id="prize", type="thing", label=params.prize, phrase=PRIZES[params.prize]))
    world.facts["hero_trait"] = "fast"
    world.facts["setting_key"] = params.setting
    return tell(world)


def generate_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        f"Write a short fairy tale about a fast little {hero.type} who must carry a message through the forest.",
        f"Tell a story where {hero.id} tries three times to cross a blocked path and a kind helper shows a safer way.",
        f"Write a gentle tale with repetition, speed, and a happy ending for {hero.id} and {helper.id}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    prize = world.facts["prize"]
    setting = world.setting.place
    return [
        QAItem(
            question=f"Who was the fast little traveler in the story?",
            answer=f"The fast little traveler was {hero.id}, a small {hero.type} who hurried through {setting}.",
        ),
        QAItem(
            question=f"What did {helper.id} ask {hero.id} to carry?",
            answer=f"{helper.id} asked {hero.id} to carry {prize.phrase} to the king before dusk.",
        ),
        QAItem(
            question=f"What happened after the path blocked {hero.id} twice?",
            answer=f"{hero.id} kept trying, but on the third try {helper.id} showed a side path, and that made the journey work.",
        ),
        QAItem(
            question=f"How many times did {hero.id} try before success?",
            answer=f"{hero.id} tried three times before reaching the castle.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does fast mean?",
            answer="Fast means moving quickly or doing something in a short time.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing or saying something again and again, often in a pattern.",
        ),
        QAItem(
            question="Why can a helper be useful in a story?",
            answer="A helper can give advice, point out a safer path, or solve a problem with the hero.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(sorted(e.meters.items()))} memes={dict(sorted(e.memes.items()))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(hero="Pip", hero_type="fox", helper="Brim", helper_type="bird", setting="forest", prize="letter"),
    StoryParams(hero="Milo", hero_type="hare", helper="Mira", helper_type="fairy", setting="hill", prize="crownleaf"),
    StoryParams(hero="Nina", hero_type="rabbit", helper="Wren", helper_type="bird", setting="river", prize="berry"),
]


ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(K) :- helper_name(K).
setting(S) :- setting_name(S).
prize(P) :- prize_name(P).

fast(H) :- hero(H).
repeated_try(H,1). repeated_try(H,2). repeated_try(H,3) :- hero(H).

blocked(S,1) :- setting(S).
blocked(S,2) :- setting(S).
cleared(S,3) :- setting(S).

successful(H,S) :- fast(H), blocked(S,1), blocked(S,2), cleared(S,3).
#show successful/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name, _ in HEROES:
        lines.append(asp.fact("hero_name", name))
    for name, _ in HELPERS:
        lines.append(asp.fact("helper_name", name))
    for s in SETTINGS:
        lines.append(asp.fact("setting_name", s))
    for p in PRIZES:
        lines.append(asp.fact("prize_name", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show successful/2."))
    got = set(asp.atoms(model, "successful"))
    want = {("Pip", "forest"), ("Milo", "hill"), ("Nina", "river")}
    if got == want:
        print(f"OK: ASP parity matches ({len(got)} cases).")
        return 0
    print("MISMATCH:")
    print("got:", sorted(got))
    print("want:", sorted(want))
    return 1


def asp_successes() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show successful/2."))
    return sorted(set(asp.atoms(model, "successful")))


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p.setting, p.hero, p.prize) for p in CURATED]


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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


def resolve_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hero and args.hero_type is None:
        args.hero_type = next(t for n, t in HEROES if n == args.hero)
    if args.helper and args.helper_type is None:
        args.helper_type = next(t for n, t in HELPERS if n == args.helper)
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")
    params = resolve_params(args, rng)
    return params


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show successful/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for s, h in asp_successes():
            print(f"{s}: {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_combo(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
            header = f"### {p.hero} in {p.setting} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
