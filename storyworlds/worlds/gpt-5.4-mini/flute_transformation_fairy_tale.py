#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/flute_transformation_fairy_tale.py
===================================================================

A standalone fairy-tale story world about a flute, a kindly helper, and a
transformation that changes what the hero can do.

Base story inspiration
----------------------
A small child or young helper finds a magical flute in a fairy-tale setting.
Playing it transforms something frightened or ordinary into a truer, better
form: a locked path opens, a shy animal becomes brave, a dull figure becomes
bright, or a hidden garden wakes up. The story should feel like a complete
fairy tale with a beginning, a turn, and a proof-of-change ending.

This world models:
- a hero who wants to use a flute,
- a guardian or fairy who worries about the magic,
- a transformation target that changes state when the flute is played,
- a resolution image that shows the transformed world.

The engine is deliberately small and constraint-checked. It prefers a single
clear tale over many weak variants.
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "fairy", "woman"}
        male = {"boy", "father", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "queen": "queen",
                "king": "king", "fairy": "fairy"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    opening: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Flute:
    id: str
    label: str
    phrase: str
    sound: str
    glow: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    before: str
    after: str
    transformation: str
    needs_help: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guardian:
    id: str
    label: str
    phrase: str
    warning: str
    blessing: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["transformed"] < THRESHOLD:
            continue
        sig = ("transformed", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["wonder"] += 1
        out.append(f"{ent.label or ent.id} seemed brighter and truer than before.")
    return out


CAUSAL_RULES = [Rule("transform", "magic", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tale_ready(target: Target, flute: Flute) -> bool:
    return "transform" in target.tags and "music" in flute.tags


def play_flute(world: World, hero: Entity, flute: Flute, target: Entity, cfg: Target) -> None:
    hero.memes["hope"] += 1
    flute_ent = world.get(flute.id)
    flute_ent.meters["played"] += 1
    target.meters["listened"] += 1
    target.meters["transformed"] += 1
    target.meters["glow"] += 1
    target.attrs["form"] = cfg.after
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} lifted the flute and played {flute.sound}. "
        f"At once, {cfg.before} began to shimmer."
    )
    world.say(
        f"The music touched {target.label}, and {cfg.transformation}."
    )


def warn(world: World, guardian: Entity, hero: Entity, flute: Flute, target: Target) -> None:
    guardian.memes["care"] += 1
    world.say(
        f'{guardian.id} raised a hand. "{guardian.facts['warning'] if False else guardian.attrs.get("warning", "")}"'
        if False else ""
    )


def guardian_warn(world: World, guardian: Entity, hero: Entity, flute: Flute, target: Target) -> None:
    guardian.memes["care"] += 1
    world.say(
        f'"{guardian.attrs.get("warning")}" said {guardian.id}. '
        f'"A flute can wake magic, but it must be used with a kind heart."'
    )
    hero.memes["doubt"] += 1


def guardian_bless(world: World, guardian: Entity, hero: Entity, flute: Flute) -> None:
    world.say(
        f'Then {guardian.id} smiled and gave {hero.id} a gentle nod. '
        f'"If the song is for helping, let it be sung."'
    )
    hero.memes["courage"] += 1


def ending(world: World, hero: Entity, target: Entity, cfg: Target) -> None:
    world.say(
        f"By the end, {target.label} was no longer {cfg.before}; it was {cfg.after}. "
        f"{hero.id} played a soft final note, and the whole place felt blessed."
    )


def tell(setting: Setting, flute: Flute, target: Target, guardian: Guardian,
         hero_name: str = "Elin", hero_gender: str = "girl") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender,
                            role="hero", traits=["kind", "curious"]))
    guard = world.add(Entity(id=guardian.id, kind="character", type="fairy",
                             role="guardian", label=guardian.label,
                             attrs={"warning": guardian.warning, "blessing": guardian.blessing}))
    flute_ent = world.add(Entity(id=flute.id, kind="thing", type="flute", label=flute.label))
    target_ent = world.add(Entity(id=target.id, kind="thing", type="thing", label=target.label,
                                  attrs={"form": target.before}))
    world.facts.update(hero=hero, guardian=guard, flute=flute_ent, target=target_ent,
                       setting=setting, flute_cfg=flute, target_cfg=target, guardian_cfg=guardian)

    world.say(setting.opening.format(hero=hero.id, place=setting.place, mood=setting.mood))
    world.say(
        f"One day {hero.id} found {flute.phrase} hidden near the old path. "
        f"It looked ordinary, but it held a secret shine."
    )
    world.para()
    world.say(
        f"{hero.id} wanted to use the flute to help {target.label}, because {target.needs_help}."
    )
    guardian_warn(world, guard, hero, flute, target)
    if not tale_ready(target, flute):
        raise StoryError("This tale needs a flute that can transform something.")
    hero.memes["resolve"] += 1
    play_flute(world, hero, flute, target_ent, target)
    world.para()
    guardian_bless(world, guard, hero, flute)
    ending(world, hero, target_ent, target)
    world.say(setting.ending)
    world.facts["outcome"] = "transformed"
    return world


