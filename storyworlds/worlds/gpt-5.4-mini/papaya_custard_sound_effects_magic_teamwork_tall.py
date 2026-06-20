#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/papaya_custard_sound_effects_magic_teamwork_tall.py
===================================================================================

A tiny Tall Tale storyworld about a papaya pudding rescue: a grand, slightly
silly kitchen adventure where sound effects, a little magic, and teamwork turn a
mess into a feast.

Seed words:
- papaya
- custard

Features:
- Sound effects
- Magic
- Teamwork

Style:
- Tall Tale
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    title: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Ingredient:
    id: str
    label: str
    phrase: str
    texture: str
    color: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Sound:
    id: str
    label: str
    say: str
    action: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class MagicMove:
    id: str
    label: str
    verb: str
    effect: str
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Team:
    id: str
    label: str
    chant: str
    finish: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_splatter(world: World) -> list[str]:
    out = []
    bowl = world.entities.get("bowl")
    if bowl and bowl.meters["tipped"] >= THRESHOLD and ("splatter", "bowl") not in world.fired:
        world.fired.add(("splatter", "bowl"))
        if "floor" in world.entities:
            world.get("floor").meters["sticky"] += 1
        for kid in list(world.entities.values()):
            if kid.kind == "character":
                kid.memes["surprise"] += 1
        out.append("__splat__")
    return out


