#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/basic_testicle_macaroni_sound_effects_folk_tale.py
============================================================================================================

A standalone storyworld for a tiny folk tale built from the seed words:
basic, testicle, macaroni, and sound effects.

Premise:
- A small village prepares a simple supper.
- A young helper wants to use a very plain, very basic macaroni pot for the village feast.
- A troublesome little clacking charm called the Testicle Bell keeps making odd sound effects.
- The bell's noise startles the cook, but the helper learns a kinder way to calm it.

Narrative shape:
- Setup: introduce the village, the cook, the helper, and the macaroni.
- Tension: the noisy charm ruins the quiet work.
- Turn: the helper discovers that the bell likes rhythmic tapping and a warm spoon.
- Resolution: the feast is saved, and the bell becomes part of the cheerful music.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven prose
- QA generation
- inline ASP twin
- `--verify`, `--asp`, `--show-asp`, `--json`, `--qa`, `--trace`, `-n`, `--all`, `--seed`
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"noise": 0.0, "warmth": 0.0, "mess": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "patience": 0.0, "fear": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"woman", "girl", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"man", "boy", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little village"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    noise: str
    calm: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    label: str
    phrase: str
    type: str
    protection: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    noise_kind: str
    can_settle_with: set[str] = field(default_factory=set)


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
    item: str
    charm: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


SETTINGS = {
    "village": Setting(place="the little village", indoors=False, affords={"cook", "carry", "ring"}),
    "kitchen": Setting(place="the warm kitchen", indoors=True, affords={"cook", "stir", "ring"}),
    "green": Setting(place="the green hill", indoors=False, affords={"carry", "ring"}),
}

ACTIONS = {
    "cook": Action(
        id="cook",
        verb="cook macaroni",
        gerund="cooking macaroni",
        rush="rush to the pot",
        noise="sizzle-sizzle",
        calm="stir in a slow circle",
        tags={"food", "macaroni", "sound"},
    ),
    "stir": Action(
        id="stir",
        verb="stir the pot",
        gerund="stirring the pot",
        rush="dash to the spoon",
        noise="clink-clink",
        calm="tap the spoon twice",
        tags={"food", "sound"},
    ),
    "ring": Action(
        id="ring",
        verb="ring the bell",
        gerund="ringing the bell",
        rush="lift the charm high",
        noise="ding-ding",
        calm="hold it close",
        tags={"sound"},
    ),
}

ITEMS = {
    "basic_pot": Item(
        label="basic pot",
        phrase="a basic pot with a round lid",
        type="pot",
        protection={"cook", "stir"},
    ),
    "macaroni_bowl": Item(
        label="macaroni bowl",
        phrase="a big bowl of macaroni",
        type="bowl",
        protection={"cook", "stir"},
        plural=False,
    ),
    "wooden_spoon": Item(
        label="wooden spoon",
        phrase="a smooth wooden spoon",
        type="spoon",
        protection={"stir"},
    ),
}

CHARMS = {
    "testicle_bell": Charm(
        id="testicle_bell",
        label="Testicle Bell",
        phrase="the old Testicle Bell",
        noise_kind="ring",
        can_settle_with={"tap", "warmth", "music"},
    ),
    "macaroni_jar": Charm(
        id="macaroni_jar",
        label="macaroni jar",
        phrase="the macaroni jar",
        noise_kind="clatter",
        can_settle_with={"lid", "warmth"},
    ),
}