SETTINGS = {
    "woods": Setting(
        "woods", "the moonlit woods", "quiet and silver",
        "In the moonlit woods, everything was quiet and silver, and {hero} "
        "walked softly past the sleeping trees.",
        "The woods shone a little brighter than before.",
        tags={"fairy_tale", "woods"},
    ),
    "castle": Setting(
        "castle", "the old castle hall", "echoing and grand",
        "In the old castle hall, the stones echoed every step, and {hero} "
        "followed the ribbon of torchlight.",
        "The castle hall felt warm and alive.",
        tags={"fairy_tale", "castle"},
    ),
    "garden": Setting(
        "garden", "the hidden garden", "sweet and still",
        "In the hidden garden, the flowers slept under a veil of dew, and "
        "{hero} found a path behind the roses.",
        "The hidden garden bloomed with gentle color.",
        tags={"fairy_tale", "garden"},
    ),
}

FLUTES = {
    "silver_flute": Flute("silver_flute", "silver flute", "a silver flute",
                          "a clear little tune", "a pale moonbeam-like glow",
                          tags={"music", "flute"}),
    "wooden_flute": Flute("wooden_flute", "wooden flute", "a wooden flute",
                          "a warm dancing tune", "a honey-colored shine",
                          tags={"music", "flute"}),
    "bird_flute": Flute("bird_flute", "bird-carved flute", "a bird-carved flute",
                        "a bright nest-song", "a gold feather glow",
                        tags={"music", "flute"}),
}

TARGETS = {
    "rose": Target("rose", "rose bush", "a rose bush", "sleepy and closed",
                   "awake and blooming", "the roses unfolded like tiny smiles",
                   "it needed a song to open after the night", tags={"transform"}),
    "statue": Target("statue", "stone statue", "a stone statue", "cold and still",
                     "warm and smiling", "the stone softened into a kindly face",
                     "it needed a song to remember its gentle heart", tags={"transform"}),
    "frog": Target("frog", "little frog", "a little frog", "shy and gray",
                   "bright green and brave", "the frog sprang up with shiny eyes",
                   "it needed a song to remember how to hop", tags={"transform"}),
    "gate": Target("gate", "iron gate", "an iron gate", "locked and silent",
                   "open and welcoming", "the gate swung open with a sigh",
                   "it needed a song to open the path home", tags={"transform"}),
}

GUARDIANS = {
    "fairy": Guardian("fairy", "fairy aunt", "a fairy aunt",
                      "A flute can wake magic, but only gentle music should call it.",
                      "That is a good kind of music. Let it help."),
    "king": Guardian("king", "old king", "an old king",
                     "Magic may answer, but it listens best to kindness.",
                     "Then play on, child, and let the blessing work."),
}

GIRL_NAMES = ["Elin", "Mira", "Lina", "Sera", "Tilda", "Nina"]
BOY_NAMES = ["Oren", "Pip", "Bram", "Finn", "Rowan", "Tomas"]


@dataclass
class StoryParams:
    setting: str
    flute: str
    target: str
    guardian: str
    hero: str
    hero_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, f, t, g) for s in SETTINGS for f in FLUTES for t in TARGETS for g in GUARDIANS
            if tale_ready(TARGETS[t], FLUTES[f])]


