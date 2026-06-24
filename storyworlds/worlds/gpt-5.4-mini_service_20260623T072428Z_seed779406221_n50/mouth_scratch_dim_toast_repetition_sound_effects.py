#!/usr/bin/env python3
"""
storyworlds/worlds/gpt_5_4_mini_service_20260623T072428Z_seed779406221_n50_mouth_scratch_dim_toast_repetition_sound_effects.py
===============================================================================================================

A standalone storyworld for a small fable-like domain about a dim room,
a scratchy sound, a mouthful of toast, repetition, and a gentle lesson.

Seed tale imagined from the prompt words:
- mouth
- scratch-dim
- toast
- repetition
- sound effects

The world is intentionally tiny: one animal hero, one tempting piece of toast,
one dim place, and one repeated action that makes a sound before the turn
arrives. The prose is state-driven, with a fable tone and a clear ending image.
"""

from __future__ import annotations

import argparse
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "fox", "rat"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"bird", "cat", "squirrel"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    dimness: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Toast:
    id: str
    label: str
    phrase: str
    warmth: str
    bite: str
    crumbs: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ScratchTool:
    id: str
    label: str
    phrase: str
    sound: str
    purpose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_crumb(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    toast = world.entities.get("toast")
    if not hero or not toast:
        return out
    if hero.meters["eager_bite"] < THRESHOLD:
        return out
    sig = ("crumb",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    toast.meters["crumbs"] += 1
    toast.meters["tilted"] += 1
    out.append("__crumb__")
    return out


def _r_sound(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    tool = world.entities.get("scratch")
    if not hero or not tool:
        return out
    if hero.memes["scratched"] < THRESHOLD:
        return out
    sig = ("sound",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["sound_effect"] = tool.sound
    out.append("__sound__")
    return out


CAUSAL_RULES = [
    Rule("crumb", "physical", _r_crumb),
    Rule("sound", "social", _r_sound),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def toast_at_risk(setting: Setting, toast: Toast) -> bool:
    return "toast" in setting.affords and toast.warmth == "warm"


def can_fix(tool: ScratchTool, toast: Toast) -> bool:
    return "soften" in tool.tags and "toast" in toast.tags


def predict_bite(world: World, hero: Entity, toast: Toast) -> dict:
    sim = world.copy()
    sim.get("hero").meters["eager_bite"] += 1
    propagate(sim, narrate=False)
    return {
        "crumbs": sim.get("toast").meters["crumbs"] >= THRESHOLD,
    }


def play_setup(world: World, hero: Entity, toast: Toast, setting: Setting) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"In the {setting.dimness} {setting.place}, {hero.id} found {toast.phrase}. "
        f"It sat there like a little sun trying not to shine."
    )


def desire(world: World, hero: Entity, toast: Toast) -> None:
    hero.meters["eager_bite"] += 1
    world.say(
        f"{hero.id} leaned close and whispered, \"Mmm, toast, toast, toast.\" "
        f"{hero.pronoun().capitalize()} wanted a bite at once."
    )


def scratch(world: World, hero: Entity, tool: ScratchTool) -> None:
    hero.memes["scratched"] += 1
    world.say(
        f"{tool.sound} {tool.sound} went the little {tool.label}, "
        f"because {hero.id} had learned the same noisy trick twice."
    )


def warn(world: World, helper: Entity, hero: Entity, toast: Toast) -> None:
    pred = predict_bite(world, hero, toast)
    if pred["crumbs"]:
        world.facts["warning"] = True
        world.say(
            f"\"Not yet,\" said {helper.id}. \"Warm toast can crumble if you rush it.\""
        )
    else:
        world.say(f"\"Careful,\" said {helper.id}, but the air was already full of crumbs.")


def repeat_wait(world: World, hero: Entity) -> None:
    hero.memes["patience"] += 1
    world.say("So {0} waited. And waited. And waited.".format(hero.id))


def cool_down(world: World, toast: Toast) -> None:
    toast.meters["warmth"] -= 1
    world.say(
        f"The toast cooled from warm to merely toasty, and the room felt less dim."
    )


def accept_lesson(world: World, hero: Entity, helper: Entity, toast: Toast, tool: ScratchTool) -> None:
    hero.memes["joy"] += 1
    hero.memes["wisdom"] += 1
    world.say(
        f"At last {hero.id} took a tiny bite. {toast.sound} said the crust, "
        f"and the {tool.label} rested in the corner, quiet now."
    )
    world.say(
        f"{hero.id} and {helper.id} smiled at the same small crumb trail and knew "
        f"that patience makes breakfast sweeter."
    )


def tell(setting: Setting, toast_cfg: Toast, scratch_cfg: ScratchTool,
         hero_name: str = "Milo", helper_name: str = "Mina") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="mouse", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="mouse", label=helper_name))
    toast = world.add(Entity(id="toast", type="toast", label=toast_cfg.label, phrase=toast_cfg.phrase))
    tool = world.add(Entity(id="scratch", type="tool", label=scratch_cfg.label, phrase=scratch_cfg.phrase))
    world.facts.update(hero=hero, helper=helper, toast_cfg=toast_cfg, scratch_cfg=scratch_cfg)
    toast.meters["warmth"] = 1.0
    hero.memes["hunger"] = 1.0

    play_setup(world, hero, toast_cfg, setting)
    world.para()
    desire(world, hero, toast_cfg)
    scratch(world, hero, scratch_cfg)
    warn(world, helper, hero, toast_cfg)
    repeat_wait(world, hero)
    cool_down(world, toast_cfg)
    world.para()
    accept_lesson(world, hero, helper, toast_cfg, scratch_cfg)
    propagate(world, narrate=False)

    world.facts.update(
        warning=world.facts.get("warning", False),
        crumbs=toast_cfg.crumbs,
        sound_effect=scratch_cfg.sound,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="kitchen", dimness="dim", affords={"toast"}),
    "pantry": Setting(place="pantry", dimness="shadowy", affords={"toast"}),
    "table": Setting(place="table by the window", dimness="softly lit", affords={"toast"}),
}

TOASTS = {
    "butter": Toast(
        id="butter",
        label="buttered toast",
        phrase="a slice of buttered toast",
        warmth="warm",
        bite="soft",
        crumbs="golden crumbs",
        sound="crack",
        tags={"toast"},
    ),
    "jam": Toast(
        id="jam",
        label="jam toast",
        phrase="a slice of jam toast",
        warmth="warm",
        bite="sticky",
        crumbs="sticky crumbs",
        sound="crisp",
        tags={"toast"},
    ),
}

SCRATCH_TOOLS = {
    "fork": ScratchTool(
        id="fork",
        label="tiny fork",
        phrase="a tiny fork",
        sound="scritch",
        purpose="nibble",
        tags={"scratch", "soften"},
    ),
    "spoon": ScratchTool(
        id="spoon",
        label="wooden spoon",
        phrase="a wooden spoon",
        sound="tap",
        purpose="tap",
        tags={"scratch", "soften"},
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Lena", "Tia"]
BOY_NAMES = ["Milo", "Otto", "Pip", "Jules"]
TRAITS = ["patient", "curious", "gentle", "bright"]


@dataclass
class StoryParams:
    setting: str
    toast: str
    scratch: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TOASTS:
            for sc in SCRATCH_TOOLS:
                if toast_at_risk(SETTINGS[s], TOASTS[t]) and can_fix(SCRATCH_TOOLS[sc], TOASTS[t]):
                    combos.append((s, t, sc))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable about {f["hero"].id} in a {f["toast_cfg"].label} kitchen, with repetition and sound effects.',
        f'Tell a gentle story where {f["hero"].id} hears "{f["sound_effect"]}" around warm toast and learns to wait.',
        f'Write a child-friendly fable that repeats a small phrase three times and ends with a wiser breakfast.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    toast = f["toast_cfg"]
    scratch = f["scratch_cfg"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little mouse who found {toast.phrase} in the dim kitchen.",
        ),
        QAItem(
            question=f"What sound did the scratch tool make?",
            answer=f"It made a {scratch.sound} sound, and the story repeats that sound to show the same eager idea twice.",
        ),
        QAItem(
            question=f"Why did {helper.id} tell {hero.id} to wait?",
            answer=f"{helper.id} knew warm toast can crumble if it is rushed, so waiting kept the breakfast tidy and calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is toast?",
            answer="Toast is bread that has been browned and made warm and crisp.",
        ),
        QAItem(
            question="What does a scratchy sound effect do in a story?",
            answer="A scratchy sound effect helps you hear the action, like tapping, scraping, or rustling.",
        ),
        QAItem(
            question="Why is a dim room important in a fable?",
            answer="A dim room makes the character look for light, patience, or a safer idea.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
toast_at_risk(S,T) :- setting(S), toast(T), affords(S,toast), warm(T).
crumbs(T) :- toast(T), eager_bite(hero).
sound_event(S) :- scratch_tool(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TOASTS.items():
        lines.append(asp.fact("toast", tid))
        if t.warmth == "warm":
            lines.append(asp.fact("warm", tid))
    for sid, s in SCRATCH_TOOLS.items():
        lines.append(asp.fact("scratch_tool", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show toast_at_risk/2."))
    clingo = set(asp.atoms(model, "toast_at_risk"))
    python = set((s, t) for s, t, _ in valid_combos())
    if clingo == python:
        print(f"OK: ASP gate matches valid_combos() ({len(python)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about dim rooms, toast, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toast", choices=TOASTS)
    ap.add_argument("--scratch", choices=SCRATCH_TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.toast is None or c[1] == args.toast)
              and (args.scratch is None or c[2] == args.scratch)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, toast, scratch = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, toast=toast, scratch=scratch, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TOASTS[params.toast], SCRATCH_TOOLS[params.scratch], params.name, params.helper)
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
    StoryParams(setting="kitchen", toast="butter", scratch="fork", name="Milo", helper="Mina", trait="patient"),
    StoryParams(setting="pantry", toast="jam", scratch="spoon", name="Nora", helper="Pip", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show toast_at_risk/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show toast_at_risk/2."))
        print(sorted(asp.atoms(model, "toast_at_risk")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
