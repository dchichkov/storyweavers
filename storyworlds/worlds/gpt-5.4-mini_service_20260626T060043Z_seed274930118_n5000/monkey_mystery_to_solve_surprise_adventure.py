#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/monkey_mystery_to_solve_surprise_adventure.py
==============================================================================================================

A small adventure storyworld about a monkey, a mystery to solve, and a surprise.

Seed-tale premise:
- A curious monkey goes on a jungle adventure.
- Something important goes missing.
- The monkey follows clues, solves the mystery, and discovers a surprising hidden scene.

The world is deliberately tiny and constraint-checked:
- the monkey must be in a setting where the mystery can happen,
- the mystery must have a believable clue trail,
- the surprise must fit the setting and the mystery's resolution.

This script follows the Storyweavers world contract and supports:
default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp.
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
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"monkey", "boy", "male"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "female"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    terrain: str
    affords: set[str] = field(default_factory=set)
    mood: str = ""


@dataclass
class Mystery:
    id: str
    missing: str
    clue_noun: str
    clue_verb: str
    search_route: str
    loss_phrase: str
    risk_phrase: str
    clue_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    reveal: str
    reason: str
    image: str
    clue_kind: str
    tags: set[str] = field(default_factory=set)


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

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class StoryParams:
    setting: str
    mystery: str
    surprise: str
    name: str
    trait: str
    companion: str
    seed: Optional[int] = None


SETTINGS = {
    "canopy": Setting(place="the high jungle canopy", terrain="trees", affords={"trail", "listen", "climb"}, mood="bright"),
    "river": Setting(place="the riverbank", terrain="water", affords={"trail", "listen", "cross"}, mood="sparkling"),
    "ruins": Setting(place="the mossy ruins", terrain="stone", affords={"trail", "peek", "climb"}, mood="quiet"),
    "clearing": Setting(place="the moonlit clearing", terrain="grass", affords={"trail", "listen", "peek"}, mood="open"),
}

MYSTERIES = {
    "missing_banana": Mystery(
        id="missing_banana",
        missing="a ripe banana",
        clue_noun="banana peel",
        clue_verb="follow the peel",
        search_route="through the vines and over a branch bridge",
        loss_phrase="had vanished from the basket",
        risk_phrase="the snack basket would stay empty",
        clue_kind="peel",
        tags={"banana", "jungle"},
    ),
    "missing_map": Mystery(
        id="missing_map",
        missing="a hand-drawn map",
        clue_noun="muddy pawprints",
        clue_verb="follow the pawprints",
        search_route="past the ferns and around the big root",
        loss_phrase="was gone from the satchel",
        risk_phrase="the path would stay a mystery",
        clue_kind="pawprints",
        tags={"map", "trail"},
    ),
    "missing_bell": Mystery(
        id="missing_bell",
        missing="a shiny little bell",
        clue_noun="jingle marks",
        clue_verb="follow the jingling sound",
        search_route="across the stones beside the creek",
        loss_phrase="had slipped off the vine loop",
        risk_phrase="the guide sound would be lost",
        clue_kind="jingle",
        tags={"bell", "sound"},
    ),
}

SURPRISES = {
    "picnic": Surprise(
        id="picnic",
        reveal="a hidden picnic with coconut cakes",
        reason="the surprise was planned for the monkey's birthday",
        image="mango slices on a cloth under the leaves",
        clue_kind="peel",
        tags={"banana", "celebration"},
    ),
    "shortcut": Surprise(
        id="shortcut",
        reveal="a secret bridge over the stream",
        reason="the old map marked a faster route home",
        image="a vine bridge swaying gently in the green light",
        clue_kind="pawprints",
        tags={"map", "trail"},
    ),
    "waterfall": Surprise(
        id="waterfall",
        reveal="a silver waterfall behind the rocks",
        reason="the ringing bell was hanging near the hidden path",
        image="water shining like ribbons under the moon",
        clue_kind="jingle",
        tags={"bell", "water"},
    ),
}


