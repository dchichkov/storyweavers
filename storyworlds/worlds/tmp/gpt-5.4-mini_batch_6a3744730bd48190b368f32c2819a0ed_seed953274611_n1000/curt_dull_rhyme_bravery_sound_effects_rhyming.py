#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/curt_dull_rhyme_bravery_sound_effects_rhyming.py
=================================================================================

A tiny rhyming storyworld about a child who finds a dull little stage act,
gathers bravery, and learns how a bright sound and a brave rhyme can turn a curt
moment into a cheerful one.

The world is intentionally small:
- one child performer
- one small stage object that can be dull or lively
- one helper who may give a curt answer
- one sound effect that can be timid or loud
- a rhyme prompt, a bravery meter, and a satisfying ending image

The script follows the storyworld contract:
- stdlib only for the prose engine
- StoryParams, build_parser, resolve_params, generate, emit, main
- a Python reasonableness gate and inline ASP_RULES twin
- QA grounded in the simulated world state, not by parsing text
- --verify exercises both the ASP parity and at least one normal generation

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/curt_dull_rhyme_bravery_sound_effects_rhyming.py
    python storyworlds/worlds/gpt-5.4-mini/curt_dull_rhyme_bravery_sound_effects_rhyming.py --qa
    python storyworlds/worlds/gpt-5.4-mini/curt_dull_rhyme_bravery_sound_effects_rhyming.py --all
    python storyworlds/worlds/gpt-5.4-mini/curt_dull_rhyme_bravery_sound_effects_rhyming.py --verify
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
SENSE_MIN = 2.0
BRAVERY_INIT = 3.0
BRAVERY_REQUIRED = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
class StageProp:
    id: str
    label: str
    phrase: str
    noise: str
    dull: bool = True
    bright: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundEffect:
    id: str
    label: str
    phrase: str
    sound: str
    volume: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class ScriptOption:
    id: str
    line: str
    style: str
    brave_cost: int
    brave_gain: int
    tags: set[str] = field(default_factory=set)


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


def _r_cheer(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    stage = world.get("stage")
    sound = world.get("sound")
    if child.memes["bravery"] < BRAVERY_REQUIRED:
        return out
    if stage.meters["dull"] >= THRESHOLD and sound.meters["loud"] >= THRESHOLD:
        sig = ("cheer",)
        if sig not in world.fired:
            world.fired.add(sig)
            stage.meters["spark"] += 1
            child.memes["pride"] += 1
            out.append("__spark__")
    return out


CAUSAL_RULES = [Rule("cheer", "social", _r_cheer)]


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


def hush_up(world: World, child: Entity, helper: Entity, sound: SoundEffect, prop: StageProp) -> None:
    child.memes["worry"] += 1
    world.say(
        f"On a little stage, {child.id} had a plan to make a rhyme, but the setup felt dull."
    )
    world.say(
        f'The {prop.label} sat there so plain, so curt, with no bright twirl or whirl.'
    )
    world.say(
        f'{helper.id} gave a curt reply: "{sound.phrase}?"'
    )


def predict_world(world: World, sound: SoundEffect) -> dict:
    sim = world.copy()
    sim.get("sound").meters["loud"] += 1 if sound.volume >= 2 else 0
    sim.get("sound").meters["soft"] += 1 if sound.volume < 2 else 0
    sim.get("child").memes["bravery"] += 1
    propagate(sim, narrate=False)
    return {
        "spark": sim.get("stage").meters["spark"] >= THRESHOLD,
        "pride": sim.get("child").memes["pride"],
    }


def perform(world: World, child: Entity, helper: Entity, prop: StageProp, sound: SoundEffect, option: ScriptOption) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} took a breath, then chose a brave little show."
    )
    world.say(
        f"{option.line} {sound.sound} went the room, and the stage stopped feeling dull."
    )
    if sound.volume >= 2:
        world.get("sound").meters["loud"] += 1
    else:
        world.get("sound").meters["soft"] += 1
    world.get("stage").meters["dull"] = 0
    world.get("stage").meters["spark"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The prop shone a bit brighter, and the rhyme came out clean and sweet."
    )


def ending(world: World, child: Entity, helper: Entity, prop: StageProp) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"In the end, {child.id} grinned at {helper.id}, and the curt little stage was not dull anymore."
    )
    world.say(
        f"The {prop.label} looked like a tiny star, and the brave rhyme stayed in the air."
    )


def valid_combo(prop: StageProp, sound: SoundEffect, option: ScriptOption) -> bool:
    return prop.dull and sound.sense >= SENSE_MIN and option.brave_gain >= BRAVERY_REQUIRED


def sensible_sounds() -> list[SoundEffect]:
    return [s for s in SOUNDS.values() if s.sense >= SENSE_MIN]


def best_sound() -> SoundEffect:
    return max(SOUNDS.values(), key=lambda s: s.sense)


def generate_story(world: World, prop: StageProp, sound: SoundEffect, option: ScriptOption) -> None:
    child = world.add(Entity(id="child", kind="character", type="girl", role="performer"))
    helper = world.add(Entity(id="helper", kind="character", type="boy", role="partner"))
    stage = world.add(Entity(id="stage", type="thing", label=prop.label))
    sound_ent = world.add(Entity(id="sound", type="thing", label=sound.label))

    child.memes["bravery"] = BRAVERY_INIT
    world.facts["prop"] = prop
    world.facts["sound"] = sound
    world.facts["option"] = option

    hush_up(world, child, helper, sound, prop)
    world.para()
    pred = predict_world(world, sound)
    if not pred["spark"]:
        child.memes["bravery"] += 1
    perform(world, child, helper, prop, sound, option)
    world.para()
    ending(world, child, helper, prop)

    world.facts.update(
        child=child,
        helper=helper,
        stage=stage,
        sound_ent=sound_ent,
        spark=world.get("stage").meters["spark"] >= THRESHOLD,
        dull=world.get("stage").meters["dull"] >= THRESHOLD,
    )


