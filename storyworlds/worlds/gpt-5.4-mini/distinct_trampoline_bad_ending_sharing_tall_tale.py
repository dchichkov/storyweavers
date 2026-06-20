#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/distinct_trampoline_bad_ending_sharing_tall_tale.py
===================================================================================

A standalone story world for a tall-tale-style little domain: two children,
one very distinct trampoline, a sharing dispute, and a bad ending that still
teaches a clean lesson. The world is small on purpose: a hero wants to keep a
special trampoline all to themselves, a sibling or friend asks to share, the
hero refuses, the trampoline goes wrong in an exaggerated tall-tale way, and the
ending proves what changed.

Seed words / instruments:
- distinct
- trampoline

Features:
- Bad Ending
- Sharing

Style:
- Tall Tale

This script follows the Storyweavers contract:
- self-contained stdlib script
- eager results import for QAItem / StoryError / StorySample
- lazy asp import inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, --show-asp
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    sky: str
    tale_line: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Trampoline:
    id: str
    label: str
    phrase: str
    distinct_mark: str
    bounce: str
    tear_risk: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class SharingChoice:
    id: str
    action: str
    result: str
    lesson: str
    sense: int

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_dizzy(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["whirling"] < THRESHOLD:
            continue
        sig = ("dizzy", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "ground" in world.entities:
            world.get("ground").meters["battered"] += 1
        for kid in list(world.entities.values()):
            if kid.kind == "character":
                kid.memes["astonishment"] += 1
        out.append("__dizzy__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_dizzy,):
            got = rule(world)
            if got:
                changed = True
                produced.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tall_tale_opening(world: World, hero: Entity, pal: Entity, setting: Setting, tramp: Trampoline) -> None:
    hero.memes["pride"] += 1
    pal.memes["wonder"] += 1
    world.say(
        f"Long ago, in {setting.place}, the sky was so big it could have hidden a parade of kites. "
        f"There stood {hero.id}, as distinct as a red apple in a gray basket, beside {pal.id}, "
        f"and between them was {tramp.phrase}."
    )
    world.say(
        f"Everyone in the yard knew the trampoline by its {tramp.distinct_mark}, and its springs sang "
        f"a tune that sounded like {tramp.bounce}."
    )


def ask_sharing(world: World, pal: Entity, hero: Entity) -> None:
    pal.memes["desire"] += 1
    world.say(
        f"\"Can I have a turn?\" asked {pal.id}. \"Sharing makes a game twice as bright.\""
    )
    hero.memes["possessive"] += 1
    world.say(
        f"{hero.id} folded {hero.pronoun('possessive')} arms. \"No, this trampoline is mine,\" {hero.pronoun()} said."
    )


def warn_of_trouble(world: World, setting: Setting, tramp: Trampoline) -> None:
    world.say(
        f"But the old yard had a tall-tale habit of answering unkindness with trouble. "
        f"The boards creaked, the wind leaned in, and the trampoline began to wobble "
        f"like a biscuit on a rocking chair."
    )
    if tramp.tear_risk:
        world.say(
            f"The {tramp.label} had a little tear hidden under the mat, and every hard bounce found it."
        )


def refuse_and_bounce(world: World, hero: Entity, pal: Entity, tramp: Trampoline) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} climbed up alone and bounced higher and higher, as if the clouds themselves were counting."
    )
    world.say(
        f"{pal.id} stepped back, worried, while {hero.id} laughed too loudly and landed too hard."
    )
    world.get("trampoline").meters["whirling"] += 1.0


def bad_ending(world: World, hero: Entity, pal: Entity, tramp: Trampoline) -> None:
    world.para()
    propagate(world, narrate=False)
    world.say(
        f"Then came the bad ending: with one last giant boing, the trampoline tipped, the torn edge split wide, "
        f"and {hero.id} tumbled into the mud like a dropped hat in a thunderstorm."
    )
    world.say(
        f"{pal.id} rushed over, but the bouncing was over, the mat was sagging, and the happy game had turned to a sad, quiet heap."
    )
    world.say(
        f"At last {hero.id} had to say the words {hero.pronoun('possessive')} heart should have said sooner: "
        f"\"I should have shared.\""
    )


def lesson(world: World, hero: Entity, pal: Entity, tramp: Trampoline) -> None:
    hero.memes["lesson"] += 1
    pal.memes["lesson"] += 1
    world.say(
        f"From then on, {hero.id} and {pal.id} used {tramp.label} by taking turns, one jump at a time, so nobody got left out."
    )
    world.say(
        f"The trampoline was still distinct, but now its best trick was teaching that a game stays brighter when it is shared."
    )


def tell(setting: Setting, tramp: Trampoline, share: SharingChoice,
         hero_name: str, hero_gender: str,
         pal_name: str, pal_gender: str,
         parent_type: str = "mother") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    pal = world.add(Entity(id=pal_name, kind="character", type=pal_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="ground", type="ground", label="the muddy ground"))
    world.add(Entity(id="trampoline", type="thing", label=tramp.label))
    world.facts["setting"] = setting
    world.facts["trampoline_cfg"] = tramp
    world.facts["sharing"] = share

    tall_tale_opening(world, hero, pal, setting, tramp)
    world.para()
    ask_sharing(world, pal, hero)
    warn_of_trouble(world, setting, tramp)

    if share.id == "refuse":
        refuse_and_bounce(world, hero, pal, tramp)
        bad_ending(world, hero, pal, tramp)
    else:
        hero.memes["generosity"] += 1
        world.say(
            f"{hero.id} thought of {pal.id}'s request and gave a slow nod. \"All right,\" {hero.pronoun()} said. "
            f"\"We can share.\""
        )
        world.say(
            f"Their turns were short and fair, and the trampoline sang a kinder tune."
        )
        lesson(world, hero, pal, tramp)

    world.facts.update(
        hero=hero,
        pal=pal,
        parent=parent,
        outcome="bad" if share.id == "refuse" else "shared",
        hurt=share.id == "refuse",
    )
    return world


SETTINGS = {
    "backyard": Setting("backyard", "the backyard", "windy", "the apple tree stood like a giant old watchman"),
    "field": Setting("field", "the open field", "wide", "the grass rolled on forever like a green sea"),
    "farm": Setting("farm", "the farmyard", "dusty", "the barn blinked red as a sleepy dragon"),
}

TRAMPOLINES = {
    "patchwork": Trampoline("patchwork", "the patchwork trampoline", "a trampoline patched with blue and gold cloth", "blue-and-gold stitches", "boom-bump, boom-bump", tear_risk=True),
    "silver": Trampoline("silver", "the silver trampoline", "a silver trampoline with bright rope edges", "bright rope edges", "ding-dong, whoop-whoop", tear_risk=False),
    "small": Trampoline("small", "the small trampoline", "a small trampoline with a round red handle", "round red handle", "tip-tap, tip-tap", tear_risk=True),
}

SHARING = {
    "refuse": SharingChoice("refuse", "refused to share", "bad ending", "Games turn sad when nobody gets a turn", 1),
    "share": SharingChoice("share", "shared the trampoline", "shared ending", "Sharing keeps the play bright", 3),
}

GIRL_NAMES = ["Lila", "Mira", "Nora", "Ruby", "Ava", "June"]
BOY_NAMES = ["Otis", "Ben", "Jasper", "Eli", "Theo", "Milo"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    trampoline: str
    sharing: str
    hero: str
    hero_gender: str
    pal: str
    pal_gender: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, t, sh) for s in SETTINGS for t in TRAMPOLINES for sh in SHARING]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about a distinct trampoline and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trampoline", choices=TRAMPOLINES)
    ap.add_argument("--sharing", choices=SHARING)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--pal")
    ap.add_argument("--pal-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              and (args.trampoline is None or c[1] == args.trampoline)
              and (args.sharing is None or c[2] == args.sharing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tramp, sharing = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    pal_gender = args.pal_gender or ("boy" if hero_gender == "girl" and rng.random() < 0.5 else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    pal_choices = [n for n in (GIRL_NAMES if pal_gender == "girl" else BOY_NAMES) if n != hero]
    pal = args.pal or rng.choice(pal_choices)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, tramp, sharing, hero, hero_gender, pal, pal_gender, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, pal = f["hero"], f["pal"]
    tramp = f["trampoline_cfg"]
    share = f["sharing"]
    return [
        f'Write a tall-tale style story for a 3-to-5-year-old that includes the word "distinct" and features {tramp.label}.',
        f"Tell a story where {hero.id} will not share {tramp.label} at first, {pal.id} asks for a turn, and the ending goes badly because of the choice.",
        f"Write a story about sharing on a trampoline that ends with a bad ending and teaches why turns matter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, pal = f["hero"], f["pal"]
    tramp = f["trampoline_cfg"]
    share = f["sharing"]
    out = [
        QAItem("Who is the story about?",
               f"It is about {hero.id} and {pal.id}, two children at the {f['setting'].place}. The story also follows their distinct trampoline and the choice they made about sharing."),
        QAItem("What did {hero} refuse to do?".format(hero=hero.id),
               f"{hero.id} refused to share {tramp.label} at first. That refusal set up the trouble that led to the bad ending."),
        QAItem("What happened at the end?",
               f"The ending was bad: the trampoline tipped, the torn edge split, and {hero.id} landed in the mud. The game stopped because the children did not share well enough."),
    ]
    if share.id == "share":
        out.append(QAItem("How did they fix the problem?",
                          f"They fixed it by taking turns and sharing {tramp.label}. That made the play fair and calm again."))
    else:
        out.append(QAItem("Why did the trouble happen?",
                          f"The trouble happened because {hero.id} kept {tramp.label} to {hero.pronoun('object')}self and would not share. Once the bouncing got too wild, the old tear gave way and the game went wrong."))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is sharing?", "Sharing means letting someone else use something too, so everyone gets a turn."),
        QAItem("What is a trampoline?", "A trampoline is a bouncy bed that lets you jump up and down for fun."),
        QAItem("What does distinct mean?", "Distinct means easy to tell apart because it has a special look or feeling."),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("backyard", "patchwork", "refuse", "Ivy", "girl", "Milo", "boy", "mother"),
    StoryParams("field", "silver", "share", "Jasper", "boy", "Lila", "girl", "father"),
    StoryParams("farm", "small", "refuse", "Nora", "girl", "Otis", "boy", "mother"),
]


def tell_story(params: StoryParams) -> World:
    world = tell(SETTINGS[params.setting], TRAMPOLINES[params.trampoline], SHARING[params.sharing],
                 params.hero, params.hero_gender, params.pal, params.pal_gender, params.parent)
    return world


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


ASP_RULES = r"""
valid(S, T, H) :- setting(S), trampoline(T), sharing(H).
"""


def asp_facts() -> str:
    import asp
    out = []
    for s in SETTINGS:
        out.append(asp.fact("setting", s))
    for t in TRAMPOLINES:
        out.append(asp.fact("trampoline", t))
    for h in SHARING:
        out.append(asp.fact("sharing", h))
    return "\n".join(out)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke-tested generation on curated params.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_sample_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (setting, trampoline, sharing) combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = build_sample_from_args(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.pal}: {p.trampoline} in {p.setting} ({p.sharing})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
