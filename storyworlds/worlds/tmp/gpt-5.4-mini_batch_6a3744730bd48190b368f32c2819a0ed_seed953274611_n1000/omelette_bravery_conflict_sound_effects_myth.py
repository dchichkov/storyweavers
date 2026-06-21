#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/omelette_bravery_conflict_sound_effects_myth.py
================================================================================

A small mythic storyworld about a brave child, a quarrel, and a noisy omelette
that becomes a gift. The world is intentionally tiny: one domain, a few typed
entities, state-driven beats, and a declarative ASP twin for parity checks.

The seed image is a child trying to make an omelette for someone they care
about. The tension is whether the eggs will crack in time, whether the helper
will argue, and whether a scary sound turns courage into action. The ending is
a bright breakfast image: the omelette is finished, the conflict softens, and
the sound effects become part of the remembered myth.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/omelette_bravery_conflict_sound_effects_myth.py
    python storyworlds/worlds/gpt-5.4-mini/omelette_bravery_conflict_sound_effects_myth.py --all
    python storyworlds/worlds/gpt-5.4-mini/omelette_bravery_conflict_sound_effects_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/omelette_bravery_conflict_sound_effects_myth.py --verify
    python storyworlds/worlds/gpt-5.4-mini/omelette_bravery_conflict_sound_effects_myth.py --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_MIN = 5.0
CONFLICT_MIN = 1.0
SOUND_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    dawn_line: str


@dataclass
class Action:
    id: str
    verb: str
    sound: str
    crack: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ConflictBeat:
    id: str
    line: str
    force: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Resolution:
    id: str
    line: str
    final_image: str
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


@dataclass
class StoryParams:
    setting: str
    action: str
    conflict: str
    resolution: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "sunken_kitchen": Setting(
        id="sunken_kitchen",
        place="the sunken kitchen",
        scene="a little fire-lit kitchen at the edge of a sleeping hall",
        dawn_line="At dawn, the kitchen stones still held the cool of night.",
    ),
    "moon_dish": Setting(
        id="moon_dish",
        place="the moon-dish hearth",
        scene="a silver hearth where pots sang like tiny bells",
        dawn_line="By moonlight, the hearth gleamed like a round shield.",
    ),
}

ACTIONS = {
    "crack_eggs": Action(
        id="crack_eggs",
        verb="crack the eggs",
        sound="crack-crack!",
        crack="CRACK!",
        result="the pan began to fill with gold",
        tags={"egg", "omelette", "sound"},
    ),
    "whisk": Action(
        id="whisk",
        verb="whisk the eggs",
        sound="shh-shh-shh!",
        crack="SHH!",
        result="the mixture turned bright and smooth",
        tags={"egg", "omelette", "sound"},
    ),
}

CONFLICTS = {
    "fear": ConflictBeat(
        id="fear",
        line="the helper feared the flame and said the meal was too bold",
        force=1,
        tags={"conflict", "bravery"},
    ),
    "argue": ConflictBeat(
        id="argue",
        line="the helper argued that the kitchen should stay quiet and still",
        force=2,
        tags={"conflict", "bravery"},
    ),
}

RESOLUTIONS = {
    "gentle": Resolution(
        id="gentle",
        line="the brave child lowered the heat, kept the pan steady, and invited the helper to watch",
        final_image="the omelette rested in the pan like a small golden shield",
        tags={"omelette", "bravery"},
    ),
    "share": Resolution(
        id="share",
        line="the brave child handed over the spoon, and together they turned the arguing into a rhythm",
        final_image="the omelette puffed up and shone at the center of the table",
        tags={"omelette", "conflict"},
    ),
}

HEROES = [("Ari", "boy"), ("Mina", "girl"), ("Tala", "girl"), ("Eli", "boy")]
HELPERS = [("Ivo", "boy"), ("Sera", "girl"), ("Nia", "girl"), ("Oren", "boy")]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for aid in ACTIONS:
            for cid in CONFLICTS:
                for rid in RESOLUTIONS:
                    combos.append((sid, aid, cid, rid))
    return combos