GIRL_NAMES = ["Anya", "Mira", "Lina", "Sera", "Nina"]
BOY_NAMES = ["Pavel", "Bram", "Oren", "Timo", "Eli"]
HELPER_NAMES = ["Milo", "Pip", "Rina", "Tess", "Jori"]
TRAITS = ["basic-hearted", "kind", "cheerful", "careful", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for a_id in setting.affords:
            for item_id in ITEMS:
                for c_id in CHARMS:
                    if a_id == "cook" and item_id == "basic_pot":
                        combos.append((s_id, a_id, item_id))
                    elif a_id == "stir" and item_id == "wooden_spoon":
                        combos.append((s_id, a_id, item_id))
                    elif a_id == "ring":
                        combos.append((s_id, a_id, item_id))
    return sorted(set(combos))


def story_can_work(action: Action, item: Item, charm: Charm) -> bool:
    if action.id == "cook" and "cook" in item.protection:
        return charm.id == "testicle_bell"
    if action.id == "stir" and "stir" in item.protection:
        return charm.id == "testicle_bell"
    if action.id == "ring":
        return True
    return False


def explain_rejection(action: Action, item: Item, charm: Charm) -> str:
    return (
        f"(No story: {action.gerund} with {item.label} and {charm.label} "
        f"does not make a sensible little folk-tale problem and fix.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.item:
        act = ACTIONS[args.action]
        item = ITEMS[args.item]
        charm = CHARMS[args.charm] if args.charm else CHARMS["testicle_bell"]
        if not story_can_work(act, item, charm):
            raise StoryError(explain_rejection(act, item, charm))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, action, item = rng.choice(combos)
    charm = args.charm or "testicle_bell"
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or ("boy" if hero_type == "girl" else "girl")
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        setting=setting,
        action=action,
        item=item,
        charm=charm,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    item = world.add(Entity(id=params.item, type=ITEMS[params.item].type, label=ITEMS[params.item].label, phrase=ITEMS[params.item].phrase, owner=hero.id, caretaker=helper.id))
    charm = world.add(Entity(id=params.charm, type="charm", label=CHARMS[params.charm].label, phrase=CHARMS[params.charm].phrase))
    world.facts.update(hero=hero, helper=helper, item=item, charm=charm, action=ACTIONS[params.action], params=params)
    return world


def apply_noise(world: World, charm: Entity, action: Action) -> None:
    charm.meters["noise"] += 1
    world.get(world.facts["hero"].id).memes["worry"] += 1
    world.say(f"Then came the {action.noise}, and the little village grew quiet around it.")


def calm_charm(world: World, helper: Entity, charm: Entity, action: Action) -> None:
    helper.memes["patience"] += 1
    world.say(
        f"{helper.id} remembered the charm liked a soft rhythm, so {helper.pronoun()} began to {action.calm}."
    )
    charm.meters["noise"] = max(0.0, charm.meters["noise"] - 1)


def generate_story(world: World, params: StoryParams) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    item = world.facts["item"]
    charm = world.facts["charm"]
    action = world.facts["action"]

    world.say(
        f"Once, in {world.setting.place}, there lived {hero.id}, a {hero.type} with a {item.label} that was as basic as bread."
    )
    world.say(
        f"{hero.id} loved {action.gerund}, because the steam and smell made supper feel warm and lucky."
    )
    world.say(
        f"Beside {hero.id} worked {helper.id}, who kept the {item.label} neat and the table ready for the feast."
    )
    world.para()
    world.say(
        f"On one evening, {hero.id} reached for {CHARMS[params.charm].phrase}, and the room answered with a bright {ACTIONS[params.action].noise}."
    )
    apply_noise(world, charm, action)
    world.say(
        f"The sound shook the spoons and made the macaroni wobble in its bowl."
    )
    hero.memes["fear"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"{helper.id} frowned, because too much noise could spill the supper and spoil the calm of the story."
    )
    world.para()
    world.say(
        f"Then {helper.id} tried a gentle trick: {helper.pronoun()} tapped the bell in time with a slow song from the hearth."
    )
    calm_charm(world, helper, charm, action)
    hero.memes["joy"] += 1
    charm.meters["warmth"] += 1
    world.say(
        f"The Testicle Bell grew friendly with the rhythm, and its clack became part of the music instead of a fright."
    )
    world.say(
        f"At last {hero.id} {action.verb}, the macaroni stayed safe in the basic pot, and the whole village ate by the fire while the little bell went ding-ding with the tune."
    )
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1)
    helper.memes["joy"] += 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a young child about a basic village, a noisy charm, and {f["action"].gerund}.',
        f"Tell a gentle story where {f['hero'].id} and {f['helper'].id} handle {CHARMS[f['charm'].id].phrase} without spilling macaroni.",
        f'Write a simple story that includes the words "basic", "testicle", and "macaroni", and ends with a happy sound effect.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, item, charm, action = f["hero"], f["helper"], f["item"], f["charm"], f["action"]
    return [
        QAItem(
            question=f"Who was the story mainly about in {world.setting.place}?",
            answer=f"The story was about {hero.id}, with {helper.id} helping beside the basic {item.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the supper?",
            answer=f"{hero.id} wanted to {action.verb}, because {action.gerund} made the meal feel special.",
        ),
        QAItem(
            question=f"What made the room noisy and caused trouble?",
            answer=f"The old {charm.label} made a bright {action.noise}, and that startled everyone for a moment.",
        ),
        QAItem(
            question=f"How did {helper.id} fix the problem?",
            answer=f"{helper.id} used a slow rhythm and a calm tap, which helped the charm settle down.",
        ),
        QAItem(
            question=f"What was the ending like?",
            answer=f"The macaroni stayed safe, the bell joined the music, and the village ended in a happy ding-ding.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "macaroni": [
        QAItem(
            question="What is macaroni?",
            answer="Macaroni is a kind of pasta with little curved tube shapes.",
        ),
    ],
    "basic": [
        QAItem(
            question="What does basic mean?",
            answer="Basic means simple and plain, not fancy.",
        ),
    ],
    "sound": [
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a noise that helps tell what is happening, like ding-ding or clink-clink.",
        ),
    ],
    "folk": [
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old story people tell again and again, often about everyday life or a magical lesson.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"basic", "macaroni", "sound", "folk"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(WORLD_KNOWLEDGE[tag])
    return out


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_fact(H).
helper(H) :- helper_fact(H).
item(I) :- item_fact(I).
charm(C) :- charm_fact(C).
action(A) :- action_fact(A).

compatible(setting, action, item) :- setting_fact(setting), action_fact(action), item_fact(item), works(action,item).
compatible_story(setting, action, item, hero_type) :- compatible(setting, action, item), hero_type_fact(hero_type).

% The specific little storyworld logic:
works(cook, basic_pot).
works(stir, wooden_spoon).
works(ring, basic_pot).
works(ring, macaroni_bowl).
works(ring, wooden_spoon).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s_id in SETTINGS:
        lines.append(asp.fact("setting_fact", s_id))
    for a_id in ACTIONS:
        lines.append(asp.fact("action_fact", a_id))
    for i_id in ITEMS:
        lines.append(asp.fact("item_fact", i_id))
    for c_id in CHARMS:
        lines.append(asp.fact("charm_fact", c_id))
    for ht in ["girl", "boy"]:
        lines.append(asp.fact("hero_type_fact", ht))
    lines.append(asp.fact("works", "cook", "basic_pot"))
    lines.append(asp.fact("works", "stir", "wooden_spoon"))
    lines.append(asp.fact("works", "ring", "basic_pot"))
    lines.append(asp.fact("works", "ring", "macaroni_bowl"))
    lines.append(asp.fact("works", "ring", "wooden_spoon"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
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


CURATED = [
    StoryParams(setting="village", action="cook", item="basic_pot", charm="testicle_bell", hero_name="Anya", hero_type="girl", helper_name="Milo", helper_type="boy"),
    StoryParams(setting="kitchen", action="stir", item="wooden_spoon", charm="testicle_bell", hero_name="Pavel", hero_type="boy", helper_name="Rina", helper_type="girl"),
    StoryParams(setting="green", action="ring", item="macaroni_bowl", charm="testicle_bell", hero_name="Sera", hero_type="girl", helper_name="Tess", helper_type="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale storyworld with macaroni and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
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


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    generate_story(world, params)
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
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible combos:")
        for t in models:
            print(" ", t)
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
            header = f"### {p.hero_name}: {p.action} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
