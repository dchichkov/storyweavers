#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/vagina_skit_cart_teamwork_kindness_repetition_adventure.py
===============================================================================================================

A small standalone story world about an adventurous classroom skit,
a rolling cart of props, and a gentle science lesson that uses teamwork,
kindness, and repetition to help everyone feel ready.

Seed image:
- A class is setting up a skit on an adventure stage.
- A prop cart keeps wobbling and needs teamwork to move safely.
- A child learns a new body word, "vagina," in a respectful science moment.
- Repeating a line together helps calm nerves and makes the performance stronger.

This world keeps the prose child-facing and concrete while still allowing
state-driven variation in who helps, what gets carried, and how the rehearsal
turns into a real performance.
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

SETTINGS_ORDER = ["classroom", "stage", "hall"]
THEMES = ["adventure", "science", "play"]
PROPS = ["cart", "lantern", "map", "cloak", "sign"]
ROLES = ["leader", "helper", "reader", "mover"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretakers: list[str] = field(default_factory=list)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    allows_skit: bool = True


@dataclass
class StoryRole:
    id: str
    line: str
    needs_repetition: bool = False
    kind_words: tuple[str, ...] = ("kindness", "teamwork")


@dataclass
class PropSpec:
    id: str
    label: str
    phrase: str
    heavy: bool = False
    rollable: bool = False


@dataclass
class StoryParams:
    setting: str
    theme: str
    prop: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "classroom": Setting(place="the classroom", indoors=True),
    "stage": Setting(place="the little stage", indoors=True),
    "hall": Setting(place="the hall", indoors=True),
}

PROPS = {
    "cart": PropSpec(id="cart", label="cart", phrase="a sturdy prop cart", heavy=True, rollable=True),
    "lantern": PropSpec(id="lantern", label="lantern", phrase="a bright lantern"),
    "map": PropSpec(id="map", label="map", phrase="a folded treasure map"),
    "cloak": PropSpec(id="cloak", label="cloak", phrase="a long adventure cloak"),
    "sign": PropSpec(id="sign", label="sign", phrase="a hand-painted sign"),
}

ROLES = {
    "leader": StoryRole(id="leader", line="Let's work together!", needs_repetition=True),
    "helper": StoryRole(id="helper", line="I can help!", needs_repetition=False),
    "reader": StoryRole(id="reader", line="We can say the new word kindly.", needs_repetition=True),
    "mover": StoryRole(id="mover", line="Push with me!", needs_repetition=False),
}


def activity_line(theme: str) -> str:
    return {
        "adventure": "an adventure skit with brave steps and a pretend trail",
        "science": "a gentle science skit with careful words and open eyes",
        "play": "a playful skit with bright voices and big smiles",
    }[theme]


def make_intro(world: World, hero: Entity, helper: Entity, prop: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved {activity_line(world.facts['theme'])}."
    )
    world.say(
        f"{helper.id}, a kind {helper.type}, came to help with the {prop.label} and the skit."
    )


def make_setup(world: World, hero: Entity, helper: Entity, prop: Entity) -> None:
    world.say(
        f"On rehearsal day, they rolled the {prop.label} into {world.setting.place}, "
        f"where the costumes and notes were waiting."
    )
    world.say(
        f"Their skit needed teamwork, because the {prop.label} was heavy and the stage was busy."
    )


def make_word_moment(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"During the skit, a teacher pointed to a science poster and said the word vagina clearly and calmly."
    )
    world.say(
        f"{hero.id} listened carefully, and {helper.id} answered with kindness so the room stayed peaceful."
    )


def make_repetition(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"Then everyone repeated the line again and again: {ROLES['reader'].line}"
    )
    world.say(
        f"Repeating it helped {hero.id} remember the words, and it helped {helper.id} keep the pace steady."
    )


def make_resolution(world: World, hero: Entity, helper: Entity, prop: Entity) -> None:
    world.say(
        f"At the end, {hero.id} and {helper.id} pushed the {prop.label} together, "
        f"and the cart rolled straight to the stage."
    )
    world.say(
        f"The skit finished in a happy adventure, with kind voices, shared work, and one brave new word remembered well."
    )