CAUSAL_RULES = [Rule("splatter", "physical", _r_splatter)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def title_talk(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f"Long ago, on a bright kitchen morning, {a.id} and {b.id} were the "
        f"sort of helpers who could stir a storm into a sunshine feast. "
        f"{a.id} wore {a.title}, and {b.id} wore {b.title}."
    )


def setup(world: World, a: Entity, b: Entity, ingredient: Ingredient, team: Team) -> None:
    a.memes["pride"] += 1
    b.memes["pride"] += 1
    world.say(
        f"They set out to make a tall-tale dessert with {ingredient.phrase}. "
        f"{team.chant}"
    )


def mistake(world: World, a: Entity, ingredient: Ingredient, sound: Sound) -> None:
    a.memes["boldness"] += 1
    world.say(
        f'But then {a.id} tried to carry the bowl one-handed. '
        f'{sound.say} The bowl gave a wobble, a wobble, a wobble.'
    )


def warn(world: World, b: Entity, ingredient: Ingredient) -> None:
    b.memes["care"] += 1
    world.say(
        f'{b.id} pointed at the {ingredient.label} and cried, '
        f'"Careful now! That papaya is slippery as a moonfish in rain boots!"'
    )


def teamwork_save(world: World, a: Entity, b: Entity, ingredient: Ingredient,
                  magic: MagicMove, sound: Sound, team: Team) -> None:
    bowl = world.get("bowl")
    a.memes["helpful"] += 1
    b.memes["helpful"] += 1
    world.say(
        f"Then they called on {magic.label}. {magic.verb.capitalize()}! "
        f"The spoon glimmered, the bowl lightened, and {b.id} tapped the rim "
        f"while {a.id} steadied the handle."
    )
    world.say(
        f"{sound.action.capitalize()} went the kitchen chairs as they moved in "
        f"one smooth dance, {team.finish}."
    )
    bowl.meters["tipped"] = 0.0
    bowl.meters["saved"] = 1.0
    world.get("custard").meters["whisked"] = 1.0
    world.say(
        f"Together they kept the {ingredient.label} from tumbling, and the "
        f"custard stayed as smooth as a cloud on a warm day."
    )


def ending(world: World, a: Entity, b: Entity, ingredient: Ingredient) -> None:
    world.say(
        f"At last, they spooned the golden dessert into a bowl, topped it with "
        f"papaya, and laughed at the near-miss. The kitchen smelled sweet, and "
        f"the tall tale ended with two proud helpers and one shining custard."
    )


def tell(ingredient: Ingredient, sound: Sound, magic: MagicMove, team: Team,
         hero_a: str = "Mira", hero_b: str = "Jo", title_a: str = "the daring spoon-keeper",
         title_b: str = "the quick-bellied whisker") -> World:
    world = World()
    a = world.add(Entity(hero_a, kind="character", type="girl", title=title_a, role="instigator"))
    b = world.add(Entity(hero_b, kind="character", type="boy", title=title_b, role="helper"))
    bowl = world.add(Entity("bowl", type="thing", label="bowl"))
    world.add(Entity("custard", type="thing", label="custard"))
    world.add(Entity("floor", type="thing", label="floor"))
    title_talk(world, a, b)
    world.para()
    setup(world, a, b, ingredient, team)
    mistake(world, a, ingredient, sound)
    warn(world, b, ingredient)
    bowl.meters["tipped"] += 1
    propagate(world, narrate=False)
    world.para()
    teamwork_save(world, a, b, ingredient, magic, sound, team)
    world.para()
    ending(world, a, b, ingredient)
    world.facts.update(
        hero_a=a, hero_b=b, ingredient=ingredient, sound=sound, magic=magic, team=team,
        bowl=bowl, outcome="saved", title_a=title_a, title_b=title_b
    )
    return world


INGREDIENTS = {
    "papaya": Ingredient("papaya", "papaya", "papaya cubes", "slippery", "golden", {"papaya"}),
    "custard": Ingredient("custard", "custard", "custard cream", "soft", "yellow", {"custard"}),
}

SOUNDS = {
    "sizzle": Sound("sizzle", "sizzle", '"Sizzle-snap!"', "The pan answered with a sizzle.", {"sound"}),
    "plop": Sound("plop", "plop", '"Plop-plop!"', "The spoon went plop, plop on the edge.", {"sound"}),
    "clang": Sound("clang", "clang", '"Clang-a-lang!"', "The bowl rang clang, bright as a bell.", {"sound"}),
}

MAGIC = {
    "glimmer": MagicMove("glimmer", "glimmering magic", "glimmered", "a shining spell of steadiness", 1, {"magic"}),
    "hover": MagicMove("hover", "hovering magic", "hovered", "a levitating spell for the bowl", 1, {"magic"}),
    "knot": MagicMove("knot", "knot-tying magic", "knotted", "a spell that made the handle easy to hold", 1, {"magic"}),
}

TEAMS = {
    "duo": Team("duo", "the two-person team", '"One to hold, one to guide!"', "moved like a tiny parade", {"teamwork"}),
    "trio": Team("trio", "the kitchen team", '"Hands together, hearts together!"', "worked like a well-trained wagon wheel", {"teamwork"}),
}

TRAITS = ["brave", "cheerful", "clever", "careful", "steady"]


@dataclass
@dataclass
class StoryParams:
    ingredient: str
    sound: str
    magic: str
    team: str
    hero_a: str
    hero_b: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(i, s, m, t) for i in INGREDIENTS for s in SOUNDS for m in MAGIC for t in TEAMS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale kitchen storyworld with papaya, custard, magic, and teamwork.")
    ap.add_argument("--ingredient", choices=INGREDIENTS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--team", choices=TEAMS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid combinations available.")
    ingredient = args.ingredient or rng.choice(sorted(INGREDIENTS))
    sound = args.sound or rng.choice(sorted(SOUNDS))
    magic = args.magic or rng.choice(sorted(MAGIC))
    team = args.team or rng.choice(sorted(TEAMS))
    if ingredient not in INGREDIENTS:
        raise StoryError("Unknown ingredient.")
    if args.name_a and args.name_b and args.name_a == args.name_b:
        raise StoryError("The two helpers need different names.")
    name_a = args.name_a or rng.choice(["Mira", "Nia", "Ada", "Lena"])
    name_b = args.name_b or rng.choice([n for n in ["Jo", "Bo", "Kai", "Tom"] if n != name_a])
    return StoryParams(ingredient, sound, magic, team, name_a, name_b)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a child that includes "{f["ingredient"].label}" and "{f["sound"].label}".',
        f"Tell a kitchen adventure where {f['hero_a'].id} and {f['hero_b'].id} use {f['magic'].label} and teamwork to save custard.",
        f"Write a magical story with sound effects, papaya, custard, and a happy ending about two helpers.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What were the helpers making?",
            answer="They were making a tall-tale dessert with custard and papaya. The whole trouble came while they were trying to carry it together."
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"They used {f['magic'].label} and worked together. {f['hero_b'].id} steadied the bowl while {f['hero_a'].id} held the handle, so the custard stayed safe."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily with the dessert saved, the kitchen calm, and both helpers proud of their teamwork. The papaya and custard were ready to eat."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is papaya?", "Papaya is a sweet tropical fruit with soft orange flesh. People often eat it fresh or use it in desserts."),
        QAItem("What is custard?", "Custard is a soft, creamy dessert made from milk, eggs, and sugar. It can be spooned into bowls or used as a filling."),
        QAItem("What does teamwork mean?", "Teamwork means people help each other and do a job together. When a team shares the work, hard jobs can become easier."),
        QAItem("What is a sound effect in a story?", "A sound effect is a word or phrase that helps you hear the action in your mind. It can make a story feel lively and big."),
        QAItem("What is magic in a story?", "Magic is a make-believe power that can do impossible things. In stories, magic can help solve a problem in a surprising way."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.title:
            bits.append(f"title={e.title}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("ingredient", k) for k in INGREDIENTS]
    lines += [asp.fact("sound", k) for k in SOUNDS]
    lines += [asp.fact("magic", k) for k in MAGIC]
    lines += [asp.fact("team", k) for k in TEAMS]
    return "\n".join(lines)


ASP_RULES = r"""
valid(I,S,M,T) :- ingredient(I), sound(S), magic(M), team(T).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(ingredient=None, sound=None, magic=None, team=None, name_a=None, name_b=None), random.Random(7)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(INGREDIENTS[params.ingredient], SOUNDS[params.sound], MAGIC[params.magic], TEAMS[params.team], params.hero_a, params.hero_b)
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
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("papaya", "clang", "glimmer", "trio", "Mira", "Jo"),
            StoryParams("custard", "sizzle", "hover", "duo", "Ada", "Kai"),
            StoryParams("papaya", "plop", "knot", "trio", "Lena", "Tom"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
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
            header = f"### {p.hero_a} & {p.hero_b}: {p.ingredient}, {p.sound}, {p.magic}, {p.team}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
