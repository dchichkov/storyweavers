#!/usr/bin/env python3
"""
storyworlds/worlds/ivy_moral_value_sound_effects_transformation_folk.py
=======================================================================

A small folk-tale story world about Ivy, moral choice, sound effects, and a
gentle transformation.

Premise:
- Ivy is a little village child who hears a needy creature near a magical place.
- A moral choice matters: sharing, honesty, or patience changes who gets helped.
- The world reacts with vivid sounds, and the ending includes a transformation
  that proves the choice mattered.

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- shared results containers imported eagerly
- inline ASP rules with a Python reasonableness gate
- a live world model with meters and memes
- child-facing prose with state-driven turns and resolution
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


# ---------------------------------------------------------------------------
# Core domain tables
# ---------------------------------------------------------------------------
MORAL_VALUES = {
    "kindness": {
        "virtue": "kindness",
        "lesson": "kindness can open a stuck heart",
        "prompt": "share the warm food",
    },
    "honesty": {
        "virtue": "honesty",
        "lesson": "honesty can mend a broken trust",
        "prompt": "tell the true story",
    },
    "patience": {
        "virtue": "patience",
        "lesson": "patience can turn a hurry into help",
        "prompt": "wait for the right moment",
    },
}

SOUND_EFFECTS = {
    "rustle": {
        "sound": "rustle-rustle",
        "image": "the leaves whispering in the wind",
        "use": "the ivy leaves stirred with a soft rustle-rustle",
    },
    "tap": {
        "sound": "tap-tap-tap",
        "image": "small footsteps on a wooden path",
        "use": "little feet went tap-tap-tap on the path",
    },
    "clink": {
        "sound": "clink-clink",
        "image": "tiny bells touching together",
        "use": "the little bells made a clink-clink",
    },
    "whoosh": {
        "sound": "whoosh",
        "image": "a quick gust of magic",
        "use": "magic passed by with a whoosh",
    },
    "creak": {
        "sound": "creak-creak",
        "image": "an old gate opening slowly",
        "use": "the old gate answered with a creak-creak",
    },
}

TRANSFORMATIONS = {
    "vinebridge": {
        "label": "vine bridge",
        "before": "a tangled ivy patch",
        "after": "a green bridge woven from ivy",
        "verb": "grew into",
        "effect": "it could carry small feet across the brook",
    },
    "cottageglow": {
        "label": "cottage glow",
        "before": "a dim cottage window",
        "after": "a warm golden cottage lamp",
        "verb": "turned into",
        "effect": "it could shine home for everyone at dusk",
    },
    "foxhelper": {
        "label": "fox helper",
        "before": "a sly little fox",
        "after": "a gentle fox carrying lanterns",
        "verb": "changed into",
        "effect": "it could guide travelers kindly through the wood",
    },
}

SETTINGS = {
    "brook": {
        "place": "the mossy brook",
        "detail": "A narrow brook ran under a leaning willow, and the water sang over the stones.",
        "grounding": "brook",
        "supports": {"kindness", "patience"},
        "transforms": {"vinebridge"},
    },
    "cottage": {
        "place": "the little cottage door",
        "detail": "A tiny cottage stood at the edge of the lane, with a sleepy lamp and a creaky gate.",
        "grounding": "cottage",
        "supports": {"honesty", "kindness"},
        "transforms": {"cottageglow"},
    },
    "wood": {
        "place": "the old folk-wood",
        "detail": "Tall trees stood close together in the old folk-wood, and every branch seemed to listen.",
        "grounding": "wood",
        "supports": {"kindness", "honesty", "patience"},
        "transforms": {"foxhelper", "vinebridge"},
    },
}


# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    transformed: bool = False
    form: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_character(self) -> bool:
        return self.kind == "character"


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    grounding: str
    supports: set[str]
    transforms: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    moral: str
    sound: str
    transformation: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting_id: str, moral_id: str, sound_id: str, transform_id: str) -> bool:
    setting = SETTINGS[setting_id]
    if moral_id not in setting.supports:
        return False
    if transform_id not in setting.transforms:
        return False
    if setting_id == "cottage" and sound_id not in {"creak", "clink"}:
        return False
    if setting_id == "brook" and sound_id not in {"rustle", "tap", "whoosh"}:
        return False
    if setting_id == "wood" and sound_id not in {"rustle", "whoosh", "creak"}:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SETTINGS:
        for m in MORAL_VALUES:
            for snd in SOUND_EFFECTS:
                for t in TRANSFORMATIONS:
                    if valid_combo(s, m, snd, t):
                        out.append((s, m, snd, t))
    return out


def explain_rejection(setting_id: str, moral_id: str, sound_id: str, transform_id: str) -> str:
    setting = SETTINGS[setting_id]
    if moral_id not in setting.supports:
        return (
            f"(No story: {setting.place} does not fit the moral value of {moral_id}. "
            f"Try a setting where that lesson matters.)"
        )
    if transform_id not in setting.transforms:
        return (
            f"(No story: the transformation '{transform_id}' does not belong at {setting.place}. "
            f"Try a transformation that can happen there.)"
        )
    return (
        f"(No story: the sound effect '{sound_id}' does not feel natural for {setting.place}. "
        f"Try a sound that matches the place.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(S,M,So,T) :- setting(S), moral(M), sound(So), transform(T),
                   supports(S,M), allows(S,T), sound_ok(S,So).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for m in sorted(s.supports):
            lines.append(asp.fact("supports", sid, m))
        for t in sorted(s.transforms):
            lines.append(asp.fact("allows", sid, t))
    for mid in MORAL_VALUES:
        lines.append(asp.fact("moral", mid))
    for snd in SOUND_EFFECTS:
        lines.append(asp.fact("sound", snd))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transform", tid))
    for sid in SETTINGS:
        if sid == "cottage":
            for snd in ("creak", "clink"):
                lines.append(asp.fact("sound_ok", sid, snd))
        elif sid == "brook":
            for snd in ("rustle", "tap", "whoosh"):
                lines.append(asp.fact("sound_ok", sid, snd))
        elif sid == "wood":
            for snd in ("rustle", "whoosh", "creak"):
                lines.append(asp.fact("sound_ok", sid, snd))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python validity gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
GIRL_NAMES = ["Ivy", "Mira", "Nora", "Lina", "Rose"]
BOY_NAMES = ["Otto", "Finn", "Jasper", "Theo"]
FOLK_NAMES = ["Ivy", "Ivy", "Ivy", "Mara", "Elin"]


def build_world(params: StoryParams) -> World:
    setting = Setting(id=params.setting, **SETTINGS[params.setting])
    world = World(setting)

    hero = world.add(Entity(
        id="Ivy",
        kind="character",
        type="girl",
        label="Ivy",
        meters={"travel": 0.0, "boldness": 0.0},
        memes={"kindness": 0.0, "worry": 0.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id="OldFox",
        kind="character",
        type="fox",
        label="an old fox",
        meters={"mischief": 0.0, "hope": 0.0},
        memes={"trust": 0.0, "hunger": 0.0},
    ))
    magic = world.add(Entity(
        id="MagicThing",
        kind="thing",
        type="thing",
        label=TRANSFORMATIONS[params.transformation]["before"],
        phrase=TRANSFORMATIONS[params.transformation]["before"],
        form=TRANSFORMATIONS[params.transformation]["before"],
        meters={"stillness": 1.0},
        memes={"sleep": 1.0},
    ))
    world.facts.update(hero=hero, helper=helper, magic=magic, params=params)
    return world


def narrate_setup(world: World) -> None:
    hero: Entity = world.facts["hero"]
    setting = world.setting
    world.say(
        f"Long ago, little Ivy lived near {setting.place}."
        f" {setting.detail}"
    )
    world.say(
        "Ivy had a soft heart and liked to do what was right, even when the path was not easy."
    )


def narrate_call(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    moral = MORAL_VALUES[world.facts["params"].moral]
    sound = SOUND_EFFECTS[world.facts["params"].sound]
    world.para()
    world.say(
        f"One evening, {sound['use']}, and Ivy heard a tiny voice by the path."
    )
    world.say(
        f"It was an old fox with a torn satchel, looking sadly at a crumb of bread."
    )
    world.say(
        f'"Please," said the fox, "I am hungry, and I have lost my way."'
    )
    world.say(
        f"Ivy remembered that {moral['virtue']} is a good way to live, so she listened carefully."
    )
    world.facts["call_heard"] = True
    hero.memes["worry"] += 1
    helper.memes["hunger"] += 1
    helper.meters["mischief"] += 1


def choose_moral(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    moral_id = world.facts["params"].moral
    moral = MORAL_VALUES[moral_id]
    world.para()
    hero.meters["travel"] += 1
    if moral_id == "kindness":
        hero.memes["kindness"] += 1
        hero.memes["joy"] += 1
        helper.memes["trust"] += 1
        world.say(
            f'Ivy smiled and chose {moral["prompt"]}. She broke her little loaf in half and shared it.'
        )
        world.say(
            "The fox's ears lifted, and his eyes grew bright with hope."
        )
    elif moral_id == "honesty":
        hero.meters["boldness"] += 1
        hero.memes["joy"] += 1
        helper.memes["trust"] += 1
        world.say(
            "Ivy admitted that she had seen the missing lantern by the brook reeds."
        )
        world.say(
            "She spoke clearly, and the fox stopped trembling, because true words can be a safe path."
        )
    elif moral_id == "patience":
        hero.meters["boldness"] += 1
        hero.memes["joy"] += 1
        helper.memes["trust"] += 1
        world.say(
            "Ivy did not rush. She waited by the path until the old wind settled and the fox could think straight."
        )
        world.say(
            "When the hurry passed, the fox could ask for help without fear."
        )


def transform_world(world: World) -> None:
    magic: Entity = world.facts["magic"]
    helper: Entity = world.facts["helper"]
    t = TRANSFORMATIONS[world.facts["params"].transformation]
    s = SOUND_EFFECTS[world.facts["params"].sound]
    world.para()
    if world.facts["params"].transformation == "vinebridge":
        world.say(
            f"Then came a {s['sound']}, and the tangled ivy began to twist and lift."
        )
        world.say(
            f"The leaves {t['verb']} a green bridge, and at last {t['effect']}."
        )
    elif world.facts["params"].transformation == "cottageglow":
        world.say(
            f"Then came a {s['sound']}, and the dim window shivered like a waking eye."
        )
        world.say(
            f"The sleepy light {t['verb']} a warm cottage glow, and at last {t['effect']}."
        )
    else:
        world.say(
            f"Then came a {s['sound']}, and the sly fox stepped through a wash of gold."
        )
        world.say(
            f"The fox {t['verb']} a gentle fox helper, and at last {t['effect']}."
        )
    magic.transformed = True
    magic.label = t["after"]
    magic.form = t["after"]
    helper.transformed = True
    helper.label = "a kind fox" if world.facts["params"].transformation == "foxhelper" else helper.label
    helper.meters["hope"] += 1
    helper.memes["trust"] += 1


def resolve(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    moral = MORAL_VALUES[world.facts["params"].moral]
    world.para()
    world.say(
        f"Ivy and the fox shared the rest of the loaf, and the brook, the gate, and the trees seemed to breathe easier."
    )
    world.say(
        f"That was how {moral['lesson']}."
    )
    world.say(
        f"In the end, the little one who had been hungry walked away safe, and Ivy went home with a light step and a warm heart."
    )
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 1
    helper.memes["hunger"] = 0.0
    helper.meters["mischief"] = 0.0


def generate_story(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate_setup(world)
    narrate_call(world)
    choose_moral(world)
    transform_world(world)
    resolve(world)

    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )
    return sample


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a gentle folk tale about Ivy, a {MORAL_VALUES[p.moral]["virtue"]}, and a magical {p.transformation}.',
        f'Tell a short story that uses the sound "{SOUND_EFFECTS[p.sound]["sound"]}" and ends with a transformation.',
        f'Write a child-friendly folk tale where Ivy learns that {MORAL_VALUES[p.moral]["lesson"]}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    moral = MORAL_VALUES[p.moral]["virtue"]
    t = TRANSFORMATIONS[p.transformation]
    snd = SOUND_EFFECTS[p.sound]["sound"]
    return [
        QAItem(
            question="Who is the story about?",
            answer="The story is about little Ivy, who lives near a magical place and makes a good choice.",
        ),
        QAItem(
            question=f"What sound was heard in the story?",
            answer=f"The story used the sound '{snd}', which helped set the folk-tale mood.",
        ),
        QAItem(
            question=f"What moral value did Ivy show?",
            answer=f"Ivy showed {moral} when she chose the right way to help.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"The transformation turned {t['before']} into {t['after']}, so the ending showed that kindness, honesty, or patience can change the world for the better.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing to help, share, or care for someone else.",
        ),
        QAItem(
            question="Why do folk tales often include magic?",
            answer="Folk tales often include magic so a story can show that small choices may lead to big changes.",
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a word or phrase, like rustle-rustle or tap-tap-tap, that helps you hear the action in your mind.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another, like a tangled ivy patch becoming a bridge.",
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
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale world about Ivy, moral choice, sound effects, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--moral", choices=MORAL_VALUES)
    ap.add_argument("--sound", choices=SOUND_EFFECTS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.moral and args.sound and args.transformation:
        if not valid_combo(args.setting, args.moral, args.sound, args.transformation):
            raise StoryError(explain_rejection(args.setting, args.moral, args.sound, args.transformation))
    combos = valid_combos()
    combos = [c for c in combos
              if (args.setting is None or c[0] == args.setting)
              and (args.moral is None or c[1] == args.moral)
              and (args.sound is None or c[2] == args.sound)
              and (args.transformation is None or c[3] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, m, snd, t = rng.choice(sorted(combos))
    return StoryParams(setting=s, moral=m, sound=snd, transformation=t)


CURATED = [
    StoryParams(setting="brook", moral="kindness", sound="rustle", transformation="vinebridge"),
    StoryParams(setting="cottage", moral="honesty", sound="creak", transformation="cottageglow"),
    StoryParams(setting="wood", moral="patience", sound="whoosh", transformation="foxhelper"),
]


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate_story(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate_story(params)
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
            header = f"### {p.setting}: {p.moral} / {p.sound} / {p.transformation}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generate(params: StoryParams) -> StorySample:
    return generate_story(params)


if __name__ == "__main__":
    main()
