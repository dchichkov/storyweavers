#!/usr/bin/env python3
"""
storyworlds/worlds/distribute_sound_effects_nursery_rhyme.py
=============================================================

A small standalone story world about a child, a nursery-rhyme scene, and the
gentle distribution of sound effects.

Premise:
- A little performer wants to tell a tiny rhyme.
- The sounds are uneven at first: one loud sound keeps crowding out the others.
- A careful helper distributes the sound effects so each moment gets its own
  voice.
- The ending proves the change by letting the whole rhyme ring in balance.

This world keeps the prose child-facing and rhythmic, with concrete actions and
clear state changes. The simulated model tracks both physical meters and
emotional memes, and the story is driven from that state instead of from a
static paragraph template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Make shared result containers importable when run directly.
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
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the nursery"
    indoor: bool = True
    afford: set[str] = field(default_factory=set)


@dataclass
class SoundEffect:
    id: str
    glyph: str
    voice: str
    volume: int
    mood: str
    kind: str  # "soft", "bright", "loud"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    protects: set[str] = field(default_factory=set)
    is_distribution_tool: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    props: dict[str, Prop] = field(default_factory=dict)
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.props = copy.deepcopy(self.props)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    effect: str
    prop: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "nursery": Setting("the nursery", True, {"soft", "bright", "loud"}),
    "playroom": Setting("the playroom", True, {"soft", "bright", "loud"}),
}

EFFECTS = {
    "plink": SoundEffect("plink", "plink", "a tiny plink", 1, "cheerful", "soft", {"bell", "tiny"}),
    "bong": SoundEffect("bong", "bong", "a round bong", 3, "surprised", "loud", {"drum", "round"}),
    "swish": SoundEffect("swish", "swish", "a soft swish", 2, "calm", "bright", {"cloth", "wind"}),
    "clap": SoundEffect("clap", "clap", "a happy clap", 2, "lively", "bright", {"hands", "party"}),
}

PROPS = {
    "basket": Prop("basket", "a little basket", {"soft", "bright"}, True),
    "ribbon": Prop("ribbon", "a ribbon hoop", {"bright", "soft"}, True),
    "drum": Prop("drum", "a toy drum", {"loud"}, True),
}

GIRL_NAMES = ["Mia", "Lily", "Nina", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Max", "Ben", "Toby"]
HELPERS = ["mother", "father", "grandma", "grandpa"]


class StoryWorld:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "StoryWorld":
        import copy
        c = StoryWorld(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def distribute_effects(world: StoryWorld, actor: Entity, effect: SoundEffect, prop: Prop) -> list[str]:
    out = []
    if effect.kind not in world.setting.afford:
        raise StoryError("That sound does not fit this small nursery-rhyme scene.")
    if prop.id not in PROPS:
        raise StoryError("Unknown prop.")
    if effect.kind not in prop.protects and prop.protects:
        return out
    sig = ("distribute", actor.id, effect.id, prop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)

    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    prop_ent = world.entities[prop.id]
    prop_ent.meters["order"] = prop_ent.meters.get("order", 0.0) + 1
    out.append(f"{actor.pronoun().capitalize()} placed {effect.voice} in {prop_ent.label}, one by one.")
    return out


def predict_balance(world: StoryWorld, effect: SoundEffect, prop: Prop) -> bool:
    sim = world.copy()
    hero = sim.entities["hero"]
    if effect.kind == "loud" and prop.id != "drum":
        return False
    return True


def introduce(world: StoryWorld, hero: Entity, helper: Entity, effect: SoundEffect) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a tune in {hero.pronoun('possessive')} toes."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved the rhyme of {effect.voice}, {helper.label}, and the warm little room."
    )


def setup_scene(world: StoryWorld, hero: Entity, helper: Entity, effect: SoundEffect, prop: Prop) -> None:
    world.say(
        f"On a bright day in {world.setting.place}, {hero.id} found {prop.label} and a voice for {effect.glyph}."
    )
    hero.meters["want_sing"] = hero.meters.get("want_sing", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} wanted to sing a nursery rhyme, but one sound kept hogging the middle.")


def warn(world: StoryWorld, helper: Entity, hero: Entity, effect: SoundEffect, prop: Prop) -> bool:
    if effect.kind == "loud" and prop.id != "drum":
        world.say(
            f'"That {effect.glyph} is too big for every line," {helper.label} said softly. "It needs sharing."'
        )
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
        return True
    return False


def conflict(world: StoryWorld, hero: Entity, effect: SoundEffect) -> None:
    hero.memes["frustration"] = hero.memes.get("frustration", 0.0) + 1
    world.say(f"{hero.id} frowned. "{effect.glyph} went boom-boom too much," {hero.pronoun()} grumbled.")
    world.say(f"Then {hero.pronoun()} tapped the table and went, {effect.glyph}! {effect.glyph}! {effect.glyph}!")


def resolve(world: StoryWorld, helper: Entity, hero: Entity, effect: SoundEffect, prop: Prop) -> None:
    hero.memes["frustration"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.meters["order"] = hero.meters.get("order", 0.0) + 1
    world.say(
        f'{helper.label} smiled and said, "Let us distribute the sound effects."'
    )
    world.say(
        f"They gave {effect.glyph} a place in {prop.label}, and each little beat found its own small home."
    )
    world.say(
        f"Then {hero.id} sang, {effect.glyph}, swish, plink, clap, and the nursery rhyme danced along."
    )


def tell(setting: Setting, effect: SoundEffect, prop: Prop, name: str, gender: str, helper_kind: str) -> StoryWorld:
    world = StoryWorld(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_kind, label=f"the {helper_kind}"))
    prop_ent = world.add(Entity(id=prop.id, kind="thing", type="prop", label=prop.label))

    world.facts.update(hero=hero, helper=helper, effect=effect, prop=prop, setting=setting)

    introduce(world, hero, helper, effect)
    world.para()
    setup_scene(world, hero, helper, effect, prop)
    warn(world, helper, hero, effect, prop)
    conflict(world, hero, effect)
    world.para()
    resolve(world, helper, hero, effect, prop)
    world.facts["resolved"] = True
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for effect_id, effect in EFFECTS.items():
            for prop_id, prop in PROPS.items():
                if effect.kind in setting.afford and (effect.kind in prop.protects or prop.id == "drum"):
                    combos.append((place, effect_id, prop_id))
    return combos


def story_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story about a child who wants to distribute "{f["effect"].glyph}" sound effects evenly.',
        f'Tell a gentle story in "{f["setting"].place}" where {f["hero"].id} and {f["helper"].label} share the sound "{f["effect"].glyph}".',
        f'Write a small rhyme where the words "distribute", "{f["effect"].glyph}", and "{f["prop"].label}" all appear naturally.',
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    effect = f["effect"]
    prop = f["prop"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the story?",
            answer=f"{hero.id} wanted to sing a nursery rhyme and distribute the {effect.glyph} sound effects more evenly.",
        ),
        QAItem(
            question=f"Why did {helper.label} say the sound needed sharing?",
            answer=f"{helper.label} said the {effect.glyph} sound was too big for every line, so it needed to be distributed with care.",
        ),
        QAItem(
            question=f"What helped the sound fit better at the end?",
            answer=f"{prop.label} helped because the sounds were placed in it one by one, so no one sound crowded out the others.",
        ),
    ]


def world_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to distribute something?",
            answer="To distribute something means to share it out among different places or people instead of keeping it all in one spot.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are little sounds that help tell a story, like clap, swish, or plink.",
        ),
        QAItem(
            question="What is a nursery rhyme?",
            answer="A nursery rhyme is a short, simple song or poem with a bouncy rhythm and easy words.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for k in sorted(s.afford):
            lines.append(asp.fact("affords", sid, k))
    for eid, e in EFFECTS.items():
        lines.append(asp.fact("effect", eid))
        lines.append(asp.fact("kind_of", eid, e.kind))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        for k in sorted(p.protects):
            lines.append(asp.fact("protects_kind", pid, k))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Effect, Prop) :- affords(Place, Kind), kind_of(Effect, Kind),
                             prop(Prop), protects_kind(Prop, Kind).
valid(Place, Effect, drum) :- affords(Place, Kind), kind_of(Effect, Kind), prop(drum).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world about distributing sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--effect", choices=EFFECTS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.effect is None or c[1] == args.effect)
        and (args.prop is None or c[2] == args.prop)
    ]
    if not combos:
        raise StoryError("No reasonable nursery-rhyme combination matches those choices.")
    place, effect, prop = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, effect=effect, prop=prop, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], EFFECTS[params.effect], PROPS[params.prop], params.name, params.gender, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="nursery", effect="plink", prop="basket", name="Mia", gender="girl", helper="mother"),
    StoryParams(place="playroom", effect="swish", prop="ribbon", name="Leo", gender="boy", helper="grandma"),
    StoryParams(place="nursery", effect="clap", prop="basket", name="Ava", gender="girl", helper="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