GIRL_NAMES = ["Maya", "Lina", "Zuri", "Nora", "Ivy", "Tia"]
BOY_NAMES = ["Milo", "Koa", "Rio", "Arlo", "Theo", "Ben"]
TRAITS = ["curious", "brave", "playful", "spry", "clever", "lively"]
COMPANIONS = ["parrot", "turtle", "frog", "owl", "lizard"]


def compatible(mystery: Mystery, surprise: Surprise, setting: Setting) -> bool:
    if mystery.clue_kind != surprise.clue_kind:
        return False
    if setting.terrain == "water" and surprise.id == "shortcut":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_id, s in SETTINGS.items():
        for m_id, m in MYSTERIES.items():
            if s_id == "river" and m_id == "missing_bell":
                continue
            for r_id, r in SURPRISES.items():
                if compatible(m, r, s):
                    out.append((s_id, m_id, r_id))
    return out


def explain_rejection(mystery: Mystery, surprise: Surprise, setting: Setting) -> str:
    return (
        f"(No story: in {setting.place}, the clue trail for {mystery.missing} does not "
        f"believably lead to {surprise.reveal}. Try a surprise that matches the clue kind.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld: a monkey solves a mystery and finds a surprise."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--companion", choices=COMPANIONS)
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
    if args.setting and args.mystery and args.surprise:
        if not compatible(MYSTERIES[args.mystery], SURPRISES[args.surprise], SETTINGS[args.setting]):
            raise StoryError(explain_rejection(MYSTERIES[args.mystery], SURPRISES[args.surprise], SETTINGS[args.setting]))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.surprise is None or c[2] == args.surprise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, mystery, surprise = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(setting=setting, mystery=mystery, surprise=surprise, name=name, trait=trait, companion=companion)


def _act_search(world: World, monkey: Entity, mystery: Mystery) -> None:
    monkey.memes["curiosity"] = monkey.memes.get("curiosity", 0) + 1
    world.say(
        f"{monkey.id} spotted {mystery.clue_noun} and decided to {mystery.clue_verb}. "
        f"The trail led {mystery.search_route}."
    )
    world.say(f"That clue meant {mystery.loss_phrase}, so the adventure was now a mystery to solve.")


def _act_worry(world: World, monkey: Entity, mystery: Mystery) -> None:
    monkey.memes["worry"] = monkey.memes.get("worry", 0) + 1
    world.say(
        f"{monkey.pronoun().capitalize()} paused for a moment because {mystery.risk_phrase}."
    )


def _act_discover(world: World, monkey: Entity, mystery: Mystery, surprise: Surprise, companion: Entity) -> None:
    monkey.memes["joy"] = monkey.memes.get("joy", 0) + 1
    monkey.memes["surprise"] = monkey.memes.get("surprise", 0) + 1
    world.say(
        f"At last, {monkey.id} found the answer: {surprise.reveal}. "
        f"{surprise.reason.capitalize()}."
    )
    world.say(
        f"Behind the last leaves, {surprise.image} waited like a secret smiling back at {monkey.id} and {companion.id}."
    )


def tell(setting: Setting, mystery: Mystery, surprise: Surprise, hero_name: str, trait: str, companion_kind: str) -> World:
    world = World(setting)
    monkey = world.add(Entity(id=hero_name, kind="character", type="monkey", label="monkey"))
    companion = world.add(Entity(id=companion_kind, kind="character", type=companion_kind, label=companion_kind))
    lost = world.add(Entity(id="lost_item", type="thing", label=mystery.missing, phrase=mystery.missing, owner=monkey.id, carried_by=None, location="hidden"))

    world.say(
        f"{monkey.id} was a {trait} monkey who loved adventure in {setting.place}."
    )
    world.say(
        f"One morning, {monkey.id} noticed that {lost.label} {mystery.loss_phrase}."
    )
    world.say(
        f"{monkey.id} and the {companion_kind} promised to solve the mystery together."
    )

    world.para()
    _act_worry(world, monkey, mystery)
    _act_search(world, monkey, mystery)

    world.para()
    _act_discover(world, monkey, mystery, surprise, companion)

    world.para()
    world.say(
        f"In the end, {monkey.id} carried the {mystery.missing} home, and the jungle felt friendly and bright."
    )
    world.say(
        f"The surprise made the day even better, and {monkey.id} grinned at the shining path ahead."
    )

    world.facts.update(hero=monkey, companion=companion, lost=lost, mystery=mystery, surprise=surprise, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    surprise = f["surprise"]
    setting = f["setting"]
    return [
        f'Write a short adventure story for a child about a monkey in {setting.place} who tries to solve a mystery.',
        f'Tell a gentle jungle story where {hero.id} discovers that {mystery.missing} is missing and then finds {surprise.reveal}.',
        f'Write an adventurous story that includes a monkey, a clue trail, and a surprise at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    surprise = f["surprise"]
    setting = f["setting"]
    companion = f["companion"]

    return [
        QAItem(
            question=f"Who is the story about, and where does {hero.id} explore?",
            answer=f"The story is about {hero.id}, a monkey who explores {setting.place}.",
        ),
        QAItem(
            question=f"What mystery does {hero.id} try to solve?",
            answer=f"{hero.id} tries to solve the mystery of {mystery.missing}, which {mystery.loss_phrase}.",
        ),
        QAItem(
            question=f"What surprise does {hero.id} find at the end?",
            answer=f"{hero.id} finds {surprise.reveal}, and {surprise.image} makes the ending feel exciting and happy.",
        ),
        QAItem(
            question=f"Who helps {hero.id} during the adventure?",
            answer=f"The {companion.id} helps by staying with {hero.id} while they follow the clues together.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "banana": (
        "Why do monkeys like bananas?",
        "Monkeys often like bananas because bananas are soft, sweet, and easy to hold and eat.",
    ),
    "trail": (
        "What is a trail?",
        "A trail is a path that people or animals can follow through grass, trees, or rocks.",
    ),
    "water": (
        "What makes a waterfall special?",
        "A waterfall is special because water flows over rocks and drops down like a shining curtain.",
    ),
    "celebration": (
        "What is a picnic?",
        "A picnic is a meal eaten outside, often on a blanket with snacks to share.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery"].tags) | set(world.facts["surprise"].tags)
    out: list[QAItem] = []
    for tag, pair in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.append(QAItem(question=pair[0], answer=pair[1]))
    return out


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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,M,R) :- setting(S), mystery(M), surprise(R),
                      clue_kind(M,K), clue_kind(R,K),
                      compatible(S,M,R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_kind", mid, m.clue_kind))
    for rid, r in SURPRISES.items():
        lines.append(asp.fact("surprise", rid))
        lines.append(asp.fact("clue_kind", rid, r.clue_kind))
    for s_id, m_id, r_id in valid_combos():
        lines.append(asp.fact("compatible", s_id, m_id, r_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], SURPRISES[params.surprise], params.name, params.trait, params.companion)
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
    StoryParams(setting="canopy", mystery="missing_banana", surprise="picnic", name="Milo", trait="curious", companion="parrot"),
    StoryParams(setting="ruins", mystery="missing_map", surprise="shortcut", name="Koa", trait="brave", companion="turtle"),
    StoryParams(setting="clearing", mystery="missing_bell", surprise="waterfall", name="Tia", trait="playful", companion="owl"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mystery and args.surprise:
        if not compatible(MYSTERIES[args.mystery], SURPRISES[args.surprise], SETTINGS[args.setting]):
            raise StoryError(explain_rejection(MYSTERIES[args.mystery], SURPRISES[args.surprise], SETTINGS[args.setting]))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.surprise is None or c[2] == args.surprise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, mystery, surprise = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(setting=setting, mystery=mystery, surprise=surprise, name=name, trait=trait, companion=companion)


def build_asp_story_program() -> str:
    return asp_program("#show valid_story/3.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(build_asp_story_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(build_asp_story_program())
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible (setting, mystery, surprise) combos:\n")
        for item in combos:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.setting} (surprise: {p.surprise})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
