#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/scorpion_misunderstanding_fairy_tale.py
======================================================================

A standalone story world for a tiny fairy-tale misunderstanding: a small
scorpion is mistaken for a mean creature at first, then understood as a
frightened helper, and the tale ends with kindness, a safe home, and a new
friendship.

The world is intentionally small and state-driven:
- characters and objects carry physical meters and emotional memes
- a misunderstanding creates tension
- a calm explanation changes the story state
- the ending image proves what changed

The story is meant to read like a gentle fairy tale, with simple magic,
concrete actions, and a clear turn from fear to understanding.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "princess"}
        male = {"boy", "father", "dad", "man", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "queen", "father": "king"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    scene: str
    place_line: str
    danger_spot: str
    light_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TaleRole:
    id: str
    title: str
    greeting: str
    home_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    mistaken_for: str
    fear_line: str
    truth_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["understood"] >= THRESHOLD and ("calm" not in world.fired):
            world.fired.add(("calm",))
            e.memes["fear"] = 0.0
            out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("calm", "social", _r_calm)]


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


def _do_misunderstanding(world: World, scorpion: Entity, child: Entity, setting: Setting, misunderstanding: Misunderstanding) -> None:
    scorpion.meters["approached"] += 1
    child.memes["fear"] += 1
    world.say(
        f"In a little forest cottage by the {setting.scene}, {child.id} saw a small scorpion near {setting.danger_spot}. "
        f'"{misunderstanding.fear_line}" {child.id} cried.'
    )


def explain(world: World, helper: Entity, child: Entity, scorpion: Entity, misunderstanding: Misunderstanding) -> None:
    child.meters["understood"] += 1
    scorpion.meters["safe"] += 1
    scorpion.memes["hope"] += 1
    world.say(
        f"Then {helper.id} knelt beside {child.id} and smiled. "
        f'{helper.id} said, "{misunderstanding.truth_line}"'
    )
    world.say(
        f"{child.id} looked again and saw that the scorpion was not chasing anyone at all. "
        f"It was only trying to hide from the cold."
    )
    propagate(world, narrate=False)


def comfort(world: World, helper: Entity, child: Entity, setting: Setting) -> None:
    child.memes["fear"] = 0.0
    child.memes["joy"] += 1
    world.say(
        f"{helper.id} wrapped a warm cloak around {child.id}'s shoulders and led {child.id} back to the lantern light. "
        f"The little room grew soft and golden, and the scorpion was safe under a leaf by the window."
    )
    world.say(
        f"{child.id} waved instead of running. The scorpion waved with its tiny claws, and the cottage felt like a kinder place."
    )


def rescue(world: World, helper: Entity, child: Entity, scorpion: Entity) -> None:
    child.meters["rescued"] += 1
    scorpion.meters["rescued"] += 1
    world.say(
        f"{helper.id} gently moved the scorpion into a little shell by the hearth, where it could not be stepped on."
    )


def tell(setting: Setting, child_role: TaleRole, helper_role: TaleRole, misunderstanding: Misunderstanding,
         response: Response, child_name: str = "Mina", child_type: str = "girl",
         helper_name: str = "Queen Elara", helper_type: str = "queen", seed: Optional[int] = None) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", labels=[])
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    scorpion = world.add(Entity(id="scorpion", kind="character", type="thing", label="scorpion", role="creature", tags={"scorpion"}))
    world.add(Entity(id="lantern", kind="thing", type="thing", label="lantern", tags={"light"}))

    child.memes["curiosity"] = 1.0
    helper.memes["kindness"] = 1.0

    world.say(
        f"Once upon a time, in {setting.scene}, there lived {child_name} the curious child and {helper_name}, the gentle ruler."
    )
    world.say(
        f"{setting.place_line} {child_name} loved to follow the glow of the lantern and listen for tiny footsteps in the night."
    )
    world.say(
        f"One evening, {child_name} went near {setting.danger_spot} and found a small scorpion there."
    )
    world.para()
    _do_misunderstanding(world, scorpion, child, setting, misunderstanding)
    world.say(
        f"{child_name} stepped back, because the scorpion's tail looked sharp and strange in the moonlight."
    )
    world.say(
        f'But {helper_name} heard the cry and came with calm footsteps.'
    )
    world.para()
    explain(world, helper, child, scorpion, misunderstanding)
    rescue(world, helper, child, scorpion)
    comfort(world, helper, child, setting)
    world.para()
    world.say(
        f"From then on, {child_name} was careful, but not afraid to ask questions. "
        f"{helper_name} kept a small shell and a warm lamp by the window, and the scorpion slept safely nearby."
    )
    world.say(
        f"In that little fairy-tale home, fear turned into understanding, and understanding turned into a gentle friend."
    )
    world.facts.update(
        child=child, helper=helper, scorpion=scorpion, setting=setting,
        misunderstanding=misunderstanding, response=response, seed=seed,
        outcome="understood",
    )
    return world


SETTINGS = {
    "forest": Setting(
        id="forest",
        scene="an old forest",
        place_line="At the edge of the forest,",
        danger_spot="a moonlit stone step",
        light_line="The lantern shone over roots and moss.",
        tags={"forest", "moon"},
    ),
    "garden": Setting(
        id="garden",
        scene="a rose garden",
        place_line="Behind the roses,",
        danger_spot="a stone path near the fountain",
        light_line="The lantern made the petals glow like tiny crowns.",
        tags={"garden", "rose"},
    ),
    "castle": Setting(
        id="castle",
        scene="a quiet castle hall",
        place_line="Inside the castle,",
        danger_spot="a stair by the silver door",
        light_line="The lantern shone on the painted walls.",
        tags={"castle", "hall"},
    ),
}

