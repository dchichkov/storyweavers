#!/usr/bin/env python3
"""
Standalone storyworld: a small mystery about an enchanted bicycle, a wary bull,
and the surprising kindness that solves the case.

The seed tale imagines a child who finds a sparkling bicycle, hears a strange
sound near a field, and learns that bravery can be gentle. The simulated world
tracks a few concrete entities and two kinds of state:

- meters: physical conditions like hidden, scratched, dusty, and enchanted
- memes: emotional conditions like bravery, kindness, surprise, and worry

The prose is authored from the world state, not a frozen template. Different
choices change the clues, the tension, and the ending image.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    reveals: str
    hidden_from: set[str] = field(default_factory=set)
    suspicious: bool = False


@dataclass
class StoryParams:
    setting: str
    hero: str
    sidekick: str
    clue: str
    seed: Optional[int] = None


SETTINGS = {
    "lane": Setting(
        place="the quiet lane",
        detail="The lane was narrow, with hedges on both sides and one small gate that could swing open in the wind.",
        mood="quiet",
        affords={"search", "ride", "listen"},
    ),
    "barn": Setting(
        place="the old barnyard",
        detail="The barnyard held dusty boards, a water trough, and footprints that looked too large to be from a child.",
        mood="dusty",
        affords={"search", "ride", "listen"},
    ),
    "garden": Setting(
        place="the back garden",
        detail="The garden was still after supper, except for a shiny patch near the path and a soft rustle by the fence.",
        mood="still",
        affords={"search", "ride", "listen"},
    ),
}

CLUES = {
    "bell": Clue(
        id="bell",
        label="a little brass bell",
        reveals="the bicycle had been near the field gate",
        suspicious=True,
    ),
    "ribbon": Clue(
        id="ribbon",
        label="a red ribbon",
        reveals="someone kind had marked the safe path home",
        suspicious=False,
    ),
    "hoofprint": Clue(
        id="hoofprint",
        label="a muddy hoofprint",
        reveals="a bull had wandered close, but only because it was following a dropped apple",
        suspicious=True,
    ),
    "glow": Clue(
        id="glow",
        label="a faint glow on the handlebars",
        reveals="the bicycle had been enchanted, but only to find its way back to its owner",
        suspicious=False,
    ),
}

HEROES = {
    "boy": ("Owen", "boy"),
    "girl": ("Mila", "girl"),
    "child": ("Rin", "child"),
}

SIDEKICKS = {
    "cat": ("a gray cat", "cat"),
    "sister": ("his little sister", "girl"),
    "neighbor": ("the neighbor", "woman"),
}

MYSTERY_WORDS = {"enchant", "bicycle", "bull's", "bravery", "kindness", "surprise"}


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.revealed: list[str] = []

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.revealed = list(self.revealed)
        return w


def _story_text(entity: Entity) -> str:
    return entity.label or entity.id


def _adjust(world: World, eid: str, meter: Optional[str] = None, meme: Optional[str] = None, amount: float = 1.0) -> None:
    e = world.get(eid)
    if meter:
        e.meters[meter] = e.meters.get(meter, 0.0) + amount
    if meme:
        e.memes[meme] = e.memes.get(meme, 0.0) + amount


def introduce(world: World, hero: Entity, sidekick: Entity, clue: Clue) -> None:
    world.say(f"{hero.id} was a curious child who liked quiet places and small puzzles.")
    world.say(f"One afternoon, {hero.pronoun()} and {sidekick.label} found a {clue.label} near an old bicycle.")


def setup_bicycle(world: World, hero: Entity, bicycle: Entity) -> None:
    _adjust(world, bicycle.id, meter="hidden", amount=1.0)
    _adjust(world, bicycle.id, meter="enchanted", amount=1.0)
    world.say(f"The bicycle stood by the fence, half in shadow, as if it had been waiting to be noticed.")
    world.say(f"{hero.id} touched the handlebars and felt a tiny shiver of surprise.")


def suspicion(world: World, hero: Entity, clue: Clue) -> None:
    _adjust(world, hero.id, meme="worry", amount=1.0)
    _adjust(world, hero.id, meme="bravery", amount=1.0)
    if clue.suspicious:
        world.say(f"{hero.id} saw {clue.label} and wondered why it was there.")
    else:
        world.say(f"{hero.id} noticed {clue.label} and thought it looked like a kind clue.")


def bull_appears(world: World, hero: Entity, bull: Entity) -> None:
    _adjust(world, bull.id, meme="restless", amount=1.0)
    _adjust(world, bull.id, meter="nearby", amount=1.0)
    world.say(f"Then a bull came into view from behind the gate, slow and dark against the grass.")
    world.say(f"{hero.id} froze, because the bull's heavy steps made the whole mystery feel bigger.")


def brave_kind_move(world: World, hero: Entity, sidekick: Entity, clue: Clue, bull: Entity) -> None:
    _adjust(world, hero.id, meme="bravery", amount=1.0)
    _adjust(world, hero.id, meme="kindness", amount=1.0)
    _adjust(world, bull.id, meme="calm", amount=1.0)
    world.say(f"{hero.id} took a deep breath and remembered that bravery did not have to be loud.")
    world.say(f"{hero.id} and {sidekick.label} moved slowly, and {hero.pronoun()} held out a dropped apple instead of running.")
    if clue.id == "hoofprint":
        world.say(f"The bull stopped at once, because it had only been following the smell of fruit.")
    else:
        world.say(f"The bull stopped at once, because gentle hands made it less nervous.")
    world.say(f"That was the surprise: the careful move solved the danger faster than shouting would have.")


def reveal_bicycle(world: World, bicycle: Entity, clue: Clue) -> None:
    _adjust(world, bicycle.id, meter="hidden", amount=-1.0)
    _adjust(world, bicycle.id, meter="found", amount=1.0)
    world.revealed.append(clue.reveals)
    world.say(f"Behind the calm bull, the bicycle was easy to see at last.")
    world.say(f"It was still special, and now its mystery had a clear answer: {clue.reveals}.")


def ending(world: World, hero: Entity, sidekick: Entity, bicycle: Entity) -> None:
    _adjust(world, hero.id, meme="joy", amount=1.0)
    world.say(f"{hero.id} smiled, because the night had turned from a puzzle into a happy story.")
    world.say(f"{sidekick.label} climbed onto the bicycle seat beside {hero.pronoun('object')}, and the lane looked friendly again.")


def tell(setting: Setting, hero_name: str, hero_type: str, sidekick_name: str, sidekick_type: str, clue: Clue) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    sidekick = world.add(Entity(id="sidekick", kind="character", type=sidekick_type, label=sidekick_name))
    bicycle = world.add(Entity(id="bicycle", kind="thing", type="bicycle", label="bicycle", phrase="an old blue bicycle"))
    bull = world.add(Entity(id="bull", kind="animal", type="bull", label="bull", phrase="a big brown bull"))
    world.facts.update(hero=hero, sidekick=sidekick, bicycle=bicycle, bull=bull, clue=clue, setting=setting)

    introduce(world, hero, sidekick, clue)
    world.para()
    setup_bicycle(world, hero, bicycle)
    suspicion(world, hero, clue)
    world.para()
    bull_appears(world, hero, bull)
    brave_kind_move(world, hero, sidekick, clue, bull)
    reveal_bicycle(world, bicycle, clue)
    world.para()
    ending(world, hero, sidekick, bicycle)
    return world


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        if "search" not in setting.affords:
            continue
        for clue_id, clue in CLUES.items():
            if clue_id in {"bell", "hoofprint", "glow", "ribbon"}:
                combos.append((setting_id, clue_id))
    return combos


def choose_names(rng: random.Random, gender: str) -> tuple[str, str, str]:
    hero_name, hero_type = HEROES[gender]
    side_name, side_type = rng.choice(list(SIDEKICKS.values()))
    return hero_name, hero_type, side_name, side_type


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    setting = f["setting"]
    return [
        f'Write a short mystery for a child about an enchanted bicycle, a bull\'s clue, and a brave choice at {setting.place}.',
        f"Tell a gentle mystery where {hero.id} follows {clue.label} and learns that kindness can solve a scary moment.",
        f'Write a story for a young child that includes the words "enchant", "bicycle", and "bull\'s" and ends with a surprise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    clue = f["clue"]
    setting = f["setting"]
    bicycle = f["bicycle"]
    bull = f["bull"]
    return [
        QAItem(
            question=f"What did {hero.id} and {sidekick.label} find at {setting.place}?",
            answer=f"They found an old bicycle and a clue that made the place feel mysterious.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel worried when the bull appeared?",
            answer=f"{hero.id} felt worried because the bull's heavy steps made the mystery seem dangerous for a moment.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery and kindness in the story?",
            answer=f"{hero.id} showed bravery by staying calm and kindness by moving slowly and offering a gentle help instead of panic.",
        ),
        QAItem(
            question=f"What was the surprise in the ending?",
            answer=f"The surprise was that the scary moment was not a fight at all; it was a puzzle that a gentle choice solved.",
        ),
        QAItem(
            question=f"What happened to the bicycle at the end?",
            answer=f"The bicycle was found again, and its mystery was explained, so it was no longer hidden.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is staying steady when something feels scary, and doing what is right even while your heart is beating fast.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is acting gently and helpfully so another person or animal feels safe and cared for.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that changes what the reader thought would happen next.",
        ),
        QAItem(
            question="What does enchant mean?",
            answer="To enchant something means to make it seem magical, as if it has a special spell or charm on it.",
        ),
        QAItem(
            question="What is a bicycle for?",
            answer="A bicycle is a two-wheeled vehicle that a person rides by pedaling with their feet.",
        ),
        QAItem(
            question="What is a bull?",
            answer="A bull is a male cow. Bulls are usually large and strong, and people stay calm and careful around them.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- place(S).
mystery_combo(S,C) :- setting(S), clue(C).
valid_story(S,C) :- mystery_combo(S,C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("place", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery_combo/2."))
    return sorted(set(asp.atoms(model, "mystery_combo")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with an enchanted bicycle and a bull.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--clue", choices=CLUES)
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue = rng.choice(sorted(combos))
    gender = args.hero or rng.choice(list(HEROES))
    hero_name, hero_type, side_name, side_type = choose_names(rng, gender)
    return StoryParams(setting=setting, hero=gender, sidekick=args.sidekick or rng.choice(list(SIDEKICKS)), clue=clue, seed=None)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    hero_name, hero_type = HEROES[params.hero]
    side_label, side_type = SIDEKICKS[params.sidekick]
    world = tell(setting, hero_name, hero_type, side_label, side_type, CLUES[params.clue])
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
    StoryParams(setting="lane", hero="boy", sidekick="cat", clue="bell"),
    StoryParams(setting="barn", hero="girl", sidekick="neighbor", clue="hoofprint"),
    StoryParams(setting="garden", hero="boy", sidekick="sister", clue="glow"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_combo/2."))
        combos = sorted(set(asp.atoms(model, "mystery_combo")))
        print(f"{len(combos)} compatible mystery combos:")
        for c in combos:
            print(" ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
