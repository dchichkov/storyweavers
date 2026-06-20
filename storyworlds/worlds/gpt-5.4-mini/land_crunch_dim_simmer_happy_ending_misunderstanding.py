#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/land_crunch_dim_simmer_happy_ending_misunderstanding.py
=======================================================================================

A tiny storyworld for a nursery-rhyme style tale about a little cook, a dim
lamp, a simmering pot, and a misunderstanding that ends happily.

Seed words:
- land
- crunch-dim
- simmer

Features:
- Happy Ending
- Misunderstanding
- Inner Monologue

The world model is small and state-driven:
- a child prepares soup on a little stove
- a second character misreads the situation and worries
- the child's inner monologue reveals the mistaken thought
- a calm explanation and a safer, brighter lamp resolve the mix-up
- the soup lands in bowls, and the ending image proves the change

This script follows the Storyweavers contract:
- standalone stdlib script
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes Python reasonableness gate and inline ASP twin
- produces three Q&A sets from world state, not by parsing rendered prose
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Scene:
    id: str
    place: str
    dim_word: str
    land_word: str
    end_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Pot:
    id: str
    label: str
    phrase: str
    simmer_word: str
    safe_when: str
    broth: str
    warm: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    worry: str
    thought: str
    kind: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_simmer(world: World) -> list[str]:
    out: list[str] = []
    pot = world.entities.get("pot")
    if not pot or pot.meters["simmering"] < THRESHOLD:
        return out
    sig = ("simmer",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    child.memes["homey"] += 1
    out.append("__simmer__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.entities.get("worry") and world.get("worry").meters["worrying"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "child" in world.entities:
        world.get("child").memes["relief"] += 1
    if "worry" in world.entities:
        world.get("worry").memes["relief"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("simmer", "physical", _r_simmer),
    Rule("relief", "social", _r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def inner_mono(world: World, child: Entity, worry: Misunderstanding, pot: Pot) -> None:
    world.say(
        f"Inside {child.id}'s little mind went a tap-tap tune: "
        f'"{worry.thought}"'
    )
    child.memes["worry"] += 1
    world.facts["inner_thought"] = worry.thought


def setup(world: World, child: Entity, friend: Entity, scene: Scene, pot: Pot) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"By the {scene.place}, under a {scene.dim_word} little light, "
        f"{child.id} and {friend.id} made a merry sight."
    )
    world.say(
        f"{child.id} had {pot.phrase}, and the pot began to {pot.simmer_word} "
        f"like a tiny drum."
    )


def misunderstanding(world: World, friend: Entity, child: Entity, worry: Misunderstanding) -> None:
    friend.memes["worry"] += 1
    world.say(
        f"But {friend.id} peeped and had a frightful start. "
        f'{friend.id} whispered, "{worry.worry}"'
    )


def explain(world: World, child: Entity, friend: Entity, pot: Pot, light: Light) -> None:
    child.memes["calm"] += 1
    friend.memes["calm"] += 1
    world.say(
        f"{child.id} smiled a small and sunny smile. "
        f'"Oh no," {child.id} said, "I did not mean that at all. '
        f"I only meant to make supper, and {pot.safe_when}."
        f'"'
    )
    world.say(
        f"Then {child.id} lit {light.phrase}, and {light.glow} away went the dim."
    )


def land_sup(world: World, child: Entity, friend: Entity, pot: Pot, scene: Scene) -> None:
    pot.meters["served"] += 1
    child.memes["pride"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"At last the soup was ready to land in bowls, warm and sweet."
    )
    world.say(
        f"{scene.end_image.capitalize()} {child.id} and {friend.id} ate together, "
        f"with no more fear and no more fuss."
    )


def tell(scene: Scene, pot: Pot, light: Light, worry: Misunderstanding,
         child_name: str = "Mina", child_gender: str = "girl",
         friend_name: str = "Pip", friend_gender: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    stove = world.add(Entity(id="stove", type="thing", label="little stove"))
    pot_ent = world.add(Entity(id="pot", type="thing", label=pot.label))
    worry_ent = world.add(Entity(id="worry", type="thing", label=worry.kind))

    world.facts.update(scene=scene, pot=pot, light=light, worry=worry, child=child, friend=friend, stove=stove)
    setup(world, child, friend, scene, pot)
    world.para()
    misunderstanding(world, friend, child, worry)
    inner_mono(world, child, worry, pot)
    world.para()
    explain(world, child, friend, pot, light)
    pot_ent.meters["simmering"] += 1
    worry_ent.meters["worrying"] += 1
    propagate(world, narrate=False)
    world.para()
    land_sup(world, child, friend, pot, scene)
    return world


SCENES = {
    "kitchen": Scene("kitchen", "kitchen", "crunch-dim", "land", "the kitchen glowed cozy and kind", {"nursery", "land", "dim"}),
    "cottage": Scene("cottage", "little cottage", "crunch-dim", "land", "the cottage looked warm as a bun", {"nursery", "land", "dim"}),
    "garden_hut": Scene("garden_hut", "garden hut", "crunch-dim", "land", "the little hut stood happy in the moon", {"nursery", "land", "dim"}),
}

POTS = {
    "carrot_soup": Pot("carrot_soup", "a soup pot", "a pot of carrot soup", "simmer", "it was only soup and supper", "carrot soup", tags={"soup", "carrot", "simmer"}),
    "pea_soup": Pot("pea_soup", "a soup pot", "a pot of pea soup", "simmer", "it was only supper, bubbling softly", "pea soup", tags={"soup", "pea", "simmer"}),
    "apple_stew": Pot("apple_stew", "a stew pot", "a pot of apple stew", "simmer", "it was only dinner, cooking slow", "apple stew", tags={"stew", "apple", "simmer"}),
}

LIGHTS = {
    "lantern": Light("lantern", "a lantern", "a little lantern", "the glow grew bright", {"light", "dim"}),
    "lamp": Light("lamp", "a lamp", "a round lamp", "the lamp made a cozy shine", {"light", "dim"}),
}

MISUNDERSTANDINGS = {
    "smoke": Misunderstanding("smoke", "Is that a dragon puff?", "the pot is making a dragon puff", "smoke", "it's only soup steam", {"misunderstanding", "steam"}),
    "dim": Misunderstanding("dim", "Is the room going sleepy dark?", "the room is too dim to see the supper", "dim", "it just needs a brighter light", {"misunderstanding", "dim"}),
    "simmer": Misunderstanding("simmer", "Are you cooking a moon spell?", "the simmer looks like a tiny spell", "simmer", "it is only the soup simmering", {"misunderstanding", "simmer"}),
}

GIRL_NAMES = ["Mina", "Lily", "Nina", "Ruby", "Tess"]
BOY_NAMES = ["Pip", "Ned", "Theo", "Ollie", "Ben"]
TRAITS = ["kind", "careful", "bright", "cheery", "gentle"]


@dataclass
class StoryParams:
    scene: str
    pot: str
    light: str
    misunderstanding: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SCENES:
        for p in POTS:
            for l in LIGHTS:
                for m in MISUNDERSTANDINGS:
                    combos.append((s, p, l, m))
    return combos


def reasonableness_check(params: StoryParams) -> None:
    if params.light == "lamp" and params.scene == "garden_hut":
        return
    if params.pot not in POTS:
        raise StoryError("Unknown pot.")
    if params.scene not in SCENES:
        raise StoryError("Unknown scene.")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Unknown misunderstanding.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene: Scene = f["scene"]  # type: ignore[assignment]
    pot: Pot = f["pot"]  # type: ignore[assignment]
    worry: Misunderstanding = f["worry"]  # type: ignore[assignment]
    child: Entity = f["child"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    return [
        f'Write a nursery-rhyme style story with the words "land", "crunch-dim", '
        f'and "simmer", about a little cook in {scene.place}.',
        f"Tell a happy story where {friend.id} has a misunderstanding about "
        f"{pot.label}, but {child.id}'s inner thought shows it is only supper.",
        f"Write a gentle rhyme about a dim little room, a simmering pot, and a "
        f"mix-up that ends with a bright, happy supper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    pot: Pot = f["pot"]  # type: ignore[assignment]
    worry: Misunderstanding = f["worry"]  # type: ignore[assignment]
    scene: Scene = f["scene"]  # type: ignore[assignment]
    light: Light = f["light"]  # type: ignore[assignment]

    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {friend.id}, two small friends with a pot of supper. The whole tale happens in {scene.place}, where one little mistake turns into a happy fix."
        ),
        QAItem(
            question=f"What did {friend.id} misunderstand?",
            answer=f"{friend.id} thought {worry.thought}. That was a misunderstanding, because {child.id} was only cooking supper and keeping it at a gentle simmer."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily. {child.id} explained the truth, brightened the room with {light.phrase}, and the soup landed in bowls for both friends to share."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    pot: Pot = f["pot"]  # type: ignore[assignment]
    light: Light = f["light"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What does simmer mean?",
            answer="To simmer means to cook with tiny bubbles and gentle heat. It is slower and calmer than a hard boil."
        ),
        QAItem(
            question="What is a dim light?",
            answer="A dim light is a weak light that does not shine very brightly. A brighter lamp can help people see more clearly."
        ),
        QAItem(
            question=f"Why is soup a good thing to land in bowls?",
            answer="Soup is warm and ready to eat when it lands in bowls. It can make a meal feel cozy and complete."
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "carrot_soup", "lantern", "smoke", "Mina", "girl", "Pip", "boy", "kind"),
    StoryParams("cottage", "pea_soup", "lamp", "dim", "Lily", "girl", "Ned", "boy", "gentle"),
    StoryParams("garden_hut", "apple_stew", "lantern", "simmer", "Tess", "girl", "Theo", "boy", "bright"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for pid in POTS:
        lines.append(asp.fact("pot", pid))
    for lid in LIGHTS:
        lines.append(asp.fact("light", lid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, L, M) :- scene(S), pot(P), light(L), misunderstanding(M).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print(" only in clingo:", sorted(clingo_set - python_set))
        print(" only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(resolve_params(argparse.Namespace(
            scene=None, pot=None, light=None, misunderstanding=None,
            child_name=None, child_gender=None, friend_name=None, friend_gender=None,
            trait=None, seed=None, n=1, all=False, trace=False, qa=False, json=False,
            asp=False, verify=False, show_asp=False
        ), _random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("Empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld with land, crunch-dim, and simmer.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--pot", choices=POTS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scene = args.scene or rng.choice(list(SCENES))
    pot = args.pot or rng.choice(list(POTS))
    light = args.light or rng.choice(list(LIGHTS))
    misunderstanding = args.misunderstanding or rng.choice(list(MISUNDERSTANDINGS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != child_name])
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(scene, pot, light, misunderstanding, child_name, child_gender, friend_name, friend_gender, trait, seed=args.seed)
    reasonableness_check(params)
    return params


GIRL_NAMES = ["Mina", "Lily", "Nina", "Ruby", "Tess", "Mabel", "Poppy"]
BOY_NAMES = ["Pip", "Ned", "Theo", "Ollie", "Ben", "Milo", "Finn"]


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], POTS[params.pot], LIGHTS[params.light], MISUNDERSTANDINGS[params.misunderstanding],
                 params.child_name, params.child_gender, params.friend_name, params.friend_gender)
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