def explain_rejection() -> str:
    return "(No story: the flute must have a magical transformation target.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about a flute transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--flute", choices=FLUTES)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.setting or args.flute or args.target or args.guardian:
        combos = [c for c in combos
                  if (args.setting is None or c[0] == args.setting)
                  and (args.flute is None or c[1] == args.flute)
                  and (args.target is None or c[2] == args.target)
                  and (args.guardian is None or c[3] == args.guardian)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, flute, target, guardian = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or (rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES))
    return StoryParams(setting, flute, target, guardian, hero, gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a young child that includes the word "flute" '
        f'and ends with a transformation.',
        f"Tell a gentle fairy tale where {f['hero'].id} plays a flute to help "
        f"{f['target_cfg'].label}, and a wise guardian approves the magic.",
        f"Write a story with a musical transformation, a clear ending image, and a flute.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    target = f["target_cfg"]
    flute = f["flute_cfg"]
    guardian = f["guardian_cfg"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, who found a flute and used it to help {target.label}. "
                   f"The tale follows {hero.id} from discovery to the transformed ending."
        ),
        QAItem(
            question="Why did the hero play the flute?",
            answer=f"{hero.id} played the flute because {target.needs_help}. "
                   f"The music was meant to wake the change gently, not to force it."
        ),
        QAItem(
            question="What did the guardian say about the flute?",
            answer=f'{guardian.label} warned that "{guardian.warning}" and then blessed the music when it was kind. '
                   f"That made the transformation feel safe and guided."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"{target.label} changed from {target.before} to {target.after}. "
                   f"The final image proves the song worked because the world looked awake and blessed."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flute?",
            answer="A flute is a musical instrument you blow across to make a clear, singing sound. "
                   "In fairy tales, a flute can sometimes carry magic."
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new form or becomes different. "
                   "In a fairy tale, that change can be magical, like a sleeping thing waking up."
        ),
        QAItem(
            question="Why do fairy tales often use music?",
            answer="Fairy tales often use music because songs feel soft, magical, and hopeful. "
                   "A tune can seem to call kindness, sleep, or change."
        ),
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
    lines.append("== (3) World knowledge questions ==")
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
        if e.attrs:
            bits.append(f"attrs={ {k:v for k,v in e.attrs.items() if v} }")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for f in FLUTES:
        lines.append(asp.fact("flute", f))
    for t in TARGETS:
        lines.append(asp.fact("target", t))
    for g in GUARDIANS:
        lines.append(asp.fact("guardian", g))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,F,T,G) :- setting(S), flute(F), target(T), guardian(G), transformable(T,F).
transformable(T,F) :- target(T), flute(F), target_tag(T, transform), flute_tag(F, music).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python.")
        if cl - py:
            print("only in ASP:", sorted(cl - py))
        if py - cl:
            print("only in Python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    flute = FLUTES[params.flute]
    target = TARGETS[params.target]
    guardian = GUARDIANS[params.guardian]
    world = tell(setting, flute, target, guardian, params.hero, params.hero_gender)
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


def tell(setting: Setting, flute: Flute, target: Target, guardian: Guardian,
         hero_name: str, hero_gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero",
                            traits=["kind", "curious"]))
    world.add(Entity(id=guardian.id, kind="character", type="fairy", role="guardian",
                     label=guardian.label, attrs={"warning": guardian.warning,
                                                   "blessing": guardian.blessing}))
    flute_ent = world.add(Entity(id=flute.id, kind="thing", type="flute", label=flute.label))
    target_ent = world.add(Entity(id=target.id, kind="thing", type="thing", label=target.label,
                                  attrs={"form": target.before}))
    world.facts.update(hero=hero, flute_cfg=flute, target_cfg=target, guardian_cfg=guardian,
                       flute=flute_ent, target=target_ent)

    world.say(setting.opening.format(hero=hero.id, place=setting.place, mood=setting.mood))
    world.say(
        f"One day, {hero.id} found {flute.phrase} near the old path. "
        f"It rested there like a secret waiting to be heard."
    )
    world.para()
    world.say(
        f"{hero.id} saw that {target.label} was {target.before} and knew it needed help."
    )
    world.say(f"{hero.id} wanted to use the flute because {target.needs_help}.")
    guardian_warn(world, world.get(guardian.id), hero, flute, target)
    play_flute(world, hero, flute, target_ent, target)
    world.para()
    guardian_bless(world, world.get(guardian.id), hero, flute)
    world.say(
        f"By the end, {target.label} was {target.after}, and the whole place felt as if it had woken from a dream."
    )
    world.say(setting.ending)
    world.facts["outcome"] = "transformed"
    return world


def guardian_warn(world: World, guardian: Entity, hero: Entity, flute: Flute, target: Target) -> None:
    guardian.memes["care"] += 1
    world.say(f'"{guardian.attrs["warning"]}" said {guardian.id}.')
    world.say(f'"{guardian.attrs["blessing"]}" the guardian whispered, "if the song is kind."')


CURATED = [
    StoryParams("woods", "silver_flute", "rose", "fairy", "Elin", "girl"),
    StoryParams("castle", "wooden_flute", "statue", "king", "Oren", "boy"),
    StoryParams("garden", "bird_flute", "frog", "fairy", "Mira", "girl"),
    StoryParams("woods", "wooden_flute", "gate", "king", "Bram", "boy"),
]


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
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
        if args.all:
            p = sample.params
            header = f"### {p.hero}: flute={p.flute}, target={p.target}, setting={p.setting}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