CHARACTERS = {
    "child": TaleRole(id="child", title="child", greeting="little", home_line="lived by the hearth"),
    "helper": TaleRole(id="helper", title="queen", greeting="gentle", home_line="kept watch over the hall"),
}

MISUNDERSTANDINGS = {
    "scorpion": Misunderstanding(
        id="scorpion",
        mistaken_for="a mean beast",
        fear_line="A scorpion! It wants to sting me!",
        truth_line="It is only a little scorpion, and it is frightened too.",
        tags={"scorpion", "fear", "understanding"},
    ),
    "shadow": Misunderstanding(
        id="shadow",
        mistaken_for="a goblin",
        fear_line="A goblin in the dark!",
        truth_line="No goblin lives here. It is only a shadow and a scared creature.",
        tags={"shadow", "fear", "understanding"},
    ),
}

RESPONSES = {
    "gentle_lantern": Response(
        id="gentle_lantern",
        sense=3,
        power=3,
        text="lifted the lantern closer and saw the little truth in the dark",
        fail="shook the lantern too wildly and only frightened the little creature more",
        qa_text="lifted the lantern closer and saw the little truth in the dark",
        tags={"light", "calm"},
    ),
    "warm_shell": Response(
        id="warm_shell",
        sense=3,
        power=3,
        text="set out a warm shell and a soft leaf, then waited quietly",
        fail="tried to hurry the scorpion, but it hid deeper in the cracks",
        qa_text="set out a warm shell and a soft leaf, then waited quietly",
        tags={"safe", "calm"},
    ),
    "shout": Response(
        id="shout",
        sense=1,
        power=1,
        text="shouted so loudly that the little scorpion darted under the floorboard",
        fail="made everything worse by shouting",
        qa_text="shouted so loudly that the little scorpion darted under the floorboard",
        tags={"noise"},
    ),
}

CURATED = [
    StoryParams(
        setting="forest",
        child_name="Mina",
        child_type="girl",
        helper_name="Queen Elara",
        helper_type="queen",
        misunderstanding="scorpion",
        response="gentle_lantern",
    ),
    StoryParams(
        setting="garden",
        child_name="Pip",
        child_type="boy",
        helper_name="Queen Mira",
        helper_type="queen",
        misunderstanding="scorpion",
        response="warm_shell",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for mis in MISUNDERSTANDINGS:
            for resp in RESPONSES:
                if RESPONSES[resp].sense >= SENSE_MIN and mis == "scorpion":
                    combos.append((setting, mis, resp))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fairy tale of a scorpion and a misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(f"(Refusing response '{args.response}': it is too noisy for a fairy tale.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.misunderstanding is None or c[1] == args.misunderstanding)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, misunderstanding, response = rng.choice(sorted(combos))
    child_name = args.child_name or rng.choice(["Mina", "Pip", "Lina", "Bram", "Tessa", "Oren"])
    helper_name = args.helper_name or rng.choice(["Queen Elara", "Queen Mira", "Queen Selene"])
    return StoryParams(
        setting=setting,
        child_name=child_name,
        child_type="girl" if child_name in {"Mina", "Lina", "Tessa"} else "boy",
        helper_name=helper_name,
        helper_type="queen",
        misunderstanding=misunderstanding,
        response=response,
    )


def tell_story(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Unknown misunderstanding.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    return tell(
        SETTINGS[params.setting],
        CHARACTERS["child"],
        CHARACTERS["helper"],
        MISUNDERSTANDINGS[params.misunderstanding],
        RESPONSES[params.response],
        child_name=params.child_name,
        child_type=params.child_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle fairy tale about {f['child'].id} and a scorpion that is first misunderstood, then explained kindly.",
        f"Tell a child-friendly story in which a scorpion causes fear at first, but a queen helps everyone understand the truth.",
        "Write a fairy tale with a scared moment, a calm explanation, and a kind ending where the scorpion is safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    scorpion = f["scorpion"]
    mis = f["misunderstanding"]
    return [
        QAItem(
            question="What did the child first think about the scorpion?",
            answer=f"{child.id} first thought the scorpion was dangerous. The sharp tail looked scary, so the child cried out before anyone explained the truth.",
        ),
        QAItem(
            question="How did the helper change the misunderstanding?",
            answer=f"{helper.id} spoke calmly and explained that the scorpion was frightened, not mean. That explanation helped the child understand that the scorpion only wanted to stay safe.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"By the end, fear had turned into understanding. The scorpion was safe, the child was calm, and the cottage felt friendly instead of frightening.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a scorpion?",
            answer="A scorpion is a small creature with claws and a curled tail. It is best to look at one carefully and not touch it unless a grown-up says it is safe.",
        ),
        QAItem(
            question="Why can a lantern help in a dark place?",
            answer="A lantern gives gentle light without making a big flame. That makes it easier to see what is really there.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstood(scorpion) :- creature(scorpion).
calm_after_explanation :- understood(child), kind(helper).
outcome(kind) :- calm_after_explanation.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        lines.append(asp.fact("power", rid, resp.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("creature", "scorpion"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show misunderstood/1.\n#show outcome/1."))
    return sorted(set(asp.atoms(model, "misunderstood")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != {("scorpion",)}:
        rc = 1
        print("MISMATCH in ASP twin.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, misunderstanding=None, response=None, child_name=None, helper_name=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generation smoke test crashed: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show misunderstood/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible misunderstanding stories:")
        for item in asp_valid_combos():
            print(item)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