def _pick_name(rng: random.Random, pool: list[tuple[str, str]], avoid: str = "") -> tuple[str, str]:
    choices = [x for x in pool if x[0] != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.conflict is None or c[2] == args.conflict)
              and (args.resolution is None or c[3] == args.resolution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, action, conflict, resolution = rng.choice(sorted(combos))
    hero, hero_gender = args.hero, args.hero_gender
    if hero is None or hero_gender is None:
        hero, hero_gender = _pick_name(rng, HEROES)
    helper, helper_gender = args.helper, args.helper_gender
    if helper is None or helper_gender is None or helper == hero:
        helper, helper_gender = _pick_name(rng, HELPERS, avoid=hero)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        action=action,
        conflict=conflict,
        resolution=resolution,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
    )


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.action not in ACTIONS:
        raise StoryError(f"Unknown action: {params.action}")
    if params.conflict not in CONFLICTS:
        raise StoryError(f"Unknown conflict: {params.conflict}")
    if params.resolution not in RESOLUTIONS:
        raise StoryError(f"Unknown resolution: {params.resolution}")

    setting = SETTINGS[params.setting]
    action = ACTIONS[params.action]
    conflict = CONFLICTS[params.conflict]
    resolution = RESOLUTIONS[params.resolution]

    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    omelette = world.add(Entity(id="omelette", kind="thing", type="food", label="omelette"))

    hero.memes["bravery"] = BRAVERY_MIN
    helper.memes["conflict"] = 0.0
    helper.memes["sound"] = 0.0

    world.say(f"{setting.dawn_line} In {setting.place}, {hero.id} stood before a warm pan and the promise of an omelette.")
    world.say(f"{hero.id} wanted to {action.verb}; {action.sound} the eggs were ready to change.")
    world.say(f"Then {helper.id} frowned and {conflict.line}.")
    helper.memes["conflict"] += conflict.force
    hero.memes["bravery"] += 1
    world.para()
    world.say(f"{hero.id} took a breath, because brave hearts do not flee at the first shout.")
    world.say(f"The pan answered with a bright {action.crack} and a cheerful {action.sound}")
    omelette.meters["filled"] += 1
    omelette.meters["warm"] += 1
    omelette.memes["wonder"] += 1
    helper.memes["sound"] += 1

    world.para()
    if params.resolution == "gentle":
        world.say(f"{resolution.line}.")
        helper.memes["conflict"] = 0.0
        helper.memes["trust"] += 1
    else:
        world.say(f"{resolution.line}.")
        helper.memes["conflict"] = max(0.0, helper.memes["conflict"] - 1)

    world.say(f"At the end, {resolution.final_image}, and {parent.label_word} smiled at the little feast.")
    omelette.meters["served"] += 1
    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        omelette=omelette,
        setting=setting,
        action=action,
        conflict=conflict,
        resolution=resolution,
        sound_effect=action.sound,
        outcome="shared",
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a small child that includes the word "omelette" and the sound "{f["sound_effect"]}".',
        f"Tell a brave kitchen myth where {f['hero'].id} and {f['helper'].id} disagree, then make breakfast anyway.",
        f"Write a short story about courage, conflict, and a noisy omelette in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    omelette = f["omelette"]
    action = f["action"]
    conflict = f["conflict"]
    resolution = f["resolution"]
    return [
        ("What did the hero want to make?",
         f"{hero.id} wanted to make an omelette. That is why the pan, the eggs, and the sound effects mattered so much."),
        ("What caused the conflict?",
         f"{helper.id} did not like the noisy cooking at first, so {conflict.line}. The worry made the kitchen feel tense for a moment."),
        ("How did the story end?",
         f"{resolution.line}. In the end, the omelette was finished and everyone sat down to eat."),
        ("What sound was important in the story?",
         f"The important sound was {action.sound}. It made the moment feel bold and a little magical, like a tiny drumbeat for breakfast."),
    ]


def world_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("What is an omelette?",
         "An omelette is a dish made by cooking beaten eggs in a pan. It can be folded and served warm."),
        ("What does bravery mean?",
         "Bravery means doing what needs to be done even when you feel nervous. Brave people can still be afraid and act anyway."),
        ("What is a sound effect in a story?",
         "A sound effect is a word or phrase that helps you imagine a noise, like crack or shh. It makes the action feel alive."),
        ("What is conflict in a story?",
         "Conflict is when characters want different things or disagree. It gives the story a turn before things get better."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict", cid))
    for rid in RESOLUTIONS:
        lines.append(asp.fact("resolution", rid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,C,R) :- setting(S), action(A), conflict(C), resolution(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic omelette storyworld with bravery and conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    StoryParams(setting="sunken_kitchen", action="crack_eggs", conflict="argue", resolution="gentle",
                hero="Ari", hero_gender="boy", helper="Sera", helper_gender="girl", parent="mother"),
    StoryParams(setting="moon_dish", action="whisk", conflict="fear", resolution="share",
                hero="Mina", hero_gender="girl", helper="Ivo", helper_gender="boy", parent="father"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.conflict is None or c[2] == args.conflict)
              and (args.resolution is None or c[3] == args.resolution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, action, conflict, resolution = rng.choice(sorted(combos))
    hero = args.hero or rng.choice([n for n, _ in HEROES])
    hero_gender = args.hero_gender or dict(HEROES).get(hero, rng.choice(["boy", "girl"]))
    helper = args.helper or rng.choice([n for n, _ in HELPERS if n != hero])
    helper_gender = args.helper_gender or dict(HELPERS).get(helper, rng.choice(["boy", "girl"]))
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        action=action,
        conflict=conflict,
        resolution=resolution,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate_from_args(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
    params.seed = args.seed
    return generate(params)


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in asp:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
