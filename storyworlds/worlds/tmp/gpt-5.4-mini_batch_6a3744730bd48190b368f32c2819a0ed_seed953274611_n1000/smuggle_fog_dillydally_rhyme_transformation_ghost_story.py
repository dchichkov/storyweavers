#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/smuggle_fog_dillydally_rhyme_transformation_ghost_story.py
==========================================================================================

A small standalone storyworld in a ghost-story mood: a child tries to smuggle a
tiny thing through fog, dillydallies when the lights go strange, and ends up
changed by a spooky but gentle transformation. The story is built from simulated
state: meters for fog, chill, shimmer, and change; memes for fear, courage, and
wonder. It includes a little rhyme beat and a clear turn where the world itself
changes shape.

The world model is intentionally narrow: the core tension is whether the child
can cross the foggy path and deliver the hidden parcel before the fog makes
everything look uncanny. The resolution is not a fight, but a transformation:
the hidden thing reveals what it really is, and the child becomes bolder.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/smuggle_fog_dillydally_rhyme_transformation_ghost_story.py
    python storyworlds/worlds/gpt-5.4-mini/smuggle_fog_dillydally_rhyme_transformation_ghost_story.py --qa
    python storyworlds/worlds/gpt-5.4-mini/smuggle_fog_dillydally_rhyme_transformation_ghost_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    plural: bool = False
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    foggy: bool = True


