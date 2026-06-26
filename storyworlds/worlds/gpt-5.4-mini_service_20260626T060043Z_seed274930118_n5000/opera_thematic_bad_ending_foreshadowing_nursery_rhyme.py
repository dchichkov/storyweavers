#!/usr/bin/env python3
"""
A small storyworld about an opera night with a thematic stage, a little
foreshadowing, and a nursery-rhyme cadence that leads to a bad ending.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    theme: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    at_risk: str
    hints: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    setting: str
    prop: str
    hero: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "opera_house": Setting(place="the opera house", theme="grand opera", affords={"singing", "practicing"}),
    "small_theatre": Setting(place="the small theatre", theme="thematic opera", affords={"singing", "dressing"}),
    "moon_stage": Setting(place="the moonlit stage", theme="nursery opera", affords={"singing", "echoing"}),
}

PROPS = {
    "lantern": Prop(
        id="lantern",
        label="lantern",
        phrase="a bright little lantern",
        at_risk="flame",
        hints=["glow", "dark", "light"],
    ),
    "crown": Prop(
        id="crown",
        label="crown",
        phrase="a tiny golden crown",
        at_risk="tilt",
        hints=["king", "queen", "shine"],
    ),
    "cloak": Prop(
        id="cloak",
        label="cloak",
        phrase="a velvet cloak",
        at_risk="tears",
        hints=["velvet", "red", "stage"],
    ),
}

HEROES = {
    "Lia": ("girl", "curious"),
    "Milo": ("boy", "gentle"),
    "Nora": ("girl", "dreamy"),
    "Theo": ("boy", "careful"),
}

CURATED = [
    StoryParams(setting="opera_house", prop="lantern", hero="Lia"),
    StoryParams(setting="small_theatre", prop="cloak", hero="Milo"),
    StoryParams(setting="moon_stage", prop="crown", hero="Nora"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("theme", sid, s.theme))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("at_risk", pid, p.at_risk))
        for h in p.hints:
            lines.append(asp.fact("hint", pid, h))
    for h, (typ, _) in HEROES.items():
        lines.append(asp.fact("hero", h))
        lines.append(asp.fact("type", h, typ))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, H) :- setting(S), prop(P), hero(H), affords(S, singing), at_risk(P, _).
"""
# The rule is intentionally simple; the Python gate performs the real check.


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in PROPS:
            for h in HEROES:
                if reasonableness_gate(s, p, h):
                    out.append((s, p, h))
    return out


def reasonableness_gate(setting: str, prop: str, hero: str) -> bool:
    return setting in SETTINGS and prop in PROPS and hero in HEROES and "singing" in SETTINGS[setting].affords


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme opera storyworld with foreshadowing and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--hero", choices=HEROES)
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
    combos = python_valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.prop:
        combos = [c for c in combos if c[1] == args.prop]
    if args.hero:
        combos = [c for c in combos if c[2] == args.hero]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    s, p, h = rng.choice(sorted(combos))
    return StoryParams(setting=s, prop=p, hero=h)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    prop_cfg = PROPS[params.prop]
    hero_type, trait = HEROES[params.hero]
    w = World(setting)
    hero = w.add(Entity(id=params.hero, kind="character", type=hero_type, label=params.hero))
    prop = w.add(Entity(id=prop_cfg.id, type=prop_cfg.label, label=prop_cfg.label, phrase=prop_cfg.phrase, owner=hero.id))
    stage = w.add(Entity(id="stage", type="stage", label="stage"))
    w.facts.update(hero=hero, prop=prop, stage=stage, trait=trait, setting=setting, prop_cfg=prop_cfg)
    return w


def generate_story(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    prop: Entity = world.facts["prop"]  # type: ignore[assignment]
    trait: str = world.facts["trait"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    prop_cfg: Prop = world.facts["prop_cfg"]  # type: ignore[assignment]

    world.say(f"In {setting.place}, by the hush of night, lived {hero.id}, so small and bright.")
    world.say(f"{hero.id} loved the {setting.theme}, and dreamed of songs that soared and spun.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {prop.label} was {prop.phrase}, and every child could see it gleam.")

    world.say(f"One warm-up day, {hero.id} asked to sing; the curtain quivered like a tiny wing.")
    world.say(f"But there was a hush before the tune, a little sign beneath the moon:")
    if prop.id == "lantern":
        world.say("The lantern flame was turning thin, as if the wind had come to win.")
    elif prop.id == "crown":
        world.say("The crown sat crooked, tilting west, as if it could not stay its best.")
    else:
        world.say("The cloak gave one small hiss and tear, as though a snag might catch it there.")
    world.say(f"That was the foreshadowing, soft and sly: a trouble waiting nearby.")

    world.say(f"{hero.id} sang on, a trilly song, but something in the night went wrong.")
    if prop.id == "lantern":
        world.say("The breeze blew out the lantern light, and shadows gulped the stage that night.")
        world.say("The singers missed their cue, you see, and the curtain fell too early.")
    elif prop.id == "crown":
        world.say("The crown toppled off in the middle of the rhyme, and rolled away in merry time.")
        world.say("The laughing crowd forgot the tune, and the star felt tears come very soon.")
    else:
        world.say("The cloak snagged hard on a painted nail, and the grand finale went pale and stale.")
        world.say("The choir lost pace, the drums went thin, and even the moon forgot to grin.")

    hero.memes["sadness"] = 1
    hero.memes["loss"] = 1
    prop.meters["ruined"] = 1
    world.say(f"So {hero.id} bowed down, with a wobble and a frown, and the opera ended poorly in town.")
    world.say(f"Yet {prop.label} stayed in {hero.id}'s heart, a shining theme though broken apart.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prop_cfg = f["prop_cfg"]
    setting = f["setting"]
    return [
        f"Write a short nursery-rhyme story about {hero.id} at {setting.place} with {prop_cfg.phrase}.",
        f"Tell a thematic opera tale where a small clue foreshadows a bad ending.",
        f"Make a child-friendly story with singing, a warning sign, and a poor finale.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    prop_cfg = world.facts["prop_cfg"]
    setting = world.facts["setting"]
    return [
        QAItem(
            question=f"Where did {hero.id} sing?",
            answer=f"{hero.id} sang at {setting.place}, where the theme of the night was {setting.theme}.",
        ),
        QAItem(
            question=f"What hinted that trouble was coming?",
            answer=f"The story foreshadowed trouble with a small sign about {prop_cfg.label} before the song went wrong.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly: the song was interrupted, the stage lost its magic, and the final feeling was sad.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an opera?", answer="An opera is a story told with singing, music, and acting on a stage."),
        QAItem(question="What is foreshadowing?", answer="Foreshadowing is a clue early in a story that hints something will happen later."),
        QAItem(question="What does thematic mean?", answer="Thematic means made around one idea or theme, so the parts of the story fit together."),
        QAItem(question="What is a nursery rhyme style?", answer="It is a simple, rhythmic way of telling a story with bouncy words and gentle repetition."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(python_valid_combos())
    if a == b:
        print(f"OK: ASP and Python agree on {len(a)} combos.")
        return 0
    print("Mismatch between ASP and Python.")
    if a - b:
        print("Only in ASP:", sorted(a - b))
    if b - a:
        print("Only in Python:", sorted(b - a))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        for t in triples:
            print(t)
        return

    rng = random.Random(args.seed)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