def generate_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    prop = world.add(Entity(id=params.prop, type=params.prop, label=PROPS[params.prop].label, phrase=PROPS[params.prop].phrase))
    world.facts.update(
        theme=params.theme,
        prop=prop.label,
        setting=setting.place,
        hero=hero,
        helper=helper,
        prop_ent=prop,
    )

    make_intro(world, hero, helper, prop)
    world.para()
    make_setup(world, hero, helper, prop)
    make_word_moment(world, hero, helper)
    world.para()
    make_repetition(world, hero, helper)
    make_resolution(world, hero, helper, prop)
    return world


def valid_combo(setting: str, theme: str, prop: str) -> bool:
    if theme == "adventure" and prop != "cart":
        return False
    if setting == "hall" and prop == "cart":
        return True
    return True


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    for role_id, role in ROLES.items():
        lines.append(asp.fact("role", role_id))
        if role.needs_repetition:
            lines.append(asp.fact("needs_repetition", role_id))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, T, P) :- setting(S), theme(T), prop(P), allows(S, T, P).
allows(_, adventure, cart).
allows(S, science, P) :- setting(S), prop(P).
allows(S, play, P) :- setting(S), prop(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, t, p) for s in SETTINGS for t in THEMES for p in PROPS if valid_combo(s, t, p)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python validity gate ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure-skirted classroom story world with a cart, kindness, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
    combos = [(s, t, p) for s in SETTINGS for t in THEMES for p in PROPS if valid_combo(s, t, p)]
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting)
              and (args.theme is None or c[1] == args.theme)
              and (args.prop is None or c[2] == args.prop)]
    if not combos:
        raise StoryError("No valid story matches the chosen options.")
    setting, theme, prop = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(["Mina", "Toby", "Luna", "Ezra", "Noa", "Iris"])
    helper_name = args.helper or rng.choice(["Kai", "Pia", "Jules", "Nora", "Milo", "Sage"])
    return StoryParams(setting=setting, theme=theme, prop=prop, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name, helper_type=helper_type)


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    prop: Entity = world.facts["prop_ent"]
    return [
        QAItem(
            question=f"Who helped {hero.id} with the {prop.label}?",
            answer=f"{helper.id} helped {hero.id} with the {prop.label}. They worked together the whole time.",
        ),
        QAItem(
            question="What word did the teacher say during the skit?",
            answer="The teacher said vagina clearly and calmly as part of the science moment.",
        ),
        QAItem(
            question=f"Why did the group repeat the line again and again?",
            answer=f"They repeated it so {hero.id} could remember it and the performance could stay steady and kind.",
        ),
        QAItem(
            question=f"How did the {prop.label} move at the end?",
            answer=f"The {prop.label} rolled straight to the stage when {hero.id} and {helper.id} pushed it together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cart used for?",
            answer="A cart is used to carry things more easily, especially when the load is heavy.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What does kindness sound like?",
            answer="Kindness sounds calm, gentle, and respectful, especially when someone is learning something new.",
        ),
        QAItem(
            question="Why can repetition help in a skit?",
            answer="Repetition can help people remember words and feel more confident.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short adventure story about a classroom skit that uses a {f['prop']} and teaches the word vagina kindly.",
        f"Tell a child-friendly story where {f['hero'].id} and {f['helper'].id} use teamwork, kindness, and repetition to finish a skit.",
        f"Create a gentle adventure tale set in {f['setting']} with a rolling cart, a new science word, and a happy performance.",
    ]


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} kind={e.kind}")
    lines.append(f"setting: {world.setting.place}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world QA ==")
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


CURATED = [
    StoryParams(setting="classroom", theme="adventure", prop="cart", hero_name="Mina", hero_type="girl", helper_name="Kai", helper_type="boy"),
    StoryParams(setting="stage", theme="science", prop="cart", hero_name="Noa", hero_type="boy", helper_name="Pia", helper_type="girl"),
    StoryParams(setting="hall", theme="play", prop="cart", hero_name="Iris", hero_type="girl", helper_name="Sage", helper_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid stories:")
        for x in vals:
            print("  ", x)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