@dataclass
class Parcel:
    id: str
    thing: str
    cover: str
    secret: str
    reveals: str
    transformed_into: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    rhyme: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    parcel: str
    charm: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_fog(world: World) -> list[str]:
    out: list[str] = []
    if world.get("fog").meters["thick"] < THRESHOLD:
        return out
    sig = ("fog",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    helper = world.get("helper")
    child.memes["unease"] += 1
    helper.memes["alert"] += 1
    out.append("The fog pressed close enough to make even familiar stones seem strange.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    parcel = world.get("parcel")
    if parcel.meters["revealed"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    child.memes["wonder"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    out.append("The hidden thing changed shape, and the air around it shimmered like a candle seen through lace.")
    return out


def _r_courage(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["wonder"] < THRESHOLD or helper.memes["courage"] < THRESHOLD:
        return out
    sig = ("courage",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["courage"] += 1
    out.append("A little brave feeling stayed behind after the scare.")
    return out


CAUSAL_RULES = [Rule("fog", _r_fog), Rule("transform", _r_transform), Rule("courage", _r_courage)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_smuggle(parcel: Parcel) -> bool:
    return "smuggle" in parcel.tags


def path_is_foggy(setting: Setting) -> bool:
    return setting.foggy


def reveal_amount(fog_thickness: int, delay: int) -> int:
    return max(0, fog_thickness - delay)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghostly storyworld: fog, rhyme, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--parcel", choices=PARCELS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--child", choices=CHILD_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PARCELS:
            for c in CHARMS:
                if can_smuggle(PARCELS[p]) and path_is_foggy(SETTINGS[s]):
                    combos.append((s, p, c))
    return combos


def explain_rejection(setting: Setting, parcel: Parcel) -> str:
    if not setting.foggy:
        return f"(No story: {setting.place} is too clear for a fog-ghost tale.)"
    if "smuggle" not in parcel.tags:
        return f"(No story: {parcel.thing} does not fit the smuggle premise.)"
    return "(No story: this combination is not reasonable.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and not SETTINGS[args.setting].foggy:
        raise StoryError(explain_rejection(SETTINGS[args.setting], PARCELS[args.parcel] if args.parcel else next(iter(PARCELS.values()))))
    combos = [c for c in valid_combos()
              if args.setting is None or c[0] == args.setting
              if args.parcel is None or c[1] == args.parcel
              if args.charm is None or c[2] == args.charm]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, parcel, charm = rng.choice(sorted(combos))
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != child])
    return StoryParams(setting=setting, parcel=parcel, charm=charm, child=child, child_gender=CHILD_GENDERS[child], helper=helper, helper_gender=HELPER_GENDERS[helper])


def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper, role="helper"))
    fog = world.add(Entity(id="fog", label="fog"))
    parcel = world.add(Entity(id="parcel", label=PARCELS[params.parcel].thing, attrs={"secret": PARCELS[params.parcel].secret}))
    charm = world.add(Entity(id="charm", label=CHARMS[params.charm].label))
    child.memes["fear"] = 1
    helper.memes["courage"] = 1
    fog.meters["thick"] = 2
    world.facts.update(child=child, helper=helper, fog=fog, parcel=parcel, charm=charm, params=params)
    return world


def tell(world: World, params: StoryParams) -> World:
    child = world.get("child")
    helper = world.get("helper")
    parcel = world.get("parcel")
    charm = world.get("charm")
    setting = world.setting
    world.say(f"That evening, {child.label} and {helper.label} walked through {setting.place} where {setting.detail}.")
    world.say(f'{child.label} had a plan to smuggle the {PARCELS[params.parcel].thing} past the old gate, and the fog made every lamp look tired.')
    world.para()
    world.say(f'{helper.label} whispered a rhyme: "{CHARMS[params.charm].rhyme}"')
    world.say(f'But {child.label} began to dillydally, because the fog kept changing the shape of the hedges.')
    child.memes["fear"] += 1
    child.memes["delay"] += 1
    child.meters["delay"] += 1
    world.get("fog").meters["thick"] += 1
    propagate(world, narrate=True)
    world.para()
    parcel.meters["revealed"] += reveal_amount(2, 1)
    world.say(f'At last the bundle opened, and the {PARCELS[params.parcel].thing} was no ordinary thing at all.')
    world.say(f'It had been hiding {PARCELS[params.parcel].secret}, and the fog turned silver around it.')
    propagate(world, narrate=True)
    world.para()
    child.memes["courage"] += 1
    world.say(f'{child.label} stopped trembling, smiled, and touched the shining thing first.')
    world.say(f'With a soft pop, it transformed into {PARCELS[params.parcel].transformed_into}, and the night felt kind instead of cold.')
    child.meters["changed"] += 1
    helper.meters["changed"] += 1
    world.say(f'{child.label} and {helper.label} went home under the fog, humming the rhyme and carrying the new shape gently in both hands.')
    world.facts["outcome"] = "transformed"
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a ghost-story for a child that includes the words "smuggle", "fog", and "dillydally".',
        f"Tell a spooky but gentle story where {p.child} tries to smuggle a {PARCELS[p.parcel].thing} through fog, then something transforms at the end.",
        f'Write a rhyme-filled ghost story with fog, a hidden parcel, and a transformation that makes the ending feel safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    parcel = PARCELS[p.parcel]
    child = p.child
    helper = p.helper
    return [
        QAItem(question="What was the child trying to do?", answer=f"{child} was trying to smuggle the {parcel.thing} through the fog without being noticed. The journey felt secret and spooky because everything looked washed in gray."),
        QAItem(question="Why did the child dillydally?", answer=f"{child} dillydallied because the fog kept making the path look strange and slow. The delay gave the night time to feel even more ghostly before the hidden thing was opened."),
        QAItem(question="What changed at the end?", answer=f"The hidden thing transformed into {parcel.transformed_into}. That change turned the scary mystery into something gentle, so the story ended with wonder instead of fear."),
        QAItem(question=f"How did {helper} help?", answer=f"{helper} spoke a rhyme and stayed brave beside {child}. The rhyme helped keep the child moving until the secret could be revealed."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    parcel = PARCELS[p.parcel]
    charm = CHARMS[p.charm]
    return [
        QAItem(question="What is fog?", answer="Fog is a cloud that rests on the ground and makes everything look soft and dim. It can hide the shape of trees, fences, and paths."),
        QAItem(question="What does smuggle mean?", answer="To smuggle something means to carry it secretly from one place to another. People smuggle things when they do not want others to see them."),
        QAItem(question="What is a rhyme?", answer="A rhyme is a pair of words or lines that sound alike at the end. Rhymes can make a story feel playful even when it is spooky."),
        QAItem(question="What is transformation in a story?", answer="Transformation is when something changes into a different form. In stories, it often makes a surprise feel magical."),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] if isinstance(x, tuple) else x for x in world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "lantern_lane": Setting(id="lantern_lane", place="Lantern Lane", detail="the cottages leaned close and the windows blinked like sleepy eyes", foggy=True),
    "graveyard_path": Setting(id="graveyard_path", place="the graveyard path", detail="the stones stood in rows and the grass whispered underfoot", foggy=True),
    "harbor_mist": Setting(id="harbor_mist", place="the harbor", detail="the water breathed mist against the docks", foggy=True),
}

PARCELS = {
    "key": Parcel(id="key", thing="silver key", cover="cloth", secret="the words to an old door", reveals="a latch", transformed_into="a tiny star-shaped lamp", tags={"smuggle"}),
    "bell": Parcel(id="bell", thing="brass bell", cover="paper", secret="a sleeping song", reveals="a chime", transformed_into="a warm little moon lantern", tags={"smuggle"}),
    "seed": Parcel(id="seed", thing="black seed", cover="moss", secret="a green pulse", reveals="a sprout", transformed_into="a ghostly white flower", tags={"smuggle"}),
}

CHARMS = {
    "whisper": Charm(id="whisper", label="whisper charm", rhyme="Fog and stone, soft and slow; keep your secret, let it glow.", effect="steady"),
    "tune": Charm(id="tune", label="lantern tune", rhyme="Dilly and dally, over the hill; follow the moon, and be still.", effect="steady"),
}

CHILD_NAMES = ["Mina", "Theo", "Nora", "Finn", "Lina", "Owen"]
HELPER_NAMES = ["Mabel", "Mr. Vale", "Aunt June", "Pip", "Rowan", "Etta"]
CHILD_GENDERS = {"Mina": "girl", "Theo": "boy", "Nora": "girl", "Finn": "boy", "Lina": "girl", "Owen": "boy"}
HELPER_GENDERS = {"Mabel": "woman", "Mr. Vale": "man", "Aunt June": "woman", "Pip": "boy", "Rowan": "boy", "Etta": "girl"}


CURATED = [
    StoryParams(setting="graveyard_path", parcel="key", charm="whisper", child="Mina", child_gender="girl", helper="Mabel", helper_gender="woman"),
    StoryParams(setting="harbor_mist", parcel="bell", charm="tune", child="Theo", child_gender="boy", helper="Mr. Vale", helper_gender="man"),
    StoryParams(setting="lantern_lane", parcel="seed", charm="whisper", child="Nora", child_gender="girl", helper="Etta", helper_gender="girl"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("foggy", sid))
    for pid, p in PARCELS.items():
        lines.append(asp.fact("parcel", pid))
        lines.append(asp.fact("smuggleable", pid))
    for cid in CHARMS:
        lines.append(asp.fact("charm", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,C) :- setting(S), parcel(P), charm(C), foggy(S), smuggleable(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP/Python parity.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, parcel=None, charm=None, child=None, helper=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: ASP parity and generate() smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.parcel not in PARCELS or params.charm not in CHARMS:
        raise StoryError("Invalid parameters.")
    world = setup_world(params)
    tell(world, params)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        for i in range(args.n):
            try:
                params = resolve_params(args, random.Random((args.seed or 0) + i))
            except StoryError as e:
                print(e)
                return
            params.seed = (args.seed or 0) + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
