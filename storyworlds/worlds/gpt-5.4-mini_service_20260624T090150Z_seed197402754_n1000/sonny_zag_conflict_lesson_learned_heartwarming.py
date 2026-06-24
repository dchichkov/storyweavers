#!/usr/bin/env python3
"""
A small heartwarming storyworld about Sonny and Zag learning to share.

Seed tale inspiration:
Sonny finds a bright kite on a windy day. Zag wants to help, but both children
grab the string at once and begin to tug. The kite droops, feelings get hurt,
and then they remember a gentle lesson: when they take turns, the fun grows.
They work together, the kite lifts, and the day ends with both smiling.

This script models:
- physical meters: tugging, wind, lift, wear, dirt, attention
- emotional memes: joy, worry, hurt, kindness, pride, lesson learned

It also exposes an inline ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import copy
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "son", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "daughter", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    breeze: bool
    indoors: bool = False


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    requires_breeze: bool = False
    can_share: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    prop: str
    first_name: str
    second_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c

    def held_prop(self) -> Optional[Entity]:
        for e in self.entities.values():
            if e.kind == "thing" and e.held_by:
                return e
        return None


def _r_tug(world: World) -> list[str]:
    out: list[str] = []
    prop = world.held_prop()
    if not prop:
        return out
    s = world.get("Sonny")
    z = world.get("Zag")
    if s.memes.get("tugging", 0) < THRESHOLD or z.memes.get("tugging", 0) < THRESHOLD:
        return out
    sig = ("tug", prop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prop.meters["stress"] = prop.meters.get("stress", 0) + 1
    s.memes["frustration"] = s.memes.get("frustration", 0) + 1
    z.memes["frustration"] = z.memes.get("frustration", 0) + 1
    out.append("The string pulled tight, and the kite wobbled in the air.")
    return out


def _r_hurt(world: World) -> list[str]:
    s = world.get("Sonny")
    z = world.get("Zag")
    if s.memes.get("frustration", 0) < THRESHOLD or z.memes.get("frustration", 0) < THRESHOLD:
        return []
    sig = ("hurt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    s.memes["hurt"] = s.memes.get("hurt", 0) + 1
    z.memes["hurt"] = z.memes.get("hurt", 0) + 1
    return ["Their smiles faded, because each one wanted to be heard."]


def _r_lesson(world: World) -> list[str]:
    s = world.get("Sonny")
    z = world.get("Zag")
    prop = world.held_prop()
    if not prop:
        return []
    if s.memes.get("kindness", 0) < THRESHOLD or z.memes.get("kindness", 0) < THRESHOLD:
        return []
    sig = ("lesson", prop.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    s.memes["lesson_learned"] = 1
    z.memes["lesson_learned"] = 1
    prop.meters["lift"] = prop.meters.get("lift", 0) + 1
    return ["Then they remembered that sharing could make the fun bigger."]


CAUSAL_RULES = [_r_tug, _r_hurt, _r_lesson]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule(world)
            if produced:
                changed = True
                lines.extend(produced)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


SETTINGS = {
    "hill": Setting(place="the windy hill", breeze=True),
    "park": Setting(place="the park", breeze=True),
    "porch": Setting(place="the porch", breeze=False),
}

PROPS = {
    "kite": Prop(
        id="kite",
        label="kite",
        phrase="a bright paper kite with a long blue tail",
        requires_breeze=True,
        can_share=True,
        tags={"wind", "play", "sharing"},
    ),
    "book": Prop(
        id="book",
        label="storybook",
        phrase="a little storybook with shiny pictures",
        requires_breeze=False,
        can_share=True,
        tags={"reading", "sharing"},
    ),
    "lantern": Prop(
        id="lantern",
        label="lantern",
        phrase="a tiny paper lantern with a warm glow",
        requires_breeze=False,
        can_share=True,
        tags={"light", "sharing"},
    ),
}

NAMES = ["Sonny", "Zag", "Milo", "Nia", "Lena", "Owen"]
CURATED = [StoryParams(setting="hill", prop="kite", first_name="Sonny", second_name="Zag")]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for s_id, s in SETTINGS.items():
        for p_id, p in PROPS.items():
            if p.requires_breeze and not s.breeze:
                continue
            combos.append((s_id, p_id))
    return combos


def explain_rejection(setting: Setting, prop: Prop) -> str:
    if prop.requires_breeze and not setting.breeze:
        return f"(No story: {prop.label} needs a breeze, but {setting.place} is too still.)"
    return "(No story: the requested combination is not reasonable for this heartwarming lesson.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about Sonny and Zag learning to share.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
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
    if args.setting and args.prop:
        if (args.setting, args.prop) not in valid_combos():
            raise StoryError(explain_rejection(SETTINGS[args.setting], PROPS[args.prop]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.prop is None or c[1] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prop = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        prop=prop,
        first_name=args.name_a or "Sonny",
        second_name=args.name_b or "Zag",
    )


def story_qa(world: World) -> list[QAItem]:
    s = world.get("Sonny")
    z = world.get("Zag")
    prop = world.get("prop")
    return [
        QAItem(
            question="Who are the two friends in the story?",
            answer=f"The story is about Sonny and Zag, two friends who start by wanting the same {prop.label}."
        ),
        QAItem(
            question=f"Why did Sonny and Zag have a conflict about the {prop.label}?",
            answer=f"They both wanted to hold the {prop.label} at the same time, so the string pulled tight and neither one felt fully heard."
        ),
        QAItem(
            question="What lesson did Sonny and Zag learn?",
            answer="They learned that sharing and taking turns can make play happier for both friends."
        ),
        QAItem(
            question=f"What happened after they stopped tugging on the {prop.label}?",
            answer=f"They used kinder hands, the {prop.label} rose smoothly again, and both Sonny and Zag smiled together."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a breeze do for a kite?",
            answer="A breeze helps a kite lift into the air and stay up instead of sinking down."
        ),
        QAItem(
            question="Why is sharing a toy kind?",
            answer="Sharing is kind because it lets more than one person enjoy the same thing without hurting feelings."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.facts["prop"]
    return [
        f"Write a heartwarming story for a young child about Sonny and Zag learning to share a {p.label}.",
        f"Tell a gentle story where Sonny and Zag have a conflict, make up, and learn a lesson together with a {p.label}.",
        f"Write a short, cozy story set at {world.setting.place} that ends with Sonny and Zag smiling beside a {p.label}.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.held_by:
            parts.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(parts)}")
    return "\n".join(lines)


def tell(setting: Setting, prop_cfg: Prop, first_name: str, second_name: str) -> World:
    world = World(setting)
    sonny = world.add(Entity(id="Sonny", kind="character", type="boy"))
    zag = world.add(Entity(id="Zag", kind="character", type="boy"))
    prop = world.add(Entity(id="prop", type=prop_cfg.id, label=prop_cfg.label, phrase=prop_cfg.phrase, owner="Sonny"))
    prop.held_by = "Sonny"

    sonny.memes["joy"] = 1
    zag.memes["joy"] = 1

    world.say(f"Sonny and Zag were outside at {setting.place}.")
    world.say(f"Sonny had found {prop_cfg.phrase}, and the bright little {prop_cfg.label} looked ready to dance in the breeze.")
    world.say(f"Zag came running over, because {second_name.lower()} wanted to help, too.")
    world.para()

    sonny.memes["tugging"] = 1
    zag.memes["tugging"] = 1
    sonny.memes["frustration"] = 1
    zag.memes["frustration"] = 1
    world.say(f"Both children reached for the {prop_cfg.label} at once.")
    world.say("Sonny held the string tight, and Zag held on as well, so the kite began to wobble.")
    propagate(world)

    world.para()
    world.say("Then Sonny took a slow breath and looked at Zag with softer eyes.")
    sonny.memes["kindness"] = 1
    zag.memes["kindness"] = 1
    world.say(f'"Let’s share it," Sonny said. "You can take the next turn."')
    world.say(f'Zag smiled back and nodded. "Okay. We can be a team."')
    if prop_cfg.requires_breeze and not setting.breeze:
        raise StoryError(explain_rejection(setting, prop_cfg))

    # Calm the tension and let the lesson resolve the scene.
    sonny.memes["frustration"] = 0
    zag.memes["frustration"] = 0
    prop.held_by = "Sonny"
    prop.meters["lift"] = prop.meters.get("lift", 0) + 1
    world.say(f"They swapped turns carefully, and the {prop_cfg.label} rose higher and steadier.")
    world.say(f"First Sonny ran a few steps, then Zag held the line with a proud grin.")
    world.say(f"In the end, the {prop_cfg.label} floated over them like a happy little boat in the sky.")
    world.say("That was the lesson they remembered: sharing can turn a small worry into a bigger joy.")

    world.facts.update(setting=setting, prop=prop, prop_cfg=prop_cfg, sonny=sonny, zag=zag)
    return world


ASP_RULES = r"""
prop_shared(P) :- prop(P).
conflict(P) :- prop_shared(P), tugging(sonny,P), tugging(zag,P).
lesson_learned(P) :- conflict(P), kind(sonny), kind(zag), take_turns(P).
heartwarming(P) :- lesson_learned(P), lift(P).
valid_story(S, P) :- setting(S), prop(P), compatible(S, P), heartwarming(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.breeze:
            lines.append(asp.fact("breeze", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if p.requires_breeze:
            lines.append(asp.fact("requires_breeze", pid))
        if p.can_share:
            lines.append(asp.fact("shareable", pid))
    for s_id, p_id in valid_combos():
        lines.append(asp.fact("compatible", s_id, p_id))
    lines.append(asp.fact("kind", "sonny"))
    lines.append(asp.fact("kind", "zag"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROPS[params.prop], params.first_name, params.second_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible combos:")
        for s_id, p_id in combos:
            print(f"  {s_id:8} {p_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.first_name} and {p.second_name} with {p.prop} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