THEMES = {
    "curt_dull": StageProp(
        id="curt_dull",
        label="curt curtain",
        phrase="a curt curtain",
        noise="flutter",
        dull=True,
        bright=False,
        tags={"curt", "dull"},
    ),
    "dull_drum": StageProp(
        id="dull_drum",
        label="dull drum",
        phrase="a dull drum",
        noise="tap",
        dull=True,
        bright=False,
        tags={"dull"},
    ),
}

SOUNDS = {
    "clap": SoundEffect(
        id="clap",
        label="clap",
        phrase="Clap-clap?",
        sound="Clap-clap",
        volume=2,
        sense=3,
        tags={"sound"},
    ),
    "ding": SoundEffect(
        id="ding",
        label="ding",
        phrase="Ding!",
        sound="Ding",
        volume=2,
        sense=3,
        tags={"sound"},
    ),
    "whisper": SoundEffect(
        id="whisper",
        label="whisper",
        phrase="A whisper?",
        sound="whisper",
        volume=1,
        sense=1,
        tags={"sound"},
    ),
}

OPTIONS = {
    "rhyme": ScriptOption(
        id="rhyme",
        line="Rhyme time, bright and light",
        style="rhyming",
        brave_cost=1,
        brave_gain=2,
        tags={"rhyme"},
    ),
    "chant": ScriptOption(
        id="chant",
        line="Sing and swing and ring the bell",
        style="rhyming",
        brave_cost=1,
        brave_gain=2,
        tags={"rhyme"},
    ),
}


@dataclass
class StoryParams:
    prop: str
    sound: str
    option: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(prop="curt_dull", sound="clap", option="rhyme", seed=101),
    StoryParams(prop="dull_drum", sound="ding", option="chant", seed=102),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pid, prop in THEMES.items():
        for sid, sound in SOUNDS.items():
            for oid, option in OPTIONS.items():
                if valid_combo(prop, sound, option):
                    combos.append((pid, sid, oid))
    return combos


def explain_rejection(sound: SoundEffect) -> str:
    return f"(No story: {sound.label} is too quiet and too uncertain for this brave rhyme story.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld with bravery and sound effects.")
    ap.add_argument("--prop", choices=THEMES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--option", choices=OPTIONS)
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
    if args.sound and SOUNDS[args.sound].sense < SENSE_MIN:
        raise StoryError(explain_rejection(SOUNDS[args.sound]))
    combos = [c for c in valid_combos()
              if (args.prop is None or c[0] == args.prop)
              and (args.sound is None or c[1] == args.sound)
              and (args.option is None or c[2] == args.option)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    prop, sound, option = rng.choice(sorted(combos))
    return StoryParams(prop=prop, sound=sound, option=option)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story with the words "curt" and "dull", and include a brave sound effect like {f["sound"].phrase}.',
        f"Tell a short rhyme story where {f['child'].id} turns a dull stage into a bright one with a brave choice.",
        f'Write a child-friendly rhyming tale about bravery, a curt reply, and a sound effect that helps the show begin.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    prop = f["prop"]
    sound = f["sound"]
    qa = [
        QAItem(
            question="What kind of stage object was in the story?",
            answer=f"It was a {prop.label}. It began dull and curt, which made the child need a braver idea.",
        ),
        QAItem(
            question="What sound helped the show?",
            answer=f"{sound.phrase} helped the show begin. The sound gave the child a cheerful cue to keep going.",
        ),
        QAItem(
            question="How did the child show bravery?",
            answer=f"{child.id} took a breath and kept going with the rhyme. That brave choice changed the mood of the whole scene.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like light and night. Rhymes can make a story feel bouncy and musical.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something even when you feel nervous. It does not mean never being scared; it means keeping on anyway.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special noise used to make a story or show feel lively. It can be a clap, a ding, or a soft whisper.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,S,O) :- prop(P), sound(S), option(O), dull_prop(P), sound_ok(S), brave_opt(O).
sound_ok(S) :- sound(S), sense(S,N), sense_min(M), N >= M.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in THEMES:
        lines.append(asp.fact("prop", pid))
        if THEMES[pid].dull:
            lines.append(asp.fact("dull_prop", pid))
    for sid, snd in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("sense", sid, snd.sense))
    for oid in OPTIONS:
        lines.append(asp.fact("option", oid))
        lines.append(asp.fact("brave_opt", oid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("only python:", sorted(py - cl))
        print("only clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(prop=None, sound=None, option=None), random.Random(7)))
        assert sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.prop not in THEMES or params.sound not in SOUNDS or params.option not in OPTIONS:
        raise StoryError("(Invalid params.)")
    if SOUNDS[params.sound].sense < SENSE_MIN:
        raise StoryError(explain_rejection(SOUNDS[params.sound]))
    world = World()
    generate_story(world, THEMES[params.prop], SOUNDS[params.sound], OPTIONS[params.option])
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
        print(f"{len(asp_valid_combos())} valid combos:")
        for c in asp_valid_combos():
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
